"""Biblioteca de ganchos: o que fez vídeo performar, medido, para o roteirista copiar o padrão (nunca o texto).

Cada linha de conhecimento/ganchos.csv é um vídeo: o gancho, o formato do gancho, quantas vezes ele
performou acima da média do próprio criador (multiplicador) e por que funcionou. Nossos posts entram
também, para comparar o que aprendemos com o que de fato funcionou no nosso perfil.

Uso:
  python central/ganchos.py ranking                 # formatos de gancho que mais performam e melhores exemplos
  python central/ganchos.py modelos --pilar comandos # 5 modelos prontos para o roteiro da semana
  python central/ganchos.py adicionar --perfil @x --gancho "..." --views 120000 --mediana 30000 --porque "..."
  python central/ganchos.py reclassificar           # refaz formato/pilar depois de mudar as regras
  python central/ganchos.py importar-metricool conhecimento/concorrentes/2026-10-26.json   # concorrentes do Metricool (seguro)
  python central/ganchos.py importar @gabrieltomaz.ia @iacomjota --sessao seu_usuario   # último recurso (instaloader)

O importar usa o instaloader (github.com/instaloader/instaloader, MIT): `pip install instaloader` e
`instaloader --login SEU_USUARIO` uma vez. Use uma conta secundária: coletar dados do Instagram fora da
API oficial vai contra os termos de uso e pode bloquear a conta.
"""
import argparse
import csv
import datetime as dt
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from empresa import perfil  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "conhecimento" / "ganchos.csv"
CAMPOS = ["data", "perfil", "gancho", "formato", "pilar", "views", "mediana_perfil", "multiplicador",
          "salvamentos", "compartilhamentos", "retencao_s", "nosso", "url", "porque"]

# Formatos de gancho, do mais específico para o mais genérico. O primeiro que bater define o formato.
FORMATOS = [
    ("salve", r"\bsalv[ae]\b|guard[ae] (esse|este)|save this"),
    ("alerta", r"cuidado|pare de|para de|nunca|erro|errad|ningu[eé]m te contou|proibid|perigo|afasta"),
    ("segredo", r"segredo|escondid|pouca gente sabe|ningu[eé]m sabe|truque|hack"),
    ("lista", r"^\s*\d+\s|\b\d+ (comandos|prompts|dicas|ferramentas|usos|sites|apps|ias|formas|jeitos|coisas|testes)"),
    ("prova", r"testei|criei|montei|fiz|usei|ganhei|economizei|resultado|em \d+ (dias|minutos|horas)"),
    ("contraste", r"antes|depois|em vez de|ao inv[eé]s|enquanto (voc[eê]|seu)|vs\.?|versus|sem gastar|de gra[cç]a"),
    ("cenario", r"^imagina|^e se|^se (o |a )?(voc[eê]|sua|seu)"),
    ("pergunta", r"\?\s*$|^(voc[eê] sabia|sabia que|quer|j[aá] pensou)"),
    ("novidade", r"saiu|chegou|lan[cç]ou|novo|nova|acabou de|agora (d[aá]|o|a)"),
]
DESCRICAO = {
    "salve": "Pede o salvamento logo de cara (\"salva esse vídeo\")",
    "alerta": "Alerta ou erro (\"pare de…\", \"cuidado…\")",
    "segredo": "Segredo ou atalho que poucos conhecem",
    "lista": "Número + lista (\"5 comandos…\")",
    "contraste": "Antes × depois, ou sem × com",
    "cenario": "Cenário (\"imagina…\", \"e se…\")",
    "pergunta": "Pergunta direta",
    "prova": "Prova pessoal (\"testei…\", \"economizei…\")",
    "novidade": "Novidade (\"saiu…\", \"acabou de…\")",
    "outro": "Afirmação direta",
}
PILARES = {
    "comandos": r"prompt|comando|chatgpt|pe[cç]a pra|pede pra",
    "repos": r"github|reposit[oó]rio|open source|c[oó]digo aberto",
    "economizar": r"gr[aá]tis|de gra[cç]a|economi|sem pagar|barato|assinatura",
    "lancamentos": r"saiu|lan[cç]|novo|nova|chegou|atualiza",
    "negocio": r"neg[oó]cio|empresa|cliente|vend|loja|whats|atendimento|site|google",
}


def formato_de(gancho: str) -> str:
    g = gancho.lower()
    return next((f for f, rx in FORMATOS if re.search(rx, g)), "outro")


def pilar_de(texto: str) -> str:
    t = texto.lower()
    return next((p for p, rx in PILARES.items() if re.search(rx, t)), "negocio")


