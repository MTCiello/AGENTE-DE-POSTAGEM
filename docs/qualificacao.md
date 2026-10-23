# Qualificação do assistente comercial (19/10/2026)

Bateria rodada na nuvem antes do teste no PC do Mateus. Mostra o que passou, o que só dá para testar no PC e o que foi construído a partir do reel "10 agentes de IA que toda empresa devia ter".

## 1. Resultado da bateria

`python central/verificar.py` (é o mesmo `testar.cmd` do Windows): **16 ok · 3 avisos · 0 falhas**.

| Verificação | Resultado | O que prova |
|---|---|---|
| Python, ffmpeg, Node, bibliotecas | ok | ambiente pronto |
| Testes automáticos | ok, **23 testes** | radar, ganchos, SDR, financeiro, vigia e briefing com dados de exemplo |
| Montagem final (mixar) | ok | vídeo + trilha com ducking e volume do Instagram |
| Oráculo de ritmo | ok | os 2 plano-sequência (CRM e comandos) aprovados no padrão do reel de referência |
| Relatório semanal, ganchos | ok | analista e pesquisador funcionando com os dados reais do perfil |
| SDR | ok | buscas geradas a partir do perfil de cliente ideal |
| **Financeiro (mês simulado)** | ok | pela linha de comando: 2 clientes, extrato OFX conciliado, cobrança e resumo |
| **Briefing do dia** | ok | 3 prioridades tiradas dos dados reais do repositório |
| **Painel (porta 3200)** | ok | o servidor sobe, a API responde com Instagram, funil, anúncios, financeiro e prioridades |
| **Equipe de agentes e comandos** | ok | 13 agentes válidos; nenhum comando chama agente que não existe |
| Escritório (pixel-agents) | ok | ver item 2 |
| Capa (Remotion) | ok | capa renderizada a partir de um roteiro |
| Voz | aviso | modelos não instalados aqui (o servidor de modelos é bloqueado na nuvem) |
| Radar (internet) | aviso | as fontes (GitHub, Reddit, Google…) são bloqueadas na nuvem; o código é coberto pelos testes |
| Vigia de concorrentes (internet) | aviso | os sites dos concorrentes são bloqueados na nuvem; testada com um site local que muda de preço |

## 2. Testes de ponta a ponta com imagem

**Escritório:** o pixel-agents 1.5.0 original subiu pelo `abrir.py` numa pasta pessoal vazia, como num PC novo. O layout da Ciello foi instalado sozinho, com as 3 salas (Pesquisa/Estúdio, Comercial, Análise/Postagem) e a apresentação do próprio pixel-agents.

![Escritório](img/teste-escritorio.png)

**Painel** com um financeiro simulado de 3 clientes (dados fictícios):

![Painel](img/teste-painel.png)

## 3. Problemas que a bateria achou (já corrigidos)

1. **Cobrança:** depois de mandar a mensagem de 7 dias, a de 3 dias continuava pendente. Agora vale só a etapa mais recente.
2. **Vigia:** 2 relatórios no mesmo minuto se sobrescreviam, e o briefing lia o relatório antigo do dia. Agora nada é sobrescrito e o briefing lê o mais novo.
3. **Categorias:** "PAGAMENTO DAS CONTAS" caía em Impostos por causa do "DAS". Agora só "DAS SIMPLES", "DAS MEI" ou "PGDAS".
4. **1ª fatura:** um cliente que começou depois do dia de vencimento ganhava uma fatura já atrasada. Agora a 1ª fatura sai no 1º vencimento depois do início.
5. **Previsão de caixa no 1º mês:** a despesa média ficava zerada. Agora usa o que já saiu no mês.
6. **Escritório:** um PC com proxy configurado podia não enxergar o pixel-agents em 127.0.0.1. Agora o endereço local nunca passa por proxy.

## 4. O assistente atende o necessário?

| Necessidade | Situação | Como foi verificado |
|---|---|---|
| Analisar o desempenho do perfil | **Pronto** | Metricool (API oficial) + relatório semanal + painel |
| Pesquisar virais do nicho | **Pronto, falta testar no PC** | radar com testes; as fontes só abrem fora da nuvem |
| Aprender ganchos validados | **Pronto** | biblioteca com 10 vídeos, ranking e modelos |
| Vídeos institucionais de qualidade | **Pronto** | 2 plano-sequência aprovados pelo oráculo; falta a sua nota |
| Capa, legenda e melhor horário | **Pronto** | capa no Remotion; horário e agendamento pelo Metricool |
| Narração com sotaque brasileiro | **Pronto, falta testar no PC** | código pronto; o modelo baixa no PC |
| Sua voz clonada | **Falta sua amostra** | Chatterbox pronto; precisa de 10 s da sua voz |
| Clone em vídeo (andando, cenário) | **Falta testar no Kaggle** | notebook pronto; precisa da sua conta e das suas fotos |
| Prospecção (SDR) | **Pronto, falta o executável do Maps** | testes com dados de exemplo; a busca real roda no PC |
| Resposta imediata a lead que chegou sozinho | **Novo · pronto** | `sdr.py entrada` + teste |
| Fechamento (closer, proposta, demo) | **Pronto** | agente + FAQ de objeções + horários pelo caixa-entrada |
| Anúncios | **Parcial** | planejamento e leitura funcionam; o resultado automático depende do Meta Ads conectado ao Metricool |
| Crescimento da empresa (MRR, caixa, CAC, LTV) | **Novo · pronto** | `financeiro.py` com 8 testes + mês simulado |
| Resumo do dia e prioridades | **Novo · pronto** | `briefing.py` + `/bom-dia` + painel |
| Concorrentes (preço e oferta) | **Novo · pronto, falta testar no PC** | vigia testada com site local; as URLs reais abrem no PC |
| Escritório pixel-agents fiel | **Pronto** | subiu do zero com o layout (item 2); falta ver os agentes ao vivo com o Claude Code no PC |
| Conselho de negócio | **Pronto** | Founder skills (MIT) + `/conselho` |

