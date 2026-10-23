"""python -m unittest discover central/testes  (galeria de estilos do Estúdio de Vídeo: Opus 98 e a biblioteca)"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ["CIELLO_COMERCIAL"] = str(Path(__file__).resolve().parents[2] / "exemplo" / "comercial")  # a empresa fictícia
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "escritorio"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import estilos  # noqa: E402
import servidor  # noqa: E402


class TesteEstilos(unittest.TestCase):
    def test_catalogo_completo_e_em_portugues(self):
        c = estilos.catalogo()
        self.assertEqual(len(c["opus98"]), 98)
        self.assertGreaterEqual(len(c["biblioteca"]), 59)
        ids = [e["id"] for e in c["opus98"] + c["biblioteca"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(e["nome"] != e["nome_en"] for e in c["opus98"]), "estilo do Opus 98 sem nome em português")
        self.assertTrue(all(e["prompt_en"] for e in c["opus98"]))
        self.assertEqual(len(c["capitulos"]), 10)
        for e in c["biblioteca"]:
            self.assertTrue((estilos.PASTA / "biblioteca" / f"{e['id']}.md").exists(), e["id"])

    def test_galeria_tem_miniatura_e_nao_leva_o_prompt(self):
        g = estilos.galeria()
        self.assertTrue(all(e["imagem"] for e in g["opus98"] + g["biblioteca"]))
        self.assertNotIn("prompt_en", g["opus98"][0])
        self.assertEqual(g["opus98"][44]["filme"], "The Godfather")

    def test_guia_do_estilo(self):
        o98 = estilos.guia("o98-66")
        self.assertIn("Style prompt", o98)
        self.assertIn("Schindler's List", o98)
        self.assertIn("Watercolor", estilos.guia("watercolor"))
        with self.assertRaises(SystemExit):
            estilos.guia("nao-existe")

    def test_pedido_ao_claude(self):
        p = estilos.pedido("o98-45", "2026-10-29-comandos-plano", empresa="Lumi Tecnologia")
        self.assertIn("python central/estilos.py ver o98-45", p)
        self.assertIn("roteiros/2026-10-29-comandos-plano.json", p)
        self.assertIn("midia/estudio/2026-10-29-comandos-plano-o98-45.mp4", p)
        self.assertIn("produtor-video", p)
        self.assertIn("Não publique", p)
        livre = estilos.pedido("watercolor", tema="IA no atendimento", data="2026-11-02")
        self.assertIn("um reel sobre: IA no atendimento", livre)
        self.assertIn("roteiros/2026-11-02-<slug>.json", livre)
        with self.assertRaises(ValueError):
            estilos.pedido("nao-existe", "2026-10-29-x")

    def test_operacao_guarda_o_estilo_do_roteiro(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "roteiros").mkdir()
            (raiz / "roteiros" / "2026-10-29-teste.json").write_text("{}", encoding="utf-8")
            with mock.patch.object(servidor, "RAIZ", raiz), mock.patch.object(estilos, "ESCOLHAS", raiz / "estado" / "estilos.json"):
                r = servidor.operar("video_estilo", {"estilo": "o98-12", "post": "2026-10-29-teste"})
                self.assertTrue(r["ok"], r)
                self.assertIn("o98-12", r["prompt"])
                self.assertEqual(estilos.escolhas(), {"2026-10-29-teste": "o98-12"})
                self.assertFalse(servidor.operar("video_estilo", {"estilo": "o98-12", "post": "2026-10-29-falta"})["ok"])
                self.assertFalse(servidor.operar("video_estilo", {"estilo": "x", "tema": "algo"})["ok"])
                self.assertTrue(servidor.operar("video_estilo", {"estilo": "ukiyoe", "tema": "algo"})["ok"])
                self.assertEqual(json.loads((raiz / "estado" / "estilos.json").read_text(encoding="utf-8")), {"2026-10-29-teste": "o98-12"})


if __name__ == "__main__":
    unittest.main()
