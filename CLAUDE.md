# Instruções

## Modelo e esforço por tarefa

Antes de executar, classifique a tarefa e delegue com o modelo e o esforço mais baratos que entregam a qualidade de sempre (tabela "Escolher modelo e esforço" em `.claude/agents/gerente.md`). Economia nunca vale um resultado pior para o cliente.

- Leve (`haiku` · `low`): só o que é interno e fácil de conferir: resumos, triagem, ajustes pequenos (cor de botão, renomear, typo), comandos simples.
- Média (`sonnet` · `low` a `high`): tudo que vai para cliente ou público ou mexe com dinheiro (legendas, mensagens, cobranças), roteiros, pesquisas, relatórios, código em poucos arquivos.
- Pesada (`opus` · `high`): arquitetura, depuração difícil, mudanças em muitos arquivos, análise e estratégia.
- Na dúvida: interno, o mais leve; o resto, o de cima. Resultado que não passa na conferência é refeito um nível acima.

Use o agente especialista de `.claude/agents/` quando houver um para a etapa; senão, `general-purpose` com `model` e `effort`.
