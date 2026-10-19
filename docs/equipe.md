# Equipe de agentes da Ciello

Treze agentes especialistas em `.claude/agents/`, coordenados por cinco comandos em `.claude/skills/`. A sessão principal do Claude Code é o **coordenador**: recebe o pedido, divide entre os agentes, junta os resultados e pede a aprovação do Mateus.

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
| **chefe-gabinete** | laranja | Resumo do dia com as 3 prioridades, delega, cobra pendências, placar de sexta | `central/briefing.py` |
| **financeiro** | verde | Assinaturas, faturas, cobrança 3/7/14 dias, extrato OFX, caixa, MRR/churn/CAC/LTV | `central/financeiro.py` |
| **caixa-entrada** | azul | Triagem do e-mail, rascunhos, horários de demo | conectores Gmail e Google Agenda (só rascunho) |
| **sucesso-cliente** | rosa | FAQ, onboarding, NPS, pedido de avaliação no Google, risco de cancelamento | `financeiro.py posvenda`, `comercial/faq.md` |

Origem dos 4 novos: o reel "10 agentes de IA que toda empresa devia ter". Avaliação de cada um em `docs/qualificacao.md`.

## Comandos

| Comando | Quando | Quem trabalha |
|---|---|---|
| `/semana` | domingo | pesquisador → roteirista (3 em paralelo) → produtor-video + produtor-imagem (em paralelo) → postagem |
| `/comercial` | todo dia útil | sdr + closer em paralelo → lista única: enviar, responder, agendar |
| `/bom-dia` | todo dia de manhã | chefe-gabinete → caixa-entrada, financeiro, sucesso-cliente e sdr conforme o briefing → uma tela com as 3 prioridades |
| `/sexta` | sexta à tarde | placar (chefe-gabinete) + resumo financeiro + vigia de concorrentes (pesquisador) + voz do cliente → uma decisão para a semana |
| `/segunda` | segunda de manhã | analista + pesquisador em paralelo → gestor-anuncios |
| `/conselho` | decisões de negócio (preço, oferta, onde investir) | Founder skills (conselho, CFO, painel de 100 compradores, marketing…) com os dados reais da Ciello |

Também dá para chamar um agente direto: "use o sdr para gerar 20 leads de odontologia em Xanxerê".

## Escritório de agentes

