"""SDR da Ciello: encontra, qualifica e aborda empresas que vendem pelo WhatsApp, e entrega tudo pronto para o CIELLO CRM.

Fluxo:
  1. consultas   gera as buscas do Google Maps a partir do perfil ideal (comercial/icp.json)
  2. buscar      roda o gosom/google-maps-scraper (MIT; executável em comercial/bin/, Docker opcional)
  3. qualificar  lê o resultado, pontua cada empresa (0–100) e junta em comercial/leads.csv
  4. abordar     monta a 1ª mensagem personalizada de cada lead com link wa.me (você envia do seu WhatsApp, 1 a 1)
  5. marcar      registra o que aconteceu (contatado, respondeu, demo, cliente, perdido, nao_contatar)
  6. hoje        lista os follow-ups do dia (cadência D+2, D+5, D+10) com o link pronto
  +  entrada     lead que chegou sozinho (DM, anúncio, site, indicação): registra e devolve a resposta em segundos
  7. crm         exporta a planilha para importar no CIELLO CRM
  +  instalar-scraper  baixa o executável do gosom para o seu sistema em comercial/bin/ (o instalar.cmd já faz)

Uso:
  python central/sdr.py consultas --segmentos imobiliaria odontologia --cidades "Chapecó SC"
  python central/sdr.py buscar                       # executável do gosom em comercial/bin/ (sem Docker)
  python central/sdr.py qualificar comercial/bruto/resultados.csv
  python central/sdr.py abordar --top 15
  python central/sdr.py marcar 12 contatado
  python central/sdr.py hoje
  python central/sdr.py crm

LGPD: só dados públicos de empresas (Google Maps), base de legítimo interesse B2B, origem informada,
saída fácil ("se não fizer sentido, me avisa que não mando mais") e lista nao-contatar respeitada.
Os arquivos com telefone ficam fora do git (.gitignore): o repositório é público.
"""
import argparse
import csv
import datetime as dt
import json
import math
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "comercial"
ICP = PASTA / "icp.json"
LEADS = PASTA / "leads.csv"
BLOQUEIO = PASTA / "nao-contatar.txt"
CAMPOS = ["id", "empresa", "segmento", "cidade", "telefone", "whatsapp", "site", "email", "nota_google", "avaliacoes",
          "pontos", "dor_citada", "maps", "etapa", "ultimo_contato", "proximo_contato", "tentativas", "origem", "obs"]
CADENCIA = [2, 5, 10]  # dias depois do contato anterior; depois da 3ª tentativa sem resposta, vira "frio"
ETAPAS = ["novo", "contatado", "respondeu", "demo", "proposta", "cliente", "perdido", "frio", "nao_contatar"]
# Reclamações de atendimento nas avaliações: é a dor exata que o CRM resolve.
DOR_ATENDIMENTO = re.compile(
    r"demor\w*|n[aã]o respond\w*|sem resposta|n[aã]o retorn\w*|sem retorno|nunca retorn\w*|n[aã]o atend\w*|"
    r"vácuo|vacuo|ningu[eé]m (me )?respond\w*|esquec\w+|atendimento (p[eé]ssimo|ruim|horr[ií]vel|demorado)|whats\w*", re.I)


def icp():
    return json.loads(ICP.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- telefone

def so_digitos(t):
    return re.sub(r"\D", "", t or "")


def normalizar_fone(t):
    """Devolve (telefone no formato 55DDDNNNNNNNN, é_celular). Celular brasileiro = 9 dígitos começando com 9."""
    d = so_digitos(t)
    if d.startswith("0"):
        d = d.lstrip("0")
    if len(d) in (10, 11):
        d = "55" + d
    if not (d.startswith("55") and len(d) in (12, 13)):
        return "", False
    return d, len(d) == 13 and d[4] == "9"


# ---------------------------------------------------------------- 1. consultas / 2. buscar

def cmd_consultas(a):
    cfg = icp()
    segs = a.segmentos or [s for s, v in sorted(cfg["segmentos"].items(), key=lambda x: -x[1]["prioridade"])]
    cidades = a.cidades or cfg["cidades"]
    linhas = [f"{termo} em {cidade} #!#{seg}" for seg in segs for termo in cfg["segmentos"][seg]["termos"] for cidade in cidades]
    destino = PASTA / "bruto" / "consultas.txt"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"{len(linhas)} buscas -> {destino}")


