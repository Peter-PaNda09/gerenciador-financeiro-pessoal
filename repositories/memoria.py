"""Repositório provisório. Cada instância começa vazia e vive em um processo."""

from copy import deepcopy
from threading import RLock

from models import (
    Categoria,
    Despesa,
    ErroValidacaoFinanceira,
    Receita,
    RegistroNaoEncontradoErro,
    Transacao,
)


class RepositorioTransacoesMemoria:
    """Guarda objetos sem banco; devolve cópias para evitar alterações sem salvar."""

    CATEGORIAS_INICIAIS = (
        (1, "Salário", "receita"),
        (2, "Alimentação", "despesa"),
        (3, "Moradia", "despesa"),
        (4, "Transporte", "despesa"),
        (5, "Outras receitas", "receita"),
        (6, "Outras despesas", "despesa"),
    )

    def __init__(self):
        self._categorias = {
            id_: Categoria(nome=nome, tipo_permitido=tipo, id=id_)
            for id_, nome, tipo in self.CATEGORIAS_INICIAIS
        }
        self._transacoes: dict[int, Transacao] = {}
        self._proximo_id = 1
        self._lock = RLock()

    @staticmethod
    def _validar_id(id_: int):
        if type(id_) is not int or id_ <= 0:
            raise ErroValidacaoFinanceira("Informe um ID inteiro positivo.", campo="id")

    def listar_categorias(self) -> list[Categoria]:
        with self._lock:
            return deepcopy(list(self._categorias.values()))

    def buscar_categoria_por_id(self, categoria_id: int) -> Categoria:
        if type(categoria_id) is not int or categoria_id not in self._categorias:
            raise ErroValidacaoFinanceira("Selecione uma categoria existente.", campo="categoria_id")
        with self._lock:
            return deepcopy(self._categorias[categoria_id])

    def _copiar_validada(self, transacao: Transacao, id_: int) -> Transacao:
        if not isinstance(transacao, (Receita, Despesa)):
            raise ErroValidacaoFinanceira("Informe um objeto Receita ou Despesa.")
        categoria = self.buscar_categoria_por_id(transacao.categoria.id)
        classe = Receita if transacao.tipo == "receita" else Despesa
        return classe(
            descricao=transacao.descricao,
            valor_centavos=transacao.valor_centavos,
            data=transacao.data,
            categoria=categoria,
            id=id_,
        )

    def salvar(self, transacao: Transacao) -> Transacao:
        """Gera o ID e retorna o registro salvo; não modifica o objeto recebido."""
        with self._lock:
            if not isinstance(transacao, Transacao):
                raise ErroValidacaoFinanceira("Informe uma transação válida.")
            if transacao.id is not None:
                raise ErroValidacaoFinanceira("O ID do cadastro é gerado pelo repositório.", campo="id")
            salva = self._copiar_validada(transacao, self._proximo_id)
            self._transacoes[salva.id] = salva
            self._proximo_id += 1
            return deepcopy(salva)

    def listar(self) -> list[Transacao]:
        """Mais recentes primeiro; em datas iguais, maior ID primeiro."""
        with self._lock:
            ordenadas = sorted(self._transacoes.values(), key=lambda t: (t.data, t.id), reverse=True)
            return deepcopy(ordenadas)

    def buscar_por_id(self, id_: int) -> Transacao:
        self._validar_id(id_)
        with self._lock:
            if id_ not in self._transacoes:
                raise RegistroNaoEncontradoErro("Lançamento não encontrado.")
            return deepcopy(self._transacoes[id_])

    def atualizar(self, transacao: Transacao) -> Transacao:
        """Substitui um objeto completo e validado, preservando seu ID."""
        with self._lock:
            if not isinstance(transacao, Transacao):
                raise ErroValidacaoFinanceira("Informe uma transação válida.")
            self.buscar_por_id(transacao.id)
            atualizada = self._copiar_validada(transacao, transacao.id)
            self._transacoes[atualizada.id] = atualizada
            return deepcopy(atualizada)

    def excluir(self, id_: int) -> None:
        with self._lock:
            self.buscar_por_id(id_)
            del self._transacoes[id_]
