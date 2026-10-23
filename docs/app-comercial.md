# Ciello Central — app de agentes para marketing e comercial

Rascunho de arquitetura (19/10/2026). Este documento junta a pesquisa de repositórios e fundamentos e propõe como montar um app próprio que substitua as ferramentas que cobram por crédito (vidIQ, Metricool) e leve o conteúdo até a venda do **CIELLO CRM**.

---

## 1. Objetivo

Dois ciclos dentro do mesmo app:

```
CONTEÚDO   Radar ─► Roteirista/Checador ─► Voz ─► Vídeo/Carrossel ─► Publicador ─► Analista
              ▲                                                                       │
              └───────────────────── aprende com o que funcionou ◄───────────────────┘

COMERCIAL  Leads (CNPJ + Google Maps) ─► Qualificação ─► Abordagem ─► CIELLO CRM
           Comentário/DM do Instagram ─► Resposta automática ─► Qualificação ─┘
```

Regra do app: **nada é publicado ou enviado sem aprovação do Mateus** (roteiro, mensagem, lista de leads). Os agentes preparam e você aprova.

Situação atual que motiva o app: 4 créditos no vidIQ até 18/11, 63 seguidores, 0 salvamentos e 0 comentários nos 6 reels, e o tempo médio assistido do CRM foi o melhor (8 s).

---

## 2. Pilares editoriais

| # | Pilar | Exemplo de post | Ponte para o negócio |
|---|---|---|---|
| 1 | **Comandos/prompts** (ChatGPT, Claude, Gemini) | "5 comandos do ChatGPT que respondem seu cliente por você" | Atendimento → CRM |
| 2 | **Lançamentos e novidades das IAs** | "Saiu ontem: o que o novo modelo X muda pra quem vende" | Autoridade |
| 3 | **Repositórios famosos do GitHub** | "Esse projeto grátis tem 70 mil estrelas e substitui uma ferramenta de R$ 100/mês" | "A Ciello instala pra você" |
| 4 | **Economizar com IA** | "Pare de pagar por X: a versão grátis faz o mesmo" | Custo × CRM |
| 5 | **IA aplicada ao negócio** | "Vendedor de IA que não dorme" | CTA direto para o CRM |

Todo post termina com a ponte para pequenos negócios. Os pilares 1 a 4 trazem alcance e o pilar 5 traz clientes. Proporção sugerida por semana: 3 de alcance para 1 de conversão.

---

## 3. Os agentes

| Agente | O que faz | Repositórios e fontes | Custo |
|---|---|---|---|
| **Radar** | Encontra os assuntos que estão crescendo nos 5 pilares e dá nota de 0 a 100 para cada um | `mvanhorn/last30days-skill`, GitHub Trending (`gtrending`), API de busca do GitHub, `trendspyg` (Google Trends BR), RSS dos blogs oficiais, Instagram `business_discovery` | Grátis (APIs oficiais e chaves opcionais) |
| **Roteirista + Checador** | Escreve o roteiro no formato que já existe em `roteiros/` e confere cada afirmação numa fonte oficial | LLM (Claude), `AGENTE.md` como guia de estilo | Centavos por roteiro |
| **Voz** | Narração em PT-BR com a voz clonada do Mateus e legenda com o tempo real de cada palavra | VoiceStudio / OmniVoice, Chatterbox pt-br, faster-whisper / WhisperX | Grátis (local) ou GPU por segundo |
| **Vídeo e carrossel** | Reels no Remotion (já existe) e carrosséis como imagens paradas no mesmo visual | `reels/` + `ffmpeg` (mistura voz e trilha, substitui o compose do vidIQ) | Grátis (Remotion é grátis para até 3 funcionários) |
| **Publicador** | Agenda e publica | Instagram Graph API (publicação oficial) ou Postiz (Apache-2.0, self-hosted) | Grátis |
| **Analista** | Coleta métricas, faz o relatório semanal e devolve ao Radar o que funcionou | Instagram Graph API (insights), SQLite/Postgres | Grátis |
| **SDR (prospecção)** | Monta a lista de empresas, qualifica, personaliza a abordagem e cadastra no CRM | Dados abertos CNPJ (Receita), `gosom/google-maps-scraper` (MIT), DuckDB | Grátis + VPS |
| **Atendente de comentários** | Quem comenta a palavra-chave recebe DM automática (resposta privada oficial) e é qualificado | Instagram Messaging API (webhook de comentário) | Grátis |
| **Orquestrador** | Agenda tudo, guarda o estado, pede aprovação e avisa o Mateus | Claude Agent SDK + agendador (cron) | — |

