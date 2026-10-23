"""Desenha os móveis novos do escritório da Ciello em pixel art, no mesmo estilo do pixel-agents (16 px por tile,
contorno escuro, cor chapada com uma linha de luz). Cada móvel vira uma pasta em
escritorio/webview-ui/public/assets/furniture/<ID>/ com o PNG e o manifest.json.

  ARQUIVOS G   CAIXAS (pilha de caixas), ESTANTE_ARQUIVO (estante de aço com caixas), SERVIDOR (o cérebro do escritório)
  COPA         BALCAO_CAFE (balcão com pia e máquina de café), GELADEIRA
  VARANDA      GUARDA_CORPO (grade de madeira), ESPREGUICADEIRA
  DECORAÇÃO    QUADRO_CIELLO e JANELA (parede), LUMINARIA, ARCADE (fliperama), BEBEDOURO, ARQUIVO_ACO,
               TRIPE_CAMERA e RING_LIGHT (o set de gravação), CAVALETE_METAS (o quadro de metas de vendas)
  PREMIUM      PORTA_CARVALHO (a porta da sala do Gerente), MESA_EXECUTIVA (mogno), POLTRONA_COURO (frente, costas e lado), ESTANTE_ESCURA, PAINEL_CIELLO (parede),
               VASO_GRANDE, APARADOR, e em cima das mesas NOTEBOOK, TROFEU e GLOBO
  PACOTE       VASO_PEQUENO, PUFE, MESA_LATERAL, PALETE_CAIXAS, MAQUINA_SALGADINHOS, GUARDA_SOL_MESA,
               TV_PAREDE, PAINEL_METRICAS e QUADRO_AVISOS (parede)

Blocos: cada móvel ocupa no chão footprintW x (footprintH - backgroundTiles) blocos de 16 px; as linhas de fundo
ficam na parede (móvel encostado) ou atrás dele. Vaso pequeno = 1 bloco, vaso grande = 2, mesa de um funcionário = 3.
O desenho preenche o bloco inteiro: a base do móvel encosta na borda de baixo do último bloco, sem sobra.

  python central/escritorio/desenhar_moveis.py      (precisa do Pillow)
Depois: cd escritorio/webview-ui && npx vite build
"""
import json
from pathlib import Path

from PIL import Image

DESTINO = Path(__file__).resolve().parents[2] / "escritorio" / "webview-ui" / "public" / "assets" / "furniture"
CONTORNO = (43, 26, 24, 255)
T = (0, 0, 0, 0)


