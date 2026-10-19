"""Quadro de presença dos agentes: cada ferramenta (e cada agente do Claude) avisa o que está fazendo.

O Escritório Ciello (central/escritorio/) lê estado/eventos.jsonl e anima os personagens.

Uso no terminal (é assim que os agentes do Claude avisam):
  python central/status.py sdr trabalhando "gerando leads de odontologia"
  python central/status.py sdr esperando "15 mensagens para o Mateus aprovar"
  python central/status.py sdr pronto "15 abordagens em comercial/abordagens/"

Uso no código:
  from status import trabalhando
  with trabalhando("pesquisador-mercado", "radar da semana"):
      ...
"""
import contextlib
import datetime as dt
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EVENTOS = RAIZ / "estado" / "eventos.jsonl"
AGENTES = ["pesquisador-mercado", "roteirista", "produtor-video", "produtor-imagem", "postagem",
           "analista", "sdr", "closer", "gestor-anuncios", "chefe-gabinete", "financeiro", "caixa-entrada", "sucesso-cliente"]
ESTADOS = ["trabalhando", "pensando", "esperando", "pronto", "erro", "parado"]


def registrar(agente: str, estado: str, tarefa: str = "") -> None:
    """Nunca derruba a ferramenta que chamou: se não der para gravar, segue em silêncio."""
    try:
        EVENTOS.parent.mkdir(parents=True, exist_ok=True)
        with EVENTOS.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": dt.datetime.now().isoformat(timespec="seconds"), "agente": agente,
                                "estado": estado, "tarefa": tarefa[:140]}, ensure_ascii=False) + "\n")
    except OSError:
        pass


@contextlib.contextmanager
def trabalhando(agente: str, tarefa: str):
    registrar(agente, "trabalhando", tarefa)
    try:
        yield
    except BaseException as e:
        if not isinstance(e, SystemExit) or e.code not in (0, None):
            registrar(agente, "erro", f"{tarefa}: {e}"[:140])
        raise
    else:
        registrar(agente, "pronto", tarefa)


def ultimo_estado(limite: int = 2000) -> dict:
    """Estado atual de cada agente (último evento) + os eventos recentes."""
    atual = {a: {"estado": "parado", "tarefa": "", "ts": ""} for a in AGENTES}
    recentes = []
    if EVENTOS.exists():
        linhas = EVENTOS.read_text(encoding="utf-8").splitlines()[-limite:]
        for l in linhas:
            try:
                e = json.loads(l)
            except ValueError:
                continue
            atual[e["agente"]] = {"estado": e["estado"], "tarefa": e.get("tarefa", ""), "ts": e["ts"]}
            recentes.append(e)
    return {"agentes": atual, "eventos": recentes[-40:][::-1]}


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[2] not in ESTADOS:
        sys.exit(f"uso: python central/status.py <agente> <{'|'.join(ESTADOS)}> [tarefa]\nagentes: {', '.join(AGENTES)}")
    registrar(sys.argv[1], sys.argv[2], " ".join(sys.argv[3:]))
