"""Gastos fixos: as assinaturas e contas que o extrato mostra todo mês, e o que costuma passar despercebido nelas.

Agrupa as despesas do extrato pelo nome (sem números, datas e prefixos do banco) e chama de fixo o que aparece em
2 meses ou mais. Aponta:
  - cobrança em dobro no mesmo mês;
  - preço que subiu de um mês para o outro;
  - conta de todo mês que não veio (cartão recusado? serviço vai cair?);
  - ferramenta nova que apareceu agora;
  - gasto fixo que não está no Plano do ano.

  python central/gastos.py
"""
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import financeiro  # noqa: E402
import plano  # noqa: E402

FORA = financeiro.FORA_DO_RESULTADO | {"Pró-labore e retiradas"}
# o que o banco põe antes do nome de quem cobrou
PREFIXOS = r"^(compra (no )?(cartao|debito|credito)|compra|pagamento( de)?( boleto)?|pag(to)?|pix (enviado|transf)|pix|deb(ito)? aut(omatico)?|debito|ted|doc|boleto|pg|pgto|ec|mp|pp|iz|sumup)\b\s*"
ASSINATURAS = {"Ferramentas e software", "Telefone e internet", "Contabilidade"}  # um PIX avulso "a classificar" não é assinatura
PARA_O_PLANO = {"Ferramentas e software": "ferramentas", "Anúncios": "anuncios", "Contabilidade": "contabilidade", "Impostos": "impostos",
                "Telefone e internet": "infraestrutura"}


