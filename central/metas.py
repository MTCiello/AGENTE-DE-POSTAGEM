"""Meta de crescimento: quantos clientes de CRM até quando, e o ritmo de prospecção que leva até lá.

A conta é o funil de trás para frente: clientes que faltam (com os cancelamentos do caminho) → testes grátis →
demos → respostas → abordagens por semana. As taxas de cada passo vêm dos seus dados (leads e clientes) quando já há
o bastante para confiar; antes disso, uma estimativa conservadora que você pode trocar. A meta fica em
financeiro/metas.json (fora do git).

  python central/metas.py                 # meta, ritmo da semana e o que está atrás
  python central/metas.py --meta 15 --ate 2027-06
"""
import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import financeiro  # noqa: E402
import plano  # noqa: E402
import sdr  # noqa: E402

SEMANAS_MES = 4.33
# taxa -> (nome, padrão, quanto dado basta para usar a sua taxa)
TAXAS = {
    "resposta": ("abordagens que respondem", 0.15, 20),
    "demo": ("respostas que viram demo", 0.40, 5),
    "teste": ("demos que entram no teste grátis", 0.50, 5),
    "conversao": ("testes que viram cliente", 0.60, 3),
}
RESPONDEU = {"respondeu", "demo", "proposta", "cliente", "perdido", "nao_contatar"}
DEPOIS_DA_DEMO = {"demo", "proposta", "cliente"}


def arquivo() -> Path:
    return financeiro.PASTA / "metas.json"


