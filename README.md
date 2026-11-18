# Gerenciador Financeiro Pessoal

Projeto acadêmico de Programação Orientada a Objetos e Desenvolvimento em JavaScript, desenvolvido na Faculdade Anhanguera Uberlândia.

A aplicação permite registrar receitas e despesas, acompanhar o resultado financeiro e consultar movimentações por período.

## Funcionalidades

- Cadastro, consulta, edição e exclusão de lançamentos.
- Classificação por categorias.
- Pesquisa por descrição e filtros por mês, tipo e categoria.
- Resumo com receitas, despesas, resultado e saldo acumulado.
- Distribuição das despesas por categoria.
- Exportação dos lançamentos filtrados em CSV.
- Interface responsiva com validações e mensagens de sucesso ou erro.
- Persistência compartilhada no Supabase.
- Módulo complementar de metas de economia pelo terminal.

## Tecnologias

Python, Flask, HTML, CSS, JavaScript, Supabase/PostgreSQL, pytest, Git e GitHub.

## Como executar

### 1. Pré-requisitos

- Python 3.11 ou superior.
- Git.
- Navegador atualizado.
- Acesso à internet e configuração do projeto Supabase.

### 2. Baixar o projeto

```powershell
git clone https://github.com/Peter-PaNda09/gerenciador-financeiro-pessoal.git
cd gerenciador-financeiro-pessoal
```

### 3. Criar o ambiente e instalar as dependências

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se o computador reconhecer apenas `python`, utilize `python -m venv .venv`.

### 4. Configurar o banco

Para utilizar o banco compartilhado do grupo, solicite a configuração ao responsável pelo Supabase. Não é necessário recriar as tabelas.

Para configurar um projeto Supabase novo, execute o script [docs/script_supabase.sql](docs/script_supabase.sql) no SQL Editor e configure as permissões de acesso adequadas.

Crie o arquivo local de configuração, caso ainda não exista:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Abra `.env` e preencha:

```dotenv
SUPABASE_URL=https://SEU-PROJETO.supabase.co
SUPABASE_KEY=SUA_CHAVE_DO_BACKEND
FLASK_DEBUG=0
```

A chave precisa ter as permissões necessárias para acessar as tabelas. O código não configura essas permissões automaticamente.

O `.env` contém a configuração local e é ignorado pelo Git. O `.env.example` contém apenas exemplos. Nunca publique chaves privilegiadas.

### 5. Iniciar a aplicação

```powershell
.\.venv\Scripts\python.exe app.py
```

Abra [http://127.0.0.1:5000](http://127.0.0.1:5000).

A interface depende do Flask: não abra o HTML diretamente.

## Persistência

Os lançamentos são armazenados nas tabelas `categorias` e `lancamentos` do Supabase.

Os valores financeiros são armazenados em centavos inteiros. Por exemplo, R$ 450,00 corresponde a `45000`.

Reiniciar o Flask não apaga os dados. Computadores configurados para o mesmo banco acessam o mesmo conjunto de lançamentos após uma nova consulta.

A versão acadêmica utiliza um perfil compartilhado, sem autenticação individual.

## Testes automatizados

Instale as dependências dos testes:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-testes.txt
```

Execute a suíte com uma pasta temporária exclusiva:

```powershell
$pastaTemporariaTeste = Join-Path (Get-Location).Path ("tmp-testes-" + [guid]::NewGuid().ToString("N"))
.\.venv\Scripts\python.exe -m pytest -q --basetemp $pastaTemporariaTeste
```

Resultado da revisão de 17/11/2026: **72 testes aprovados, sem falhas ou xfail**.

A suíte cobre cadastro, consulta, edição, exclusão, filtros, validações, resumo financeiro, CSV, classes POO e o módulo complementar de metas.

Os testes da API usam as rotas, o serviço e os modelos reais com um repositório fictício isolado. Não precisam de `.env` nem acessam ou alteram os dados do Supabase.

Essa suíte não substitui a conferência manual da aplicação com o banco real.

Detalhes e evidências: [docs/testes-api-peter.md](docs/testes-api-peter.md).

## Módulo complementar de metas

Desenvolvido por Daniel para a disciplina de POO, com correção posterior de Peterson para entradas não finitas.

```powershell
.\.venv\Scripts\python.exe .\modulo-complementar\meta_economia.py
```

Após a demonstração e os testes internos, o menu permite criar metas, adicionar economias e consultar o progresso.

As metas ficam na memória durante a execução. Esse módulo é separado do site e do Supabase.

Revisão: [docs/revisao-meta-daniel.md](docs/revisao-meta-daniel.md).

## Organização do código

- `app.py`: interface e rotas Flask.
- `models.py`: classes e validações do domínio.
- `servico.py`: operações, filtros, cálculos e exportação.
- `persistencia_supabase.py`: acesso ao banco remoto.
- `templates/index.html`: estrutura da interface.
- `static/css/styles.css`: estilos e responsividade.
- `static/js/app.js`: interação, DOM e chamadas à API.
- `tests/`: testes da API e do módulo complementar.
- `tests_models.py`: testes das classes de domínio.
- `docs/`: documentação, SQL, diagrama e evidências.

## Programação Orientada a Objetos

- **Abstração:** `Transacao` define comportamentos comuns.
- **Herança:** `Receita` e `Despesa` herdam de `Transacao`.
- **Polimorfismo:** `impacto_no_saldo()` retorna valores positivos ou negativos conforme a classe.
- **Encapsulamento:** propriedades validam os atributos.
- **Associação:** cada transação está vinculada a uma categoria.

![Diagrama de classes](docs/diagrama_classes.png)

[Diagrama editável em PlantUML](docs/diagrama_classes.puml).

## Integrantes

| Integrante | Disciplinas |
| --- | --- |
| Igor Assis | POO e Desenvolvimento em JavaScript |
| João Vitor Costa Peixoto | POO e Desenvolvimento em JavaScript |
| João Vitor Guerra Rodrigues | POO e Desenvolvimento em JavaScript |
| Marcos Vinícius Cavalcante | POO e Desenvolvimento em JavaScript |
| Peterson Mário | POO e Desenvolvimento em JavaScript |
| Daniel Almeida | Somente POO, no módulo complementar |

As contribuições e a evolução do projeto estão registradas no histórico de commits e nos pull requests.

## Roteiro de conferência manual

- Cadastrar uma receita e uma despesa.
- Editar um lançamento e conferir o resumo.
- Excluir um lançamento.
- Utilizar pesquisa e filtros.
- Exportar e conferir o CSV.
- Reiniciar o Flask e verificar a persistência.
