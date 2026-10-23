"""Chefe de Gabinete: o resumo do dia do Mateus (caixa, vendas, conteúdo) com as 3 prioridades e quem cobra cada pendência.

Lê só o que as outras ferramentas já gravam no PC: financeiro/, comercial/leads.csv, metricas/, radar/, roteiros/,
midia/final/ e estado/eventos.jsonl. Não usa internet nem créditos, então pode rodar sozinho às 7h (agendar.cmd).

  python central/briefing.py              # resumo do dia -> estado/briefing/AAAA-MM-DD.md
  python central/briefing.py --semana     # placar da semana (para a revisão de sexta)
"""
import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))
import atendimento  # noqa: E402
import carteira  # noqa: E402
import conteudo  # noqa: E402
import decisoes  # noqa: E402
import financeiro  # noqa: E402
import gastos  # noqa: E402
import metas  # noqa: E402
import plano  # noqa: E402
import sdr  # noqa: E402
import status  # noqa: E402

LEADS = RAIZ / "comercial" / "leads.csv"
QUENTES = ("respondeu", "demo", "proposta")
DIAS_PT = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def ler_leads():
    if not LEADS.exists():
        return []
    with LEADS.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def data_ou_none(t):
    try:
        return financeiro.data(t)
    except ValueError:
        return None


def ultimo_arquivo(pasta, padrao):
    arqs = [p for p in pasta.glob(padrao) if re.match(r"\d{4}-\d{2}-\d{2}", p.name.split("concorrentes-")[-1])]
    return max(arqs, key=lambda p: (re.search(r"\d{4}-\d{2}-\d{2}", p.name).group(0), p.stat().st_mtime)) if arqs else None


def idade(arq, ref):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", arq.name) if arq else None
    return (ref - financeiro.data(m.group(1))).days if m else None


# ---------------------------------------------------------------- o que cada área tem pendente

