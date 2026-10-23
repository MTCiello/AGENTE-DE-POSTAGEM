"""Ciello OS: o assistente inteiro numa área de trabalho. O fundo é o Escritório (a tela pixel em web/escritorio/,
fork MIT do pixel-agents em escritorio/, servida pelo núcleo em Python de nucleo/, sem Node), com a barra de tarefas
embaixo e janelas que movem e redimensionam. Os apps ficam no menu Iniciar.

O escritório é servido pelo mesmo endereço do Ciello OS (/escritorio/): clicar num personagem abre a janela daquele
agente. Cada sessão do Claude Code aberta na pasta do assistente vira um personagem; com os hooks (o escritório
pergunta na primeira vez), os movimentos são instantâneos.

  python central/escritorio/servidor.py              # ou clique duas vezes em Ciello.cmd
  python central/escritorio/servidor.py --sem-escritorio --sem-navegador

Abre em http://127.0.0.1:3200 numa janela de app do Edge/Chrome (sem barra de endereço), como um programa instalado.

Fontes (todas locais):
  estado/eventos.jsonl     o que cada agente está fazendo (central/status.py): abre a janela do agente que começou
  .claude/agents/*.md      a equipe (nome, função e cor de cada agente)
  metricas/ roteiros/ midia/capas/   Instagram, próximos posts e capas
  comercial/leads.csv      funil comercial (SDR e closer)
  anuncios/*.json          campanhas pagas (gestor de anúncios)
  financeiro/              MRR, caixa e faturas (central/financeiro.py) e as 3 prioridades do dia (central/briefing.py)
  radar/                   tendências e vigia de concorrentes

Os botões das janelas só rodam a lista fixa de ACOES abaixo, e só a partir desta página (token por sessão).
Os formulários (cliente, pagamento, extrato, lead, funil, Instagram, anúncios) operam sem o Claude: operacao.py.
"""
import argparse
import html
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AQUI = Path(__file__).resolve().parent
WEB = AQUI / "web"
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(AQUI.parent))
sys.path.insert(0, str(RAIZ / "instalador"))
import status  # noqa: E402
import atendimento  # noqa: E402
import briefing  # noqa: E402
import calendario  # noqa: E402
import conexoes  # noqa: E402
import carteira  # noqa: E402
import conteudo  # noqa: E402
import decisoes  # noqa: E402
import estudio_video  # noqa: E402
import financeiro  # noqa: E402
import gastos  # noqa: E402
import metas  # noqa: E402
import atexit  # noqa: E402
import atualizacao  # noqa: E402

import estudio_voz  # noqa: E402
import operacao  # noqa: E402
import piloto  # noqa: E402
import plano  # noqa: E402
import sdr  # noqa: E402
import social  # noqa: E402
import terminal  # noqa: E402
from nucleo import persistencia  # noqa: E402
from nucleo import websocket  # noqa: E402
from nucleo.sala import Sala  # noqa: E402

ETAPAS_FUNIL = ["novo", "contatado", "respondeu", "demo", "proposta", "cliente"]
PY = sys.executable
TOKEN = secrets.token_urlsafe(24)
TELA = WEB / "escritorio"  # build da tela do escritório (escritorio/webview-ui: npx vite build)
TIPOS = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".woff2": "font/woff2", ".mp4": "video/mp4",
         ".ttf": "font/ttf", ".wav": "audio/wav", ".ico": "image/x-icon", ".json": "application/json", ".webmanifest": "application/manifest+json"}
sala = None  # o escritório (nucleo.sala.Sala), criado no main
terminais = terminal.Terminais(RAIZ)  # terminais do Claude dentro do OS (janela "Claude Code")
atexit.register(terminais.fechar_todos)

# O que os botões das janelas podem rodar: id -> (rótulo, agente, argumentos). Nada fora desta lista roda.
ACOES = {
    "briefing": ("Briefing do dia", "gerente", ["central/briefing.py"]),
    "placar": ("Placar da semana", "gerente", ["central/briefing.py", "--semana"]),
    "fin_resumo": ("Resumo financeiro", "financeiro", ["central/financeiro.py", "resumo"]),
    "fin_faturar": ("Faturas do mês", "financeiro", ["central/financeiro.py", "faturar"]),
    "fin_cobrar": ("Cobranças do dia", "financeiro", ["central/financeiro.py", "cobrar"]),
    "posvenda": ("Pós-venda do dia", "sucesso-cliente", ["central/financeiro.py", "posvenda"]),
    "sdr_hoje": ("Follow-ups de hoje", "sdr", ["central/sdr.py", "hoje"]),
    "sdr_abordar": ("Abordar os 15 melhores leads", "sdr", ["central/sdr.py", "abordar", "--top", "15"]),
    "sdr_crm": ("Exportar para o CIELLO CRM", "sdr", ["central/sdr.py", "crm"]),
    "sdr_buscar": ("Buscar empresas no Google Maps", "sdr", ["central/sdr.py", "buscar"]),
    "sdr_qualificar": ("Qualificar o resultado da busca", "sdr", ["central/sdr.py", "qualificar", "comercial/bruto/resultados.csv"]),
    "vigia": ("Vigia de concorrentes", "pesquisador-mercado", ["central/vigia.py", "checar"]),
    "radar": ("Radar de tendências", "pesquisador-mercado", ["central/radar.py"]),
    "ganchos": ("Ranking de ganchos", "pesquisador-mercado", ["central/ganchos.py", "ranking"]),
    "relatorio": ("Relatório semanal", "analista", ["central/relatorio.py"]),
    "verificar": ("Verificação do assistente", "sistema", ["central/verificar.py", "--rapido"]),
    "piloto": ("Rodada do piloto automático", "postagem", ["central/piloto.py", "rodar"]),
    "sincronizar": ("Sincronizar as redes", "analista", ["central/social.py", "sincronizar"]),
    "atualizacao_verificar": ("Procurar atualizações do Ciello OS", "sistema", ["instalador/atualizacao.py", "verificar"]),
    "atualizacao_aplicar": ("Atualizar o Ciello OS", "sistema", ["instalador/atualizacao.py", "aplicar"]),
    "voz_instalar": ("Instalar a voz (Kokoro e Chatterbox, uns 3 GB)", "produtor-video", ["-m", "pip", "install", "-r", "central/requirements-voz.txt"]),
}
execucoes = {}
trava = threading.Lock()
PORTA_ATUAL = [3200]  # o login do Google/TikTok volta para esta porta


