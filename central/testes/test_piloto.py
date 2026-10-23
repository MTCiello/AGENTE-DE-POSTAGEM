"""python -m unittest discover central/testes  (piloto automático e calendário do mês)"""
import datetime as dt
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import calendario  # noqa: E402
import conexoes  # noqa: E402
import conteudo  # noqa: E402
import dados  # noqa: E402
import ganchos  # noqa: E402
import ia  # noqa: E402
import piloto  # noqa: E402
import sdr  # noqa: E402
import social  # noqa: E402
import status  # noqa: E402
from provedores import base  # noqa: E402
from testes.test_social import Falso  # noqa: E402

AMANHA = dt.date(2026, 11, 3)  # uma terça-feira; o post é de quarta, 04/11
POST = "2026-11-04-crm-whatsapp"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "roteiros").mkdir()
        (self.tmp / "midia" / "final").mkdir(parents=True)
        (self.tmp / "comercial").mkdir()
        (self.tmp / "historico.md").write_text("| Data | Tema | Viral | Vídeo | Status |\n|---|---|---|---|---|\n", encoding="utf-8")
        (self.tmp / "roteiros" / f"{POST}.json").write_text(json.dumps({"pilar": "negocio", "legenda": "Seu WhatsApp perde venda\n\n#ciello",
                                                                         "scenes": [{"type": "hook", "say": "Seu WhatsApp perde venda"}]}), encoding="utf-8")
        (self.tmp / "midia" / "final" / f"{POST}.mp4").write_bytes(b"0" * 100)
        for p in (mock.patch.dict(os.environ, {"CIELLO_DADOS": str(self.tmp)}),
                  mock.patch.multiple(conteudo, RAIZ=self.tmp, ROTEIROS=self.tmp / "roteiros", HISTORICO=self.tmp / "historico.md"),
                  mock.patch.object(status, "EVENTOS", self.tmp / "eventos.jsonl"), mock.patch.object(ganchos, "CSV", self.tmp / "ganchos.csv"),
                  mock.patch.multiple(sdr, LEADS=self.tmp / "comercial" / "leads.csv", PASTA=self.tmp / "comercial",
                                      BLOQUEIO=self.tmp / "comercial" / "nao-contatar.txt"),
                  mock.patch.object(piloto, "executar", lambda cmd, cwd, timeout=3600: (True, "ok")),
                  mock.patch.object(piloto.ia, "rodar", self.ia_falsa)):
            p.start()
            self.addCleanup(p.stop)
        self.pedidos_ia = []
        self.con = dados.banco()
        self.addCleanup(self.con.close)
        calendario.configurar({"dias": "2"})  # só quarta, para o teste ficar curto
        self.http = Falso({
            "/17841/media_publish": {"id": "m9"},
            "/17841/media": lambda req: {"id": "cont1"} if req.method == "POST" else {"data": []},
            "rupload": {"ok": True}, "cont1": {"status_code": "FINISHED"}, "m9": {"permalink": "https://ig/p/9"},
            "/replies": {"id": "r1"},
            "/17841": {"username": "ciellotec", "followers_count": 70},
            "oauth2.googleapis.com/token": {"access_token": "a"},
            "youtube/v3/channels": {"items": [{"id": "UC", "snippet": {"title": "Ciello"}, "statistics": {"subscriberCount": "5"},
                                               "contentDetails": {"relatedPlaylists": {"uploads": "UU"}}}]},
            "youtube/v3/playlistItems": {"items": []}, "youtube/v3/commentThreads": {"items": []},
            "upload/youtube": lambda req: (200, {"Location": "https://up.yt/s"}, b"{}") if req.method == "POST" else (200, {}, b""),
            "up.yt/s": {"id": "yt1"},
        })
        p = mock.patch.object(base, "transporte", self.http)
        p.start()
        self.addCleanup(p.stop)
        conexoes.salvar_credenciais("instagram", {"token": "t", "ig_id": "17841"})
        import cofre
        cofre.guardar("provedor:youtube", {"client_id": "c", "client_secret": "s", "refresh_token": "r"})
        conexoes.configurar_rede("instagram", ativa=True, via="instagram")
        conexoes.configurar_rede("youtube", ativa=True, via="youtube")

    def ia_falsa(self, pedido, titulo="", timeout=0):
        self.pedidos_ia.append(pedido)
        return {"ok": True, "saida": "ok"}

    def envios(self):
        return {r["rede"]: dict(r) for r in self.con.execute("SELECT * FROM envios")}


