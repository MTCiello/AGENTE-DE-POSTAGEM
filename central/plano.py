"""Plano do ano da Ciello: projeção de 12 meses, ponto de equilíbrio e auditoria do plano (o que está faltando ou não fecha).

O plano fica em financeiro/plano.json (fora do git): os negócios (fechados, em negociação, "talvez"), os custos (mensais,
anuais ou únicos), o regime de imposto e quanto você precisa tirar por mês. A auditoria aponta os furos que costumam
passar despercebidos: meses sem receita, imposto que não entrou, custo anual que não foi provisionado, receita
concentrada num cliente, plano que conta "talvez" como certo, limite do MEI, quantos clientes faltam para te pagar.

  python central/plano.py              # projeção + auditoria -> financeiro/relatorios/plano-AAAA.md
  python central/plano.py --ano 2027

Na janela Financeiro → Plano do ano dá para editar tudo e discutir o resultado com o agente Financeiro.
Os números de imposto são aproximações para planejar (confirme com o contador).
"""
import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import financeiro  # noqa: E402

STATUS = {"fechado": 1.0, "negociando": 0.5, "talvez": 0.25}  # chance padrão de cada status (dá para mudar no negócio)
# regime -> (alíquota sobre a receita, imposto fixo mensal, teto de receita no ano). Aproximações para planejar.
REGIMES = {
    "mei": {"nome": "MEI", "aliquota": 0.0, "fixo": 86.0, "teto": 81000.0,
            "nota": "DAS fixo de uns R$ 86/mês; teto de R$ 81 mil no ano. Confira com o contador se a sua atividade (software, sites) pode ser MEI."},
    "simples3": {"nome": "Simples Nacional · Anexo III", "aliquota": 0.06, "fixo": 0.0, "teto": 4800000.0,
                 "nota": "6% na 1ª faixa (até R$ 180 mil no ano). Serviços de software caem no Anexo III quando o pró-labore é pelo menos 28% da receita (fator R)."},
    "simples5": {"nome": "Simples Nacional · Anexo V", "aliquota": 0.155, "fixo": 0.0, "teto": 4800000.0,
                 "nota": "15,5% na 1ª faixa: é onde cai software sem o fator R. Subir o pró-labore para 28% da receita leva ao Anexo III (6%)."},
}
PADRAO = {"ano": dt.date.today().year + (1 if dt.date.today().month >= 10 else 0), "regime": "", "pro_labore": 0.0,
          "churn_mensal": 0.0, "taxa_recebimento": 0.0, "negocios": [], "custos": []}


def arquivo() -> Path:
    return financeiro.PASTA / "plano.json"


def ler() -> dict:
    try:
        return {**PADRAO, **json.loads(arquivo().read_text(encoding="utf-8"))}
    except (OSError, ValueError):
        return dict(PADRAO, negocios=[], custos=[])


def gravar(p: dict):
    arquivo().parent.mkdir(parents=True, exist_ok=True)
    arquivo().write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")


def meses(ano: int) -> list[str]:
    return [f"{ano}-{m:02d}" for m in range(1, 13)]


def chance(n: dict) -> float:
    try:
        return float(n["chance"]) if n.get("chance") not in (None, "") else STATUS.get(n.get("status", "fechado"), 1.0)
    except (TypeError, ValueError):
        return STATUS.get(n.get("status", "fechado"), 1.0)


def receita_do_negocio(n: dict, mes: str, churn: float = 0.0) -> float:
    """Quanto este negócio fatura no mês (sem ponderar pela chance). Recorrente perde `churn` ao mês depois do 1º."""
    inicio = n.get("inicio") or mes
    if mes < inicio[:7]:
        return 0.0
    valor = float(n.get("valor") or 0)
    tipo = n.get("tipo", "mensal")
    passados = (int(mes[:4]) - int(inicio[:4])) * 12 + int(mes[5:7]) - int(inicio[5:7])
    if tipo == "unico":
        return valor if passados == 0 else 0.0
    if tipo == "parcelas":
        return valor if passados < int(n.get("parcelas") or 1) else 0.0
    if n.get("fim") and mes > n["fim"][:7]:
        return 0.0
    return valor * (1 - churn) ** passados