## 5. Os 10 agentes do reel

Todos os 10 cartões repetem o mesmo modelo: o que faz, quando roda, com o que se conecta e por que se paga. Os números ("78%", "7x", "76%"…) são estatísticas de mercado usadas como gancho; não são resultado dos agentes.

| # | Agente do reel | O que o assistente já tinha | O que foi feito agora | Fica para depois |
|---|---|---|---|---|
| 1 | **Chefe de Gabinete:** resumo de CEO, delega, cobra pendências, placar; todo dia 7h + sexta | coordenador e comandos, sem resumo diário | agente `chefe-gabinete` + `central/briefing.py` (3 prioridades, pendências com dono, placar) + `/bom-dia`, `/sexta` + `agendar.cmd` (7h no Windows) + prioridades no painel | — |
| 2 | **Marketing:** posts, vídeo curto, agenda, métricas | **completo** (pesquisador, roteirista, produtores, postagem, analista) | — | cortar vídeo longo em reels (dá para fazer com o faster-whisper que já está no projeto, quando houver vídeo longo) |
| 3 | **Vendas:** responde em minutos, qualifica, marca call, follow-up | SDR (ativo) + closer, sem lead que chega sozinho | `sdr.py entrada`: registra o lead da DM, do anúncio, do site ou da indicação e devolve a resposta com 3 perguntas de qualificação; closer marca a demo pelo caixa-entrada | resposta automática 24h: exige a API oficial do WhatsApp (paga) e um servidor ligado |
| 4 | **Suporte:** FAQ, pedidos simples, todo canal, caso difícil | nada | agente `sucesso-cliente` + `comercial/faq.md` (você aprova, a resposta entra no FAQ) | atendimento automático: mesmo motivo do item 3 |
| 5 | **Recepcionista:** atende ligação, marca horário | nada | — | precisa de telefonia paga e agente de voz; não faz sentido para o volume atual |
| 6 | **Caixa de Entrada:** triagem do e-mail, rascunhos, reunião, resumo | só rascunho no closer | agente `caixa-entrada` com os conectores Gmail e Google Agenda: triagem em 3 grupos, **só rascunhos**, 3 horários livres para demo | — |
| 7 | **Financeiro:** classifica despesa, cobra 3/7/14 dias, concilia, prevê caixa | nada | agente `financeiro` + `central/financeiro.py`: extrato OFX/CSV do banco, regras de categoria, baixa automática de fatura, o que não bate, cobrança 3/7/14 com wa.me, caixa 30/60/90, MRR, churn, CAC, LTV | emissão de boleto/Pix automática (precisa de banco com API) |
| 8 | **Pesquisa:** concorrente, tendência, dor do cliente, resumo de sexta | radar, ganchos, concorrentes no Metricool, dor nas avaliações (SDR) | `central/vigia.py`: preço, plano e oferta de Agendor, RD Station, Kommo e PipeRun desde a última vez + link dos anúncios ativos de cada um | changedetection.io (Apache-2.0) se um dia precisar vigiar dezenas de páginas |
| 9 | **Avaliações:** pede avaliação, responde, alerta da ruim, relatório | nada | `financeiro.py posvenda` + `nps`: boas-vindas D+1, uso D+7, NPS D+30, pedido de avaliação no Google só para nota 9–10, indicação D+90; alerta de cliente com nota até 6 no briefing | — |
| 10 | **Contratação:** vaga, triagem, entrevista, 1º dia | nada | — | quando a Ciello contratar a 1ª pessoa (o `/conselho` já ajuda a decidir o momento) |

**Por que não os itens 5 e 10 agora:** custam dinheiro todo mês (telefonia) ou resolvem um problema que a Ciello ainda não tem (contratar). Os outros 8 estão cobertos, sem dependência nova: tudo é Python da biblioteca padrão, os conectores que você já tem (Gmail, Agenda, Metricool) e arquivos no seu PC.

**Ideia de conteúdo:** o reel em si é um formato forte para a Ciello. Um cartão por agente, barra de progresso e CTA "comenta EQUIPE". Dá para fazer "5 agentes que o seu comercial devia ter" com os nossos agentes reais.

## 6. O que testar hoje à noite (além do `docs/teste-de-hoje.md`)

- [ ] `testar.cmd` terminou com 0 falhas. Os avisos de radar e vigia devem **sumir** no PC: se a vigia disser que uma URL está fora do ar, troque a URL em `comercial/concorrentes.json`.
- [ ] `/bom-dia` no Claude Code: saiu uma tela com as 3 prioridades?
- [ ] Cadastre um cliente de verdade (ou de teste) e baixe o extrato do banco em **OFX**: `python central/financeiro.py cliente ...` → `faturar` → `importar extrato.ofx` → `resumo`. As despesas caíram na categoria certa?
- [ ] `agendar.cmd` (opcional): amanhã às 7h deve aparecer `estado\briefing\2026-10-20.md`.
