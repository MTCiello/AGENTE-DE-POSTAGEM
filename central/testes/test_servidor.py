"""python -m unittest discover central/testes"""
import http.client
import json
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "escritorio"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import servidor  # noqa: E402


class TesteCielloOS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), servidor.Painel)
        cls.porta = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def pedir(self, metodo, caminho, corpo=None, cabecalhos=None):
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=10)
        c.request(metodo, caminho, body=json.dumps(corpo) if corpo is not None else None, headers=cabecalhos or {})
        r = c.getresponse()
        dado = r.read()
        c.close()
        return r.status, dado

    def test_pagina_com_token_e_arquivos(self):
        cod, html = self.pedir("GET", "/")
        self.assertEqual(cod, 200)
        self.assertIn(servidor.TOKEN.encode(), html)
        self.assertIn(b"Ciello OS", html)
        self.assertEqual(self.pedir("GET", "/web/app.js")[0], 200)
        self.assertEqual(self.pedir("GET", "/web/../servidor.py")[0], 404)  # nada fora da pasta web
        self.assertEqual(self.pedir("GET", "/midia/../AGENTE.md")[0], 404)

    def test_apis_dos_apps(self):
        for app in servidor.APPS:
            with mock.patch.object(servidor, "pixel_no_ar", return_value=False):
                cod, dado = self.pedir("GET", f"/api/app/{app}")
            self.assertEqual(cod, 200, app)
            self.assertNotIn("erro", json.loads(dado), app)
        equipe = json.loads(self.pedir("GET", "/api/equipe")[1])
        self.assertGreaterEqual(len(equipe), 13)
        self.assertTrue(all(a["nome"] and a["descricao"] for a in equipe))

    def test_so_roda_acao_da_lista_e_com_token(self):
        self.assertEqual(self.pedir("POST", "/api/rodar", {"acao": "briefing"})[0], 403)  # sem token
        tk = {"X-Ciello-Token": servidor.TOKEN, "Content-Type": "application/json"}
        self.assertEqual(self.pedir("POST", "/api/rodar", {"acao": "rm -rf /"}, tk)[0], 400)
        outro_host = {**tk, "Host": "site-malicioso.com"}
        self.assertEqual(self.pedir("POST", "/api/rodar", {"acao": "briefing"}, outro_host)[0], 403)
        self.assertEqual(self.pedir("GET", "/api/kpis", None, {"Host": "site-malicioso.com"})[0], 403)

    def test_executa_e_acompanha(self):
        with mock.patch.dict(servidor.ACOES, {"teste": ("Teste", "sistema", ["-c", "print('ola do teste')"])}), \
                mock.patch.object(servidor.status, "registrar"):
            ex = json.loads(self.pedir("POST", "/api/rodar", {"acao": "teste"}, {"X-Ciello-Token": servidor.TOKEN})[1])
            for _ in range(50):
                st = json.loads(self.pedir("GET", f"/api/execucao/{ex['id']}")[1])
                if st["terminou"]:
                    break
                threading.Event().wait(0.1)
        self.assertEqual(st["codigo"], 0)
        self.assertIn("ola do teste", st["saida"])


if __name__ == "__main__":
    unittest.main()