def coletar(ref):
    """Lista de itens {peso, dono, texto}: o peso decide as 3 prioridades; o resto vira pendência."""
    itens = []
    add = lambda peso, dono, texto: itens.append({"peso": peso, "dono": dono, "texto": texto})

    fin = financeiro.situacao(ref)
    if fin["atrasadas"]:
        total = sum(f["valor"] for f in fin["atrasadas"])
        add(100 + max(f["dias"] for f in fin["atrasadas"]), "financeiro",
            f"Cobrar {len(fin['atrasadas'])} fatura(s) atrasada(s) ({financeiro.reais(total)}): Financeiro → Cobrança e pós-venda (ou `python central/financeiro.py cobrar`)")
    for alerta in fin["alertas"]:
        if alerta.startswith("caixa previsto"):
            add(85, "financeiro", f"Atenção ao caixa: {alerta}")
        elif "NPS" in alerta:
            pass  # a saúde da carteira (abaixo) já cobre nota baixa, com o motivo e a mensagem
        elif "classificar" in alerta:
            add(20, "financeiro", f"{alerta}: Financeiro → Lançamentos")
    for t in fin.get("testes", []):
        if t["dias"] <= 5:
            quando = f"acabou há {-t['dias']} dia(s)" if t["dias"] < 0 else ("acaba hoje" if t["dias"] == 0 else f"acaba em {t['dias']} dia(s)")
            add(92 if t["dias"] <= 1 else 78, "closer",
                f"Teste grátis de {t['empresa']} {quando}: ligue e feche ({financeiro.reais(t['valor'])}/mês). Fechou? Financeiro → Clientes → Virou cliente")
    cart = carteira.carteira(ref)
    for s in [s for s in cart["clientes"] if s["nivel"] == "risco" and s["atraso"] <= 3][:3]:  # atraso já está na cobrança
        add(76, "sucesso-cliente", f"{s['empresa']} em risco de cancelar ({'; '.join(s['motivos'][:2])}): {s['acao'].lower()}, mensagem pronta em Financeiro → Clientes")
    conversar = [s for s in cart["clientes"] if s["nivel"] == "atencao" and s["sem_conversa"] > 45]
    if conversar:
        add(42, "sucesso-cliente", f"Puxar conversa com {len(conversar)} cliente(s) sem contato há mais de 45 dias ({', '.join(s['empresa'] for s in conversar[:3])}): Financeiro → Clientes")
    if cart["promotores"]:
        add(31, "sucesso-cliente", f"{len(cart['promotores'])} cliente(s) que deram 9 ou 10: pedir indicação (Financeiro → Clientes)")
    if fin["posvenda_devidos"]:
        add(55, "sucesso-cliente", f"{fin['posvenda_devidos']} mensagem(ns) de pós-venda: Financeiro → Cobrança e pós-venda (ou `python central/financeiro.py posvenda`)")

    leads = ler_leads()
    quentes = [l for l in leads if l["etapa"] in QUENTES]
    parados = [l for l in quentes if (d := data_ou_none(l.get("ultimo_contato"))) and (ref - d).days >= 1]
    if parados:
        nomes = ", ".join(f"#{l['id']} {l['empresa'][:25]}" for l in parados[:3])
        add(95, "closer", f"Responder {len(parados)} lead(s) quente(s) parado(s) desde ontem ou antes: {nomes}")
    ag = sdr.agenda(ref, dias=1)
    for d in ag["proximas"]:
        hora = d["quando"][11:16]
        add(97 if d["dias"] == 0 else 66, "closer", f"Demo {'hoje' if d['dias'] == 0 else 'amanhã'} às {hora} com {d['empresa']}: mande o lembrete (Comercial → Hoje → Agenda)")
    for d in ag["sem_desfecho"][:3]:
        add(74, "closer", f"Como foi a demo com {d['empresa']} ({d['quando'][8:10]}/{d['quando'][5:7]})? Marque proposta, cliente ou perdido")
    devidos = [l for l in leads if l["etapa"] == "contatado" and l.get("proximo_contato") and l["proximo_contato"] <= ref.isoformat()]
    if devidos:
        add(70, "sdr", f"Enviar {len(devidos)} follow-up(s) do dia: Comercial → Hoje (ou `python central/sdr.py hoje`)")
    fila = sum(l["etapa"] == "novo" for l in leads)
    if fila < 15:
        add(50, "sdr", f"Fila com {fila} lead(s) novo(s): gerar mais (consultas → buscar → qualificar)")

    # conteúdo: post perto de sair sem vídeo, pronto sem agendar, rascunho esquecido, semana com poucos posts
    for alerta in conteudo.alertas(conteudo.quadro(raiz=RAIZ, ref=ref), ref):
        dono = "postagem" if ("agendado" in alerta or "publicação" in alerta) else ("roteirista" if "meta é 3" in alerta else "produtor-video")
        add((90 if "sai hoje" in alerta else 80) if " sai " in alerta else 62 if "publicação" in alerta else 48, dono, alerta)

    # o que costuma passar despercebido no financeiro
    clientes = financeiro.ler(financeiro.CLIENTES, financeiro.C_CLIENTE)
    ativos = [c for c in clientes if c["status"] == "ativo" and float(c["valor_mensal"] or 0)]
    mes = ref.strftime("%Y-%m")
    faturas = financeiro.ler(financeiro.FATURAS, financeiro.C_FATURA)
    if ativos and ref.day >= 1 and not any(f["competencia"] == mes and not f["descricao"].startswith("Site") for f in faturas):
        add(82, "financeiro", f"As faturas de {ref:%m/%Y} ainda não foram geradas ({len(ativos)} assinatura(s)): Financeiro → Gerar faturas")
    sem_zap = [c["empresa"] for c in ativos if not (c.get("whatsapp") or "").strip()]
    if sem_zap:
        add(35, "financeiro", f"Cliente(s) sem WhatsApp cadastrado, sem como cobrar ou mandar pós-venda: {', '.join(sem_zap[:3])}")
    peso_gasto = {"dobro": 72, "parou": 64, "subiu": 46, "nova": 34}
    for a in [a for a in gastos.analisar(ref)["alertas"] if a["tipo"] in peso_gasto][:3]:
        add(peso_gasto[a["tipo"]], "financeiro", f"{a['texto']} (Financeiro → Lançamentos)")
    faltam = [x for x in atendimento.ler() if not x["completa"]]
    if faltam:
        add(33, "sucesso-cliente", f"{len(faltam)} resposta(s) do FAQ em branco (ex.: {faltam[0]['pergunta']}): Atendimento → FAQ incompleto")
    ops = financeiro.oportunidades()
    if ops:
        add(38, "closer", f"{len(ops)} cliente(s) prontos para o 2º produto (site ou CRM): Comercial → Hoje → Vender para quem já é cliente")
    try:
        p = plano.ler()
        if p["negocios"] or p["custos"]:
            for a in [a for a in plano.auditar(p) if a["nivel"] == "alto"][:2]:
                add(58, "financeiro", f"Plano {p['ano']}: {a['titulo']}. {a['detalhe']}")
    except (OSError, ValueError, KeyError):
        pass

    # meta de crescimento: a semana está no ritmo? e as decisões que pediram para rever
    try:
        r = metas.calcular(ref=ref)
        if r["tem_meta"] and r.get("atras") and ref.weekday() < 5:
            s = r["por_semana"]
            add(57, "sdr", f"Semana atrás do ritmo da meta ({r['meta']} clientes até {r['ate'][5:7]}/{r['ate'][2:4]}): {', '.join(r['atras'])}. "
                f"Hoje dá para tirar o atraso com umas {max(1, round(s['abordagens'] / 5))} abordagens: Comercial → Hoje")
        for x in decisoes.para_rever(ref)[:2]:
            add(52, "financeiro", f"Rever a decisão \"{x['titulo']}\" ({'adiada' if x['estado'] == 'adiada' else 'regra da casa'}): Financeiro → Metas e decisões")
    except (OSError, ValueError, KeyError):
        pass

    retrato = ultimo_arquivo(RAIZ / "metricas", "20??-??-??.json")
    dias = idade(retrato, ref)
    if dias is None or dias >= 7:
        add(45, "analista", "Retrato semanal do Instagram " + (f"tem {dias} dias" if dias is not None else "nunca foi feito") + ": rode /segunda")
    radar = ultimo_arquivo(RAIZ / "radar", "20??-??-??*.md")
    dias = idade(radar, ref)
    if dias is None or dias >= 7:
        add(40, "pesquisador-mercado", "Radar de tendências " + (f"tem {dias} dias" if dias is not None else "nunca rodou") + ": `python central/radar.py`")
    vigia = ultimo_arquivo(RAIZ / "radar", "concorrentes-*.md")
    if vigia and (idade(vigia, ref) or 0) <= 7 and "**mudou**" in vigia.read_text(encoding="utf-8"):
        add(65, "pesquisador-mercado", f"Concorrente mudou preço ou oferta: ver {vigia.relative_to(RAIZ).as_posix()}")
    elif not vigia or (idade(vigia, ref) or 0) >= 7:
        add(30, "pesquisador-mercado", "Vigia de concorrentes da semana: `python central/vigia.py checar`")

    for agente, e in status.ultimo_estado()["agentes"].items():
        if e["estado"] == "esperando":
            add(88, "Mateus", f"{agente} espera sua aprovação: {e['tarefa']}")
        elif e["estado"] == "erro":
            add(60, agente, f"terminou com erro: {e['tarefa']}")
    return sorted(itens, key=lambda i: -i["peso"]), fin, leads


