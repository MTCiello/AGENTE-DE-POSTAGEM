"""Verificação do assistente: roda cada função de ponta a ponta e diz o que está pronto.

  python central/verificar.py            # tudo (inclui radar na internet e capa no Remotion)
  python central/verificar.py --rapido   # pula o que depende de internet ou demora

Resultado no terminal e em estado/verificacao.txt (mande esse arquivo se algo falhar).
"""
import argparse
import importlib.util
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PY = sys.executable
OK, AVISO, FALHA = "OK", "AVISO", "FALHA"
resultados = []


def rodar(cmd, cwd=RAIZ, timeout=600, env=None):
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", **(env or {})}
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env)
    return r.returncode, (r.stdout + r.stderr).strip()


def checar(nome, func):
    t0 = time.time()
    try:
        estado, msg = func()
    except Exception as e:  # um teste quebrado não derruba os outros
        estado, msg = FALHA, f"{type(e).__name__}: {e}"
    resultados.append((nome, estado, msg, time.time() - t0))
    marca = {OK: "[ok]   ", AVISO: "[aviso]", FALHA: "[FALHA]"}[estado]
    print(f"{marca} {nome}: {msg.splitlines()[0][:150] if msg else ''}", flush=True)


def ultima(txt, n=3):
    return " | ".join(l for l in txt.splitlines()[-n:] if l.strip())


# ---------------------------------------------------------------- verificações

def python_versao():
    v = sys.version_info
    if v < (3, 10):
        return FALHA, f"Python {v.major}.{v.minor}: precisa do 3.10 ou mais novo (recomendado 3.11)"
    return OK, f"Python {v.major}.{v.minor}.{v.micro} ({platform.system()})"


def ffmpeg():
    falta = [p for p in ("ffmpeg", "ffprobe") if not shutil.which(p)]
    if falta:
        return FALHA, "ffmpeg não encontrado: winget install Gyan.FFmpeg (depois abra um terminal novo)"
    _, out = rodar(["ffmpeg", "-version"])
    return OK, out.splitlines()[0]


def node():
    if not shutil.which("node"):
        return FALHA, "Node não encontrado: winget install OpenJS.NodeJS.LTS"
    _, out = rodar(["node", "--version"])
    maior = int(re.findall(r"\d+", out)[0])
    if maior < 20:
        return FALHA, f"Node {out}: o Remotion precisa do 20 ou mais novo"
    if not (RAIZ / "reels" / "node_modules").exists():
        return AVISO, f"Node {out}, mas falta 'npm install' na pasta reels (o instalar.cmd faz isso)"
    return OK, f"Node {out} e reels/node_modules"


def libs_python():
    falta = [m for m in ("numpy", "soundfile") if importlib.util.find_spec(m) is None]
    if falta:
        return FALHA, f"faltam {', '.join(falta)}: pip install -r central/requirements.txt"
    return OK, "numpy e soundfile"


def testes():
    cod, out = rodar([PY, "-m", "unittest", "discover", "central/testes"])
    if cod == 0:
        return OK, ultima(out, 2)
    # nomeia o que falhou e a última linha do erro de cada um (vai também para estado/verificacao.txt)
    motivos = []
    for bloco in re.split(r"^={50,}$", out, flags=re.M)[1:]:
        partes = re.split(r"^-{50,}$", bloco, flags=re.M)
        if len(partes) < 2:
            continue
        erro = [l for l in partes[1].strip().splitlines() if l.strip()]
        motivos.append(f"{partes[0].strip().split(' (')[0]} -> {erro[-1].strip()[:160] if erro else '?'}")
    return FALHA, ultima(out, 1) + ("\n         " + "\n         ".join(motivos) if motivos else "")