def custo_no_mes(c: dict, mes: str) -> float:
    valor = float(c.get("valor") or 0)
    freq = c.get("frequencia", "mensal")
    if c.get("inicio") and mes < c["inicio"][:7]:
        return 0.0
    if freq == "anual":
        return valor if mes[5:7] == (c.get("mes") or "01")[-2:] else 0.0
    if freq == "unico":
        return valor if mes == (c.get("mes") or c.get("inicio") or "")[:7] else 0.0
    return valor


def projetar(p: dict) -> list[dict]:
    reg = REGIMES.get(p.get("regime") or "", {"aliquota": 0.0, "fixo": 0.0})
    churn, taxa = float(p.get("churn_mensal") or 0), float(p.get("taxa_recebimento") or 0)
    out, acumulado = [], 0.0
    for mes in meses(int(p["ano"])):
        certa = sum(receita_do_negocio(n, mes, churn) for n in p["negocios"] if chance(n) >= 1)
        provavel = sum(receita_do_negocio(n, mes, churn) * chance(n) for n in p["negocios"])
        bruta_otimista = sum(receita_do_negocio(n, mes, churn) for n in p["negocios"])
        custos = sum(custo_no_mes(c, mes) for c in p["custos"])
        imposto = provavel * reg["aliquota"] + reg["fixo"]
        taxas = provavel * taxa
        resultado = provavel - imposto - taxas - custos
        acumulado += resultado
        out.append({"mes": mes, "receita_certa": round(certa, 2), "receita_provavel": round(provavel, 2),
                    "receita_se_tudo_fechar": round(bruta_otimista, 2), "custos": round(custos, 2), "imposto": round(imposto, 2),
                    "taxas": round(taxas, 2), "resultado": round(resultado, 2), "acumulado": round(acumulado, 2),
                    "sobra_para_voce": round(resultado - float(p.get("pro_labore") or 0), 2)})
    return out


def equilibrio(p: dict) -> dict:
    """Quantos clientes de CRM pagam os custos fixos e o seu pró-labore."""
    crm = financeiro.produtos().get("crm", {})
    preco = float(crm.get("mensal") or 0)
    reg = REGIMES.get(p.get("regime") or "", {"aliquota": 0.0, "fixo": 0.0})
    fixos = sum(float(c.get("valor") or 0) / (12 if c.get("frequencia") == "anual" else 1)
                for c in p["custos"] if c.get("frequencia", "mensal") in ("mensal", "anual"))
    liquido = preco * (1 - reg["aliquota"] - float(p.get("taxa_recebimento") or 0))
    alvo = fixos + reg["fixo"] + float(p.get("pro_labore") or 0)
    return {"preco_crm": preco, "liquido_por_cliente": round(liquido, 2), "custos_fixos_mes": round(fixos, 2),
            "clientes_para_custos": math.ceil((fixos + reg["fixo"]) / liquido) if liquido else None,
            "clientes_para_te_pagar": math.ceil(alvo / liquido) if liquido else None}