def cmd_buscar(a):
    bruto = PASTA / "bruto"
    if not (bruto / "consultas.txt").exists():
        sys.exit("Rode antes: python central/sdr.py consultas")
    opcoes = ["-depth", str(a.profundidade), "-lang", "pt", "-exit-on-inactivity", "3m"]
    # 1º o executável do gosom (sem Docker), em comercial/bin/: o instalar.cmd baixa (sdr.py instalar-scraper)
    binario = a.binario or next((str(p) for p in sorted((PASTA / "bin").glob("google*maps*scraper*")) if p.is_file()), None)
    if binario:
        cmd = [binario, "-input", str(bruto / "consultas.txt"), "-results", str(bruto / "resultados.csv"), *opcoes]
    elif shutil.which("docker"):
        cmd = ["docker", "run", "--rm", "-v", "gmaps-playwright-cache:/opt", "-v", f"{bruto.resolve()}:/work",
               "gosom/google-maps-scraper", "-input", "/work/consultas.txt", "-results", "/work/resultados.csv", *opcoes]
    else:
        sys.exit("Falta o buscador do Google Maps. Baixe com:\n"
                 "  python central/sdr.py instalar-scraper\n"
                 "(ou passe --binario CAMINHO). Docker não é necessário.\n"
                 "Sem scraper: qualquer CSV com colunas title, phone, website, review_count, review_rating serve para o 'qualificar'.")
    if a.email:
        cmd.append("-email")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    print("ok ->", bruto / "resultados.csv", "| agora: python central/sdr.py qualificar comercial/bruto/resultados.csv")


# ---------------------------------------------------------------- 3. qualificar

def textos_avaliacoes(bruto):
    """O gosom grava as avaliações como JSON (lista de objetos com 'Description'); aceita variações."""
    if not bruto:
        return []
    try:
        dado = json.loads(bruto)
    except (TypeError, ValueError):
        return [bruto]
    itens = dado if isinstance(dado, list) else [dado]
    return [str(i.get("Description") or i.get("description") or i.get("text") or "") if isinstance(i, dict) else str(i) for i in itens]


def trecho_dor(textos):
    for t in textos:
        for m in DOR_ATENDIMENTO.finditer(t):
            if "whats" not in m.group(0).lower():  # "WhatsApp" sozinho não é reclamação
                ini = max(0, m.start() - 60)
                return re.sub(r"\s+", " ", t[ini:m.end() + 60]).strip()
    return ""


def pontuar(lead, prioridade, textos):
    """0–100: encaixe do segmento 30 · movimento 25 · dor de atendimento 25 · canal de contato 20."""
    encaixe = 6 * prioridade
    n = int(lead.get("avaliacoes") or 0)
    movimento = min(25, round(25 * math.log10(1 + n) / math.log10(301)))  # ~300 avaliações = nota cheia
    dor = 25 if lead["dor_citada"] else (8 if any(DOR_ATENDIMENTO.search(t) for t in textos) else 0)
    canal = (14 if lead["whatsapp"] == "sim" else 6 if lead["telefone"] else 0) + (3 if lead["site"] else 0) + (3 if lead["email"] else 0)
    return encaixe + movimento + dor + canal


def ler_leads():
    if not LEADS.exists():
        return []
    with LEADS.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def gravar_leads(leads):
    PASTA.mkdir(parents=True, exist_ok=True)
    with LEADS.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        for l in leads:
            w.writerow({k: l.get(k, "") for k in CAMPOS})


def bloqueados():
    return {so_digitos(l) for l in BLOQUEIO.read_text(encoding="utf-8").splitlines()} if BLOQUEIO.exists() else set()


def ler_bruto(caminho: Path):
    if caminho.suffix == ".json":
        txt = caminho.read_text(encoding="utf-8").strip()
        return json.loads(txt) if txt.startswith("[") else [json.loads(l) for l in txt.splitlines() if l.strip()]
    with caminho.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


RELEASES = "https://api.github.com/repos/gosom/google-maps-scraper/releases/latest"


