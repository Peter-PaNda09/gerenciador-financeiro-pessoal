# Contrato da API - Gerenciador Financeiro Pessoal

**Versão:** 1.0 - 11/11/2026  
**Equipe:** JV Guerra, Marcos, Igor, JV Peixoto e Peterson.  
**Validação:** revisar em conjunto na issue #1 antes de considerar o contrato aprovado.

Este documento define o padrão de comunicação entre a interface JavaScript e o backend Python/Flask. Ele descreve o comportamento a implementar; sua existência não significa que as rotas já estão prontas.

## 1. Regras gerais

- Caminho base: `/api`. Exemplo local: `http://localhost:5000/api`.
- A página e os arquivos HTML/CSS/JS serão servidos pelo Flask no mesmo endereço do backend.
- O JavaScript chama caminhos relativos, como `/api/lancamentos`.
- Dados de requisição e resposta usam JSON, exceto o download CSV.
- POST e PUT exigem o cabeçalho `Content-Type: application/json`.
- O sistema inicial tem um único perfil, moeda BRL (real) e lançamentos manuais já realizados. Não há login nesta versão.
- Não há paginação nesta versão: a consulta devolve todos os registros correspondentes aos filtros.
- Dinheiro é enviado e calculado em centavos inteiros: R$ 450,00 = `45000`.
- Valores de lançamentos são sempre positivos; `tipo` determina entrada ou saída.
- Datas são strings no formato `AAAA-MM-DD`, sem horário. A tela pode exibi-las como DD/MM/AAAA.
- A data atual para validações considera o fuso `America/Sao_Paulo`.
- IDs são inteiros positivos e gerados pelo armazenamento; o navegador não escolhe o ID de um cadastro.
- Campos, tipos e nomes deste documento devem ser iguais em todas as implementações.

## 2. Padrão das respostas

### Sucesso com um objeto

```json
{
  "dados": {
    "id": 3,
    "descricao": "Mercado",
    "valor_centavos": 45000,
    "data": "2026-11-05",
    "tipo": "despesa",
    "categoria_id": 2
  }
}
```

### Sucesso com uma lista

```json
{
  "dados": [],
  "meta": {
    "quantidade": 0
  }
}
```

`meta.quantidade` é o número de itens em `dados`, depois de aplicar os filtros. Uma lista vazia é sucesso, com status 200.

### Erro

```json
{
  "erro": {
    "codigo": "VALIDACAO",
    "mensagem": "Confira os campos informados.",
    "campos": {
      "valor_centavos": "Informe um valor inteiro maior que zero."
    }
  }
}
```

`erro.campos` sempre existe e é um objeto. Pode estar vazio (`{}`) quando o erro não pertence a um campo específico. A interface mostra `erro.mensagem` e pode apresentar os erros de cada campo junto aos inputs.

## 3. Campos do lançamento

| Campo | Tipo JSON | Enviado em POST/PUT? | Regra |
| --- | --- | --- | --- |
| `id` | número inteiro | Não | Identificador gerado pelo sistema; permanece igual na edição. |
| `descricao` | string | Sim, obrigatório | De 1 a 120 caracteres após remover espaços nas extremidades. |
| `valor_centavos` | número inteiro | Sim, obrigatório | Maior que zero; não aceitar string, booleano ou número com parte decimal. |
| `data` | string | Sim, obrigatório | Data existente em `AAAA-MM-DD`, igual ou anterior à data atual. |
| `tipo` | string | Sim, obrigatório | Exatamente `receita` ou `despesa`, em minúsculas. |
| `categoria_id` | número inteiro | Sim, obrigatório | Categoria existente e compatível com o tipo do lançamento. |

POST e PUT recebem exatamente os cinco campos graváveis. Campo ausente, desconhecido ou com valor `null` gera erro 400. Não enviar `id`, nome da categoria ou totais no corpo dessas operações.

O backend repete todas as validações, mesmo quando o formulário já validou os dados. Falhas de validação não alteram o armazenamento.

## 4. Categorias iniciais

