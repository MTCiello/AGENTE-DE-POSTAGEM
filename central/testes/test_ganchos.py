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


if __name__ == "__main__":
    unittest.main()
