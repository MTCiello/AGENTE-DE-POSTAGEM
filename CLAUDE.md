# Instruções

## Modelo e esforço por tarefa

Antes de executar, classifique a tarefa e delegue com o modelo e o esforço mais baratos que dão conta (tabela "Escolher modelo e esforço" em `.claude/agents/gerente.md`). Na dúvida, o mais leve.

- Leve (`haiku` · `low`): descrições, legendas, textos curtos, traduções, resumos, ajustes pequenos (cor de botão, renomear, typo), comandos simples.
- Média (`sonnet` · `medium`): roteiros, pesquisas com poucas buscas, relatórios, textos longos, código em poucos arquivos.
- Pesada (`opus` · `high`): arquitetura, depuração difícil, mudanças em muitos arquivos, análise e estratégia.

Use o agente especialista de `.claude/agents/` quando houver um para a etapa; senão, `general-purpose` com `model` e `effort`.
