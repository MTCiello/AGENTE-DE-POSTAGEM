"""python -m unittest discover central/testes"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ganchos  # noqa: E402


class TesteGanchos(unittest.TestCase):
    def test_formatos(self):
        casos = {
            "Salva esse vídeo antes que apaguem": "salve",
            "Pare de usar o ChatGPT só pra escrever texto": "alerta",
            "5 comandos do ChatGPT que vendem por você": "lista",
            "Testei o Claude no meu negócio por 7 dias": "prova",
            "Se a sua equipe vende pelo WhatsApp…": "cenario",
            "Imagina um vendedor que não dorme": "cenario",
            "Você sabia que o Gemini faz isso?": "pergunta",
            "Saiu o novo modelo grátis do ChatGPT": "novidade",
            "Seu negócio é invisível no Google": "outro",
        }
        for gancho, esperado in casos.items():
            self.assertEqual(ganchos.formato_de(gancho), esperado, gancho)

    def test_multiplicador(self):
        l = ganchos.completar({"gancho": "5 prompts grátis", "views": "90000", "mediana_perfil": "30000"})
        self.assertEqual(l["multiplicador"], "3.00")
        self.assertEqual(l["pilar"], "comandos")

    def test_importar_metricool(self):
        import json, tempfile
        from types import SimpleNamespace as NS
        tmp = Path(tempfile.mkdtemp())
        original = ganchos.CSV
        ganchos.CSV = tmp / "ganchos.csv"
        try:
            reels = [{"perfil": "iacomjota", "texto": f"Dica {i}", "url": f"https://ig/{i}", "data": "2026-10-10", "interacoes": v}
                     for i, v in enumerate([100, 120, 110, 900])]
            (tmp / "c.json").write_text(json.dumps(reels), encoding="utf-8")
            ganchos.cmd_importar_metricool(NS(arquivo=str(tmp / "c.json"), minimo=1.5))
            linhas = ganchos.ler()
            self.assertEqual(len(linhas), 1)  # só o reel de 900 passa de 1,5x a mediana (115)
            self.assertEqual(linhas[0]["perfil"], "@iacomjota")
            self.assertAlmostEqual(float(linhas[0]["multiplicador"]), 900 / 115, places=1)
        finally:
            ganchos.CSV = original


if __name__ == "__main__":
    unittest.main()
