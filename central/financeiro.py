"""Financeiro da Ciello: assinaturas do CIELLO CRM, cobrança, extrato do banco, caixa e números de crescimento.

Faz o papel do "Agente Financeiro" (classifica despesa, cobra fatura atrasada, marca o que não bate, prevê o caixa)
e do pós-venda (boas-vindas, NPS, pedido de avaliação no Google, indicação). Só biblioteca padrão.

Fluxo do mês:
  python central/financeiro.py cliente --empresa "Imobiliária X" --valor 149 --dia 10 --whatsapp 49999998888
  python central/financeiro.py cliente --lead 12 --valor 149 --dia 10      # puxa empresa e WhatsApp do comercial/leads.csv
  python central/financeiro.py faturar                  # faturas do mês para todos os clientes ativos
  python central/financeiro.py importar extrato.ofx     # extrato do banco (OFX ou CSV): classifica e dá baixa nas faturas
  python central/financeiro.py cobrar                   # faturas atrasadas 3, 7 e 14 dias: mensagens com link wa.me
  python central/financeiro.py enviado cobranca 7       # registra que a cobrança da fatura 7 foi enviada
  python central/financeiro.py posvenda                 # boas-vindas D+1, uso D+7, NPS D+30, avaliação, indicação D+90
  python central/financeiro.py nps 3 10                 # nota do cliente 3 (9–10 recebe o pedido de avaliação no Google)
  python central/financeiro.py resumo                   # MRR, churn, CAC, LTV, caixa, previsão 30/60/90 dias, o que não bate

Produtos e preços: comercial/produtos.json (CRM com 30 dias grátis, site à vista ou parcelado, hospedagem).
  python central/financeiro.py cliente --empresa "X" --produto crm --teste 30     # começa no teste grátis
  python central/financeiro.py converter 4                                        # o teste virou assinatura
  python central/financeiro.py venda --empresa "Y" --forma parcelado              # site 12x, mais a hospedagem

Outros: pago, cancelar, editar, lancar (Pix/dinheiro fora do extrato), categoria (classificar na mão),
config (saldo inicial, alerta de saldo, link de avaliação).

Tudo isso também funciona pela janela Financeiro do Ciello OS, sem o Claude.

Os dados ficam em financeiro/ (fora do git: o repositório é público). Só financeiro/categorias.json vai para o git.
Mensagens nunca são enviadas daqui: você revisa e envia do seu WhatsApp.
"""
import argparse
import calendar
import csv
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = Path(os.environ.get("CIELLO_FINANCEIRO") or RAIZ / "financeiro")  # outra pasta só para testes e simulações
CLIENTES, FATURAS, LANCAMENTOS = PASTA / "clientes.csv", PASTA / "faturas.csv", PASTA / "lancamentos.csv"
CONFIG = PASTA / "config.json"
REGRAS = RAIZ / "financeiro" / "categorias.json"  # regras versionadas no git, valem para qualquer pasta de dados
LEADS = RAIZ / "comercial" / "leads.csv"
PRODUTOS = RAIZ / "comercial" / "produtos.json"  # produtos e preços de lista (CRM, site, hospedagem)
C_CLIENTE = ["id", "empresa", "contato", "whatsapp", "plano", "valor_mensal", "dia_vencimento", "inicio", "status",
             "cancelado_em", "motivo", "lead_id", "nps", "posvenda", "obs", "teste_ate", "ultimo_contato"]
C_FATURA = ["id", "cliente_id", "competencia", "vencimento", "valor", "pago_em", "lancamento", "cobrancas", "descricao"]
C_LANC = ["id", "data", "descricao", "valor", "categoria", "fitid", "fatura_id", "origem"]
COBRANCA = [3, 7, 14]                    # dias de atraso
POSVENDA = [1, 7, 30, 90]                # dias desde o início
SEM_CATEGORIA = "a classificar"
RECEITA = "Receita de assinaturas"
RECEITA_SITES = "Receita de sites"
FORA_DO_RESULTADO = {"Transferência entre contas", "Aplicação/resgate"}


# ---------------------------------------------------------------- arquivos

def ler(caminho, campos):
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8", newline="") as f:
        return [{k: (r.get(k) or "") for k in campos} for r in csv.DictReader(f)]


def gravar(caminho, campos, linhas):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for l in linhas:
            w.writerow({k: l.get(k, "") for k in campos})


def config():
    base = {"saldo_inicial": 0.0, "data_saldo": "", "alerta_saldo": 1000.0, "link_avaliacao": "", "assinatura": "Mateus"}
    if CONFIG.exists():
        base.update(json.loads(CONFIG.read_text(encoding="utf-8")))
    return base


def salvar_config(cfg):
    PASTA.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")


def produtos() -> dict:
    """Catálogo de comercial/produtos.json, por id (crm, site, hospedagem)."""
    try:
        return {p["id"]: p for p in json.loads(PRODUTOS.read_text(encoding="utf-8"))["produtos"]}
    except (OSError, ValueError, KeyError):
        return {}


def proximo_id(linhas):
    return max([int(l["id"]) for l in linhas if str(l["id"]).isdigit()] or [0]) + 1


# ---------------------------------------------------------------- números, datas e texto

def num(t, br=True):
    """'1.234,56' → 1234.56 · '-50.00' → -50.0 · 'R$ 149' → 149.0. br=False: ponto é sempre decimal (OFX)."""
    s = re.sub(r"[^\d,.\-]", "", str(t or "").replace("−", "-"))
    if not s or s in "-.,":
        return 0.0
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    elif br and re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")  # 1.234 no padrão brasileiro é mil duzentos e trinta e quatro
    return float(s)


def data(t):
    t = str(t or "").strip()
    for fmt, n in (("%Y%m%d", 8), ("%Y-%m-%d", 10), ("%d/%m/%Y", 10), ("%d/%m/%y", 8)):
        try:
            return dt.datetime.strptime(t[:n], fmt).date()
        except ValueError:
            continue
    raise ValueError(f"data que não entendi: {t!r}")


def hoje():
    return dt.date.today()


def reais(v):
    return ("-" if v < 0 else "") + "R$ " + f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def sem_acento(t):
    tabela = str.maketrans("áàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇ", "aaaaeeiooouucAAAAEEIOOOUUC")
    return (t or "").translate(tabela).lower()


def vencimento(competencia, dia):
    ano, mes = map(int, competencia.split("-"))
    return dt.date(ano, mes, min(int(dia), calendar.monthrange(ano, mes)[1]))


def meses_atras(mes, n):
    ano, m = map(int, mes.split("-"))
    m -= n
    while m <= 0:
        m += 12
        ano -= 1
    return f"{ano:04d}-{m:02d}"


def link_wa(fone, texto):
    d = re.sub(r"\D", "", fone or "")
    if len(d) in (10, 11):
        d = "55" + d
    return f"https://wa.me/{d}?text={urllib.parse.quote(texto)}" if d else ""