def nome(descricao: str) -> str:
    """'COMPRA CARTAO ANTHROPIC *CLAUDE 10/10' → 'anthropic claude'."""
    t = financeiro.sem_acento(descricao)
    t = re.sub(r"[^a-z ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    for _ in range(2):
        t = re.sub(PREFIXOS, "", t).strip()
    palavras = [p for p in t.split() if len(p) > 1][:3]
    return " ".join(palavras)


def _por_mes(lancs):
    """{nome: {mes: [lançamentos]}} só das despesas que contam para o resultado."""
    grupos = {}
    for l in lancs:
        v = float(l["valor"])
        if v >= 0 or l["categoria"] in FORA:
            continue
        k = nome(l["descricao"])
        if k:
            grupos.setdefault(k, {}).setdefault(l["data"][:7], []).append(l)
    return grupos


def no_plano(k: str, custos: list[dict]) -> bool:
    palavras = [p for p in k.split() if len(p) > 3]
    return any(any(p in financeiro.sem_acento(c.get("item", "")) for p in palavras) for c in custos)


def analisar(ref: dt.date | None = None, lancs=None) -> dict:
    ref = ref or financeiro.hoje()
    lancs = lancs if lancs is not None else financeiro.ler(financeiro.LANCAMENTOS, financeiro.C_LANC)
    mes = ref.strftime("%Y-%m")
    ultimos = {financeiro.meses_atras(mes, i) for i in range(0, 4)}
    p = plano.ler()
    custos = p.get("custos") or []
    meses_com_extrato = {l["data"][:7] for l in lancs}
    fixos, alertas = [], []
    add = lambda nivel, tipo, texto, item=None: alertas.append({"nivel": nivel, "tipo": tipo, "texto": texto, "item": item})
    for k, por_mes in _por_mes(lancs).items():
        meses = sorted(por_mes)
        recentes = [m for m in meses if m in ultimos]
        todos = [l for m in meses for l in por_mes[m]]
        ultimo = max(todos, key=lambda l: l["data"])
        rotulo = ultimo["descricao"].strip()[:40]
        categoria = ultimo["categoria"]
        # em dobro: o mesmo valor duas vezes no mesmo mês, num gasto que normalmente vem uma vez
        for m in recentes:
            vals = [round(-float(l["valor"]), 2) for l in por_mes[m]]
            repetidos = {v for v in vals if vals.count(v) > 1}
            if repetidos and (len(meses) >= 2 or categoria in ASSINATURAS):
                v = max(repetidos)
                add("alto", "dobro", f"{rotulo}: {financeiro.reais(v)} cobrado {vals.count(v)} vezes em {m[5:]}/{m[:4]}. Confira se não é cobrança repetida.",
                    {"nome": k, "valor": v})
        if len(recentes) < 2:
            primeira = min(l["data"] for l in todos)
            if len(todos) == 1 and categoria in ASSINATURAS and not no_plano(k, custos) and (ref - financeiro.data(primeira)).days <= 35 and len(meses_com_extrato) >= 2:
                v = -float(ultimo["valor"])
                add("dica", "nova", f"{rotulo}: {financeiro.reais(v)} em {primeira[8:10]}/{primeira[5:7]}, primeira vez no extrato. É uma assinatura nova? Se for, entra no Plano do ano.",
                    {"nome": k, "valor": v, "categoria": categoria})
            continue
        valor_mes = {m: round(-sum(float(l["valor"]) for l in por_mes[m]), 2) for m in meses}
        vals = list(valor_mes.values())
        if categoria not in ASSINATURAS and max(vals) > 1.3 * min(vals):
            continue  # gasto que varia (combustível, mercado): não é conta fixa
        anteriores = vals[:-1]
        estavel = len(anteriores) >= 2 and max(anteriores) <= 1.05 * min(anteriores)
        atual_m = meses[-1]
        atual = -float(ultimo["valor"])
        anterior = valor_mes[meses[-2]]
        dia = int(round(sum(int(l["data"][8:10]) for l in todos) / len(todos)))
        item = {"nome": k, "rotulo": rotulo, "categoria": categoria, "valor": round(atual, 2), "anterior": anterior, "dia": dia,
                "meses": len(meses), "ultimo": ultimo["data"], "no_plano": no_plano(k, custos)}
        fixos.append(item)
        unico_no_mes = len(por_mes[atual_m]) == 1 and len(por_mes[meses[-2]]) == 1
        if unico_no_mes and (categoria in ASSINATURAS or estavel) and atual > anterior * 1.05 and atual - anterior >= 2:
            add("medio", "subiu", f"{rotulo} subiu de {financeiro.reais(anterior)} para {financeiro.reais(atual)} (+{atual / anterior - 1:.0%}). Aumento combinado ou reajuste sem aviso?", item)
        # a conta de todo mês que não veio este mês (passou uns dias do dia de sempre)
        if atual_m < mes and atual_m == financeiro.meses_atras(mes, 1) and ref.day > dia + 5 and mes in meses_com_extrato:
            add("medio", "parou", f"{rotulo} vem todo dia {dia} e ainda não apareceu em {mes[5:]}/{mes[:4]}. Cancelou, mudou de cartão ou o pagamento falhou (o serviço pode cair)?", item)
        if custos and not item["no_plano"]:
            add("dica", "fora_do_plano", f"{rotulo} ({financeiro.reais(atual)}/mês) não está no Plano do ano.", item)
    fixos.sort(key=lambda x: -x["valor"])
    ordem = {"alto": 0, "medio": 1, "dica": 2}
    alertas.sort(key=lambda a: ordem[a["nivel"]])
    return {"fixos": fixos, "total_mensal": round(sum(f["valor"] for f in fixos if f["ultimo"][:7] >= financeiro.meses_atras(mes, 1)), 2),
            "alertas": alertas, "plano_mensal": round(sum(float(c.get("valor") or 0) for c in custos if c.get("frequencia", "mensal") == "mensal"), 2),
            "tem_plano": bool(custos), "para_o_plano": PARA_O_PLANO}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    r = analisar()
    print(f"Gastos fixos: {financeiro.reais(r['total_mensal'])}/mês" + (f" (no Plano do ano: {financeiro.reais(r['plano_mensal'])})" if r["tem_plano"] else ""))
    for f in r["fixos"]:
        print(f"  {f['rotulo']:<40} {financeiro.reais(f['valor']):>12}  dia {f['dia']:>2}  {f['meses']} meses")
    for a in r["alertas"]:
        print(f"[{a['nivel']}] {a['texto']}")


if __name__ == "__main__":
    main()