def escolher_executavel(assets, sistema=None, arquitetura=None):
    """Na lista de arquivos da versão, o executável deste PC (ex.: google-maps-scraper-1.9.2-windows-amd64.exe)."""
    import platform
    sistema = (sistema or platform.system()).lower()
    arquitetura = (arquitetura or platform.machine()).lower()
    arq = "arm64" if arquitetura in ("arm64", "aarch64") else "amd64"
    nome_so = {"windows": "windows", "darwin": "darwin", "linux": "linux"}.get(sistema, sistema)
    candidatos = [x for x in assets if nome_so in x["name"].lower() and arq in x["name"].lower()
                  and not x["name"].lower().endswith((".sha256", ".txt", ".sig"))]
    if nome_so == "windows":
        candidatos = [x for x in candidatos if x["name"].lower().endswith(".exe")] or candidatos
    return candidatos[0] if candidatos else None


def cmd_instalar_scraper(a):
    """Baixa a versão mais nova do gosom/google-maps-scraper (MIT) para comercial/bin/. Não instala nada no sistema."""
    destino_dir = PASTA / "bin"
    existentes = [p for p in destino_dir.glob("google*maps*scraper*") if p.is_file()] if destino_dir.exists() else []
    if existentes and not a.forcar:
        print(f"já está em comercial/bin/: {existentes[0].name} (use --forcar para baixar de novo)")
        return
    pedido = urllib.request.Request(RELEASES, headers={"Accept": "application/vnd.github+json", "User-Agent": "ciello-sdr"})
    try:
        with urllib.request.urlopen(pedido, timeout=30) as r:
            versao = json.load(r)
    except OSError as e:
        sys.exit(f"Não deu para consultar o GitHub ({e}). Baixe à mão em github.com/gosom/google-maps-scraper/releases "
                 "e salve em comercial/bin/.")
    asset = escolher_executavel(versao.get("assets", []))
    if not asset:
        sys.exit(f"A versão {versao.get('tag_name', '?')} não tem executável para este sistema. "
                 "Baixe à mão em github.com/gosom/google-maps-scraper/releases ou use o Docker.")
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / asset["name"]
    temporario = destino.with_name(destino.name + ".baixando")
    print(f"baixando {asset['name']} ({asset.get('size', 0) / 1e6:.0f} MB, versão {versao.get('tag_name', '?')})...")
    with urllib.request.urlopen(urllib.request.Request(asset["browser_download_url"], headers={"User-Agent": "ciello-sdr"}), timeout=300) as r, \
            open(temporario, "wb") as f:
        shutil.copyfileobj(r, f)
    if asset.get("size") and temporario.stat().st_size != asset["size"]:
        temporario.unlink()
        sys.exit("O download veio incompleto. Rode de novo: python central/sdr.py instalar-scraper")
    for antigo in existentes:
        antigo.unlink()
    temporario.replace(destino)
    if not sys.platform.startswith("win"):
        destino.chmod(0o755)
    print(f"pronto: {destino.relative_to(RAIZ)}. Na 1ª busca ele baixa o navegador que usa (uns minutos).")


def cmd_qualificar(a):
    cfg = icp()
    leads = ler_leads()
    vistos = {l["telefone"] for l in leads if l["telefone"]} | {l["maps"] for l in leads if l["maps"]}
    bloq = bloqueados()
    proximo_id = max([int(l["id"]) for l in leads] or [0]) + 1
    novos = 0
    for r in ler_bruto(Path(a.arquivo)):
        if str(r.get("status", "")).lower().startswith(("closed", "permanently", "fechado")):
            continue
        fone, celular = normalizar_fone(r.get("phone"))
        maps = r.get("link") or ""
        if (fone and fone in vistos) or (maps and maps in vistos) or (fone and fone in bloq):
            continue
        seg = (r.get("input_id") or "").split("#!#")[-1].strip() if "#!#" in (r.get("input_id") or "") else a.segmento
        if seg not in cfg["segmentos"]:
            seg = a.segmento or "outro"
        textos = textos_avaliacoes(r.get("user_reviews"))
        endereco = r.get("address") or ""
        cidade = next((c.split(" SC")[0] for c in cfg["cidades"] if c.split(" SC")[0].lower() in endereco.lower()), "")
        emails = r.get("emails") or ""
        lead = {"id": proximo_id, "empresa": r.get("title", "").strip(), "segmento": seg, "cidade": cidade, "telefone": fone,
                "whatsapp": "sim" if celular else "", "site": r.get("website") or "", "email": emails.split(",")[0].strip() if emails else "",
                "nota_google": r.get("review_rating") or "", "avaliacoes": r.get("review_count") or 0, "dor_citada": trecho_dor(textos),
                "maps": maps, "etapa": "novo", "tentativas": 0, "origem": "Google Maps (dado público)"}
        lead["pontos"] = pontuar(lead, cfg["segmentos"].get(seg, {}).get("prioridade", 2), textos)
        if lead["pontos"] < a.minimo or not fone:
            continue
        leads.append(lead)
        vistos |= {fone, maps}
        proximo_id += 1
        novos += 1
    leads.sort(key=lambda l: (l["etapa"] != "novo", -int(l["pontos"])))
    gravar_leads(leads)
    print(f"{novos} leads novos (total {len(leads)}) -> {LEADS}")
    for l in [l for l in leads if l["etapa"] == "novo"][:10]:
        dor = " · dor: " + l["dor_citada"][:60] if l["dor_citada"] else ""
        print(f"  #{l['id']:<4} {l['pontos']:>3}  {l['empresa'][:40]:40} {l['segmento']:12} {'WhatsApp' if l['whatsapp'] else 'fixo'}{dor}")