# ---------------------------------------------------------------- clientes e faturas

def cmd_cliente(a):
    clientes = ler(CLIENTES, C_CLIENTE)
    empresa, whatsapp = a.empresa, a.whatsapp
    if a.lead:
        lead = next((l for l in ler(LEADS, ["id", "empresa", "telefone"]) if l["id"] == str(a.lead)), None)
        if not lead:
            sys.exit(f"lead {a.lead} não está em {LEADS}")
        empresa, whatsapp = empresa or lead["empresa"], whatsapp or lead["telefone"]
    if not empresa:
        sys.exit("informe --empresa ou --lead")
    produto = produtos().get(getattr(a, "produto", "") or "", {})
    valor = a.valor if a.valor is not None else produto.get("mensal")
    if valor is None:
        sys.exit("informe --valor (ou --produto com preço em comercial/produtos.json)")
    inicio = a.inicio or hoje().isoformat()
    teste = getattr(a, "teste", 0) or 0
    c = {"id": proximo_id(clientes), "empresa": empresa, "contato": a.contato, "whatsapp": whatsapp,
         "plano": a.plano or getattr(a, "produto", "") or "", "valor_mensal": f"{valor:.2f}", "dia_vencimento": a.dia,
         "inicio": inicio, "status": "teste" if teste else "ativo", "lead_id": a.lead or "",
         "teste_ate": (data(inicio) + dt.timedelta(days=teste)).isoformat() if teste else ""}
    clientes.append(c)
    gravar(CLIENTES, C_CLIENTE, clientes)
    print(f"cliente #{c['id']} {empresa}: {reais(valor)}/mês, vence dia {a.dia}"
          + (f" · em teste grátis até {data(c['teste_ate']):%d/%m} (depois: Virou cliente)" if teste else "")
          + (f" · lembre: python central/sdr.py marcar {a.lead} cliente" if a.lead else ""))


def cmd_converter(a):
    """O teste grátis virou assinatura: passa a ativo e a 1ª fatura sai no próximo vencimento."""
    clientes = ler(CLIENTES, C_CLIENTE)
    c = achar(clientes, a.id, "cliente")
    if c["status"] != "teste":
        sys.exit(f"cliente #{c['id']} não está em teste (está {c['status']})")
    c.update(status="ativo", inicio=a.data or hoje().isoformat())
    if a.valor is not None:
        c["valor_mensal"] = f"{a.valor:.2f}"
    gravar(CLIENTES, C_CLIENTE, clientes)
    print(f"cliente #{c['id']} {c['empresa']}: assinatura ativa desde {data(c['inicio']):%d/%m}, {reais(float(c['valor_mensal']))}/mês")


def cmd_venda(a):
    """Venda de site: à vista (1 fatura) ou parcelada (N faturas mensais), mais a hospedagem como assinatura."""
    cat = produtos().get("site", {})
    clientes, faturas = ler(CLIENTES, C_CLIENTE), ler(FATURAS, C_FATURA)
    if a.cliente:
        c = achar(clientes, a.cliente, "cliente")
    else:
        empresa, whatsapp = a.empresa, a.whatsapp
        if a.lead:
            lead = next((l for l in ler(LEADS, ["id", "empresa", "telefone"]) if l["id"] == str(a.lead)), None)
            if not lead:
                sys.exit(f"lead {a.lead} não está em {LEADS}")
            empresa, whatsapp = empresa or lead["empresa"], whatsapp or lead["telefone"]
        if not empresa:
            sys.exit("informe --cliente, --empresa ou --lead")
        hosp = produtos().get("hospedagem", {})
        mensal = 0.0 if a.sem_hospedagem else (a.hospedagem if a.hospedagem is not None else hosp.get("mensal", 0.0))
        c = {"id": proximo_id(clientes), "empresa": empresa, "contato": a.contato, "whatsapp": whatsapp,
             "plano": "hospedagem" if mensal else "site", "valor_mensal": f"{mensal:.2f}", "dia_vencimento": a.dia,
             "inicio": a.inicio_hospedagem or hoje().isoformat(), "status": "ativo" if mensal else "projeto", "lead_id": a.lead or ""}
        clientes.append(c)
    parcelado = a.forma == "parcelado"
    n = a.parcelas or (cat.get("parcelas", 12) if parcelado else 1)
    valor = a.valor if a.valor is not None else (cat.get("parcela") if parcelado else cat.get("avista"))
    if valor is None:
        sys.exit("informe --valor (ou o preço do site em comercial/produtos.json)")
    primeira = data(a.primeira) if a.primeira else hoje()
    for i in range(n):
        ano, mes = primeira.year + (primeira.month - 1 + i) // 12, (primeira.month - 1 + i) % 12 + 1
        venc = dt.date(ano, mes, min(primeira.day, calendar.monthrange(ano, mes)[1]))
        faturas.append({"id": proximo_id(faturas), "cliente_id": c["id"], "competencia": venc.strftime("%Y-%m"),
                        "vencimento": venc.isoformat(), "valor": f"{valor:.2f}",
                        "descricao": f"Site parcela {i + 1}/{n}" if n > 1 else "Site à vista"})
    gravar(CLIENTES, C_CLIENTE, clientes)
    gravar(FATURAS, C_FATURA, faturas)
    total = valor * n
    print(f"site para {c['empresa']} (cliente #{c['id']}): " + (f"{n}x {reais(valor)} = {reais(total)}" if n > 1 else f"{reais(valor)} à vista")
          + f", 1º vencimento {primeira:%d/%m}" + (f" · hospedagem {reais(float(c['valor_mensal']))}/mês" if float(c["valor_mensal"] or 0) else ""))


def o_que(f, de=False) -> str:
    """Como chamar esta fatura na mensagem: "a mensalidade do CIELLO CRM"; com de=True, "da mensalidade...")."""
    d = f.get("descricao") or ""
    if d.startswith("Site parcela"):
        artigo, resto = "a", f"parcela {d.split()[-1]} do seu site"
    elif d.startswith("Site"):
        artigo, resto = "o", "pagamento do seu site"
    elif d == "Hospedagem" or (f.get("cliente") or {}).get("plano") == "hospedagem":
        artigo, resto = "a", "hospedagem do seu site"
    else:
        artigo, resto = "a", "mensalidade do CIELLO CRM"
    return f"{'d' if de else ''}{artigo} {resto}"


def cmd_cancelar(a):
    clientes = ler(CLIENTES, C_CLIENTE)
    c = achar(clientes, a.id, "cliente")
    c.update(status="cancelado", cancelado_em=a.data or hoje().isoformat(), motivo=a.motivo)
    gravar(CLIENTES, C_CLIENTE, clientes)
    print(f"cliente #{c['id']} {c['empresa']} cancelado ({c['motivo'] or 'sem motivo anotado'})")


