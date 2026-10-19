"""Painel Ciello: como a empresa está crescendo (Instagram, funil comercial, anúncios) e o que as ferramentas rodaram.

O escritório dos agentes é o pixel-agents original (central/escritorio/abrir.py, porta 3100); este painel fica na 3200.

  python central/escritorio/servidor.py          # abre http://127.0.0.1:3200

Fontes (todas locais):
  estado/eventos.jsonl     o que cada agente está fazendo (central/status.py)
  metricas/*.json          retratos semanais do Instagram (Analista)
  comercial/leads.csv      funil comercial (SDR e closer)
  anuncios/*.json          campanhas pagas (gestor de anúncios)
  financeiro/              MRR, caixa e faturas (central/financeiro.py) e as 3 prioridades do dia (central/briefing.py)
"""
import argparse
import csv
import json
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(AQUI.parent))
import status  # noqa: E402
import briefing  # noqa: E402
import financeiro  # noqa: E402

ETAPAS_FUNIL = ["novo", "contatado", "respondeu", "demo", "proposta", "cliente"]


def kpis():
    out = {"instagram": None, "funil": None, "anuncios": None, "financeiro": None, "prioridades": []}
    retratos = sorted((RAIZ / "metricas").glob("20??-??-??.json"))
    if retratos:
        atual = json.loads(retratos[-1].read_text(encoding="utf-8"))
        ant = json.loads(retratos[-2].read_text(encoding="utf-8")) if len(retratos) > 1 else None
        reels = atual.get("reels", [])
        alc = sum(r.get("alcance", 0) for r in reels) or 1
        out["instagram"] = {
            "data": atual["data"], "seguidores": atual["perfil"]["seguidores"],
            "seguidores_antes": (ant or {}).get("perfil", {}).get("seguidores", atual["perfil"].get("seguidores_inicio")),
            "alcance": atual["perfil"].get("alcance", 0), "contas_engajadas": atual["perfil"].get("contas_engajadas", 0),
            "tempo_medio": round(sum(r.get("tempo_medio_s", 0) for r in reels) / max(1, len(reels)), 1),
            "salvamentos_pct": round(100 * sum(r.get("salvamentos", 0) for r in reels) / alc, 2),
            "compart_pct": round(100 * sum(r.get("compartilhamentos", 0) for r in reels) / alc, 2),
            "serie": [{"data": json.loads(p.read_text(encoding="utf-8"))["data"],
                       "seguidores": json.loads(p.read_text(encoding="utf-8"))["perfil"]["seguidores"]} for p in retratos[-12:]],
            "horario": atual.get("melhor_horario", {}),
        }
    leads = RAIZ / "comercial" / "leads.csv"
    if leads.exists():
        with leads.open(encoding="utf-8") as f:
            linhas = list(csv.DictReader(f))
        ordem = {e: i for i, e in enumerate(ETAPAS_FUNIL)}
        # funil acumulado: quem chegou na demo também passou por "contatado" e "respondeu"
        alcancou = {e: sum(1 for l in linhas if ordem.get(l["etapa"], -1) >= i) for e, i in ordem.items()}
        out["funil"] = {"etapas": [{"etapa": e, "n": alcancou[e]} for e in ETAPAS_FUNIL],
                        "perdidos": sum(l["etapa"] in ("perdido", "frio") for l in linhas), "total": len(linhas)}
    campanhas = []
    for p in sorted((RAIZ / "anuncios").glob("*.json")):
        try:
            campanhas += json.loads(p.read_text(encoding="utf-8")).get("campanhas", [])
        except ValueError:
            pass
    if campanhas:
        gasto = sum(c.get("gasto", 0) for c in campanhas)
        conversas = sum(c.get("conversas", 0) for c in campanhas)
        clientes = sum(c.get("clientes", 0) for c in campanhas)
        out["anuncios"] = {"gasto": gasto, "conversas": conversas, "clientes": clientes,
                           "custo_conversa": round(gasto / conversas, 2) if conversas else None,
                           "custo_cliente": round(gasto / clientes, 2) if clientes else None, "campanhas": len(campanhas)}
    try:  # um arquivo do financeiro com problema não derruba o painel
        fin = financeiro.situacao()
        out["financeiro"] = fin if fin["tem_dados"] else None
        itens, _, _ = briefing.coletar(financeiro.hoje())
        out["prioridades"] = [{"texto": i["texto"], "dono": i["dono"]} for i in itens[:3]]
    except Exception as e:  # noqa: BLE001
        out["financeiro"], out["prioridades"] = None, [{"texto": f"erro ao ler o financeiro: {e}", "dono": "financeiro"}]
    return out


class Painel(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def _json(self, dado):
        corpo = json.dumps(dado, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path.startswith("/api/estado"):
            return self._json(status.ultimo_estado())
        if self.path.startswith("/api/kpis"):
            return self._json(kpis())
        corpo = (AQUI / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(corpo)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--porta", type=int, default=3200)
    ap.add_argument("--sem-navegador", action="store_true")
    a = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", a.porta), Painel)
    url = f"http://127.0.0.1:{a.porta}"
    print("Painel Ciello em", url, "(Ctrl+C para sair)")
    if not a.sem_navegador:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
