"""Estado dos agentes, o laço de eventos e os temporizadores.

Tudo o que mexe nos agentes roda numa thread só (o Laco), como no servidor original: as threads do WebSocket e
dos hooks só põem trabalho na fila. Assim não há corrida entre a leitura do JSONL, um hook e um clique na tela.
"""
from __future__ import annotations

import heapq
import itertools
import os
import queue
import random
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

# tempos (segundos) iguais aos do original
FERRAMENTA_FEITA = 0.3      # espera antes de avisar "ferramenta terminou" (evita piscar)
PERMISSAO = 7.0             # ferramenta parada esse tempo = provavelmente pedindo permissão
TEXTO_PARADO = 5.0          # resposta só de texto sem nada novo = terminou a vez
CONTEXTO_PADRAO = 200_000
CONTEXTO_FAIXAS = (200_000, 1_000_000)
CONTEXTO_CAUDA = 256 * 1024
PALETAS = 6
MATIZ_MIN, MATIZ_FAIXA = 45, 271
ID_SOMBRA = 1_000_000       # agentes "sombra" (sub-agentes sem nome) começam aqui

# ferramentas do Claude Code
ISENTAS = frozenset({"Task", "Agent", "AskUserQuestion"})   # não pedem permissão
SUBAGENTE = frozenset({"Task", "Agent"})                     # criam sub-agente
LEITURA = ("Read", "Grep", "Glob", "WebFetch", "WebSearch")
COLEGA = frozenset({"Agent"})                                 # cria colega de equipe
DENTRO_DA_VEZ = frozenset({"Task"})
COMANDO_MAX, TAREFA_MAX = 30, 40


def chave_caminho(p):
    """Mesmo arquivo escrito de jeitos diferentes (C:\\ e c:\\ no Windows) vira a mesma chave."""
    if not p:
        return p
    r = os.path.abspath(p)
    return r.lower() if os.name == "nt" else r


def mesmo_caminho(a, b):
    return chave_caminho(a) == chave_caminho(b)


class Caminhos(set):
    """Conjunto de caminhos que compara pela chave (ver chave_caminho)."""

    def add(self, p):
        super().add(chave_caminho(p))

    def __contains__(self, p):
        return super().__contains__(chave_caminho(p))

    def discard(self, p):
        super().discard(chave_caminho(p))


# ------------------------------------------------------------------ laço de eventos

class Temporizador:
    __slots__ = ("quando", "fn", "args", "intervalo", "cancelado")

    def __init__(self, quando, fn, args, intervalo=None):
        self.quando, self.fn, self.args, self.intervalo, self.cancelado = quando, fn, args, intervalo, False

    def cancelar(self):
        self.cancelado = True


class Laco:
    def __init__(self):
        self.fila = queue.Queue()
        self.agenda = []
        self.seq = itertools.count()
        self.thread = None
        self.parar = False

    def depois(self, seg, fn, *args):
        t = Temporizador(time.monotonic() + seg, fn, args)
        self.chamar(self._agendar, t)
        return t

    def a_cada(self, seg, fn, *args):
        t = Temporizador(time.monotonic() + seg, fn, args, seg)
        self.chamar(self._agendar, t)
        return t

    def chamar(self, fn, *args):
        """Põe na fila (pode ser chamado de qualquer thread)."""
        self.fila.put((fn, args))

    def _agendar(self, t):
        heapq.heappush(self.agenda, (t.quando, next(self.seq), t))

    def _rodar(self, fn, args):
        try:
            fn(*args)
        except Exception as e:  # noqa: BLE001  um erro num agente não derruba o escritório
            print(f"[escritório] erro em {getattr(fn, '__name__', fn)}: {type(e).__name__}: {e}")

    def passo(self, espera=0.0):
        """Roda o que venceu e o que está na fila. Devolve False quando é para parar."""
        agora = time.monotonic()
        while self.agenda and self.agenda[0][0] <= agora:
            _, _, t = heapq.heappop(self.agenda)
            if t.cancelado:
                continue
            self._rodar(t.fn, t.args)
            if t.intervalo and not t.cancelado:
                t.quando = agora + t.intervalo
                self._agendar(t)
        if self.agenda:
            espera = min(espera, max(0.0, self.agenda[0][0] - time.monotonic()))
        try:
            fn, args = self.fila.get(timeout=espera) if espera > 0 else self.fila.get_nowait()
        except queue.Empty:
            return not self.parar
        self._rodar(fn, args)
        while True:
            try:
                fn, args = self.fila.get_nowait()
            except queue.Empty:
                break
            self._rodar(fn, args)
        return not self.parar

    def iniciar(self):
        def rodar():
            while self.passo(0.5):
                pass

        self.thread = threading.Thread(target=rodar, name="escritorio-laco", daemon=True)
        self.thread.start()

    def esperar_fila(self, limite=2.0):
        """Espera a fila esvaziar (para os testes)."""
        feito = threading.Event()
        self.chamar(feito.set)
        return feito.wait(limite)


