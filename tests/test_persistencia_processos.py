"""Executa operações em processos separados para comprovar a persistência no disco."""

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


class TestPersistenciaEntreProcessos(unittest.TestCase):
    def test_flask_recupera_registro_apos_encerrar_processo(self):
        codigo = """
import json, sys
from app import create_app
app = create_app(caminho_banco=sys.argv[1])
client = app.test_client()
if sys.argv[2] == 'cadastrar':
    resposta = client.post('/api/lancamentos', json={
        'descricao': 'Mercado', 'valor_centavos': 45000,
        'data': '2026-11-05', 'tipo': 'despesa', 'categoria_id': 2
    })
else:
    resposta = client.get('/api/lancamentos?mes=2026-11&tipo=despesa')
print(json.dumps({'status': resposta.status_code, 'corpo': resposta.get_json()}))
"""
        raiz = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as pasta:
            caminho = str(Path(pasta) / "persistente.sqlite3")
            def executar(operacao):
                resultado = subprocess.run(
                    [sys.executable, "-c", codigo, caminho, operacao],
                    cwd=raiz, capture_output=True, text=True, timeout=20, check=True,
                )
                return json.loads(resultado.stdout)
            cadastro = executar("cadastrar")
            self.assertEqual(cadastro["status"], 201)
            consulta = executar("consultar")
            self.assertEqual(consulta["status"], 200)
            self.assertEqual(consulta["corpo"]["dados"], [cadastro["corpo"]["dados"]])
            self.assertEqual(consulta["corpo"]["meta"]["quantidade"], 1)
