"""Persistência local em arquivo SQLite, usando a mesma interface da memória."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3

from models import (
    Categoria,
    Despesa,
    ErroValidacaoFinanceira,
    Receita,
    RegistroNaoEncontradoErro,
    Transacao,
)
from repositories.categorias import CATEGORIAS_INICIAIS


class RepositorioTransacoesSQLite:
    """Abre e fecha uma conexão por operação; não compartilha conexões entre threads."""

    MAX_INTEIRO = 2**63 - 1
    CONSULTA = """
        SELECT l.id, l.descricao, l.valor_centavos, l.data, l.tipo,
               c.id AS categoria_id, c.nome AS categoria_nome, c.tipo_permitido
          FROM lancamentos AS l
          JOIN categorias AS c ON c.id = l.categoria_id
    """

    def __init__(self, caminho_banco):
        if str(caminho_banco) == ":memory:":
            raise ValueError("Use um caminho de arquivo para o repositório persistente.")
        self.caminho_banco = Path(caminho_banco).expanduser().resolve()
        self.caminho_banco.parent.mkdir(parents=True, exist_ok=True)
        self._inicializar_banco()

    @contextmanager
    def _conexao(self):
        conexao = sqlite3.connect(str(self.caminho_banco), timeout=10)
        conexao.row_factory = sqlite3.Row
        conexao.execute("PRAGMA foreign_keys = ON")
        try:
            # Confirma a transação ao terminar ou desfaz em caso de erro.
            with conexao:
                yield conexao
        finally:
            conexao.close()

    def _inicializar_banco(self):
        with self._conexao() as conexao:
            conexao.executescript("""
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY CHECK (id > 0),
                    nome TEXT NOT NULL UNIQUE,
                    tipo_permitido TEXT NOT NULL
                        CHECK (tipo_permitido IN ('receita', 'despesa')),
                    UNIQUE (id, tipo_permitido)
                );
                CREATE TABLE IF NOT EXISTS lancamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL
                        CHECK (length(trim(descricao)) BETWEEN 1 AND 120),
                    valor_centavos INTEGER NOT NULL
                        CHECK (typeof(valor_centavos) = 'integer' AND valor_centavos > 0),
                    data TEXT NOT NULL
                        CHECK (data GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
                    tipo TEXT NOT NULL CHECK (tipo IN ('receita', 'despesa')),
                    categoria_id INTEGER NOT NULL,
                    FOREIGN KEY (categoria_id, tipo)
                        REFERENCES categorias(id, tipo_permitido) ON DELETE RESTRICT
                );
                CREATE INDEX IF NOT EXISTS idx_lancamentos_data_id
                    ON lancamentos(data DESC, id DESC);
            """)
            conexao.executemany(
                "INSERT OR IGNORE INTO categorias (id, nome, tipo_permitido) VALUES (?, ?, ?)",
                CATEGORIAS_INICIAIS,
            )
            existentes = conexao.execute(
                "SELECT id, nome, tipo_permitido FROM categorias ORDER BY id"
            ).fetchall()
            if [tuple(c) for c in existentes] != list(CATEGORIAS_INICIAIS):
                raise RuntimeError(
                    "O banco possui categorias diferentes do contrato. "
                    "Confira o arquivo configurado; os registros existentes não foram apagados."
                )

    @classmethod
    def _validar_id(cls, id_):
        if type(id_) is not int or not 0 < id_ <= cls.MAX_INTEIRO:
            raise ErroValidacaoFinanceira("Informe um ID inteiro positivo válido.", campo="id")

    @staticmethod
    def _categoria(linha):
        return Categoria(linha["nome"], linha["tipo_permitido"], id=linha["id"])

    @staticmethod
    def _transacao(linha):
        categoria = Categoria(
            linha["categoria_nome"], linha["tipo_permitido"], id=linha["categoria_id"]
        )
        classe = Receita if linha["tipo"] == "receita" else Despesa
        return classe(
            linha["descricao"], linha["valor_centavos"], linha["data"], categoria, id=linha["id"]
        )

    def listar_categorias(self):
        with self._conexao() as conexao:
            linhas = conexao.execute("SELECT * FROM categorias ORDER BY id").fetchall()
            return [self._categoria(linha) for linha in linhas]

    def buscar_categoria_por_id(self, categoria_id):
        if type(categoria_id) is not int or not 0 < categoria_id <= self.MAX_INTEIRO:
            raise ErroValidacaoFinanceira("Selecione uma categoria existente.", campo="categoria_id")
        with self._conexao() as conexao:
            linha = conexao.execute("SELECT * FROM categorias WHERE id = ?", (categoria_id,)).fetchone()
            if linha is None:
                raise ErroValidacaoFinanceira("Selecione uma categoria existente.", campo="categoria_id")
            return self._categoria(linha)

    def _copiar_validada(self, transacao, id_):
        if not isinstance(transacao, (Receita, Despesa)):
            raise ErroValidacaoFinanceira("Informe um objeto Receita ou Despesa.")
        if transacao.valor_centavos > self.MAX_INTEIRO:
            raise ErroValidacaoFinanceira(
                "O valor ultrapassa o limite de centavos suportado pelo banco.", campo="valor_centavos"
            )
        categoria = self.buscar_categoria_por_id(transacao.categoria.id)
        classe = Receita if transacao.tipo == "receita" else Despesa
        return classe(
            transacao.descricao, transacao.valor_centavos, transacao.data, categoria, id=id_
        )

    @staticmethod
    def _valores(transacao):
        return (
            transacao.descricao, transacao.valor_centavos, transacao.data,
            transacao.tipo, transacao.categoria.id,
        )

    def salvar(self, transacao):
        if not isinstance(transacao, Transacao):
            raise ErroValidacaoFinanceira("Informe uma transação válida.")
        if transacao.id is not None:
            raise ErroValidacaoFinanceira("O ID do cadastro é gerado pelo repositório.", campo="id")
        salva = self._copiar_validada(transacao, None)
        with self._conexao() as conexao:
            cursor = conexao.execute(
                "INSERT INTO lancamentos (descricao, valor_centavos, data, tipo, categoria_id) "
                "VALUES (?, ?, ?, ?, ?)",
                self._valores(salva),
            )
            salva.id = cursor.lastrowid
        return salva

    def listar(self):
        with self._conexao() as conexao:
            linhas = conexao.execute(self.CONSULTA + " ORDER BY l.data DESC, l.id DESC").fetchall()
            return [self._transacao(linha) for linha in linhas]

    def buscar_por_id(self, id_):
        self._validar_id(id_)
        with self._conexao() as conexao:
            linha = conexao.execute(self.CONSULTA + " WHERE l.id = ?", (id_,)).fetchone()
            if linha is None:
                raise RegistroNaoEncontradoErro("Lançamento não encontrado.")
            return self._transacao(linha)

    def atualizar(self, transacao):
        if not isinstance(transacao, Transacao):
            raise ErroValidacaoFinanceira("Informe uma transação válida.")
        self.buscar_por_id(transacao.id)
        atualizada = self._copiar_validada(transacao, transacao.id)
        with self._conexao() as conexao:
            cursor = conexao.execute(
                "UPDATE lancamentos SET descricao = ?, valor_centavos = ?, data = ?, tipo = ?, "
                "categoria_id = ? WHERE id = ?",
                (*self._valores(atualizada), atualizada.id),
            )
            if cursor.rowcount == 0:
                raise RegistroNaoEncontradoErro("Lançamento não encontrado.")
        return atualizada

    def excluir(self, id_):
        self._validar_id(id_)
        with self._conexao() as conexao:
            cursor = conexao.execute("DELETE FROM lancamentos WHERE id = ?", (id_,))
            if cursor.rowcount == 0:
                raise RegistroNaoEncontradoErro("Lançamento não encontrado.")
