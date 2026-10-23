"""python -m unittest discover central/testes  (operação sem o Claude: formulários das janelas do Ciello OS)"""
import datetime as dt
import http.client
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

os.environ["CIELLO_COMERCIAL"] = str(Path(__file__).resolve().parents[2] / "exemplo" / "comercial")  # a empresa fictícia
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "escritorio"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import financeiro as fin  # noqa: E402
import operacao  # noqa: E402
import sdr  # noqa: E402
import servidor  # noqa: E402

HOJE = dt.date(2026, 11, 20)
ICP = Path(__file__).resolve().parent.parent.parent / "exemplo" / "comercial" / "icp.json"
OFX = """OFXHEADER:100
<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><BANKTRANLIST>
<STMTTRN><TRNTYPE>CREDIT<DTPOSTED>20261112<TRNAMT>149.00<FITID>a1<MEMO>PIX RECEBIDO IMOBILIARIA SOL</STMTTRN>
<STMTTRN><TRNTYPE>DEBIT<DTPOSTED>20261113<TRNAMT>-59.90<FITID>a2<MEMO>CANVA PRO</STMTTRN>
</BANKTRANLIST><LEDGERBAL><BALAMT>2500.00<DTASOF>20261115</LEDGERBAL></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>
"""
LEADS_CSV = ("title,phone,website,review_count,review_rating,link\n"
             "Imobiliária Norte,(49) 99911-2233,https://norte.com,40,4.1,https://maps/1\n"
             "Ótica Centro,(49) 3322-1100,,5,4.8,https://maps/2\n")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        f = self.tmp / "financeiro"
        com = self.tmp / "comercial"
        com.mkdir()
        shutil.copy(ICP, com / "icp.json")
        self.patches = [
            mock.patch.multiple(fin, PASTA=f, CLIENTES=f / "clientes.csv", FATURAS=f / "faturas.csv",
                                LANCAMENTOS=f / "lancamentos.csv", CONFIG=f / "config.json", LEADS=com / "leads.csv"),
            mock.patch.object(fin, "hoje", lambda: HOJE),
            mock.patch.multiple(sdr, PASTA=com, ICP=com / "icp.json", LEADS=com / "leads.csv", BLOQUEIO=com / "nao-contatar.txt"),
            mock.patch.object(operacao, "RAIZ", self.tmp),
        ]
        for p in self.patches:
            p.start()
        self.addCleanup(lambda: [p.stop() for p in self.patches])


