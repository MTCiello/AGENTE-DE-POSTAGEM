"""python -m unittest discover central/testes"""
import csv
import datetime as dt
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import briefing  # noqa: E402
import financeiro as fin  # noqa: E402
import status  # noqa: E402
import vigia  # noqa: E402

PAGINA = """<html><head><title>Planos</title><style>.x{}</style><script>var preco = "R$ 1,00";</script></head><body>
<nav>Entrar</nav><h1>Planos</h1><div class="card"><h2>Básico</h2><p>R$ <span>{basico}</span>/mês por usuário</p></div>
<div class="card"><h2>Pro</h2><p>R$ 117,90/mês</p><ul><li>WhatsApp integrado</li><li>{extra}</li></ul></div></body></html>"""


class Silencioso(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


class TesteVigia(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "site").mkdir()
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(Silencioso, directory=str(self.tmp / "site")))
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        base = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.cfg = self.tmp / "concorrentes.json"
        self.cfg.write_text(json.dumps({"concorrentes": [{"nome": "CRM X", "anuncios": "CRM X", "urls": [
            {"rotulo": "preços", "url": f"{base}/precos.html"}, {"rotulo": "fora do ar", "url": f"{base}/nao-existe.html"}]}]}), encoding="utf-8")

    def pagina(self, basico, extra):
        (self.tmp / "site" / "precos.html").write_text(PAGINA.replace("{basico}", basico).replace("{extra}", extra), encoding="utf-8")

    def checar(self):
        with mock.patch.dict(os.environ, {"NO_PROXY": "127.0.0.1", "no_proxy": "127.0.0.1"}):
            vigia.cmd_checar(NS(arquivo=str(self.cfg), so=None, saida=str(self.tmp / "radar"), fotos=str(self.tmp / "fotos")))
        return max((self.tmp / "radar").glob("concorrentes-*.md"), key=lambda p: p.stat().st_mtime_ns).read_text(encoding="utf-8")

    def test_texto_e_precos(self):
        txt = vigia.texto_visivel(PAGINA.replace("{basico}", "65,70").replace("{extra}", "Funil"))
        self.assertNotIn("var preco", txt)
        self.assertIn("R$ 65,70/mês", txt)  # o <span> no meio do preço não quebra a linha
        self.assertEqual(vigia.precos(txt), ["R$ 117,90/mês", "R$ 65,70/mês por usuário"])

    def test_detecta_mudanca_de_preco_e_nao_sobrescreve(self):
        self.pagina("65,70", "Funil de vendas")
        rel1 = self.checar()
        self.assertIn("1ª foto guardada", rel1)
        self.assertIn("não consegui abrir", rel1)
        self.assertIn("facebook.com/ads/library", rel1)
        self.checar_igual = self.checar()
        self.assertIn("sem mudança", self.checar_igual)
        self.pagina("79,90", "Agente de IA no WhatsApp")
        rel3 = self.checar()
        self.assertIn("**mudou**", rel3)
        self.assertIn("R$ 65,70/mês por usuário → R$ 79,90/mês por usuário", rel3)
        self.assertIn("Agente de IA no WhatsApp", rel3)
        self.assertEqual(len(list((self.tmp / "radar").glob("concorrentes-*.md"))), 3)  # relatórios do mesmo dia não se apagam


class TesteBriefing(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for d in ("roteiros", "midia/final", "metricas", "radar", "financeiro", "comercial", "estado", "anuncios"):
            (self.tmp / d).mkdir(parents=True)
        pasta = self.tmp / "financeiro"
        shutil.copy(fin.REGRAS, pasta / "categorias.json")
        self.ref = dt.date(2026, 11, 20)
        ps = [mock.patch.multiple(fin, PASTA=pasta, CLIENTES=pasta / "clientes.csv", FATURAS=pasta / "faturas.csv",
                                  LANCAMENTOS=pasta / "lancamentos.csv", CONFIG=pasta / "config.json", REGRAS=pasta / "categorias.json"),
              mock.patch.object(fin, "hoje", lambda: self.ref),
              mock.patch.multiple(briefing, RAIZ=self.tmp, LEADS=self.tmp / "comercial" / "leads.csv"),
              mock.patch.object(status, "EVENTOS", self.tmp / "estado" / "eventos.jsonl")]
        for p in ps:
            p.start()
            self.addCleanup(p.stop)

    def test_prioridades_na_ordem_certa(self):
        fin.cmd_cliente(NS(empresa="Imobiliária Sol", lead=None, contato="Ana", whatsapp="49999990000", plano="", valor=149, dia=10, inicio="2026-10-01"))
        fin.cmd_faturar(NS(mes="2026-11"))  # vencida há 10 dias
        with (self.tmp / "comercial" / "leads.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "empresa", "etapa", "ultimo_contato", "proximo_contato"])
            w.writeheader()
            w.writerow({"id": 7, "empresa": "Clínica Sorriso", "etapa": "respondeu", "ultimo_contato": "2026-11-18"})
            w.writerow({"id": 8, "empresa": "Ótica Lux", "etapa": "contatado", "ultimo_contato": "2026-11-15", "proximo_contato": "2026-11-20"})
        (self.tmp / "roteiros" / "2026-11-21-dica.json").write_text("{}", encoding="utf-8")  # post amanhã sem vídeo final
        status.registrar("sdr", "esperando", "15 mensagens para aprovar")
        texto = briefing.briefing(self.ref)
        prioridades = texto.split("## Números")[0]
        self.assertLess(prioridades.index("fatura"), prioridades.index("Clínica Sorriso"))
        self.assertIn("espera sua aprovação", prioridades)
        self.assertIn("Post de 21/11", texto)
        self.assertIn("follow-up", texto)
        self.assertIn("MRR** R$ 149,00", texto)
        placar = briefing.placar(self.ref)
        self.assertIn("| Leads trabalhados (contato na semana) | 2 |", placar)


if __name__ == "__main__":
    unittest.main()
