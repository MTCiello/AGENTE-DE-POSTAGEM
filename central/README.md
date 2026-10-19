# Central — produção local, sem créditos

Ferramentas que rodam no PC do Mateus e substituem o que o vidIQ cobrava (narração e montagem final). Visão geral do app em [`docs/app-comercial.md`](../docs/app-comercial.md).

| Script | Faz | Substitui |
|---|---|---|
| `voz.py` | Narração de cada cena do roteiro e tempos das cenas | `vidiq_voiceover_generate` |
| `legendas.py` | Tempo real de cada palavra (karaokê) | estimativa pelo tamanho da palavra |
| `mixar.py` | Vídeo + voz + trilha com ducking, -14 LUFS | `vidiq_compose` |

## Fluxo de um reel

```bash
# 1. voz: gera audio/<slug>/narracao.wav e imprime os *_TIMES
python central/voz.py roteiros/2026-10-21-teste-ideia.json --saida audio/teste-ideia --nome TESTE

# 2. cole os *_TIMES e os tempos das LINES (audio/<slug>/tempos.json) na composição e renderize
cd reels && node render.mjs TesteIdeia ../midia/2026-10-21-teste-ideia.mp4 && cd ..

# 3. montagem final (varie --inicio-trilha entre os reels)
python central/mixar.py midia/2026-10-21-teste-ideia.mp4 audio/teste-ideia/narracao.wav midia/final/2026-10-21-teste-ideia.mp4 --inicio-trilha 12
```

Para testar o fluxo sem baixar nenhum modelo, use `--motor teste` no passo 1 (tons no lugar da voz).

## Instalação no Windows (PC com AMD de 8 GB)

**Por que CPU:** o PyTorch para placas AMD no Windows ainda é experimental (só algumas RX 7000/9000 e com builds alfa). Uma narração de reel tem ~25 s e a CPU gera isso em poucos minutos, então começamos na CPU, que é estável. A GPU fica para depois (ver abaixo).

1. **Python 3.11**: `winget install Python.Python.3.11` (o Chatterbox foi testado no 3.11)
2. **ffmpeg**: `winget install Gyan.FFmpeg`
3. **Node.js** (Remotion): `winget install OpenJS.NodeJS.LTS`
4. **espeak-ng** (o Kokoro usa para pronúncia): instalar o `.msi` em github.com/espeak-ng/espeak-ng/releases
5. No terminal, dentro da pasta do repositório:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r central/requirements.txt
```

Na primeira execução, cada motor baixa o seu modelo do Hugging Face (Kokoro ~300 MB, Chatterbox ~2 GB, whisper small ~500 MB).

## Clonar a voz do Mateus (Chatterbox)

1. Grave **10 s** falando natural, no tom dos reels, num cômodo sem eco, com o celular a um palmo da boca. Salve como `marca/voz-mateus.wav` (o `.gitignore` não sobe `.wav`; guarde uma cópia).
2. Gere a mesma cena com as duas opções e compare às cegas:

```powershell
python central/voz.py roteiros/2026-10-21-teste-ideia.json --motor kokoro --voz pm_alex --saida audio/teste-kokoro
python central/voz.py roteiros/2026-10-21-teste-ideia.json --motor chatterbox --ref marca/voz-mateus.wav --saida audio/teste-clone
```

3. Ajustes do Chatterbox: `--expressao 0.6` deixa mais animado; `--cfg 0.3` fala mais devagar e claro.

O Chatterbox põe uma marca d'água inaudível (Perth) em todo áudio gerado. Ela não aparece no som e serve para identificar fala sintética.

## GPU AMD (depois, opcional)

- **RX 7600 / 7600 XT (RDNA3):** existem wheels do PyTorch com ROCm para Windows (projeto TheRock da AMD), ainda em fase alfa. Se funcionar, use `--dispositivo auto` no Chatterbox.
- **RX 6600 / 6650 XT (RDNA2):** não há suporte no Windows. No Linux funciona com `HSA_OVERRIDE_GFX_VERSION=10.3.0`.
- **LLM local** (para triagem de leads sem gastar uso do Claude): LM Studio ou Ollama usam Vulkan e rodam bem em AMD de 8 GB com modelos de 7–8B em 4 bits.
