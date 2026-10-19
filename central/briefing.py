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
import financeiro  # noqa: E402
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
            f"Cobrar {len(fin['atrasadas'])} fatura(s) atrasada(s) ({financeiro.reais(total)}): `python central/financeiro.py cobrar`")
    for alerta in fin["alertas"]:
        if alerta.startswith("caixa previsto"):
            add(85, "financeiro", f"Atenção ao caixa: {alerta}")
        elif "NPS" in alerta:
            add(75, "sucesso-cliente", f"Ligar para {alerta.split(': ', 1)[-1]} (nota baixa, risco de cancelar)")
        elif "classificar" in alerta:
            add(20, "financeiro", f"{alerta}: ajuste financeiro/categorias.json")
    if fin["posvenda_devidos"]:
        add(55, "sucesso-cliente", f"{fin['posvenda_devidos']} mensagem(ns) de pós-venda: `python central/financeiro.py posvenda`")

    leads = ler_leads()
    quentes = [l for l in leads if l["etapa"] in QUENTES]
    parados = [l for l in quentes if (d := data_ou_none(l.get("ultimo_contato"))) and (ref - d).days >= 1]
    if parados:
        nomes = ", ".join(f"#{l['id']} {l['empresa'][:25]}" for l in parados[:3])
        add(95, "closer", f"Responder {len(parados)} lead(s) quente(s) parado(s) desde ontem ou antes: {nomes}")
    devidos = [l for l in leads if l["etapa"] == "contatado" and l.get("proximo_contato") and l["proximo_contato"] <= ref.isoformat()]
    if devidos:
        add(70, "sdr", f"Enviar {len(devidos)} follow-up(s) do dia: `python central/sdr.py hoje`")
    fila = sum(l["etapa"] == "novo" for l in leads)
    if fila < 15:
        add(50, "sdr", f"Fila com {fila} lead(s) novo(s): gerar mais (consultas → buscar → qualificar)")

    for rot in sorted((RAIZ / "roteiros").glob("20??-??-??-*.json")):
        quando = financeiro.data(rot.name[:10])
        faltam = (quando - ref).days
        if 0 <= faltam <= 7 and not (RAIZ / "midia" / "final" / f"{rot.stem}.mp4").exists():
            add(80 if faltam <= 2 else 60, "produtor-video", f"Post de {quando:%d/%m} ({rot.stem[11:]}) ainda sem vídeo final")

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
        L.append("- **Financeiro** ainda sem dados: cadastre o 1º cliente (`financeiro.py cliente`) e importe o extrato do banco")
    if leads:
        por = {e: sum(l["etapa"] == e for l in leads) for e in ("novo", "contatado", *QUENTES, "cliente")}
        L.append("- **Comercial** " + " · ".join(f"{k} {v}" for k, v in por.items()))
    else:
        L.append("- **Comercial** sem leads ainda: `/comercial` ou `python central/sdr.py consultas`")
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
