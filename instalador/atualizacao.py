"""Gerenciador de atualizações do Ciello OS: procura versão nova no GitHub e aplica sem mexer nos seus dados.

    python instalador/atualizacao.py status      versão instalada, canal e última verificação
    python instalador/atualizacao.py verificar   procura agora (mostra o que mudou)
    python instalador/atualizacao.py aplicar     baixa e instala a versão nova (com cópia de segurança)

    python instalador/atualizacao.py manifesto   anota os arquivos instalados (o instalador roda no fim)

Canais (estado/atualizacoes/config.json, ou a janela de Atualizações):
- "estavel": as versões publicadas em Releases (tags vX.Y.Z), as mesmas do instalador CielloOS-Setup.
- "teste": o último commit de uma branch (padrão: a branch em que o assistente está sendo desenvolvido).

Pasta clonada com Git: a atualização é um `git pull --ff-only` (não baixa ZIP).

Nunca são tocados: .venv, estado/, leads e abordagens, financeiro, founder, áudios, rascunhos do Estúdio,
node_modules e ferramentas/. Arquivos do programa que você editou vão antes para
estado/atualizacoes/<data>/backup/.
"""
import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

RAIZ = Path(__file__).resolve().parent.parent
PADRAO = {"repo": "MTCiello/AGENTE-DE-POSTAGEM", "canal": "estavel", "branch_teste": "ccr-75504115-gpanzf",
          "verificar_ao_abrir": True, "intervalo_horas": 12}
API = "https://api.github.com"

# Caminhos (relativos à pasta do assistente) que a atualização nunca cria, apaga nem sobrescreve.
PROTEGIDOS = (".git", ".venv", "estado", "audio", "ferramentas", "midia/estudio", "reels/node_modules",
              "escritorio/webview-ui/node_modules", "reels/public/clone", "comercial/leads.csv", "comercial/abordagens",
              "comercial/bruto", "comercial/bin", "comercial/nao-contatar.txt", "founder", "financeiro")
# Exceções dentro das pastas protegidas: arquivos do programa que vêm no pacote.
LIBERADOS = ("founder/idea.md", "financeiro/categorias.json")
# Se um destes mudar, as dependências são reinstaladas depois da atualização.
DEPENDENCIAS = ("central/requirements.txt", "central/requirements-voz.txt", "reels/package.json", "reels/package-lock.json")


# ---------------------------------------------------------------- configuração e estado

def pasta_estado(raiz=RAIZ):
    return Path(raiz) / "estado" / "atualizacoes"


def ler_json(p, padrao=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def gravar_json(p, dado):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(dado, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def config(raiz=RAIZ):
    return {**PADRAO, **(ler_json(pasta_estado(raiz) / "config.json", {}) or {})}


def salvar_config(raiz=RAIZ, **mudancas):
    p = pasta_estado(raiz) / "config.json"
    atual = {**(ler_json(p, {}) or {}), **{k: v for k, v in mudancas.items() if k in PADRAO}}
    gravar_json(p, atual)
    return {**PADRAO, **atual}


def estado(raiz=RAIZ):
    return ler_json(pasta_estado(raiz) / "estado.json", {}) or {}


def salvar_estado(raiz=RAIZ, **mudancas):
    novo = {**estado(raiz), **mudancas}
    gravar_json(pasta_estado(raiz) / "estado.json", novo)
    return novo


def versao_local(raiz=RAIZ):
    try:
        return (Path(raiz) / "VERSION").read_text(encoding="utf-8").strip() or "0.0.0"
    except OSError:
        return "0.0.0"


def numeros(versao):
    """'v1.10.2' -> (1, 10, 2); o que não for número vira 0 (para comparar sem quebrar)."""
    partes = []
    for p in str(versao).strip().lstrip("vV").split("-")[0].split("."):
        partes.append(int(p) if p.isdigit() else 0)
    while len(partes) < 3:
        partes.append(0)
    return tuple(partes)


def mais_nova(remota, local):
    return numeros(remota) > numeros(local)


def eh_git(raiz=RAIZ):
    return (Path(raiz) / ".git").exists() and shutil.which("git") is not None


# ---------------------------------------------------------------- GitHub

def pedir(url, tempo=15):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "Ciello-OS-atualizador"})
    with urllib.request.urlopen(req, timeout=tempo) as r:
        return r.read()


def pedir_json(url, tempo=15):
    return json.loads(pedir(url, tempo).decode("utf-8"))