# ------------------------------------------------------------------ agente

@dataclass(eq=False)
class Agente:
    id: int
    sessao: str
    pasta_projeto: str
    jsonl: str
    externo: bool = True
    deslocamento: int = 0
    sobra: str = ""
    # ferramenta ativa: id -> [status, nome]; dict guarda a ordem de chegada
    ferramentas: dict = field(default_factory=dict)
    # sub-agentes: id da ferramenta-mãe -> {id da sub-ferramenta: nome}
    subferramentas: dict = field(default_factory=dict)
    segundo_plano: dict = field(default_factory=dict)   # ids de Agent em segundo plano (conjunto ordenado)
    esperando: bool = False
    permissao_enviada: bool = False
    teve_ferramentas: bool = False
    pasta_nome: str | None = None
    ultimo_dado: float = 0.0
    linhas: int = 0
    tipos_vistos: set = field(default_factory=set)
    gancho_entregue: bool = False
    so_ganchos: bool = False
    limpeza_pendente: bool = False
    gancho_ferramenta: str | None = None
    gancho_ferramenta_nome: str | None = None
    gancho_colega: bool = False
    contexto: int = 0
    contexto_max: int = CONTEXTO_PADRAO
    viu_principal: bool = False
    equipe: str | None = None
    nome: str | None = None
    equipe_das_tags: bool = False
    lider: bool | None = None
    lider_id: int | None = None
    equipe_tmux: bool | None = None
    spawn_id: str | None = None
    spawns_colega: set = field(default_factory=set)
    paleta: int | None = None
    matiz: int | None = None
    # agentes da Ciello que moram no escritório (residentes.py): não vêm de sessão nem são gravados
    residente: bool = False
    # Task/Agent deste agente que foram para um residente: id da ferramenta -> id do residente
    redirecionados: dict = field(default_factory=dict)

    def status(self, tid):
        return self.ferramentas[tid][0] if tid in self.ferramentas else None

    def nome_ferramenta(self, tid):
        return self.ferramentas[tid][1] if tid in self.ferramentas else None

    def tirar_ferramenta(self, tid):
        self.ferramentas.pop(tid, None)

    def info_equipe(self, **extra):
        return {"type": "agentTeamInfo", "id": self.id, "teamName": self.equipe, "agentName": self.nome,
                "isTeamLead": self.lider, "leadAgentId": self.lider_id, **extra}

    def persistido(self):
        return {"id": self.id, "sessionId": self.sessao, "isExternal": self.externo or None, "jsonlFile": self.jsonl,
                "projectDir": self.pasta_projeto, "directoryName": self.pasta_nome, "teamName": self.equipe,
                "agentName": self.nome, "isTeamLead": self.lider, "leadAgentId": self.lider_id,
                "teamUsesTmux": self.equipe_tmux,
                "backgroundAgentToolIds": list(self.segundo_plano) or None, "palette": self.paleta, "hueShift": self.matiz}


