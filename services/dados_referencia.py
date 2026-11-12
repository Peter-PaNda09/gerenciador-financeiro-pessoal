"""Dados fictícios para validar os cálculos do resumo financeiro."""

from dataclasses import dataclass
from datetime import date


@dataclass
class ReceitaExemplo:
    valor_centavos: int
    categoria: str = "Salário"
    data: date = date(2026, 11, 5)

    def impacto_financeiro(self) -> int:
        # Receitas aumentam o saldo e, por isso, retornam valor positivo.
        return self.valor_centavos


@dataclass
class DespesaExemplo:
    valor_centavos: int
    categoria: str
    data: date = date(2026, 11, 5)

    def impacto_financeiro(self) -> int:
        # Despesas diminuem o saldo e retornam valor negativo.
        return -self.valor_centavos


def criar_dados_exemplo():
    """Cria os valores do enunciado: R$ 3.000,00 de receita e R$ 1.500,00 em despesas."""
    return [
        ReceitaExemplo(300_000),
        DespesaExemplo(90_000, "Moradia"),
        DespesaExemplo(45_000, "Alimentação"),
        DespesaExemplo(15_000, "Transporte"),
    ]
