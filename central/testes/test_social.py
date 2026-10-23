"""python -m unittest discover central/testes  (conexões, banco local da rede social, resultados e comentários)"""
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

os.environ["CIELLO_COMERCIAL"] = str(Path(__file__).resolve().parents[2] / "exemplo" / "comercial")  # a empresa fictícia
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cofre  # noqa: E402
import conexoes  # noqa: E402
import dados  # noqa: E402
import ganchos  # noqa: E402
import social  # noqa: E402
from provedores import PROVEDORES, base  # noqa: E402
from provedores.base import ErroConexao  # noqa: E402


class Falso:
    """Transporte HTTP falso: responde pelo pedaço do endereço e guarda o que foi pedido."""

    def __init__(self, rotas):
        self.rotas, self.pedidos = rotas, []

    def __call__(self, req, timeout):
        self.pedidos.append(req)
        for trecho, resp in self.rotas.items():
            if trecho in req.full_url:
                if isinstance(resp, Exception):
                    raise resp
                if callable(resp):
                    resp = resp(req)
                if isinstance(resp, tuple):
                    return resp
                return 200, {}, json.dumps(resp).encode()
        raise urllib.error.HTTPError(req.full_url, 404, "nada", {}, io.BytesIO(b"{}"))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        p = mock.patch.dict(os.environ, {"CIELLO_DADOS": str(self.tmp)})
        p.start()
        self.addCleanup(p.stop)
        self.con = dados.banco()
        self.addCleanup(self.con.close)

    def transporte(self, rotas):
        f = Falso(rotas)
        p = mock.patch.object(base, "transporte", f)
        p.start()
        self.addCleanup(p.stop)
        return f


class TesteBase(Base):
    def test_banco_e_cofre(self):
        self.assertEqual(self.con.execute("PRAGMA user_version").fetchone()[0], max(dados.MIGRACOES))
        self.assertTrue(str(dados.estado("x")).startswith(str(self.tmp)))
        cofre.guardar("provedor:x", {"token": "segredo123"})
        self.assertNotIn("segredo123", dados.estado("cofre.json").read_text())
        self.assertEqual(cofre.ler("provedor:x"), {"token": "segredo123"})
        cofre.apagar("provedor:x")
        self.assertEqual(cofre.ler("provedor:x"), {})


class TesteConexoes(Base):
    def test_conectar_cair_e_desconectar_sem_perder_historico(self):
        rotas = {"simpleProfiles": [{"id": 1234567, "label": "Lumi", "instagram": "lumi.exemplo"}],
                 "analytics/reels/instagram": {"data": [{"reelId": "r1", "publishedAt": "2026-10-01T10:00", "content": "Gancho A", "views": 120,
                                                         "reach": 90, "saved": 2, "averageWatchTime": 6500}]},
                 "inbox/post-comments": {"data": [{"id": "c1", "postId": "r1", "from": {"name": "ana"}, "message": "Quanto custa o CRM?"}]}}
        self.transporte(rotas)
        r = conexoes.salvar_credenciais("metricool", {"token": "tok-abc", "user_id": "1", "blog_id": "1234567"})
        self.assertTrue(r["ok"], r)
        self.assertEqual(conexoes.estados()["metricool"]["conta"], "Lumi")
        self.assertEqual(conexoes.credenciais("metricool")["fuso"], "America/Sao_Paulo")
        self.assertTrue(conexoes.configurar_rede("instagram", via="metricool")["ok"])
        sync = social.sincronizar(["metricool"], self.con)
        self.assertEqual(sync[0]["novos"], 2)  # 1 reel + 1 comentário
        pub = self.con.execute("SELECT * FROM publicacoes").fetchone()
        self.assertEqual((pub["views"], pub["tempo_medio_s"], pub["fonte"]), (120, 6.5, "metricool"))
        # o provedor cai: a checagem registra, nada é apagado, e a próxima sincronização não zera os números
        self.transporte({"simpleProfiles": urllib.error.HTTPError("x", 401, "x", {}, io.BytesIO(b"token expired")),
                         "analytics": urllib.error.URLError("sem rede")})
        self.assertFalse(conexoes.checar("metricool")["ok"])
        self.assertEqual(conexoes.caidas()[0]["id"], "metricool")
        self.assertIn("401 token inválido", conexoes.estados()["metricool"]["mensagem"])
        self.assertFalse(social.sincronizar(["metricool"], self.con)[0]["ok"])
        self.assertEqual(self.con.execute("SELECT views FROM publicacoes").fetchone()[0], 120)
        # desconectar apaga só a senha
        conexoes.desconectar("metricool")
        self.assertEqual(conexoes.credenciais("metricool"), {})
        self.assertEqual(conexoes.redes()["instagram"]["via"], "")
        h = social.historico_por_provedor(self.con)["metricool"]
        self.assertEqual((h["publicacoes"], h["comentarios"]), (1, 1))

    def test_rede_so_publica_por_quem_publica_nela(self):
        self.assertFalse(conexoes.configurar_rede("tiktok", via="instagram")["ok"])
        self.assertTrue(conexoes.configurar_rede("tiktok", ativa=True, via="tiktok")["ok"])
        self.assertEqual(conexoes.redes()["tiktok"], {"ativa": True, "via": "tiktok"})

    def test_oauth_youtube(self):
        conexoes.salvar_credenciais("youtube", {"client_id": "cid", "client_secret": "sec"})
        ini = conexoes.oauth_inicio("youtube", "http://127.0.0.1:3200")
        self.assertIn("redirect_uri=http%3A%2F%2F127.0.0.1%3A3200%2Foauth%2Fyoutube", ini["url"])
        estado = ini["url"].split("state=")[1].split("&")[0]
        self.transporte({"oauth2.googleapis.com/token": lambda req: {"refresh_token": "rt", "access_token": "at"},
                         "youtube/v3/channels": {"items": [{"id": "UC1", "snippet": {"title": "Lumi"}, "statistics": {"subscriberCount": "12"},
                                                            "contentDetails": {"relatedPlaylists": {"uploads": "UU1"}}}]}})
        self.assertFalse(conexoes.oauth_retorno("youtube", "cod", "estado-falso")["ok"])
        r = conexoes.oauth_retorno("youtube", "cod", estado)
        self.assertTrue(r["ok"], r)
        self.assertEqual(conexoes.credenciais("youtube")["refresh_token"], "rt")


