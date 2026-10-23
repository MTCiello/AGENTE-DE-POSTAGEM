# Equipe de agentes da empresa

Treze agentes especialistas em `.claude/agents/`, coordenados por cinco comandos em `.claude/skills/`. A sessão principal do Claude Code é o **coordenador**: recebe o pedido, divide entre os agentes, junta os resultados e pede a aprovação do usuário.

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
| **gerente** | amarelo | O único coordenador: recebe o seu objetivo, monta a esteira e delega; resumo do dia, placar de sexta e cobrança de pendências (clique nele no escritório) | `central/briefing.py` |
| **financeiro** | verde | Assinaturas, faturas, cobrança 3/7/14 dias, extrato OFX, caixa, MRR/churn/CAC/LTV | `central/financeiro.py` |
| **caixa-entrada** | azul | Triagem do e-mail, rascunhos, horários de demo | conectores Gmail e Google Agenda (só rascunho) |
| **sucesso-cliente** | rosa | FAQ, onboarding, NPS, pedido de avaliação no Google, risco de cancelamento | `financeiro.py posvenda`, `comercial/faq.md` |

Origem dos 4 novos: o reel "10 agentes de IA que toda empresa devia ter". Avaliação de cada um em `docs/qualificacao.md`.

## Comandos

| Comando | Quando | Quem trabalha |
|---|---|---|
| `/semana` | domingo | pesquisador → roteirista (3 em paralelo) → produtor-video + produtor-imagem (em paralelo) → postagem |
| `/comercial` | todo dia útil | sdr + closer em paralelo → lista única: enviar, responder, agendar |
| `/bom-dia` | todo dia de manhã | gerente → caixa-entrada, financeiro, sucesso-cliente e sdr conforme o briefing → uma tela com as 3 prioridades |
| `/sexta` | sexta à tarde | placar (gerente) + resumo financeiro + vigia de concorrentes (pesquisador) + voz do cliente → uma decisão para a semana |
| `/segunda` | segunda de manhã | analista + pesquisador em paralelo → gestor-anuncios |
| `/conselho` | decisões de negócio (preço, oferta, onde investir) | Founder skills (conselho, CFO, painel de 100 compradores, marketing…) com os dados reais da empresa |

**Modelo e esforço por tarefa:** o Gerente classifica cada etapa e escolhe o modelo e o esforço antes de delegar, equilibrando qualidade e economia: `haiku · low` só para o que é interno e fácil de conferir (resumo, triagem, trocar a cor de um botão); `sonnet` (esforço `low` a `high`) para tudo que vai para cliente ou público ou mexe com dinheiro, roteiros, pesquisa e código pequeno; `opus · high` para arquitetura, bug difícil, mudanças grandes e estratégia. Resultado que não passa na conferência do Gerente é refeito um nível acima. A tabela está em `.claude/agents/gerente.md`, cada agente tem um padrão no cabeçalho (`model`, `effort`) e a caixa de objetivos abre o Gerente no `sonnet`.

Também dá para chamar um agente direto: "use o sdr para gerar 20 leads de odontologia em Xanxerê".

## Escritório de agentes

