# Diário noturno do Ciello OS

Loop de evolução que roda enquanto o Mateus dorme: **simular o uso → achar o que trava ou passa despercebido → pesquisar → desenvolver → testar → ajustar a usabilidade → publicar**.
Regras: só na branch `ccr-75504115-gpanzf`, nada é enviado, agendado ou publicado de verdade, e dados reais (leads, clientes, valores da planilha) nunca entram aqui (o repositório é público). O que é dado seu vai só na conversa.

## Resumo para o café

_(atualizado no fim da noite)_

## Para o Mateus decidir

- **Hospedagem de R$ 90:** é mensal? Considerei mensal. Se for anual, mude em `comercial/produtos.json` (`"mensal": 7.5`, ou me avise para criar o tipo anual).
- **Preços no GitHub:** os preços de lista (CRM, site, hospedagem) ficaram em `comercial/produtos.json`, versionados, porque são os mesmos que vão para todo cliente. Se preferir que fiquem só no PC, eu movo para fora do git.

## Voltas

### Volta 1 · 22/10 21h–00h · Financeiro com os produtos reais

**Simulação:** cadastrei como cliente um CRM em teste grátis, um site parcelado e uma hospedagem. Não dava: o financeiro só conhecia assinatura mensal. Site parcelado não tinha onde entrar, e o teste grátis de 30 dias virava fatura no 1º vencimento.

**Feito:**
- `comercial/produtos.json`: CRM R$ 397/mês com 30 dias grátis, site R$ 1.500 à vista ou 12x R$ 137,90, hospedagem R$ 90/mês. O financeiro, a janela e os agentes leem daqui.
- **Teste grátis de verdade:** o cliente entra como "teste" com data de fim. Não fatura, já recebe as boas-vindas do pós-venda e aparece no Bom dia quando faltam 5 dias ("ligue e feche"). Os botões **Virou cliente** e **Desistiu** ficam na aba Clientes.
- **Venda de site** (`financeiro.py venda` e o botão **+ Venda de site**): à vista ou parcelado. As parcelas viram faturas, entram na previsão de caixa como "sites a receber" e, quando o extrato paga, viram "Receita de sites". A hospedagem vira assinatura.
- **Cobrança fala do que está sendo cobrado:** "a parcela 3/12 do seu site", "a hospedagem do seu site" ou "a mensalidade do CIELLO CRM".
- **Comercial → lead "cliente":** você escolhe entre CRM em teste, CRM já pagando, site à vista ou site parcelado.

**Bug achado na simulação e corrigido:** o formulário "Nova assinatura" abria com o produto "Outro" marcado e o cadastro falhava por falta de valor.

**Testes:** 3 testes novos (teste grátis, site parcelado com hospedagem, site à vista); todos passam.

### Volta 2 · 23/10 00h–01h · Plano do ano, auditoria e preço

**Simulação:** levei a sua planilha "NEGÓCIOS CIELLO" (aba da "CONTROLE PESSOAL") para o Ciello OS para ver se ele acharia os furos. Os números ficam só no seu PC e na conversa, nunca aqui. O financeiro não tinha onde guardar um plano de ano nem como discutir regras: só olhava o passado (extrato e faturas).

**Feito:**
- `central/plano.py` + **Financeiro → Plano do ano**: negócios (fechado, negociando ou talvez, com a chance de cada um), custos (mensal, anual ou único), regime de imposto (MEI, Simples Anexo III ou V), cancelamentos e taxas. A projeção de 12 meses mostra receita certa, provável e "se tudo fechar", impostos, resultado e quanto sobra para você.
- **Auditoria "O que olhar"**: aponta meses sem receita, imposto fora do plano, teto do MEI, negócio sem status, receita concentrada num cliente ou produto, nenhum cancelamento previsto, custo de entrega (servidor, domínio, API) fora do plano, custo anual que pesa num mês só, sem contador, fator R, e em quantos meses a empresa já te paga. Também calcula quantos clientes de CRM faltam para isso.
- **Ideias de preço** a partir dos preços reais: juros embutidos no site parcelado (10% a mais, 1,5% ao mês), plano anual do CRM (12 por 10), taxa de implantação, hospedagem como receita que fica.
- **Discutir com o Financeiro**: abre o Claude com o plano e pede 2 caminhos com números para cada ponto, uma recomendação, 3 regras e um plano de 90 dias. **Puxar da planilha** pede ao agente para ler a aba do Google Drive e montar o plano, mostrando antes de gravar.
- O agente Financeiro conhece os produtos, o teste grátis, a venda de site e o plano.