def montagem():
    with tempfile.TemporaryDirectory() as tmp:  # vídeo, voz e trilha de teste gerados na hora (não usa os seus arquivos)
        video, silencio, trilha = Path(tmp) / "video.mp4", Path(tmp) / "voz.wav", Path(tmp) / "trilha.mp3"
        rodar(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=navy:s=360x640:d=2", "-pix_fmt", "yuv420p", str(video)])
        rodar(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "1", str(silencio)])
        rodar(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=4", str(trilha)])
        saida = Path(tmp) / "final.mp4"
        cod, out = rodar([PY, "central/mixar.py", str(video), str(silencio), str(saida), "--trilha", str(trilha), "--inicio-trilha", "1"])
        if cod or not saida.exists():
            return FALHA, ultima(out)
        _, loud = rodar(["ffmpeg", "-nostats", "-i", str(saida), "-af", "ebur128", "-f", "null", "-"])
        lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", loud)
        return OK, f"vídeo + trilha montado ({lufs[-1] if lufs else '?'} LUFS)"


def oraculo():
    notas = []
    for video in sorted((RAIZ / "midia" / "final").glob("*-plano.mp4")):
        cod, out = rodar([PY, "central/analisar_video.py", str(video)])
        notas.append((video.stem[11:], "aprovado" in out, ultima(out, 1)))
    if not notas:
        return AVISO, "nenhum plano-sequência em midia/final"
    reprovados = [n for n, ok, _ in notas if not ok]
    return (AVISO if reprovados else OK), ", ".join(f"{n}: {'aprovado' if ok else 'reprovado'}" for n, ok, _ in notas)


def relatorio():
    if not list((RAIZ / "metricas").glob("20??-??-??.json")):
        return AVISO, "ainda sem retrato do Instagram em metricas/ (Conteúdo → Salvar retrato, ou importe os seus dados)"
    cod, out = rodar([PY, "central/relatorio.py"])
    arq = sorted((RAIZ / "metricas").glob("relatorio-*.md"))
    return (OK if cod == 0 and arq else FALHA), (f"{arq[-1].relative_to(RAIZ)}" if arq else ultima(out))


def ganchos():
    cod, out = rodar([PY, "central/ganchos.py", "ranking"])
    return (OK if cod == 0 else FALHA), out.splitlines()[0] if out else ""


def sdr():
    with tempfile.TemporaryDirectory() as tmp:  # o perfil de cliente do exemplo, sem mexer em comercial/
        shutil.copy(RAIZ / "exemplo" / "comercial" / "icp.json", Path(tmp) / "icp.json")
        cod, out = rodar([PY, "central/sdr.py", "consultas", "--segmentos", "imobiliaria", "--cidades", "Joinville SC"],
                         env={"CIELLO_COMERCIAL": tmp})
    if cod:
        return FALHA, ultima(out)
    binario = list((RAIZ / "comercial" / "bin").glob("google*maps*scraper*")) if (RAIZ / "comercial" / "bin").exists() else []
    if not binario and not shutil.which("docker"):
        return AVISO, ("consultas ok; falta o executável do Google Maps: rode o instalar.cmd de novo "
                       "(ou python central/sdr.py instalar-scraper)")
    return OK, f"consultas ok e scraper encontrado ({binario[0].name if binario else 'docker'})"


def radar():
    with tempfile.TemporaryDirectory() as tmp:  # testa sem mexer em radar/ do repositório
        cod, out = rodar([PY, "central/radar.py", "--dias", "7", "--saida", tmp], timeout=300)
    falhas = re.findall(r"^(\w+)\s+falhou", out, re.M)
    if cod:
        return FALHA, ultima(out)
    linha = next((l.split(" -> ")[0] for l in out.splitlines() if "assuntos ->" in l), "")
    return (AVISO if falhas else OK), linha + (f" · fontes fora do ar: {', '.join(falhas)}" if falhas else "")


OFX_TESTE = """<OFX><BANKTRANLIST>
<STMTTRN><TRNTYPE>CREDIT<DTPOSTED>{d1}<TRNAMT>149.00<FITID>V1<MEMO>PIX RECEBIDO CLIENTE TESTE</STMTTRN>
<STMTTRN><TRNTYPE>DEBIT<DTPOSTED>{d1}<TRNAMT>-50.00<FITID>V2<MEMO>FACEBK ADS</STMTTRN>
</BANKTRANLIST><LEDGERBAL><BALAMT>1000.00<DTASOF>{d1}</LEDGERBAL></OFX>"""


def financeiro():
    """Um mês simulado pela linha de comando, numa pasta temporária (não toca nos seus dados)."""
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "CIELLO_FINANCEIRO": tmp}
        hoje = time.strftime("%Y-%m-%d")
        ofx = Path(tmp) / "extrato.ofx"
        ofx.write_text(OFX_TESTE.format(d1=hoje.replace("-", "")), encoding="utf-8")
        passos = [["cliente", "--empresa", "Cliente Teste", "--valor", "149", "--dia", "1", "--whatsapp", "49999990000", "--inicio", "2020-01-01"],
                  ["cliente", "--empresa", "Cliente Atrasado", "--valor", "99", "--dia", "1", "--inicio", "2020-01-01"],
                  ["faturar", "--mes", hoje[:7]], ["faturar", "--mes", "2020-01"], ["importar", str(ofx)],
                  ["cobrar"], ["posvenda"], ["resumo"]]
        saidas = []
        for p in passos:
            r = subprocess.run([PY, "central/financeiro.py", *p], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60)
            if r.returncode:
                return FALHA, f"financeiro.py {p[0]}: {ultima(r.stdout + r.stderr)}"
            saidas.append(r.stdout)
        if "1 faturas baixadas" not in saidas[4]:
            return FALHA, "o extrato não deu baixa na fatura: " + saidas[4].strip()
        if "cobranças para enviar" not in saidas[5]:
            return FALHA, "a fatura atrasada não gerou cobrança: " + saidas[5].strip()
        mrr = re.search(r"\*\*MRR (R\$ [\d.,]+)", saidas[7])
        return OK, f"mês simulado: 2 clientes, extrato OFX conciliado, cobrança e resumo (MRR {mrr.group(1) if mrr else '?'})"


