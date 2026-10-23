"""python -m unittest discover central/testes"""
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
import financeiro as fin  # noqa: E402

HOJE = dt.date(2026, 11, 20)
OFX = """OFXHEADER:100
DATA:OFXSGML
<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><BANKTRANLIST>
<STMTTRN><TRNTYPE>CREDIT<DTPOSTED>20261111120000[-3:BRT]<TRNAMT>149.00<FITID>A1<MEMO>PIX RECEBIDO IMOBILIARIA SOL LTDA</STMTTRN>
<STMTTRN><TRNTYPE>DEBIT<DTPOSTED>20261112<TRNAMT>-300.00<FITID>A2<MEMO>FACEBK *ADS LUMI</STMTTRN>
<STMTTRN><TRNTYPE>DEBIT<DTPOSTED>20261113<TRNAMT>-110.00<FITID>A3<MEMO>ANTHROPIC CLAUDE</STMTTRN>
<STMTTRN><TRNTYPE>DEBIT<DTPOSTED>20261114<TRNAMT>-12.90<FITID>A4<MEMO>TARIFA PACOTE SERVIÇOS</STMTTRN>
<STMTTRN><TRNTYPE>CREDIT<DTPOSTED>20261115<TRNAMT>57.00<FITID>A5<MEMO>PIX RECEBIDO FULANO</STMTTRN>
</BANKTRANLIST><LEDGERBAL><BALAMT>5000.00<DTASOF>20261115</LEDGERBAL></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>
"""