**Bugs achados na simulação e corrigidos:**
- Um campo chamado "item" quebrava o formulário (no navegador, `form.elements.item` é uma função). Agora todo formulário lê os campos com `namedItem`.
- A participação de um produto passava de 100% ("118% da receita vem do CRM") porque os cancelamentos entravam num lado da conta e não no outro.

**Testes:** 6 testes novos do plano; todos passam.

### Volta 3 · 23/10 · Prospecção com duas ofertas e clientela

**Simulação:** entrei no Comercial como você numa terça de manhã, com um cliente terminando o teste grátis e leads sem site na fila.
- O SDR oferecia CRM até para empresa sem site, e um "site" que era só o Instagram contava como site.
- Quem estava acabando o teste só aparecia no Financeiro.
- Ninguém lembrava de vender o 2º produto para quem já é cliente.

**Feito:**
- **Duas ofertas no SDR:** lead com site recebe a oferta do CRM; lead sem site, ou com Instagram, Linktree ou iFood no lugar do site, recebe a de site. Cada oferta tem a sua 1ª mensagem e o seu follow-up ("Procurei vocês no Google e não encontrei um site…", "no ar em até 7 dias úteis", "posso te mandar 2 exemplos?").
  - A oferta aparece como selo em cada lead e dá para filtrar a lista por ela.
- **Comercial → Hoje → Teste grátis acabando:** quem termina o teste em até 7 dias aparece com a mensagem de fechamento pronta, o link do WhatsApp e os botões **Virou cliente** e **Desistiu**.
- **Vender para quem já é cliente:** cliente de CRM sem site recebe a oferta de site; cliente de site sem CRM recebe a do teste do CRM. Cada um vem com a mensagem pronta. **Já ofereci** tira o cliente da lista por 60 dias. Quem está no teste fica de fora.
- **FAQ** com os preços reais e o passo a passo do site (o mesmo do seu material: 7 dias úteis, até 2 rodadas de ajustes). Os agentes SDR e Closer foram atualizados.

**Testes:** 2 testes novos (as ofertas e mensagens; fim do teste e oportunidades na carteira).

### Volta 4 · 23/10 · Painel de entrada e produção de conteúdo

**Simulação:** abri o OS como na sexta de manhã: "o que eu faço agora e o que está escapando?". Três problemas:
- O Bom dia mostrava as prioridades, mas sem como agir dali.
- O conteúdo não tinha onde ver em que etapa cada post estava.
- Os posts que ficaram como rascunho no Metricool simplesmente sumiam da vista.

**Feito:**
- **Conteúdo → Produção:** cada post da agenda com as 7 etapas (roteiro, narração, vídeo, final, capa, legenda, agendado), o próximo passo e quem faz.
  - **Gerar legenda:** um rascunho sai das falas do roteiro (gancho, valor, chamada, hashtags), sem o Claude. Você edita e salva.
  - **Já agendei / Foi publicado?:** registra no historico.md.
  - **Terminar com a equipe:** chama os agentes só para o que falta e pede a sua aprovação antes de agendar.
  - Também lista os próximos horários livres (seg, qua e sex às 10h).
