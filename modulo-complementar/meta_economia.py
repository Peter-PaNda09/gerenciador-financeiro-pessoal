"""
Módulo Complementar: Metas de Economia (Gerenciador Financeiro Pessoal)
Disciplina: Programação Orientada a Objetos (POO) em Python

Resumo dos conceitos de POO aplicados neste arquivo:
- Classe (MetaEconomia): Molde que define a estrutura e o comportamento de uma meta financeira.
- Objeto: Instância concreta criada a partir da classe (ex.: meta_notebook).
- Construtor (__init__): Método especial executado ao criar o objeto, responsável por validar
  e inicializar os atributos no estado inicial.
- Atributos: Características da meta (_nome, _valor_desejado_centavos, _valor_acumulado_centavos).
- Métodos: Ações e cálculos da classe (adicionar_economia, calcular_quanto_falta,
  calcular_percentual_progresso, verificar_conclusao, resumo).
- Encapsulamento: Proteção dos atributos internos (prefixo _) com leitura via @property,
  impedindo alterações diretas no saldo fora do método adicionar_economia().
"""


class MetaEconomia:
    """Representa uma meta financeira pessoal e controla o progresso das economias."""

    def __init__(self, nome: str, valor_desejado: float):
        """
        Construtor da classe MetaEconomia.
        Inicializa a meta com um nome, um valor desejado (objetivo) e saldo acumulado zero.
        """
        # Validação do nome da meta (não pode ser vazio ou conter apenas espaços)
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError("Erro: O nome da meta não pode ser vazio.")

        # Validação do valor desejado (deve ser numérico e maior que zero)
        if not isinstance(valor_desejado, (int, float)) or isinstance(valor_desejado, bool):
            raise ValueError("Erro: O valor desejado deve ser um número válido.")

        valor_centavos = round(valor_desejado * 100)
        if valor_centavos <= 0:
            raise ValueError("Erro: O valor desejado da meta deve ser maior que zero.")

        # Atributos encapsulados (armazenados em centavos inteiros para evitar erros de ponto flutuante)
        self._nome = nome.strip()
        self._valor_desejado_centavos = valor_centavos
        self._valor_acumulado_centavos = 0

    @property
    def nome(self) -> str:
        """Retorna o nome da meta."""
        return self._nome

    @property
    def valor_desejado(self) -> float:
        """Retorna o valor desejado da meta em reais."""
        return self._valor_desejado_centavos / 100.0

    @property
    def valor_acumulado(self) -> float:
        """
        Retorna o valor acumulado até o momento em reais.
        Não possui 'setter' público: alterações só podem ocorrer pelo método adicionar_economia().
        """
        return self._valor_acumulado_centavos / 100.0

    def adicionar_economia(self, valor: float) -> None:
        """
        Registra um novo aporte (economia) na meta após validar o valor informado.
        """
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise ValueError("Erro: O valor do aporte deve ser um número válido.")

        aporte_centavos = round(valor * 100)
        if aporte_centavos <= 0:
            raise ValueError("Erro: O valor do aporte deve ser maior que zero.")

        self._valor_acumulado_centavos += aporte_centavos

    def calcular_quanto_falta(self) -> float:
        """
        Calcula quanto falta (em reais) para atingir o objetivo.
        O valor restante nunca fica negativo (retorna 0.0 se atingir ou ultrapassar a meta).
        """
        restante_centavos = self._valor_desejado_centavos - self._valor_acumulado_centavos
        if restante_centavos <= 0:
            return 0.0
        return restante_centavos / 100.0

    def calcular_percentual_progresso(self) -> float:
        """
        Calcula o percentual de progresso da meta.
        Pode ultrapassar 100% caso o valor acumulado supere o valor desejado.
        """
        return (self._valor_acumulado_centavos / self._valor_desejado_centavos) * 100.0

    def verificar_conclusao(self) -> bool:
        """
        Verifica se a meta foi concluída (acumulado igual ou superior ao valor desejado).
        """
        return self._valor_acumulado_centavos >= self._valor_desejado_centavos

    def exibir_status(self) -> str:
        """Retorna uma linha formatada com o resumo atual da meta."""
        status = "Concluída" if self.verificar_conclusao() else "Em andamento"
        return (
            f"Meta: {self.nome} | "
            f"Objetivo: R$ {self.valor_desejado:,.2f} | "
            f"Acumulado: R$ {self.valor_acumulado:,.2f} | "
            f"Progresso: {self.calcular_percentual_progresso():.1f}% | "
            f"Restante: R$ {self.calcular_quanto_falta():,.2f} | "
            f"Status: {status}"
        ).replace(",", "X").replace(".", ",").replace("X", ".")


