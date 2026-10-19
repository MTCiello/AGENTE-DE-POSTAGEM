"""python -m unittest discover central/testes"""
import csv
import datetime as dt
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sdr  # noqa: E402

ICP_ORIGINAL = sdr.ICP

AVAL_DOR = json.dumps([{"Name": "Ana", "Rating": 2, "Description": "Ótimo produto, mas pedi orçamento pelo WhatsApp e ninguém me respondeu por dois dias."}])
AVAL_OK = json.dumps([{"Name": "Rui", "Rating": 5, "Description": "Atendimento excelente."}])
BRUTO = [
    {"input_id": "imobiliária em Chapecó SC #!#imobiliaria", "title": "Imobiliária Sol", "phone": "(49) 99912-3456", "website": "https://sol.com.br",
     "review_count": "180", "review_rating": "4.6", "address": "Rua X, Centro, Chapecó - SC", "link": "https://maps.google.com/?cid=1", "user_reviews": AVAL_DOR, "emails": "", "status": ""},
    {"input_id": "pet shop em Chapecó SC #!#pet", "title": "Pet Feliz", "phone": "(49) 3322-1100", "website": "",
     "review_count": "12", "review_rating": "4.9", "address": "Chapecó - SC", "link": "https://maps.google.com/?cid=2", "user_reviews": AVAL_OK, "emails": "", "status": ""},
    {"input_id": "imobiliária em Chapecó SC #!#imobiliaria", "title": "Imóveis Fechada", "phone": "(49) 99988-7766", "website": "",
     "review_count": "50", "review_rating": "4.0", "address": "Chapecó - SC", "link": "https://maps.google.com/?cid=3", "user_reviews": "", "emails": "", "status": "Permanently closed"},
]


class TesteSDR(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copy(ICP_ORIGINAL, self.tmp / "icp.json")
        for nome, valor in {"PASTA": self.tmp, "ICP": self.tmp / "icp.json", "LEADS": self.tmp / "leads.csv", "BLOQUEIO": self.tmp / "nao-contatar.txt"}.items():
            setattr(sdr, nome, valor)
        self.bruto = self.tmp / "resultados.csv"
        with self.bruto.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(BRUTO[0]))
            w.writeheader()
            w.writerows(BRUTO)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def qualificar(self):
        sdr.cmd_qualificar(NS(arquivo=str(self.bruto), segmento="", minimo=0))
        return sdr.ler_leads()

    def test_telefone(self):
        self.assertEqual(sdr.normalizar_fone("(49) 99912-3456"), ("5549999123456", True))
        self.assertEqual(sdr.normalizar_fone("49 3322-1100"), ("554933221100", False))
        self.assertEqual(sdr.normalizar_fone("123"), ("", False))

    def test_qualificar(self):
        leads = self.qualificar()
        self.assertEqual([l["empresa"] for l in leads], ["Imobiliária Sol", "Pet Feliz"])  # fechada sai, ordem por pontos
        sol = leads[0]
        self.assertEqual(sol["segmento"], "imobiliaria")
        self.assertEqual(sol["whatsapp"], "sim")
        self.assertIn("ninguém me respondeu", sol["dor_citada"])
        self.assertGreater(int(sol["pontos"]), int(leads[1]["pontos"]))
        self.assertEqual(len(self.qualificar()), 2)  # rodar de novo não duplica

    def test_abordar_e_cadencia(self):
        self.qualificar()
        sdr.cmd_abordar(NS(top=5, assinatura="Mateus"))
        md = next((self.tmp / "abordagens").glob("*.md")).read_text(encoding="utf-8")
        self.assertIn("https://wa.me/5549999123456?text=", md)
        self.assertIn("me avisa que não mando mais", md)
        sdr.cmd_marcar(NS(id=1, etapa="contatado", obs=""))
        l = sdr.ler_leads()[0]
        self.assertEqual(l["proximo_contato"], (dt.date.today() + dt.timedelta(days=2)).isoformat())
        for _ in range(3):
            sdr.cmd_marcar(NS(id=1, etapa="contatado", obs=""))
        self.assertEqual(sdr.ler_leads()[0]["etapa"], "frio")

    def test_nao_contatar_e_crm(self):
        self.qualificar()
        sdr.cmd_marcar(NS(id=1, etapa="nao_contatar", obs="pediu para não receber"))
        self.assertIn("5549999123456", sdr.bloqueados())
        sdr.cmd_crm(NS(todos=True, separador=";"))
        csv_crm = next(self.tmp.glob("crm-*.csv")).read_text(encoding="utf-8-sig")
        self.assertNotIn("Imobiliária Sol", csv_crm)
        self.assertIn("Pet Feliz", csv_crm)


if __name__ == "__main__":
    unittest.main()
