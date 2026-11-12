(() => {
  "use strict";

  const data = window.FinanceData.source;
  const elements = {
    summaryMonth: document.getElementById("summary-month"),
    listMonth: document.getElementById("list-month-filter"),
    typeFilter: document.getElementById("type-filter"),
    categoryFilter: document.getElementById("category-filter"),
    searchFilter: document.getElementById("search-filter"),
    body: document.getElementById("transactions-body"),
    listState: document.getElementById("list-state"),
    resultsCount: document.getElementById("results-count"),
    dialog: document.getElementById("entry-dialog"),
    form: document.getElementById("entry-form"),
    formTitle: document.getElementById("form-title"),
    formError: document.getElementById("form-error"),
    category: document.getElementById("entry-category"),
    typeInputs: Array.from(document.querySelectorAll('input[name="tipo"]')),
    description: document.getElementById("entry-description"),
    amount: document.getElementById("entry-amount"),
    date: document.getElementById("entry-date"),
    entryId: document.getElementById("entry-id"),
    saveButton: document.getElementById("save-entry"),
    feedback: document.getElementById("global-feedback")
  };

  let categories = [];
  const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

  function todayInSaoPaulo() {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: "America/Sao_Paulo",
      year: "numeric",
      month: "2-digit",
      day: "2-digit"
    }).formatToParts(new Date());
    const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    return `${values.year}-${values.month}-${values.day}`;
  }

  function formatDate(date) {
    const [year, month, day] = date.split("-");
    return `${day}/${month}/${year}`;
  }

  function currentType() {
    return elements.typeInputs.find((input) => input.checked).value;
  }

  function selectedFilters() {
    const filters = {
      mes: elements.listMonth.value,
      tipo: elements.typeFilter.value,
      categoria_id: elements.categoryFilter.value,
      busca: elements.searchFilter.value.trim()
    };
    return Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
  }

  function categoryName(id) {
    const category = categories.find((item) => item.id === id);
    return category ? category.nome : "Categoria removida";
  }

  function updateCategoryOptions() {
    const type = currentType();
    const options = categories.filter((category) => !type || category.tipo === type);
    const selected = elements.category.value;
    elements.category.replaceChildren(new Option("Selecione uma categoria", ""));
    options.forEach((category) => elements.category.add(new Option(category.nome, String(category.id))));
    if (options.some((category) => String(category.id) === selected)) elements.category.value = selected;
  }

  function setLoading(isLoading) {
    elements.listState.hidden = !isLoading;
    if (isLoading) {
      elements.listState.textContent = "Carregando lançamentos...";
      elements.body.replaceChildren();
    }
  }

  function showFeedback(message, isError = false) {
    elements.feedback.textContent = message;
    elements.feedback.classList.toggle("feedback-error", isError);
    elements.feedback.hidden = false;
    window.clearTimeout(showFeedback.timeout);
    showFeedback.timeout = window.setTimeout(() => { elements.feedback.hidden = true; }, 5000);
  }

  function showListError(error) {
    elements.listState.textContent = error.message || "Não foi possível carregar os lançamentos.";
    elements.listState.classList.add("state-error");
    elements.listState.hidden = false;
  }

  function updateCount(count) {
    elements.resultsCount.textContent = `${count} ${count === 1 ? "lançamento" : "lançamentos"}`;
  }

  function renderExpenseCategories(expenses) {
    const container = document.getElementById("expense-category-list");
    container.replaceChildren();
    if (!expenses.length) {
      const emptyState = document.createElement("p");
      emptyState.className = "category-summary-state";
      emptyState.textContent = "Nenhuma despesa neste período.";
      container.append(emptyState);
      return;
    }

    const largestExpense = Math.max(...expenses.map((expense) => expense.valor_centavos));
    expenses.forEach((expense) => {
      const item = document.createElement("div");
      item.className = "category-summary-item";
      const details = document.createElement("div");
      details.className = "category-summary-details";
      const name = document.createElement("span");
      name.className = "category-summary-name";
      name.textContent = expense.categoria_nome;
      const amount = document.createElement("span");
      amount.className = "category-summary-amount";
      amount.textContent = money.format(expense.valor_centavos / 100);
      const track = document.createElement("div");
      track.className = "category-summary-track";
      track.setAttribute("role", "img");
      track.setAttribute("aria-label", `${expense.categoria_nome}: ${amount.textContent}`);
      const bar = document.createElement("span");
      bar.className = "category-summary-bar";
      bar.style.width = `${Math.max(4, expense.valor_centavos / largestExpense * 100)}%`;
      track.append(bar);
      details.append(name, amount);
      item.append(details, track);
      container.append(item);
    });
  }

  function renderEntries(entries) {
    elements.body.replaceChildren();
    elements.listState.classList.remove("state-error");
    if (!entries.length) {
      elements.listState.textContent = "Nenhum lançamento encontrado. Ajuste os filtros ou cadastre uma movimentação.";
      elements.listState.hidden = false;
      updateCount(0);
      return;
    }
    elements.listState.hidden = true;
    updateCount(entries.length);
    entries.forEach((entry) => {
      const row = document.createElement("tr");
      const descriptionCell = document.createElement("td");
      const description = document.createElement("span");
      description.className = "entry-description";
      description.textContent = entry.descricao;
      descriptionCell.append(description);

      const categoryCell = document.createElement("td");
      categoryCell.textContent = categoryName(entry.categoria_id);
      const dateCell = document.createElement("td");
      dateCell.textContent = formatDate(entry.data);
      const typeCell = document.createElement("td");
      const badge = document.createElement("span");
      badge.className = `type-badge ${entry.tipo}`;
      badge.textContent = entry.tipo === "receita" ? "Receita" : "Despesa";
      typeCell.append(badge);
      const amountCell = document.createElement("td");
      amountCell.className = `amount-cell ${entry.tipo}`;
      amountCell.textContent = `${entry.tipo === "receita" ? "+" : "−"} ${money.format(entry.valor_centavos / 100)}`;
      const actionsCell = document.createElement("td");
      actionsCell.className = "row-actions";
      const editButton = document.createElement("button");
      editButton.className = "icon-button row-action";
      editButton.type = "button";
      editButton.textContent = "✎";
      editButton.setAttribute("aria-label", `Editar ${entry.descricao}`);
      editButton.addEventListener("click", () => openEditForm(entry));
      const deleteButton = document.createElement("button");
      deleteButton.className = "icon-button row-action delete-action";
      deleteButton.type = "button";
      deleteButton.textContent = "×";
      deleteButton.setAttribute("aria-label", `Excluir ${entry.descricao}`);
      deleteButton.addEventListener("click", () => removeEntry(entry));
      actionsCell.append(editButton, deleteButton);
      row.append(descriptionCell, categoryCell, dateCell, typeCell, amountCell, actionsCell);
      elements.body.append(row);
    });
  }

  async function loadEntries() {
    setLoading(true);
    try {
      const entries = await data.getEntries(selectedFilters());
      renderEntries(entries);
    } catch (error) {
      showListError(error);
      updateCount(0);
      showFeedback(error.message || "Não foi possível carregar os lançamentos.", true);
    }
  }

  async function loadSummary() {
    try {
      const summary = await data.getSummary(elements.summaryMonth.value);
      document.getElementById("summary-income").textContent = money.format(summary.receitas_centavos / 100);
      document.getElementById("summary-expense").textContent = money.format(summary.despesas_centavos / 100);
      document.getElementById("summary-result").textContent = money.format(summary.resultado_centavos / 100);
      document.getElementById("summary-balance").textContent = money.format(summary.saldo_acumulado_centavos / 100);
      document.getElementById("summary-result").classList.toggle("negative-value", summary.resultado_centavos < 0);
      document.getElementById("summary-balance").classList.toggle("negative-value", summary.saldo_acumulado_centavos < 0);
      renderExpenseCategories(summary.despesas_por_categoria);
    } catch (error) {
      const container = document.getElementById("expense-category-list");
      const errorState = document.createElement("p");
      errorState.className = "category-summary-state";
      errorState.textContent = "Não foi possível carregar as despesas por categoria.";
      container.replaceChildren(errorState);
      showFeedback(error.message || "Não foi possível carregar o resumo financeiro.", true);
    }
  }

  async function refresh() {
    await Promise.all([loadEntries(), loadSummary()]);
  }

  function clearFieldErrors() {
    elements.form.querySelectorAll(".field-error").forEach((field) => { field.textContent = ""; });
    elements.form.querySelectorAll("[aria-invalid='true']").forEach((field) => field.removeAttribute("aria-invalid"));
    elements.formError.hidden = true;
    elements.formError.textContent = "";
  }

  function showFieldErrors(errors) {
    clearFieldErrors();
    const mapping = {
      descricao: "error-descricao",
      valor_centavos: "error-valor_centavos",
      data: "error-data",
      categoria_id: "error-categoria_id",
      tipo: null
    };
    Object.entries(errors).forEach(([field, message]) => {
      const errorElement = mapping[field] ? document.getElementById(mapping[field]) : elements.form.querySelector('[data-error-for="tipo"]');
      if (errorElement) errorElement.textContent = message;
      const input = {
        descricao: elements.description,
        valor_centavos: elements.amount,
        data: elements.date,
        categoria_id: elements.category
      }[field];
      if (input) input.setAttribute("aria-invalid", "true");
    });
  }

  function validateForm() {
    const errors = {};
    const description = elements.description.value.trim();
    const amountValue = elements.amount.value.trim();
    const normalizedAmount = amountValue.replace(",", ".");
    const cents = Math.round(Number(normalizedAmount) * 100);
    const date = elements.date.value;
    const categoryId = Number(elements.category.value);
    const type = currentType();

    if (!description) errors.descricao = "Informe a descrição do lançamento.";
    else if (description.length > 120) errors.descricao = "A descrição deve ter no máximo 120 caracteres.";
    if (!/^\d+(?:[.,]\d{1,2})?$/.test(amountValue) || !Number.isFinite(Number(normalizedAmount)) || Number(normalizedAmount) <= 0 || !Number.isSafeInteger(cents)) {
      errors.valor_centavos = "Informe um valor maior que zero, com até duas casas decimais.";
    }
    if (!date) errors.data = "Informe a data do lançamento.";
    else if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || new Date(`${date}T00:00:00Z`).toISOString().slice(0, 10) !== date) {
      errors.data = "Informe uma data válida.";
    } else if (date > todayInSaoPaulo()) errors.data = "A data não pode ser posterior a hoje.";
    const category = categories.find((item) => item.id === categoryId);
    if (!categoryId || !category) errors.categoria_id = "Selecione uma categoria.";
    else if (category.tipo !== type) errors.categoria_id = "A categoria selecionada não pertence ao tipo informado.";
    return {
      errors,
      payload: {
        descricao: description,
        valor_centavos: cents,
        data: date,
        tipo: type,
        categoria_id: categoryId
      }
    };
  }

  function openCreateForm() {
    elements.form.reset();
    elements.entryId.value = "";
    elements.formTitle.textContent = "Novo lançamento";
    elements.saveButton.textContent = "Salvar lançamento";
    elements.date.value = todayInSaoPaulo();
    elements.typeInputs[0].checked = true;
    updateCategoryOptions();
    clearFieldErrors();
    elements.dialog.showModal();
    elements.description.focus();
  }

  function openEditForm(entry) {
    elements.form.reset();
    elements.entryId.value = String(entry.id);
    elements.formTitle.textContent = "Editar lançamento";
    elements.saveButton.textContent = "Salvar alterações";
    elements.description.value = entry.descricao;
    elements.amount.value = (entry.valor_centavos / 100).toFixed(2).replace(".", ",");
    elements.date.value = entry.data;
    elements.typeInputs.forEach((input) => { input.checked = input.value === entry.tipo; });
    updateCategoryOptions();
    elements.category.value = String(entry.categoria_id);
    clearFieldErrors();
    elements.dialog.showModal();
    elements.description.focus();
  }

  async function submitForm(event) {
    event.preventDefault();
    clearFieldErrors();
    const { errors, payload } = validateForm();
    if (Object.keys(errors).length) {
      showFieldErrors(errors);
      const firstInvalid = elements.form.querySelector("[aria-invalid='true']");
      if (firstInvalid) firstInvalid.focus();
      return;
    }

    elements.saveButton.disabled = true;
    elements.saveButton.textContent = "Salvando...";
    try {
      await data.saveEntry(payload, elements.entryId.value || null);
      elements.dialog.close();
      showFeedback(elements.entryId.value ? "Lançamento atualizado com sucesso." : "Lançamento cadastrado com sucesso.");
      await refresh();
    } catch (error) {
      if (error.fields && Object.keys(error.fields).length) showFieldErrors(error.fields);
      elements.formError.textContent = error.message || "Não foi possível salvar. Tente novamente.";
      elements.formError.hidden = false;
    } finally {
      elements.saveButton.disabled = false;
      elements.saveButton.textContent = elements.entryId.value ? "Salvar alterações" : "Salvar lançamento";
    }
  }

  async function removeEntry(entry) {
    if (!window.confirm(`Excluir o lançamento "${entry.descricao}"? Esta ação não pode ser desfeita.`)) return;
    try {
      await data.deleteEntry(entry.id);
      showFeedback("Lançamento excluído com sucesso.");
      await refresh();
    } catch (error) {
      showFeedback(error.message || "Não foi possível excluir o lançamento.", true);
    }
  }

  async function exportEntries() {
    const button = document.getElementById("export-button");
    button.disabled = true;
    try {
      await data.exportEntries(selectedFilters());
      showFeedback("Sua exportação CSV está pronta.");
    } catch (error) {
      showFeedback(error.message || "Não foi possível exportar os lançamentos.", true);
    } finally {
      button.disabled = false;
    }
  }

  async function initialize() {
    try {
      document.getElementById("current-date-label").textContent = new Intl.DateTimeFormat("pt-BR", {
        weekday: "long",
        day: "numeric",
        month: "long",
        timeZone: "America/Sao_Paulo"
      }).format(new Date()).toLocaleUpperCase("pt-BR");
      categories = await data.getCategories();
      categories.forEach((category) => elements.categoryFilter.add(new Option(category.nome, String(category.id))));
      updateCategoryOptions();
      elements.date.max = todayInSaoPaulo();
      await refresh();
    } catch (error) {
      showFeedback(error.message || "Não foi possível iniciar o gerenciador financeiro.", true);
      showListError(error);
    }
  }

  document.getElementById("new-entry-button").addEventListener("click", openCreateForm);
  document.getElementById("close-dialog").addEventListener("click", () => elements.dialog.close());
  document.getElementById("cancel-dialog").addEventListener("click", () => elements.dialog.close());
  elements.form.addEventListener("submit", submitForm);
  elements.typeInputs.forEach((input) => input.addEventListener("change", updateCategoryOptions));
  elements.summaryMonth.addEventListener("change", loadSummary);
  [elements.listMonth, elements.typeFilter, elements.categoryFilter].forEach((input) => input.addEventListener("change", loadEntries));
  elements.searchFilter.addEventListener("input", () => {
    window.clearTimeout(elements.searchFilter.debounce);
    elements.searchFilter.debounce = window.setTimeout(loadEntries, 180);
  });
  document.getElementById("clear-filters").addEventListener("click", () => {
    elements.listMonth.value = "";
    elements.typeFilter.value = "";
    elements.categoryFilter.value = "";
    elements.searchFilter.value = "";
    loadEntries();
  });
  document.getElementById("export-button").addEventListener("click", exportEntries);
  elements.dialog.addEventListener("click", (event) => {
    if (event.target === elements.dialog) elements.dialog.close();
  });
  initialize();
})();
