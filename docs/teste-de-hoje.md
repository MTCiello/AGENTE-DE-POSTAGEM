# Teste de hoje à noite (19/10)

Roteiro para baixar o assistente no seu PC (Windows) e testar tudo, com foco no **Ciello OS e no escritório novo** (em Python, sem Node). Marque o que deu certo. Se algo falhar, me mande o `estado\verificacao.txt` ou um print da mensagem de erro.

**Tempo:** uns 40 minutos para o essencial (passos 1 a 5). O resto é opcional.

**Antes de começar:** o Claude Code instalado e com login feito (é ele que faz os agentes trabalharem). Para conferir, abra o PowerShell e rode `claude --version`. Se não tiver: `irm https://claude.ai/install.ps1 | iex` e depois `claude` para entrar na conta.

## 1. Baixar (5 min)

**Primeira vez, com Git (recomendado, facilita as próximas atualizações):**
```powershell
git clone -b ccr-75504115-gpanzf https://github.com/MTCiello/AGENTE-DE-POSTAGEM.git C:\Ciello\agente-de-postagem
```

**Já tinha baixado com Git:** dentro da pasta do assistente:
```powershell
git pull
```

**Sem Git:** baixe o ZIP, extraia em `C:\Ciello\` e renomeie a pasta para `agente-de-postagem`:
https://github.com/MTCiello/AGENTE-DE-POSTAGEM/archive/refs/heads/ccr-75504115-gpanzf.zip

> Se for **substituir** uma pasta antiga pelo ZIP novo, copie antes as pastas que só existem no seu PC: `comercial\` (leads), `financeiro\`, `estado\` e `founder\`. Elas não estão no GitHub de propósito.

## 2. Instalar (10 a 20 min) · clique duas vezes em `instalar.cmd`

- Se faltar Git, Node, ffmpeg ou Python, ele instala pelo winget e pede para **fechar e rodar de novo**.
- Depois cria o ambiente Python (`.venv`) e instala o Remotion (`reels`, o único que ainda usa Node).
- No fim pergunta se instala a voz (uns 3 GB). Se responder **S** e o seu Python for o 3.13, ele instala o Python 3.12 e refaz o ambiente do assistente nele, porque a voz ainda não roda no 3.13 (se pedir, feche e rode o `instalar.cmd` de novo).
- O aviso amarelo `npm warn install-scripts ... esbuild` é só aviso do npm novo: pode ignorar.
- Se o Windows avisar "o Windows protegeu o computador" num `.cmd`: **Mais informações → Executar assim mesmo**.

## 3. Verificar tudo (5 a 10 min) · clique duas vezes em `testar.cmd`

Ele roda cada função de ponta a ponta e mostra `[ok]`, `[aviso]` ou `[FALHA]`:

| Verificação | O que significa se passar |
|---|---|
| Python, ffmpeg, Node, bibliotecas | O PC está pronto |
| Testes automáticos | Radar, ganchos, SDR, financeiro, Ciello OS e o escritório funcionam |
| Ciello OS | A área de trabalho sobe e responde |
| Escritório de agentes | A tela do escritório está compilada e os 6 personagens e 38 móveis carregam (sem Node) |
| Montagem final, oráculo de ritmo | Vídeo + trilha no volume do Instagram e o plano-sequência no padrão |
| SDR | Gera as buscas e acha o buscador do Google Maps (o `instalar.cmd` baixa sozinho) |
| Radar (internet) | Mostra **aviso** se alguma fonte estiver fora do ar |
| Capa (Remotion) | Na 1ª vez demora: o Remotion baixa o navegador dele |
| Voz | **Aviso** é normal se você não instalou a voz |

- [ ] Terminou com **0 falhas**.

## 4. Ciello OS · clique duas vezes em `Ciello.cmd`

Abre uma janela preta (o servidor, deixe aberta) e o Ciello OS numa janela própria do Edge. **Fechar a janela preta desliga tudo.**

- [ ] Abriu a área de trabalho com o **escritório de fundo, centralizado**, no azul da Ciello, e a barra de tarefas embaixo.
- [ ] Os apps estão no **menu Iniciar** (botão da nuvem): Bom dia, Financeiro, Comercial, Conteúdo, Equipe...
- [ ] Janelas: arrastar pela barra, redimensionar pelas bordas, duplo clique maximiza, arrastar até a borda encaixa na metade da tela.
- [ ] Na janela **Bom dia**, o botão **Atualizar briefing** abre uma janela com a saída ao vivo.

## 5. O escritório novo (o principal de hoje, ~15 min)

**Apresentação (só na 1ª vez):**
- [ ] Um personagem apresenta o escritório em português.
- [ ] No passo dos hooks, clique **Instalar hooks**. Isso acrescenta os avisos do Claude Code em `~/.claude/settings.json` (guarda uma cópia como `settings.json.ciello.backup`) e troca os hooks antigos do pixel-agents, se você os tinha.
- [ ] Se você já usava o pixel-agents, o seu layout veio junto. Se não, entrou o layout da Ciello (Pesquisa, Estúdio, Comercial, Análise & Anúncios, Postagem).

**Engrenagem (botão ao lado do escritório na barra de tarefas):**
- [ ] Sem a engrenagem, o escritório fica limpo (sem botões).
- [ ] Com a engrenagem: aparecem **+ Agente, Layout, Configurações**, os botões de zoom e os cartões dos agentes. Os menus estão nas cores da Ciello (marfim e dourado) e em português.
- [ ] **Configurações:** "Detecção instantânea (hooks)" aparece marcada.

**Mover e zoom:**
- [ ] Segurar o **botão do meio (scroll)** e arrastar move o escritório. O scroll sozinho também move.
- [ ] **Ctrl + scroll** aproxima e afasta, e para em 2x e 6x.
- [ ] Menu Iniciar → **Centralizar escritório** volta para o meio.

**Agentes trabalhando:**
- [ ] Engrenagem → **+ Agente**: abre o Claude Code numa janela nova, já na pasta do assistente, e um personagem novo entra no escritório.
- [ ] Nessa janela, rode `/bom-dia`. O personagem senta e "digita"; os balões mostram o que ele faz em português ("Lendo...", "Rodando...").
- [ ] Rode `/comercial`. Os ajudantes (sdr, closer...) aparecem ao lado do coordenador.
- [ ] **Clique no personagem** do coordenador: abre a janela do agente que está trabalhando com ele (ex.: SDR). Clique num ajudante: abre a janela dele.
- [ ] Quando o Claude Code pede permissão para algo, aparece o balão de "..." em cima do personagem na hora (é o hook funcionando).
- [ ] Ao fechar a janela do Claude Code (`/exit`), o personagem sai do escritório.

**Layout:**
- [ ] Engrenagem → **Layout**: mude um móvel de lugar, **Salvar**, feche o `Ciello.cmd` e abra de novo. A mudança ficou.

Se algo do escritório falhar, me mande um print e o que aparece na janela preta do `Ciello.cmd`.

## 6. Ver o que já foi produzido (5 min)

- [ ] `midia\final\2026-10-27-crm-plano.mp4`: o plano-sequência do CRM. Nota de 0 a 10 comparando com o reel de referência: ____
- [ ] `midia\capas\`: as capas da semana.
- [ ] `radar\2026-10-19.md`: a pauta sugerida para a semana de 26/10.
- [ ] `metricas\relatorio-2026-10-19.md`: o primeiro relatório do perfil.

## 7. SDR de verdade (opcional, ~15 min)

O `instalar.cmd` já baixa o buscador do Google Maps para `comercial\bin\`. Se o `testar.cmd` ainda avisar que falta, rode `python central\sdr.py instalar-scraper`. Na 1ª busca ele baixa o navegador que usa (uns minutos).

Num terminal na pasta do assistente:
```powershell
.venv\Scripts\activate
python central\sdr.py consultas --segmentos imobiliaria odontologia --cidades "Chapecó SC"
python central\sdr.py buscar
python central\sdr.py qualificar comercial\bruto\resultados.csv
python central\sdr.py abordar --top 10
```
- [ ] Abriu `comercial\abordagens\AAAA-MM-DD.md` com mensagens e links do WhatsApp.
- [ ] As empresas do topo são bons clientes para o CRM? Anote 2 que estão fora do lugar.

## 8. Chefe de gabinete, financeiro, vigia e pós-venda (opcional, ~15 min)

```powershell
.venv\Scripts\activate
python central\briefing.py                     # as 3 prioridades de hoje
python central\vigia.py checar                 # preço e oferta dos concorrentes
python central\financeiro.py cliente --empresa "Cliente Teste" --valor 149 --dia 10
python central\financeiro.py faturar
python central\financeiro.py importar C:\caminho\extrato.ofx   # extrato do banco em OFX
python central\financeiro.py resumo
```
- [ ] O briefing faz sentido para o seu dia? O que faltou: ____
- [ ] A vigia abriu as 5 páginas? (URL que falhar: troque em `comercial\concorrentes.json`)
- [ ] As despesas do extrato caíram na categoria certa? Quantas ficaram "a classificar": ____
- [ ] Opcional: `agendar.cmd` para o briefing sair sozinho às 7h.

## 9. Clone no Kaggle e voz (opcionais, para outro dia se faltar tempo)

**Clone (~1 h, quase tudo esperando download):** kaggle.com → conta com telefone verificado → *Create → New Notebook → File → Import Notebook* → `central\clone\ciello_clone_kaggle.ipynb` → **GPU T4 x2** e **Internet On** → *Run All* → abra o link `gradio.live` e siga o "Teste desta noite" no fim do notebook. **Desligue a sessão (Stop session) no fim.**
- [ ] Boca acompanha o português? 0 a 10: ____ · Parece real? 0 a 10: ____

**Voz (se instalou no passo 2):**
```powershell
.venv\Scripts\activate
python central\voz.py roteiros\2026-10-27-crm-plano.json --saida audio\crm --nome CRM
```
- [ ] Naturalidade da narração 0 a 10: ____

## Se algo der errado

| Sintoma | O que fazer |
|---|---|
| A janela preta do `Ciello.cmd` diz que a porta 3200 está em uso | Já tem um Ciello OS aberto: feche a outra janela preta (ou reinicie o PC) |
| Abriu no navegador comum em vez de janela própria | Normal se o Edge não for encontrado; funciona igual |
| O escritório ficou só com a logo da Ciello | O `Ciello.cmd` foi aberto com `--sem-escritorio`, ou a pasta `central\escritorio\web\escritorio` está faltando: baixe de novo |
| Os personagens demoram uns segundos para reagir | Os hooks não foram instalados: engrenagem → Configurações → marque **Detecção instantânea (hooks)** |
| Quer tirar os hooks | Mesmo lugar, desmarque. A cópia do seu `settings.json` original fica em `~/.claude/settings.json.ciello.backup` |
| "+ Agente" abre uma janela dizendo que o Claude Code não foi encontrado | Instale com `irm https://claude.ai/install.ps1 \| iex`, abra um terminal novo e tente de novo |
| O personagem não abre janela ao clicar | O agente precisa de nome: ajudante com a descrição começando pelo nome (`sdr: ...`), como os comandos `/bom-dia` e `/comercial` já fazem |

## O que eu preciso de volta
1. O `estado\verificacao.txt`.
2. Os itens do passo 5 que não funcionaram (com print, se der).
3. Sua nota para o vídeo do CRM e o que mudaria.
4. Preço e planos do CRM e o cabeçalho da planilha de importação.
