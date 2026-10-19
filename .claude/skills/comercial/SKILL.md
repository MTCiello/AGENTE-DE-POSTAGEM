---
description: Rotina comercial do dia com o SDR e o closer (novos leads, follow-ups, respostas e demos).
argument-hint: "[segmento ou cidade opcional]"
disable-model-invocation: true
---

Rotina comercial do dia da Ciello. Foco pedido pelo Mateus: $ARGUMENTS

Em paralelo:
- **sdr**:
  - follow-ups de hoje (`python central/sdr.py hoje`);
  - se houver menos de 15 leads `novo`, gerar mais (consultas → buscar → qualificar) no segmento ou cidade pedidos;
  - `abordar --top 15`, revisando à mão as 5 melhores mensagens.
- **closer**: para cada lead em `respondeu`, `demo` ou `proposta`, a próxima ação com a mensagem pronta e o rascunho de proposta ou convite quando fizer sentido.

No fim, entregue ao Mateus uma lista única do dia: **enviar agora** (links wa.me), **responder** (closer), **agendar** (demos). Nada é enviado sem ele.
