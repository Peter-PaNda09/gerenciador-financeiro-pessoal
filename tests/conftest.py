"""Importa a aplicação real, trocando só o módulo de persistência por um fake."""

import importlib
import importlib.util
from pathlib import Path
import socket
import sys
import types
from unittest.mock import patch

import pytest
from tests.repositorio_fake import RepositorioFake


@pytest.fixture(autouse=True)
def bloquear_rede(monkeypatch):
    def proibido(*args, **kwargs):
        raise AssertionError("Os testes isolados não podem acessar a rede nem o Supabase real.")
    monkeypatch.setattr(socket.socket, "connect", proibido)
    monkeypatch.setattr(socket, "create_connection", proibido)


@pytest.fixture(scope="session")
def modulo_app():
    persistencia = types.ModuleType("persistencia_supabase")
    persistencia.RepositorioTransacoes = RepositorioFake
    # Evita até a importação do adaptador real: não lê .env nem cria o cliente remoto.
    def rede_proibida(*args, **kwargs):
        raise AssertionError("A importação da aplicação nos testes não pode acessar a rede.")
    with patch.dict(sys.modules, {"persistencia_supabase": persistencia}), \
            patch.object(socket.socket, "connect", rede_proibida), \
            patch.object(socket, "create_connection", rede_proibida):
        modulo = importlib.import_module("app")
        yield modulo


@pytest.fixture
def ambiente_api(modulo_app, monkeypatch):
    repo = RepositorioFake()
    servico = modulo_app.GerenciadorFinanceiro(repo)
    monkeypatch.setattr(modulo_app, "repositorio", repo)
    monkeypatch.setattr(modulo_app, "gerenciador", servico)
    monkeypatch.setitem(modulo_app.app.config, "TESTING", True)
    return types.SimpleNamespace(client=modulo_app.app.test_client(), repo=repo,
                                 app=modulo_app.app, modulo=modulo_app)


@pytest.fixture
def api(ambiente_api):
    return ambiente_api.client


@pytest.fixture
def payload():
    return {"descricao": "Mercado", "valor_centavos": 45000,
            "data": "2020-02-05", "tipo": "despesa", "categoria_id": 22}


@pytest.fixture
def cadastrar(api, payload):
    def criar(**alteracoes):
        resposta = api.post("/api/lancamentos", json={**payload, **alteracoes})
        assert resposta.status_code == 201, resposta.get_data(as_text=True)
        return resposta.get_json()["dados"]
    return criar


@pytest.fixture(scope="session")
def daniel():
    caminho = Path(__file__).resolve().parents[1] / "modulo-complementar/meta_economia.py"
    spec = importlib.util.spec_from_file_location("meta_economia_daniel_em_teste", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo
