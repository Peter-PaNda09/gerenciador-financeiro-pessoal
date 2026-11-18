# Testes da API e correções - contribuição de Peterson

Relatório atualizado em 17/11/2026. Base: `main` `df7f9bc`, com os testes e as correções locais de Peterson na branch `PETER`, na pasta `teste-api-peter`.

## Resultado atual

**72 testes aprovados, sem falhas, erros, testes pulados ou marcações de falha conhecida.** A suíte foi executada normalmente, sem `--runxfail`. O resultado por caso está em [resultado-testes-peter.json](evidencias/resultado-testes-peter.json).

| Grupo | Aprovados | Pendências conhecidas |
| --- | ---: | ---: |
| Fluxos da API | 31 | 0 |
| Consistência da API e ligação com HTML | 15 | 0 |
| Módulo complementar de Daniel | 20 | 0 |
| Testes de classes já existentes | 6 | 0 |
| **Total** | **72** | **0** |

Na verificação inicial havia 65 testes aprovados e 7 casos marcados como falha conhecida. Esses sete casos representavam quatro problemas. Peterson corrigiu os trechos de funcionamento, executou novamente os testes e retirou as marcações `pendencia` e `xfail` dos casos resolvidos. As verificações dentro dos testes foram preservadas.

Os casos corrigidos agora são testes normais: se uma alteração reintroduzir os erros, eles falharão. O resultado de 72 aprovações corresponde aos cenários cobertos pela suíte; não é uma garantia de ausência de qualquer defeito no sistema.

## Correções realizadas por Peterson

| Referência local | Arquivo | Correção e efeito | Casos resolvidos |
| --- | --- | --- | ---: |
| API-01 | `servico.py` | `valor_centavos` deixa de passar pelo conversor de reais. O valor original segue para a classe `Transacao`, que exige inteiro positivo. Texto e decimal são rejeitados, evitando multiplicação por 100 no cadastro e na edição. | 3 |
| API-02 | `servico.py` | Descrição deixa de ser convertida automaticamente com `str()`. Um valor nulo chega à validação da classe e é rejeitado, em vez de virar a palavra `None`. | 1 |
| WEB-01 | `templates/index.html` | Adicionados `current-section`, `status-dot` e `connection-status`, identificadores procurados pelo JavaScript ao iniciar. Texto inicial passa a ser `Conectando...`. | 1 |
| META-01 | `modulo-complementar/meta_economia.py` | Adicionados `import math` e `math.isfinite()` sobre o valor multiplicado por 100, antes de `round()`, na criação da meta e no aporte. Valores infinitos geram `ValueError`, já tratado pelo menu. | 2 |

As referências API-01, API-02, WEB-01 e META-01 são identificadores deste relatório, não números de issues abertas no GitHub.

O trabalho original dos colegas continua identificado no histórico da aplicação. Daniel implementou a correção do nome Xbox e o menu; Peterson acrescentou a proteção contra valores não finitos e os testes independentes que a verificam.

## Arquivos dos testes e da documentação

| Arquivo | Função |
| --- | --- |
| `requirements-testes.txt` | Dependências para a suíte isolada. Não é a lista completa de instalação da aplicação com Supabase. |
| `pytest.ini` | Descoberta dos novos testes e dos seis testes existentes de `tests_models.py`. |
| `tests/conftest.py` | Configuração do Flask real para testes e bloqueio de rede. |
| `tests/repositorio_fake.py` | Banco fictício exclusivo dos testes, recriado para cada caso. |
| `tests/test_api_fluxos.py` | Cadastro, consulta, edição, exclusão, filtros, validações, cálculos e CSV. |
| `tests/test_api_consistencia.py` | Consistência financeira, dados necessários e ligação entre HTML e JS. |
| `tests/test_meta_daniel.py` | Verificação do módulo de Daniel, incluindo a proteção corrigida por Peterson e entrada pelo terminal. |
| `docs/evidencias/resultado-testes-peter.json` | Resultado da execução atual e histórico resumido das correções. |
| `docs/revisao-meta-daniel.md` | Revisão do módulo complementar e distinção das contribuições. |

## Instalação e execução no Windows

Abra o PowerShell na pasta desta cópia do projeto. Se ainda não houver ambiente virtual:

```powershell
py -m venv .venv
```

Se o computador reconhecer somente `python`, use `python -m venv .venv`.

Instale as dependências dos testes:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-testes.txt
```

Escolha uma pasta temporária nova, exclusiva para testes, e execute a suíte:

```powershell
$pastaTemporariaTeste = Join-Path (Get-Location).Path ("tmp-testes-" + [guid]::NewGuid().ToString("N"))
.\.venv\Scripts\python.exe -m pytest -q --basetemp $pastaTemporariaTeste
```

Resultado esperado na versão corrigida:

```text
72 passed
```

A pasta explícita evita o erro de permissão observado no diretório temporário padrão do pytest no computador de Peterson. A regra `tmp-testes-*/` do `.gitignore` mantém essas pastas fora do versionamento.

Não é necessário iniciar o Flask separadamente, configurar `.env` ou acessar Supabase. Para executar somente a API:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_api_fluxos.py tests/test_api_consistencia.py --basetemp $pastaTemporariaTeste
```

Resultado esperado: **46 testes aprovados**. Para conferir somente o módulo complementar:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_meta_daniel.py --basetemp $pastaTemporariaTeste
```

Resultado esperado: **20 testes aprovados**. Os seis testes de classes existentes completam o total de 72.

## Como a aplicação é testada

```text
requisição do teste
        -> rota real do app.py
        -> GerenciadorFinanceiro real
        -> Receita, Despesa e Categoria reais
        -> repositório fictício exclusivo dos testes
        -> resposta real do Flask
```

O banco fictício fornece os métodos que o serviço usa. Ele é carregado somente nos testes e não substitui o Supabase ao executar a aplicação normalmente. O adaptador remoto não é importado nesse fluxo, evitando leitura de configuração e criação do cliente remoto. Conexões de rede são bloqueadas na importação e durante os casos.

Cada teste recebe dados próprios. As categorias fictícias usam IDs 11, 22, 33 e 44, evitando depender dos identificadores de outra base. As datas históricas permitem conferir filtros e saldo acumulado sem criar lançamentos futuros.

## Escopo e limites

- Os testes verificam operações, validações, filtros, cálculos, CSV e tratamento de erros pela API.
- A conferência WEB-01 verifica a presença dos identificadores no HTML servido; não substitui um teste completo em navegador.
- Não são exercitados o adaptador, as permissões, as tabelas nem a conexão do Supabase real. Nenhum lançamento do grupo foi alterado por esta suíte.
- O módulo complementar continua usando memória durante a sessão e não é integrado ao site ou ao banco remoto.
- O contrato antigo da equipe não é exigido pela suíte e permanece no local original, sem alteração nesta atualização.
- Na data deste relatório, as correções estão na `PETER` local, ainda sem commit ou publicação. A atualização dos relatórios não cria commit nem modifica a `main`.

## Como explicar a contribuição ao grupo

Peterson acrescentou testes que verificam a API real com um banco fictício isolado, reproduziu quatro problemas e corrigiu o tratamento de valores, descrição, ligação entre HTML e JavaScript e entradas não finitas nas metas. A suíte passou de 65 aprovações e 7 falhas conhecidas para 72 aprovações. Os testes dos casos corrigidos continuam ativos para detectar se os problemas voltarem.
