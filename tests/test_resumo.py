"""Testes dos cálculos financeiros da parte do Igor.

Execute na pasta do projeto com:
    python -m unittest discover -s tests -v
"""

import unittest
from dataclasses import dataclass
from datetime import date

from services.resumo import CalculadoraFinanceira


# Classes simples usadas nos testes para simular os objetos do JV Guerra.
# Elas seguem o contrato: receita retorna impacto positivo e despesa negativo.
@dataclass
class ReceitaFake:
    valor_centavos: int
    categoria: str = "Salário"
    data: date = date(2026, 11, 5)

    def impacto_financeiro(self) -> int:
        return self.valor_centavos


@dataclass
class DespesaFake:
    valor_centavos: int
    categoria: str = "Outros"
    data: date = date(2026, 11, 5)

    def impacto_financeiro(self) -> int:
        return -self.valor_centavos


class TestCalculadoraFinanceira(unittest.TestCase):
    def setUp(self):
        # Cria uma calculadora nova para cada teste, evitando dependência entre eles.
        self.calculadora = CalculadoraFinanceira()

    def test_exemplo_principal(self):
        # Confere os valores do exemplo apresentado na atividade.
        transacoes = [
            ReceitaFake(300_000),
            DespesaFake(90_000, "Moradia"),
            DespesaFake(45_000, "Alimentação"),
            DespesaFake(15_000, "Transporte"),
        ]

        resumo = self.calculadora.gerar_resumo(transacoes, transacoes)

        self.assertEqual(resumo.receitas_centavos, 300_000)
        self.assertEqual(resumo.despesas_centavos, 150_000)
        self.assertEqual(resumo.resultado_periodo_centavos, 150_000)
        self.assertEqual(resumo.saldo_acumulado_centavos, 150_000)

    def test_edicao_de_despesa_atualiza_totais(self):
        # Antes: despesa de R$ 450,00.
        antes = [
            ReceitaFake(300_000),
            DespesaFake(90_000, "Moradia"),
            DespesaFake(45_000, "Alimentação"),
            DespesaFake(15_000, "Transporte"),
        ]
        resumo_antes = self.calculadora.gerar_resumo(antes, antes)

        # Depois da edição: R$ 450,00 passa a R$ 500,00.
        depois = [
            ReceitaFake(300_000),
            DespesaFake(90_000, "Moradia"),
            DespesaFake(50_000, "Alimentação"),
            DespesaFake(15_000, "Transporte"),
        ]
        resumo_depois = self.calculadora.gerar_resumo(depois, depois)

        self.assertEqual(resumo_antes.despesas_centavos, 150_000)
        self.assertEqual(resumo_antes.resultado_periodo_centavos, 150_000)
        self.assertEqual(resumo_depois.despesas_centavos, 155_000)
        self.assertEqual(resumo_depois.resultado_periodo_centavos, 145_000)

    def test_agrupamento_por_categoria(self):
        # Duas despesas da mesma categoria devem ser somadas em um único total.
        transacoes = [
            ReceitaFake(300_000),
            DespesaFake(10_000, "Alimentação"),
            DespesaFake(20_000, "Alimentação"),
            DespesaFake(15_000, "Transporte"),
        ]

        resultado = self.calculadora.agrupar_despesas_por_categoria(transacoes)

        self.assertEqual(
            resultado,
            {"Alimentação": 30_000, "Transporte": 15_000},
        )

    def test_periodo_sem_movimentos_fica_zerado(self):
        # O mês está vazio, mas existe saldo anterior no histórico.
        # Os cartões do mês ficam zerados e o saldo histórico é preservado.
        historico = [ReceitaFake(200_000), DespesaFake(50_000, "Moradia")]

        resumo = self.calculadora.gerar_resumo([], historico)

        self.assertEqual(resumo.receitas_centavos, 0)
        self.assertEqual(resumo.despesas_centavos, 0)
        self.assertEqual(resumo.resultado_periodo_centavos, 0)
        self.assertEqual(resumo.despesas_por_categoria_centavos, {})
        self.assertEqual(resumo.saldo_acumulado_centavos, 150_000)

    def test_historico_considera_meses_anteriores(self):
        mes_anterior = [
            ReceitaFake(250_000, data=date(2026, 10, 10)),
            DespesaFake(80_000, "Moradia", date(2026, 10, 12)),
        ]
        mes_atual = [
            ReceitaFake(300_000, data=date(2026, 11, 5)),
            DespesaFake(100_000, "Alimentação", date(2026, 11, 6)),
        ]

        resumo = self.calculadora.gerar_resumo(
            transacoes_periodo=mes_atual,
            transacoes_ate_data=mes_anterior + mes_atual,
        )

        # Resultado de novembro: 300.000 - 100.000 = 200.000 centavos.
        self.assertEqual(resumo.resultado_periodo_centavos, 200_000)
        # Saldo histórico: (250.000 - 80.000) + (300.000 - 100.000).
        self.assertEqual(resumo.saldo_acumulado_centavos, 370_000)

    def test_exclusao_atualiza_totais(self):
        # Simula a lista antes e depois da remoção de uma despesa.
        com_despesa = [ReceitaFake(100_000), DespesaFake(30_000, "Lazer")]
        sem_despesa = [ReceitaFake(100_000)]

        resumo_com = self.calculadora.gerar_resumo(com_despesa, com_despesa)
        resumo_sem = self.calculadora.gerar_resumo(sem_despesa, sem_despesa)

        self.assertEqual(resumo_com.despesas_centavos, 30_000)
        self.assertEqual(resumo_sem.despesas_centavos, 0)
        self.assertEqual(resumo_sem.resultado_periodo_centavos, 100_000)

    def test_categoria_vazia_recebe_nome_padrao(self):
        transacoes = [DespesaFake(1_000, "  ")]

        resultado = self.calculadora.agrupar_despesas_por_categoria(transacoes)

        self.assertEqual(resultado, {"Sem categoria": 1_000})


if __name__ == "__main__":
    unittest.main()
