"""Desenha os móveis novos do escritório da Ciello em pixel art, no mesmo estilo do pixel-agents (16 px por tile,
contorno escuro, cor chapada com uma linha de luz). Cada móvel vira uma pasta em
escritorio/webview-ui/public/assets/furniture/<ID>/ com o PNG e o manifest.json.

  ARQUIVOS G   CAIXAS (pilha de caixas), ESTANTE_ARQUIVO (estante de aço com caixas), SERVIDOR (o cérebro do escritório)
  COPA         BALCAO_CAFE (balcão com pia e máquina de café), GELADEIRA
  VARANDA      GUARDA_CORPO (grade de madeira), ESPREGUICADEIRA

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
    return t, {"category": "decor", "footprintW": 1, "footprintH": 1, "backgroundTiles": 0}


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


MOVEIS = {"CAIXAS": ("Caixas", caixas), "ESTANTE_ARQUIVO": ("Estante de arquivos", estante_arquivo), "SERVIDOR": ("Servidor", servidor),
          "BALCAO_CAFE": ("Balcão com café", balcao_cafe), "GELADEIRA": ("Geladeira", geladeira),
          "GUARDA_CORPO": ("Guarda-corpo", guarda_corpo), "ESPREGUICADEIRA": ("Espreguiçadeira", espreguicadeira)}


def main():
    for ident, (nome, desenhar) in MOVEIS.items():
        tela, extra = desenhar()
        pasta = DESTINO / ident
        pasta.mkdir(parents=True, exist_ok=True)
        tela.im.save(pasta / f"{ident}.png")
        manifest = {"id": ident, "name": nome, "category": extra["category"], "type": "asset", "canPlaceOnWalls": False,
                    "canPlaceOnSurfaces": False, "backgroundTiles": extra["backgroundTiles"], "width": tela.w, "height": tela.h,
                    "footprintW": extra["footprintW"], "footprintH": extra["footprintH"]}
        (pasta / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{ident}: {tela.w}x{tela.h}")


if __name__ == "__main__":
    main()
