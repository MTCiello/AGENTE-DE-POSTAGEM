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
| `/conselho` | decisões de negócio (preço, oferta, onde investir) | Founder skills (conselho, CFO, painel de 100 compradores, marketing…) com os dados reais da Ciello |

Também dá para chamar um agente direto: "use o sdr para gerar 20 leads de odontologia em Xanxerê".

## Ver quem está trabalhando: Escritório Ciello

Painel próprio, sem Claude Code, VS Code ou Docker: só Python e o navegador.

```powershell
python central/escritorio/servidor.py          # abre http://127.0.0.1:3100
python central/escritorio/servidor.py --demo   # personagens animados de teste
```

- **Escritório em pixel art** (desenhado em código, sem imagens de terceiros): um personagem por agente, por setor (Pesquisa, Estúdio, Postagem, Análise & Anúncios, Comercial), com a I.V.A. coordenando.
  - **Trabalhando:** digitando, com o monitor aceso.
  - **Pensando:** balão "…".
  - **Precisa de você:** balão "!" e acenando.
  - **Pronto:** balão "✓".
  - **Erro:** balão "×".
- **Crescimento:** seguidores, alcance, tempo médio no reel (meta 6 s) e salvamentos (meta 1%), a partir de `metricas/`.
- **Comercial:** funil novo → contatado → respondeu → demo → proposta → cliente, com a conversão de cada etapa (`comercial/leads.csv`).
- **Anúncios:** investido, conversas, custo por conversa e custo por cliente (`anuncios/*.json`).
- **De onde vem o estado:**
  - as ferramentas avisam sozinhas (`radar`, `ganchos`, `sdr`, `relatorio`, `voz`, `mixar`);
  - os agentes do Claude avisam com `python central/status.py <agente> trabalhando|esperando|pronto "tarefa"`;
  - tudo cai em `estado/eventos.jsonl`, que fica fora do git.

## Próximas integrações candidatas (foco: métricas, anúncios e crescimento)

| Para | Como | Dependência |
|---|---|---|
| Resultado dos anúncios no painel | Meta Ads conectado ao Metricool (conectores `metaAds`/`facebookAds`) → `anuncios/*.json` | nenhuma nova |
| Atribuição de lead por anúncio ou post | Link do WhatsApp com texto de origem (`?text=Vim pelo anúncio X`) e a etapa no `sdr.py` | nenhuma |
| Agendar demonstrações | Link de agenda do Google Agenda (agendamento de horários) | nenhuma |
| Previsão de crescimento | Projeção de seguidores e clientes no painel a partir dos retratos semanais | nenhuma |
