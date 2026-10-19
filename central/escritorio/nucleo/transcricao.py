"""Lê cada linha do JSONL de uma sessão do Claude Code e traduz em movimento no escritório.

Regras iguais às do original: ferramenta começou/terminou, sub-agente (Task/Agent) com as ferramentas dele,
agente em segundo plano que só termina no "queue-operation", fim da vez pelo turn_duration, equipe (teamName),
e os temporizadores de "esperando" e "permissão" quando os hooks não estão entregando.
"""
from __future__ import annotations

import json
import re
import time

from .agentes import (COLEGA, ISENTAS, SUBAGENTE, TEXTO_PARADO, Agente, Loja, Relogios, atualizar_contexto,
                      status_ferramenta)

PADRAO_COLEGA = re.compile(r"agent_id:\s*([^\s@]+)@(\S+)")
ASSINCRONO = "Async agent launched successfully."
TIPOS_IGNORADOS = {"file-history-snapshot", "system", "queue-operation"}


def texto_resultado(conteudo):
    if isinstance(conteudo, str):
        return conteudo
    if isinstance(conteudo, list):
        return "\n".join(i["text"] if isinstance(i, dict) and isinstance(i.get("text"), str) else "" for i in conteudo)
    return ""


def resultado_assincrono(bloco):
    c = bloco.get("content")
    if isinstance(c, list):
        return any(isinstance(i, dict) and isinstance(i.get("text"), str) and i["text"].startswith(ASSINCRONO) for i in c)
    return isinstance(c, str) and c.startswith(ASSINCRONO)


def colega_do_resultado(nome_ferramenta, conteudo):
    if nome_ferramenta not in COLEGA:
        return None
    m = PADRAO_COLEGA.search(texto_resultado(conteudo))
    return {"colega": m.group(1), "equipe": m.group(2)} if m else None


def e_spawn_colega(nome, entrada):
    return nome == "Agent" and isinstance(entrada, dict) and entrada.get("run_in_background") is True