- **Alertas de conteúdo:** post que sai em até 2 dias sem vídeo final, post pronto e não agendado, posts com data passada sem registro de publicação, semana com menos de 3 posts e o limite de 20 posts do Metricool grátis.
- **Bom dia como painel de entrada:** a caixa "o que você quer que a equipe faça hoje?" (Enter manda) e atalhos que abrem a janela já na aba certa (Cobrança, Comercial de hoje, Produção de conteúdo, Plano do ano, Estúdio de Voz, Esteiras).
- **O Bom dia passou a apontar o que costuma passar despercebido:** faturas do mês não geradas, cliente sem WhatsApp cadastrado, clientes prontos para o 2º produto, furos graves do plano do ano e os alertas de conteúdo.

**Bugs achados na simulação e corrigidos:**
- Com o vídeo final pronto, a etapa "vídeo" ainda aparecia pendente.
- O plano vazio dizia "te paga em 12 de 12 meses". Agora mostra 3 passos para montar o plano.

**Testes:** 2 testes novos do quadro de conteúdo; os 91 passam.

### Volta 5 · 23/10 · Primeiros passos

**Simulação:** abri o OS "zerado", como ele está hoje no seu PC. O financeiro não tem nenhum dos clientes que já pagam, então MRR, cobrança e pós-venda ficam vazios, e nada na tela dizia por onde começar.

**Feito:** o cartão **Primeiros passos** no Bom dia (x de 6, com barra de progresso):
1. clientes que já pagam;
2. saldo do banco;
3. plano do ano;
4. a sua voz;
5. números do Instagram;
6. leads na fila.

Cada passo tem **Fazer agora**, que abre a janela na aba certa já com o formulário aberto. O passo some da lista quando está feito, e **Esconder** tira o cartão.

### Volta 6 · 23/10 · Tendências e análise de métricas

**Simulação:** rodei o radar e a vigia de concorrentes como no seu PC num dia sem internet (aqui a rede bloqueia). **Bug sério:** com todas as fontes fora, os dois gravavam um relatório vazio por cima do último bom, e as janelas Tendências e Concorrentes passavam a mostrar o vazio.

**Feito:**
- **Radar e vigia sem internet** não gravam mais nada: avisam "o último continua valendo" e mantêm o relatório bom na tela.
- **Tendências → Pauta sugerida:** cada assunto do radar vira um item com nota e ângulo, e com o botão **Virar roteiro** (o roteirista confere os fatos antes e salva no próximo horário livre). Também há **Fazer os 3 reels da semana com esta pauta** e **Montar com o Claude**, que monta o radar ou a vigia com busca web quando a rede do PC falhar.
- **Conteúdo → Análise:** o relatório semanal do Instagram (retenção, salvamentos, compartilhamentos, horário, o que mudar) dentro do OS, com **Gerar o relatório da semana**, **Anotar números novos** e **Discutir com o Analista**.

### Volta 7 · 23/10 · Estúdio de Vídeo com HyperFrames

**Simulação:** tentei "criar um vídeo" como você contou que tentou. Não havia caminho: cada reel exigia código novo e 6 comandos.

**Pesquisa:** HyperFrames (HeyGen, Apache-2.0, versão 0.8.186). O vídeo é um HTML com tempos nos atributos e animação GSAP; o CLI renderiza no Chrome sem janela com ffmpeg e já mistura o áudio. Testei aqui: instala pelo npm em segundos e baixa o próprio Chrome.

**Feito:**
- `central/estudio_video.py`: **roteiro → narração → vídeo**, sem escrever código.
  - Cada cena vira título animado (tirado do roteiro ou da fala: "Segundo: transforme esta conversa…" vira o rótulo "Segundo" e o título "transforme esta conversa em um orçamento"), mais lista numerada quando o roteiro tem itens e legenda sincronizada com a fala (tempos reais do `voz.py`).
  - Leva também a marca, a barra de progresso, a trilha baixinha e o selo no final.
  - Sai em 1080x1920 com áudio, em `midia/estudio/` (rascunho); **usar** copia para `midia/final/`.
