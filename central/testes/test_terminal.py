"""python -m unittest discover central/testes  (terminal do Claude dentro do Ciello OS)"""
import http.client
import json
import os
import sys
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

os.environ["CIELLO_COMERCIAL"] = str(Path(__file__).resolve().parents[2] / "exemplo" / "comercial")  # a empresa fictícia
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "escritorio"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import servidor  # noqa: E402
import terminal  # noqa: E402
from testes.test_servidor import ws_conectar, ws_ler, ws_mandar  # noqa: E402

FALSO = [sys.executable, "-c", "import sys; print('ola do claude'); sys.stdout.flush(); print('eco', input()); sys.stdout.flush()"]


@unittest.skipIf(sys.platform.startswith("win"), "no Windows o terminal usa o pywinpty (testado no PC)")
class TesteTerminal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trava = mock.patch.object(terminal, "COMANDO_CLAUDE", FALSO)
        cls.trava.start()
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), servidor.Painel)
        cls.porta = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        servidor.terminais.fechar_todos()
        cls.trava.stop()

    def abrir(self, corpo):
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=10)
        c.request("POST", "/api/terminal", body=json.dumps(corpo), headers={"X-Ciello-Token": servidor.TOKEN, "Content-Type": "application/json"})
        r = c.getresponse()
        return r.status, json.loads(r.read())

    def ler_ate(self, leitor, texto, limite=10):
        visto, fim = "", time.time() + limite
        while texto not in visto and time.time() < fim:
            m = ws_ler(leitor)
            if m["tipo"] == "saida":
                visto += m["dados"]
            elif m["tipo"] == "fim":
                return visto, m
        return visto, None

    def test_conversa_com_o_processo_e_avisa_o_fim(self):
        cod, r = self.abrir({"prompt": "Use o subagente sdr para: teste", "titulo": "SDR"})
        self.assertEqual(cod, 200)
        self.assertEqual(servidor.terminais.get(r["id"]).titulo, "SDR")
        s_, leitor, status = ws_conectar(self.porta, f"/terminal?token={servidor.TOKEN}&id={r['id']}")
        self.assertIn(b"101", status)
        visto, _ = self.ler_ate(leitor, "ola do claude")
        self.assertIn("ola do claude", visto)
        ws_mandar(s_, {"tipo": "tamanho", "linhas": 40, "colunas": 120})
        ws_mandar(s_, {"tipo": "entrada", "dados": "mundo\r"})
        visto, fim = self.ler_ate(leitor, "eco mundo")
        self.assertIn("eco mundo", visto)
        while fim is None:
            m = ws_ler(leitor)
            fim = m if m["tipo"] == "fim" else None
        self.assertEqual(fim["codigo"], 0)
        s_.close()
        # a janela reaberta recebe o que já passou
        s2, leitor2, _ = ws_conectar(self.porta, f"/terminal?token={servidor.TOKEN}&id={r['id']}")
        self.assertIn("ola do claude", ws_ler(leitor2)["dados"])
        s2.close()

    def test_sem_token_ou_de_outro_site_nao_entra(self):
        _, r = self.abrir({})
        s_, _, status = ws_conectar(self.porta, f"/terminal?token=errado&id={r['id']}")
        self.assertIn(b"403", status)
        s_.close()
        s_, _, status = ws_conectar(self.porta, f"/terminal?token={servidor.TOKEN}&id={r['id']}", "https://site-malicioso.com")
        self.assertIn(b"403", status)
        s_.close()
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=10)
        c.request("POST", "/api/terminal", body="{}")
        self.assertEqual(c.getresponse().status, 403)

    def test_comando_do_claude(self):
        with mock.patch.object(terminal, "COMANDO_CLAUDE", None), mock.patch.object(terminal.shutil, "which", return_value=r"C:\x\claude.cmd"):
            self.assertEqual(terminal.comando_claude("oi", True), ["cmd.exe", "/c", r"C:\x\claude.cmd", "--dangerously-skip-permissions", "oi"])
        with mock.patch.object(terminal, "COMANDO_CLAUDE", None), mock.patch.object(terminal.shutil, "which", return_value=None):
            self.assertIn("Claude Code não encontrado", " ".join(terminal.comando_claude()))


if __name__ == "__main__":
    unittest.main()
