"""Testes do radar sem internet: python -m unittest discover central/testes"""
import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import radar  # noqa: E402

HOJE = dt.date(2026, 10, 19)
DESDE = HOJE - dt.timedelta(days=7)

GITHUB = {"items": [
    {"full_name": "fulano/agente-vendas", "description": "Open-source AI sales agent for WhatsApp", "html_url": "https://github.com/fulano/agente-vendas",
     "created_at": "2026-10-14T10:00:00Z", "stargazers_count": 4200, "language": "Python", "topics": ["llm", "agent"]},
    {"full_name": "beltrano/tts-local", "description": "Free local TTS, ElevenLabs alternative", "html_url": "https://github.com/beltrano/tts-local",
     "created_at": "2026-10-16T10:00:00Z", "stargazers_count": 900, "language": "Python", "topics": []},
]}
HN = {"hits": [
    {"title": "OpenAI launches GPT-6 for business", "url": "https://openai.com/news/gpt-6", "created_at": "2026-10-17T12:00:00Z", "points": 1500, "num_comments": 800, "objectID": "1"},
    {"title": "Show HN: My Rust database", "url": "https://example.com/db", "created_at": "2026-10-17T12:00:00Z", "points": 900, "num_comments": 100, "objectID": "2"},
]}
REDDIT = {"data": {"children": [
    {"data": {"title": "10 ChatGPT prompts that saved my small business hours", "permalink": "/r/ChatGPT/comments/a/", "created_utc": 1760700000, "ups": 12000, "num_comments": 400, "selftext": ""}},
    {"data": {"title": "Weekly thread", "permalink": "/r/ChatGPT/comments/b/", "created_utc": 1760700000, "ups": 5, "stickied": True}},
]}}
NOTICIAS = b"""<?xml version="1.0"?><rss><channel>
<item><title>ChatGPT ganha novo recurso gratuito para empresas - Tecmundo</title><link>https://www.tecmundo.com.br/x</link>
<pubDate>Fri, 17 Oct 2026 10:00:00 GMT</pubDate><description>&lt;b&gt;resumo&lt;/b&gt;</description></item>
</channel></rss>"""
TRENDS = b"""<?xml version="1.0"?><rss xmlns:ht="https://trends.google.com/trending/rss"><channel>
<item><title>gemini 3</title><ht:approx_traffic>200.000+</ht:approx_traffic><link>https://trends.google.com/x</link><pubDate>Sun, 19 Oct 2026 08:00:00 -0700</pubDate></item>
<item><title>flamengo</title><ht:approx_traffic>500.000+</ht:approx_traffic><link>https://trends.google.com/y</link><pubDate>Sun, 19 Oct 2026 08:00:00 -0700</pubDate></item>
</channel></rss>"""


class TesteRadar(unittest.TestCase):
    def setUp(self):
        self.itens = (radar.parse_github(GITHUB) + radar.parse_hn(HN) + radar.parse_reddit(REDDIT, "ChatGPT")
                      + radar.parse_rss(NOTICIAS, "noticias") + radar.parse_rss(TRENDS, "trends"))

    def test_parsers(self):
        self.assertEqual(len(self.itens), 2 + 2 + 1 + 1 + 2)  # o fixado do reddit sai
        trend = [i for i in self.itens if i["fonte"] == "trends"][0]
        self.assertEqual(trend["metrica"], 200000)
        self.assertEqual([i for i in self.itens if i["fonte"] == "noticias"][0]["data"], "2026-10-17")

    def test_filtra_o_que_nao_e_ia(self):
        titulos = [i["titulo"] for i in radar.pontuar(self.itens, DESDE)]
        self.assertNotIn("flamengo", titulos)
        self.assertNotIn("Show HN: My Rust database", titulos)
        self.assertIn("gemini 3", titulos)

    def test_pilares(self):
        r = {i["titulo"][:20]: i["pilar"] for i in radar.pontuar(self.itens, DESDE)}
        self.assertEqual(r["fulano/agente-vendas"], "repos")
        self.assertEqual(r["10 ChatGPT prompts t"], "comandos")
        self.assertEqual(r["OpenAI launches GPT-"], "lancamentos")

    def test_nota_e_ordem(self):
        r = radar.pontuar(self.itens, DESDE)
        self.assertTrue(all(0 < i["nota"] <= 100 for i in r))
        self.assertEqual(r, sorted(r, key=lambda i: -i["nota"]))

    def test_relatorio(self):
        md = radar.relatorio(radar.pontuar(self.itens, DESDE), {"reddit": "HTTPError"}, HOJE, 7)
        self.assertIn("## Top 10 geral", md)
        self.assertIn("Fontes que falharam: reddit", md)


if __name__ == "__main__":
    unittest.main()
