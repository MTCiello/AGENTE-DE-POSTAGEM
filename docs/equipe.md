# Equipe de agentes da Ciello

Nove agentes especialistas em `.claude/agents/`, coordenados por três comandos em `.claude/skills/`. A sessão principal do Claude Code é o **coordenador**: recebe o pedido, divide entre os agentes, junta os resultados e pede a aprovação do Mateus.

| Agente | Cor | Função | Ferramentas principais |
|---|---|---|---|
| **pesquisador-mercado** | ciano | Tendências dos 5 pilares, concorrentes e biblioteca de ganchos | `central/radar.py`, `central/ganchos.py`, Metricool (concorrentes), busca web |
| **roteirista** | — | Pauta → roteiros com gancho validado e fontes | `roteiros/*.json`, `ganchos.py modelos` |
| **produtor-video** | vermelho | Narração, Remotion (I.V.A. ou clone), montagem final | `voz.py`, `render.mjs`, `CloneReel`, `mixar.py`, notebook do Kaggle |
| **produtor-imagem** | laranja | Capas, carrosséis, criativos de anúncio | `capa.mjs`, stills no Remotion |
| **postagem** | verde | Legenda, horário, agendamento, histórico | Metricool |
| **analista** | roxo | Retrato semanal, relatório, aprendizado | `relatorio.py`, `metricas/` |
| **sdr** | azul | Leads, qualificação, 1ª mensagem, follow-up | `central/sdr.py`, Google Maps (gosom), Vibe Prospecting (custo aprovado) |
| **closer** | amarelo | Objeções, demonstração, proposta, agenda | Gamma, Gmail (rascunho), Google Agenda |
| **gestor-anuncios** | rosa | Plano e leitura de anúncios Meta | relatório do analista, criativos dos produtores |

## Comandos

| Comando | Quando | Quem trabalha |
|---|---|---|
| `/semana` | domingo | pesquisador → roteirista (3 em paralelo) → produtor-video + produtor-imagem (em paralelo) → postagem |
| `/comercial` | todo dia útil | sdr + closer em paralelo → lista única: enviar, responder, agendar |
| `/segunda` | segunda de manhã | analista + pesquisador em paralelo → gestor-anuncios |

Também dá para chamar um agente direto: "use o sdr para gerar 20 leads de odontologia em Xanxerê".

## Ver quem está trabalhando: pixel-agents

O [pixel-agents](https://github.com/pablodelucca/pixel-agents) (MIT) mostra cada sessão do Claude Code como um personagem num escritório em pixel art. A animação muda conforme o agente escreve, lê ou roda comandos, e os subagentes aparecem como personagens ligados ao coordenador. Aparece um balão quando o agente precisa de aprovação.

**Instalar no PC (funciona com o Claude Code local, não com a sessão na nuvem):**
1. VS Code 1.105 ou mais novo e Claude Code instalado (`npm install -g @anthropic-ai/claude-code`).
2. Extensões do VS Code → instalar **Pixel Agents** (`pablodelucca.pixel-agents`).
3. Abrir a pasta `agente-de-postagem` no VS Code → painel **Pixel Agents** → **+ Agent** (abre o Claude Code já ligado ao escritório).
4. Rodar `/semana`, `/comercial` ou `/segunda`: cada agente chamado aparece como um personagem.

Sem VS Code: `npx pixel-agents` na pasta do projeto abre o escritório no navegador (`http://127.0.0.1:3100`).

**Montar o escritório da Ciello:** no editor **Layout**, crie áreas com o nome de cada setor (Pesquisa, Estúdio, Postagem, Comercial, Análise) e exporte o layout em JSON para `.claude/pixel-agents-layout.json`, para não perder.

> Equipes com "teammates" (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) também aparecem no pixel-agents, cada um como sessão completa. São experimentais e gastam bem mais uso, então começamos com subagentes.

## Próximas integrações candidatas (GitHub primeiro, a verificar)

| Para | Repositório | Por quê |
|---|---|---|
| Agendar demonstrações | [Cal.com](https://github.com/calcom/cal.com) | Link de agenda no WhatsApp; o lead escolhe o horário e cai no Google Agenda |
| Caixa de entrada única (Instagram DM + WhatsApp oficial) | [Chatwoot](https://github.com/chatwoot/chatwoot) | Comentário → DM e respostas num lugar só, via APIs oficiais |
| Validar e-mail antes de prospectar | [Reacher](https://github.com/reacherhq/check-if-email-exists) | Evita e-mail inválido e queda de reputação do domínio |
| Cadência de e-mail B2B | [listmonk](https://github.com/knadh/listmonk) | Sequências de e-mail com descadastro (LGPD) |
| Leads por CNPJ (cidade + CNAE) | [minha-receita](https://github.com/cuducos/minha-receita) | Base aberta da Receita para completar o Google Maps |
