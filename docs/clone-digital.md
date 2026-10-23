# Clone digital do usuário — sem HeyGen, com modelos abertos

Pesquisa de 19/10/2026 sobre como fazer vídeos hiper-realistas com o clone do usuário (falando, andando, em cenários) usando repositórios abertos, no estilo do Higgsfield, e como isso entra no gerador de reels.

## O que o Higgsfield faz por baixo

O Higgsfield é um estúdio que junta modelos de imagem e vídeo (vários deles fechados e pagos) com uma camada de "personagem consistente". O equivalente aberto é montar o mesmo com 4 peças:

| Peça | Função | Melhor opção aberta | Licença |
|---|---|---|---|
| 1. **Identidade** | Fotos do usuário em qualquer cenário, sempre com o mesmo rosto | **Qwen-Image-Edit-2511** (aceita várias fotos de referência e segura a identidade). Depois, com GPU melhor: LoRA do rosto com `ostris/ai-toolkit` | Apache-2.0 / MIT |
| 2. **Fala** | A foto vira vídeo falando, sincronizado com a narração, com gestos e corpo | **InfiniteTalk** (MeiGen-AI): imagem + áudio → até ~1 min de vídeo, 480p ou 720p, corpo inteiro. Alternativas: Wan-S2V (mais movimento de câmera) e HunyuanVideo-Avatar | Apache-2.0 |
| 3. **Movimento** | O clone andando, entrando numa loja, mexendo no celular | **Wan 2.2 imagem → vídeo** (clipes de 5 s) e **Wan2.2-Animate**: copia o movimento de um vídeo de referência (por exemplo, o usuário gravando a si mesmo andando com o celular) para a imagem do clone, em qualquer cenário. **LTX-2.3** também gera áudio | Apache-2.0 / LTX: grátis até US$ 10 mi de faturamento |
| 4. **Ajuste de boca** | Corrige a sincronia labial se algum clipe sair fora | **LatentSync 1.5** (~8 GB) ou MuseTalk | Apache-2.0 / MIT |

Hubs que já juntam vários desses modelos: **ComfyUI** (fluxos prontos para InfiniteTalk, Wan-Animate e Qwen-Edit) e **Wan2GP** (interface simples para pouca VRAM, com suporte a AMD RDNA 2/3/4 e modelos a partir de 6 GB, usando a RAM do PC como apoio).

> O "Open-Higgsfield-AI" do GitHub é só uma interface para APIs pagas (Muapi). Não roda nada localmente.

## Onde rodar com R$ 0

Esses modelos têm 14B de parâmetros e foram feitos para placas NVIDIA de 16 a 24 GB. Na AMD de 8 GB, no Windows, eles rodam no máximo com o Wan2GP e muita RAM, de forma lenta e experimental. O caminho de custo zero é a GPU grátis na nuvem:

| Opção | O que dá | Uso |
|---|---|---|
| **Kaggle** (grátis) | ~30 h/semana de GPU (T4 ou P100, 16 GB), sessões de até 9 h | **Principal.** Um notebook roda ComfyUI ou os scripts do InfiniteTalk e do Wan e devolve os clipes |
| Google Colab grátis | T4 16 GB, sem garantia de tempo | Reserva |
| Hugging Face ZeroGPU | ~5 min de GPU/dia na conta grátis | Só para testes rápidos em Spaces prontos |
| PC (AMD 8 GB) | Wan2GP em modo de pouca VRAM | Experimento. Montagem, voz e legendas continuam no PC (`central/`) |
| **Com investimento** | GPU alugada por hora (RunPod/Modal, 4090 ou L40S) ou APIs pagas (Kling, Veo, Seedance via fal) | Mais qualidade e velocidade. É aqui que entra o LoRA do rosto |

Ordem de grandeza: numa T4, um clipe de 5 s em 480p com a LoRA de aceleração (4 a 8 passos) leva minutos, e um minuto de InfiniteTalk pode levar bem mais. As 30 h semanais cobrem 3 reels e os testes. **Estimativa a medir no primeiro teste.**

## Solução pronta escolhida: Wan2GP no Kaggle