def auditar(p: dict) -> list[dict]:
    """Os furos do plano: {nivel: alto|medio|dica, titulo, detalhe}."""
    proj = projetar(p)
    achados = []
    add = lambda nivel, titulo, detalhe: achados.append({"nivel": nivel, "titulo": titulo, "detalhe": detalhe})
    receita_ano = sum(m["receita_provavel"] for m in proj)
    if not p["negocios"]:
        add("alto", "Plano sem negócios", "Cadastre os clientes atuais (fechados) e as negociações, com a chance de cada uma.")
        return achados
    vazios = [m["mes"][5:] for m in proj if m["receita_provavel"] == 0]
    if vazios:
        add("alto", f"{len(vazios)} mês(es) sem nenhuma receita",
            f"Meses {', '.join(vazios)}: os contratos recorrentes acabam antes ou começam depois? Se continuam, marque como mensal sem data de fim.")
    if not p.get("regime"):
        add("alto", "Imposto fora do plano", "Escolha o regime (MEI, Simples Anexo III ou V). No Simples, a 1ª faixa é de 6% a 15,5% da receita: "
            f"em {financeiro.reais(receita_ano)} no ano, isso é de {financeiro.reais(receita_ano * 0.06)} a {financeiro.reais(receita_ano * 0.155)}.")
    else:
        reg = REGIMES[p["regime"]]
        se_tudo = sum(m["receita_se_tudo_fechar"] for m in proj)
        if se_tudo > reg["teto"]:
            add("alto", f"Passa do teto do {reg['nome']}", f"Se tudo fechar, a receita do ano ({financeiro.reais(se_tudo)}) passa de {financeiro.reais(reg['teto'])}: "
                "planeje a mudança de regime antes (com o contador), senão a cobrança vem retroativa.")
        elif se_tudo > 0.8 * reg["teto"]:
            add("medio", f"Perto do teto do {reg['nome']}", f"{financeiro.reais(se_tudo)} de {financeiro.reais(reg['teto'])} se tudo fechar.")
        if p["regime"] == "simples5" and p.get("pro_labore") and receita_ano and float(p["pro_labore"]) * 12 / receita_ano >= 0.28:
            add("dica", "Fator R pode baixar o imposto", "Se você de fato tirar esse pró-labore (com INSS), ele passa de 28% da receita: no Simples, o software cai no Anexo III (6%) em vez do V (15,5%). Vale fazer a conta com o contador.")
    sem_status = [n for n in p["negocios"] if not n.get("status")]
    if sem_status:
        add("medio", f"{len(sem_status)} negócio(s) sem status", "Marque fechado, negociando ou talvez: o plano conta cada um pela chance de fechar.")
    talvez = [n for n in p["negocios"] if chance(n) < 1]
    if talvez:
        diff = sum(m["receita_se_tudo_fechar"] - m["receita_provavel"] for m in proj)
        add("dica", f"{len(talvez)} negócio(s) ainda não fechado(s)", f"Contando só a chance de cada um, o ano tem {financeiro.reais(diff)} a menos do que se tudo fechar. "
            "O plano usa o valor provável; o otimista aparece ao lado.")
    churn = float(p.get("churn_mensal") or 0)
    no_ano = lambda n: sum(receita_do_negocio(n, m, churn) * chance(n) for m in meses(int(p["ano"])))  # mesma base de receita_ano
    clientes = {}
    for n in p["negocios"]:
        clientes[n.get("cliente", "?")] = clientes.get(n.get("cliente", "?"), 0) + no_ano(n)
    if receita_ano and clientes:
        maior, valor = max(clientes.items(), key=lambda x: x[1])
        if valor / receita_ano > 0.25 and len(clientes) > 1:
            add("medio", f"{maior} é {valor / receita_ano:.0%} da receita", "Se esse cliente sair, o ano muda de figura: vale um contrato mais longo ou um 2º produto para ele.")
    produtos = {}
    for n in p["negocios"]:
        produtos[n.get("produto") or "outro"] = produtos.get(n.get("produto") or "outro", 0) + no_ano(n)
    if receita_ano and produtos:
        prod, valor = max(produtos.items(), key=lambda x: x[1])
        if valor / receita_ano > 0.6 and len(p["negocios"]) >= 3:
            nomes = {"crm": "CIELLO CRM", "site": "sites", "hospedagem": "hospedagem", "instagram": "Instagram", "sistema": "sistemas sob medida"}
            add("dica", f"{valor / receita_ano:.0%} da receita vem de {nomes.get(prod, prod)}", "Receita concentrada num produto: uma taxa de implantação ou um plano anual dão fôlego sem depender de mais clientes.")
    recorrentes = [n for n in p["negocios"] if n.get("tipo", "mensal") == "mensal"]
    if recorrentes and not float(p.get("churn_mensal") or 0):
        add("medio", "Nenhum cancelamento previsto", "O plano supõe que nenhum cliente cancela no ano. Teste com 3% ao mês (churn) para ver o ano mais realista.")
    cats = {c.get("categoria", "") for c in p["custos"]}
    if any(n.get("produto") in ("crm", "hospedagem") for n in p["negocios"]) and not cats & {"servidor", "infraestrutura", "hospedagem"}:
        add("alto", "Custo de entrega fora do plano", "Há clientes de CRM ou hospedagem, mas nenhum custo de servidor, domínio ou API no plano. Quanto custa manter cada cliente no ar?")
    if not cats & {"contabilidade"}:
        add("dica", "Sem contador no plano", "Mesmo no MEI vale prever a declaração anual; no Simples, o contador costuma custar de R$ 150 a R$ 400/mês.")
    anuais = [c for c in p["custos"] if c.get("frequencia") == "anual"]
    if anuais:
        add("dica", f"{len(anuais)} custo(s) anual(is)", "Eles pesam num mês só: separe 1/12 por mês para não ser pego de surpresa ("
            + ", ".join(f"{c['item']} {financeiro.reais(float(c['valor']))}" for c in anuais[:3]) + ").")
    if not p["custos"]:
        add("alto", "Plano sem custos", "Cadastre as ferramentas (Claude, Heygen…), servidor, domínios, anúncios e impostos.")
    if p.get("pro_labore"):
        meses_ok = sum(1 for m in proj if m["sobra_para_voce"] >= 0)
        if meses_ok < 12:
            eq = equilibrio(p)
            add("alto" if meses_ok < 6 else "medio", f"A empresa te paga em {meses_ok} de 12 meses",
                f"Para cobrir os custos fixos e os seus {financeiro.reais(float(p['pro_labore']))}/mês, são uns {eq['clientes_para_te_pagar']} clientes de CRM "
                f"({financeiro.reais(eq['liquido_por_cliente'])} líquido cada).")
    else:
        add("medio", "Quanto você precisa tirar?", "Informe o pró-labore desejado: o plano mostra em quais meses a empresa já te paga e quantos clientes faltam.")
    if not float(p.get("taxa_recebimento") or 0):
        add("dica", "Taxas de recebimento", "Boleto, cartão e link de pagamento custam de 1% a 5%. Se receber por Pix, pode deixar zero.")
    ordem = {"alto": 0, "medio": 1, "dica": 2}
    return sorted(achados, key=lambda a: ordem[a["nivel"]])


