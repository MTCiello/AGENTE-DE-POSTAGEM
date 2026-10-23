"""Gera o layout padrão do escritório (formato OfficeLayout v1 do pixel-agents): 4 salas simples, uma por time.

  +---------+-----------+
  | Gerente ==  Produtor |
  |         |   Social   |
  +----||---+----||-----+
  |Comercial== Vendas    |
  +---------+-----------+

Os agentes moram nestas salas (central/escritorio/nucleo/residentes.py): Gerente; Produtor Social (conteúdo);
Comercial (financeiro, anúncios, caixa de entrada); Vendas (SDR, closer, sucesso do cliente).
O seu escritório pode ser outro: desenhe no editor do escritório (Layout) ou importe um layout.json pela janela
Boas-vindas (Importar meus dados) ou pelo próprio editor. O padrão só entra quando não existe layout nenhum.

Blocos: o escritório é uma grade de blocos de 16 px. A parede tem 32 px de altura e cobre o bloco de cima, então a
última fileira de uma sala com parede embaixo vira VAZIO (menos em frente às portas). Móvel alto só encostado na parede
do fundo (a linha de fundo dele fica na linha da parede); no meio da sala, só móveis baixos.

  python central/escritorio/gerar_layout.py   ->  central/escritorio/layout-padrao.json
"""
import json
from pathlib import Path

COLS, ROWS = 19, 16
PAREDE, LISO, CIMENTO, TABUA, XADREZ, VAZIO = 0, 1, 4, 7, 9, 255
COR = {  # cores dos pisos (colorize do pixel-agents: h, s, b, c)
    "parede": {"h": 214, "s": 20, "b": -95, "c": -55},
    "gerente": {"h": 30, "s": 30, "b": -45, "c": -80},      # madeira
    "comercial": {"h": 35, "s": 25, "b": -35, "c": -85},    # madeira clara
    "social": {"h": 205, "s": 20, "b": -20, "c": -80},      # cinza azulado
    "vendas": {"h": 35, "s": 30, "b": -30, "c": -85},       # madeira clara
}
# sala: (rótulo, cor da área, piso, cor do piso, col0, col1, lin0, lin1)
SALAS = [
    ("Gerente", "#E0A81C", TABUA, "gerente", 1, 7, 2, 7),
    ("Comercial", "#D9533B", TABUA, "comercial", 1, 7, 9, 14),
    ("Produtor Social", "#EC70A0", LISO, "social", 9, 17, 2, 7),
    ("Vendas", "#5E92E6", TABUA, "vendas", 9, 17, 9, 14),
]
# portas: (col, lin, sala cujo piso a porta usa)
PORTAS = ([(8, r, "Gerente") for r in (3, 4)]                   # Gerente <-> Produtor Social
          + [(4, 8, "Gerente")]                                 # Gerente <-> Comercial
          + [(8, r, "Comercial") for r in (10, 11)]             # Comercial <-> Vendas
          + [(c, 8, "Produtor Social") for c in (13, 14)])      # Produtor Social <-> Vendas
NEUTRO = {"h": 210, "s": 20, "b": -30, "c": 0, "colorize": True}
CLARO = {"h": 40, "s": 30, "b": 15, "c": 0, "colorize": True}
# tapetes: (col0, col1, lin0, lin1, variante, cor, cor de destaque)
TAPETES = [(2, 6, 3, 5, 0, NEUTRO, CLARO), (12, 16, 10, 13, 2, NEUTRO, CLARO)]
LUGARES_FIXOS = {}

tiles = [VAZIO] * (COLS * ROWS)
cores = [None] * (COLS * ROWS)
areas = [None] * (COLS * ROWS)
tapetes = [None] * (COLS * ROWS)
moveis = []
SALA = {s[0]: s for s in SALAS}


def pos(c, r):
    return r * COLS + c


def movel(tipo, c, r):
    uid = f"f-padrao-{len(moveis) + 1:03d}"
    moveis.append({"uid": uid, "type": tipo, "col": c, "row": r})
    return uid


