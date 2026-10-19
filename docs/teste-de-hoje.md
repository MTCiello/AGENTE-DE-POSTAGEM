# Teste de hoje à noite (19/10)

Tudo aqui funciona sem o seu rosto e sem a sua voz. Marque o que deu certo. Se algo falhar, me mande o `estado\verificacao.txt` ou a mensagem de erro.

## 1. Baixar (5 min)

**Sem Git:** baixe o ZIP, extraia em `C:\Ciello\` e renomeie a pasta para `agente-de-postagem`:
https://github.com/MTCiello/AGENTE-DE-POSTAGEM/archive/refs/heads/ccr-75504115-gpanzf.zip

**Com Git:**
```powershell
git clone -b ccr-75504115-gpanzf https://github.com/MTCiello/AGENTE-DE-POSTAGEM.git C:\Ciello\agente-de-postagem
```

## 2. Instalar (10–20 min) · clique duas vezes em `instalar.cmd`

- Se faltar Git, Node, ffmpeg ou Python, ele instala pelo winget e pede para **rodar de novo**.
- Depois cria o ambiente Python (`.venv`) e instala o Remotion (`reels`).
- No fim pergunta se instala a voz: **ok responder "N" hoje** (são ~3 GB).

## 3. Verificar tudo (5–10 min) · clique duas vezes em `testar.cmd`

Ele roda cada função de ponta a ponta e mostra `[ok]`, `[aviso]` ou `[FALHA]`:

| Verificação | O que significa se passar |
|---|---|
| Python, ffmpeg, Node, bibliotecas | O PC está pronto |
| Testes automáticos | Radar, ganchos e SDR funcionam |
| Montagem final | Vídeo + trilha saem no volume do Instagram |
| Oráculo de ritmo | O plano-sequência do CRM está no padrão do reel de referência |
| Relatório semanal, biblioteca de ganchos | Analista e pesquisador funcionando |
| SDR | Gera as buscas. Mostra **aviso** até você baixar o executável do Google Maps (passo 6) |
| Radar (internet) | Busca nas fontes. Mostra **aviso** se alguma estiver fora do ar |
| Capa (Remotion) | Na 1ª vez demora: o Remotion baixa o navegador dele |
| Voz | **Aviso** é normal se você não instalou a voz |

- [ ] Terminou com **0 falhas**.

## 4. Escritório (pixel-agents) · clique duas vezes em `Escritorio-Ciello.cmd`

- [ ] Abriu no navegador o pixel-agents com as 3 salas da Ciello (Pesquisa/Estúdio, Comercial, Análise/Postagem).
- [ ] Na apresentação, aceite a instalação dos hooks.
- [ ] Abra o Claude Code nesta pasta (botão **+ Agent** do escritório ou um terminal) e rode `/comercial`: o coordenador senta numa mesa e os agentes aparecem ao lado dele trabalhando.

## 5. Ver o que já foi produzido

- [ ] `midia\final\2026-10-27-crm-plano.mp4`: o plano-sequência do CRM. Nota de 0 a 10 comparando com o reel de referência: ____
- [ ] `midia\capas\`: as capas da semana.
- [ ] `radar\2026-10-19.md`: a pauta sugerida para a semana de 26/10.
- [ ] `metricas\relatorio-2026-10-19.md`: o primeiro relatório do perfil.
- [ ] Painel de crescimento: `.venv\Scripts\python central\escritorio\servidor.py` (abre a porta 3200).

## 6. SDR de verdade (opcional hoje, ~15 min)

1. Baixe o executável para Windows em https://github.com/gosom/google-maps-scraper/releases e salve em `comercial\bin\`.
2. Num terminal na pasta do assistente:
```powershell
.venv\Scripts\activate
python central\sdr.py consultas --segmentos imobiliaria odontologia --cidades "Chapecó SC"
python central\sdr.py buscar
python central\sdr.py qualificar comercial\bruto\resultados.csv
python central\sdr.py abordar --top 10
```
- [ ] Abriu `comercial\abordagens\AAAA-MM-DD.md` com mensagens e links do WhatsApp.
- [ ] As empresas do topo são bons clientes para o CRM? Anote 2 que estão fora do lugar.

## 7. Clone no Kaggle (opcional, ~1 h, quase tudo esperando download)

1. kaggle.com → criar conta → verificar o telefone.
2. *Create → New Notebook → File → Import Notebook* → `central\clone\ciello_clone_kaggle.ipynb`.
3. Painel da direita: **GPU T4 x2** e **Internet On** → *Run All* → abrir o link `gradio.live`.
4. Siga o "Teste desta noite" no fim do notebook.
- [ ] Tempo da foto: ____ · da fala (~10 s): ____ · do andando (~5 s): ____
- [ ] Boca acompanha o português? 0–10: ____ · Parece real? 0–10: ____
- **Desligue a sessão (Stop session) no fim.**

## 8. Voz (opcional) · se instalou a voz no passo 2
```powershell
.venv\Scripts\activate
python central\voz.py roteiros\2026-10-27-crm-plano.json --saida audio\crm --nome CRM
```
- [ ] Kokoro gerou a narração em português. Naturalidade 0–10: ____

## O que eu preciso de volta
1. O `estado\verificacao.txt`.
2. Sua nota para o vídeo do CRM e o que mudaria.
3. Preço e planos do CRM e o cabeçalho da planilha de importação.
