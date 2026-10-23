"""Atendimento sem o Claude: acha no FAQ (comercial/faq.md) a resposta para a pergunta do cliente e mantém o FAQ.

O FAQ é uma lista em Markdown por seção: "- **Pergunta?** Resposta". Trechos entre ⟨ ⟩ são respostas que faltam.
A busca compara as palavras da pergunta do cliente (sem acento, com sinônimos do dia a dia) com as perguntas e
respostas do FAQ. Resposta nova ou completada pela janela Atendimento é gravada aqui mesmo.

  python central/atendimento.py "quanto fica o sistema por mês?"
  python central/atendimento.py --faltando
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from empresa import nome_produto  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
FAQ = RAIZ / "comercial" / "faq.md"
ITEM = re.compile(r"^- \*\*(.+?)\*\*\s*(.*)$")
VAZIAS = set("a o as os um uma de da do das dos e em no na nos nas por pra pro para com que se ao eu voce voces vc meu minha "
             "seu sua tem ter e eh isso isto esse essa aqui la ja so mais muito como qual quais quando onde oi ola bom dia tarde noite "
             "tudo bem obrigado obrigada gostaria queria saber me te nos lhe ele ela".split())
# palavras que o cliente usa → as que estão no FAQ
SINONIMOS = {"preco": "custa", "valor": "custa", "valores": "custa", "mensalidade": "custa", "quanto": "custa", "fica": "custa", "plano": "planos",
             "pagar": "pago", "pagamento": "pago", "boleto": "pago", "pix": "pago", "cartao": "pago", "atrasado": "atrasei", "atraso": "atrasei",
             "vencido": "atrasei", "esqueci": "atrasei", "contrato": "fidelidade", "cancelo": "fidelidade", "cancelar": "fidelidade", "multa": "fidelidade",
             "app": "celular", "aplicativo": "celular", "android": "celular", "iphone": "celular", "usuarios": "pessoas", "atendentes": "pessoas",
             "vendedores": "pessoas", "equipe": "pessoas", "funcionarios": "pessoas", "contatos": "importar", "planilha": "importar",
             "excel": "importar", "conversas": "conversas", "historico": "conversas", "suporte": "suporte", "ajuda": "suporte",
             "demora": "respondem", "pagina": "site", "website": "site", "hospedagem": "site", "dominio": "site", "prazo": "site",
             "business": "business", "caro": "caro", "barato": "caro", "teste": "custa", "gratis": "custa", "gratuito": "custa"}


def sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(c) != "Mn")


def palavras(t: str) -> set[str]:
    out = set()
    for p in re.findall(r"[a-z0-9]+", sem_acento(t)):
        if p in VAZIAS or len(p) < 3 and not p.isdigit():
            continue
        out.add(SINONIMOS.get(p, p))
        if p.endswith("s") and len(p) > 4:
            out.add(p[:-1])
    return out


def ler() -> list[dict]:
    if not FAQ.exists():
        return []
    itens, secao = [], ""
    for i, linha in enumerate(FAQ.read_text(encoding="utf-8").splitlines()):
        if linha.startswith("## "):
            secao = linha[3:].strip()
            continue
        m = ITEM.match(linha)
        if m:
            itens.append({"i": len(itens), "linha": i, "secao": secao, "pergunta": m.group(1).strip(), "resposta": m.group(2).strip(),
                          "completa": "⟨" not in m.group(2) and bool(m.group(2).strip())})
    return itens


def buscar(texto: str, n=3) -> list[dict]:
    alvo = palavras(texto)
    if not alvo:
        return []
    achados = []
    for it in ler():
        pq, rs = palavras(it["pergunta"]), palavras(it["resposta"])
        nota = 3 * len(alvo & pq) + len(alvo & rs)
        if nota:
            achados.append({**it, "nota": nota})
    return sorted(achados, key=lambda x: (-x["nota"], not x["completa"]))[:n]


def salvar(pergunta: str, resposta: str, i=None, secao: str = "Perguntas novas") -> dict:
    """Troca a resposta do item `i` (completar o FAQ) ou acrescenta uma pergunta nova na seção."""
    pergunta = re.sub(r"\s+", " ", str(pergunta or "")).strip().strip("*")[:200]
    resposta = re.sub(r"\s+", " ", str(resposta or "")).strip()[:1000]
    if not pergunta or not resposta:
        return {"ok": False, "saida": "escreva a pergunta e a resposta"}
    linhas = FAQ.read_text(encoding="utf-8").splitlines() if FAQ.exists() else [f"# FAQ do {nome_produto('crm')}", ""]
    nova = f"- **{pergunta}** {resposta}"
    itens = ler()
    if i not in (None, "") and 0 <= int(i) < len(itens):
        linhas[itens[int(i)]["linha"]] = nova
    else:
        cab = f"## {secao}"
        if cab in linhas:
            fim = linhas.index(cab) + 1
            while fim < len(linhas) and not linhas[fim].startswith("## "):
                fim += 1
            while fim > 0 and not linhas[fim - 1].strip():
                fim -= 1
            linhas.insert(fim, nova)
        else:
            linhas += ["", cab, nova]
    FAQ.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return {"ok": True, "saida": "FAQ atualizado (comercial/faq.md)"}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pergunta", nargs="?")
    ap.add_argument("--faltando", action="store_true", help="lista as respostas que ainda faltam no FAQ")
    a = ap.parse_args()
    if a.faltando:
        for it in ler():
            if not it["completa"]:
                print(f"[{it['secao']}] {it['pergunta']} → {it['resposta'] or '(vazia)'}")
        return
    for it in buscar(a.pergunta or ""):
        print(f"({it['nota']}) {it['pergunta']}\n    {it['resposta']}")


if __name__ == "__main__":
    main()
