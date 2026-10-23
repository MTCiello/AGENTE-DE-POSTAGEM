---
description: Rotina comercial do dia com o SDR e o closer (novos leads, follow-ups, respostas e demos).
argument-hint: "[segmento ou cidade opcional]"
disable-model-invocation: true
---

Rotina comercial do dia da empresa. Foco pedido pelo usuário: $ARGUMENTS

Em paralelo:
- **sdr**:
  - follow-ups de hoje (`python central/sdr.py hoje`);
  - se houver menos de 15 leads `novo`, gerar mais (consultas → buscar → qualificar) no segmento ou cidade pedidos;
  - `abordar --top 15`, revisando à mão as 5 melhores mensagens.
- **closer**: para cada lead em `respondeu`, `demo` ou `proposta`, a próxima ação com a mensagem pronta e o rascunho de proposta ou convite quando fizer sentido.

No fim, entregue ao usuário uma lista única do dia: **enviar agora** (links wa.me), **responder** (closer), **agendar** (demos). Nada é enviado sem ele.

**Escritório (pixel-agents):** chame cada agente pelo nome. Com as equipes do Claude Code ligadas (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), crie **teammates** com o tipo e o nome do agente (ex.: teammate `sdr` do tipo `sdr`): cada um ganha personagem e mesa com o nome. Sem equipes, use subagentes com a descrição começando pelo nome do agente (ex.: `sdr: follow-ups do dia`), que aparece no balão do personagem.
