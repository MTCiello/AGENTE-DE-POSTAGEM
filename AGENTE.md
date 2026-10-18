# Agente de Postagem — Ciello

Procedimento semanal que o agente segue toda vez que roda. Este arquivo é a fonte da verdade: se algo mudar (horários, perfis, estilo), mude aqui.

## Contexto da marca
- Marca: **Ciello** — tecnologia, sites, automação e IA para micro e pequenas empresas (Chapecó/SC e região).
- Instagram: **@ciellotec** · Metricool brand id **6611209** · fuso **America/Sao_Paulo**.
- Paleta: #161616 (fundo), #F5F5F5 (texto), #1693A5 (destaque). Tagline: "Tecnologia que eleva".
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
5. **Renderizar**: `python3 gerador/render_reel.py roteiros/X.json midia/X.mp4`. Conferir 3–4 frames antes de seguir.
6. **Publicar a mídia**: commit + push em `main`. URL pública do vídeo:
   `https://raw.githubusercontent.com/MTCiello/agente-de-postagem/main/midia/X.mp4`
7. **Agendar no Metricool** (`createScheduledPost`): Instagram `type: REEL`, `autoPublish: true`, `videoCoverMilliseconds: 1500`.
   - Datas: **segunda, quarta e sexta às 10:00** (America/Sao_Paulo) da semana seguinte.
   - Legenda: 1ª linha = gancho; 3–5 linhas curtas de valor; CTA ("Chama no direct" ou "Comenta IA"); palavras-chave em texto corrido (ex.: "inteligência artificial para pequenas empresas", "automação", "Chapecó"); 3–5 hashtags no fim.
8. **Registrar** em `historico.md` (data, tema, fonte do viral, URL do vídeo, link do Metricool) e fazer commit.
9. **Avisar o Mateus** com um resumo curto: os 3 temas, por que cada um, e os horários agendados.

## Regras
- Se qualquer passo falhar (vidIQ sem créditos, push rejeitado, Metricool recusou), não publique pela metade: agende como rascunho (`draft: true`) e avise o que falhou.
- Não repostar vídeo de terceiros, não usar logo/marca de outras empresas além de citar o nome do produto.
- Toda a comunicação em português do Brasil.
