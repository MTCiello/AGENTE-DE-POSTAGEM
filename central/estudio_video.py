"""Estúdio de Vídeo: o roteiro vira reel pronto, sem escrever código, com o HyperFrames (Apache-2.0, HTML → MP4).

Passos (`gerar` faz todos):
  1. narração  central/voz.py com a voz escolhida no Estúdio de Voz (pula se audio/<slug>/narracao.wav já existe)
  2. montar    um projeto HyperFrames em estado/estudio/<post>/: cada cena com título, lista e legenda sincronizada
               com a fala (tempos de audio/<slug>/tempos.json), a marca da empresa (marca/) e a trilha
  3. render    `hyperframes render` (Chrome sem janela + ffmpeg): já sai com voz e trilha mixadas
               -> midia/estudio/<post>-<modelo>.mp4 (rascunho; "usar" copia para midia/final/)

  python central/estudio_video.py gerar 2026-10-29-comandos-plano --modelo escuro
  python central/estudio_video.py montar 2026-10-29-comandos-plano     # só o projeto (para abrir no Studio do HyperFrames)
  python central/estudio_video.py usar 2026-10-29-comandos-plano --modelo escuro
  python central/estudio_video.py modelos

Funciona com qualquer roteiro de roteiros/ (campos usados: type, say, kicker/tag, lines/title/text, items/answer/cards).
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from empresa import perfil  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
ROTEIROS = RAIZ / "roteiros"
TRABALHO = RAIZ / "estado" / "estudio"
RASCUNHOS = RAIZ / "midia" / "estudio"
FONTES = RAIZ / "central" / "escritorio" / "web" / "fontes"
TRILHA = RAIZ / "midia" / "trilhas" / "trilha-01.mp3"
GSAP = RAIZ / "reels" / "node_modules" / "gsap" / "dist" / "gsap.min.js"  # local: renderiza mesmo sem internet
VERSAO_HF = "0.8.186"
LARGURA, ALTURA = 1080, 1920
PAUSA = 0.22  # a mesma do voz.py

MODELOS = {
    "escuro": {"nome": "Escuro", "descricao": "Azul profundo com títulos em marfim e ouro (o padrão da marca)",
               "fundo": "#13213A", "fundo2": "#263A59", "texto": "#F8F4E8", "cinza": "#8C9AB3", "ouro": "#E0A81C", "logo": "logo-simbolo-marfim.svg"},
    "claro": {"nome": "Claro", "descricao": "Marfim com títulos em carvão e ouro, mais leve para dicas e listas",
              "fundo": "#F8F4E8", "fundo2": "#EFE7D2", "texto": "#161616", "cinza": "#8C877C", "ouro": "#C98F0A", "logo": "logo-simbolo-carvao.svg"},
}
ROTULO_TIPO = {"hook": "", "cta": "Salva pra testar depois", "ponte": "", "comando": "Comando", "item": "", "prompt": "Teste"}


# ---------------------------------------------------------------- roteiro → cenas
def _segmentos(v):
    """[["Texto", "ouro"], ...] | "Texto" | ["a", "b"] → [(texto, cor)]."""
    if not v:
        return []
    if isinstance(v, str):
        return [(v, "marfim")]
    out = []
    for x in v:
        if isinstance(x, (list, tuple)) and x:
            out.append((str(x[0]), str(x[1]) if len(x) > 1 else "marfim"))
        elif isinstance(x, str):
            out.append((x, "marfim"))
    return out


LIGACOES = {"a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos", "e", "em", "no", "na", "nos", "nas", "por", "pra", "pro",
            "para", "com", "que", "se", "ao", "à", "sem", "seu", "sua", "meu", "minha", "mais", "muito"}


def _ouro_no_fim(palavras):
    if len(palavras) <= 2:
        return [(" ".join(palavras), "ouro")]
    return [(" ".join(palavras[:-2]), "marfim"), (" ".join(palavras[-2:]), "ouro")]


def _titulo_da_fala(fala: str, tipo: str = ""):
    """Sem título no roteiro, tira um da fala: até 7 palavras, as 2 últimas em ouro. Devolve (título, rótulo).
    "Primeiro: responda como atendente..." → rótulo "Primeiro", título "responda como atendente da minha loja"."""
    rotulo = ""
    m = re.match(r"^\s*([\wÀ-ú]+(?: [\wÀ-ú]+)?):\s+(.*)", fala)
    if m and len(m.group(1).split()) <= 2:
        rotulo, fala = m.group(1), m.group(2)
    frases = [f.strip(" .!?") for f in re.split(r"(?<=[.!?])\s+", fala.strip()) if f.strip(" .!?")]
    if not frases:
        return [], rotulo
    if tipo in ("hook", "cta") or rotulo:
        escolhida = re.split(r"[,;]\s", frases[0])[0]
    else:  # ponte e itens: a frase mais curta costuma ser a ideia ("É o nosso CRM")
        curtas = [f for f in frases if 2 <= len(f.split()) <= 8]
        escolhida = min(curtas, key=lambda f: len(f.split())) if curtas else re.split(r"[,;]\s", frases[0])[0]
    palavras = escolhida.split()
    corte = palavras[:8 if tipo == "hook" else 7]
    while len(corte) < len(palavras) and len(corte) > 2 and corte[-1].lower().strip(",") in LIGACOES:
        corte.pop()  # "orçamento com" → "orçamento": título não termina em preposição
    return _ouro_no_fim([w.strip(",") for w in corte]), rotulo


def _itens(c):
    for k in ("items", "answer", "results", "cards", "lista"):
        v = c.get(k)
        if isinstance(v, list) and v:
            out = []
            for x in v[:4]:
                if isinstance(x, dict):
                    out.append(str(x.get("title") or x.get("text") or x.get("titulo") or next(iter(x.values()), "")))
                elif isinstance(x, (list, tuple)):
                    out.append(" ".join(str(y) for y in x if isinstance(y, str))[:80])
                else:
                    out.append(str(x))
            return [i for i in out if i.strip()]
    return []


def normalizar(roteiro: dict) -> list[dict]:
    cenas = []
    for c in roteiro.get("scenes", []):
        fala = re.sub(r"\s+", " ", str(c.get("say") or "")).strip()
        titulo = _segmentos(c.get("lines")) or _segmentos(c.get("title")) or (
            [(str(c["text"]), "marfim")] + ([(str(c["highlight"]), "ouro")] if c.get("highlight") else []) if c.get("text") else [])
        rotulo = ""
        if not titulo:
            titulo, rotulo = _titulo_da_fala(fala, c.get("type", ""))
        cenas.append({"tipo": c.get("type", ""), "kicker": str(c.get("kicker") or c.get("tag") or rotulo or ROTULO_TIPO.get(c.get("type", ""), "")),
                      "titulo": titulo, "itens": _itens(c), "fala": fala})
    return cenas


def tempos(slug: str, cenas: list[dict]) -> tuple[list[tuple[float, float]], float]:
    """Início e fim de cada cena (da narração real, se já existe) e a duração total."""
    arq = RAIZ / "audio" / slug / "tempos.json"
    if arq.exists():
        t = json.loads(arq.read_text(encoding="utf-8"))
        linhas = t.get("linhas") or []
        if len(linhas) == len(cenas):
            total = float(t.get("tempos", {}).get("total") or linhas[-1]["to"] + 0.8)
            return [(float(l["from"]), float(l["to"])) for l in linhas], total
    out, t0 = [], 0.0
    for c in cenas:  # estimativa: 15 caracteres por segundo, como o motor de teste do voz.py
        d = 0.35 + max(1, len(c["fala"])) / 15
        out.append((round(t0, 2), round(t0 + d, 2)))
        t0 += d + PAUSA
    return out, round(out[-1][1] + 0.8, 2) if out else 3.0


def legendas(fala: str, ini: float, fim: float, palavras=4):
    """A fala em pedaços de até `palavras`, com o tempo dividido pelo tamanho de cada pedaço."""
    p = fala.split()
    pedacos = [" ".join(p[i:i + palavras]) for i in range(0, len(p), palavras)] or [""]
    total = sum(len(x) + 1 for x in pedacos)
    out, t = [], ini
    for x in pedacos:
        d = (fim - ini) * (len(x) + 1) / total
        out.append((x, round(t, 3), round(d, 3)))
        t += d
    return out


# ---------------------------------------------------------------- projeto HyperFrames
def _cor(nome, m):
    return {"ouro": m["ouro"], "cinza": m["cinza"]}.get(nome, m["texto"])


def html_projeto(cenas, janelas, total, modelo="escuro", narracao=True, trilha=True, gsap="gsap.min.js", logo=True) -> str:
    m = MODELOS[modelo]
    e = html.escape
    secoes, falas, anim = [], [], []
    for i, (c, (ini, fim)) in enumerate(zip(cenas, janelas)):
        prox = janelas[i + 1][0] if i + 1 < len(janelas) else total
        dur = round(prox - ini, 3)
        titulo = "".join(f'<span style="color:{_cor(cor, m)}">{e(t)}</span> ' for t, cor in c["titulo"])
        itens = "".join(f'<li><b>{n}</b>{e(t)}</li>' for n, t in enumerate(c["itens"], 1))
        classe = "cena final" if c["tipo"] == "cta" else "cena"
        secoes.append(f'<section id="c{i}" class="clip {classe}" data-start="{ini:.3f}" data-duration="{dur:.3f}" data-track-index="1">'
                      f'<div class="kicker">{e(c["kicker"])}</div><h1 class="titulo">{titulo}</h1>'
                      + (f'<ol class="itens">{itens}</ol>' if itens else "")
                      + ('<img class="selo" src="logo.svg" alt="">' if c["tipo"] == "cta" and logo else "") + "</section>")
        anim.append(f'tl.from("#c{i} .kicker", {{opacity: 0, y: 24, duration: 0.3, ease: "power2.out"}}, {ini + 0.05:.3f});')
        anim.append(f'tl.from("#c{i} .titulo span", {{opacity: 0, y: 70, duration: 0.45, stagger: 0.12, ease: "power3.out"}}, {ini + 0.12:.3f});')
        if c["itens"]:
            passo = max(0.25, (fim - ini - 0.6) / (len(c["itens"]) + 1))
            for n in range(len(c["itens"])):
                anim.append(f'tl.from("#c{i} .itens li:nth-child({n + 1})", {{opacity: 0, x: -60, duration: 0.35, ease: "power2.out"}}, {ini + 0.5 + passo * n:.3f});')
        if c["tipo"] == "cta":
            anim.append(f'tl.from("#c{i} .selo", {{opacity: 0, scale: 0.6, duration: 0.5, ease: "back.out(1.7)"}}, {ini + 0.3:.3f});')
        for j, (texto, t, d) in enumerate(legendas(c["fala"], ini, fim)):
            falas.append(f'<div id="l{i}_{j}" class="clip legenda" data-start="{t:.3f}" data-duration="{d:.3f}" data-track-index="2">{e(texto)}</div>')
    audio = ""
    if narracao:
        audio += f'<audio data-start="0" data-duration="{total:.3f}" data-track-index="3" src="narracao.wav"></audio>'
    if trilha:
        audio += (f'<audio data-start="0" data-duration="{total:.3f}" data-track-index="4" data-volume="0.12" data-fade-in="0.5" '
                  f'data-fade-out="1.2" src="trilha.mp3"></audio>')
    return f"""<!doctype html>
