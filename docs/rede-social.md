# Rede social no piloto automático

Objetivo: o Ciello OS pesquisa, produz e publica os reels (e os equivalentes no TikTok e no YouTube Shorts) sem você, e só te chama para o que é humano: o lead que quer comprar, a pergunta que o FAQ não cobre, uma conexão que caiu.

## Onde fica cada coisa

| Janela | Para quê |
|---|---|
| **Rede social → Piloto** | Modo (Automático, Aprovar cada post ou Pausado), fila de publicação com **Segurar**, **Aprovar** e **Tentar de novo**, e o diário do que o piloto fez |
| **Rede social → Calendário do mês** | Dia a dia: o post, o pilar, a etapa e o envio em cada rede. Dias vazios recebem o pilar menos usado. Também mostra a previsão do mês (views e seguidores) e o limite do Metricool |
| **Rede social → Comentários** | Caixa de comentários. Quem quer comprar vira lead no Comercial; elogios e perguntas do FAQ o piloto responde sozinho |
| **Rede social → Resultados** | Cada post, 7 dias depois, contra a mediana dos 10 anteriores da mesma rede. Vai sozinho para a biblioteca de ganchos |
| **Conexões** | Conectar, checar e desconectar cada provedor, e escolher por onde cada rede publica |

## A rodada do piloto (de hora em hora)

Rode o `agendar.cmd` uma vez: ele cria a tarefa **Ciello Piloto** no Agendador do Windows. Cada rodada:

1. **Checa as conexões em uso.** Se uma caiu, os posts daquela rede esperam na fila (nada se perde) e o Bom dia avisa.
2. **Sincroniza** números e comentários para o banco local (`estado/ciello.db`) e avalia os posts com 7 dias.
3. **Comentários:**
   - quem quer comprar vira lead no Comercial;
   - elogio e pergunta que o FAQ cobre recebem resposta automática (ajustável);
   - o resto fica para você.
4. **Produção dos próximos 7 dias:**
   - o Claude escreve os roteiros que faltam, com pesquisa e checagem de fatos (no máximo um pedido a cada 6 h);
   - o PC faz narração, vídeo (HyperFrames), capa e legenda.
5. **Publicação** em cada rede ligada, no horário de cada uma:
   - os provedores que agendam (Metricool, YouTube, Ponte com o Claude) recebem o post 12 h antes, e o PC pode estar desligado na hora;
   - os que não agendam (Instagram direto, TikTok) saem na hora, e o PC precisa estar ligado.

Uma trava impede duas rodadas ao mesmo tempo. O que a rotina semanal (ou você) já registrou como agendado no `historico.md` não é agendado de novo.

## Histórico que não se perde

- **Cópia local:** tudo o que vem do Metricool, Instagram, YouTube ou TikTok é copiado para o banco local. Uma sincronização nunca apaga nada.
- **Desconectar:** apaga só a senha. Os posts, os números e os comentários ficam, e a janela Conexões mostra quantos estão guardados de cada provedor.
- **Provedor caiu:** os posts ficam na fila com o motivo e saem quando a conexão volta. Se passar da hora, viram "passou da hora", com **Tentar de novo**.
- **Exportar histórico (CSV):** leva tudo para onde você quiser.
- **Senhas:** ficam no cofre (`estado/cofre.json`). No Windows são cifradas com a proteção do seu usuário (DPAPI), e nada disso vai para o GitHub.

## Conectar cada provedor

### Ponte com o Claude (o que funciona hoje, Metricool grátis)

- **Como é:** já vem ligada para o Instagram. O Claude Code agenda no Metricool pelo conector que você já tem.
- **Plano grátis do Metricool:**
  - 20 posts por mês, e cada rede conta como um post (3 redes × 3 posts por semana passa do limite);
  - guarda só 30 dias de histórico; o resto fica no banco local.
- **Limite no calendário:** o calendário avisa quando o mês passa do limite.

### Metricool pela API (plano Advanced ou Custom)

- **Plano:** a API da Metricool só existe nesses planos.
- **Credenciais:**
  1. Abra Metricool → Configurações da conta → API e copie o token.
  2. O userId e o blogId (a marca) estão no endereço do Metricool.
- **O que ganha:** um conector cobre Instagram, TikTok e YouTube, agenda lá e traz os comentários. O vídeo sobe do PC para a Metricool, sem precisar de link público.

### Instagram direto (API da Meta, sem custo)

- **Pré-requisitos:** conta profissional e um app seu em developers.facebook.com (Facebook Login for Business).
- **Credenciais:** gere um token de longa duração e anote o ID da conta do Instagram. O token vale 60 dias.
- **Publicação:** o reel sobe direto do PC. A Meta não agenda pela API, então o PC precisa estar ligado na hora.

### YouTube Shorts (API do Google, sem custo)

1. No Google Cloud, crie um projeto e ligue a **YouTube Data API v3**.
2. Crie a credencial **OAuth do tipo "App para computador"**.
3. Em Conexões, cole o client id e o secret, salve e clique em **Entrar com o Google**.

**Atenção:** projeto sem a auditoria do Google publica como **privado**. A auditoria é um formulário do Google e leva algumas semanas. A cota dá uns 6 vídeos por dia.

### TikTok (API oficial, sem custo)

1. Crie um app em developers.tiktok.com com Login Kit e Content Posting API.
2. Cadastre no app o endereço de retorno que a janela Conexões mostra.
3. Cole a client key e o secret e clique em **Entrar com o TikTok**.

**Atenção:**
- até a auditoria do TikTok, os vídeos saem **privados**;
- a API comum não lista nem responde comentários (a caixa avisa "responda pelo app");
- o PC precisa estar ligado na hora.

## Pensando no produto instalado

- **Pasta de dados configurável:** `central/dados.py` decide onde ficam os dados (`CIELLO_DADOS`). Instalado, o programa vai para Arquivos de Programas e os dados para `%LOCALAPPDATA%\Ciello`. Roteiros, mídia, histórico, banco e cofre já seguem essa pasta.
- **Banco versionado:** o banco local (SQLite) tem migrações numeradas. Quem atualiza o programa não perde dados.
- **Conectores trocáveis:** cada provedor é um conector (`central/provedores/`) com testar, coletar, publicar e responder. Trocar o Metricool pela API direta, ou somar outra rede, não mexe no resto.
- **Motor de IA trocável:** o "cérebro" está isolado em `central/ia.py`. Hoje é o Claude Code instalado; num produto para outros clientes, pode ser a API da Anthropic com a chave do cliente.
- **Sem GitHub:** nada aqui depende do GitHub. O vídeo sobe do PC para o provedor. Só a rotina semanal na nuvem ainda usa o GitHub para hospedar o vídeo.
- **Ainda falta para virar instalador:**
  - mover Estúdio de Vídeo, voz, financeiro e comercial para a mesma pasta de dados;
  - empacotar o Python com o programa (instalador .msi ou .exe);
  - apps da Meta, Google e TikTok em nome da empresa, auditados, para os clientes não precisarem criar os deles.
