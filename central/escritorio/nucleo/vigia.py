"""Acha e acompanha as sessões do Claude Code: cada sessão vira um agente no escritório.

  - lê o JSONL de cada agente a cada 0,5 s (só o que é novo)
  - a cada 3 s procura sessões novas na pasta do projeto (e em todas, com "ver todas as sessões")
  - a cada 1 s procura colegas de equipe e agentes em segundo plano (subagents/ ao lado da sessão)
  - sub-agente sem nome não vira personagem: o JSONL dele é lido numa "loja sombra" e aparece como as
    ferramentas do sub-personagem ao lado de quem o chamou
  - sem hooks, a cada 30 s tira agentes cujo arquivo sumiu
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from .agentes import (ID_SOMBRA, SUBAGENTE, Agente, Caminhos, Laco, Loja, Relogios, chave_caminho, mesmo_caminho,
                      semear_contexto)
from .transcricao import Leitor

LEITURA_POLL = 0.5
VARREDURA_PROJETO = 1.0
VARREDURA_EXTERNA = 3.0
CHECAGEM_ANTIGOS = 30.0
ATIVO_RECENTE = 120.0         # só adota sessão mexida nos últimos 2 min
DISPENSA = 180.0               # fechou no X: não readota por 3 min
GLOBAL_MIN_BYTES = 3072
GLOBAL_MAX_IDADE = 600.0
MAX_LEITURA = 65536
CABECA_EQUIPE = 16384
SESSAO = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jsonl$", re.I)
PROJETOS = Path.home() / ".claude" / "projects"
EQUIPES = Path.home() / ".claude" / "teams"


def pasta_normalizada(caminho):
    return re.sub(r"[^a-zA-Z0-9-]", "-", str(caminho))


def pasta_de_sessoes(projeto, raiz=None):
    """~/.claude/projects/<caminho do projeto com tudo que não é letra/número trocado por ->."""
    raiz = Path(raiz) if raiz else PROJETOS
    nome = pasta_normalizada(projeto)
    alvo = raiz / nome
    if alvo.exists() or not raiz.exists():
        return alvo
    for c in raiz.iterdir():
        if c.name.lower() == nome.lower():
            return c
    return alvo


def nome_da_pasta(nome_dir):
    partes = nome_dir.lstrip("-").split("-")
    return partes[-1] or nome_dir


def jsonls(pasta):
    try:
        return [os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith(".jsonl")]
    except OSError:
        return []


def cabeca(arq, n=8192):
    try:
        with open(arq, "rb") as f:
            return f.read(n).decode("utf-8", "replace")
    except OSError:
        return None


# ------------------------------------------------------------------ equipe (formato do Claude Code)

def lateral(jsonl):
    """Metadados do agente lançado: <arquivo>.meta.json ao lado do JSONL."""
    try:
        d = json.loads(Path(re.sub(r"\.jsonl$", ".meta.json", jsonl)).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict) or not isinstance(d.get("agentType"), str):
        return None
    texto = lambda k: d[k] if isinstance(d.get(k), str) else None
    return {"agentType": d["agentType"], "toolUseId": texto("toolUseId"), "description": texto("description"), "name": texto("name")}


def meta_equipe(jsonl):
    """{equipe, nome} da sessão, None se não é de equipe, ... (Ellipsis) se ainda não dá para saber."""
    texto = cabeca(jsonl, CABECA_EQUIPE)
    if texto is None:
        return ...
    for linha in texto.split("\n"):
        if not linha.strip():
            continue
        try:
            r = json.loads(linha)
        except ValueError:
            continue
        if isinstance(r.get("teamName"), str):
            return {"equipe": r["teamName"], "nome": r["agentName"] if isinstance(r.get("agentName"), str) else None}
        if r.get("type") in ("user", "assistant"):
            return None
    return ...


def membros_da_equipe(equipe):
    try:
        d = json.loads((EQUIPES / equipe / "config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(d.get("members"), list):
        return None
    return {m["name"] for m in d["members"] if isinstance(m, dict) and isinstance(m.get("name"), str) and m.get("isActive") is not False}


class Dispensas:
    """Arquivos que não devem ser readotados: fechados no X (3 min), trocados por /clear (sempre), os que já
    existiam ao abrir (até mudarem) e os /clear esperando a segunda volta da varredura."""

    def __init__(self):
        self.temporarias, self.permanentes, self.semeados, self.pendentes = {}, set(), {}, {}

    def dispensar(self, p, quando=None):
        self.temporarias[chave_caminho(p)] = quando or time.time()

    def liberar(self, p):
        self.temporarias.pop(chave_caminho(p), None)

    def dispensado(self, p):
        k = chave_caminho(p)
        t = self.temporarias.get(k)
        if t is None:
            return False
        if time.time() - t < DISPENSA:
            return True
        del self.temporarias[k]
        return False

    def para_sempre(self, p):
        self.permanentes.add(chave_caminho(p))

    def permanente(self, p):
        return chave_caminho(p) in self.permanentes

    def semear(self, p, mtime):
        self.semeados[chave_caminho(p)] = mtime

    def semeado(self, p):
        return self.semeados.get(chave_caminho(p))

    def tirar_semente(self, p):
        self.semeados.pop(chave_caminho(p), None)

    def pendente(self, p):
        return chave_caminho(p) in self.pendentes

    def marcar_pendente(self, p):
        self.pendentes[chave_caminho(p)] = time.time()

    def tirar_pendente(self, p):
        self.pendentes.pop(chave_caminho(p), None)


# ------------------------------------------------------------------ leitura dos arquivos

class Pista:
    """Uma loja com seus relógios, seu leitor e a leitura periódica dos arquivos de cada agente."""

    def __init__(self, laco: Laco, loja: Loja):
        self.laco, self.loja = laco, loja
        self.rel = Relogios(loja)
        self.leitor = Leitor(loja, self.rel)
        self.leituras = {}

    def observar(self, aid):
        semear_contexto(self.loja, self.loja.get(aid))
        self.parar(aid)

        def poll():
            if aid not in self.loja:
                self.parar(aid)
                return
            self.ler_novas(aid)

        self.leituras[aid] = self.laco.a_cada(LEITURA_POLL, poll)

    def parar(self, aid):
        t = self.leituras.pop(aid, None)
        if t:
            t.cancelar()

    def ler_novas(self, aid):
        a = self.loja.get(aid)
        if not a:
            return
        try:
            tam = os.path.getsize(a.jsonl)
            if tam <= a.deslocamento:
                return
            with open(a.jsonl, "rb") as f:
                f.seek(a.deslocamento)
                bloco = f.read(min(tam - a.deslocamento, MAX_LEITURA))
        except FileNotFoundError:
            return
        except OSError as e:
            print(f"[escritório] agente {aid}: erro lendo o arquivo: {e}")
            return
        a.deslocamento += len(bloco)
        dados = (a.sobra.encode("utf-8") if isinstance(a.sobra, str) else a.sobra) + bloco
        *linhas, resto = dados.split(b"\n")
        a.sobra = resto
        if any(l.strip() for l in linhas):
            self.rel.cancelar_espera(aid)
            self.rel.cancelar_permissao(aid)
            if a.permissao_enviada and not a.gancho_entregue and not a.lider_id:
                a.permissao_enviada = False
                self.loja.transmitir({"type": "agentToolPermissionClear", "id": aid})
        for l in linhas:
            if l.strip():
                self.leitor.linha(aid, l.decode("utf-8", "replace"))
                if aid not in self.loja:
                    return


class Sombra:
    """Sub-agentes sem nome (lançados em segundo plano): o JSONL deles é lido numa loja à parte e o que acontece lá
    vira subagentToolStart/Done do sub-personagem ao lado do líder. As ferramentas só "terminam" no fim da vez do
    sub-agente, para o boneco digitar a vez inteira em vez de piscar a cada ferramenta."""

    def __init__(self, laco: Laco, principal: Loja):
        self.principal = principal
        self.loja = Loja(laco)
        self.loja.proximo_id = ID_SOMBRA
        self.loja.ouvintes.append(self._traduzir)
        self.pista = Pista(laco, self.loja)
        self.chaves = {}
        self.vivas = {}
        self.residentes = None  # se a tarefa foi para um residente, a atividade aparece nele

    def observando(self, jsonl):
        return any(mesmo_caminho(a.jsonl, jsonl) for a in self.loja.valores())

    def observar(self, lider: Agente, lider_id, jsonl, tid):
        sid = self.loja.novo_id()
        self.loja.por(sid, Agente(id=sid, sessao=lider.sessao, pasta_projeto=lider.pasta_projeto, jsonl=jsonl,
                                  ultimo_dado=time.time(), lider_id=lider_id, spawn_id=tid))
        self.chaves[sid] = (lider_id, tid)
        self.pista.observar(sid)
        self.pista.ler_novas(sid)

    def tirar_por_spawn(self, lider_id, tid):
        for sid, chave in list(self.chaves.items()):
            if chave == (lider_id, tid):
                self._tirar(sid)
                return

    def tirar_do_lider(self, lider_id):
        for sid, chave in list(self.chaves.items()):
            if chave[0] == lider_id:
                self._tirar(sid)

    def _tirar(self, sid):
        self.pista.parar(sid)
        self.pista.rel.cancelar_espera(sid)
        self.pista.rel.cancelar_permissao(sid)
        self.chaves.pop(sid, None)
        self.vivas.pop(sid, None)
        self.loja.tirar(sid)

    def _traduzir(self, msg):
        chave = self.chaves.get(msg.get("id"))
        if not chave:
            return
        lider_id, tid = chave
        tipo = msg["type"]
        lider = self.principal.get(lider_id)
        if lider and tid in lider.redirecionados and self.residentes:
            if tipo == "agentToolStart":
                self.vivas.setdefault(msg["id"], {})[msg["toolId"]] = True
                self.residentes.sub_inicio(lider, tid, msg["toolId"], msg.get("status") or "", msg.get("toolName") or "")
            elif tipo == "agentToolsClear" or (tipo == "agentStatus" and msg.get("status") == "waiting"):
                for t in list(self.vivas.get(msg["id"]) or {}):
                    self.residentes.sub_fim(lider, tid, t)
                self.vivas.pop(msg["id"], None)
            elif tipo == "agentToolPermission":
                self.residentes.permissao(lider, tid)
            return
        if tipo == "agentToolStart":
            self.vivas.setdefault(msg["id"], {})[msg["toolId"]] = True
            self.principal.transmitir({"type": "subagentToolStart", "id": lider_id, "parentToolId": tid,
                                       "toolId": msg["toolId"], "status": msg.get("status")})
        elif tipo == "agentToolsClear" or (tipo == "agentStatus" and msg.get("status") == "waiting"):
            vivas = self.vivas.get(msg["id"])
            for t in list(vivas or {}):
                self.principal.transmitir({"type": "subagentToolDone", "id": lider_id, "parentToolId": tid, "toolId": t})
            if vivas:
                vivas.clear()
        elif tipo == "agentToolPermission":
            self.principal.transmitir({"type": "subagentToolPermission", "id": lider_id, "parentToolId": tid})


# ------------------------------------------------------------------ o vigia

class Vigia:
    def __init__(self, laco: Laco, loja: Loja, raiz_sessoes=None):
        self.laco, self.loja = laco, loja
        self.pista = Pista(laco, loja)
        self.rel, self.leitor = self.pista.rel, self.pista.leitor
        self.sombra = Sombra(laco, loja)
        self.dispensas = Dispensas()
        self.conhecidos = Caminhos()
        self.vistos = Caminhos()          # todo JSONL que já passou por uma varredura (ou existia ao abrir)
        self.colegas_conhecidos = Caminhos()
        self.sem_equipe = set()
        self.pastas = []
        self.raiz_sessoes = Path(raiz_sessoes) if raiz_sessoes else PROJETOS
        self.ganchos_ligados = False
        self.ver_todas = False
        self.global_varrido = False
        self.residentes = None  # residentes.Residentes: colega com nome de agente da casa não vira personagem novo
        self.timers = []
        # ganchos (preenchidos pela sala)
        self.registrar = lambda sessao, aid: None
        self.desregistrar = lambda sessao: None
        self.ao_tirar = lambda aid, agente: None
        self.leitor.ao_detectar_segundo_plano = self.procurar_segundo_plano
        self.leitor.ao_terminar_segundo_plano = self._segundo_plano_terminou
        self.leitor.ao_trocar_equipe = self._equipe_trocou

    # ------------------------------------------------------------ início
    def acompanhar(self, pasta_projeto):
        pasta = str(pasta_projeto)
        for f in jsonls(pasta):
            self.conhecidos.add(f)
            self.vistos.add(f)
            try:
                self.dispensas.semear(f, os.path.getmtime(f))
            except OSError:
                pass
        if not any(mesmo_caminho(p, pasta) for p in self.pastas):
            self.pastas.append(pasta)

    def iniciar(self):
        self.timers = [self.laco.a_cada(VARREDURA_PROJETO, self._varrer_projeto),
                       self.laco.a_cada(VARREDURA_EXTERNA, self._varrer_externas),
                       self.laco.a_cada(CHECAGEM_ANTIGOS, self._tirar_sumidos)]

    def parar(self):
        for t in self.timers:
            t.cancelar()
        for aid in [i for i, _ in self.loja]:
            self.tirar(aid)

    def acompanhada(self, pasta):
        return any(mesmo_caminho(p, pasta) for p in self.pastas)

    # ------------------------------------------------------------ agentes
    def novo_agente(self, **campos):
        aid = self.loja.novo_id()
        a = Agente(id=aid, ultimo_dado=time.time(), **campos)
        return aid, a

    def adotar(self, jsonl, pasta_projeto, pasta_nome=None):
        """Sessão nova vira agente. Arquivo recém-criado é lido do começo; sessão que já vinha rodando, do fim."""
        try:
            st = os.stat(jsonl)
            nascimento = getattr(st, "st_birthtime", None) or (st.st_ctime if os.name == "nt" else None)
            if nascimento:
                novo = time.time() - nascimento <= VARREDURA_EXTERNA * 2
            else:  # Linux não guarda a criação: novo é o arquivo que a varredura ainda não tinha visto
                novo = jsonl not in self.vistos
            deslocamento = 0 if novo else st.st_size
        except OSError:
            deslocamento = 0
        self.vistos.add(jsonl)
        aid, a = self.novo_agente(sessao=Path(jsonl).stem, pasta_projeto=pasta_projeto, jsonl=jsonl,
                                  deslocamento=deslocamento, pasta_nome=pasta_nome)
        self.loja.escolher_paleta(a)
        self.loja.por(aid, a)
        self.loja.gravar()
        self.pista.observar(aid)
        self.pista.ler_novas(aid)
        return a

    def adotar_do_gancho(self, sessao, transcricao, cwd):
        if transcricao:
            if any(mesmo_caminho(a.jsonl, transcricao) for a in self.loja.valores()):
                return None
            if self.dispensas.dispensado(transcricao) or self.dispensas.permanente(transcricao):
                return None
            self.conhecidos.add(transcricao)
            pasta = os.path.dirname(transcricao)
            a = self.adotar(transcricao, pasta, nome_da_pasta(os.path.basename(pasta)))
            a.sessao, a.gancho_entregue = sessao, True
            self.registrar(a.sessao, a.id)
            return a
        aid, a = self.novo_agente(sessao=sessao, pasta_projeto=cwd, jsonl="", gancho_entregue=True, so_ganchos=True,
                                  pasta_nome=os.path.basename(cwd) if cwd else None)
        self.loja.escolher_paleta(a)
        self.loja.por(aid, a)
        self.loja.gravar()
        self.registrar(a.sessao, aid)
        return a

    def tirar(self, aid):
        a = self.loja.get(aid)
        if not a:
            return
        if a.residente:  # agente da casa não sai do escritório: só larga a sessão e volta para a rotina
            return self._soltar_residente(a)
        self.pista.parar(aid)
        self.rel.cancelar_espera(aid)
        self.rel.cancelar_permissao(aid)
        self.ao_tirar(aid, a)
        self.loja.tirar(aid)
        self.loja.gravar()

    def _soltar_residente(self, a: Agente):
        self.pista.parar(a.id)
        self.rel.cancelar_espera(a.id)
        self.rel.cancelar_permissao(a.id)
        if a.sessao:
            self.desregistrar(a.sessao)
        a.jsonl, a.sessao, a.deslocamento, a.sobra = "", "", 0, b""
        a.lider_id = a.equipe = a.equipe_tmux = None
        a.ferramentas.clear()
        a.subferramentas.clear()
        a.esperando, a.permissao_enviada = True, False
        self.loja.transmitir(a.info_equipe())
        self.loja.transmitir({"type": "agentToolsClear", "id": a.id})
        self.loja.transmitir({"type": "agentStatus", "id": a.id, "status": "waiting", "awaitingInput": False})

    def _assumir(self, r: Agente, arq, sessao, lider_id, lider):
        """O colega de equipe com nome de agente da casa: o próprio residente passa a ler a sessão dele."""
        if mesmo_caminho(r.jsonl, arq):
            return
        self.pista.parar(r.id)
        r.jsonl, r.deslocamento, r.sobra, r.linhas = arq, 0, b"", 0
        r.sessao, r.lider_id = sessao, lider_id
        r.equipe = lider.equipe if lider else None
        r.equipe_tmux = lider.equipe_tmux if lider else None
        r.ultimo_dado = time.time()
        self.loja.transmitir(r.info_equipe(teamUsesTmux=r.equipe_tmux))
        if sessao:
            self.registrar(sessao, r.id)
        self.pista.observar(r.id)
        self.pista.ler_novas(r.id)

    def tirar_colega(self, aid, motivo=""):
        a = self.loja.get(aid)
        if not a:
            return
        self.dispensas.dispensar(a.jsonl)
        if not a.spawn_id:
            self.desregistrar(a.sessao)
        self.tirar(aid)
        if a.lider_id is not None:
            lider = self.loja.get(a.lider_id)
            if lider and lider.lider and not any(x.lider_id == a.lider_id for x in self.loja.valores()):
                lider.lider = None
                self.loja.transmitir(lider.info_equipe())
                self.loja.gravar()

    def tirar_colegas(self, lider_id):
        for aid, a in self.loja:
            if a.lider_id == lider_id:
                self.dispensas.dispensar(a.jsonl)
                if not a.spawn_id:
                    self.desregistrar(a.sessao)
                self.tirar(aid)

    def fechar(self, aid):
        """Fechado no X da tela: some e não volta por 3 minutos."""
        a = self.loja.get(aid)
        if not a:
            return
        self.tirar_colegas(aid)
        self.sombra.tirar_do_lider(aid)
        self.dispensas.dispensar(a.jsonl)
        self.tirar(aid)

    def trocar_arquivo(self, aid, novo):
        """/clear ou /resume: o mesmo personagem passa a ler a sessão nova."""
        a = self.loja.get(aid)
        if not a:
            return
        self.pista.parar(aid)
        self.rel.cancelar_espera(aid)
        self.rel.cancelar_permissao(aid)
        self.rel.limpar_atividade(a, aid)
        self.dispensas.para_sempre(a.jsonl)
        a.sessao, a.jsonl, a.deslocamento, a.sobra = Path(novo).stem, novo, 0, b""
        self.loja.gravar()
        self.pista.observar(aid)
        self.pista.ler_novas(aid)

    # ------------------------------------------------------------ varreduras
    def _varrer_projeto(self):
        self.procurar_todos_os_colegas()
        for aid in self._colegas_dispensados():
            self.tirar_colega(aid, "equipe")

    def _varrer_externas(self):
        for pasta in self.pastas:
            self.varrer_pasta(pasta)
        if self.ver_todas:
            self._varrer_todas()

    def varrer_pasta(self, pasta):
        agora = time.time()
        if any(a.limpeza_pendente and mesmo_caminho(a.pasta_projeto, pasta) for a in self.loja.valores()):
            return
        arquivos = jsonls(pasta)
        try:
            self._varrer_arquivos(pasta, arquivos, agora)
        finally:
            for arq in arquivos:
                self.vistos.add(arq)

    def _varrer_arquivos(self, pasta, arquivos, agora):
        for arq in arquivos:
            semente = self.dispensas.semeado(arq)
            if semente is not None:
                try:
                    if os.path.getmtime(arq) > semente:
                        self.dispensas.tirar_semente(arq)
                        self.conhecidos.discard(arq)
                except OSError:
                    pass
                continue
            if arq in self.conhecidos or self.dispensas.permanente(arq) or self.dispensas.dispensado(arq):
                continue
            if any(mesmo_caminho(a.jsonl, arq) for a in self.loja.valores()):
                continue
            meta = meta_equipe(arq)
            if meta and meta is not ... and self.residentes:
                rid = self.residentes.por_nome(meta.get("nome"))
                if rid is not None:  # sessão de colega com nome de agente da casa: o residente assume, sem clone
                    self.conhecidos.add(arq)
                    lider = next((x for x in self.loja.valores() if x.equipe == meta["equipe"] and x.lider_id is None
                                  and not x.residente), None)
                    self._assumir(self.loja.get(rid), arq, Path(arq).stem, lider.id if lider else None, lider)
                    continue
            meta = meta if self.ganchos_ligados else None
            if meta and meta is not ... and meta.get("nome"):
                if any(a.equipe == meta["equipe"] and a.lider_id is None for a in self.loja.valores()):
                    continue
            try:
                if agora - os.path.getmtime(arq) > ATIVO_RECENTE:
                    continue
            except OSError:
                continue
            texto = cabeca(arq)
            if texto is None:
                continue
            if "/clear</command-name>" in texto:
                if not self.dispensas.pendente(arq):
                    self.dispensas.marcar_pendente(arq)
                    continue
                self.dispensas.tirar_pendente(arq)
            self.conhecidos.add(arq)
            self.adotar(arq, pasta)

    def _varrer_todas(self):
        agora = time.time()
        try:
            pastas = [str(p) for p in self.raiz_sessoes.iterdir() if p.is_dir()]
        except OSError:
            return
        for pasta in pastas:
            if self.acompanhada(pasta):
                continue
            arquivos = jsonls(pasta)
            if not self.global_varrido:  # na primeira volta, o que já existia não é sessão nova
                for arq in arquivos:
                    self.vistos.add(arq)
            for arq in arquivos:
                if arq in self.conhecidos or any(mesmo_caminho(a.jsonl, arq) for a in self.loja.valores()):
                    continue
                try:
                    st = os.stat(arq)
                except OSError:
                    continue
                if st.st_size < GLOBAL_MIN_BYTES or agora - st.st_mtime > GLOBAL_MAX_IDADE:
                    continue
                self.conhecidos.add(arq)
                self.adotar(arq, pasta, nome_da_pasta(os.path.basename(pasta)))
            for arq in arquivos:
                self.vistos.add(arq)
        self.global_varrido = True

    def _tirar_sumidos(self):
        if self.ganchos_ligados:
            return  # com hooks, o SessionEnd cuida disso
        for aid, a in self:
            if a.externo and a.jsonl and not os.path.exists(a.jsonl):
                self.conhecidos.discard(a.jsonl)
                self.tirar(aid)

    def __iter__(self):
        return iter(self.loja)

    # ------------------------------------------------------------ colegas e segundo plano
    def _spawns_vivos(self, lider: Agente):
        ids = dict(lider.segundo_plano)
        for tid, (_, nome) in lider.ferramentas.items():
            if nome in SUBAGENTE:
                ids[tid] = True
        return ids

    def descobrir(self, pasta_projeto, sessao_lider, equipe=None):
        achados = []
        sub = os.path.join(pasta_projeto, sessao_lider, "subagents")
        try:
            nomes = os.listdir(sub)
        except OSError:
            nomes = []
        for n in nomes:
            if n.endswith(".jsonl"):
                caminho = os.path.join(sub, n)
                m = lateral(caminho)
                if m:
                    achados.append({"jsonl": caminho, "colega": m["agentType"], "toolUseId": m["toolUseId"], "name": m["name"]})
        if equipe:
            try:
                topo = os.listdir(pasta_projeto)
            except OSError:
                return achados
            for n in topo:
                if not SESSAO.match(n):
                    continue
                caminho = os.path.join(pasta_projeto, n)
                if caminho in self.sem_equipe or mesmo_caminho(caminho, os.path.join(pasta_projeto, f"{sessao_lider}.jsonl")):
                    continue
                m = meta_equipe(caminho)
                if m is None:
                    self.sem_equipe.add(caminho)
                    continue
                if m is ... or m["equipe"] != equipe or not m["nome"]:
                    continue
                achados.append({"jsonl": caminho, "colega": m["nome"], "sessao": n[:-6]})
        return achados

    def procurar_colegas(self, pasta_projeto, sessao, lider_id):
        lider = self.loja.get(lider_id)
        vivos = self._spawns_vivos(lider) if lider else {}
        for e in self.descobrir(pasta_projeto, sessao, lider.equipe if lider else None):
            arq = e["jsonl"]
            if e.get("toolUseId") and e["toolUseId"] in vivos:
                continue
            if arq in self.colegas_conhecidos:
                continue
            if self.sombra.observando(arq) or any(mesmo_caminho(a.jsonl, arq) for a in self.loja.valores()):
                continue
            self.colegas_conhecidos.add(arq)
            rid = self.residentes.por_nome(e["colega"]) if self.residentes else None
            if rid is not None and self.loja.get(rid):
                self._assumir(self.loja.get(rid), arq, e.get("sessao") or sessao, lider_id, lider)
                continue
            existente = next((a for a in self.loja.valores() if a.lider_id == lider_id and a.nome == e["colega"]), None)
            if existente:
                self.pista.parar(existente.id)
                existente.jsonl, existente.deslocamento, existente.sobra = arq, 0, b""
                existente.ultimo_dado, existente.linhas, existente.esperando = time.time(), 0, False
                existente.equipe_tmux = lider.equipe_tmux if lider else None
                if e.get("sessao") and existente.sessao != e["sessao"]:
                    existente.sessao = e["sessao"]
                    self.registrar(e["sessao"], existente.id)
                self.pista.observar(existente.id)
                self.pista.ler_novas(existente.id)
                continue
            aid, a = self.novo_agente(sessao=e.get("sessao") or sessao, pasta_projeto=pasta_projeto, jsonl=arq,
                                      nome=e["colega"], lider_id=lider_id, equipe=lider.equipe if lider else None,
                                      equipe_tmux=lider.equipe_tmux if lider else None)
            if lider and lider.paleta is not None:
                a.paleta, a.matiz = lider.paleta, lider.matiz or 0
            else:
                self.loja.escolher_paleta(a)
            self.loja.por(aid, a)
            self.loja.gravar()
            if e.get("sessao"):
                self.registrar(e["sessao"], aid)
            self.pista.observar(aid)
            self.pista.ler_novas(aid)

    def procurar_segundo_plano(self, lider_id):
        """Agent lançado em segundo plano: com nome vira colega (personagem próprio), sem nome fica na sombra."""
        lider = self.loja.get(lider_id)
        if not lider or not lider.sessao or not lider.pasta_projeto:
            return
        vivos = self._spawns_vivos(lider)
        if not vivos:
            return
        for e in self.descobrir(lider.pasta_projeto, lider.sessao):
            tid = e.get("toolUseId")
            if not tid or tid not in vivos:
                continue
            if self.sombra.observando(e["jsonl"]) or any(mesmo_caminho(a.jsonl, e["jsonl"]) for a in self.loja.valores()):
                continue
            rid = self.residentes.por_nome(e.get("name")) if self.residentes else None
            if rid is not None and tid not in lider.redirecionados:  # spawn com nome de agente da casa: é ele
                chave = next(k for k, v in self.residentes.ids.items() if v == rid)
                desc = (lider.status(tid) or "").removeprefix("Subtask:").strip()
                self.residentes.comecar(lider, tid, {"subagent_type": chave, "description": desc})
            if not e.get("name") or tid not in lider.segundo_plano or tid in lider.redirecionados:
                self.sombra.observar(lider, lider_id, e["jsonl"], tid)
                continue
            aid, a = self.novo_agente(sessao=lider.sessao, pasta_projeto=lider.pasta_projeto, jsonl=e["jsonl"],
                                      nome=e["name"], lider_id=lider_id, spawn_id=tid)
            if lider.paleta is not None:
                a.paleta, a.matiz = lider.paleta, lider.matiz or 0
            else:
                self.loja.escolher_paleta(a)
            self.loja.por(aid, a)
            if not lider.lider:
                lider.lider = True
                self.loja.transmitir(lider.info_equipe(isTeamLead=True))
            self.loja.gravar()
            self.loja.transmitir({"type": "subagentClear", "id": lider_id, "parentToolId": tid})
            self.pista.observar(aid)
            self.pista.ler_novas(aid)

    def procurar_todos_os_colegas(self):
        for aid, a in self:
            if a.lider_id is not None or not a.sessao or not a.pasta_projeto:
                continue
            self.procurar_segundo_plano(aid)
            if a.equipe:
                self.procurar_colegas(a.pasta_projeto, a.sessao, aid)

    def _colegas_dispensados(self):
        por_equipe = {}
        for aid, a in self:
            if a.lider_id is None or a.equipe_tmux or not a.equipe:
                continue
            por_equipe.setdefault(a.equipe, []).append((aid, a))
        sair = []
        for equipe, membros in por_equipe.items():
            nomes = membros_da_equipe(equipe)
            for aid, a in membros:
                if nomes is None or (a.nome and a.nome not in nomes):
                    sair.append(aid)
        return sair

    def _segundo_plano_terminou(self, lider_id, tid):
        for aid, a in self:
            if a.lider_id == lider_id and a.spawn_id == tid:
                self.tirar_colega(aid, "segundo plano terminou")
                break
        self.sombra.tirar_por_spawn(lider_id, tid)

    def _equipe_trocou(self, lider_id, anterior):
        for aid, a in self:
            if a.lider_id == lider_id and a.equipe == anterior:
                self.tirar_colega(aid, "troca de equipe")

    # ------------------------------------------------------------ restaurar
    def restaurar(self, persistidos):
        maior = 0
        for p in persistidos:
            if not p.get("isExternal") or (p.get("leadAgentId") is not None and not p.get("teamName")):
                continue
            arq = p.get("jsonlFile") or ""
            if not arq or not os.path.exists(arq):
                continue
            aid = p["id"]
            if aid in self.loja or any(mesmo_caminho(a.jsonl, arq) for a in self.loja.valores()):
                # já acompanhada (pelo id, ou adotada de novo com outro id): não cria a mesma sessão duas vezes
                self.conhecidos.add(arq)
                maior = max(maior, aid)
                continue
            if self.residentes and self.residentes.por_nome(p.get("agentName")) is not None:
                continue  # colega antigo com nome de agente da casa: o residente cuida se a sessão voltar
            a = Agente(id=aid, sessao=p.get("sessionId") or Path(arq).stem, pasta_projeto=p.get("projectDir") or "",
                       jsonl=arq, ultimo_dado=time.time(), pasta_nome=p.get("directoryName") or p.get("folderName"),
                       equipe=p.get("teamName"), nome=p.get("agentName"), lider=p.get("isTeamLead"),
                       lider_id=p.get("leadAgentId"), equipe_tmux=p.get("teamUsesTmux"),
                       paleta=p.get("palette"), matiz=p.get("hueShift"))
            a.segundo_plano = {t: True for t in p.get("backgroundAgentToolIds") or []}
            self.loja.escolher_paleta(a)
            self.loja.por(aid, a)
            self.conhecidos.add(arq)
            try:
                a.deslocamento = os.path.getsize(arq)
                self.pista.observar(aid)
            except OSError:
                pass
            self.registrar(a.sessao, aid)
            maior = max(maior, aid)
        if maior >= self.loja.proximo_id:
            self.loja.proximo_id = maior + 1
        self.loja.gravar()
