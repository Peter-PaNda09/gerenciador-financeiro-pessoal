from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Dict, Any, Optional


class ErroValidacaoFinanceira(ValueError):
    """
    Exceção de domínio lançada quando uma validação falha (HTTP 400).
    Armazena a mensagem geral e o campo específico para destacar no formulário do front-end.
    """

    def __init__(
        self,
        mensagem: str,
        campo: Optional[str] = None,
        campos: Optional[Dict[str, str]] = None,
    ):
        super().__init__(mensagem)
        self.mensagem = mensagem
        if campos:
            self.campos = campos
        elif campo:
            self.campos = {campo: mensagem}
        else:
            self.campos = {}


class RegistroNaoEncontradoErro(LookupError):
    """Exceção lançada quando um lançamento ou categoria não é encontrado (HTTP 404)."""

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class Categoria:
    """
    Representa a classificação de um lançamento financeiro e seu tipo permitido
    ('receita' ou 'despesa').
    """
    TIPOS_PERMITIDOS = ("receita", "despesa")

    def __init__(
        self,
        nome: str,
        tipo_permitido: str,
        id: Optional[int] = None,
    ):
        self._id: Optional[int] = None
        self._nome: str = ""
        self._tipo_permitido: str = ""

        self.id = id
        self.nome = nome
        self.tipo_permitido = tipo_permitido

    @property
    def id(self) -> Optional[int]:
        return self._id

    @id.setter
    def id(self, valor: Optional[int]) -> None:
        if valor is not None and (isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0):
            raise ErroValidacaoFinanceira("O ID da categoria deve ser um inteiro positivo.", campo="categoria_id")
        self._id = valor

    @property
    def nome(self) -> str:
        return self._nome

    @nome.setter
    def nome(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ErroValidacaoFinanceira("O nome da categoria é obrigatório.", campo="categoria_id")
        self._nome = valor.strip()

    @property
    def tipo_permitido(self) -> str:
        return self._tipo_permitido

    @tipo_permitido.setter
    def tipo_permitido(self, valor: str) -> None:
        if not isinstance(valor, str) or valor.strip().lower() not in self.TIPOS_PERMITIDOS:
            raise ErroValidacaoFinanceira(
                f"Tipo permitido inválido: '{valor}'. Use 'receita' ou 'despesa'.",
                campo="tipo",
            )
        self._tipo_permitido = valor.strip().lower()

    @property
    def tipo(self) -> str:
        """Alias para compatibilidade direta com o app.js (category.tipo)."""
        return self._tipo_permitido

    def para_dict(self) -> Dict[str, Any]:
        """Converte os dados da categoria em dicionário no formato esperado pelo front-end."""
        return {
            "id": self._id,
            "nome": self._nome,
            "tipo": self._tipo_permitido,
            "tipo_permitido": self._tipo_permitido,
        }


class Transacao(ABC):
    """
    Classe base abstrata que reúne id, descrição, valor_centavos, data e categoria.
    Aplica encapsulamento com validações e define impacto_no_saldo().
    """

    def __init__(
        self,
        descricao: str,
        valor_centavos: int,
        data: str,
        categoria: Categoria,
        id: Optional[int] = None,
    ):
        self._id: Optional[int] = None
        self._descricao: str = ""
        self._valor_centavos: int = 0
        self._data: date = date.today()
        self._categoria: Optional[Categoria] = None

        self.id = id
        self.descricao = descricao
        self.valor_centavos = valor_centavos
        self.data = data
        self.categoria = categoria

    @property
    @abstractmethod
    def tipo(self) -> str:
        """Retorna 'receita' ou 'despesa' conforme a subclasse."""
        pass

    @abstractmethod
    def impacto_no_saldo(self) -> int:
        """Retorna centavos positivos para Receita e negativos para Despesa."""
        pass

    @property
    def id(self) -> Optional[int]:
        return self._id

    @id.setter
    def id(self, valor: Optional[int]) -> None:
        if valor is not None and (isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0):
            raise ErroValidacaoFinanceira("O ID do lançamento deve ser um inteiro positivo.")
        self._id = valor

    @property
    def descricao(self) -> str:
        return self._descricao

    @descricao.setter
    def descricao(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ErroValidacaoFinanceira("Informe a descrição do lançamento.", campo="descricao")
        texto = valor.strip()
        if len(texto) > 120:
            raise ErroValidacaoFinanceira(
                "A descrição deve ter no máximo 120 caracteres.",
                campo="descricao",
            )
        self._descricao = texto

    @property
    def valor_centavos(self) -> int:
        return self._valor_centavos

    @valor_centavos.setter
    def valor_centavos(self, valor: int) -> None:
        if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
            raise ErroValidacaoFinanceira(
                "Informe um valor maior que zero, com até duas casas decimais.",
                campo="valor_centavos",
            )
        self._valor_centavos = valor

    @property
    def data(self) -> str:
        """Retorna a data no formato ISO AAAA-MM-DD."""
        return self._data.isoformat()

    @data.setter
    def data(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ErroValidacaoFinanceira("Informe a data do lançamento.", campo="data")
        try:
            data_convertida = datetime.strptime(valor.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ErroValidacaoFinanceira("Informe uma data válida.", campo="data")
        if data_convertida > date.today():
            raise ErroValidacaoFinanceira("A data não pode ser posterior a hoje.", campo="data")
        self._data = data_convertida

    @property
    def data_br(self) -> str:
        return self._data.strftime("%d/%m/%Y")

    @property
    def categoria(self) -> Categoria:
        return self._categoria  # type: ignore

    @categoria.setter
    def categoria(self, nova_categoria: Categoria) -> None:
        if not isinstance(nova_categoria, Categoria):
            raise ErroValidacaoFinanceira("Selecione uma categoria.", campo="categoria_id")
        if nova_categoria.tipo_permitido != self.tipo:
            raise ErroValidacaoFinanceira(
                "A categoria selecionada não pertence ao tipo informado.",
                campo="categoria_id",
            )
        self._categoria = nova_categoria

    @property
    def valor_reais(self) -> float:
        return round(self._valor_centavos / 100.0, 2)

    @staticmethod
    def converter_para_centavos(valor_entrada: Any) -> int:
        if isinstance(valor_entrada, bool) or valor_entrada is None:
            raise ErroValidacaoFinanceira(
                "Informe um valor maior que zero, com até duas casas decimais.",
                campo="valor_centavos",
            )
        if isinstance(valor_entrada, int):
            return valor_entrada
        if isinstance(valor_entrada, (float, str)):
            texto = str(valor_entrada).strip().replace("R$", "").strip()
            if "," in texto and "." in texto:
                texto = texto.replace(".", "").replace(",", ".")
            elif "," in texto:
                texto = texto.replace(",", ".")
            try:
                partes = texto.split(".")
                if len(partes) == 2 and len(partes[1]) > 2:
                    raise ValueError
                return int(round(float(texto) * 100))
            except ValueError:
                raise ErroValidacaoFinanceira(
                    "Informe um valor maior que zero, com até duas casas decimais.",
                    campo="valor_centavos",
                )
        raise ErroValidacaoFinanceira(
            "Informe um valor maior que zero, com até duas casas decimais.",
            campo="valor_centavos",
        )

    def para_dict(self) -> Dict[str, Any]:
        """Converte os dados do objeto em dicionário seguindo o contrato do front-end."""
        return {
            "id": self._id,
            "descricao": self._descricao,
            "valor_centavos": self._valor_centavos,
            "valor_reais": self.valor_reais,
            "data": self.data,
            "data_br": self.data_br,
            "tipo": self.tipo,
            "categoria_id": self._categoria.id if self._categoria else None,
            "categoria_nome": self._categoria.nome if self._categoria else None,
            "impacto_no_saldo": self.impacto_no_saldo(),
        }


class Receita(Transacao):
    """Subclasse concreta que representa entrada de dinheiro (+valor_centavos)."""

    @property
    def tipo(self) -> str:
        return "receita"

    def impacto_no_saldo(self) -> int:
        return +self.valor_centavos


class Despesa(Transacao):
    """Subclasse concreta que representa saída de dinheiro (-valor_centavos)."""

    @property
    def tipo(self) -> str:
        return "despesa"

    def impacto_no_saldo(self) -> int:
        return -self.valor_centavos
