# Agente de Postagem — Ciello

Procedimento semanal que o agente segue toda vez que roda. Este arquivo é a fonte da verdade: se algo mudar (horários, perfis, estilo), mude aqui.

## Contexto da marca
- Marca: **Ciello** — tecnologia, sites, automação e IA para micro e pequenas empresas (Chapecó/SC e região).
- Instagram: **@ciellotec** · Metricool brand id **6611209** · fuso **America/Sao_Paulo**.
- Identidade oficial (manual de marca): Tinta #0d0d0d, Ouro #C8960A (acento, usar pouco), Teal #1693A5 (secundária), Branco, Cinza #888888, Carvão #1a1a1a. Fundo papel #F5F5F5 com blocos diagonais em tinta. Títulos em Barlow Condensed Black, linhas de apoio em Barlow Condensed Light cinza, ênfase em Playfair Display Black Italic dourado, texto em DM Sans. Logo: nuvem em contorno + CIELLO espaçado. Tagline: "Tecnologia que eleva". O gerador v3 já aplica tudo isso — nos roteiros use os campos kicker/pre/big/accent/post (hook), num/tag/title/body/prompt (item) e kicker/pre/big/accent/button/save (cta).
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
5. **Narração**: escrever a fala completa de cada reel em português do Brasil coloquial ("pra", "tá", "você"), dividida por cena no campo `say` do roteiro. Gerar com `vidiq_voiceover_generate` (voz atual: Liam `TX3LPaxmHKxFdv7VOQHJ`; trocar pela voz clonada do Mateus quando existir) e anotar `durationSeconds`.
6. **Renderizar o visual** sincronizado com a fala: `python3 gerador/render_reel.py roteiros/X.json midia/X.mp4 --total <duração da voz + 0.8> --silent`. Conferir 3–4 frames.
7. **Publicar a mídia**: commit + push em `main`. URL pública do vídeo:
   `https://raw.githubusercontent.com/MTCiello/agente-de-postagem/main/midia/X.mp4`
8. **Montar o final no vidIQ**: `vidiq_video_upload` (URL acima) → `vidiq_compose` vertical com o vídeo, a narração (startAtSeconds 0.1) e a trilha (volume 0.4, duckTo 0.18). Trilha atual: https://ai-music-tracks.s3.us-east-1.amazonaws.com/90b27dc2-6bce-4d67-931e-15a70ae728f3/d40be94a-c72e-4ac9-90c9-651f74badfd2.wav (variar `trimStartSeconds` entre os reels).
9. **Agendar no Metricool** com a URL do vídeo final do compose (`createScheduledPost`): Instagram `type: REEL`, `autoPublish: true`, `videoCoverMilliseconds: 1500`.
   - Datas: **segunda, quarta e sexta às 10:00** (America/Sao_Paulo) da semana seguinte.
   - Legenda: 1ª linha = gancho; 3–5 linhas curtas de valor; CTA ("Chama no direct" ou "Comenta IA"); palavras-chave em texto corrido (ex.: "inteligência artificial para pequenas empresas", "automação", "Chapecó"); 3–5 hashtags no fim.
10. **Registrar** em `historico.md` (data, tema, fonte do viral, URL do vídeo, link do Metricool) e fazer commit.
11. **Avisar o Mateus** com um resumo curto: os 3 temas, por que cada um, e os horários agendados.

## Regras
- Se qualquer passo falhar (vidIQ sem créditos, push rejeitado, Metricool recusou), não publique pela metade: agende como rascunho (`draft: true`) e avise o que falhou.
- Não repostar vídeo de terceiros, não usar logo/marca de outras empresas além de citar o nome do produto.
- Toda a comunicação em português do Brasil.

## Orçamento de créditos vidIQ (plano atual: 150/mês)
- Pesquisa: outlier search 5 + reels dos perfis 5 cada.
- Narração: 14 por reel (até 1000 caracteres). Compose: ~7 por reel. Trilha nova: 25 (reaproveitar a atual).
- Uma semana completa custa ~65–90 créditos. Se o saldo (`vidiq_balance`) não cobrir, priorize: 1 outlier search + 2 perfis, e reels sem narração (só trilha local) — e avise o Mateus.