def cor(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


class Tela:
    def __init__(self, w, h):
        self.im = Image.new("RGBA", (w, h), T)
        self.px = self.im.load()
        self.w, self.h = w, h

    def ret(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                self.px[x, y] = c

    def caixa(self, x0, y0, x1, y1, preenche, luz=None, sombra=None):
        """Retângulo com contorno, uma linha de luz em cima e sombra embaixo."""
        self.ret(x0, y0, x1, y1, CONTORNO)
        self.ret(x0 + 1, y0 + 1, x1 - 1, y1 - 1, preenche)
        if luz:
            self.ret(x0 + 1, y0 + 1, x1 - 1, y0 + 1, luz)
        if sombra:
            self.ret(x0 + 1, y1 - 1, x1 - 1, y1 - 1, sombra)

    def p(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = c


PAPELAO, PAPELAO_LUZ, PAPELAO_SOMBRA, FITA = cor("c8935a"), cor("deb27a"), cor("9a6a3a"), cor("e9d3a8")
ACO, ACO_LUZ, ACO_SOMBRA = cor("8a94a3"), cor("b9c2cf"), cor("5d6675")
AZUL, AZUL_LUZ = cor("3a6fb0"), cor("6a9ad6")
MADEIRA, MADEIRA_LUZ, MADEIRA_SOMBRA = cor("a8743f"), cor("c99357"), cor("7a5130")


def caixa_papelao(t, x0, y0, x1, y1, etiqueta=True):
    t.caixa(x0, y0, x1, y1, PAPELAO, PAPELAO_LUZ, PAPELAO_SOMBRA)
    meio = (x0 + x1) // 2
    t.ret(meio, y0 + 1, meio, min(y1 - 1, y0 + 3), FITA)  # fita na tampa
    if etiqueta and x1 - x0 >= 7 and y1 - y0 >= 6:
        t.ret(x0 + 2, y1 - 4, x0 + 5, y1 - 3, cor("f4ecd8"))


def caixas():
    t = Tela(16, 32)
    caixa_papelao(t, 1, 19, 14, 31)
    caixa_papelao(t, 2, 9, 13, 19)
    caixa_papelao(t, 4, 1, 11, 9, etiqueta=False)
    return t, {"category": "storage", "footprintW": 1, "footprintH": 2, "backgroundTiles": 1}


def estante_arquivo():
    t = Tela(32, 32)
    # colunas e prateleiras de aço
    for x in (1, 30):
        t.ret(x - 1, 0, x + 1, 31, CONTORNO)
        t.ret(x, 1, x, 30, ACO_LUZ)
    for y in (10, 20, 30):
        t.ret(1, y - 1, 30, y + 1, CONTORNO)
        t.ret(2, y, 29, y, ACO)
    # caixas de papelão e caixas-arquivo azuis em cada prateleira
    caixa_papelao(t, 3, 2, 12, 9, etiqueta=False)
    t.caixa(13, 3, 19, 9, AZUL, AZUL_LUZ)
    t.caixa(20, 3, 26, 9, AZUL, AZUL_LUZ)
    caixa_papelao(t, 3, 12, 14, 19)
    caixa_papelao(t, 15, 13, 28, 19)
    t.caixa(3, 22, 9, 29, AZUL, AZUL_LUZ)
    caixa_papelao(t, 10, 22, 21, 29)
    t.caixa(22, 23, 28, 29, cor("d9533b"), cor("ef7d63"))
    for x in (5, 15, 22):  # etiquetas das caixas-arquivo
        t.ret(x, 5 if x > 10 else 24, x + 2, 6 if x > 10 else 25, cor("f4ecd8"))
    return t, {"category": "storage", "footprintW": 2, "footprintH": 2, "backgroundTiles": 1}


def servidor():
    t = Tela(16, 32)
    t.caixa(1, 1, 14, 31, cor("2b2f3a"), cor("4a5161"), cor("1c1f27"))
    for y in range(4, 29, 4):  # gavetas do rack com luzes
        t.ret(3, y, 12, y + 2, cor("3b4150"))
        t.p(4, y + 1, cor("3ddc84"))
        t.p(6, y + 1, cor("3ddc84") if y % 8 else cor("5ec8ff"))
        t.p(11, y + 1, cor("ffb84d") if y == 12 else cor("2b2f3a"))
        t.ret(8, y + 1, 9, y + 1, cor("5d6675"))
    return t, {"category": "electronics", "footprintW": 1, "footprintH": 2, "backgroundTiles": 1}


def balcao_cafe():
    t = Tela(32, 32)
    # balcão (tampo claro, portas de madeira)
    t.caixa(0, 15, 31, 31, MADEIRA, MADEIRA_LUZ, MADEIRA_SOMBRA)
    t.ret(1, 15, 30, 17, cor("e8e4dc"))
    t.ret(1, 18, 30, 18, CONTORNO)
    for x in (10, 21):
        t.ret(x, 19, x, 30, CONTORNO)
    for x in (8, 12, 19, 23):
        t.p(x, 24, cor("e9d3a8"))
    # pia com torneira
    t.ret(19, 15, 28, 16, cor("9aa4b2"))
    t.ret(23, 11, 24, 14, ACO)
    t.ret(23, 11, 26, 11, ACO)
    # máquina de café
    t.caixa(2, 2, 13, 16, cor("3a3f4a"), cor("5a6170"), cor("262a32"))
    t.ret(4, 4, 11, 6, cor("1c1f27"))
    t.p(5, 5, cor("3ddc84"))
    t.ret(6, 10, 9, 10, ACO_LUZ)  # bico
    t.ret(6, 12, 9, 15, cor("f4ecd8"))  # xícara
    t.ret(7, 12, 8, 12, cor("6b3e26"))
    # duas canecas no balcão
    for x in (15, 17):
        t.ret(x, 12, x + 1, 14, cor("d9533b") if x == 15 else cor("e0a81c"))
    return t, {"category": "kitchen", "footprintW": 2, "footprintH": 2, "backgroundTiles": 1}


def geladeira():
    t = Tela(16, 32)
    t.caixa(1, 0, 14, 31, cor("e6ebf0"), cor("ffffff"), cor("b8c1cc"))
    t.ret(2, 11, 13, 11, CONTORNO)
    t.ret(11, 4, 12, 8, ACO)
    t.ret(11, 14, 12, 21, ACO)
    t.ret(3, 3, 5, 5, cor("e0a81c"))  # ímã
    t.ret(4, 15, 7, 18, cor("f4ecd8"))  # bilhete
    return t, {"category": "kitchen", "footprintW": 1, "footprintH": 2, "backgroundTiles": 1}


def guarda_corpo():
    t = Tela(16, 16)
    t.ret(0, 3, 15, 6, CONTORNO)
    t.ret(0, 4, 15, 5, MADEIRA_LUZ)
    for x in (1, 7, 13):
        t.ret(x, 6, x + 2, 15, CONTORNO)
        t.ret(x + 1, 6, x + 1, 14, MADEIRA)
    return t, {"category": "outdoor", "footprintW": 1, "footprintH": 1, "backgroundTiles": 0}


def espreguicadeira():
    t = Tela(16, 32)
    t.caixa(2, 2, 13, 12, cor("2fb7c4"), cor("6fd6df"), cor("1f8a94"))  # encosto
    for y in range(4, 11, 3):
        t.ret(3, y, 12, y, cor("f4ecd8"))
    t.caixa(2, 12, 13, 27, cor("2fb7c4"), cor("6fd6df"), cor("1f8a94"))  # assento
    for y in range(15, 26, 3):
        t.ret(3, y, 12, y, cor("f4ecd8"))
    t.ret(2, 28, 3, 31, CONTORNO)
    t.ret(12, 28, 13, 31, CONTORNO)
    return t, {"category": "chairs", "footprintW": 1, "footprintH": 2, "backgroundTiles": 0}


def quadro_ciello():
    """A logo da Ciello (contorno de nuvem marfim com o ponto dourado) num quadro azul-marinho, para a parede do Gerente."""
    t = Tela(32, 32)
    t.caixa(1, 3, 30, 28, cor("263a59"), cor("3a5582"), cor("13213a"))
    marfim, ouro = cor("f8f4e8"), cor("e0a81c")

    desenho = [  # a nuvem da logo, traço grosso aberto embaixo à direita, e o ponto dourado
        ".......#####........",
        "......##...##.......",
        ".....##.....##......",
        "..####.......##.....",
        ".##...........#.....",
        "##............##....",
        "#..............#....",
        "#..............#....",
        "##.............#....",
        ".#############.#.oo.",
        "...............#.oo.",
    ]
    for y, linha in enumerate(desenho):
        for x, ch in enumerate(linha):
            if ch == "#":
                t.p(x + 6, y + 9, marfim)
            elif ch == "o":
                t.p(x + 6, y + 9, ouro)
    t.ret(13, 1, 18, 2, CONTORNO)  # gancho
    return t, {"category": "wall", "footprintW": 2, "footprintH": 2, "backgroundTiles": 0, "parede": True}


def janela():
    t = Tela(32, 32)
    t.caixa(2, 4, 29, 27, cor("cfe8f5"), cor("eaf6fb"), cor("9fc9de"))
    t.ret(15, 5, 16, 26, cor("f4ecd8"))  # caixilho
    t.ret(3, 15, 28, 16, cor("f4ecd8"))
    for x, y in ((6, 8), (7, 8), (8, 9), (21, 10), (22, 10), (23, 9)):  # nuvenzinhas
        t.p(x, y, cor("ffffff"))
    t.ret(3, 24, 28, 26, cor("7fbf6a"))  # copa de árvore lá fora
    t.ret(1, 27, 30, 29, CONTORNO)
    t.ret(2, 28, 29, 28, cor("e8e4dc"))  # parapeito
    return t, {"category": "wall", "footprintW": 2, "footprintH": 2, "backgroundTiles": 0, "parede": True}


def tripe_camera():
    t = Tela(16, 32)
    t.caixa(3, 4, 12, 11, cor("2b2f3a"), cor("4a5161"))
    t.ret(12, 6, 14, 9, CONTORNO)  # lente
    t.ret(13, 7, 13, 8, cor("5ec8ff"))
    t.p(5, 6, cor("d9533b"))  # luz de gravando
    t.ret(7, 12, 8, 24, CONTORNO)
    for i in range(7):  # pernas do tripé
        t.p(7 - i, 24 + i, CONTORNO)
        t.p(8 + i, 24 + i, CONTORNO)
        t.p(7, 24 + i, CONTORNO)
    return t, {"category": "electronics", "footprintW": 1, "footprintH": 2, "backgroundTiles": 1}


def ring_light():
    t = Tela(16, 32)
    for x in range(16):
        for y in range(14):
            d = (x - 7.5) ** 2 + (y - 7) ** 2
            if 30 <= d <= 49:
                t.p(x, y, cor("fff6cf") if d < 42 else CONTORNO)
    t.ret(7, 14, 8, 28, CONTORNO)
    t.ret(4, 29, 11, 31, CONTORNO)
    return t, {"category": "electronics", "footprintW": 1, "footprintH": 2, "backgroundTiles": 1}


def bebedouro():
    t = Tela(16, 32)
    t.caixa(4, 1, 11, 12, cor("8fd3f4"), cor("c8ecfb"), cor("5aa9d6"))  # galão
    t.caixa(2, 12, 13, 31, cor("e6ebf0"), cor("ffffff"), cor("b8c1cc"))
    t.ret(5, 17, 6, 18, cor("5ec8ff"))
    t.ret(9, 17, 10, 18, cor("d9533b"))
    t.ret(4, 22, 11, 23, cor("9aa4b2"))
    return t, {"category": "kitchen", "footprintW": 1, "footprintH": 2, "backgroundTiles": 1}


def arcade():
    t = Tela(16, 32)
    t.caixa(1, 0, 14, 31, cor("6b4fbb"), cor("8e6bd8"), cor("4b2f99"))
    t.caixa(3, 4, 12, 13, cor("1c1f27"))
    t.ret(5, 7, 6, 8, cor("3ddc84"))
    t.ret(9, 9, 10, 10, cor("e0a81c"))
    t.ret(2, 16, 13, 18, cor("2b2f3a"))
    t.p(5, 17, cor("d9533b"))
    t.p(8, 17, cor("5ec8ff"))
    t.p(10, 17, cor("e0a81c"))
    t.ret(5, 22, 10, 22, cor("e0a81c"))
    return t, {"category": "decor", "footprintW": 1, "footprintH": 2, "backgroundTiles": 1}


def luminaria():
    t = Tela(16, 32)
    t.caixa(3, 2, 12, 9, cor("f1c95a"), cor("fff0b5"), cor("d99a0b"))  # cúpula
    t.ret(7, 10, 8, 28, CONTORNO)
    t.ret(4, 29, 11, 31, CONTORNO)
    t.ret(5, 30, 10, 30, cor("5d6675"))
    return t, {"category": "decor", "footprintW": 1, "footprintH": 2, "backgroundTiles": 1}


def cavalete_metas():
    t = Tela(16, 32)
    t.caixa(1, 2, 14, 18, cor("f8f8f4"), cor("ffffff"))
    for i, h in enumerate((3, 5, 4, 7, 9)):  # gráfico de barras subindo
        t.ret(3 + i * 2, 16 - h, 3 + i * 2, 15, cor("3dbe6e") if i == 4 else cor("5e92e6"))
    t.ret(3, 4, 9, 4, cor("d9533b"))  # "META"
    for x in (3, 12):
        t.ret(x, 19, x + 1, 31, CONTORNO)
    t.ret(7, 19, 8, 29, MADEIRA_SOMBRA)
    return t, {"category": "decor", "footprintW": 1, "footprintH": 2, "backgroundTiles": 1}


def arquivo_aco():
    t = Tela(16, 32)
    t.caixa(1, 4, 14, 31, ACO, ACO_LUZ, ACO_SOMBRA)
    for y in (6, 14, 22):
        t.ret(2, y + 7, 13, y + 7, CONTORNO)
        t.ret(6, y + 2, 9, y + 3, ACO_SOMBRA)
        t.ret(5, y + 5, 10, y + 5, cor("f4ecd8"))
    t.ret(4, 1, 11, 4, PAPELAO)  # caixa de documentos em cima
    t.ret(4, 1, 11, 1, CONTORNO)
    return t, {"category": "storage", "footprintW": 1, "footprintH": 2, "backgroundTiles": 1}


# ------------------------------------------------------------------ premium (sala do Gerente) e pacote de decoração
MOGNO, MOGNO_LUZ, MOGNO_SOMBRA, MOGNO_BRILHO = cor("5c2a1c"), cor("7d3f2a"), cor("3d1a10"), cor("9a5538")
MOGNO_CONTORNO = cor("240c06")
OURO, OURO_LUZ, OURO_SOMBRA = cor("e0a81c"), cor("f6d77a"), cor("a87810")
COURO, COURO_LUZ, COURO_SOMBRA = cor("2e2c36"), cor("4f4c5e"), cor("19181f")
MARINHO, MARINHO_LUZ, MARINHO_SOMBRA = cor("263a59"), cor("3a5582"), cor("13213a")
FOLHA, FOLHA_LUZ, FOLHA_ESCURA, FOLHA_CONTORNO = cor("3f8a48"), cor("74b85e"), cor("2b6634"), cor("173a1d")
SOMBRA_CHAO = (0, 0, 0, 51)  # a sombra suave no chão, igual à dos móveis do pixel-agents


def sombra(t, x0, x1, y0, y1=None):
    t.ret(x0, y0, x1, y0 if y1 is None else y1, SOMBRA_CHAO)


def elipse(t, cx, cy, rx, ry, c, contorno=None):
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d <= 1:
                t.p(x, y, c)
            elif contorno and d <= 1.55:
                if t.px[x, y][3] == 0 if 0 <= x < t.w and 0 <= y < t.h else False:
                    t.p(x, y, contorno)


def folha(t, cx, cy, rx, ry, base=FOLHA):
    elipse(t, cx, cy, rx, ry, base, FOLHA_CONTORNO)
    t.p(int(cx - rx / 3), int(cy - ry / 3), FOLHA_LUZ)
    if rx >= 3:
        t.p(int(cx - rx / 3) + 1, int(cy - ry / 3), FOLHA_LUZ)


def mesa_executiva():
    """Mesa de mogno do Gerente, de frente para a sala: tampo com apoio de couro marinho e o painel frontal entalhado."""
    t = Tela(48, 32)
    sombra(t, 2, 45, 30, 31)
    t.ret(0, 2, 47, 18, MOGNO_CONTORNO)                  # tampo
    t.ret(1, 3, 46, 16, MOGNO_LUZ)
    t.ret(1, 3, 46, 3, MOGNO_BRILHO)
    for x in range(4, 46, 9):                             # veio da madeira
        t.ret(x, 6 + x % 4, x + 4, 6 + x % 4, MOGNO)
    t.caixa(13, 5, 34, 13, MARINHO, MARINHO_LUZ, MARINHO_SOMBRA)  # apoio de couro
    t.ret(15, 7, 32, 7, OURO_SOMBRA)
    t.ret(1, 16, 46, 17, MOGNO)                           # borda do tampo com filete dourado
    t.ret(1, 17, 46, 17, OURO)
    t.ret(1, 18, 46, 29, MOGNO)                           # painel da frente
    t.ret(0, 18, 0, 30, MOGNO_CONTORNO)
    t.ret(47, 18, 47, 30, MOGNO_CONTORNO)
    for x0 in (3, 25):                                    # dois quadros entalhados
        t.ret(x0, 20, x0 + 19, 27, MOGNO_SOMBRA)
        t.ret(x0 + 1, 21, x0 + 18, 26, MOGNO_LUZ)
        t.ret(x0 + 2, 22, x0 + 17, 25, MOGNO)
    t.ret(23, 22, 24, 25, OURO)                           # emblema
    t.p(23, 22, OURO_LUZ)
    t.ret(0, 30, 47, 30, MOGNO_CONTORNO)                  # rodapé
    t.ret(1, 29, 46, 29, MOGNO_SOMBRA)
    return t, {"category": "desks", "footprintW": 3, "footprintH": 2, "backgroundTiles": 1}


def poltrona_frente():
    t = Tela(16, 32)
    sombra(t, 3, 12, 30, 31)
    t.ret(4, 26, 11, 27, COURO_SOMBRA)                    # pé de estrela
    t.ret(7, 23, 8, 27, ACO_SOMBRA)
    t.ret(3, 28, 4, 29, CONTORNO)
    t.ret(11, 28, 12, 29, CONTORNO)
    t.ret(7, 28, 8, 29, CONTORNO)
    t.caixa(3, 4, 12, 20, COURO, COURO_LUZ)               # encosto alto
    t.ret(3, 4, 3, 4, T)
    t.ret(12, 4, 12, 4, T)
    for x, y in ((5, 8), (10, 8), (7, 11), (5, 14), (10, 14)):  # capitonê
        t.p(x, y, COURO_SOMBRA)
        t.p(x, y - 1, COURO_LUZ)
    t.caixa(1, 15, 3, 23, COURO_SOMBRA, COURO)            # braços
    t.caixa(12, 15, 14, 23, COURO_SOMBRA, COURO)
    t.caixa(3, 18, 12, 24, COURO, COURO_LUZ, COURO_SOMBRA)  # assento
    t.p(2, 16, OURO)
    t.p(13, 16, OURO)
    return t


def poltrona_costas():
    t = Tela(16, 32)
    sombra(t, 3, 12, 30, 31)
    t.ret(3, 28, 4, 29, CONTORNO)
    t.ret(11, 28, 12, 29, CONTORNO)
    t.ret(7, 25, 8, 29, ACO_SOMBRA)
    t.caixa(1, 17, 3, 25, COURO_SOMBRA, COURO)            # braços
    t.caixa(12, 17, 14, 25, COURO_SOMBRA, COURO)
    t.caixa(3, 6, 12, 26, COURO, COURO_LUZ, COURO_SOMBRA)  # costas do encosto
    t.ret(3, 6, 3, 6, T)
    t.ret(12, 6, 12, 6, T)
    t.ret(7, 8, 8, 24, COURO_SOMBRA)                      # costura do meio
    t.ret(4, 8, 4, 24, COURO_LUZ)
    return t


def poltrona_lado():
    t = Tela(16, 32)
    sombra(t, 3, 13, 30, 31)
    t.ret(4, 28, 13, 29, CONTORNO)                        # pé
    t.ret(8, 24, 9, 27, ACO_SOMBRA)
    t.caixa(2, 5, 6, 24, COURO, COURO_LUZ, COURO_SOMBRA)  # encosto (de perfil, olhando para a direita)
    t.ret(2, 5, 2, 5, T)
    t.caixa(5, 18, 13, 24, COURO, COURO_LUZ, COURO_SOMBRA)  # assento
    t.caixa(6, 15, 12, 17, COURO_SOMBRA, COURO)           # braço
    t.ret(11, 17, 12, 19, COURO_SOMBRA)
    t.p(12, 15, OURO)
    return t


def poltrona_couro():
    return None, {"category": "chairs", "footprintW": 1, "footprintH": 2, "backgroundTiles": 1,
                  "grupo": [("FRONT", "front", poltrona_frente), ("BACK", "back", poltrona_costas), ("SIDE", "side", poltrona_lado)]}


def estante_escura():
    """Estante de mogno do chão ao teto: livros, um troféu e o armário embaixo."""
    t = Tela(32, 48)
    sombra(t, 1, 30, 46, 47)
    t.ret(0, 0, 31, 45, MOGNO_CONTORNO)
    t.ret(1, 1, 30, 2, MOGNO_BRILHO)                      # cornija
    t.ret(1, 3, 30, 44, MOGNO)
    t.ret(3, 4, 28, 33, cor("2a1209"))                    # fundo das prateleiras
    for y in (13, 23, 33):
        t.ret(2, y, 29, y, MOGNO_LUZ)
        t.ret(2, y + 1, 29, y + 1, MOGNO_SOMBRA)
    lombadas = [MARINHO_LUZ, OURO, cor("8c2f39"), cor("2f6b4f"), cor("e8dcc0"), MARINHO, cor("8c2f39"), OURO_SOMBRA]
    x = 4
    for i, c in enumerate(lombadas):                      # livros em pé, prateleira de cima
        alto = 7 + (i * 5) % 3
        t.ret(x, 13 - alto, x + 1, 12, c)
        t.p(x, 13 - alto + 2, OURO_LUZ if c != OURO else MOGNO_SOMBRA)
        x += 2 if i % 3 else 3
    t.ret(22, 9, 26, 12, OURO)                            # troféu pequeno
    t.ret(23, 7, 25, 8, OURO_LUZ)
    t.ret(23, 12, 25, 12, MOGNO_SOMBRA)
    for i, c in enumerate((cor("2f6b4f"), MARINHO_LUZ, cor("e8dcc0"))):  # livros deitados, prateleira do meio
        t.ret(4, 22 - i * 2, 13 - i, 22 - i * 2 + 1, c)
    t.ret(17, 17, 21, 22, cor("e6ebf0"))                  # vasinho com planta
    t.ret(17, 17, 21, 17, CONTORNO)
    folha(t, 18, 15, 2, 2)
    folha(t, 21, 14, 2, 2, FOLHA_ESCURA)
    for i, c in enumerate((cor("8c2f39"), OURO, MARINHO, cor("e8dcc0"), MARINHO_LUZ, cor("2f6b4f"))):
        t.ret(5 + i * 4, 26, 7 + i * 4, 32, c)            # prateleira de baixo
        t.p(6 + i * 4, 28, OURO_LUZ if c != OURO else MOGNO_SOMBRA)
    t.ret(2, 35, 29, 44, MOGNO_LUZ)                       # armário
    t.ret(15, 35, 16, 44, MOGNO_CONTORNO)
    for x0 in (3, 18):
        t.ret(x0, 36, x0 + 10, 43, MOGNO)
        t.ret(x0, 36, x0 + 10, 36, MOGNO_SOMBRA)
    t.ret(13, 39, 13, 40, OURO)
    t.ret(18, 39, 18, 40, OURO)
    return t, {"category": "storage", "footprintW": 2, "footprintH": 3, "backgroundTiles": 2}


def painel_ciello():
    """A logo da Ciello num painel marinho com moldura de mogno e filete dourado, iluminado por duas arandelas."""
    t = Tela(48, 32)
    t.ret(1, 3, 46, 29, MOGNO_CONTORNO)
    t.ret(2, 4, 45, 28, MOGNO_LUZ)
    t.ret(2, 4, 45, 4, MOGNO_BRILHO)
    t.ret(4, 6, 43, 26, OURO_SOMBRA)
    t.ret(5, 7, 42, 25, MARINHO)
    t.ret(5, 7, 42, 7, MARINHO_LUZ)
    marfim = cor("f8f4e8")
    desenho = [
        ".......#####........",
        "......##...##.......",
        ".....##.....##......",
        "..####.......##.....",
        ".##...........#.....",
        "##............##....",
        "#..............#....",
        "#..............#....",
        "##.............#....",
        ".#############.#.oo.",
        "...............#.oo.",
    ]
    for y, linha in enumerate(desenho):
        for x, ch in enumerate(linha):
            if ch == "#":
                t.p(x + 15, y + 9, marfim)
            elif ch == "o":
                t.p(x + 15, y + 9, OURO)
    t.ret(17, 22, 30, 22, OURO)                           # sublinhado
    for x in (8, 38):                                     # arandelas
        t.ret(x, 0, x + 1, 2, OURO_SOMBRA)
        t.ret(x - 1, 2, x + 2, 3, OURO_LUZ)
    return t, {"category": "wall", "footprintW": 3, "footprintH": 2, "backgroundTiles": 0, "parede": True}


def vaso_grande():
    """Planta alta num vaso de cerâmica escura com faixa dourada: 2 blocos no chão."""
    t = Tela(32, 48)
    sombra(t, 7, 24, 46, 47)
    t.ret(15, 16, 16, 37, MADEIRA_SOMBRA)                 # caule
    t.p(14, 26, MADEIRA_SOMBRA)
    t.p(17, 21, MADEIRA_SOMBRA)
    folhas = [(15, 5, 4, 3, FOLHA), (9, 9, 4, 3, FOLHA_ESCURA), (22, 9, 4, 3, FOLHA), (11, 15, 5, 3, FOLHA),
              (21, 15, 5, 3, FOLHA_ESCURA), (6, 20, 4, 3, FOLHA), (25, 21, 4, 3, FOLHA), (12, 23, 4, 3, FOLHA_ESCURA),
              (20, 26, 4, 3, FOLHA), (8, 28, 4, 2, FOLHA_ESCURA), (24, 29, 3, 2, FOLHA_ESCURA), (16, 11, 3, 2, FOLHA)]
    for cx, cy, rx, ry, c in folhas:
        folha(t, cx, cy, rx, ry, c)
    t.ret(8, 34, 23, 36, CONTORNO)                        # boca do vaso
    t.ret(9, 35, 22, 35, cor("4a3a30"))
    t.ret(9, 36, 22, 45, CONTORNO)
    t.ret(10, 36, 21, 44, cor("2f3440"))
    t.ret(10, 36, 11, 44, cor("4a5161"))
    t.ret(10, 39, 21, 40, OURO)
    t.ret(10, 39, 21, 39, OURO_LUZ)
    t.ret(11, 45, 20, 45, CONTORNO)
    return t, {"category": "decor", "footprintW": 2, "footprintH": 3, "backgroundTiles": 2}


def vaso_pequeno():
    """Suculenta num vaso branco: 1 bloco, baixo, vai em qualquer canto."""
    t = Tela(16, 16)
    sombra(t, 4, 11, 15)
    for cx, cy, rx, ry, c in ((8, 6, 3, 2, FOLHA), (5, 8, 2, 2, FOLHA_ESCURA), (11, 8, 2, 2, FOLHA_ESCURA), (8, 4, 2, 2, FOLHA)):
        folha(t, cx, cy, rx, ry, c)
    t.caixa(4, 9, 11, 14, cor("e6ebf0"), cor("ffffff"), cor("b8c1cc"))
    t.ret(5, 10, 10, 10, OURO)
    return t, {"category": "decor", "footprintW": 1, "footprintH": 1, "backgroundTiles": 0}


def notebook():
    """Notebook visto por trás (a tampa com o ponto dourado da Ciello), para quem senta de frente para a sala."""
    t = Tela(16, 32)  # o desenho fica na metade de cima, sobre o tampo; a de baixo é a frente da mesa
    t.caixa(2, 4, 13, 13, cor("c9ced6"), cor("eef1f4"), cor("9aa2ad"))
    t.ret(7, 8, 8, 9, OURO)
    t.ret(1, 13, 14, 14, CONTORNO)
    t.ret(2, 13, 13, 13, cor("5d6675"))
    return t, {"category": "electronics", "footprintW": 1, "footprintH": 2, "backgroundTiles": 1, "superficie": True}


def trofeu():
    t = Tela(16, 32)  # o desenho fica na metade de cima, sobre o tampo; a de baixo é a frente da mesa
    t.ret(4, 2, 11, 7, CONTORNO)
    t.ret(5, 2, 10, 7, OURO)
    t.ret(5, 2, 6, 6, OURO_LUZ)
    t.ret(2, 3, 4, 3, OURO_SOMBRA)
    t.ret(2, 3, 2, 5, OURO_SOMBRA)
    t.ret(11, 3, 13, 3, OURO_SOMBRA)
    t.ret(13, 3, 13, 5, OURO_SOMBRA)
    t.ret(6, 8, 9, 8, OURO_SOMBRA)
    t.ret(7, 9, 8, 10, OURO)
    t.caixa(4, 11, 11, 14, MOGNO, MOGNO_LUZ)
    t.ret(6, 12, 9, 12, OURO)
    return t, {"category": "decor", "footprintW": 1, "footprintH": 2, "backgroundTiles": 1, "superficie": True}


def globo():
    t = Tela(16, 32)  # o desenho fica na metade de cima, sobre o tampo; a de baixo é a frente da mesa
    elipse(t, 8, 6, 4.5, 4.5, cor("3a6fb0"), CONTORNO)
    for x, y in ((6, 4), (7, 4), (6, 5), (5, 6), (9, 7), (10, 7), (10, 8), (9, 3)):  # continentes
        t.p(x, y, cor("7fbf6a"))
    t.p(6, 3, cor("a8d3ff"))
    for y in range(1, 12):                                # meridiano dourado
        t.p(13 if 3 < y < 9 else 12, y, OURO)
    t.ret(7, 11, 8, 12, OURO_SOMBRA)
    t.caixa(4, 12, 11, 14, MOGNO, MOGNO_LUZ)
    return t, {"category": "decor", "footprintW": 1, "footprintH": 2, "backgroundTiles": 1, "superficie": True}


def aparador():
    """Aparador baixo de mogno com puxadores dourados; serve de apoio para troféu, globo e café."""
    t = Tela(32, 32)
    sombra(t, 1, 30, 30, 31)
    t.ret(0, 12, 31, 29, MOGNO_CONTORNO)
    t.ret(1, 13, 30, 15, MOGNO_LUZ)
    t.ret(1, 13, 30, 13, MOGNO_BRILHO)
    t.ret(1, 16, 30, 28, MOGNO)
    for x0 in (2, 12, 22):
        t.ret(x0, 17, x0 + 7, 27, MOGNO_SOMBRA)
        t.ret(x0 + 1, 18, x0 + 6, 26, MOGNO_LUZ)
        t.ret(x0 + 2, 19, x0 + 5, 25, MOGNO)
        t.ret(x0 + 3, 21, x0 + 4, 21, OURO)
    t.ret(2, 29, 3, 30, MOGNO_CONTORNO)
    t.ret(28, 29, 29, 30, MOGNO_CONTORNO)
    return t, {"category": "desks", "footprintW": 2, "footprintH": 2, "backgroundTiles": 1}


def pufe():
    t = Tela(16, 16)
    sombra(t, 2, 13, 14, 15)
    elipse(t, 7.5, 9, 6, 4.5, cor("e0a81c"), CONTORNO)
    elipse(t, 7.5, 7, 5, 2.5, cor("f1c95a"))
    t.p(7, 7, cor("a87810"))
    t.ret(3, 11, 12, 11, cor("c08e12"))
    return t, {"category": "chairs", "footprintW": 1, "footprintH": 1, "backgroundTiles": 0}


def mesa_lateral():
    t = Tela(16, 16)
    sombra(t, 3, 12, 15)
    elipse(t, 7.5, 5, 6, 3, MADEIRA_LUZ, CONTORNO)
    t.ret(3, 4, 11, 4, cor("e0b77a"))
    t.ret(7, 8, 8, 13, CONTORNO)
    t.ret(4, 14, 11, 14, CONTORNO)
    return t, {"category": "desks", "footprintW": 1, "footprintH": 1, "backgroundTiles": 0}


def palete_caixas():
    """Palete de madeira com uma camada de caixas: baixo, 2 blocos, fica bem no meio do estoque."""
    t = Tela(32, 16)
    sombra(t, 1, 30, 15)
    t.ret(0, 11, 31, 14, CONTORNO)
    t.ret(1, 12, 30, 12, MADEIRA_LUZ)
    for x in (1, 14, 27):
        t.ret(x, 13, x + 3, 13, MADEIRA)
    caixa_papelao(t, 1, 3, 11, 11, etiqueta=False)
    caixa_papelao(t, 11, 1, 21, 11)
    caixa_papelao(t, 21, 4, 30, 11, etiqueta=False)
    t.ret(3, 7, 7, 8, cor("f4ecd8"))
    return t, {"category": "storage", "footprintW": 2, "footprintH": 1, "backgroundTiles": 0}


def maquina_salgadinhos():
    t = Tela(16, 32)
    sombra(t, 1, 14, 31)
    t.caixa(1, 1, 14, 30, cor("d9533b"), cor("ef7d63"), cor("a83a26"))
    t.caixa(3, 4, 10, 24, cor("cfe8f5"), cor("eaf6fb"))   # vitrine
    for y, cores in ((7, ("e0a81c", "3dbe6e", "5e92e6")), (12, ("8e6bd8", "e0a81c", "d9533b")), (17, ("3dbe6e", "5e92e6", "e0a81c"))):
        for i, c in enumerate(cores):
            t.ret(4 + i * 2, y, 4 + i * 2, y + 2, cor(c))
        t.ret(4, y + 3, 9, y + 3, ACO)
    t.ret(11, 6, 12, 13, cor("2b2f3a"))                   # teclado
    t.p(11, 8, cor("3ddc84"))
    t.ret(11, 16, 12, 17, cor("1c1f27"))                  # moedas
    t.ret(3, 26, 10, 28, cor("1c1f27"))                   # gaveta de saída
    return t, {"category": "kitchen", "footprintW": 1, "footprintH": 2, "backgroundTiles": 1}


def guarda_sol_mesa():
    """Mesa redonda com guarda-sol listrado, para a varanda."""
    t = Tela(32, 48)
    sombra(t, 4, 27, 44, 46)
    t.ret(15, 9, 16, 40, cor("e8e4dc"))                   # haste
    t.ret(15, 9, 15, 40, ACO)
    for y in range(0, 12):                                # lona em gomos
        meia = int(2 + y * 1.25)
        for x in range(16 - meia, 16 + meia):
            t.p(x, y + 1, cor("f8f4e8") if ((x - 16) // 3) % 2 else cor("2fb7c4"))
    t.ret(1, 13, 30, 13, CONTORNO)
    for x in range(1, 31, 3):
        t.p(x, 14, cor("1f8a94"))
    t.ret(15, 0, 16, 0, CONTORNO)
    elipse(t, 15.5, 33, 10, 4, cor("f8f4e8"), CONTORNO)   # tampo da mesa
    t.ret(8, 34, 23, 34, cor("dcd6c8"))
    t.ret(19, 30, 21, 32, cor("d9533b"))                  # copo de suco
    t.ret(10, 31, 12, 32, cor("e0a81c"))
    t.ret(14, 37, 17, 43, CONTORNO)
    t.ret(10, 44, 21, 45, CONTORNO)
    return t, {"category": "outdoor", "footprintW": 2, "footprintH": 3, "backgroundTiles": 2}


def tv_parede():
    t = Tela(32, 32)
    t.caixa(1, 6, 30, 25, cor("1c1f27"), cor("2b2f3a"))
    t.ret(3, 8, 28, 23, MARINHO)
    for y in range(8, 24):                                # degradê da tela
        if y > 15:
            t.ret(3, y, 28, y, MARINHO_SOMBRA)
    t.ret(13, 12, 13, 19, cor("f8f4e8"))                  # play
    for i in range(4):
        t.ret(14 + i, 13 + i // 2, 14 + i, 18 - i // 2, cor("f8f4e8"))
    t.ret(4, 21, 18, 21, cor("d9533b"))                   # barra de progresso
    t.ret(19, 21, 27, 21, cor("5d6675"))
    t.ret(15, 26, 16, 27, CONTORNO)
    return t, {"category": "wall", "footprintW": 2, "footprintH": 2, "backgroundTiles": 0, "parede": True}


def painel_metricas():
    t = Tela(32, 32)
    t.caixa(1, 4, 30, 27, cor("1c1f27"), cor("2b2f3a"))
    t.ret(3, 6, 28, 25, cor("101522"))
    alturas = (3, 5, 4, 7, 6, 9, 11)
    for i, h in enumerate(alturas):                       # barras subindo
        t.ret(4 + i * 3, 24 - h, 5 + i * 3, 23, cor("3dbe6e") if i == len(alturas) - 1 else cor("5e92e6"))
    pontos = [(4, 16), (8, 15), (12, 16), (16, 12), (20, 11), (24, 8), (27, 7)]
    for (x0, y0), (x1, y1) in zip(pontos, pontos[1:]):    # linha de seguidores
        for k in range(x1 - x0 + 1):
            t.p(x0 + k, round(y0 + (y1 - y0) * k / max(1, x1 - x0)), OURO)
    t.ret(4, 7, 9, 7, cor("f8f4e8"))
    t.ret(22, 7, 23, 8, cor("3ddc84"))
    return t, {"category": "wall", "footprintW": 2, "footprintH": 2, "backgroundTiles": 0, "parede": True}


def quadro_avisos():
    t = Tela(32, 32)
    t.caixa(1, 4, 30, 27, cor("b78a52"), cor("caa06a"), cor("8f6a3c"))  # cortiça
    t.ret(0, 3, 31, 3, MADEIRA_SOMBRA)
    t.ret(0, 28, 31, 28, MADEIRA_SOMBRA)
    notas = [(4, 7, "fff3a0"), (12, 6, "a8e6cf"), (21, 8, "ffb3c1"), (5, 16, "a8d3ff"), (14, 15, "fff3a0"), (22, 18, "f8f4e8")]
    for x, y, c in notas:
        t.caixa(x, y, x + 6, y + 6, cor(c))
        t.ret(x + 2, y + 3, x + 4, y + 3, cor("5d6675"))
        t.p(x + 3, y + 1, cor("d9533b"))
    return t, {"category": "wall", "footprintW": 2, "footprintH": 2, "backgroundTiles": 0, "parede": True}


CARVALHO, CARVALHO_LUZ, CARVALHO_SOMBRA, CARVALHO_CONTORNO = cor("4a2e1b"), cor("6b4429"), cor("2f1c10"), cor("1a0e07")


def porta_carvalho():
    """Porta de carvalho escuro, fechada, para o vão de uma parede (a da sala do Gerente): batente, duas almofadas
    entalhadas e a maçaneta dourada. Não bloqueia o chão: quem tem lugar na sala passa por ela."""
    t = Tela(16, 32)
    t.ret(0, 0, 15, 31, CARVALHO_CONTORNO)               # batente
    t.ret(1, 1, 14, 31, CARVALHO_SOMBRA)
    t.ret(2, 2, 13, 31, CARVALHO)                        # folha da porta
    t.ret(2, 2, 13, 2, CARVALHO_LUZ)
    for y0, y1 in ((5, 14), (18, 28)):                   # almofadas entalhadas
        t.ret(4, y0, 11, y1, CARVALHO_SOMBRA)
        t.ret(5, y0 + 1, 11, y1, CARVALHO_LUZ)
        t.ret(5, y0 + 1, 10, y1 - 1, CARVALHO)
    for x, y in ((7, 8), (8, 11), (6, 22), (9, 25)):      # veio da madeira
        t.p(x, y, CARVALHO_SOMBRA)
    t.ret(11, 16, 12, 17, OURO)                          # maçaneta
    t.p(11, 16, OURO_LUZ)
    t.ret(1, 31, 14, 31, CARVALHO_CONTORNO)              # soleira
    return t, {"category": "wall", "footprintW": 1, "footprintH": 2, "backgroundTiles": 2, "parede": True}


MOVEIS = {"CAIXAS": ("Caixas", caixas), "ESTANTE_ARQUIVO": ("Estante de arquivos", estante_arquivo), "SERVIDOR": ("Servidor", servidor),
          "BALCAO_CAFE": ("Balcão com café", balcao_cafe), "GELADEIRA": ("Geladeira", geladeira),
          "GUARDA_CORPO": ("Guarda-corpo", guarda_corpo), "ESPREGUICADEIRA": ("Espreguiçadeira", espreguicadeira),
          "QUADRO_CIELLO": ("Quadro da Ciello", quadro_ciello), "JANELA": ("Janela", janela), "TRIPE_CAMERA": ("Câmera no tripé", tripe_camera),
          "RING_LIGHT": ("Ring light", ring_light), "BEBEDOURO": ("Bebedouro", bebedouro), "ARCADE": ("Fliperama", arcade),
          "LUMINARIA": ("Luminária", luminaria), "CAVALETE_METAS": ("Cavalete de metas", cavalete_metas), "ARQUIVO_ACO": ("Arquivo de aço", arquivo_aco),
          "MESA_EXECUTIVA": ("Mesa executiva de mogno", mesa_executiva), "POLTRONA_COURO": ("Poltrona de couro", poltrona_couro),
          "ESTANTE_ESCURA": ("Estante de mogno", estante_escura), "PAINEL_CIELLO": ("Painel da Ciello", painel_ciello),
          "VASO_GRANDE": ("Vaso grande", vaso_grande), "VASO_PEQUENO": ("Vaso pequeno", vaso_pequeno), "NOTEBOOK": ("Notebook", notebook),
          "TROFEU": ("Troféu", trofeu), "GLOBO": ("Globo", globo), "APARADOR": ("Aparador", aparador), "PUFE": ("Pufe", pufe),
          "MESA_LATERAL": ("Mesinha lateral", mesa_lateral), "PALETE_CAIXAS": ("Palete com caixas", palete_caixas),
          "MAQUINA_SALGADINHOS": ("Máquina de salgadinhos", maquina_salgadinhos), "GUARDA_SOL_MESA": ("Mesa com guarda-sol", guarda_sol_mesa),
          "TV_PAREDE": ("TV de parede", tv_parede), "PAINEL_METRICAS": ("Painel de métricas", painel_metricas),
          "QUADRO_AVISOS": ("Mural de avisos", quadro_avisos), "PORTA_CARVALHO": ("Porta de carvalho", porta_carvalho)}


def main():
    for ident, (nome, desenhar) in MOVEIS.items():
        tela, extra = desenhar()
        pasta = DESTINO / ident
        pasta.mkdir(parents=True, exist_ok=True)
        manifest = {"id": ident, "name": nome, "category": extra["category"], "type": "asset", "canPlaceOnWalls": extra.get("parede", False),
                    "canPlaceOnSurfaces": extra.get("superficie", False), "backgroundTiles": extra["backgroundTiles"]}
        tam = {"footprintW": extra["footprintW"], "footprintH": extra["footprintH"]}
        if "grupo" in extra:  # grupo de rotação (frente, costas, lado espelhado), como as cadeiras do pixel-agents
            manifest.update({"type": "group", "groupType": "rotation", "rotationScheme": "3-way-mirror", "members": []})
            for sufixo, orientacao, desenhar_membro in extra["grupo"]:
                membro = desenhar_membro()
                mid = f"{ident}_{sufixo}"
                membro.im.save(pasta / f"{mid}.png")
                manifest["members"].append({"type": "asset", "id": mid, "file": f"{mid}.png", "width": membro.w, "height": membro.h, **tam,
                                            "orientation": orientacao, **({"mirrorSide": True} if orientacao == "side" else {})})
            print(f"{ident}: grupo com {len(extra['grupo'])}")
        else:
            tela.im.save(pasta / f"{ident}.png")
            manifest.update({"width": tela.w, "height": tela.h, **tam})
            print(f"{ident}: {tela.w}x{tela.h}")
        (pasta / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
