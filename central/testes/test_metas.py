"""python -m unittest discover central/testes  (meta de crescimento e decisões do negócio)"""
import datetime as dt
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import decisoes  # noqa: E402
import financeiro as fin  # noqa: E402
import metas  # noqa: E402
import plano  # noqa: E402
import sdr  # noqa: E402

SEG = dt.date(2026, 11, 2)  # uma segunda-feira


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        cat = self.tmp / "produtos.json"
        cat.write_text(json.dumps({"produtos": [{"id": "crm", "mensal": 397, "teste_dias": 30},
                                                {"id": "site", "avista": 1500, "parcelas": 12, "parcela": 137.9}, {"id": "hospedagem", "mensal": 90}]}), encoding="utf-8")
        for p in (mock.patch.object(fin, "PASTA", self.tmp), mock.patch.object(fin, "PRODUTOS", cat),
                  mock.patch.multiple(fin, CLIENTES=self.tmp / "clientes.csv", FATURAS=self.tmp / "faturas.csv"),
                  mock.patch.object(sdr, "LEADS", self.tmp / "leads.csv")):
            p.start()
            self.addCleanup(p.stop)

    def clientes(self, *linhas):
        base = {"valor_mensal": "397.00", "dia_vencimento": "10", "plano": "crm", "status": "ativo", "inicio": "2026-09-01"}
        fin.gravar(fin.CLIENTES, fin.C_CLIENTE, [{**base, "id": str(i + 1), "empresa": f"C{i + 1}", **l} for i, l in enumerate(linhas)])

    def leads(self, *etapas, **extra):
        sdr.gravar_leads([{"id": str(i + 1), "empresa": f"L{i + 1}", "etapa": e, "origem": "Google Maps", **extra} for i, e in enumerate(etapas)])


class TesteMeta(Base):
    def test_sem_meta_sugere_o_equilibrio(self):
        plano.gravar({**plano.PADRAO, "pro_labore": 3000, "custos": [{"item": "Servidor", "valor": 200, "frequencia": "mensal"}], "negocios": []})
        r = metas.calcular(ref=SEG)
        self.assertFalse(r["tem_meta"])
        self.assertEqual(r["sugestao"], 9)  # (3000 + 200) / 397 → 9 clientes
        self.assertIn("Sugestão: 9 clientes", metas.resumo(r))

    def test_funil_de_tras_para_frente(self):
        self.clientes({}, {}, {"status": "teste", "teste_ate": "2026-11-20"}, {"plano": "hospedagem", "valor_mensal": "90"})
        r = metas.calcular({"clientes": 10, "ate": "2027-05"}, ref=SEG)
        self.assertEqual((r["ativos"], r["em_teste"], r["vindo_do_teste"]), (2, 1, 1))  # hospedagem não conta como CRM
        self.assertEqual((r["meses"], r["meses_uteis"], r["faltam"]), (6, 5, 7))  # o teste de 30 dias come 1 mês
        self.assertEqual(r["por_semana"], {"clientes": 0.3, "testes": 1, "demos": 2, "respostas": 3, "abordagens": 18})
        self.assertEqual(r["mrr_meta"], 3970)
        self.assertTrue(any("estimativa" in a for a in r["avisos"]))
        self.assertEqual(r["atras"], [])  # segunda de manhã ainda não está atrás

    def test_cancelamentos_e_meta_coberta(self):
        self.clientes(*[{} for _ in range(10)])
        plano.gravar({**plano.PADRAO, "churn_mensal": 0.05})
        r = metas.calcular({"clientes": 10, "ate": "2027-05"}, ref=SEG)
        self.assertEqual((r["perdas"], r["faltam"]), (3, 3))  # 10 × 5% × 6 meses
        r = metas.calcular({"clientes": 5, "ate": "2027-05"}, ref=SEG)
        self.assertEqual(r["faltam"], 0)
        self.assertIn("subir a meta", r["avisos"][0])

    def test_sem_tempo_pelo_funil(self):
        r = metas.calcular({"clientes": 3, "ate": "2026-12"}, ref=SEG)
        self.assertEqual(r["meses_uteis"], 0)
        self.assertIn("Não dá tempo pelo funil", r["avisos"][0])

    def test_taxas_dos_seus_dados_e_escritas(self):
        self.leads(*(["contatado"] * 15 + ["respondeu"] * 3 + ["proposta"] * 2), ultimo_contato="")
        t = metas.taxas({})
        self.assertEqual((t["resposta"]["origem"], round(t["resposta"]["valor"], 2), t["resposta"]["dados"]), ("seus dados", 0.25, "5 de 20"))
        self.assertEqual(t["demo"]["origem"], "seus dados")  # 2 de 5 respostas chegaram à demo
        self.assertEqual(t["teste"]["origem"], "estimativa")  # ainda nenhum teste grátis registrado
        self.assertEqual(metas.taxas({"taxas": {"teste": 0.8}})["teste"], {"nome": metas.TAXAS["teste"][0], "valor": 0.8, "origem": "sua", "dados": "0 de 2"})

    def test_ritmo_da_semana(self):
        qui = SEG + dt.timedelta(days=3)
        sdr.gravar_leads([{"id": "1", "empresa": "A", "etapa": "contatado", "ultimo_contato": qui.isoformat(), "origem": "Google Maps"},
                          {"id": "2", "empresa": "B", "etapa": "demo", "agenda": f"{qui}T15:00", "ultimo_contato": qui.isoformat(), "origem": "Google Maps"},
                          {"id": "3", "empresa": "C", "etapa": "contatado", "ultimo_contato": (SEG - dt.timedelta(days=1)).isoformat(), "origem": "Google Maps"}])
        r = metas.calcular({"clientes": 20, "ate": "2027-05"}, ref=qui)
        self.assertEqual(r["feito"], {"abordagens": 1, "demos": 1, "testes": 0})
        self.assertTrue(r["atras"] and r["atras"][0].startswith("1 de "))

    def test_configurar(self):
        self.assertTrue(metas.configurar({"clientes": "12", "ate": "2027-6", "taxa_resposta": "20"})["ok"])
        self.assertEqual(metas.ler(), {"clientes": 12, "ate": "2027-06", "taxas": {"resposta": 0.2}})
        self.assertTrue(metas.configurar({"taxa_resposta": ""})["ok"])
        self.assertEqual(metas.ler()["taxas"], {})
        self.assertFalse(metas.configurar({"taxa_demo": "150"})["ok"])
        self.assertFalse(metas.configurar({"ate": "2027-13"})["ok"])
        self.assertFalse(metas.configurar({"clientes": "abc"})["ok"])