class TesteProvedores(Base):
    def test_instagram_coleta_e_publica_pelo_pc(self):
        video = self.tmp / "v.mp4"
        video.write_bytes(b"0" * 1000)
        f = self.transporte({
            "rupload.facebook.com": {"success": True},
            "/media_publish": {"id": "m9"},
            "/17841/media": lambda req: {"id": "cont1"} if req.method == "POST" else {"data": [
                {"id": "m1", "caption": "Gancho X", "media_product_type": "REELS", "timestamp": "2026-10-20T13:00:00+0000",
                 "permalink": "https://ig/p/1", "like_count": 4, "comments_count": 1}]},
            "m1/insights": {"data": [{"name": "views", "values": [{"value": 300}]}, {"name": "ig_reels_avg_watch_time", "values": [{"value": 5200}]}]},
            "m1/comments": {"data": [{"id": "k1", "text": "Top demais 🔥", "username": "rui", "timestamp": "2026-10-20T14:00:00+0000"}]},
            "cont1": {"status_code": "FINISHED"}, "m9": {"permalink": "https://ig/p/9"},
            "/17841": {"username": "lumi.exemplo", "followers_count": 63},
        })
        ig = PROVEDORES["instagram"]
        cred = {"token": "t", "ig_id": "17841"}
        self.assertEqual(ig.testar(cred)["conta"], "@lumi.exemplo")
        pac = ig.coletar(cred, "2026-10-01")
        self.assertEqual((pac["publicacoes"][0]["views"], pac["publicacoes"][0]["tempo_medio_s"]), (300, 5.2))
        self.assertEqual(social.categoria(pac["comentarios"][0]["texto"]), "elogio")
        r = ig.publicar(cred, {"arquivo": str(video), "texto": "legenda", "rede": "instagram", "quando": "2026-10-27T10:00"})
        self.assertEqual(r, {"estado": "publicado", "id_ext": "m9", "url": "https://ig/p/9"})
        upload = next(q for q in f.pedidos if "rupload" in q.full_url)
        self.assertEqual((upload.get_header("File_size"), len(upload.data)), ("1000", 1000))  # o vídeo sobe do PC, sem link público

    def test_tiktok_publica_privado_sem_auditoria(self):
        video = self.tmp / "v.mp4"
        video.write_bytes(b"0" * 500)
        f = self.transporte({"oauth/token": {"access_token": "a", "refresh_token": "rt2"},
                             "creator_info": {"data": {"privacy_level_options": ["SELF_ONLY"]}},
                             "video/init": {"data": {"upload_url": "https://up.tiktok/x", "publish_id": "p1"}},
                             "up.tiktok": (201, {}, b"")})
        cred = {"client_key": "k", "client_secret": "s", "refresh_token": "rt1"}
        r = PROVEDORES["tiktok"].publicar(cred, {"arquivo": str(video), "texto": "oi", "rede": "tiktok", "quando": "2026-10-27T18:00"})
        self.assertEqual((r["id_ext"], "privado" in r["aviso"]), ("p1", True))
        init = json.loads(next(q for q in f.pedidos if "video/init" in q.full_url).data)
        self.assertEqual(init["post_info"]["privacy_level"], "SELF_ONLY")
        self.assertEqual((cred["refresh_token"], cred["_mudou"]), ("rt2", True))  # o novo refresh token é guardado

    def test_youtube_agenda_no_proprio_youtube(self):
        video = self.tmp / "v.mp4"
        video.write_bytes(b"0" * 10)
        f = self.transporte({"oauth2.googleapis.com/token": {"access_token": "a"},
                             "upload/youtube": lambda req: (200, {"Location": "https://up.yt/s1"}, b"{}") if req.method == "POST" else (200, {}, b""),
                             "up.yt/s1": {"id": "vid1"}})
        quando = (dt.datetime.now() + dt.timedelta(days=2)).strftime("%Y-%m-%dT10:00")
        r = PROVEDORES["youtube"].publicar({"client_id": "c", "client_secret": "s", "refresh_token": "r"},
                                           {"arquivo": str(video), "titulo": "T" * 150, "texto": "d", "rede": "youtube", "quando": quando})
        self.assertEqual((r["estado"], r["id_ext"]), ("agendado", "vid1"))
        meta = json.loads(next(q for q in f.pedidos if "uploadType=resumable" in q.full_url).data)
        self.assertEqual((meta["status"]["privacyStatus"], len(meta["snippet"]["title"])), ("private", 100))
        self.assertTrue(meta["status"]["publishAt"].endswith("Z"))


