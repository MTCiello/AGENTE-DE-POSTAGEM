# Teste de hoje (23/10): o que chegou de madrugada

Atualize a pasta (`git pull` dentro do assistente, ou baixe o ZIP de novo, guardando antes `comercial\`, `financeiro\`, `estado\` e `founder\`). Depois abra o Ciello OS e siga a lista. Uns 30 minutos.

- [ ] **Bom dia:** em uma prioridade, clique em **Abrir** e confira se caiu na janela e na aba certas. Em outra, clique em **Hoje não** e veja se ela some.
- [ ] **Primeiros passos → Cadastre os clientes que já pagam:** cadastre de verdade os CRMs e as hospedagens que já pagam. Isso liga a cobrança, a carteira e a meta.
- [ ] **Financeiro → Clientes:** confira a faixa "Saúde da carteira" e a nota de cada cliente (passe o mouse para ver os motivos). Teste **Conversei**.
- [ ] **Financeiro → Metas e decisões → Definir a meta:** escolha clientes e mês. Confira o "Ritmo da semana" e se ele aparece no topo de **Comercial → Hoje**.
- [ ] **Metas e decisões → decisões em aberto:** clique em **Discutir** em uma ideia de preço (abre o Claude) e **Decida** outra. Confira em "Regras da casa".
- [ ] **Plano do ano → Simular preço:** mude a mensalidade e o % no anual e veja quantos clientes pagam a conta.
- [ ] **Financeiro → Importar extrato** (OFX ou CSV de 2 a 3 meses) e depois **Lançamentos → Gastos fixos:** apareceu algo em dobro, que subiu ou que não veio?
- [ ] **Comercial → Quentes → Agendar demo:** marque uma demo e confira a mensagem de confirmação e o link do Google Agenda.
- [ ] **Conteúdo → Produção → Postar** (post de 27/10 ou 29/10): vídeo, capa e legenda num lugar só.

O que travar ou estranhar, me mande um print.

---

# Teste de 19/10 (instalação e verificação)

Roteiro para baixar o assistente no seu PC (Windows) e testar tudo, com foco no **Ciello OS e no escritório novo** (em Python, sem Node). Marque o que deu certo. Se algo falhar, me mande o `estado\verificacao.txt` ou um print da mensagem de erro.

**Tempo:** pouco mais de 1 hora para o essencial (passos 1 a 7). O resto é opcional.

**Antes de começar:** o Claude Code instalado e com login feito (é ele que faz os agentes trabalharem; o passo 6 mostra o que funciona mesmo sem ele). Para conferir, abra o PowerShell e rode `claude --version`. Se não tiver: `irm https://claude.ai/install.ps1 | iex` e depois `claude` para entrar na conta.

## 1. Baixar (5 min)

**Primeira vez, com Git (recomendado, facilita as próximas atualizações):**
```powershell
git clone https://github.com/MTCiello/AGENTE-DE-POSTAGEM.git C:\Ciello\agente-de-postagem
```

**Já tinha baixado com Git:** dentro da pasta do assistente (desde 23/10 tudo está na `main`):
```powershell
git checkout main
git pull
```

**Sem Git:** baixe o ZIP, extraia em `C:\Ciello\` e renomeie a pasta para `agente-de-postagem`:
https://github.com/MTCiello/AGENTE-DE-POSTAGEM/archive/refs/heads/main.zip

> Se for **substituir** uma pasta antiga pelo ZIP novo, copie antes as pastas que só existem no seu PC: `comercial\` (leads), `financeiro\`, `estado\` e `founder\`. Elas não estão no GitHub de propósito.

## 2. Instalar (10 a 20 min) · clique duas vezes em `instalar.cmd`

- Se faltar Git, Node, ffmpeg ou Python, ele instala pelo winget e pede para **fechar e rodar de novo**.
- Depois cria o ambiente Python (`.venv`) e instala o Remotion (`reels`, o único que ainda usa Node).
- Ele também instala o `pywinpty`, que faz o terminal do Claude rodar dentro do Ciello OS. **Se você já tinha instalado antes, rode o `instalar.cmd` de novo.**
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

**Como usar (resumo):** os 13 agentes moram no escritório. Parados, eles andam, conversam entre si (balão azul) e descansam na mesa. Para um agente trabalhar, ele precisa ser chamado pelo Claude Code, e há 3 jeitos:
1. **Pela janela do agente:** clique no personagem (ou Menu Iniciar → agente) → escreva o que ele deve fazer em **Iniciar** (ou clique numa sugestão) → **Iniciar no Claude Code**. Abre o terminal do Claude aqui dentro com o pedido; o agente vai para um PC e começa.
2. **Pelo terminal:** ícone do terminal na barra de tarefas (ao lado do escritório) e escreva, por exemplo, "use o sdr para gerar 20 leads de odontologia em Chapecó", ou um comando: `/bom-dia`, `/comercial`, `/semana`.
3. **Pelos comandos da janela:** os botões como `/comercial` chamam a equipe toda daquela rotina.

Os botões de **Rodar agora** (ex.: "Follow-ups de hoje") continuam rodando a ferramenta direto, sem o Claude Code.

**Agentes trabalhando:**
- [ ] Assim que abre, o escritório tem os 13 agentes andando, conversando e descansando nas mesas (PCs desligados).
- [ ] Clique no **SDR** no escritório: abre a janela dele. Em **Iniciar**, escolha "listar os follow-ups de hoje" → **Iniciar no Claude Code**. Abriu a janela **Claude Code · SDR** com o pedido já enviado?
- [ ] No escritório, o SDR foi até um PC, o PC ligou e ele "digita"; os balões mostram o que ele faz em português ("Lendo...", "Rodando...").
- [ ] Quando termina, aparece o visto verde em cima dele e ele volta para a rotina.
- [ ] Ícone do terminal na barra de tarefas → rode `/comercial`: o SDR e o Closer vão para os PCs da área Comercial.
- [ ] Quando o Claude Code pede permissão, aparece o balão de "..." em cima de quem está pedindo (é o hook funcionando). Responda no terminal.
- [ ] No terminal: Ctrl+C com texto selecionado copia; Ctrl+V cola; redimensionar a janela ajusta o terminal.
- [ ] Engrenagem → **+ Agente** também abre um terminal novo aqui dentro.
- [ ] Fechar a janela do terminal encerra aquele Claude Code.

**Layout e áreas:**
- [ ] Engrenagem → **Layout**: mude um móvel de lugar, **Salvar**, feche o `Ciello.cmd` e abra de novo. A mudança ficou.
- [ ] Engrenagem → **Layout** → clique numa área → **Adicionar agente…** e escolha alguém de outra área (ex.: o Analista na Postagem). Ele vai na hora para uma mesa da área nova, e continua lá depois de fechar e abrir o `Ciello.cmd`.
- [ ] **Sem duplicados:** com uma ou duas sessões do Claude Code abertas, feche e abra o `Ciello.cmd`. Cada agente aparece uma vez só (nada de dois SDRs).

Se algo do escritório falhar, me mande um print e o que aparece na janela preta do `Ciello.cmd`.

## 6. Operar sem o Claude (~10 min)

O Ciello OS não depende do Claude: os números e o dia a dia rodam direto no seu PC. Acabaram os tokens? Feche o Claude Code e teste tudo isto só pelas janelas (cada uma mostra o selo verde **Funciona sem o Claude**). Para não misturar com dados reais, use nomes de teste e apague depois (Cancelar no cliente, Perdido no lead).

**Financeiro** (menu Iniciar → Financeiro):
- [ ] **+ Cliente**: "Cliente Teste", R$ 149, dia 10. Apareceu na aba **Clientes**.
- [ ] **Caixa**: informe o saldo do banco de hoje. O "Caixa hoje" mudou.
- [ ] **Gerar faturas** do mês. Em **Visão geral**, a fatura aparece em "Faturas em aberto"; clique **Recebi** e ela some.
- [ ] **Importar extrato**: escolha o OFX (ou CSV) exportado do app do banco. Quantas despesas ficaram "a classificar": ____ (classifique na aba **Lançamentos**, escolhendo a categoria na lista).
- [ ] **Lançar receita/despesa**: um Pix que não passou pelo extrato.
- [ ] Aba **Cobrança e pós-venda**: as mensagens já vêm escritas. **Abrir no WhatsApp** abre a conversa com o texto pronto (nada é enviado sozinho; você revisa e envia). Depois clique **Enviei**.
- [ ] Na aba **Clientes**: **Editar**, **NPS** e **Cancelar** (o cancelado sai do MRR; **Reativar** traz de volta).

**Comercial** (menu Iniciar → Comercial):
- [ ] **+ Lead que chegou**: um nome e um WhatsApp de teste. A resposta pronta aparece com o link do WhatsApp.
- [ ] Aba **Hoje**: os melhores leads novos aparecem com a 1ª mensagem pronta. **Enviei** marca o contato e agenda o follow-up (2, 5 e 10 dias); os follow-ups do dia aparecem aqui com a mensagem certa para a tentativa.
- [ ] Aba **Leads**: busque pelo nome, filtre por etapa, mude a etapa na lista. Mudar para **cliente** abre o cadastro no Financeiro já com a empresa e o WhatsApp do lead.
- [ ] Aba **Buscar leads**: escolha segmentos e cidades → **Buscar no Google Maps** (leva de 5 a 30 minutos) → **Qualificar o resultado**. Ou **Importar planilha** com uma lista que você já tenha.
- [ ] **Exportar para o CRM**: gera a planilha em `comercial\`.

**Conteúdo e Anúncios:**
- [ ] Conteúdo → **Anotar números do Instagram**: copie do app do Instagram (Painel profissional → Insights) os seguidores, o alcance e os números de 1 ou 2 reels. Os cartões atualizam e o **Relatório semanal** usa esse retrato.
- [ ] Anúncios → **+ Campanha**: copie os números do Gerenciador de Anúncios. **Atualizar** muda os números da mesma campanha.
- [ ] **Bom dia**: as 3 prioridades e os números aparecem sem o Claude (o botão **Atualizar briefing** também).

O que precisa do Claude: os agentes (pesquisa, roteiro, vídeo, legendas, análise escrita, puxar números do Metricool). O resto é do OS.

## 7. Objetivos, esteiras e Estúdio de Voz (novo, ~15 min)

**Menu Iniciar:** agora separado em **Criar, Vender, Gerir**, com a caixa "O que você quer fazer?" no alto.
- [ ] Escreva um objetivo na caixa do menu (ex.: "crie 3 vídeos das novidades da semana, faça a capa, a descrição e programe a postagem") e aperte **Enter**. Abre o **Claude Code · Objetivo** com o pedido para o coordenador.
- [ ] O coordenador mostra um plano curto, chama os agentes (cada um vai para o PC no escritório) e **pede a sua aprovação** antes de agendar ou publicar.
- [ ] Digitar só o nome de um app (ex.: "financeiro") e Enter abre o app.

**Objetivos e esteiras** (menu Iniciar → "O que você quer fazer?"):
- [ ] As esteiras prontas mostram a cadeia de agentes (quem trabalha agora fica verde): Semana de conteúdo, Um vídeo sobre um tema, Prospecção do dia, Bom dia, Campanha de anúncio, Fechamento da semana.
- [ ] Rode **Um vídeo sobre um tema** com um tema seu. O roteiro vem para você aprovar.

**Estúdio de Voz** (menu Iniciar → Criar):
- [ ] Se aparecer "A voz ainda não está instalada", clique **Instalar agora** (uns 3 GB; se falhar, rode o `instalar.cmd` e responda **S** na voz).
- [ ] **Gravar**: permita o microfone, leia o texto em voz alta (10 a 20 s) e clique **Parar**. A gravação aparece com o player para ouvir.
- [ ] **Testar**: motor **Sua voz (Chatterbox)** → **Ouvir**. A 1ª vez baixa o modelo (uns minutos). Nota de 0 a 10 para a semelhança com a sua voz: ____
- [ ] Compare com a **Voz pronta (Kokoro)**. Se gostar da sua, **Usar esta voz nos vídeos**: os vídeos novos saem com ela.
- [ ] Opcional, **VoiceStudio**: baixe o instalador do Windows em github.com/debpalash/VoiceStudio/releases, abra o app e volte ao Estúdio de Voz. O cartão fica verde: **Clonar a minha gravação no VoiceStudio**, depois teste com o motor VoiceStudio. Nota comparando com o Chatterbox: ____

## 8. Ver o que já foi produzido (5 min)

- [ ] `midia\final\2026-10-27-crm-plano.mp4`: o plano-sequência do CRM. Nota de 0 a 10 comparando com o reel de referência: ____
- [ ] `midia\capas\`: as capas da semana.
- [ ] `radar\2026-10-19.md`: a pauta sugerida para a semana de 26/10.
- [ ] `metricas\relatorio-2026-10-19.md`: o primeiro relatório do perfil.

## 9. SDR de verdade (opcional, ~15 min)

Pelo Ciello OS: Comercial → aba **Buscar leads** (passo 6). Ou, pela linha de comando:

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

## 10. Chefe de gabinete, financeiro, vigia e pós-venda (opcional, ~15 min)

O financeiro e o pós-venda também ficam todos na janela Financeiro (passo 6). Pela linha de comando:

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

## 11. Clone no Kaggle e voz (opcionais, para outro dia se faltar tempo)

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
| Um formulário diz "Servidor desligado" | A janela preta do `Ciello.cmd` foi fechada: abra de novo (os dados já salvos continuam lá) |
| O personagem não abre janela ao clicar | O agente precisa de nome: ajudante com a descrição começando pelo nome (`sdr: ...`), como os comandos `/bom-dia` e `/comercial` já fazem |

## O que eu preciso de volta
1. O `estado\verificacao.txt`.
2. Os itens dos passos 5, 6 e 7 que não funcionaram (com print, se der), e as notas das vozes.
3. Sua nota para o vídeo do CRM e o que mudaria.
4. Preço e planos do CRM e o cabeçalho da planilha de importação.
