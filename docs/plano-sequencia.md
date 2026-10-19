# Plano-sequência: o padrão de vídeo "feito no Claude" na identidade da Ciello

## De onde veio

| Fonte | O que aproveitamos | O que **não** usamos |
|---|---|---|
| Reel de referência (@viniciusguimaraes.ia, 40 s, enviado pelo Mateus) | Medidas de ritmo e a linguagem visual: papel creme com cidade em traço, texto que se monta palavra a palavra com destaque colorido, card de legenda, janela escura que nasce de um card, contadores e gráficos, texto riscado trocado por pílula, rede ligando um centro a vários celulares, caixa de comentário com "Publicado ✓" e "DM enviada" | O vídeo em si (não vai para o repositório), os textos e a cor laranja |
| [onetake](https://github.com/feitangyuan/onetake) | Os princípios: algo continua de uma cena para a outra (sem troca de slide), ritmo com durações variadas, câmera que antecipa, pousa e balança de leve, interface reconstruída em vez de gravada, e um "oráculo" que mede o vídeo | **O código.** A licença é PolyForm **Noncommercial**, então não pode ser usado em conteúdo comercial |
| [HyperFrames](https://github.com/heygen-com/hyperframes) (HeyGen, Apache-2.0) | Foi a ferramenta do reel de referência. Fica como alternativa se a empresa passar de 3 pessoas (limite da licença grátis do Remotion) | Não instalado: mantemos uma ferramenta só (Remotion) |

## Medidas da referência (`python central/analisar_video.py`)

- 40,5 s, **só 4 cortes secos**: o resto são transições que transformam um elemento no próximo.
- **~60% do tempo com o fundo calmo**: só elementos pequenos se mexendo.
- **~2,2 viradas grandes a cada 10 s**: uma a cada 3–5 s, quase sempre um painel escuro grande entrando ou saindo.
- Planos variando 6,5x (o menor de ~1 s, o maior de ~11 s).

## O kit (`reels/src/plano/kit.tsx`)

| Peça | Para quê |
|---|---|
| `Papel` | Fundo creme com o horizonte de Chapecó (com a catedral) em traço fino e a marca d'água |
| `Cinetico` | Frase palavra a palavra; `*palavra*` sai em ouro; `riscado` passa o risco por cima |
| `Bloco`, `MarcaCiello`, `IconeConversa` | Ícones em card branco com sombra |
| `Pilula` | Pílulas ✓ (verde), ✕ (vermelha) e ouro |
| `Janela` | Card branco que vira janela escura estilo Mac (`morph` 0 → 1) |
| `CardLegenda` | Card de legenda embaixo da janela |
| `Contador` | Número subindo com desaceleração |
| `camera` | Chaves `[tempo, x, y, zoom]`, balanço de mão e tranco ao pousar |

## Regras para cada filme novo

1. **Um fio que atravessa tudo.** No filme do CRM, as mensagens perdidas do começo viram os cards do funil, a rede da equipe se recolhe num ponto dourado e esse ponto pousa no "Comenta".
2. **Uma virada grande a cada 3–5 s**, de preferência um painel escuro grande entrando ou saindo, ou um soco de câmera. Entre as viradas, só elementos pequenos se mexem.
3. **Interface reconstruída** (o CRM é desenhado em código, com o selo "exemplo"), nunca número inventado apresentado como resultado.
4. **Antes de entregar:** `python central/analisar_video.py midia/X.mp4 --ref referencia.mp4` precisa dar **aprovado**.

## Primeiro filme: "A conversa que não se perde" (`CrmPlano`)

- **Arquivos:** roteiro e falas em `roteiros/2026-10-27-crm-plano.json`; vídeo em `midia/2026-10-27-crm-plano.mp4`; com trilha em `midia/final/`; capa em `midia/capas/`.
- **Resultado do oráculo:** 65% de fundo calmo, 1,6 virada a cada 10 s e continuidade 0,76. **Aprovado.**
- **Falta:** a narração com a voz do Mateus (`central/voz.py`). Depois, ajustar as constantes de tempo do `CrmPlano.tsx` (SAI0, CARD, VOA, MOVE, SAIJ, OBJ, RISCA, HUB, JUNTA, CTA) pelos tempos da fala.
- **Dá para melhorar com prints reais do CIELLO CRM:** com eles, a janela reproduz as telas verdadeiras do produto.