<html lang="pt-BR" data-resolution="portrait">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width={LARGURA}, height={ALTURA}">
<script src="{gsap}"></script>
<style>
@font-face {{ font-family: Oswald; font-weight: 600; src: url(fontes/oswald-latin-600-normal.woff2) format("woff2"); }}
@font-face {{ font-family: Inter; font-weight: 600; src: url(fontes/inter-latin-600-normal.woff2) format("woff2"); }}
@font-face {{ font-family: Inter; font-weight: 700; src: url(fontes/inter-latin-700-normal.woff2) format("woff2"); }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {LARGURA}px; height: {ALTURA}px; overflow: hidden; background: {m['fundo']}; }}
#root {{ position: relative; width: 100%; height: 100%; font-family: Inter, sans-serif; color: {m['texto']};
  background: radial-gradient(1200px 900px at 75% 20%, {m['fundo2']}, transparent 65%), {m['fundo']}; }}
.marca {{ position: absolute; top: 90px; left: 80px; display: flex; align-items: center; gap: 18px; font: 600 34px Oswald, sans-serif; letter-spacing: 6px; }}
.marca img {{ width: 72px; }}
.clip {{ position: absolute; }}
.cena {{ inset: 0; padding: 0 80px; display: flex; flex-direction: column; justify-content: center; gap: 36px; padding-bottom: 260px; }}
.kicker {{ font: 700 34px Inter, sans-serif; letter-spacing: 6px; text-transform: uppercase; color: {m['ouro']}; }}
.titulo {{ font: 600 132px/1.02 Oswald, sans-serif; letter-spacing: -1px; text-transform: uppercase; }}
.titulo span {{ display: inline-block; }}
.itens {{ list-style: none; display: flex; flex-direction: column; gap: 22px; }}
.itens li {{ display: flex; gap: 26px; align-items: baseline; font: 600 48px/1.2 Inter, sans-serif; }}
.itens b {{ font: 600 54px Oswald, sans-serif; color: {m['ouro']}; min-width: 50px; }}
.final {{ align-items: flex-start; }} .selo {{ width: 190px; margin-top: 20px; }}
.legenda {{ left: 80px; right: 80px; bottom: 300px; font: 700 54px/1.25 Inter, sans-serif; text-align: center; color: {m['texto']};
  padding: 18px 28px; border-radius: 22px; background: color-mix(in srgb, {m['fundo']} 70%, transparent); }}
