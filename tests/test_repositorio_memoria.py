import unittest
from concurrent.futures import ThreadPoolExecutor

from models import Despesa, ErroValidacaoFinanceira, Receita, RegistroNaoEncontradoErro
from repositories.memoria import RepositorioTransacoesMemoria


class TestRepositorioMemoria(unittest.TestCase):
    def setUp(self):
        self.repo = RepositorioTransacoesMemoria()

    def despesa(self, data="2026-11-05", valor=45000):
        return Despesa("Mercado", valor, data, self.repo.buscar_categoria_por_id(2))

    def test_comeca_vazio_com_seis_categorias(self):
        self.assertEqual(self.repo.listar(), [])
        categorias = self.repo.listar_categorias()
        self.assertEqual([c.id for c in categorias], [1, 2, 3, 4, 5, 6])
        self.assertEqual(categorias[0].tipo_permitido, "receita")
        self.assertEqual(categorias[1].nome, "Alimentação")

    def test_salvar_gera_id_e_retorna_objeto_real_sem_modificar_entrada(self):
        entrada = self.despesa()
        salva = self.repo.salvar(entrada)
        self.assertEqual(salva.id, 1)
        self.assertIsNone(entrada.id)
        self.assertIsInstance(salva, Despesa)
        self.assertEqual(salva.impacto_no_saldo(), -45000)
        self.assertEqual(self.repo.buscar_por_id(1).para_dict(), salva.para_dict())

    def test_ids_nao_sao_reutilizados_apos_exclusao(self):
        self.repo.salvar(self.despesa())
        self.repo.excluir(1)
        self.assertEqual(self.repo.salvar(self.despesa()).id, 2)

    def test_retornos_sao_copias_e_nao_alteram_registros(self):
        salva = self.repo.salvar(self.despesa())
        salva.descricao = "Alterada no retorno"
        encontrada = self.repo.buscar_por_id(1)
        encontrada.categoria.nome = "Alterada na consulta"
        self.repo.listar()[0].valor_centavos = 1
        self.assertEqual(self.repo.buscar_por_id(1).descricao, "Mercado")
        self.assertEqual(self.repo.buscar_por_id(1).categoria.nome, "Alimentação")
        self.assertEqual(self.repo.buscar_por_id(1).valor_centavos, 45000)

    def test_categorias_retornadas_nao_alteram_configuracao(self):
        self.repo.listar_categorias()[0].nome = "Alterada"
        self.repo.buscar_categoria_por_id(1).tipo_permitido = "despesa"
        self.assertEqual(self.repo.buscar_categoria_por_id(1).nome, "Salário")
        self.assertEqual(self.repo.buscar_categoria_por_id(1).tipo_permitido, "receita")

    def test_ordem_por_data_e_id_decrescentes(self):
        self.repo.salvar(self.despesa("2026-11-03"))
        self.repo.salvar(self.despesa("2026-11-05"))
        self.repo.salvar(self.despesa("2026-11-05"))
        self.assertEqual([t.id for t in self.repo.listar()], [3, 2, 1])

    def test_atualizar_preserva_id_e_tipo_pode_mudar_validamente(self):
        salva = self.repo.salvar(self.despesa())
        receita = Receita("Reembolso", 10000, salva.data, self.repo.buscar_categoria_por_id(5), id=salva.id)
        atualizada = self.repo.atualizar(receita)
        self.assertEqual(atualizada.id, 1)
        self.assertIsInstance(self.repo.buscar_por_id(1), Receita)
        self.assertEqual(len(self.repo.listar()), 1)

    def test_registros_inexistentes_nao_alteram_colecao(self):
        inexistente = self.despesa()
        inexistente.id = 99
        for operacao in (lambda: self.repo.buscar_por_id(99), lambda: self.repo.excluir(99), lambda: self.repo.atualizar(inexistente)):
            with self.assertRaises(RegistroNaoEncontradoErro):
                operacao()
        self.assertEqual(self.repo.listar(), [])

    def test_ids_e_categorias_invalidos(self):
        for id_ in [True, None, "1", 0, -1]:
            with self.subTest(id=id_):
                with self.assertRaises(ErroValidacaoFinanceira):
                    self.repo.buscar_por_id(id_)
        for categoria_id in [True, 99, "1", None]:
            with self.subTest(categoria_id=categoria_id):
                with self.assertRaises(ErroValidacaoFinanceira):
                    self.repo.buscar_categoria_por_id(categoria_id)

    def test_cadastro_com_id_rejeitado_sem_consumir_identificador(self):
        transacao = self.despesa()
        transacao.id = 99
        with self.assertRaises(ErroValidacaoFinanceira):
            self.repo.salvar(transacao)
        self.assertEqual(self.repo.salvar(self.despesa()).id, 1)

    def test_instancias_nao_compartilham_dados(self):
        self.repo.salvar(self.despesa())
        self.assertEqual(RepositorioTransacoesMemoria().listar(), [])

    def test_cadastros_simultaneos_recebem_ids_unicos(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            salvas = list(pool.map(lambda _: self.repo.salvar(self.despesa()), range(30)))
        self.assertEqual({t.id for t in salvas}, set(range(1, 31)))
        self.assertEqual(len(self.repo.listar()), 30)