class TesteOperacao(Base):
    def test_ciclo_do_financeiro_sem_claude(self):
        r = operacao.operar("fin_cliente", {"empresa": "Imobiliária Sol", "valor": "149,00", "dia": "10", "whatsapp": "49 99999-8888",
                                            "contato": "Ana Souza", "inicio": "2026-10-01"})
        self.assertTrue(r["ok"], r)
        self.assertIn("cliente #1", r["saida"])
        self.assertTrue(operacao.operar("fin_faturar", {"mes": "2026-11"})["ok"])
        fatura = fin.ler(fin.FATURAS, fin.C_FATURA)[0]
        self.assertEqual(fatura["vencimento"], "2026-11-10")
        # 10 dias de atraso: a cobrança da etapa D+7 aparece pronta, com o link do WhatsApp
        cob = fin.cobrancas_devidas()
        self.assertEqual((cob[0]["fatura_id"], cob[0]["etapa"]), ("1", 7))
        self.assertTrue(cob[0]["link"].startswith("https://wa.me/5549999998888?text="))
        self.assertTrue(operacao.operar("fin_enviado", {"tipo": "cobranca", "id": "1", "etapa": "7"})["ok"])
        self.assertEqual(fin.cobrancas_devidas(), [])
        # o extrato do banco dá baixa na fatura e classifica a despesa
        r = operacao.importar_arquivo("extrato", "extrato nov.ofx", OFX.encode())
        self.assertTrue(r["ok"], r)
        self.assertIn("1 faturas baixadas", r["saida"])
        self.assertTrue((fin.PASTA / "extratos").is_dir())
        self.assertEqual(fin.situacao(HOJE)["atrasadas"], [])
        lanc = fin.ler(fin.LANCAMENTOS, fin.C_LANC)
        canva = next(l for l in lanc if "CANVA" in l["descricao"])
        self.assertEqual(canva["categoria"], "Ferramentas e software")
        self.assertTrue(operacao.operar("fin_categoria", {"id": canva["id"], "categoria": "Marketing"})["ok"])
        self.assertEqual(fin.ler(fin.LANCAMENTOS, fin.C_LANC)[1]["categoria"], "Marketing")
        self.assertIn("Marketing", fin.categorias())
        # despesa lançada à mão (o sinal vem do formulário), edição, NPS, cancelamento e reativação
        r = operacao.operar("fin_lancar", {"valor": "-1.200,00", "descricao": "-aluguel sala", "data": "2026-11-05"})
        self.assertTrue(r["ok"], r)
        self.assertEqual(fin.ler(fin.LANCAMENTOS, fin.C_LANC)[-1]["valor"], "-1200.00")
        self.assertEqual(fin.ler(fin.LANCAMENTOS, fin.C_LANC)[-1]["descricao"], "-aluguel sala")
        self.assertTrue(operacao.operar("fin_editar", {"id": "1", "valor": "199", "obs": "plano equipe"})["ok"])
        self.assertEqual(fin.ler(fin.CLIENTES, fin.C_CLIENTE)[0]["valor_mensal"], "199.00")
        self.assertTrue(operacao.operar("fin_nps", {"id": "1", "nota": "10"})["ok"])
        self.assertIn("avaliacao", [p["etapa"] for p in fin.posvendas_devidos(HOJE)])
        self.assertTrue(operacao.operar("fin_cancelar", {"id": "1", "motivo": "preço"})["ok"])
        self.assertEqual(fin.situacao(HOJE)["mrr"], 0)
        self.assertTrue(operacao.operar("fin_editar", {"id": "1", "reativar": True})["ok"])
        self.assertEqual(fin.situacao(HOJE)["mrr"], 199)
        self.assertTrue(operacao.operar("fin_config", {"saldo": "3.000", "data": "2026-11-20", "assinatura": "Ana"})["ok"])
        self.assertEqual(fin.config()["saldo_inicial"], 3000.0)

    def test_erros_voltam_como_texto_e_nada_fora_da_lista_roda(self):
        r = operacao.operar("fin_pago", {"id": "99"})
        self.assertFalse(r["ok"])
        self.assertIn("fatura 99 não encontrado", r["saida"])
        self.assertFalse(operacao.operar("fin_cliente", {"empresa": "X"})["ok"])  # sem valor
        self.assertFalse(operacao.operar("os_system", {})["ok"])
        self.assertFalse(operacao.operar("fin_nps", {"id": "1", "nota": "11"})["ok"])
        self.assertFalse(operacao.operar("fin_categoria", {"id": "1", "categoria": "--todos"})["ok"])
        self.assertFalse(operacao.operar("sdr_marcar", {"id": "1", "etapa": "apagar"})["ok"])
        self.assertFalse(operacao.importar_arquivo("extrato", "virus.exe", b"x")["ok"])
        self.assertFalse(operacao.importar_arquivo("outro", "a.csv", b"x")["ok"])
        # o nome do arquivo enviado nunca sai da pasta de dados
        operacao.importar_arquivo("leads", "../../../etc/leads.csv", LEADS_CSV.encode())
        self.assertTrue(any((sdr.PASTA / "bruto").glob("importado-*-leads.csv")))

    def test_ciclo_do_comercial_sem_claude(self):
        r = operacao.importar_arquivo("leads", "lista.csv", LEADS_CSV.encode(), {"segmento": "imobiliaria", "minimo": "0"})
        self.assertTrue(r["ok"], r)
        leads = sdr.ler_leads()
        self.assertEqual(len(leads), 2)
        norte = next(l for l in leads if l["empresa"] == "Imobiliária Norte")
        self.assertTrue(operacao.operar("sdr_marcar", {"id": norte["id"], "etapa": "contatado"})["ok"])
        norte = next(l for l in sdr.ler_leads() if l["id"] == norte["id"])
        self.assertEqual((norte["etapa"], norte["tentativas"]), ("contatado", "1"))
        self.assertTrue(operacao.operar("sdr_anotar", {"id": norte["id"], "texto": "pediu retorno sexta"})["ok"])
        self.assertIn("pediu retorno sexta", sdr.ler_leads()[0]["obs"] + sdr.ler_leads()[1]["obs"])
        r = operacao.operar("sdr_entrada", {"nome": "Carla", "empresa": "Clínica Sorriso", "telefone": "49 98888-7777",
                                            "origem": "instagram", "mensagem": "quanto custa?"})
        self.assertTrue(r["ok"], r)
        self.assertIn("https://wa.me/5549988887777", r["saida"])
        self.assertTrue(operacao.operar("sdr_consultas", {"segmentos": ["imobiliaria"], "cidades": ["Vila Serena SC"]})["ok"])
        self.assertIn("imobiliária em Vila Serena SC", (sdr.PASTA / "bruto" / "consultas.txt").read_text(encoding="utf-8"))
        self.assertTrue(operacao.operar("sdr_crm", {"todos": True})["ok"])
        # fechou: vira cliente no financeiro puxando empresa e WhatsApp do lead
        r = operacao.operar("fin_cliente", {"lead": norte["id"], "valor": "149"})
        self.assertTrue(r["ok"], r)
        self.assertEqual(fin.ler(fin.CLIENTES, fin.C_CLIENTE)[0]["empresa"], "Imobiliária Norte")

    def test_instagram_e_anuncios_anotados_a_mao(self):
        pasta = self.tmp / "metricas"
        pasta.mkdir()
        (pasta / "2026-11-13.json").write_text(json.dumps({"data": "2026-11-13", "perfil": {"seguidores": 60}, "reels": [],
                                                          "melhor_horario": {"seg": [10, 11, 12]}}), encoding="utf-8")
        r = operacao.salvar_retrato({"data": "2026-11-20", "seguidores": "1.063", "alcance": "563",
                                     "reels": [{"gancho": "Se a sua equipe vende pelo WhatsApp", "views": "98", "tempo_medio_s": "7,98"}, {"gancho": ""}]})
        self.assertTrue(r["ok"], r)
        d = json.loads((pasta / "2026-11-20.json").read_text(encoding="utf-8"))
        self.assertEqual(d["perfil"]["seguidores"], 1063)
        self.assertEqual(d["perfil"]["seguidores_inicio"], 60)
        self.assertEqual(d["melhor_horario"], {"seg": [10, 11, 12]})
        self.assertEqual((len(d["reels"]), d["reels"][0]["tempo_medio_s"], d["reels"][0]["data"]), (1, 7.98, "2026-11-20"))
        self.assertFalse(operacao.salvar_retrato({"seguidores": ""})["ok"])
        r = operacao.salvar_campanha({"nome": "Teste imobiliárias", "inicio": "2026-11-03", "gasto": "105,50", "conversas": "14"})
        self.assertTrue(r["ok"], r)
        operacao.salvar_campanha({"nome": "Teste imobiliárias", "inicio": "2026-11-04", "gasto": "120", "clientes": "1"})
        arqs = list((self.tmp / "anuncios").glob("*.json"))
        self.assertEqual(len(arqs), 1)  # atualizar não duplica
        c = json.loads(arqs[0].read_text(encoding="utf-8"))["campanhas"]
        self.assertEqual((len(c), c[0]["gasto"], c[0]["clientes"]), (1, 120.0, 1))


