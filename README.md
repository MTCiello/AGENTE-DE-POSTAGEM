# AGENTE DE POSTAGEM

**Instalar e testar no Windows:** `instalar.cmd` → `testar.cmd` → **`Ciello.cmd`** (o app inteiro numa área de trabalho). Passo a passo em `docs/teste-de-hoje.md`.

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
- `docs/teste-de-hoje.md` — roteiro de teste de todas as ferramentas
- `docs/plano-sequencia.md` + `reels/src/plano/` — vídeos em plano-sequência (padrão do reel de referência) e `central/analisar_video.py` (oráculo de ritmo)
- `Ciello.cmd` — **Ciello OS**: área de trabalho com barra de tarefas, janelas que movem e redimensionam, o escritório de agentes de fundo e um app para cada área (`central/escritorio/servidor.py` + `web/`; o escritório é a tela de `escritorio/` com o núcleo em Python de `central/escritorio/nucleo/`, sem Node). Funciona sem o Claude: Financeiro, Comercial, Conteúdo e Anúncios operam direto pelas janelas (`central/escritorio/operacao.py`)
- `radar/` — assuntos em alta por pilar · `conhecimento/ganchos.csv` — biblioteca de ganchos · `metricas/` — retratos semanais e relatórios
- `reels/capa.mjs` — capa do reel a partir do roteiro
- `central/sdr.py` + `comercial/icp.json` — prospecção: leads, abordagem por wa.me, cadência e CSV do CRM
- `.claude/agents/` + `.claude/skills/` — equipe de 13 agentes e comandos `/bom-dia`, `/semana`, `/comercial`, `/segunda`, `/sexta` (ver `docs/equipe.md`)
- `central/briefing.py` — gerente: as 3 prioridades do dia e o placar da semana · `central/financeiro.py` — assinaturas, cobrança, extrato, caixa, MRR/CAC/LTV e pós-venda · `central/vigia.py` — preço e oferta dos concorrentes
- `docs/qualificacao.md` — bateria de testes, nota de cada função e avaliação dos "10 agentes de IA"

Gerar um reel manualmente:

```bash
pip install pillow numpy   # precisa de ffmpeg instalado
python3 gerador/render_reel.py roteiros/2026-10-18-piloto.json midia/teste.mp4
```
