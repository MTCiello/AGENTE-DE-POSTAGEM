"""python -m unittest discover central/testes  (plano do ano: projeção, equilíbrio e auditoria)"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import financeiro as fin  # noqa: E402
import plano  # noqa: E402


class TestePlano(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        cat = self.tmp / "produtos.json"
        cat.write_text(json.dumps({"produtos": [{"id": "crm", "mensal": 397, "teste_dias": 30},
                                                {"id": "site", "avista": 1500, "parcelas": 12, "parcela": 137.9}, {"id": "hospedagem", "mensal": 90}]}), encoding="utf-8")
        for p in (mock.patch.object(fin, "PASTA", self.tmp), mock.patch.object(fin, "PRODUTOS", cat),
                  mock.patch.multiple(fin, CLIENTES=self.tmp / "clientes.csv", FATURAS=self.tmp / "faturas.csv")):
            p.start()
            self.addCleanup(p.stop)

    def base(self, **k):
        return {**plano.PADRAO, "ano": 2027, "negocios": [], "custos": [], **k}

    def test_receita_por_tipo_de_negocio(self):
        mensal = {"valor": 397, "tipo": "mensal", "inicio": "2027-03"}
        self.assertEqual([plano.receita_do_negocio(mensal, m) for m in ("2027-02", "2027-03", "2027-12")], [0, 397, 397])
        self.assertAlmostEqual(plano.receita_do_negocio(mensal, "2027-05", churn=0.1), 397 * 0.81)
        parc = {"valor": 150, "tipo": "parcelas", "parcelas": 10, "inicio": "2027-01"}
        self.assertEqual(sum(plano.receita_do_negocio(parc, m) for m in plano.meses(2027)), 1500)
        self.assertEqual(plano.receita_do_negocio({"valor": 900, "tipo": "unico", "inicio": "2027-06"}, "2027-07"), 0)
        self.assertEqual(plano.receita_do_negocio({"valor": 100, "inicio": "2027-01", "fim": "2027-06"}, "2027-07"), 0)
        self.assertEqual(plano.custo_no_mes({"valor": 738.8, "frequencia": "anual", "mes": "2027-03"}, "2027-03"), 738.8)
        self.assertEqual(plano.custo_no_mes({"valor": 738.8, "frequencia": "anual", "mes": "2027-03"}, "2027-04"), 0)

    def test_projecao_pondera_a_chance_e_cobra_imposto(self):
        p = self.base(regime="simples3", negocios=[{"cliente": "A", "produto": "crm", "valor": 1000, "inicio": "2027-01", "status": "fechado"},
                                                   {"cliente": "B", "produto": "crm", "valor": 1000, "inicio": "2027-01", "status": "talvez"}],
                      custos=[{"item": "Claude", "valor": 100, "frequencia": "mensal", "categoria": "ferramentas"}])
        jan = plano.projetar(p)[0]
        self.assertEqual((jan["receita_certa"], jan["receita_provavel"], jan["receita_se_tudo_fechar"]), (1000, 1250, 2000))
        self.assertEqual((jan["imposto"], jan["resultado"]), (75.0, 1075.0))

    def test_auditoria_acha_os_furos_de_um_plano_real(self):
        # parecido com a planilha: receita só em jan-fev, sem imposto, sem servidor, sem status, sem churn
        neg = [{"cliente": f"C{i}", "produto": "crm", "tipo": "mensal", "valor": 397, "inicio": "2027-01", "fim": "2027-02"} for i in range(7)]
        p = self.base(pro_labore=3274, negocios=neg, custos=[{"item": "Claude", "valor": 121.44, "frequencia": "mensal", "categoria": "ferramentas"}])
        titulos = " | ".join(a["titulo"] for a in plano.auditar(p))
        for esperado in ("mês(es) sem nenhuma receita", "Imposto fora do plano", "sem status", "Custo de entrega", "Nenhum cancelamento", "te paga em"):
            self.assertIn(esperado.lower(), titulos.lower())
        self.assertEqual(plano.auditar(p)[0]["nivel"], "alto")
        self.assertTrue(all(a["titulo"].count("%") == 0 or int(a["titulo"].split("%")[0].split()[-1]) <= 100 for a in plano.auditar(p)))

    def test_teto_do_mei_e_equilibrio(self):
        neg = [{"cliente": f"C{i}", "produto": "crm", "valor": 397, "inicio": "2027-01", "status": "fechado"} for i in range(20)]
        p = self.base(regime="mei", negocios=neg, pro_labore=3000, custos=[{"item": "Servidor", "valor": 1200, "frequencia": "anual", "mes": "2027-03", "categoria": "servidor"}])
        self.assertIn("teto", plano.auditar(p)[0]["titulo"].lower())
        eq = plano.equilibrio(p)
        self.assertEqual(eq["custos_fixos_mes"], 100.0)
        self.assertEqual(eq["clientes_para_te_pagar"], 9)  # (100 + 86 + 3000) / 397 = 8,02: arredonda para cima

    def test_edicao_pela_janela(self):
        self.assertTrue(plano.salvar_item("negocios", {"cliente": "Loja", "produto": "site", "tipo": "parcelas", "valor": "150", "parcelas": "10", "inicio": "2027-02", "status": "negociando"})["ok"])
        self.assertTrue(plano.salvar_item("custos", {"item": "Servidor", "valor": "738,80", "frequencia": "anual", "mes": "2027-03", "categoria": "servidor"})["ok"])
        self.assertFalse(plano.salvar_item("negocios", {"cliente": "", "valor": "1"})["ok"])
        self.assertFalse(plano.salvar_item("negocios", {"cliente": "X", "valor": "1", "inicio": "março"})["ok"])
        self.assertTrue(plano.salvar_item("negocios", {"i": 0, "cliente": "Loja Nova", "valor": "200", "status": "fechado"})["ok"])
        self.assertTrue(plano.configurar({"regime": "simples5", "pro_labore": "3.274", "churn_mensal": "3"})["ok"])
        p = plano.ler()
        self.assertEqual((p["negocios"][0]["cliente"], p["custos"][0]["valor"], p["pro_labore"], p["churn_mensal"]), ("Loja Nova", 738.8, 3274.0, 0.03))
        self.assertTrue(plano.remover_item("custos", 0)["ok"])
        self.assertFalse(plano.remover_item("custos", 5)["ok"])
        self.assertFalse(plano.configurar({"regime": "isento"})["ok"])
        janela = plano.para_janela()
        self.assertEqual(len(janela["projecao"]), 12)
        self.assertTrue(janela["precos"])

    def test_ideias_de_preco(self):
        txt = " ".join(x["detalhe"] for x in plano.precos())
        self.assertIn("1,5% ao mês", txt)
        self.assertIn("R$ 1.654,80", txt)
