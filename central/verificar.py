"""Verificação do assistente: roda cada função de ponta a ponta e diz o que está pronto.

  python central/verificar.py            # tudo (inclui radar na internet e capa no Remotion)
  python central/verificar.py --rapido   # pula o que depende de internet ou demora

Resultado no terminal e em estado/verificacao.txt (mande esse arquivo se algo falhar).
"""
import argparse
import importlib.util
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PY = sys.executable
OK, AVISO, FALHA = "OK", "AVISO", "FALHA"
resultados = []


def rodar(cmd, cwd=RAIZ, timeout=600):
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env)
    return r.returncode, (r.stdout + r.stderr).strip()


def checar(nome, func):
    t0 = time.time()
    try:
        estado, msg = func()
    except Exception as e:  # um teste quebrado não derruba os outros
        estado, msg = FALHA, f"{type(e).__name__}: {e}"
    resultados.append((nome, estado, msg, time.time() - t0))
    marca = {OK: "[ok]   ", AVISO: "[aviso]", FALHA: "[FALHA]"}[estado]
    print(f"{marca} {nome}: {msg.splitlines()[0][:150] if msg else ''}", flush=True)


def ultima(txt, n=3):
    return " | ".join(l for l in txt.splitlines()[-n:] if l.strip())


# ---------------------------------------------------------------- verificações

def python_versao():
    v = sys.version_info
    if v < (3, 10):
        return FALHA, f"Python {v.major}.{v.minor}: precisa do 3.10 ou mais novo (recomendado 3.11)"
    return OK, f"Python {v.major}.{v.minor}.{v.micro} ({platform.system()})"


def ffmpeg():
    falta = [p for p in ("ffmpeg", "ffprobe") if not shutil.which(p)]
    if falta:
        return FALHA, "ffmpeg não encontrado: winget install Gyan.FFmpeg (depois abra um terminal novo)"
    _, out = rodar(["ffmpeg", "-version"])
    return OK, out.splitlines()[0]


def node():
    if not shutil.which("node"):
        return FALHA, "Node não encontrado: winget install OpenJS.NodeJS.LTS"
    _, out = rodar(["node", "--version"])
    maior = int(re.findall(r"\d+", out)[0])
    if maior < 20:
        return FALHA, f"Node {out}: o pixel-agents e o Remotion precisam do 20 ou mais novo"
    if not (RAIZ / "reels" / "node_modules").exists():
        return AVISO, f"Node {out}, mas falta 'npm install' na pasta reels (o instalar.cmd faz isso)"
    return OK, f"Node {out} e reels/node_modules"


def libs_python():
    falta = [m for m in ("numpy", "soundfile") if importlib.util.find_spec(m) is None]
    if falta:
        return FALHA, f"faltam {', '.join(falta)}: pip install -r central/requirements.txt"
    return OK, "numpy e soundfile"


def testes():
    cod, out = rodar([PY, "-m", "unittest", "discover", "central/testes"])
    return (OK if cod == 0 else FALHA), ultima(out, 2)


def montagem():
    video = RAIZ / "midia" / "2026-10-21-teste-ideia.mp4"
    with tempfile.TemporaryDirectory() as tmp:
        silencio = Path(tmp) / "voz.wav"
        rodar(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "1", str(silencio)])
        saida = Path(tmp) / "final.mp4"
        cod, out = rodar([PY, "central/mixar.py", str(video), str(silencio), str(saida), "--inicio-trilha", "10"])
        if cod or not saida.exists():
            return FALHA, ultima(out)
        _, loud = rodar(["ffmpeg", "-nostats", "-i", str(saida), "-af", "ebur128", "-f", "null", "-"])
        lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", loud)
        return OK, f"vídeo + trilha montado ({lufs[-1] if lufs else '?'} LUFS)"


def oraculo():
    cod, out = rodar([PY, "central/analisar_video.py", "midia/final/2026-10-27-crm-plano.mp4"])
    return (OK if "aprovado" in out else AVISO), "plano-sequência do CRM: " + ("aprovado" if "aprovado" in out else ultima(out))


def relatorio():
    cod, out = rodar([PY, "central/relatorio.py"])
    arq = sorted((RAIZ / "metricas").glob("relatorio-*.md"))
    return (OK if cod == 0 and arq else FALHA), (f"{arq[-1].relative_to(RAIZ)}" if arq else ultima(out))


