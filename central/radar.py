"""Radar: o que está crescendo nos 5 pilares do conteúdo, com nota de 0 a 100.

Só biblioteca padrão do Python, então roda em qualquer PC sem instalar nada.

Fontes (todas abertas e sem chave):
  github     repositórios novos que mais ganharam estrelas (pilar "repositórios famosos")
  hn         Hacker News: o que a comunidade de tecnologia mais votou
  reddit     r/ChatGPT, r/ClaudeAI, r/OpenAI, r/LocalLLaMA, r/ChatGPTPromptGenius…
  noticias   Google Notícias em português (lançamentos e o que a mídia BR está falando)
  trends     Google Trends Brasil (o que o brasileiro está buscando hoje)
  blogs      blogs oficiais (OpenAI, Google)
  last30days opcional: roda o mvanhorn/last30days-skill se --last30days apontar para ele

Uso:
  python central/radar.py                      # últimos 7 dias, todas as fontes
  python central/radar.py --dias 14 --sem reddit
  python central/radar.py --last30days ../last30days-skill/skills/last30days/scripts/last30days.py

Saída: radar/AAAA-MM-DD.md (para ler) e radar/AAAA-MM-DD.json (para o agente usar).
"""
import argparse
import datetime as dt
import email.utils
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (compatible; CielloRadar/1.0)"

PILARES = {
    "comandos": "Comandos e prompts",
    "lancamentos": "Lançamentos e novidades",
    "repos": "Repositórios famosos",
    "economizar": "Economizar com IA",
    "negocio": "IA no negócio",
}
# Palavras que puxam cada pilar (português e inglês). Peso = quantas batem.
TERMOS = {
    "comandos": r"prompts?|comandos?|instru[cç][oõ]es|custom instructions|system prompt|truques?|tricks?|hacks?|dicas?|tips?|templates?",
    "lancamentos": r"lan[cç]a|lan[cç]amento|launch(es|ed)?|releas(e|es|ed)|announc(e|es|ed)|anuncia|novo modelo|new model|now available|chega|update|atualiza[cç][aã]o|gpt-?\d|claude \w+ ?\d|gemini \d|llama \d|sora|veo \d|o\d-",
    "economizar": r"gr[aá]tis|gratuito|free|open[- ]source|c[oó]digo aberto|alternativ\w+|barat\w+|cheap\w*|economi\w+|save money|local(ly)?|self[- ]hosted|sem pagar",
    "negocio": r"neg[oó]cio|business|empresa|vendas?|sales|marketing|whats ?app|atendimento|customer|cliente|crm|small business|pequen\w+ empresa|empreend\w+|automa[cç][aã]o|automation|agent(e|s)?",
}
# Filtro de relevância: o item precisa falar de IA.
IA = re.compile(r"\b(ia|ai|a\.i\.|chat ?gpt|openai|claude|anthropic|gemini|llm|gpt|copilot|perplexity|deepseek|qwen|llama|mistral|grok|midjourney|agente|agent|intelig[eê]ncia artificial|machine learning|mcp)\b", re.I)

REDDIT_SUBS = ["ChatGPT", "ClaudeAI", "OpenAI", "LocalLLaMA", "ChatGPTPromptGenius", "singularity", "artificial"]
NOTICIAS_BUSCAS = ["ChatGPT", "inteligência artificial", "Claude IA", "Gemini Google IA", "IA pequenas empresas", "prompt ChatGPT"]
HN_BUSCAS = ["ChatGPT", "Claude", "Gemini", "OpenAI", "LLM", "open source AI", "AI agent"]
BLOGS = {"OpenAI": "https://openai.com/news/rss.xml", "Google AI": "https://blog.google/technology/ai/rss/"}
OFICIAIS = ("openai.com", "anthropic.com", "blog.google", "deepmind.google", "ai.meta.com", "github.com", "microsoft.com")


# ---------------------------------------------------------------- coleta

def baixar(url: str, json_=True, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        dado = r.read()
    return json.loads(dado) if json_ else dado


def item(fonte, titulo, url, data=None, metrica=0.0, resumo="", extra=None):
    return {"fonte": fonte, "titulo": titulo.strip(), "url": url, "data": data, "metrica": float(metrica or 0),
            "resumo": (resumo or "").strip()[:300], **(extra or {})}


def parse_github(js):
    return [item("github", f"{r['full_name']}: {r.get('description') or ''}", r["html_url"], r.get("created_at", "")[:10],
                 r.get("stargazers_count", 0), r.get("description") or "", {"linguagem": r.get("language"), "topicos": r.get("topics", [])})
            for r in js.get("items", [])]


def github(desde: dt.date):
    q = f"created:>{desde.isoformat()} stars:>100 (llm OR ai OR agent OR chatgpt OR claude OR mcp OR gpt OR gemini)"
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({"q": q, "sort": "stars", "order": "desc", "per_page": 30})
    h = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    return parse_github(baixar(url, headers=h))


def parse_hn(js):
    return [item("hn", h.get("title") or "", h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                 (h.get("created_at") or "")[:10], h.get("points", 0), extra={"comentarios": h.get("num_comments", 0)})
            for h in js.get("hits", []) if h.get("title")]


def hn(desde: dt.date):
    ts = int(dt.datetime.combine(desde, dt.time()).timestamp())
    out = []
    for b in HN_BUSCAS:
        url = "https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode(
            {"query": b, "tags": "story", "numericFilters": f"created_at_i>{ts},points>50", "hitsPerPage": 15})
        out += parse_hn(baixar(url))
    return out