def ler():
    if not CSV.exists():
        return []
    with CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def gravar(linhas):
    CSV.parent.mkdir(parents=True, exist_ok=True)
    with CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        for l in linhas:
            w.writerow({k: l.get(k, "") for k in CAMPOS})


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def completar(l: dict) -> dict:
    l["formato"] = l.get("formato") or formato_de(l["gancho"])
    l["pilar"] = l.get("pilar") or pilar_de(f"{l['gancho']} {l.get('porque', '')}")
    v, m = num(l.get("views")), num(l.get("mediana_perfil"))
    if v and m and not l.get("multiplicador"):
        l["multiplicador"] = f"{v / m:.2f}"
    return l


# ---------------------------------------------------------------- comandos

def cmd_adicionar(a):
    linhas = ler()
    nova = completar({"data": a.data or dt.date.today().isoformat(), "perfil": a.perfil, "gancho": a.gancho, "formato": a.formato,
                      "pilar": a.pilar, "views": a.views, "mediana_perfil": a.mediana, "salvamentos": a.salvamentos,
                      "compartilhamentos": a.compartilhamentos, "retencao_s": a.retencao, "nosso": "sim" if a.nosso else "",
                      "url": a.url, "porque": a.porque})
    if any(l["url"] and l["url"] == nova["url"] for l in linhas):
        sys.exit("Esse vídeo já está na biblioteca.")
    gravar(linhas + [nova])
    print(f"ok: [{nova['formato']}/{nova['pilar']}] {nova['gancho']}")


def cmd_importar(a):
    try:
        import instaloader
    except ImportError:
        sys.exit("Instale antes: pip install instaloader")
    L = instaloader.Instaloader(download_pictures=False, download_videos=False, save_metadata=False, quiet=True)
    if a.sessao:
        L.load_session_from_file(a.sessao)
    linhas = ler()
    urls = {l["url"] for l in linhas}
    limite = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=a.dias)
    novos = 0
    for perfil in a.perfis:
        nome = perfil.lstrip("@")
        reels = []
        for post in instaloader.Profile.from_username(L.context, nome).get_posts():
            data = post.date_utc.replace(tzinfo=dt.timezone.utc)
            if data < limite:
                break
            if not post.is_video:
                continue
            views = getattr(post, "video_play_count", None) or post.video_view_count or 0
            reels.append((post, views))
            if len(reels) >= a.max:
                break
        if not reels:
            continue
        mediana = statistics.median(v for _, v in reels) or 1
        for post, views in reels:
            url = f"https://www.instagram.com/reel/{post.shortcode}/"
            if url in urls or views < mediana * a.minimo:
                continue  # só entra o que performou acima da média do criador
            gancho = (post.caption or "").strip().split("\n")[0][:160]
            linhas.append(completar({"data": post.date_utc.date().isoformat(), "perfil": "@" + nome, "gancho": gancho,
                                     "views": int(views), "mediana_perfil": int(mediana), "url": url,
                                     "porque": "a analisar (gancho tirado da 1ª linha da legenda)"}))
            urls.add(url)
            novos += 1
        print(f"@{nome}: {len(reels)} reels, mediana {int(mediana)} views")
    gravar(linhas)
    print(f"{novos} ganchos novos acima de {a.minimo}x a mediana")


def cmd_importar_metricool(a):
    """Reels dos concorrentes cadastrados no Metricool (API oficial, sem risco para a conta).

    O agente salva o retorno do Metricool (IGCR01 perfil, IGCR03 texto, IGCR04 url, IGCR05 data,
    IGCR07 curtidas, IGCR08 comentários, IGCR09 interações) como lista de objetos com as chaves
    perfil, texto, url, data, curtidas, comentarios, interacoes.
    """
    import json
    reels = json.loads(Path(a.arquivo).read_text(encoding="utf-8"))
    linhas = ler()
    urls = {l["url"] for l in linhas}
    por_perfil = {}
    for r in reels:
        por_perfil.setdefault(r["perfil"], []).append(r)
    novos = 0
    for perfil, rs in por_perfil.items():
        inter = [num(r.get("interacoes")) or (num(r.get("curtidas")) or 0) + (num(r.get("comentarios")) or 0) for r in rs]
        mediana = statistics.median(inter) or 1
        for r, i in zip(rs, inter):
            if r["url"] in urls or i < mediana * a.minimo:
                continue
            gancho = (r.get("texto") or "").strip().split("\n")[0][:160]
            linhas.append(completar({"data": (r.get("data") or "")[:10], "perfil": "@" + perfil.lstrip("@"), "gancho": gancho,
                                     "multiplicador": f"{i / mediana:.2f}", "url": r["url"],
                                     "porque": f"a analisar · {int(i)} interações (mediana {int(mediana)}) · Metricool"}))
            urls.add(r["url"])
            novos += 1
        print(f"@{perfil.lstrip('@')}: {len(rs)} reels, mediana {int(mediana)} interações")
    gravar(linhas)
    print(f"{novos} ganchos novos acima de {a.minimo}x a mediana")


