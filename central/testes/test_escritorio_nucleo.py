"""python -m unittest discover central/testes  (núcleo do escritório: central/escritorio/nucleo)"""
import heapq
import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "escritorio"))
from nucleo import ganchos as G  # noqa: E402
from nucleo import png, websocket  # noqa: E402
from nucleo.agentes import Laco, Loja  # noqa: E402
from nucleo.ativos import Ativos  # noqa: E402
from nucleo.vigia import Vigia, pasta_de_sessoes  # noqa: E402

TELA = Path(__file__).resolve().parent.parent / "escritorio" / "web" / "escritorio"


def vencer(laco: Laco):
    """Faz todos os temporizadores agendados vencerem agora (sem esperar 7 s de verdade)."""
    laco.passo(0)
    for _, _, t in laco.agenda:
        t.quando = 0
    laco.agenda = [(0, s, t) for _, s, t in laco.agenda]
    heapq.heapify(laco.agenda)
    laco.passo(0)


class Montagem(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.laco = Laco()
        self.loja = Loja(self.laco)
        self.msgs = []
        self.loja.ouvintes.append(self.msgs.append)
        self.vigia = Vigia(self.laco, self.loja, self.dir)
        self.projeto = self.dir / "-projeto"
        self.projeto.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def tipos(self):
        return [m["type"] for m in self.msgs]

    def sessao(self, nome="aaaaaaaa-1111-2222-3333-444444444444"):
        return self.projeto / f"{nome}.jsonl"

    def escrever(self, arq, *registros):
        with open(arq, "a", encoding="utf-8") as f:
            for r in registros:
                f.write(json.dumps(r) + "\n")

    def ler(self, aid=1):
        self.vigia.pista.ler_novas(aid)
        self.laco.passo(0)


class TesteTranscricao(Montagem):
    def adotar(self):
        self.vigia.acompanhar(self.projeto)
        arq = self.sessao()
        self.escrever(arq, {"type": "user", "message": {"content": "oi"}})
        self.vigia.varrer_pasta(str(self.projeto))  # arquivo novo (não estava na semente): lido do começo
        return arq

    def test_sessao_nova_vira_agente_e_ferramenta_comeca_e_termina(self):
        arq = self.adotar()
        self.assertEqual(self.msgs[0]["type"], "agentCreated")
        self.assertIn(self.msgs[0]["palette"], range(6))
        self.escrever(arq, {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "C:\\pasta\\roteiro.md"}}]}})
        self.ler()
        inicio = next(m for m in self.msgs if m["type"] == "agentToolStart")
        self.assertEqual((inicio["toolId"], inicio["status"], inicio["toolName"]), ("t1", "Reading roteiro.md", "Read"))
        self.escrever(arq, {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1"}]}},
                      {"type": "system", "subtype": "turn_duration"})
        self.ler()
        vencer(self.laco)
        self.assertIn({"type": "agentToolDone", "id": 1, "toolId": "t1"}, self.msgs)
        self.assertIn({"type": "agentStatus", "id": 1, "status": "waiting", "awaitingInput": False}, self.msgs)

    def test_ferramenta_parada_vira_pedido_de_permissao(self):
        arq = self.adotar()
        self.escrever(arq, {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "b1", "name": "Bash", "input": {"command": "python central/sdr.py abordar --top 15 --enviar"}}]}})
        self.ler()
        st = next(m for m in self.msgs if m["type"] == "agentToolStart")["status"]
        self.assertEqual(st, "Running: python central/sdr.py abordar \u2026")  # 30 caracteres + reticências
        vencer(self.laco)
        self.assertIn({"type": "agentToolPermission", "id": 1}, self.msgs)

    def test_subagente_com_ferramentas_e_fim(self):
        arq = self.adotar()
        self.escrever(arq, {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t2", "name": "Task", "input": {"description": "pesquisador-mercado: tendências"}}]}},
            {"type": "progress", "parentToolUseID": "t2", "data": {"message": {"type": "assistant", "message": {
                "content": [{"type": "tool_use", "id": "s1", "name": "WebSearch", "input": {}}]}}}})
        self.ler()
        self.assertIn({"type": "subagentToolStart", "id": 1, "parentToolId": "t2", "toolId": "s1", "status": "Searching the web"}, self.msgs)
        self.escrever(arq, {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t2"}]}})
        self.ler()
        self.assertIn({"type": "subagentClear", "id": 1, "parentToolId": "t2"}, self.msgs)

    def test_agente_em_segundo_plano_so_termina_no_queue_operation(self):
        arq = self.adotar()
        self.escrever(arq, {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "g1", "name": "Agent", "input": {"description": "roteirista"}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "g1",
                                                      "content": [{"type": "text", "text": "Async agent launched successfully. id=x"}]}]}},
            {"type": "system", "subtype": "turn_duration"})
        self.ler()
        vencer(self.laco)
        self.assertNotIn({"type": "agentToolDone", "id": 1, "toolId": "g1"}, self.msgs)
        refeito = [m for m in self.msgs if m["type"] == "agentToolStart" and m.get("runInBackground")]
        self.assertTrue(refeito)
        self.escrever(arq, {"type": "queue-operation", "operation": "enqueue", "content": "<tool-use-id>g1</tool-use-id>"})
        self.ler()
        vencer(self.laco)
        self.assertIn({"type": "agentToolDone", "id": 1, "toolId": "g1"}, self.msgs)

    def test_contexto_e_janela_do_modelo(self):
        arq = self.adotar()
        self.escrever(arq, {"type": "assistant", "message": {"model": "claude-haiku-4-5", "content": "ok",
                                                               "usage": {"input_tokens": 100, "cache_read_input_tokens": 1000}}})
        self.ler()
        uso = next(m for m in self.msgs if m["type"] == "agentContextUsage")
        self.assertEqual((uso["contextTokens"], uso["maxContextTokens"]), (1100, 200_000))

    def test_restaurar_nao_duplica_sessao_ja_adotada_com_outro_id(self):
        arq = self.adotar()
        self.loja.proximo_id = 50
        self.vigia.restaurar([{"id": 7, "isExternal": True, "jsonlFile": str(arq), "sessionId": "x", "projectDir": str(self.projeto)}])
        self.assertEqual([a.id for a in self.loja.valores()], [1])

    def test_sessao_antiga_nao_e_adotada_e_fechada_nao_volta(self):
        arq = self.adotar()
        self.vigia.fechar(1)
        self.assertIn({"type": "agentClosed", "id": 1}, self.msgs)
        self.vigia.conhecidos.discard(arq)
        self.vigia.varrer_pasta(str(self.projeto))
        self.assertEqual(self.tipos().count("agentCreated"), 1)  # dispensado por 3 minutos
        velho = self.sessao("bbbbbbbb-1111-2222-3333-444444444444")
        self.escrever(velho, {"type": "user", "message": {"content": "oi"}})
        os.utime(velho, (time.time() - 600, time.time() - 600))
        self.vigia.varrer_pasta(str(self.projeto))
        self.assertEqual(self.tipos().count("agentCreated"), 1)