def parse_reddit(js, sub):
    out = []
    for c in js.get("data", {}).get("children", []):
        d = c.get("data", {})
        if d.get("stickied"):
            continue
        out.append(item("reddit", d.get("title", ""), "https://www.reddit.com" + d.get("permalink", ""),
                        dt.datetime.fromtimestamp(d.get("created_utc", 0), dt.timezone.utc).date().isoformat(),
                        d.get("ups", 0), d.get("selftext", ""), {"sub": sub, "comentarios": d.get("num_comments", 0)}))
    return out


def reddit(dias: int):
    t = "week" if dias <= 7 else "month"
    out = []
    for s in REDDIT_SUBS:
        out += parse_reddit(baixar(f"https://www.reddit.com/r/{s}/top.json?t={t}&limit=25"), s)
    return out


def _data_rss(txt):
    try:
        return email.utils.parsedate_to_datetime(txt).date().isoformat()
    except (TypeError, ValueError):
        return (txt or "")[:10] or None


def parse_rss(xml: bytes, fonte: str, extra=None):
    raiz = ET.fromstring(xml)
    ns = {"ht": "https://trends.google.com/trending/rss"}
    out = []
    for it in raiz.iter("item"):
        titulo = it.findtext("title") or ""
        trafego = it.findtext("ht:approx_traffic", namespaces=ns)
        metrica = float(re.sub(r"\D", "", trafego) or 0) if trafego else 0
        resumo = re.sub(r"<[^>]+>", " ", it.findtext("description") or "")
        out.append(item(fonte, titulo, it.findtext("link") or "", _data_rss(it.findtext("pubDate")), metrica, resumo, extra))
    return out


def noticias(_dias):
    out = []
    for b in NOTICIAS_BUSCAS:
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": f"{b} when:7d", "hl": "pt-BR", "gl": "BR", "ceid": "BR:pt-419"})
        out += parse_rss(baixar(url, json_=False), "noticias", {"busca": b})
    return out


def trends(_dias):
    return parse_rss(baixar("https://trends.google.com/trending/rss?geo=BR", json_=False), "trends")


def blogs(_dias):
    out = []
    for nome, url in BLOGS.items():
        out += parse_rss(baixar(url, json_=False), "blogs", {"blog": nome})
    return out


def last30days(script: str, saida: Path):
    """Roda o last30days-skill (MIT) e guarda o JSON bruto ao lado do relatório."""
    destino = saida.with_name(saida.stem + "-last30days.json")
    temas = ["ChatGPT prompts", "Claude AI", "AI tools for small business", "open source AI tools"]
    brutos = {}
    for tema in temas:
        r = subprocess.run([sys.executable, script, tema, "--emit=json"], capture_output=True, text=True, timeout=900)
        brutos[tema] = json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip().startswith("{") else {"erro": r.stderr[-500:]}
    destino.write_text(json.dumps(brutos, ensure_ascii=False, indent=1), encoding="utf-8")
    return destino


FONTES = {"github": github, "hn": hn, "reddit": reddit, "noticias": noticias, "trends": trends, "blogs": blogs}


# ---------------------------------------------------------------- nota

def tokens(txt):
    return {w for w in re.findall(r"[a-zà-ú0-9]{4,}", txt.lower())}


def ja_postado():
    """Títulos e temas que já saíram (historico.md), para não repetir assunto."""
    h = RAIZ / "historico.md"
    return [tokens(l) for l in h.read_text(encoding="utf-8").splitlines() if l.startswith("|")] if h.exists() else []


