# Anúncios

O gestor de anúncios grava cada teste em `anuncios/AAAA-MM-DD-nome.json`, e o Escritório Ciello soma tudo no painel.

```json
{"campanhas": [
  {"nome": "Teste CRM imobiliárias", "inicio": "2026-11-03", "fim": "2026-11-09", "objetivo": "mensagens no WhatsApp",
   "publico": "donos de empresa, Chapecó +40 km", "criativo": "reel 6x1 vendedor IA",
   "gasto": 105.0, "impressoes": 9800, "cliques": 210, "conversas": 14, "demos": 3, "clientes": 1}
]}
```

Regra: só números que aparecem no Gerenciador de Anúncios (ou no Metricool) e no `sdr.py`. Nada estimado.