def estacao(c, r):
    """Mesa de frente com PC e banco (módulo do layout padrão): 3 colunas x 3 linhas."""
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


def montar():
    # paredes em volta de cada sala; depois os pisos por cima e as portas
    for nome, _, _, _, c0, c1, r0, r1 in SALAS:
        for c in range(c0 - 1, c1 + 2):
            for r in range(r0 - 1, r1 + 2):
                if r >= ROWS:
                    continue
                tiles[pos(c, r)] = PAREDE
                cores[pos(c, r)] = COR["parede"]
    for nome, _, piso, cor, c0, c1, r0, r1 in SALAS:
        for c in range(c0, c1 + 1):
            for r in range(r0, r1 + 1):
                tiles[pos(c, r)], cores[pos(c, r)], areas[pos(c, r)] = piso, COR[cor], nome
    for c, r, lado in PORTAS:
        _, _, piso, cor, *_ = SALA[lado]
        tiles[pos(c, r)], cores[pos(c, r)] = piso, COR[cor]
    # a fileira que a parede de baixo cobre (a parede tem 2 blocos de altura na tela) sai da sala
    for i in range(COLS * ROWS):
        c, r = i % COLS, i // COLS
        if areas[i] and r + 1 < ROWS and tiles[pos(c, r + 1)] == PAREDE:
            tiles[i], cores[i], areas[i] = VAZIO, None, None
    for c0, c1, r0, r1, variante, cor, destaque in TAPETES:
        for c in range(c0, c1 + 1):
            for r in range(r0, r1 + 1):
                if tiles[pos(c, r)] not in (PAREDE, VAZIO):
                    tapetes[pos(c, r)] = {"variant": variante, "color": cor, "accentColor": destaque}

    # Gerente: mesa executiva com a poltrona atrás, estante e vaso grande encostados na parede do fundo
    movel("VASO_GRANDE", 1, 0)
    movel("ESTANTE_ESCURA", 6, 0)
    LUGARES_FIXOS["Gerente"] = movel("POLTRONA_COURO_FRONT", 4, 1)
    movel("MESA_EXECUTIVA", 3, 3)
    movel("NOTEBOOK", 3, 3)
    movel("POLTRONA_COURO_BACK", 3, 4)
    movel("POLTRONA_COURO_BACK", 5, 4)
    movel("VASO_PEQUENO", 7, 6)

    # Comercial: 2 mesas na parede de cima (a porta do Gerente fica entre elas) e a 3ª embaixo
    estacao(1, 8)
    estacao(5, 8)
    estacao(1, 11)
    movel("VASO_PEQUENO", 7, 13)

    # Produtor Social: 4 mesas, a primeira fila colada na parede, com janela e painel de métricas acima
    for r in (1, 4):
        for c in (10, 14):
            estacao(c, r)
    movel("JANELA", 9, 0)
    movel("PAINEL_METRICAS", 13, 0)
    movel("VASO_PEQUENO", 17, 6)

    # Vendas: vaso grande e TV na parede do fundo, mesa de reunião do time no meio
    movel("VASO_GRANDE", 9, 7)
    movel("TV_PAREDE", 11, 7)
    mesa_reuniao(13, 10)
    movel("VASO_PEQUENO", 17, 13)

    return {
        "version": 1, "cols": COLS, "rows": ROWS, "tiles": tiles, "tileColors": cores,
        "furniture": moveis, "pets": [], "carpetTiles": tapetes,
        "areas": [{"label": n, "color": cor} for n, cor, *_ in SALAS],
        "areaTiles": areas, "lugaresFixos": LUGARES_FIXOS,
    }


if __name__ == "__main__":
    layout = montar()
    destino = Path(__file__).with_name("layout-padrao.json")
    destino.write_text(json.dumps(layout, ensure_ascii=False), encoding="utf-8")
    lugares = sum(1 for m in moveis if any(k in m["type"] for k in ("CHAIR", "BENCH", "SOFA", "ESPREGUICADEIRA", "POLTRONA", "PUFE")))
    print(f"{len(moveis)} móveis, {lugares} lugares -> {destino}")
