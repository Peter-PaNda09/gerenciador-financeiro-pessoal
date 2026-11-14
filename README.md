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

## Entrega inicial da branch PETER

Esta etapa implementa o repositório em memória e o primeiro fluxo HTTP usando as classes reais de JV Guerra:

- `GET /api/categorias`: seis categorias predefinidas.
- `POST /api/lancamentos`: cadastro de receitas e despesas em centavos.
- `GET /api/lancamentos`: consulta com filtros de mês, tipo, categoria e descrição.
- Validações e respostas JSON conforme [docs/contrato-api.md](docs/contrato-api.md).

O repositório começa sem lançamentos. Atualizar o navegador mantém os dados enquanto o servidor continua rodando. **Encerrar ou reiniciar o processo apaga os lançamentos.** Instâncias/processos diferentes não compartilham dados. Não há banco de dados ou credenciais nesta etapa.

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

A suíte inclui os testes de domínio de JV Guerra, o repositório em memória e as rotas Flask. As rotas são verificadas com o cliente de testes do Flask, sem precisar iniciar um servidor separado.

## Organização

```text
app.py                         # Rotas, validação do contrato e criação da aplicação.
models.py                      # Classes de JV Guerra e data no fuso acordado.
repositories/memoria.py        # Repositório provisório de Peterson.
tests/test_api.py              # Cadastro, consulta, filtros e erros HTTP.
tests/test_repositorio_memoria.py
tests_models.py                # Testes de domínio de JV Guerra.
docs/contrato-api.md           # Acordo da API completa a implementar por etapas.
docs/repositorio-memoria.md    # Métodos internos e integração com o serviço.
```

As classes e os testes de Guerra foram incorporados preservando a autoria dos commits. A adaptação de fuso horário usa America/Sao_Paulo, como definido no contrato. O arquivo de modelos também possui dados auxiliares; as rotas selecionam somente os campos públicos do contrato.

## Próximas integrações

1. Marcos conecta seu serviço aos métodos documentados do repositório.
2. A rota passa a chamar esse serviço, mantendo os mesmos pedidos e respostas HTTP.
3. Igor integra o resumo usando as classes reais do domínio.
4. Peterson e Peixoto conectam a interface; o modo fictício continua útil até que todas as rotas consumidas por ela existam.
5. Trocar o repositório em memória pela persistência definitiva e completar edição, exclusão e CSV.

Esta entrega avança as issues de repositório e integração; não conclui a exigência de persistência após reinício.
