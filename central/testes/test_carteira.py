"""python -m unittest discover central/testes  (saúde da carteira de clientes)"""
import datetime as dt
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

os.environ["CIELLO_COMERCIAL"] = str(Path(__file__).resolve().parents[2] / "exemplo" / "comercial")  # a empresa fictícia
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import carteira  # noqa: E402
import financeiro as fin  # noqa: E402

REF = dt.date(2026, 10, 23)


class TesteCarteira(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(fin, "PASTA", self.tmp), mock.patch.multiple(fin, CLIENTES=self.tmp / "clientes.csv", FATURAS=self.tmp / "faturas.csv",
                                                                                CONFIG=self.tmp / "config.json"),
                  mock.patch.object(fin, "hoje", lambda: REF)):
            p.start()
            self.addCleanup(p.stop)
        base = {"valor_mensal": "397.00", "dia_vencimento": "10", "plano": "crm", "status": "ativo", "whatsapp": "49 99999-0000",
                "posvenda": "1,7,30,90,avaliacao"}
        fin.gravar(fin.CLIENTES, fin.C_CLIENTE, [
            {**base, "id": "1", "empresa": "Feliz", "contato": "Ana", "inicio": "2025-06-01", "nps": "10", "ultimo_contato": "2026-10-01"},
            {**base, "id": "2", "empresa": "Atrasada", "contato": "Rui", "inicio": "2025-06-01", "nps": "8", "ultimo_contato": "2026-10-01"},
            {**base, "id": "3", "empresa": "Calada", "contato": "Lia", "inicio": "2025-06-01", "nps": "", "ultimo_contato": "2026-06-01"},
            {**base, "id": "4", "empresa": "Brava", "contato": "Edu", "inicio": "2026-09-01", "nps": "4", "posvenda": "1,7"},
            {**base, "id": "5", "empresa": "Cancelada", "inicio": "2025-01-01", "status": "cancelado"},
        ])
        f = lambda i, cid, venc, pago: {"id": str(i), "cliente_id": cid, "competencia": venc[:7], "vencimento": venc, "valor": "397.00", "pago_em": pago,
                                        "lancamento": "", "cobrancas": "", "descricao": ""}
        fin.gravar(fin.FATURAS, fin.C_FATURA, [
            f(1, "1", "2026-09-10", "2026-09-10"), f(2, "1", "2026-10-10", "2026-10-09"),
            f(3, "2", "2026-08-10", "2026-08-20"), f(4, "2", "2026-09-10", "2026-09-19"), f(5, "2", "2026-10-03", ""),
        ])

    def test_notas_e_motivos(self):
        r = carteira.carteira(REF)
        s = {x["empresa"]: x for x in r["clientes"]}
        self.assertNotIn("Cancelada", s)
        self.assertEqual((s["Feliz"]["nota"], s["Feliz"]["nivel"], s["Feliz"]["acao"]), (100, "saudavel", "Pedir indicação"))
        self.assertIn("Falo com cuidado", s["Feliz"]["mensagem"])
        # atrasada: 20 dias de atraso (-40), costuma atrasar ~10 dias (-15), nota 8 (-10)
        self.assertEqual(s["Atrasada"]["nota"], 35)
        self.assertEqual(s["Atrasada"]["motivos"][:2], ["fatura atrasada há 20 dias", "costuma pagar com 10 dias de atraso"])
        self.assertTrue(s["Atrasada"]["acao"].startswith("Cobrar") and not s["Atrasada"]["mensagem"])
        # calada: sem nota (-5) e 144 dias sem conversa (-20)
        self.assertEqual((s["Calada"]["nota"], s["Calada"]["nivel"], s["Calada"]["acao"]), (75, "atencao", "Puxar conversa"))
        self.assertIn("sem conversa há 144 dias", s["Calada"]["motivos"])
        # brava: nota 4 (-35), 52 dias sem conversa (-10), primeiros 90 dias (-5), pós-venda D+30 pendente (-5)
        self.assertEqual((s["Brava"]["nota"], s["Brava"]["nivel"]), (45, "risco"))
        self.assertIn("Vi a sua nota", s["Brava"]["mensagem"])
        self.assertEqual([x["empresa"] for x in r["clientes"]][0], "Atrasada")  # pior primeiro
        self.assertEqual((r["contagem"], r["mrr_em_risco"]), ({"saudavel": 1, "atencao": 1, "risco": 2}, 794.0))

    def test_conversa_zera_o_tempo_sem_contato(self):
        with mock.patch("sys.stdout"):
            fin.cmd_conversa(NS(id="3", texto="liguei, equipe usando bem   o funil"))
        c = next(c for c in fin.ler(fin.CLIENTES, fin.C_CLIENTE) if c["id"] == "3")
        self.assertEqual((c["ultimo_contato"], c["obs"]), ("2026-10-23", "23/10: liguei, equipe usando bem o funil"))
        s = next(x for x in carteira.carteira(REF)["clientes"] if x["id"] == "3")
        self.assertEqual((s["nota"], s["nivel"]), (95, "saudavel"))


if __name__ == "__main__":
    unittest.main()
