# Galeria de estilos do Estúdio de Vídeo

157 estilos de vídeo para o Claude produzir os reels, vindos do [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) (LemoLab):

- **Opus 98**: os 98 estilos do filme [OPUSCAR 98](https://lemomo-ai.github.io/lemo-opuscar/opuscar98/), um para cada vencedor do Oscar de Melhor Filme (1927–2025), cada um com um prompt de estilo reutilizável;
- **Biblioteca**: 59 estilos com guia completo (visual, cor, tipografia, movimento, câmera e som).

## Como funciona

1. No Ciello OS, abra **Estúdio de Vídeo → Galeria de estilos** (ou o botão **Escolher estilo** num roteiro).
2. Escolha o estilo, o roteiro (ou escreva um tema) e clique em **Produzir com o Claude**.
3. O Claude Code abre com o pedido pronto (`central/estilos.py → pedido`): o produtor de vídeo lê o guia (`python central/estilos.py ver <estilo>`), monta o vídeo no HyperFrames em 9:16 com a narração do Estúdio de Voz e deixa o rascunho em `midia/estudio/<post>-<estilo>.mp4`.
4. Confira a prévia no cartão do roteiro e clique em **Usar o do estilo** para virar o vídeo final. Nada é publicado sem você.

## Arquivos

| Arquivo | O que é |
|---|---|
| `catalogo.json` | os dois catálogos (nomes em português e inglês, época ou família, prompts) |
| `biblioteca/<estilo>.md` | o guia de cada estilo da biblioteca (`STYLE.md` original) |
| `DIRECTOR.md`, `TECHNIQUE.md` | direção e técnica do lemo-opuscar (o Claude usa como referência) |
| `nomes-pt.json` | os nomes, épocas, famílias e usos em português |
| `importar.py` | refaz tudo a partir de um clone do lemo-opuscar (para trazer estilos novos) |
| `../../central/escritorio/web/estilos/` | as miniaturas da galeria |

Para atualizar quando sair estilo novo no lemo-opuscar:

```
git clone --depth 1 https://github.com/lemomo-ai/lemo-opuscar /tmp/opuscar
curl -LO https://github.com/lemomo-ai/lemo-opuscar/releases/download/films/opuscar98.mp4
python reels/estilos/importar.py /tmp/opuscar --video opuscar98.mp4
```

Estilo novo sem nome em `nomes-pt.json` aparece com o nome em inglês até alguém traduzir. Licenças em [`LICENCA.md`](LICENCA.md).