#barra {{ position: absolute; left: 0; bottom: 0; height: 14px; width: 0; background: {m['ouro']}; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="{LARGURA}" data-height="{ALTURA}">
<div class="marca">{'<img src="logo.svg" alt="">' if logo else ""}{e(perfil()["nome"].upper())}</div>
{chr(10).join(secoes)}
{chr(10).join(falas)}
<div id="barra"></div>
{audio}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
tl.fromTo("#barra", {{ width: 0 }}, {{ width: {LARGURA}, duration: {total:.3f}, ease: "none" }}, 0);
{chr(10).join(anim)}
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body>
</html>
"""


def montar(post: str, modelo="escuro", trilha=True) -> Path:
    post = Path(post).stem
    roteiro = json.loads((ROTEIROS / f"{post}.json").read_text(encoding="utf-8"))
    slug = post[11:]
    cenas = normalizar(roteiro)
    if not cenas:
        raise SystemExit("O roteiro não tem cenas.")
    janelas, total = tempos(slug, cenas)
    pasta = TRABALHO / post
    if pasta.exists():
        shutil.rmtree(pasta)
    (pasta / "fontes").mkdir(parents=True)
    for f in ("oswald-latin-600-normal.woff2", "inter-latin-600-normal.woff2", "inter-latin-700-normal.woff2"):
        if (FONTES / f).exists():
            shutil.copy(FONTES / f, pasta / "fontes" / f)
    logo = RAIZ / "marca" / MODELOS[modelo]["logo"]  # o logo da empresa (fora do git); sem ele, só o nome
    if logo.exists():
        shutil.copy(logo, pasta / "logo.svg")
    narr = RAIZ / "audio" / slug / "narracao.wav"
    if narr.exists():
        shutil.copy(narr, pasta / "narracao.wav")
    usar_trilha = trilha and TRILHA.exists()
    if usar_trilha:
        shutil.copy(TRILHA, pasta / "trilha.mp3")
    if GSAP.exists():
        shutil.copy(GSAP, pasta / "gsap.min.js")
    gsap = "gsap.min.js" if GSAP.exists() else "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
    (pasta / "index.html").write_text(html_projeto(cenas, janelas, total, modelo, narr.exists(), usar_trilha, gsap, logo.exists()), encoding="utf-8")
    (pasta / "hyperframes.json").write_text(json.dumps({"name": post}), encoding="utf-8")
    (pasta / "meta.json").write_text(json.dumps({"id": post, "name": post}), encoding="utf-8")
    print(f"projeto montado: {pasta} · {len(cenas)} cenas · {total:.1f}s" + ("" if narr.exists() else " · sem narração (tempos estimados)"))
    return pasta


# ---------------------------------------------------------------- render
def comando_hyperframes() -> list[str]:
    """O CLI do HyperFrames instalado em reels/ (npm install); senão, pelo npx na versão fixada."""
    local = RAIZ / "reels" / "node_modules" / ".bin" / ("hyperframes.cmd" if os.name == "nt" else "hyperframes")
    if local.exists():
        return [str(local)]
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        raise SystemExit("Falta o Node.js (npx). Rode o instalar.cmd.")
    return [npx, "--yes", f"hyperframes@{VERSAO_HF}"]


def renderizar(pasta: Path, saida: Path, qualidade="looks"):
    saida.parent.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "HYPERFRAMES_SKIP_SKILLS": "1", "HYPERFRAMES_TELEMETRY": "0", "DO_NOT_TRACK": "1"}
    cmd = [*comando_hyperframes(), "render", str(pasta), "-o", str(saida), "-q", qualidade, "--quiet"]
    print(" ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=pasta, env=env)
    if r.returncode or not saida.exists():
        raise SystemExit(f"O HyperFrames não gerou o vídeo (código {r.returncode}). Rode 'npx hyperframes doctor' na pasta reels para ver o que falta.")
    print(f"vídeo: {saida}")


def narrar(post: str, motor=None):
    slug = Path(post).stem[11:]
    if (RAIZ / "audio" / slug / "narracao.wav").exists():
        print("narração: já existe")
        return
    cmd = [sys.executable, str(RAIZ / "central" / "voz.py"), str(ROTEIROS / f"{Path(post).stem}.json"), "--saida", str(RAIZ / "audio" / slug)]
    if motor:
        cmd.append(f"--motor={motor}")
    print("narração:", " ".join(cmd[1:]), flush=True)
    r = subprocess.run(cmd, cwd=RAIZ)
    if r.returncode:
        raise SystemExit("A narração não saiu. Confira o Estúdio de Voz (voz instalada e escolhida).")


def rascunho(post: str, modelo: str) -> Path:
    return RASCUNHOS / f"{Path(post).stem}-{modelo}.mp4"


def usar(post: str, modelo: str) -> Path:
    origem = rascunho(post, modelo)
    if not origem.exists():
        raise SystemExit("Gere o vídeo antes.")
    destino = RAIZ / "midia" / "final" / f"{Path(post).stem}.mp4"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(origem, destino)
    print(f"vídeo final: {destino}")
    return destino


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome in ("gerar", "montar", "usar"):
        s = sub.add_parser(nome)
        s.add_argument("post", help="nome do roteiro (ex.: 2026-10-29-comandos-plano)")
        s.add_argument("--modelo", choices=list(MODELOS), default="escuro")
        if nome != "usar":
            s.add_argument("--sem-trilha", action="store_true")
        if nome == "gerar":
            s.add_argument("--motor", help="motor da narração (padrão: o do Estúdio de Voz)")
            s.add_argument("--rascunho", action="store_true", help="render rápido (qualidade draft)")
    sub.add_parser("modelos")
    a = ap.parse_args()
    if a.cmd == "modelos":
        for k, m in MODELOS.items():
            print(f"{k:8} {m['nome']}: {m['descricao']}")
        return
    if not (ROTEIROS / f"{Path(a.post).stem}.json").exists():
        sys.exit(f"Roteiro {a.post} não encontrado em roteiros/.")
    if a.cmd == "usar":
        usar(a.post, a.modelo)
        return
    if a.cmd == "gerar":
        narrar(a.post, a.motor)
    pasta = montar(a.post, a.modelo, not a.sem_trilha)
    if a.cmd == "gerar":
        renderizar(pasta, rascunho(a.post, a.modelo), "draft" if a.rascunho else "looks")


if __name__ == "__main__":
    from status import trabalhando
    with trabalhando("produtor-video", "Estúdio de Vídeo"):
        main()
