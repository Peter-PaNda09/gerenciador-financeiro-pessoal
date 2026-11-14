# Repositório em memória: acordo interno

O contrato HTTP continua em [contrato-api.md](contrato-api.md). Este arquivo documenta o armazenamento provisório para Marcos e Peterson integrarem suas partes.

## Métodos disponíveis

Classe: `RepositorioTransacoesMemoria`, em `repositories/memoria.py`.

| Método | Recebe | Retorna |
| --- | --- | --- |
| `salvar(transacao)` | Receita ou Despesa sem ID. | Cópia do registro salvo com ID gerado. |
| `listar()` | Nada. | Objetos por data decrescente e ID decrescente. |
| `buscar_por_id(id)` | Inteiro positivo. | Cópia do objeto encontrado. |
| `atualizar(transacao)` | Objeto completo, válido e com ID existente. | Cópia do objeto atualizado. |
| `excluir(id)` | Inteiro positivo existente. | `None`. |
| `listar_categorias()` | Nada. | Categorias predefinidas por ID crescente. |
| `buscar_categoria_por_id(id)` | ID de categoria predefinida. | Cópia do objeto Categoria. |

- `salvar` não altera o objeto recebido. Use o retorno para obter o ID: `salva = repositorio.salvar(transacao)`.
- IDs não são reutilizados após exclusões enquanto a mesma instância existir.
- Consultas retornam cópias: alterar um objeto recebido não muda os dados guardados. Para salvar uma edição, chamar `atualizar`.
- Buscar, atualizar ou excluir um lançamento inexistente lança `RegistroNaoEncontradoErro`.
- IDs inválidos, categoria inexistente e objetos inválidos lançam `ErroValidacaoFinanceira`.
- A categoria é reconstruída a partir do cadastro predefinido, para preservar sua identidade e compatibilidade com receita/despesa.
- Esta implementação usa os nomes da tabela acima, em vez dos nomes alternativos `obter_todos`, `listar_todos` ou `remover`.

## Exemplo com objetos reais

```python
from models import Despesa
from repositories.memoria import RepositorioTransacoesMemoria

repositorio = RepositorioTransacoesMemoria()
categoria = repositorio.buscar_categoria_por_id(2)
despesa = Despesa("Mercado", 45000, "2026-11-05", categoria)
salva = repositorio.salvar(despesa)

print(salva.id)
print(repositorio.listar()[0].impacto_no_saldo())  # -45000
```

## Limites desta etapa

O armazenamento é uma coleção de objetos Python. Reiniciar o processo cria uma coleção vazia. Cada aplicação criada por `create_app()` recebe uma instância independente, a menos que o repositório seja passado explicitamente.

As rotas atuais validam o contrato e instanciam as classes de domínio antes de chamar o repositório. Esse é o ponto provisório de integração: quando o serviço de Marcos estiver compatível, as rotas delegam a ele cadastro e consulta. Não é necessário criar outra classe de transação nem alterar o formato público da API.

Na troca por um banco, preservar os métodos e o comportamento documentados; acrescentar os testes de persistência após reinício. A implementação HTTP inicial contém somente categorias, POST de lançamentos e GET de lançamentos.
