"""Operação sem o Claude: as janelas do Ciello OS cadastram cliente, dão baixa em fatura, importam extrato, movem o
funil e registram lead chamando as mesmas ferramentas da linha de comando (financeiro.py e sdr.py), direto, sem
agente nenhum no meio. Acabaram os tokens? O OS continua mostrando os números e operando o dia a dia.

Cada operação é uma lista fixa de campos com tipo e limite (nada vira comando fora disso). O pedido da janela vira os
argumentos do próprio parser da ferramenta e roda aqui dentro, com a saída devolvida para a janela.
Mensagens nunca são enviadas daqui: a janela mostra o texto e o link wa.me, e você envia do seu WhatsApp.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import re
import threading
from pathlib import Path

import financeiro
import sdr

RAIZ = Path(__file__).resolve().parent.parent.parent
TRAVA = threading.Lock()  # uma operação por vez (as ferramentas leem e regravam o CSV inteiro)
ORIGENS = ["instagram", "anuncio", "site", "indicacao", "outro"]


class Invalido(ValueError):
    pass


# ---------------------------------------------------------------- tipos dos campos

def _texto(v, maximo=500):
    if not isinstance(v, (str, int, float)):
        raise Invalido("texto inválido")
    t = str(v).strip()
    if len(t) > maximo:
        raise Invalido(f"texto com mais de {maximo} letras")
    return t


def _numero(v):
    t = _texto(v, 40)
    if not re.search(r"\d", t):
        raise Invalido("número inválido")
    return repr(financeiro.num(t))


def _inteiro(minimo, maximo):
    def conv(v):
        try:
            n = int(str(v).strip())
        except ValueError:
            raise Invalido("número inteiro inválido") from None
        if not minimo <= n <= maximo:
            raise Invalido(f"fora de {minimo} a {maximo}")
        return str(n)
    return conv


def _data(v):
    t = _texto(v, 10)
    try:
        return dt.date.fromisoformat(t).isoformat()
    except ValueError:
        raise Invalido("data inválida (use AAAA-MM-DD)") from None


def _datahora(v):
    t = _texto(v, 16)
    try:
        return dt.datetime.fromisoformat(t).strftime("%Y-%m-%dT%H:%M")
    except ValueError:
        raise Invalido("data e hora inválidas") from None


def _mes(v):
    t = _texto(v, 7)
    if not re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])", t):
        raise Invalido("mês inválido (use AAAA-MM)")
    return t


def _escolha(opcoes):
    def conv(v):
        t = _texto(v, 80)
        if t not in (opcoes() if callable(opcoes) else opcoes):
            raise Invalido("opção inválida")
        return t
    return conv


def _lista(v):
    itens = v if isinstance(v, list) else [x for x in re.split(r"[,\n]", str(v or ""))]
    out = [_texto(x, 80) for x in itens if str(x).strip()]
    if any(x.startswith("-") for x in out) or len(out) > 40:
        raise Invalido("lista inválida")
    return out


SIM = "sim"  # campo liga/desliga: vira só a opção, sem valor
ID = _inteiro(1, 10_000_000)
NOTA = _inteiro(0, 10)
DIA = _inteiro(1, 31)
segmentos = lambda: list(sdr.icp()["segmentos"])

# operação -> (ferramenta, comando, campos). Campo: (nome, conversor, obrigatório, opção da linha de comando ou None
# para posicional). Opções vão como --opcao=valor: um texto começando com "-" nunca vira outra opção.
OPERACOES = {
    "fin_cliente": (financeiro, "cliente", [
        ("empresa", _texto, False, "--empresa"), ("contato", _texto, False, "--contato"), ("whatsapp", _texto, False, "--whatsapp"),
        ("plano", _texto, False, "--plano"), ("valor", _numero, False, "--valor"), ("dia", DIA, False, "--dia"),
        ("inicio", _data, False, "--inicio"), ("lead", ID, False, "--lead"),
        ("produto", _escolha(["crm", "hospedagem"]), False, "--produto"), ("teste", _inteiro(0, 90), False, "--teste")]),
    "fin_converter": (financeiro, "converter", [("id", ID, True, None), ("data", _data, False, "--data"), ("valor", _numero, False, "--valor")]),
    "fin_venda": (financeiro, "venda", [
        ("cliente", ID, False, "--cliente"), ("empresa", _texto, False, "--empresa"), ("lead", ID, False, "--lead"),
        ("contato", _texto, False, "--contato"), ("whatsapp", _texto, False, "--whatsapp"),
        ("forma", _escolha(["avista", "parcelado"]), False, "--forma"), ("valor", _numero, False, "--valor"),
        ("parcelas", _inteiro(1, 48), False, "--parcelas"), ("primeira", _data, False, "--primeira"), ("dia", DIA, False, "--dia"),
        ("hospedagem", _numero, False, "--hospedagem"), ("sem_hospedagem", SIM, False, "--sem-hospedagem")]),
    "fin_editar": (financeiro, "editar", [
        ("id", ID, True, None), ("empresa", _texto, False, "--empresa"), ("contato", _texto, False, "--contato"),
        ("whatsapp", _texto, False, "--whatsapp"), ("plano", _texto, False, "--plano"), ("obs", _texto, False, "--obs"),
        ("valor", _numero, False, "--valor"), ("dia", DIA, False, "--dia"), ("reativar", SIM, False, "--reativar")]),
    "fin_cancelar": (financeiro, "cancelar", [("id", ID, True, None), ("motivo", _texto, False, "--motivo"), ("data", _data, False, "--data")]),
    "fin_faturar": (financeiro, "faturar", [("mes", _mes, False, "--mes")]),
    "fin_pago": (financeiro, "pago", [("id", ID, True, None), ("data", _data, False, "--data")]),
    "fin_lancar": (financeiro, "lancar", [
        ("valor", _numero, True, "--valor"), ("descricao", _texto, True, "--descricao"), ("categoria", _texto, False, "--categoria"),
        ("data", _data, False, "--data")]),
    "fin_categoria": (financeiro, "categoria", [("id", ID, True, None), ("categoria", _texto, True, None)]),
    "fin_reclassificar": (financeiro, "reclassificar", []),
    "fin_enviado": (financeiro, "enviado", [
        ("tipo", _escolha(["cobranca", "posvenda"]), True, None), ("id", ID, True, None),
        ("etapa", _escolha(["1", "3", "7", "14", "30", "90", "avaliacao"]), False, "--etapa")]),
    "fin_nps": (financeiro, "nps", [("id", ID, True, None), ("nota", NOTA, True, None)]),
    "fin_config": (financeiro, "config", [
        ("saldo", _numero, False, "--saldo"), ("data", _data, False, "--data"), ("alerta", _numero, False, "--alerta"),
        ("link_avaliacao", _texto, False, "--link-avaliacao"), ("assinatura", _texto, False, "--assinatura")]),
    "sdr_marcar": (sdr, "marcar", [("id", ID, True, None), ("etapa", _escolha(sdr.ETAPAS), True, None), ("obs", _texto, False, "--obs")]),
    "sdr_agendar": (sdr, "agendar", [("id", ID, True, None), ("quando", _datahora, True, "--quando"), ("obs", _texto, False, "--obs"),
                                      ("assinatura", _texto, False, "--assinatura")]),
    "sdr_anotar": (sdr, "anotar", [("id", ID, True, None), ("texto", _texto, True, None)]),
    "sdr_entrada": (sdr, "entrada", [
        ("nome", _texto, False, "--nome"), ("empresa", _texto, False, "--empresa"), ("telefone", _texto, False, "--telefone"),
        ("origem", _escolha(ORIGENS), False, "--origem"), ("segmento", _texto, False, "--segmento"), ("cidade", _texto, False, "--cidade"),
        ("mensagem", _texto, False, "--mensagem"), ("assinatura", _texto, False, "--assinatura")]),
    "sdr_consultas": (sdr, "consultas", [("segmentos", _lista, False, "--segmentos"), ("cidades", _lista, False, "--cidades")]),
    "sdr_crm": (sdr, "crm", [("todos", SIM, False, "--todos")]),
}


def argumentos(op, dados) -> list[str]:
    """Os argumentos da linha de comando para esta operação, só com os campos conhecidos e já conferidos."""
    if op not in OPERACOES:
        raise Invalido("operação desconhecida")
    if not isinstance(dados, dict):
        raise Invalido("dados inválidos")
    _, comando, campos = OPERACOES[op]
    argv, posicionais = [comando], []
    for nome, conv, obrigatorio, opcao in campos:
        v = dados.get(nome)
        vazio = v is None or v is False or (isinstance(v, (str, list)) and not (v.strip() if isinstance(v, str) else v))
        if vazio:
            if obrigatorio:
                raise Invalido(f"preencha: {nome}")
            continue
        if conv is SIM:
            argv.append(opcao)
            continue
        try:
            valor = conv(v)
        except Invalido as e:
            raise Invalido(f"{nome}: {e}") from None
        if opcao is None:
            if valor.startswith("-") and not re.fullmatch(r"-?\d+", valor):
                raise Invalido(f"{nome}: não pode começar com '-'")
            posicionais.append(valor)
        elif isinstance(valor, list):
            argv += [opcao, *valor]
        else:
            argv.append(f"{opcao}={valor}")
    return argv[:1] + posicionais + argv[1:]


def rodar(modulo, argv) -> dict:
    """Roda um comando da ferramenta aqui dentro e devolve o que ela escreveu. Erro de uso ou sys.exit vira ok=False."""
    saida = io.StringIO()
    with TRAVA, contextlib.redirect_stdout(saida), contextlib.redirect_stderr(saida):
        try:
            a = modulo.parser().parse_args(argv)
            a.f(a)
            ok = True
        except SystemExit as e:
            ok = e.code in (None, 0)
            if isinstance(e.code, str):
                print(e.code)
        except (OSError, ValueError, KeyError) as e:
            ok = False
            print(f"Não deu certo: {e}")
    # as dicas de linha de comando ("depois rode python central/...") não fazem sentido na janela: lá é um botão
    texto = re.sub(r"\n*Depois da resposta: python [^\n]*| · lembre: python [^\n]*", "", saida.getvalue())
    texto = texto.replace("(ajuste financeiro/categorias.json e rode 'reclassificar')", "(classifique na aba Lançamentos)")
    return {"ok": ok, "saida": texto.strip()}


def operar(op, dados) -> dict:
    try:
        argv = argumentos(op, dados or {})
    except Invalido as e:
        return {"ok": False, "saida": str(e)}
    return rodar(OPERACOES[op][0], argv)


# ---------------------------------------------------------------- arquivos (extrato do banco, planilha de leads)

def _nome_seguro(nome):
    base = re.sub(r"[^\w.\-]+", "-", Path(str(nome or "arquivo")).name).strip("-.") or "arquivo"
    return base[-80:]


def importar_arquivo(tipo, nome, dados: bytes, opcoes=None) -> dict:
    """Guarda o arquivo enviado pela janela na pasta de dados (fora do git) e roda a importação da ferramenta."""
    opcoes = opcoes or {}
    nome = _nome_seguro(nome)
    sufixo = Path(nome).suffix.lower()
    carimbo = dt.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    if tipo == "extrato":
        if sufixo not in (".ofx", ".csv"):
            return {"ok": False, "saida": "O extrato precisa ser .ofx ou .csv (o banco exporta nos dois)."}
        destino = financeiro.PASTA / "extratos" / f"{carimbo}-{nome}"
        argv = ["importar", str(destino)]
        modulo = financeiro
    elif tipo == "leads":
        if sufixo not in (".csv", ".json"):
            return {"ok": False, "saida": "A planilha de leads precisa ser .csv (ou o .json do buscador)."}
        destino = sdr.PASTA / "bruto" / f"importado-{carimbo}-{nome}"
        argv = ["qualificar", str(destino)]
        try:
            if opcoes.get("segmento"):
                argv.append(f"--segmento={_escolha(segmentos)(opcoes['segmento'])}")
            if opcoes.get("minimo") not in (None, ""):
                argv.append(f"--minimo={_inteiro(0, 100)(opcoes['minimo'])}")
        except Invalido as e:
            return {"ok": False, "saida": str(e)}
        modulo = sdr
    else:
        return {"ok": False, "saida": "tipo de arquivo desconhecido"}
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(dados)
    r = rodar(modulo, argv)
    r["arquivo"] = destino.name
    return r


# ---------------------------------------------------------------- Instagram e anúncios anotados à mão

def _int(v, nome):
    if v in (None, ""):
        return 0
    try:
        n = int(float(str(v).replace(".", "").replace(",", ".")))
    except ValueError:
        raise Invalido(f"{nome}: número inválido") from None
    if n < 0 or n > 10**9:
        raise Invalido(f"{nome}: número inválido")
    return n


def _real(v, nome):
    if v in (None, ""):
        return 0.0
    n = financeiro.num(v)
    if n < 0 or n > 10**9:
        raise Invalido(f"{nome}: número inválido")
    return round(n, 2)


def salvar_retrato(d, pasta=None) -> dict:
    """Retrato do Instagram digitado na janela Conteúdo (quando o Metricool pelo Claude não está à mão).
    Mesmo formato do retrato do analista; o melhor horário vem do retrato anterior."""
    pasta = pasta or RAIZ / "metricas"
    try:
        dia = _data(d.get("data") or dt.date.today().isoformat())
        if d.get("seguidores") in (None, ""):
            raise Invalido("preencha: seguidores")
        perfil = {k: _int(d.get(k), k) for k in ("seguidores", "alcance", "contas_engajadas", "posts")}
        reels = []
        for r in (d.get("reels") or [])[:30]:
            if not isinstance(r, dict) or not str(r.get("gancho") or "").strip():
                continue
            reels.append({"data": _data(r.get("data") or dia), "gancho": _texto(r["gancho"], 200),
                          **{k: _int(r.get(k), k) for k in ("views", "alcance", "salvamentos", "compartilhamentos", "comentarios")},
                          "tempo_medio_s": _real(r.get("tempo_medio_s"), "tempo médio")})
    except Invalido as e:
        return {"ok": False, "saida": str(e)}
    anteriores = sorted(p for p in pasta.glob("20??-??-??.json") if p.stem < dia)
    anterior = json.loads(anteriores[-1].read_text(encoding="utf-8")) if anteriores else {}
    arq = pasta / f"{dia}.json"
    base = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else {}
    perfil["seguidores_inicio"] = (anterior.get("perfil") or {}).get("seguidores", perfil["seguidores"])
    retrato = {**base, "data": dia, "fonte": "anotado à mão no Ciello OS",
               "perfil": {**(base.get("perfil") or {}), **perfil},
               "reels": reels or base.get("reels") or [],
               "melhor_horario": base.get("melhor_horario") or anterior.get("melhor_horario") or {}}
    pasta.mkdir(parents=True, exist_ok=True)
    arq.write_text(json.dumps(retrato, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"ok": True, "saida": f"retrato de {dia} salvo: {perfil['seguidores']} seguidores, {len(retrato['reels'])} reels"}


def salvar_campanha(d, pasta=None) -> dict:
    """Campanha do Meta Ads anotada à mão na janela Anúncios (números do Gerenciador de Anúncios)."""
    pasta = pasta or RAIZ / "anuncios"
    try:
        nome = _texto(d.get("nome"), 120)
        if not nome:
            raise Invalido("preencha: nome da campanha")
        c = {"nome": nome, "inicio": _data(d.get("inicio") or dt.date.today().isoformat()),
             "fim": _data(d["fim"]) if d.get("fim") else "", "objetivo": _texto(d.get("objetivo") or "", 120),
             "publico": _texto(d.get("publico") or "", 200), "criativo": _texto(d.get("criativo") or "", 200),
             "gasto": _real(d.get("gasto"), "gasto"),
             **{k: _int(d.get(k), k) for k in ("impressoes", "cliques", "conversas", "demos", "clientes")}}
    except Invalido as e:
        return {"ok": False, "saida": str(e)}
    pasta.mkdir(parents=True, exist_ok=True)
    # a campanha com este nome é atualizada no arquivo onde já está; nova vai para anuncios/AAAA-MM-DD-nome.json
    for arq in sorted(pasta.glob("*.json")):
        try:
            atual = json.loads(arq.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if any(x.get("nome") == nome for x in atual.get("campanhas", [])):
            atual["campanhas"] = [c if x.get("nome") == nome else x for x in atual["campanhas"]]
            break
    else:
        slug = re.sub(r"[^a-z0-9]+", "-", financeiro.sem_acento(nome)).strip("-")[:50] or "campanha"
        arq = pasta / f"{c['inicio']}-{slug}.json"
        atual = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else {"campanhas": []}
        atual.setdefault("campanhas", []).append(c)
    arq.write_text(json.dumps(atual, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"ok": True, "saida": f"campanha \"{nome}\" salva em anuncios/{arq.name}"}
