"""Gera o layout do escritório da Ciello no formato do pixel-agents (OfficeLayout v1).

Usa os mesmos móveis e os mesmos módulos do layout padrão do pixel-agents (estação com mesa + PC + banco;
mesa de reunião com cadeiras e PCs laterais; sofás em volta da mesa de centro), em três salas:

  Sala 1  Pesquisa (em cima) e Estúdio (embaixo)        4 estações
  Sala 2  Comercial: mesa do SDR/closer + sala de demo   4 lugares + sofás
  Sala 3  Análise & Anúncios (em cima) e Postagem        4 estações

  python central/escritorio/gerar_layout.py   ->  central/escritorio/layout-ciello.json
"""
import json
from pathlib import Path

COLS, ROWS = 37, 14
PAREDE, MADEIRA, AZUL, XADREZ, VAZIO = 0, 7, 1, 9, 255
COR = {  # cores dos pisos e da parede tiradas do layout padrão do pixel-agents
    PAREDE: {"h": 214, "s": 30, "b": -100, "c": -55},
    MADEIRA: {"h": 25, "s": 48, "b": -43, "c": -88},
    AZUL: {"h": 209, "s": 39, "b": -25, "c": -80},
    XADREZ: {"h": 209, "s": 0, "b": -16, "c": -8},
}
SALAS = [(1, 11, MADEIRA), (13, 23, AZUL), (25, 35, MADEIRA)]  # colunas internas e piso
PORTAS = range(6, 9)  # linhas das portas entre as salas
AREAS = [
    ("Pesquisa", "#2FB7C4", 1, 11, 2, 6), ("Estúdio", "#D9533B", 1, 11, 7, 12),
    ("Comercial", "#E0A81C", 13, 23, 2, 12),
    ("Análise & Anúncios", "#8E6BD8", 25, 35, 2, 6), ("Postagem", "#3DBE6E", 25, 35, 7, 12),
]

tiles = [VAZIO] * (COLS * ROWS)
areas = [None] * (COLS * ROWS)
moveis = []


def pos(c, r):
    return r * COLS + c


def movel(tipo, c, r):
    moveis.append({"uid": f"f-ciello-{len(moveis) + 1:03d}", "type": tipo, "col": c, "row": r})


def estacao(c, r):
    """Mesa de frente com PC e banco (módulo do layout padrão)."""
    movel("DESK_FRONT", c, r)
    movel("PC_FRONT_OFF", c + 1, r)
    movel("CUSHIONED_BENCH", c + 1, r + 2)


def mesa_reuniao(c, r):
    """Mesa com 4 cadeiras laterais e 4 PCs (módulo do layout padrão)."""
    movel("TABLE_FRONT", c, r)
    for dr in (0, 2):
        movel("WOODEN_CHAIR_SIDE", c - 1, r + dr)
        movel("WOODEN_CHAIR_SIDE:left", c + 3, r + dr)
        movel("PC_SIDE", c, r + dr)
        movel("PC_SIDE:left", c + 2, r + dr)


def sofas(c, r):
    """Mesa de centro com sofás em volta (módulo do layout padrão)."""
    movel("COFFEE_TABLE", c, r)
    movel("SOFA_FRONT", c, r - 1)
    movel("SOFA_SIDE", c - 1, r)
    movel("SOFA_SIDE:left", c + 2, r)
    movel("SOFA_BACK", c, r + 2)
    movel("COFFEE", c, r + 1)


# paredes e pisos
for c in range(COLS):
    tiles[pos(c, 1)] = PAREDE
for r in range(1, ROWS - 1):
    for c in (0, 12, 24, 36):
        tiles[pos(c, r)] = PAREDE
for c0, c1, piso in SALAS:
    for r in range(2, ROWS - 1):
        for c in range(c0, c1 + 1):
            tiles[pos(c, r)] = piso
for r in PORTAS:
    for c in (12, 24):
        tiles[pos(c, r)] = SALAS[0][2] if c == 12 else SALAS[2][2]
for nome, _, c0, c1, r0, r1 in AREAS:
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            areas[pos(c, r)] = nome

# Sala 1: Pesquisa e Estúdio
for r in (3, 8):
    for c in (2, 7):
        estacao(c, r)
movel("DOUBLE_BOOKSHELF", 2, 0)
movel("CLOCK", 6, 0)
movel("HANGING_PLANT", 9, 0)
movel("PLANT", 11, 1)
movel("BIN", 1, 12)

# Sala 2: Comercial (mesa do time de vendas + canto de demonstração)
mesa_reuniao(17, 3)
sofas(18, 9)
movel("WHITEBOARD", 15, 0)
movel("LARGE_PAINTING", 19, 0)
movel("PLANT_2", 13, 1)
movel("LARGE_PLANT", 21, 10)

# Sala 3: Análise & Anúncios e Postagem
for r in (3, 8):
    for c in (26, 31):
        estacao(c, r)
movel("SMALL_PAINTING", 27, 0)
movel("DOUBLE_BOOKSHELF", 30, 0)
movel("HANGING_PLANT", 34, 0)
movel("PLANT_2", 35, 1)
movel("BIN", 35, 12)

layout = {
    "version": 1, "cols": COLS, "rows": ROWS, "tiles": tiles,
    "tileColors": [COR.get(t) for t in tiles],
    "furniture": moveis, "pets": [],
    "areas": [{"label": n, "color": cor} for n, cor, *_ in AREAS],
    "areaTiles": areas,
}
destino = Path(__file__).with_name("layout-ciello.json")
destino.write_text(json.dumps(layout, ensure_ascii=False), encoding="utf-8")
print(f"{len(moveis)} móveis, {sum(1 for m in moveis if 'CHAIR' in m['type'] or 'BENCH' in m['type'])} lugares -> {destino}")