---

## 4. Voz no nível ElevenLabs sem crédito

### Candidatos (licença é o que manda)

| Opção | Licença | Português | Hardware | Veredito |
|---|---|---|---|---|
| **VoiceStudio** (`debpalash/VoiceStudio`, motor padrão OmniVoice da k2-fsa) | App AGPL-3.0; código do OmniVoice Apache-2.0 (licença dos pesos: confirmar no Hugging Face) | 600+ idiomas (confirmar PT na `docs/languages.md`) | GPU NVIDIA ideal; roda em CPU, mais lento | **Testar primeiro.** Já vem com API local e MCP para agentes, clonagem com 3–10 s de referência e 17 motores para trocar |
| **Chatterbox Multilingual pt-br** (Resemble AI) | MIT | Tem modelo próprio para **português do Brasil** (`Chatterbox-Multilingual-pt-br`) | 500M; versões Turbo (350M) e Nano (110M, CPU) | **Segunda opção forte.** Põe marca d'água inaudível (Perth) em todo áudio |
| **Qwen3-TTS** | Código Apache-2.0; pesos com licença própria (ler antes) | Sim, entre 10 idiomas | ~4–8 GB de VRAM (estimativa de terceiros) | Boa expressividade, mais pesado |
| **Kokoro 82M** | Apache-2.0 | 3 vozes pt-br, sem clonagem | CPU | Reserva rápida, qualidade menor |
| ❌ XTTS v2, Voxtral TTS, Fish S2, F5-TTS | Não comercial | — | — | **Não usar**: a Ciello é empresa e os posts vendem |

### Plano de teste

1. Gravar **60 s da voz do Mateus** num lugar silencioso (celular perto da boca, sem eco).
2. Gerar as mesmas 5 frases de um roteiro real em VoiceStudio, Chatterbox pt-br e Qwen3-TTS.
3. **Teste cego**: ouvir sem saber qual é qual e dar nota para naturalidade, sotaque e ritmo. A que vencer vira a voz padrão.
4. Passar o áudio no **faster-whisper/WhisperX** para pegar o tempo real de cada palavra. Hoje o `Karaoke` em `reels/src/Captions.tsx` estima o tempo pelo tamanho das palavras, e com o tempo real a legenda fica cravada na fala.
5. Misturar voz e trilha com `ffmpeg` (ducking da trilha). Isso substitui o `vidiq_compose` hoje mesmo, antes da voz nova ficar pronta.

---

## 5. Radar: de onde vêm os assuntos

| Fonte | O que traz | Limite |
|---|---|---|
| `last30days-skill` | O que está bombando em Reddit, X, YouTube, TikTok, Hacker News e GitHub nos últimos 30 dias, ranqueado por engajamento | Reddit, HN e GitHub sem chave; X e YouTube com chave opcional |
| GitHub Trending + API de busca (`created:>7 dias`, por estrelas) | **Repositórios famosos** da semana (pilar 3) | Trending não tem API oficial, mas a busca tem |
| `trendspyg` (Google Trends) | O que o brasileiro está pesquisando ("comandos chatgpt", "ia grátis") | Algumas funções precisam de Chrome |
| RSS oficiais (OpenAI, Anthropic, Google, Meta, Microsoft) + portais de tecnologia | **Lançamentos** (pilar 2) e fonte para o checador | Grátis |
| Instagram `business_discovery` | Curtidas, comentários e views dos posts dos perfis de referência (@iacomjota, @viniciusguimaraes.ia…) | Oficial; só funciona com contas profissionais |
| Instagram busca por hashtag | Top posts de #chatgpt, #inteligenciaartificial | 30 hashtags diferentes a cada 7 dias |
| YouTube Data API | Vídeos em alta no nicho | 10.000 unidades/dia; cada busca custa 100 |

**Nota de cada assunto (0–100):**