def numeros(fin, leads, ref):
    L = []
    if fin["tem_dados"]:
        prev = fin["previsao"][30]
        L.append(f"- **Caixa** {financeiro.reais(fin['caixa'])} (em 30 dias ≈ {financeiro.reais(prev)}) · **MRR** "
                 f"{financeiro.reais(fin['mrr'])} · {fin['clientes_ativos']} clientes"
                 + (f" · fôlego {fin['runway_meses']} meses" if fin["runway_meses"] else ""))
    else:
        L.append("- **Financeiro** ainda sem dados: na janela Financeiro, **+ Cliente** e **Importar extrato** (funciona sem o Claude)")
    if leads:
        por = {e: sum(l["etapa"] == e for l in leads) for e in ("novo", "contatado", *QUENTES, "cliente")}
        L.append("- **Comercial** " + " · ".join(f"{k} {v}" for k, v in por.items()))
    else:
        L.append("- **Comercial** sem leads ainda: Comercial → **Buscar leads** (sem o Claude) ou `/comercial`")
    retrato = ultimo_arquivo(RAIZ / "metricas", "20??-??-??.json")
    if retrato:
        p = json.loads(retrato.read_text(encoding="utf-8"))["perfil"]
        L.append(f"- **Instagram** {p['seguidores']} seguidores · alcance {p.get('alcance', 0)} (retrato de {retrato.stem[8:10]}/{retrato.stem[5:7]})")
    proximos = [r for r in sorted((RAIZ / "roteiros").glob("20??-??-??-*.json")) if r.name[:10] >= ref.isoformat()]
    if proximos:
        L.append(f"- **Próximo post** {proximos[0].name[8:10]}/{proximos[0].name[5:7]}: {proximos[0].stem[11:]}")
    return L