- **Dois modelos:** Ciello escuro (azul, marfim e ouro) e Ciello claro (marfim, carvão e ouro).
- **Janela Estúdio de Vídeo** (menu Iniciar → Criar):
  - **+ Novo roteiro** sem o Claude: data no próximo horário livre, gancho, itens e chamada;
  - escolha do modelo e **Gerar vídeo** (ou **Rascunho rápido**), com o andamento ao vivo;
  - prévia do vídeo na própria janela e **Usar como vídeo final**.
  - O quadro de produção do Conteúdo ganhou **Gerar no Estúdio** em cada post sem vídeo.
- **GSAP e HyperFrames locais** em `reels/` (versões fixas); o `instalar.cmd` também baixa o navegador do HyperFrames. O vídeo sai mesmo sem internet. O `testar.cmd` ganhou a verificação "Estúdio de Vídeo (HyperFrames)", que renderiza um vídeo de teste.
- O agente Produtor de Vídeo e o AGENTE.md usam o Estúdio como caminho rápido; o Remotion fica para o visual especial (plano-sequência, I.V.A., clone).
- `audio/` (a sua voz) e `midia/estudio/` (rascunhos) ficam fora do GitHub.

**Bugs achados na simulação e corrigidos:**
- O GSAP vinha de um CDN: sem internet, o vídeo não saía.
- Títulos terminavam em preposição ("…orçamento com") ou viravam só "PRIMEIRO".
- Gerar um vídeo abria a janela do Produtor de Vídeo por cima e repetia o aviso de "terminou".

**Testes:** 5 testes novos (títulos, legendas, projeto HTML, tempos reais, roteiro escrito à mão). Também gerei 2 vídeos de verdade, pelo terminal e pela janela, nos dois modelos.

### Volta 8 · 23/10 · Atendimento a clientes sem o Claude

**Simulação:** fiz 6 perguntas típicas de cliente ("quanto fica o sistema por mês?", "funciona no iphone?", "esqueci de pagar o boleto"…). Sem o Claude não havia como responder pelo OS. E o FAQ que o Sucesso do Cliente usa tem **6 respostas em branco**, justamente as mais comuns: celular, fidelidade, WhatsApp Business, quantas pessoas, se perde as conversas, colunas da importação.

**Feito:**
- `central/atendimento.py` + **janela Atendimento** (menu Iniciar → Vender).
  - Você cola a pergunta e o OS acha as respostas no FAQ, entendendo o jeito de o cliente falar ("fica" → custa, "boleto" → pagamento, "iphone" → celular, "cancelar" → fidelidade).
  - A resposta vem editável, com **Abrir no WhatsApp** para o cliente escolhido e **Copiar**.
  - Não achou: **Escrever a resposta e guardar no FAQ** ou **Pedir ao Sucesso do Cliente**.
- **FAQ incompleto:** a lista das respostas em branco, com **Responder**. A resposta é gravada no FAQ e o agente passa a usar. O Bom dia também avisa.

**Bug achado na simulação e corrigido:** apertar Enter buscava, mas a tela não mostrava o resultado (a atualização esperava o cursor sair da caixa de texto).

**Testes:** 2 testes novos (busca com as palavras do cliente; completar e acrescentar no FAQ).

### Volta 9 · 23/10 · Tela de notebook (1366x768)

**Simulação:** percorri o menu Iniciar, Bom dia, Financeiro, Comercial, Conteúdo, Estúdio de Vídeo, Atendimento, Objetivos e Estúdio de Voz em 1366x768. Tudo cabe e funciona; as faixas de botões quebram em 2 linhas sem esconder nada.

**Ajuste:** em telas até 1440 px de largura, cada app abre maximizado na 1ª vez (um app por vez, sem arrastar janela). Depois vale o tamanho que você deixar. Terminal e execução continuam em janela.

### Volta 10 · 23/10 · Agenda de demos

**Simulação:** um lead respondeu "pode ser amanhã às 15h?". O Comercial só deixava mudar a etapa para "demo". Não havia onde guardar data e hora, nem mensagem de confirmação, lembrete no dia ou aviso de demo que passou sem desfecho. Era fácil esquecer a demo ou não registrar o resultado.

