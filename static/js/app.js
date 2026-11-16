(() => {
  "use strict";

  const API = "/api";
  const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
  const $ = (id) => document.getElementById(id);
  const estado = { categorias: [], lancamentos: [], listaId: 0, resumoId: 0 };
  let temporizadorBusca;
  let temporizadorAviso;

  function hojeBrasil() {
    const partes = new Intl.DateTimeFormat("en-US", {
      timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit", day: "2-digit"
    }).formatToParts(new Date());
    const p = Object.fromEntries(partes.map((item) => [item.type, item.value]));
    return `${p.year}-${p.month}-${p.day}`;
  }
  const reais = (centavos) => moeda.format((Number(centavos) || 0) / 100);
  const dataBR = (iso) => /^\d{4}-\d\d-\d\d$/.test(String(iso || ""))
    ? iso.split("-").reverse().join("/") : "—";

  function aviso(texto, erro = false) {
    const area = $("global-feedback");
    area.textContent = texto;
    area.classList.toggle("feedback-error", erro);
    area.hidden = false;
    clearTimeout(temporizadorAviso);
    temporizadorAviso = setTimeout(() => { area.hidden = true; }, 7000);
  }

  function status(texto, falhou = false) {
    $("connection-status").textContent = texto;
    $("status-dot").classList.remove("waiting");
    $("status-dot").classList.toggle("status-error", falhou);
  }

  function query(filtros) {
    const p = new URLSearchParams();
    Object.entries(filtros).forEach(([chave, valor]) => {
      if (valor !== "" && valor !== null && valor !== undefined) p.set(chave, String(valor));
    });
    return p.toString() ? `?${p.toString()}` : "";
  }

  // API centralizada: trata erros de rede, HTTP e mensagens Flask.
  async function api(caminho, metodo = "GET", dados = undefined, csv = false) {
    let resposta;
    try {
      resposta = await fetch(`${API}${caminho}`, {
        method: metodo,
        headers: dados === undefined ? {} : { "Content-Type": "application/json" },
        body: dados === undefined ? undefined : JSON.stringify(dados),
        cache: "no-store"
      });
    } catch (_) {
      throw new Error("Não foi possível conectar ao Flask. Verifique se o servidor está ligado.");
    }
    if (!resposta.ok) {
      let conteudo = {};
      try { conteudo = await resposta.json(); } catch (_) { /* resposta sem JSON */ }
      const erro = new Error(conteudo?.erro?.mensagem || `Erro HTTP ${resposta.status}.`);
      erro.campos = conteudo?.erro?.campos || {};
      throw erro;
    }
    if (csv) return resposta.blob();
    const json = await resposta.json();
    if (!json || !("dados" in json)) throw new Error("Resposta inválida da API Flask.");
    return json.dados;
  }

  function tipoFormulario() {
    return document.querySelector('input[name="tipo"]:checked')?.value || "despesa";
  }
  function preencherSelect(elemento, lista, texto) {
    const antes = elemento.value;
    elemento.replaceChildren(new Option(texto, ""));
    lista.forEach((c) => elemento.add(new Option(c.nome, String(c.id))));
    if (lista.some((c) => String(c.id) === antes)) elemento.value = antes;
  }
  function categoriasDoFormulario(manter = null) {
    const select = $("entry-category");
    const antes = manter === null ? select.value : String(manter);
    const validas = estado.categorias.filter((c) => c.tipo === tipoFormulario());
    preencherSelect(select, validas, "Selecione uma categoria");
    if (validas.some((c) => String(c.id) === antes)) select.value = antes;
  }
  function nomeCategoria(id) {
    return estado.categorias.find((c) => c.id === Number(id))?.nome || "Categoria não encontrada";
  }

  async function carregarCategorias() {
    try {
      const lista = await api("/categorias");
      if (!Array.isArray(lista)) throw new Error("Lista de categorias inválida.");
      estado.categorias = lista.map((c) => ({
        ...c, id: Number(c.id), tipo: c.tipo || c.tipo_permitido
      }));
      preencherSelect($("category-filter"), estado.categorias, "Todas as categorias");
      categoriasDoFormulario();
      status("Conectado ao servidor");
    } catch (erro) {
      status("Não foi possível carregar as categorias", true);
      aviso(erro.message, true);
      $("entry-category").replaceChildren(new Option("Categorias indisponíveis", ""));
    }
  }

  function filtros() {
    return {
      mes: $("list-month-filter").value,
      tipo: $("type-filter").value,
      categoria_id: $("category-filter").value,
      busca: $("search-filter").value.trim()
    };
  }

  function td(texto, classe = "") {
    const celula = document.createElement("td");
    celula.textContent = texto;
    if (classe) celula.className = classe;
    return celula;
  }

  function exibirLancamentos(lista) {
    const corpo = $("transactions-body");
    const mensagem = $("list-state");
    corpo.replaceChildren();
    $("results-count").textContent = `${lista.length} ${lista.length === 1 ? "lançamento" : "lançamentos"}`;
    mensagem.hidden = lista.length > 0;
    mensagem.classList.remove("state-error");
    mensagem.textContent = lista.length ? "" : "Nenhum lançamento encontrado nesse período.";

    lista.forEach((registro) => {
      const linha = document.createElement("tr");
      const descricao = td(registro.descricao);
      const categoria = td(nomeCategoria(registro.categoria_id));
      const data = td(dataBR(registro.data));
      const tipo = td("");
      const tag = document.createElement("span");
      tag.className = `type-badge ${registro.tipo}`;
      tag.textContent = registro.tipo === "receita" ? "Receita" : "Despesa";
      tipo.append(tag);
      const valor = td(`${registro.tipo === "receita" ? "+" : "−"} ${reais(registro.valor_centavos)}`, `amount-cell ${registro.tipo}`);
      const acoes = td("", "row-actions");

      const editar = document.createElement("button");
      editar.type = "button";
      editar.className = "icon-button row-action";
      editar.textContent = "✎";
      editar.setAttribute("aria-label", `Editar ${registro.descricao}`);
      editar.addEventListener("click", () => abrirEdicao(registro));

      const excluir = document.createElement("button");
      excluir.type = "button";
      excluir.className = "icon-button row-action delete-action";
      excluir.textContent = "×";
      excluir.setAttribute("aria-label", `Excluir ${registro.descricao}`);
      excluir.addEventListener("click", () => excluirLancamento(registro));

      acoes.append(editar, excluir);
      linha.append(descricao, categoria, data, tipo, valor, acoes);
      corpo.append(linha);
    });
  }

  async function carregarLancamentos() {
    const atual = ++estado.listaId;
    const mensagem = $("list-state");
    mensagem.hidden = false;
    mensagem.classList.remove("state-error");
    mensagem.textContent = "Carregando lançamentos...";
    try {
      const lista = await api(`/lancamentos${query(filtros())}`);
      if (atual !== estado.listaId) return;
      if (!Array.isArray(lista)) throw new Error("Lista de lançamentos inválida.");
      estado.lancamentos = lista;
      exibirLancamentos(lista);
    } catch (erro) {
      if (atual !== estado.listaId) return;
      estado.lancamentos = [];
      $("transactions-body").replaceChildren();
      $("results-count").textContent = "0 lançamentos";
      mensagem.hidden = false;
      mensagem.classList.add("state-error");
      mensagem.textContent = erro.message;
      aviso(erro.message, true);
    }
  }

  function exibirCategoriasResumo(lista) {
    const area = $("expense-category-list");
    area.replaceChildren();
    if (!lista.length) {
      const vazio = document.createElement("p");
      vazio.className = "category-summary-state";
      vazio.textContent = "Nenhuma despesa no mês selecionado.";
      area.append(vazio);
      return;
    }
    const maior = Math.max(...lista.map((c) => Number(c.valor_centavos)), 1);
    lista.forEach((categoria) => {
      const bloco = document.createElement("div");
      bloco.className = "category-summary-item";
      const cabecalho = document.createElement("div");
      cabecalho.className = "category-summary-details";
      const nome = document.createElement("span");
      nome.className = "category-summary-name";
      nome.textContent = categoria.categoria_nome;
      const total = document.createElement("strong");
      total.className = "category-summary-amount";
      total.textContent = reais(categoria.valor_centavos);
      cabecalho.append(nome, total);
      const trilha = document.createElement("div");
      trilha.className = "category-summary-track";
      const barra = document.createElement("span");
      barra.className = "category-summary-bar";
      barra.style.width = `${Math.max(3, 100 * categoria.valor_centavos / maior)}%`;
      trilha.append(barra);
      bloco.append(cabecalho, trilha);
      area.append(bloco);
    });
  }

  async function carregarResumo() {
    const atual = ++estado.resumoId;
    try {
      const resumo = await api(`/resumo${query({ mes: $("summary-month").value })}`);
      if (atual !== estado.resumoId) return;
      [
        ["summary-income", resumo.receitas_centavos],
        ["summary-expense", resumo.despesas_centavos],
        ["summary-result", resumo.resultado_centavos],
        ["summary-balance", resumo.saldo_acumulado_centavos]
      ].forEach(([id, centavos]) => {
        $(id).textContent = reais(centavos);
        $(id).classList.toggle("negative-value", Number(centavos) < 0);
      });
      exibirCategoriasResumo(Array.isArray(resumo.despesas_por_categoria) ? resumo.despesas_por_categoria : []);
    } catch (erro) {
      if (atual !== estado.resumoId) return;
      $("expense-category-list").textContent = "Não foi possível carregar o resumo.";
      aviso(erro.message, true);
    }
  }

  function limparErros() {
    $("form-error").hidden = true;
    $("form-error").textContent = "";
    document.querySelectorAll(".field-error").forEach((e) => { e.textContent = ""; });
    $("entry-form").querySelectorAll('[aria-invalid="true"]').forEach((e) => e.removeAttribute("aria-invalid"));
  }
  function mostrarErros(campos) {
    Object.entries(campos).forEach(([campo, texto]) => {
      const idCampo = {
        descricao: "entry-description", valor_centavos: "entry-amount",
        data: "entry-date", categoria_id: "entry-category"
      }[campo];
      const erro = $(`error-${campo}`);
      if (erro) erro.textContent = texto;
      if (idCampo) $(idCampo).setAttribute("aria-invalid", "true");
    });
  }

  // Converte "1.234,56" e "1234.56" em 123456 centavos, sem float.
  function analisarValor(texto) {
    const normal = String(texto).trim().replace(/^R\$\s*/, "").replace(/\s/g, "");
    let base = normal;
    if (/^\d{1,3}(\.\d{3})+(,\d{1,2})?$/.test(normal)) base = normal.replace(/\./g, "");
    if (!/^\d+([.,]\d{1,2})?$/.test(base)) return null;
    const [inteiros, decimais = ""] = base.replace(",", ".").split(".");
    const centavos = Number(inteiros) * 100 + Number(decimais.padEnd(2, "0"));
    return Number.isSafeInteger(centavos) && centavos > 0 ? centavos : null;
  }

  function validar() {
    const descricao = $("entry-description").value.trim();
    const valor_centavos = analisarValor($("entry-amount").value);
    const data = $("entry-date").value;
    const tipo = tipoFormulario();
    const categoria_id = Number($("entry-category").value);
    const erros = {};
    if (!descricao || descricao.length > 120) erros.descricao = "Informe uma descrição de até 120 caracteres.";
    if (valor_centavos === null) erros.valor_centavos = "Informe um valor maior que zero (ex.: 50,00).";
    const parsed = /^\d{4}-\d\d-\d\d$/.test(data) ? new Date(`${data}T12:00:00Z`) : new Date(NaN);
    if (Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== data || data > hojeBrasil()) {
      erros.data = "Informe uma data válida, não futura.";
    }
    if (!estado.categorias.some((c) => c.id === categoria_id && c.tipo === tipo)) {
      erros.categoria_id = "Selecione uma categoria compatível com o tipo.";
    }
    return { erros, payload: { descricao, valor_centavos, data, tipo, categoria_id } };
  }

  function abrirNovo() {
    const modal = $("entry-dialog");
    $("entry-form").reset();
    $("entry-id").value = "";
    $("form-title").textContent = "Novo lançamento";
    $("save-entry").textContent = "Salvar lançamento";
    document.querySelector('input[name="tipo"][value="despesa"]').checked = true;
    $("entry-date").max = hojeBrasil();
    $("entry-date").value = hojeBrasil();
    categoriasDoFormulario();
    limparErros();
    if (!modal.open) modal.showModal();
    $("entry-description").focus();
    if (!estado.categorias.length) {
      $("form-error").textContent = "Categorias indisponíveis. Confira a conexão do Flask com o Supabase.";
      $("form-error").hidden = false;
    }
  }

  function abrirEdicao(registro) {
    $("entry-form").reset();
    $("entry-id").value = registro.id;
    $("form-title").textContent = "Editar lançamento";
    $("save-entry").textContent = "Salvar alterações";
    $("entry-description").value = registro.descricao;
    $("entry-amount").value = (registro.valor_centavos / 100).toFixed(2).replace(".", ",");
    $("entry-date").max = hojeBrasil();
    $("entry-date").value = registro.data;
    document.querySelector(`input[name="tipo"][value="${registro.tipo}"]`).checked = true;
    categoriasDoFormulario(registro.categoria_id);
    limparErros();
    if (!$("entry-dialog").open) $("entry-dialog").showModal();
    $("entry-description").focus();
  }

  async function salvar(evento) {
    evento.preventDefault();
    limparErros();
    const { erros, payload } = validar();
    if (Object.keys(erros).length) {
      mostrarErros(erros);
      $("entry-form").querySelector('[aria-invalid="true"]')?.focus();
      return;
    }
    const id = $("entry-id").value;
    const botao = $("save-entry");
    botao.disabled = true;
    botao.textContent = "Salvando...";
    try {
      await api(id ? `/lancamentos/${id}` : "/lancamentos", id ? "PUT" : "POST", payload);
      $("entry-dialog").close();
      $("list-month-filter").value = payload.data.slice(0, 7);
      $("summary-month").value = payload.data.slice(0, 7);
      $("type-filter").value = "";
      $("category-filter").value = "";
      $("search-filter").value = "";
      aviso(id ? "Lançamento atualizado com sucesso!" : "Lançamento cadastrado com sucesso!");
      await Promise.all([carregarLancamentos(), carregarResumo()]);
    } catch (erro) {
      mostrarErros(erro.campos || {});
      $("form-error").textContent = erro.message;
      $("form-error").hidden = false;
    } finally {
      botao.disabled = false;
      botao.textContent = id ? "Salvar alterações" : "Salvar lançamento";
    }
  }

  async function excluirLancamento(registro) {
    if (!window.confirm(`Excluir "${registro.descricao}"? Essa operação não pode ser desfeita.`)) return;
    try {
      await api(`/lancamentos/${registro.id}`, "DELETE");
      aviso("Lançamento excluído com sucesso!");
      await Promise.all([carregarLancamentos(), carregarResumo()]);
    } catch (erro) { aviso(erro.message, true); }
  }

  async function exportarCSV() {
    const botao = $("export-button");
    botao.disabled = true;
    try {
      const arquivo = await api(`/exportar${query(filtros())}`, "GET", undefined, true);
      const url = URL.createObjectURL(arquivo);
      const link = document.createElement("a");
      link.href = url;
      link.download = filtros().mes ? `lancamentos-${filtros().mes}.csv` : "lancamentos.csv";
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      aviso("Arquivo CSV exportado!");
    } catch (erro) { aviso(erro.message, true); }
    finally { botao.disabled = false; }
  }

  function navegar() {
    const hash = location.hash === "#lancamentos" ? "#lancamentos" : "#painel";
    document.querySelectorAll(".nav-link").forEach((link) => {
      const atual = link.getAttribute("href") === hash;
      link.classList.toggle("active", atual);
      if (atual) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    $("current-section").textContent = hash === "#lancamentos" ? "Lançamentos" : "Painel";
  }

  function registrarEventos() {
    // Eventos registrados ANTES de consultar a API. Falhas do banco não travam o modal.
    $("new-entry-button").addEventListener("click", abrirNovo);
    $("close-dialog").addEventListener("click", () => $("entry-dialog").close());
    $("cancel-dialog").addEventListener("click", () => $("entry-dialog").close());
    $("entry-form").addEventListener("submit", salvar);
    document.querySelectorAll('input[name="tipo"]').forEach((r) => r.addEventListener("change", () => categoriasDoFormulario()));
    $("list-month-filter").addEventListener("change", carregarLancamentos);
    $("type-filter").addEventListener("change", carregarLancamentos);
    $("category-filter").addEventListener("change", carregarLancamentos);
    $("summary-month").addEventListener("change", carregarResumo);
    $("search-filter").addEventListener("input", () => {
      clearTimeout(temporizadorBusca);
      temporizadorBusca = setTimeout(carregarLancamentos, 250);
    });
    $("clear-filters").addEventListener("click", () => {
      $("list-month-filter").value = "";
      $("type-filter").value = "";
      $("category-filter").value = "";
      $("search-filter").value = "";
      carregarLancamentos();
    });
    $("export-button").addEventListener("click", exportarCSV);
    $("entry-dialog").addEventListener("click", (evento) => {
      const modal = $("entry-dialog");
      const r = modal.getBoundingClientRect();
      if (evento.target === modal && (evento.clientX < r.left || evento.clientX > r.right || evento.clientY < r.top || evento.clientY > r.bottom)) modal.close();
    });
    window.addEventListener("hashchange", navegar);
    navegar();
  }

  async function iniciar() {
    try {
      status("JavaScript ativo • conectando...");
      registrarEventos();
      const hoje = hojeBrasil();
      $("summary-month").value = hoje.slice(0, 7);
      $("list-month-filter").value = hoje.slice(0, 7);
      $("entry-date").max = hoje;
      $("current-date-label").textContent = new Intl.DateTimeFormat("pt-BR", {
        timeZone: "America/Sao_Paulo", weekday: "long", day: "numeric", month: "long"
      }).format(new Date()).toUpperCase();
      await carregarCategorias();
      // Erros nestas duas consultas não interrompem os eventos da página.
      await Promise.all([carregarLancamentos(), carregarResumo()]);
    } catch (erro) {
      console.error("Erro ao iniciar o frontend:", erro);
      status("Erro de inicialização do JavaScript", true);
      aviso(erro.message, true);
    }
  }

  // Como o script fica no fim do <body>, o HTML já está disponível.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar, { once: true });
  } else {
    iniciar();
  }
})();
