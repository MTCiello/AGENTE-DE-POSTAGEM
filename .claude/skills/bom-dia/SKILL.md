---
description: Começo do dia com o chefe de gabinete - caixa, vendas, conteúdo, e-mails e as 3 prioridades.
disable-model-invocation: true
---

1. **chefe-gabinete**: `python central/briefing.py` e leia o resultado.
2. Em paralelo, conforme o briefing:
   - **caixa-entrada**: e-mails não lidos (triagem e rascunhos) e agenda de hoje e amanhã;
   - **financeiro**: se houver fatura atrasada, `python central/financeiro.py cobrar`;
   - **sucesso-cliente**: se houver pós-venda devido, `python central/financeiro.py posvenda`;
   - **sdr**: se houver follow-up, `python central/sdr.py hoje`.
3. Entregue ao Mateus **uma tela**: as 3 prioridades com o próximo passo pronto (links wa.me, rascunhos no Gmail, horários de demo) e, abaixo, o resto em até 5 linhas. Nada é enviado sem ele.

**Escritório (pixel-agents):** chame cada agente pelo nome. Com as equipes do Claude Code ligadas (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), crie **teammates** com o tipo e o nome do agente; sem equipes, use subagentes com a descrição começando pelo nome do agente (ex.: `financeiro: cobranças do dia`).