def pontuar(itens, desde: dt.date):
    vistos = ja_postado()
    # viralidade = posição da métrica dentro da própria fonte (estrela, voto e tráfego não se comparam entre si)
    por_fonte = {}
    for it in itens:
        por_fonte.setdefault(it["fonte"], []).append(it["metrica"])
    for it in itens:
        texto = f"{it['titulo']} {it['resumo']}"
        if it["fonte"] != "github" and not IA.search(texto):
            it["nota"] = 0
            continue
        ms = sorted(por_fonte[it["fonte"]])
        pct = (sum(m <= it["metrica"] for m in ms) / len(ms)) if any(ms) else 0.5
        recente = it["data"] and it["data"] >= desde.isoformat()
        viral = 35 * pct * (1.0 if recente or not it["data"] else 0.6)

        forca = {p: len(re.findall(rx, texto, re.I)) for p, rx in TERMOS.items()}
        if it["fonte"] == "github":  # repositório é sempre do pilar "repos"; o resto conta como ponte
            forca["repos"] = 3
            pilar = "repos"
        else:
            pilar = max(forca, key=forca.get) if any(forca.values()) else "lancamentos"
        aderencia = 25 * min(1, forca.get(pilar, 0) / 2) if forca.get(pilar) else 8
        ponte = 20 if forca["negocio"] else 12 if forca["economizar"] else 6
        tk = tokens(texto)
        repetido = any(len(tk & v) / max(1, len(tk | v)) > 0.25 for v in vistos if v)
        novidade = 0 if repetido else 10
        url = it["url"] or ""
        verificavel = 10 if any(d in url for d in OFICIAIS) or it["fonte"] in ("noticias", "blogs", "github") else 5

        it.update(pilar=pilar, nota=round(viral + aderencia + ponte + novidade + verificavel),
                  partes={"viral": round(viral), "pilar": round(aderencia), "negocio": ponte, "novidade": novidade, "fonte": verificavel})
    vivos = [i for i in itens if i["nota"] > 0]
    # mesma notícia em várias buscas: fica a de nota maior
    unicos = {}
    for it in sorted(vivos, key=lambda i: -i["nota"]):
        chave = re.sub(r"\W+", "", it["titulo"].lower())[:60]
        unicos.setdefault(chave, it)
    return sorted(unicos.values(), key=lambda i: -i["nota"])


# ---------------------------------------------------------------- relatório

def relatorio(itens, erros, hoje, dias):
    linhas = [f"# Radar — {hoje.strftime('%d/%m/%Y')} (últimos {dias} dias)", ""]
    if erros:
        linhas += ["> Fontes que falharam: " + ", ".join(f"{k} ({v})" for k, v in erros.items()), ""]
    linhas += ["## Top 10 geral", "", "| Nota | Pilar | Assunto | Fonte |", "|---|---|---|---|"]
    for it in itens[:10]:
        linhas.append(f"| {it['nota']} | {PILARES[it['pilar']]} | [{it['titulo'][:90]}]({it['url']}) | {it['fonte']} |")
    for p, nome in PILARES.items():
        do_pilar = [i for i in itens if i["pilar"] == p][:5]
        if not do_pilar:
            continue
        linhas += ["", f"## {nome}", ""]
        for it in do_pilar:
            m = f" · {int(it['metrica'])}" if it["metrica"] else ""
            linhas.append(f"- **{it['nota']}** [{it['titulo'][:110]}]({it['url']}) — {it['fonte']}{m}")
    linhas += ["", "_Nota = viralidade 35 + pilar 25 + ponte com negócio 20 + novidade 10 + fonte verificável 10._"]
    return "\n".join(linhas) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dias", type=int, default=7)
    ap.add_argument("--sem", nargs="*", default=[], choices=list(FONTES), help="fontes para pular")
    ap.add_argument("--saida", type=Path, default=RAIZ / "radar")
    ap.add_argument("--last30days", help="caminho do scripts/last30days.py (opcional)")
    a = ap.parse_args()

    hoje = dt.date.today()
    desde = hoje - dt.timedelta(days=a.dias)
    itens, erros = [], {}
    for nome, f in FONTES.items():
        if nome in a.sem:
            continue
        try:
            achados = f(desde) if nome in ("github", "hn") else f(a.dias)
            itens += achados
            print(f"{nome:9} {len(achados):4} itens")
        except Exception as e:  # uma fonte fora do ar não derruba o radar
            erros[nome] = type(e).__name__
            print(f"{nome:9} falhou: {e}", file=sys.stderr)

    ranqueados = pontuar(itens, desde)
    if not ranqueados and erros:
        # sem internet (ou todas as fontes fora): não grava um radar vazio por cima do último bom
        sys.exit("Nenhuma fonte respondeu (sem internet ou bloqueio de rede). O último radar continua valendo; tente de novo mais tarde.")
    a.saida.mkdir(parents=True, exist_ok=True)
    base = a.saida / hoje.isoformat()
    if base.with_suffix(".md").exists():  # nunca sobrescreve um radar do dia (pode ter sido feito à mão)
        base = a.saida / f"{hoje.isoformat()}-{dt.datetime.now():%H%M}"
    base.with_suffix(".json").write_text(json.dumps({"data": hoje.isoformat(), "dias": a.dias, "erros": erros, "itens": ranqueados},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    base.with_suffix(".md").write_text(relatorio(ranqueados, erros, hoje, a.dias), encoding="utf-8")
    if a.last30days:
        print("last30days:", last30days(a.last30days, base.with_suffix(".json")))
    print(f"\n{len(ranqueados)} assuntos -> {base.with_suffix('.md')}")


if __name__ == "__main__":
    from status import trabalhando
    with trabalhando("pesquisador-mercado", "radar da semana"):
        main()
