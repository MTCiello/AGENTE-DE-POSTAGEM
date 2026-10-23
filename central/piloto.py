"""Piloto automático da rede social: pesquisa, produz e publica sem você, e só te chama para o que é humano.

A cada rodada (o Agendador do Windows roda de hora em hora, ver agendar.cmd):
  1. checa as conexões em uso (provedor caído: não publica no escuro, guarda na fila e avisa);
  2. sincroniza números e comentários para o banco local e avalia os posts com 7 dias (biblioteca de ganchos);
  3. comentários: responde sozinho elogio e pergunta que o FAQ cobre; quem quer comprar vira lead no Comercial;
  4. produção dos próximos dias do calendário: o Claude pesquisa e escreve os roteiros que faltam; o PC faz
     narração, vídeo, capa e legenda (Estúdio de Voz, Estúdio de Vídeo, capa.mjs, legenda);
  5. publicação em cada rede ligada, pelo provedor escolhido em Conexões, respeitando o modo:
       automatico  publica sozinho; você pode "Segurar" qualquer post até a hora do envio
       aprovar     prepara tudo e espera o seu "Aprovar" em cada post
       pausado     não produz nem publica (os números e comentários continuam sendo guardados)

  python central/piloto.py rodar          # uma rodada agora
  python central/piloto.py estado         # o que está na fila e o que aconteceu
"""
import argparse
import contextlib
import datetime as dt
import io
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parent))
import calendario  # noqa: E402
import conexoes  # noqa: E402
import conteudo  # noqa: E402
import dados  # noqa: E402
import ia  # noqa: E402
import social  # noqa: E402
import status  # noqa: E402
from provedores import PROVEDORES  # noqa: E402
from provedores.base import ErroConexao, NaoSuportado  # noqa: E402

MODOS = {"automatico": "Automático", "aprovar": "Aprovar cada post", "pausado": "Pausado"}
PADRAO = {"modo": "automatico", "antecedencia_dias": 7, "envio_antecedencia_h": 12, "responder": "elogios_e_faq",
          "leads_para_comercial": True, "modelo_video": "escuro", "max_tentativas": 3}
FINAIS = {"publicado", "agendado", "segurado", "cancelado"}


def config() -> dict:
    try:
        c = json.loads(dados.estado("piloto.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        c = {}
    return {**PADRAO, **c}


def configurar(d: dict) -> dict:
    c = config()
    if d.get("modo") is not None:
        if d["modo"] not in MODOS:
            return {"ok": False, "saida": "modo inválido"}
        c["modo"] = d["modo"]
    for k, lim in (("antecedencia_dias", (1, 21)), ("envio_antecedencia_h", (1, 72)), ("max_tentativas", (1, 10))):
        if d.get(k) not in (None, ""):
            try:
                c[k] = min(max(int(d[k]), lim[0]), lim[1])
            except ValueError:
                return {"ok": False, "saida": f"{k} inválido"}
    if d.get("responder") in ("elogios_e_faq", "elogios", "nunca"):
        c["responder"] = d["responder"]
    if d.get("modelo_video"):
        c["modelo_video"] = str(d["modelo_video"])
    if "leads_para_comercial" in d:
        c["leads_para_comercial"] = bool(d["leads_para_comercial"])
    dados.estado("piloto.json").write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"ok": True, "saida": f"Piloto: {MODOS[c['modo']]}"}


def registrar(evento: str, detalhe: str = "", ok: bool = True):
    with dados.estado("piloto.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"quando": dt.datetime.now().isoformat(timespec="seconds"), "evento": evento, "detalhe": detalhe, "ok": ok},
                           ensure_ascii=False) + "\n")


def diario(n=40) -> list[dict]:
    try:
        linhas = dados.estado("piloto.jsonl").read_text(encoding="utf-8").splitlines()[-n:]
    except OSError:
        return []
    return [json.loads(l) for l in reversed(linhas) if l.strip()]


def executar(cmd: list[str], cwd: Path, timeout=3600) -> tuple[bool, str]:
    """Roda um passo de produção no PC. Os testes trocam esta função."""
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode == 0, (p.stdout + p.stderr)[-800:]
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)


# ---------------------------------------------------------------- 3. comentários

