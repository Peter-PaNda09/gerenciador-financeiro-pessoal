from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Dict, Any, Optional


class ErroValidacaoFinanceira(ValueError):
    """Exceção de domínio lançada quando uma validação de atributo ou regra falha."""
    pass


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
            raise ErroValidacaoFinanceira("O ID da categoria deve ser um número inteiro positivo.")
        self._id = valor

    @property
    def nome(self) -> str:
        return self._nome

    @nome.setter
    def nome(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ErroValidacaoFinanceira("O nome da categoria é obrigatório.")
        self._nome = valor.strip()

    @property
    def tipo_permitido(self) -> str:
        return self._tipo_permitido

    @tipo_permitido.setter
    def tipo_permitido(self, valor: str) -> None:
        if not isinstance(valor, str) or valor.strip().lower() not in self.TIPOS_PERMITIDOS:
            raise ErroValidacaoFinanceira(
                f"Tipo permitido inválido: '{valor}'. Use 'receita' ou 'despesa'."
            )
        self._tipo_permitido = valor.strip().lower()

    def para_dict(self) -> Dict[str, Any]:
        """Converte os dados da categoria para dicionário conforme contrato da API."""
        return {
            "id": self._id,
            "nome": self._nome,
            "tipo_permitido": self._tipo_permitido,
        }


class Transacao(ABC):
    """
    Classe base abstrata que reúne id, descrição, valor_centavos, data e categoria.
    Garante encapsulamento estrito e exige a implementação de impacto_no_saldo().
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
        """Retorna o tipo da transação ('receita' ou 'despesa')."""
        pass

    @abstractmethod
    def impacto_no_saldo(self) -> int:
        """
        Retorna o impacto em centavos no saldo:
        positivo para Receita e negativo para Despesa.
        """
        pass

    @property
    def id(self) -> Optional[int]:
        return self._id

    @id.setter
    def id(self, valor: Optional[int]) -> None:
        if valor is not None and (isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0):
            raise ErroValidacaoFinanceira("O ID do lançamento deve ser um número inteiro positivo.")
        self._id = valor

    @property
    def descricao(self) -> str:
        return self._descricao

    @descricao.setter
    def descricao(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ErroValidacaoFinanceira("A descrição do lançamento é obrigatória.")
        self._descricao = valor.strip()

    @property
    def valor_centavos(self) -> int:
        return self._valor_centavos

    @valor_centavos.setter
    def valor_centavos(self, valor: int) -> None:
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise ErroValidacaoFinanceira(
                "O valor deve ser informado em centavos inteiros (ex.: R$ 10,50 = 1050)."
            )
        if valor <= 0:
            raise ErroValidacaoFinanceira("O valor do lançamento deve ser maior que zero.")
        self._valor_centavos = valor

    @property
    def data(self) -> str:
        """Retorna a data no formato ISO AAAA-MM-DD."""
        return self._data.isoformat()

    @data.setter
    def data(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ErroValidacaoFinanceira("A data do lançamento é obrigatória.")
        try:
            data_convertida = datetime.strptime(valor.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ErroValidacaoFinanceira(
                "Data inválida. Utilize o formato AAAA-MM-DD com uma data real."
            )
        if data_convertida > date.today():
            raise ErroValidacaoFinanceira(
                "Não é permitido informar uma data futura para o lançamento."
            )
        self._data = data_convertida

    @property
    def data_br(self) -> str:
        """Retorna a data no formato brasileiro DD/MM/AAAA para exibição."""
        return self._data.strftime("%d/%m/%Y")

    @property
    def categoria(self) -> Categoria:
        return self._categoria  # type: ignore

    @categoria.setter
    def categoria(self, nova_categoria: Categoria) -> None:
        if not isinstance(nova_categoria, Categoria):
            raise ErroValidacaoFinanceira("A categoria informada deve ser um objeto Categoria válido.")
        if nova_categoria.tipo_permitido != self.tipo:
            raise ErroValidacaoFinanceira(
                f"A categoria '{nova_categoria.nome}' ({nova_categoria.tipo_permitido}) "
                f"não é compatível com um lançamento do tipo '{self.tipo}'."
            )
        self._categoria = nova_categoria

    @property
    def valor_reais(self) -> float:
        """Retorna o valor convertido de centavos para reais."""
        return round(self._valor_centavos / 100.0, 2)

    def para_dict(self) -> Dict[str, Any]:
        """
        Converte os dados do objeto em dicionário seguindo os campos combinados
        no contrato da equipe (página 3 e página 4 do guia).
        """
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
    """Representa uma entrada financeira; soma centavos positivos ao saldo."""

    @property
    def tipo(self) -> str:
        return "receita"

    def impacto_no_saldo(self) -> int:
        return +self.valor_centavos


class Despesa(Transacao):
    """Representa uma saída financeira; retorna centavos negativos no saldo."""

    @property
    def tipo(self) -> str:
        return "despesa"

    def impacto_no_saldo(self) -> int:
        return -self.valor_centavos
