"""Ciello OS: o assistente inteiro numa área de trabalho. O fundo é o Escritório (a tela pixel em web/escritorio/,
fork MIT do pixel-agents em escritorio/, servida pelo núcleo em Python de nucleo/, sem Node), com a barra de tarefas
embaixo e janelas que movem e redimensionam. Os apps ficam no menu Iniciar.

O escritório é servido pelo mesmo endereço do Ciello OS (/escritorio/) para a ponte (web/ponte-escritorio.js) ouvir o
clique num personagem e abrir a janela daquele agente. Cada sessão do Claude Code aberta na pasta do assistente vira
um personagem; com os hooks (o escritório pergunta na primeira vez), os movimentos são instantâneos.

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
"""
import argparse
import csv
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
import status  # noqa: E402
import briefing  # noqa: E402
import financeiro  # noqa: E402
from nucleo import websocket  # noqa: E402
from nucleo.sala import Sala  # noqa: E402

ETAPAS_FUNIL = ["novo", "contatado", "respondeu", "demo", "proposta", "cliente"]
PY = sys.executable
TOKEN = secrets.token_urlsafe(24)
TELA = WEB / "escritorio"  # build da tela do escritório (escritorio/webview-ui: npx vite build)
TIPOS = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".woff2": "font/woff2", ".mp4": "video/mp4",
         ".ttf": "font/ttf", ".ico": "image/x-icon", ".json": "application/json", ".webmanifest": "application/manifest+json"}
sala = None  # o escritório (nucleo.sala.Sala), criado no main

# O que os botões das janelas podem rodar: id -> (rótulo, agente, argumentos). Nada fora desta lista roda.
ACOES = {
    "briefing": ("Briefing do dia", "chefe-gabinete", ["central/briefing.py"]),
    "placar": ("Placar da semana", "chefe-gabinete", ["central/briefing.py", "--semana"]),
    "fin_resumo": ("Resumo financeiro", "financeiro", ["central/financeiro.py", "resumo"]),
    "fin_faturar": ("Faturas do mês", "financeiro", ["central/financeiro.py", "faturar"]),
    "fin_cobrar": ("Cobranças do dia", "financeiro", ["central/financeiro.py", "cobrar"]),
    "posvenda": ("Pós-venda do dia", "sucesso-cliente", ["central/financeiro.py", "posvenda"]),
    "sdr_hoje": ("Follow-ups de hoje", "sdr", ["central/sdr.py", "hoje"]),
    "sdr_abordar": ("Abordar os 15 melhores leads", "sdr", ["central/sdr.py", "abordar", "--top", "15"]),
    "sdr_crm": ("Exportar para o CIELLO CRM", "sdr", ["central/sdr.py", "crm"]),
    "vigia": ("Vigia de concorrentes", "pesquisador-mercado", ["central/vigia.py", "checar"]),
    "radar": ("Radar de tendências", "pesquisador-mercado", ["central/radar.py"]),
    "ganchos": ("Ranking de ganchos", "pesquisador-mercado", ["central/ganchos.py", "ranking"]),
    "relatorio": ("Relatório semanal", "analista", ["central/relatorio.py"]),
    "verificar": ("Verificação do assistente", "sistema", ["central/verificar.py", "--rapido"]),
}
execucoes = {}
trava = threading.Lock()


# ---------------------------------------------------------------- leitura dos dados