def cuidar_comentarios(con, c) -> dict:
    feitos = {"respondidos": 0, "leads": 0}
    for com in social.caixa(con):
        if com["categoria"] == "lead" and c["leads_para_comercial"]:
            try:
                import sdr
                origem = "instagram" if com["rede"] == "instagram" else "outro"
                with contextlib.redirect_stdout(io.StringIO()):  # a mensagem de resposta fica no Comercial
                    sdr.cmd_entrada(NS(nome=com["autor"], empresa=f"@{com['autor']} ({conexoes.REDES[com['rede']]})", telefone="", origem=origem,
                                       segmento="", cidade="", mensagem=f"Comentou: {com['texto'][:200]}", assinatura="Mateus"))
            except SystemExit:
                pass
            social.marcar(com["rede"], com["id_ext"], "lead", con)
            feitos["leads"] += 1
            registrar("lead", f"@{com['autor']} no {com['rede']}: {com['texto'][:80]}")
        elif com["sugestao"] and (com["categoria"] == "elogio" and c["responder"] != "nunca"
                                  or com["categoria"] == "pergunta" and c["responder"] == "elogios_e_faq"):
            r = social.responder(com["rede"], com["id_ext"], com["sugestao"], con)
            if r["ok"] and "publicada" in r["saida"]:
                feitos["respondidos"] += 1
    return feitos


# ---------------------------------------------------------------- 4. produção

def roteiros_que_faltam(ref: dt.date, c) -> list[dict]:
    hoje = ref
    fim = ref + dt.timedelta(days=c["antecedencia_dias"])
    faltam = []
    meses = {(hoje.year, hoje.month), (fim.year, fim.month)}
    for ano, m in sorted(meses):
        for d in calendario.mes(ano, m, ref)["dias"]:
            dia = dt.date.fromisoformat(d["data"])
            if hoje < dia <= fim and d["slot"] and not d["post"]:
                faltam.append({"data": d["data"], "pilar": d.get("sugestao", "")})
    return faltam


def pedir_roteiros(faltam: list[dict]) -> dict:
    lista = "\n".join(f"- {f['data']}: pilar {calendario.NOMES_PILARES.get(f['pilar'], f['pilar'])}" for f in faltam)
    pedido = ("Use o pesquisador-mercado e o roteirista, seguindo o AGENTE.md. Escreva um roteiro de reel para cada data abaixo, "
              "no mesmo formato dos arquivos de roteiros/ (scenes com type hook/item/cta e o texto falado em \"say\"; campo \"pilar\"; "
              "capa com tag e linhas), salvando em roteiros/<data>-<slug>.json:\n" + lista + "\n\n"
              "Antes: leia o radar mais recente em radar/, rode `python central/ganchos.py modelos` para o pilar de cada dia e confira "
              "os fatos numa fonte oficial (passo 3 do AGENTE.md). Não repita temas do historico.md. Gancho de até 9 palavras, "
              "2 a 4 itens, CTA \"Salva pra testar depois\". Não agende nada. No fim, responda só a lista dos arquivos criados.")
    return ia.rodar(pedido, f"Roteiros de {len(faltam)} post(s)")


def produzir(post: dict, c) -> tuple[bool, str]:
    """Narração + vídeo + capa + legenda de um post, no PC. Pula o que já existe."""
    raiz, stem = dados.RAIZ, post["post"]  # o programa (scripts); os arquivos do post ficam em conteudo.RAIZ (dados)
    pasta = conteudo.RAIZ
    py = sys.executable
    if not post["etapas"]["final"]:
        ok, saida = executar([py, "central/estudio_video.py", "gerar", stem, f"--modelo={c['modelo_video']}"], raiz)
        if not ok:
            return False, f"vídeo: {saida[-300:]}"
        ok, saida = executar([py, "central/estudio_video.py", "usar", stem, f"--modelo={c['modelo_video']}"], raiz)
        if not ok:
            return False, f"vídeo final: {saida[-300:]}"
    if not post["etapas"]["capa"]:
        ok, saida = executar(["node", "capa.mjs", str(pasta / "roteiros" / f"{stem}.json"), str(pasta / "midia" / "capas" / f"{stem}.jpg")], raiz / "reels")
        if not ok:
            registrar("capa", f"{stem}: capa não saiu ({saida[-200:]}); o post segue sem capa", ok=False)
    if not post["etapas"]["legenda"]:
        r = conteudo.gerar_legenda(stem)
        if not r.get("ok", True):
            return False, f"legenda: {r.get('saida', '')}"
    return True, "pronto"