class TesteResultadosEComentarios(Base):
    def test_guardar_nao_apaga_e_avaliar_alimenta_ganchos(self):
        csv_ganchos = self.tmp / "ganchos.csv"
        p = mock.patch.object(ganchos, "CSV", csv_ganchos)
        p.start()
        self.addCleanup(p.stop)
        (self.tmp / "roteiros").mkdir()
        (self.tmp / "roteiros" / "2026-10-10-crm.json").write_text(json.dumps({"scenes": [{"type": "hook", "lines": [["Seu WhatsApp"], ["perde venda"]]}]}))
        pubs = [{"rede": "instagram", "id_ext": f"p{i}", "data": f"2026-09-{10 + i:02d}T10:00", "texto": f"post {i}", "views": 100} for i in range(5)]
        pubs.append({"rede": "instagram", "id_ext": "novo", "data": "2026-10-10T10:00", "texto": "legenda", "views": 260, "salvamentos": 3})
        social.guardar(self.con, {"publicacoes": pubs}, "instagram")
        social.guardar(self.con, {"publicacoes": [{"rede": "instagram", "id_ext": "novo", "data": "2026-10-10T10:00", "views": None, "texto": ""}]}, "instagram")
        self.assertEqual(self.con.execute("SELECT views, texto FROM publicacoes WHERE id_ext='novo'").fetchone()[:], (260, "legenda"))
        r = {x["id_ext"]: x for x in social.avaliar(self.con, dt.date(2026, 10, 20))}
        self.assertEqual((r["novo"]["multiplicador"], r["novo"]["veredito"], r["novo"]["gancho"]), (2.6, "acima", "Seu WhatsApp perde venda"))
        nossos = [l for l in ganchos.ler() if l["nosso"] == "sim"]
        self.assertIn(("Seu WhatsApp perde venda", "2.60"), [(l["gancho"], l["multiplicador"]) for l in nossos])
        self.assertEqual(len(nossos), 3)  # p3 e p4 também já têm 3 anteriores para comparar
        self.assertEqual(social.avaliar(self.con, dt.date(2026, 10, 21)), [])  # não avalia duas vezes

    def test_caixa_de_comentarios(self):
        self.assertEqual(social.categoria("Quanto custa pra minha loja?"), "lead")
        self.assertEqual(social.categoria("Funciona no iPhone?"), "pergunta")
        self.assertEqual(social.categoria("Muito bom!! 👏"), "elogio")
        self.assertEqual(social.categoria("Ganhe 1000 seguidores grátis www.x.com"), "spam")
        social.guardar(self.con, {"comentarios": [{"rede": "tiktok", "id_ext": "t1", "autor": "lia", "texto": "tenho interesse, me chama"},
                                                   {"rede": "tiktok", "id_ext": "t2", "autor": "rui", "texto": "show"}]}, "tiktok")
        cx = social.caixa(self.con)
        self.assertEqual([c["categoria"] for c in cx], ["lead", "elogio"])
        self.assertIn("@lia", cx[0]["sugestao"])
        self.transporte({"oauth/token": {"access_token": "a"}})
        r = social.responder("tiktok", "t2", "Valeu!", self.con)
        self.assertTrue(r["ok"])
        self.assertIn("responda pelo app", r["saida"])
        self.assertEqual(self.con.execute("SELECT estado FROM comentarios WHERE id_ext='t2'").fetchone()[0], "responder_no_app")

    def test_ponte_claude_importa_retratos(self):
        (self.tmp / "metricas").mkdir()
        (self.tmp / "metricas" / "2026-10-19.json").write_text(json.dumps({"data": "2026-10-19", "perfil": {"seguidores": 63},
                                                                            "reels": [{"data": "2026-10-14", "gancho": "Se a sua equipe", "views": 98}]}))
        social.guardar(self.con, PROVEDORES["claude"].coletar({}, "2026-01-01"), "claude")
        self.assertEqual(self.con.execute("SELECT seguidores FROM perfil").fetchone()[0], 63)
        self.assertEqual(self.con.execute("SELECT dia FROM metricas_dia").fetchone()[0], "2026-10-19")
        exp = social.exportar(self.tmp / "exp", self.con)
        self.assertIn("Se a sua equipe", (exp / "publicacoes.csv").read_text(encoding="utf-8-sig"))


if __name__ == "__main__":
    unittest.main()
