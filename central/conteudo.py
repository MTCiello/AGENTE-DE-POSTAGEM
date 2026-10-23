"""Quadro de produção de conteúdo: cada post da agenda, em que etapa está e o que falta para ir ao ar.

Etapas de um post (o nome do arquivo é a data + o slug, ex.: 2026-10-27-crm-plano):
  roteiro   roteiros/<post>.json
  narração  audio/<slug>/narracao.wav (central/voz.py)
  vídeo     midia/<post>.mp4 (visual, sem áudio)
  final     midia/final/<post>.mp4 (voz + trilha, central/mixar.py)
  capa      midia/capas/<post>.jpg
  legenda   campo "legenda" do roteiro (rascunho automático aqui; o agente de postagem refina)
  agendado  linha do historico.md com o vídeo do post e status "Agendado" (ou "Publicado")

  python central/conteudo.py                    # o quadro no terminal
  python central/conteudo.py legenda <post>     # gera o rascunho de legenda no roteiro
  python central/conteudo.py agendado <post> --quando "27/10 10h"   # registra no historico.md

Sem o Claude, o quadro, a legenda e o registro funcionam; o agendamento no Metricool é feito pelo agente de postagem
(com a sua aprovação) ou por você no app do Metricool.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ROTEIROS = RAIZ / "roteiros"
HISTORICO = RAIZ / "historico.md"
ETAPAS = ["roteiro", "narracao", "video", "final", "capa", "legenda", "agendado"]
ROTULOS = {"roteiro": "Roteiro", "narracao": "Narração", "video": "Vídeo", "final": "Final", "capa": "Capa", "legenda": "Legenda", "agendado": "Agendado"}
DONO = {"roteiro": "roteirista", "narracao": "produtor-video", "video": "produtor-video", "final": "produtor-video",
        "capa": "produtor-imagem", "legenda": "postagem", "agendado": "postagem"}
HASHTAGS = "#inteligenciaartificial #pequenosnegocios #chapeco #empreendedorismo #ciello"
LIMITE_METRICOOL = 20  # posts por mês no plano grátis


def hoje():
    return dt.date.today()


def ler_roteiro(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def historico(arquivo=None) -> list[dict]:
    """Linhas da tabela do historico.md: data, tema, vídeo, status."""
    arquivo = arquivo or HISTORICO
    if not arquivo.exists():
        return []
    out = []
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        cel = [c.strip() for c in linha.strip().strip("|").split("|")]
        if len(cel) >= 5 and not cel[0].startswith(("Data", "---")) and linha.strip().startswith("|"):
            out.append({"data": cel[0], "tema": cel[1], "origem": cel[2], "video": cel[3], "status": cel[4], "linha": linha})
    return out


def titulo(d: dict, stem: str) -> str:
    linhas = (d.get("capa") or {}).get("linhas") or []
    t = " ".join(l[0] if isinstance(l, list) else str(l) for l in linhas)
    return t or stem[11:].replace("-", " ")


def post(p: Path, hist=None, raiz=None, ref=None) -> dict:
    raiz, ref = raiz or RAIZ, ref or hoje()
    stem, slug = p.stem, p.stem[11:]
    d = ler_roteiro(p)
    hist = historico() if hist is None else hist
    linha = next((h for h in hist if stem in h["video"] or stem in h["linha"]), None)
    status = (linha or {}).get("status", "")
    feito = {"roteiro": bool(d.get("scenes")),
             "narracao": (raiz / "audio" / slug / "narracao.wav").exists() or (raiz / "midia" / "final" / f"{stem}.mp4").exists(),
             "video": (raiz / "midia" / f"{stem}.mp4").exists() or (raiz / "midia" / "final" / f"{stem}.mp4").exists(),  # o final já tem o vídeo
             "final": (raiz / "midia" / "final" / f"{stem}.mp4").exists(),
             "capa": (raiz / "midia" / "capas" / f"{stem}.jpg").exists(),
             "legenda": bool((d.get("legenda") or "").strip()),
             "agendado": bool(re.search(r"agendad|publicad", status, re.I))}
    falta = [e for e in ETAPAS if not feito[e]]
    data = dt.date.fromisoformat(stem[:10])
    return {"post": stem, "slug": slug, "data": data.isoformat(), "dias": (data - ref).days, "titulo": titulo(d, stem),
            "etapas": feito, "falta": falta, "proximo": falta[0] if falta else None, "dono": DONO[falta[0]] if falta else None,
            "status_historico": status, "legenda": d.get("legenda", ""), "pronto": not falta}


def quadro(dias_passados=14, raiz=None, ref=None) -> list[dict]:
    """Os posts da agenda (os de até `dias_passados` atrás também). `raiz` e `ref` trocam a pasta e o dia (testes, briefing)."""
    roteiros = (raiz / "roteiros") if raiz else ROTEIROS
    hist = historico((raiz / "historico.md") if raiz else None)
    ps = [post(p, hist, raiz, ref) for p in sorted(roteiros.glob("20??-??-??-*.json"))]
    return [p for p in ps if p["dias"] >= -dias_passados]


def alertas(ps=None, ref=None) -> list[str]:
    ps = quadro(ref=ref) if ps is None else ps
    out = []
    for p in ps:
        if 0 <= p["dias"] <= 2 and not p["etapas"]["final"]:
            quando = "sai hoje" if p["dias"] == 0 else "sai amanhã" if p["dias"] == 1 else f"sai em {p['dias']} dias"
            out.append(f"Post de {p['data'][8:]}/{p['data'][5:7]} ({p['slug']}) {quando} e ainda não tem o vídeo final")
        elif 0 <= p["dias"] <= 2 and not p["etapas"]["agendado"]:
            out.append(f"Post de {p['data'][8:]}/{p['data'][5:7]} ({p['slug']}) está pronto mas não foi agendado")
    passados = [p for p in ps if p["dias"] < 0 and not re.search(r"publicad", p["status_historico"], re.I)]
    if passados:
        out.append(f"{len(passados)} post(s) com data passada sem registro de publicação ({', '.join(p['data'][8:] + '/' + p['data'][5:7] for p in passados[:5])}): "
                   "foram ao ar? Se ficaram como rascunho no Metricool, refaça a data ou marque como publicado")
    semana = [p for p in ps if 0 <= p["dias"] <= 7]
    if len(semana) < 3:
        out.append(f"Só {len(semana)} post(s) nos próximos 7 dias: a meta é 3 (seg, qua e sex)")
    mes = (ref or hoje()).strftime("%Y-%m")
    agendados_mes = sum(1 for p in ps if p["data"][:7] == mes and p["etapas"]["agendado"])
    if agendados_mes >= LIMITE_METRICOOL - 2:
        out.append(f"{agendados_mes} posts agendados no mês: o Metricool grátis aceita {LIMITE_METRICOOL}")
    return out


def proximos_horarios(n=3, ref=None):
    """Próximos seg, qua e sex às 10h (o padrão do AGENTE.md), sem os dias que já têm post."""
    ref = ref or hoje()
    ocupados = {p["data"] for p in quadro()}
    out, d = [], ref + dt.timedelta(days=1)
    while len(out) < n:
        if d.weekday() in (0, 2, 4) and d.isoformat() not in ocupados:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def legenda_rascunho(d: dict) -> str:
    """Rascunho a partir das falas do roteiro: gancho na 1ª linha, 3 linhas de valor, CTA e hashtags."""
    cenas = d.get("scenes") or []
    falas = [re.sub(r"\s+", " ", c.get("say", "")).strip() for c in cenas]
    gancho = next((f for c, f in zip(cenas, falas) if c.get("type") == "hook"), falas[0] if falas else "")
    itens = [f for c, f in zip(cenas, falas) if c.get("type") not in ("hook", "cta")][:3]
    cta = next((f for c, f in zip(cenas, falas) if c.get("type") == "cta"), "Salva pra testar depois e me chama no direct.")
    corpo = "\n".join(f"👉 {i}" for i in itens)
    return f"{gancho}\n\n{corpo}\n\n{cta}\n\nInteligência artificial para pequenas empresas de Chapecó e região.\n\n{HASHTAGS}".strip()


def gerar_legenda(stem: str, forcar=False) -> dict:
    p = ROTEIROS / f"{Path(stem).stem}.json"
    d = ler_roteiro(p)
    if not d:
        return {"ok": False, "saida": f"roteiro {stem} não encontrado"}
    if d.get("legenda") and not forcar:
        return {"ok": True, "saida": "a legenda já existe", "legenda": d["legenda"]}
    d["legenda"] = legenda_rascunho(d)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"ok": True, "saida": "rascunho de legenda salvo no roteiro (revise antes de postar)", "legenda": d["legenda"]}


def salvar_legenda(stem: str, texto: str) -> dict:
    p = ROTEIROS / f"{Path(stem).stem}.json"
    d = ler_roteiro(p)
    if not d:
        return {"ok": False, "saida": f"roteiro {stem} não encontrado"}
    d["legenda"] = str(texto or "").strip()[:2200]  # limite de legenda do Instagram
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"ok": True, "saida": "legenda salva"}


def marcar_agendado(stem: str, quando: str = "", status: str = "Agendado") -> dict:
    """Registra no historico.md que o post foi agendado (você agendou no Metricool) ou publicado."""
    stem = Path(stem).stem
    p = ROTEIROS / f"{stem}.json"
    if not p.exists():
        return {"ok": False, "saida": f"roteiro {stem} não encontrado"}
    quando = re.sub(r"[|\n]", " ", quando or f"{stem[8:10]}/{stem[5:7]} 10h").strip()[:30]
    status = "Publicado" if status == "Publicado" else "Agendado"
    texto = HISTORICO.read_text(encoding="utf-8") if HISTORICO.exists() else "# Histórico de postagens\n\n| Data do post | Tema | Viral de origem | Vídeo | Status |\n|---|---|---|---|---|\n"
    linhas = texto.split("\n")
    for i, l in enumerate(linhas):
        if l.startswith("|") and stem in l:
            cel = [c.strip() for c in l.strip().strip("|").split("|")]
            if len(cel) >= 5:
                cel[0], cel[4] = quando, f"{status} (Ciello OS, {hoje():%d/%m})"
                linhas[i] = "| " + " | ".join(cel) + " |"
                break
    else:
        nova = f"| {quando} | {titulo(ler_roteiro(p), stem)} | — | midia/final/{stem}.mp4 | {status} (Ciello OS, {hoje():%d/%m}) |"
        fim_tabela = max((i for i, l in enumerate(linhas) if l.startswith("|")), default=len(linhas) - 1)
        linhas.insert(fim_tabela + 1, nova)
    HISTORICO.write_text("\n".join(linhas), encoding="utf-8")
    return {"ok": True, "saida": f"{stem}: {status.lower()} para {quando} (registrado no historico.md)"}


def slug(t: str) -> str:
    t = t.lower().translate(str.maketrans("áàâãéêíóôõúüç", "aaaaeeiooouuc"))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:40] or "post"


def novo_roteiro(data: str, gancho: str, itens: list[str], cta: str = "", pilar: str = "") -> dict:
    """Roteiro escrito à mão no Estúdio de Vídeo (sem o Claude): gancho, 2 a 4 itens e a chamada."""
    try:
        dia = dt.date.fromisoformat(str(data))
    except ValueError:
        return {"ok": False, "saida": "data inválida (use AAAA-MM-DD)"}
    gancho = re.sub(r"\s+", " ", str(gancho or "")).strip()[:160]
    itens = [re.sub(r"\s+", " ", str(i)).strip()[:240] for i in (itens or []) if str(i).strip()][:4]
    if not gancho or not itens:
        return {"ok": False, "saida": "escreva o gancho e pelo menos 1 item"}
    cta = re.sub(r"\s+", " ", str(cta or "")).strip()[:200] or "Salva pra testar depois e me chama no direct."
    nome = f"{dia.isoformat()}-{slug(gancho)}"
    arq = ROTEIROS / f"{nome}.json"
    if arq.exists():
        return {"ok": False, "saida": f"já existe um roteiro {nome}"}
    p = gancho.rstrip(".!?").split()
    meio = max(1, len(p) - 2)
    roteiro = {"_origem": "Estúdio de Vídeo do Ciello OS (escrito à mão)", "pilar": pilar,
               "capa": {"tag": "IA pro seu negócio", "linhas": [[" ".join(p[:meio]), "marfim"], [" ".join(p[meio:]), "ouro"]], "apoio": "Salva pra usar depois"},
               "scenes": [{"type": "hook", "say": gancho}] + [{"type": "item", "say": i} for i in itens] + [{"type": "cta", "say": cta}]}
    ROTEIROS.mkdir(parents=True, exist_ok=True)
    arq.write_text(json.dumps(roteiro, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"ok": True, "saida": f"roteiro {nome} criado", "post": nome}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("legenda"); s.add_argument("post"); s.add_argument("--forcar", action="store_true")
    s = sub.add_parser("agendado"); s.add_argument("post"); s.add_argument("--quando", default=""); s.add_argument("--publicado", action="store_true")
    a = ap.parse_args()
    if a.cmd == "legenda":
        r = gerar_legenda(a.post, a.forcar)
        print(r["saida"]); print(r.get("legenda", ""))
        return
    if a.cmd == "agendado":
        print(marcar_agendado(a.post, a.quando, "Publicado" if a.publicado else "Agendado")["saida"])
        return
    for p in quadro():
        marcas = " ".join(("✔" if p["etapas"][e] else "·") + ROTULOS[e][:3] for e in ETAPAS)
        print(f"{p['data']}  {p['slug'][:28]:28}  {marcas}  " + (f"próximo: {ROTULOS[p['proximo']]} ({p['dono']})" if p["proximo"] else "pronto"))
    for x in alertas():
        print("!", x)


if __name__ == "__main__":
    main()
