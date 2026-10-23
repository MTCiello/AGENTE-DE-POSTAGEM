"""python -m unittest discover central/testes  (Estúdio de Vídeo: roteiro → projeto HyperFrames)"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ["CIELLO_COMERCIAL"] = str(Path(__file__).resolve().parents[2] / "exemplo" / "comercial")  # a empresa fictícia
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import conteudo  # noqa: E402
import estudio_video as ev  # noqa: E402

ROTEIRO = {"scenes": [
    {"type": "hook", "say": "Três comandos do ChatGPT que respondem cliente por você. Salva antes de fechar o vídeo."},
    {"type": "comando", "say": "Segundo: transforme esta conversa em um orçamento com itens, valor e prazo."},
    {"type": "ponte", "say": "Agora imagina isso no WhatsApp da equipe toda. É o Lumi CRM."},
    {"type": "prompt", "kicker": "Teste 1", "title": [["O cliente", "marfim"], ["desconfiado", "ouro"]], "answer": ["Preço alto", "Marca nova"], "say": "Pede pra ela agir como cliente."},
    {"type": "cta", "say": "Salva pra usar hoje e comenta COMANDOS que eu te mando."}]}


class TesteEstudioVideo(unittest.TestCase):
    def test_titulos_e_itens_saem_do_roteiro(self):
        c = ev.normalizar(ROTEIRO)
        texto = lambda i: " ".join(t for t, _ in c[i]["titulo"])
        self.assertEqual(texto(0), "Três comandos do ChatGPT que respondem cliente")  # sem terminar em "por"
        self.assertEqual((c[1]["kicker"], texto(1)), ("Segundo", "transforme esta conversa em um orçamento"))
        self.assertEqual(texto(2), "É o Lumi CRM")  # ponte: a frase curta é a ideia
        self.assertEqual((c[3]["kicker"], texto(3), c[3]["itens"]), ("Teste 1", "O cliente desconfiado", ["Preço alto", "Marca nova"]))
        self.assertEqual(c[0]["titulo"][-1][1], "ouro")

    def test_legendas_cobrem_a_fala_inteira(self):
        partes = ev.legendas("um dois três quatro cinco seis sete", 1.0, 3.0)
        self.assertEqual([p[0] for p in partes], ["um dois três quatro", "cinco seis sete"])
        self.assertAlmostEqual(partes[0][1], 1.0)
        self.assertAlmostEqual(partes[-1][1] + partes[-1][2], 3.0, places=2)

    def test_projeto_html_com_tempos_audio_e_timeline(self):
        cenas = ev.normalizar(ROTEIRO)
        janelas, total = ev.tempos("nao-existe", cenas)  # sem narração: estimativa
        self.assertEqual(len(janelas), 5)
        self.assertTrue(all(a < b for a, b in janelas))
        h = ev.html_projeto(cenas, janelas, total, "claro", narracao=True, trilha=False)
        self.assertIn('data-composition-id="main"', h)
        self.assertIn(f'data-duration="{total:.3f}"', h)
        self.assertEqual(h.count('class="clip cena'), 5)
        self.assertIn('src="narracao.wav"', h)
        self.assertNotIn("trilha.mp3", h)
        self.assertIn('window.__timelines["main"] = tl;', h)
        self.assertIn("#F8F4E8", h)  # fundo do modelo claro
        self.assertIn("&lt;", ev.html_projeto([{"tipo": "hook", "kicker": "", "titulo": [("<b>x</b>", "ouro")], "itens": [], "fala": "a <i>"}],
                                              [(0, 1)], 2, "escuro", False, False))  # texto do roteiro é escapado

    def test_tempos_da_narracao_real(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "audio" / "x").mkdir(parents=True)
        (tmp / "audio" / "x" / "tempos.json").write_text(json.dumps({"tempos": {"total": 9.5}, "linhas": [{"from": 0, "to": 3.1}, {"from": 3.3, "to": 8.7}]}), encoding="utf-8")
        with mock.patch.object(ev, "RAIZ", tmp):
            janelas, total = ev.tempos("x", [{"fala": "a"}, {"fala": "b"}])
        self.assertEqual((janelas, total), ([(0.0, 3.1), (3.3, 8.7)], 9.5))

    def test_novo_roteiro_escrito_a_mao(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        with mock.patch.object(conteudo, "ROTEIROS", tmp):
            r = conteudo.novo_roteiro("2026-11-23", "Pare de perder cliente no WhatsApp", ["Responda rápido.", "", "Use um funil."], "")
            self.assertTrue(r["ok"], r)
            self.assertEqual(r["post"], "2026-11-23-pare-de-perder-cliente-no-whatsapp")
            d = json.loads((tmp / f"{r['post']}.json").read_text(encoding="utf-8"))
            self.assertEqual([s["type"] for s in d["scenes"]], ["hook", "item", "item", "cta"])
            self.assertEqual(d["capa"]["linhas"][-1], ["no WhatsApp", "ouro"])
            self.assertFalse(conteudo.novo_roteiro("2026-11-23", "Pare de perder cliente no WhatsApp", ["x"])["ok"])  # não sobrescreve
            self.assertFalse(conteudo.novo_roteiro("amanhã", "x", ["y"])["ok"])
            self.assertFalse(conteudo.novo_roteiro("2026-11-24", "x", [])["ok"])