def cmd_editar(a):
    clientes = ler(CLIENTES, C_CLIENTE)
    c = achar(clientes, a.id, "cliente")
    for campo in ("empresa", "contato", "whatsapp", "plano", "obs"):
        if getattr(a, campo) is not None:
            c[campo] = getattr(a, campo).strip()
    if a.valor is not None:
        c["valor_mensal"] = f"{a.valor:.2f}"
    if a.dia is not None:
        c["dia_vencimento"] = str(a.dia)
    if a.reativar:
        c.update(status="ativo", cancelado_em="", motivo="")
    gravar(CLIENTES, C_CLIENTE, clientes)
    print(f"cliente #{c['id']} {c['empresa']}: {reais(float(c['valor_mensal']))}/mês, vence dia {c['dia_vencimento']}, {c['status']}")


def achar(linhas, id_, nome):
    item = next((l for l in linhas if l["id"] == str(id_)), None)
    if not item:
        sys.exit(f"{nome} {id_} não encontrado")
    return item


def cmd_faturar(a):
    comp = a.mes or hoje().strftime("%Y-%m")
    faturas = ler(FATURAS, C_FATURA)
    existentes = {(f["cliente_id"], f["competencia"]) for f in faturas if not f["descricao"].startswith("Site")}
    novas = 0
    for c in ler(CLIENTES, C_CLIENTE):
        # 1ª fatura no 1º vencimento depois do início (antes disso é o período de teste)
        if c["status"] != "ativo" or not float(c["valor_mensal"] or 0) or (c["id"], comp) in existentes or vencimento(comp, c["dia_vencimento"]) < data(c["inicio"]):
            continue
        faturas.append({"id": proximo_id(faturas), "cliente_id": c["id"], "competencia": comp,
                        "vencimento": vencimento(comp, c["dia_vencimento"]).isoformat(), "valor": c["valor_mensal"],
                        "descricao": "Hospedagem" if c["plano"] == "hospedagem" else "Mensalidade"})
        novas += 1
    gravar(FATURAS, C_FATURA, faturas)
    print(f"{novas} faturas de {comp} criadas ({sum(f['competencia'] == comp for f in faturas)} no mês)")


def cmd_pago(a):
    faturas = ler(FATURAS, C_FATURA)
    f = achar(faturas, a.id, "fatura")
    f["pago_em"] = a.data or hoje().isoformat()
    gravar(FATURAS, C_FATURA, faturas)
    print(f"fatura #{f['id']} paga em {f['pago_em']}")


# ---------------------------------------------------------------- extrato do banco

def ler_ofx(caminho):
    """OFX 1.x (SGML) dos bancos brasileiros: tags folha sem fechamento, texto em latin-1 ou utf-8."""
    bruto = caminho.read_bytes()
    try:
        txt = bruto.decode("utf-8")
    except UnicodeDecodeError:
        txt = bruto.decode("cp1252", errors="replace")
    campo = lambda bloco, tag: (re.search(rf"<{tag}>([^<\r\n]*)", bloco, re.I) or [None, ""])[1].strip()
    itens = []
    for bloco in re.findall(r"<STMTTRN>(.*?)</STMTTRN>", txt, re.S | re.I):
        desc = " ".join(x for x in (campo(bloco, "NAME"), campo(bloco, "MEMO")) if x)
        itens.append({"data": data(campo(bloco, "DTPOSTED")).isoformat(), "valor": num(campo(bloco, "TRNAMT"), br=False),
                      "descricao": desc, "fitid": campo(bloco, "FITID")})
    saldo = None
    m = re.search(r"<LEDGERBAL>(.*?)(</LEDGERBAL>|$)", txt, re.S | re.I)
    if m and campo(m.group(1), "BALAMT"):
        saldo = (num(campo(m.group(1), "BALAMT"), br=False), data(campo(m.group(1), "DTASOF")).isoformat())
    return itens, saldo


def ler_csv_extrato(caminho):
    """CSV exportado pelo banco: aceita ; ou , e cabeçalhos como Data, Descrição/Histórico, Valor (ou Crédito/Débito)."""
    txt = caminho.read_bytes()
    try:
        txt = txt.decode("utf-8-sig")
    except UnicodeDecodeError:
        txt = txt.decode("cp1252")
    linhas = txt.splitlines()
    sep = ";" if linhas and linhas[0].count(";") >= linhas[0].count(",") else ","
    itens = []
    for r in csv.DictReader(linhas, delimiter=sep):
        r = {sem_acento(k).strip(): v for k, v in r.items() if k}
        quando = r.get("data") or r.get("data lancamento") or r.get("date")
        if not quando:
            continue
        if r.get("valor") not in (None, ""):
            valor = num(r["valor"])
        else:
            valor = num(r.get("credito")) - abs(num(r.get("debito")))
        desc = r.get("descricao") or r.get("historico") or r.get("lancamento") or r.get("memo") or ""
        itens.append({"data": data(quando).isoformat(), "valor": valor, "descricao": desc.strip(), "fitid": ""})
    return itens, None


def regras():
    return json.loads(REGRAS.read_text(encoding="utf-8"))["regras"] if REGRAS.exists() else []


def classificar(descricao, valor, lista_regras):
    d = sem_acento(descricao)
    for r in lista_regras:
        if r.get("tipo") == "receita" and valor < 0 or r.get("tipo") == "despesa" and valor > 0:
            continue
        if any(sem_acento(t) in d for t in r["termos"]):
            return r["categoria"]
    return SEM_CATEGORIA


def conciliar(lanc, faturas, clientes):
    """Dá baixa na fatura em aberto com o mesmo valor e vencimento próximo; nome do cliente na descrição desempata."""
    if float(lanc["valor"]) <= 0 or lanc.get("fatura_id"):
        return None
    nomes = {c["id"]: sem_acento(c["empresa"]) for c in clientes}
    quando = data(lanc["data"])
    candidatas = [f for f in faturas if not f["pago_em"] and abs(float(f["valor"]) - float(lanc["valor"])) < 0.01
                  and -10 <= (quando - data(f["vencimento"])).days <= 45]
    if not candidatas:
        return None
    desc = sem_acento(lanc["descricao"])
    def nome_bate(f):
        palavras = [p for p in re.findall(r"\w+", nomes.get(f["cliente_id"], "")) if len(p) > 3]
        return any(p in desc for p in palavras)
    candidatas.sort(key=lambda f: (not nome_bate(f), abs((quando - data(f["vencimento"])).days)))
    if len(candidatas) > 1 and not nome_bate(candidatas[0]):
        return None  # dois clientes com o mesmo valor e nenhum nome no extrato: fica para você conferir
    f = candidatas[0]
    f.update(pago_em=lanc["data"], lancamento=lanc["id"])
    lanc.update(fatura_id=f["id"], categoria=RECEITA_SITES if f.get("descricao", "").startswith("Site") else RECEITA)
    return f


