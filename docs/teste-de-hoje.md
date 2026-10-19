# Teste de hoje à noite (19/10)

Tudo aqui funciona sem o seu rosto e sem a sua voz. Marque o que deu certo e me conte o que falhou (de preferência com a mensagem de erro).

## 0. Preparar o PC (uma vez, ~15 min)

```powershell
winget install Git.Git Python.Python.3.11 OpenJS.NodeJS.LTS Gyan.FFmpeg
git clone https://github.com/MTCiello/agente-de-postagem.git
cd agente-de-postagem
git checkout ccr-75504115-gpanzf
cd reels; npm install; cd ..
```

## 1. Capas · ~2 min · só Node
```powershell
cd reels
node capa.mjs ../roteiros/2026-10-21-teste-ideia.json ../midia/capas/teste.jpg
node capa.mjs ../roteiros/2026-10-23-texto-cara-de-ia.json ../midia/capas/teste-creme.jpg --tema=creme --selo="3 sinais"
```
- [ ] A capa abriu com título, I.V.A. e logo, sem nada cortado.
- [ ] Recortada em 3:4 (como na grade do perfil), o título continua inteiro.

## 2. Radar · ~2 min · só Python
```powershell
python central/radar.py
```
- [ ] Gerou `radar/AAAA-MM-DD.md`. Abra e veja se os assuntos do topo fazem sentido para o seu nicho.
- [ ] Anote as fontes que falharam (aparecem no topo do relatório).
- Opcional: `git clone https://github.com/mvanhorn/last30days-skill` e `python central/radar.py --last30days last30days-skill/skills/last30days/scripts/last30days.py`.

## 3. Biblioteca de ganchos · ~5 min
```powershell
python central/ganchos.py ranking
python central/ganchos.py modelos --pilar comandos
```
- [ ] Mostrou os 10 vídeos da biblioteca (4 virais + 6 nossos).
- Opcional, com **conta secundária** do Instagram: `pip install instaloader`, `instaloader --login SUA_CONTA_SECUNDARIA` e depois `python central/ganchos.py importar @gabrieltomaz.ia @iacomjota --sessao SUA_CONTA_SECUNDARIA`.
- [ ] Os reels dos perfis de referência entraram com o multiplicador.

## 4. Relatório semanal · ~1 min
```powershell
python central/relatorio.py
```
- [ ] Abriu `metricas/relatorio-2026-10-19.md` com perfil, reels, o que mudar e horário.

## 5. Clone no Kaggle · ~1 h (a maior parte esperando download)
1. kaggle.com → criar conta → verificar telefone (exigido para GPU e internet).
2. *Create → New Notebook → File → Import Notebook* → enviar `central/clone/ciello_clone_kaggle.ipynb`.
3. Painel da direita: **Accelerator: GPU T4 x2**, **Internet: On**.
4. *Run All* e abrir o link `https://….gradio.live` que aparece no fim.
5. Seguir o "Teste desta noite" no fim do notebook: personagem → narração de teste → fala (InfiniteTalk) → andando (Wan 2.2 5B).
- [ ] A tela do Wan2GP abriu.
- [ ] Tempo para gerar a foto: ____ · a fala (≈10 s): ____ · o andando (≈5 s): ____
- [ ] A boca acompanha a fala em português? Nota de 0 a 10: ____
- [ ] Parece real? Nota de 0 a 10: ____
- **Desligue a sessão (Stop session) quando acabar.** A cota grátis é de ~30 h por semana.

## 6. Reel com o clone · ~5 min
Baixe os vídeos da aba *Output* do Kaggle e coloque em `reels/public/clone/` com os nomes `cena1-fala.mp4` e `cena2-andando.mp4`.
```powershell
cd reels
node render.mjs CloneReel ../midia/teste-clone.mp4
```
- [ ] O reel saiu com as suas 2 cenas, as cenas 3 e 4 como rascunho, legenda e cartão final.

## 7. Voz e montagem final (opcional hoje)
```powershell
py -3.11 -m venv .venv; .venv\Scripts\activate; pip install -r central/requirements.txt
python central/voz.py roteiros/2026-10-21-teste-ideia.json --saida audio/teste --nome TESTE
python central/mixar.py midia/2026-10-21-teste-ideia.mp4 audio/teste/narracao.wav midia/final/teste.mp4
```
- [ ] Kokoro gerou a voz em português. Nota da naturalidade: ____
- [ ] O vídeo final saiu com voz e trilha, e a trilha abaixa quando a voz fala.
