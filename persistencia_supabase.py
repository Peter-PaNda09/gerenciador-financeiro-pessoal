import os
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client
from models import (
    Categoria,
    Transacao,
    Receita,
    Despesa,
    ErroValidacaoFinanceira,
    RegistroNaoEncontradoErro,
)

load_dotenv()


class RepositorioTransacoes:
    """Concentra a leitura e escrita no Supabase e converte linhas em objetos POO."""

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        supabase_url = url or os.environ.get("SUPABASE_URL")
        supabase_key = key or os.environ.get("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise RuntimeError(
                "Credenciais do Supabase ausentes. Defina SUPABASE_URL e SUPABASE_KEY no arquivo .env."
            )

        self._client: Client = create_client(supabase_url, supabase_key)

    def listar_categorias(self, tipo: Optional[str] = None) -> List[Categoria]:
        query = self._client.table("categorias").select("id, nome, tipo_permitido")
        if tipo:
            query = query.eq("tipo_permitido", tipo.strip().lower())

        resposta = query.order("id").execute()
        return [
            Categoria(
                id=linha["id"],
                nome=linha["nome"],
                tipo_permitido=linha["tipo_permitido"],
            )
            for linha in resposta.data
        ]

    def buscar_categoria_por_id(self, categoria_id: int) -> Categoria:
        resposta = (
            self._client.table("categorias")
            .select("id, nome, tipo_permitido")
            .eq("id", categoria_id)
            .execute()
        )
        if not resposta.data:
            raise ErroValidacaoFinanceira("Selecione uma categoria.", campo="categoria_id")
        linha = resposta.data[0]
        return Categoria(
            id=linha["id"],
            nome=linha["nome"],
            tipo_permitido=linha["tipo_permitido"],
        )

    def _instanciar_transacao(self, linha: Dict[str, Any]) -> Transacao:
        dados_cat = linha.get("categorias") or {}
        categoria = Categoria(
            id=dados_cat.get("id", linha["categoria_id"]),
            nome=dados_cat.get("nome", "Categoria removida"),
            tipo_permitido=dados_cat.get("tipo_permitido", linha["tipo"]),
        )
        classe_concreta = Receita if linha["tipo"] == "receita" else Despesa
        return classe_concreta(
            id=linha["id"],
            descricao=linha["descricao"],
            valor_centavos=linha["valor_centavos"],
            data=str(linha["data"]),
            categoria=categoria,
        )

    def salvar(self, transacao: Transacao) -> Transacao:
        payload = {
            "descricao": transacao.descricao,
            "valor_centavos": transacao.valor_centavos,
            "data": transacao.data,
            "tipo": transacao.tipo,
            "categoria_id": transacao.categoria.id,
        }
        resposta = self._client.table("lancamentos").insert(payload).execute()
        if not resposta.data:
            raise ErroValidacaoFinanceira("Não foi possível salvar o lançamento no Supabase.")
        transacao.id = resposta.data[0]["id"]
        return transacao

    def atualizar(self, transacao: Transacao) -> Transacao:
        if transacao.id is None:
            raise ErroValidacaoFinanceira("Não é possível atualizar um lançamento sem ID.")

        payload = {
            "descricao": transacao.descricao,
            "valor_centavos": transacao.valor_centavos,
            "data": transacao.data,
            "tipo": transacao.tipo,
            "categoria_id": transacao.categoria.id,
        }
        resposta = (
            self._client.table("lancamentos")
            .update(payload)
            .eq("id", transacao.id)
            .execute()
        )
        if not resposta.data:
            raise RegistroNaoEncontradoErro(
                "Este lançamento não foi encontrado. Atualize a página e tente novamente."
            )
        return transacao

    def excluir(self, id_transacao: int) -> None:
        resposta = (
            self._client.table("lancamentos")
            .delete()
            .eq("id", id_transacao)
            .execute()
        )
        if not resposta.data:
            raise RegistroNaoEncontradoErro(
                "Este lançamento não foi encontrado. Atualize a página e tente novamente."
            )

    def buscar_por_id(self, id_transacao: int) -> Transacao:
        resposta = (
            self._client.table("lancamentos")
            .select("id, descricao, valor_centavos, data, tipo, categoria_id, categorias(id, nome, tipo_permitido)")
            .eq("id", id_transacao)
            .execute()
        )
        if not resposta.data:
            raise RegistroNaoEncontradoErro(
                "Este lançamento não foi encontrado. Atualize a página e tente novamente."
            )
        return self._instanciar_transacao(resposta.data[0])

    def listar_todos(self) -> List[Transacao]:
        resposta = (
            self._client.table("lancamentos")
            .select("id, descricao, valor_centavos, data, tipo, categoria_id, categorias(id, nome, tipo_permitido)")
            .order("data", desc=True)
            .order("id", desc=True)
            .execute()
        )
        return [self._instanciar_transacao(linha) for linha in resposta.data]
