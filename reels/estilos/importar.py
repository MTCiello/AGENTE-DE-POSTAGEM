"""Importa a galeria de estilos do lemo-opuscar (MIT, github.com/lemomo-ai/lemo-opuscar) para o Estúdio de Vídeo.

Duas coleções:
  - Opus 98: os 98 estilos do filme OPUSCAR 98 (um por vencedor do Oscar de Melhor Filme, 1927–2025), cada um com
    o prompt de estilo reutilizável (styleboard/opuscar98_styles.json);
  - Biblioteca: os estilos com guia completo (styles/<slug>/STYLE.md).

Gera reels/estilos/catalogo.json, reels/estilos/biblioteca/<slug>.md, copia DIRECTOR.md e TECHNIQUE.md e grava as
miniaturas em central/escritorio/web/estilos/ (precisa do ffmpeg). Os nomes em português vêm de nomes-pt.json:
estilo novo sem nome em português aparece com o nome em inglês até alguém traduzir.

  git clone --depth 1 https://github.com/lemomo-ai/lemo-opuscar /tmp/opuscar
  curl -LO https://github.com/lemomo-ai/lemo-opuscar/releases/download/films/opuscar98.mp4
  python reels/estilos/importar.py /tmp/opuscar --video opuscar98.mp4
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
MINIATURAS = RAIZ / "central" / "escritorio" / "web" / "estilos"
# o quadro do filme tem tarjas com o título em cima e embaixo: recorta o meio em 16:9
RECORTE = "crop=1422:800:249:142,scale=400:-2"


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def importar(origem: Path, video: Path | None):
    pt = json.loads((AQUI / "nomes-pt.json").read_text(encoding="utf-8"))
    o98 = json.loads((origem / "styleboard" / "opuscar98_styles.json").read_text(encoding="utf-8"))
    MINIATURAS.mkdir(parents=True, exist_ok=True)

    opus = []
    for f in o98["films"]:
        ident = f"o98-{f['no']:02d}"
        opus.append({"id": ident, "n": f["no"], "ano": f["year"], "filme": f["title"], "capitulo": f["chapter"],
                     "nome": pt["opus98"].get(str(f["no"]), f["style_en"]), "nome_en": f["style_en"],
                     "render": f["render"], "tom": f["dim"], "tecnicas": f["blend_en"],
                     "descricao_en": f["desc_en"], "prompt_en": f["prompt_en"],
                     "planos": [s["cam"] for s in f.get("shots", [])]})
        if video:
            ffmpeg("-ss", str(f["frame_sec"]), "-i", str(video), "-frames:v", "1", "-vf", RECORTE, "-q:v", "6",
                   str(MINIATURAS / f"{ident}.jpg"))

    (AQUI / "biblioteca").mkdir(exist_ok=True)
    bib = []
    for s in json.loads((origem / "styleboard" / "catalog.json").read_text(encoding="utf-8")):
        slug = s["slug"]
        nome, usos = pt["biblioteca"].get(slug, [s["en"], s["uses"]])
        shutil.copyfile(origem / "styles" / slug / "STYLE.md", AQUI / "biblioteca" / f"{slug}.md")
        bib.append({"id": slug, "nome": nome, "nome_en": s["en"], "familia": pt["familias"].get(s["cat_en"], s["cat_en"]),
                    "usos": usos, "exemplo_en": s["line"]})
        quadro = origem / "docs" / "frames" / f"{slug}.jpg"
        if quadro.exists():
            ffmpeg("-i", str(quadro), "-vf", "scale=400:-2", "-q:v", "6", str(MINIATURAS / f"{slug}.jpg"))

    for doc in ("DIRECTOR.md", "TECHNIQUE.md"):
        shutil.copyfile(origem / doc, AQUI / doc)
    catalogo = {"fonte": "https://github.com/lemomo-ai/lemo-opuscar", "filme": o98["film"],
                "capitulos": [{"id": c["id"], "nome": pt["capitulos"].get(c["id"], c["en"]), "anos": c["years"]} for c in o98["chapters"]],
                "familias": list(dict.fromkeys(b["familia"] for b in bib)), "opus98": opus, "biblioteca": bib}
    (AQUI / "catalogo.json").write_text(json.dumps(catalogo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(opus)} estilos do Opus 98 e {len(bib)} da biblioteca")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("origem", type=Path, help="pasta do lemo-opuscar clonado")
    ap.add_argument("--video", type=Path, help="opuscar98.mp4 (para as miniaturas do Opus 98)")
    a = ap.parse_args()
    importar(a.origem, a.video)