def cmd_importar(a):
    caminho = Path(a.arquivo)
    itens, saldo = ler_ofx(caminho) if caminho.suffix.lower() == ".ofx" else ler_csv_extrato(caminho)
    lancs, faturas, clientes = ler(LANCAMENTOS, C_LANC), ler(FATURAS, C_FATURA), ler(CLIENTES, C_CLIENTE)
    vistos = {l["fitid"] for l in lancs if l["fitid"]} | {(l["data"], f"{float(l['valor']):.2f}", l["descricao"]) for l in lancs}
    lista_regras = regras()
    novos = baixas = 0
    for i in itens:
        chave = (i["data"], f"{i['valor']:.2f}", i["descricao"])
        if (i["fitid"] and i["fitid"] in vistos) or chave in vistos:
            continue
        l = {"id": proximo_id(lancs), "data": i["data"], "descricao": i["descricao"], "valor": f"{i['valor']:.2f}",
             "categoria": classificar(i["descricao"], i["valor"], lista_regras), "fitid": i["fitid"],
             "origem": caminho.suffix.lower().lstrip(".")}
        if conciliar(l, faturas, clientes):
            baixas += 1
        lancs.append(l)
        vistos |= {i["fitid"], chave}
        novos += 1
    gravar(LANCAMENTOS, C_LANC, lancs)
    gravar(FATURAS, C_FATURA, faturas)
    if saldo:
        cfg = config()
        cfg.update(saldo_inicial=saldo[0], data_saldo=saldo[1])
        salvar_config(cfg)
    pendentes = sum(l["categoria"] == SEM_CATEGORIA for l in lancs)
    print(f"{novos} lançamentos novos · {baixas} faturas baixadas"
          + (f" · saldo do banco {reais(saldo[0])} em {saldo[1]}" if saldo else "")
          + (f" · {pendentes} a classificar (ajuste financeiro/categorias.json e rode 'reclassificar')" if pendentes else ""))


def cmd_reclassificar(a):
    lancs, lista_regras = ler(LANCAMENTOS, C_LANC), regras()
    n = 0
    for l in lancs:
        if l["categoria"] == SEM_CATEGORIA or a.todos and not l["fatura_id"]:
            nova = classificar(l["descricao"], float(l["valor"]), lista_regras)
            n += nova != l["categoria"]
            l["categoria"] = nova
    gravar(LANCAMENTOS, C_LANC, lancs)
    print(f"{n} lançamentos reclassificados · {sum(l['categoria'] == SEM_CATEGORIA for l in lancs)} ainda a classificar")


def cmd_categoria(a):
    """Classifica um lançamento na mão (o que as regras de financeiro/categorias.json não pegaram)."""
    lancs = ler(LANCAMENTOS, C_LANC)
    l = achar(lancs, a.id, "lançamento")
    l["categoria"] = a.categoria.strip()
    gravar(LANCAMENTOS, C_LANC, lancs)
    print(f"lançamento #{l['id']} {reais(float(l['valor']))} \"{l['descricao'][:40]}\" · {l['categoria']}")


def categorias():
    """Categorias conhecidas: as das regras, a receita de assinaturas e as que já foram usadas."""
    nomes = [RECEITA, RECEITA_SITES] + [r["categoria"] for r in regras()] + [l["categoria"] for l in ler(LANCAMENTOS, C_LANC)]
    return [c for i, c in enumerate(nomes) if c and c != SEM_CATEGORIA and c not in nomes[:i]]


def cmd_lancar(a):
    lancs = ler(LANCAMENTOS, C_LANC)
    l = {"id": proximo_id(lancs), "data": a.data or hoje().isoformat(), "descricao": a.descricao, "valor": f"{a.valor:.2f}",
         "categoria": a.categoria or classificar(a.descricao, a.valor, regras()), "origem": "manual"}
    baixa = conciliar(l, f := ler(FATURAS, C_FATURA), ler(CLIENTES, C_CLIENTE))
    lancs.append(l)
    gravar(LANCAMENTOS, C_LANC, lancs)
    gravar(FATURAS, C_FATURA, f)
    print(f"lançamento #{l['id']} {reais(a.valor)} · {l['categoria']}" + (f" · baixou a fatura #{baixa['id']}" if baixa else ""))


# ---------------------------------------------------------------- cobrança e pós-venda

def atrasadas(ref=None):
    ref = ref or hoje()
    clientes = {c["id"]: c for c in ler(CLIENTES, C_CLIENTE)}
    out = []
    for f in ler(FATURAS, C_FATURA):
        if f["pago_em"]:
            continue
        dias = (ref - data(f["vencimento"])).days
        if dias > 0:
            out.append({**f, "dias": dias, "cliente": clientes.get(f["cliente_id"], {})})
    return sorted(out, key=lambda f: -f["dias"])


def msg_cobranca(f, etapa, assinatura):
    nome = (f["cliente"].get("contato") or "").split(" ")[0] or "tudo bem"
    venc = data(f["vencimento"]).strftime("%d/%m")
    valor = reais(float(f["valor"]))
    item = o_que(f)
    if etapa == 3:
        return (f"Oi, {nome}! Aqui é {assinatura}, da Ciello. Passando só para lembrar {o_que(f, de=True)} "
                f"de {valor} que venceu em {venc}. Se já pagou, desconsidera. Quer que eu reenvie o Pix?")
    if etapa == 7:
        return (f"Oi, {nome}! {item[0].upper() + item[1:]} de {valor} (venc. {venc}) ainda aparece em aberto aqui. "
                f"Consegue ver pra mim hoje? Se precisar de outra data, me fala que a gente combina.")
    pausa = "o site" if "site" in item else "o acesso da equipe"
    return (f"Oi, {nome}. {item[0].upper() + item[1:]} de {valor} está com 14 dias de atraso. Para não precisar pausar "
            f"{pausa}, consegue regularizar até sexta? Se estiver difícil, me liga que a gente acha um jeito.")


def etapa_atual(dias, etapas, feitas):
    """A etapa mais recente alcançada, se ela (ou uma posterior) ainda não foi enviada: atrasou a 7, não manda a 3."""
    alcancadas = [e for e in etapas if dias >= e]
    enviadas = [int(x) for x in feitas.split(",") if x.isdigit()]
    if not alcancadas or any(e >= alcancadas[-1] for e in enviadas):
        return None
    return alcancadas[-1]


def etapa_devida(dias, feitas):
    return etapa_atual(dias, COBRANCA, feitas)