def precos() -> list[dict]:
    """Leituras de preço a partir do catálogo: juros embutidos no parcelado, margem do CRM, ideias para testar."""
    cat = financeiro.produtos()
    out = []
    site, crm, hosp = cat.get("site"), cat.get("crm"), cat.get("hospedagem")
    if site and site.get("parcelas") and site.get("parcela") and site.get("avista"):
        total = site["parcelas"] * site["parcela"]
        # taxa mensal que iguala as parcelas ao valor à vista (juros embutidos), por bisseção
        lo, hi = 0.0, 0.2
        for _ in range(60):
            mid = (lo + hi) / 2
            vp = sum(site["parcela"] / (1 + mid) ** k for k in range(1, site["parcelas"] + 1))
            lo, hi = (mid, hi) if vp > site["avista"] else (lo, mid)
        juros = f"{lo * 100:.1f}".replace(".", ",")
        out.append({"produto": "site", "titulo": f"Parcelado custa {total / site['avista'] - 1:.0%} a mais",
                    "detalhe": f"{site['parcelas']}x {financeiro.reais(site['parcela'])} = {financeiro.reais(total)} contra {financeiro.reais(site['avista'])} à vista: "
                               f"juros embutidos de uns {juros}% ao mês. Se o cliente atrasar parcelas, a margem some: peça entrada de 30% ou cobre a 1ª parcela na assinatura do contrato."})
    if crm and crm.get("mensal"):
        out.append({"produto": "crm", "titulo": "Plano anual do CRM",
                    "detalhe": f"12 meses por 10 ({financeiro.reais(crm['mensal'] * 10)} à vista ou 12x {financeiro.reais(crm['mensal'] * 10 / 12)}): "
                               "caixa adiantado e menos cancelamento. Ofereça no fim do teste grátis para quem já está usando."})
        out.append({"produto": "crm", "titulo": "Taxa de implantação",
                    "detalhe": "Hoje o CRM não cobra implantação. Uma taxa única (configuração do WhatsApp, funil e treinamento da equipe) "
                               "paga o seu tempo no início e filtra quem não vai usar. Pode ser isenta para quem fecha no plano anual."})
    if site and hosp and hosp.get("mensal"):
        out.append({"produto": "hospedagem", "titulo": "Hospedagem é a receita que fica",
                    "detalhe": f"{financeiro.reais(hosp['mensal'])}/mês por site soma {financeiro.reais(hosp['mensal'] * 12)} no ano por cliente. "
                               "Todo site vendido deveria sair com a hospedagem já assinada (está no formulário de venda)."})
    return out


