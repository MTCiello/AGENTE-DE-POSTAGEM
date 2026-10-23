"""python -m unittest discover central/testes"""
import http.client
import json
import os
import socket
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

os.environ["CIELLO_COMERCIAL"] = str(Path(__file__).resolve().parents[2] / "exemplo" / "comercial")  # a empresa fictícia
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


def ws_conectar(porta, caminho="/ws", origem=None):
    """Cliente WebSocket mínimo para os testes: devolve (socket, leitor) depois do 101."""
    s_ = socket.create_connection(("127.0.0.1", porta), timeout=10)
    origem = origem or f"http://127.0.0.1:{porta}"
    s_.sendall(f"GET {caminho} HTTP/1.1\r\nHost: 127.0.0.1:{porta}\r\nOrigin: {origem}\r\nUpgrade: websocket\r\n"
               "Connection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n".encode())
    leitor = s_.makefile("rb")
    status = leitor.readline()
    while leitor.readline() not in (b"\r\n", b""):
        pass
    return s_, leitor, status


def ws_mandar(s_, msg):
    corpo = json.dumps(msg).encode()
    cab = bytes([0x81]) + (bytes([0x80 | len(corpo)]) if len(corpo) < 126 else bytes([0x80 | 126]) + len(corpo).to_bytes(2, "big"))
    s_.sendall(cab + b"\0\0\0\0" + corpo)  # máscara zero: o corpo vai como está


def ws_ler(leitor):
    b1, b2 = leitor.read(2)
    tam = b2 & 0x7F
    if tam == 126:
        tam = int.from_bytes(leitor.read(2), "big")
    elif tam == 127:
        tam = int.from_bytes(leitor.read(8), "big")
    return json.loads(leitor.read(tam))


class TesteEscritorio(unittest.TestCase):
    """O escritório de verdade (nucleo.sala) dentro do Ciello OS, com a casa e as sessões numa pasta temporária."""

    @classmethod
    def setUpClass(cls):
        from nucleo import ganchos, persistencia
        from nucleo.sala import Sala
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.travas = [mock.patch.object(persistencia, "CASA", d / "casa"),
                      mock.patch.object(persistencia, "LAYOUT_ANTIGO", d / "nao-existe.json"),
                      mock.patch.object(ganchos, "CONFIG_CLAUDE", d / "claude" / "settings.json")]
        for t in cls.travas:
            t.start()
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), servidor.Painel)
        cls.porta = cls.srv.server_address[1]
        cls.sessoes = d / "projects"
        cls.sala = Sala(servidor.TELA, servidor.RAIZ, cls.porta, raiz_sessoes=cls.sessoes)
        cls.travas.append(mock.patch.object(servidor, "sala", cls.sala))
        cls.travas[-1].start()
        cls.pasta = cls.sala.iniciar()
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        cls.sala.laco.parar = True
        for t in cls.travas:
            t.stop()
        cls.tmp.cleanup()

    def pedir(self, metodo, caminho, corpo=None, cabecalhos=None):
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=10)
        c.request(metodo, caminho, body=corpo, headers=cabecalhos or {})
        r = c.getresponse()
        return r.status, r.read()

    def test_pagina_do_escritorio_e_os_arquivos_saem_do_build(self):
        cod, html = self.pedir("GET", "/escritorio/?token=abc")
        self.assertEqual(cod, 200)
        self.assertIn(b'<html lang="pt-BR">', html)
        self.assertIn("<title>Escritório</title>".encode(), html)
        self.assertEqual(self.pedir("GET", "/escritorio/assets/furniture-catalog.json")[0], 200)
        self.assertEqual(self.pedir("GET", "/escritorio/../servidor.py")[0], 404)
        app = json.loads(self.pedir("GET", "/api/app/escritorio")[1])
        self.assertEqual(app, {"no_ar": True, "url": f"/escritorio/?token={servidor.TOKEN}"})

    def test_tela_com_token_recebe_tudo_e_ve_a_sessao_nova(self):
        s_, leitor, status = ws_conectar(self.porta, f"/ws?token={servidor.TOKEN}")
        self.assertTrue(status.startswith(b"HTTP/1.0 101") or status.startswith(b"HTTP/1.1 101"), status)
        ws_mandar(s_, {"type": "webviewReady"})
        tipos = []
        while "layoutLoaded" not in tipos:
            m = ws_ler(leitor)
            tipos.append(m["type"])
            if m["type"] == "officeAccess":
                self.assertFalse(m["readOnly"])
            if m["type"] == "layoutLoaded":
                self.assertEqual(m["layout"]["cols"], 27)  # o layout padrão entra na primeira vez
        self.assertEqual(tipos[:3], ["officeAccess", "providerCapabilities", "characterSpritesLoaded"])
        self.assertIn("furnitureAssetsLoaded", tipos)
        self.pasta.mkdir(parents=True, exist_ok=True)
        arq = self.pasta / "cccccccc-1111-2222-3333-444444444444.jsonl"
        arq.write_text(json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": "Grep", "input": {}}]}}) + "\n", encoding="utf-8")
        vistos = {}
        while not {"agentCreated", "agentToolStart"} <= set(vistos):
            m = ws_ler(leitor)
            vistos[m["type"]] = m
        self.assertEqual(vistos["agentToolStart"]["status"], "Searching code")
        s_.close()

    def test_tela_sem_token_so_olha(self):
        s_, leitor, _ = ws_conectar(self.porta, "/ws")
        ws_mandar(s_, {"type": "webviewReady"})
        self.assertEqual(ws_ler(leitor), {"type": "officeAccess", "readOnly": True})
        s_.close()

    def test_outro_site_nao_abre_o_websocket_do_escritorio(self):
        for origem in ("https://site-malicioso.com", "http://127.0.0.1:3100"):
            s_, leitor, status = ws_conectar(self.porta, f"/ws?token={servidor.TOKEN}", origem)
            self.assertTrue(status.startswith(b"HTTP/1.0 403"), status)
            s_.close()

    def test_hook_so_entra_com_o_token_do_servidor_json(self):
        evento = json.dumps({"session_id": "x", "hook_event_name": "Stop"})
        self.assertEqual(self.pedir("POST", "/api/ganchos/claude", evento)[0], 401)
        from nucleo import persistencia
        anotado = json.loads((persistencia.CASA / "servidor.json").read_text())
        self.assertEqual(anotado["porta"], self.porta)
        cod, corpo = self.pedir("POST", "/api/ganchos/claude", evento, {"Authorization": f"Bearer {anotado['token']}"})
        self.assertEqual((cod, corpo), (200, b"ok"))
        self.assertEqual(self.pedir("POST", "/api/ganchos/claude", "{", {"Authorization": f"Bearer {anotado['token']}"})[0], 400)


if __name__ == "__main__":
    unittest.main()
