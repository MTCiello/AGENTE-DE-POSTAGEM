"""Conexões com os provedores externos: conectar, checar, desconectar, e por onde cada rede publica.

As senhas ficam no cofre (cofre.py); o estado de cada conexão (conta, última checagem, erro) fica em
estado/conexoes.json; e a escolha "o Instagram publica pela Ponte com o Claude, o YouTube pela API do
Google…" fica em estado/redes.json. Desconectar apaga só a senha: o histórico (banco local) continua.
"""
import datetime as dt
import json
import secrets

import cofre
import dados
from provedores import PROVEDORES
from provedores.base import ErroConexao

REDES = {"instagram": "Instagram", "tiktok": "TikTok", "youtube": "YouTube Shorts"}
REDES_PADRAO = {"instagram": {"ativa": True, "via": "claude"}, "tiktok": {"ativa": False, "via": ""}, "youtube": {"ativa": False, "via": ""}}
_oauth: dict[str, tuple[str, str]] = {}  # estado -> (provedor, endereço de retorno), só enquanto o OS está aberto


def agora() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _ler(nome, padrao):
    try:
        return json.loads(dados.estado(nome).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return json.loads(json.dumps(padrao))


def _gravar(nome, valor):
    dados.estado(nome).write_text(json.dumps(valor, ensure_ascii=False, indent=1), encoding="utf-8")


def estados() -> dict:
    return _ler("conexoes.json", {})


def redes() -> dict:
    r = _ler("redes.json", REDES_PADRAO)
    return {k: {**REDES_PADRAO[k], **r.get(k, {})} for k in REDES}


def configurar_rede(rede: str, ativa=None, via=None) -> dict:
    if rede not in REDES:
        return {"ok": False, "saida": "rede desconhecida"}
    r = redes()
    if via is not None:
        if via and (via not in PROVEDORES or rede not in PROVEDORES[via].PUBLICA):
            return {"ok": False, "saida": f"{PROVEDORES.get(via, via)} não publica no {REDES[rede]}"}
        r[rede]["via"] = via
    if ativa is not None:
        r[rede]["ativa"] = bool(ativa)
    _gravar("redes.json", r)
    return {"ok": True, "saida": f"{REDES[rede]}: {'ligado' if r[rede]['ativa'] else 'desligado'}" + (f", publica por {PROVEDORES[r[rede]['via']].NOME}" if r[rede]["via"] else "")}


def credenciais(pid: str) -> dict:
    return cofre.ler(f"provedor:{pid}")


def _guardar_se_mudou(pid, cred):
    if cred.pop("_mudou", False):
        cofre.guardar(f"provedor:{pid}", cred)


def salvar_credenciais(pid: str, valores: dict) -> dict:
    p = PROVEDORES.get(pid)
    if not p:
        return {"ok": False, "saida": "provedor desconhecido"}
    cred = credenciais(pid)
    for c in p.CAMPOS:
        v = str(valores.get(c["nome"]) or "").strip()
        if v:
            cred[c["nome"]] = v
        elif c.get("padrao") and not cred.get(c["nome"]):
            cred[c["nome"]] = c["padrao"]
    cofre.guardar(f"provedor:{pid}", cred)
    return checar(pid) if not p.OAUTH or cred.get("refresh_token") else {"ok": True, "saida": "salvo: agora clique em Entrar"}


def checar(pid: str) -> dict:
    """Testa a conexão agora e grava o resultado. Nunca apaga nada se falhar."""
    p = PROVEDORES[pid]
    cred = credenciais(pid)
    est = estados()
    e = est.get(pid, {})
    try:
        info = p.testar(cred)
        _guardar_se_mudou(pid, cred)
        e.update(conectado=True, ok=True, mensagem="", conta=info.get("conta", ""), ultima_checagem=agora(), falhas=0,
                 desde=e.get("desde") or agora())
        r = {"ok": True, "saida": f"{p.NOME}: conectado ({info.get('conta', '')})"}
    except ErroConexao as ex:
        e.update(ok=False, mensagem=str(ex), ultima_checagem=agora(), falhas=int(e.get("falhas", 0)) + 1,
                 caiu_em=e.get("caiu_em") if not e.get("ok", True) else agora())
        e.setdefault("conectado", bool(cred) or not p.CAMPOS)
        r = {"ok": False, "saida": f"{p.NOME}: {ex}"}
    if e.get("ok"):
        e.pop("caiu_em", None)
    est[pid] = e
    _gravar("conexoes.json", est)
    return r


def desconectar(pid: str) -> dict:
    cofre.apagar(f"provedor:{pid}")
    est = estados()
    est[pid] = {"conectado": False, "desconectado_em": agora()}
    _gravar("conexoes.json", est)
    r = redes()
    for k, v in r.items():
        if v["via"] == pid:
            v["via"] = ""
    _gravar("redes.json", r)
    return {"ok": True, "saida": f"{PROVEDORES[pid].NOME} desconectado. O histórico continua guardado no seu PC."}


def oauth_inicio(pid: str, base: str) -> dict:
    p = PROVEDORES[pid]
    cred = credenciais(pid)
    if not p.OAUTH:
        return {"ok": False, "saida": "este provedor não usa login"}
    if not all(cred.get(c["nome"]) for c in p.CAMPOS):
        return {"ok": False, "saida": "preencha e salve as credenciais do app primeiro"}
    estado = secrets.token_urlsafe(16)
    retorno = f"{base}/oauth/{pid}"
    _oauth[estado] = (pid, retorno)
    return {"ok": True, "url": p.url_autorizacao(cred, retorno, estado), "retorno": retorno}


def oauth_retorno(pid: str, codigo: str, estado: str) -> dict:
    if _oauth.get(estado, (None,))[0] != pid:
        return {"ok": False, "saida": "login expirado ou de outra janela: clique em Entrar de novo"}
    _, retorno = _oauth.pop(estado)
    cred = credenciais(pid)
    try:
        cred.update(PROVEDORES[pid].trocar_codigo(cred, codigo, retorno))
    except ErroConexao as e:
        return {"ok": False, "saida": str(e)}
    cofre.guardar(f"provedor:{pid}", cred)
    return checar(pid)


def via(rede: str):
    """(id, provedor, credenciais) de quem publica nesta rede, ou None."""
    r = redes().get(rede, {})
    pid = r.get("via")
    if not r.get("ativa") or not pid or pid not in PROVEDORES:
        return None
    return pid, PROVEDORES[pid], credenciais(pid)


def caidas() -> list[dict]:
    """Conexões em uso que estão falhando (para o Bom dia e para o piloto não publicar no escuro)."""
    est, out = estados(), []
    usadas = {v["via"] for v in redes().values() if v["ativa"] and v["via"]}
    for pid in usadas:
        e = est.get(pid, {})
        if e and not e.get("ok", True):
            out.append({"id": pid, "nome": PROVEDORES[pid].NOME, "mensagem": e.get("mensagem", ""), "desde": e.get("caiu_em", "")})
    return out


def para_janela(historico: dict | None = None) -> dict:
    est = estados()
    lista = []
    for pid, p in PROVEDORES.items():
        cred = credenciais(pid)
        lista.append({**p.resumo(), "estado": est.get(pid, {}),
                      "preenchidos": {c["nome"]: (("•" * 6 + cred[c["nome"]][-4:]) if c.get("segredo") else cred[c["nome"]])
                                      for c in p.CAMPOS if cred.get(c["nome"])},
                      "logado": bool(cred.get("refresh_token")), "historico": (historico or {}).get(pid, {})})
    return {"provedores": lista, "redes": redes(), "nomes_redes": REDES, "cofre_protegido": cofre.protegido()}
