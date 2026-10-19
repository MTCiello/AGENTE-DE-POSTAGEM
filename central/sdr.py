"""SDR da Ciello: encontra, qualifica e aborda empresas que vendem pelo WhatsApp, e entrega tudo pronto para o CIELLO CRM.

Fluxo:
  1. consultas   gera as buscas do Google Maps a partir do perfil ideal (comercial/icp.json)
  2. buscar      roda o gosom/google-maps-scraper (MIT, Docker) e guarda o resultado bruto
  3. qualificar  lê o resultado, pontua cada empresa (0–100) e junta em comercial/leads.csv
  4. abordar     monta a 1ª mensagem personalizada de cada lead com link wa.me (você envia do seu WhatsApp, 1 a 1)
  5. marcar      registra o que aconteceu (contatado, respondeu, demo, cliente, perdido, nao_contatar)
  6. hoje        lista os follow-ups do dia (cadência D+2, D+5, D+10) com o link pronto
  7. crm         exporta a planilha para importar no CIELLO CRM

Uso:
  python central/sdr.py consultas --segmentos imobiliaria odontologia --cidades "Chapecó SC"
  python central/sdr.py buscar                       # precisa do Docker
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
    if not shutil.which("docker"):
        sys.exit("Precisa do Docker Desktop (docker.com). O scraper é o gosom/google-maps-scraper.")
    cmd = ["docker", "run", "--rm", "-v", "gmaps-playwright-cache:/opt", "-v", f"{bruto.resolve()}:/work",
           "gosom/google-maps-scraper", "-input", "/work/consultas.txt", "-results", "/work/resultados.csv",
           "-depth", str(a.profundidade), "-lang", "pt", "-exit-on-inactivity", "3m"]
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
    s = sub.add_parser("buscar"); s.add_argument("--profundidade", type=int, default=2); s.add_argument("--email", action="store_true"); s.set_defaults(f=cmd_buscar)
    s = sub.add_parser("qualificar"); s.add_argument("arquivo"); s.add_argument("--segmento", default=""); s.add_argument("--minimo", type=int, default=35); s.set_defaults(f=cmd_qualificar)
    s = sub.add_parser("abordar"); s.add_argument("--top", type=int, default=15); s.add_argument("--assinatura", default="Mateus"); s.set_defaults(f=cmd_abordar)
    s = sub.add_parser("marcar"); s.add_argument("id", type=int); s.add_argument("etapa", choices=ETAPAS); s.add_argument("--obs", default=""); s.set_defaults(f=cmd_marcar)
    s = sub.add_parser("hoje"); s.set_defaults(f=cmd_hoje)
    s = sub.add_parser("crm"); s.add_argument("--todos", action="store_true", help="inclui leads ainda não contatados"); s.add_argument("--separador", default=";"); s.set_defaults(f=cmd_crm)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