def limpar(msg):
    """undefined do JavaScript some do JSON; aqui None faz o mesmo (menos o layout, que pode ser null de propósito)."""
    return {k: v for k, v in msg.items() if v is not None or k == "layout"}


class Loja:
    """Dona dos agentes. Avisa quem ouve (as telas conectadas) a cada mudança."""

    def __init__(self, laco: Laco, gravar=None):
        self.laco = laco
        self.agentes: dict[int, Agente] = {}
        self.proximo_id = 1
        self.ouvintes = []
        self.gravar_agentes = gravar
        self.qtd_paletas = PALETAS

    def __iter__(self):
        return iter(list(self.agentes.items()))

    def valores(self):
        return list(self.agentes.values())

    def get(self, aid):
        return self.agentes.get(aid)

    def __contains__(self, aid):
        return aid in self.agentes

    def novo_id(self):
        aid = self.proximo_id
        self.proximo_id += 1
        return aid

    def por(self, aid, agente):
        """Guarda o agente; se é novo, a tela fica sabendo na hora (agentCreated), como no original."""
        novo = aid not in self.agentes
        self.agentes[aid] = agente
        if novo:
            a = agente
            self.transmitir({"type": "agentCreated", "id": aid, "directoryName": a.pasta_nome, "isExternal": a.externo or None,
                             "isTeammate": (a.lider_id is not None) or None, "teammateName": a.nome,
                             "parentAgentId": a.lider_id, "teamName": a.equipe, "hooksOnly": a.so_ganchos or None,
                             "palette": a.paleta, "hueShift": a.matiz})

    def tirar(self, aid):
        if self.agentes.pop(aid, None) is None:
            return False
        self.transmitir({"type": "agentClosed", "id": aid})
        return True

    def transmitir(self, msg):
        msg = limpar(msg)
        for ouvinte in list(self.ouvintes):
            ouvinte(msg)

    def gravar(self):
        if self.gravar_agentes:
            self.gravar_agentes([limpar(a.persistido()) for a in self.agentes.values() if not a.spawn_id and not a.residente])

    def escolher_paleta(self, agente):
        """As primeiras N pessoas ganham cada uma um personagem; depois repete com outra cor (matiz ≥ 45°)."""
        if agente.paleta is not None:
            return
        n = self.qtd_paletas
        contagem = [0] * n
        for a in self.agentes.values():
            if a.paleta is not None and a.paleta < n:
                contagem[a.paleta] += 1
        menor = min(contagem)
        agente.paleta = random.choice([i for i, c in enumerate(contagem) if c == menor])
        agente.matiz = MATIZ_MIN + random.randrange(MATIZ_FAIXA) if menor > 0 else 0

    # equipe -------------------------------------------------------
    def colegas_na_mesma_sessao(self, lider_id):
        return [(i, a) for i, a in self if a.lider_id == lider_id and not a.equipe_tmux]

    def promovido(self, lider_id, tid):
        return any(a.lider_id == lider_id and a.spawn_id == tid for a in self.agentes.values())


# ------------------------------------------------------------------ status das ferramentas

