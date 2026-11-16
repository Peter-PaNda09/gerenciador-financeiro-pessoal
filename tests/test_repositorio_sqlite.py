from pathlib import Path
from contextlib import closing
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from models import ErroValidacaoFinanceira
from repositories.sqlite import RepositorioTransacoesSQLite
from tests.test_repositorio_memoria import ContratoRepositorio


class TestRepositorioSQLite(ContratoRepositorio, unittest.TestCase):
    def setUp(self):
        self.pasta = TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.caminho = Path(self.pasta.name) / "dados" / "teste.sqlite3"
        self.repo = RepositorioTransacoesSQLite(self.caminho)

    def criar_repositorio_vazio(self):
        return RepositorioTransacoesSQLite(Path(self.pasta.name) / "outro.sqlite3")

    def test_reabrir_banco_preserva_registros_categorias_e_sequencia(self):
        self.repo.salvar(self.despesa())
        for _ in range(3):
            nova = RepositorioTransacoesSQLite(self.caminho)
            self.assertEqual(len(nova.listar_categorias()), 6)
            self.assertEqual(nova.buscar_por_id(1).valor_centavos, 45000)
        salva = nova.salvar(self.despesa())
        self.assertEqual(salva.id, 2)
        self.assertEqual(len(nova.listar()), 2)

    def test_edicao_e_exclusao_tambem_persistem(self):
        salva = self.repo.salvar(self.despesa())
        salva.valor_centavos = 50000
        self.repo.atualizar(salva)
        nova = RepositorioTransacoesSQLite(self.caminho)
        self.assertEqual(nova.buscar_por_id(1).valor_centavos, 50000)
        nova.excluir(1)
        self.assertEqual(RepositorioTransacoesSQLite(self.caminho).listar(), [])

    def test_falha_de_validacao_na_edicao_preserva_original(self):
        salva = self.repo.salvar(self.despesa())
        salva.categoria.id = 999
        with self.assertRaises(ErroValidacaoFinanceira):
            self.repo.atualizar(salva)
        self.assertEqual(self.repo.buscar_por_id(1).valor_centavos, 45000)
        self.assertEqual(self.repo.buscar_por_id(1).categoria.id, 2)

    def test_descricao_com_aspas_e_sql_e_apenas_texto(self):
        entrada = self.despesa()
        entrada.descricao = "Mercado'); DROP TABLE lancamentos; --"
        salva = self.repo.salvar(entrada)
        self.assertEqual(self.repo.buscar_por_id(salva.id).descricao, entrada.descricao)
        self.assertEqual(len(self.repo.listar()), 1)

    def test_restricoes_do_banco_impedem_tipo_incompativel_e_valor_negativo(self):
        for tipo, categoria_id, valor in [("despesa", 1, 100), ("despesa", 2, -1)]:
            with self.subTest(tipo=tipo, categoria_id=categoria_id, valor=valor):
                with closing(sqlite3.connect(self.caminho)) as conexao:
                    conexao.execute("PRAGMA foreign_keys = ON")
                    with self.assertRaises(sqlite3.IntegrityError):
                        with conexao:
                            conexao.execute(
                                "INSERT INTO lancamentos (descricao, valor_centavos, data, tipo, categoria_id) "
                                "VALUES (?, ?, ?, ?, ?)",
                                ("Inválida", valor, "2026-11-05", tipo, categoria_id),
                            )
        self.assertEqual(self.repo.listar(), [])

    def test_categorias_modificadas_nao_sao_silenciosamente_sobrescritas(self):
        self.repo.salvar(self.despesa())
        with closing(sqlite3.connect(self.caminho)) as conexao:
            with conexao:
                conexao.execute("UPDATE categorias SET nome = ? WHERE id = ?", ("Outra", 2))
        with self.assertRaisesRegex(RuntimeError, "categorias diferentes"):
            RepositorioTransacoesSQLite(self.caminho)
        with closing(sqlite3.connect(self.caminho)) as conexao:
            self.assertEqual(conexao.execute("SELECT count(*) FROM lancamentos").fetchone()[0], 1)
            self.assertEqual(conexao.execute("SELECT nome FROM categorias WHERE id=2").fetchone()[0], "Outra")

    def test_rejeita_valor_fora_do_limite_sem_gravar(self):
        entrada = self.despesa(valor=2**63)
        with self.assertRaises(ErroValidacaoFinanceira):
            self.repo.salvar(entrada)
        self.assertEqual(self.repo.listar(), [])

    def test_rejeita_sqlite_em_memoria_nesta_classe(self):
        with self.assertRaises(ValueError):
            RepositorioTransacoesSQLite(":memory:")