# ---------------------------------------------------------------- 4. abordar / 6. hoje

def link_wa(fone, texto):
    return f"https://wa.me/{fone}?text={urllib.parse.quote(texto)}"


def primeira_mensagem(l, cfg, assinatura):
    seg = cfg["segmentos"].get(l["segmento"], {})
    nome = l["empresa"].split(" - ")[0].strip()
    if l["dor_citada"]:
        gancho = (f"Vi nas avaliações do Google de vocês alguém comentando sobre demora no retorno. "
                  f"Isso é muito comum quando o atendimento fica espalhado no WhatsApp de cada um.")
    else:
        gancho = f"Trabalho com {l['segmento'].replace('_', ' ')}s aqui da região e o que mais vejo é: {seg.get('dor', 'cliente sem retorno no WhatsApp')}."
    return (f"Oi, tudo bem? Aqui é {assinatura}, da Ciello, de Chapecó. {gancho}\n\n"
            f"A gente montou o CIELLO CRM: a equipe toda atende no mesmo WhatsApp, com funil e lembrete de retorno. "
            f"Posso te mostrar em 15 minutos como ficaria na {nome}? São 30 dias grátis.\n\n"
            f"(Se não fizer sentido, me avisa que não mando mais.)")


def seguimento(l, n):
    nome = l["empresa"].split(" - ")[0].strip()
    textos = [
        f"Oi! Passando de novo sobre o CIELLO CRM para a {nome}. Quer que eu mande um vídeo de 1 minuto mostrando como funciona?",
        f"Oi! Uma pergunta rápida: hoje quantas pessoas atendem o WhatsApp da {nome}? Pergunto porque é aí que o CRM mais ajuda.",
        f"Oi! Vou parar de insistir 🙂 Se em algum momento quiserem organizar o atendimento do WhatsApp, é só me chamar. Abraço!",
    ]
    return textos[min(n, len(textos)) - 1]


def cmd_abordar(a):
    cfg = icp()
    leads = [l for l in ler_leads() if l["etapa"] == "novo" and l["telefone"]]
    leads.sort(key=lambda l: -int(l["pontos"]))
    hoje = dt.date.today().isoformat()
    destino = PASTA / "abordagens" / f"{hoje}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    L = [f"# Abordagens de {hoje}", "", "Clique, revise e envie do seu WhatsApp. Depois: `python central/sdr.py marcar ID contatado`.", ""]
    for l in leads[: a.top]:
        msg = primeira_mensagem(l, cfg, a.assinatura)
        L += [f"## #{l['id']} · {l['empresa']} · {l['pontos']} pts", "",
              f"{l['segmento']} · {l['cidade']} · nota {l['nota_google'] or '?'} ({l['avaliacoes']} avaliações) · [Maps]({l['maps']})"
              + (f" · [site]({l['site']})" if l["site"] else ""), ""]
        if l["dor_citada"]:
            L += [f"> Avaliação: \"…{l['dor_citada']}…\"", ""]
        L += ["```", msg, "```", "", f"[Abrir no WhatsApp]({link_wa(l['telefone'], msg)})" if l["whatsapp"] else f"Telefone fixo: ligar {l['telefone']}", ""]
    destino.write_text("\n".join(L), encoding="utf-8")
    print(f"{min(a.top, len(leads))} abordagens -> {destino}")