def _ranking_formatos(linhas):
    fora = [l for l in linhas if l.get("nosso") != "sim" and num(l.get("multiplicador"))]
    grupos = {}
    for l in fora:
        grupos.setdefault(l["formato"], []).append(num(l["multiplicador"]))
    return sorted(((f, statistics.median(ms), len(ms)) for f, ms in grupos.items()), key=lambda x: -x[1])


def cmd_reclassificar(_a):
    """Refaz formato e pilar de todas as linhas (use depois de melhorar as regras)."""
    linhas = [completar({**l, "formato": "", "pilar": ""}) for l in ler()]
    gravar(linhas)
    for l in linhas:
        print(f"[{l['formato']}/{l['pilar']}] {l['gancho'][:80]}")


def cmd_ranking(a):
    linhas = ler()
    print(f"{len(linhas)} vídeos na biblioteca ({sum(l.get('nosso') == 'sim' for l in linhas)} nossos)\n")
    print("FORMATOS QUE MAIS PERFORMAM (mediana do multiplicador sobre a média do criador)")
    for f, m, n in _ranking_formatos(linhas):
        print(f"  {m:5.1f}x  {DESCRICAO.get(f, f):55} ({n} vídeos)")
    print("\nMELHORES EXEMPLOS")
    fora = sorted((l for l in linhas if l.get("nosso") != "sim"), key=lambda l: -(num(l.get("multiplicador")) or num(l.get("views")) or 0))
    for l in fora[: a.top]:
        mult = f"{num(l['multiplicador']):.1f}x" if num(l.get("multiplicador")) else f"{int(num(l['views']) or 0)} views"
        print(f"  {mult:>12}  [{l['formato']}] {l['gancho'][:80]}  — {l['perfil']}")
    nossos = [l for l in linhas if l.get("nosso") == "sim"]
    if nossos:
        print(f"\nNOSSOS POSTS (o que o público do {perfil()['instagram'] or 'nosso perfil'} respondeu)")
        for l in sorted(nossos, key=lambda l: -(num(l.get("views")) or 0)):
            print(f"  {int(num(l['views']) or 0):>6} views · {l.get('salvamentos') or 0} salv. · {l.get('retencao_s') or '?'} s  [{l['formato']}] {l['gancho'][:70]}")


def cmd_modelos(a):
    linhas = ler()
    ordem = [f for f, _, _ in _ranking_formatos(linhas)] or [f for f, _ in FORMATOS]
    print(f"Modelos de gancho para o pilar '{a.pilar or 'todos'}' (adapte; nunca copie o texto):\n")
    for f in ordem[:5]:
        ex = [l for l in linhas if l["formato"] == f and l.get("nosso") != "sim" and (not a.pilar or l["pilar"] == a.pilar)]
        ex.sort(key=lambda l: -(num(l.get("multiplicador")) or 0))
        print(f"- {DESCRICAO.get(f, f)}")
        for l in ex[:2]:
            print(f"    ex.: \"{l['gancho'][:90]}\" ({l['perfil']}) — {l.get('porque', '')[:80]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("adicionar")
    for c in ("perfil", "gancho"):
        s.add_argument(f"--{c}", required=True)
    for c in ("formato", "pilar", "views", "mediana", "salvamentos", "compartilhamentos", "retencao", "url", "porque", "data"):
        s.add_argument(f"--{c}", default="")
    s.add_argument("--nosso", action="store_true", help="post do nosso perfil")
    s.set_defaults(f=cmd_adicionar)
    s = sub.add_parser("importar")
    s.add_argument("perfis", nargs="+")
    s.add_argument("--sessao", help="usuário com sessão salva pelo 'instaloader --login'")
    s.add_argument("--dias", type=int, default=30)
    s.add_argument("--max", type=int, default=30, help="reels por perfil")
    s.add_argument("--minimo", type=float, default=1.5, help="só guarda reels acima de N x a mediana do perfil")
    s.set_defaults(f=cmd_importar)
    s = sub.add_parser("importar-metricool")
    s.add_argument("arquivo", help="JSON salvo pelo agente a partir dos concorrentes do Metricool")
    s.add_argument("--minimo", type=float, default=1.5)
    s.set_defaults(f=cmd_importar_metricool)
    s = sub.add_parser("reclassificar")
    s.set_defaults(f=cmd_reclassificar)
    s = sub.add_parser("ranking")
    s.add_argument("--top", type=int, default=10)
    s.set_defaults(f=cmd_ranking)
    s = sub.add_parser("modelos")
    s.add_argument("--pilar", choices=list(PILARES))
    s.set_defaults(f=cmd_modelos)
    a = ap.parse_args()
    from status import trabalhando
    with trabalhando("pesquisador-mercado", f"ganchos: {a.cmd}"):
        a.f(a)


if __name__ == "__main__":
    main()
