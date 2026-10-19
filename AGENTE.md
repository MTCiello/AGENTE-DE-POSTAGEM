# Agente de Postagem — Ciello

Procedimento semanal que o agente segue toda vez que roda. Este arquivo é a fonte da verdade: se algo mudar (horários, perfis, estilo), mude aqui.

## Contexto da marca
- Marca: **Ciello** — tecnologia, sites, automação e IA para micro e pequenas empresas (Chapecó/SC e região).
- Instagram: **@ciellotec** · Metricool brand id **6611209** · fuso **America/Sao_Paulo**.
- Identidade atual (posts do @ciellotec — **não usar os posts antigos do Drive**): fundo carvão texturizado com luz quente, títulos em Anton caixa alta (marfim / cinza / ouro #E0A81C), texto em serifa, rótulos espaçados em ouro, pílulas. Logo oficial em `marca/`. Mascote **I.V.A.** (`reels/src/Iva.tsx`): computador retrô azul-marinho com rosto ciano na tela, fiel ao protótipo em `marca/iva-prototipo.png` (expressões em `marca/iva-expressoes.png`); o botão laranja é o ponteiro dela. Tagline: "Tecnologia que eleva".
- **Motor de vídeo: Remotion (`reels/`)**, no padrão do reel "fim da escala 6x1" (o favorito do Mateus): fundo creme em degradê radial, **um mundo isomérico que continua de cena em cena** com a câmera andando (zoom/pan), pessoinhas, lojas, pinos, cards e celular entrando com molas suaves, legenda karaokê centralizada (palavras escurecem quando faladas, grifo dourado nas palavras-chave), I.V.A. em SVG — computador retrô azul-marinho do protótipo (`marca/iva-prototipo.png`), rosto ciano "O O" com sorrisinho, painel turquesa e disquete; o botão laranja vira o Pontinho que aponta, cartão final escuro "Comente PALAVRA". Exemplos de referência: `reels/src/VendedorIA.tsx`, `TesteIdeia.tsx` e `TextoIA.tsx`. Peças prontas em `reels/src/common.tsx` (TopTitle, Pill, Chip com risco, Bubble, Billboard com troca de texto, Coins, PhoneChat, IvaActor com Pontinho, EndCard) e `reels/src/iso.tsx` (Disc, Shop, Person, Pin): monte cada reel novo com elas e registre a composição em `reels/src/Root.tsx`. Renderizar: `cd reels && npm install && node render.mjs <Composicao> ../midia/X.mp4`. O gerador Python (`gerador/`) fica só como reserva.
- Ângulo editorial: pegar o que está viral no nicho de IA e traduzir para **"IA aplicada ao seu negócio"**, para que as views virem clientes.

## Equipe
Nove agentes em `.claude/agents/` (pesquisador-mercado, roteirista, produtor-video, produtor-imagem, postagem, analista, sdr, closer, gestor-anuncios), coordenados por `/semana`, `/comercial` e `/segunda`. Visão completa em `docs/equipe.md`. Quem está trabalhando e os números da empresa: `python central/escritorio/servidor.py` (Escritório Ciello).

## Perfis de referência
Cadastrar como **concorrentes no Metricool** (API oficial, sem risco para a conta) para o pesquisador puxar os reels toda semana.
@iacomjota · @viniciusguimaraes.ia · @gabrieltomaz.ia · @theodacoda

## Passo a passo semanal (roda domingo à noite)

1. **Pesquisar virais da semana**
   - **Radar**: no PC, `python central/radar.py` (GitHub, Hacker News, Reddit, Google Notícias BR, Google Trends BR, blogs oficiais) → `radar/AAAA-MM-DD.md` com nota 0–100 por pilar. Na nuvem, onde essas fontes são bloqueadas, montar o radar com WebSearch no mesmo formato (exemplo: `radar/2026-10-19.md`).
   - **Ganchos**: no PC, `python central/ganchos.py importar @iacomjota @viniciusguimaraes.ia @gabrieltomaz.ia @theodacoda --sessao <conta secundária>` guarda os reels que passaram de 1,5x a mediana do criador.
   - vidIQ `vidiq_instagram_tiktok_outlier_search`: query sobre IA/Claude/ChatGPT/automação, `descriptionLanguage: ["pt"]`, últimos 7 dias, audiência `Culture/Region: Brazil/Brazilian; Global: false; Demographics: donos de pequenos negócios e profissionais curiosos por IA, 22-45;`. Repetir com `embeddingType: "hook"` para pegar ganchos.
   - vidIQ `vidiq_ig_profile_reels` nos 4 perfis de referência; ranquear reels dos últimos 7 dias por views.
   - WebSearch: lançamentos e novidades de IA da semana (Claude, ChatGPT, Gemini, ferramentas novas).
2. **Escolher 3 temas** com maior potencial (views acima da mediana do criador + assunto que dá para aplicar a pequenos negócios). Não repetir temas de `historico.md`.
3. **Checar fatos.** Toda afirmação sobre um produto ou recurso precisa ser confirmada numa fonte oficial ou confiável da semana. Se não der para confirmar, troque o tema.
4. **Roteirizar** cada reel em `roteiros/AAAA-MM-DD-slug.json` no formato do gerador (hook → 2 a 4 itens → cta), 18–28s no total. Adaptar formato e gancho; **nunca copiar texto, roteiro ou visual de outro criador**.
   - Gancho: até 9 palavras, com uma palavra em destaque. Antes de escrever, rode `python central/ganchos.py modelos --pilar <pilar>` e use um dos formatos que mais performam (adaptar o padrão, nunca o texto).
   - CTA sempre com "Salva pra testar depois" (saves e shares são o que mais distribui).
5. **Narração (local, sem créditos)**: escrever a fala completa de cada reel em português do Brasil coloquial ("pra", "tá", "você"), dividida por cena no campo `say` do roteiro. Gerar no PC do Mateus com `python central/voz.py roteiros/X.json --saida audio/<slug> --nome <PREFIXO>` (motor `chatterbox` com `--ref marca/voz-mateus.wav` quando a voz clonada estiver aprovada; até lá, `kokoro`). O script imprime os `*_TIMES` e grava os tempos das falas em `audio/<slug>/tempos.json`. Detalhes em `central/README.md`.
   - **Plano-sequência** (padrão do reel de referência feito no Claude): kit em `reels/src/plano/`, regras em `docs/plano-sequencia.md`. Antes de agendar, `python central/analisar_video.py midia/X.mp4` precisa dar **aprovado**.
   - **Reel com o clone digital do Mateus** (em vez do mundo isométrico): descrever as cenas numa montagem JSON (modelo em `reels/src/montagens/exemplo-clone.json`), gerar os clipes conforme `docs/clone-digital.md` e renderizar com `node render.mjs CloneReel X.mp4 --props=montagem.json`. Postar com `isAiGenerated: true`.
6. **Renderizar o visual** sincronizado com a fala: criar a composição em `reels/src/`, colar os `*_TIMES` e usar os `from`/`to` de `tempos.json` nas `LINES`, e rodar `node render.mjs`. Conferir stills com `--frames=...` antes do vídeo inteiro.
7. **Montar o final**: `python central/mixar.py midia/X.mp4 audio/<slug>/narracao.wav midia/final/X.mp4 --inicio-trilha N` (voz + trilha `midia/trilhas/trilha-01.mp3` com ducking, -14 LUFS; variar `--inicio-trilha` entre os reels).
8. **Publicar a mídia**: commit + push em `main`. URL pública do vídeo final:
   `https://raw.githubusercontent.com/MTCiello/agente-de-postagem/main/midia/final/X.mp4`
9. **Capa**: `cd reels && node capa.mjs ../roteiros/X.json ../midia/capas/X.jpg` (usa o gancho do roteiro; bloco `"capa"` no roteiro ou `--selo=`, `--tema=creme`, `--iva=` para ajustar). O título fica na faixa central 3:4, que é o que aparece na grade do perfil.
10. **Agendar no Metricool** com a URL do vídeo final (`createScheduledPost`): Instagram `type: REEL`, `autoPublish: true`, `videoThumbnailUrl` = URL pública da capa (`.../main/midia/capas/X.jpg`). Plano grátis: **20 posts por mês** e **30 dias de histórico**, então não passe de 20 agendamentos no mês.
   - Datas: **segunda, quarta e sexta às 10:00** (America/Sao_Paulo) da semana seguinte.
   - Legenda: 1ª linha = gancho; 3–5 linhas curtas de valor; CTA ("Chama no direct" ou "Comenta IA"); palavras-chave em texto corrido (ex.: "inteligência artificial para pequenas empresas", "automação", "Chapecó"); 3–5 hashtags no fim.
11. **Registrar** em `historico.md` (data, tema, fonte do viral, URL do vídeo, link do Metricool) e fazer commit. Sete dias depois de cada post, lançar o resultado na biblioteca: `python central/ganchos.py adicionar --nosso --perfil @ciellotec --gancho "..." --views N --salvamentos N --compartilhamentos N --retencao S`.
12. **Avisar o Mateus** com um resumo curto: os 3 temas, por que cada um, e os horários agendados.

## Analista (toda segunda de manhã)
1. Puxar do Metricool (`getAnalyticsDataByMetrics`, últimos 30 dias): seguidores (IGEV01), alcance (IGEV06), contas engajadas (IGEV42) e os reels (IGRE01, IGRE03, IGRE23, IGRE11, IGRE12, IGRE21, IGRE07, IGRE24). Puxar também `getBestTimeToPostByNetwork` (instagram, próxima semana).
2. Salvar em `metricas/AAAA-MM-DD.json` no mesmo formato de `metricas/2026-10-19.json`. O plano grátis só guarda 30 dias, então **este arquivo é o histórico**.
3. `python central/relatorio.py` → `metricas/relatorio-AAAA-MM-DD.md` e resumo para o Mateus.
4. Lançar na biblioteca de ganchos os posts que completaram 7 dias (`central/ganchos.py adicionar --nosso`).
5. Horário: o principal sai do relatório (hoje **10h**). Uma vez por semana, testar o horário de teste (hoje **18h**) e comparar depois de 4 semanas.

## Regras
- **GitHub primeiro.** Antes de construir qualquer função nova, procurar um repositório aberto que já resolva (licença que permita uso comercial, mantido, bem avaliado) e integrar. Código próprio só para costurar as peças ou quando não existir nada pronto.
- Se qualquer passo falhar (vidIQ sem créditos, push rejeitado, Metricool recusou), não publique pela metade: agende como rascunho (`draft: true`) e avise o que falhou.
- Não repostar vídeo de terceiros, não usar logo/marca de outras empresas além de citar o nome do produto.
- Toda a comunicação em português do Brasil.

## Orçamento de créditos vidIQ (plano atual: 150/mês)
- Narração e montagem agora são locais (`central/`), então o vidIQ fica **só para pesquisa**: outlier search 5 + reels dos perfis 5 cada (~25 por semana).
- Se o saldo (`vidiq_balance`) não cobrir, pesquise com WebSearch e com os perfis de referência abertos no navegador, e avise o Mateus.
