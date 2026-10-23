"""Os agentes da Ciello moram no escritório.

Cada agente de .claude/agents/ vira um personagem fixo, com nome e lugar na sua área (Pesquisa, Estúdio, Comercial,
Análise & Anúncios, Postagem). Parado, ele circula pelo escritório (a tela cuida da rotina). Quando uma sessão do
Claude Code chama esse agente (Task/Agent com subagent_type "sdr", ou descrição "sdr: ..."), é ele quem senta no PC e
trabalha: as ferramentas do subagente aparecem nele, e não num ajudante temporário ao lado do coordenador. Quando a
tarefa termina, ele levanta (com o visto de pronto) e volta para a rotina.
"""
from __future__ import annotations

import re
from pathlib import Path

from .agentes import Agente, Loja, Relogios

ID_BASE = 10_000  # longe dos ids das sessões (que começam em 1)
AREAS = {  # as salas do layout da Ciello (central/escritorio/gerar_layout.py)
    "gerente": "Gerente",
    "pesquisador-mercado": "Produtor Social", "roteirista": "Produtor Social", "produtor-video": "Produtor Social",
    "produtor-imagem": "Produtor Social", "postagem": "Produtor Social", "analista": "Produtor Social",
    "sdr": "Vendas", "closer": "Vendas", "sucesso-cliente": "Vendas",
    "financeiro": "Comercial", "gestor-anuncios": "Comercial", "caixa-entrada": "Comercial",
}
SALA_DAS_SESSOES = "Gerente"  # a sessão do Claude Code em que você conversa (os objetivos) senta na sala do Gerente
# o mesmo nome das janelas do Ciello OS (web/app.js, NOMES): o clique no personagem acha a janela por ele
NOMES = {
    "gerente": "Gerente", "pesquisador-mercado": "Pesquisador de Mercado", "roteirista": "Roteirista",
    "produtor-video": "Produtor de Vídeo", "produtor-imagem": "Produtor de Imagem", "postagem": "Postagem",
    "analista": "Analista", "gestor-anuncios": "Gestor de Anúncios", "sdr": "SDR", "closer": "Closer",
    "financeiro": "Financeiro", "caixa-entrada": "Caixa de Entrada", "sucesso-cliente": "Sucesso do Cliente",
}
PALETAS = 6
MATIZES = (0, 110, 220)  # sétimo agente em diante: mesmo personagem, outra cor


def equipe(raiz: Path) -> list[str]:
    """Nomes dos agentes definidos em .claude/agents/*.md (campo name do cabeçalho)."""
    nomes = []
    for md in sorted((Path(raiz) / ".claude" / "agents").glob("*.md")):
        try:
            cab = md.read_text(encoding="utf-8").split("---")[1]
        except (OSError, IndexError):
            continue
        m = re.search(r"^name:\s*(\S+)", cab, re.M)
        if m:
            nomes.append(m.group(1))
    return nomes