# ---------------------------------------------------------------- leitura dos dados

def ler_json(p, padrao=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def ler_leads():
    return sdr.ler_leads()


def campanhas():
    out = []
    for p in sorted((RAIZ / "anuncios").glob("*.json")):
        out += (ler_json(p, {}) or {}).get("campanhas", [])
    return out


def kpis():
    out = {"instagram": None, "funil": None, "anuncios": None, "financeiro": None, "prioridades": []}
    retratos = sorted((RAIZ / "metricas").glob("20??-??-??.json"))
    if retratos:
        atual = ler_json(retratos[-1])
        ant = ler_json(retratos[-2]) if len(retratos) > 1 else None
        reels = atual.get("reels", [])
        alc = sum(r.get("alcance", 0) for r in reels) or 1
        out["instagram"] = {
            "data": atual["data"], "seguidores": atual["perfil"]["seguidores"],
            "seguidores_antes": (ant or {}).get("perfil", {}).get("seguidores", atual["perfil"].get("seguidores_inicio")),
            "alcance": atual["perfil"].get("alcance", 0), "contas_engajadas": atual["perfil"].get("contas_engajadas", 0),
            "tempo_medio": round(sum(r.get("tempo_medio_s", 0) for r in reels) / max(1, len(reels)), 1),
            "salvamentos_pct": round(100 * sum(r.get("salvamentos", 0) for r in reels) / alc, 2),
            "compart_pct": round(100 * sum(r.get("compartilhamentos", 0) for r in reels) / alc, 2),
            "serie": [{"data": d["data"], "seguidores": d["perfil"]["seguidores"]} for d in map(ler_json, retratos[-12:])],
            "horario": atual.get("melhor_horario", {}),
            "reels": sorted(reels, key=lambda r: -r.get("alcance", 0))[:6],
        }
    linhas = ler_leads()
    if linhas:
        ordem = {e: i for i, e in enumerate(ETAPAS_FUNIL)}
        # funil acumulado: quem chegou na demo também passou por "contatado" e "respondeu"
        alcancou = {e: sum(1 for l in linhas if ordem.get(l["etapa"], -1) >= i) for e, i in ordem.items()}
        out["funil"] = {"etapas": [{"etapa": e, "n": alcancou[e]} for e in ETAPAS_FUNIL],
                        "perdidos": sum(l["etapa"] in ("perdido", "frio") for l in linhas), "total": len(linhas)}
    cs = campanhas()
    if cs:
        gasto = sum(c.get("gasto", 0) for c in cs)
        conversas = sum(c.get("conversas", 0) for c in cs)
        clientes = sum(c.get("clientes", 0) for c in cs)
        out["anuncios"] = {"gasto": gasto, "conversas": conversas, "clientes": clientes,
                           "custo_conversa": round(gasto / conversas, 2) if conversas else None,
                           "custo_cliente": round(gasto / clientes, 2) if clientes else None, "campanhas": len(cs)}
    try:  # um arquivo do financeiro com problema não derruba o painel
        fin = financeiro.situacao()
        out["financeiro"] = fin if fin["tem_dados"] else None
        itens, _, _ = briefing.coletar(financeiro.hoje())
        out["prioridades"] = [{"texto": i["texto"], "dono": i["dono"]} for i in itens[:3]]
    except Exception as e:  # noqa: BLE001
        out["financeiro"], out["prioridades"] = None, [{"texto": f"erro ao ler o financeiro: {e}", "dono": "financeiro"}]
    return out


def equipe():
    agentes = []
    for p in sorted((RAIZ / ".claude" / "agents").glob("*.md")):
        cab = p.read_text(encoding="utf-8").split("---")[1]
        campo = lambda k: (re.search(rf"^{k}:\s*(.+)$", cab, re.M) or [None, ""])[1].strip()
        agentes.append({"nome": campo("name"), "descricao": campo("description"), "cor": campo("color"),
                        "acoes": [{"id": k, "rotulo": v[0]} for k, v in ACOES.items() if v[1] == campo("name")]})
    est = status.ultimo_estado()
    for a in agentes:
        a.update(est["agentes"].get(a["nome"], {"estado": "parado", "tarefa": "", "ts": ""}))
        a["eventos"] = [e for e in est["eventos"] if e["agente"] == a["nome"]][:8]
    return agentes


def app_escritorio():
    if sala is None or not (TELA / "index.html").exists():
        return {"no_ar": False}
    return {"no_ar": True, "url": f"/escritorio/?token={TOKEN}"}


def primeiros_passos():
    """O que falta para o Ciello OS refletir a empresa real. Cada passo diz onde resolver (janela, aba e formulário)."""
    clientes = financeiro.ler(financeiro.CLIENTES, financeiro.C_CLIENTE)
    cfg = financeiro.config()
    retratos = sorted((RAIZ / "metricas").glob("20??-??-??.json"))
    idade = (financeiro.hoje() - financeiro.data(retratos[-1].stem)).days if retratos else None
    p = plano.ler()
    passos = [
        ("clientes", "Cadastre os clientes que já pagam", "CRM, hospedagem e sites em andamento: sem eles não há cobrança, pós-venda nem MRR.",
         bool(clientes), ["financeiro", "clientes", "novoCliente"]),
        ("caixa", "Informe o saldo do banco", "É o ponto de partida do caixa e da previsão de 30, 60 e 90 dias.",
         bool(cfg.get("data_saldo")) or financeiro.LANCAMENTOS.exists(), ["financeiro", "geral", "caixa"]),
        ("plano", "Monte o plano do ano", "Negócios, custos e quanto você precisa tirar: a auditoria aponta o que não fecha.",
         bool(p["negocios"]), ["financeiro", "plano", ""]),
        ("meta", "Defina a meta de clientes", "Quantos clientes até quando: o OS calcula as abordagens e demos da semana e avisa se ficar para trás.",
         bool(metas.ler().get("clientes")), ["financeiro", "rumo", "meta"]),
        ("voz", "Grave a sua voz", "10 a 20 segundos lendo um texto: os vídeos podem sair com a sua voz.",
         estudio_voz.voz.AMOSTRA.exists(), ["voz", "", ""]),
        ("instagram", "Atualize os números do Instagram", "Retrato da semana: o Bom dia e o relatório usam.",
         idade is not None and idade <= 7, ["conteudo", "instagram", "retrato"]),
        ("leads", "Coloque leads na fila", "Busca no Google Maps, planilha ou quem chegou sozinho.",
         sdr.LEADS.exists() and bool(sdr.ler_leads()), ["comercial", "buscar", ""]),
    ]
    return [{"id": i, "titulo": t, "porque": d, "feito": f, "abrir": a} for i, t, d, f, a in passos]


def app_briefing():
    ref = financeiro.hoje()
    itens, fin, leads = briefing.coletar(ref)
    return {"data": ref.isoformat(), "itens": itens, "numeros": briefing.numeros(fin, leads, ref), "passos": primeiros_passos()}


def app_financeiro():
    clientes = financeiro.ler(financeiro.CLIENTES, financeiro.C_CLIENTE)
    lancs = financeiro.ler(financeiro.LANCAMENTOS, financeiro.C_LANC)
    faturas = financeiro.ler(financeiro.FATURAS, financeiro.C_FATURA)
    ref = financeiro.hoje()
    mes = ref.strftime("%Y-%m")
    serie = [financeiro.metricas_mes(financeiro.meses_atras(mes, i), clientes, lancs) for i in range(5, -1, -1)]
    por_id = {c["id"]: c for c in clientes}
    abertas = [{"id": f["id"], "empresa": por_id.get(f["cliente_id"], {}).get("empresa", "?"), "competencia": f["competencia"], "descricao": f["descricao"],
                "vencimento": f["vencimento"], "valor": float(f["valor"] or 0), "dias": (ref - financeiro.data(f["vencimento"])).days}
               for f in faturas if not f["pago_em"]]
    ultimos = sorted(lancs, key=lambda l: (l["data"], int(l["id"]) if l["id"].isdigit() else 0), reverse=True)
    cfg = financeiro.config()
    return {"situacao": financeiro.situacao(), "serie": serie, "clientes": clientes,
            "faturas_abertas": sorted(abertas, key=lambda f: f["vencimento"]),
            "faturado_no_mes": any(f["competencia"] == mes for f in faturas), "mes": mes,
            "cobrancas": financeiro.cobrancas_devidas(), "posvenda": financeiro.posvendas_devidos(),
            "gastos": gastos.analisar(ref, lancs), "carteira": carteira.carteira(ref), "lancamentos": ultimos[:40], "a_classificar": [l for l in ultimos if l["categoria"] == financeiro.SEM_CATEGORIA][:40],
            "categorias": financeiro.categorias(), "produtos": financeiro.produtos(),
            "config": {k: cfg[k] for k in ("saldo_inicial", "data_saldo", "alerta_saldo", "link_avaliacao", "assinatura")}}


def app_comercial():
    leads = ler_leads()
    hoje = financeiro.hoje().isoformat()
    try:
        cfg_icp = sdr.icp()
    except (OSError, ValueError):
        cfg_icp = {"segmentos": {}, "cidades": []}
    assinatura = financeiro.config()["assinatura"]
    campos = ("id", "empresa", "segmento", "cidade", "telefone", "whatsapp", "site", "email", "nota_google", "avaliacoes", "pontos",
              "etapa", "ultimo_contato", "proximo_contato", "tentativas", "dor_citada", "maps", "origem", "obs", "agenda")
    resumo = lambda l: {**{k: l.get(k) or "" for k in campos}, "oferta": sdr.oferta(l)}

    def com_msg(l, msg):
        return {**resumo(l), "mensagem": msg, "link": sdr.link_wa(l["telefone"], msg) if l.get("whatsapp") and l.get("telefone") else ""}

    followups = [com_msg(l, sdr.seguimento(l, int(l.get("tentativas") or 1))) for l in leads
                 if l["etapa"] == "contatado" and l.get("proximo_contato") and l["proximo_contato"] <= hoje]
    novos = sorted((l for l in leads if l["etapa"] == "novo" and l.get("telefone")), key=lambda l: -int(l.get("pontos") or 0))[:15]
    abordar = []
    for l in novos:
        try:
            abordar.append(com_msg(l, sdr.primeira_mensagem(l, cfg_icp, assinatura)))
        except (KeyError, ValueError):
            abordar.append(com_msg(l, ""))
    return {"funil": kpis()["funil"], "hoje": hoje, "testes": financeiro.testes_acabando(), "oportunidades": financeiro.oportunidades(), "agenda": sdr.agenda(),
            "ritmo": metas.calcular(), "quentes": [resumo(l) for l in leads if l["etapa"] in ("respondeu", "demo", "proposta")],
            "followups": followups, "abordar": abordar, "novos": [resumo(l) for l in novos[:8]],
            "leads": [resumo(l) for l in leads], "etapas": sdr.ETAPAS, "segmentos": list(cfg_icp["segmentos"]),
            "cidades": cfg_icp["cidades"], "tem_consultas": (sdr.PASTA / "bruto" / "consultas.txt").exists(),
            "tem_resultado": (sdr.PASTA / "bruto" / "resultados.csv").exists(),
            "tem_buscador": any(p.is_file() for p in (sdr.PASTA / "bin").glob("google*maps*scraper*"))}


def app_conteudo():
    posts = []
    for r in sorted((RAIZ / "roteiros").glob("20??-??-??-*.json")):
        d = ler_json(r, {}) or {}
        linhas = (d.get("capa") or {}).get("linhas") or []
        titulo = " ".join(l[0] if isinstance(l, list) else str(l) for l in linhas) or r.stem[11:].replace("-", " ")
        capa = RAIZ / "midia" / "capas" / f"{r.stem}.jpg"
        posts.append({"data": r.name[:10], "slug": r.stem[11:], "titulo": titulo,
                      "capa": f"/midia/capas/{capa.name}" if capa.exists() else "",
                      "final": (RAIZ / "midia" / "final" / f"{r.stem}.mp4").exists()})
    quadro = conteudo.quadro()
    return {"instagram": kpis()["instagram"], "posts": posts[::-1], "quadro": quadro, "alertas": conteudo.alertas(quadro),
            "horarios": conteudo.proximos_horarios(), "etapas": [[e, conteudo.ROTULOS[e]] for e in conteudo.ETAPAS],
            "relatorio": ultimo_relatorio_instagram()}


def app_video():
    """Estúdio de Vídeo: os roteiros da agenda, o que já tem narração, rascunho e final, e os modelos."""
    posts = []
    for q in conteudo.quadro(dias_passados=30):
        rasc = {m: estudio_video.rascunho(q["post"], m).exists() for m in estudio_video.MODELOS}
        posts.append({**{k: q[k] for k in ("post", "slug", "data", "dias", "titulo", "etapas")}, "rascunhos": rasc,
                      "narracao": (RAIZ / "audio" / q["slug"] / "narracao.wav").exists()})
    return {"posts": posts[::-1], "modelos": {k: {"nome": v["nome"], "descricao": v["descricao"], "fundo": v["fundo"], "ouro": v["ouro"], "texto": v["texto"]}
                                              for k, v in estudio_video.MODELOS.items()},
            "hyperframes": (RAIZ / "reels" / "node_modules" / ".bin" / ("hyperframes.cmd" if os.name == "nt" else "hyperframes")).exists(),
            "voz": estudio_voz.voz.preferencia()["motor"], "proximos": conteudo.proximos_horarios()}


def app_atendimento():
    """FAQ (com o que falta completar) e os clientes com WhatsApp, para a resposta sair com o link certo."""
    clientes = [{"id": c["id"], "empresa": c["empresa"], "contato": c["contato"], "whatsapp": c["whatsapp"]}
                for c in financeiro.ler(financeiro.CLIENTES, financeiro.C_CLIENTE) if c["status"] in ("ativo", "teste", "projeto") and c["whatsapp"]]
    quentes = [{"id": f"lead{l['id']}", "empresa": l["empresa"], "contato": "", "whatsapp": l["telefone"]}
               for l in ler_leads() if l.get("etapa") in ("respondeu", "demo", "proposta") and l.get("telefone")]
    return {"faq": atendimento.ler(), "clientes": clientes + quentes}


def ultimo_relatorio_instagram():
    arqs = sorted((RAIZ / "metricas").glob("relatorio-20??-??-??.md"))
    return {"arquivo": arqs[-1].relative_to(RAIZ).as_posix(), "texto": arqs[-1].read_text(encoding="utf-8")} if arqs else None


def ultimo_md(padrao):
    arqs = [p for p in (RAIZ / "radar").glob(padrao) if re.search(r"\d{4}-\d{2}-\d{2}", p.name)]
    if not arqs:
        return None
    p = max(arqs, key=lambda p: (re.search(r"\d{4}-\d{2}-\d{2}", p.name).group(0), p.stat().st_mtime))
    return {"arquivo": p.relative_to(RAIZ).as_posix(), "texto": p.read_text(encoding="utf-8")}


def app_rumo():
    return {"meta": metas.calcular(), "taxas_padrao": {k: v[1] for k, v in metas.TAXAS.items()}, **decisoes.para_janela()}


def app_conexoes():
    return conexoes.para_janela(social.historico_por_provedor())


def app_redes():
    """Rede social: piloto (fila e diário), calendário do mês com a previsão, comentários e resultados."""
    hoje = financeiro.hoje()
    prox = (hoje.replace(day=1) + __import__("datetime").timedelta(days=32)).replace(day=1)
    return {"piloto": piloto.para_janela(), "calendario": calendario.mes(hoje.year, hoje.month, hoje),
            "calendario_proximo": calendario.mes(prox.year, prox.month, hoje), "comentarios": social.caixa(),
            "aguardando": social.caixa(estado="responder_no_app"), "resultados": social.resultados(),
            "conexoes": {pid: e for pid, e in conexoes.estados().items()}, "redes": conexoes.redes(), "nomes_redes": conexoes.REDES}


def app_concorrentes():
    cfg = ler_json(RAIZ / "comercial" / "concorrentes.json", {"concorrentes": []})
    return {"relatorio": ultimo_md("concorrentes-*.md"), "concorrentes": [c["nome"] for c in cfg["concorrentes"]]}


def app_tendencias():
    return {"relatorio": ultimo_md("20??-??-??*.md")}


APPS = {"escritorio": app_escritorio, "conexoes": app_conexoes, "redes": app_redes, "rumo": app_rumo, "voz": estudio_voz.estado, "video": app_video, "atendimento": app_atendimento, "plano": plano.para_janela, "briefing": app_briefing, "financeiro": app_financeiro, "comercial": app_comercial,
        "conteudo": app_conteudo, "concorrentes": app_concorrentes, "tendencias": app_tendencias,
        "anuncios": lambda: {"campanhas": campanhas(), "resumo": kpis()["anuncios"]}, "atualizacoes": atualizacao.resumo_status}


# ---------------------------------------------------------------- execução das ações

def rodar(acao):
    rotulo, agente, args = ACOES[acao]
    return executar(rotulo, agente, args, acao)


def executar(rotulo, agente, args, acao="tarefa"):
    """Roda `python <args>` na pasta do assistente em segundo plano; a janela acompanha por /api/execucao/<id>."""
    eid = f"{int(time.time() * 1000)}-{acao}"
    ex = {"id": eid, "acao": acao, "rotulo": rotulo, "agente": agente, "saida": "", "terminou": False, "codigo": None,
          "inicio": time.strftime("%H:%M:%S")}
    with trava:
        execucoes[eid] = ex

    def trabalho():
        status.registrar(agente, "trabalhando", rotulo)
        env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
        try:
            proc = subprocess.Popen([PY, *args], cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding="utf-8", errors="replace", env=env)
            for linha in proc.stdout:
                with trava:
                    ex["saida"] = (ex["saida"] + linha)[-60000:]
            ex["codigo"] = proc.wait()
            proc.stdout.close()
        except OSError as e:
            ex["saida"] += f"\nNão consegui rodar: {e}"
            ex["codigo"] = -1
        ex["terminou"] = True
        status.registrar(agente, "pronto" if ex["codigo"] == 0 else "erro", rotulo)

    threading.Thread(target=trabalho, daemon=True).start()
    return ex


# ---------------------------------------------------------------- operação sem o Claude (janelas Financeiro, Comercial, Conteúdo, Anúncios)

def operar(op, dados):
    if op == "voz_testar":
        try:
            args, nome = estudio_voz.args_teste(dados)
        except ValueError as e:
            return {"ok": False, "saida": str(e)}
        ex = executar("Teste de voz", "produtor-video", args, "voz")
        return {"ok": True, "saida": "Gerando a voz…", "execucao": ex["id"], "arquivo": nome}
    if op == "voz_preferir":
        return estudio_voz.preferir(dados)
    if op == "voz_clonar_vs":
        ex = executar("Clonar a sua voz no VoiceStudio", "produtor-video", ["central/voz.py", "--clonar-voicestudio=Mateus (Ciello)"], "voz")
        return {"ok": True, "saida": "Clonando no VoiceStudio…", "execucao": ex["id"]}
    if op == "voz_vozes_vs":
        try:
            return {"ok": True, "saida": "", "vozes": estudio_voz.voz.VoiceStudio(espera=30).vozes()}
        except (OSError, RuntimeError, ValueError) as e:
            return {"ok": False, "saida": f"Não consegui falar com o VoiceStudio: {e}"}
    if op == "faq_buscar":
        return {"ok": True, "saida": "", "achados": atendimento.buscar(str(dados.get("texto") or "")[:1000], 4)}
    if op == "faq_salvar":
        return atendimento.salvar(dados.get("pergunta"), dados.get("resposta"), dados.get("i"), str(dados.get("secao") or "Perguntas novas")[:60])
    if op == "video_roteiro":
        itens = dados.get("itens")
        itens = itens if isinstance(itens, list) else str(itens or "").split("\n")
        return conteudo.novo_roteiro(dados.get("data"), dados.get("gancho"), itens, dados.get("cta"), str(dados.get("pilar") or "")[:40])
    if op in ("video_gerar", "video_usar"):
        post, modelo = str(dados.get("post") or ""), dados.get("modelo") or "escuro"
        if not re.fullmatch(r"20\d\d-\d\d-\d\d-[\w\-]{1,80}", post) or modelo not in estudio_video.MODELOS or not (RAIZ / "roteiros" / f"{post}.json").exists():
            return {"ok": False, "saida": "roteiro ou modelo inválido"}
        if op == "video_usar":
            try:
                destino = estudio_video.usar(post, modelo)
            except SystemExit as e:
                return {"ok": False, "saida": str(e)}
            return {"ok": True, "saida": f"vídeo final salvo em {destino.relative_to(RAIZ).as_posix()}"}
        args = ["central/estudio_video.py", "gerar", post, f"--modelo={modelo}"] + (["--rascunho"] if dados.get("rascunho") else [])
        ex = executar(f"Vídeo · {post[11:]}", "produtor-video", args, "video")
        return {"ok": True, "saida": "Gerando o vídeo…", "execucao": ex["id"]}
    if op in ("cont_legenda", "cont_legenda_salvar", "cont_agendado"):
        post = str(dados.get("post") or "")
        if not re.fullmatch(r"20\d\d-\d\d-\d\d-[\w\-]{1,80}", post):
            return {"ok": False, "saida": "post inválido"}
        if op == "cont_legenda":
            return conteudo.gerar_legenda(post, bool(dados.get("forcar")))
        if op == "cont_legenda_salvar":
            return conteudo.salvar_legenda(post, dados.get("texto", ""))
        return conteudo.marcar_agendado(post, str(dados.get("quando") or ""), "Publicado" if dados.get("publicado") else "Agendado")
    if op == "conexao_salvar":
        return conexoes.salvar_credenciais(str(dados.get("provedor")), dados)
    if op == "conexao_checar":
        return conexoes.checar(str(dados.get("provedor")))
    if op == "conexao_desconectar":
        return conexoes.desconectar(str(dados.get("provedor")))
    if op == "conexao_rede":
        return conexoes.configurar_rede(str(dados.get("rede")), dados.get("ativa"), dados.get("via"))
    if op == "oauth_inicio":
        return conexoes.oauth_inicio(str(dados.get("provedor")), f"http://127.0.0.1:{PORTA_ATUAL[0]}")
    if op == "piloto_config":
        return piloto.configurar(dados)
    if op == "calendario_config":
        return calendario.configurar(dados)
    if op in ("envio_segurar", "envio_aprovar", "envio_tentar"):
        f = {"envio_segurar": piloto.segurar, "envio_aprovar": piloto.aprovar, "envio_tentar": piloto.tentar_de_novo}[op]
        return f(str(dados.get("post")), str(dados.get("rede")))
    if op == "comentario_responder":
        return social.responder(str(dados.get("rede")), str(dados.get("id")), str(dados.get("texto") or ""))
    if op == "comentario_marcar":
        return social.marcar(str(dados.get("rede")), str(dados.get("id")), str(dados.get("estado")))
    if op == "social_exportar":
        destino = social.exportar(social.dados.estado("exportacao", financeiro.hoje().isoformat()))
        return {"ok": True, "saida": f"Histórico exportado em CSV: {destino}"}
    if op == "meta_config":
        return metas.configurar(dados)
    if op == "decisao_salvar":
        return decisoes.salvar(dados)
    if op == "decisao_remover":
        return decisoes.remover(str(dados.get("chave") or ""))
    if op == "plano_config":
        return plano.configurar(dados)
    if op == "plano_item":
        return plano.salvar_item(dados.get("lista"), dados)
    if op == "plano_remover":
        return plano.remover_item(dados.get("lista"), dados.get("i", -1))
    if op == "plano_importar":
        p = plano.ler()
        n = plano.importar_clientes(p)
        plano.gravar(p)
        return {"ok": True, "saida": f"{n} assinatura(s) do financeiro entraram no plano" if n else "Nenhuma assinatura nova para trazer."}
    if op == "ig_retrato":
        return operacao.salvar_retrato(dados)
    if op == "anuncio":
        return operacao.salvar_campanha(dados)
    if op in ("sdr_entrada", "sdr_agendar") and not dados.get("assinatura"):
        dados = {**dados, "assinatura": financeiro.config()["assinatura"]}
    return operacao.operar(op, dados)


# ---------------------------------------------------------------- servidor

class Painel(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def _enviar(self, corpo, tipo, codigo=200):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, dado, codigo=200):
        self._enviar(json.dumps(dado, ensure_ascii=False, default=str).encode("utf-8"), "application/json; charset=utf-8", codigo)

    def _local(self):
        """Só responde para o próprio app: endereço local no Host e, quando o navegador manda Origin (WebSocket,
        POST), a origem tem de ser o Ciello OS. Sem isso, outro site aberto no navegador poderia ler o escritório."""
        host = (self.headers.get("Host") or "").split(":")[0]
        porta = self.server.server_address[1]
        origem = self.headers.get("Origin")
        if host not in ("127.0.0.1", "localhost") or (origem and origem not in (f"http://127.0.0.1:{porta}", f"http://localhost:{porta}")):
            self._json({"erro": "só pelo próprio Ciello OS"}, 403)
            return False
        return True

    def _arquivo(self, base, rel):
        alvo = (base / rel).resolve()
        if not alvo.is_relative_to(base.resolve()) or not alvo.is_file() or alvo.suffix.lower() not in TIPOS:
            return self._json({"erro": "não encontrado"}, 404)
        self._enviar(alvo.read_bytes(), TIPOS[alvo.suffix.lower()])

    def _tela(self, rel):
        """A tela do escritório (build de escritorio/webview-ui). Ela mesma avisa a área de trabalho do clique num
        personagem e obedece à engrenagem e ao "centralizar" (src/ciello/ na tela)."""
        return self._arquivo(TELA, urllib.request.unquote(rel or "index.html"))

    def _websocket(self):
        """O escritório conversa por aqui. Com o token do Ciello OS a tela pode mudar coisas; sem ele, só olha."""
        if sala is None:
            return self._json({"erro": "escritório desligado"}, 503)
        consulta = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
        privilegiada = secrets.compare_digest((consulta.get("token") or [""])[0], TOKEN)
        conexao = websocket.aceitar(self)
        if conexao is None:
            return self._json({"erro": "esperava WebSocket"}, 400)
        sala.conectar(conexao, privilegiada)

    def _terminal(self):
        """A janela "Claude Code" conversa com o terminal por aqui (só com o token desta sessão do Ciello OS)."""
        consulta = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
        if not secrets.compare_digest((consulta.get("token") or [""])[0], TOKEN):
            return self._json({"erro": "token inválido"}, 403)
        t = terminais.get((consulta.get("id") or [""])[0])
        if t is None:
            return self._json({"erro": "terminal não encontrado"}, 404)
        conexao = websocket.aceitar(self)
        if conexao is None:
            return self._json({"erro": "esperava WebSocket"}, 400)
        t.ouvir(conexao.enviar)
        try:
            while (texto := conexao.receber()) is not None:
                try:
                    msg = json.loads(texto)
                except ValueError:
                    continue
                if msg.get("tipo") == "entrada" and isinstance(msg.get("dados"), str):
                    t.escrever(msg["dados"])
                elif msg.get("tipo") == "tamanho":
                    t.redimensionar(int(msg.get("linhas") or 0), int(msg.get("colunas") or 0))
        finally:
            t.largar(conexao.enviar)

    def _oauth(self, pid):
        """O Google ou o TikTok voltam para cá depois do login: troca o código pelo token e guarda no cofre."""
        q = {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).items()}
        if q.get("error"):
            r = {"ok": False, "saida": f"login cancelado ({q.get('error_description') or q['error']})"}
        else:
            r = conexoes.oauth_retorno(pid, q.get("code", ""), q.get("state", ""))
        cor = "#1F8A4C" if r["ok"] else "#C8442F"
        corpo = (f"<!doctype html><meta charset=utf-8><title>Ciello OS</title><body style='font:16px sans-serif;background:#F8F4E8;"
                 f"display:grid;place-items:center;height:90vh'><div style='text-align:center'><h2 style='color:{cor}'>"
                 f"{'Conectado!' if r['ok'] else 'Não deu certo'}</h2><p>{html.escape(r['saida'])}</p><p>Pode fechar esta aba e voltar ao Ciello OS.</p></div>")
        return self._enviar(corpo.encode("utf-8"), "text/html; charset=utf-8")

    def do_GET(self):
        if not self._local():
            return
        try:
            self._get()
        except Exception as e:  # noqa: BLE001  um arquivo com problema vira erro 500, não "servidor desligado"
            try:
                self._json({"erro": f"{type(e).__name__}: {e}"}, 500)
            except OSError:
                pass

    def _get(self):
        caminho = self.path.split("?")[0]
        if caminho == "/escritorio":
            self.send_response(301)
            self.send_header("Location", "/escritorio/" + self.path[len("/escritorio"):])
            return self.end_headers()
        if caminho.startswith("/escritorio/"):
            return self._tela(caminho[len("/escritorio/"):])
        if caminho == "/ws":  # a tela abre o WebSocket na raiz do endereço
            return self._websocket()
        if caminho == "/terminal":
            return self._terminal()
        if caminho in ("/", "/index.html"):
            html = (WEB / "index.html").read_text(encoding="utf-8").replace("__CIELLO_TOKEN__", TOKEN)
            return self._enviar(html.encode("utf-8"), TIPOS[".html"])
        if caminho.startswith("/web/"):
            return self._arquivo(WEB, caminho[5:])
        if caminho.startswith("/midia/"):
            return self._arquivo(RAIZ / "midia", urllib.request.unquote(caminho[7:]))
        if caminho.startswith("/api/voz/arquivo/"):
            alvo = estudio_voz.arquivo(urllib.request.unquote(caminho[17:]))
            return self._enviar(alvo.read_bytes(), TIPOS[".wav"]) if alvo else self._json({"erro": "não encontrado"}, 404)
        if caminho == "/api/terminais":
            return self._json({"ids": [tid for tid, t in terminais.todos.items() if t.fim is None]})
        if caminho == "/api/estado":
            return self._json(status.ultimo_estado())
        if caminho == "/api/kpis":
            return self._json(kpis())
        if caminho == "/api/equipe":
            return self._json(equipe())
        if caminho.startswith("/oauth/") and caminho[7:] in conexoes.PROVEDORES:
            return self._oauth(caminho[7:])
        if caminho.startswith("/api/app/") and caminho[9:] in APPS:
            return self._json(APPS[caminho[9:]]())
        if caminho.startswith("/api/execucao/"):
            ex = execucoes.get(caminho[14:])
            return self._json(ex) if ex else self._json({"erro": "execução não encontrada"}, 404)
        return self._json({"erro": "não encontrado"}, 404)

    def do_POST(self):
        if not self._local():
            return
        if self.path == "/api/ganchos/claude":
            return self._gancho()
        if self.headers.get("X-Ciello-Token") != TOKEN:
            return self._json({"erro": "token inválido"}, 403)
        tam = int(self.headers.get("Content-Length") or 0)
        if self.path.startswith("/api/enviar?"):
            return self._enviar_arquivo(tam)
        if tam > 1_000_000:
            return self._json({"erro": "pedido grande demais"}, 413)
        try:
            pedido = json.loads(self.rfile.read(tam) or b"{}") if tam else {}
        except ValueError:
            return self._json({"erro": "JSON inválido"}, 400)
        if self.path == "/api/rodar":
            if pedido.get("acao") not in ACOES:
                return self._json({"erro": "ação desconhecida"}, 400)
            return self._json(rodar(pedido["acao"]))
        if self.path == "/api/operar":
            return self._json(operar(pedido.get("op"), pedido.get("dados") or {}))
        if self.path == "/api/terminal":
            prompt = pedido.get("prompt") if isinstance(pedido.get("prompt"), str) and pedido["prompt"].strip() else None
            t = terminais.abrir(prompt, str(pedido.get("titulo") or "")[:80], persistencia.preferencia("bypassPermissions"))
            return self._json({"id": t.id})
        if self.path == "/api/terminal/fechar":
            terminais.fechar(pedido.get("id"))
            return self._json({"ok": True})
        return self._json({"erro": "não encontrado"}, 404)

    def _enviar_arquivo(self, tam):
        """Extrato do banco ou planilha de leads mandados pela janela (o arquivo vai no corpo, o resto na URL)."""
        if not 0 < tam <= 25_000_000:
            return self._json({"ok": False, "saida": "arquivo vazio ou maior que 25 MB"}, 413)
        dados = self.rfile.read(tam)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).items()}
        if q.get("tipo") == "voz":
            return self._json(estudio_voz.salvar_amostra(q.get("nome"), dados))
        return self._json(operacao.importar_arquivo(q.get("tipo"), q.get("nome"), dados, q))

    def _gancho(self):
        """Evento de hook do Claude Code (central/escritorio/gancho.py), com o token anotado em servidor.json."""
        if sala is None:
            return self._json({"erro": "escritório desligado"}, 503)
        if not secrets.compare_digest(self.headers.get("Authorization") or "", f"Bearer {sala.token_gancho}"):
            return self._json({"erro": "token inválido"}, 401)
        tam = int(self.headers.get("Content-Length") or 0)
        if tam > 65536:
            return self._json({"erro": "evento grande demais"}, 413)
        try:
            evento = json.loads(self.rfile.read(tam) or b"{}")
        except ValueError:
            return self._json({"erro": "JSON inválido"}, 400)
        sala.gancho(evento)
        self._enviar(b"ok", "text/plain; charset=utf-8")