class TestePiloto(Base):
    def test_fila_hora_e_publicacao(self):
        piloto.rodar(dt.datetime.combine(AMANHA, dt.time(9)), self.con)
        e = self.envios()
        self.assertEqual((e["instagram"]["estado"], e["youtube"]["estado"]), ("na_fila", "na_fila"))
        # o YouTube agenda no próprio YouTube 12h antes; o Instagram direto sai na hora do post
        piloto.rodar(dt.datetime(2026, 11, 4, 0, 30), self.con)
        e = self.envios()
        self.assertEqual((e["instagram"]["estado"], e["youtube"]["estado"]), ("na_fila", "agendado"))
        piloto.rodar(dt.datetime(2026, 11, 4, 10, 5), self.con)
        e = self.envios()
        self.assertEqual((e["instagram"]["estado"], e["instagram"]["url"]), ("publicado", "https://ig/p/9"))
        self.assertIn("Publicado", (self.tmp / "historico.md").read_text(encoding="utf-8"))
        n = len(self.http.pedidos)
        piloto.rodar(dt.datetime(2026, 11, 4, 11, 0), self.con)
        self.assertFalse(any("media_publish" in q.full_url for q in self.http.pedidos[n:]))  # não publica duas vezes

    def test_segurar_e_modo_aprovar(self):
        piloto.rodar(dt.datetime.combine(AMANHA, dt.time(9)), self.con)
        self.assertTrue(piloto.segurar(POST, "instagram", self.con)["ok"])
        piloto.configurar({"modo": "aprovar"})
        piloto.rodar(dt.datetime(2026, 11, 4, 10, 5), self.con)
        e = self.envios()
        self.assertEqual((e["instagram"]["estado"], e["youtube"]["estado"]), ("segurado", "na_fila"))
        self.con.execute("DELETE FROM envios WHERE rede='youtube'")
        self.con.commit()
        piloto.rodar(dt.datetime(2026, 11, 4, 10, 6), self.con)
        self.assertEqual(self.envios()["youtube"]["estado"], "aguardando_aprovacao")
        piloto.aprovar(POST, "youtube", self.con)
        piloto.rodar(dt.datetime(2026, 11, 4, 10, 7), self.con)
        self.assertEqual(self.envios()["youtube"]["estado"], "agendado")  # 12h no YouTube: fica agendado lá

    def test_nao_duplica_o_que_ja_foi_agendado(self):
        conteudo.marcar_agendado(POST, "04/11 10h", "Agendado")
        piloto.rodar(dt.datetime(2026, 11, 4, 10, 5), self.con)
        e = self.envios()["instagram"]
        self.assertEqual((e["estado"], e["via"]), ("agendado", "historico"))
        self.assertFalse(any("media_publish" in q.full_url for q in self.http.pedidos))

    def test_conexao_caida_guarda_na_fila(self):
        self.http.rotas["/17841"] = urllib.error.HTTPError("x", 401, "x", {}, io.BytesIO(b"expired"))
        piloto.rodar(dt.datetime(2026, 11, 4, 10, 5), self.con)
        e = self.envios()["instagram"]
        self.assertEqual(e["estado"], "na_fila")
        self.assertIn("fora do ar", e["erro"])
        self.assertTrue(any(d["evento"] == "conexao" and not d["ok"] for d in piloto.diario()))

    def test_pausado_nao_produz_nem_publica(self):
        piloto.configurar({"modo": "pausado"})
        r = piloto.rodar(dt.datetime(2026, 11, 4, 10, 5), self.con)
        self.assertNotIn("publicacao", r)
        self.assertEqual(self.envios(), {})

    def test_pede_roteiros_dos_dias_vazios(self):
        piloto.configurar({"antecedencia_dias": 10})
        piloto.rodar(dt.datetime.combine(AMANHA, dt.time(9)), self.con, produzir_videos=False)
        self.assertEqual(len(self.pedidos_ia), 1)
        self.assertIn("2026-11-11", self.pedidos_ia[0])  # a próxima quarta, sem roteiro
        self.assertNotIn(f"- {POST[:10]}", self.pedidos_ia[0])  # a de 04/11 já tem
        piloto.rodar(dt.datetime.combine(AMANHA, dt.time(10)), self.con, produzir_videos=False)
        self.assertEqual(len(self.pedidos_ia), 1)  # uma hora depois não pede de novo

    def test_comentarios_lead_e_elogio(self):
        social.guardar(self.con, {"comentarios": [{"rede": "instagram", "id_ext": "c1", "autor": "lojadalia", "texto": "Quanto custa? Tenho interesse"},
                                                   {"rede": "instagram", "id_ext": "c2", "autor": "rui", "texto": "Top demais 🔥"}]}, "instagram")
        piloto.rodar(dt.datetime.combine(AMANHA, dt.time(9)), self.con, produzir_videos=False)
        estados = dict(self.con.execute("SELECT id_ext, estado FROM comentarios").fetchall())
        self.assertEqual(estados, {"c1": "lead", "c2": "respondido"})
        self.assertIn("@lojadalia", (self.tmp / "comercial" / "leads.csv").read_text(encoding="utf-8"))
        self.assertTrue(any("/c2/replies" in q.full_url for q in self.http.pedidos))