def cobrancas_devidas(ref=None):
    """Cobranças a enviar hoje: fatura, etapa (D+3, D+7, D+14), mensagem pronta e link wa.me."""
    assinatura = config()["assinatura"]
    out = []
    for f in atrasadas(ref):
        etapa = etapa_devida(f["dias"], f["cobrancas"])
        if etapa:
            msg = msg_cobranca(f, etapa, assinatura)
            out.append({"fatura_id": f["id"], "cliente_id": f["cliente_id"], "empresa": f["cliente"].get("empresa", "?"),
                        "valor": float(f["valor"]), "dias": f["dias"], "etapa": etapa, "mensagem": msg,
                        "link": link_wa(f["cliente"].get("whatsapp"), msg)})
    return out


def cmd_cobrar(a):
    L = [f"# Cobranças de {hoje().isoformat()}", "", "Revise e envie do seu WhatsApp. Depois: `python central/financeiro.py enviado cobranca ID`.", ""]
    devidas = cobrancas_devidas()
    for c in devidas:
        L += [f"## Fatura #{c['fatura_id']} · {c['empresa']} · {reais(c['valor'])} · {c['dias']} dias (etapa D+{c['etapa']})",
              "", "```", c["mensagem"], "```", "", f"[Abrir no WhatsApp]({c['link']})" if c["link"] else "Sem WhatsApp cadastrado: ligar.", ""]
    destino = PASTA / "cobrancas" / f"{hoje().isoformat()}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(L), encoding="utf-8")
    print(f"{len(devidas)} cobranças para enviar -> {destino}" if devidas else "nenhuma cobrança devida hoje")


def posvenda_devida(c, ref=None):
    ref = ref or hoje()
    if c["status"] not in ("ativo", "teste"):  # quem está no teste grátis é quem mais precisa de boas-vindas
        return None
    return etapa_atual((ref - data(c["inicio"])).days, POSVENDA, c["posvenda"])


def msg_posvenda(c, etapa, cfg):
    nome = (c.get("contato") or "").split(" ")[0] or "tudo bem"
    if etapa == 1:
        return (f"Oi, {nome}! Seja bem-vindo ao CIELLO CRM 🎉 Qualquer dúvida na configuração, me chama aqui. "
                f"Dica do 1º dia: conecte o WhatsApp e crie as etapas do seu funil, leva 10 minutos.")
    if etapa == 7:
        return (f"Oi, {nome}! Uma semana de CIELLO CRM. A equipe já está atendendo por ele? "
                f"Se quiser, faço uma call de 15 minutos para ajustar o funil com vocês.")
    if etapa == 30:
        return (f"Oi, {nome}! Um mês de CIELLO CRM. Pergunta rápida: de 0 a 10, quanto você recomendaria o CRM "
                f"para outro empresário? Sua resposta me ajuda a melhorar.")
    return (f"Oi, {nome}! 3 meses juntos 🙌 Conhece algum empresário que sofre com o WhatsApp bagunçado? "
            f"Se indicar e ele fechar, seu próximo mês sai por nossa conta.")


def posvendas_devidos(ref=None):
    """Mensagens de pós-venda de hoje (D+1, D+7, D+30, D+90 e o pedido de avaliação para NPS 9–10), prontas e com link."""
    cfg = config()
    out = []
    for c in ler(CLIENTES, C_CLIENTE):
        etapa = posvenda_devida(c, ref)
        if etapa:
            msg = msg_posvenda(c, etapa, cfg)
            out.append({"cliente_id": c["id"], "empresa": c["empresa"], "etapa": str(etapa), "rotulo": f"D+{etapa}",
                        "mensagem": msg, "link": link_wa(c["whatsapp"], msg)})
        if c["status"] == "ativo" and c["nps"] and int(c["nps"]) >= 9 and "avaliacao" not in c["posvenda"].split(","):
            link = cfg["link_avaliacao"] or "(configure: python central/financeiro.py config --link-avaliacao URL)"
            msg = (f"Que bom que você curtiu, obrigado! 🙏 Se puder deixar essa nota no Google, ajuda muito outros empresários "
                   f"a conhecer a Ciello: {link}")
            out.append({"cliente_id": c["id"], "empresa": c["empresa"], "etapa": "avaliacao",
                        "rotulo": f"pedido de avaliação (NPS {c['nps']})", "mensagem": msg, "link": link_wa(c["whatsapp"], msg)})
    return out


def cmd_posvenda(a):
    L = [f"# Pós-venda de {hoje().isoformat()}", "", "Revise e envie. Depois: `python central/financeiro.py enviado posvenda CLIENTE`.", ""]
    devidos = posvendas_devidos()
    for p in devidos:
        L += [f"## Cliente #{p['cliente_id']} · {p['empresa']} · {p['rotulo']}", "", "```", p["mensagem"], "```", "",
              f"[Abrir no WhatsApp]({p['link']})" if p["link"] else "Sem WhatsApp cadastrado.", ""]
        if p["etapa"] == "avaliacao":
            L += [f"Depois: `python central/financeiro.py enviado posvenda {p['cliente_id']} --etapa avaliacao`", ""]
    destino = PASTA / "posvenda" / f"{hoje().isoformat()}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(L), encoding="utf-8")
    print(f"{len(devidos)} mensagens de pós-venda -> {destino}" if devidos else "nenhum pós-venda devido hoje")


def cmd_enviado(a):
    if a.tipo == "cobranca":
        faturas = ler(FATURAS, C_FATURA)
        f = achar(faturas, a.id, "fatura")
        etapa = a.etapa or etapa_devida((hoje() - data(f["vencimento"])).days, f["cobrancas"])
        if not etapa:
            sys.exit("nenhuma etapa de cobrança devida para essa fatura")
        f["cobrancas"] = ",".join(x for x in (f["cobrancas"], str(etapa)) if x)
        gravar(FATURAS, C_FATURA, faturas)
    else:
        clientes = ler(CLIENTES, C_CLIENTE)
        c = achar(clientes, a.id, "cliente")
        etapa = a.etapa or posvenda_devida(c)
        if not etapa:
            sys.exit("nenhuma etapa de pós-venda devida para esse cliente")
        c["posvenda"] = ",".join(x for x in (c["posvenda"], str(etapa)) if x)
        c["ultimo_contato"] = hoje().isoformat()
        gravar(CLIENTES, C_CLIENTE, clientes)
    print(f"{a.tipo} {a.id}: etapa {etapa} registrada")


def cmd_nps(a):
    clientes = ler(CLIENTES, C_CLIENTE)
    c = achar(clientes, a.id, "cliente")
    c["nps"] = str(a.nota)
    c["ultimo_contato"] = hoje().isoformat()
    gravar(CLIENTES, C_CLIENTE, clientes)
    if a.nota >= 9:
        print(f"{c['empresa']}: NPS {a.nota} (promotor) · o 'posvenda' já prepara o pedido de avaliação no Google")
    elif a.nota <= 6:
        print(f"{c['empresa']}: NPS {a.nota} (detrator) · risco de cancelamento: ligue esta semana e anote o motivo em --obs")
    else:
        print(f"{c['empresa']}: NPS {a.nota} (neutro)")


