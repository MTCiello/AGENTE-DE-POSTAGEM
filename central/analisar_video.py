"""Mede o ritmo de um vídeo: o "oráculo" que avisa se o reel parece slide antes de alguém assistir.

Serve para estudar uma referência e para conferir os nossos reels. Só precisa de ffmpeg e numpy.

  python central/analisar_video.py referencia.mp4
  python central/analisar_video.py midia/final/x.mp4 --ref referencia.mp4   # compara com a referência

Mede:
  cortes        trocas bruscas de imagem (diferença entre quadros muito acima da vizinhança)
  planos        duração de cada trecho entre cortes; variação boa = maior ÷ menor ≥ 4
  parado        % do tempo com fundo calmo (só elementos pequenos se mexendo); a referência de 40 s feita no Claude fica em ~60%
  viradas       picos de movimento (transições grandes) a cada 10 s; a referência tem ~2,5
  energia       movimento por segundo, para ver onde o vídeo acelera e onde segura
  carrega       nos cortes, quanto da imagem continua (cor e composição); alto = transição que carrega
"""
import argparse
import json
import subprocess
import sys

import numpy as np

W, H = 72, 128  # miniatura vertical; basta para ritmo


def quadros(caminho, fps):
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                      "stream=width,height:stream_side_data=rotation:format=duration", "-of", "json", caminho],
                                     capture_output=True, text=True, check=True).stdout)
    dur = float(info["format"]["duration"])
    bruto = subprocess.run(["ffmpeg", "-v", "error", "-i", caminho, "-vf", f"fps={fps},scale={W}:{H},format=gray",
                            "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    q = np.frombuffer(bruto, np.uint8).reshape(-1, H, W).astype(np.float32)
    return q, dur


def analisar(caminho, fps=30):
    q, dur = quadros(caminho, fps)
    d = np.abs(np.diff(q, axis=0)).mean(axis=(1, 2))  # movimento entre quadros (0–255)
    viz = np.array([np.median(d[max(0, i - 8):i + 9]) for i in range(len(d))])
    cortes = [i + 1 for i in range(len(d)) if d[i] > 18 and d[i] > 4 * (viz[i] + 1)]
    # junta cortes colados (fade de 2–3 quadros)
    unicos = []
    for c in cortes:
        if not unicos or c - unicos[-1] > 3:
            unicos.append(c)
    limites = [0] + unicos + [len(q)]
    planos = [round((b - a) / fps, 2) for a, b in zip(limites, limites[1:]) if b > a]
    parado = float((d < 0.6).mean() * 100)
    energia = [round(float(d[i:i + fps].mean()), 2) for i in range(0, len(d), fps)]
    viradas = sum(1 for i, e in enumerate(energia) if e > 3 and (i == 0 or energia[i - 1] <= 3))
    carrega = []
    for c in unicos:
        a, b = q[max(0, c - 2)], q[min(len(q) - 1, c + 1)]
        ha, hb = np.histogram(a, 32, (0, 255))[0], np.histogram(b, 32, (0, 255))[0]
        cor = float(np.minimum(ha, hb).sum() / max(1, ha.sum()))           # paleta que continua
        comp = float(1 - np.abs(a - b).mean() / 128)                        # composição que continua
        carrega.append(round(0.5 * cor + 0.5 * max(0.0, comp), 2))
    return {"arquivo": caminho, "duracao_s": round(dur, 2), "cortes": len(unicos),
            "cortes_s": [round(c / fps, 2) for c in unicos], "planos_s": planos,
            "variacao_planos": round(max(planos) / max(0.04, min(planos)), 1) if planos else 0,
            "plano_mediano_s": round(float(np.median(planos)), 2) if planos else 0,
            "parado_pct": round(parado, 1), "energia_por_s": energia,
            "viradas_10s": round(10 * viradas / max(1.0, dur), 1),
            "carrega_media": round(float(np.mean(carrega)), 2) if carrega else 1.0}


def barra(v, mx, n=24):
    return "█" * int(round(n * v / mx)) if mx else ""


def imprimir(r):
    print(f"\n{r['arquivo']}  ·  {r['duracao_s']} s")
    print(f"  cortes: {r['cortes']}  em {r['cortes_s'][:20]}{' …' if len(r['cortes_s']) > 20 else ''}")
    print(f"  planos: mediana {r['plano_mediano_s']} s · variação {r['variacao_planos']}x (bom ≥ 4x)")
    print(f"  parado: {r['parado_pct']}% (bom: 35–75%) · viradas: {r['viradas_10s']} a cada 10 s (bom: 1,5–4) · carrega nos cortes: {r['carrega_media']} (bom ≥ 0.5)")
    mx = max(r["energia_por_s"] or [1])
    print("  energia por segundo:")
    for s, e in enumerate(r["energia_por_s"]):
        print(f"   {s:3d}s {barra(e, mx)} {e}")


def veredito(r, ref=None):
    """Limites calibrados no reel de referência feito no Claude (40 s, 4 cortes, ~60% de fundo calmo, ~2,5 viradas a cada 10 s)."""
    falhas = []
    if r["variacao_planos"] < 4 and r["cortes"] >= 3:
        falhas.append("planos com duração parecida demais (vira slide): varie de 0,3 s a 2,5 s")
    if r["parado_pct"] < 35:
        falhas.append("agitado demais: deixe o fundo calmo e anime só os elementos")
    if r["parado_pct"] > 75:
        falhas.append("parado demais: falta movimento entre as ideias")
    if not 1.5 <= r["viradas_10s"] <= 4:
        falhas.append(f"{r['viradas_10s']} viradas a cada 10 s: o bom é uma transição grande a cada 3–5 s")
    if r["cortes"] >= 3 and r["carrega_media"] < 0.5:
        falhas.append("cortes que trocam tudo: deixe algo continuar de uma cena para a outra")
    if r["cortes"] / max(1.0, r["duracao_s"]) > 0.25:
        falhas.append("cortes secos demais: prefira transições que transformam um elemento no próximo")
    if ref:
        print(f"\nreferência: parado {ref['parado_pct']}% · viradas {ref['viradas_10s']}/10 s · cortes {ref['cortes']} em {ref['duracao_s']} s")
    print("\nVEREDITO:", "aprovado" if not falhas else "ajustar")
    for f in falhas:
        print("  -", f)
    return not falhas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--ref", help="vídeo de referência para comparar")
    ap.add_argument("--json", help="grava o resultado em JSON")
    a = ap.parse_args()
    r = analisar(a.video)
    imprimir(r)
    ref = None
    if a.ref:
        ref = analisar(a.ref)
        imprimir(ref)
    ok = veredito(r, ref)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(json.dumps({"video": r, "ref": ref}, ensure_ascii=False, indent=1))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