O escritório é nosso: a tela pixel (`escritorio/`) começou como fork do [pixel-agents](https://github.com/pablodelucca/pixel-agents) v1.5.0 (MIT, © Pablo De Lucca; personagens baseados no [Metro City, de JIK-A-4](https://jik-a-4.itch.io/metrocity-free-topdown-character-pack)) e quem a alimenta é o núcleo em Python do Ciello OS (`central/escritorio/nucleo/`). **Não precisa de Node** e abre junto com o `Ciello.cmd`. A aparência é a mesma do pixel-agents (sprites, móveis e layout conferidos pixel a pixel com o 1.5.0); daqui para frente dá para mudar o que quiser (personagens, escritório, menus).

**Como funciona:** o núcleo acompanha toda sessão do Claude Code aberta na pasta do assistente (`~/.claude/projects/<pasta>`): cada sessão vira um personagem, cada ferramenta vira animação, subagentes aparecem ao lado de quem os chamou. Na primeira vez o layout da Ciello é instalado em `~/.ciello/escritorio/layout.json` (se você já usava o pixel-agents, o seu layout de `~/.pixel-agents` é trazido).

**Primeira vez:** a apresentação do escritório pergunta se pode instalar os **hooks** do Claude Code (o modo instantâneo). Aceite: o escritório adiciona `central/escritorio/gancho.py` aos eventos em `~/.claude/settings.json`, guarda uma cópia (`settings.json.ciello.backup`) e troca os hooks antigos do pixel-agents, se houver. Sem hooks também funciona, só que o "pedindo permissão" e o "terminou" são estimados pelo tempo.

**O layout da Ciello** (`central/escritorio/layout-ciello.json`, gerado por `gerar_layout.py` com os mesmos móveis e módulos do layout padrão):

| Sala | Áreas | Lugares |
|---|---|---|
| Esquerda | **Pesquisa** (em cima) e **Estúdio** (embaixo) | 4 estações |
| Meio | **Comercial**: mesa da equipe de vendas e sofás para demonstração | 4 cadeiras + sofás |
| Direita | **Análise & Anúncios** (em cima) e **Postagem** (embaixo) | 4 estações |

O editor **Layout** do escritório (engrenagem → Layout) continua funcionando para mudar o que quiser.

**Como os agentes aparecem:**
- **Com equipes ligadas** (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` no `.claude/settings.json` do seu PC): `/semana`, `/comercial` e `/segunda` criam teammates com o nome de cada agente (sdr, closer, pesquisador-mercado…). Cada um senta numa mesa com o nome em cima. As equipes são experimentais e gastam mais uso.
- **Sem equipes:** os agentes rodam como subagentes e aparecem como personagens ao lado do coordenador, com o balão mostrando "sdr: follow-ups do dia".
- **Animações:** digitando quando trabalha, "…" quando pede permissão, ✓ quando termina, passeio pelo escritório quando está livre.

## Ciello OS: o app inteiro numa área de trabalho

Clique duas vezes em **`Ciello.cmd`**. Abre numa janela própria do Edge (ou Chrome), sem barra de endereço, como um programa instalado.

- **O fundo da área de trabalho é o Escritório**, ao vivo, **em português** e no azul da Ciello, centralizado ao abrir. Ele roda dentro do próprio Ciello OS (`--sem-escritorio` desliga; aí o fundo mostra a logo).
- **Engrenagem na barra de tarefas:** os controles do escritório (**+ Agente**, **Layout**, **Configurações**, botões de zoom e os cartões dos agentes) ficam escondidos; a engrenagem mostra e esconde. Os menus usam as cores e as fontes da Ciello; os balões em cima dos personagens continuam em pixel.
- **+ Agente** abre o Claude Code numa janela nova, já na pasta do assistente; a sessão aparece no escritório sozinha.
- **Mover e dar zoom:** segure o **botão do meio (scroll)** e arraste para mover o escritório; **Ctrl + scroll** aproxima e afasta, entre **2x e 6x** (`ZOOM_MIN`/`ZOOM_MAX` em `escritorio/webview-ui/src/constants.ts`). O scroll sozinho também move. Menu Iniciar → **Centralizar escritório** volta para o meio.
- **Clicar num personagem do escritório abre a janela daquele agente**. Para isso funcionar, o agente precisa ter nome: teammate com o nome do agente (equipes ligadas) ou subagente com a descrição começando pelo nome (`sdr: follow-ups do dia`), como os comandos `/bom-dia`, `/comercial`, `/semana` já pedem. Clicar no coordenador abre a janela de quem está trabalhando com ele; sem ninguém, abre a Equipe.
- **Apps só no menu Iniciar** (o botão com a nuvem): Bom dia, Financeiro, Comercial, Conteúdo e Instagram, Tendências, Concorrentes, Anúncios, Equipe, Atividade e Verificação, além da equipe de agentes. Não há ícones na área de trabalho.
- **Barra de tarefas:** Iniciar, **Mostrar escritório** (minimiza as janelas; clicar de novo traz de volta), janelas abertas, agentes trabalhando, notificações e relógio.
- **Quando um agente começa a trabalhar**, aparece um aviso no canto e a janela dele abre sozinha (desligue no menu Iniciar).
- **Botões das janelas** (ex.: "Cobranças do dia") rodam a ferramenta e abrem uma janela com a saída ao vivo. Só rodam as ações da lista fixa do `servidor.py`, e só a partir do próprio app.
- **Janelas:** arrastar pela barra de título, redimensionar pelas bordas e cantos, duplo clique para maximizar, arrastar até a borda esquerda/direita para ocupar metade da tela (até o topo maximiza). A posição de cada janela fica salva.

**Português:** os textos da tela estão em português no próprio código (`escritorio/webview-ui/src`). Só as mensagens entre a tela e o servidor continuam em inglês ("Reading", "Subtask:"...), porque o código depende delas; na tela elas aparecem traduzidas (`src/office/statusPtBr.ts`).

**Como o clique chega no app:** a tela do escritório roda dentro do Ciello OS, no mesmo endereço (`/escritorio/`). O código da Ciello na tela (`escritorio/webview-ui/src/ciello/`) aprende o nome de cada agente e, quando um personagem é clicado, avisa a área de trabalho, que abre a janela daquele agente. A engrenagem e o "Centralizar escritório" chegam pelo mesmo caminho.

![Ciello OS](img/ciello-os-escritorio-fundo-e-apps.png)

Interface em `central/escritorio/web/` (HTML, CSS e JavaScript sem dependências; fontes Oswald e Inter, licença OFL).

## Próximas integrações candidatas (foco: métricas, anúncios e crescimento)

| Para | Como | Dependência |
|---|---|---|
| Resultado dos anúncios no painel | Meta Ads conectado ao Metricool (conectores `metaAds`/`facebookAds`) → `anuncios/*.json` | nenhuma nova |
| Atribuição de lead por anúncio ou post | Link do WhatsApp com texto de origem (`?text=Vim pelo anúncio X`) e a etapa no `sdr.py` | nenhuma |
| Agendar demonstrações | feito: caixa-entrada sugere horários (`suggest_time`) e prepara o convite | conector Google Agenda |
| Previsão de crescimento | Projeção de seguidores e clientes no painel a partir dos retratos semanais | nenhuma |

## Funções futuras

- **Agentes com mesa e nome no escritório:** ligar as equipes do Claude Code (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` no `.claude/settings.json` do PC). Até lá, os agentes aparecem como ajudantes do coordenador, com o nome no balão.
- **Resultado dos anúncios no painel:** Meta Ads conectado ao Metricool, alimentando `anuncios/`.
- **Atribuição de lead por anúncio ou post:** texto de origem no link do WhatsApp.
- **Recepcionista por voz** (atender ligação 24h): precisa de telefonia paga (ex.: número virtual + agente de voz). Fica para quando houver investimento.
- **Atendimento automático 24h no WhatsApp** (suporte sem o Mateus): exige a API oficial do WhatsApp (paga por conversa) e um servidor ligado. Hoje o sucesso-cliente prepara as respostas e o Mateus envia.
- **Contratação** (vaga, triagem, entrevista): quando a Ciello contratar a 1ª pessoa.
- **Previsão de crescimento** no painel, a partir dos retratos semanais.
- **Telas reais do CIELLO CRM** no plano-sequência, a partir de prints.