class TesteFinanceiro(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        pasta = self.tmp / "financeiro"
        pasta.mkdir()
        shutil.copy(fin.REGRAS, pasta / "categorias.json")
        self.patches = [mock.patch.multiple(fin, PASTA=pasta, CLIENTES=pasta / "clientes.csv", FATURAS=pasta / "faturas.csv",
                                            LANCAMENTOS=pasta / "lancamentos.csv", CONFIG=pasta / "config.json",
                                            REGRAS=pasta / "categorias.json", LEADS=self.tmp / "leads.csv"),
                        mock.patch.object(fin, "hoje", lambda: HOJE)]
        for p in self.patches:
            p.start()
        self.addCleanup(lambda: [p.stop() for p in self.patches])
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def cliente(self, empresa, valor=149, dia=10, inicio="2026-10-01", whatsapp="49999990000"):
        fin.cmd_cliente(NS(empresa=empresa, lead=None, contato="Ana Souza", whatsapp=whatsapp, plano="", valor=valor, dia=dia, inicio=inicio))

    def test_numeros_e_datas(self):
        self.assertEqual(fin.num("1.234,56"), 1234.56)
        self.assertEqual(fin.num("R$ 149"), 149.0)
        self.assertEqual(fin.num("-50.00", br=False), -50.0)
        self.assertEqual(fin.num("1.234"), 1234.0)
        self.assertEqual(fin.num("1,234.50"), 1234.5)
        self.assertEqual(fin.data("20261111120000[-3:BRT]"), dt.date(2026, 11, 11))
        self.assertEqual(fin.data("05/11/2026"), dt.date(2026, 11, 5))
        self.assertEqual(fin.vencimento("2026-02", 31), dt.date(2026, 2, 28))
        self.assertEqual(fin.meses_atras("2026-01", 2), "2025-11")
        self.assertEqual(fin.reais(-1234.5), "-R$ 1.234,50")

    def test_classificacao(self):
        r = fin.regras()
        self.assertEqual(fin.classificar("FACEBK *ADS", -300, r), "Anúncios")
        self.assertEqual(fin.classificar("Tarifa pacote serviços", -12.9, r), "Tarifas e juros")
        self.assertEqual(fin.classificar("PAGAMENTO DAS CONTAS DE LUZ", -90, r), fin.SEM_CATEGORIA)  # "das" sozinho não é imposto
        self.assertEqual(fin.classificar("DAS SIMPLES NACIONAL", -76, r), "Impostos")
        self.assertEqual(fin.classificar("PIX RECEBIDO FULANO", 57, r), fin.SEM_CATEGORIA)

    def test_fluxo_extrato_baixa_e_nao_duplica(self):
        self.cliente("Imobiliária Sol")
        self.cliente("Clínica Sorriso")
        fin.cmd_faturar(NS(mes="2026-11"))
        faturas = fin.ler(fin.FATURAS, fin.C_FATURA)
        self.assertEqual(len(faturas), 2)
        ofx = self.tmp / "extrato.ofx"
        ofx.write_bytes(OFX.encode("cp1252"))
        fin.cmd_importar(NS(arquivo=str(ofx)))
        faturas = {f["cliente_id"]: f for f in fin.ler(fin.FATURAS, fin.C_FATURA)}
        self.assertEqual(faturas["1"]["pago_em"], "2026-11-11")  # o nome no Pix desempatou entre dois clientes de R$ 149
        self.assertEqual(faturas["2"]["pago_em"], "")
        lancs = fin.ler(fin.LANCAMENTOS, fin.C_LANC)
        cats = {l["fitid"]: l["categoria"] for l in lancs}
        self.assertEqual(cats["A1"], fin.RECEITA)
        self.assertEqual(cats["A2"], "Anúncios")
        self.assertEqual(cats["A3"], "Ferramentas e software")
        self.assertEqual(fin.config()["saldo_inicial"], 5000.0)
        fin.cmd_importar(NS(arquivo=str(ofx)))
        self.assertEqual(len(fin.ler(fin.LANCAMENTOS, fin.C_LANC)), 5)  # o mesmo extrato de novo não duplica
        fin.cmd_faturar(NS(mes="2026-11"))
        self.assertEqual(len(fin.ler(fin.FATURAS, fin.C_FATURA)), 2)  # faturar de novo também não
        self.cliente("Ótica Lux", dia=15, inicio="2026-11-18")
        fin.cmd_faturar(NS(mes="2026-11"))
        self.assertEqual(len(fin.ler(fin.FATURAS, fin.C_FATURA)), 2)  # começou depois do vencimento: 1ª fatura só em dezembro
        fin.cmd_faturar(NS(mes="2026-12"))
        self.assertEqual(len(fin.ler(fin.FATURAS, fin.C_FATURA)), 5)

    def test_csv_do_banco(self):
        arq = self.tmp / "extrato.csv"
        arq.write_text("Data;Histórico;Crédito;Débito\n02/11/2026;PIX RECEBIDO X;149,00;\n03/11/2026;GOOGLE ADS;;1.200,00\n", encoding="cp1252")
        itens, _ = fin.ler_csv_extrato(arq)
        self.assertEqual([i["valor"] for i in itens], [149.0, -1200.0])
        self.assertEqual(itens[1]["data"], "2026-11-03")

    def test_cobranca_3_7_14(self):
        self.cliente("Imobiliária Sol", dia=12)
        fin.cmd_faturar(NS(mes="2026-11"))  # venceu 12/11: 8 dias de atraso em 20/11
        atr = fin.atrasadas()
        self.assertEqual(atr[0]["dias"], 8)
        self.assertEqual(fin.etapa_devida(8, ""), 7)
        fin.cmd_cobrar(NS())
        texto = (fin.PASTA / "cobrancas" / "2026-11-20.md").read_text(encoding="utf-8")
        self.assertIn("wa.me/5549999990000", texto)
        self.assertIn("R$ 149,00", texto)
        fin.cmd_enviado(NS(tipo="cobranca", id="1", etapa=None))
        self.assertIsNone(fin.etapa_devida(8, fin.ler(fin.FATURAS, fin.C_FATURA)[0]["cobrancas"]))
        self.assertEqual(fin.etapa_devida(15, "7"), 14)

    def test_posvenda_nps_e_avaliacao(self):
        self.cliente("Clínica Sorriso", inicio="2026-10-15")  # D+36
        c = fin.ler(fin.CLIENTES, fin.C_CLIENTE)[0]
        self.assertEqual(fin.posvenda_devida(c), 30)
        fin.cmd_enviado(NS(tipo="posvenda", id="1", etapa=None))
        fin.cmd_nps(NS(id="1", nota=10))
        fin.cmd_config(NS(saldo=None, data=None, alerta=None, link_avaliacao="https://g.page/r/ciello/review", assinatura=None))
        fin.cmd_posvenda(NS())
        texto = (fin.PASTA / "posvenda" / "2026-11-20.md").read_text(encoding="utf-8")
        self.assertIn("pedido de avaliação", texto)
        self.assertIn("g.page/r/ciello/review", texto)

    def test_situacao_e_metricas(self):
        self.cliente("A", valor=200, inicio="2026-09-01")
        self.cliente("B", valor=100, inicio="2026-10-05")
        self.cliente("C", valor=100, inicio="2026-11-03")
        fin.cmd_cancelar(NS(id="2", data="2026-11-10", motivo="sem uso"))
        fin.cmd_config(NS(saldo=1000.0, data="2026-10-01", alerta=500.0, link_avaliacao=None, assinatura=None))
        for d, v, desc in [("2026-10-10", -900, "GOOGLE ADS"), ("2026-10-12", 300, "PIX"), ("2026-11-04", -200, "FACEBK ADS")]:
            fin.cmd_lancar(NS(valor=v, descricao=desc, categoria=None, data=d))
        s = fin.situacao()
        self.assertEqual(s["mrr"], 300.0)
        self.assertEqual(s["clientes_ativos"], 2)
        self.assertEqual(s["caixa"], 200.0)
        self.assertTrue(any("caixa previsto" in x for x in s["alertas"]))
        m = fin.metricas_mes("2026-11", fin.ler(fin.CLIENTES, fin.C_CLIENTE), fin.ler(fin.LANCAMENTOS, fin.C_LANC))
        self.assertEqual((m["novos"], m["cancelados"], m["ativos"]), (1, 1, 2))
        self.assertAlmostEqual(m["churn"], 0.5)  # 1 de 2 ativos no início do mês
        self.assertEqual(m["cac"], 200.0)
        fin.cmd_resumo(NS(mes="2026-11", meses=3))
        self.assertIn("MRR R$ 300,00", (fin.PASTA / "relatorios" / "2026-11.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()


class TesteProdutos(TesteFinanceiro):
    """Produtos reais: CRM com teste grátis, site à vista ou parcelado, hospedagem."""

    def setUp(self):
        super().setUp()
        cat = self.tmp / "produtos.json"
        cat.write_text('{"produtos": [{"id": "crm", "tipo": "assinatura", "mensal": 397, "teste_dias": 30},'
                       '{"id": "site", "tipo": "projeto", "avista": 1500, "parcelas": 12, "parcela": 137.9},'
                       '{"id": "hospedagem", "tipo": "assinatura", "mensal": 90}]}', encoding="utf-8")
        p = mock.patch.object(fin, "PRODUTOS", cat)
        p.start()
        self.addCleanup(p.stop)

    def novo(self, **k):
        base = dict(empresa="Imob Sol", lead=None, contato="Ana", whatsapp="49999990000", plano="", valor=None, dia=10,
                    inicio="2026-11-01", produto="crm", teste=30)
        fin.cmd_cliente(NS(**{**base, **k}))

    def test_teste_gratis_nao_fatura_e_avisa_o_fim(self):
        self.novo()
        c = fin.ler(fin.CLIENTES, fin.C_CLIENTE)[0]
        self.assertEqual((c["status"], c["valor_mensal"], c["teste_ate"]), ("teste", "397.00", "2026-12-01"))
        fin.cmd_faturar(NS(mes="2026-12"))
        self.assertEqual(fin.ler(fin.FATURAS, fin.C_FATURA), [])
        with mock.patch.object(fin, "hoje", lambda: dt.date(2026, 11, 28)):
            s = fin.situacao()
        self.assertEqual((s["mrr"], s["mrr_em_teste"], s["testes"][0]["dias"]), (0, 397.0, 3))
        self.assertTrue(any("acaba em 3" in a for a in s["alertas"]))
        self.assertTrue(fin.posvendas_devidos(dt.date(2026, 11, 2)))  # boas-vindas também no teste
        fin.cmd_converter(NS(id="1", data="2026-12-01", valor=None))
        fin.cmd_faturar(NS(mes="2027-01"))
        f = fin.ler(fin.FATURAS, fin.C_FATURA)
        self.assertEqual((len(f), f[0]["valor"], f[0]["descricao"]), (1, "397.00", "Mensalidade"))
        with self.assertRaises(SystemExit):
            fin.cmd_converter(NS(id="1", data=None, valor=None))

    def test_venda_de_site_parcelado_com_hospedagem(self):
        fin.cmd_venda(NS(cliente=None, empresa="Padaria Pão", lead=None, contato="Rui", whatsapp="49988887777", forma="parcelado",
                         valor=None, parcelas=None, primeira="2026-11-25", dia=10, hospedagem=None, sem_hospedagem=False, inicio_hospedagem="2026-12-01"))
        f = fin.ler(fin.FATURAS, fin.C_FATURA)
        self.assertEqual(len(f), 12)
        self.assertEqual((f[0]["vencimento"], f[11]["vencimento"], f[0]["valor"], f[3]["descricao"]), ("2026-11-25", "2027-10-25", "137.90", "Site parcela 4/12"))
        c = fin.ler(fin.CLIENTES, fin.C_CLIENTE)[0]
        self.assertEqual((c["plano"], c["valor_mensal"], c["status"]), ("hospedagem", "90.00", "ativo"))
        fin.cmd_faturar(NS(mes="2026-12"))  # hospedagem fatura; parcelas não duplicam
        f = fin.ler(fin.FATURAS, fin.C_FATURA)
        self.assertEqual([x["descricao"] for x in f[12:]], ["Hospedagem"])
        s = fin.situacao(dt.date(2026, 11, 20))
        self.assertAlmostEqual(s["sites_a_receber"][30], 137.9)
        self.assertAlmostEqual(s["sites_a_receber"][90], 137.9 * 3)
        atr = fin.atrasadas(dt.date(2026, 12, 2))
        msg = fin.msg_cobranca(atr[0], 7, "Ana")
        self.assertIn("A parcela 1/12 do seu site", msg)
        self.assertIn("da hospedagem do seu site", fin.msg_cobranca({**f[12], "cliente": c}, 3, "Ana"))
        self.assertIn("pausar o site", fin.msg_cobranca(atr[0], 14, "Ana"))
        # pagamento da parcela no extrato vira receita de sites
        lanc = {"id": "1", "data": "2026-11-26", "descricao": "PIX PADARIA PAO", "valor": "137.90"}
        fin.conciliar(lanc, f, [c])
        self.assertEqual(lanc["categoria"], fin.RECEITA_SITES)

    def test_site_a_vista_sem_hospedagem(self):
        fin.cmd_venda(NS(cliente=None, empresa="Loja X", lead=None, contato="", whatsapp="", forma="avista", valor=None, parcelas=None,
                         primeira=None, dia=10, hospedagem=None, sem_hospedagem=True, inicio_hospedagem=None))
        f = fin.ler(fin.FATURAS, fin.C_FATURA)
        self.assertEqual((len(f), f[0]["valor"], f[0]["descricao"]), (1, "1500.00", "Site à vista"))
        self.assertEqual(fin.ler(fin.CLIENTES, fin.C_CLIENTE)[0]["status"], "projeto")
        self.assertEqual(fin.situacao()["clientes_ativos"], 0)

    def test_fim_do_teste_e_oportunidades_na_carteira(self):
        self.novo(empresa="Ótica Visão", inicio="2026-10-25")  # teste até 24/11: faltam 4 dias
        self.novo(empresa="Imob Sol", teste=0, inicio="2026-09-01")
        fin.cmd_venda(NS(cliente=None, empresa="Padaria", lead=None, contato="Rui", whatsapp="49988887777", forma="avista", valor=None,
                         parcelas=None, primeira=None, dia=10, hospedagem=None, sem_hospedagem=False, inicio_hospedagem=None))
        t = fin.testes_acabando()
        self.assertEqual([(x["empresa"], x["dias"]) for x in t], [("Ótica Visão", 4)])
        self.assertIn("vai até 24/11", t[0]["mensagem"])
        self.assertIn("R$ 397,00/mês", t[0]["mensagem"])
        ops = {o["empresa"]: o["oferta"] for o in fin.oportunidades()}
        self.assertEqual(ops, {"Imob Sol": "site", "Padaria": "crm"})  # quem está no teste não recebe oferta
