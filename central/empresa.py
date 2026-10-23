"""Quem usa o Ciello OS: o nome da empresa, quem assina as mensagens, a cidade, o Instagram e os produtos.

Tudo vem de comercial/empresa.json e comercial/produtos.json, que ficam fora do git (cada empresa tem os seus).
O Ciello OS chega com uma empresa fictícia de exemplo (pasta exemplo/, ver central/dados_iniciais.py); sem
nenhum arquivo, valem os textos neutros de PADRAO. CIELLO_COMERCIAL troca a pasta (os testes usam a do exemplo).

    from empresa import perfil, nome_produto
    f"Aqui é {perfil()['responsavel']}, da {perfil()['nome']}. Conhece o {nome_produto('crm')}?"
"""
import json
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ / "exemplo" / "comercial"

PADRAO = {
    "nome": "",                     # como aparece nas mensagens: "Aqui é Ana, da {nome}"
    "responsavel": "",              # quem assina as mensagens e recebe o "Bom dia"
    "cidade": "",                   # só o nome ("Joinville"): entra nas mensagens ("Aqui é Ana, da X, de Joinville")
    "uf": "",                       # "SC"
    "regiao": "",                   # "Cidade e região": usado nas legendas e no perfil de cliente
    "instagram": "",                # "@perfil"
    "publico": "pequenas empresas",
    "hashtags": "#pequenosnegocios #empreendedorismo",
    "assinatura_legenda": "",       # frase fixa no fim das legendas do Instagram
    "exemplo": False,               # true = dados fictícios que vêm com o Ciello OS
}
NOMES_PADRAO = {"crm": "CRM", "site": "site", "hospedagem": "hospedagem"}


def _ler(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def pasta() -> Path:
    return Path(os.environ.get("CIELLO_COMERCIAL") or RAIZ / "comercial")


def perfil() -> dict:
    dados = _ler(pasta() / "empresa.json")
    return {**PADRAO, **{k: v for k, v in (dados or {}).items() if not k.startswith("_")}}


def produtos(caminho=None) -> dict:
    """Catálogo de comercial/produtos.json, por id (crm, site, hospedagem)."""
    dados = _ler(Path(caminho or pasta() / "produtos.json")) or {}
    try:
        return {p["id"]: p for p in dados["produtos"]}
    except (KeyError, TypeError):
        return {}


def nome_produto(id_="crm", caminho=None) -> str:
    return (produtos(caminho).get(id_) or {}).get("nome") or NOMES_PADRAO.get(id_, id_)


def apresentacao(assinatura=None, com_cidade=False) -> str:
    """"Aqui é Ana, da Aurora" (com_cidade: ", de Joinville") para abrir as mensagens."""
    p = perfil()
    quem = assinatura or p["responsavel"]
    cidade = f", de {p['cidade']}" if com_cidade and p["cidade"] else ""
    if p["nome"]:
        return f"Aqui é {quem + ', ' if quem else ''}da {p['nome']}{cidade}"
    return f"Aqui é {quem or 'do comercial'}{cidade}"


def quem_assina(assinatura=None) -> str:
    """"Ana, da Lumi" para fechar uma mensagem (sem perfil: só o nome, ou nada)."""
    p = perfil()
    quem = assinatura or p["responsavel"]
    return ", da ".join(x for x in (quem, p["nome"]) if x)


def responsavel() -> str:
    return perfil()["responsavel"]


def teste_gratis(id_="crm") -> str:
    """"São 30 dias grátis." quando o produto tem teste; senão, nada."""
    dias = (produtos().get(id_) or {}).get("teste_dias") or 0
    return f"São {dias} dias grátis." if dias else ""