As categorias abaixo são predefinidas. A criação inicial deve manter os mesmos IDs em todas as máquinas e poder ser repetida sem duplicá-las. Não haverá cadastro/edição/exclusão de categorias pela API nesta versão.

| ID | Nome | Tipo permitido |
| --- | --- | --- |
| 1 | Salário | receita |
| 2 | Alimentação | despesa |
| 3 | Moradia | despesa |
| 4 | Transporte | despesa |
| 5 | Outras receitas | receita |
| 6 | Outras despesas | despesa |

A interface carrega as categorias pela API, usa seus nomes na exibição e envia somente `categoria_id` no lançamento.

## 5. Rotas da versão 1

| Método | Rota | Finalidade | Sucesso |
| --- | --- | --- | --- |
| GET | `/api/categorias` | Consultar categorias predefinidas. | 200 |
| GET | `/api/lancamentos` | Consultar lançamentos e filtros. | 200 |
| POST | `/api/lancamentos` | Cadastrar um lançamento. | 201 |
| PUT | `/api/lancamentos/<id>` | Substituir os campos graváveis de um lançamento. | 200 |
| DELETE | `/api/lancamentos/<id>` | Excluir um lançamento. | 200 |
| GET | `/api/resumo` | Consultar indicadores de um mês. | 200 |
| GET | `/api/exportar` | Baixar lançamentos em CSV. | 200 |

`<id>` é substituído pelo identificador real, por exemplo `/api/lancamentos/3`.

### 5.1. Consultar categorias

**Pedido:** `GET /api/categorias`

**Resposta 200**, ordenada por ID crescente:

```json
{
  "dados": [
    {"id": 1, "nome": "Salário", "tipo": "receita"},
    {"id": 2, "nome": "Alimentação", "tipo": "despesa"},
    {"id": 3, "nome": "Moradia", "tipo": "despesa"},
    {"id": 4, "nome": "Transporte", "tipo": "despesa"},
    {"id": 5, "nome": "Outras receitas", "tipo": "receita"},
    {"id": 6, "nome": "Outras despesas", "tipo": "despesa"}
  ],
  "meta": {"quantidade": 6}
}
```

Não há parâmetros de consulta nesta rota. A interface filtra as categorias pelo tipo selecionado no formulário.

### 5.2. Consultar lançamentos

**Pedido:** `GET /api/lancamentos`

Parâmetros opcionais:

| Parâmetro | Exemplo | Comportamento |
| --- | --- | --- |
| `mes` | `2026-11` | Seleciona datas daquele mês/ano. |
| `tipo` | `despesa` | Seleciona apenas `receita` ou `despesa`. |
| `categoria_id` | `2` | Seleciona uma categoria existente. |
| `busca` | `mercado` | Procura trecho da descrição sem diferenciar maiúsculas/minúsculas; acentos continuam significativos. |

- Sem filtros, retorna todos os lançamentos.
- Todos os filtros informados são combinados: cada registro precisa atender a todos eles.
- Ordenação: data decrescente; em datas iguais, ID decrescente.
- O mês precisa ter formato `AAAA-MM` e representar um mês válido.
- Omitir parâmetros sem seleção; não enviar valores como `tipo=todos` ou `mes=`.
- Parâmetros desconhecidos, repetidos ou com valores vazios geram 400. Para `busca`, remover espaços nas extremidades e omitir o parâmetro se ficar vazio.
- `categoria_id` é enviado como texto na URL, mas deve representar um inteiro positivo de uma categoria existente.
- Se tipo e categoria forem válidos, mas os filtros combinados não encontrarem registros, retornar lista vazia com 200.

**Exemplo:** `GET /api/lancamentos?mes=2026-11&tipo=despesa&categoria_id=2&busca=mercado`

**Resposta 200:**

```json
{
  "dados": [
    {
      "id": 3,
      "descricao": "Mercado",
      "valor_centavos": 45000,
      "data": "2026-11-05",
      "tipo": "despesa",
      "categoria_id": 2
    }
  ],
  "meta": {"quantidade": 1}
}
```