| Critério | Peso |
|---|---|
| Viralidade: está crescendo mais rápido que a média do criador ou da fonte | 35 |
| Encaixa em um dos 5 pilares | 25 |
| Dá para virar dica para pequeno negócio | 20 |
| Novidade: não está no `historico.md` | 10 |
| Verificável: tem fonte oficial | 10 |

O Analista ajusta os pesos com o tempo, conforme os temas que geraram salvamentos, compartilhamentos e DMs.

---

## 6. Analista: as métricas que importam

Puxar direto da **Instagram Graph API** (permissão `instagram_manage_insights`) para um banco local, sem pagar Metricool.

| Métrica | Por que importa | Meta inicial |
|---|---|---|
| Taxa de visualização acima de 3 s | Mede se o gancho funciona | > 60% |
| Tempo médio assistido | Hoje está em 2,5–8 s | > 50% do vídeo |
| Salvamentos e compartilhamentos | É o que o algoritmo mais distribui | > 1% do alcance |
| Seguidores por post | Crescimento | positivo em todo post |
| Comentários com palavra-chave e DMs | Interesse comercial | ≥ 3 por semana |
| Leads → demonstrações → clientes | **A métrica que paga as contas** | acompanhar no CRM |

Relatório semanal toda segunda: top e pior post, por quê, e o que muda na próxima semana.

---

## 7. Comercial: do lead ao CRM

**De onde vêm os leads**
- **Dados abertos do CNPJ (Receita Federal):** base completa e atualizada todo mês. Filtrar por **CNAE + município** (Chapecó e região) com DuckDB. Traz razão social, data de abertura e porte.
- **`gosom/google-maps-scraper` (MIT):** telefone, site, nota, número de avaliações e o **texto das avaliações**.

**Qualificação (perfil ideal do CIELLO CRM):** empresas que vendem pelo WhatsApp e têm equipe, como clínicas, imobiliárias, lojas de móveis, autopeças, academias, escolas e concessionárias. Ganham mais pontos as que têm muitas avaliações (movimento) e **reclamações de atendimento nas avaliações** ("demoram pra responder", "ninguém retorna"). Essa reclamação vira o gancho da mensagem personalizada.

**Abordagem, com segurança jurídica e de conta**
- **E-mail B2B:** a LGPD permite pela base do **legítimo interesse**, desde que você diga de onde veio o contato, ofereça descadastro imediato e tenha o teste de balanceamento documentado (guia da ANPD de 2024).
- **WhatsApp:** só um a um ou pela **Cloud API oficial da Meta**. Disparo em massa por conexão não oficial (Baileys/Evolution API) **pode banir o número para sempre**. Não arriscar o número da empresa.
- **Inbound:** quem comenta a palavra do CTA recebe a resposta privada oficial (1 mensagem em até 7 dias) e entra no funil.
- Tudo cai no funil do **CIELLO CRM**, se ele tiver API ou importação.

**Material de venda que os agentes produzem:** apresentação do CRM, roteiro da demonstração de 15 min, respostas às objeções ("já uso o WhatsApp Business", "é caro") e cadência de follow-up (D+2, D+5, D+10).

---

## 8. Stack sugerida

| Camada | Escolha | Por quê |
|---|---|---|
| Agentes | **Python + Claude Agent SDK** | Já é como este repositório trabalha. O `last30days` é uma skill no mesmo formato. Usar um modelo barato para triagem e um forte para roteiro |
| Agendamento | cron / APScheduler | Simples. n8n é opcional (licença permite uso interno, não revenda) |
| Banco | SQLite → Postgres | Histórico, leads, métricas e notas do Radar |
| Vídeo | Remotion + ffmpeg (já existe) | — |
| Voz | VoiceStudio ou Chatterbox via API local | — |
| Painel | Começa com relatório + aprovação por mensagem; depois painel web | Entrega valor antes de ter tela bonita |
| Infra | **Agora:** PC do Mateus (CPU) + Claude na nuvem. **Com investimento:** VPS pequena para Radar, banco e painel, e GPU sob demanda (RunPod ou Modal, cobrança por segundo) | Começa com R$ 0 |

**Custo mensal:** VPS, chamadas de LLM e alguns minutos de GPU. A tendência é ficar abaixo de vidIQ + Metricool pagos, mas os valores exatos dependem do volume e precisam ser medidos no primeiro mês.

---

## 9. Licenças, se um dia o app virar produto

