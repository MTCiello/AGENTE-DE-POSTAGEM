"""Rede social no banco local: sincronizar com os provedores, o resultado de cada post e a caixa de comentários.

Tudo o que vem de fora é copiado para estado/ciello.db e nunca é apagado por uma sincronização. Se um
provedor cair ou for desconectado, os números, os posts e os comentários continuam aqui.

  python central/social.py sincronizar        # puxa de todos os provedores conectados
  python central/social.py resultados         # como foi cada post depois de 7 dias
  python central/social.py comentarios        # caixa de comentários com a resposta sugerida
"""
import argparse
import csv
import datetime as dt
import json
import re
import statistics
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atendimento  # noqa: E402
import conexoes  # noqa: E402
import dados  # noqa: E402
import ganchos  # noqa: E402
from provedores import PROVEDORES  # noqa: E402
from provedores.base import ErroConexao, NaoSuportado  # noqa: E402

METRICAS = ("views", "alcance", "curtidas", "comentarios", "compartilhamentos", "salvamentos", "tempo_medio_s")
DIAS_RESULTADO = 7


def agora():
    return dt.datetime.now().isoformat(timespec="seconds")


def sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(c) != "Mn")


# ---------------------------------------------------------------- sincronizar

def guardar(con, pacote: dict, fonte: str, ref: dt.date | None = None) -> int:
    """Junta no banco o que um provedor devolveu. Atualiza números, nunca apaga. Devolve quantos itens são novos."""
    hoje = (ref or dt.date.today()).isoformat()
    novos = 0
    for p in pacote.get("perfil", []):
        if p.get("seguidores") is None:
            continue
        con.execute("INSERT INTO perfil (rede, dia, seguidores, alcance, engajadas, fonte) VALUES (?,?,?,?,?,?) "
                    "ON CONFLICT(rede, dia) DO UPDATE SET seguidores=excluded.seguidores, alcance=COALESCE(excluded.alcance, alcance), "
                    "engajadas=COALESCE(excluded.engajadas, engajadas), fonte=excluded.fonte",
                    (p["rede"], p["dia"], p["seguidores"], p.get("alcance"), p.get("engajadas"), fonte))
    for p in pacote.get("publicacoes", []):
        existe = con.execute("SELECT 1 FROM publicacoes WHERE rede=? AND id_ext=?", (p["rede"], p["id_ext"])).fetchone()
        novos += not existe
        valores = [p.get(m) for m in METRICAS]
        con.execute(f"INSERT INTO publicacoes (rede, id_ext, data, tipo, texto, url, {', '.join(METRICAS)}, fonte, atualizado_em) "
                    f"VALUES (?,?,?,?,?,?,{','.join('?' * len(METRICAS))},?,?) ON CONFLICT(rede, id_ext) DO UPDATE SET "
                    "texto=COALESCE(NULLIF(excluded.texto,''), texto), url=COALESCE(NULLIF(excluded.url,''), url), "
                    + ", ".join(f"{m}=COALESCE(excluded.{m}, {m})" for m in METRICAS) + ", fonte=excluded.fonte, atualizado_em=excluded.atualizado_em",
                    (p["rede"], p["id_ext"], p.get("data", ""), p.get("tipo", ""), p.get("texto", ""), p.get("url", ""), *valores, fonte, agora()))
        if any(v is not None for v in valores):
            con.execute(f"INSERT OR REPLACE INTO metricas_dia (rede, id_ext, dia, {', '.join(METRICAS)}) VALUES (?,?,?,{','.join('?' * len(METRICAS))})",
                        (p["rede"], p["id_ext"], p.get("_dia") or hoje, *valores))
    for c in pacote.get("comentarios", []):
        cur = con.execute("INSERT OR IGNORE INTO comentarios (rede, id_ext, publicacao, autor, texto, data, categoria, fonte) VALUES (?,?,?,?,?,?,?,?)",
                          (c["rede"], c["id_ext"], c.get("publicacao", ""), c.get("autor", ""), c.get("texto", ""), c.get("data", ""),
                           categoria(c.get("texto", "")), fonte))
        novos += cur.rowcount
    con.commit()
    return novos


