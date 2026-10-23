"""Dados de exemplo, limpeza e importação: como o Ciello OS começa a ser usado.

O repositório é público e não tem dado de ninguém. Ele traz uma empresa fictícia em exemplo/ (Lumi Tecnologia) para
dar para conhecer o sistema cheio. Na primeira abertura (preparar), a pasta exemplo/ é copiada para os lugares de
verdade e anotada em estado/dados.json; quem já tem dados (uma instalação antiga) não recebe o exemplo por cima.

    python central/dados_iniciais.py status
    python central/dados_iniciais.py exemplo              # copia o exemplo (só onde não tem nada)
    python central/dados_iniciais.py limpar               # apaga só o que veio do exemplo e você não editou
    python central/dados_iniciais.py importar dados.zip   # seus dados (exportados de outro PC ou montados à mão)
    python central/dados_iniciais.py exportar dados.zip   # tudo o que é seu, para guardar ou levar para outro PC

O .zip tem as mesmas pastas do Ciello OS (comercial/, financeiro/, roteiros/...). O layout do escritório vai como
escritorio/layout.json e entra em ~/.ciello/escritorio/layout.json (o anterior fica guardado ao lado).
"""
import argparse
import datetime as dt
import hashlib
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path, PurePosixPath

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
EXEMPLO = RAIZ / "exemplo"
sys.path.insert(0, str(AQUI / "escritorio"))
from nucleo import persistencia  # noqa: E402

# o que é do usuário (fora do git; a atualização não mexe): pastas inteiras e arquivos soltos
PASTAS = ("comercial", "financeiro", "founder", "conhecimento", "metricas", "radar", "roteiros", "midia", "marca",
          "anuncios", "audio")
SOLTOS = ("historico.md",)
LAYOUT = "escritorio/layout.json"  # no .zip; no PC fica em persistencia.CASA
IGNORAR = {"README.md", "categorias.json", ".gitkeep"}  # arquivos do programa dentro das pastas de dados
SINAIS = ("comercial/empresa.json", "comercial/leads.csv", "comercial/produtos.json", "financeiro/clientes.csv",
          "founder/idea.md")  # qualquer um deles = já tem dados seus


def manifesto_arq() -> Path:
    return RAIZ / "estado" / "dados.json"


