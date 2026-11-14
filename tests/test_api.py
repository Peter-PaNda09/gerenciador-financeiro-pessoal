import unittest
from datetime import date, timedelta
from unittest.mock import patch

from app import CAMPOS_LANCAMENTO, create_app


class TestApiLancamentos(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.repo = self.app.extensions["repositorio_transacoes"]
        self.payload = {"descricao": "Mercado", "valor_centavos": 45000, "data": "2026-11-05", "tipo": "despesa", "categoria_id": 2}

    def cadastrar(self, **alteracoes):
        return self.client.post("/api/lancamentos", json={**self.payload, **alteracoes})

    def assert_erro(self, resposta, status, codigo, campo=None):
        self.assertEqual(resposta.status_code, status)
        erro = resposta.get_json()["erro"]
        self.assertEqual(set(erro), {"codigo", "mensagem", "campos"})
        self.assertEqual(erro["codigo"], codigo)
        self.assertIsInstance(erro["mensagem"], str)
        self.assertIsInstance(erro["campos"], dict)
        if campo:
            self.assertIn(campo, erro["campos"])

    def test_lista_inicial_vazia(self):
        resposta = self.client.get("/api/lancamentos")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json(), {"dados": [], "meta": {"quantidade": 0}})

    def test_categorias_com_ids_estaveis_e_campos_publicos(self):
        resposta = self.client.get("/api/categorias")
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.get_json()
        self.assertEqual(corpo["meta"]["quantidade"], 6)
        self.assertEqual(corpo["dados"][0], {"id": 1, "nome": "Salário", "tipo": "receita"})
        self.assertTrue(all(set(c) == {"id", "nome", "tipo"} for c in corpo["dados"]))
        self.assert_erro(self.client.get("/api/categorias?tipo=receita"), 400, "VALIDACAO", "tipo")

    def test_cadastro_e_consulta_mesmo_registro_em_centavos(self):
        resposta = self.cadastrar(descricao="  Mercado  ")
        self.assertEqual(resposta.status_code, 201)
        dados = resposta.get_json()["dados"]
        self.assertEqual(dados, {"id": 1, **self.payload})
        self.assertEqual(set(dados), set(CAMPOS_LANCAMENTO))
        consulta = self.client.get("/api/lancamentos").get_json()
        self.assertEqual(consulta, {"dados": [dados], "meta": {"quantidade": 1}})

    def test_receita_usa_objeto_real_do_dominio(self):
        resposta = self.cadastrar(descricao="Salário", tipo="receita", categoria_id=1, valor_centavos=300000)
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(self.repo.buscar_por_id(1).impacto_no_saldo(), 300000)

    def test_tipos_json_e_valores_invalidos_nao_gravam(self):
        casos = {
            "valor_centavos": [True, "45000", 45000.0, 0, -1, None],
            "categoria_id": [True, "2", 2.0, 0, 99, None],
            "descricao": ["", "   ", "x" * 121, 123, None],
            "tipo": ["DESPESA", "Despesa", " despesa", "transferencia", None],
            "data": ["2026-02-30", "2026-1-05", "05/11/2026", "2099-12-31", None],
        }
        for campo, valores in casos.items():
            for valor in valores:
                with self.subTest(campo=campo, valor=valor):
                    self.assert_erro(self.cadastrar(**{campo: valor}), 400, "VALIDACAO", campo)
        self.assertEqual(self.repo.listar(), [])
        self.assertEqual(self.cadastrar().get_json()["dados"]["id"], 1)

    def test_campos_ausentes_e_desconhecidos(self):
        for campo in self.payload:
            incompleto = {k: v for k, v in self.payload.items() if k != campo}
            with self.subTest(campo=campo):
                self.assert_erro(self.client.post("/api/lancamentos", json=incompleto), 400, "VALIDACAO", campo)
        for campo, valor in [("id", 10), ("valor", 450), ("categoria_nome", "Alimentação")]:
            self.assert_erro(self.cadastrar(**{campo: valor}), 400, "VALIDACAO", campo)
        self.assertEqual(self.repo.listar(), [])

    def test_categoria_incompativel_nao_grava(self):
        self.assert_erro(self.cadastrar(categoria_id=1), 400, "VALIDACAO", "categoria_id")
        self.assertEqual(self.repo.listar(), [])

    def test_json_invalido_e_corpo_com_tipo_errado(self):
        self.assert_erro(self.client.post("/api/lancamentos", data="{", content_type="application/json"), 400, "JSON_INVALIDO")
        self.assert_erro(self.client.post("/api/lancamentos", data="", content_type="application/json"), 400, "JSON_INVALIDO")
        for corpo in ["null", "[]", '"texto"', "1", "true"]:
            with self.subTest(corpo=corpo):
                self.assert_erro(self.client.post("/api/lancamentos", data=corpo, content_type="application/json"), 400, "VALIDACAO")
        self.assertEqual(self.repo.listar(), [])

    def test_cabecalho_json_obrigatorio(self):
        for content_type in [None, "text/plain", "application/x-www-form-urlencoded"]:
            with self.subTest(content_type=content_type):
                self.assert_erro(self.client.post("/api/lancamentos", data="{}", content_type=content_type), 415, "TIPO_CONTEUDO_INVALIDO")

    def test_data_no_fuso_do_contrato(self):
        from models import data_atual_sao_paulo
        hoje = data_atual_sao_paulo()
        self.assertEqual(self.cadastrar(data=hoje.isoformat()).status_code, 201)
        self.assert_erro(self.cadastrar(data=(hoje + timedelta(days=1)).isoformat()), 400, "VALIDACAO", "data")
        with patch("models.datetime") as relogio:
            relogio.now.return_value.date.return_value = date(2026, 11, 14)
            self.assertEqual(data_atual_sao_paulo(), date(2026, 11, 14))
            self.assertEqual(str(relogio.now.call_args.args[0]), "America/Sao_Paulo")

    def test_filtros_combinados_e_ordenacao(self):
        self.cadastrar(descricao="Aluguel", categoria_id=3, data="2026-11-03", valor_centavos=90000)
        self.cadastrar(descricao="Mercado antigo", data="2026-10-05")
        self.cadastrar(descricao="Mercado novembro")
        self.cadastrar(descricao="Salário", tipo="receita", categoria_id=1)
        todos = self.client.get("/api/lancamentos").get_json()
        self.assertEqual([t["id"] for t in todos["dados"]], [4, 3, 1, 2])
        resposta = self.client.get("/api/lancamentos?mes=2026-11&tipo=despesa&categoria_id=2&busca=MERCADO")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual([t["id"] for t in resposta.get_json()["dados"]], [3])
        self.assertEqual(resposta.get_json()["meta"]["quantidade"], 1)
        self.assertEqual(len(self.repo.listar()), 4)

    def test_filtros_validos_sem_resultados(self):
        self.cadastrar()
        resposta = self.client.get("/api/lancamentos?tipo=receita&categoria_id=2")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json(), {"dados": [], "meta": {"quantidade": 0}})

    def test_busca_remove_espacos_e_preserva_acentos(self):
        self.cadastrar(descricao="Ônibus", categoria_id=4)
        self.assertEqual(self.client.get("/api/lancamentos", query_string={"busca": " ÔNIBUS "}).get_json()["meta"]["quantidade"], 1)
        self.assertEqual(self.client.get("/api/lancamentos?busca=onibus").get_json()["meta"]["quantidade"], 0)

    def test_filtros_invalidos_desconhecidos_ou_repetidos(self):
        consultas = ["mes=2026-13", "mes=2026-1", "mes=0000-01", "mes=", "mes=2026-11&mes=2026-10", "tipo=todos", "tipo=RECEITA", "categoria_id=99", "categoria_id=2.0", "categoria_id=-1", "busca=", "busca=%20", "data_inicio=2026-11-01", "limite=10"]
        for consulta in consultas:
            with self.subTest(consulta=consulta):
                self.assert_erro(self.client.get("/api/lancamentos?" + consulta), 400, "VALIDACAO")

    def test_novo_app_perde_lancamentos_como_documentado(self):
        self.cadastrar()
        self.assertEqual(create_app().test_client().get("/api/lancamentos").get_json()["dados"], [])

    def test_rotas_futuras_nao_estao_implementadas(self):
        self.assert_erro(self.client.get("/api/resumo?mes=2026-11"), 404, "NAO_ENCONTRADO")
        self.assert_erro(self.client.get("/api/exportar"), 404, "NAO_ENCONTRADO")

    def test_metodo_indisponivel_mantem_envelope_json(self):
        self.assert_erro(self.client.delete("/api/lancamentos"), 405, "METODO_NAO_PERMITIDO")

    def test_erro_inesperado_nao_expoe_detalhes(self):
        with patch.object(self.repo, "listar", side_effect=RuntimeError("detalhe interno de teste")):
            with self.assertLogs(self.app.logger, level="ERROR"):
                resposta = self.client.get("/api/lancamentos")
        self.assert_erro(resposta, 500, "ERRO_INTERNO")
        self.assertNotIn("detalhe interno", resposta.get_data(as_text=True))
