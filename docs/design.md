# Sistema visual do Ciello OS

Referência curta para quem mexe em `central/escritorio/web/`. Inspirado nas Human Interface Guidelines da Apple: pouca coisa na tela, uma hierarquia clara e o mesmo comportamento em todas as janelas.

![Janela Financeiro](img/financeiro.png)

## Base

| Item | Valor |
|---|---|
| Letra | Inter em tudo. Oswald só na marca do papel de parede |
| Tamanhos | 13 px no corpo, 14/600 nos subtítulos, 26/700 no título da página |
| Cor de ação | `--azul` #263A59 (botão principal, seleção, gráficos) |
| Destaque | `--ouro` #E0A81C só para foco e atenção, nunca para ação |
| Texto | `--tinta` #1D1B18, secundário `--cinza` #6B665C |
| Grade | múltiplos de 8 px (4 px em ajustes finos) |
| Raios | 8 controles, 10 linhas, 12 janelas, 18 painéis, 22 dock |

As variáveis estão no `:root` de `app.css`. Use sempre a variável, nunca a cor solta.

## Estrutura da tela

- **Barra de cima** (30 px): marca, nome do app ativo, estado da equipe, avisos e relógio.
- **Dock** flutuante embaixo: botão Iniciar, apps fixos (`NO_DOCK` em `app.js`), janelas abertas com um ponto embaixo e atalhos do sistema.
- **Menu Iniciar** no estilo Spotlight: campo de busca que também manda pedidos à equipe, apps por grupo (`GRUPOS`) e a lista de agentes com o estado de cada um.

![Menu Iniciar](img/menu-iniciar.png)

## Janela

- **Barra de título unificada** (52 px): ícone, nome do app e a seção atual; à direita, as ações da tela e os botões minimizar, maximizar e fechar (fechar fica vermelho no hover).
- **Ações**: a tela escreve os botões em `.acoes.topo` como sempre; `arrumar(j)` leva os botões para a barra. Cabem 1 a 3 conforme a largura, o resto vai para o menu `…`.
- **Navegação lateral** (216 px): as abas (`abas(j, lista)`) viram a lista da lateral. Uma lista curta de modos, que muda só a vista e não a seção, usa `nav.abas.seg` e fica no conteúdo como controle segmentado.
- **Lista e detalhe**: para escolher um item e ver os detalhes (como em Tendências), lista à esquerda e o item escolhido à direita.

![Tendências em lista e detalhe](img/tendencias.png)

## Regras

1. Um botão principal (`.bt.pri`) por área. Os outros são `.bt`.
2. Texto em frase normal, sem CAIXA ALTA em títulos.
3. Nada de cor solta para dizer estado: use `.chip` (`pronto`, `trabalhando`, `esperando`, `erro`, `parado`).
4. Alvos clicáveis com pelo menos 28 px de altura; foco visível com `--foco`.
5. As capturas de `img/` usam só dados fictícios (veja o [índice](README.md#imagens)).