- **VoiceStudio (AGPL-3.0):** uso interno é livre. Oferecer como serviço modificado obriga a abrir o código.
- **Remotion:** grátis até 3 funcionários. Acima disso, licença de empresa.
- **n8n:** não pode ser revendido como serviço.
- **Chatterbox (MIT), Kokoro, OmniVoice (Apache):** liberados, mas confirmar a licença dos pesos.
- Coletar Instagram/TikTok por scraping fere os termos de uso. **Preferir sempre as APIs oficiais.**

---

## 10. Roteiro de construção

| Fase | Quando | Entrega | Efeito |
|---|---|---|---|
| **0. Sem créditos** | Semana 1 | Mixagem com `ffmpeg` no lugar do compose; teste cego de vozes; clone da voz do Mateus; legenda com tempo real | Os reels voltam a sair com narração, sem vidIQ |
| **1. Radar + Roteirista** | Semanas 2–3 | Radar com os 5 pilares e nota; roteiros com checagem; carrosséis | Pauta da semana automática |
| **2. Comercial v1** | Semanas 3–4 | Lista qualificada de Chapecó e região, mensagens personalizadas, comentário → DM | Primeiras demonstrações agendadas |
| **3. Analista** | Mês 2 | Métricas pela Graph API, relatório semanal, ajuste automático dos pesos | O sistema aprende |
| **4. Painel** | Mês 2–3 | Tela única: pauta, aprovação, leads, resultados | Operação em 15 min por dia |

---

## 11. Decisões (19/10/2026)

| Pergunta | Resposta | O que muda |
|---|---|---|
| Hardware | PC com placa **AMD de 8 GB** | Voz e legendas rodam na **CPU** (estável no Windows). GPU AMD fica para depois (ROCm no Windows ainda é alfa) |
| CIELLO CRM | Importa **planilha** | O SDR entrega um CSV no formato de importação do CRM |
| Metricool | **Grátis**: 20 posts/mês, 30 dias de histórico | Continua como publicador. O Analista salva um retrato semanal das métricas em `metricas/` para não perder o histórico |
| Uso | **Só interno** (assistente pessoal de comercial, redes e anúncios) | Licenças AGPL, Remotion grátis (até 3 pessoas) e n8n estão liberadas |
| Orçamento | **R$ 0 por enquanto**, tudo no PC | Sem VPS e sem GPU alugada. Investimento entra depois |

**Divisão de trabalho com custo zero**

| Parte | Onde roda | Faz |
|---|---|---|
| **Cérebro** (Claude, pela assinatura) | Sessão agendada na nuvem ou Claude Code no PC | Radar, roteiros, checagem, análise, mensagens de venda, agendamento no Metricool |
| **Músculos** (`central/`) | PC do Mateus | Voz (`voz.py`), legendas (`legendas.py`), render (Remotion) e montagem (`mixar.py`) |
| **LLM local** (opcional) | LM Studio/Ollama com Vulkan na AMD | Triagem em volume (centenas de leads) sem gastar uso do Claude |

**Fase 0 (feita):** `central/mixar.py` monta o reel final localmente (testado: -14,1 LUFS, AAC 48 kHz). `central/voz.py` gera a narração com Kokoro ou com a voz clonada no Chatterbox e calcula os tempos das cenas. `central/legendas.py` tira o tempo de cada palavra. A trilha foi trazida para `midia/trilhas/`. Falta rodar Kokoro e Chatterbox no PC (os modelos não baixam neste ambiente de nuvem) e gravar a referência da voz.

---

## Fontes