def cmd_hoje(a):
    hoje = dt.date.today().isoformat()
    devidos = [l for l in ler_leads() if l["etapa"] == "contatado" and l["proximo_contato"] and l["proximo_contato"] <= hoje]
    if not devidos:
        print("Nenhum follow-up para hoje.")
        return
    for l in devidos:
        n = int(l["tentativas"] or 1)
        msg = seguimento(l, n)
        print(f"#{l['id']} {l['empresa']} (tentativa {n + 1})\n  {msg}\n  {link_wa(l['telefone'], msg) if l['whatsapp'] else 'ligar ' + l['telefone']}\n")


# ---------------------------------------------------------------- lead que chegou sozinho (DM, site, anúncio, indicação)

PERGUNTAS = ["Hoje quantas pessoas atendem o WhatsApp de vocês?", "Mais ou menos quantos contatos novos chegam por semana?",
             "Como vocês controlam hoje quem já respondeu e quem precisa de retorno?"]


def resposta_entrada(nome, origem, assinatura):
    canal = {"instagram": "pelo Instagram", "anuncio": "pelo anúncio", "site": "pelo site", "indicacao": "por indicação"}.get(origem, "")
    return (f"Oi{', ' + nome if nome else ''}! Aqui é {assinatura}, da Ciello. Obrigado por chamar {canal}".rstrip() + " 🙂\n\n"
            "Pra eu te mostrar o CIELLO CRM do jeito certo, me conta rapidinho:\n"
            + "\n".join(f"{i}. {q}" for i, q in enumerate(PERGUNTAS, 1))
            + "\n\nSe preferir, já marco 15 minutos com você hoje ou amanhã pra te mostrar funcionando.")


def cmd_entrada(a):
    """Velocidade de resposta: lead que chega sozinho é registrado e respondido na hora (meta: menos de 5 minutos)."""
    cfg = icp()
    leads = ler_leads()
    fone, celular = normalizar_fone(a.telefone)
    if fone and fone in bloqueados():
        sys.exit("Esse número está na lista nao-contatar.")
    existente = next((l for l in leads if fone and l["telefone"] == fone), None)
    hoje = dt.date.today().isoformat()
    if existente:
        l = existente
        l["etapa"], l["proximo_contato"] = "respondeu", ""
    else:
        l = {"id": max([int(x["id"]) for x in leads] or [0]) + 1, "empresa": a.empresa or a.nome or fone, "segmento": a.segmento or "outro",
             "cidade": a.cidade, "telefone": fone, "whatsapp": "sim" if celular else "", "etapa": "respondeu", "tentativas": 0,
             "avaliacoes": 0, "origem": f"entrada: {a.origem}"}
        prioridade = cfg["segmentos"].get(l["segmento"], {}).get("prioridade", 2)
        l["pontos"] = 6 * prioridade + 25 + (20 if celular else 10)  # chegou sozinho = intenção alta
        leads.append(l)
    l["ultimo_contato"] = hoje
    if a.mensagem:
        l["obs"] = (l.get("obs", "") + f" | {dt.date.today():%d/%m} entrada ({a.origem}): {a.mensagem}").strip(" |")
    gravar_leads(leads)
    msg = resposta_entrada(a.nome.split(" ")[0] if a.nome else "", a.origem, a.assinatura)
    print(f"#{l['id']} {l['empresa']} registrado como 'respondeu' ({l['origem']}). Responda agora:\n\n{msg}\n")
    print(link_wa(fone, msg) if fone else "(sem telefone: responda pela DM)")
    print(f"\nDepois da resposta: python central/sdr.py marcar {l['id']} demo --obs \"equipe X, Y contatos/semana\"")


# ---------------------------------------------------------------- 5. marcar

def cmd_marcar(a):
    leads = ler_leads()
    l = next((x for x in leads if x["id"] == str(a.id)), None)
    if not l:
        sys.exit(f"Lead #{a.id} não encontrado.")
    hoje = dt.date.today()
    l["ultimo_contato"] = hoje.isoformat()
    if a.obs:
        l["obs"] = (l.get("obs", "") + f" | {hoje:%d/%m}: {a.obs}").strip(" |")
    if a.etapa == "contatado":
        n = int(l["tentativas"] or 0) + 1
        l["tentativas"] = n
        if n > len(CADENCIA):
            l["etapa"], l["proximo_contato"] = "frio", ""
        else:
            l["etapa"], l["proximo_contato"] = "contatado", (hoje + dt.timedelta(days=CADENCIA[n - 1])).isoformat()
    else:
        l["etapa"], l["proximo_contato"] = a.etapa, ""
        if a.etapa == "nao_contatar":
            with BLOQUEIO.open("a", encoding="utf-8") as f:
                f.write(l["telefone"] + "\n")
    gravar_leads(leads)
    print(f"#{l['id']} {l['empresa']}: {l['etapa']}" + (f" · próximo contato {l['proximo_contato']}" if l["proximo_contato"] else ""))