def consultar(cfg=None, raiz=RAIZ, tempo=15):
    """Pergunta ao GitHub qual é a versão mais nova do canal. Não baixa nada."""
    cfg = cfg or config()
    repo = cfg["repo"]
    if eh_git(raiz):
        return consultar_git(raiz, tempo)
    if cfg["canal"] == "teste":
        branch = cfg["branch_teste"]
        c = pedir_json(f"{API}/repos/{repo}/commits/{branch}", tempo)
        instalado = estado(raiz).get("commit")
        return {"canal": "teste", "versao": c["sha"][:7], "nova": c["sha"] != instalado,
                "titulo": c["commit"]["message"].splitlines()[0], "notas": c["commit"]["message"],
                "data": c["commit"]["committer"]["date"], "pacote": f"https://codeload.github.com/{repo}/zip/{c['sha']}",
                "commit": c["sha"], "pagina": c.get("html_url", "")}
    try:
        r = pedir_json(f"{API}/repos/{repo}/releases/latest", tempo)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"canal": "estavel", "versao": None, "nova": False, "titulo": "Nenhuma versão publicada ainda", "notas": ""}
        raise
    tag = r["tag_name"]
    instalador = next((a["browser_download_url"] for a in r.get("assets", []) if a["name"].lower().endswith(".exe")), "")
    return {"canal": "estavel", "versao": tag.lstrip("vV"), "nova": mais_nova(tag, versao_local(raiz)),
            "titulo": r.get("name") or tag, "notas": r.get("body") or "", "data": r.get("published_at", ""),
            "pacote": r["zipball_url"], "instalador": instalador, "pagina": r.get("html_url", "")}


def git(raiz, *args, tempo=60):
    return subprocess.run(["git", *args], cwd=raiz, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=tempo)


def consultar_git(raiz=RAIZ, tempo=60):
    """Pasta clonada: compara o commit local com o da branch remota."""
    busca = git(raiz, "fetch", "--quiet", tempo=tempo)
    if busca.returncode:
        raise OSError(busca.stderr.strip() or "git fetch falhou")
    atras = git(raiz, "rev-list", "--count", "HEAD..@{u}")
    if atras.returncode:
        raise OSError("a branch local não acompanha nenhuma branch do GitHub")
    n = int(atras.stdout.strip() or 0)
    log = git(raiz, "log", "--format=%h %s", "HEAD..@{u}").stdout.strip()
    return {"canal": "git", "versao": git(raiz, "rev-parse", "--short", "@{u}").stdout.strip(), "nova": n > 0,
            "titulo": f"{n} atualização(ões) na branch" if n else "Em dia com o GitHub", "notas": log}


def verificar(cfg=None, raiz=RAIZ, tempo=15):
    """Consulta e anota o resultado (a janela e o lançador leem daqui). Erro de rede vira mensagem, não exceção."""
    try:
        info = consultar(cfg, raiz, tempo)
        info["erro"] = ""
    except (OSError, ValueError, KeyError) as e:
        info = {"nova": False, "erro": f"Não consegui falar com o GitHub: {e}"}
    salvar_estado(raiz, ultima_verificacao=time.strftime("%Y-%m-%dT%H:%M:%S"), ultima_consulta=info)
    return info


