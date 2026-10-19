"""python -m unittest discover central/testes"""
import http.client
import json
import socket
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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

    def test_erro_numa_rota_vira_500_e_nao_derruba_a_conexao(self):
        with mock.patch.object(servidor, "equipe", side_effect=IndexError("agente sem cabeçalho")):
            cod, dado = self.pedir("GET", "/api/equipe")
        self.assertEqual(cod, 500)
        self.assertIn("IndexError", json.loads(dado)["erro"])


class PixelFalso(BaseHTTPRequestHandler):
    """Faz o papel do pixel-agents: uma página HTML e um WebSocket que devolve o Host/Origin recebidos e ecoa."""
    def log_message(self, *_):
        pass

    def do_GET(self):
        if self.headers.get("Upgrade") == "websocket":
            self.wfile.write(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n\r\n")
            self.wfile.write(f"{self.path}|{self.headers['Host']}|{self.headers['Origin']}\n".encode())
            self.wfile.flush()
            dado = self.connection.recv(100)
            self.connection.sendall(b"eco:" + dado)
            return
        corpo = b"<!doctype html><html><head><title>Pixel Agents</title></head><body></body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(corpo)


class TesteRepasseEscritorio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pixel = ThreadingHTTPServer(("127.0.0.1", 0), PixelFalso)
        threading.Thread(target=cls.pixel.serve_forever, daemon=True).start()
        cls.trava = mock.patch.object(servidor, "PIXEL", cls.pixel.server_address[1])
        cls.trava.start()
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), servidor.Painel)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.trava.stop()
        for s_ in (cls.srv, cls.pixel):
            s_.shutdown()
            s_.server_close()

    def test_pagina_do_escritorio_ganha_a_ponte(self):
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        c.request("GET", "/escritorio/?token=abc")
        r = c.getresponse()
        html = r.read()
        self.assertEqual(r.status, 200)
        self.assertIn(b'<script src="/web/pixel-ptbr.js"></script><script src="/web/ponte-escritorio.js"></script>', html)
        self.assertIn("<title>Escritório</title>".encode(), html)

    def test_websocket_passa_nos_dois_sentidos(self):
        porta_os = self.srv.server_address[1]
        s_ = socket.create_connection(("127.0.0.1", porta_os), timeout=10)
        s_.sendall(f"GET /ws?token=abc HTTP/1.1\r\nHost: 127.0.0.1:{porta_os}\r\nOrigin: http://127.0.0.1:{porta_os}\r\n"
                   "Upgrade: websocket\r\nConnection: Upgrade\r\n\r\n".encode())
        recebido = b""
        while b"\n" not in recebido.split(b"\r\n\r\n", 1)[-1] or b"\r\n\r\n" not in recebido:
            pedaco = s_.recv(1000)
            self.assertTrue(pedaco, recebido)  # conexão fechada antes da resposta completa
            recebido += pedaco
        self.assertTrue(recebido.startswith(b"HTTP/1.1 101"))
        caminho, host, origem = recebido.split(b"\r\n\r\n", 1)[1].decode().strip().split("|")
        porta = self.pixel.server_address[1]
        self.assertEqual((caminho, host, origem), ("/ws?token=abc", f"127.0.0.1:{porta}", f"http://127.0.0.1:{porta}"))
        s_.sendall(b"ola")
        self.assertEqual(s_.recv(100), b"eco:ola")
        s_.close()


    def test_outro_site_nao_abre_o_websocket_do_escritorio(self):
        for origem in (b"https://site-malicioso.com", b"http://127.0.0.1:3100"):
            s_ = socket.create_connection(("127.0.0.1", self.srv.server_address[1]), timeout=10)
            s_.sendall(b"GET /ws?token=abc HTTP/1.1\r\nHost: 127.0.0.1:3200\r\nOrigin: " + origem +
                       b"\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n\r\n")
            resposta = b""
            while chunk := s_.recv(1000):
                resposta += chunk
            s_.close()
            self.assertTrue(resposta.startswith(b"HTTP/1.0 403"), resposta[:40])


if __name__ == "__main__":
    unittest.main()