def abrir_como_app(url):
    """Edge ou Chrome em modo app (janela própria, sem abas nem barra de endereço); senão, o navegador padrão."""
    candidatos = [shutil.which(n) for n in ("msedge", "chrome", "google-chrome", "chromium")]
    for var in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA"):
        base = os.environ.get(var)
        if base:
            candidatos += [os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"),
                           os.path.join(base, "Google", "Chrome", "Application", "chrome.exe")]
    for exe in filter(None, candidatos):
        if os.path.exists(exe):
            subprocess.Popen([exe, f"--app={url}", "--start-maximized"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
    webbrowser.open(url)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--porta", type=int, default=3200)
    ap.add_argument("--sem-navegador", action="store_true")
    ap.add_argument("--sem-escritorio", action="store_true", help="não liga o escritório de agentes")
    a = ap.parse_args()
    global sala
    PORTA_ATUAL[0] = a.porta
    srv = ThreadingHTTPServer(("127.0.0.1", a.porta), Painel)
    url = f"http://127.0.0.1:{a.porta}"
    print("Ciello OS em", url, "(Ctrl+C para sair)")
    if not a.sem_escritorio:
        sala = Sala(TELA, RAIZ, a.porta)
        print("Escritório acompanhando as sessões do Claude Code em", sala.iniciar())
    if not a.sem_navegador:
        threading.Timer(0.6, lambda: abrir_como_app(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