def hora_de_verificar(cfg=None, raiz=RAIZ, agora=None):
    cfg = cfg or config()
    if not cfg.get("verificar_ao_abrir", True):
        return False
    ultima = estado(raiz).get("ultima_verificacao")
    if not ultima:
        return True
    try:
        t = time.mktime(time.strptime(ultima, "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return True
    return ((agora or time.time()) - t) >= float(cfg.get("intervalo_horas", 12)) * 3600


# ---------------------------------------------------------------- aplicar

def protegido(rel):
    rel = PurePosixPath(rel).as_posix()
    if rel in LIBERADOS:
        return False
    return any(rel == p or rel.startswith(p + "/") for p in PROTEGIDOS)


def sha(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def ler_pacote(dados):
    """ZIP do GitHub (tudo dentro de uma pasta 'dono-repo-sha/') -> {caminho relativo: bytes}."""
    arquivos = {}
    with zipfile.ZipFile(io.BytesIO(dados)) as z:
        nomes = [n for n in z.namelist() if not n.endswith("/")]
        prefixo = os.path.commonprefix(nomes)
        prefixo = prefixo[:prefixo.rfind("/") + 1] if "/" in prefixo else ""
        for n in nomes:
            rel = n[len(prefixo):]
            partes = PurePosixPath(rel).parts
            if not rel or ".." in partes or rel.startswith("/") or ":" in partes[0]:
                continue  # caminho estranho no ZIP: ignora
            arquivos[rel] = z.read(n)
    if "central/escritorio/servidor.py" not in arquivos:
        raise ValueError("o pacote baixado não parece ser o Ciello OS")
    return arquivos


def impressao_dependencias(raiz):
    out = {}
    for rel in DEPENDENCIAS:
        p = Path(raiz) / rel
        out[rel] = sha(p) if p.exists() else None
    return out


def instalar_pacote(arquivos, raiz=RAIZ, avisar=print):
    """Grava os arquivos novos, apaga os que saíram do programa e guarda cópia do que você tinha editado."""
    raiz = Path(raiz)
    pasta = pasta_estado(raiz)
    manifesto_antigo = ler_json(pasta / "manifesto.json", {}) or {}
    backup = pasta / time.strftime("%Y-%m-%d_%H%M%S") / "backup"
    guardados, gravados, apagados = [], 0, 0

    def guardar(rel, alvo):
        destino = backup / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(alvo, destino)
        guardados.append(rel)

    novo_manifesto = {}
    for rel, conteudo in sorted(arquivos.items()):
        if protegido(rel):
            continue
        h = hashlib.sha256(conteudo).hexdigest()
        novo_manifesto[rel] = h
        alvo = raiz / rel
        if alvo.exists():
            atual = sha(alvo)
            if atual == h:
                continue
            if manifesto_antigo.get(rel) != atual:  # você mexeu (ou não sabemos de onde veio): guarda antes
                guardar(rel, alvo)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        tmp = alvo.with_name(alvo.name + ".novo-ciello")
        tmp.write_bytes(conteudo)
        os.replace(tmp, alvo)
        gravados += 1

    for rel, h in manifesto_antigo.items():  # saiu do programa nesta versão
        if rel in novo_manifesto or protegido(rel):
            continue
        alvo = raiz / rel
        if alvo.is_file():
            if sha(alvo) != h:
                guardar(rel, alvo)
            alvo.unlink()
            apagados += 1

    gravar_json(pasta / "manifesto.json", novo_manifesto)
    if guardados:
        avisar(f"Guardei {len(guardados)} arquivo(s) que estavam diferentes em {backup}")
    return {"gravados": gravados, "apagados": apagados, "guardados": guardados, "backup": str(backup) if guardados else ""}


def anotar_instalados(raiz=RAIZ):
    """Manifesto da instalação atual: a primeira atualização sabe o que veio do instalador e o que você mudou."""
    raiz = Path(raiz)
    manifesto = {}
    for p in raiz.rglob("*"):
        rel = p.relative_to(raiz).as_posix()
        if p.is_file() and not protegido(rel) and "__pycache__" not in p.parts:
            manifesto[rel] = sha(p)
    gravar_json(pasta_estado(raiz) / "manifesto.json", manifesto)
    return len(manifesto)


def python_do_assistente(raiz=RAIZ):
    for p in (Path(raiz) / ".venv" / "Scripts" / "python.exe", Path(raiz) / ".venv" / "bin" / "python"):
        if p.exists():
            return str(p)
    exe = Path(sys.executable)
    console = exe.with_name("python.exe")  # pythonw.exe (lançador) -> python.exe
    return str(console if exe.name.lower() == "pythonw.exe" and console.exists() else exe)


def reinstalar_dependencias(antes, depois, raiz=RAIZ, avisar=print):
    """Só o que mudou: requisitos do Python, voz (se estava instalada) e o gerador de vídeo."""
    raiz = Path(raiz)
    py = python_do_assistente(raiz)
    instalado = ler_json(raiz / "estado" / "instalacao.json", {}) or {}
    comps = set(instalado.get("componentes", ["base"]))
    passos = []
    if antes.get("central/requirements.txt") != depois.get("central/requirements.txt"):
        passos.append(("Bibliotecas do Python", [py, "-m", "pip", "install", "-r", "central/requirements.txt"]))
    if "voz" in comps and antes.get("central/requirements-voz.txt") != depois.get("central/requirements-voz.txt"):
        passos.append(("Estúdio de Voz", [py, "-m", "pip", "install", "-r", "central/requirements-voz.txt"]))
    npm = shutil.which("npm")
    if npm and (raiz / "reels" / "node_modules").exists() and any(
            antes.get(k) != depois.get(k) for k in ("reels/package.json", "reels/package-lock.json")):
        passos.append(("Gerador de vídeo", [npm, "install", "--no-audit", "--no-fund"]))
    for rotulo, cmd in passos:
        avisar(f"Atualizando dependências: {rotulo}...")
        cwd = raiz / "reels" if rotulo == "Gerador de vídeo" else raiz
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode:
            avisar(f"[aviso] {rotulo} não terminou: {(r.stdout + r.stderr).strip()[-600:]}")
    return [p[0] for p in passos]


def aplicar(cfg=None, raiz=RAIZ, avisar=print, info=None):
    """Baixa e instala a versão nova do canal. Devolve um resumo para a janela."""
    cfg = cfg or config()
    raiz = Path(raiz)
    if eh_git(raiz):
        antes = impressao_dependencias(raiz)
        avisar("Pasta clonada com Git: puxando as novidades (git pull --ff-only)...")
        r = git(raiz, "pull", "--ff-only", tempo=300)
        avisar((r.stdout + r.stderr).strip())
        if r.returncode:
            return {"ok": False, "erro": "o git pull não terminou (tem mudança local?). Veja a mensagem acima."}
        deps = reinstalar_dependencias(antes, impressao_dependencias(raiz), raiz, avisar)
        salvar_estado(raiz, ultima_atualizacao=time.strftime("%Y-%m-%dT%H:%M:%S"), ultima_consulta={"nova": False})
        return {"ok": True, "versao": versao_local(raiz), "dependencias": deps}
    info = info or consultar(cfg, raiz)
    if not info.get("nova"):
        avisar("Você já está na versão mais nova.")
        return {"ok": True, "versao": versao_local(raiz), "nada": True}
    avisar(f"Baixando a versão {info['versao']}...")
    dados = pedir(info["pacote"], tempo=300)
    arquivos = ler_pacote(dados)
    antes = impressao_dependencias(raiz)
    avisar(f"Instalando {len(arquivos)} arquivos (seus dados ficam onde estão)...")
    resumo = instalar_pacote(arquivos, raiz, avisar)
    deps = reinstalar_dependencias(antes, impressao_dependencias(raiz), raiz, avisar)
    salvar_estado(raiz, commit=info.get("commit") or estado(raiz).get("commit"), versao=versao_local(raiz),
                  ultima_atualizacao=time.strftime("%Y-%m-%dT%H:%M:%S"), ultima_consulta={**info, "nova": False})
    avisar(f"Pronto: Ciello OS {versao_local(raiz)}. Feche e abra o Ciello OS para usar a versão nova.")
    return {"ok": True, "versao": versao_local(raiz), "dependencias": deps, **resumo}


def resumo_status(raiz=RAIZ):
    cfg = config()
    e = estado(raiz)
    return {"versao": versao_local(raiz), "canal": "git" if eh_git(raiz) else cfg["canal"], "repo": cfg["repo"],
            "verificar_ao_abrir": cfg["verificar_ao_abrir"], "ultima_verificacao": e.get("ultima_verificacao"),
            "ultima_atualizacao": e.get("ultima_atualizacao"), "consulta": e.get("ultima_consulta") or {}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comando", choices=["status", "verificar", "aplicar", "manifesto"], nargs="?", default="status")
    ap.add_argument("--canal", choices=["estavel", "teste"], help="troca o canal e guarda a escolha")
    a = ap.parse_args()
    cfg = salvar_config(canal=a.canal) if a.canal else config()
    if a.comando == "manifesto":
        print(f"{anotar_instalados()} arquivos do programa anotados.")
        return 0
    if a.comando == "status":
        s = resumo_status()
        print(f"Ciello OS {s['versao']} · canal {s['canal']} · última verificação: {s['ultima_verificacao'] or 'nunca'}")
        return 0
    if a.comando == "verificar":
        print(f"Ciello OS {versao_local()} instalado. Procurando atualização ({'git' if eh_git() else cfg['canal']})...")
        info = verificar(cfg)
        if info.get("erro"):
            print(info["erro"])
            return 1
        if info.get("nova"):
            print(f"Versão nova disponível: {info['versao']} · {info.get('titulo', '')}")
            if info.get("notas"):
                print("\nO que mudou:\n" + info["notas"])
            print("\nPara instalar: botão Atualizar agora (janela Atualizações) ou `python instalador/atualizacao.py aplicar`.")
        else:
            print(info.get("titulo") if info.get("versao") is None else f"Tudo em dia (versão mais nova: {info['versao']}).")
        return 0
    try:
        r = aplicar(cfg)
    except (OSError, ValueError, zipfile.BadZipFile) as e:
        print(f"A atualização não terminou: {e}. Nada dos seus dados foi tocado.")
        return 1
    if not r.get("ok"):
        print(r.get("erro"))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
