"""Relatório semanal do @ciellotec a partir dos retratos em metricas/AAAA-MM-DD.json.

O Metricool grátis só guarda 30 dias. Por isso, toda semana o agente salva um retrato
(passo "Analista" do AGENTE.md) e este script compara com a semana anterior.

Uso:
  python central/relatorio.py            # usa o retrato mais recente
  python central/relatorio.py --data 2026-10-19
Saída: metricas/relatorio-AAAA-MM-DD.md
"""
import argparse
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "metricas"
# Metas iniciais do docs/app-comercial.md, seção 6
META_TEMPO_S = 6.0  # ~ metade de um reel de 20–28 s, considerando quem sai cedo
META_SALVA = 0.01  # salvamentos por alcance
META_COMPART = 0.01
DIAS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]


def carregar(data=None):
    retratos = sorted(PASTA.glob("20??-??-??.json"))
    if not retratos:
        raise SystemExit("Nenhum retrato em metricas/. Salve um com o passo Analista do AGENTE.md.")
    if data:
        retratos = [r for r in retratos if r.stem <= data]
    atual = json.loads(retratos[-1].read_text(encoding="utf-8"))
    anterior = json.loads(retratos[-2].read_text(encoding="utf-8")) if len(retratos) > 1 else None
    return atual, anterior


def delta(a, b):
    if b is None:
        return ""
    d = a - b
    return f" ({'+' if d >= 0 else ''}{d:g})"


def avaliar(r):
    alc = r.get("alcance") or 0
    sinais = []
    sinais.append("✅ prende" if r.get("tempo_medio_s", 0) >= META_TEMPO_S else "⚠️ gancho fraco")
    if alc and r.get("salvamentos", 0) / alc >= META_SALVA:
        sinais.append("✅ salvam")
    if alc and r.get("compartilhamentos", 0) / alc >= META_COMPART:
        sinais.append("✅ compartilham")
    return " · ".join(sinais)


def horario(mh: dict):
    """Horário principal (o que mais aparece no topo) e horário de teste (o 2º pico, fora do principal ±2h)."""
    conta = {}
    for horas in mh.values():
        for i, h in enumerate(horas):
            conta[h] = conta.get(h, 0) + (3 - i)
    ordem = sorted(conta, key=lambda h: -conta[h])
    principal = ordem[0]
    teste = next((h for h in ordem[1:] if abs(h - principal) > 2), None)
    return principal, teste


def montar(atual, anterior):
    p, q = atual["perfil"], (anterior or {}).get("perfil", {})
    reels = sorted(atual.get("reels", []), key=lambda r: -(r.get("views") or 0))
    L = [f"# Relatório @ciellotec — {atual['data']}", "",
         f"Período: {atual['periodo']['de']} a {atual['periodo']['ate']} · fonte: {atual.get('fonte', '')}", "",
         "## Perfil", "",
         f"- Seguidores: **{p['seguidores']}**{delta(p['seguidores'], q.get('seguidores'))} (início do período: {p.get('seguidores_inicio', '?')})",
         f"- Alcance: **{p.get('alcance', 0)}**{delta(p.get('alcance', 0), q.get('alcance'))}",
         f"- Contas que interagiram: **{p.get('contas_engajadas', 0)}**{delta(p.get('contas_engajadas', 0), q.get('contas_engajadas'))}",
         f"- Posts no período: **{p.get('posts', 0)}**", ""]
    if reels:
        L += ["## Reels", "", "| Data | Gancho | Views | Alcance | Tempo médio | Salv. | Comp. | Leitura |", "|---|---|---|---|---|---|---|---|"]
        for r in reels:
            L.append(f"| {r['data']} | {r['gancho'][:60]} | {r.get('views', 0)} | {r.get('alcance', 0)} | {r.get('tempo_medio_s', 0):.1f} s | "
                     f"{r.get('salvamentos', 0)} | {r.get('compartilhamentos', 0)} | {avaliar(r)} |")
        melhor_tempo = max(reels, key=lambda r: r.get("tempo_medio_s", 0))
        L += ["", f"- Mais visto: **{reels[0]['gancho'][:70]}** ({reels[0].get('views', 0)} views)",
              f"- Prendeu mais: **{melhor_tempo['gancho'][:70]}** ({melhor_tempo.get('tempo_medio_s', 0):.1f} s)"]
        sem_salvar = all(not r.get("salvamentos") for r in reels)
        fracos = sum(r.get("tempo_medio_s", 0) < META_TEMPO_S for r in reels)
        L += ["", "## O que mudar", ""]
        if fracos:
            L.append(f"- {fracos} de {len(reels)} reels perdem a pessoa antes de {META_TEMPO_S:g} s: gancho na tela no 1º segundo, até 9 palavras, "
                     "e um formato do topo de `python central/ganchos.py ranking`.")
        if sem_salvar:
            L.append("- Ninguém salvou: troque o CTA de comentário por **\"Salva pra testar depois\"** e entregue algo que vale guardar (lista, comandos, passo a passo).")
        L.append(f"- Repetir o que prendeu mais (\"{melhor_tempo['gancho'][:50]}…\"): cenário real do cliente + produto resolvendo.")
    if atual.get("melhor_horario"):
        principal, teste = horario(atual["melhor_horario"])
        L += ["", "## Horário", "",
              f"- Principal: **{principal}h** (topo em {sum(v[0] == principal for v in atual['melhor_horario'].values())} de 7 dias).",
              f"- Teste: **{teste}h** em 1 post por semana, para comparar com o principal." if teste is not None else "",
              "- Com poucos seguidores, o Metricool mostra o hábito do público em geral. Confirme com os seus próprios posts depois de 4 semanas."]
    if atual.get("obs"):
        L += ["", f"_Obs.: {atual['obs']}_"]
    return "\n".join(l for l in L if l is not None) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data")
    a = ap.parse_args()
    atual, anterior = carregar(a.data)
    saida = PASTA / f"relatorio-{atual['data']}.md"
    saida.write_text(montar(atual, anterior), encoding="utf-8")
    print(saida.read_text(encoding="utf-8"))


if __name__ == "__main__":
    from status import trabalhando
    with trabalhando("analista", "relatório semanal"):
        main()
