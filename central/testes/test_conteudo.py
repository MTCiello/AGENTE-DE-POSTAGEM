"""python -m unittest discover central/testes  (quadro de produção de conteúdo)"""
import datetime as dt
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

HOJE = dt.date(2026, 11, 20)
ROTEIRO = {"capa": {"linhas": [["3 comandos", "marfim"], ["de IA", "ouro"]]},
           "scenes": [{"type": "hook", "say": "Três comandos que respondem cliente."}, {"type": "comando", "say": "Primeiro: responda curto."},
                      {"type": "comando", "say": "Segundo: faça o orçamento."}, {"type": "cta", "say": "Salva pra usar hoje."}]}


class TesteConteudo(unittest.TestCase):
    def setUp(self):
        self.raiz = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.raiz, True)
        (self.raiz / "roteiros").mkdir()
        for nome in ("2026-11-18-velho", "2026-11-21-amanha", "2026-11-25-semana"):
            (self.raiz / "roteiros" / f"{nome}.json").write_text(json.dumps(ROTEIRO), encoding="utf-8")
        (self.raiz / "midia" / "final").mkdir(parents=True)
        (self.raiz / "midia" / "capas").mkdir()
        (self.raiz / "midia" / "final" / "2026-11-25-semana.mp4").write_bytes(b"x")
        (self.raiz / "midia" / "capas" / "2026-11-25-semana.jpg").write_bytes(b"x")
        (self.raiz / "historico.md").write_text("# Histórico\n\n| Data do post | Tema | Viral | Vídeo | Status |\n|---|---|---|---|---|\n"
                                                "| 18/11 10h | velho | x | midia/2026-11-18-velho.mp4 | Rascunho no Metricool |\n", encoding="utf-8")
        for p in (mock.patch.multiple(conteudo, RAIZ=self.raiz, ROTEIROS=self.raiz / "roteiros", HISTORICO=self.raiz / "historico.md"),
                  mock.patch.object(conteudo, "hoje", lambda: HOJE)):
            p.start()
            self.addCleanup(p.stop)

    def test_quadro_e_alertas(self):
        q = {p["slug"]: p for p in conteudo.quadro()}
        self.assertEqual(q["semana"]["proximo"], "legenda")
        self.assertTrue(q["semana"]["etapas"]["final"] and q["semana"]["etapas"]["narracao"])
        self.assertEqual((q["amanha"]["proximo"], q["amanha"]["dono"], q["amanha"]["dias"]), ("narracao", "produtor-video", 1))
        self.assertEqual(q["velho"]["status_historico"], "Rascunho no Metricool")
        al = " | ".join(conteudo.alertas())
        self.assertIn("Post de 21/11 (amanha) sai amanhã", al)
        self.assertIn("1 post(s) com data passada sem registro de publicação (18/11)", al)
        self.assertIn("Só 2 post(s) nos próximos 7 dias", al)
        self.assertEqual(conteudo.proximos_horarios(), ["2026-11-23", "2026-11-27", "2026-11-30"])  # 25/11 já tem post

    def test_legenda_e_registro_de_agendamento(self):
        r = conteudo.gerar_legenda("2026-11-25-semana")
        self.assertTrue(r["ok"])
        self.assertTrue(r["legenda"].startswith("Três comandos que respondem cliente."))
        self.assertIn("👉 Primeiro: responda curto.", r["legenda"])
        self.assertIn("Salva pra usar hoje.", r["legenda"])
        self.assertEqual(conteudo.gerar_legenda("2026-11-25-semana")["saida"], "a legenda já existe")
        self.assertTrue(conteudo.salvar_legenda("2026-11-25-semana", "minha legenda")["ok"])
        self.assertEqual(json.loads((self.raiz / "roteiros" / "2026-11-25-semana.json").read_text(encoding="utf-8"))["legenda"], "minha legenda")
        self.assertTrue(conteudo.marcar_agendado("2026-11-25-semana", "25/11 10h")["ok"])
        self.assertTrue(conteudo.marcar_agendado("2026-11-18-velho", "18/11 10h", "Publicado")["ok"])
        hist = (self.raiz / "historico.md").read_text(encoding="utf-8")
        self.assertIn("| 25/11 10h | 3 comandos de IA | — | midia/final/2026-11-25-semana.mp4 | Agendado", hist)
        self.assertIn("| 18/11 10h | velho | x | midia/2026-11-18-velho.mp4 | Publicado", hist)
        q = {p["slug"]: p for p in conteudo.quadro()}
        self.assertTrue(q["semana"]["pronto"])
        self.assertNotIn("data passada", " ".join(conteudo.alertas()))
        self.assertFalse(conteudo.marcar_agendado("2026-01-01-nao-existe")["ok"])
