"""Hook do Claude Code para o escritório da Ciello: repassa o evento ao Ciello OS e sai.

O Claude Code roda este script a cada evento (instalado pelo escritório, com a sua permissão, em
~/.claude/settings.json). Ele lê o evento da entrada padrão e manda para 127.0.0.1 com o token que o
Ciello OS anotou em ~/.ciello/escritorio/servidor.json. Se o Ciello OS estiver fechado, não faz nada.
Nunca trava o Claude Code: sai sempre com código 0, em no máximo 2 segundos.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

CASA = Path(os.environ.get("CIELLO_ESCRITORIO_CASA") or Path.home() / ".ciello" / "escritorio")


def main():
    try:
        corpo = sys.stdin.buffer.read(65536)
        json.loads(corpo)
        alvo = json.loads((CASA / "servidor.json").read_text(encoding="utf-8"))
        pedido = urllib.request.Request(f"http://127.0.0.1:{int(alvo['porta'])}/api/ganchos/claude", data=corpo,
                                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {alvo['token']}"})
        urllib.request.build_opener(urllib.request.ProxyHandler({})).open(pedido, timeout=2).read()
    except Exception:  # noqa: BLE001  o Claude Code segue normalmente mesmo sem escritório
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)
