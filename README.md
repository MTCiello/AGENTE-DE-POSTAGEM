# AGENTE DE POSTAGEM

Agente semanal de reels da **Ciello** (@ciellotec).

Toda semana ele pesquisa os vídeos de IA que estão viralizando, adapta 3 temas para pequenos negócios, gera os reels com a identidade da marca e agenda no Metricool (segunda, quarta e sexta às 10h).

- `AGENTE.md` — o procedimento completo que o agente segue
- `gerador/render_reel.py` — transforma um roteiro JSON em reel 1080×1920 com trilha
- `roteiros/` — roteiros de cada reel
- `midia/` — vídeos publicados (servidos ao Metricool por link público)
- `historico.md` — o que já foi postado
- `central/` — narração, legendas e montagem final no PC, sem créditos (ver `central/README.md`)
- `docs/app-comercial.md` — arquitetura do app de agentes (conteúdo + comercial)
- `docs/clone-digital.md` — clone digital hiper-realista com modelos abertos e o modelo `CloneReel`

Gerar um reel manualmente:

```bash
pip install pillow numpy   # precisa de ffmpeg instalado
python3 gerador/render_reel.py roteiros/2026-10-18-piloto.json midia/teste.mp4
```
