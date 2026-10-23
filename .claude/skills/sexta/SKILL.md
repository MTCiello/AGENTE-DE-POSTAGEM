---
description: Revisão de sexta - placar da semana, financeiro, concorrentes e a decisão da próxima semana.
disable-model-invocation: true
---

Em paralelo:
- **gerente**: `python central/briefing.py --semana` (placar).
- **financeiro**: `python central/financeiro.py resumo` (MRR, churn, CAC, caixa e previsão) e o que não bate.
- **pesquisador-mercado**: `python central/vigia.py checar` (preço, plano e oferta dos concorrentes) + anúncios ativos deles pelo link da Biblioteca de Anúncios.
- **sucesso-cliente**: o que os clientes elogiaram, pediram e reclamaram na semana.

Depois, o **gerente** fecha em 10 linhas: o que melhorou, o que piorou, o que o concorrente mudou e **uma** decisão para a próxima semana. Se a decisão for grande (preço, contratação, verba de anúncio), rode `/conselho` antes.

**Escritório (pixel-agents):** chame cada agente pelo nome (teammates com o nome do agente ou subagentes com a descrição começando pelo nome).
