# Central — produção local, sem créditos

Ferramentas que rodam no PC do usuário e substituem o que o vidIQ cobrava (narração e montagem final). Visão geral do app em [`docs/app-comercial.md`](../docs/app-comercial.md).

| Script | Faz | Substitui |
|---|---|---|
| `voz.py` | Narração de cada cena do roteiro e tempos das cenas | `vidiq_voiceover_generate` |
| `legendas.py` | Tempo real de cada palavra (karaokê) | estimativa pelo tamanho da palavra |
| `mixar.py` | Vídeo + voz + trilha com ducking, -14 LUFS | `vidiq_compose` |
| `radar.py` | Assuntos em alta nos 5 pilares, com nota 0–100 (só biblioteca padrão) | pesquisa manual / outliers do vidIQ |
| `ganchos.py` | Biblioteca de ganchos validados (multiplicador sobre a mediana do criador) | `vidiq_ig_profile_reels` |
| `relatorio.py` | Relatório semanal a partir de `metricas/` | histórico pago do Metricool |
| `sdr.py` | Leads do Google Maps, qualificação, 1ª mensagem wa.me, cadência, resposta imediata a lead que chegou sozinho (`entrada`) e CSV do CRM | prospecção manual |
| `briefing.py` | Chefe de gabinete: 3 prioridades do dia, pendências por dono e placar da semana | — |
| `financeiro.py` | Assinaturas, faturas, cobrança 3/7/14 dias, extrato OFX/CSV com conciliação, caixa e previsão, MRR/churn/CAC/LTV, pós-venda e NPS | planilha / ERP pago |
| `vigia.py` | Preço, plano e oferta dos concorrentes (diferença desde a última vez) e link dos anúncios ativos | changedetection.io (quando precisar de mais) |
| `verificar.py` | Bateria de verificação de tudo (grava `estado/verificacao.txt`) | — |
| `clone/ciello_clone_kaggle.ipynb` | Wan2GP na GPU grátis do Kaggle: clone falando, andando, identidade e voz | HeyGen / Higgsfield |

Testes (sem internet): `python -m unittest discover central/testes`

## Fluxo de um reel

```bash
# 1. voz: gera audio/<slug>/narracao.wav e imprime os *_TIMES
python central/voz.py roteiros/X.json --saida audio/X --nome X

# 2. cole os *_TIMES e os tempos das LINES (audio/<slug>/tempos.json) na composição e renderize
cd reels && node render.mjs <Composicao> ../midia/X.mp4 && cd ..

# 3. montagem final (varie --inicio-trilha entre os reels)
python central/mixar.py midia/X.mp4 audio/X/narracao.wav midia/final/X.mp4 --inicio-trilha 12
```

Para testar o fluxo sem baixar nenhum modelo, use `--motor teste` no passo 1 (tons no lugar da voz).

## Instalação no Windows (PC com AMD de 8 GB)

Clique duas vezes em `instalar.cmd` na raiz do repositório e depois em `testar.cmd`. Passo a passo em `docs/instalador.md`.

- **Base** (`central/requirements.txt`): numpy e soundfile. É rápida.
- **Voz** (`central/requirements-voz.txt`): Kokoro, Chatterbox e faster-whisper. São ~3 GB; o instalador pergunta.
- **Por que CPU:** o PyTorch para placas AMD no Windows ainda é experimental. A CPU gera ~25 s de narração em poucos minutos.
- **Modelos:** cada motor de voz baixa o seu na primeira execução (Kokoro ~300 MB, Chatterbox ~2 GB, Whisper small ~500 MB).
- **Verificação:** `python central/verificar.py` (ou `testar.cmd`) roda cada função e grava `estado/verificacao.txt`.

## Clonar a voz do usuário (Chatterbox)

1. Grave **10 s** falando natural, no tom dos reels, num cômodo sem eco, com o celular a um palmo da boca. Salve como `marca/minha-voz.wav` (o `.gitignore` não sobe `.wav`; guarde uma cópia).
2. Gere a mesma cena com as duas opções e compare às cegas:

```powershell
python central/voz.py roteiros/2026-10-21-teste-ideia.json --motor kokoro --voz pm_alex --saida audio/teste-kokoro
python central/voz.py roteiros/2026-10-21-teste-ideia.json --motor chatterbox --ref marca/minha-voz.wav --saida audio/teste-clone
```

3. Ajustes do Chatterbox: `--expressao 0.6` deixa mais animado; `--cfg 0.3` fala mais devagar e claro.

O Chatterbox põe uma marca d'água inaudível (Perth) em todo áudio gerado. Ela não aparece no som e serve para identificar fala sintética.

## GPU AMD (depois, opcional)

- **RX 7600 / 7600 XT (RDNA3):** existem wheels do PyTorch com ROCm para Windows (projeto TheRock da AMD), ainda em fase alfa. Se funcionar, use `--dispositivo auto` no Chatterbox.
- **RX 6600 / 6650 XT (RDNA2):** não há suporte no Windows. No Linux funciona com `HSA_OVERRIDE_GFX_VERSION=10.3.0`.
- **LLM local** (para triagem de leads sem gastar uso do Claude): LM Studio ou Ollama usam Vulkan e rodam bem em AMD de 8 GB com modelos de 7–8B em 4 bits.
