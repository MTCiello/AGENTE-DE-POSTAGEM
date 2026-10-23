"""python -m unittest discover central/testes  (atendimento pelo FAQ)"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ["CIELLO_COMERCIAL"] = str(Path(__file__).resolve().parents[2] / "exemplo" / "comercial")  # a empresa fictícia
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import atendimento  # noqa: E402

FAQ = """# FAQ

## Planos e pagamento
- **Quanto custa o CRM?** R$ 397/mês, 30 dias grátis.
- **Tem fidelidade?** ⟨sim/não⟩. Cancela quando quiser.
- **Atrasei o pagamento, e agora?** Me chama que eu reenvio o Pix.

## Uso
- **Funciona no celular?** ⟨resposta⟩.
"""


class TesteAtendimento(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "faq.md").write_text(FAQ, encoding="utf-8")
        p = mock.patch.object(atendimento, "FAQ", self.tmp / "faq.md")
        p.start()
        self.addCleanup(p.stop)

    def test_acha_a_resposta_com_as_palavras_do_cliente(self):
        self.assertEqual(atendimento.buscar("quanto fica o sistema por mês?")[0]["pergunta"], "Quanto custa o CRM?")
        self.assertEqual(atendimento.buscar("esqueci de pagar o boleto")[0]["pergunta"], "Atrasei o pagamento, e agora?")
        self.assertEqual(atendimento.buscar("posso cancelar quando quiser?")[0]["pergunta"], "Tem fidelidade?")
        r = atendimento.buscar("funciona no iphone?")[0]
        self.assertEqual((r["pergunta"], r["completa"]), ("Funciona no celular?", False))
        self.assertEqual(atendimento.buscar("oi, tudo bem?"), [])

    def test_completar_e_acrescentar_no_faq(self):
        faltam = [x for x in atendimento.ler() if not x["completa"]]
        self.assertEqual([x["pergunta"] for x in faltam], ["Tem fidelidade?", "Funciona no celular?"])
        self.assertTrue(atendimento.salvar("Funciona no celular?", "Sim, no navegador do celular.", faltam[1]["i"])["ok"])
        self.assertTrue(atendimento.salvar("Tem nota fiscal?", "Sim, todo mês.", None, "Planos e pagamento")["ok"])
        self.assertTrue(atendimento.salvar("Tem treinamento?", "Sim, no 1º dia.")["ok"])
        texto = (self.tmp / "faq.md").read_text(encoding="utf-8")
        self.assertIn("- **Funciona no celular?** Sim, no navegador do celular.", texto)
        self.assertLess(texto.index("Tem nota fiscal?"), texto.index("## Uso"))  # entrou na seção certa
        self.assertIn("## Perguntas novas\n- **Tem treinamento?** Sim, no 1º dia.", texto)
        self.assertEqual(len([x for x in atendimento.ler() if not x["completa"]]), 1)
        self.assertFalse(atendimento.salvar("", "x")["ok"])
