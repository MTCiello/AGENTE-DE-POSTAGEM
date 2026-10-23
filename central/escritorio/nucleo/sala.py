"""A sala: junta ativos, vigia e hooks, e conversa com cada tela do escritório pelo WebSocket.

A ordem do aperto de mão (webviewReady) é a do original: acesso, capacidades, ativos, preferências, hooks, áreas,
agentes, layout e, por fim, o que cada agente está fazendo agora.
"""
from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
from pathlib import Path

from . import ganchos as G
from . import persistencia as P
from .agentes import LEITURA, PALETAS, SUBAGENTE, Laco, Loja, limpar
from .ativos import Ativos
from .ganchos import Ganchos
from .residentes import Residentes
from .vigia import Vigia, pasta_de_sessoes

VERSAO = "1.5.0"
MATIZ_MAX = 360


class Sala:
    def __init__(self, raiz_build: Path, projeto: Path, porta: int, raiz_sessoes=None):
        self.ativos = Ativos(raiz_build)
        self.laco = Laco()
        self.loja = Loja(self.laco, P.gravar_agentes)
        self.loja.qtd_paletas = self.ativos.qtd_paletas or PALETAS
        self.vigia = Vigia(self.laco, self.loja, raiz_sessoes)
        self.ganchos = Ganchos(self.vigia)
        self.projeto, self.porta = projeto, porta
        # os agentes da Ciello moram no escritório e recebem as tarefas que o Claude Code passa a eles
        self.residentes = Residentes(self.loja, self.vigia.rel)
        self.residentes.carregar(projeto)
        self.vigia.leitor.residentes = self.vigia.sombra.residentes = self.ganchos.residentes = self.residentes
        self.vigia.residentes = self.residentes
        self.token_gancho = secrets.token_urlsafe(24)

    # ---------------------------------------------------------- ciclo de vida
    def iniciar(self):
        cfg = P.config()
        self.vigia.ganchos_ligados = cfg["hooks"] is True and G.instalados()
        self.vigia.ver_todas = bool(cfg["preferencias"]["watchAllSessions"])
        self._anotar_servidor()
        pasta = pasta_de_sessoes(self.projeto, self.vigia.raiz_sessoes)
        # volta com as sessões acompanhadas antes de começar a procurar novas (senão a mesma sessão ganhava 2 ids)
        self.vigia.restaurar(P.estado()["agentes"])
        self.vigia.acompanhar(pasta)
        self.vigia.iniciar()
        self.laco.iniciar()
        return pasta

    def _anotar_servidor(self):
        """O script do hook lê daqui para onde mandar o evento (só este PC lê: fica na pasta do usuário)."""
        arq = P.CASA / "servidor.json"
        P.CASA.mkdir(parents=True, exist_ok=True)
        arq.write_text(json.dumps({"porta": self.porta, "token": self.token_gancho, "pid": os.getpid()}), encoding="utf-8")
        try:
            os.chmod(arq, 0o600)
        except OSError:
            pass

    # ---------------------------------------------------------- telas conectadas
    def conectar(self, conexao, privilegiada: bool):
        """Atende uma tela até ela fechar (roda na thread da conexão)."""
        def ouvir(msg):
            if not conexao.enviar(msg):
                self.laco.chamar(self._desligar, ouvir)

        self.laco.chamar(self.loja.ouvintes.append, ouvir)
        try:
            while (texto := conexao.receber()) is not None:
                try:
                    msg = json.loads(texto)
                except ValueError:
                    continue
                if isinstance(msg, dict) and msg.get("type"):
                    self.laco.chamar(self.mensagem, msg, conexao, privilegiada)
        finally:
            self.laco.chamar(self._desligar, ouvir)

    def _desligar(self, ouvir):
        if ouvir in self.loja.ouvintes:
            self.loja.ouvintes.remove(ouvir)

    def gancho(self, evento: dict):
        """Evento vindo do script do hook (thread HTTP)."""
        if isinstance(evento, dict) and evento.get("session_id") and evento.get("hook_event_name"):
            self.laco.chamar(self.ganchos.evento, evento)

    # ---------------------------------------------------------- mensagens da tela
    def mensagem(self, msg, conexao, privilegiada):
        enviar = lambda m: conexao.enviar(limpar(m))
        tipo = msg.get("type")
        if tipo == "webviewReady":
            return self.pronta(enviar, privilegiada)
        if not privilegiada:
            return self._recusar(tipo, enviar)
        if tipo == "closeAgent":
            if not getattr(self.loja.get(msg.get("id")), "residente", False):  # os da casa não saem
                self.vigia.fechar(msg.get("id"))
        elif tipo == "requestDiagnostics":
            enviar({"type": "agentDiagnostics", "agents": self._diagnostico()})
        elif tipo == "saveLayout" and isinstance(msg.get("layout"), dict):
            P.gravar_layout(msg["layout"])
        elif tipo == "saveAgentSeats" and isinstance(msg.get("seats"), dict):
            for chave, meta in msg["seats"].items():
                a = self.loja.get(int(chave)) if str(chave).isdigit() else None
                if not a or not isinstance(meta, dict):
                    continue
                p, h = meta.get("palette"), meta.get("hueShift")
                if isinstance(p, int) and not isinstance(p, bool) and 0 <= p < self.loja.qtd_paletas:
                    a.paleta = p
                if isinstance(h, int) and not isinstance(h, bool) and 0 <= h <= MATIZ_MAX:
                    a.matiz = h
            P.gravar_lugares(msg["seats"])
        elif tipo in ("setSoundEnabled", "setAlwaysShowLabels", "setGhostHeadlessAgents", "setShowAreas"):
            P.definir_preferencia({"setSoundEnabled": "soundEnabled", "setAlwaysShowLabels": "alwaysShowLabels",
                                   "setGhostHeadlessAgents": "ghostHeadlessAgents", "setShowAreas": "showAreas"}[tipo],
                                  msg.get("enabled"))
        elif tipo == "setLastSeenVersion":
            P.definir_preferencia("lastSeenVersion", msg.get("version"))
        elif tipo == "setWatchAllSessions":
            P.definir_preferencia("watchAllSessions", bool(msg.get("enabled")))
            self.vigia.ver_todas = bool(msg.get("enabled"))
        elif tipo == "setHooksInfoShown":
            P.definir_preferencia("hooksInfoShown", True)
        elif tipo == "setBypassPermissions" and isinstance(msg.get("enabled"), bool):
            P.definir_preferencia("bypassPermissions", msg["enabled"])
            self.loja.transmitir({"type": "bypassPermissionsUpdated", "enabled": msg["enabled"]})
        elif tipo == "setHooksEnabled":
            self._hooks(bool(msg.get("enabled")), enviar)
        elif tipo == "hooksConsentResponse":
            escolha = msg.get("choice")
            if escolha == "install":
                self._hooks(True, enviar)
            elif escolha == "never":
                self._hooks(False, enviar)
            else:  # "agora não": pergunta de novo na próxima vez
                enviar({"type": "hooksStatus", "providerId": "claude", "installed": G.instalados()})
        elif tipo == "saveAreaMappings" and isinstance(msg.get("mappings"), dict):
            c = P.config()
            c["areas"] = msg["mappings"]
            P.gravar_config(c)
        elif tipo in ("addExternalAssetDirectory", "removeExternalAssetDirectory"):
            enviar({"type": "externalAssetDirectoriesUpdated", "dirs": P.config()["pastasDeAtivos"]})
        elif tipo == "launchAgent":
            self.abrir_claude()
        # focusAgent: quem abre a janela do agente é a área de trabalho do Ciello OS

    def abrir_claude(self):
        """+ Agente: abre o Claude Code numa janela de console nova, na pasta do assistente. A sessão nova aparece
        no escritório sozinha (o vigia adota). Com "pular permissões" ligado, abre com --dangerously-skip-permissions."""
        args = ["claude"] + (["--dangerously-skip-permissions"] if P.preferencia("bypassPermissions") else [])
        if os.name != "nt":
            print(f"[escritório] + Agente: abra um terminal em {self.projeto} e rode: {' '.join(args)}")
            return
        if not shutil.which("claude"):
            args = ["echo", "Claude Code não encontrado neste PC. Para instalar, veja claude.com/claude-code"]
        subprocess.Popen(["cmd.exe", "/k", *args], cwd=self.projeto, creationflags=subprocess.CREATE_NEW_CONSOLE)

    def _areas(self, cfg):
        """Áreas atribuídas. A área inicial de cada agente entra uma vez só; depois vale o que você mudar no editor
        (inclusive tirar alguém de uma área)."""
        vistos = set(cfg.get("areasVistas") or [])
        novos = {k: v for k, v in self.residentes.areas().items() if k not in vistos}
        if novos:
            cfg["areas"] = {**novos, **cfg["areas"]}
            cfg["areasVistas"] = sorted(vistos | set(novos))
            P.gravar_config(cfg)
        return cfg["areas"]

    def _hooks(self, ligar, enviar):
        try:
            if ligar:
                G.instalar()
            elif G.instalados():
                G.desinstalar()
        except (OSError, ValueError) as e:
            print(f"[escritório] não deu para {'instalar' if ligar else 'tirar'} os hooks: {e}")
        instalado = G.instalados()
        c = P.config()
        c["hooks"] = ligar if instalado == ligar else c["hooks"]
        P.gravar_config(c)
        self.vigia.ganchos_ligados = ligar and instalado
        enviar({"type": "hooksStatus", "providerId": "claude", "installed": instalado})

    def _recusar(self, tipo, enviar):
        if tipo == "setHooksEnabled":
            enviar({"type": "hooksStatus", "providerId": "claude", "installed": G.instalados()})
        elif tipo in ("setSoundEnabled", "setAlwaysShowLabels", "setGhostHeadlessAgents", "setWatchAllSessions",
                      "setShowAreas", "setBypassPermissions", "setShowHostDirectories"):
            enviar(self._preferencias())
        elif tipo == "saveAreaMappings":
            enviar({"type": "areaMappingsLoaded", "mappings": P.config()["areas"]})

    def _preferencias(self):
        cfg = P.config()
        p = cfg["preferencias"]
        return {"type": "settingsLoaded", "soundEnabled": p["soundEnabled"], "lastSeenVersion": p["lastSeenVersion"],
                "extensionVersion": VERSAO, "watchAllSessions": p["watchAllSessions"],
                "alwaysShowLabels": p["alwaysShowLabels"], "ghostHeadlessAgents": p["ghostHeadlessAgents"],
                "hooksEnabled": cfg["hooks"] is not False, "hooksInfoShown": p["hooksInfoShown"],
                "externalAssetDirectories": cfg["pastasDeAtivos"], "showAreas": p["showAreas"],
                "bypassPermissions": p["bypassPermissions"], "showHostDirectories": p["showHostDirectories"]}

    def pronta(self, enviar, privilegiada):
        enviar({"type": "officeAccess", "readOnly": not privilegiada})
        enviar({"type": "providerCapabilities", "readingTools": list(LEITURA), "subagentToolNames": sorted(SUBAGENTE, key=["Task", "Agent"].index)})
        for m in self.ativos.mensagens():
            enviar(m)
        layout = P.ler_layout() or self.ativos.layout_padrao  # antes das áreas: um layout novo refaz as áreas e os lugares
        cfg = P.config()
        prefs = self._preferencias()
        enviar(prefs)
        instalado = G.instalados()
        enviar({"type": "areaMappingsLoaded", "mappings": self._areas(cfg)})
        self.vigia.ver_todas = prefs["watchAllSessions"]
        self.vigia.ganchos_ligados = cfg["hooks"] is True and instalado
        self.vigia.restaurar(P.estado()["agentes"])
        lugares = P.estado()["lugares"]
        fixos = (layout or {}).get("lugaresFixos") or {}  # a poltrona do Gerente já nasce dele (gerar_layout.py)
        ids, meta, nomes, externos = [], {}, {}, {}
        for aid, a in self.loja:
            ids.append(aid)
            if a.pasta_nome:
                nomes[aid] = a.pasta_nome
            if a.externo:
                externos[aid] = True
            lugar = (lugares.get(str(aid)) or {}).get("seatId") or (fixos.get(a.pasta_nome) if a.residente else None)
            meta[aid] = limpar({"palette": a.paleta, "hueShift": a.matiz, "seatId": lugar})
        enviar({"type": "existingAgents", "agents": ids, "agentMeta": meta, "directoryNames": nomes, "externalAgents": externos})
        enviar({"type": "layoutLoaded", "layout": layout})
        self._reenviar_atividade(enviar)
        # o original manda o estado dos hooks depois (é assíncrono lá); a tela trata em qualquer ordem
        enviar({"type": "hooksStatus", "providerId": "claude", "installed": instalado})
        if not instalado and cfg["hooks"] is None and privilegiada:
            enviar({"type": "hooksConsentRequest", "providerId": "claude", "headline": G.TITULO_CONSENTIMENTO,
                    "disclosure": G.TEXTO_CONSENTIMENTO})

    def _reenviar_atividade(self, enviar):
        for aid, a in self.loja:
            if a.equipe or a.nome or a.lider:
                enviar(a.info_equipe(teamUsesTmux=a.equipe_tmux))
            for tid, (st, nome) in list(a.ferramentas.items()):
                if tid in a.segundo_plano or tid in a.redirecionados:
                    continue
                enviar({"type": "agentToolStart", "id": aid, "toolId": tid, "status": st, "toolName": nome or ""})
            for tid in a.segundo_plano:
                if self.loja.promovido(aid, tid) or not a.status(tid) or tid in a.redirecionados:
                    continue
                enviar({"type": "agentToolStart", "id": aid, "toolId": tid, "status": a.status(tid),
                        "toolName": a.nome_ferramenta(tid), "runInBackground": True,
                        "isTeammateSpawn": (tid in a.spawns_colega) or None})
            if a.esperando:
                # residente parado é a rotina dele, não "acabou agora": sem visto nem som ao abrir a tela
                enviar({"type": "agentStatus", "id": aid, "status": "waiting", "silencioso": True if a.residente else None})
            if a.contexto > 0:
                enviar({"type": "agentContextUsage", "id": aid, "contextTokens": a.contexto, "maxContextTokens": a.contexto_max})

    def _diagnostico(self):
        saida = []
        for a in self.loja.valores():
            try:
                tam, existe = os.path.getsize(a.jsonl), True
            except OSError:
                tam, existe = 0, False
            saida.append({"id": a.id, "projectDir": a.pasta_projeto, "projectDirExists": os.path.exists(a.pasta_projeto),
                          "jsonlFile": a.jsonl, "jsonlExists": existe, "fileSize": tam, "fileOffset": a.deslocamento,
                          "lastDataAt": int(a.ultimo_dado * 1000), "linesProcessed": a.linhas})
        return saida