def ler() -> dict:
    try:
        return json.loads(arquivo().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def gravar(m: dict):
    arquivo().parent.mkdir(parents=True, exist_ok=True)
    arquivo().write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")


def e_crm(c: dict) -> bool:
    return (c.get("plano") or "crm").strip().lower().startswith("crm")


def contagens() -> dict:
    """O funil que já aconteceu: abordados, responderam, demos, testes decididos e convertidos."""
    leads = [l for l in sdr.ler_leads() if not (l.get("origem") or "").startswith("entrada")]
    abordados = [l for l in leads if l["etapa"] != "novo"]
    responderam = [l for l in abordados if l["etapa"] in RESPONDEU]
    demos = [l for l in responderam if l.get("agenda") or l["etapa"] in DEPOIS_DA_DEMO]
    clientes = financeiro.ler(financeiro.CLIENTES, financeiro.C_CLIENTE)
    testes = [c for c in clientes if c.get("teste_ate") and e_crm(c)]
    decididos = [c for c in testes if c["status"] != "teste"]
    return {"abordados": len(abordados), "responderam": len(responderam), "demos": len(demos),
            "testes": len(testes), "testes_decididos": len(decididos), "convertidos": sum(c["status"] == "ativo" for c in decididos)}


def taxas(m: dict | None = None) -> dict:
    """Cada taxa com a origem: a que você escreveu, a dos seus dados (se já há o bastante) ou a estimativa."""
    m = m if m is not None else ler()
    n = contagens()
    base = {"resposta": (n["responderam"], n["abordados"]), "demo": (n["demos"], n["responderam"]),
            "teste": (n["testes"], n["demos"]), "conversao": (n["convertidos"], n["testes_decididos"])}
    out = {}
    for k, (nome, padrao, minimo) in TAXAS.items():
        sim, total = base[k]
        escrita = (m.get("taxas") or {}).get(k)
        if escrita not in (None, ""):
            out[k] = {"nome": nome, "valor": float(escrita), "origem": "sua", "dados": f"{sim} de {total}"}
        elif total >= minimo and sim:
            out[k] = {"nome": nome, "valor": sim / total, "origem": "seus dados", "dados": f"{sim} de {total}"}
        else:
            out[k] = {"nome": nome, "valor": padrao, "origem": "estimativa", "dados": f"{sim} de {total}" if total else "sem dados ainda"}
    return out


def meses_ate(ate: str, ref: dt.date) -> int:
    ano, mes = map(int, ate.split("-")[:2])
    return max(0, (ano - ref.year) * 12 + mes - ref.month)


def semana(ref: dt.date) -> tuple[dt.date, dt.date]:
    seg = ref - dt.timedelta(days=ref.weekday())
    return seg, seg + dt.timedelta(days=6)


def feito_na_semana(ref: dt.date) -> dict:
    seg, dom = semana(ref)
    dentro = lambda t: bool(t) and seg.isoformat() <= t[:10] <= dom.isoformat()
    leads = sdr.ler_leads()
    clientes = financeiro.ler(financeiro.CLIENTES, financeiro.C_CLIENTE)
    return {"abordagens": sum(1 for l in leads if dentro(l.get("ultimo_contato")) and l["etapa"] in ("contatado", "frio")
                              and not (l.get("origem") or "").startswith("entrada")),
            "demos": sum(1 for l in leads if dentro(l.get("agenda"))),
            "testes": sum(1 for c in clientes if c.get("teste_ate") and dentro(c.get("inicio")))}


def calcular(m: dict | None = None, ref: dt.date | None = None) -> dict:
    """Da meta ao ritmo semanal. Sem meta, devolve a sugestão (o ponto de equilíbrio do plano)."""
    ref = ref or dt.date.today()
    m = m if m is not None else ler()
    clientes = financeiro.ler(financeiro.CLIENTES, financeiro.C_CLIENTE)
    ativos = sum(1 for c in clientes if c["status"] == "ativo" and e_crm(c) and float(c["valor_mensal"] or 0))
    em_teste = sum(1 for c in clientes if c["status"] == "teste" and e_crm(c))
    p = plano.ler()
    eq = plano.equilibrio(p) if p.get("pro_labore") else {}
    out = {"tem_meta": bool(m.get("clientes") and m.get("ate")), "ativos": ativos, "em_teste": em_teste,
           "sugestao": eq.get("clientes_para_te_pagar"), "preco": financeiro.produtos().get("crm", {}).get("mensal") or 0,
           "taxas": taxas(m), "contagens": contagens(), "feito": feito_na_semana(ref), "avisos": []}
    if not out["tem_meta"]:
        return out
    tx = {k: v["valor"] or 0.01 for k, v in out["taxas"].items()}
    meta, ate = int(m["clientes"]), m["ate"]
    meses = meses_ate(ate, ref)
    teste_dias = int(financeiro.produtos().get("crm", {}).get("teste_dias") or 0)
    meses_uteis = max(meses - math.ceil(teste_dias / 30), 0)  # quem entra no teste depois disso só vira cliente depois da meta
    churn = float(p.get("churn_mensal") or 0)
    perdas = round(ativos * churn * meses)
    vindo = round(em_teste * tx["conversao"])
    faltam = max(0, meta - ativos - vindo + perdas)
    out.update(meta=meta, ate=ate, meses=meses, meses_uteis=meses_uteis, perdas=perdas, vindo_do_teste=vindo, faltam=faltam,
               mrr_meta=meta * out["preco"], mrr_atual=ativos * out["preco"])
    if faltam == 0:
        out["por_semana"] = {"clientes": 0, "testes": 0, "demos": 0, "respostas": 0, "abordagens": 0}
        out["avisos"].append("Com os clientes de hoje e os testes em andamento, a meta já está coberta. Que tal subir a meta?")
        return out
    if meses_uteis == 0:
        out["avisos"].append(f"Não dá tempo pelo funil: o teste grátis leva {teste_dias} dias e a meta é para {ate[5:7]}/{ate[:4]}. Empurre a data ou feche sem teste.")
        meses_uteis = 1
    semanas = meses_uteis * SEMANAS_MES
    clientes_sem = faltam / semanas
    testes = clientes_sem / tx["conversao"]
    demos = testes / tx["teste"]
    respostas = demos / tx["demo"]
    abordagens = respostas / tx["resposta"]
    out["por_semana"] = {"clientes": round(clientes_sem, 1), "testes": math.ceil(testes), "demos": math.ceil(demos),
                         "respostas": math.ceil(respostas), "abordagens": math.ceil(abordagens)}
    if out["por_semana"]["abordagens"] > 100:
        out["avisos"].append(f"{out['por_semana']['abordagens']} abordagens por semana é muito para fazer à mão. Quem chama sozinho "
                             "(anúncio, Instagram, indicação) pula essa etapa: invista neles ou empurre a data.")
    if any(v["origem"] == "estimativa" for v in out["taxas"].values()):
        out["avisos"].append("Parte das taxas ainda é estimativa. Com umas 20 abordagens e 5 demos registradas, a conta passa a usar os seus números.")
    seg, _ = semana(ref)
    dias_passados = min((ref - seg).days, 5)  # dias úteis que já terminaram: segunda de manhã ninguém está atrás
    esperado = lambda total: total * dias_passados / 5
    atras = []
    for chave, nome in (("abordagens", "abordagens"), ("demos", "demos")):
        alvo, feito = out["por_semana"][chave], out["feito"][chave]
        if feito < math.floor(esperado(alvo)):
            atras.append(f"{feito} de {alvo} {nome}")
    out["atras"] = atras
    return out


def configurar(d: dict) -> dict:
    m = ler()
    try:
        if d.get("clientes") not in (None, ""):
            m["clientes"] = int(float(d["clientes"]))
            if m["clientes"] < 1:
                raise ValueError("a meta precisa ser de pelo menos 1 cliente")
        if d.get("ate"):
            ano, mes = map(int, str(d["ate"]).split("-")[:2])
            if not 1 <= mes <= 12:
                raise ValueError("mês inválido")
            m["ate"] = f"{ano}-{mes:02d}"
        taxas_ = dict(m.get("taxas") or {})
        for k in TAXAS:
            v = d.get(f"taxa_{k}")
            if v is None:
                continue
            if str(v).strip() == "":
                taxas_.pop(k, None)  # vazio = volta a usar os dados ou a estimativa
            else:
                x = float(str(v).replace(",", ".")) / 100
                if not 0 < x <= 1:
                    raise ValueError(f"taxa de {TAXAS[k][0]} precisa estar entre 1% e 100%")
                taxas_[k] = round(x, 4)
        m["taxas"] = taxas_
    except ValueError as e:
        return {"ok": False, "saida": str(e) if "invalid" not in str(e) else "número inválido"}
    gravar(m)
    return {"ok": True, "saida": "meta atualizada"}


def resumo(r: dict) -> str:
    if not r["tem_meta"]:
        return "Sem meta definida." + (f" Sugestão: {r['sugestao']} clientes (o seu ponto de equilíbrio)." if r.get("sugestao") else "")
    s = r["por_semana"]
    L = [f"Meta: {r['meta']} clientes de CRM até {r['ate'][5:7]}/{r['ate'][:4]} (hoje {r['ativos']}, {r['em_teste']} em teste). Faltam {r['faltam']}.",
         f"Por semana: {s['abordagens']} abordagens → {s['respostas']} respostas → {s['demos']} demos → {s['testes']} testes grátis.",
         f"Nesta semana: {r['feito']['abordagens']} abordagens, {r['feito']['demos']} demos, {r['feito']['testes']} testes."]
    return "\n".join(L + [f"⚠ {a}" for a in r["avisos"]])


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--meta", type=int, help="clientes de CRM")
    ap.add_argument("--ate", help="AAAA-MM")
    a = ap.parse_args()
    if a.meta or a.ate:
        r = configurar({"clientes": a.meta, "ate": a.ate})
        if not r["ok"]:
            sys.exit(r["saida"])
    print(resumo(calcular()))


if __name__ == "__main__":
    main()
