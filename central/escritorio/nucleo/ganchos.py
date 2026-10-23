"""Hooks do Claude Code: o modo instantâneo do escritório.

Com os hooks instalados, o Claude Code avisa na hora quando uma sessão começa/termina, quando uma ferramenta
começa, quando pede permissão e quando termina a vez. O JSONL continua dando os detalhes (nome da ferramenta,
sub-agentes); os hooks só substituem os palpites por tempo (7 s de permissão, 5 s de texto parado).

Instalar mexe em ~/.claude/settings.json, então só acontece com o "sim" do Mateus na tela do escritório.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

from .agentes import SUBAGENTE, DENTRO_DA_VEZ, COLEGA, Agente, Loja, status_ferramenta
from .vigia import Vigia, meta_equipe

BUFFER = 5.0                  # evento de sessão ainda desconhecida espera até 5 s pelo agente
FIM_DE_SESSAO = 2.0           # /clear e /resume: espera o SessionStart que vem logo depois
EVENTOS = ("SessionStart", "SessionEnd", "Stop", "PermissionRequest", "Notification", "PreToolUse", "PostToolUse",
           "PostToolUseFailure", "SubagentStart", "SubagentStop", "TeammateIdle", "TaskCompleted")
CONFIG_CLAUDE = Path.home() / ".claude" / "settings.json"
SCRIPT = Path(__file__).resolve().parent.parent / "gancho.py"
MARCA = "gancho.py"                      # nosso comando termina com .../central/escritorio/gancho.py
DO_PIXEL_AGENTS = ("claude-hook.js", "pixel-agents-hook.js")  # os do pixel-agents original, que substituímos
COPIA = ".ciello.backup"

TITULO_CONSENTIMENTO = "Uma última coisa: os hooks!"
TEXTO_CONSENTIMENTO = "\n\n".join([
    f"Para os agentes se mexerem na hora, o escritório adiciona hooks para {len(EVENTOS)} eventos do Claude Code em "
    f"~/.claude/settings.json. Suas configurações continuam lá, e uma cópia de segurança é guardada uma vez como "
    f"settings.json{COPIA}. Hooks antigos do pixel-agents, se houver, são trocados pelos da Ciello.",
    "O Claude Code vai mandar esses eventos (inclusive nomes e entradas das ferramentas) para o Ciello OS neste PC. "
    "Nada sai do computador: o servidor só escuta em 127.0.0.1.",
    "Dá para tirar os hooks quando quiser em Configurações → Detecção instantânea (hooks).",
])


# ------------------------------------------------------------------ instalação em ~/.claude/settings.json

def _comando():
    py = Path(sys.executable)
    if os.name == "nt" and py.name.lower() == "python.exe" and (py.parent / "pythonw.exe").exists():
        py = py.parent / "pythonw.exe"  # sem janela de console piscando a cada evento
    return f'"{py}" "{SCRIPT}"'


def _nosso(cmd):
    return isinstance(cmd, str) and MARCA in cmd.replace("\\", "/") and "central/escritorio" in cmd.replace("\\", "/")


def _do_pixel_agents(cmd):
    return isinstance(cmd, str) and any(n in cmd for n in DO_PIXEL_AGENTS)


def _ler_config(caminho):
    if not caminho.exists():
        return {}
    dados = json.loads(caminho.read_text(encoding="utf-8") or "{}")
    if not isinstance(dados, dict):
        raise ValueError("settings.json não é um objeto")
    return dados


def _gravar_config(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    copia = caminho.with_name(caminho.name + COPIA)
    if caminho.exists() and not copia.exists():
        shutil.copy2(caminho, copia)
    tmp = caminho.with_name(caminho.name + ".ciello-tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, caminho)


def _sem(entradas, descartar):
    """Tira os comandos que `descartar` reconhece; mantém hooks de outras ferramentas que dividam a entrada."""
    saida = []
    for e in entradas if isinstance(entradas, list) else []:
        if not isinstance(e, dict) or not isinstance(e.get("hooks"), list):
            saida.append(e)
            continue
        hooks = [h for h in e["hooks"] if not (isinstance(h, dict) and descartar(h.get("command")))]
        if hooks:
            saida.append({**e, "hooks": hooks})
    return saida


def instalados(caminho=None):
    try:
        dados = _ler_config(caminho or CONFIG_CLAUDE)
    except (OSError, ValueError):
        return False
    for entradas in (dados.get("hooks") or {}).values():
        for e in entradas if isinstance(entradas, list) else []:
            for h in (e.get("hooks") or []) if isinstance(e, dict) else []:
                if isinstance(h, dict) and _nosso(h.get("command")):
                    return True
    return False


def instalar(caminho=None):
    caminho = caminho or CONFIG_CLAUDE
    dados = _ler_config(caminho)
    hooks = dados.get("hooks") if isinstance(dados.get("hooks"), dict) else {}
    for evento in list(hooks):
        hooks[evento] = _sem(hooks[evento], lambda c: _nosso(c) or _do_pixel_agents(c))
        if not hooks[evento]:
            del hooks[evento]
    for evento in EVENTOS:
        hooks.setdefault(evento, []).append({"matcher": "", "hooks": [{"type": "command", "command": _comando(), "timeout": 5}]})
    dados["hooks"] = hooks
    _gravar_config(caminho, dados)


def desinstalar(caminho=None):
    caminho = caminho or CONFIG_CLAUDE
    dados = _ler_config(caminho)
    hooks = dados.get("hooks")
    if not isinstance(hooks, dict):
        return
    for evento in list(hooks):
        hooks[evento] = _sem(hooks[evento], _nosso)
        if not hooks[evento]:
            del hooks[evento]
    if not hooks:
        del dados["hooks"]
    _gravar_config(caminho, dados)


# ------------------------------------------------------------------ eventos

def normalizar(bruto):
    nome, sessao = bruto.get("hook_event_name"), bruto.get("session_id")
    if not isinstance(nome, str) or not isinstance(sessao, str):
        return None
    texto = lambda k: bruto[k] if isinstance(bruto.get(k), str) else None
    if nome == "PreToolUse":
        entrada = bruto.get("tool_input") if isinstance(bruto.get("tool_input"), dict) else {}
        return {"tipo": "inicio", "ferramenta": texto("tool_name") or "", "entrada": entrada}
    if nome in ("PostToolUse", "PostToolUseFailure"):
        return {"tipo": "fim"}
    if nome == "Stop":
        return {"tipo": "fim_da_vez"}
    if nome == "SubagentStart":
        return {"tipo": "sub_inicio"}
    if nome == "SubagentStop":
        return {"tipo": "sub_fim"}
    if nome == "PermissionRequest":
        return {"tipo": "permissao"}
    if nome == "Notification":
        n = texto("notification_type")
        if n == "permission_prompt":
            return {"tipo": "permissao"}
        if n == "idle_prompt":
            return {"tipo": "fim_da_vez", "aguardando": True}
        return None
    if nome == "SessionStart":
        return {"tipo": "sessao_inicio", "origem": texto("source"), "transcricao": texto("transcript_path"), "cwd": texto("cwd")}
    if nome == "SessionEnd":
        return {"tipo": "sessao_fim", "motivo": texto("reason")}
    if nome == "TeammateIdle":
        return {"tipo": "colega_fim", "motivo": "idle"}
    if nome == "TaskCompleted":
        return {"tipo": "colega_fim", "motivo": "completed"}
    return None


def nome_do_colega(evento):
    for k in ("teammate_name", "agent_type"):
        if isinstance(evento.get(k), str):
            return evento[k]
    return None


class Ganchos:
    """Encaminha cada evento para o agente da sessão (session_id). Sessão desconhecida fica pendente até um evento
    confirmar que é de verdade (a extensão do VS Code abre e fecha sessões vazias)."""

    def __init__(self, vigia: Vigia):
        self.vigia, self.loja, self.rel = vigia, vigia.loja, vigia.rel
        self.sessoes = {}       # session_id -> id do agente
        self.pendentes = {}     # session_id -> {transcricao, cwd}
        self.buffer = []        # (quando, evento)
        vigia.registrar = self.registrar
        vigia.desregistrar = self.desregistrar
        self.SUBAGENTE = SUBAGENTE | COLEGA | DENTRO_DA_VEZ
        self.residentes = None

    # ---------------------------------------------------------- roteamento
    def registrar(self, sessao, aid):
        self.sessoes[sessao] = aid
        agora = time.time()
        guardados = [e for t, e in self.buffer if e.get("session_id") == sessao and agora - t <= BUFFER]
        self.buffer = [(t, e) for t, e in self.buffer if e.get("session_id") != sessao and agora - t <= BUFFER]
        for e in guardados:
            self.evento(e)

    def desregistrar(self, sessao):
        self.sessoes.pop(sessao, None)

    def _acompanhada(self, transcricao, cwd):
        if self.vigia.ver_todas:
            return True
        pasta = os.path.dirname(transcricao) if transcricao else cwd
        return bool(pasta) and any(os.path.abspath(a.pasta_projeto).lower() == os.path.abspath(pasta).lower()
                                   for a in self.loja.valores())

    def evento(self, bruto):
        n = normalizar(bruto)
        if not n:
            return
        sessao = bruto["session_id"]
        if n["tipo"] == "sessao_inicio":
            return self._sessao_inicio(sessao, n)
        if n["tipo"] == "sessao_fim" and sessao in self.pendentes:
            del self.pendentes[sessao]
            return
        pendente = self.pendentes.pop(sessao, None)
        if pendente:
            self._sessao_externa(sessao, pendente["transcricao"], pendente["cwd"])
            return self.evento(bruto)
        aid = self.sessoes.get(sessao)
        if aid is None:
            for i, a in self.loja:
                if a.sessao == sessao:
                    self.registrar(a.sessao, i)
                    aid = i
                    break
        if aid is None:
            agora = time.time()
            self.buffer = [(t, e) for t, e in self.buffer if agora - t <= BUFFER]
            esperando = any(e.get("session_id") == sessao for _, e in self.buffer)
            sem_registro = any(a.sessao and a.sessao not in self.sessoes for a in self.loja.valores())
            if esperando or sem_registro:
                self.buffer.append((agora, bruto))
            return
        a = self.loja.get(aid)
        if not a:
            return
        a.gancho_entregue = True
        tipo = n["tipo"]
        if tipo == "sessao_fim":
            self._sessao_fim(a, aid, n.get("motivo"))
        elif tipo == "inicio":
            self._inicio(a, aid, n["ferramenta"], n["entrada"])
        elif tipo == "fim":
            self._fim(a, aid)
        elif tipo == "sub_inicio":
            self._sub_inicio(bruto, a, aid)
        elif tipo == "sub_fim":
            self._sub_fim(a, aid)
        elif tipo == "permissao":
            self._permissao(a, aid)
        elif tipo == "fim_da_vez":
            self.esperando(a, aid, n.get("aguardando") is True)
        elif tipo == "colega_fim":
            self._colega_fim(bruto, a, aid, n["motivo"] == "completed")

    # ---------------------------------------------------------- sessões
    def _sessao_inicio(self, sessao, n):
        if sessao in self.sessoes:
            a = self.loja.get(self.sessoes[sessao])
            if a:
                a.gancho_entregue = True
            return
        for i, a in self.loja:
            if a.sessao == sessao:
                self.registrar(a.sessao, i)
                a.gancho_entregue = True
                return
        transcricao, cwd = n.get("transcricao"), n.get("cwd")
        if n.get("origem") in ("clear", "resume"):
            pasta = os.path.dirname(transcricao) if transcricao else cwd
            if pasta:
                for i, a in self.loja:
                    if a.limpeza_pendente and os.path.abspath(a.pasta_projeto).lower() == os.path.abspath(pasta).lower():
                        a.limpeza_pendente = False
                        self.desregistrar(a.sessao)
                        self.registrar(sessao, i)
                        if transcricao:
                            self.vigia.conhecidos.add(transcricao)
                            self.vigia.trocar_arquivo(i, transcricao)
                        a.sessao = sessao
                        self.registrar(sessao, i)
                        return
        if transcricao or cwd:
            if n.get("origem") == "resume" and transcricao:
                self.vigia.dispensas.liberar(transcricao)
                self.vigia.dispensas.tirar_semente(transcricao)
                self.vigia.conhecidos.discard(transcricao)
            self.pendentes[sessao] = {"transcricao": transcricao, "cwd": cwd or ""}

    def _sessao_externa(self, sessao, transcricao, cwd):
        pasta = os.path.dirname(transcricao) if transcricao else cwd
        if transcricao:
            meta = meta_equipe(transcricao)
            if meta and meta is not ... and meta.get("nome"):
                for lid, lider in self.loja:
                    if lider.equipe != meta["equipe"] or lider.lider_id is not None:
                        continue
                    self.vigia.procurar_colegas(lider.pasta_projeto, lider.sessao, lid)
                    break
                if any(os.path.abspath(a.jsonl) == os.path.abspath(transcricao) for a in self.loja.valores()):
                    return
        if not self.vigia.acompanhada(pasta) and not self.vigia.ver_todas:
            return
        self.vigia.adotar_do_gancho(sessao, transcricao, cwd)

    def _sessao_fim(self, a: Agente, aid, motivo):
        if motivo in ("clear", "resume"):
            a.limpeza_pendente = True
            self.esperando(a, aid)

            def sem_continuacao():
                if a.limpeza_pendente:
                    a.limpeza_pendente = False
                    self.encerrar(aid)

            self.loja.laco.depois(FIM_DE_SESSAO, sem_continuacao)
        else:
            self.esperando(a, aid)
            self.encerrar(aid)

    def encerrar(self, aid):
        a = self.loja.get(aid)
        if not a:
            return
        self.vigia.dispensas.tirar_semente(a.jsonl)
        self.vigia.dispensas.dispensar(a.jsonl)
        self.vigia.tirar_colegas(aid)
        self.vigia.sombra.tirar_do_lider(aid)
        if a.externo:
            self.desregistrar(a.sessao)
            self.vigia.tirar(aid)

    # ---------------------------------------------------------- ferramentas
    def _inicio(self, a: Agente, aid, ferramenta, entrada):
        tid = f"hook-{int(time.time() * 1000)}"
        a.gancho_ferramenta, a.gancho_ferramenta_nome = tid, ferramenta
        a.gancho_colega = ferramenta == "Agent" and entrada.get("run_in_background") is True
        if self.loja.colegas_na_mesma_sessao(aid):
            return
        self.rel.cancelar_espera(aid)
        a.esperando, a.permissao_enviada, a.teve_ferramentas = False, False, True
        if ferramenta not in ("Task", "Agent"):
            self.loja.transmitir({"type": "agentToolStart", "id": aid, "toolId": tid,
                                  "status": status_ferramenta(ferramenta, entrada), "toolName": ferramenta})
        self.loja.transmitir({"type": "agentStatus", "id": aid, "status": "active"})

    def _fim(self, a: Agente, aid):
        if a.gancho_ferramenta:
            if not self.loja.colegas_na_mesma_sessao(aid):
                self.loja.transmitir({"type": "agentToolDone", "id": aid, "toolId": a.gancho_ferramenta})
            a.gancho_ferramenta = a.gancho_ferramenta_nome = None

    def _sub_inicio(self, bruto, a: Agente, aid):
        tipo_agente = nome_do_colega(bruto) or "unknown"
        if a.gancho_colega and a.equipe:
            self.vigia.procurar_colegas(a.pasta_projeto, bruto["session_id"], aid)
            return
        mae = next((tid for tid, (_, nome) in a.ferramentas.items() if nome in self.SUBAGENTE), None)
        if not mae or mae in a.redirecionados:  # residente: o JSONL do subagente mostra o trabalho nele
            return
        sub_id = f"hook-sub-{tipo_agente}-{int(time.time() * 1000)}"
        a.subferramentas.setdefault(mae, {})[sub_id] = tipo_agente
        self.loja.transmitir({"type": "subagentToolStart", "id": aid, "parentToolId": mae, "toolId": sub_id,
                              "status": f"Subtask: {tipo_agente}"})

    def _sub_fim(self, a: Agente, aid):
        colegas = self.loja.colegas_na_mesma_sessao(aid)
        if colegas:
            for i, c in colegas:
                self.esperando(c, i)
            return
        mae = next((tid for tid, (_, nome) in a.ferramentas.items() if nome in self.SUBAGENTE and tid in a.subferramentas), None)
        if not mae or mae in a.redirecionados:
            return
        a.subferramentas.pop(mae, None)
        self.loja.transmitir({"type": "subagentClear", "id": aid, "parentToolId": mae})

    def _permissao(self, a: Agente, aid):
        colegas = self.loja.colegas_na_mesma_sessao(aid)
        if colegas:
            for i, c in colegas:
                self.rel.cancelar_permissao(i)
                c.permissao_enviada = True
                self.loja.transmitir({"type": "agentToolPermission", "id": i})
            return
        self.rel.cancelar_permissao(aid)
        a.permissao_enviada = True
        self.loja.transmitir({"type": "agentToolPermission", "id": aid})
        for mae in a.subferramentas:
            if not (self.residentes and self.residentes.permissao(a, mae)):
                self.loja.transmitir({"type": "subagentToolPermission", "id": aid, "parentToolId": mae})

    def _colega_fim(self, bruto, a: Agente, aid, tarefa_concluida):
        nome = nome_do_colega(bruto)
        colegas = self.loja.colegas_na_mesma_sessao(aid)
        if not colegas:
            if not tarefa_concluida:
                self.esperando(a, aid)
            return
        alvo = [(i, c) for i, c in colegas if nome and c.nome == nome][:1] or colegas
        for i, c in alvo:
            self.esperando(c, i)

    def esperando(self, a: Agente, aid, aguardando=False):
        """Fim da vez: limpa as ferramentas (menos as de segundo plano) e mostra o agente parado."""
        self.rel.cancelar_espera(aid)
        self.rel.cancelar_permissao(aid)
        for tid in list(a.ferramentas):
            if tid in a.segundo_plano:
                continue
            nome = a.nome_ferramenta(tid)
            a.tirar_ferramenta(tid)
            if tid in a.redirecionados and self.residentes:
                self.residentes.terminar(a, tid)
            if nome in self.SUBAGENTE:
                a.subferramentas.pop(tid, None)
                self.vigia.leitor.ao_terminar_segundo_plano(aid, tid)
        self.loja.transmitir({"type": "agentToolsClear", "id": aid})
        self.rel.reenviar_segundo_plano(a)
        a.esperando, a.permissao_enviada, a.teve_ferramentas = True, False, False
        a.gancho_ferramenta = None
        self.loja.transmitir({"type": "agentStatus", "id": aid, "status": "waiting", "awaitingInput": aguardando})
