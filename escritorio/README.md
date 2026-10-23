# Escritório de agentes da Ciello (tela)

A tela pixel do escritório que é o fundo do Ciello OS. Começou como fork do
[pixel-agents](https://github.com/pablodelucca/pixel-agents) **v1.5.0** (MIT, © Pablo De Lucca, ver `LICENSE`)
e agora é código nosso: a partir daqui o escritório evolui junto com o assistente (personagens próprios,
personalização do escritório, menus na identidade da Ciello).

O que mudou em relação ao original:

- **Sem servidor Node.** Quem conversa com a tela é o núcleo em Python do Ciello OS
  (`central/escritorio/nucleo/`), que fala o mesmo protocolo (WebSocket `/ws`, mensagens em
  `core/asyncapi.yaml`). Os sprites, os móveis e o layout chegam iguais, pixel a pixel, aos do servidor
  original (conferido com o 1.5.0 do npm).
- **Só a tela foi trazida:** `webview-ui/` (React + canvas) e `core/` (tipos, protocolo e leitura dos
  ativos usada no build). Extensão do VS Code, CLI e terminal embutido ficaram de fora.
- **Ciello no código:** textos em português (o protocolo segue em inglês; `src/office/statusPtBr.ts` traduz o que
  aparece), menus nas cores e fontes da Ciello (`src/index.css`; o que está dentro da cena, `.cena`, segue pixel),
  zoom entre 2x e 6x, controles atrás da engrenagem do Ciello OS, centralizar e clique no personagem abrindo a
  janela do agente (`src/ciello/`). Saíram o changelog, o aviso de versão e o Discord do projeto original.
- O build sai direto em `central/escritorio/web/escritorio/`, que vai para o git: o PC do Mateus não precisa
  de Node para abrir o escritório (o Node continua só para o Remotion).

## Compilar depois de mudar a tela

```
cd escritorio/webview-ui
npm install --legacy-peer-deps
npx vite build
```

Abra o `Ciello.cmd` e confira. Os testes do núcleo ficam em `central/testes/test_escritorio_nucleo.py` e
`central/testes/test_servidor.py`.

## Créditos

- pixel-agents © 2026 Pablo De Lucca, licença MIT (`LICENSE`).
- Personagens baseados no [Metro City](https://jik-a-4.itch.io/metrocity-free-topdown-character-pack), de JIK-A-4,
  como no projeto original.
- Fonte FS Pixel Sans (`webview-ui/public/fonts/`), como no projeto original.
