"""Substituto do banco SOMENTE para testes; não é persistência da aplicação."""

from copy import deepcopy

from models import Categoria, Receita, Despesa, ErroValidacaoFinanceira, RegistroNaoEncontradoErro


class RepositorioFake:
    """Uma base independente por teste, com IDs fictícios deliberadamente diferentes."""

    def __init__(self):
        self.categorias = {
            11: Categoria("Salário", "receita", id=11),
            22: Categoria("Alimentação", "despesa", id=22),
            33: Categoria("Moradia", "despesa", id=33),
            44: Categoria("Transporte", "despesa", id=44),
        }
        self.registros = {}
        self.proximo_id = 1

    def listar_categorias(self, tipo=None):
        return [deepcopy(c) for c in self.categorias.values() if tipo is None or c.tipo == tipo]

    def buscar_categoria_por_id(self, categoria_id):
        if categoria_id not in self.categorias:
            raise ErroValidacaoFinanceira("Categoria inexistente.", campo="categoria_id")
        return deepcopy(self.categorias[categoria_id])

    @staticmethod
    def _copiar(transacao, id_):
        classe = Receita if transacao.tipo == "receita" else Despesa
        return classe(transacao.descricao, transacao.valor_centavos, transacao.data,
                      deepcopy(transacao.categoria), id=id_)

    def salvar(self, transacao):
        salva = self._copiar(transacao, self.proximo_id)
        self.proximo_id += 1
        self.registros[salva.id] = salva
        return deepcopy(salva)

    def listar_todos(self):
        return sorted(deepcopy(list(self.registros.values())),
                      key=lambda t: (t.data, t.id), reverse=True)

    def buscar_por_id(self, id_):
        if id_ not in self.registros:
            raise RegistroNaoEncontradoErro("Lançamento não encontrado.")
        return deepcopy(self.registros[id_])

    def atualizar(self, transacao):
        self.buscar_por_id(transacao.id)
        self.registros[transacao.id] = self._copiar(transacao, transacao.id)
        return self.buscar_por_id(transacao.id)

    def excluir(self, id_):
        self.buscar_por_id(id_)
        del self.registros[id_]
