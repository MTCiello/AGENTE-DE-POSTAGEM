"""python -m unittest discover central/testes  (Estúdio de Voz: gravação, testes de voz e o VoiceStudio pela API local)"""
import base64
import http.client
import io
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "escritorio"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import estudio_voz  # noqa: E402
import servidor  # noqa: E402
import voz  # noqa: E402


def wav_bytes(seg=1.0, sr=24000):
    b = io.BytesIO()
    t = np.arange(int(seg * sr)) / sr
    sf.write(b, (0.3 * np.sin(2 * np.pi * 200 * t)).astype(np.float32), sr, format="WAV")
    return b.getvalue()


class FalsoVoiceStudio(BaseHTTPRequestHandler):
    """Imita o servidor MCP do VoiceStudio: respostas em text/event-stream e sessão no cabeçalho, como na doc dele."""
    chamadas = []

    def log_message(self, *_):
        pass

    def do_GET(self):
        self.send_response(200 if self.path.startswith("/.well-known/voicestudio-speech") else 404)
        self.end_headers()
        self.wfile.write(b"{}")

    def do_POST(self):
        msg = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FalsoVoiceStudio.chamadas.append((msg.get("method"), self.headers.get("Mcp-Session-Id"), msg.get("params")))
        if "id" not in msg:
            self.send_response(202)
            self.end_headers()
            return
        m, params = msg["method"], msg.get("params", {})
        if m == "initialize":
            res = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "omnivoice"}}
        elif m == "tools/list":
            res = {"tools": [{"name": "clone_voice", "inputSchema": {"properties": {"ref_audio_base64": {}, "name": {}, "language": {}}}}]}
        elif params.get("name") == "list_voices":
            res = {"content": [{"type": "text", "text": json.dumps([{"profile_id": "p1", "name": "Mateus"}])}]}
        elif params.get("name") == "clone_voice":
            ok = "ref_audio_base64" in params["arguments"] and params["arguments"].get("language") == "Portuguese"
            res = {"content": [{"type": "text", "text": json.dumps({"profile_id": "novo-42"} if ok else {"error": "faltou"})}]}
        else:  # generate_speech
            res = {"content": [{"type": "text", "text": json.dumps({"wav_base64": base64.b64encode(wav_bytes(0.5)).decode()})}]}
        corpo = f"event: message\ndata: {json.dumps({'jsonrpc': '2.0', 'id': msg['id'], 'result': res})}\n\n".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Mcp-Session-Id", "sessao-1")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.patches = [mock.patch.object(voz, "PREFERENCIA", self.tmp / "voz.json"), mock.patch.object(voz, "AMOSTRA", self.tmp / "marca" / "voz-mateus.wav"),
                        mock.patch.object(estudio_voz, "PASTA", self.tmp / "voz")]
        for p in self.patches:
            p.start()
        self.addCleanup(lambda: [p.stop() for p in self.patches])


class TesteVoiceStudio(Base):
    def setUp(self):
        super().setUp()
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), FalsoVoiceStudio)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        FalsoVoiceStudio.chamadas = []

    def test_fala_lista_e_clona_pela_api_local(self):
        self.assertTrue(voz.voicestudio_no_ar(self.url))
        self.assertFalse(voz.voicestudio_no_ar("http://127.0.0.1:9"))
        vs = voz.VoiceStudio(self.url)
        audio, sr = vs.falar("oi", "p1")
        self.assertEqual((sr, len(audio)), (24000, 12000))
        self.assertEqual(vs.vozes(), [{"id": "p1", "nome": "Mateus"}])
        voz.AMOSTRA.parent.mkdir(parents=True)
        voz.AMOSTRA.write_bytes(wav_bytes())
        self.assertEqual(vs.clonar(voz.AMOSTRA, "Mateus"), "novo-42")
        metodos = [m for m, _, _ in FalsoVoiceStudio.chamadas]
        self.assertEqual(metodos[:3], ["initialize", "notifications/initialized", "tools/call"])
        self.assertEqual(metodos.count("initialize"), 1)  # a sessão é reaproveitada
        self.assertTrue(all(s == "sessao-1" for _, s, _ in FalsoVoiceStudio.chamadas[1:]))

    def test_narracao_de_um_roteiro_pelo_voicestudio(self):
        roteiro = self.tmp / "r.json"
        roteiro.write_text(json.dumps({"scenes": [{"say": "Primeira cena."}, {"say": "Segunda cena."}]}), encoding="utf-8")
        voz.salvar_preferencia({**voz.PADRAO, "motor": "voicestudio", "perfil": "p1"})
        with mock.patch.object(voz, "VOICESTUDIO", self.url), mock.patch.object(sys, "argv", ["voz.py", str(roteiro), "--saida", str(self.tmp / "audio")]):
            voz.main()
        tempos = json.loads((self.tmp / "audio" / "tempos.json").read_text(encoding="utf-8"))
        self.assertEqual(tempos["motor"], "voicestudio")
        self.assertEqual(len(tempos["linhas"]), 2)
        self.assertTrue((self.tmp / "audio" / "narracao.wav").exists())
        falas = [p["arguments"] for m, _, p in FalsoVoiceStudio.chamadas if m == "tools/call"]
        self.assertEqual(falas[0], {"text": "Primeira cena.", "profile_id": "p1"})


