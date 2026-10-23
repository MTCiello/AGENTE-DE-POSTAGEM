"""Metricool pela API oficial (app.metricool.com/api). Precisa do plano Advanced ou Custom: no Free e no Starter
a Metricool não libera a API. Um conector cobre Instagram, TikTok e YouTube, e o agendamento fica guardado lá
(o PC pode estar desligado na hora do post).

Os nomes dos campos das respostas variam entre versões da API: o código aceita os nomes conhecidos e ignora o
resto. Para o plano grátis, use a Ponte com o Claude (provedores/claude.py), que usa o conector do Claude.
"""
import datetime as dt
import mimetypes
from pathlib import Path

from .base import ErroConexao, Provedor, http, numero

API = "https://app.metricool.com/api"
REDE_METRICOOL = {"instagram": "instagram", "tiktok": "tiktok", "youtube": "youtube"}


def _lista(resp):
    if isinstance(resp, list):
        return resp
    if isinstance(resp, dict):
        for k in ("data", "items", "posts", "reels", "results", "comments", "conversations"):
            if isinstance(resp.get(k), list):
                return resp[k]
    return []


def _dia(v) -> str:
    if isinstance(v, dict):
        v = v.get("dateTime") or v.get("date")
    if isinstance(v, (int, float)):
        return dt.datetime.fromtimestamp(v / (1000 if v > 1e11 else 1)).isoformat(timespec="minutes")
    return str(v or "")[:16]


