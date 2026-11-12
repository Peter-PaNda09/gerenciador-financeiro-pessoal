from flask import Flask, request, jsonify, Response, render_template
from models import ErroValidacaoFinanceira, RegistroNaoEncontradoErro
from repository import RepositorioTransacoes
from service import GerenciadorFinanceiro

app = Flask(__name__, static_folder="static", template_folder="templates")

repositorio = RepositorioTransacoes()
gerenciador = GerenciadorFinanceiro(repositorio)


@app.errorhandler(ErroValidacaoFinanceira)
def tratar_erro_validacao(erro: ErroValidacaoFinanceira):
    return (
        jsonify(
            {
                "erro": {
                    "mensagem": erro.mensagem,
                    "campos": erro.campos,
                }
            }
        ),
        400,
    )


@app.errorhandler(RegistroNaoEncontradoErro)
def tratar_erro_nao_encontrado(erro: RegistroNaoEncontradoErro):
    return (
        jsonify(
            {
                "erro": {
                    "mensagem": erro.mensagem,
                    "campos": {},
                }
            }
        ),
        404,
    )


@app.errorhandler(Exception)
def tratar_erro_inesperado(erro: Exception):
    return (
        jsonify(
            {
                "erro": {
                    "mensagem": "Não foi possível concluir a operação. Tente novamente.",
                    "detalhe": str(erro),
                    "campos": {},
                }
            }
        ),
        500,
    )


@app.route("/", methods=["GET"])
def pagina_inicial():
    return render_template("index.html")


@app.route("/api/categorias", methods=["GET"])
def listar_categorias():
    tipo = request.args.get("tipo")
    categorias = gerenciador.listar_categorias(tipo=tipo)
    return jsonify({"dados": [c.para_dict() for c in categorias]}), 200


@app.route("/api/lancamentos", methods=["GET"])
def listar_lancamentos():
    mes = request.args.get("mes")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    tipo = request.args.get("tipo")
    busca = request.args.get("busca")

    categoria_id_param = request.args.get("categoria_id")
    categoria_id = None
    if categoria_id_param:
        try:
            categoria_id = int(categoria_id_param)
        except ValueError:
            raise ErroValidacaoFinanceira("Categoria inválida.", campo="categoria_id")

    lancamentos = gerenciador.consultar_lancamentos(
        mes=mes,
        data_inicio=data_inicio,
        data_fim=data_fim,
        tipo=tipo,
        categoria_id=categoria_id,
        busca=busca,
    )
    return jsonify({"dados": [t.para_dict() for t in lancamentos]}), 200


@app.route("/api/lancamentos", methods=["POST"])
def criar_lancamento():
    dados = request.get_json(silent=True)
    if dados is None:
        raise ErroValidacaoFinanceira("Corpo da requisição JSON ausente ou inválido.")
    novo = gerenciador.cadastrar_lancamento(dados)
    return jsonify({"dados": novo.para_dict()}), 201


@app.route("/api/lancamentos/<int:id_lancamento>", methods=["PUT"])
def atualizar_lancamento(id_lancamento: int):
    dados = request.get_json(silent=True)
    if dados is None:
        raise ErroValidacaoFinanceira("Corpo da requisição JSON ausente ou inválido.")
    atualizado = gerenciador.editar_lancamento(id_lancamento, dados)
    return jsonify({"dados": atualizado.para_dict()}), 200


@app.route("/api/lancamentos/<int:id_lancamento>", methods=["DELETE"])
def remover_lancamento(id_lancamento: int):
    gerenciador.excluir_lancamento(id_lancamento)
    return jsonify({"dados": {"id": id_lancamento, "excluido": True}}), 200


@app.route("/api/resumo", methods=["GET"])
def obter_resumo():
    mes = request.args.get("mes")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    resumo = gerenciador.calcular_resumo(
        mes=mes, data_inicio=data_inicio, data_fim=data_fim
    )
    return jsonify({"dados": resumo}), 200


@app.route("/api/exportar", methods=["GET"])
def exportar_csv():
    mes = request.args.get("mes")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    tipo = request.args.get("tipo")
    busca = request.args.get("busca")

    categoria_id_param = request.args.get("categoria_id")
    categoria_id = int(categoria_id_param) if categoria_id_param else None

    conteudo_csv = gerenciador.exportar_csv(
        mes=mes,
        data_inicio=data_inicio,
        data_fim=data_fim,
        tipo=tipo,
        categoria_id=categoria_id,
        busca=busca,
    )

    csv_com_bom = "\ufeff" + conteudo_csv
    nome_arquivo = f"lancamentos-{mes}.csv" if mes else "lancamentos.csv"

    return Response(
        csv_com_bom,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={nome_arquivo}"},
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