class TesteResidentes(Montagem):
    def setUp(self):
        super().setUp()
        from nucleo.residentes import ID_BASE, Residentes
        agentes = self.dir / "raiz" / ".claude" / "agents"
        agentes.mkdir(parents=True)
        for nome in ("sdr", "closer"):
            (agentes / f"{nome}.md").write_text(f"---\nname: {nome}\ndescription: x\n---\ncorpo\n", encoding="utf-8")
        self.res = Residentes(self.loja, self.vigia.rel)
        self.res.carregar(self.dir / "raiz")
        self.vigia.leitor.residentes = self.vigia.sombra.residentes = self.vigia.residentes = self.res
        self.sdr = ID_BASE + 1  # closer, sdr em ordem alfabética
        self.msgs.clear()

    def test_residente_assume_a_tarefa_e_volta_para_a_rotina(self):
        self.assertEqual(self.loja.get(self.sdr).nome, "SDR")
        self.assertEqual(self.loja.get(self.sdr).pasta_nome, "SDR")
        self.assertEqual(self.res.areas()["SDR"], ["Vendas"])
        self.vigia.acompanhar(self.projeto)
        arq = self.sessao()
        self.escrever(arq, {"type": "user", "message": {"content": "oi"}})
        self.vigia.varrer_pasta(str(self.projeto))
        coord = max(i for i, a in self.loja if not a.residente)
        self.escrever(arq, {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": "Task", "input": {"description": "follow-ups do dia", "subagent_type": "sdr"}}]}},
            {"type": "progress", "parentToolUseID": "t1", "data": {"message": {"type": "assistant", "message": {
                "content": [{"type": "tool_use", "id": "s1", "name": "Read", "input": {"file_path": "leads.csv"}}]}}}})
        self.ler(coord)
        self.assertIn({"type": "agentStatus", "id": self.sdr, "status": "active"}, self.msgs)
        self.assertIn({"type": "agentToolStart", "id": self.sdr, "toolId": "t1", "status": "follow-ups do dia", "toolName": ""}, self.msgs)
        self.assertIn({"type": "agentToolStart", "id": self.sdr, "toolId": "s1", "status": "Reading leads.csv", "toolName": "Read"}, self.msgs)
        self.assertFalse([m for m in self.msgs if m["type"].startswith("subagent")])  # sem ajudante temporário
        self.assertFalse([m for m in self.msgs if m["type"] == "agentToolStart" and m["id"] == coord and m["toolId"] == "t1"])
        self.escrever(arq, {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1"}]}})
        self.ler(coord)
        self.assertEqual(self.msgs[-1], {"type": "agentStatus", "id": self.sdr, "status": "waiting", "awaitingInput": False})
        self.assertTrue(self.loja.get(self.sdr).esperando)
        self.assertEqual(self.loja.get(coord).redirecionados, {})

    def test_colega_de_equipe_com_nome_de_agente_da_casa_nao_duplica(self):
        self.vigia.acompanhar(self.projeto)
        lider_arq = self.sessao()
        self.escrever(lider_arq, {"type": "user", "message": {"content": "oi"}})
        self.vigia.varrer_pasta(str(self.projeto))
        lider_id = max(i for i, a in self.loja if not a.residente)
        self.loja.get(lider_id).equipe = "time-1"
        colega = self.sessao("bbbbbbbb-1111-2222-3333-444444444444")
        self.escrever(colega, {"type": "user", "teamName": "time-1", "agentName": "sdr", "message": {"content": "vai"}})
        antes = len(self.loja.agentes)
        self.vigia.procurar_colegas(str(self.projeto), self.loja.get(lider_id).sessao, lider_id)
        self.assertEqual(len(self.loja.agentes), antes)  # nenhum SDR novo: o residente assumiu
        sdr = self.loja.get(self.sdr)
        self.assertEqual(Path(sdr.jsonl).name, colega.name)
        self.assertEqual(sdr.lider_id, lider_id)
        self.vigia.tirar_colega(self.sdr, "equipe")  # a equipe acabou: ele volta para a rotina, não some
        self.assertIn(self.sdr, self.loja)
        self.assertEqual((sdr.jsonl, sdr.lider_id, sdr.esperando), ("", None, True))

    def test_vez_nova_solta_o_residente_e_residente_nao_e_gravado(self):
        gravados = []
        self.loja.gravar_agentes = gravados.append
        self.loja.gravar()
        self.assertEqual(gravados[-1], [])
        pai = self.loja.get(self.sdr)  # qualquer agente serve de "pai" aqui
        self.assertTrue(self.res.comecar(pai, "tx", {"description": "closer: proposta"}))
        self.vigia.rel.limpar_atividade(pai, pai.id)
        self.assertTrue(self.loja.get(self.res.ids["closer"]).esperando)


class TesteGanchos(Montagem):
    def test_sessao_confirmada_pelo_hook_vira_agente_e_para_de_adivinhar(self):
        g = G.Ganchos(self.vigia)
        self.vigia.acompanhar(self.projeto)
        arq = self.sessao()
        self.escrever(arq, {"type": "user", "message": {"content": "oi"}})
        base = {"session_id": "s-1", "transcript_path": str(arq), "cwd": "/projeto"}
        g.evento({**base, "hook_event_name": "SessionStart", "source": "startup"})
        self.assertEqual(self.tipos(), [])  # só pendente: a extensão abre sessões vazias
        g.evento({**base, "hook_event_name": "PreToolUse", "tool_name": "Grep", "tool_input": {}})
        a = self.loja.get(1)
        self.assertTrue(a and a.gancho_entregue)
        self.assertEqual(a.sessao, "s-1")
        inicio = next(m for m in self.msgs if m["type"] == "agentToolStart")
        self.assertTrue(inicio["toolId"].startswith("hook-"))
        g.evento({**base, "hook_event_name": "Notification", "notification_type": "permission_prompt"})
        self.assertIn({"type": "agentToolPermission", "id": 1}, self.msgs)
        g.evento({**base, "hook_event_name": "Stop"})
        self.assertEqual(self.msgs[-1], {"type": "agentStatus", "id": 1, "status": "waiting", "awaitingInput": False})
        g.evento({**base, "hook_event_name": "SessionEnd", "reason": "exit"})
        self.assertIn({"type": "agentClosed", "id": 1}, self.msgs)

    def test_sessao_que_abre_e_fecha_sem_nada_e_descartada(self):
        g = G.Ganchos(self.vigia)
        base = {"session_id": "s-2", "transcript_path": str(self.sessao()), "cwd": "/projeto"}
        g.evento({**base, "hook_event_name": "SessionStart"})
        g.evento({**base, "hook_event_name": "SessionEnd", "reason": "exit"})
        self.assertEqual(self.msgs, [])
        self.assertEqual(g.pendentes, {})


class TesteInstalacaoDosHooks(unittest.TestCase):
    def test_instala_preserva_os_outros_troca_os_do_pixel_agents_e_desinstala(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "settings.json"
            outro = {"matcher": "Bash", "hooks": [{"type": "command", "command": "meu-lint.sh"}]}
            antigo = {"matcher": "", "hooks": [{"type": "command", "command": 'node "/home/m/.pixel-agents/hooks/claude-hook.js"'}]}
            cfg.write_text(json.dumps({"model": "opus", "hooks": {"PreToolUse": [outro, antigo], "Stop": [antigo]}}))
            self.assertFalse(G.instalados(cfg))
            G.instalar(cfg)
            dados = json.loads(cfg.read_text())
            self.assertTrue(G.instalados(cfg))
            self.assertEqual(dados["model"], "opus")
            self.assertEqual(set(dados["hooks"]), set(G.EVENTOS))
            self.assertIn(outro, dados["hooks"]["PreToolUse"])
            self.assertNotIn("claude-hook.js", cfg.read_text())
            self.assertTrue((Path(d) / "settings.json.ciello.backup").exists())
            G.instalar(cfg)  # de novo: não duplica
            self.assertEqual(len(json.loads(cfg.read_text())["hooks"]["Stop"]), 1)
            G.desinstalar(cfg)
            self.assertEqual(json.loads(cfg.read_text()), {"model": "opus", "hooks": {"PreToolUse": [outro]}})


class TesteWebSocket(unittest.TestCase):
    def test_quadros_mascarados_grandes_e_ping(self):
        a, b = socket.socketpair()
        con = websocket.Conexao(a, a.makefile("rb"))

        def quadro(op, corpo, mascara=b"\x01\x02\x03\x04"):
            tam = len(corpo)
            cab = bytes([0x80 | op]) + (bytes([0x80 | tam]) if tam < 126 else bytes([0x80 | 126]) + tam.to_bytes(2, "big"))
            return cab + mascara + bytes(c ^ mascara[i % 4] for i, c in enumerate(corpo))

        grande = json.dumps({"type": "saveLayout", "layout": {"x": "é" * 300}}).encode()
        b.sendall(quadro(websocket.PING, b"oi") + quadro(websocket.TEXTO, grande))
        self.assertEqual(json.loads(con.receber())["layout"]["x"], "é" * 300)
        self.assertEqual(b.recv(4), bytes([0x80 | websocket.PONG, 2]) + b"oi")
        con.enviar({"type": "ok"})
        self.assertEqual(b.recv(100)[2:], b'{"type":"ok"}')
        b.sendall(quadro(websocket.FECHAR, b"\x03\xe8"))
        self.assertIsNone(con.receber())
        a.close()
        b.close()


class TesteAtivos(unittest.TestCase):
    def test_ativos_do_build(self):
        if not (TELA / "assets").exists():
            self.skipTest("tela não compilada")
        a = Ativos(TELA)
        self.assertEqual(len(a.personagens), 6)
        self.assertEqual([len(a.personagens[0][d]) for d in ("down", "up", "right")], [7, 7, 7])
        self.assertEqual((len(a.personagens[0]["down"][0]), len(a.personagens[0]["down"][0][0])), (32, 16))
        self.assertEqual(set(a.moveis["sprites"]), {c["id"] for c in a.moveis["catalog"]})
        self.assertEqual(len(a.paredes[0]), 16)  # 16 peças por conjunto (bitmask), cada uma 16×32
        self.assertTrue(all(len(p) == 32 and len(p[0]) == 16 for p in a.paredes[0]))
        self.assertTrue(a.layout_padrao and a.layout_padrao.get("layoutRevision"))
        tipos = [m["type"] for m in a.mensagens()]
        self.assertEqual(tipos, ["characterSpritesLoaded", "petSpritesLoaded", "floorTilesLoaded", "wallTilesLoaded",
                                 "carpetTilesLoaded", "furnitureAssetsLoaded"])

    def test_layout_da_ciello_tem_todas_as_salas_ligadas(self):
        """Cada sala do esboço existe, todo móvel existe no catálogo e dá para andar de qualquer sala a qualquer outra."""
        if not (TELA / "assets").exists():
            self.skipTest("tela não compilada")
        lay = json.loads((Path(__file__).resolve().parent.parent / "escritorio" / "layout-ciello.json").read_text(encoding="utf-8"))
        cat = {c["id"]: c for c in Ativos(TELA).moveis["catalog"]}
        rotulos = {a["label"] for a in lay["areas"]}
        self.assertEqual(rotulos, {"Gerente", "Arquivos G", "Copa", "Área de lazer", "Varanda", "Produtor Social", "Comercial", "Vendas"})
        C = lay["cols"]
        bloqueado = set()
        for m in lay["furniture"]:
            item = cat.get(m["type"].split(":")[0])
            self.assertIsNotNone(item, m["type"])
            if item.get("category") == "chairs" or item.get("canPlaceOnSurfaces"):
                continue
            for dr in range(item.get("backgroundTiles", 0), item["footprintH"]):
                for dc in range(item["footprintW"]):
                    bloqueado.add((m["col"] + dc, m["row"] + dr))
        andavel = {(i % C, i // C) for i, v in enumerate(lay["tiles"]) if v not in (0, 255)} - bloqueado
        inicio = next(q for q in andavel if lay["areaTiles"][q[1] * C + q[0]] == "Gerente")
        vistos, fila = {inicio}, [inicio]
        while fila:
            c, r = fila.pop()
            for v in ((c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)):
                if v in andavel and v not in vistos:
                    vistos.add(v)
                    fila.append(v)
        alcancadas = {lay["areaTiles"][r * C + c] for c, r in vistos} - {None}
        self.assertEqual(alcancadas, rotulos)
        # as portas são exatamente as do Mateus: um caminho único entre as salas
        portas = set()
        for c, r in andavel:
            if lay["areaTiles"][r * C + c] is None:  # quadrado de porta
                vizinhas = {lay["areaTiles"][rr * C + cc] for cc, rr in ((c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1))
                            if (cc, rr) in andavel} - {None}
                if len(vizinhas) == 2:
                    portas.add(frozenset(vizinhas))
        esperadas = {frozenset(x) for x in [("Arquivos G", "Gerente"), ("Gerente", "Comercial"), ("Comercial", "Área de lazer"),
                                            ("Área de lazer", "Varanda"), ("Área de lazer", "Produtor Social"),
                                            ("Produtor Social", "Vendas")]}
        self.assertEqual(portas, esperadas)
        # nenhuma sala encosta na outra sem porta, a não ser a Copa e a Área de lazer, que são um ambiente só
        abertas = set()
        for c, r in andavel:
            a = lay["areaTiles"][r * C + c]
            for cc, rr in ((c + 1, r), (c, r + 1)):
                b = lay["areaTiles"][rr * C + cc] if (cc, rr) in andavel else None
                if a and b and a != b:
                    abertas.add(frozenset((a, b)))
        self.assertEqual(abertas, {frozenset(("Copa", "Área de lazer"))})
        # perspectiva 3/4: a parede (2 blocos de altura na tela) cobre o bloco de cima, então nenhum bloco de sala fica
        # logo acima de uma parede (escondido atrás dela, com agente sumindo); e móvel alto de frente só encostado na
        # parede do fundo, com a última linha de fundo na linha da parede, senão parece boiar no meio da sala
        for i, v in enumerate(lay["tiles"]):
            c, r = i % C, i // C
            if lay["areaTiles"][i] and r + 1 < lay["rows"]:
                self.assertNotEqual(lay["tiles"][i + C], 0, f"bloco {(c, r)} de {lay['areaTiles'][i]} fica atrás da parede")
        soltos = {"TRIPE_CAMERA", "GUARDA_SOL_MESA"}  # na vida real ficam soltos mesmo
        for m in lay["furniture"]:
            tipo = m["type"].split(":")[0]
            item = cat[tipo]
            bg = item.get("backgroundTiles") or 0
            if not bg or item.get("canPlaceOnSurfaces") or item.get("canPlaceOnWalls") or item.get("category") in ("desks", "chairs") or tipo in soltos:
                continue
            fundo = [lay["tiles"][(m["row"] + bg - 1) * C + m["col"] + dc] for dc in range(item["footprintW"])]
            self.assertTrue(all(v == 0 for v in fundo), f"{m['type']} em {(m['col'], m['row'])} está solto da parede do fundo")
        # a poltrona atrás da mesa de mogno é do Gerente
        poltrona = next(m for m in lay["furniture"] if m["uid"] == lay["lugaresFixos"]["Gerente"])
        self.assertEqual(poltrona["type"], "POLTRONA_COURO_FRONT")
        self.assertEqual(lay["areaTiles"][(poltrona["row"] + 1) * C + poltrona["col"]], "Gerente")
        self.assertEqual(lay["cielloLayout"], 6)

    def test_layout_novo_da_ciello_substitui_o_antigo(self):
        from nucleo import persistencia as P
        with tempfile.TemporaryDirectory() as d, mock.patch.object(P, "CASA", Path(d)):
            P._gravar(Path(d) / "layout.json", {"version": 1, "cols": 37, "rows": 14})
            P._gravar(Path(d) / "config.json", {"areas": {"SDR": ["Comercial"]}, "areasVistas": ["SDR"]})
            novo = P.ler_layout()
            self.assertEqual((novo["cols"], novo["cielloLayout"]), (27, 6))
            self.assertTrue((Path(d) / "layout-antigo-v0.json").exists())  # cópia do antigo
            self.assertEqual((P.config()["areas"], P.config()["areasVistas"]), ({}, []))  # as áreas refazem com as salas novas
            P.gravar_layout({**novo, "cielloLayout": None})  # o editor salva sem a versão
            self.assertEqual(P.ler_layout()["cielloLayout"], 6)  # e não troca de novo

    def test_png_paleta_com_transparencia(self):
        import struct
        import zlib

        def pedaco(nome, corpo):
            return struct.pack(">I", len(corpo)) + nome + corpo + struct.pack(">I", zlib.crc32(nome + corpo))

        img = b"\x89PNG\r\n\x1a\n" + pedaco(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 3, 0, 0, 0)) + \
            pedaco(b"PLTE", b"\xff\x00\x00\x00\x80\xff") + pedaco(b"tRNS", b"\x00\x80") + \
            pedaco(b"IDAT", zlib.compress(b"\x00\x00\x01")) + pedaco(b"IEND", b"") + b"lixo depois do fim"
        self.assertEqual(png.ler(img).recorte(0, 0, 2, 1), [["", "#0080FF80"]])

    def test_pasta_de_sessoes_do_projeto(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(pasta_de_sessoes("C:\\Users\\mateus\\AGENTE-DE-POSTAGEM", d).name, "C--Users-mateus-AGENTE-DE-POSTAGEM")
            (Path(d) / "c--users-mateus-agente-de-postagem").mkdir()
            achada = pasta_de_sessoes("C:\\Users\\mateus\\AGENTE-DE-POSTAGEM", d)
            self.assertTrue(achada.is_dir())  # no Windows o nome com outra caixa já é a mesma pasta
            self.assertEqual(achada.name.lower(), "c--users-mateus-agente-de-postagem")


if __name__ == "__main__":
    unittest.main()