class TesteRotasDeOperacao(Base):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), servidor.Painel)
        cls.porta = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def pedir(self, metodo, caminho, corpo=None, cabecalhos=None):
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=10)
        c.request(metodo, caminho, body=corpo, headers=cabecalhos or {})
        r = c.getresponse()
        return r.status, json.loads(r.read())

    def test_formularios_e_arquivo_pela_janela(self):
        tk = {"X-Ciello-Token": servidor.TOKEN, "Content-Type": "application/json"}
        corpo = json.dumps({"op": "fin_cliente", "dados": {"empresa": "Ótica Luz", "valor": "99,90", "whatsapp": "49 99999-1111"}})
        self.assertEqual(self.pedir("POST", "/api/operar", corpo)[0], 403)  # sem token
        cod, r = self.pedir("POST", "/api/operar", corpo, tk)
        self.assertEqual(cod, 200)
        self.assertTrue(r["ok"], r)
        cod, r = self.pedir("POST", "/api/enviar?tipo=extrato&nome=extrato.ofx", OFX.encode(), {"X-Ciello-Token": servidor.TOKEN})
        self.assertTrue(r["ok"], r)
        _, d = self.pedir("GET", "/api/app/financeiro")
        self.assertEqual(d["clientes"][0]["empresa"], "Ótica Luz")
        self.assertIn("Ferramentas e software", d["categorias"])
        self.assertTrue(d["lancamentos"])
        self.assertEqual(d["config"]["saldo_inicial"], 2500.0)
        operacao.importar_arquivo("leads", "l.csv", LEADS_CSV.encode(), {"segmento": "imobiliaria", "minimo": "0"})
        _, d = self.pedir("GET", "/api/app/comercial")
        self.assertEqual(len(d["leads"]), 2)
        self.assertIn("imobiliaria", d["segmentos"])
        celular = next(l for l in d["abordar"] if l["whatsapp"])
        self.assertIn("Lumi", celular["mensagem"])
        self.assertTrue(celular["link"].startswith("https://wa.me/"))
        self.assertFalse(next(l for l in d["abordar"] if not l["whatsapp"])["link"])  # fixo: ligar
        corpo = json.dumps({"op": "ig_retrato", "dados": {"seguidores": "70"}})
        self.assertTrue(self.pedir("POST", "/api/operar", corpo, tk)[1]["ok"])


if __name__ == "__main__":
    unittest.main()