def relatorio(p: dict) -> str:
    proj, eq = projetar(p), equilibrio(p)
    reg = REGIMES.get(p.get("regime") or "", {})
    total = lambda k: sum(m[k] for m in proj)
    L = [f"# Plano {p['ano']}", "", f"Regime: {reg.get('nome', 'não informado')} · pró-labore desejado {financeiro.reais(float(p.get('pro_labore') or 0))}/mês", "",
         f"**Receita provável no ano {financeiro.reais(total('receita_provavel'))}** (certa {financeiro.reais(total('receita_certa'))}, "
         f"se tudo fechar {financeiro.reais(total('receita_se_tudo_fechar'))}) · custos {financeiro.reais(total('custos'))} · impostos {financeiro.reais(total('imposto'))} · "
         f"resultado {financeiro.reais(total('resultado'))}", "",
         f"Equilíbrio: {eq['clientes_para_custos'] or '—'} clientes de CRM pagam os custos; {eq['clientes_para_te_pagar'] or '—'} pagam também você.", "",
         "## O que olhar", ""]
    L += [f"- **{a['titulo']}** ({a['nivel']}): {a['detalhe']}" for a in auditar(p)]
    L += ["", "## Mês a mês", "", "| Mês | Receita provável | Custos | Impostos | Resultado | Acumulado | Sobra para você |", "|---|---|---|---|---|---|---|"]
    L += [f"| {m['mes']} | {financeiro.reais(m['receita_provavel'])} | {financeiro.reais(m['custos'])} | {financeiro.reais(m['imposto'])} | "
          f"{financeiro.reais(m['resultado'])} | {financeiro.reais(m['acumulado'])} | {financeiro.reais(m['sobra_para_voce'])} |" for m in proj]
    L += ["", "## Ideias de preço", ""] + [f"- **{x['titulo']}**: {x['detalhe']}" for x in precos()]
    return "\n".join(L) + "\n"


def importar_clientes(p: dict) -> int:
    """Traz para o plano os clientes que já estão no financeiro (assinaturas ativas e em teste), sem repetir."""
    ja = {(n.get("cliente"), n.get("produto")) for n in p["negocios"]}
    novos = 0
    for c in financeiro.ler(financeiro.CLIENTES, financeiro.C_CLIENTE):
        if c["status"] not in ("ativo", "teste") or not float(c["valor_mensal"] or 0):
            continue
        prod = c["plano"] or "crm"
        if (c["empresa"], prod) in ja:
            continue
        p["negocios"].append({"cliente": c["empresa"], "produto": prod, "tipo": "mensal", "valor": float(c["valor_mensal"]),
                              "inicio": f"{p['ano']}-01", "status": "fechado" if c["status"] == "ativo" else "negociando"})
        novos += 1
    return novos


# ---------------------------------------------------------------- edição pela janela (Financeiro → Plano do ano)

TIPOS = ["mensal", "parcelas", "unico"]
FREQ = ["mensal", "anual", "unico"]
CATEGORIAS = ["ferramentas", "servidor", "infraestrutura", "hospedagem", "anuncios", "contabilidade", "terceiros", "impostos", "outros"]


def _mes(v, padrao=""):
    t = str(v or padrao).strip()[:7]
    if t and not (len(t) == 7 and t[4] == "-" and t[:4].isdigit() and t[5:].isdigit() and 1 <= int(t[5:]) <= 12):
        raise ValueError("mês inválido (use AAAA-MM)")
    return t


def _valor(v, nome):
    n = financeiro.num(v) if isinstance(v, str) else float(v or 0)
    if n < 0 or n > 10**8:
        raise ValueError(f"{nome} inválido")
    return round(n, 2)