def ganchos():
    cod, out = rodar([PY, "central/ganchos.py", "ranking"])
    return (OK if cod == 0 else FALHA), out.splitlines()[0] if out else ""


def sdr():
    cod, out = rodar([PY, "central/sdr.py", "consultas", "--segmentos", "imobiliaria", "--cidades", "Chapecó SC"])
    if cod:
        return FALHA, ultima(out)
    binario = list((RAIZ / "comercial" / "bin").glob("google*maps*scraper*")) if (RAIZ / "comercial" / "bin").exists() else []
    if not binario and not shutil.which("docker"):
        return AVISO, ("consultas ok; falta o executável do Google Maps: baixe em "
                       "github.com/gosom/google-maps-scraper/releases e salve em comercial/bin/")
    return OK, f"consultas ok e scraper encontrado ({binario[0].name if binario else 'docker'})"


def radar():
    with tempfile.TemporaryDirectory() as tmp:  # testa sem mexer em radar/ do repositório
        cod, out = rodar([PY, "central/radar.py", "--dias", "7", "--saida", tmp], timeout=300)
    falhas = re.findall(r"^(\w+)\s+falhou", out, re.M)
    if cod:
        return FALHA, ultima(out)
    linha = next((l.split(" -> ")[0] for l in out.splitlines() if "assuntos ->" in l), "")
    return (AVISO if falhas else OK), linha + (f" · fontes fora do ar: {', '.join(falhas)}" if falhas else "")


def capa():
    if not (RAIZ / "reels" / "node_modules").exists():
        return AVISO, "pulei: falta npm install em reels"
    destino = RAIZ / "midia" / "capas" / "_teste-verificacao.jpg"
    cod, out = rodar(["node", "capa.mjs", "../roteiros/2026-10-21-teste-ideia.json", str(destino)], cwd=RAIZ / "reels", timeout=900)
    if cod or not destino.exists():
        return FALHA, ultima(out)
    destino.unlink()
    return OK, "capa renderizada no Remotion (na 1ª vez ele baixa o navegador dele)"


def escritorio():
    if not shutil.which("npx"):
        return FALHA, "npx não encontrado (vem com o Node.js)"
    if not (RAIZ / "central" / "escritorio" / "layout-ciello.json").exists():
        return FALHA, "layout-ciello.json não encontrado"
    return OK, "pronto: clique em Escritorio-Ciello.cmd (pixel-agents 1.5.0 + layout da Ciello)"


def voz():
    falta = [m for m in ("kokoro", "chatterbox", "faster_whisper") if importlib.util.find_spec(m) is None]
    if falta:
        return AVISO, f"opcional, não instalado ({', '.join(falta)}): pip install -r central/requirements-voz.txt"
    return OK, "kokoro, chatterbox e faster-whisper instalados"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rapido", action="store_true")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    print(f"Verificando o assistente em {RAIZ}\n")
    lista = [("Python", python_versao), ("ffmpeg", ffmpeg), ("Node", node), ("Bibliotecas Python", libs_python),
             ("Testes automáticos", testes), ("Montagem final (mixar)", montagem), ("Oráculo de ritmo", oraculo),
             ("Relatório semanal", relatorio), ("Biblioteca de ganchos", ganchos), ("SDR", sdr),
             ("Escritório (pixel-agents)", escritorio), ("Voz (opcional)", voz)]
    if not a.rapido:
        lista += [("Radar (internet)", radar), ("Capa (Remotion)", capa)]
    for nome, f in lista:
        checar(nome, f)
    n = {e: sum(1 for _, s, _, _ in resultados if s == e) for e in (OK, AVISO, FALHA)}
    resumo = f"\n{n[OK]} ok · {n[AVISO]} avisos · {n[FALHA]} falhas"
    print(resumo)
    saida = RAIZ / "estado" / "verificacao.txt"
    saida.parent.mkdir(exist_ok=True)
    saida.write_text(f"{time.strftime('%d/%m/%Y %H:%M')} · {platform.platform()} · Python {platform.python_version()}\n"
                     + "\n".join(f"[{s}] {nome} ({t:.0f}s): {m}" for nome, s, m, t in resultados) + resumo + "\n", encoding="utf-8")
    print(f"Relatório: {saida.relative_to(RAIZ)}")
    sys.exit(1 if n[FALHA] else 0)


if __name__ == "__main__":
    main()