O escritório é nosso: a tela pixel (`escritorio/`) começou como fork do [pixel-agents](https://github.com/pablodelucca/pixel-agents) v1.5.0 (MIT, © Pablo De Lucca; personagens baseados no [Metro City, de JIK-A-4](https://jik-a-4.itch.io/metrocity-free-topdown-character-pack)) e quem a alimenta é o núcleo em Python do Ciello OS (`central/escritorio/nucleo/`). **Não precisa de Node** e abre junto com o `Ciello.cmd`. A aparência é a mesma do pixel-agents (sprites, móveis e layout conferidos pixel a pixel com o 1.5.0); daqui para frente dá para mudar o que quiser (personagens, escritório, menus).

**Como funciona:** o núcleo acompanha toda sessão do Claude Code aberta na pasta do assistente (`~/.claude/projects/<pasta>`): cada sessão vira um personagem, cada ferramenta vira animação, subagentes aparecem ao lado de quem os chamou. Na primeira vez o layout padrão é instalado em `~/.ciello/escritorio/layout.json` (se você já usava o pixel-agents, o seu layout de `~/.pixel-agents` é trazido).

**Primeira vez:** a apresentação do escritório pergunta se pode instalar os **hooks** do Claude Code (o modo instantâneo). Aceite: o escritório adiciona `central/escritorio/gancho.py` aos eventos em `~/.claude/settings.json`, guarda uma cópia (`settings.json.ciello.backup`) e troca os hooks antigos do pixel-agents, se houver. Sem hooks também funciona, só que o "pedindo permissão" e o "terminou" são estimados pelo tempo.

**O layout padrão** (`central/escritorio/layout-padrao.json`, gerado por `gerar_layout.py`; entra só quando ainda não existe um layout seu, e um layout próprio vem no .zip de dados como `escritorio/layout.json`):

| Sala | Áreas | Lugares |
|---|---|---|
| Em cima, à esquerda | **Gerente** (e a sessão do Claude Code em que você conversa) | mesa de reunião |
| Em cima, à direita | **Produtor Social**: pesquisa, roteiro, vídeo, imagem, postagem e análise | estações |
| Embaixo, à esquerda | **Comercial**: financeiro, anúncios e caixa de entrada | estações |
| Embaixo, à direita | **Vendas**: SDR, closer e sucesso do cliente | estações |

Um layout seu precisa ter salas com esses quatro nomes, para cada agente achar a dele.

O editor **Layout** do escritório (engrenagem → Layout) continua funcionando para mudar o que quiser.

**Como os agentes aparecem:**
- **Os 13 moram no escritório**, cada um na sua sala (Gerente, Produtor Social, Comercial, Vendas), com o nome em cima ao passar o mouse. Parados, andam, conversam e descansam na mesa.
- **Quando o Claude Code chama um agente** (por `/comercial`, `/semana`, "use o sdr para..." ou pela janela dele), é o próprio personagem que vai para o PC e trabalha. A sessão do Claude Code (o coordenador) também aparece, sentada e digitando.
- **Equipes do Claude Code** (opcional, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`): teammates com nome próprio continuam virando personagens separados. São experimentais e gastam mais uso.
- **Animações:** digitando quando trabalha, "…" quando pede permissão, ✓ quando termina, passeio pelo escritório quando está livre.

## Ciello OS: o app inteiro numa área de trabalho

Clique duas vezes em **`Ciello.cmd`**. Abre numa janela própria do Edge (ou Chrome), sem barra de endereço, como um programa instalado.

- **O fundo da área de trabalho é o Escritório**, ao vivo, **em português** e no azul do Ciello OS, centralizado ao abrir. Ele roda dentro do próprio Ciello OS (`--sem-escritorio` desliga; aí o fundo mostra a logo).
- **Engrenagem na barra de tarefas:** os controles do escritório (**+ Agente**, **Layout**, **Configurações**, botões de zoom e os cartões dos agentes) ficam escondidos; a engrenagem mostra e esconde. Os menus usam as cores e as fontes do Ciello OS; os balões em cima dos personagens continuam em pixel.
- **Terminal do Claude dentro do OS:** o ícone de terminal na barra de tarefas (e o **+ Agente** do escritório) abre uma janela com o Claude Code rodando na pasta do assistente (`central/escritorio/terminal.py`, xterm.js; no Windows usa o `pywinpty`). Cada janela é um processo; fechar a janela encerra.
- **Os agentes moram no escritório** (`central/escritorio/nucleo/residentes.py`): os 13 de `.claude/agents/` ficam no escritório, cada um na sua área. Parados, andam, conversam entre si e descansam na mesa; quando o Claude Code chama um deles (`subagent_type`, ou descrição "sdr: ..."), é ele que vai para o PC e trabalha, e volta para a rotina quando termina.
- **Iniciar pela janela do agente:** escreva a tarefa (ou clique numa sugestão) e **Iniciar no Claude Code**: abre o terminal com "Use o subagente <agente> para: <tarefa>".
- **Mover e dar zoom:** segure o **botão do meio (scroll)** e arraste para mover o escritório; **Ctrl + scroll** aproxima e afasta, entre **2x e 6x** (`ZOOM_MIN`/`ZOOM_MAX` em `escritorio/webview-ui/src/constants.ts`). O scroll sozinho também move. Menu Iniciar → **Centralizar escritório** volta para o meio.
- **Clicar num personagem do escritório abre a janela daquele agente**. Para isso funcionar, o agente precisa ter nome: teammate com o nome do agente (equipes ligadas) ou subagente com a descrição começando pelo nome (`sdr: follow-ups do dia`), como os comandos `/bom-dia`, `/comercial`, `/semana` já pedem. Clicar no coordenador abre a janela de quem está trabalhando com ele; sem ninguém, abre a Equipe.
- **Apps só no menu Iniciar** (o botão com a nuvem): Bom dia, Financeiro, Comercial, Conteúdo e Instagram, Tendências, Concorrentes, Anúncios, Equipe, Atividade e Verificação, além da equipe de agentes. Não há ícones na área de trabalho.
- **Barra de tarefas:** Iniciar, **Mostrar escritório** (minimiza as janelas; clicar de novo traz de volta), janelas abertas, agentes trabalhando, notificações e relógio.
- **Quando um agente começa a trabalhar**, aparece um aviso no canto e a janela dele abre sozinha (desligue no menu Iniciar).
- **Botões das janelas** (ex.: "Cobranças do dia") rodam a ferramenta e abrem uma janela com a saída ao vivo. Só rodam as ações da lista fixa do `servidor.py`, e só a partir do próprio app.
- **Menu Iniciar por objetivo:** Criar, Vender e Gerir. Escreva um objetivo na caixa do menu e aperte Enter: abre o Claude Code como coordenador, que monta o plano, distribui o trabalho entre os agentes (cada um aparece trabalhando no escritório) e pede a sua aprovação antes de publicar, enviar ou gastar.
- **Objetivos e esteiras:** objetivos livres, pedidos recentes e esteiras prontas (Semana de conteúdo, Um vídeo sobre um tema, Prospecção do dia, Bom dia, Campanha de anúncio, Fechamento da semana) com a cadeia de agentes ao vivo.
- **Estúdio de Vídeo** (`central/estudio_video.py`, [HyperFrames](https://github.com/heygen-com/hyperframes), Apache-2.0): escreva um roteiro (gancho, itens, chamada) ou use um da agenda, escolha o modelo (escuro ou claro) e clique **Gerar vídeo**. A narração usa a voz do Estúdio de Voz; o vídeo sai em 1080x1920 com títulos animados, legenda sincronizada com a fala, a marca e a trilha, em `midia/estudio/`. **Usar como vídeo final** copia para `midia/final/`. Funciona sem o Claude.
- **Estúdio de Voz** (`central/escritorio/estudio_voz.py`): gravar a sua voz pelo microfone (fica em `marca/minha-voz.wav`, fora do git), testar frases com o Kokoro (vozes prontas), o Chatterbox (a sua voz clonada) ou o VoiceStudio, e escolher a voz dos vídeos (`estado/voz.json`, que o `voz.py` usa quando não recebe `--motor`). O **VoiceStudio** (AGPL-3.0) roda como programa separado: o assistente fala com a API local dele (MCP em `127.0.0.1:3900/mcp/`) e só usa o áudio gerado.
- **Funciona sem o Claude** (`central/escritorio/operacao.py`): sem tokens, o OS continua mostrando os números e operando o dia a dia. **Financeiro:** cadastrar, editar, cancelar e reativar cliente, gerar faturas, dar baixa, importar o extrato do banco (OFX/CSV), lançar receita e despesa, classificar lançamento, caixa, NPS, e as mensagens de cobrança e pós-venda prontas com o link do WhatsApp. **Comercial:** lead que chegou sozinho, funil com mudança de etapa, follow-ups e 1ª abordagem prontos, busca de leads, anotação, lista com busca e filtro, importar planilha e exportar para o CRM; um lead que vira cliente já é cadastrado no Financeiro. **Conteúdo:** anotar à mão os números do Instagram. **Anúncios:** registrar campanha. Os formulários chamam as mesmas ferramentas da linha de comando (`financeiro.py`, `sdr.py`), cada um com uma lista fixa de campos; nada é enviado a ninguém (você abre o WhatsApp, revisa e envia).
- **Janelas:** arrastar pela barra de título, redimensionar pelas bordas e cantos, duplo clique para maximizar, arrastar até a borda esquerda/direita para ocupar metade da tela (até o topo maximiza). A posição de cada janela fica salva.

**Português:** os textos da tela estão em português no próprio código (`escritorio/webview-ui/src`). Só as mensagens entre a tela e o servidor continuam em inglês ("Reading", "Subtask:"...), porque o código depende delas; na tela elas aparecem traduzidas (`src/office/statusPtBr.ts`).

**Como o clique chega no app:** a tela do escritório roda dentro do Ciello OS, no mesmo endereço (`/escritorio/`). O código do Ciello OS na tela (`escritorio/webview-ui/src/ciello/`) aprende o nome de cada agente e, quando um personagem é clicado, avisa a área de trabalho, que abre a janela daquele agente. A engrenagem e o "Centralizar escritório" chegam pelo mesmo caminho.

![Ciello OS](img/visao-geral.png)

Interface em `central/escritorio/web/` (HTML, CSS e JavaScript sem dependências; fontes Oswald e Inter, licença OFL).

## Próximas integrações candidatas (foco: métricas, anúncios e crescimento)

| Para | Como | Dependência |
|---|---|---|
| Resultado dos anúncios no painel | Meta Ads conectado ao Metricool (conectores `metaAds`/`facebookAds`) → `anuncios/*.json` | nenhuma nova |
| Atribuição de lead por anúncio ou post | Link do WhatsApp com texto de origem (`?text=Vim pelo anúncio X`) e a etapa no `sdr.py` | nenhuma |
| Agendar demonstrações | feito: caixa-entrada sugere horários (`suggest_time`) e prepara o convite | conector Google Agenda |
| Previsão de crescimento | Projeção de seguidores e clientes no painel a partir dos retratos semanais | nenhuma |

## Funções futuras

- **Resultado dos anúncios no painel:** Meta Ads conectado ao Metricool, alimentando `anuncios/`.
- **Atribuição de lead por anúncio ou post:** texto de origem no link do WhatsApp.
- **Recepcionista por voz** (atender ligação 24h): precisa de telefonia paga (ex.: número virtual + agente de voz). Fica para quando houver investimento.
- **Atendimento automático 24h no WhatsApp** (suporte sem o usuário): exige a API oficial do WhatsApp (paga por conversa) e um servidor ligado. Hoje o sucesso-cliente prepara as respostas e o usuário envia.
- **Contratação** (vaga, triagem, entrevista): quando a empresa contratar a 1ª pessoa.
- **Previsão de crescimento** no painel, a partir dos retratos semanais.
- **Telas reais do CRM** no plano-sequência, a partir de prints.

