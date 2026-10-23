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
