(() => {
  "use strict";

  const STORAGE_KEY = "meu-financeiro-lancamentos-v1";
  const USE_MOCK_DATA = true;
  const CATEGORIES = [
    { id: 1, nome: "Salário", tipo: "receita" },
    { id: 2, nome: "Alimentação", tipo: "despesa" },
    { id: 3, nome: "Moradia", tipo: "despesa" },
    { id: 4, nome: "Transporte", tipo: "despesa" },
    { id: 5, nome: "Outras receitas", tipo: "receita" },
    { id: 6, nome: "Outras despesas", tipo: "despesa" }
  ];
  const DEMO_ENTRIES = [
    { id: 4, descricao: "Ônibus", valor_centavos: 15000, data: "2026-11-07", tipo: "despesa", categoria_id: 4 },
    { id: 3, descricao: "Mercado", valor_centavos: 45000, data: "2026-11-05", tipo: "despesa", categoria_id: 2 },
    { id: 2, descricao: "Aluguel", valor_centavos: 90000, data: "2026-11-03", tipo: "despesa", categoria_id: 3 },
    { id: 1, descricao: "Salário", valor_centavos: 300000, data: "2026-11-02", tipo: "receita", categoria_id: 1 }
  ];

  function readEntries() {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === null) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(DEMO_ENTRIES));
      return DEMO_ENTRIES.map((entry) => ({ ...entry }));
    }

    const entries = JSON.parse(stored);
    if (!Array.isArray(entries)) {
      throw new Error("Os dados salvos localmente estão inválidos. Limpe os dados do navegador para reiniciar a demonstração.");
    }
    return entries;
  }

  function writeEntries(entries) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  }

  function monthOf(date) {
    return date.slice(0, 7);
  }

  function getCategories() {
    return Promise.resolve(CATEGORIES.map((category) => ({ ...category })));
  }

  function getEntries(filters = {}) {
    let entries = readEntries();
    if (filters.mes) entries = entries.filter((entry) => monthOf(entry.data) === filters.mes);
    if (filters.tipo) entries = entries.filter((entry) => entry.tipo === filters.tipo);
    if (filters.categoria_id) entries = entries.filter((entry) => entry.categoria_id === Number(filters.categoria_id));
    if (filters.busca) {
      const search = filters.busca.trim().toLocaleLowerCase("pt-BR");
      entries = entries.filter((entry) => entry.descricao.toLocaleLowerCase("pt-BR").includes(search));
    }
    return Promise.resolve(entries.sort((a, b) => b.data.localeCompare(a.data) || b.id - a.id));
  }

  function getSummary(month) {
    const entries = readEntries();
    const periodEntries = entries.filter((entry) => monthOf(entry.data) === month);
    const priorEntries = entries.filter((entry) => entry.data <= `${month}-31`);
    const total = (list, type) => list
      .filter((entry) => entry.tipo === type)
      .reduce((sum, entry) => sum + entry.valor_centavos, 0);
    const grouped = new Map();
    periodEntries.filter((entry) => entry.tipo === "despesa").forEach((entry) => {
      grouped.set(entry.categoria_id, (grouped.get(entry.categoria_id) || 0) + entry.valor_centavos);
    });
    const despesasPorCategoria = Array.from(grouped, ([categoria_id, valor_centavos]) => ({
      categoria_id,
      categoria_nome: CATEGORIES.find((category) => category.id === categoria_id).nome,
      valor_centavos
    })).sort((a, b) => b.valor_centavos - a.valor_centavos || a.categoria_id - b.categoria_id);
    const receitas = total(periodEntries, "receita");
    const despesas = total(periodEntries, "despesa");
    return Promise.resolve({
      mes: month,
      receitas_centavos: receitas,
      despesas_centavos: despesas,
      resultado_centavos: receitas - despesas,
      saldo_acumulado_centavos: total(priorEntries, "receita") - total(priorEntries, "despesa"),
      despesas_por_categoria: despesasPorCategoria
    });
  }

  function saveEntry(payload, id) {
    const entries = readEntries();
    if (id) {
      const index = entries.findIndex((entry) => entry.id === Number(id));
      if (index < 0) throw new Error("Este lançamento não foi encontrado. Atualize a página e tente novamente.");
      entries[index] = { id: Number(id), ...payload };
      writeEntries(entries);
      return Promise.resolve({ ...entries[index] });
    }
    const nextId = entries.reduce((largest, entry) => Math.max(largest, entry.id), 0) + 1;
    const entry = { id: nextId, ...payload };
    entries.push(entry);
    writeEntries(entries);
    return Promise.resolve({ ...entry });
  }

  function deleteEntry(id) {
    const entries = readEntries();
    if (!entries.some((entry) => entry.id === Number(id))) {
      throw new Error("Este lançamento não foi encontrado. Atualize a página e tente novamente.");
    }
    writeEntries(entries.filter((entry) => entry.id !== Number(id)));
    return Promise.resolve();
  }

  function escapeCsv(value) {
    const text = String(value);
    return /[;"\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  }

  async function exportEntries(filters = {}) {
    const entries = await getEntries(filters);
    const rows = [
      ["id", "data", "descricao", "tipo", "categoria", "valor"],
      ...entries.map((entry) => [
        entry.id,
        entry.data,
        entry.descricao,
        entry.tipo,
        CATEGORIES.find((category) => category.id === entry.categoria_id).nome,
        (entry.valor_centavos / 100).toFixed(2).replace(".", ",")
      ])
    ];
    const csv = `\uFEFF${rows.map((row) => row.map(escapeCsv).join(";")).join("\r\n")}`;
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filters.mes ? `lancamentos-${filters.mes}.csv` : "lancamentos.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  const mockDataSource = { getCategories, getEntries, getSummary, saveEntry, deleteEntry, exportEntries };

  function createApiDataSource(baseUrl = "/api") {
    async function request(path, options = {}) {
      let response;
      try {
        response = await fetch(`${baseUrl}${path}`, {
          ...options,
          headers: options.body ? { "Content-Type": "application/json", ...options.headers } : options.headers
        });
      } catch (error) {
        throw new Error("Não foi possível conectar ao servidor. Tente novamente.");
      }

      const contentType = response.headers.get("content-type") || "";
      if (!response.ok) {
        const body = contentType.includes("application/json") ? await response.json() : null;
        const message = body && body.erro && body.erro.mensagem
          ? body.erro.mensagem
          : "Não foi possível concluir a operação. Tente novamente.";
        const error = new Error(message);
        error.fields = body && body.erro ? body.erro.campos : {};
        throw error;
      }
      if (contentType.includes("application/json")) return response.json();
      return response;
    }

    function queryString(filters) {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== "" && value !== undefined && value !== null) params.set(key, value);
      });
      const query = params.toString();
      return query ? `?${query}` : "";
    }

    return {
      async getCategories() {
        return (await request("/categorias")).dados;
      },
      async getEntries(filters = {}) {
        return (await request(`/lancamentos${queryString(filters)}`)).dados;
      },
      async getSummary(month) {
        return (await request(`/resumo${queryString({ mes: month })}`)).dados;
      },
      async saveEntry(payload, id) {
        const method = id ? "PUT" : "POST";
        const path = id ? `/lancamentos/${id}` : "/lancamentos";
        return (await request(path, { method, body: JSON.stringify(payload) })).dados;
      },
      async deleteEntry(id) {
        return request(`/lancamentos/${id}`, { method: "DELETE" });
      },
      async exportEntries(filters = {}) {
        const response = await request(`/exportar${queryString(filters)}`);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filters.mes ? `lancamentos-${filters.mes}.csv` : "lancamentos.csv";
        link.click();
        URL.revokeObjectURL(url);
      }
    };
  }

  window.FinanceData = {
    source: USE_MOCK_DATA ? mockDataSource : createApiDataSource(),
    mock: mockDataSource,
    api: createApiDataSource
  };
})();
