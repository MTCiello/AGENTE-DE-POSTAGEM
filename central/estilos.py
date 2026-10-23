"""Galeria de estilos do Estúdio de Vídeo: os 98 estilos do OPUSCAR 98 e a biblioteca do lemo-opuscar (MIT).

Você escolhe um estilo na galeria e o Claude produz o reel nele: lê o guia do estilo, monta o vídeo no HyperFrames
com a narração e os tempos do roteiro e deixa o rascunho em midia/estudio/<post>-<estilo>.mp4.
O catálogo fica em reels/estilos/ (gerado por reels/estilos/importar.py).

  python central/estilos.py listar                 # todos, por coleção
  python central/estilos.py ver o98-45             # o guia completo que o Claude segue
  python central/estilos.py ver watercolor
"""
import argparse
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "reels" / "estilos"
ESCOLHAS = RAIZ / "estado" / "estudio" / "estilos.json"
MINIATURAS = RAIZ / "central" / "escritorio" / "web" / "estilos"
POST = re.compile(r"20\d\d-\d\d-\d\d-[\w\-]{1,80}")


@lru_cache(maxsize=1)
def catalogo() -> dict:
    arq = PASTA / "catalogo.json"
    if not arq.exists():
        return {"capitulos": [], "familias": [], "opus98": [], "biblioteca": []}
    return json.loads(arq.read_text(encoding="utf-8"))


def achar(ident: str) -> dict | None:
    c = catalogo()
    return next((e for e in c["opus98"] + c["biblioteca"] if e["id"] == ident), None)


def colecao(ident: str) -> str:
    return "opus98" if str(ident).startswith("o98-") else "biblioteca"


def galeria() -> dict:
    """O que a tela precisa para montar a galeria (sem os prompts, que só o Claude lê)."""
    c = catalogo()
    mini = lambda i: f"/web/estilos/{i}.jpg" if (MINIATURAS / f"{i}.jpg").exists() else ""  # noqa: E731
    return {"capitulos": c["capitulos"], "familias": c["familias"], "filme": c.get("filme", ""),
            "opus98": [{"id": e["id"], "nome": e["nome"], "nome_en": e["nome_en"], "filme": e["filme"], "ano": e["ano"],
                        "capitulo": e["capitulo"], "render": e["render"], "tom": e["tom"], "tecnicas": e["tecnicas"],
                        "imagem": mini(e["id"])} for e in c["opus98"]],
            "biblioteca": [{"id": e["id"], "nome": e["nome"], "nome_en": e["nome_en"], "familia": e["familia"],
                            "usos": e["usos"], "imagem": mini(e["id"])} for e in c["biblioteca"]]}


def guia(ident: str) -> str:
    """O guia que o Claude segue: o prompt de estilo do Opus 98 ou o STYLE.md da biblioteca."""
    e = achar(ident)
    if not e:
        raise SystemExit(f"Estilo {ident} não existe. Veja: python central/estilos.py listar")
    if colecao(ident) == "biblioteca":
        return (PASTA / "biblioteca" / f"{ident}.md").read_text(encoding="utf-8")
    planos = ", ".join(dict.fromkeys(e["planos"]))
    return (f"# {e['nome_en']} ({e['nome']})\n\nOPUSCAR 98 · nº {e['n']} · feito para {e['filme']} ({e['ano']}) · {e['render']} · {e['tom']}\n\n"
            f"## Style prompt\n\n{e['prompt_en']}\n\n## What it is\n\n{e['descricao_en']}\n\n"
            f"## Techniques blended\n\n" + "\n".join(f"- {t}" for t in e["tecnicas"]) +
            (f"\n\n## Shot grammar used in the film\n\n{planos}\n" if planos else "\n"))


