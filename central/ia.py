"""O "cérebro" que o piloto automático usa para pesquisar, escrever roteiros e, na ponte, agendar no Metricool.

Hoje é o Claude Code instalado no PC (`claude -p`, sem janela), com os agentes e o AGENTE.md do assistente.
No produto instalado dá para trocar por outro motor (a API da Anthropic com a chave do cliente, por exemplo)
mudando só este arquivo: o piloto chama ia.rodar() e não sabe quem está do outro lado.
"""
import datetime as dt
import json
import os
import shutil
import subprocess

import dados

# ferramentas que o Claude pode usar sem pedir: ler e escrever arquivos do assistente, rodar os scripts dele e pesquisar
FERRAMENTAS = "Read,Write,Edit,Glob,Grep,WebSearch,WebFetch,Bash(python central/*),Bash(node reels/*),mcp__claude_ai_Metricool*,mcp__claude_ai_vidIQ*"


def comando() -> list[str] | None:
    """O executável do motor. CIELLO_IA troca (testes e outros motores)."""
    if os.environ.get("CIELLO_IA"):
        return os.environ["CIELLO_IA"].split()
    exe = shutil.which("claude")
    return [exe] if exe else None


def disponivel() -> bool:
    return comando() is not None


def rodar(pedido: str, titulo: str = "", timeout: int = 1800) -> dict:
    """Roda um pedido sem janela e devolve {ok, saida}. Tudo fica registrado em estado/ia.jsonl."""
    cmd = comando()
    if not cmd:
        return {"ok": False, "saida": "Claude Code não está instalado neste PC (rode o instalar.cmd)."}
    inicio = dt.datetime.now()
    try:
        p = subprocess.run([*cmd, "-p", pedido, "--allowedTools", FERRAMENTAS, "--output-format", "text"], cwd=dados.RAIZ,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        r = {"ok": p.returncode == 0, "saida": (p.stdout or p.stderr or "").strip()[-4000:]}
    except subprocess.TimeoutExpired:
        r = {"ok": False, "saida": f"passou de {timeout // 60} minutos"}
    except OSError as e:
        r = {"ok": False, "saida": str(e)}
    with dados.estado("ia.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"quando": inicio.isoformat(timespec="seconds"), "titulo": titulo, "ok": r["ok"],
                            "segundos": round((dt.datetime.now() - inicio).total_seconds()), "saida": r["saida"][-600:]}, ensure_ascii=False) + "\n")
    return r