class Leitor:
    def __init__(self, loja: Loja, relogios: Relogios):
        self.loja, self.rel = loja, relogios
        # avisos para o vigia (preenchidos por quem monta o escritório)
        self.ao_detectar_segundo_plano = lambda lider_id: None
        self.ao_terminar_segundo_plano = lambda lider_id, tid: None
        self.ao_trocar_equipe = lambda lider_id, equipe_anterior: None

    # ------------------------------------------------------------------ equipe
    def ligar_equipe(self, a: Agente):
        if not a.equipe:
            return
        time_ = [x for x in self.loja.valores() if x.equipe == a.equipe]
        lider = next((x for x in time_ if not x.nome), None) or next((x for x in time_ if x.lider), None)
        if not lider:
            return
        for x in time_:
            if x.id == lider.id:
                x.lider, x.lider_id = True, None
            else:
                x.lider, x.lider_id = False, lider.id

    # ------------------------------------------------------------------ linha
    def linha(self, aid, texto):
        a = self.loja.get(aid)
        if not a:
            return
        a.ultimo_dado = time.time()
        a.linhas += 1
        try:
            reg = json.loads(texto)
        except ValueError:
            return
        if not isinstance(reg, dict):
            return
        try:
            self._registro(aid, a, reg)
        except (KeyError, TypeError, AttributeError, ValueError):
            pass  # linha fora do formato esperado: ignora, como o original

    def _registro(self, aid, a: Agente, reg):
        loja, rel = self.loja, self.rel
        equipe = reg.get("teamName")
        if isinstance(equipe, str) and equipe != a.equipe:
            a.equipe, a.equipe_das_tags = equipe, True
            a.nome = reg["agentName"] if isinstance(reg.get("agentName"), str) else None
            a.lider = a.lider_id = None
            self.ligar_equipe(a)
            loja.transmitir(a.info_equipe())

        atualizar_contexto(loja, a, reg)
        conteudo = (reg.get("message") or {}).get("content") if isinstance(reg.get("message"), dict) else None
        if conteudo is None:
            conteudo = reg.get("content")
        tipo = reg.get("type")

        if tipo == "assistant" and isinstance(conteudo, list):
            blocos = [b for b in conteudo if isinstance(b, dict)]
            if any(b.get("type") == "tool_use" for b in blocos):
                rel.cancelar_espera(aid)
                a.esperando, a.teve_ferramentas = False, True
                loja.transmitir({"type": "agentStatus", "id": aid, "status": "active"})
                nao_isenta = False
                for b in blocos:
                    if b.get("type") != "tool_use" or not b.get("id"):
                        continue
                    nome = b.get("name") or ""
                    entrada = b.get("input") if isinstance(b.get("input"), dict) else {}
                    st = status_ferramenta(nome, entrada)
                    a.ferramentas[b["id"]] = [st, nome]
                    if nome not in ISENTAS:
                        nao_isenta = True
                    if a.equipe and e_spawn_colega(nome, entrada) and not a.equipe_tmux:
                        a.equipe_tmux = True
                        loja.transmitir(a.info_equipe(teamUsesTmux=True))
                        for cid, colega in loja:
                            if cid != aid and colega.lider_id == aid:
                                colega.equipe_tmux = True
                                loja.transmitir(colega.info_equipe(teamUsesTmux=True))
                    sub = nome in SUBAGENTE
                    colega_spawn = sub and isinstance(entrada.get("name"), str) and len(entrada["name"]) > 0
                    if colega_spawn:
                        a.spawns_colega.add(b["id"])
                    via_jsonl = a.gancho_entregue and bool(loja.colegas_na_mesma_sessao(aid))
                    if not a.gancho_entregue or via_jsonl or sub:
                        loja.transmitir({"type": "agentToolStart", "id": aid, "toolId": b["id"], "status": st,
                                         "toolName": nome, "permissionActive": a.permissao_enviada,
                                         "runInBackground": sub and entrada.get("run_in_background") is True,
                                         "isTeammateSpawn": colega_spawn or None})
                if nao_isenta and not a.gancho_entregue and not a.lider_id:
                    rel.iniciar_permissao(aid)
            elif any(b.get("type") == "text" for b in blocos) and not a.teve_ferramentas:
                if not a.gancho_entregue:
                    rel.iniciar_espera(aid, TEXTO_PARADO)
        elif tipo == "assistant" and isinstance(conteudo, str):
            if not a.teve_ferramentas and not a.gancho_entregue:
                rel.iniciar_espera(aid, TEXTO_PARADO)
        elif tipo == "progress":
            self._progresso(aid, a, reg)
        elif tipo == "user":
            if isinstance(conteudo, list):
                blocos = [b for b in conteudo if isinstance(b, dict)]
                if any(b.get("type") == "tool_result" for b in blocos):
                    for b in blocos:
                        if b.get("type") == "tool_result" and b.get("tool_use_id"):
                            self._resultado(aid, a, b)
                    if not a.ferramentas:
                        a.teve_ferramentas = False
                else:
                    self._nova_vez(aid, a)
            elif isinstance(conteudo, str) and conteudo.strip():
                self._nova_vez(aid, a)
        elif tipo == "queue-operation" and reg.get("operation") == "enqueue":
            m = re.search(r"<tool-use-id>(.*?)</tool-use-id>", reg.get("content") or "") if isinstance(reg.get("content"), str) else None
            if m and m.group(1) in a.segundo_plano:
                tid = m.group(1)
                a.segundo_plano.pop(tid, None)
                a.subferramentas.pop(tid, None)
                loja.transmitir({"type": "subagentClear", "id": aid, "parentToolId": tid})
                a.tirar_ferramenta(tid)
                self.ao_terminar_segundo_plano(aid, tid)
                if not a.gancho_entregue:
                    rel.feito_depois({"type": "agentToolDone", "id": aid, "toolId": tid})
        elif tipo == "system" and reg.get("subtype") == "turn_duration":
            self._fim_da_vez(aid, a)
        elif tipo and tipo not in a.tipos_vistos and tipo not in TIPOS_IGNORADOS:
            a.tipos_vistos.add(tipo)

    def _nova_vez(self, aid, a):
        self.rel.cancelar_espera(aid)
        self.rel.limpar_atividade(a, aid)
        a.teve_ferramentas = False

    def _resultado(self, aid, a: Agente, b):
        loja, rel = self.loja, self.rel
        tid = b["tool_use_id"]
        nome = a.nome_ferramenta(tid)
        colega = colega_do_resultado(nome, b.get("content")) if nome else None
        if colega and not a.equipe_das_tags and not a.lider_id and a.equipe != colega["equipe"]:
            if a.equipe:
                self.ao_trocar_equipe(aid, a.equipe)
            a.equipe, a.lider = colega["equipe"], True
            self.ligar_equipe(a)
            loja.transmitir(a.info_equipe())
        if not colega and nome in SUBAGENTE and resultado_assincrono(b):
            a.segundo_plano[tid] = True
            st = a.status(tid)
            if st:
                loja.transmitir({"type": "agentToolStart", "id": aid, "toolId": tid, "status": st, "toolName": nome,
                                 "runInBackground": True, "isTeammateSpawn": (tid in a.spawns_colega) or None})
            self.ao_detectar_segundo_plano(aid)
            return
        if nome in SUBAGENTE:
            a.subferramentas.pop(tid, None)
            loja.transmitir({"type": "subagentClear", "id": aid, "parentToolId": tid})
            self.ao_terminar_segundo_plano(aid, tid)
        a.tirar_ferramenta(tid)
        via_jsonl = a.gancho_entregue and bool(loja.colegas_na_mesma_sessao(aid))
        if not a.gancho_entregue or via_jsonl or nome in ("Task", "Agent"):
            rel.feito_depois({"type": "agentToolDone", "id": aid, "toolId": tid})

    def _fim_da_vez(self, aid, a: Agente):
        loja, rel = self.loja, self.rel
        rel.cancelar_espera(aid)
        rel.cancelar_permissao(aid)
        if len(a.ferramentas) > len(a.segundo_plano):
            for tid in list(a.ferramentas):
                if tid in a.segundo_plano:
                    continue
                nome = a.nome_ferramenta(tid)
                a.tirar_ferramenta(tid)
                if nome in SUBAGENTE:
                    a.subferramentas.pop(tid, None)
                    self.ao_terminar_segundo_plano(aid, tid)
            if not a.gancho_entregue:
                loja.transmitir({"type": "agentToolsClear", "id": aid})
            rel.reenviar_segundo_plano(a)
        elif a.ferramentas and not a.segundo_plano:
            a.ferramentas.clear()
            a.subferramentas.clear()
            if not a.gancho_entregue:
                loja.transmitir({"type": "agentToolsClear", "id": aid})
        a.esperando, a.permissao_enviada, a.teve_ferramentas = True, False, False
        if not a.gancho_entregue:
            loja.transmitir({"type": "agentStatus", "id": aid, "status": "waiting", "awaitingInput": False})

    def _progresso(self, aid, a: Agente, reg):
        mae = reg.get("parentToolUseID")
        dados = reg.get("data")
        if not mae or not isinstance(dados, dict):
            return
        if dados.get("type") in ("bash_progress", "mcp_progress"):
            if mae in a.ferramentas and not a.gancho_entregue and not a.lider_id:
                self.rel.iniciar_permissao(aid)
            return
        if a.nome_ferramenta(mae) not in SUBAGENTE:
            return
        msg = dados.get("message")
        if not isinstance(msg, dict):
            return
        interno = msg.get("message") if isinstance(msg.get("message"), dict) else {}
        conteudo = interno.get("content")
        if not isinstance(conteudo, list):
            return
        if msg.get("type") == "assistant":
            nao_isenta = False
            for b in conteudo:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id"):
                    nome = b.get("name") or ""
                    st = status_ferramenta(nome, b.get("input") or {})
                    a.subferramentas.setdefault(mae, {})[b["id"]] = nome
                    if nome not in ISENTAS:
                        nao_isenta = True
                    self.loja.transmitir({"type": "subagentToolStart", "id": aid, "parentToolId": mae, "toolId": b["id"], "status": st})
            if nao_isenta and not a.gancho_entregue:
                self.rel.iniciar_permissao(aid)
        elif msg.get("type") == "user":
            for b in conteudo:
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id"):
                    a.subferramentas.get(mae, {}).pop(b["tool_use_id"], None)
                    self.rel.feito_depois({"type": "subagentToolDone", "id": aid, "parentToolId": mae, "toolId": b["tool_use_id"]})
            presa = any(n not in ISENTAS for subs in a.subferramentas.values() for n in subs.values())
            if presa and not a.gancho_entregue:
                self.rel.iniciar_permissao(aid)