def executar_demonstracao() -> None:
    """
    Demonstração prática no terminal seguindo o exemplo do enunciado.
    """
    print("=" * 75)
    print("SIMULADOR DE METAS DE ECONOMIA - DEMONSTRAÇÃO")
    print("=" * 75)

    # 1. Instanciando o objeto com a meta do enunciado: juntar R$ 2.000,00 para um notebook
    meta_notebook = MetaEconomia("Notebook", 2000.00)
    print("\n[1] Estado inicial da meta:")
    print("   ", meta_notebook.exibir_status())

    # 2. Registrando dois aportes de R$ 250,00
    meta_notebook.adicionar_economia(250.00)
    meta_notebook.adicionar_economia(250.00)
    print("\n[2] Após dois aportes de R$ 250,00:")
    print("   ", meta_notebook.exibir_status())

    # 3. Atingindo exatamente R$ 2.000,00 (aporte de R$ 1.500,00)
    meta_notebook.adicionar_economia(1500.00)
    print("\n[3] Ao atingir a meta de R$ 2.000,00 (+ R$ 1.500,00):")
    print("   ", meta_notebook.exibir_status())

    # 4. Ultrapassando a meta (+ R$ 200,00) para demonstrar que o restante continua zero
    meta_notebook.adicionar_economia(200.00)
    print("\n[4] Ultrapassando a meta (+ R$ 200,00):")
    print("   ", meta_notebook.exibir_status())

    # 5. Demonstrando a rejeição de dados inválidos
    print("\n[5] Demonstração das validações (rejeição de valores inválidos):")
    exemplos_invalidos = [
        ("Nome vazio", lambda: MetaEconomia("   ", 1000.00)),
        ("Valor desejado zero", lambda: MetaEconomia("Viagem", 0)),
        ("Valor desejado negativo", lambda: MetaEconomia("Viagem", -500.00)),
        ("Aporte zero", lambda: meta_notebook.adicionar_economia(0)),
        ("Aporte negativo", lambda: meta_notebook.adicionar_economia(-100.00)),
    ]

    for descricao, operacao in exemplos_invalidos:
        try:
            operacao()
        except ValueError as erro:
            print(f"    - {descricao}: bloqueado com sucesso -> '{erro}'")