class TesteEstudio(Base):
    def test_gravacao_vira_a_referencia_em_wav(self):
        r = estudio_voz.salvar_amostra("gravacao.wav", wav_bytes(12))
        self.assertTrue(r["ok"], r)
        self.assertEqual(sf.info(str(voz.AMOSTRA)).samplerate, 24000)
        self.assertAlmostEqual(r["duracao"], 12, delta=0.2)
        self.assertIn("curta", estudio_voz.salvar_amostra("g.wav", wav_bytes(2))["saida"])
        self.assertFalse(estudio_voz.salvar_amostra("virus.exe", b"x")["ok"])
        self.assertEqual(estudio_voz.arquivo("amostra.wav"), voz.AMOSTRA)
        self.assertIsNone(estudio_voz.arquivo("../../voz.json"))

    def test_escolha_da_voz_e_argumentos_conferidos(self):
        self.assertFalse(estudio_voz.preferir({"motor": "chatterbox"})["ok"])  # sem gravação
        self.assertTrue(estudio_voz.preferir({"motor": "kokoro", "voz": "pf_dora"})["ok"])
        self.assertEqual(voz.preferencia()["voz"], "pf_dora")
        self.assertFalse(estudio_voz.preferir({"motor": "rm"})["ok"])
        args, nome = estudio_voz.args_teste({"motor": "kokoro", "voz": "pm_alex", "texto": "--motor=x oi"})
        self.assertIn("--texto=--motor=x oi", args)  # o texto nunca vira opção
        self.assertTrue(nome.endswith("-kokoro.wav"))
        for ruim in ({"motor": "x"}, {"motor": "kokoro", "voz": "y"}, {"motor": "voicestudio", "perfil": "a b;c"}):
            with self.assertRaises(ValueError):
                estudio_voz.args_teste(ruim)

    def test_frase_de_teste_pelo_terminal(self):
        saida = self.tmp / "t.wav"
        r = subprocess.run([sys.executable, str(Path(voz.__file__)), "--texto=Oi, tudo bem?", f"--saida={saida}", "--motor=teste"],
                           capture_output=True, text=True, cwd=voz.RAIZ)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertGreater(sf.info(str(saida)).duration, 0.5)


class TesteRotas(Base):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), servidor.Painel)
        cls.porta = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def pedir(self, metodo, caminho, corpo=None, cab=None):
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=20)
        c.request(metodo, caminho, body=corpo, headers=cab or {})
        r = c.getresponse()
        return r.status, r.read()

    def test_gravar_testar_e_ouvir_pela_janela(self):
        tk = {"X-Ciello-Token": servidor.TOKEN}
        cod, r = self.pedir("POST", "/api/enviar?tipo=voz&nome=gravacao.wav", wav_bytes(10), tk)
        self.assertTrue(json.loads(r)["ok"], r)
        self.assertEqual(self.pedir("GET", "/api/voz/arquivo/amostra.wav")[0], 200)
        d = json.loads(self.pedir("GET", "/api/app/voz")[1])
        self.assertTrue(d["amostra"]["existe"])
        with mock.patch.object(servidor.status, "registrar"):
            r = json.loads(self.pedir("POST", "/api/operar", json.dumps({"op": "voz_testar", "dados": {"motor": "teste", "texto": "Testando a voz."}}),
                                      {**tk, "Content-Type": "application/json"})[1])
            self.assertTrue(r["ok"], r)
            for _ in range(100):
                ex = json.loads(self.pedir("GET", f"/api/execucao/{r['execucao']}")[1])
                if ex["terminou"]:
                    break
                time.sleep(0.1)
        self.assertEqual(ex["codigo"], 0, ex["saida"])
        cod, wav = self.pedir("GET", f"/api/voz/arquivo/{r['arquivo']}")
        self.assertEqual(cod, 200)
        self.assertEqual(wav[:4], b"RIFF")


if __name__ == "__main__":
    unittest.main()