# ---------------------------------------------------------------- 7. crm

def cmd_crm(a):
    mapa_arq = PASTA / "crm_colunas.json"
    mapa = json.loads(mapa_arq.read_text(encoding="utf-8")) if mapa_arq.exists() else {
        "Nome": "empresa", "Telefone": "telefone", "E-mail": "email", "Empresa": "empresa", "Origem": "origem",
        "Etapa": "etapa", "Observações": "obs"}
    leads = [l for l in ler_leads() if l["etapa"] not in ("nao_contatar",) and (a.todos or l["etapa"] != "novo")]
    destino = PASTA / f"crm-{dt.date.today().isoformat()}.csv"
    with destino.open("w", encoding="utf-8-sig", newline="") as f:  # utf-8-sig abre certo no Excel
        w = csv.writer(f, delimiter=a.separador)
        w.writerow(list(mapa))
        for l in leads:
            linha = []
            for col, campo in mapa.items():
                v = l.get(campo, "")
                if campo == "obs":
                    v = "; ".join(x for x in [f"{l['pontos']} pts", l["segmento"], f"dor: {l['dor_citada']}" if l["dor_citada"] else "", l.get("obs", "")] if x)
                linha.append(v)
            w.writerow(linha)
    print(f"{len(leads)} leads -> {destino}" + ("" if mapa_arq.exists() else "  (colunas genéricas; ajuste em comercial/crm_colunas.json)"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("consultas"); s.add_argument("--segmentos", nargs="*"); s.add_argument("--cidades", nargs="*"); s.set_defaults(f=cmd_consultas)
    s = sub.add_parser("buscar"); s.add_argument("--profundidade", type=int, default=2); s.add_argument("--binario", help="caminho do executável do gosom"); s.add_argument("--email", action="store_true"); s.set_defaults(f=cmd_buscar)
    s = sub.add_parser("qualificar"); s.add_argument("arquivo"); s.add_argument("--segmento", default=""); s.add_argument("--minimo", type=int, default=35); s.set_defaults(f=cmd_qualificar)
    s = sub.add_parser("abordar"); s.add_argument("--top", type=int, default=15); s.add_argument("--assinatura", default="Mateus"); s.set_defaults(f=cmd_abordar)
    s = sub.add_parser("marcar"); s.add_argument("id", type=int); s.add_argument("etapa", choices=ETAPAS); s.add_argument("--obs", default=""); s.set_defaults(f=cmd_marcar)
    s = sub.add_parser("hoje"); s.set_defaults(f=cmd_hoje)
    s = sub.add_parser("entrada", help="lead que chegou sozinho: registra e devolve a resposta pronta")
    s.add_argument("--nome", default=""); s.add_argument("--empresa", default=""); s.add_argument("--telefone", default="")
    s.add_argument("--origem", default="instagram", choices=["instagram", "anuncio", "site", "indicacao", "outro"])
    s.add_argument("--segmento", default=""); s.add_argument("--cidade", default=""); s.add_argument("--mensagem", default="")
    s.add_argument("--assinatura", default="Mateus"); s.set_defaults(f=cmd_entrada)
    s = sub.add_parser("crm"); s.add_argument("--todos", action="store_true", help="inclui leads ainda não contatados"); s.add_argument("--separador", default=";"); s.set_defaults(f=cmd_crm)
    s = sub.add_parser("instalar-scraper", help="baixa o executável do Google Maps para comercial/bin/")
    s.add_argument("--forcar", action="store_true", help="baixa de novo mesmo se já existir"); s.set_defaults(f=cmd_instalar_scraper)
    a = ap.parse_args()
    from status import trabalhando
    with trabalhando("sdr", a.cmd):
        a.f(a)


if __name__ == "__main__":
    main()