def ler_json(p, padrao=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def ler_leads():
    arq = RAIZ / "comercial" / "leads.csv"
    if not arq.exists():
        return []
    with arq.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


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


def app_briefing():
    ref = financeiro.hoje()
    itens, fin, leads = briefing.coletar(ref)
    return {"data": ref.isoformat(), "itens": itens, "numeros": briefing.numeros(fin, leads, ref)}


def app_financeiro():
    clientes = financeiro.ler(financeiro.CLIENTES, financeiro.C_CLIENTE)
    lancs = financeiro.ler(financeiro.LANCAMENTOS, financeiro.C_LANC)
    mes = financeiro.hoje().strftime("%Y-%m")
    serie = [financeiro.metricas_mes(financeiro.meses_atras(mes, i), clientes, lancs) for i in range(5, -1, -1)]
    return {"situacao": financeiro.situacao(), "serie": serie,
            "clientes": [{k: c[k] for k in ("id", "empresa", "plano", "valor_mensal", "inicio", "status", "nps")} for c in clientes]}


def app_comercial():
    leads = ler_leads()
    hoje = financeiro.hoje().isoformat()
    campos = ("id", "empresa", "segmento", "cidade", "etapa", "pontos", "ultimo_contato", "proximo_contato", "dor_citada", "origem", "obs")
    resumo = lambda l: {k: l.get(k, "") for k in campos}
    return {"funil": kpis()["funil"],
            "quentes": [resumo(l) for l in leads if l["etapa"] in ("respondeu", "demo", "proposta")],
            "followups": [resumo(l) for l in leads if l["etapa"] == "contatado" and l.get("proximo_contato") and l["proximo_contato"] <= hoje],
            "novos": [resumo(l) for l in sorted((l for l in leads if l["etapa"] == "novo"), key=lambda l: -int(l.get("pontos") or 0))[:8]]}


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
    return {"instagram": kpis()["instagram"], "posts": posts[::-1]}


def ultimo_md(padrao):
    arqs = [p for p in (RAIZ / "radar").glob(padrao) if re.search(r"\d{4}-\d{2}-\d{2}", p.name)]
    if not arqs:
        return None
    p = max(arqs, key=lambda p: (re.search(r"\d{4}-\d{2}-\d{2}", p.name).group(0), p.stat().st_mtime))
    return {"arquivo": p.relative_to(RAIZ).as_posix(), "texto": p.read_text(encoding="utf-8")}


def app_concorrentes():
    cfg = ler_json(RAIZ / "comercial" / "concorrentes.json", {"concorrentes": []})
    return {"relatorio": ultimo_md("concorrentes-*.md"), "concorrentes": [c["nome"] for c in cfg["concorrentes"]]}


def app_tendencias():
    return {"relatorio": ultimo_md("20??-??-??*.md")}


APPS = {"escritorio": app_escritorio, "briefing": app_briefing, "financeiro": app_financeiro, "comercial": app_comercial,
        "conteudo": app_conteudo, "concorrentes": app_concorrentes, "tendencias": app_tendencias,
        "anuncios": lambda: {"campanhas": campanhas(), "resumo": kpis()["anuncios"]}}


# ---------------------------------------------------------------- execução das ações

def rodar(acao):
    rotulo, agente, args = ACOES[acao]
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
        except OSError as e:
            ex["saida"] += f"\nNão consegui rodar: {e}"
            ex["codigo"] = -1
        ex["terminou"] = True
        status.registrar(agente, "pronto" if ex["codigo"] == 0 else "erro", rotulo)

    threading.Thread(target=trabalho, daemon=True).start()
    return ex


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
        """A tela do escritório. Só a página inicial ganha a ponte (o script que ouve o clique nos personagens)."""
        if rel in ("", "index.html"):
            html = (TELA / "index.html").read_bytes()
            html = html.replace(b"<head>", b'<head><script src="/web/pixel-ptbr.js"></script><script src="/web/ponte-escritorio.js"></script>', 1)
            html = html.replace(b'<html lang="en">', b'<html lang="pt-BR">', 1).replace(b"<title>Pixel Agents</title>", "<title>Escritório</title>".encode(), 1)
            return self._enviar(html, TIPOS[".html"])
        return self._arquivo(TELA, urllib.request.unquote(rel))

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
        if caminho in ("/", "/index.html"):
            html = (WEB / "index.html").read_text(encoding="utf-8").replace("__CIELLO_TOKEN__", TOKEN)
            return self._enviar(html.encode("utf-8"), TIPOS[".html"])
        if caminho.startswith("/web/"):
            return self._arquivo(WEB, caminho[5:])
        if caminho.startswith("/midia/"):
            return self._arquivo(RAIZ / "midia", urllib.request.unquote(caminho[7:]))
        if caminho == "/api/estado":
            return self._json(status.ultimo_estado())
        if caminho == "/api/kpis":
            return self._json(kpis())
        if caminho == "/api/equipe":
            return self._json(equipe())
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
        pedido = json.loads(self.rfile.read(tam) or b"{}") if tam else {}
        if self.path == "/api/rodar":
            if pedido.get("acao") not in ACOES:
                return self._json({"erro": "ação desconhecida"}, 400)
            return self._json(rodar(pedido["acao"]))
        return self._json({"erro": "não encontrado"}, 404)

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
