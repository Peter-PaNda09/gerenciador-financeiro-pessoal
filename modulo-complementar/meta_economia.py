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
  calcular_percentual_progresso, verificar_conclusao, exibir_status).
- Encapsulamento: Proteção dos atributos internos (prefixo _) com leitura via @property,
  impedindo alterações diretas no saldo fora do método adicionar_economia().
"""


def formatar_moeda(valor: float) -> str:
    """Formata um número float no padrão monetário brasileiro (ex.: R$ 2.000,00)."""
    texto_num = f"{valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {texto_num}"


def formatar_percentual(valor: float) -> str:
    """Formata um número float como percentual brasileiro (ex.: 25,0%)."""
    texto_num = f"{valor:.1f}".replace(".", ",")
    return f"{texto_num}%"


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
        """Retorna uma linha formatada com o resumo atual da meta, preservando o nome original."""
        status = "Concluída" if self.verificar_conclusao() else "Em andamento"
        objetivo_fmt = formatar_moeda(self.valor_desejado)
        acumulado_fmt = formatar_moeda(self.valor_acumulado)
        progresso_fmt = formatar_percentual(self.calcular_percentual_progresso())
        restante_fmt = formatar_moeda(self.calcular_quanto_falta())

        return (
            f"Meta: {self.nome} | "
            f"Objetivo: {objetivo_fmt} | "
            f"Acumulado: {acumulado_fmt} | "
            f"Progresso: {progresso_fmt} | "
            f"Restante: {restante_fmt} | "
            f"Status: {status}"
        )


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
    - Preservação do nome original em exibir_status() (caso 'Xbox')
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

    # 7. Teste de formatação em exibir_status() preservando nomes com 'X' (ex.: 'Xbox')
    meta_xbox = MetaEconomia("Xbox", 3500.00)
    meta_xbox.adicionar_economia(500.00)
    status_xbox = meta_xbox.exibir_status()
    assert "Meta: Xbox |" in status_xbox, f"O nome 'Xbox' foi alterado indevidamente: {status_xbox}"
    assert ".box" not in status_xbox, "A letra 'X' não pode ser substituída por ponto."
    assert "R$ 3.500,00" in status_xbox, "O valor desejado deve estar formatado no padrão brasileiro."
    assert "R$ 500,00" in status_xbox, "O valor acumulado deve estar formatado no padrão brasileiro."
    print("[OK] Teste 7: Formatação de exibir_status() preservando o nome 'Xbox' validada.")

    print("\nTodos os testes passaram com sucesso!")
    print("=" * 75)


def ler_valor_monetario(mensagem: str) -> float:
    """
    Lê um texto digitado pelo usuário e converte para float,
    aceitando tanto vírgula quanto ponto decimal (ex.: 250,50 ou 250.50).
    Levanta ValueError com mensagem clara se o formato for inválido.
    """
    entrada = input(mensagem).strip()
    if not entrada:
        raise ValueError("Erro: Nenhum valor foi digitado.")

    # Se o usuário digitar no formato brasileiro com milhar e vírgula (ex.: 2.000,50)
    if "," in entrada and "." in entrada:
        entrada = entrada.replace(".", "").replace(",", ".")
    elif "," in entrada:
        entrada = entrada.replace(",", ".")

    try:
        return float(entrada)
    except ValueError:
        raise ValueError("Erro: Digite um valor numérico válido (ex.: 250 ou 250,50).")


def listar_metas(metas: list[MetaEconomia]) -> bool:
    """
    Exibe todas as metas cadastradas com seu número de identificação.
    Retorna True se houver metas ou False caso a lista esteja vazia.
    """
    if not metas:
        print("\n[!] Nenhuma meta cadastrada até o momento. Crie uma meta primeiro (opção 1).")
        return False

    print("\n--- Metas Cadastradas ---")
    for indice, meta in enumerate(metas, start=1):
        situacao = "Concluída" if meta.verificar_conclusao() else "Em andamento"
        print(
            f"[{indice}] {meta.nome} "
            f"(Objetivo: {formatar_moeda(meta.valor_desejado)} | Situação: {situacao})"
        )
    return True


def escolher_meta(metas: list[MetaEconomia]) -> MetaEconomia | None:
    """
    Mostra a lista de metas e solicita ao usuário que escolha uma pelo número.
    Retorna o objeto MetaEconomia escolhido ou None se a escolha for inválida/vazia.
    """
    if not listar_metas(metas):
        return None

    escolha_str = input("\nDigite o número da meta desejada: ").strip()
    try:
        indice = int(escolha_str)
    except ValueError:
        print("\n[Erro] Identificação inválida. Digite apenas o número inteiro correspondente à meta.")
        return None

    if indice < 1 or indice > len(metas):
        print(f"\n[Erro] Opção fora do intervalo. Escolha um número entre 1 e {len(metas)}.")
        return None

    return metas[indice - 1]


def executar_menu() -> None:
    """
    Executa o menu interativo no terminal para gerenciar metas de economia em memória.
    """
    metas: list[MetaEconomia] = []

    while True:
        print("\n" + "=" * 75)
        print("MENU - GERENCIADOR DE METAS DE ECONOMIA")
        print("=" * 75)
        print("1 - Criar uma meta (informar nome e valor desejado)")
        print("2 - Listar as metas com identificação")
        print("3 - Adicionar um valor economizado à meta escolhida")
        print("4 - Consultar acumulado, quanto falta, percentual e situação da meta")
        print("5 - Sair")
        print("-" * 75)

        opcao = input("Escolha uma opção (1 a 5): ").strip()

        if opcao == "1":
            print("\n--- Nova Meta de Economia ---")
            nome = input("Nome da meta (ex.: Xbox, Notebook, Viagem): ")
            try:
                valor_desejado = ler_valor_monetario("Valor desejado (R$): ")
                nova_meta = MetaEconomia(nome, valor_desejado)
                metas.append(nova_meta)
                print(
                    f"\n[Sucesso] Meta '{nova_meta.nome}' criada com objetivo de "
                    f"{formatar_moeda(nova_meta.valor_desejado)}! (ID: {len(metas)})"
                )
            except ValueError as erro:
                print(f"\n[{erro}]")

        elif opcao == "2":
            listar_metas(metas)

        elif opcao == "3":
            print("\n--- Adicionar Economia ---")
            meta_escolhida = escolher_meta(metas)
            if meta_escolhida is not None:
                try:
                    valor_aporte = ler_valor_monetario(
                        f"Informe o valor para adicionar à meta '{meta_escolhida.nome}' (R$): "
                    )
                    meta_escolhida.adicionar_economia(valor_aporte)
                    print(f"\n[Sucesso] Economia de {formatar_moeda(valor_aporte)} registrada!")
                    print("   ", meta_escolhida.exibir_status())
                except ValueError as erro:
                    print(f"\n[{erro}]")

        elif opcao == "4":
            print("\n--- Consultar Detalhes da Meta ---")
            meta_escolhida = escolher_meta(metas)
            if meta_escolhida is not None:
                situacao = "Concluída" if meta_escolhida.verificar_conclusao() else "Em andamento"
                print("\n" + "-" * 50)
                print(f"Meta:                {meta_escolhida.nome}")
                print(f"Valor desejado:      {formatar_moeda(meta_escolhida.valor_desejado)}")
                print(f"Valor acumulado:     {formatar_moeda(meta_escolhida.valor_acumulado)}")
                print(f"Quanto falta:        {formatar_moeda(meta_escolhida.calcular_quanto_falta())}")
                print(f"Percentual atingido: {formatar_percentual(meta_escolhida.calcular_percentual_progresso())}")
                print(f"Situação da meta:    {situacao}")
                print("-" * 50)

        elif opcao == "5":
            print("\nEncerrando o gerenciador de metas. Até mais!")
            break

        else:
            print("\n[Erro] Opção inválida! Por favor, digite um número de 1 a 5.")


if __name__ == "__main__":
    executar_demonstracao()
    executar_testes()
    executar_menu()
