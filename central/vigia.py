"""Vigia de concorrentes: preço, plano, oferta e anúncio dos CRMs que disputam o mesmo cliente do CIELLO CRM.

Faz o "vigia o concorrente" do Agente de Pesquisa. Cada página de comercial/concorrentes.json é baixada, vira texto
e é comparada com a da última vez (guardada em estado/vigia/). O que mudou vai para radar/concorrentes-AAAA-MM-DD.md.
Só biblioteca padrão. Para vigiar dezenas de páginas com JavaScript e alertas, o caminho maior é o
changedetection.io (Apache-2.0, `pip install changedetection.io`), sem Docker.

  python central/vigia.py checar            # baixa tudo, compara e escreve o relatório
  python central/vigia.py anuncios          # links da Biblioteca de Anúncios da Meta (Brasil) de cada concorrente
  python central/vigia.py checar --so Kommo

Anúncios: a API oficial da Biblioteca de Anúncios só devolve anúncios políticos; os comerciais aparecem na página
pública (facebook.com/ads/library), então o relatório traz o link pronto para você (ou o pesquisador) abrir.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONCORRENTES = RAIZ / "comercial" / "concorrentes.json"
FOTOS = RAIZ / "estado" / "vigia"
PRECO = re.compile(r"(?:R\$|US\$|\$|€)\s?\d[\d.,]*(?:\s?(?:/|por)\s?(?:mês|mes|usuário|usuario|user|ano))*", re.I)
NAVEGADOR = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


class Texto(HTMLParser):
    """Só o texto visível: pula script, style, svg e afins; quebra linha nos blocos."""
    PULAR = {"script", "style", "noscript", "svg", "template", "iframe", "head"}
    BLOCO = {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "br", "td", "th", "header", "footer", "nav", "ul", "ol", "table"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes, self.fundo = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.PULAR:
            self.fundo += 1
        elif tag in self.BLOCO:
            self.partes.append("\n")

    def handle_endtag(self, tag):
        if tag in self.PULAR and self.fundo:
            self.fundo -= 1
        elif tag in self.BLOCO:
            self.partes.append("\n")

    def handle_data(self, d):
        if not self.fundo:
            self.partes.append(d)


def texto_visivel(html, inicio="", fim=""):
    p = Texto()
    p.feed(html)
    linhas = [re.sub(r"\s+", " ", l).strip() for l in "".join(p.partes).splitlines()]
    linhas = [l for l in linhas if len(l) > 1]
    txt = "\n".join(dict.fromkeys(linhas))  # sem repetir menu e rodapé duplicados
    if inicio and inicio in txt:
        txt = txt[txt.index(inicio):]
    if fim and fim in txt:
        txt = txt[: txt.index(fim) + len(fim)]
    return txt


def baixar(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": NAVEGADOR, "Accept-Language": "pt-BR,pt;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        bruto = r.read()
        cs = r.headers.get_content_charset() or "utf-8"
    return bruto.decode(cs, errors="replace")


def precos(txt):
    return sorted({re.sub(r"\s+", " ", m.group(0)).strip(" .,") for m in PRECO.finditer(txt)})


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:60] + "-" + hashlib.sha1(t.encode()).hexdigest()[:6]


def comparar(antes, agora, limite=12):
    """Linhas que entraram e saíram (sem ligar para a ordem: menus que mudam de lugar não contam)."""
    a, b = antes.splitlines(), agora.splitlines()
    sa, sb = set(a), set(b)
    entrou = [l for l in b if l not in sa][:limite]
    saiu = [l for l in a if l not in sb][:limite]
    return entrou, saiu, [p for p in precos(agora) if p not in precos(antes)], [p for p in precos(antes) if p not in precos(agora)]


def link_anuncios(termo):
    q = urllib.parse.urlencode({"active_status": "active", "ad_type": "all", "country": "BR", "q": termo,
                                "search_type": "keyword_unordered", "media_type": "all"})
    return f"https://www.facebook.com/ads/library/?{q}"


def destino_relatorio(pasta, dia):
    """Nunca sobrescreve: 2ª vigia do dia ganha a hora no nome (e um número, se for no mesmo minuto)."""
    alvo, n = pasta / f"concorrentes-{dia}.md", 1
    while alvo.exists():
        alvo = pasta / f"concorrentes-{dia}-{dt.datetime.now():%H%M}{'' if n == 1 else f'-{n}'}.md"
        n += 1
    return alvo


def cmd_checar(a):
    cfg = json.loads(Path(a.arquivo).read_text(encoding="utf-8"))
    fotos = Path(a.fotos)
    fotos.mkdir(parents=True, exist_ok=True)
    dia = dt.date.today().isoformat()
    L = [f"# Concorrentes · {dia}", "", "O que mudou nas páginas desde a última vigia (preço, plano, oferta).", ""]
    mudou = erros = abertas = 0
    for c in cfg["concorrentes"]:
        if a.so and c["nome"].lower() not in [s.lower() for s in a.so]:
            continue
        L += [f"## {c['nome']}", ""]
        for u in c["urls"]:
            arq = fotos / f"{slug(u['url'])}.txt"
            try:
                agora = texto_visivel(baixar(u["url"]), u.get("inicio", ""), u.get("fim", ""))
            except Exception as e:  # uma página fora do ar não para a vigia
                erros += 1
                L += [f"- **{u['rotulo']}**: não consegui abrir ({type(e).__name__}: {str(e)[:80]}) · {u['url']}"]
                print(f"{c['nome']} · {u['rotulo']} falhou: {e}", file=sys.stderr)
                continue
            abertas += 1
            if not arq.exists():
                arq.write_text(agora, encoding="utf-8")
                pr = precos(agora)
                L += [f"- **{u['rotulo']}**: 1ª foto guardada · preços na página: {', '.join(pr[:8]) or 'nenhum em texto'} · {u['url']}"]
                continue
            antes = arq.read_text(encoding="utf-8")
            if antes == agora:
                L += [f"- **{u['rotulo']}**: sem mudança · {u['url']}"]
                continue
            entrou, saiu, p_novo, p_saiu = comparar(antes, agora)
            mudou += 1
            L += [f"- **{u['rotulo']}**: **mudou** · {u['url']}"]
            if p_novo or p_saiu:
                L += [f"  - Preço: {', '.join(p_saiu) or '—'} → {', '.join(p_novo) or '—'}"]
            L += [f"  - Entrou: \"{l[:140]}\"" for l in entrou] + [f"  - Saiu: \"{l[:140]}\"" for l in saiu]
            arq.write_text(agora, encoding="utf-8")
        if c.get("anuncios"):
            L += [f"- Anúncios ativos no Brasil: [Biblioteca de Anúncios]({link_anuncios(c['anuncios'])})"]
        if c.get("instagram"):
            L += [f"- Instagram: https://www.instagram.com/{c['instagram']}/ (reels novos entram na biblioteca de ganchos)"]
        L.append("")
    if erros and not abertas:
        # nenhuma página abriu (sem internet): não grava um relatório vazio por cima da última vigia boa
        sys.exit("Nenhuma página abriu (sem internet ou bloqueio de rede). A última vigia continua valendo; tente de novo mais tarde.")
    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    rel = destino_relatorio(saida, dia)
    rel.write_text("\n".join(L), encoding="utf-8")
    print(f"{mudou} páginas mudaram · {erros} fora do ar -> {rel}")


def cmd_anuncios(a):
    for c in json.loads(Path(a.arquivo).read_text(encoding="utf-8"))["concorrentes"]:
        print(f"{c['nome']}: {link_anuncios(c.get('anuncios') or c['nome'])}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arquivo", default=str(CONCORRENTES))
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("checar"); s.add_argument("--so", nargs="*"); s.add_argument("--saida", default=str(RAIZ / "radar"))
    s.add_argument("--fotos", default=str(FOTOS)); s.set_defaults(f=cmd_checar)
    s = sub.add_parser("anuncios"); s.set_defaults(f=cmd_anuncios)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
