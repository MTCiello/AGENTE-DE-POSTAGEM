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

    def test_entrada_responde_na_hora(self):
        self.qualificar()
        sdr.cmd_entrada(NS(nome="Ana Paula", empresa="Clínica Bem", telefone="(49) 98888-1111", origem="anuncio", segmento="odontologia",
                           cidade="Chapecó", mensagem="quanto custa?", assinatura="Mateus"))
        nova = next(l for l in sdr.ler_leads() if l["empresa"] == "Clínica Bem")
        self.assertEqual((nova["etapa"], nova["origem"]), ("respondeu", "entrada: anuncio"))
        self.assertIn("quanto custa?", nova["obs"])
        msg = sdr.resposta_entrada("Ana", "anuncio", "Mateus")
        self.assertIn("pelo anúncio", msg)
        self.assertIn("quantas pessoas atendem", msg)
        # quem já estava na base (veio do Maps) e chamou sozinho sobe para "respondeu" sem duplicar
        sdr.cmd_entrada(NS(nome="", empresa="", telefone="49 99912-3456", origem="instagram", segmento="", cidade="", mensagem="", assinatura="Mateus"))
        leads = sdr.ler_leads()
        self.assertEqual(len(leads), 3)
        self.assertEqual(next(l for l in leads if l["empresa"] == "Imobiliária Sol")["etapa"], "respondeu")
        sdr.BLOQUEIO.write_text("5549977776666\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            sdr.cmd_entrada(NS(nome="", empresa="X", telefone="49 97777-6666", origem="site", segmento="", cidade="", mensagem="", assinatura="Mateus"))



class TesteDuasOfertas(TesteSDR):
    """CRM para quem tem site; site para quem não tem (ou só tem Instagram)."""

    def test_oferta_e_mensagem_por_lead(self):
        leads = {l["empresa"]: l for l in self.qualificar()}
        self.assertEqual(leads["Imobiliária Sol"]["oferta"], "crm")
        self.assertEqual(leads["Pet Feliz"]["oferta"], "site")
        cfg = sdr.icp()
        self.assertIn("CIELLO CRM", sdr.primeira_mensagem(leads["Imobiliária Sol"], cfg, "Mateus"))
        msg = sdr.primeira_mensagem(leads["Pet Feliz"], cfg, "Mateus")
        self.assertIn("não encontrei um site", msg)
        self.assertIn("7 dias úteis", msg)
        self.assertIn("Google", sdr.seguimento(leads["Pet Feliz"], 2))
        so_insta = {**leads["Imobiliária Sol"], "oferta": "", "site": "https://www.instagram.com/imobsol"}
        self.assertEqual(sdr.oferta(so_insta), "site")
        self.assertIn("só com o Instagram", sdr.primeira_mensagem(so_insta, cfg, "Mateus"))
        self.assertEqual(sdr.oferta({"site": "https://linktr.ee/x"}), "site")
        self.assertEqual(sdr.oferta({"site": "https://sol.com.br"}), "crm")


class TesteInstalarScraper(unittest.TestCase):
    ASSETS = [{"name": n, "size": 3, "browser_download_url": f"https://exemplo/{n}"} for n in (
        "google-maps-scraper-1.9.2-darwin-amd64", "google-maps-scraper-1.9.2-linux-amd64",
        "google-maps-scraper-1.9.2-windows-amd64.exe", "checksums.txt")]

    def test_escolhe_o_executavel_do_sistema(self):
        self.assertEqual(sdr.escolher_executavel(self.ASSETS, "Windows", "AMD64")["name"], "google-maps-scraper-1.9.2-windows-amd64.exe")
        self.assertEqual(sdr.escolher_executavel(self.ASSETS, "Linux", "x86_64")["name"], "google-maps-scraper-1.9.2-linux-amd64")
        self.assertIsNone(sdr.escolher_executavel(self.ASSETS, "Windows", "ARM64"))

    def test_baixa_para_comercial_bin_e_troca_a_versao_antiga(self):
        import io
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "bin").mkdir()
            (Path(d) / "bin" / "google-maps-scraper-1.8.0-windows-amd64.exe").write_bytes(b"velho")
            respostas = [io.BytesIO(json.dumps({"tag_name": "v1.9.2", "assets": self.ASSETS}).encode()), io.BytesIO(b"exe")]
            with mock.patch.object(sdr, "PASTA", Path(d)), mock.patch.object(sdr, "RAIZ", Path(d).parent), \
                    mock.patch.object(sdr.urllib.request, "urlopen", side_effect=lambda *a, **k: respostas.pop(0)), \
                    mock.patch.object(sdr, "escolher_executavel", side_effect=lambda assets: assets[2]):
                sdr.cmd_instalar_scraper(NS(forcar=True))
            self.assertEqual([p.name for p in (Path(d) / "bin").iterdir()], ["google-maps-scraper-1.9.2-windows-amd64.exe"])
            self.assertEqual((Path(d) / "bin" / "google-maps-scraper-1.9.2-windows-amd64.exe").read_bytes(), b"exe")


