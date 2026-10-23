"""Ponte com o Claude: usa o conector do Metricool que já está no seu Claude (funciona no plano grátis).

Não guarda senha nenhuma aqui: quem fala com o Metricool é o Claude Code. Coletar = importar os retratos que a
rotina semanal grava em metricas/AAAA-MM-DD.json. Publicar = pedir ao Claude (sem janela) que agende no
Metricool, seguindo o AGENTE.md. É o caminho de hoje; quando você conectar uma API direta, ela assume.
"""
import datetime as dt
import hashlib
import json

import dados
import ia

from .base import ErroConexao, Provedor


class PonteClaude(Provedor):
    ID = "claude"
    NOME = "Ponte com o Claude (Metricool grátis)"
    REDES = ("instagram", "tiktok", "youtube")
    PUBLICA = REDES
    AGENDA = True
    CAMPOS = []
    AJUDA = "Usa o conector do Metricool do seu Claude. Funciona no plano grátis do Metricool (20 posts por mês)."
    LIMITE = "Metricool grátis: 20 posts por mês e 30 dias de histórico (o OS guarda o resto aqui)."

    def testar(self, cred):
        if not ia.disponivel():
            raise ErroConexao("Claude Code não encontrado neste PC")
        retratos = sorted((dados.pasta_dados() / "metricas").glob("20??-??-??.json"))
        return {"conta": "Claude Code", "ultimo_retrato": retratos[-1].stem if retratos else ""}

    def coletar(self, cred, desde):
        out = {"perfil": [], "publicacoes": [], "comentarios": []}
        for arq in sorted((dados.pasta_dados() / "metricas").glob("20??-??-??.json")):
            try:
                r = json.loads(arq.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            p = r.get("perfil", {})
            out["perfil"].append({"rede": "instagram", "dia": r.get("data", arq.stem), "seguidores": p.get("seguidores"),
                                  "alcance": p.get("alcance"), "engajadas": p.get("contas_engajadas")})
            for reel in r.get("reels", []):
                if (reel.get("data") or "") < desde:
                    continue
                chave = reel.get("id") or "retrato-" + hashlib.sha1(f"{reel.get('data')}{reel.get('gancho')}".encode()).hexdigest()[:12]
                out["publicacoes"].append({"rede": "instagram", "id_ext": str(chave), "data": reel.get("data", ""), "tipo": "reels",
                                           "texto": reel.get("gancho", ""), "url": reel.get("url", ""), "views": reel.get("views"),
                                           "alcance": reel.get("alcance"), "salvamentos": reel.get("salvamentos"),
                                           "compartilhamentos": reel.get("compartilhamentos"), "comentarios": reel.get("comentarios"),
                                           "tempo_medio_s": reel.get("tempo_medio_s"), "_dia": r.get("data", arq.stem)})
        return out

    def publicar(self, cred, envio):
        rede = {"instagram": "Instagram (REEL)", "tiktok": "TikTok", "youtube": "YouTube (Short)"}[envio["rede"]]
        pedido = (f"Use o agente postagem. Agende no Metricool (brand 6611209, fuso America/Sao_Paulo) o post {envio['post']} no {rede} "
                  f"para {envio['quando'][:16].replace('T', ' ')}, com autoPublish true, o vídeo {envio['arquivo']} "
                  f"(siga o AGENTE.md para a URL pública do vídeo), a capa {envio.get('capa') or '(sem capa)'} e este texto:\n\n{envio.get('texto', '')}\n\n"
                  + (f"Título do YouTube: {envio.get('titulo', '')}\n" if envio["rede"] == "youtube" else "")
                  + "Não mude o texto. No fim, responda só AGENDADO ou ERRO: motivo.")
        r = ia.rodar(pedido, f"Agendar {envio['post']} · {envio['rede']}")
        if not r["ok"] or "AGENDADO" not in r["saida"].upper():
            raise ErroConexao(f"o Claude não confirmou o agendamento: {r['saida'][-300:]}")
        return {"estado": "agendado", "id_ext": f"claude-{dt.datetime.now():%Y%m%d%H%M}", "url": ""}
