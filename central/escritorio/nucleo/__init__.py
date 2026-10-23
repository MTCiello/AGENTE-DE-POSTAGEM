"""Núcleo do escritório da Ciello: o servidor do escritório pixel em Python.

Fala exatamente o protocolo da tela do escritório (fork MIT do pixel-agents em escritorio/), de modo que a
aparência e os movimentos ficam idênticos, sem Node no PC:

  png.py           decodifica os PNGs dos sprites (só biblioteca padrão)
  ativos.py        personagens, pets, pisos, paredes, tapetes, móveis e layout padrão
  persistencia.py  configurações, agentes, lugares e layout em ~/.ciello/escritorio
  agentes.py       estado de cada agente, o laço de eventos e os temporizadores
  transcricao.py   lê as linhas do JSONL das sessões do Claude Code
  vigia.py         acha sessões novas, sub-agentes e colegas de equipe
  ganchos.py       eventos dos hooks do Claude Code (modo instantâneo)
  websocket.py     WebSocket mínimo (RFC 6455)
  sala.py          junta tudo: o que a tela pede e o que ela recebe
"""
