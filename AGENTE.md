# Agente de Postagem — Ciello

Procedimento semanal que o agente segue toda vez que roda. Este arquivo é a fonte da verdade: se algo mudar (horários, perfis, estilo), mude aqui.

## Contexto da marca
- Marca: **Ciello** — tecnologia, sites, automação e IA para micro e pequenas empresas (Chapecó/SC e região).
- Instagram: **@ciellotec** · Metricool brand id **6611209** · fuso **America/Sao_Paulo**.
- Identidade atual (posts do @ciellotec — **não usar os posts antigos do Drive**): fundo carvão texturizado com luz quente, títulos em Anton caixa alta (marfim / cinza / ouro #E0A81C), texto em serifa, rótulos espaçados em ouro, pílulas. Logo oficial em `marca/`. Mascote **I.V.A.** (`reels/src/Iva.tsx`): computador retrô azul-marinho com rosto ciano na tela, fiel ao protótipo em `marca/iva-prototipo.png` (expressões em `marca/iva-expressoes.png`); o botão laranja é o ponteiro dela. Tagline: "Tecnologia que eleva".
- **Motor de vídeo: Remotion (`reels/`)**, no padrão do reel "fim da escala 6x1" (o favorito do Mateus): fundo creme em degradê radial, **um mundo isomérico que continua de cena em cena** com a câmera andando (zoom/pan), pessoinhas, lojas, pinos, cards e celular entrando com molas suaves, legenda karaokê centralizada (palavras escurecem quando faladas, grifo dourado nas palavras-chave), I.V.A. em SVG — computador retrô azul-marinho do protótipo (`marca/iva-prototipo.png`), rosto ciano "O O" com sorrisinho, painel turquesa e disquete; o botão laranja vira o Pontinho que aponta, cartão final escuro "Comente PALAVRA". Exemplos de referência: `reels/src/VendedorIA.tsx`, `TesteIdeia.tsx` e `TextoIA.tsx`. Peças prontas em `reels/src/common.tsx` (TopTitle, Pill, Chip com risco, Bubble, Billboard com troca de texto, Coins, PhoneChat, IvaActor com Pontinho, EndCard) e `reels/src/iso.tsx` (Disc, Shop, Person, Pin): monte cada reel novo com elas e registre a composição em `reels/src/Root.tsx`. Renderizar: `cd reels && npm install && node render.mjs <Composicao> ../midia/X.mp4`. O gerador Python (`gerador/`) fica só como reserva.
- Ângulo editorial: pegar o que está viral no nicho de IA e traduzir para **"IA aplicada ao seu negócio"**, para que as views virem clientes.

## Perfis de referência
@iacomjota · @viniciusguimaraes.ia · @gabrieltomaz.ia · @theodacoda

## Passo a passo semanal (roda domingo à noite)

1. **Pesquisar virais da semana**
   - vidIQ `vidiq_instagram_tiktok_outlier_search`: query sobre IA/Claude/ChatGPT/automação, `descriptionLanguage: ["pt"]`, últimos 7 dias, audiência `Culture/Region: Brazil/Brazilian; Global: false; Demographics: donos de pequenos negócios e profissionais curiosos por IA, 22-45;`. Repetir com `embeddingType: "hook"` para pegar ganchos.
   - vidIQ `vidiq_ig_profile_reels` nos 4 perfis de referência; ranquear reels dos últimos 7 dias por views.
   - WebSearch: lançamentos e novidades de IA da semana (Claude, ChatGPT, Gemini, ferramentas novas).
2. **Escolher 3 temas** com maior potencial (views acima da mediana do criador + assunto que dá para aplicar a pequenos negócios). Não repetir temas de `historico.md`.
3. **Checar fatos.** Toda afirmação sobre um produto ou recurso precisa ser confirmada numa fonte oficial ou confiável da semana. Se não der para confirmar, troque o tema.
4. **Roteirizar** cada reel em `roteiros/AAAA-MM-DD-slug.json` no formato do gerador (hook → 2 a 4 itens → cta), 18–28s no total. Adaptar formato e gancho; **nunca copiar texto, roteiro ou visual de outro criador**.
   - Gancho: até 9 palavras, com uma palavra em destaque.
   - CTA sempre com "Salva pra testar depois" (saves e shares são o que mais distribui).
5. **Narração (local, sem créditos)**: escrever a fala completa de cada reel em português do Brasil coloquial ("pra", "tá", "você"), dividida por cena no campo `say` do roteiro. Gerar no PC do Mateus com `python central/voz.py roteiros/X.json --saida audio/<slug> --nome <PREFIXO>` (motor `chatterbox` com `--ref marca/voz-mateus.wav` quando a voz clonada estiver aprovada; até lá, `kokoro`). O script imprime os `*_TIMES` e grava os tempos das falas em `audio/<slug>/tempos.json`. Detalhes em `central/README.md`.
6. **Renderizar o visual** sincronizado com a fala: criar a composição em `reels/src/`, colar os `*_TIMES` e usar os `from`/`to` de `tempos.json` nas `LINES`, e rodar `node render.mjs`. Conferir stills com `--frames=...` antes do vídeo inteiro.
7. **Montar o final**: `python central/mixar.py midia/X.mp4 audio/<slug>/narracao.wav midia/final/X.mp4 --inicio-trilha N` (voz + trilha `midia/trilhas/trilha-01.mp3` com ducking, -14 LUFS; variar `--inicio-trilha` entre os reels).
8. **Publicar a mídia**: commit + push em `main`. URL pública do vídeo final:
   `https://raw.githubusercontent.com/MTCiello/agente-de-postagem/main/midia/final/X.mp4`
9. **Agendar no Metricool** com a URL do vídeo final (`createScheduledPost`): Instagram `type: REEL`, `autoPublish: true`, `videoCoverMilliseconds: 1500`. Plano grátis: **20 posts por mês** e **30 dias de histórico**, então não passe de 20 agendamentos no mês.
   - Datas: **segunda, quarta e sexta às 10:00** (America/Sao_Paulo) da semana seguinte.
   - Legenda: 1ª linha = gancho; 3–5 linhas curtas de valor; CTA ("Chama no direct" ou "Comenta IA"); palavras-chave em texto corrido (ex.: "inteligência artificial para pequenas empresas", "automação", "Chapecó"); 3–5 hashtags no fim.
10. **Registrar** em `historico.md` (data, tema, fonte do viral, URL do vídeo, link do Metricool) e fazer commit.
11. **Avisar o Mateus** com um resumo curto: os 3 temas, por que cada um, e os horários agendados.

## Regras
- Se qualquer passo falhar (vidIQ sem créditos, push rejeitado, Metricool recusou), não publique pela metade: agende como rascunho (`draft: true`) e avise o que falhou.
- Não repostar vídeo de terceiros, não usar logo/marca de outras empresas além de citar o nome do produto.
- Toda a comunicação em português do Brasil.

## Orçamento de créditos vidIQ (plano atual: 150/mês)
- Narração e montagem agora são locais (`central/`), então o vidIQ fica **só para pesquisa**: outlier search 5 + reels dos perfis 5 cada (~25 por semana).
- Se o saldo (`vidiq_balance`) não cobrir, pesquise com WebSearch e com os perfis de referência abertos no navegador, e avise o Mateus.
