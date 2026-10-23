"""O que o escritório guarda entre uma abertura e outra, em ~/.ciello/escritorio:

  config.json   preferências da tela (som, rótulos, áreas, hooks...) e mapeamento das áreas
  estado.json   agentes acompanhados (para voltar depois de reiniciar) e lugar/cor de cada um
  layout.json   o escritório desenhado (salas, móveis, cores)

Na primeira vez, se existir o layout do pixel-agents original (~/.pixel-agents/layout.json), ele é trazido;
senão entra o layout padrão (central/escritorio/layout-padrao.json). O seu layout entra pelo editor do escritório
(Layout → Importar) ou pela janela Boas-vindas (Importar meus dados: escritorio/layout.json no .zip).
Quando o layout padrão muda (campo cielloLayout), quem ainda usa um padrão anterior (mesmo mexido no editor) recebe o
novo, com cópia do antigo em layout-antigo-v<N>.json. Um layout importado sem esse campo nunca é trocado.
"""
import json
import os
import shutil
from pathlib import Path

CASA = Path(os.environ.get("CIELLO_ESCRITORIO_CASA") or Path.home() / ".ciello" / "escritorio")
LAYOUT_PADRAO = Path(__file__).resolve().parent.parent / "layout-padrao.json"
LAYOUT_ANTIGO = Path.home() / ".pixel-agents" / "layout.json"

PREFERENCIAS = {  # nome na tela -> padrão
    "soundEnabled": True, "lastSeenVersion": "", "alwaysShowLabels": False, "ghostHeadlessAgents": False,
    "watchAllSessions": False, "hooksInfoShown": False, "showAreas": True, "bypassPermissions": False,
    "showHostDirectories": False,
}


def _ler(p: Path, padrao):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p: Path, dado):
    """Grava num temporário e troca de uma vez: um desligamento no meio não corrompe o arquivo."""
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(dado, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


# ------------------------------------------------------------------ preferências

def _do_pixel_agents():
    """Primeira abertura: traz as preferências e as áreas que já estavam no pixel-agents original."""
    antigo = _ler(Path.home() / ".pixel-agents" / "config.json", {})
    prefs = antigo.get("standalone") if isinstance(antigo.get("standalone"), dict) else {}
    return {"preferencias": {k: prefs[k] for k in PREFERENCIAS if k in prefs},
            "areas": prefs.get("areaMappings") if isinstance(prefs.get("areaMappings"), dict) else {}}


def config():
    c = _ler(CASA / "config.json", None)
    if c is None:
        c = _do_pixel_agents()
    prefs = c.get("preferencias") if isinstance(c.get("preferencias"), dict) else {}
    c["preferencias"] = {k: prefs.get(k, v) for k, v in PREFERENCIAS.items()}
    if not isinstance(c.get("areas"), dict):
        c["areas"] = {}
    c["areas"] = {k: [x for x in v if isinstance(x, str)] for k, v in c["areas"].items() if isinstance(v, list)}
    if not isinstance(c.get("pastasDeAtivos"), list):
        c["pastasDeAtivos"] = []
    c.setdefault("hooks", None)  # None = ainda não perguntado; True/False = resposta de quem usa
    return c


def gravar_config(c):
    _gravar(CASA / "config.json", c)


def preferencia(nome):
    return config()["preferencias"].get(nome, PREFERENCIAS.get(nome))


def definir_preferencia(nome, valor):
    if nome not in PREFERENCIAS:
        return
    c = config()
    c["preferencias"][nome] = valor
    gravar_config(c)


# ------------------------------------------------------------------ agentes e lugares

def estado():
    e = _ler(CASA / "estado.json", {})
    return {"agentes": e.get("agentes") if isinstance(e.get("agentes"), list) else [],
            "lugares": e.get("lugares") if isinstance(e.get("lugares"), dict) else {}}


def gravar_agentes(agentes):
    e = estado()
    e["agentes"] = agentes
    _gravar(CASA / "estado.json", e)


def gravar_lugares(lugares):
    e = estado()
    e["lugares"] = lugares
    _gravar(CASA / "estado.json", e)


# ------------------------------------------------------------------ layout

def versao_padrao(layout) -> int:
    return int(layout.get("cielloLayout") or 0) if isinstance(layout, dict) else 0


def _padrao_antigo(layout) -> bool:
    """O layout é um padrão que já veio com o app? Os numerados (cielloLayout) e o de 4 salas, que não tinha número."""
    if versao_padrao(layout):
        return True
    rotulos = {a.get("label") for a in layout.get("areas") or [] if isinstance(a, dict)}
    return (layout.get("cols"), layout.get("rows")) == (19, 16) and rotulos == {"Gerente", "Produtor Social", "Comercial", "Vendas"}


def ler_layout():
    p = CASA / "layout.json"
    if not p.exists():
        origem = LAYOUT_ANTIGO if LAYOUT_ANTIGO.exists() else LAYOUT_PADRAO
        if origem.exists():
            CASA.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origem, p)
    atual = _ler(p, None)
    novo = _ler(LAYOUT_PADRAO, None)
    if isinstance(atual, dict) and novo is not None and _padrao_antigo(atual) and versao_padrao(atual) < versao_padrao(novo):
        atualizar_layout(atual, novo)
        return novo
    return atual


def atualizar_layout(antigo, novo):
    """Chegou um layout padrão novo: guarda uma cópia do antigo, troca e refaz as áreas e os lugares dos agentes
    (as salas mudaram). Quem quiser o antigo de volta: Layout → Importar a cópia guardada."""
    _gravar(CASA / f"layout-antigo-v{versao_padrao(antigo)}.json", antigo)
    _gravar(CASA / "layout.json", novo)
    c = config()
    c["areas"], c["areasVistas"] = {}, []
    gravar_config(c)
    e = estado()
    e["lugares"] = {}
    _gravar(CASA / "estado.json", e)


def gravar_layout(layout):
    """O editor de layout salva sem o campo cielloLayout: mantém a versão, senão o padrão seria trocado de novo."""
    v = versao_padrao(_ler(CASA / "layout.json", None))
    if v and isinstance(layout, dict) and not layout.get("cielloLayout"):
        layout = {**layout, "cielloLayout": v}
    _gravar(CASA / "layout.json", layout)