def ultima_sync(con, pid) -> str:
    r = con.execute("SELECT quando FROM sincronizacoes WHERE provedor=? AND ok=1 ORDER BY quando DESC LIMIT 1", (pid,)).fetchone()
    return r[0] if r else ""


def sincronizar(pids: list[str] | None = None, con=None, ref: dt.date | None = None) -> list[dict]:
    """Puxa de cada provedor em uso. Um provedor fora do ar não atrapalha os outros nem apaga nada."""
    con = con or dados.banco()
    em_uso = {v["via"] for v in conexoes.redes().values() if v["ativa"] and v["via"]}
    conectados = {pid for pid, e in conexoes.estados().items() if e.get("conectado")}
    alvo = pids or sorted(em_uso | conectados | {"claude"})
    out = []
    for pid in alvo:
        p = PROVEDORES.get(pid)
        if not p:
            continue
        cred = conexoes.credenciais(pid)
        if p.CAMPOS and not cred:
            continue
        ultima = ultima_sync(con, pid)
        desde = ((dt.date.fromisoformat(ultima[:10]) - dt.timedelta(days=30)) if ultima else (ref or dt.date.today()) - dt.timedelta(days=90)).isoformat()
        try:
            n = guardar(con, p.coletar(cred, desde), pid, ref)
            conexoes._guardar_se_mudou(pid, cred)
            r = {"provedor": pid, "ok": True, "mensagem": f"{n} novo(s)", "novos": n}
        except NaoSuportado:
            continue
        except ErroConexao as e:
            r = {"provedor": pid, "ok": False, "mensagem": str(e), "novos": 0}
        con.execute("INSERT INTO sincronizacoes VALUES (?,?,?,?,?)", (pid, agora(), int(r["ok"]), r["mensagem"], r["novos"]))
        con.commit()
        out.append(r)
    return out


def historico_por_provedor(con=None) -> dict:
    """O que está guardado de cada provedor (a janela Conexões mostra: desconectar não apaga isto)."""
    con = con or dados.banco()
    out = {}
    for pid in PROVEDORES:
        pubs = con.execute("SELECT COUNT(*), MIN(data) FROM publicacoes WHERE fonte=?", (pid,)).fetchone()
        coms = con.execute("SELECT COUNT(*) FROM comentarios WHERE fonte=?", (pid,)).fetchone()[0]
        out[pid] = {"publicacoes": pubs[0], "desde": (pubs[1] or "")[:10], "comentarios": coms, "ultima_sync": ultima_sync(con, pid)}
    return out