### 5.3. Cadastrar lançamento

**Pedido:** `POST /api/lancamentos`

**Cabeçalho:** `Content-Type: application/json`

**Corpo:**

```json
{
  "descricao": "Mercado",
  "valor_centavos": 45000,
  "data": "2026-11-05",
  "tipo": "despesa",
  "categoria_id": 2
}
```

**Resposta 201:**

```json
{
  "dados": {
    "id": 3,
    "descricao": "Mercado",
    "valor_centavos": 45000,
    "data": "2026-11-05",
    "tipo": "despesa",
    "categoria_id": 2
  }
}
```

O ID 3 é ilustrativo; o ID real é gerado pelo repositório. Pedidos repetidos de cadastro criam registros diferentes; a interface deve impedir cliques repetidos enquanto o envio estiver em andamento.

### 5.4. Editar lançamento

**Pedido:** `PUT /api/lancamentos/3`

PUT exige todos os cinco campos graváveis, mesmo quando somente o valor mudar. Não há edição parcial por PATCH nesta versão.

**Corpo:**

```json
{
  "descricao": "Mercado",
  "valor_centavos": 50000,
  "data": "2026-11-05",
  "tipo": "despesa",
  "categoria_id": 2
}
```

**Resposta 200:**

```json
{
  "dados": {
    "id": 3,
    "descricao": "Mercado",
    "valor_centavos": 50000,
    "data": "2026-11-05",
    "tipo": "despesa",
    "categoria_id": 2
  }
}
```

O ID não muda. É permitido alterar o tipo se a categoria enviada continuar compatível. Dados inválidos geram 400; ID positivo inexistente gera 404. Nenhuma mudança parcial é salva quando há erro.

### 5.5. Excluir lançamento

**Pedido:** `DELETE /api/lancamentos/4`

Não enviar corpo JSON.

**Resposta 200:**

```json
{
  "dados": {
    "id": 4,
    "excluido": true
  }
}
```

A exclusão é definitiva. A interface pede confirmação antes de enviar o pedido. Excluir um ID positivo inexistente, inclusive um registro já excluído, gera 404.

### 5.6. Consultar resumo financeiro

**Pedido:** `GET /api/resumo?mes=2026-11`

`mes` é obrigatório e precisa representar um mês válido em `AAAA-MM`. Esta rota aceita somente esse parâmetro, sem repetição.

Os exemplos abaixo consideram os quatro lançamentos fictícios da seção 7, sem a edição e a exclusão exemplificadas acima.

**Resposta 200:**

```json
{
  "dados": {
    "mes": "2026-11",
    "receitas_centavos": 300000,
    "despesas_centavos": 150000,
    "resultado_centavos": 150000,
    "saldo_acumulado_centavos": 150000,
    "despesas_por_categoria": [
      {"categoria_id": 3, "categoria_nome": "Moradia", "valor_centavos": 90000},
      {"categoria_id": 2, "categoria_nome": "Alimentação", "valor_centavos": 45000},
      {"categoria_id": 4, "categoria_nome": "Transporte", "valor_centavos": 15000}
    ]
  }
}
```

Regras dos indicadores:

- `receitas_centavos`: soma das receitas do mês solicitado.
- `despesas_centavos`: soma das despesas do mês solicitado, como valor positivo.
- `resultado_centavos`: receitas menos despesas do mesmo mês; pode ser negativo.
- `saldo_acumulado_centavos`: receitas menos despesas de todos os registros até o último dia do mês solicitado. O saldo inicial é zero; não há filtro de data inicial nesse indicador.
- `despesas_por_categoria`: somente categorias com despesas no mês; ordenar por valor decrescente e, em empate, por ID crescente.
- Sem movimentos no mês, receitas, despesas e resultado são zero; o agrupamento é `[]`. O saldo acumulado pode continuar diferente de zero por causa de meses anteriores.
- Os cartões do painel usam esta rota e consideram o mês completo. Filtros de tipo, categoria e busca afetam a lista e a exportação, não os cartões mensais.
- O saldo é dos lançamentos cadastrados; não representa uma sincronização com saldo bancário.