class TesteDecisoes(Base):
    def test_sugestoes_decidir_e_regras(self):
        abertas = decisoes.sugestoes()
        titulos = [s["titulo"] for s in abertas]
        self.assertIn("Plano anual do CRM", titulos)
        self.assertNotIn("Plano sem negócios", titulos)  # sem plano montado, não cobra furo do plano
        r = decisoes.salvar({"titulo": "Plano anual do CRM", "decisao": "Oferecer no fim do teste: 12 por 10.", "revisar": "2027-01-15"}, ref=SEG)
        self.assertTrue(r["ok"])
        self.assertNotIn("Plano anual do CRM", [s["titulo"] for s in decisoes.sugestoes()])
        regras = decisoes.regras_arquivo().read_text(encoding="utf-8")
        self.assertIn("- **Plano anual do CRM:** Oferecer no fim do teste: 12 por 10. (decidido em 02/11/2026; rever em 15/01/2027)", regras)
        self.assertEqual(decisoes.para_rever(dt.date(2027, 1, 15))[0]["titulo"], "Plano anual do CRM")
        self.assertEqual(decisoes.para_rever(dt.date(2027, 1, 14)), [])

    def test_chave_ignora_numeros(self):
        self.assertEqual(decisoes.chave("3 negócio(s) sem status"), decisoes.chave("5 negócio(s) sem status"))
        self.assertEqual(decisoes.chave("Parcelado custa 20% a mais"), decisoes.chave("Parcelado custa 10% a mais"))

    def test_adiar_descartar_e_validar(self):
        self.assertFalse(decisoes.salvar({"titulo": "X", "estado": "decidida"})["ok"])  # decidir pede o texto da regra
        self.assertFalse(decisoes.salvar({"titulo": "", "decisao": "y"})["ok"])
        self.assertFalse(decisoes.salvar({"titulo": "X", "decisao": "y", "revisar": "amanhã"})["ok"])
        self.assertTrue(decisoes.salvar({"titulo": "Taxa de implantação", "estado": "adiada"}, ref=SEG)["ok"])
        d = decisoes.ler()[0]
        self.assertEqual((d["estado"], d["revisar"]), ("adiada", "2026-12-02"))  # 30 dias depois
        self.assertIn("(nenhuma decisão registrada ainda)", decisoes.regras_arquivo().read_text(encoding="utf-8"))
        # decidir depois o mesmo assunto atualiza, não duplica
        decisoes.salvar({"titulo": "Taxa de implantação", "decisao": "R$ 300, isenta no plano anual", "estado": "decidida"}, ref=SEG)
        self.assertEqual([(x["estado"], x["revisar"]) for x in decisoes.ler()], [("decidida", "")])
        self.assertTrue(decisoes.remover(decisoes.chave("Taxa de implantação"))["ok"])
        self.assertEqual(decisoes.ler(), [])
        self.assertFalse(decisoes.remover("nada")["ok"])

    def test_furos_do_plano_viram_decisoes(self):
        plano.gravar({**plano.PADRAO, "ano": 2027, "negocios": [{"cliente": "A", "produto": "crm", "valor": 397, "inicio": "2027-01", "status": "fechado"}], "custos": []})
        abertas = {s["titulo"]: s for s in decisoes.sugestoes()}
        self.assertEqual(abertas["Imposto fora do plano"]["origem"], "plano")
        self.assertEqual(abertas["Imposto fora do plano"]["nivel"], "alto")
        self.assertTrue(all(s["nivel"] != "dica" for s in abertas.values() if s["origem"] == "plano"))


if __name__ == "__main__":
    unittest.main()