def salvar_item(lista: str, d: dict) -> dict:
    """Inclui (ou troca, com `i`) um negócio ou um custo do plano."""
    p = ler()
    try:
        if lista == "negocios":
            nome = str(d.get("cliente") or "").strip()[:120]
            if not nome:
                raise ValueError("preencha o cliente")
            item = {"cliente": nome, "produto": str(d.get("produto") or "outro")[:30], "tipo": d.get("tipo") if d.get("tipo") in TIPOS else "mensal",
                    "valor": _valor(d.get("valor"), "valor"), "inicio": _mes(d.get("inicio"), f"{p['ano']}-01"),
                    "status": d.get("status") if d.get("status") in STATUS else "fechado"}
            if item["tipo"] == "parcelas":
                item["parcelas"] = int(d.get("parcelas") or 1)
            if d.get("fim"):
                item["fim"] = _mes(d["fim"])
            if d.get("chance") not in (None, ""):
                item["chance"] = max(0.0, min(1.0, _valor(d["chance"], "chance") / 100))
        elif lista == "custos":
            nome = str(d.get("item") or "").strip()[:120]
            if not nome:
                raise ValueError("preencha o custo")
            item = {"item": nome, "valor": _valor(d.get("valor"), "valor"), "frequencia": d.get("frequencia") if d.get("frequencia") in FREQ else "mensal",
                    "categoria": d.get("categoria") if d.get("categoria") in CATEGORIAS else "outros"}
            if item["frequencia"] in ("anual", "unico"):
                item["mes"] = _mes(d.get("mes"), f"{p['ano']}-01")
            if d.get("inicio"):
                item["inicio"] = _mes(d["inicio"])
        else:
            raise ValueError("lista inválida")
    except ValueError as e:
        return {"ok": False, "saida": str(e)}
    i = d.get("i")
    if i not in (None, "") and 0 <= int(i) < len(p[lista]):
        p[lista][int(i)] = item
    else:
        p[lista].append(item)
    gravar(p)
    return {"ok": True, "saida": f"{'negócio' if lista == 'negocios' else 'custo'} salvo: {item.get('cliente') or item.get('item')}"}


def remover_item(lista: str, i) -> dict:
    p = ler()
    if lista not in ("negocios", "custos") or not 0 <= int(i) < len(p[lista]):
        return {"ok": False, "saida": "item não encontrado"}
    tirado = p[lista].pop(int(i))
    gravar(p)
    return {"ok": True, "saida": f"removido: {tirado.get('cliente') or tirado.get('item')}"}


def configurar(d: dict) -> dict:
    p = ler()
    try:
        if d.get("ano"):
            p["ano"] = int(d["ano"])
        if d.get("regime") is not None:
            if d["regime"] not in ("", *REGIMES):
                raise ValueError("regime inválido")
            p["regime"] = d["regime"]
        for campo, nome in (("pro_labore", "pró-labore"),):
            if d.get(campo) not in (None, ""):
                p[campo] = _valor(d[campo], nome)
        for campo in ("churn_mensal", "taxa_recebimento"):
            if d.get(campo) not in (None, ""):
                p[campo] = min(0.5, _valor(d[campo], campo) / 100)  # a janela manda em %
    except ValueError as e:
        return {"ok": False, "saida": str(e)}
    gravar(p)
    return {"ok": True, "saida": "plano atualizado"}


def para_janela() -> dict:
    p = ler()
    return {"plano": p, "projecao": projetar(p), "auditoria": auditar(p), "equilibrio": equilibrio(p), "precos": precos(),
            "regimes": {k: {"nome": v["nome"], "nota": v["nota"], "aliquota": v["aliquota"], "fixo": v["fixo"]} for k, v in REGIMES.items()}, "status": STATUS,
            "categorias": CATEGORIAS, "existe": arquivo().exists()}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ano", type=int)
    a = ap.parse_args()
    p = ler()
    if a.ano:
        p["ano"] = a.ano
    texto = relatorio(p)
    destino = financeiro.PASTA / "relatorios" / f"plano-{p['ano']}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    print(texto)
    print(f"-> {destino}")


if __name__ == "__main__":
    main()