class Residentes:
    def __init__(self, loja: Loja, rel: Relogios):
        self.loja, self.rel = loja, rel
        self.ids: dict[str, int] = {}
        rel.ao_soltar = self.terminar

    def carregar(self, raiz: Path):
        self.raiz = raiz
        for i, nome in enumerate(equipe(raiz)):
            rid = ID_BASE + i
            a = Agente(id=rid, sessao="", pasta_projeto=str(raiz), jsonl="", externo=False, residente=True,
                       esperando=True, nome=NOMES.get(nome, nome), pasta_nome=NOMES.get(nome, nome),
                       paleta=i % PALETAS, matiz=MATIZES[(i // PALETAS) % len(MATIZES)])
            self.loja.por(rid, a)
            self.ids[nome] = rid
            self.loja.transmitir(a.info_equipe())
            self.loja.transmitir({"type": "agentStatus", "id": rid, "status": "waiting", "silencioso": True})

    def areas(self) -> dict[str, list[str]]:
        """Área inicial de cada residente (a chave é o nome dele, que aparece no editor de áreas para você mudar)."""
        areas = {NOMES.get(n, n): [AREAS[n]] for n in self.ids if n in AREAS}
        if getattr(self, "raiz", None):
            areas[Path(self.raiz).name] = [SALA_DAS_SESSOES]
        return areas

    # ---------------------------------------------------------- quem é chamado
    def por_nome(self, nome) -> int | None:
        """Id do residente com este nome ("sdr", "SDR", "pesquisador mercado"...), ou None."""
        if not isinstance(nome, str):
            return None
        n = nome.strip().lower()
        for chave, rid in self.ids.items():
            if n in (chave, chave.replace("-", " "), NOMES.get(chave, "").lower()):
                return rid
        return None

    def para(self, entrada) -> int | None:
        """Id do residente que esta chamada de Task/Agent aciona, ou None."""
        if not isinstance(entrada, dict):
            return None
        tipo = entrada.get("subagent_type")
        if isinstance(tipo, str) and tipo in self.ids:
            return self.ids[tipo]
        desc = entrada.get("description")
        if isinstance(desc, str) and ":" in desc:
            prefixo = desc.split(":", 1)[0].strip().lower()
            for nome, rid in self.ids.items():
                if prefixo in (nome, nome.replace("-", " "), NOMES.get(nome, "").lower()):
                    return rid
        return None

    def comecar(self, pai: Agente, tid: str, entrada: dict) -> bool:
        rid = self.para(entrada)
        r = self.loja.get(rid) if rid is not None else None
        if not r:
            return False
        pai.redirecionados[tid] = rid
        desc = entrada.get("description") if isinstance(entrada.get("description"), str) else ""
        if ":" in desc:
            desc = desc.split(":", 1)[1].strip()
        status = desc or "Trabalhando"
        r.ferramentas[tid] = [status, ""]
        r.esperando = False
        self.loja.transmitir({"type": "agentStatus", "id": rid, "status": "active"})
        self.loja.transmitir({"type": "agentToolStart", "id": rid, "toolId": tid, "status": status, "toolName": ""})
        return True

    # ---------------------------------------------------------- ferramentas do subagente
    def sub_inicio(self, pai: Agente, mae: str, sub_id: str, status: str, nome_ferramenta: str = ""):
        r = self.loja.get(pai.redirecionados.get(mae))
        if not r:
            return
        r.ferramentas[sub_id] = [status, nome_ferramenta]
        self.loja.transmitir({"type": "agentToolStart", "id": r.id, "toolId": sub_id, "status": status,
                              "toolName": nome_ferramenta})

    def sub_fim(self, pai: Agente, mae: str, sub_id: str):
        r = self.loja.get(pai.redirecionados.get(mae))
        if not r or sub_id not in r.ferramentas:
            return
        r.tirar_ferramenta(sub_id)
        self.rel.feito_depois({"type": "agentToolDone", "id": r.id, "toolId": sub_id})

    def permissao(self, pai: Agente, mae: str) -> bool:
        rid = pai.redirecionados.get(mae)
        if rid is None:
            return False
        self.loja.transmitir({"type": "agentToolPermission", "id": rid})
        return True

    # ---------------------------------------------------------- fim
    def terminar(self, pai: Agente, tid: str):
        """A tarefa acabou (ou foi interrompida): o residente levanta quando não sobra nenhuma outra."""
        rid = pai.redirecionados.pop(tid, None)
        r = self.loja.get(rid) if rid is not None else None
        if not r:
            return
        r.ferramentas.pop(tid, None)
        # as sub-ferramentas desta tarefa: tudo o que o residente tem e não é outra tarefa ativa
        outras = {t for p in self.loja.valores() for t, x in p.redirecionados.items() if x == rid}
        for t in [t for t in r.ferramentas if t not in outras]:
            r.tirar_ferramenta(t)
        if r.ferramentas:
            self.rel.feito_depois({"type": "agentToolDone", "id": rid, "toolId": tid})
            return
        r.esperando, r.permissao_enviada = True, False
        self.loja.transmitir({"type": "agentToolsClear", "id": rid})
        self.loja.transmitir({"type": "agentStatus", "id": rid, "status": "waiting", "awaitingInput": False})