# ---------------------------------------------------------------- escolha por roteiro
def escolhas() -> dict:
    try:
        return json.loads(ESCOLHAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def escolher(post: str, ident: str):
    d = escolhas()
    d[post] = ident
    ESCOLHAS.parent.mkdir(parents=True, exist_ok=True)
    ESCOLHAS.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def pedido(ident: str, post: str = "", tema: str = "", empresa: str = "a empresa", data: str = "") -> str:
    """O pedido que vai para o Claude Code quando você escolhe um estilo na galeria."""
    e = achar(ident)
    if not e:
        raise ValueError("estilo inválido")
    nome = f"\"{e['nome']}\" ({e['nome_en']})"
    origem = f"Opus 98, nº {e['n']}" if colecao(ident) == "opus98" else f"biblioteca, {e['familia']}"
    if post:
        slug = post[11:]
        alvo = f"o reel do roteiro roteiros/{post}.json"
        passo_roteiro = (f"1. Narração: se audio/{slug}/narracao.wav ainda não existe, rode `python central/voz.py roteiros/{post}.json --saida audio/{slug}` "
                         f"(sem --motor: vale a voz do Estúdio de Voz). Os tempos de cada fala ficam em audio/{slug}/tempos.json.")
        saida = f"midia/estudio/{post}-{ident}.mp4"
    else:
        slug = "<slug>"
        alvo = f"um reel sobre: {tema}"
        passo_roteiro = (f"1. Roteiro e narração: escreva o roteiro em roteiros/{data or 'AAAA-MM-DD'}-<slug>.json (<post> daqui em diante) no formato do AGENTE.md "
                         "(gancho, 2 a 4 itens, CTA, 18–28 s, fatos checados), me mostre para eu aprovar e só então narre com "
                         "`python central/voz.py roteiros/<post>.json --saida audio/<slug>`.")
        saida = f"midia/estudio/<post>-{ident}.mp4"
    return f"""Produza {alvo} no estilo {nome} da galeria de estilos ({origem}) para a {empresa}.

Delegue ao agente produtor-video com a ferramenta Task (descrição começando com "produtor-video:"), para ele aparecer trabalhando no escritório. Passe a ele este pedido inteiro.

O estilo:
- Guia do estilo: `python central/estilos.py ver {ident}`. É a regra fixa (visual, cor, tipografia, movimento, câmera, som). Siga tudo.
- Direção: reels/estilos/DIRECTOR.md (história, ritmo, câmera e a checagem antes de entregar). Técnica: reels/estilos/TECHNIQUE.md §2 e §3 (a imagem é uma função do tempo; uma linha do tempo comanda tudo). Esses guias vêm do lemo-opuscar: onde falam das ferramentas deles (core/, Kokoro, mix), use as nossas abaixo.
- Pegue só a gramática visual. Não copie a história, os personagens (como o Clawd), as cenas nem as obras citadas como referência, e não use marca de terceiros.

Passos:
{passo_roteiro}
2. Projeto: `python central/estudio_video.py montar {post or '<post>'}` monta estado/estudio/{post or '<post>'}/ com a narração, a trilha, as fontes, o GSAP e um index.html com os tempos certos. Copie a pasta para estado/estudio/{post or '<post>'}-{ident}/ e reescreva o index.html no estilo: mesmo texto, mesma ordem e mesmos tempos da fala, vertical 1080×1920 a 30 fps (o estilo nasceu em 16:9: recomponha para 9:16, com o assunto no terço central), legenda sincronizada e legível no celular, e o cartão final com a chamada do roteiro. Desenhe tudo em código (canvas, SVG, CSS, WebGL); nada de vídeo gerado por IA nem banco de imagens.
3. Prova do visual: antes do vídeo inteiro, faça um rascunho (`python central/estudio_video.py renderizar estado/estudio/{post or '<post>'}-{ident} {saida} --rascunho`), tire 2 ou 3 quadros com o ffmpeg (gancho, meio e final), olhe e compare com o guia do estilo. Corrija o que destoar.
4. Vídeo: `python central/estudio_video.py renderizar estado/estudio/{post or '<post>'}-{ident} {saida}` e depois `python central/analisar_video.py {saida}`: precisa dar aprovado.
5. Não publique, não agende e não copie para midia/final/. No fim, me diga em poucas linhas onde está o vídeo e o que você decidiu no visual. Eu confiro a prévia no Estúdio de Vídeo e clico em Usar como vídeo final."""


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("listar")
    s = sub.add_parser("ver")
    s.add_argument("estilo")
    a = ap.parse_args()
    if a.cmd == "ver":
        print(guia(a.estilo))
        return
    c = catalogo()
    print("Opus 98 (um estilo por vencedor do Oscar de Melhor Filme):")
    for e in c["opus98"]:
        print(f"  {e['id']:8} {e['nome']}  ·  {e['filme']} ({e['ano']})")
    print("\nBiblioteca:")
    for e in c["biblioteca"]:
        print(f"  {e['id']:20} {e['nome']}  ·  {e['familia']}")


if __name__ == "__main__":
    main()