def cmd_conversa(a):
    """Registra uma conversa com o cliente (ligação, visita, WhatsApp): a saúde da carteira conta os dias desde a última."""
    clientes = ler(CLIENTES, C_CLIENTE)
    c = achar(clientes, a.id, "cliente")
    texto = " ".join(a.texto.split())[:300]
    c["obs"] = (c["obs"] + f" | {hoje():%d/%m}: {texto}").strip(" |")[-1500:]
    c["ultimo_contato"] = hoje().isoformat()
    gravar(CLIENTES, C_CLIENTE, clientes)
    print(f"{c['empresa']}: conversa registrada ({hoje():%d/%m})")


def msg_fim_teste(c, assinatura):
    nome = (c.get("contato") or "").split(" ")[0] or "tudo bem"
    fim = data(c["teste_ate"])
    passou = fim < hoje()
    return (f"Oi, {nome}! Aqui é {assinatura}, da Ciello. O teste grátis do CIELLO CRM de vocês {'terminou' if passou else 'vai até'} {fim:%d/%m}. "
            f"Como está sendo para a equipe? Se fizer sentido seguir, eu deixo tudo ativo: fica {reais(float(c['valor_mensal']))}/mês, "
            f"todo dia {c['dia_vencimento']}. Se quiser ajustar alguma coisa antes, me fala que eu resolvo.")


def testes_acabando(ref=None, dias=7):
    """Clientes no teste grátis que acabam em até `dias` (ou já acabaram), com a mensagem de fechamento pronta."""
    ref = ref or hoje()
    assinatura = config()["assinatura"]
    out = []
    for c in ler(CLIENTES, C_CLIENTE):
        if c["status"] == "teste" and c["teste_ate"] and (data(c["teste_ate"]) - ref).days <= dias:
            msg = msg_fim_teste(c, assinatura)
            out.append({"cliente_id": c["id"], "empresa": c["empresa"], "teste_ate": c["teste_ate"], "dias": (data(c["teste_ate"]) - ref).days,
                        "valor": float(c["valor_mensal"] or 0), "mensagem": msg, "link": link_wa(c["whatsapp"], msg)})
    return sorted(out, key=lambda t: t["dias"])


def oportunidades():
    """Vender o 2º produto para quem já é cliente: CRM para quem tem site, site para quem tem CRM."""
    assinatura = config()["assinatura"]
    por_empresa = {}
    for c in ler(CLIENTES, C_CLIENTE):
        if c["status"] in ("ativo", "projeto", "teste"):  # quem está no teste entra para não receber oferta antes de decidir
            por_empresa.setdefault(sem_acento(c["empresa"]).strip(), []).append(c)
    out = []
    for cs in por_empresa.values():
        planos = {c["plano"] or "crm" for c in cs}
        if any(x["status"] == "teste" for x in cs):
            continue
        c = cs[0]
        nome = (c.get("contato") or "").split(" ")[0] or "tudo bem"
        if "crm" in planos and not planos & {"hospedagem", "site"}:
            msg = (f"Oi, {nome}! Aqui é {assinatura}, da Ciello. Uma ideia: com o CRM organizando o WhatsApp, um site com o botão do WhatsApp "
                   f"traz mais conversa para a equipe atender. Fazemos em até 7 dias úteis. Quer que eu te mostre 2 exemplos?")
            out.append({"cliente_id": c["id"], "empresa": c["empresa"], "oferta": "site", "porque": "tem o CRM e ainda não tem site com a Ciello",
                        "mensagem": msg, "link": link_wa(c["whatsapp"], msg)})
        elif planos & {"hospedagem", "site"} and "crm" not in planos:
            msg = (f"Oi, {nome}! Aqui é {assinatura}, da Ciello. O site de vocês está trazendo contatos pelo WhatsApp? "
                   f"Se a conversa se perde entre as pessoas da equipe, o CIELLO CRM organiza tudo num lugar só. Dá pra testar 30 dias grátis.")
            out.append({"cliente_id": c["id"], "empresa": c["empresa"], "oferta": "crm", "porque": "tem site com a Ciello e ainda não usa o CRM",
                        "mensagem": msg, "link": link_wa(c["whatsapp"], msg)})
    return out


# ---------------------------------------------------------------- números do negócio

def mrr_em(clientes, dia):
    return sum(float(c["valor_mensal"]) for c in clientes
               if c["inicio"] and data(c["inicio"]) <= dia and not (c["cancelado_em"] and data(c["cancelado_em"]) <= dia))


def saldo_atual(cfg, lancs):
    corte = cfg["data_saldo"]
    return float(cfg["saldo_inicial"]) + sum(float(l["valor"]) for l in lancs if not corte or l["data"] > corte)


