"""Consistência financeira e integração atuais; independe do contrato antigo."""

from datetime import date

import pytest


@pytest.mark.parametrize("valor", ["45000", 45000.0])
def test_entrada_monetaria_deve_ser_rejeitada_ou_preservar_o_valor_em_centavos(
    ambiente_api, payload, valor
):
    resposta = ambiente_api.client.post(
        "/api/lancamentos",
        json={**payload, "valor_centavos": valor},
    )

    assert resposta.status_code in (201, 400)

    if resposta.status_code == 201:
        salvo = resposta.get_json()["dados"]

        assert salvo["valor_centavos"] == 45000, (
            "45000 centavos precisam continuar representando R$ 450,00"
        )

        assert (
            ambiente_api.repo.buscar_por_id(salvo["id"]).valor_centavos
            == 45000
        )
    else:
        assert ambiente_api.repo.registros == {}


def test_edicao_nao_pode_multiplicar_o_saldo_por_mudar_o_tipo_json(
    api, cadastrar, payload
):
    original = cadastrar()

    resposta = api.put(
        f"/api/lancamentos/{original['id']}",
        json={**payload, "valor_centavos": "45000"},
    )

    assert resposta.status_code in (200, 400)

    salvo = api.get("/api/lancamentos").get_json()["dados"][0]

    assert salvo["id"] == original["id"]
    assert salvo["valor_centavos"] == original["valor_centavos"]


def test_descricao_nula_nao_e_uma_descricao_informada(
    ambiente_api, payload
):
    resposta = ambiente_api.client.post(
        "/api/lancamentos",
        json={**payload, "descricao": None},
    )

    assert resposta.status_code == 400
    assert ambiente_api.repo.registros == {}


@pytest.mark.parametrize(
    "campo",
    ["descricao", "valor_centavos", "data", "tipo", "categoria_id"],
)
def test_dados_necessarios_ao_lancamento_sao_obrigatorios(
    api, payload, campo
):
    incompleto = {
        chave: valor
        for chave, valor in payload.items()
        if chave != campo
    }

    resposta = api.post("/api/lancamentos", json=incompleto)

    assert resposta.status_code == 400


def test_id_do_cadastro_e_gerado_pelo_backend(api, payload):
    resposta = api.post(
        "/api/lancamentos",
        json={**payload, "id": 999},
    )

    # A API atual ignora o ID extra.
    # Rejeitá-lo também seria uma decisão válida.
    assert resposta.status_code in (201, 400)

    if resposta.status_code == 201:
        assert resposta.get_json()["dados"]["id"] != 999


@pytest.mark.parametrize(
    "metodo,rota",
    [
        ("post", "/api/lancamentos"),
        ("put", "/api/lancamentos/1"),
    ],
)
def test_corpo_incompativel_e_rejeitado_com_erro_compreensivel(
    api, metodo, rota
):
    resposta = getattr(api, metodo)(
        rota,
        data="{}",
        content_type="text/plain",
    )

    assert resposta.status_code in (400, 415)
    assert resposta.get_json()["erro"]["mensagem"]


def test_resumo_sem_mes_usa_mes_atual_conforme_implementacao(api):
    resposta = api.get("/api/resumo")

    assert resposta.status_code == 200

    assert (
        resposta.get_json()["dados"]["mes"]
        == date.today().strftime("%Y-%m")
    )


def test_rota_html_e_arquivos_estaticos_sao_servidos(api):
    resposta = api.get("/")

    assert resposta.status_code == 200
    assert b"<html" in resposta.data

    for rota in ["/static/js/app.js", "/static/css/styles.css"]:
        assert api.get(rota).status_code == 200


def test_html_possui_os_elementos_que_o_js_usa_na_inicializacao(api):
    from html.parser import HTMLParser

    class ExtrairIds(HTMLParser):
        def __init__(self):
            super().__init__()
            self.ids = set()

        def handle_starttag(self, tag, attrs):
            self.ids.update(
                valor
                for nome, valor in attrs
                if nome == "id"
            )

    parser = ExtrairIds()
    parser.feed(api.get("/").get_data(as_text=True))

    esperados = {
        "connection-status",
        "status-dot",
        "current-section",
    }

    assert esperados <= parser.ids, (
        f"Elementos ausentes no HTML: {sorted(esperados - parser.ids)}"
    )