### 5.7. Exportar lançamentos

**Pedido:** `GET /api/exportar?mes=2026-11&tipo=despesa`

Aceita os mesmos filtros, validações e ordenação de `GET /api/lancamentos`. Exporta todos os registros correspondentes, sem paginação.

**Resposta 200:** arquivo CSV, não JSON.

Cabeçalhos esperados:

```http
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="lancamentos-2026-11.csv"
```

- Sem filtro de mês, nomear o arquivo como `lancamentos.csv`.
- Usar UTF-8 com BOM e separador ponto e vírgula (`;`).
- Colunas: `id;data;descricao;tipo;categoria;valor`.
- Data em `AAAA-MM-DD`; valor em reais com duas casas e vírgula decimal, sem símbolo R$.
- O valor é positivo; a coluna `tipo` identifica receita ou despesa.
- Converter `categoria_id` para o nome da categoria na exportação.
- Usar um gerador CSV que preserve colunas quando descrições contiverem aspas, ponto e vírgula ou quebras de linha.
- Consulta sem resultados gera um arquivo apenas com cabeçalho.
- Erros de filtro continuam seguindo o padrão JSON de erro, com status 400.

Exemplo com as despesas do cenário original:

```csv
id;data;descricao;tipo;categoria;valor
4;2026-11-07;Ônibus;despesa;Transporte;150,00
3;2026-11-05;Mercado;despesa;Alimentação;450,00
2;2026-11-03;Aluguel;despesa;Moradia;900,00
```

## 6. Códigos de erro

| Status HTTP | `erro.codigo` | Quando usar |
| --- | --- | --- |
| 400 | `VALIDACAO` | Campos, filtros ou ID no caminho com valor inválido. |
| 400 | `JSON_INVALIDO` | Corpo com sintaxe JSON inválida. |
| 404 | `NAO_ENCONTRADO` | ID positivo inexistente em edição ou exclusão. |
| 415 | `TIPO_CONTEUDO_INVALIDO` | POST/PUT sem `Content-Type: application/json`. |
| 500 | `ERRO_INTERNO` | Falha inesperada do servidor. |

JSON válido que não seja um objeto, como uma lista ou `null`, gera 400/VALIDACAO. IDs no caminho que não sejam inteiros positivos geram 400/VALIDACAO. Os erros das rotas documentadas devem seguir o envelope da seção 2.

Exemplo de categoria incompatível:

```json
{
  "erro": {
    "codigo": "VALIDACAO",
    "mensagem": "Confira os campos informados.",
    "campos": {
      "categoria_id": "A categoria selecionada não pertence ao tipo informado."
    }
  }
}
```

Exemplo de registro inexistente:

```json
{
  "erro": {
    "codigo": "NAO_ENCONTRADO",
    "mensagem": "Lançamento não encontrado.",
    "campos": {}
  }
}
```

Falha de conexão não é uma resposta JSON da API. O JavaScript deve tratar esse caso e mostrar uma mensagem própria, por exemplo: "Não foi possível conectar ao servidor. Tente novamente."

## 7. Dados fictícios para desenvolver a interface

Peixoto pode usar a resposta abaixo como dados simulados enquanto a API é implementada. O backend e os testes podem usar a mesma massa de referência. Esses registros não devem ser inseridos automaticamente em toda inicialização; a carga de demonstração deve ser explícita para evitar duplicações.

**Exemplo de resposta para `GET /api/lancamentos?mes=2026-11`:**

```json
{
  "dados": [
    {"id": 4, "descricao": "Ônibus", "valor_centavos": 15000, "data": "2026-11-07", "tipo": "despesa", "categoria_id": 4},
    {"id": 3, "descricao": "Mercado", "valor_centavos": 45000, "data": "2026-11-05", "tipo": "despesa", "categoria_id": 2},
    {"id": 2, "descricao": "Aluguel", "valor_centavos": 90000, "data": "2026-11-03", "tipo": "despesa", "categoria_id": 3},
    {"id": 1, "descricao": "Salário", "valor_centavos": 300000, "data": "2026-11-02", "tipo": "receita", "categoria_id": 1}
  ],
  "meta": {"quantidade": 4}
}
```

