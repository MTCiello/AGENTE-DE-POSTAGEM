"""TikTok pela API oficial (Login Kit + Display API + Content Posting API).

Precisa de um app em developers.tiktok.com com os produtos Login Kit e Content Posting API. Enquanto o app não
passa pela auditoria do TikTok, os vídeos só saem como privados (SELF_ONLY): o OS avisa e publica assim mesmo,
para você tornar público pelo celular. A API comum não lista comentários.
"""
import datetime as dt
import urllib.parse
from pathlib import Path

from .base import ErroConexao, NaoSuportado, Provedor, http, numero

API = "https://open.tiktokapis.com/v2"
ESCOPOS = "user.info.basic,user.info.stats,video.list,video.publish,video.upload"


class TikTok(Provedor):
    ID = "tiktok"
    NOME = "TikTok (API oficial)"
    REDES = ("tiktok",)
    PUBLICA = ("tiktok",)
    OAUTH = True
    CAMPOS = [{"nome": "client_key", "rotulo": "Client key", "ajuda": "developers.tiktok.com → seu app"},
              {"nome": "client_secret", "rotulo": "Client secret", "segredo": True}]
    AJUDA = "Cadastre no app do TikTok o endereço de retorno que aparece na janela e clique em Entrar com o TikTok."
    LIMITE = "App sem auditoria do TikTok só publica como privado. Precisa do PC ligado na hora do post."

    def url_autorizacao(self, cred, retorno, estado):
        return "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
            "client_key": cred.get("client_key"), "scope": ESCOPOS, "response_type": "code", "redirect_uri": retorno, "state": estado})

    def trocar_codigo(self, cred, codigo, retorno):
        r = http("POST", f"{API}/oauth/token/", form={"client_key": cred.get("client_key"), "client_secret": cred.get("client_secret"),
                                                       "code": codigo, "grant_type": "authorization_code", "redirect_uri": retorno})
        if not r.get("refresh_token"):
            raise ErroConexao(f"o TikTok não devolveu o token: {r.get('error_description') or r}")
        return {"refresh_token": r["refresh_token"], "open_id": r.get("open_id", "")}

    def _acesso(self, cred):
        if not cred.get("refresh_token"):
            raise ErroConexao("falta entrar com o TikTok")
        r = http("POST", f"{API}/oauth/token/", form={"client_key": cred.get("client_key"), "client_secret": cred.get("client_secret"),
                                                       "grant_type": "refresh_token", "refresh_token": cred["refresh_token"]})
        if not r.get("access_token"):
            raise ErroConexao(f"o TikTok recusou o login salvo: {r.get('error_description') or r}")
        if r.get("refresh_token") and r["refresh_token"] != cred["refresh_token"]:
            cred["refresh_token"] = r["refresh_token"]  # o TikTok troca o refresh token: conexoes.py grava o novo
            cred["_mudou"] = True
        return {"Authorization": f"Bearer {r['access_token']}"}

    def testar(self, cred):
        u = http("GET", f"{API}/user/info/", params={"fields": "open_id,display_name,follower_count,video_count"},
                 headers=self._acesso(cred)).get("data", {}).get("user", {})
        return {"conta": u.get("display_name", ""), "seguidores": numero(u.get("follower_count"))}

    def coletar(self, cred, desde):
        h = self._acesso(cred)
        u = http("GET", f"{API}/user/info/", params={"fields": "follower_count"}, headers=h).get("data", {}).get("user", {})
        out = {"perfil": [{"rede": "tiktok", "dia": dt.date.today().isoformat(), "seguidores": numero(u.get("follower_count"))}],
               "publicacoes": [], "comentarios": []}
        campos = "id,title,video_description,create_time,share_url,view_count,like_count,comment_count,share_count"
        for v in http("POST", f"{API}/video/list/", params={"fields": campos}, headers=h, json_corpo={"max_count": 20}).get("data", {}).get("videos", []):
            data = dt.datetime.fromtimestamp(v.get("create_time", 0)).isoformat(timespec="minutes")
            if data[:10] < desde:
                continue
            out["publicacoes"].append({"rede": "tiktok", "id_ext": str(v["id"]), "data": data, "tipo": "video",
                                       "texto": v.get("title") or v.get("video_description", ""), "url": v.get("share_url", ""),
                                       "views": numero(v.get("view_count")), "curtidas": numero(v.get("like_count")),
                                       "comentarios": numero(v.get("comment_count")), "compartilhamentos": numero(v.get("share_count"))})
        return out

    def publicar(self, cred, envio):
        h = self._acesso(cred)
        info = http("POST", f"{API}/post/publish/creator_info/query/", headers=h, json_corpo={}).get("data", {})
        opcoes = info.get("privacy_level_options") or ["SELF_ONLY"]
        privacidade = "PUBLIC_TO_EVERYONE" if "PUBLIC_TO_EVERYONE" in opcoes else opcoes[0]
        dados = Path(envio["arquivo"]).read_bytes()
        r = http("POST", f"{API}/post/publish/video/init/", headers=h, json_corpo={
            "post_info": {"title": envio.get("texto", "")[:2200], "privacy_level": privacidade, "disable_comment": False,
                          "disable_duet": False, "disable_stitch": False},
            "source_info": {"source": "FILE_UPLOAD", "video_size": len(dados), "chunk_size": len(dados), "total_chunk_count": 1}}).get("data", {})
        if not r.get("upload_url"):
            raise ErroConexao(f"o TikTok não abriu o envio: {r}")
        http("PUT", r["upload_url"], headers={"Content-Type": "video/mp4", "Content-Range": f"bytes 0-{len(dados) - 1}/{len(dados)}"},
             dados=dados, timeout=900, bruto=True)
        aviso = "" if privacidade == "PUBLIC_TO_EVERYONE" else " (privado: o app ainda não passou pela auditoria do TikTok)"
        return {"estado": "publicado", "id_ext": r.get("publish_id", ""), "url": "", "aviso": aviso.strip()}

    def responder(self, cred, comentario, texto):
        raise NaoSuportado("a API do TikTok não responde comentários: responda pelo app")