def status_ferramenta(nome, entrada=None):
    e = entrada if isinstance(entrada, dict) else {}
    base = lambda p: Path(p.replace("\\", "/")).name if isinstance(p, str) else ""
    if nome == "Read":
        return f"Reading {base(e.get('file_path'))}"
    if nome == "Edit":
        return f"Editing {base(e.get('file_path'))}"
    if nome == "Write":
        return f"Writing {base(e.get('file_path'))}"
    if nome == "Bash":
        cmd = e.get("command") if isinstance(e.get("command"), str) else ""
        return "Running: " + (cmd[:COMANDO_MAX] + "\u2026" if len(cmd) > COMANDO_MAX else cmd)
    if nome == "Glob":
        return "Searching files"
    if nome == "Grep":
        return "Searching code"
    if nome == "WebFetch":
        return "Fetching web content"
    if nome == "WebSearch":
        return "Searching the web"
    if nome in ("Task", "Agent"):
        d = e.get("description") if isinstance(e.get("description"), str) else ""
        return ("Subtask: " + (d[:TAREFA_MAX] + "\u2026" if len(d) > TAREFA_MAX else d)) if d else "Running subtask"
    if nome == "AskUserQuestion":
        return "Waiting for your answer"
    if nome == "EnterPlanMode":
        return "Planning"
    if nome == "NotebookEdit":
        return "Editing notebook"
    if nome == "TeamCreate":
        t = e.get("team_name") if isinstance(e.get("team_name"), str) else ""
        return f"Creating team: {t}" if t else "Creating team"
    if nome == "SendMessage":
        r = e.get("recipient") if isinstance(e.get("recipient"), str) else ""
        return f"-> {r}" if r else "Sending message"
    return f"Using {nome}"


# ------------------------------------------------------------------ temporizadores

class Relogios:
    """Os dois temporizadores por agente do original: "esperando" (fim da vez) e "permissão"."""

    def __init__(self, loja: Loja):
        self.loja, self.laco = loja, loja.laco
        self.espera: dict[int, Temporizador] = {}
        self.permissao: dict[int, Temporizador] = {}
        # quando uma tarefa que foi para um residente acaba sem tool_result (vez nova, Esc): residentes.py liga
        self.ao_soltar = lambda pai, tid: None

    def cancelar_espera(self, aid):
        t = self.espera.pop(aid, None)
        if t:
            t.cancelar()

    def cancelar_permissao(self, aid):
        t = self.permissao.pop(aid, None)
        if t:
            t.cancelar()

    def iniciar_espera(self, aid, seg):
        self.cancelar_espera(aid)

        def venceu():
            self.espera.pop(aid, None)
            a = self.loja.get(aid)
            if a:
                a.esperando = True
            self.loja.transmitir({"type": "agentStatus", "id": aid, "status": "waiting", "awaitingInput": False})

        self.espera[aid] = self.laco.depois(seg, venceu)

    def iniciar_permissao(self, aid):
        self.cancelar_permissao(aid)

        def venceu():
            self.permissao.pop(aid, None)
            a = self.loja.get(aid)
            if not a:
                return
            presa = any((f[1] or "") not in ISENTAS for f in a.ferramentas.values())
            maes = []
            for mae, subs in a.subferramentas.items():
                if any(n not in ISENTAS for n in subs.values()):
                    maes.append(mae)
                    presa = True
            if presa:
                a.permissao_enviada = True
                self.loja.transmitir({"type": "agentToolPermission", "id": aid})
                for mae in maes:
                    rid = a.redirecionados.get(mae)
                    if rid is not None:  # o pedido é do residente que está fazendo a tarefa
                        self.loja.transmitir({"type": "agentToolPermission", "id": rid})
                    else:
                        self.loja.transmitir({"type": "subagentToolPermission", "id": aid, "parentToolId": mae})

        self.permissao[aid] = self.laco.depois(PERMISSAO, venceu)

    def feito_depois(self, msg):
        """Avisa que a ferramenta terminou 300 ms depois (como o original, para a animação não piscar)."""
        self.laco.depois(FERRAMENTA_FEITA, self.loja.transmitir, msg)

    def reenviar_segundo_plano(self, a: Agente):
        for tid in a.segundo_plano:
            if self.loja.promovido(a.id, tid) or tid in a.redirecionados:
                continue
            st = a.status(tid)
            if st:
                self.loja.transmitir({"type": "agentToolStart", "id": a.id, "toolId": tid, "status": st,
                                      "toolName": a.nome_ferramenta(tid), "runInBackground": True,
                                      "isTeammateSpawn": (tid in a.spawns_colega) or None})

    def limpar_atividade(self, a: Agente | None, aid):
        """Nova vez começando: tira as ferramentas (menos os agentes em segundo plano) e marca ativo."""
        if not a:
            return
        for tid in [t for t in a.redirecionados if t not in a.segundo_plano]:
            self.ao_soltar(a, tid)
        if a.segundo_plano:
            for tid in list(a.ferramentas):
                if tid in a.segundo_plano:
                    continue
                a.tirar_ferramenta(tid)
                a.subferramentas.pop(tid, None)
        else:
            a.ferramentas.clear()
            a.subferramentas.clear()
        a.esperando = False
        a.permissao_enviada = False
        self.cancelar_permissao(aid)
        self.loja.transmitir({"type": "agentToolsClear", "id": aid})
        self.reenviar_segundo_plano(a)
        self.loja.transmitir({"type": "agentStatus", "id": aid, "status": "active"})


