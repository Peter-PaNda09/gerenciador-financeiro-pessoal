import csv
import io
import calendar
from datetime import date
from typing import List, Dict, Any, Optional, Tuple
from models import (
    Transacao,
    Receita,
    Despesa,
    Categoria,
    ErroValidacaoFinanceira,
)
from repository import RepositorioTransacoes


class GerenciadorFinanceiro:
    """
    Coordena o cadastro, edição, exclusão, filtragem, cálculo de indicadores
    e exportação CSV das transações financeiras.
    """

    def __init__(self, repositorio: RepositorioTransacoes):
        self._repositorio = repositorio

    def listar_categorias(self, tipo: Optional[str] = None) -> List[Categoria]:
        return self._repositorio.listar_categorias(tipo=tipo)

    def _construir_transacao_a_partir_de_dados(
        self, dados: Dict[str, Any], id_transacao: Optional[int] = None
    ) -> Transacao:
        if not isinstance(dados, dict):
            raise ErroValidacaoFinanceira("Formato de dados JSON inválido.")

        tipo = str(dados.get("tipo", "")).strip().lower()
        if tipo not in ("receita", "despesa"):
            raise ErroValidacaoFinanceira(
                "O campo 'tipo' é obrigatório e deve ser 'receita' ou 'despesa'."
            )

        try:
            categoria_id = int(dados.get("categoria_id"))  # type: ignore
        except (TypeError, ValueError):
            raise ErroValidacaoFinanceira("O campo 'categoria_id' deve ser um número inteiro.")

        categoria = self._repositorio.buscar_categoria_por_id(categoria_id)

        if "valor_centavos" in dados and dados["valor_centavos"] is not None:
            valor_centavos = Transacao.converter_para_centavos(dados["valor_centavos"])
        elif "valor" in dados and dados["valor"] is not None:
            valor_centavos = Transacao.converter_para_centavos(dados["valor"])
        else:
            raise ErroValidacaoFinanceira("Informe 'valor_centavos' ou 'valor' no lançamento.")

        descricao = dados.get("descricao", "")
        data_lancamento = dados.get("data", "")

        classe_transacao = Receita if tipo == "receita" else Despesa
        return classe_transacao(
            id_transacao=id_transacao,
            descricao=descricao,
            valor_centavos=valor_centavos,
            data_lancamento=data_lancamento,
            categoria=categoria,
        )

    def cadastrar_lancamento(self, dados: Dict[str, Any]) -> Transacao:
        nova_transacao = self._construir_transacao_a_partir_de_dados(dados)
        return self._repositorio.salvar(nova_transacao)

    def editar_lancamento(self, id_transacao: int, dados: Dict[str, Any]) -> Transacao:
        self._repositorio.buscar_por_id(id_transacao)
        transacao_atualizada = self._construir_transacao_a_partir_de_dados(
            dados, id_transacao=id_transacao
        )
        return self._repositorio.atualizar(transacao_atualizada)

    def excluir_lancamento(self, id_transacao: int) -> None:
        self._repositorio.excluir(id_transacao)

    @staticmethod
    def _obter_intervalo_mes(mes_ano: str) -> Tuple[str, str]:
        """Converte 'AAAA-MM' em ('AAAA-MM-01', 'AAAA-MM-ULTIMO_DIA')."""
        try:
            partes = mes_ano.strip().split("-")
            if len(partes) != 2:
                raise ValueError
            ano = int(partes[0])
            mes = int(partes[1])
            ultimo_dia = calendar.monthrange(ano, mes)[1]
            return f"{ano:04d}-{mes:02d}-01", f"{ano:04d}-{mes:02d}-{ultimo_dia:02d}"
        except (ValueError, IndexError):
            raise ErroValidacaoFinanceira(
                "Filtro de mês inválido. Use o formato AAAA-MM (ex.: 2026-11)."
            )

    def consultar_lancamentos(
        self,
        mes: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        tipo: Optional[str] = None,
        categoria_id: Optional[int] = None,
        busca: Optional[str] = None,
    ) -> List[Transacao]:
        transacoes = self._repositorio.listar_todos()

        if mes:
            inicio_mes, fim_mes = self._obter_intervalo_mes(mes)
            transacoes = [t for t in transacoes if inicio_mes <= t.data <= fim_mes]
        else:
            if data_inicio:
                transacoes = [t for t in transacoes if t.data >= data_inicio.strip()]
            if data_fim:
                transacoes = [t for t in transacoes if t.data <= data_fim.strip()]

        if tipo:
            tipo_limpo = tipo.strip().lower()
            if tipo_limpo not in ("receita", "despesa"):
                raise ErroValidacaoFinanceira("Filtro de tipo inválido. Use 'receita' ou 'despesa'.")
            transacoes = [t for t in transacoes if t.tipo == tipo_limpo]

        if categoria_id is not None:
            transacoes = [t for t in transacoes if t.categoria.id == categoria_id]

        if busca and busca.strip():
            termo = busca.strip().lower()
            transacoes = [t for t in transacoes if termo in t.descricao.lower()]

        return transacoes

    def calcular_resumo(
        self,
        mes: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
    ) -> Dict[str, Any]:
        todas_transacoes = self._repositorio.listar_todos()

        if mes:
            inicio_periodo, fim_periodo = self._obter_intervalo_mes(mes)
        else:
            inicio_periodo = data_inicio.strip() if data_inicio else "0001-01-01"
            fim_periodo = data_fim.strip() if data_fim else date.today().isoformat()

        transacoes_periodo = [
            t for t in todas_transacoes if inicio_periodo <= t.data <= fim_periodo
        ]
        transacoes_ate_data_final = [
            t for t in todas_transacoes if t.data <= fim_periodo
        ]

        receitas_periodo_centavos = sum(
            t.valor_centavos for t in transacoes_periodo if isinstance(t, Receita)
        )
        despesas_periodo_centavos = sum(
            t.valor_centavos for t in transacoes_periodo if isinstance(t, Despesa)
        )

        # Polimorfismo: soma impacto_no_saldo() de Receita (+) e Despesa (-)
        resultado_periodo_centavos = sum(
            t.impacto_no_saldo() for t in transacoes_periodo
        )
        saldo_acumulado_centavos = sum(
            t.impacto_no_saldo() for t in transacoes_ate_data_final
        )

        gastos_por_categoria: Dict[int, Dict[str, Any]] = {}
        for t in transacoes_periodo:
            if isinstance(t, Despesa) and t.categoria.id is not None:
                cat_id = t.categoria.id
                if cat_id not in gastos_por_categoria:
                    gastos_por_categoria[cat_id] = {
                        "categoria_id": cat_id,
                        "categoria_nome": t.categoria.nome,
                        "total_centavos": 0,
                    }
                gastos_por_categoria[cat_id]["total_centavos"] += t.valor_centavos

        lista_despesas_categoria = []
        for item in sorted(
            gastos_por_categoria.values(),
            key=lambda x: x["total_centavos"],
            reverse=True,
        ):
            percentual = (
                round((item["total_centavos"] / despesas_periodo_centavos) * 100, 2)
                if despesas_periodo_centavos > 0
                else 0.0
            )
            lista_despesas_categoria.append(
                {
                    "categoria_id": item["categoria_id"],
                    "categoria_nome": item["categoria_nome"],
                    "total_centavos": item["total_centavos"],
                    "total_reais": round(item["total_centavos"] / 100.0, 2),
                    "percentual_despesas": percentual,
                }
            )

        return {
            "periodo": {
                "mes": mes,
                "data_inicio": inicio_periodo if inicio_periodo != "0001-01-01" else None,
                "data_fim": fim_periodo,
            },
            "receitas_periodo_centavos": receitas_periodo_centavos,
            "receitas_periodo_reais": round(receitas_periodo_centavos / 100.0, 2),
            "despesas_periodo_centavos": despesas_periodo_centavos,
            "despesas_periodo_reais": round(despesas_periodo_centavos / 100.0, 2),
            "resultado_periodo_centavos": resultado_periodo_centavos,
            "resultado_periodo_reais": round(resultado_periodo_centavos / 100.0, 2),
            "saldo_acumulado_centavos": saldo_acumulado_centavos,
            "saldo_acumulado_reais": round(saldo_acumulado_centavos / 100.0, 2),
            "despesas_por_categoria": lista_despesas_categoria,
        }

    def exportar_csv(
        self,
        mes: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        tipo: Optional[str] = None,
        categoria_id: Optional[int] = None,
        busca: Optional[str] = None,
    ) -> str:
        lancamentos = self.consultar_lancamentos(
            mes=mes,
            data_inicio=data_inicio,
            data_fim=data_fim,
            tipo=tipo,
            categoria_id=categoria_id,
            busca=busca,
        )

        buffer = io.StringIO()
        escritor = csv.writer(buffer, delimiter=";")
        escritor.writerow(["id", "data", "tipo", "categoria", "descricao", "valor"])

        for t in lancamentos:
            valor_decimal_br = f"{t.valor_reais:.2f}".replace(".", ",")
            escritor.writerow(
                [
                    t.id,
                    t.data,
                    t.tipo,
                    t.categoria.nome,
                    t.descricao,
                    valor_decimal_br,
                ]
            )

        return buffer.getvalue()
