"""Rotas reais do Flask + serviço e modelos reais, com dados fictícios isolados."""

import csv
from datetime import date, timedelta
import io

import pytest


def test_lista_vazia_e_novo_teste_nao_tem_dados_de_outro(api):
    resposta = api.get("/api/lancamentos")
    assert resposta.status_code == 200
    assert resposta.get_json()["dados"] == []


def test_categorias_consultadas_sem_ids_fixos_da_interface(api):
    resposta = api.get("/api/categorias")
    assert resposta.status_code == 200
    categorias = resposta.get_json()["dados"]
    assert {c["id"] for c in categorias} == {11, 22, 33, 44}
    assert next(c for c in categorias if c["id"] == 22)["nome"] == "Alimentação"


@pytest.mark.parametrize("tipo,categoria_id,valor", [("receita", 11, 300000), ("despesa", 22, 45000)])
def test_cadastro_consulta_e_objeto_real(ambiente_api, cadastrar, tipo, categoria_id, valor):
    salvo = cadastrar(tipo=tipo, categoria_id=categoria_id, valor_centavos=valor)
    assert salvo["id"] == 1
    assert salvo["valor_centavos"] == valor
    lista = ambiente_api.client.get("/api/lancamentos").get_json()["dados"]
    assert lista == [salvo]
    impacto = ambiente_api.repo.buscar_por_id(1).impacto_no_saldo()
    assert impacto == (valor if tipo == "receita" else -valor)


def test_edicao_preserva_id_e_substitui_valor(api, cadastrar, payload):
    salvo = cadastrar()
    resposta = api.put(f"/api/lancamentos/{salvo['id']}", json={**payload, "valor_centavos": 50000})
    assert resposta.status_code == 200
    assert resposta.get_json()["dados"]["id"] == salvo["id"]
    lista = api.get("/api/lancamentos").get_json()["dados"]
    assert len(lista) == 1
    assert lista[0]["valor_centavos"] == 50000


def test_exclusao_remove_somente_o_id_escolhido(api, cadastrar):
    apagar = cadastrar(descricao="Apagar")
    manter = cadastrar(descricao="Manter")
    resposta = api.delete(f"/api/lancamentos/{apagar['id']}")
    assert resposta.status_code == 200
    assert resposta.get_json()["dados"] == {"id": apagar["id"], "excluido": True}
    assert [t["id"] for t in api.get("/api/lancamentos").get_json()["dados"]] == [manter["id"]]


def test_edicao_e_exclusao_de_inexistente_retornam_404(api, payload):
    assert api.put("/api/lancamentos/999", json=payload).status_code == 404
    assert api.delete("/api/lancamentos/999").status_code == 404


@pytest.mark.parametrize("campo,valor", [
    ("descricao", ""), ("descricao", "   "), ("descricao", "a" * 121),
    ("valor_centavos", 0), ("valor_centavos", -1), ("valor_centavos", True),
    ("data", "2020-02-30"), ("data", (date.today() + timedelta(days=1)).isoformat()),
    ("tipo", "transferencia"), ("categoria_id", 999), ("categoria_id", 11),
])
def test_validacoes_basicas_nao_gravam(ambiente_api, payload, campo, valor):
    resposta = ambiente_api.client.post("/api/lancamentos", json={**payload, campo: valor})
    assert resposta.status_code == 400
    assert "erro" in resposta.get_json()
    assert ambiente_api.repo.registros == {}


def test_edicao_invalida_preserva_o_registro(api, cadastrar, payload):
    salvo = cadastrar()
    resposta = api.put(f"/api/lancamentos/{salvo['id']}", json={**payload, "valor_centavos": -1})
    assert resposta.status_code == 400
    assert api.get("/api/lancamentos").get_json()["dados"] == [salvo]


def test_json_malformado_e_lista_sao_rejeitados(api):
    assert api.post("/api/lancamentos", data="{", content_type="application/json").status_code == 400
    assert api.post("/api/lancamentos", json=[]).status_code == 400


def test_filtros_combinados_busca_sem_diferenciar_maiusculas_e_ordenacao(api, cadastrar):
    cadastrar(descricao="Mercado janeiro", data="2020-01-05")
    cadastrar(descricao="Aluguel", categoria_id=33)
    mercado = cadastrar(descricao="Mercado fevereiro")
    salario = cadastrar(descricao="Salário", tipo="receita", categoria_id=11)
    lista = api.get("/api/lancamentos").get_json()["dados"]
    assert [t["id"] for t in lista] == [salario["id"], mercado["id"], 2, 1]
    filtrada = api.get("/api/lancamentos?mes=2020-02&tipo=despesa&categoria_id=22&busca=MERCADO")
    assert filtrada.status_code == 200
    assert [t["id"] for t in filtrada.get_json()["dados"]] == [mercado["id"]]


