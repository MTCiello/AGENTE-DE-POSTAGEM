"""YouTube (Shorts) pela YouTube Data API v3, com login do Google (OAuth) feito no próprio Ciello OS.

Precisa de um projeto no Google Cloud com a YouTube Data API ligada e uma credencial OAuth do tipo
"App para computador" (client id e client secret). O login volta para o próprio OS (127.0.0.1).
Atenção: projeto que ainda não passou pela auditoria do Google publica como PRIVADO; depois da auditoria, público.
"""
import datetime as dt
import urllib.parse
from pathlib import Path

from .base import ErroConexao, Provedor, http, numero

API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos"
TOKEN = "https://oauth2.googleapis.com/token"
ESCOPOS = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.force-ssl"


class YouTube(Provedor):
    ID = "youtube"
    NOME = "YouTube (API do Google)"
    REDES = ("youtube",)
    PUBLICA = ("youtube",)
    AGENDA = True
    OAUTH = True
    CAMPOS = [{"nome": "client_id", "rotulo": "Client ID", "ajuda": "Google Cloud → APIs e serviços → Credenciais → ID do cliente OAuth (App para computador)"},
              {"nome": "client_secret", "rotulo": "Client secret", "segredo": True}]
    AJUDA = "Crie a credencial OAuth do tipo 'App para computador', salve aqui e clique em Entrar com o Google."
    LIMITE = "Projeto sem auditoria do Google publica como privado. Cota diária da API: uns 6 vídeos por dia."

    def url_autorizacao(self, cred, retorno, estado):
        return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
            "client_id": cred.get("client_id"), "redirect_uri": retorno, "response_type": "code", "scope": ESCOPOS,
            "access_type": "offline", "prompt": "consent", "state": estado})

    def trocar_codigo(self, cred, codigo, retorno):
        r = http("POST", TOKEN, form={"code": codigo, "client_id": cred.get("client_id"), "client_secret": cred.get("client_secret"),
                                       "redirect_uri": retorno, "grant_type": "authorization_code"})
        if not r.get("refresh_token"):
            raise ErroConexao("o Google não devolveu o refresh_token (tente de novo: ele só vem no 1º consentimento)")
        return {"refresh_token": r["refresh_token"]}

    def _acesso(self, cred):
        if not cred.get("refresh_token"):
            raise ErroConexao("falta entrar com o Google")
        r = http("POST", TOKEN, form={"client_id": cred.get("client_id"), "client_secret": cred.get("client_secret"),
                                       "refresh_token": cred["refresh_token"], "grant_type": "refresh_token"})
        return {"Authorization": f"Bearer {r['access_token']}"}

    def _canal(self, cred, h):
        itens = http("GET", f"{API}/channels", params={"part": "snippet,statistics,contentDetails", "mine": "true"}, headers=h).get("items", [])
        if not itens:
            raise ErroConexao("esta conta do Google não tem canal no YouTube")
        return itens[0]

    def testar(self, cred):
        c = self._canal(cred, self._acesso(cred))
        return {"conta": c["snippet"]["title"], "seguidores": numero(c["statistics"].get("subscriberCount"))}

    def coletar(self, cred, desde):
        h = self._acesso(cred)
        c = self._canal(cred, h)
        out = {"perfil": [{"rede": "youtube", "dia": dt.date.today().isoformat(), "seguidores": numero(c["statistics"].get("subscriberCount"))}],
               "publicacoes": [], "comentarios": []}
        uploads = c["contentDetails"]["relatedPlaylists"]["uploads"]
        ids = [i["contentDetails"]["videoId"] for i in http("GET", f"{API}/playlistItems", params={"part": "contentDetails", "playlistId": uploads,
                                                                                                    "maxResults": 50}, headers=h).get("items", [])]
        if ids:
            for v in http("GET", f"{API}/videos", params={"part": "snippet,statistics", "id": ",".join(ids)}, headers=h).get("items", []):
                data = v["snippet"]["publishedAt"][:16]
                if data[:10] < desde:
                    continue
                s = v.get("statistics", {})
                out["publicacoes"].append({"rede": "youtube", "id_ext": v["id"], "data": data, "tipo": "short", "texto": v["snippet"]["title"],
                                           "url": f"https://youtube.com/shorts/{v['id']}", "views": numero(s.get("viewCount")),
                                           "curtidas": numero(s.get("likeCount")), "comentarios": numero(s.get("commentCount"))})
        for t in http("GET", f"{API}/commentThreads", params={"part": "snippet", "allThreadsRelatedToChannelId": c["id"], "maxResults": 50},
                      headers=h).get("items", []):
            s = t["snippet"]["topLevelComment"]["snippet"]
            out["comentarios"].append({"rede": "youtube", "id_ext": t["snippet"]["topLevelComment"]["id"], "publicacao": t["snippet"].get("videoId", ""),
                                       "autor": s.get("authorDisplayName", ""), "texto": s.get("textOriginal", ""), "data": s.get("publishedAt", "")[:16]})
        return out

    def publicar(self, cred, envio):
        h = self._acesso(cred)
        quando = dt.datetime.fromisoformat(envio["quando"][:16])
        agora = dt.datetime.fromisoformat(envio["agora"]) if envio.get("agora") else dt.datetime.now()
        agendar = quando > agora + dt.timedelta(minutes=15)
        meta = {"snippet": {"title": envio.get("titulo", "")[:100], "description": envio.get("texto", "")[:4900], "categoryId": "28"},
                "status": {"privacyStatus": "private" if agendar else "public", "selfDeclaredMadeForKids": False}}
        if agendar:  # o YouTube publica sozinho na hora: o PC pode estar desligado
            meta["status"]["publishAt"] = quando.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        dados = Path(envio["arquivo"]).read_bytes()
        _, cab, _ = http("POST", UPLOAD, params={"uploadType": "resumable", "part": "snippet,status"},
                         headers={**h, "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(dados))}, json_corpo=meta, bruto=True)
        destino = cab.get("Location") or cab.get("location")
        if not destino:
            raise ErroConexao("o YouTube não abriu o envio do vídeo")
        v = http("PUT", destino, headers={**h, "Content-Type": "video/mp4"}, dados=dados, timeout=900)
        return {"estado": "agendado" if agendar else "publicado", "id_ext": v.get("id", ""), "url": f"https://youtube.com/shorts/{v.get('id', '')}"}

    def responder(self, cred, comentario, texto):
        http("POST", f"{API}/comments", params={"part": "snippet"}, headers=self._acesso(cred),
             json_corpo={"snippet": {"parentId": comentario["id_ext"], "textOriginal": texto}})
        return {"ok": True}
