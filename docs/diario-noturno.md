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