# ------------------------------------------------------------------ uso de contexto

def tokens_contexto(registro):
    uso = (registro.get("message") or {}).get("usage") if isinstance(registro, dict) else None
    if not isinstance(uso, dict):
        return 0
    soma = sum(v for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
               if isinstance(v := uso.get(k), (int, float)))
    return int(soma) if soma > 0 else 0


def janela_do_modelo(registro):
    import re
    modelo = (registro.get("message") or {}).get("model") if isinstance(registro, dict) else None
    if not modelo or modelo == "<synthetic>":
        return None
    return 200_000 if re.search(r"haiku|claude-[123]|-4-[01]\b", modelo, re.I) else 1_000_000


def alargar(observado, atual):
    janela = max(atual or 0, CONTEXTO_PADRAO)
    for faixa in CONTEXTO_FAIXAS:
        if faixa >= observado:
            return max(janela, faixa)
    maior = CONTEXTO_FAIXAS[-1]
    return max(janela, -(-observado // maior) * maior)


def aplicar_contexto(loja: Loja, a: Agente, tokens, principal, janela):
    if principal:
        a.viu_principal = True
    a.contexto = tokens
    a.contexto_max = alargar(tokens, janela if janela is not None else a.contexto_max)
    loja.transmitir({"type": "agentContextUsage", "id": a.id, "contextTokens": a.contexto, "maxContextTokens": a.contexto_max})


def atualizar_contexto(loja: Loja, a: Agente, registro):
    tokens = tokens_contexto(registro)
    if tokens <= 0:
        return
    lateral = registro.get("isSidechain") is True
    if lateral and a.viu_principal:
        return
    aplicar_contexto(loja, a, tokens, not lateral, janela_do_modelo(registro))


def semear_contexto(loja: Loja, a: Agente):
    """Agente adotado no meio da sessão: lê o fim do arquivo para já mostrar o medidor de contexto."""
    import json
    if not a or a.contexto > 0 or not a.jsonl:
        return
    try:
        tam = os.path.getsize(a.jsonl)
        inicio = max(0, tam - CONTEXTO_CAUDA)
        if tam - inicio <= 0:
            return
        with open(a.jsonl, "rb") as f:
            f.seek(inicio)
            texto = f.read().decode("utf-8", "replace")
        if inicio > 0:
            texto = texto[texto.find("\n") + 1:]
    except OSError:
        return
    lateral = None
    for linha in reversed(texto.split("\n")):
        if not linha:
            continue
        try:
            reg = json.loads(linha)
        except ValueError:
            continue
        tokens = tokens_contexto(reg)
        if tokens <= 0:
            continue
        if reg.get("isSidechain") is True:
            lateral = lateral or (tokens, janela_do_modelo(reg))
            continue
        aplicar_contexto(loja, a, tokens, True, janela_do_modelo(reg))
        return
    if lateral:
        aplicar_contexto(loja, a, lateral[0], False, lateral[1])