def situacao(ref=None):
    """Retrato para o briefing do dia e o painel: MRR, caixa, atrasos, previsão e alertas."""
    ref = ref or hoje()
    cfg, clientes, lancs = config(), ler(CLIENTES, C_CLIENTE), ler(LANCAMENTOS, C_LANC)
    mes = ref.strftime("%Y-%m")
    ativos = [c for c in clientes if c["status"] == "ativo"]
    mrr = sum(float(c["valor_mensal"]) for c in ativos)
    testes = sorted(({"id": c["id"], "empresa": c["empresa"], "teste_ate": c["teste_ate"], "valor": float(c["valor_mensal"] or 0),
                      "dias": (data(c["teste_ate"]) - ref).days} for c in clientes if c["status"] == "teste" and c["teste_ate"]),
                    key=lambda t: t["dias"])
    sites = [f for f in ler(FATURAS, C_FATURA) if not f["pago_em"] and f["descricao"].startswith("Site")]
    a_receber = {d: round(sum(float(f["valor"]) for f in sites if 0 <= (data(f["vencimento"]) - ref).days <= d), 2) for d in (30, 60, 90)}
    # despesa média dos últimos 3 meses fechados (sem transferências entre contas)
    meses = [meses_atras(mes, i) for i in (1, 2, 3)]
    desp = [-sum(float(l["valor"]) for l in lancs if l["data"][:7] == m and float(l["valor"]) < 0
                 and l["categoria"] not in FORA_DO_RESULTADO) for m in meses]
    meses_com_dado = [d for m, d in zip(meses, desp) if any(l["data"][:7] == m for l in lancs)]
    if meses_com_dado:
        despesa_media = sum(meses_com_dado) / len(meses_com_dado)
    else:  # 1º mês de uso: o que já saiu neste mês serve de estimativa (por baixo)
        despesa_media = -sum(float(l["valor"]) for l in lancs if l["data"][:7] == mes and float(l["valor"]) < 0
                             and l["categoria"] not in FORA_DO_RESULTADO)
    caixa = saldo_atual(cfg, lancs)
    atras = atrasadas(ref)
    previsao = {d: round(caixa + (mrr - despesa_media) * d / 30 + a_receber[d], 2) for d in (30, 60, 90)}
    queima = despesa_media - mrr
    alertas = []
    if atras:
        alertas.append(f"{len(atras)} fatura(s) atrasada(s): {reais(sum(float(f['valor']) for f in atras))}")
    menor = min(previsao.values())
    if lancs and menor < float(cfg["alerta_saldo"]):
        alertas.append(f"caixa previsto abaixo de {reais(float(cfg['alerta_saldo']))} em até 90 dias ({reais(menor)})")
    for t in testes:
        if t["dias"] < 0:
            alertas.append(f"teste grátis de {t['empresa']} acabou há {-t['dias']} dia(s): virou cliente ou não?")
        elif t["dias"] <= 5:
            alertas.append(f"teste grátis de {t['empresa']} acaba em {t['dias']} dia(s): ligue para fechar")
    sem_cat = sum(l["categoria"] == SEM_CATEGORIA for l in lancs)
    if sem_cat:
        alertas.append(f"{sem_cat} lançamento(s) a classificar")
    detratores = [c["empresa"] for c in ativos if c["nps"] and int(c["nps"]) <= 6]
    if detratores:
        alertas.append(f"cliente(s) insatisfeito(s) (NPS ≤ 6): {', '.join(detratores)}")
    return {"mes": mes, "clientes_ativos": len(ativos), "mrr": round(mrr, 2), "caixa": round(caixa, 2),
            "despesa_media": round(despesa_media, 2), "previsao": previsao,
            "runway_meses": round(caixa / queima, 1) if queima > 0 else None,
            "atrasadas": [{"id": f["id"], "empresa": f["cliente"].get("empresa", ""), "valor": float(f["valor"]), "dias": f["dias"]} for f in atras],
            "cobrancas_devidas": sum(1 for f in atras if etapa_devida(f["dias"], f["cobrancas"])),
            "posvenda_devidos": sum(1 for c in clientes if posvenda_devida(c, ref)),
            "testes": testes, "mrr_em_teste": round(sum(t["valor"] for t in testes), 2), "sites_a_receber": a_receber,
            "alertas": alertas, "tem_dados": bool(clientes or lancs)}


def metricas_mes(mes, clientes, lancs):
    ano, m = map(int, mes.split("-"))
    ini, fim = dt.date(ano, m, 1), dt.date(ano, m, calendar.monthrange(ano, m)[1])
    novos = [c for c in clientes if c["inicio"][:7] == mes]
    cancel = [c for c in clientes if c["cancelado_em"][:7] == mes]
    ativos_ini = [c for c in clientes if data(c["inicio"]) < ini and not (c["cancelado_em"] and data(c["cancelado_em"]) < ini)]
    do_mes = [l for l in lancs if l["data"][:7] == mes and l["categoria"] not in FORA_DO_RESULTADO]
    receitas = sum(float(l["valor"]) for l in do_mes if float(l["valor"]) > 0)
    despesas = -sum(float(l["valor"]) for l in do_mes if float(l["valor"]) < 0)
    anuncios = -sum(float(l["valor"]) for l in do_mes if float(l["valor"]) < 0 and l["categoria"] == "Anúncios")
    mrr_fim = mrr_em(clientes, fim)
    ativos_fim = sum(1 for c in clientes if data(c["inicio"]) <= fim and not (c["cancelado_em"] and data(c["cancelado_em"]) <= fim))
    churn = len(cancel) / len(ativos_ini) if ativos_ini else 0.0
    arpa = mrr_fim / ativos_fim if ativos_fim else 0.0
    cac = anuncios / len(novos) if novos and anuncios else None
    por_cat = {}
    for l in do_mes:
        if float(l["valor"]) < 0:
            por_cat[l["categoria"]] = por_cat.get(l["categoria"], 0) - float(l["valor"])
    return {"mes": mes, "mrr": mrr_fim, "mrr_novo": sum(float(c["valor_mensal"]) for c in novos),
            "mrr_perdido": sum(float(c["valor_mensal"]) for c in cancel), "novos": len(novos), "cancelados": len(cancel),
            "ativos": ativos_fim, "churn": churn, "arpa": arpa, "ltv": arpa / churn if churn else None, "cac": cac,
            "payback": cac / arpa if cac and arpa else None, "receitas": receitas, "despesas": despesas,
            "resultado": receitas - despesas, "por_categoria": dict(sorted(por_cat.items(), key=lambda x: -x[1]))}


def cmd_resumo(a):
    ref = hoje()
    mes = a.mes or ref.strftime("%Y-%m")
    clientes, lancs, faturas = ler(CLIENTES, C_CLIENTE), ler(LANCAMENTOS, C_LANC), ler(FATURAS, C_FATURA)
    s = situacao(ref)
    serie = [metricas_mes(meses_atras(mes, i), clientes, lancs) for i in range(a.meses - 1, -1, -1)]
    atual = serie[-1]
    fmt = lambda v, f: "—" if v is None else f(v)
    L = [f"# Financeiro · {mes}", "",
         f"**MRR {reais(atual['mrr'])}** · {atual['ativos']} clientes · ARPA {reais(atual['arpa'])} · "
         f"churn {atual['churn']:.1%} · LTV {fmt(atual['ltv'], reais)} · CAC {fmt(atual['cac'], reais)} · "
         f"payback {fmt(atual['payback'], lambda v: f'{v:.1f} meses')}", "",
         f"**Caixa {reais(s['caixa'])}** · despesa média {reais(s['despesa_media'])}/mês · previsão: "
         + " · ".join(f"{d} dias {reais(v)}" for d, v in s["previsao"].items())
         + (f" · fôlego {s['runway_meses']} meses" if s["runway_meses"] else " · operação se paga" if s["despesa_media"] else ""), ""]
    if not s["tem_dados"]:
        L += ["Sem dados ainda: `financeiro.py cliente ...`, `faturar` e `importar extrato.ofx` (o banco exporta em OFX ou CSV).", ""]
    if s["alertas"]:
        L += ["## Alertas", ""] + [f"- {x}" for x in s["alertas"]] + [""]
    L += ["## Mês a mês", "", "| Mês | MRR | + novo | − perdido | Clientes | Receitas | Despesas | Resultado |", "|---|---|---|---|---|---|---|---|"]
    L += [f"| {m['mes']} | {reais(m['mrr'])} | {reais(m['mrr_novo'])} | {reais(m['mrr_perdido'])} | {m['ativos']} | "
          f"{reais(m['receitas'])} | {reais(m['despesas'])} | {reais(m['resultado'])} |" for m in serie]
    if atual["por_categoria"]:
        L += ["", f"## Despesas de {mes} por categoria", ""] + [f"- {k}: {reais(v)}" for k, v in atual["por_categoria"].items()]
    # o que não bate: crédito sem fatura e fatura paga sem crédito no extrato
    sem_fatura = [l for l in lancs if float(l["valor"]) > 0 and not l["fatura_id"] and l["categoria"] in (SEM_CATEGORIA, RECEITA)]
    pagas_sem_extrato = [f for f in faturas if f["pago_em"] and not f["lancamento"]] if lancs else []
    if sem_fatura or pagas_sem_extrato:
        L += ["", "## O que não bate", ""]
        L += [f"- Crédito sem fatura: {l['data']} {reais(float(l['valor']))} \"{l['descricao'][:50]}\" (cliente novo? valor diferente?)" for l in sem_fatura[:15]]
        L += [f"- Fatura #{f['id']} marcada como paga em {f['pago_em']}, sem crédito no extrato" for f in pagas_sem_extrato[:15]]
    a_classificar = [l for l in lancs if l["categoria"] == SEM_CATEGORIA and float(l["valor"]) < 0]
    if a_classificar:
        L += ["", "## A classificar (adicione o termo em financeiro/categorias.json)", ""]
        L += [f"- {l['data']} {reais(float(l['valor']))} \"{l['descricao'][:60]}\"" for l in a_classificar[:20]]
    texto = "\n".join(L) + "\n"
    destino = PASTA / "relatorios" / f"{mes}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    print(texto)
    print(f"-> {destino}")