def ler_manifesto() -> dict | None:
    try:
        return json.loads(manifesto_arq().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def gravar_manifesto(m: dict):
    p = manifesto_arq()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def agora() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def do_usuario(rel: str) -> bool:
    """Caminho (com /) que pode entrar ou sair num .zip de dados."""
    partes = PurePosixPath(rel).parts
    if not partes or rel.startswith("/") or ".." in partes or "\\" in rel or ":" in partes[0]:
        return False
    return rel == LAYOUT or rel in SOLTOS or (partes[0] in PASTAS and len(partes) > 1 and partes[-1] not in IGNORAR)


def arquivos_exemplo():
    for p in sorted(EXEMPLO.rglob("*")):
        rel = p.relative_to(EXEMPLO).as_posix()
        if p.is_file() and do_usuario(rel):
            yield rel, p


def tem_dados_proprios() -> bool:
    return any((RAIZ / s).exists() for s in SINAIS)


# ---------------------------------------------------------------- comandos

def status() -> dict:
    m = ler_manifesto() or {}
    exemplo = [r for r, h in (m.get("exemplo") or {}).items() if (RAIZ / r).exists()]
    empresa = {}
    try:
        empresa = json.loads((RAIZ / "comercial" / "empresa.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return {"modo": m.get("modo") or ("proprio" if tem_dados_proprios() else "vazio"), "exemplo": len(exemplo),
            "empresa": empresa.get("nome", ""), "boas_vindas": not m.get("boas_vindas_vistas"), "quando": m.get("quando", "")}


def preparar() -> dict:
    """Primeira abertura: com o PC vazio, entra o exemplo; com dados de uma versão anterior, só anota."""
    m = ler_manifesto()
    if m is not None:
        return m
    if tem_dados_proprios():
        m = {"modo": "proprio", "exemplo": {}, "quando": agora(), "boas_vindas_vistas": True}
        gravar_manifesto(m)
        return m
    copiar_exemplo()
    return ler_manifesto()


def copiar_exemplo() -> dict:
    m = ler_manifesto() or {}
    copiados = dict(m.get("exemplo") or {})
    for rel, origem in arquivos_exemplo():
        alvo = RAIZ / rel
        if alvo.exists():
            continue  # nunca por cima de um arquivo seu
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, alvo)
        copiados[rel] = sha(alvo)
    m.update({"modo": "exemplo", "exemplo": copiados, "quando": agora()})
    gravar_manifesto(m)
    return {"ok": True, "saida": f"{len(copiados)} arquivo(s) de exemplo da Lumi Tecnologia (empresa fictícia)"}


def limpar() -> dict:
    """Apaga o que veio do exemplo. O que você editou depois fica (e é avisado)."""
    m = ler_manifesto() or {}
    apagados, mantidos = 0, []
    for rel, h in (m.get("exemplo") or {}).items():
        alvo = RAIZ / rel
        if not alvo.is_file():
            continue
        if sha(alvo) != h:
            mantidos.append(rel)
            continue
        alvo.unlink()
        apagados += 1
        pasta = alvo.parent
        while pasta != RAIZ and pasta.is_dir() and not any(pasta.iterdir()):
            pasta.rmdir()
            pasta = pasta.parent
    m.update({"modo": "limpo", "exemplo": {r: m["exemplo"][r] for r in mantidos}, "quando": agora()})
    gravar_manifesto(m)
    saida = f"{apagados} arquivo(s) de exemplo apagados."
    if mantidos:
        saida += f" Ficaram {len(mantidos)} que você editou: {', '.join(mantidos[:5])}{'...' if len(mantidos) > 5 else ''}"
    return {"ok": True, "saida": saida, "mantidos": mantidos}


def importar(conteudo: bytes) -> dict:
    """Recebe o .zip: limpa o exemplo antes, guarda cópia do que for substituído e grava só caminhos de dados."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(conteudo))
    except zipfile.BadZipFile:
        return {"ok": False, "saida": "não é um arquivo .zip"}
    nomes = [n for n in zf.namelist() if not n.endswith("/")]
    # aceita o .zip com uma pasta em volta (ex.: dados-ciello/comercial/...)
    prefixo = ""
    if nomes and not any(do_usuario(n) for n in nomes):
        topo = {n.split("/")[0] for n in nomes}
        if len(topo) == 1:
            prefixo = topo.pop() + "/"
    validos = [(n, n[len(prefixo):]) for n in nomes if n.startswith(prefixo) and do_usuario(n[len(prefixo):])]
    if not validos:
        return {"ok": False, "saida": "o .zip não tem nenhuma pasta do Ciello OS (comercial/, financeiro/, roteiros/...)"}
    if (ler_manifesto() or {}).get("modo") == "exemplo":
        limpar()
    backup = RAIZ / "estado" / "importacoes" / dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    gravados, guardados = 0, 0
    for nome, rel in validos:
        alvo = persistencia.CASA / "layout.json" if rel == LAYOUT else RAIZ / rel
        dado = zf.read(nome)
        if alvo.exists():
            if alvo.read_bytes() == dado:
                continue
            copia = backup / rel
            copia.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(alvo, copia)
            guardados += 1
        alvo.parent.mkdir(parents=True, exist_ok=True)
        tmp = alvo.with_name(alvo.name + ".importando")
        tmp.write_bytes(dado)
        tmp.replace(alvo)
        gravados += 1
    m = ler_manifesto() or {}
    m.update({"modo": "importado", "quando": agora(), "boas_vindas_vistas": True})
    gravar_manifesto(m)
    saida = f"{gravados} arquivo(s) importados."
    if guardados:
        saida += f" {guardados} que já existiam foram guardados em {backup.relative_to(RAIZ).as_posix()}."
    if any(rel == LAYOUT for _, rel in validos):
        saida += " O layout do escritório entra ao reabrir o Ciello OS."
    return {"ok": True, "saida": saida, "gravados": gravados}


def exportar(destino: Path | None = None) -> dict:
    """Tudo o que é seu num .zip (o mesmo formato que o importar recebe)."""
    destino = destino or RAIZ / "estado" / "exportacoes" / f"ciello-dados-{dt.date.today():%Y-%m-%d}.zip"
    destino.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
        for pasta in PASTAS:
            for p in sorted((RAIZ / pasta).rglob("*")):
                rel = p.relative_to(RAIZ).as_posix()
                if p.is_file() and do_usuario(rel) and "__pycache__" not in p.parts:
                    zf.write(p, rel)
                    n += 1
        for rel in SOLTOS:
            if (RAIZ / rel).is_file():
                zf.write(RAIZ / rel, rel)
                n += 1
        if (persistencia.CASA / "layout.json").is_file():
            zf.write(persistencia.CASA / "layout.json", LAYOUT)
            n += 1
    return {"ok": True, "saida": f"{n} arquivo(s) em {destino.name}", "arquivo": str(destino), "nome": destino.name}


def boas_vindas_vistas() -> dict:
    m = ler_manifesto() or {"modo": "vazio", "exemplo": {}}
    m["boas_vindas_vistas"] = True
    gravar_manifesto(m)
    return {"ok": True, "saida": ""}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("exemplo")
    sub.add_parser("limpar")
    s = sub.add_parser("importar"); s.add_argument("zip", type=Path)
    s = sub.add_parser("exportar"); s.add_argument("zip", type=Path, nargs="?")
    a = ap.parse_args()
    if a.cmd == "status":
        r = status()
        print(f"modo: {r['modo']} · empresa: {r['empresa'] or '(sem nome)'} · arquivos de exemplo: {r['exemplo']}")
        return
    if a.cmd == "exemplo":
        r = copiar_exemplo()
    elif a.cmd == "limpar":
        r = limpar()
    elif a.cmd == "importar":
        r = importar(a.zip.read_bytes())
    else:
        r = exportar(a.zip)
    print(r["saida"])
    sys.exit(0 if r["ok"] else 1)


if __name__ == "__main__":
    main()
