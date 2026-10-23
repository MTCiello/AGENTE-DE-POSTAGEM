---
description: Ciclo semanal de conteúdo da empresa com a equipe de agentes (pesquisa → roteiro → vídeo e imagem → postagem).
argument-hint: "[tema opcional ou 'rascunho']"
disable-model-invocation: true
---

Coordene a equipe para produzir e agendar os 3 reels da próxima semana (seg/qua/sex), seguindo `AGENTE.md`. Pedido extra do usuário: $ARGUMENTS

1. **pesquisador-mercado**: radar da semana, ganchos atualizados e 3 temas com fonte oficial.
2. Mostre os 3 temas ao usuário e espere o ok (ou troque o que ele pedir).
3. **roteirista**: os 3 roteiros. Um subagente por roteiro, em paralelo.
4. Em paralelo, para cada roteiro:
   - **produtor-video**: narração, render e montagem final;
   - **produtor-imagem**: capa.
5. **postagem**: legendas e agendamento no Metricool (rascunho se faltar algo).
6. Resumo final em uma tabela: tema, gancho, horário, status, link do Metricool.

**Escritório (pixel-agents):** chame cada agente pelo nome. Com as equipes do Claude Code ligadas (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), crie **teammates** com o tipo e o nome do agente (ex.: teammate `sdr` do tipo `sdr`): cada um ganha personagem e mesa com o nome. Sem equipes, use subagentes com a descrição começando pelo nome do agente (ex.: `sdr: follow-ups do dia`), que aparece no balão do personagem.
