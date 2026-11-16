import unittest
from models import (
    Categoria,
    Transacao,
    Receita,
    Despesa,
    ErroValidacaoFinanceira,
)


class TestesClassesDominioFinanceiro(unittest.TestCase):
    def setUp(self):
        self.cat_salario = Categoria(nome="Salário", tipo_permitido="receita", id=1)
        self.cat_alimentacao = Categoria(nome="Alimentação", tipo_permitido="despesa", id=2)

    def test_1_construcao_valida_receita_e_despesa(self):
        """Critério 1: Receita e Despesa podem ser instanciadas e utilizadas."""
        receita = Receita(
            descricao="Salário Mensal",
            valor_centavos=300000,
            data="2026-11-05",
            categoria=self.cat_salario,
            id=10,
        )
        despesa = Despesa(
            descricao="Mercado",
            valor_centavos=45000,
            data="2026-11-05",
            categoria=self.cat_alimentacao,
            id=11,
        )

        self.assertEqual(receita.descricao, "Salário Mensal")
        self.assertEqual(receita.valor_centavos, 300000)
        self.assertEqual(receita.tipo, "receita")
        self.assertEqual(despesa.descricao, "Mercado")
        self.assertEqual(despesa.valor_centavos, 45000)
        self.assertEqual(despesa.tipo, "despesa")

    def test_2_classe_transacao_nao_pode_ser_instanciada_diretamente(self):
        """Verifica se Transacao é realmente abstrata (ABC)."""
        with self.assertRaises(TypeError):
            Transacao(  # type: ignore
                descricao="Genérica",
                valor_centavos=1000,
                data="2026-11-05",
                categoria=self.cat_salario,
            )

    def test_3_validacoes_na_construcao_rejeitam_dados_invalidos(self):
        """Critério 2: Objetos com dados inválidos são rejeitados com erros compreensíveis."""
        # Descrição vazia
        with self.assertRaises(ErroValidacaoFinanceira):
            Receita(
                descricao="   ",
                valor_centavos=10000,
                data="2026-11-05",
                categoria=self.cat_salario,
            )

        # Valor igual a zero ou negativo
        for valor_invalido in (0, -1, -45000):
            with self.assertRaises(ErroValidacaoFinanceira):
                Despesa(
                    descricao="Mercado",
                    valor_centavos=valor_invalido,
                    data="2026-11-05",
                    categoria=self.cat_alimentacao,
                )

        # Data futura ou inválida
        with self.assertRaises(ErroValidacaoFinanceira):
            Despesa(
                descricao="Mercado Futuro",
                valor_centavos=10000,
                data="2099-12-31",
                categoria=self.cat_alimentacao,
            )

        # Categoria incompatível com o tipo (Receita com categoria de Despesa)
        with self.assertRaises(ErroValidacaoFinanceira):
            Receita(
                descricao="Salário com categoria errada",
                valor_centavos=10000,
                data="2026-11-05",
                categoria=self.cat_alimentacao,
            )

    def test_4_encapsulamento_impede_alteracoes_invalidas(self):
        """Atividade 4: Encapsulamento impede alterações que deixem objetos inválidos."""
        despesa = Despesa(
            descricao="Mercado",
            valor_centavos=45000,
            data="2026-11-05",
            categoria=self.cat_alimentacao,
        )

        # Tentar alterar descrição para vazio após o objeto já criado
        with self.assertRaises(ErroValidacaoFinanceira):
            despesa.descricao = ""

        # Tentar alterar valor para negativo após o objeto já criado
        with self.assertRaises(ErroValidacaoFinanceira):
            despesa.valor_centavos = -500

        # Tentar trocar categoria para uma de receita
        with self.assertRaises(ErroValidacaoFinanceira):
            despesa.categoria = self.cat_salario

        # Garante que o objeto manteve seus valores originais intactos
        self.assertEqual(despesa.descricao, "Mercado")
        self.assertEqual(despesa.valor_centavos, 45000)
        self.assertEqual(despesa.categoria.nome, "Alimentação")

    def test_5_impactos_opostos_no_saldo_polimorfismo(self):
        """Critério 3: Receita e Despesa apresentam impactos opostos no saldo para o mesmo valor."""
        valor_igual = 10000  # R$ 100,00 em centavos

        receita = Receita(
            descricao="Reembolso",
            valor_centavos=valor_igual,
            data="2026-11-05",
            categoria=self.cat_salario,
        )
        despesa = Despesa(
            descricao="Compra",
            valor_centavos=valor_igual,
            data="2026-11-05",
            categoria=self.cat_alimentacao,
        )

        self.assertEqual(receita.impacto_no_saldo(), +10000)
        self.assertEqual(despesa.impacto_no_saldo(), -10000)
        self.assertEqual(receita.impacto_no_saldo() + despesa.impacto_no_saldo(), 0)

    def test_6_conversao_para_dict_segue_contrato(self):
        """Critério 4: A conversão para dicionário (para_dict) segue os campos combinados."""
        despesa = Despesa(
            descricao="Mercado",
            valor_centavos=45000,
            data="2026-11-05",
            categoria=self.cat_alimentacao,
            id=7,
        )

        dicionario = despesa.para_dict()
        campos_obrigatorios = {
            "id",
            "descricao",
            "valor_centavos",
            "data",
            "tipo",
            "categoria_id",
        }

        self.assertTrue(campos_obrigatorios.issubset(dicionario.keys()))
        self.assertEqual(dicionario["id"], 7)
        self.assertEqual(dicionario["descricao"], "Mercado")
        self.assertEqual(dicionario["valor_centavos"], 45000)
        self.assertEqual(dicionario["data"], "2026-11-05")
        self.assertEqual(dicionario["tipo"], "despesa")
        self.assertEqual(dicionario["categoria_id"], 2)
        self.assertEqual(dicionario["impacto_no_saldo"], -45000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