def briefing(ref):
    itens, fin, leads = coletar(ref)
    L = [f"# Bom dia, Mateus · {DIAS_PT[ref.weekday()]} {ref:%d/%m}", "", "## As 3 prioridades de hoje", ""]
    top = itens[:3]
    L += [f"{n}. {i['texto']} _(com: {i['dono']})_" for n, i in enumerate(top, 1)] or ["Nada urgente. Bom dia para gravar conteúdo ou prospectar."]
    L += ["", "## Números", ""] + numeros(fin, leads, ref)
    if itens[3:]:
        L += ["", "## Pendências (quem cobra)", ""] + [f"- [{i['dono']}] {i['texto']}" for i in itens[3:]]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- placar da semana

def placar(ref):
    ini = ref - dt.timedelta(days=6)
    na_semana = lambda t: (d := data_ou_none(t)) is not None and ini <= d <= ref
    leads = ler_leads()
    contatos = [l for l in leads if na_semana(l.get("ultimo_contato"))]
    clientes = financeiro.ler(financeiro.CLIENTES, financeiro.C_CLIENTE)
    novos = [c for c in clientes if na_semana(c["inicio"])]
    perdidos = [c for c in clientes if na_semana(c["cancelado_em"])]
    fin = financeiro.situacao(ref)
    retratos = sorted((RAIZ / "metricas").glob("20??-??-??.json"))
    L = [f"# Placar da semana · {ini:%d/%m} a {ref:%d/%m}", "", "| Indicador | Semana |", "|---|---|",
         f"| Leads trabalhados (contato na semana) | {len(contatos)} |",
         f"| Responderam / demo / proposta | {sum(l['etapa'] in QUENTES for l in contatos)} |",
         f"| Clientes novos | {len(novos)} (+{financeiro.reais(sum(float(c['valor_mensal']) for c in novos))} MRR) |",
         f"| Cancelamentos | {len(perdidos)} |",
         f"| MRR atual | {financeiro.reais(fin['mrr'])} |",
         f"| Caixa | {financeiro.reais(fin['caixa'])} |"]
    if retratos:
        atual = json.loads(retratos[-1].read_text(encoding="utf-8"))["perfil"]
        antes = json.loads(retratos[-2].read_text(encoding="utf-8"))["perfil"]["seguidores"] if len(retratos) > 1 else atual.get("seguidores_inicio")
        L.append(f"| Seguidores | {atual['seguidores']} ({atual['seguidores'] - (antes or atual['seguidores']):+d}) |")
    gasto = 0.0
    for p in (RAIZ / "anuncios").glob("*.json"):
        try:
            gasto += sum(c.get("gasto", 0) for c in json.loads(p.read_text(encoding="utf-8")).get("campanhas", []))
        except ValueError:
            pass
    if gasto:
        L.append(f"| Anúncios (acumulado) | {financeiro.reais(gasto)} |")
    itens, _, _ = coletar(ref)
    L += ["", "## Para a próxima semana", ""] + [f"- {i['texto']} _(com: {i['dono']})_" for i in itens[:5]]
    return "\n".join(L) + "\n"


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--semana", action="store_true", help="placar da semana em vez do resumo do dia")
    ap.add_argument("--data", help="AAAA-MM-DD (padrão: hoje)")
    a = ap.parse_args()
    ref = financeiro.data(a.data) if a.data else dt.date.today()
    texto = placar(ref) if a.semana else briefing(ref)
    destino = RAIZ / "estado" / "briefing" / f"{'placar-' if a.semana else ''}{ref.isoformat()}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    status.registrar("chefe-gabinete", "pronto", f"{'placar da semana' if a.semana else 'briefing do dia'} em {destino.name}")
    print(texto)
    print(f"-> {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
