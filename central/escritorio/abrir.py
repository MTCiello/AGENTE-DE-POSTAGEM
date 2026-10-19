"""Abre o Escritório Ciello: o pixel-agents original (github.com/pablodelucca/pixel-agents, MIT),
sem alteração, rodando na pasta do assistente e com o layout da Ciello.

  python central/escritorio/abrir.py                  # ou clique duas vezes em Escritorio-Ciello.cmd
  python central/escritorio/abrir.py --layout         # reinstala o layout da Ciello (guarda o atual em backup)
  python central/escritorio/abrir.py --sem-navegador

O pixel-agents acompanha toda sessão do Claude Code aberta nesta pasta. Cada teammate da equipe (sdr, closer,
pesquisador-mercado…) ganha um personagem com nome e mesa; subagentes aparecem ao lado de quem os chamou.
Na primeira vez, o próprio escritório pede para instalar os hooks do Claude Code (aceite: é o modo mais preciso).
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

VERSAO = "1.5.0"  # versão do pixel-agents testada com o layout; atualize aqui de propósito, nunca "latest"
PORTA = 3100
RAIZ = Path(__file__).resolve().parent.parent.parent
LAYOUT_CIELLO = Path(__file__).with_name("layout-ciello.json")
CASA = Path.home() / ".pixel-agents"


def instalar_layout(forcar: bool):
    destino = CASA / "layout.json"
    if destino.exists() and not forcar:
        return
    CASA.mkdir(exist_ok=True)
    if destino.exists():
        backup = destino.with_name(f"layout-backup-{time.strftime('%Y%m%d-%H%M%S')}.json")
        shutil.copy2(destino, backup)
        print("layout anterior guardado em", backup)
    shutil.copy2(LAYOUT_CIELLO, destino)
    print("layout da Ciello instalado")


def no_ar():
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/api/health", timeout=1) as r:
            return r.status == 200
    except OSError:
        return False


def url_com_token():
    token = (CASA / "standalone-token").read_text(encoding="utf-8").strip() if (CASA / "standalone-token").exists() else ""
    return f"http://127.0.0.1:{PORTA}/?token={token}" if token else f"http://127.0.0.1:{PORTA}/"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layout", action="store_true", help="reinstala o layout da Ciello")
    ap.add_argument("--sem-navegador", action="store_true")
    a = ap.parse_args()

    npx = shutil.which("npx")
    if not npx:
        sys.exit("Precisa do Node.js 20 ou mais novo: winget install OpenJS.NodeJS.LTS")
    instalar_layout(a.layout)

    if no_ar():
        print("O escritório já está aberto.")
    else:
        # roda na raiz do assistente: o pixel-agents acompanha as sessões do Claude Code desta pasta
        proc = subprocess.Popen([npx, "-y", f"pixel-agents@{VERSAO}", "--port", str(PORTA)], cwd=RAIZ)
        for _ in range(120):
            if no_ar() or proc.poll() is not None:
                break
            time.sleep(0.5)
        if not no_ar():
            sys.exit("O pixel-agents não subiu. Veja a mensagem acima.")
    url = url_com_token()
    print("Escritório Ciello:", url.split("?")[0], "(o link com token fica só no seu navegador)")
    if not a.sem_navegador:
        webbrowser.open(url)
    try:
        while no_ar():
            time.sleep(2)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