class Metricool(Provedor):
    ID = "metricool"
    NOME = "Metricool (API)"
    REDES = ("instagram", "tiktok", "youtube")
    PUBLICA = REDES
    AGENDA = True
    CAMPOS = [{"nome": "token", "rotulo": "Token da API", "segredo": True, "ajuda": "Metricool → Configurações da conta → API"},
              {"nome": "user_id", "rotulo": "userId", "ajuda": "o número depois de userId= no endereço do Metricool"},
              {"nome": "blog_id", "rotulo": "blogId (marca)", "ajuda": "o número depois de blogId= (ex.: 1234567)"},
              {"nome": "fuso", "rotulo": "Fuso", "padrao": "America/Sao_Paulo"}]
    AJUDA = "Só nos planos Advanced e Custom. No plano grátis, use a Ponte com o Claude."
    LIMITE = "Cada rede conta como um post no limite do seu plano."

    def _get(self, cred, caminho, params=None):
        return http("GET", API + caminho, params={**(params or {}), "userId": cred.get("user_id"), "blogId": cred.get("blog_id"),
                                                    "userToken": cred.get("token")}, headers={"X-Mc-Auth": cred.get("token", "")})

    def _envia(self, cred, metodo, caminho, corpo):
        return http(metodo, API + caminho, params={"userId": cred.get("user_id"), "blogId": cred.get("blog_id"), "userToken": cred.get("token")},
                    headers={"X-Mc-Auth": cred.get("token", "")}, json_corpo=corpo)

    def testar(self, cred):
        if not all(cred.get(k) for k in ("token", "user_id", "blog_id")):
            raise ErroConexao("preencha token, userId e blogId")
        marcas = _lista(self._get(cred, "/admin/simpleProfiles"))
        marca = next((m for m in marcas if str(m.get("id") or m.get("blogId")) == str(cred["blog_id"])), None)
        if marcas and not marca:
            raise ErroConexao(f"a marca {cred['blog_id']} não está nesta conta")
        redes = [r for r in self.REDES if marca and marca.get(r)]
        return {"conta": (marca or {}).get("label") or (marca or {}).get("name") or f"marca {cred['blog_id']}", "redes": redes}

    def coletar(self, cred, desde):
        fim = dt.date.today()
        periodo = {"from": f"{desde}T00:00:00", "to": f"{fim}T23:59:59", "timezone": cred.get("fuso") or "America/Sao_Paulo"}
        out = {"perfil": [], "publicacoes": [], "comentarios": []}
        for rede in self.REDES:
            caminho = "/v2/analytics/reels/instagram" if rede == "instagram" else f"/v2/analytics/posts/{rede}"
            try:
                itens = _lista(self._get(cred, caminho, periodo))
            except ErroConexao as e:
                if "403" in str(e) or "404" in str(e):
                    continue  # rede não conectada na marca
                raise
            for p in itens:
                pid = p.get("reelId") or p.get("postId") or p.get("videoId") or p.get("id") or p.get("mediaId")
                if not pid:
                    continue
                tempo = numero(p.get("averageWatchTime"), p.get("avgWatchTime"), p.get("averageViewDuration"))
                out["publicacoes"].append({
                    "rede": rede, "id_ext": str(pid), "data": _dia(p.get("publishedAt") or p.get("created") or p.get("date") or p.get("publicationDate")),
                    "tipo": str(p.get("type") or ("reel" if rede == "instagram" else "video")).lower(),
                    "texto": p.get("content") or p.get("text") or p.get("caption") or p.get("title") or p.get("description") or "",
                    "url": p.get("url") or p.get("permalink") or p.get("link") or "",
                    "views": numero(p.get("views"), p.get("videoViews"), p.get("plays"), p.get("viewCount")),
                    "alcance": numero(p.get("reach"), p.get("impressionsUnique")),
                    "curtidas": numero(p.get("likes"), p.get("likeCount"), p.get("reactions")),
                    "comentarios": numero(p.get("comments"), p.get("commentCount")),
                    "compartilhamentos": numero(p.get("shares"), p.get("shareCount")),
                    "salvamentos": numero(p.get("saved"), p.get("saves")),
                    "tempo_medio_s": tempo / 1000 if tempo and tempo > 300 else tempo})
            try:
                perfil = self._get(cred, f"/v2/analytics/{rede}/profile", periodo)
                if isinstance(perfil, dict):
                    perfil = perfil.get("data", perfil)
                seg = numero(*(perfil.get(k) for k in ("followers", "followersCount", "subscribers", "fans"))) if isinstance(perfil, dict) else None
                if seg is not None:
                    out["perfil"].append({"rede": rede, "dia": fim.isoformat(), "seguidores": seg,
                                          "alcance": numero(perfil.get("reach")), "engajadas": numero(perfil.get("accountsEngaged"))})
            except ErroConexao:
                pass
            try:
                for c in _lista(self._get(cred, "/v2/inbox/post-comments", {"provider": rede.upper()})):
                    cid = c.get("id") or c.get("commentId")
                    if cid:
                        autor = c.get("from") or c.get("author") or c.get("username") or ""
                        out["comentarios"].append({"rede": rede, "id_ext": str(cid), "publicacao": str(c.get("postId") or ""),
                                                   "autor": autor.get("name", "") if isinstance(autor, dict) else str(autor),
                                                   "texto": c.get("message") or c.get("text") or "", "data": _dia(c.get("created") or c.get("date"))})
            except ErroConexao:
                pass
        return out

    def _subir(self, cred, arquivo: Path) -> str:
        """Sobe o vídeo para o armazenamento da Metricool e devolve a URL que o agendamento usa."""
        tipo = mimetypes.guess_type(arquivo.name)[0] or "video/mp4"
        t = self._envia(cred, "PUT", "/v2/media/s3/upload-transactions", {"filename": arquivo.name, "contentType": tipo})
        t = t.get("data", t) if isinstance(t, dict) else {}
        destino = t.get("presignedUrl") or t.get("uploadUrl") or t.get("signedUrl") or t.get("url")
        if not destino:
            raise ErroConexao("a Metricool não devolveu o endereço de envio do vídeo")
        http("PUT", destino, headers={"Content-Type": tipo}, dados=arquivo.read_bytes(), timeout=600, bruto=True)
        return t.get("fileUrl") or t.get("publicUrl") or t.get("mediaUrl") or destino.split("?")[0]

    def publicar(self, cred, envio):
        url = envio.get("url_publica") or self._subir(cred, Path(envio["arquivo"]))
        rede = envio["rede"]
        corpo = {"text": envio.get("texto", ""), "providers": [{"network": REDE_METRICOOL[rede]}],
                 "publicationDate": {"dateTime": envio["quando"][:16] + ":00", "timezone": cred.get("fuso") or "America/Sao_Paulo"},
                 "draft": False, "autoPublish": True, "media": [url]}
        if rede == "instagram":
            corpo["instagramData"] = {"type": "REEL"}
        elif rede == "youtube":
            corpo["youtubeData"] = {"title": envio.get("titulo", "")[:100], "type": "short", "privacy": "public"}
        elif rede == "tiktok":
            corpo["tiktokData"] = {"privacyOption": "PUBLIC_TO_EVERYONE"}
        r = self._envia(cred, "POST", "/v2/scheduler/posts", corpo)
        r = r.get("data", r) if isinstance(r, dict) else {}
        return {"estado": "agendado", "id_ext": str(r.get("id") or r.get("uuid") or ""), "url": ""}

    def responder(self, cred, comentario, texto):
        self._envia(cred, "POST", "/v2/inbox/post-comments", {"commentId": comentario["id_ext"], "message": texto})
        return {"ok": True}