def cmd_config(a):
    cfg = config()
    if a.saldo is not None:
        cfg.update(saldo_inicial=a.saldo, data_saldo=a.data or hoje().isoformat())
    if a.alerta is not None:
        cfg["alerta_saldo"] = a.alerta
    if a.link_avaliacao:
        cfg["link_avaliacao"] = a.link_avaliacao
    if a.assinatura:
        cfg["assinatura"] = a.assinatura
    salvar_config(cfg)
    print(json.dumps(cfg, ensure_ascii=False, indent=1))


def parser():
    """Os comandos da linha de comando. O Ciello OS usa este mesmo parser para operar sem o Claude."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("cliente"); s.add_argument("--empresa", default=""); s.add_argument("--lead", type=int); s.add_argument("--contato", default="")
    s.add_argument("--whatsapp", default=""); s.add_argument("--plano", default=""); s.add_argument("--valor", type=float, help="padrão: o preço do --produto")
    s.add_argument("--produto", default="", help="crm ou hospedagem (preço de comercial/produtos.json)")
    s.add_argument("--teste", type=int, default=0, help="dias de teste grátis (o CRM tem 30): não fatura até virar cliente")
    s.add_argument("--dia", type=int, default=10); s.add_argument("--inicio"); s.set_defaults(f=cmd_cliente)
    s = sub.add_parser("converter", help="o teste grátis virou assinatura"); s.add_argument("id"); s.add_argument("--data")
    s.add_argument("--valor", type=float); s.set_defaults(f=cmd_converter)
    s = sub.add_parser("venda", help="venda de site: à vista ou parcelado, com a hospedagem como assinatura")
    s.add_argument("--cliente"); s.add_argument("--empresa", default=""); s.add_argument("--lead", type=int); s.add_argument("--contato", default="")
    s.add_argument("--whatsapp", default=""); s.add_argument("--forma", choices=["avista", "parcelado"], default="avista")
    s.add_argument("--valor", type=float, help="valor à vista ou de cada parcela (padrão: comercial/produtos.json)")
    s.add_argument("--parcelas", type=int); s.add_argument("--primeira", help="1º vencimento (padrão: hoje)")
    s.add_argument("--dia", type=int, default=10, help="dia de vencimento da hospedagem")
    s.add_argument("--hospedagem", type=float, help="mensalidade da hospedagem (padrão: comercial/produtos.json)")
    s.add_argument("--sem-hospedagem", action="store_true"); s.add_argument("--inicio-hospedagem"); s.set_defaults(f=cmd_venda)
    s = sub.add_parser("editar", help="muda os dados de um cliente (só o que for informado)"); s.add_argument("id")
    for campo in ("empresa", "contato", "whatsapp", "plano", "obs"):
        s.add_argument(f"--{campo}")
    s.add_argument("--valor", type=float); s.add_argument("--dia", type=int); s.add_argument("--reativar", action="store_true"); s.set_defaults(f=cmd_editar)
    s = sub.add_parser("cancelar"); s.add_argument("id"); s.add_argument("--data"); s.add_argument("--motivo", default=""); s.set_defaults(f=cmd_cancelar)
    s = sub.add_parser("faturar"); s.add_argument("--mes", help="AAAA-MM (padrão: mês atual)"); s.set_defaults(f=cmd_faturar)
    s = sub.add_parser("pago"); s.add_argument("id"); s.add_argument("--data"); s.set_defaults(f=cmd_pago)
    s = sub.add_parser("importar"); s.add_argument("arquivo", help="extrato .ofx ou .csv"); s.set_defaults(f=cmd_importar)
    s = sub.add_parser("reclassificar"); s.add_argument("--todos", action="store_true"); s.set_defaults(f=cmd_reclassificar)
    s = sub.add_parser("categoria", help="classifica um lançamento na mão"); s.add_argument("id"); s.add_argument("categoria"); s.set_defaults(f=cmd_categoria)
    s = sub.add_parser("lancar"); s.add_argument("--valor", type=float, required=True, help="negativo = despesa")
    s.add_argument("--descricao", required=True); s.add_argument("--categoria"); s.add_argument("--data"); s.set_defaults(f=cmd_lancar)
    s = sub.add_parser("cobrar"); s.set_defaults(f=cmd_cobrar)
    s = sub.add_parser("posvenda"); s.set_defaults(f=cmd_posvenda)
    s = sub.add_parser("enviado"); s.add_argument("tipo", choices=["cobranca", "posvenda"]); s.add_argument("id")
    s.add_argument("--etapa", help="padrão: a etapa devida hoje"); s.set_defaults(f=cmd_enviado)
    s = sub.add_parser("nps"); s.add_argument("id"); s.add_argument("nota", type=int, choices=range(11)); s.set_defaults(f=cmd_nps)
    s = sub.add_parser("conversa", help="registra uma conversa com o cliente"); s.add_argument("id"); s.add_argument("texto"); s.set_defaults(f=cmd_conversa)
    s = sub.add_parser("resumo"); s.add_argument("--mes"); s.add_argument("--meses", type=int, default=6); s.set_defaults(f=cmd_resumo)
    s = sub.add_parser("config"); s.add_argument("--saldo", type=float); s.add_argument("--data"); s.add_argument("--alerta", type=float)
    s.add_argument("--link-avaliacao"); s.add_argument("--assinatura"); s.set_defaults(f=cmd_config)
    return ap


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    a = parser().parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
