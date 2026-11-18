"""Conferência do arquivo original de Daniel, incluindo seu menu de terminal."""

import re
from pathlib import Path
import subprocess
import sys

import pytest

pytestmark = pytest.mark.daniel


def executar_menu(daniel, monkeypatch, capsys, entradas):
    respostas = iter(entradas)
    monkeypatch.setattr("builtins.input", lambda mensagem="": next(respostas))
    daniel.executar_menu()
    return capsys.readouterr().out


def test_sete_grupos_de_asserts_do_proprio_daniel(daniel, capsys):
    daniel.executar_testes()
    saida = capsys.readouterr().out
    assert saida.count("[OK] Teste") == 7
    assert "Todos os testes passaram" in saida


@pytest.mark.parametrize("nome", ["Xbox", "Xbox, edição X. Série_X", "Viagem X, Y. Z"])
def test_exibir_status_preserva_nome_e_formata_numeros(daniel, nome):
    meta = daniel.MetaEconomia(nome, 3500)
    meta.adicionar_economia(500)
    status = meta.exibir_status()
    assert f"Meta: {nome} |" in status
    assert "Objetivo: R$ 3.500,00" in status
    assert "Acumulado: R$ 500,00" in status
    assert "Progresso: 14,3%" in status
    assert "Restante: R$ 3.000,00" in status


def test_menu_cria_xbox_recebe_aporte_e_consulta(daniel, monkeypatch, capsys):
    saida = executar_menu(daniel, monkeypatch, capsys,
                         ["1", "Xbox", "3.500,00", "3", "1", "500,00", "4", "1", "5"])
    assert "Meta 'Xbox' criada" in saida
    assert "Economia de R$ 500,00 registrada" in saida
    assert re.search(r"Valor acumulado:\s+R\$ 500,00", saida)
    assert re.search(r"Quanto falta:\s+R\$ 3.000,00", saida)
    assert "Encerrando" in saida


def test_menu_duas_metas_e_conclusao_sem_misturar_saldos(daniel, monkeypatch, capsys):
    saida = executar_menu(daniel, monkeypatch, capsys,
                         ["1", "Xbox", "100", "1", "Viagem", "200",
                          "3", "2", "250", "4", "1", "4", "2", "5"])
    assert re.search(r"Meta:\s+Xbox.*?Valor acumulado:\s+R\$ 0,00", saida, re.S)
    assert re.search(r"Meta:\s+Viagem.*?Valor acumulado:\s+R\$ 250,00", saida, re.S)
    assert "Percentual atingido: 125,0%" in saida
    assert "Situação da meta:    Concluída" in saida


@pytest.mark.parametrize("opcao", ["2", "3", "4"])
def test_menu_sem_metas_orienta_o_usuario(daniel, monkeypatch, capsys, opcao):
    saida = executar_menu(daniel, monkeypatch, capsys, [opcao, "5"])
    assert "Nenhuma meta cadastrada" in saida
    assert "Encerrando" in saida


@pytest.mark.parametrize("escolha", ["abc", "0", "99"])
def test_menu_id_invalido_volta_ao_menu(daniel, monkeypatch, capsys, escolha):
    saida = executar_menu(daniel, monkeypatch, capsys,
                         ["1", "Xbox", "100", "3", escolha, "5"])
    assert "[Erro]" in saida
    assert "Encerrando" in saida


def test_menu_valores_invalidos_nao_impedem_nova_tentativa(daniel, monkeypatch, capsys):
    saida = executar_menu(daniel, monkeypatch, capsys,
                         ["x", "1", "", "100", "1", "Xbox", "abc",
                          "1", "Xbox", "100", "3", "1", "-50", "4", "1", "5"])
    assert "Opção inválida" in saida
    assert "nome da meta não pode ser vazio" in saida
    assert "Digite um valor numérico válido" in saida
    assert re.search(r"Valor acumulado:\s+R\$ 0,00", saida)
    assert "Encerrando" in saida


@pytest.mark.parametrize("texto,esperado", [("2.000,50", 2000.50), ("250,50", 250.50), ("250.50", 250.50)])
def test_leitura_monetaria_aceita_formatos_usados_no_menu(daniel, monkeypatch, texto, esperado):
    monkeypatch.setattr("builtins.input", lambda mensagem="": texto)
    assert daniel.ler_valor_monetario("Valor: ") == esperado


def test_saldos_sao_centavos_e_propriedade_publica_nao_tem_setter(daniel):
    meta = daniel.MetaEconomia("Cofrinho", 1)
    meta.adicionar_economia(0.1)
    meta.adicionar_economia(0.2)
    assert meta.valor_acumulado == 0.3
    with pytest.raises(AttributeError):
        meta.valor_acumulado = 500


def test_arquivo_completo_aceita_comandos_no_terminal(tmp_path):
    arquivo = Path(__file__).resolve().parents[1] / "modulo-complementar/meta_economia.py"
    resultado = subprocess.run(
        [sys.executable, "-X", "utf8", str(arquivo)],
        input="1\nXbox\n3.500,00\n3\n1\n500,00\n4\n1\n5\n",
        capture_output=True, encoding="utf-8", timeout=10, cwd=tmp_path,
    )
    assert resultado.returncode == 0, resultado.stderr
    assert "Meta 'Xbox' criada" in resultado.stdout
    assert "Economia de R$ 500,00 registrada" in resultado.stdout
    assert "Quanto falta:        R$ 3.000,00" in resultado.stdout
    assert "Encerrando o gerenciador" in resultado.stdout
    assert "Traceback" not in resultado.stderr


@pytest.mark.parametrize("local", ["criacao", "aporte"])
def test_menu_valor_infinito_deve_ser_rejeitado_sem_encerrar(daniel, monkeypatch, capsys, local):
    if local == "criacao":
        entradas = ["1", "Xbox", "inf", "5"]
    else:
        entradas = ["1", "Xbox", "100", "3", "1", "1e309", "5"]
    saida = executar_menu(daniel, monkeypatch, capsys, entradas)
    assert "Encerrando" in saida
