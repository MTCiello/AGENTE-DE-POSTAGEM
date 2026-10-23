"""Decisões do negócio: o que está em aberto (furos do plano, ideias de preço), o que você decidiu e quando rever.

O que você decide vira regra da casa em financeiro/regras.md, que os agentes (financeiro, closer, SDR) leem antes de
propor preço, desconto ou condição. Nada aqui muda preço ou plano sozinho: só registra a sua decisão e o porquê.
Fica fora do git (financeiro/decisoes.json).

  python central/decisoes.py            # em aberto, para rever e regras da casa
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import financeiro  # noqa: E402
import plano  # noqa: E402

ESTADOS = {"decidida": "Decidida", "adiada": "Para depois", "descartada": "Não se aplica"}


def arquivo() -> Path:
    return financeiro.PASTA / "decisoes.json"


def regras_arquivo() -> Path:
    return financeiro.PASTA / "regras.md"


def ler() -> list[dict]:
    try:
        return json.loads(arquivo().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def chave(titulo: str) -> str:
    """O mesmo assunto com outro número ("3 negócios sem status" → "5 negócios…") continua sendo a mesma decisão."""
    t = financeiro.sem_acento(titulo)
    t = re.sub(r"r\$\s*[\d.,]+|[\d.,]+%?", " ", t)
    return re.sub(r"[^a-z]+", "-", t).strip("-")[:60]


def sugestoes() -> list[dict]:
    """Assuntos para decidir: os furos importantes do plano e as ideias de preço que ainda não têm decisão."""
    feitas = {d["chave"] for d in ler()}
    out = []
    p = plano.ler()
    if p["negocios"] or p["custos"]:
        for a in plano.auditar(p):
            if a["nivel"] in ("alto", "medio"):
                out.append({"chave": chave(a["titulo"]), "titulo": a["titulo"], "detalhe": a["detalhe"], "origem": "plano", "nivel": a["nivel"]})
    for x in plano.precos():
        out.append({"chave": chave(x["titulo"]), "titulo": x["titulo"], "detalhe": x["detalhe"], "origem": "preço", "nivel": "dica"})
    vistos, unicas = set(feitas), []
    for s in out:
        if s["chave"] not in vistos:
            vistos.add(s["chave"])
            unicas.append(s)
    return unicas


def salvar(d: dict, ref: dt.date | None = None) -> dict:
    ref = ref or dt.date.today()
    titulo = re.sub(r"\s+", " ", str(d.get("titulo") or "")).strip()[:160]
    estado = d.get("estado") or "decidida"
    texto = re.sub(r"\s+", " ", str(d.get("decisao") or "")).strip()[:800]
    if not titulo:
        return {"ok": False, "saida": "escreva o assunto"}
    if estado not in ESTADOS:
        return {"ok": False, "saida": "estado inválido"}
    if estado == "decidida" and not texto:
        return {"ok": False, "saida": "escreva o que você decidiu (vira regra para os agentes)"}
    revisar = str(d.get("revisar") or "").strip()
    if revisar:
        try:
            revisar = dt.date.fromisoformat(revisar[:10]).isoformat()
        except ValueError:
            return {"ok": False, "saida": "data para rever inválida"}
    elif estado == "adiada":
        revisar = (ref + dt.timedelta(days=30)).isoformat()
    lista = ler()
    k = d.get("chave") or chave(titulo)
    item = next((x for x in lista if x["chave"] == k), None)
    novo = {"chave": k, "titulo": titulo, "detalhe": str(d.get("detalhe") or "")[:800], "estado": estado, "decisao": texto,
            "data": ref.isoformat(), "revisar": revisar, "origem": d.get("origem") or "você"}
    if item:
        item.update({c: v for c, v in novo.items() if v or c in ("revisar", "decisao")})
    else:
        lista.append(novo)
    arquivo().parent.mkdir(parents=True, exist_ok=True)
    arquivo().write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")
    escrever_regras(lista)
    return {"ok": True, "saida": {"decidida": "decisão registrada: vira regra para os agentes", "adiada": f"fica para {revisar[8:10]}/{revisar[5:7]}",
                                  "descartada": "marcada como não se aplica"}[estado]}


def remover(k: str) -> dict:
    lista = ler()
    resto = [x for x in lista if x["chave"] != k]
    if len(resto) == len(lista):
        return {"ok": False, "saida": "decisão não encontrada"}
    arquivo().write_text(json.dumps(resto, ensure_ascii=False, indent=1), encoding="utf-8")
    escrever_regras(resto)
    return {"ok": True, "saida": "decisão apagada (o assunto volta para em aberto, se ainda vale)"}


def escrever_regras(lista: list[dict]):
    regras = [x for x in lista if x["estado"] == "decidida"]
    L = ["# Regras da casa (decisões do Mateus)", "",
         "Gerado pelo Ciello OS (Financeiro → Metas e decisões). Siga estas regras ao propor preço, desconto, condição ou plano;",
         "se uma situação pedir outra coisa, pergunte ao Mateus antes. Não edite à mão: mude pela janela.", ""]
    for x in sorted(regras, key=lambda x: x["data"]):
        rever = f"; rever em {x['revisar'][8:10]}/{x['revisar'][5:7]}/{x['revisar'][:4]}" if x.get("revisar") else ""
        L.append(f"- **{x['titulo']}:** {x['decisao']} (decidido em {x['data'][8:10]}/{x['data'][5:7]}/{x['data'][:4]}{rever})")
    if not regras:
        L.append("(nenhuma decisão registrada ainda)")
    regras_arquivo().parent.mkdir(parents=True, exist_ok=True)
    regras_arquivo().write_text("\n".join(L) + "\n", encoding="utf-8")


def para_rever(ref: dt.date | None = None) -> list[dict]:
    ref = (ref or dt.date.today()).isoformat()
    return [x for x in ler() if x.get("revisar") and x["revisar"] <= ref and x["estado"] != "descartada"]


def para_janela(ref: dt.date | None = None) -> dict:
    lista = ler()
    rever = {x["chave"] for x in para_rever(ref)}
    return {"abertas": sugestoes(), "decisoes": [{**x, "rever_agora": x["chave"] in rever} for x in sorted(lista, key=lambda x: x["data"], reverse=True)],
            "estados": ESTADOS}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    j = para_janela()
    print("Em aberto:")
    for s in j["abertas"]:
        print(f"  [{s['origem']}] {s['titulo']}")
    print("Para rever:")
    for x in [x for x in j["decisoes"] if x["rever_agora"]]:
        print(f"  {x['titulo']} ({ESTADOS[x['estado']]})")
    print("Regras da casa:")
    for x in [x for x in j["decisoes"] if x["estado"] == "decidida"]:
        print(f"  {x['titulo']}: {x['decisao']}")


if __name__ == "__main__":
    main()