# ---------------------------------------------------------------- 5. publicação

def _texto(post_stem: str) -> tuple[str, str]:
    try:
        d = json.loads((conteudo.ROTEIROS / f"{post_stem}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    legenda = (d.get("legenda") or "").strip()
    titulo = legenda.split("\n")[0][:95] if legenda else post_stem[11:].replace("-", " ")
    return legenda, titulo


def _envio(con, post, rede):
    r = con.execute("SELECT * FROM envios WHERE post=? AND rede=?", (post, rede)).fetchone()
    return dict(r) if r else None


def _salvar_envio(con, post, rede, **campos):
    atual = _envio(con, post, rede) or {"post": post, "rede": rede, "estado": "", "quando": "", "via": "", "id_ext": "", "url": "", "erro": "", "tentativas": 0}
    atual.update(campos, atualizado_em=dt.datetime.now().isoformat(timespec="seconds"))
    con.execute("INSERT OR REPLACE INTO envios (post, rede, estado, quando, via, id_ext, url, erro, tentativas, atualizado_em) VALUES (?,?,?,?,?,?,?,?,?,?)",
                tuple(atual[k] for k in ("post", "rede", "estado", "quando", "via", "id_ext", "url", "erro", "tentativas", "atualizado_em")))
    con.commit()


def publicar_fila(con, c, agora: dt.datetime) -> dict:
    feitos = {"enviados": 0, "esperando": 0, "erros": 0}
    cal = calendario.config()
    caidas = {x["id"] for x in conexoes.caidas()}
    mes_atual = agora.strftime("%Y-%m")
    usados_metricool = con.execute("SELECT COUNT(*) FROM envios WHERE via IN ('claude','metricool') AND estado IN ('agendado','publicado') "
                                   "AND substr(quando,1,7)=?", (mes_atual,)).fetchone()[0]
    for p in conteudo.quadro(dias_passados=1, ref=agora.date()):
        if not (p["etapas"]["final"] and p["etapas"]["legenda"]):
            continue
        for rede, info in conexoes.redes().items():
            if not info["ativa"] or not info["via"]:
                continue
            quando = f"{p['data']}T{cal['horarios'][rede]}"
            e = _envio(con, p["post"], rede)
            if not e and rede == "instagram" and p["etapas"]["agendado"]:  # a rotina semanal (ou você) já agendou: não duplica
                _salvar_envio(con, p["post"], rede, estado="agendado", quando=quando, via="historico", erro="registrado no historico.md")
                continue
            if e and (e["estado"] in FINAIS or e["tentativas"] >= c["max_tentativas"]):
                continue
            if c["modo"] == "aprovar" and (not e or e["estado"] != "aprovado"):
                if not e:
                    _salvar_envio(con, p["post"], rede, estado="aguardando_aprovacao", quando=quando, via=info["via"])
                feitos["esperando"] += 1
                continue
            hora_post = dt.datetime.fromisoformat(quando)
            prov = PROVEDORES[info["via"]]
            momento = hora_post - dt.timedelta(hours=c["envio_antecedencia_h"]) if prov.AGENDA else hora_post
            if hora_post < agora - dt.timedelta(hours=6):
                _salvar_envio(con, p["post"], rede, estado="perdido", quando=quando, via=info["via"], erro="passou da hora sem ser enviado")
                continue
            if agora < momento:
                if not e:
                    _salvar_envio(con, p["post"], rede, estado="na_fila", quando=quando, via=info["via"])
                continue
            if info["via"] in caidas:
                _salvar_envio(con, p["post"], rede, estado="na_fila", quando=quando, via=info["via"], erro=f"{prov.NOME} fora do ar: espera a conexão voltar")
                continue
            if info["via"] in ("claude", "metricool") and cal["limite_metricool"] and usados_metricool >= cal["limite_metricool"]:
                _salvar_envio(con, p["post"], rede, estado="na_fila", quando=quando, via=info["via"], erro="limite de posts do Metricool no mês")
                continue
            legenda, titulo = _texto(p["post"])
            envio = {"post": p["post"], "rede": rede, "quando": quando, "agora": agora.isoformat(timespec="minutes"), "texto": legenda, "titulo": titulo,
                     "arquivo": str(conteudo.RAIZ / "midia" / "final" / f"{p['post']}.mp4"),
                     "capa": str(conteudo.RAIZ / "midia" / "capas" / f"{p['post']}.jpg") if p["etapas"]["capa"] else ""}
            status.registrar("postagem", "trabalhando", f"Publicando {p['post']} no {conexoes.REDES[rede]}")
            try:
                cred = conexoes.credenciais(info["via"])
                r = prov.publicar(cred, envio)
                conexoes._guardar_se_mudou(info["via"], cred)
                _salvar_envio(con, p["post"], rede, estado=r["estado"], quando=quando, via=info["via"], id_ext=r.get("id_ext", ""),
                              url=r.get("url", ""), erro=r.get("aviso", ""))
                if info["via"] in ("claude", "metricool"):
                    usados_metricool += 1
                feitos["enviados"] += 1
                registrar("publicacao", f"{p['post']} · {conexoes.REDES[rede]} · {r['estado']}" + (f" · {r['aviso']}" if r.get("aviso") else ""))
                if rede == "instagram" and not p["etapas"]["agendado"]:
                    conteudo.marcar_agendado(p["post"], f"{p['data'][8:]}/{p['data'][5:7]} {cal['horarios'][rede][:2]}h",
                                             "Publicado" if r["estado"] == "publicado" else "Agendado")
                status.registrar("postagem", "pronto", f"{p['post']} no {conexoes.REDES[rede]}")
            except (ErroConexao, NaoSuportado, OSError) as ex:
                _salvar_envio(con, p["post"], rede, estado="erro", quando=quando, via=info["via"], erro=str(ex)[:300],
                              tentativas=(e or {}).get("tentativas", 0) + 1)
                feitos["erros"] += 1
                registrar("publicacao", f"{p['post']} · {conexoes.REDES[rede]}: {ex}", ok=False)
                status.registrar("postagem", "erro", f"{p['post']} no {conexoes.REDES[rede]}: {str(ex)[:80]}")
    return feitos


def segurar(post: str, rede: str, con=None) -> dict:
    con = con or dados.banco()
    e = _envio(con, post, rede)
    if e and e["estado"] in ("publicado", "agendado"):
        return {"ok": False, "saida": "já foi enviado: cancele direto na rede (ou no Metricool)"}
    _salvar_envio(con, post, rede, estado="segurado", quando=(e or {}).get("quando", ""), via=(e or {}).get("via", ""))
    registrar("segurado", f"{post} · {rede}")
    return {"ok": True, "saida": "Segurado: não vai ao ar nesta rede."}


def aprovar(post: str, rede: str, con=None) -> dict:
    con = con or dados.banco()
    e = _envio(con, post, rede)
    if e and e["estado"] in ("publicado", "agendado"):
        return {"ok": False, "saida": "já foi enviado"}
    _salvar_envio(con, post, rede, estado="aprovado", erro="", tentativas=0, quando=(e or {}).get("quando", ""), via=(e or {}).get("via", ""))
    return {"ok": True, "saida": "Aprovado: vai ao ar no horário."}


def tentar_de_novo(post: str, rede: str, con=None) -> dict:
    con = con or dados.banco()
    e = _envio(con, post, rede)
    if not e:
        return {"ok": False, "saida": "envio não encontrado"}
    _salvar_envio(con, post, rede, estado="na_fila", erro="", tentativas=0, quando=e["quando"], via=e["via"])
    return {"ok": True, "saida": "Volta para a fila: sai na próxima rodada do piloto."}


# ---------------------------------------------------------------- a rodada

def rodar(agora: dt.datetime | None = None, con=None, produzir_videos=True) -> dict:
    agora = agora or dt.datetime.now()
    con = con or dados.banco()
    c = config()
    out = {"quando": agora.isoformat(timespec="minutes"), "modo": c["modo"]}
    em_uso = sorted({v["via"] for v in conexoes.redes().values() if v["ativa"] and v["via"]})
    out["conexoes"] = {pid: conexoes.checar(pid)["ok"] for pid in em_uso}
    for pid, ok in out["conexoes"].items():
        if not ok:
            registrar("conexao", f"{PROVEDORES[pid].NOME} caiu: os posts dessa rede esperam na fila", ok=False)
    out["sincronizacao"] = social.sincronizar(con=con)
    out["resultados"] = social.avaliar(con, agora.date())
    for r in out["resultados"]:
        registrar("resultado", f"{r['data'][:10]} {r['rede']}: {r['multiplicador']}x a média ({r['veredito']})")
    out["comentarios"] = cuidar_comentarios(con, c)
    if c["modo"] == "pausado":
        registrar("rodada", "pausado: só guardei números e comentários")
        return out
    faltam = roteiros_que_faltam(agora.date(), c)
    ultimo_pedido = dados.estado("piloto-roteiros.txt")
    try:
        recente = agora - dt.datetime.fromisoformat(ultimo_pedido.read_text().strip()) < dt.timedelta(hours=6)
    except (OSError, ValueError):
        recente = False
    if faltam and not recente:  # no máximo um pedido de roteiros a cada 6 horas, mesmo se o Claude falhar
        ultimo_pedido.write_text(agora.isoformat(timespec="minutes"))
        r = pedir_roteiros(faltam)
        registrar("roteiros", f"{len(faltam)} pedido(s): {r['saida'][-200:]}", ok=r["ok"])
        out["roteiros"] = {"pedidos": len(faltam), "ok": r["ok"]}
    if produzir_videos:
        prontos = []
        for p in conteudo.quadro(dias_passados=0, ref=agora.date()):
            dias = (dt.date.fromisoformat(p["data"]) - agora.date()).days
            if 0 <= dias <= c["antecedencia_dias"] and not (p["etapas"]["final"] and p["etapas"]["legenda"]):
                status.registrar("produtor-video", "trabalhando", f"Produzindo {p['post']}")
                ok, msg = produzir(p, c)
                status.registrar("produtor-video", "pronto" if ok else "erro", f"{p['post']}: {msg[:80]}")
                registrar("producao", f"{p['post']}: {msg}", ok=ok)
                prontos.append({"post": p["post"], "ok": ok, "mensagem": msg})
        out["producao"] = prontos
    out["publicacao"] = publicar_fila(con, c, agora)
    registrar("rodada", f"{out['publicacao']['enviados']} enviado(s), {out['publicacao']['esperando']} esperando aprovação, "
                        f"{out['publicacao']['erros']} erro(s), {out['comentarios']['respondidos']} comentário(s) respondido(s), "
                        f"{out['comentarios']['leads']} lead(s)")
    return out


def fila(con=None, dias=14) -> list[dict]:
    con = con or dados.banco()
    desde = (dt.date.today() - dt.timedelta(days=2)).isoformat()
    ate = (dt.date.today() + dt.timedelta(days=dias)).isoformat()
    return [dict(r) for r in con.execute("SELECT * FROM envios WHERE quando>=? AND quando<=? ORDER BY quando", (desde, ate + "T23:59"))]


def para_janela() -> dict:
    con = dados.banco()
    return {"config": config(), "modos": MODOS, "fila": fila(con), "diario": diario(), "ia": ia.disponivel(), "caidas": conexoes.caidas()}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("acao", choices=["rodar", "estado"])
    a = ap.parse_args()
    if a.acao == "rodar":
        trava = dados.estado("piloto.trava")
        try:
            if dt.datetime.now() - dt.datetime.fromisoformat(trava.read_text().strip()) < dt.timedelta(hours=3):
                print("outra rodada do piloto ainda está trabalhando (render ou Claude): esta fica para a próxima hora")
                return
        except (OSError, ValueError):
            pass
        trava.write_text(dt.datetime.now().isoformat(timespec="seconds"))
        try:
            r = rodar()
        finally:
            trava.unlink(missing_ok=True)
        print(json.dumps({k: v for k, v in r.items() if k != "sincronizacao"}, ensure_ascii=False, indent=1, default=str))
    else:
        print(f"modo: {MODOS[config()['modo']]}")
        for e in fila():
            print(f"{e['quando']} {e['rede']:<9} {e['estado']:<20} {e['post']} {e['erro']}")
        for d in diario(15):
            print(f"{d['quando']} {'ok ' if d['ok'] else 'ERRO'} {d['evento']}: {d['detalhe']}")


if __name__ == "__main__":
    main()