class TesteAgendaDemo(TesteSDR):
    """Agendar a demo: data e hora no lead, confirmação, link do Google Agenda e lembrete no dia."""

    def test_agendar_e_agenda(self):
        self.qualificar()
        hoje = dt.date.today()
        quando = dt.datetime.combine(hoje, dt.time(15, 30))
        sdr.cmd_agendar(NS(id=1, quando=quando.strftime("%Y-%m-%dT%H:%M"), obs="quer ver o funil", assinatura="Mateus"))
        l = sdr.ler_leads()[0]
        self.assertEqual((l["etapa"], l["agenda"], l["proximo_contato"]), ("demo", quando.strftime("%Y-%m-%dT%H:%M"), hoje.isoformat()))
        self.assertIn("quer ver o funil", l["obs"])
        ag = sdr.agenda(hoje)
        self.assertEqual([x["empresa"] for x in ag["proximas"]], ["Imobiliária Sol"])
        self.assertIn("hoje às 15:30", ag["proximas"][0]["mensagem"])  # no dia: lembrete
        self.assertTrue(ag["proximas"][0]["link"].startswith("https://wa.me/"))
        # no dia seguinte, a demo que ficou em "demo" pede o desfecho
        depois = sdr.agenda(hoje + dt.timedelta(days=1))
        self.assertEqual((depois["proximas"], [x["id"] for x in depois["sem_desfecho"]]), ([], [l["id"]]))
        # com desfecho (proposta), sai das duas listas
        sdr.cmd_marcar(NS(id=1, etapa="proposta", obs=""))
        self.assertEqual(sdr.agenda(hoje + dt.timedelta(days=1)), {"proximas": [], "sem_desfecho": []})

    def test_link_e_confirmacao(self):
        l = {"empresa": "Ótica Centro", "telefone": "5549999123456", "site": "https://otica.com.br", "obs": ""}
        quando = dt.datetime(2030, 3, 4, 9, 0)
        url = sdr.link_agenda(l, quando)
        self.assertIn("dates=20300304T090000%2F20300304T092000", url)
        self.assertIn("ctz=America%2FSao_Paulo", url)
        self.assertIn("CIELLO CRM", sdr.msg_confirmacao(l, quando))
        self.assertIn("04/03 às 09:00", sdr.msg_confirmacao(l, quando))
        self.assertIn("como ficaria o de vocês", sdr.msg_confirmacao({**l, "site": ""}, quando))

    def test_data_invalida(self):
        self.qualificar()
        with self.assertRaises(SystemExit):
            sdr.cmd_agendar(NS(id=1, quando="amanhã cedo", obs="", assinatura="Mateus"))


if __name__ == "__main__":
    unittest.main()