@pytest.mark.parametrize("query", ["mes=2020-13", "tipo=invalido", "categoria_id=abc", "categoria_id=-1"])
def test_filtros_invalidos_basicos(api, query):
    assert api.get("/api/lancamentos?" + query).status_code == 400


def test_resumo_usa_mes_e_inclui_historico_no_saldo(api, cadastrar):
    cadastrar(descricao="Saldo anterior", tipo="receita", categoria_id=11,
              data="2020-01-01", valor_centavos=100000)
    cadastrar(descricao="Salário", tipo="receita", categoria_id=11, valor_centavos=300000)
    cadastrar(descricao="Aluguel", categoria_id=33, valor_centavos=90000)
    cadastrar()
    cadastrar(descricao="Ônibus", categoria_id=44, valor_centavos=15000)
    resumo = api.get("/api/resumo?mes=2020-02").get_json()["dados"]
    assert [resumo[k] for k in ["receitas_centavos", "despesas_centavos", "resultado_centavos",
                               "saldo_acumulado_centavos"]] == [300000, 150000, 150000, 250000]
    assert [c["categoria_id"] for c in resumo["despesas_por_categoria"]] == [33, 22, 44]
    sem_movimento = api.get("/api/resumo?mes=2020-03").get_json()["dados"]
    assert sem_movimento["resultado_centavos"] == 0
    assert sem_movimento["saldo_acumulado_centavos"] == 250000


def test_resumo_recalcula_depois_de_editar_e_excluir(api, cadastrar, payload):
    salvo = cadastrar()
    api.put(f"/api/lancamentos/{salvo['id']}", json={**payload, "valor_centavos": 50000})
    assert api.get("/api/resumo?mes=2020-02").get_json()["dados"]["resultado_centavos"] == -50000
    api.delete(f"/api/lancamentos/{salvo['id']}")
    assert api.get("/api/resumo?mes=2020-02").get_json()["dados"]["resultado_centavos"] == 0


def test_csv_repete_filtros_da_consulta_e_escapa_ponto_e_virgula(api, cadastrar):
    salvo = cadastrar(descricao='Mercado; "promoção"')
    cadastrar(descricao="Aluguel", categoria_id=33)
    cadastrar(descricao="Mercado janeiro", data="2020-01-01")
    query = "mes=2020-02&tipo=despesa&categoria_id=22&busca=mercado"
    consulta = api.get("/api/lancamentos?" + query).get_json()["dados"]
    resposta = api.get("/api/exportar?" + query)
    assert resposta.status_code == 200
    assert resposta.data.startswith(b"\xef\xbb\xbf")
    assert "attachment" in resposta.headers["Content-Disposition"]
    linhas = list(csv.reader(io.StringIO(resposta.data.decode("utf-8-sig")), delimiter=";"))
    assert linhas[0] == ["id", "data", "descricao", "tipo", "categoria", "valor"]
    assert len(linhas) - 1 == len(consulta) == 1
    assert linhas[1] == [str(salvo["id"]), "2020-02-05", 'Mercado; "promoção"',
                         "despesa", "Alimentação", "450,00"]


def test_csv_vazio_tem_apenas_cabecalho(api):
    resposta = api.get("/api/exportar")
    assert resposta.data.decode("utf-8-sig") == "id;data;descricao;tipo;categoria;valor\r\n"


def test_erro_interno_e_tratado_sem_expor_detalhes(ambiente_api, monkeypatch):
    def falhar():
        raise RuntimeError("Detalhe interno que não deve ir para o navegador")
    monkeypatch.setattr(ambiente_api.repo, "listar_todos", falhar)
    resposta = ambiente_api.client.get("/api/lancamentos")
    assert resposta.status_code == 500
    assert resposta.get_json()["erro"]["mensagem"] == "Erro interno do servidor."
    assert "Detalhe interno" not in resposta.get_data(as_text=True)


def test_rotas_e_metodos_inexistentes(api):
    assert api.get("/api/nao-existe").status_code == 404
    assert api.delete("/api/lancamentos").status_code == 405