class TesteCalendario(Base):
    def test_mes_e_previsao(self):
        calendario.configurar({"dias": "0,2,4"})
        for i in range(4):
            social.guardar(self.con, {"publicacoes": [{"rede": "instagram", "id_ext": f"p{i}", "data": f"2026-10-0{i + 1}T10:00", "views": 100 + i * 10}],
                                      "perfil": [{"rede": "instagram", "dia": f"2026-10-0{i + 1}", "seguidores": 60 + i}]}, "instagram")
        r = calendario.mes(2026, 11, AMANHA, self.con)
        dia4 = next(d for d in r["dias"] if d["data"] == "2026-11-04")
        self.assertEqual((dia4["post"]["pilar"], dia4["redes"]["instagram"]["hora"], dia4["redes"]["youtube"]["hora"]), ("negocio", "10:00", "12:00"))
        vazio = next(d for d in r["dias"] if d["data"] == "2026-11-06")
        self.assertIn(vazio["sugestao"], calendario.PILARES)
        self.assertNotEqual(vazio["sugestao"], "negocio")  # o pilar já usado fica por último
        prev = r["previsao"]["redes"]["instagram"]
        self.assertEqual((prev["posts_planejados"], prev["mediana_views"], prev["views_previstas"]), (12, 115.0, 1380))  # 02/11 já passou sem post: não conta
        self.assertGreater(prev["seguidores_fim_mes"], 63)
        self.assertTrue(any("YouTube" in a for a in r["previsao"]["avisos"]))  # sem histórico ainda
        self.assertFalse(calendario.configurar({"hora_tiktok": "25:00"})["ok"])

    def test_limite_do_metricool(self):
        conexoes.configurar_rede("instagram", via="claude")
        conexoes.configurar_rede("youtube", via="claude")
        calendario.configurar({"dias": "0,1,2,3,4", "limite_metricool": "20"})
        r = calendario.mes(2026, 11, AMANHA, self.con)
        self.assertEqual(r["previsao"]["posts_metricool"], 40)  # 20 dias úteis restantes × 2 redes
        self.assertTrue(any("permite 20" in a for a in r["previsao"]["avisos"]))


if __name__ == "__main__":
    unittest.main()