**Feito:**
- **Agendar demo** (Comercial, em "Quentes" ou ao mudar a etapa para demo): você escolhe data e hora, e o OS guarda no lead e devolve:
  - a **mensagem de confirmação** pronta para o WhatsApp ("Combinado! Amanhã às 15:00 eu te mostro…");
  - o link **Adicionar ao Google Agenda**, que abre no navegador; nada é criado sem você clicar em salvar.
- **Comercial → Hoje → Agenda de demos:**
  - no dia da demo, o **lembrete** ("Passando para confirmar nossa conversa de hoje às 15:30…");
  - **Remarcar**.
- **Como foram as demos?** A demo que passou e continua em "demo" pede o desfecho: proposta, fechou ou perdido.
- **Bom dia:** "Demo hoje às…" no topo, "Demo amanhã" e "Como foi a demo com…".
- Pelo terminal: `python central/sdr.py agendar 12 --quando 2026-10-24T15:00`.

**Testes:** 3 testes novos (agendar e a agenda do dia; link do Google Agenda e confirmação; data inválida).

### Volta 11 · 23/10 · Meta de crescimento e decisões do negócio

**Simulação:**
- **Meta:** o Plano do ano dizia "são 9 clientes para te pagar", mas em lugar nenhum dava para responder "e o que eu faço esta semana para chegar lá?".
- **Decisões:** as ideias de preço e os furos do plano apareciam como texto. Não havia onde registrar "decidi X", nem como os agentes saberem a regra. O pedido era justamente "discutir uma regra ou plano de implantação".

**Feito:**
- **Financeiro → Metas e decisões** (aba nova).
  - **Meta de clientes:** você diz quantos clientes de CRM quer e até quando. O OS faz o funil de trás para frente: clientes que faltam (descontando os que devem vir do teste grátis e somando os cancelamentos do caminho), testes, demos, respostas e **abordagens por semana**.
    - O teste de 30 dias entra na conta: quem começa o teste depois de certo mês só vira cliente depois da meta.
    - As taxas do funil usam **os seus dados** assim que há o bastante (20 abordagens, 5 demos). Antes disso é uma estimativa conservadora, marcada como tal, e dá para trocar.
  - **Ritmo da semana:** abordagens, demos e testes feitos contra o necessário, com o aviso "atrás" quando faltar. Só contam os dias úteis que já terminaram, então ninguém fica "atrás" na segunda de manhã. A mesma faixa aparece no topo de **Comercial → Hoje**.
  - **Montar o plano de 90 dias com a equipe:** abre o Claude (chefe de gabinete + financeiro + SDR) com a meta e o ritmo, para montar o plano de implantação semana a semana.
  - **Decisões em aberto:** os pontos importantes do plano e as ideias de preço, cada um com 4 botões:
    - **Discutir:** abre o Claude com 2 ou 3 caminhos, os números e uma regra sugerida, sem decidir por você;
    - **Decidir:** grava a regra;
    - **Depois:** lembra em 30 dias;
    - **Não se aplica.**
  - **Regras da casa:** o que você decide vai para `financeiro/regras.md` (fora do git). Financeiro, closer e SDR passaram a ler esse arquivo antes de falar de preço, desconto ou condição.
- **Bom dia:**
  - avisa quando a semana está atrás do ritmo e quantas abordagens tiram o atraso;
  - avisa quando chega a data de rever uma decisão;
  - "Defina a meta de clientes" entrou nos Primeiros passos.
- Pelo terminal: `python central/metas.py --meta 12 --ate 2027-06` e `python central/decisoes.py`.

**Bug achado na simulação e corrigido:** na segunda de manhã a semana já aparecia "atrás do ritmo".

**Testes:** 11 testes novos: funil de trás para frente, cancelamentos, meta já coberta, sem tempo pelo teste grátis, taxas dos seus dados, ritmo da semana, validação, decisões e regras, chave do assunto e adiar/descartar.

### Volta 12 · 23/10 · O que passa despercebido no extrato