- VoiceStudio: [GitHub](https://github.com/debpalash/VoiceStudio) · [catálogo de motores](https://github.com/debpalash/VoiceStudio/blob/main/docs/feature-catalog.md) · [besthub.dev](https://www.besthub.dev/articles/voicestudio-local-first-open-source-voice-platform-for-cloning-dubbing-tts-8315f8ed2488)
- OmniVoice: [GitHub k2-fsa/OmniVoice](https://github.com/k2-fsa/OmniVoice) · [Hugging Face](https://huggingface.co/k2-fsa/OmniVoice)
- Chatterbox: [GitHub resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox) · [model card](https://huggingface.co/ResembleAI/chatterbox/blob/main/README.md)
- Comparativos de TTS 2026: [pinggy.io](https://pinggy.io/blog/best_open_source_self_hosted_text_to_speech_models/) · [openvoxai](https://openvoxai.com/blog/best-free-local-tts-models-2026) · [Coqui XTTS (licença)](https://localaimaster.com/models/coqui-tts)
- Qwen3-TTS: [FAQ](https://www.mintlify.com/QwenLM/Qwen3-TTS/resources/faq) · [guia de VRAM](https://insiderllm.com/guides/crane-qwen3-tts-local-voice-cloning/)
- Kokoro: [PyPI](https://pypi.org/project/kokoro/) · [vozes pt-br](https://replicate.com/alphanumericuser/kokoro-82m)
- WhisperX: [docs](https://docsearch.algolia.com/mcp/docs/repo/m-bain/whisperx)
- last30days-skill: [docs](https://docsearch.algolia.com/mcp/docs/repo/mvanhorn/last30days-skill) · [análise](https://emelia.io/hub/ai-agent-tech-monitoring)
- GitHub Trending: [gtrending](https://pypi.org/project/gtrending/0.4.0)
- Google Trends: [trendspyg](https://github.com/flack0x/trendspyg)
- Instagram: [Business Discovery](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/business-discovery) · [Hashtag Search](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/hashtag-search) · [guia da API 2026](https://www.getphyllo.com/post/instagram-api-guide) · [comentário → DM](https://inro.social/blog/instagram-comment-to-dm-automation)
- YouTube Data API: [visão geral oficial](https://developers.google.com/youtube/v3/getting-started) · [cotas](https://channelcrawler.com/insights/youtube-api-daily-limit-quotas-costs-and-how-to-scale-beyond-10000-units-channelcrawler)
- Postiz: [self-hosting](https://www.mintlify.com/gitroomhq/postiz-app/self-hosting/overview) · [Railway](https://railway.com/deploy/deploy-postiz)
- short-video-maker (referência de pipeline): [Docker Hub](https://hub.docker.com/r/gyoridavid/short-video-maker)
- Remotion: [preços](https://www.remotion.dev/docs/pricing) · [FAQ de licença](https://www.remotion.dev/docs/license/faq)
- n8n: [licença](https://dev.to/alifar/the-real-limits-of-n8n-free-automation-what-you-need-to-know-before-shipping-to-production-59o6)
- Frameworks de agentes: [comparativo 2026](https://pasqualepillitteri.it/en/news/3095/claude-agent-sdk-vs-langgraph-vs-crewai-benchmark-2026-en)
- WhatsApp: [Evolution API × API oficial](https://horadecodar.com.br/evolution-api-vs-api-oficial-whatsapp/) · [risco do Baileys](https://pasqualepillitteri.it/pt/news/12976/integrar-whatsapp-evolution-api-cloud-api-meta)
- Leads: [google-maps-scraper](https://github.com/gosom/google-maps-scraper) · [base CNPJ com DuckDB](https://www.tabnews.com.br/jeffev/transformei-a-base-aberta-do-cnpj-73-milhoes-de-estabelecimentos-em-buscas-de-segundos-sem-servidor-e-sem-banco-de-dados) · [prospecção com CNPJ](https://www.tabnews.com.br/antoniorincon/prospeccao-b2b-com-dados-publicos-de-cnpj-achar-enriquecer)
- LGPD: [legítimo interesse na visão da ANPD](https://www.bmalaw.com.br/conteudo/direito-digital-protecao-de-dados-e-cybersecurity/artigos-e-noticias/o-legitimo-interesse-na-visao-da-anpd/pdf) · [prospecção pelo CNPJ](https://www.socialhub.pro/?p=32858)
- GPU serverless: [RunPod × Modal](https://lyceum.technology/magazine/modal-vs-runpod-for-serverless-gpu-inference/)
- AMD: [ROCm em Radeon (oficial)](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/index.html) · [PyTorch AMD no Windows](https://github.com/sfinktah/amd-torch/) · [instalação AMD do Wan2GP (TheRock)](https://github.com/deepbeepmeep/Wan2GP/blob/main/docs/AMD-INSTALLATION.md) · [IA local em AMD 2026](https://www.mindstudio.ai/blog/running-local-ai-amd-rocm-ollama-lm-studio)
- Metricool grátis: [limites 2026](https://www.costbench.com/software/social-media-management/metricool/free-plan/)
