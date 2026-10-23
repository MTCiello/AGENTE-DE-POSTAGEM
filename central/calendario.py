"""Calendário do mês da rede social (Instagram, TikTok e YouTube Shorts) e a previsão do mês.

Um mesmo vídeo vertical sai nas 3 redes, cada uma no seu horário. O calendário mostra, dia a dia, o post
(roteiro), em que etapa ele está e como está o envio em cada rede; sugere o pilar dos dias vazios para
equilibrar os 5 pilares; e confere o limite de posts do Metricool. A previsão usa o histórico do banco local
(a mediana de views de cada rede e a tendência de seguidores).

  python central/calendario.py              # mês atual
  python central/calendario.py 2026-11
"""
import argparse
import calendar
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conexoes  # noqa: E402
import conteudo  # noqa: E402
import dados  # noqa: E402
import ganchos  # noqa: E402

PILARES = list(ganchos.PILARES)  # comandos, repos, economizar, lancamentos, negocio
NOMES_PILARES = {"comandos": "Comandos e prompts", "repos": "Repositórios", "economizar": "Economizar com IA", "lancamentos": "Lançamentos",
                 "negocio": "IA no negócio"}
PADRAO = {"dias": [0, 2, 4], "horarios": {"instagram": "10:00", "tiktok": "18:00", "youtube": "12:00"}, "limite_metricool": 20}
DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def config() -> dict:
    try:
        c = json.loads(dados.estado("calendario.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        c = {}
    return {**PADRAO, **c, "horarios": {**PADRAO["horarios"], **c.get("horarios", {})}}


def configurar(d: dict) -> dict:
    c = config()
    try:
        if d.get("dias") is not None:
            dias = sorted({int(x) for x in (d["dias"] if isinstance(d["dias"], list) else str(d["dias"]).split(","))})
            if not dias or any(x < 0 or x > 6 for x in dias):
                raise ValueError("escolha pelo menos um dia")
            c["dias"] = dias
        for rede in conexoes.REDES:
            h = str(d.get(f"hora_{rede}") or "").strip()
            if h:
                dt.time.fromisoformat(h)
                c["horarios"][rede] = h[:5]
        if d.get("limite_metricool") not in (None, ""):
            c["limite_metricool"] = max(0, int(d["limite_metricool"]))
    except ValueError as e:
        return {"ok": False, "saida": str(e) or "valor inválido"}
    dados.estado("calendario.json").write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"ok": True, "saida": "calendário atualizado"}


def pilar_do_roteiro(post: dict) -> str:
    try:
        d = json.loads((conteudo.ROTEIROS / f"{post['post']}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    texto = " ".join(str(s.get("say") or "") for s in d.get("scenes", []))
    return d.get("pilar") or ganchos.pilar_de(f"{post.get('titulo', '')} {texto}")


def envios(con, posts: list[str]) -> dict:
    if not posts:
        return {}
    q = con.execute(f"SELECT * FROM envios WHERE post IN ({','.join('?' * len(posts))})", posts).fetchall()
    return {(r["post"], r["rede"]): dict(r) for r in q}


def mes(ano: int, m: int, ref: dt.date | None = None, con=None) -> dict:
    ref = ref or dt.date.today()
    con = con or dados.banco()
    c = config()
    redes = {k: v for k, v in conexoes.redes().items() if v["ativa"]}
    posts = {p["data"]: p for p in conteudo.quadro(dias_passados=400, ref=ref)}
    env = envios(con, [p["post"] for p in posts.values()])
    ultimo = calendar.monthrange(ano, m)[1]
    # pilares já usados (últimas 4 semanas antes do mês + o próprio mês) para sugerir os dias vazios
    inicio = dt.date(ano, m, 1)
    usados = {k: 0 for k in PILARES}
    for data, p in posts.items():
        d = dt.date.fromisoformat(data)
        if inicio - dt.timedelta(days=28) <= d <= dt.date(ano, m, ultimo):
            pl = pilar_do_roteiro(p)
            if pl in usados:
                usados[pl] += 1
    dias = []
    for n in range(1, ultimo + 1):
        d = dt.date(ano, m, n)
        p = posts.get(d.isoformat())
        slot = d.weekday() in c["dias"]
        if not p and (not slot or d < ref):
            continue  # dia sem post: só os que ainda vão chegar
        item = {"data": d.isoformat(), "dia_semana": DIAS_SEMANA[d.weekday()], "passado": d < ref, "slot": slot, "post": None, "redes": {}}
        if p:
            item["post"] = {"post": p["post"], "titulo": p["titulo"], "pronto": p["pronto"], "falta": p["falta"], "pilar": pilar_do_roteiro(p),
                            "final": p["etapas"]["final"]}
        elif d >= ref:
            sugerido = min(PILARES, key=lambda k: (usados[k], PILARES.index(k)))
            usados[sugerido] += 1
            item["sugestao"] = sugerido
        for rede in redes:
            e = env.get((p["post"], rede)) if p else None
            item["redes"][rede] = {"hora": c["horarios"][rede], "estado": (e or {}).get("estado") or ("—" if not p else "sem registro" if d < ref else "na fila" if p["pronto"] or p["etapas"]["final"] else "em produção"),
                                   "url": (e or {}).get("url", ""), "erro": (e or {}).get("erro", "")}
        dias.append(item)
    return {"ano": ano, "mes": m, "dias": dias, "redes": redes, "nomes_redes": conexoes.REDES, "pilares": NOMES_PILARES,
            "uso_pilares": usados, "config": c, "etapas": conteudo.ROTULOS, "previsao": previsao(ano, m, dias, redes, con, ref)}


def _tendencia(con, rede, ref):
    pts = con.execute("SELECT dia, seguidores FROM perfil WHERE rede=? AND dia>=? ORDER BY dia", (rede, (ref - dt.timedelta(days=90)).isoformat())).fetchall()
    if len(pts) < 2:
        return (pts[-1]["seguidores"], 0.0) if pts else (None, None)
    x0 = dt.date.fromisoformat(pts[0]["dia"])
    xs = [(dt.date.fromisoformat(p["dia"]) - x0).days for p in pts]
    ys = [p["seguidores"] for p in pts]
    if xs[-1] == 0:
        return ys[-1], 0.0
    mx, my = statistics.mean(xs), statistics.mean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    return ys[-1], (sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0)  # seguidores por dia


def previsao(ano, m, dias, redes, con, ref) -> dict:
    """Quanto o mês deve render se o calendário for cumprido, rede a rede, a partir do seu histórico."""
    fim = dt.date(ano, m, calendar.monthrange(ano, m)[1])
    c = config()
    out, metricool = {}, 0
    for rede, info in redes.items():
        vals = [r[0] for r in con.execute("SELECT views FROM publicacoes WHERE rede=? AND views IS NOT NULL ORDER BY data DESC LIMIT 10", (rede,))]
        med = statistics.median(vals) if len(vals) >= 3 else None
        planejados = sum(1 for d in dias if (d["post"] if d["passado"] else d["slot"] or d["post"]))  # dia passado sem post não conta
        feitos = con.execute("SELECT COUNT(*), COALESCE(SUM(views),0) FROM publicacoes WHERE rede=? AND substr(data,1,7)=?",
                             (rede, f"{ano}-{m:02d}")).fetchone()
        seg, por_dia = _tendencia(con, rede, ref)
        dias_ate_fim = max(0, (fim - ref).days)
        out[rede] = {"posts_planejados": planejados, "mediana_views": med, "views_previstas": round(med * planejados) if med else None,
                     "publicados_no_mes": feitos[0], "views_no_mes": feitos[1], "seguidores": seg,
                     "seguidores_fim_mes": round(seg + por_dia * dias_ate_fim) if seg is not None and por_dia is not None else None,
                     "via": info["via"], "historico": len(vals)}
        if info["via"] in ("claude", "metricool"):
            metricool += planejados
    limite = c["limite_metricool"]
    avisos = []
    if limite and metricool > limite:
        avisos.append(f"O calendário pede {metricool} posts pelo Metricool e o seu plano permite {limite} por mês: "
                      "tire um dia, publique alguma rede pela API direta ou suba o plano.")
    for rede, p in out.items():
        if p["historico"] < 3:
            avisos.append(f"{conexoes.REDES[rede]}: ainda sem histórico para prever views (precisa de 3 posts sincronizados).")
    return {"redes": out, "posts_metricool": metricool, "limite_metricool": limite, "avisos": avisos}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mes", nargs="?", help="AAAA-MM")
    a = ap.parse_args()
    hoje = dt.date.today()
    ano, m = map(int, (a.mes or hoje.strftime("%Y-%m")).split("-"))
    r = mes(ano, m)
    for d in r["dias"]:
        p = d["post"]
        print(f"{d['data'][8:]}/{d['data'][5:7]} {d['dia_semana']}  " + (f"{p['titulo'][:50]} [{NOMES_PILARES.get(p['pilar'], p['pilar'])}]" if p
                                                                         else f"(vazio · sugestão: {NOMES_PILARES.get(d.get('sugestao'), '—')})"))
    for rede, p in r["previsao"]["redes"].items():
        print(f"{conexoes.REDES[rede]}: {p['posts_planejados']} posts · views previstas {p['views_previstas'] or '—'} · seguidores no fim do mês {p['seguidores_fim_mes'] or '—'}")
    for a_ in r["previsao"]["avisos"]:
        print("⚠", a_)


if __name__ == "__main__":
    main()