**Simulação:** importei 3 meses de extrato com casos que acontecem na vida real:
- o Canva cobrado 2 vezes no mesmo mês;
- o Claude que subiu de R$ 110 para R$ 121,44;
- o servidor (todo dia 5) que não veio em outubro: cartão recusado, e o site do cliente pode cair;
- uma ferramenta nova (Heygen) que ninguém pôs no plano.

O Financeiro mostrava tudo como lançamentos soltos, sem nenhum aviso.

**Feito:**
- `central/gastos.py`, em **Financeiro → Lançamentos → Gastos fixos**.
  - O OS junta as despesas pelo nome. Ele tira números, datas e prefixos do banco ("COMPRA CARTAO", "PIX ENVIADO", "Pagamento de boleto"). Vira fixo o que aparece em 2 meses ou mais; o que varia muito (combustível, mercado) fica de fora.
  - Avisa:
    - **em dobro** (mesmo valor duas vezes no mês);
    - **subiu** (com o percentual);
    - **não veio** (a conta de todo dia X que passou da data);
    - **nova** (ferramenta que apareceu agora);
    - **fora do plano** (gasto fixo que o Plano do ano não tem).
  - **Pôr no plano:** um clique leva o gasto para o Plano do ano, como custo mensal.
- **Bom dia:** cobrança em dobro, conta que não veio, aumento e assinatura nova entram nas prioridades e pendências.

**Ruídos achados na simulação e corrigidos:**
- Um PIX avulso "a classificar" aparecia como "assinatura nova".
- A assinatura nova continuava aparecendo depois de ir para o plano.
- O Bom dia dizia "sai em 0 dia(s)". Agora diz "sai hoje" (e sobe de prioridade) ou "sai amanhã".

**Testes:** 4 testes novos (nome sem prefixo do banco; os 5 avisos num extrato de 3 meses; PIX avulso; mês sem extrato não acusa conta parada).

### Volta 13 · 23/10 · Saúde da carteira

**Simulação:** uma cliente com NPS 10 estava com a fatura 48 dias atrasada, outra deu nota 6 e ninguém ligou, e outra estava há meses sem conversa. Cada sinal ficava num canto (cobrança, NPS, pós-venda), e ninguém juntava "quem está para cancelar?".

**Feito:**
- `central/carteira.py`: cada cliente ativo ganha uma **nota de 0 a 100**, os motivos e a próxima ação.
  - **O que tira pontos:**
    - atraso agora;
    - o costume de pagar atrasado (média das últimas 6 faturas);
    - a nota de satisfação;
    - os dias sem conversa;
    - os primeiros 90 dias;
    - o pós-venda pendente.
  - **Faixas:** saudável (80+), atenção (55+) e risco.
  - **Mensagem pronta para o WhatsApp:**
    - "Vi a sua nota e queria entender…" para quem deu nota baixa;
    - "como está o CRM aí com a equipe?" para quem está esquecido;
    - **pedido de indicação** para quem deu 9 ou 10. Sem prometer recompensa: isso é decisão sua.
  - Quem está atrasado vai direto para a **Cobrança**, que já tem as mensagens por etapa.
- **Financeiro → Clientes:**
  - faixa "Saúde da carteira" com a receita em risco por mês;
  - os cartões de ação;
  - a nota de cada cliente na tabela, com os motivos ao passar o mouse;
  - botão **Conversei**, para registrar ligação, visita ou WhatsApp e zerar o "sem conversa".
- **Bom dia:** cliente em risco (com motivo), clientes sem conversa há mais de 45 dias e promotores para pedir indicação. A nota baixa deixou de aparecer duplicada.

**Achado na simulação e corrigido:** os clientes em risco por atraso não apareciam na lista de ação, porque não tinham mensagem própria. Agora aparecem com o botão **Cobrar**.

**Para o Mateus decidir:** vale ter uma **recompensa por indicação** (ex.: um mês grátis para quem indicar e o indicado fechar)? Se sim, registre em Metas e decisões e as mensagens passam a citar.

**Testes:** 2 testes novos (notas, motivos, ações e ordem; registrar conversa melhora a nota).
