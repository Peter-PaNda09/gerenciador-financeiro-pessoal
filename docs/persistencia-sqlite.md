# Persistência local em SQLite

## Onde os dados ficam

Ao executar `app.py`, a aplicação cria `instance/financeiro.sqlite3` na pasta do projeto. Não é necessário instalar um servidor de banco: o Python utiliza o módulo `sqlite3` da biblioteca padrão.

O arquivo é criado uma vez e reutilizado nas próximas execuções. Parar o Flask ou reiniciar o computador preserva os cadastros. Cada computador tem sua própria base; atualizar o código pelo Git não compartilha nem apaga os registros.

Lançamentos de uma execução antiga em memória não são migrados automaticamente. O SQLite começa vazio na primeira execução, com as seis categorias predefinidas.

## Estrutura

| Tabela | Campos principais |
| --- | --- |
| `categorias` | `id`, `nome`, `tipo_permitido`. |
| `lancamentos` | `id`, `descricao`, `valor_centavos`, `data`, `tipo`, `categoria_id`. |

- Os IDs das categorias são explícitos e iguais aos do [contrato HTTP](contrato-api.md).
- O SQLite gera os IDs dos lançamentos, sem reutilizar IDs excluídos após uma gravação confirmada.
- Dinheiro é armazenado como inteiro em centavos; datas, como texto ISO `AAAA-MM-DD`.
- O banco reforça valores positivos, campos obrigatórios, limites de descrição e a relação entre tipo e categoria. As classes Python e a API validam também as datas reais e não futuras.
- Todas as conexões ativam chaves estrangeiras e são fechadas ao fim da operação.
- Gravações válidas são confirmadas; falhas na transação desfazem suas alterações.
- A inicialização cria tabelas ausentes e insere categorias faltantes. Ela não apaga lançamentos. Categorias incompatíveis geram um erro explicativo em vez de serem sobrescritas.

## Interface para o serviço de Marcos

Classe: `RepositorioTransacoesSQLite`, em `repositories/sqlite.py`.

| Método | Comportamento |
| --- | --- |
| `salvar(transacao)` | Recebe Receita/Despesa sem ID e devolve um novo objeto salvo com ID. |
| `listar()` | Devolve objetos por data decrescente, depois ID decrescente. |
| `buscar_por_id(id)` | Devolve o objeto ou lança `RegistroNaoEncontradoErro`. |
| `atualizar(transacao)` | Grava um objeto completo validado, preservando o ID existente. |
| `excluir(id)` | Exclui o registro ou lança `RegistroNaoEncontradoErro`. |
| `listar_categorias()` | Devolve as seis categorias por ID crescente. |
| `buscar_categoria_por_id(id)` | Devolve a categoria ou lança `ErroValidacaoFinanceira`. |

Assim como na memória, o objeto recebido por `salvar` não é alterado: use o retorno para obter seu ID. Alterar um objeto consultado também não altera o banco; chame `atualizar` para confirmar a edição.

O limite do campo monetário é o inteiro de 64 bits do SQLite. Valores que excedam esse limite são rejeitados com erro de validação. O contrato JSON exige um inteiro, sem conversão de strings ou de números decimais em centavos.

## Ligação ao Flask

```python
from app import create_app

app = create_app()  # instance/financeiro.sqlite3
```

Para usar outro arquivo em um teste ou demonstração separada:

```python
app = create_app(caminho_banco="dados/demonstracao.sqlite3")
```

O caminho padrão é baseado na pasta da aplicação, independentemente da pasta de onde o terminal a iniciou. Um caminho personalizado relativo é resolvido a partir da pasta atual. Aplicações que apontam para o mesmo arquivo leem os mesmos registros.

O arquivo `app.py` não cria o banco ao ser apenas importado. A aplicação e o banco são inicializados quando `create_app()` é chamado, inclusive pela execução normal `python app.py`.

As rotas atuais continuam sendo GET de categorias, POST de lançamentos e GET de lançamentos. O repositório possui edição e exclusão para a integração futura do serviço; isso não significa que as rotas PUT/DELETE já estão disponíveis.

## Conferência manual de persistência

1. Atualize sua branch PETER e execute o Flask conforme o README.
2. Abra `/` e confira `"armazenamento": "sqlite"`.
3. Cadastre Mercado e anote o ID.
4. Consulte `/api/lancamentos` e confirme o valor.
5. Encerre o Flask com Ctrl+C.
6. Inicie novamente e consulte a lista antes de enviar outro cadastro.
7. O lançamento deve continuar com o mesmo ID, valor e categoria.

## Banco local e testes

O diretório `instance/` e os arquivos SQLite são ignorados pelo Git. Para atualizar o código, preserve o arquivo do banco. Para fazer uma cópia de segurança simples, encerre o servidor e copie `instance/financeiro.sqlite3`.

Os testes usam diretórios e bancos temporários, sem alterar a base local de uso normal. Há testes de contrato nos dois repositórios, restrições do banco, operações simultâneas e cadastro/consulta Flask em processos Python separados.