def briefing():
    cod, out = rodar([PY, "central/briefing.py"])
    if cod:
        return FALHA, ultima(out)
    prioridades = re.findall(r"^\d\. (.+?) _\(com", out, re.M)
    return OK, f"{len(prioridades)} prioridades hoje" + (f" · 1ª: {prioridades[0][:80]}" if prioridades else "")


def painel():
    """Sobe o painel numa porta livre, lê a API e desliga."""
    import socket
    import urllib.request
    with socket.socket() as s_:
        s_.bind(("127.0.0.1", 0))
        porta = s_.getsockname()[1]
    proc = subprocess.Popen([PY, "central/escritorio/servidor.py", "--porta", str(porta), "--sem-navegador", "--sem-escritorio"], cwd=RAIZ,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        abridor = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # localhost não passa por proxy
        for _ in range(40):
            try:
                k = __import__("json").loads(abridor.open(f"http://127.0.0.1:{porta}/api/kpis", timeout=2).read())
                html = abridor.open(f"http://127.0.0.1:{porta}/", timeout=2).read().decode("utf-8")
                break
            except OSError:
                time.sleep(0.25)
        else:
            return FALHA, "o painel não respondeu: " + (proc.stderr.read(400).decode(errors="replace") if proc.poll() is not None else "sem resposta")
        faltam = [c for c in ("instagram", "funil", "anuncios", "financeiro", "prioridades") if c not in k]
        if faltam or "Ciello OS" not in html:
            return FALHA, f"API incompleta: faltam {faltam}"
        js = abridor.open(f"http://127.0.0.1:{porta}/web/app.js", timeout=2).read()
        equipe = __import__("json").loads(abridor.open(f"http://127.0.0.1:{porta}/api/equipe", timeout=5).read())
        return OK, f"Ciello OS ok (testado na porta {porta}): área de trabalho, {len(equipe)} agentes, {len(k['prioridades'])} prioridades ({len(js) // 1024} KB de interface)"
    finally:
        proc.terminate()


def equipe():
    """Cada agente tem nome e descrição; cada comando só chama agentes que existem; o quadro de status conhece todos."""
    sys.path.insert(0, str(RAIZ / "central"))
    import status as st
    agentes = {}
    for p in sorted((RAIZ / ".claude" / "agents").glob("*.md")):
        cab = p.read_text(encoding="utf-8").split("---")[1]
        nome = re.search(r"^name:\s*(\S+)", cab, re.M)
        if not nome or not re.search(r"^description:\s*\S", cab, re.M):
            return FALHA, f"{p.name} sem name/description no cabeçalho"
        agentes[nome.group(1)] = p
    problemas = []
    comandos = sorted((RAIZ / ".claude" / "skills").glob("*/SKILL.md"))
    for sk in comandos:
        if sk.parent.name.startswith("founder") or sk.parent.name == "conselho":
            continue
        citados = set(re.findall(r"\*\*([a-z-]+)\*\*", sk.read_text(encoding="utf-8")))
        problemas += [f"/{sk.parent.name} cita '{c}'" for c in citados if c not in agentes and "-" in c]
    fora = sorted(set(agentes) - set(st.AGENTES))
    if fora:
        problemas.append(f"status.py não conhece: {', '.join(fora)}")
    if problemas:
        return FALHA, "; ".join(problemas)
    return OK, f"{len(agentes)} agentes e {len(comandos)} comandos/skills consistentes"


def vigia():
    with tempfile.TemporaryDirectory() as tmp:  # não mexe nas fotos reais nem em radar/
        cod, out = rodar([PY, "central/vigia.py", "checar", "--saida", tmp, "--fotos", tmp], timeout=300)
    if cod:
        return FALHA, ultima(out)
    linha = next((l for l in out.splitlines() if "fora do ar" in l and "->" in l), "")
    fora = int(re.search(r"(\d+) fora do ar", linha).group(1)) if linha else 0
    return (AVISO if fora else OK), linha.split(" -> ")[0] + (" (troque as URLs que falharam em comercial/concorrentes.json)" if fora else "")


def capa():
    if not (RAIZ / "reels" / "node_modules").exists():
        return AVISO, "pulei: falta npm install em reels"
    destino = RAIZ / "midia" / "capas" / "_teste-verificacao.jpg"
    cod, out = rodar(["node", "capa.mjs", "../roteiros/2026-10-21-teste-ideia.json", str(destino)], cwd=RAIZ / "reels", timeout=900)
    if cod or not destino.exists():
        return FALHA, ultima(out)
    destino.unlink()
    return OK, "capa renderizada no Remotion (na 1ª vez ele baixa o navegador dele)"


def estudio_video():
    """Monta um projeto do Estúdio de Vídeo e renderiza 1 s no HyperFrames (sem narração)."""
    hf = RAIZ / "reels" / "node_modules" / ".bin" / ("hyperframes.cmd" if os.name == "nt" else "hyperframes")
    if not hf.exists():
        return AVISO, "pulei: falta npm install em reels (o instalar.cmd faz)"
    os.environ.setdefault("HYPERFRAMES_SKIP_SKILLS", "1")
    sys.path.insert(0, str(RAIZ / "central"))
    import estudio_video as ev
    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp) / "projeto"
        (pasta / "fontes").mkdir(parents=True)
        cenas = ev.normalizar({"scenes": [{"type": "hook", "say": "Teste do Estúdio de Vídeo."}]})
        if ev.GSAP.exists():
            shutil.copy(ev.GSAP, pasta / "gsap.min.js")
        shutil.copy(RAIZ / "marca" / "logo-simbolo-marfim.svg", pasta / "logo.svg")
        (pasta / "index.html").write_text(ev.html_projeto(cenas, [(0, 0.8)], 1.0, "escuro", False, False), encoding="utf-8")
        saida = Path(tmp) / "teste.mp4"
        cod, out = rodar([str(hf), "render", str(pasta), "-o", str(saida), "-q", "draft", "--quiet"], cwd=pasta, timeout=600)
        if cod or not saida.exists():
            return FALHA, ultima(out)
    return OK, "vídeo de teste renderizado no HyperFrames (Estúdio de Vídeo pronto)"