def exportar(destino: Path, con=None) -> Path:
    """Tudo em CSV, para levar para onde quiser (o histórico é seu)."""
    con = con or dados.banco()
    destino.mkdir(parents=True, exist_ok=True)
    for tabela in ("publicacoes", "metricas_dia", "perfil", "comentarios", "envios"):
        linhas = con.execute(f"SELECT * FROM {tabela}").fetchall()
        with (destino / f"{tabela}.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow([d[0] for d in con.execute(f"SELECT * FROM {tabela} LIMIT 0").description])
            w.writerows([tuple(r) for r in linhas])
    return destino


# ---------------------------------------------------------------- resultado de cada post

def _mediana(con, rede, antes_de, n=10):
    vals = [r[0] for r in con.execute("SELECT views FROM publicacoes WHERE rede=? AND data<? AND views IS NOT NULL ORDER BY data DESC LIMIT ?",
                                      (rede, antes_de, n))]
    return statistics.median(vals) if len(vals) >= 3 else None


def _post_do_roteiro(texto: str, data: str) -> tuple[str, str]:
    """Liga uma publicação ao roteiro que a gerou (pela data e pelo gancho) para a biblioteca saber o gancho certo."""
    pasta = dados.pasta_dados() / "roteiros"
    for r in sorted(pasta.glob(f"{data[:10]}-*.json")):
        try:
            d = json.loads(r.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        hook = next((s for s in d.get("scenes", []) if s.get("type") == "hook"), {})
        gancho = " ".join(l[0] if isinstance(l, list) else str(l) for l in hook.get("lines", [])) or hook.get("say") or hook.get("fala", "")
        return r.stem, gancho
    return "", (texto or "").split("\n")[0][:140]


def avaliar(con=None, ref: dt.date | None = None) -> list[dict]:
    """Posts com 7 dias ou mais e ainda sem veredito: compara com a mediana dos 10 anteriores da mesma rede e
    lança na biblioteca de ganchos (o roteirista passa a copiar o que de fato funcionou no @ciellotec)."""
    con = con or dados.banco()
    ref = ref or dt.date.today()
    limite = (ref - dt.timedelta(days=DIAS_RESULTADO)).isoformat()
    novos = []
    for p in con.execute("SELECT * FROM publicacoes WHERE data<=? AND views IS NOT NULL AND (rede, id_ext) NOT IN "
                         "(SELECT rede, id_ext FROM avaliacoes) ORDER BY data", (limite + "T23:59",)).fetchall():
        med = _mediana(con, p["rede"], p["data"])
        if not med:
            continue
        mult = p["views"] / med if med else None
        veredito = "acima" if mult >= 1.3 else "abaixo" if mult <= 0.7 else "na média"
        con.execute("INSERT INTO avaliacoes VALUES (?,?,?,?,?)", (p["rede"], p["id_ext"], ref.isoformat(), round(mult, 2), veredito))
        post, gancho = _post_do_roteiro(p["texto"], p["data"])
        if post and not p["post"]:
            con.execute("UPDATE publicacoes SET post=? WHERE rede=? AND id_ext=?", (post, p["rede"], p["id_ext"]))
        if gancho:
            linhas = ganchos.ler()
            url = p["url"] or f"{p['rede']}:{p['id_ext']}"
            if not any(l.get("url") == url for l in linhas):
                porque = {"acima": "acima da média do perfil", "abaixo": "abaixo da média do perfil", "na média": "na média do perfil"}[veredito]
                ganchos.gravar(linhas + [ganchos.completar({
                    "data": p["data"][:10], "perfil": f"@ciellotec ({p['rede']})", "gancho": gancho, "views": int(p["views"]),
                    "mediana_perfil": int(med), "salvamentos": p["salvamentos"] or "", "compartilhamentos": p["compartilhamentos"] or "",
                    "retencao_s": p["tempo_medio_s"] or "", "nosso": "sim", "url": url, "porque": f"{porque} ({mult:.1f}x)"})])
        novos.append({"rede": p["rede"], "id_ext": p["id_ext"], "data": p["data"], "texto": p["texto"][:120], "views": p["views"],
                      "mediana": med, "multiplicador": round(mult, 2), "veredito": veredito, "gancho": gancho})
    con.commit()
    return novos


def resultados(con=None, dias=60) -> list[dict]:
    con = con or dados.banco()
    desde = (dt.date.today() - dt.timedelta(days=dias)).isoformat()
    return [dict(r) for r in con.execute(
        "SELECT p.rede, p.id_ext, p.data, p.texto, p.url, p.views, p.salvamentos, p.compartilhamentos, p.tempo_medio_s, p.post, "
        "a.multiplicador, a.veredito FROM publicacoes p LEFT JOIN avaliacoes a USING (rede, id_ext) WHERE p.data>=? ORDER BY p.data DESC", (desde,))]


# ---------------------------------------------------------------- comentários

LEAD = r"\b(preco|quanto (custa|e|fica|cobra)|valor|valores|orcamento|como funciona|quero|tenho interesse|interessad|contrat|demo|teste gratis|whats|zap|me chama|chama no|dm|direct|contato)\b"
SPAM = r"(https?://|www\.|ganhe|seguidores gratis|promo|sorteio|crypto|bitcoin|investimento garantido|\bdm for\b)"
ELOGIO = r"\b(top|show|incrivel|muito bom|excelente|parabens|amei|adorei|sensacional|que massa|massa|demais|util|obrigad)\b|[👏🔥❤😍🙌👍]"


def categoria(texto: str) -> str:
    t = sem_acento(texto)
    if re.search(SPAM, t):
        return "spam"
    if re.search(LEAD, t):
        return "lead"
    if "?" in t:
        return "pergunta"
    if re.search(ELOGIO, t, re.I) or re.search(ELOGIO, texto or ""):
        return "elogio"
    return "outro"


AGRADECER = ["Valeu demais! 🙌", "Que bom que ajudou! Salva pra testar depois 😉", "Obrigado! Tem mais vindo por aí 🚀"]


def sugestao(c: dict) -> str:
    cat, nome = c["categoria"], (c.get("autor") or "").lstrip("@")
    if cat == "lead":
        return f"Oi{', @' + nome if nome else ''}! Te chamei no direct para te mostrar como funciona 😉"
    if cat == "pergunta":
        achados = atendimento.buscar(c.get("texto", ""), 1)
        if achados and achados[0]["completa"] and achados[0]["nota"] >= 3:
            return achados[0]["resposta"][:600]
        return ""
    if cat == "elogio":
        return AGRADECER[sum(map(ord, c["id_ext"])) % len(AGRADECER)]
    return ""


def caixa(con=None, estado="novo", limite=100) -> list[dict]:
    con = con or dados.banco()
    linhas = con.execute("SELECT * FROM comentarios WHERE estado=? ORDER BY CASE categoria WHEN 'lead' THEN 0 WHEN 'pergunta' THEN 1 "
                         "WHEN 'outro' THEN 2 WHEN 'elogio' THEN 3 ELSE 4 END, data DESC LIMIT ?", (estado, limite)).fetchall()
    return [{**dict(r), "sugestao": sugestao(dict(r))} for r in linhas]


def responder(rede: str, id_ext: str, texto: str, con=None) -> dict:
    """Responde pelo provedor que cobre a rede. Se ele não responde comentários, marca para você responder pelo app."""
    con = con or dados.banco()
    c = con.execute("SELECT * FROM comentarios WHERE rede=? AND id_ext=?", (rede, id_ext)).fetchone()
    if not c:
        return {"ok": False, "saida": "comentário não encontrado"}
    texto = re.sub(r"\s+", " ", texto or "").strip()[:2000]
    if not texto:
        return {"ok": False, "saida": "escreva a resposta"}
    pid = c["fonte"] if c["fonte"] in PROVEDORES else None
    try:
        if not pid:
            raise NaoSuportado("provedor desconhecido")
        PROVEDORES[pid].responder(conexoes.credenciais(pid), dict(c), texto)
        estado, saida = "respondido", "Resposta publicada."
    except NaoSuportado as e:
        estado, saida = "responder_no_app", f"Este provedor não responde pela API ({e}). Copie a resposta e responda pelo app."
    except ErroConexao as e:
        return {"ok": False, "saida": f"Não deu para responder agora: {e}. Nada se perdeu: tente de novo."}
    con.execute("UPDATE comentarios SET estado=?, resposta=?, respondido_em=? WHERE rede=? AND id_ext=?", (estado, texto, agora(), rede, id_ext))
    con.commit()
    return {"ok": True, "saida": saida}


def marcar(rede: str, id_ext: str, estado: str, con=None) -> dict:
    if estado not in ("novo", "ignorado", "lead", "respondido"):
        return {"ok": False, "saida": "estado inválido"}
    con = con or dados.banco()
    con.execute("UPDATE comentarios SET estado=? WHERE rede=? AND id_ext=?", (estado, rede, id_ext))
    con.commit()
    return {"ok": True, "saida": {"ignorado": "Ignorado.", "lead": "Marcado como lead.", "novo": "De volta à caixa.", "respondido": "Marcado como respondido."}[estado]}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("acao", choices=["sincronizar", "resultados", "comentarios", "exportar"])
    a = ap.parse_args()
    if a.acao == "sincronizar":
        for r in sincronizar():
            print(f"{'ok ' if r['ok'] else 'ERRO'} {r['provedor']}: {r['mensagem']}")
        for r in avaliar():
            print(f"resultado: {r['data'][:10]} {r['rede']} {r['multiplicador']}x ({r['veredito']}) {r['gancho'][:60]}")
    elif a.acao == "resultados":
        for r in resultados():
            print(f"{r['data'][:10]} {r['rede']:<9} {int(r['views'] or 0):>6} views  {r['veredito'] or '(menos de 7 dias)':<10} {(r['texto'] or '')[:60]}")
    elif a.acao == "comentarios":
        for c in caixa():
            print(f"[{c['categoria']}] {c['rede']} @{c['autor']}: {c['texto'][:80]}\n   → {c['sugestao'] or '(responder você)'}")
    else:
        print(exportar(dados.estado("exportacao", dt.date.today().isoformat())))


if __name__ == "__main__":
    main()
