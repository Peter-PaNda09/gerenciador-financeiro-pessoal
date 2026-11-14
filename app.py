"""Primeira integração de Peterson: categorias, cadastro e consulta em memória."""

import re
from datetime import date

from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest, HTTPException, UnsupportedMediaType

from models import (
    Despesa,
    ErroValidacaoFinanceira,
    Receita,
    RegistroNaoEncontradoErro,
    data_atual_sao_paulo,
)
from repositories.memoria import RepositorioTransacoesMemoria


CAMPOS_CADASTRO = {"descricao", "valor_centavos", "data", "tipo", "categoria_id"}
CAMPOS_LANCAMENTO = ("id", "descricao", "valor_centavos", "data", "tipo", "categoria_id")
FILTROS = {"mes", "tipo", "categoria_id", "busca"}


def serializar_lancamento(transacao):
    """Expõe somente os seis campos públicos do contrato HTTP."""
    dados = transacao.para_dict()
    return {campo: dados[campo] for campo in CAMPOS_LANCAMENTO}


def validar_parametros(permitidos):
    """Evita que filtros digitados incorretamente sejam ignorados silenciosamente."""
    erros = {}
    for nome in request.args:
        if nome not in permitidos:
            erros[nome] = "Parâmetro desconhecido."
        elif len(request.args.getlist(nome)) != 1:
            erros[nome] = "Informe o parâmetro apenas uma vez."
        elif not request.args[nome].strip():
            erros[nome] = "Omita o parâmetro quando não houver seleção."
    if erros:
        raise ErroValidacaoFinanceira("Confira os filtros informados.", campos=erros)


def criar_transacao(dados, repositorio, hoje):
    """Valida o JSON; as classes do domínio também validam o objeto criado."""
    if not isinstance(dados, dict):
        raise ErroValidacaoFinanceira("O corpo JSON deve ser um objeto.")

    erros = {campo: "Campo obrigatório." for campo in sorted(CAMPOS_CADASTRO - dados.keys())}
    erros.update({campo: "Campo não permitido no cadastro." for campo in sorted(dados.keys() - CAMPOS_CADASTRO)})
    for campo in CAMPOS_CADASTRO & dados.keys():
        if dados[campo] is None:
            erros[campo] = "O campo não pode ser nulo."

    descricao = dados.get("descricao")
    if "descricao" in dados and (not isinstance(descricao, str) or not 1 <= len(descricao.strip()) <= 120):
        erros["descricao"] = "Informe uma descrição de 1 a 120 caracteres."
    valor = dados.get("valor_centavos")
    if "valor_centavos" in dados and (type(valor) is not int or valor <= 0):
        erros["valor_centavos"] = "Informe um valor inteiro maior que zero."
    tipo = dados.get("tipo")
    if "tipo" in dados and tipo not in ("receita", "despesa"):
        erros["tipo"] = "Use exatamente receita ou despesa."
    categoria_id = dados.get("categoria_id")
    if "categoria_id" in dados and (type(categoria_id) is not int or categoria_id <= 0):
        erros["categoria_id"] = "Informe o ID inteiro de uma categoria existente."

    if "data" in dados:
        data = dados["data"]
        try:
            if not isinstance(data, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", data):
                raise ValueError
            if date.fromisoformat(data) > hoje():
                erros["data"] = "A data não pode ser posterior a hoje."
        except ValueError:
            erros["data"] = "Informe uma data existente em AAAA-MM-DD."

    if erros:
        raise ErroValidacaoFinanceira("Confira os campos informados.", campos=erros)

    categoria = repositorio.buscar_categoria_por_id(categoria_id)
    classe = Receita if tipo == "receita" else Despesa
    return classe(descricao=descricao, valor_centavos=valor, data=dados["data"], categoria=categoria)


def filtrar_lancamentos(repositorio):
    validar_parametros(FILTROS)
    filtros = request.args
    erros = {}
    mes = filtros.get("mes")
    if mes is not None:
        try:
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}", mes):
                raise ValueError
            date.fromisoformat(mes + "-01")
        except ValueError:
            erros["mes"] = "Informe um mês válido em AAAA-MM."
    tipo = filtros.get("tipo")
    if tipo is not None and tipo not in ("receita", "despesa"):
        erros["tipo"] = "Use exatamente receita ou despesa."
    categoria_id = filtros.get("categoria_id")
    if categoria_id is not None:
        if not re.fullmatch(r"[1-9][0-9]*", categoria_id):
            erros["categoria_id"] = "Informe o ID inteiro de uma categoria existente."
        else:
            categoria_id = int(categoria_id)
            try:
                repositorio.buscar_categoria_por_id(categoria_id)
            except ErroValidacaoFinanceira as erro:
                erros.update(erro.campos)
    if erros:
        raise ErroValidacaoFinanceira("Confira os filtros informados.", campos=erros)

    busca = filtros.get("busca", "").strip().lower()
    return [
        transacao for transacao in repositorio.listar()
        if (mes is None or transacao.data[:7] == mes)
        and (tipo is None or transacao.tipo == tipo)
        and (categoria_id is None or transacao.categoria.id == categoria_id)
        and (not busca or busca in transacao.descricao.lower())
    ]