Resultados esperados, considerando apenas esses registros:

| Cenário | Receitas | Despesas | Resultado |
| --- | --- | --- | --- |
| Original | R$ 3.000,00 | R$ 1.500,00 | R$ 1.500,00 |
| Editar Mercado para R$ 500,00 | R$ 3.000,00 | R$ 1.550,00 | R$ 1.450,00 |
| Depois excluir Ônibus | R$ 3.000,00 | R$ 1.400,00 | R$ 1.600,00 |

O exemplo de POST da seção 5.3 é um exemplo de cadastro separado. Se os quatro registros de referência já estiverem carregados, não repetir o POST esperando que o mesmo registro seja reaproveitado.

## 8. Responsabilidades e fluxo interno

| Integrante | Parte relacionada ao contrato |
| --- | --- |
| JV Guerra | Objetos do domínio, construtores, encapsulamento, herança, polimorfismo e conversão de objetos para dicionários. |
| Marcos | Serviço financeiro: operações, validações e aplicação de filtros em colaboração com o repositório. |
| Igor | Cálculos e agrupamentos retornados pela rota de resumo. |
| JV Peixoto | HTML/CSS/JS, dados simulados, chamadas HTTP, apresentação dos resultados e feedback ao usuário. |
| Peterson | Rotas Flask, tradução de erros, repositório, persistência, exportação e integração. |

Fluxo: interface -> rota Flask -> serviço/objetos/cálculos -> repositório quando necessário -> resposta da rota -> atualização da interface.

O contrato HTTP não obriga que cada rota corresponda a uma classe. Os nomes dos métodos internos devem ser combinados pelo trio e por Peterson, preservando a API pública definida aqui.

## 9. Como começar e conferir a integração

1. Revisar este documento na issue #1 e disponibilizá-lo na `main`.
2. Guerra prepara os objetos mínimos; Peterson disponibiliza o repositório provisório em memória; Peixoto usa os dados simulados.
3. Marcos implementa cadastro e consulta; Igor prepara o resumo com dados conhecidos.
4. Peterson e Peixoto integram primeiro POST e GET de lançamentos.
5. Após um cadastro bem-sucedido, a interface consulta novamente a lista e o resumo do mês selecionado.
6. Repetir a atualização após edição e exclusão, preservando os filtros escolhidos na tela.
7. Trocar a implementação em memória pela persistente, completar os demais fluxos e conferir o CSV.

Checklist comum de aceite:

- [ ] Nomes de campos e tipos iguais aos exemplos.
- [ ] Dinheiro em centavos inteiros no JSON e na lógica financeira.
- [ ] Formulário usa categorias compatíveis e não envia ID no cadastro.
- [ ] Lista vazia retorna 200 com `dados: []` e quantidade zero.
- [ ] Filtros e ordenação são iguais na consulta e na exportação.
- [ ] Cadastro responde 201; edição e exclusão respondem 200.
- [ ] Erros esperados usam o envelope `erro` e os status documentados.
- [ ] Nenhuma operação inválida salva alteração parcial.
- [ ] Exemplos financeiros conferem antes e depois de editar/excluir.
- [ ] Saldo acumulado inclui meses anteriores, mesmo quando o mês consultado estiver vazio.
- [ ] Atualizar a página e reiniciar o backend preserva os dados na versão persistente.

## 10. Alterações neste acordo

Mudanças em campos, rotas, filtros ou respostas devem ser discutidas na issue correspondente e atualizadas neste arquivo antes da integração. Avisar quem consome a informação, atualizar os exemplos e registrar a mudança abaixo. Depois da revisão e da entrada do documento na `main`, concluir a issue #1.

| Versão | Data | Mudança |
| --- | --- | --- |
| 1.0 | 11/11/2026 | Contrato inicial para revisão da equipe. |
