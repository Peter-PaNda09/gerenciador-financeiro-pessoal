# Gerenciador financeiro pessoal

Projeto integrado de Python/Programação Orientada a Objetos e HTML/CSS/JavaScript.

## Equipe

| Integrante | Frente |
| --- | --- |
| JV Guerra | Classes e modelagem de POO. |
| Marcos | Serviço e operações financeiras. |
| Igor | Cálculos e resumo financeiro. |
| JV Peixoto | Interface HTML/CSS/JavaScript. |
| Peterson | Gestão, integração, persistência e exportação. |

## Persistência SQLite na branch PETER

Esta etapa usa um repositório SQLite para guardar os lançamentos no computador, mantendo as classes reais de JV Guerra e o padrão HTTP combinado:

- `GET /api/categorias`: seis categorias predefinidas.
- `POST /api/lancamentos`: cadastro de receitas e despesas em centavos.
- `GET /api/lancamentos`: consulta com filtros de mês, tipo, categoria e descrição.
- Validações e respostas JSON conforme [docs/contrato-api.md](docs/contrato-api.md).

Na primeira execução, a aplicação cria automaticamente `instance/financeiro.sqlite3`, as tabelas e as seis categorias com os IDs do contrato. O banco começa sem lançamentos. **Os novos cadastros continuam salvos ao encerrar e reiniciar o Flask.** A inicialização não apaga registros nem duplica categorias.

O caminho padrão é relativo à pasta da aplicação, não ao terminal usado para iniciá-la. Aplicações que usam o mesmo arquivo recuperam os mesmos dados; computadores ou arquivos diferentes têm bases independentes. Não é necessário configurar Supabase, conta online ou credenciais.

O arquivo do banco fica fora do Git. Compartilhar o código no GitHub não envia os lançamentos cadastrados. O repositório em memória continua disponível para testes isolados. Registros de uma execução antiga em memória não são transferidos automaticamente para o SQLite.

PUT, DELETE, resumo, exportação e interface integrada ainda são próximas etapas. Os métodos de atualizar/excluir já existem no repositório para o serviço utilizar, mas as rotas correspondentes ainda não foram implementadas.

## Instalação e execução no Windows

Requer Python 3.10 ou superior. Na pasta do projeto, usando PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Se o comando disponível na sua máquina for `python`, use `python -m venv .venv` no primeiro passo. Não é necessário ativar o ambiente virtual para executar os comandos acima.

Abra no navegador:

- http://127.0.0.1:5000/ - informações da API e rotas disponíveis.
- http://127.0.0.1:5000/api/categorias - categorias.
- http://127.0.0.1:5000/api/lancamentos - inicialmente uma lista vazia.

O servidor permanece em execução nesse terminal. Use outro terminal para enviar os pedidos abaixo. Para encerrar, pressione Ctrl+C.

### Cadastrar uma despesa e consultá-la

```powershell
$lancamento = @{
    descricao = "Mercado"
    valor_centavos = 45000
    data = "2026-11-05"
    tipo = "despesa"
    categoria_id = 2
} | ConvertTo-Json

Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/lancamentos' -Method Post -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($lancamento))

Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/lancamentos?mes=2026-11&tipo=despesa'
```

O cadastro responde 201 com o objeto em `dados`. A consulta responde 200 com `dados` e `meta.quantidade`. R$ 450,00 é enviado como `45000`, não `450` nem `"45000"`.

## Testes

Na pasta do projeto:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

A suíte inclui os testes de domínio de JV Guerra, os dois repositórios e as rotas Flask usando SQLite. Também verifica o encerramento de um processo e a recuperação do cadastro em outro processo. Os testes usam bancos temporários, sem ler ou alterar seu banco real.

### Conferir a persistência manualmente

1. Inicie `app.py` e confirme que a página inicial mostra `"armazenamento": "sqlite"`.
2. Cadastre Mercado com o exemplo acima e anote o ID retornado.
3. Consulte `/api/lancamentos` e confirme o registro.
4. Encerre o servidor com Ctrl+C.
5. Execute novamente `.\.venv\Scripts\python.exe app.py`.
6. Consulte `/api/lancamentos` antes de cadastrar novamente: Mercado deve continuar com o mesmo ID e valor.

Não remova `instance/financeiro.sqlite3` para atualizar o projeto. Para uma cópia de segurança simples, encerre o servidor e copie esse arquivo para outro local.

## Organização

```text
app.py                         # Rotas, validação do contrato e criação da aplicação.
models.py                      # Classes de JV Guerra e data no fuso acordado.
repositories/sqlite.py         # Repositório persistente padrão.
repositories/memoria.py        # Repositório em memória para testes.
repositories/categorias.py     # Seis categorias compartilhadas pelos repositórios.
tests/test_api.py              # Cadastro, consulta, filtros e erros HTTP.
tests/test_repositorio_memoria.py
tests/test_repositorio_sqlite.py
tests/test_persistencia_processos.py
tests_models.py                # Testes de domínio de JV Guerra.
docs/contrato-api.md           # Acordo da API completa a implementar por etapas.
docs/repositorio-memoria.md    # Métodos internos e integração com o serviço.
docs/persistencia-sqlite.md     # Estrutura do banco e uso do repositório SQLite.
instance/financeiro.sqlite3    # Criado localmente e ignorado pelo Git.
```

As classes e os testes de Guerra foram incorporados preservando a autoria dos commits. A adaptação de fuso horário usa America/Sao_Paulo, como definido no contrato. O arquivo de modelos também possui dados auxiliares; as rotas selecionam somente os campos públicos do contrato.

## Próximas integrações

1. Marcos conecta seu serviço aos métodos documentados do repositório.
2. A rota passa a chamar esse serviço, mantendo os mesmos pedidos e respostas HTTP.
3. Igor integra o resumo usando as classes reais do domínio.
4. Peterson e Peixoto conectam a interface; o modo fictício continua útil até que todas as rotas consumidas por ela existam.
5. Completar as rotas de edição, exclusão e CSV usando o repositório persistente.

Esta entrega implementa a persistência após reinício e mantém o escopo HTTP inicial de categorias, cadastro e consulta. A interface integrada e as demais rotas continuam como próximas etapas.
