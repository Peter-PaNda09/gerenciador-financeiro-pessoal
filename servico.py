class ServicoFinanceiro:
    """
    Classe de serviço responsável pelas operações financeiras,
    regras de negócio e validações antes da persistência.
    """
    def __init__(self, repositorio):
        self.repositorio = repositorio

    def cadastrar_lancamento(self, transacao_objeto):
        """
        Cadastra uma nova transação após validar as regras de negócio.
        Recebe diretamente a instância do objeto (Receita ou Despesa) criada pelo domínio.
        """
        # Validação básica de integridade do objeto recebido
        if not transacao_objeto:
            raise ValueError("O objeto de transação não pode ser nulo.")
        
        if not transacao_objeto.descricao or not transacao_objeto.descricao.strip():
            raise ValueError("A descrição do lançamento é obrigatória.")
        
        if transacao_objeto.valor <= 0:
            raise ValueError("O valor da transação deve ser estritamente positivo.")

        # Validação de tipo compatível
        if transacao_objeto.tipo.lower() not in ["receita", "despesa"]:
            raise ValueError("Tipo de transação inválido. Deve ser 'receita' ou 'despesa'.")

        # Delega ao repositório a persistência real dos dados
        return self.repositorio.salvar(transacao_objeto)

    def listar_lancamentos(self, filtros=None):
        """
        Retorna todos os lançamentos aplicando filtros opcionais 
        (por tipo, categoria ou período) para consumo do painel e dos cálculos do Igor.
        """
        transacoes = self.repositorio.obter_todos()
        
        if not filtros:
            return transacoes
            
        resultado = transacoes
        if "tipo" in filtros and filtros["tipo"]:
            resultado = [t for t in resultado if t.tipo.lower() == filtros["tipo"].lower()]
            
        if "categoria" in filtros and filtros["categoria"]:
            resultado = [t for t in resultado if t.categoria.lower() == filtros["categoria"].lower()]
            
        return resultado

    def editar_lancamento(self, id_transacao, novos_dados):
        """
        Edita um registro existente, verificando obrigatoriamente 
        se o identificador existe no repositório antes de alterar.
        """
        registro_existente = self.repositorio.buscar_por_id(id_transacao)
        if not registro_existente:
            raise ValueError(f"Registro com ID {id_transacao} não foi encontrado para edição.")

        # Validação de regras em caso de alteração de valores
        if "valor" in novos_dados and novos_dados["valor"] <= 0:
            raise ValueError("O valor atualizado deve ser positivo.")

        return self.repositorio.atualizar(id_transacao, novos_dados)

    def excluir_lancamento(self, id_transacao):
        """
        Exclui um registro, validando se ele realmente existe antes de apagar,
        evitando falhas impeditivas no sistema.
        """
        registro_existente = self.repositorio.buscar_por_id(id_transacao)
        if not registro_existente:
            raise ValueError(f"Registro com ID {id_transacao} não foi encontrado para exclusão.")

        return self.repositorio.remover(id_transacao)