def create_app(repositorio=None, hoje=None):
    """Injeta o repositório para permitir testes e a futura troca por um banco."""
    app = Flask(__name__)
    app.json.ensure_ascii = False
    repositorio = repositorio if repositorio is not None else RepositorioTransacoesMemoria()
    hoje = hoje if hoje is not None else data_atual_sao_paulo
    app.extensions["repositorio_transacoes"] = repositorio

    def erro_json(status, codigo, mensagem, campos=None):
        return jsonify({"erro": {"codigo": codigo, "mensagem": mensagem, "campos": campos or {}}}), status

    @app.errorhandler(ErroValidacaoFinanceira)
    def tratar_validacao(erro):
        return erro_json(400, "VALIDACAO", erro.mensagem, erro.campos)

    @app.errorhandler(RegistroNaoEncontradoErro)
    def tratar_nao_encontrado(erro):
        return erro_json(404, "NAO_ENCONTRADO", erro.mensagem)

    @app.errorhandler(HTTPException)
    def tratar_http(erro):
        if isinstance(erro, UnsupportedMediaType):
            return erro_json(415, "TIPO_CONTEUDO_INVALIDO", "Envie Content-Type: application/json.")
        if isinstance(erro, BadRequest):
            return erro_json(400, "JSON_INVALIDO", "O corpo da requisição contém JSON inválido.")
        if erro.code == 404:
            return erro_json(404, "NAO_ENCONTRADO", "Rota não encontrada.")
        if erro.code == 405:
            return erro_json(405, "METODO_NAO_PERMITIDO", "Método não disponível nesta rota.")
        return erro_json(erro.code, "ERRO_HTTP", erro.description)

    @app.errorhandler(Exception)
    def tratar_inesperado(erro):
        app.logger.exception("Erro inesperado ao processar a requisição.")
        return erro_json(500, "ERRO_INTERNO", "Ocorreu um erro interno no servidor.")

    @app.get("/")
    def inicio():
        return jsonify({
            "mensagem": "API do gerenciador financeiro pessoal em execução.",
            "armazenamento": "memoria",
            "rotas_implementadas": ["GET /api/categorias", "POST /api/lancamentos", "GET /api/lancamentos"],
        })

    @app.get("/api/categorias")
    def listar_categorias():
        validar_parametros(set())
        categorias = [
            {"id": c.id, "nome": c.nome, "tipo": c.tipo_permitido}
            for c in repositorio.listar_categorias()
        ]
        return jsonify({"dados": categorias, "meta": {"quantidade": len(categorias)}})

    @app.get("/api/lancamentos")
    def listar_lancamentos():
        transacoes = filtrar_lancamentos(repositorio)
        dados = [serializar_lancamento(transacao) for transacao in transacoes]
        return jsonify({"dados": dados, "meta": {"quantidade": len(dados)}})

    @app.post("/api/lancamentos")
    def cadastrar_lancamento():
        if request.mimetype != "application/json":
            raise UnsupportedMediaType()
        transacao = criar_transacao(request.get_json(), repositorio, hoje)
        salva = repositorio.salvar(transacao)
        return jsonify({"dados": serializar_lancamento(salva)}), 201

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
