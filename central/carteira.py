"""Saúde da carteira: cada cliente ativo com uma nota de 0 a 100, os motivos e a próxima ação.

Junta o que já está no financeiro: atraso agora e o costume de pagar atrasado, a nota de satisfação (NPS), quanto
tempo faz desde a última conversa, os primeiros 90 dias (quando mais se cancela) e o pós-venda pendente. Quem está em
risco aparece com uma mensagem pronta para puxar conversa; quem é promotor, com o pedido de indicação. Nada é
enviado: a mensagem abre no WhatsApp para você revisar.

  python central/carteira.py
"""
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import financeiro  # noqa: E402
from empresa import apresentacao, nome_produto  # noqa: E402

NIVEIS = ((80, "saudavel"), (55, "atencao"), (0, "risco"))


def _dias(a, b):
    return (financeiro.data(a) - financeiro.data(b)).days


def avaliar(c: dict, faturas: list[dict], ref: dt.date) -> dict:
    nota, motivos = 100, []
    tira = lambda pontos, motivo: (motivos.append(motivo), pontos)[1]
    minhas = [f for f in faturas if f["cliente_id"] == c["id"]]
    abertas = [(ref - financeiro.data(f["vencimento"])).days for f in minhas if not f["pago_em"]]
    atraso = max([d for d in abertas if d > 0], default=0)
    if atraso > 14:
        nota -= tira(40, f"fatura atrasada há {atraso} dias")
    elif atraso > 3:
        nota -= tira(25, f"fatura atrasada há {atraso} dias")
    pagas = sorted((f for f in minhas if f["pago_em"]), key=lambda f: f["vencimento"])[-6:]
    if len(pagas) >= 2:
        media = sum(max(0, _dias(f["pago_em"], f["vencimento"])) for f in pagas) / len(pagas)
        if media > 5:
            nota -= tira(15, f"costuma pagar com {round(media)} dias de atraso")
    casa = (ref - financeiro.data(c["inicio"])).days
    nps = int(c["nps"]) if (c.get("nps") or "").isdigit() else None
    if nps is not None and nps <= 6:
        nota -= tira(35, f"deu nota {nps} de 10")
    elif nps is not None and nps <= 8:
        nota -= tira(10, f"nota {nps} de 10 (nem fã, nem crítico)")
    elif nps is None and casa >= 45:
        nota -= tira(5, "ainda sem nota de satisfação")
    ultimo = max(x for x in (c.get("ultimo_contato") or "", c["inicio"]) if x)
    sem_conversa = (ref - financeiro.data(ultimo)).days
    if sem_conversa > 90:
        nota -= tira(20, f"sem conversa há {sem_conversa} dias")
    elif sem_conversa > 45:
        nota -= tira(10, f"sem conversa há {sem_conversa} dias")
    if casa < 90:
        nota -= tira(5, "nos primeiros 90 dias (quando mais se cancela)")
    if financeiro.posvenda_devida(c, ref):
        nota -= tira(5, "pós-venda pendente")
    nota = max(0, nota)
    nivel = next(n for minimo, n in NIVEIS if nota >= minimo)
    return {"id": c["id"], "empresa": c["empresa"], "contato": c.get("contato", ""), "whatsapp": c.get("whatsapp", ""), "plano": c.get("plano", ""),
            "valor": float(c["valor_mensal"] or 0), "nota": nota, "nivel": nivel, "motivos": motivos, "nps": nps, "atraso": atraso,
            "sem_conversa": sem_conversa, "casa": casa}


def _primeiro_nome(c):
    return (c.get("contato") or "").split(" ")[0] or "tudo bem"


def mensagem(s: dict, assinatura: str) -> tuple[str, str]:
    """(ação, mensagem) para cada situação. Atraso fica com a cobrança, que já tem mensagens por etapa."""
    nome = _primeiro_nome(s)
    produto = "o site" if (s["plano"] or "crm") in ("site", "hospedagem") else f"o {nome_produto('crm')}"
    if s["atraso"] > 3:
        return "Cobrar (Financeiro → Cobrança e pós-venda)", ""
    if s["nps"] is not None and s["nps"] <= 6:
        return "Ligar e entender o que não está bom", (f"Oi, {nome}! {apresentacao(assinatura)}. Vi a sua nota e queria entender melhor: "
                                                     f"o que não está funcionando com {produto}? Posso te ligar 10 minutos hoje ou amanhã?")
    if s["nivel"] != "saudavel":
        return "Puxar conversa", (f"Oi, {nome}! {apresentacao(assinatura)}. Passando para saber como está {produto} aí com a equipe: "
                                  "tem alguma coisa travando ou que eu possa ajustar?")
    if s["nps"] is not None and s["nps"] >= 9:
        return "Pedir indicação", (f"Oi, {nome}! Que bom saber que {produto} está ajudando vocês. Se lembrar de alguém (outra empresa daqui) que "
                                   "também perde cliente no WhatsApp, me passa o contato? Falo com cuidado e só cito você se você quiser.")
    return "", ""


def carteira(ref: dt.date | None = None) -> dict:
    ref = ref or financeiro.hoje()
    assinatura = financeiro.config()["assinatura"]
    faturas = financeiro.ler(financeiro.FATURAS, financeiro.C_FATURA)
    clientes = [c for c in financeiro.ler(financeiro.CLIENTES, financeiro.C_CLIENTE) if c["status"] == "ativo"]
    lista = []
    for c in clientes:
        s = avaliar(c, faturas, ref)
        acao, msg = mensagem(s, assinatura)
        lista.append({**s, "acao": acao, "mensagem": msg, "link": financeiro.link_wa(s["whatsapp"], msg) if msg and s["whatsapp"] else ""})
    lista.sort(key=lambda s: (s["nota"], -s["valor"]))
    mrr = sum(s["valor"] for s in lista)
    em_risco = sum(s["valor"] for s in lista if s["nivel"] == "risco")
    return {"clientes": lista, "contagem": {n: sum(s["nivel"] == n for s in lista) for _, n in NIVEIS},
            "mrr_em_risco": round(em_risco, 2), "mrr": round(mrr, 2),
            "promotores": [s for s in lista if s["acao"] == "Pedir indicação"]}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    r = carteira()
    print(f"{r['contagem']['saudavel']} saudáveis · {r['contagem']['atencao']} em atenção · {r['contagem']['risco']} em risco "
          f"({financeiro.reais(r['mrr_em_risco'])}/mês de {financeiro.reais(r['mrr'])})")
    for s in r["clientes"]:
        print(f"  {s['nota']:>3}  {s['empresa'][:30]:<30} {'; '.join(s['motivos']) or 'tudo certo'}" + (f"  → {s['acao']}" if s["acao"] else ""))


if __name__ == "__main__":
    main()