def executar_testes() -> None:
    """
    Executa os testes automatizados com assert solicitados na atividade:
    - Estado inicial
    - Soma de aportes
    - Progresso
    - Conclusão
    - Valor acima da meta
    - Rejeição de dados inválidos
    """
    print("\n" + "=" * 75)
    print("EXECUTANDO TESTES AUTOMATIZADOS (ASSERT)")
    print("=" * 75)

    # 1. Teste de estado inicial
    meta = MetaEconomia("Notebook", 2000.00)
    assert meta.nome == "Notebook", "O nome inicial deve ser 'Notebook'."
    assert meta.valor_desejado == 2000.00, "O valor desejado deve ser 2000.00."
    assert meta.valor_acumulado == 0.0, "O valor acumulado deve começar em zero."
    assert meta.calcular_quanto_falta() == 2000.00, "O valor restante inicial deve ser 2000.00."
    assert meta.calcular_percentual_progresso() == 0.0, "O progresso inicial deve ser 0%."
    assert meta.verificar_conclusao() is False, "A meta não deve iniciar concluída."
    print("[OK] Teste 1: Estado inicial validado.")

    # 2. Teste de soma de aportes e cálculo de progresso parcial (exemplo do PDF)
    meta.adicionar_economia(250.00)
    meta.adicionar_economia(250.00)
    assert meta.valor_acumulado == 500.00, "Após dois aportes de 250, o acumulado deve ser 500.00."
    assert meta.calcular_percentual_progresso() == 25.0, "O progresso deve ser de 25.0%."
    assert meta.calcular_quanto_falta() == 1500.00, "O restante deve ser 1500.00."
    assert meta.verificar_conclusao() is False, "A meta ainda não deve estar concluída."
    print("[OK] Teste 2: Soma de aportes e progresso parcial (25%) validados.")

    # 3. Teste de conclusão exata da meta
    meta.adicionar_economia(1500.00)
    assert meta.valor_acumulado == 2000.00, "O acumulado deve ser 2000.00."
    assert meta.calcular_percentual_progresso() == 100.0, "O progresso deve ser 100.0%."
    assert meta.calcular_quanto_falta() == 0.0, "Ao atingir a meta, o restante deve ser zero."
    assert meta.verificar_conclusao() is True, "Ao atingir 2000.00, a meta deve estar concluída."
    print("[OK] Teste 3: Conclusão exata da meta validada.")

    # 4. Teste de valor acima da meta (restante nunca negativo e percentual > 100%)
    meta.adicionar_economia(200.00)
    assert meta.valor_acumulado == 2200.00, "O acumulado deve ser 2200.00."
    assert round(meta.calcular_percentual_progresso(), 2) == 110.0, "O progresso deve ser 110.0%."
    assert meta.calcular_quanto_falta() == 0.0, "O valor restante nunca pode ficar negativo."
    assert meta.verificar_conclusao() is True, "A meta deve permanecer concluída acima do objetivo."
    print("[OK] Teste 4: Valor acima da meta (110% e restante zero) validado.")

    # 5. Teste de precisão com centavos (evitando erros de ponto flutuante como 0.1 + 0.2)
    meta_centavos = MetaEconomia("Cofrinho", 1.00)
    meta_centavos.adicionar_economia(0.10)
    meta_centavos.adicionar_economia(0.20)
    assert meta_centavos.valor_acumulado == 0.30, "A soma de 0.10 + 0.20 deve ser exatamente 0.30."
    assert meta_centavos.calcular_quanto_falta() == 0.70, "O restante deve ser exatamente 0.70."
    print("[OK] Teste 5: Precisão em centavos inteiros validada.")

    # 6. Testes de rejeição de dados inválidos
    # 6.1 Nome vazio ou apenas espaços
    for nome_invalido in ["", "   "]:
        deu_erro = False
        try:
            MetaEconomia(nome_invalido, 100.00)
        except ValueError:
            deu_erro = True
        assert deu_erro, f"Deveria rejeitar nome inválido: {repr(nome_invalido)}"

    # 6.2 Valor desejado zero ou negativo
    for objetivo_invalido in [0, -0.01, -500]:
        deu_erro = False
        try:
            MetaEconomia("Reserva", objetivo_invalido)
        except ValueError:
            deu_erro = True
        assert deu_erro, f"Deveria rejeitar valor desejado inválido: {objetivo_invalido}"

    # 6.3 Aporte zero ou negativo (garantindo também que o saldo não foi alterado)
    saldo_anterior = meta.valor_acumulado
    for aporte_invalido in [0, -0.01, -150]:
        deu_erro = False
        try:
            meta.adicionar_economia(aporte_invalido)
        except ValueError:
            deu_erro = True
        assert deu_erro, f"Deveria rejeitar aporte inválido: {aporte_invalido}"
    assert meta.valor_acumulado == saldo_anterior, "Aportes inválidos não podem alterar o acumulado."
    print("[OK] Teste 6: Rejeição de dados inválidos validada.")

    print("\nTodos os testes passaram com sucesso!")
    print("=" * 75)


if __name__ == "__main__":
    executar_demonstracao()
    executar_testes()
