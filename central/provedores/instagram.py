"""Instagram direto pela API da Meta (Instagram Graph API), sem intermediário.

Precisa de uma conta profissional do Instagram ligada a um app da Meta (Facebook Login for Business) e de um
token de longa duração. Como o app é seu e a conta é sua, não precisa de revisão da Meta para postar no seu
perfil. O vídeo sobe direto do PC (upload "resumable"), sem precisar de link público.
"""
import time
from pathlib import Path

from .base import ErroConexao, Provedor, http, numero

VERSAO = "v21.0"
GRAPH = f"https://graph.facebook.com/{VERSAO}"
RUPLOAD = f"https://rupload.facebook.com/ig-api-upload/{VERSAO}"


class Instagram(Provedor):
    ID = "instagram"
    NOME = "Instagram (API da Meta)"
    REDES = ("instagram",)
    PUBLICA = ("instagram",)
    CAMPOS = [{"nome": "token", "rotulo": "Token de acesso (longa duração)", "segredo": True,
               "ajuda": "developers.facebook.com → seu app → Instagram → gerar token"},
              {"nome": "ig_id", "rotulo": "ID da conta do Instagram", "ajuda": "aparece junto do token (Instagram Business Account ID)"}]
    AJUDA = "Conta profissional + app da Meta seu. O token de longa duração vale 60 dias: o OS avisa antes de vencer."
    LIMITE = "Até 50 publicações por dia pela API. Precisa do PC ligado na hora do post (a Meta não agenda pela API)."

    def _get(self, cred, caminho, **params):
        return http("GET", f"{GRAPH}/{caminho}", params={**params, "access_token": cred.get("token")})

    def testar(self, cred):
        if not cred.get("token") or not cred.get("ig_id"):
            raise ErroConexao("preencha o token e o ID da conta")
        r = self._get(cred, cred["ig_id"], fields="username,followers_count,media_count")
        return {"conta": "@" + str(r.get("username", "")), "seguidores": r.get("followers_count")}

    def coletar(self, cred, desde):
        out = {"perfil": [], "publicacoes": [], "comentarios": []}
        conta = self._get(cred, cred["ig_id"], fields="followers_count")
        out["perfil"].append({"rede": "instagram", "dia": time.strftime("%Y-%m-%d"), "seguidores": numero(conta.get("followers_count"))})
        midias = self._get(cred, f"{cred['ig_id']}/media", fields="id,caption,media_product_type,timestamp,permalink,like_count,comments_count",
                           limit=50).get("data", [])
        for i, m in enumerate(midias):
            data = str(m.get("timestamp", ""))[:16]
            if data[:10] < desde:
                continue
            p = {"rede": "instagram", "id_ext": m["id"], "data": data, "tipo": str(m.get("media_product_type", "")).lower(),
                 "texto": m.get("caption", ""), "url": m.get("permalink", ""), "curtidas": numero(m.get("like_count")),
                 "comentarios": numero(m.get("comments_count"))}
            try:
                metricas = "views,reach,saved,shares,ig_reels_avg_watch_time" if p["tipo"] == "reels" else "views,reach,saved,shares"
                for x in self._get(cred, f"{m['id']}/insights", metric=metricas).get("data", []):
                    v = numero(*(x.get("values") or [{}])[0].values()) if x.get("values") else numero(x.get("total_value", {}).get("value"))
                    chave = {"views": "views", "reach": "alcance", "saved": "salvamentos", "shares": "compartilhamentos",
                             "ig_reels_avg_watch_time": "tempo_medio_s"}.get(x.get("name"))
                    if chave:
                        p[chave] = v / 1000 if chave == "tempo_medio_s" and v else v
            except ErroConexao:
                pass  # post antigo ou tipo sem insights
            out["publicacoes"].append(p)
            if i < 10 and m.get("comments_count"):
                for c in self._get(cred, f"{m['id']}/comments", fields="id,text,username,timestamp").get("data", []):
                    out["comentarios"].append({"rede": "instagram", "id_ext": c["id"], "publicacao": m["id"], "autor": c.get("username", ""),
                                               "texto": c.get("text", ""), "data": str(c.get("timestamp", ""))[:16]})
        return out

    def publicar(self, cred, envio):
        arquivo = Path(envio["arquivo"])
        c = http("POST", f"{GRAPH}/{cred['ig_id']}/media", form={"media_type": "REELS", "upload_type": "resumable", "caption": envio.get("texto", ""),
                                                               "share_to_feed": "true", "access_token": cred["token"]})
        container = c.get("id")
        if not container:
            raise ErroConexao(f"a Meta não criou o container do reel: {c}")
        dados = arquivo.read_bytes()
        http("POST", f"{RUPLOAD}/{container}", headers={"Authorization": f"OAuth {cred['token']}", "offset": "0", "file_size": str(len(dados))},
             dados=dados, timeout=900)
        for _ in range(60):  # a Meta processa o vídeo antes de deixar publicar
            st = self._get(cred, container, fields="status_code").get("status_code")
            if st == "FINISHED":
                break
            if st == "ERROR":
                raise ErroConexao("a Meta recusou o vídeo (formato, duração ou tamanho)")
            time.sleep(self.ESPERA)
        pub = http("POST", f"{GRAPH}/{cred['ig_id']}/media_publish", form={"creation_id": container, "access_token": cred["token"]})
        link = self._get(cred, pub["id"], fields="permalink").get("permalink", "") if pub.get("id") else ""
        return {"estado": "publicado", "id_ext": pub.get("id", ""), "url": link}

    ESPERA = 10

    def responder(self, cred, comentario, texto):
        http("POST", f"{GRAPH}/{comentario['id_ext']}/replies", form={"message": texto, "access_token": cred["token"]})
        return {"ok": True}