def escritorio():
    """O escritório roda em Python dentro do Ciello OS: confere a tela compilada e se os sprites carregam."""
    tela = RAIZ / "central" / "escritorio" / "web" / "escritorio"
    if not (tela / "index.html").exists():
        return FALHA, "tela do escritório não compilada (escritorio/webview-ui: npm install e npx vite build)"
    sys.path.insert(0, str(RAIZ / "central" / "escritorio"))
    from nucleo.ativos import Ativos
    a = Ativos(tela)
    if not a.personagens or not a.moveis:
        return FALHA, "sprites do escritório não carregaram (pasta assets do build)"
    if os.name == "nt" and importlib.util.find_spec("winpty") is None:
        return AVISO, "escritório ok, mas o terminal do Claude dentro do OS precisa do pywinpty: rode o instalar.cmd de novo"
    return OK, f"pronto no Ciello.cmd: {len(a.personagens)} personagens, {len(a.moveis['catalog'])} móveis, terminal do Claude, sem Node"


def voz():
    falta = [m for m in ("kokoro", "chatterbox", "faster_whisper") if importlib.util.find_spec(m) is None]
    if falta:
        return AVISO, f"opcional, não instalado ({', '.join(falta)}): pip install -r central/requirements-voz.txt"
    return OK, "kokoro, chatterbox e faster-whisper instalados"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rapido", action="store_true")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    print(f"Verificando o assistente em {RAIZ}\n")
    import dados_iniciais  # primeira vez: a empresa fictícia de exemplo, como na primeira abertura do Ciello OS
    dados_iniciais.preparar()
    lista = [("Python", python_versao), ("ffmpeg", ffmpeg), ("Node", node), ("Bibliotecas Python", libs_python),
             ("Testes automáticos", testes), ("Montagem final (mixar)", montagem), ("Oráculo de ritmo", oraculo),
             ("Relatório semanal", relatorio), ("Biblioteca de ganchos", ganchos), ("SDR", sdr),
             ("Financeiro (mês simulado)", financeiro), ("Briefing do dia", briefing), ("Ciello OS (porta 3200)", painel),
             ("Equipe de agentes e comandos", equipe), ("Escritório de agentes", escritorio), ("Voz (opcional)", voz)]
    if not a.rapido:
        lista += [("Radar (internet)", radar), ("Vigia de concorrentes (internet)", vigia), ("Capa (Remotion)", capa), ("Estúdio de Vídeo (HyperFrames)", estudio_video)]
    for nome, f in lista:
        checar(nome, f)
    n = {e: sum(1 for _, s, _, _ in resultados if s == e) for e in (OK, AVISO, FALHA)}
    resumo = f"\n{n[OK]} ok · {n[AVISO]} avisos · {n[FALHA]} falhas"
    print(resumo)
    saida = RAIZ / "estado" / "verificacao.txt"
    saida.parent.mkdir(exist_ok=True)
    saida.write_text(f"{time.strftime('%d/%m/%Y %H:%M')} · {platform.platform()} · Python {platform.python_version()}\n"
                     + "\n".join(f"[{s}] {nome} ({t:.0f}s): {m}" for nome, s, m, t in resultados) + resumo + "\n", encoding="utf-8")
    print(f"Relatório: {saida.relative_to(RAIZ)}")
    sys.exit(1 if n[FALHA] else 0)


if __name__ == "__main__":
    main()
