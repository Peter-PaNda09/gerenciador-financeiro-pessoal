"""Cálculos financeiros para o painel do sistema.

Contrato esperado para cada transação:
- possuir o método impacto_financeiro();
- retornar um inteiro em centavos: positivo para Receita e negativo para Despesa;
- possuir o atributo categoria (usado no agrupamento de despesas).

A filtragem por mês/data é responsabilidade do serviço (parte do Marcos).
Esta classe recebe as transações já filtradas e não conhece a interface.
"""

from dataclasses import dataclass
from typing import Iterable, Protocol


class TransacaoFinanceira(Protocol):
    """Interface mínima esperada das classes Receita e Despesa."""

    categoria: str

    def impacto_financeiro(self) -> int:
        """Retorna o impacto no saldo, em centavos e com sinal."""
        ...


@dataclass(frozen=True)
class ResumoFinanceiro:
    """Valores do resumo em centavos para evitar erros de ponto flutuante."""

    receitas_centavos: int
    despesas_centavos: int
    resultado_periodo_centavos: int
    saldo_acumulado_centavos: int
    despesas_por_categoria_centavos: dict[str, int]

    def para_dict(self) -> dict:
        """Devolve os campos em formato simples, pronto para a camada da API."""
        return {
            "receitas_centavos": self.receitas_centavos,
            "despesas_centavos": self.despesas_centavos,
            "resultado_periodo_centavos": self.resultado_periodo_centavos,
            "saldo_acumulado_centavos": self.saldo_acumulado_centavos,
            "despesas_por_categoria_centavos": dict(
                self.despesas_por_categoria_centavos
            ),
        }


class CalculadoraFinanceira:
    """Calcula indicadores a partir de objetos Receita e Despesa."""

    @staticmethod
    def _impacto(transacao: TransacaoFinanceira) -> int:
        """Lê o impacto definido pelo próprio objeto e valida o retorno."""
        metodo = getattr(transacao, "impacto_financeiro", None)
        if not callable(metodo):
            raise TypeError(
                "A transação precisa implementar impacto_financeiro()."
            )

        impacto = metodo()
        # bool é subclasse de int em Python, mas não representa um valor monetário.
        if isinstance(impacto, bool) or not isinstance(impacto, int):
            raise TypeError(
                "impacto_financeiro() deve retornar um número inteiro de centavos."
            )
        return impacto

    @staticmethod
    def _categoria(transacao: TransacaoFinanceira) -> str:
        """Obtém a categoria; usa 'Sem categoria' quando estiver vazia."""
        categoria = getattr(transacao, "categoria", None)
        if categoria is None or not str(categoria).strip():
            return "Sem categoria"
        return str(categoria).strip()

    def calcular_totais(
        self, transacoes: Iterable[TransacaoFinanceira]
    ) -> tuple[int, int, int]:
        """Retorna (receitas, despesas, resultado), todos em centavos.

        Receitas são impactos positivos. Despesas são impactos negativos,
        mas o total de despesas é apresentado como valor positivo.
        Resultado = receitas - despesas.
        """
        # Os acumuladores começam em zero, então um período sem movimentos
        # já produz um resumo válido, sem precisar de tratamento especial.
        receitas = 0
        despesas = 0

        for transacao in transacoes:
            # O próprio objeto decide seu impacto: positivo para receita
            # e negativo para despesa. A calculadora apenas soma os valores.
            impacto = self._impacto(transacao)
            if impacto > 0:
                receitas += impacto
            elif impacto < 0:
                # O cartão de despesas mostra um total positivo, por isso
                # usamos o valor absoluto do impacto negativo.
                despesas += abs(impacto)

        # O resultado do período considera somente as transações recebidas.
        resultado = receitas - despesas
        return receitas, despesas, resultado

    def calcular_saldo_acumulado(
        self, transacoes_ate_data: Iterable[TransacaoFinanceira]
    ) -> int:
        """Soma o impacto de todos os registros até a data escolhida.

        O serviço deve passar todas as transações históricas até a data,
        e não apenas as transações do mês selecionado.
        """
        # Diferentemente do resultado mensal, o saldo usa todo o histórico
        # até a data escolhida, incluindo os meses anteriores.
        return sum(self._impacto(transacao) for transacao in transacoes_ate_data)

    def agrupar_despesas_por_categoria(
        self, transacoes: Iterable[TransacaoFinanceira]
    ) -> dict[str, int]:
        """Agrupa somente despesas por categoria, em centavos positivos."""
        # Cada chave representa uma categoria e guarda a soma das despesas
        # daquela categoria. Receitas não entram neste agrupamento.
        totais: dict[str, int] = {}

        for transacao in transacoes:
            impacto = self._impacto(transacao)
            if impacto < 0:
                categoria = self._categoria(transacao)
                # Se a categoria ainda não existir, começa em zero.
                totais[categoria] = totais.get(categoria, 0) + abs(impacto)

        # A ordenação deixa a resposta previsível para testes e para a API.
        return dict(sorted(totais.items()))

    def gerar_resumo(
        self,
        transacoes_periodo: Iterable[TransacaoFinanceira],
        transacoes_ate_data: Iterable[TransacaoFinanceira],
    ) -> ResumoFinanceiro:
        """Monta o resumo do período e o saldo histórico até a data.

        - transacoes_periodo: registros do mês/período selecionado.
        - transacoes_ate_data: todos os registros desde o início até a data.

        Listas vazias retornam valores zerados, sem gerar erro.
        """
        # Convertemos para lista para percorrer os registros mais de uma vez,
        # inclusive quando o serviço envia um gerador em vez de uma lista.
        periodo = list(transacoes_periodo)
        historico = list(transacoes_ate_data)

        # Indicadores do período usam apenas o mês selecionado.
        receitas, despesas, resultado = self.calcular_totais(periodo)
        despesas_por_categoria = self.agrupar_despesas_por_categoria(periodo)
        # O saldo acumulado usa o histórico completo até a data, não somente
        # o mês selecionado. Assim, os dois indicadores não se confundem.
        saldo_acumulado = self.calcular_saldo_acumulado(historico)

        # Reunimos os valores em um objeto para a camada da API utilizar.
        return ResumoFinanceiro(
            receitas_centavos=receitas,
            despesas_centavos=despesas,
            resultado_periodo_centavos=resultado,
            saldo_acumulado_centavos=saldo_acumulado,
            despesas_por_categoria_centavos=despesas_por_categoria,
        )