Seguindo o "GitHub primeiro": em vez de montar cada modelo separado, o **[Wan2GP](https://github.com/deepbeepmeep/Wan2GP)** já junta todos numa tela só e baixa cada modelo sozinho na primeira vez:
- InfiniteTalk e LongCat Avatar (fala);
- Wan 2.2 5B FastWan e LTX-2.5 (movimento);
- Qwen Image Edit Plus 2511 (identidade);
- Lynx (troca de rosto);
- Qwen3 TTS e OmniVoice (voz).

A licença (WanGP Community License 2.0) libera uso dentro da empresa e venda do que for gerado.

- **Notebook:** `central/clone/ciello_clone_kaggle.ipynb`. No Kaggle: *File → Import Notebook*, GPU T4 x2, Internet On, *Run All* e abrir o link `gradio.live`.
- Foi baseado em dois notebooks da comunidade: [jigs10/ltx-2.5-kaggle-wan2gp](https://github.com/jigs10/ltx-2.5-kaggle-wan2gp) (LTX-2.5 a ~15 min por 5 s de vídeo numa T4) e [Square-Zero-Labs/Wan2GP-on-Colab](https://github.com/Square-Zero-Labs/Wan2GP-on-Colab) (indica o Wan 2.2 5B FastWan em 480p para 16 GB).
- Alternativa só para fala: [sruckh/InfiniteTalk-Google-Collab](https://github.com/sruckh/InfiniteTalk-Google-Collab) (ComfyUI, MIT) com o fluxo oficial `wanvideo_2_1_14B_I2V_InfiniteTalk_example_03.json` do [ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper).
- **Ainda não testado no Kaggle por mim:** este ambiente não acessa o Kaggle nem o Hugging Face. O primeiro teste é o do usuário.

## Fluxo no gerador

```
fotos do usuário ─► [Qwen-Image-Edit] ─► cenas em imagem (escritório, rua, loja)
                                            │
roteiro ─► central/voz.py (voz clonada) ─► narração por cena
                                            │
              ┌─────────────────────────────┼──────────────────────────────┐
     cena falando                   cena em movimento               ajuste de boca
  [InfiniteTalk: imagem+fala]   [Wan 2.2 I2V / Wan-Animate]        [LatentSync se preciso]
              └─────────────────────────────┼──────────────────────────────┘
                                            ▼
             reels/public/clone/*.mp4 ─► Remotion "CloneReel" (legenda, rótulos, cartão final)
                                            ▼
                         central/mixar.py (narração + trilha, -14 LUFS) ─► Metricool
```

### O que já está no repositório

- **`reels/src/CloneReel.tsx`**: composição que monta um reel a partir de uma **montagem JSON**, sem escrever código novo:
  - cada cena é um clipe em `reels/public/clone/`, com zoom lento e corte suave;
  - pílula de rótulo opcional no topo;
  - legenda karaokê no modo `video`, com letra clara e sombra sobre a filmagem;
  - cartão final "Comente PALAVRA" da marca.
- Cena sem clipe vira um **quadro de rascunho** com a descrição da cena. Dá para montar e aprovar o reel inteiro antes de gerar qualquer vídeo.
- **`reels/src/montagens/exemplo-clone.json`**: exemplo de reel do CRM com 4 cenas (fala no escritório, andando na sua cidade, loja com celular, CTA).
- `render.mjs` aceita `--props=montagem.json`:

```bash
cd reels
node render.mjs CloneReel ../midia/clone-crm.mp4 --props=src/montagens/exemplo-clone.json
python ../central/mixar.py ../midia/clone-crm.mp4 ../audio/clone-crm/narracao.wav ../midia/final/clone-crm.mp4
```

Os tempos das cenas e das `falas` vêm do `tempos.json` do `central/voz.py`, como nos outros reels.

## Material que o usuário precisa produzir (uma vez)

1. **20 a 30 fotos**: rosto de frente, de lado e 3/4, meio corpo e corpo inteiro, 2 ou 3 roupas, luz de dia sem sombra dura. É a base da identidade.
2. **3 vídeos curtos de referência de movimento** (10 s cada, celular na vertical): andando em direção à câmera, gesticulando enquanto fala e mexendo no celular. O Wan-Animate usa esses movimentos.
3. **10 s de voz limpa** (já pedido para o `central/voz.py`).

## Cuidados

- **Só a imagem e a voz do próprio o usuário**, nunca de outra pessoa.
- Marcar o post como **conteúdo gerado por IA** (`isAiGenerated: true` no Metricool/Instagram). Isso evita punição da plataforma e mantém a confiança, que é o que vende consultoria.
- Os clipes abertos ainda falham em mãos, texto em telas e movimentos longos. Use clipes curtos (3 a 6 s), cortes frequentes e deixe as telas do CRM para o Remotion (mockup real), não para a IA.

## Roteiro de construção

| Etapa | Entrega |
|---|---|
| 1. Identidade | Notebook Kaggle com Qwen-Image-Edit: fotos → 5 cenas do clone aprovadas |
| 2. Fala | Notebook Kaggle com InfiniteTalk: cena + narração → clipe falando. Teste de sincronia com áudio em português |
| 3. Movimento | Wan 2.2 I2V e Wan-Animate com os vídeos de referência |
| 4. Primeiro reel | Montagem do `exemplo-clone.json` com clipes reais, mixagem e publicação |
| 5. Com investimento | LoRA do rosto (ai-toolkit) em GPU alugada, 720p, e comparação com Kling/Veo via API |

## Fontes

- InfiniteTalk: [GitHub MeiGen-AI](https://github.com/MeiGen-AI/InfiniteTalk) · [artigo](https://arxiv.org/pdf/2508.14033)
- Wan-S2V: [artigo](https://arxiv.org/html/2508.18621v1) · OmniAvatar: [artigo](https://arxiv.org/pdf/2506.18866) · Kandinsky S2V (out/2026): [artigo](https://arxiv.org/html/2610.19290v1) · benchmark de corpo inteiro: [WB-DH](https://arxiv.org/pdf/2508.08891)
- Wan2.2-Animate: [model card](https://huggingface.co/aiplexdeveloper/Wan2.2-Animate-14B/blob/main/README.md) · [fluxo ComfyUI](https://comfy.org/workflows/use-cases/ai-character-replacement/) · [guia](https://aireiter.com/blog/wan2-2-animate-guide)
- Wan2GP: [GitHub](https://github.com/deepbeepmeep/Wan2GP) · [instalação AMD](https://github.com/deepbeepmeep/Wan2GP/blob/main/docs/AMD-INSTALLATION.md) · [VRAM Wan 2.2 e LTX-2](https://evezone.evetech.co.za/quick-bytes/vram-needed-for-local-ai-video-generation-wan-2-2-and-ltx-2)
- LTX-2: [licença](https://ltx.io/model/license) · [Wikipedia](https://en.wikipedia.org/wiki/LTX_(text-to-video_model))
- Qwen-Image-Edit-2511: [Hugging Face](https://huggingface.co/Qwen/Qwen-Image-Edit-2511) · [The Decoder](https://the-decoder.com/qwen-updates-image-editing-model-with-better-character-consistency/)
- LoRA de personagem: [ai-toolkit (guia)](https://localaimaster.com/blog/ai-toolkit-lora-training-guide) · [consistência no Wan 2.2](https://www.runcomfy.com/trainer/ai-toolkit/wan-2-2-i2v-character-consistency-lora)
- Lip sync: [licenças 2026](https://www.creativeainews.com/articles/open-source-lip-sync-licenses-commercial-use-2026/) · [LatentSync](https://sync.so/blog/what-is-latentsync) · [MuseTalk](https://sync.so/blog/what-is-musetalk)
- Alternativas ao Higgsfield: [Open-Higgsfield-AI](https://github.com/omidvarnia/Open-Higgsfield-AI) · [lista 2026](https://www.myarchitectai.com/blog/higgsfield-alternatives)
- GPU grátis: [Kaggle](https://agentdeals.dev/vendor/kaggle) · [ComfyUI no Kaggle](https://lilys.ai/notes/pt/comfyui-20251214/comfyui-free-kaggle-pc-mobile) · [ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu)
