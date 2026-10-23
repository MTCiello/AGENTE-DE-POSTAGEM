"""python -m unittest discover central/testes  (gastos fixos e o que passa despercebido no extrato)"""
import datetime as dt
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import financeiro as fin  # noqa: E402
import gastos  # noqa: E402
import plano  # noqa: E402

REF = dt.date(2026, 10, 23)


def l(data, desc, valor, cat="Ferramentas e software"):
    return {"id": "", "data": data, "descricao": desc, "valor": f"{valor:.2f}", "categoria": cat, "fitid": "", "fatura_id": "", "origem": "ofx"}


class TesteGastos(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        p = mock.patch.object(fin, "PASTA", self.tmp)
        p.start()
        self.addCleanup(p.stop)

    def test_nome_sem_prefixo_e_numeros(self):
        self.assertEqual(gastos.nome("COMPRA CARTAO ANTHROPIC *CLAUDE 10/10"), "anthropic claude")
        self.assertEqual(gastos.nome("PIX ENVIADO Contabilidade Oeste Ltda"), "contabilidade oeste ltda")
        self.assertEqual(gastos.nome("Pagamento de boleto HOSTINGER 8812"), "hostinger")

    def test_alertas(self):
        lancs = [
            # Claude: todo mês, subiu em outubro
            l("2026-08-10", "ANTHROPIC *CLAUDE", -110), l("2026-09-10", "ANTHROPIC *CLAUDE", -110), l("2026-10-10", "ANTHROPIC *CLAUDE", -121.44),
            # Canva: cobrado 2 vezes em outubro
            l("2026-09-03", "CANVA PRO", -59.9), l("2026-10-03", "CANVA PRO", -59.9), l("2026-10-05", "CANVA PRO", -59.9),
            # servidor: todo dia 5, não veio em outubro
            l("2026-08-05", "HOSTINGER BR", -61.5), l("2026-09-05", "HOSTINGER BR", -61.5),
            # nova: apareceu agora
            l("2026-10-15", "HEYGEN TECHNOLOGY", -169.18),
            # combustível varia: não é conta fixa
            l("2026-09-12", "POSTO IPIRANGA", -120, "a classificar"), l("2026-10-12", "POSTO IPIRANGA", -260, "Combustível"),
            # transferência e retirada não contam
            l("2026-09-20", "TRANSF MESMA TITULARIDADE", -500, "Transferência entre contas"), l("2026-10-20", "TRANSF MESMA TITULARIDADE", -500, "Transferência entre contas"),
            l("2026-10-01", "Pagamento cliente", 397, "Receita de assinaturas"),
        ]
        plano.gravar({**plano.PADRAO, "custos": [{"item": "Claude Code", "valor": 121.44, "frequencia": "mensal", "categoria": "ferramentas"}], "negocios": []})
        r = gastos.analisar(REF, lancs)
        tipos = {(a["tipo"], a["item"]["nome"]) for a in r["alertas"]}
        self.assertIn(("subiu", "anthropic claude"), tipos)
        self.assertIn(("dobro", "canva pro"), tipos)
        self.assertIn(("parou", "hostinger br"), tipos)
        self.assertIn(("nova", "heygen technology"), tipos)
        self.assertIn(("fora_do_plano", "hostinger br"), tipos)
        self.assertNotIn(("fora_do_plano", "anthropic claude"), tipos)  # "Claude Code" no plano
        self.assertEqual(r["alertas"][0]["tipo"], "dobro")  # o mais grave primeiro
        nomes = [f["nome"] for f in r["fixos"]]
        self.assertNotIn("posto ipiranga", nomes)
        self.assertNotIn("transf mesma titularidade", nomes)
        self.assertEqual(r["plano_mensal"], 121.44)
        claude = next(f for f in r["fixos"] if f["nome"] == "anthropic claude")
        self.assertEqual((claude["valor"], claude["anterior"], claude["dia"], claude["meses"]), (121.44, 110.0, 10, 3))
        self.assertAlmostEqual(r["total_mensal"], 121.44 + 59.9 + 61.5)  # o hostinger de setembro ainda conta

    def test_pix_avulso_nao_e_assinatura_nova(self):
        lancs = [l("2026-09-02", "CANVA PRO", -59.9), l("2026-10-08", "PIX PADARIA EVENTO", -120, "a classificar"), l("2026-10-15", "HEYGEN", -169.18)]
        self.assertEqual([a["item"]["nome"] for a in gastos.analisar(REF, lancs)["alertas"] if a["tipo"] == "nova"], ["heygen"])
        plano.gravar({**plano.PADRAO, "custos": [{"item": "Heygen", "valor": 169.18, "frequencia": "mensal"}], "negocios": []})
        self.assertNotIn("nova", {a["tipo"] for a in gastos.analisar(REF, lancs)["alertas"]})  # já foi para o plano

    def test_sem_extrato_do_mes_nao_acusa_conta_parada(self):
        lancs = [l("2026-08-05", "HOSTINGER", -61.5), l("2026-09-05", "HOSTINGER", -61.5)]
        self.assertNotIn("parou", {a["tipo"] for a in gastos.analisar(REF, lancs)["alertas"]})  # outubro ainda não foi importado


if __name__ == "__main__":
    unittest.main()
