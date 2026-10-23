"""O que todo conector tem em comum: HTTP sem dependências e o formato dos dados.

Formato que o coletar() devolve (tudo opcional):
  {"perfil": [{"rede", "dia", "seguidores", "alcance", "engajadas"}],
   "publicacoes": [{"rede", "id_ext", "data", "tipo", "texto", "url", "views", "alcance", "curtidas", "comentarios",
                    "compartilhamentos", "salvamentos", "tempo_medio_s"}],
   "comentarios": [{"rede", "id_ext", "publicacao", "autor", "texto", "data"}]}
"""
import json
import urllib.error
import urllib.parse
import urllib.request


class ErroConexao(Exception):
    """A conexão caiu, o token venceu ou o provedor recusou. A mensagem vai para a janela Conexões."""


class NaoSuportado(Exception):
    """Este provedor não faz isso (ex.: o TikTok não lista comentários pela API comum)."""


def _transporte(req: urllib.request.Request, timeout: int):
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, dict(r.headers), r.read()


transporte = _transporte  # os testes trocam por um falso


def http(metodo: str, url: str, params: dict | None = None, headers: dict | None = None, json_corpo=None,
         form: dict | None = None, dados: bytes | None = None, timeout: int = 60, bruto: bool = False):
    """Faz a chamada e devolve o JSON (ou (status, headers, bytes) com bruto=True). Erro vira ErroConexao com o motivo."""
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    h = dict(headers or {})
    corpo = dados
    if json_corpo is not None:
        corpo = json.dumps(json_corpo).encode()
        h.setdefault("Content-Type", "application/json")
    elif form is not None:
        corpo = urllib.parse.urlencode(form).encode()
        h.setdefault("Content-Type", "application/x-www-form-urlencoded")
    req = urllib.request.Request(url, data=corpo, headers=h, method=metodo)
    try:
        status, cab, resp = transporte(req, timeout)
    except urllib.error.HTTPError as e:
        detalhe = e.read()[:400].decode("utf-8", "replace")
        raise ErroConexao(f"{e.code} {_motivo(e.code)}: {detalhe}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ErroConexao(f"sem resposta ({getattr(e, 'reason', e)}). Internet ou provedor fora do ar?") from None
    if bruto:
        return status, cab, resp
    if not resp:
        return {}
    try:
        return json.loads(resp)
    except ValueError:
        return {"texto": resp.decode("utf-8", "replace")}


def _motivo(code: int) -> str:
    return {400: "pedido recusado", 401: "token inválido ou vencido", 403: "sem permissão (plano ou escopo)",
            404: "não encontrado", 429: "limite de uso do provedor", 500: "erro no provedor", 503: "provedor fora do ar"}.get(code, "erro")


def numero(*valores):
    """O primeiro valor numérico (as APIs mudam o nome dos campos: views, plays, videoViews…)."""
    for v in valores:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                continue
    return None


class Provedor:
    ID = ""
    NOME = ""
    REDES: tuple[str, ...] = ()       # redes que ele cobre
    CAMPOS: list[dict] = []           # credenciais pedidas na janela Conexões
    AJUDA = ""                        # como conseguir as credenciais (texto curto)
    OAUTH = False                     # tem botão "Entrar com…"
    PUBLICA: tuple[str, ...] = ()     # redes em que ele publica
    AGENDA = False                    # o provedor guarda o agendamento (o PC pode estar desligado na hora)
    LIMITE = ""                       # aviso de limite (privado até auditoria, posts por mês…)

    def testar(self, cred: dict) -> dict:
        raise NotImplementedError

    def coletar(self, cred: dict, desde: str) -> dict:
        raise NaoSuportado

    def publicar(self, cred: dict, envio: dict) -> dict:
        raise NaoSuportado

    def responder(self, cred: dict, comentario: dict, texto: str) -> dict:
        raise NaoSuportado

    def resumo(self) -> dict:
        return {"id": self.ID, "nome": self.NOME, "redes": list(self.REDES), "campos": self.CAMPOS, "ajuda": self.AJUDA,
                "oauth": self.OAUTH, "publica": list(self.PUBLICA), "agenda": self.AGENDA, "limite": self.LIMITE}
