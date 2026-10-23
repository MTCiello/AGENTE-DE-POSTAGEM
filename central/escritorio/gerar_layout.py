"""Gera o layout do escritório da Ciello no formato do pixel-agents (OfficeLayout v1), a partir do esboço do Mateus.

  +---------+---------+-----------+
  | Gerente ==Arquivos |  Produtor |
  +----||---+---------+   Social  |
  |Comercial|  Copa   ==          |
  |         == Lazer  +----||-----+
  +---------+---||----+  Vendas   |
  |      Varanda      |           |
  +~~~~~~~~~~~~~~~~~~~+-----------+

As portas são só estas (um caminho único, como o Mateus pediu):
  Arquivos G <-> Gerente <-> Comercial <-> Área de lazer + Copa (um ambiente só, sem parede entre elas)
                                                    <-> Varanda (larga, embaixo do Comercial e da Área de lazer)
                                                    <-> Produtor Social <-> Vendas

Blocos: o escritório é uma grade de blocos de 16 px. Um bloco de parede ocupa um bloco; um vaso pequeno, 1; um vaso
grande, 2; a mesa de um funcionário, 3 (os móveis ocupam no chão footprintW x (footprintH - linhas de fundo)).

Perspectiva (vista de cima em 3/4):
  - A parede tem 32 px de altura: ela cobre o bloco de cima. Por isso a última fileira de uma sala com parede
    embaixo fica escondida atrás da parede: aqui ela vira VAZIO (ninguém anda nem põe móvel onde não se vê), menos
    em frente às portas. Assim cada sala mostra exatamente os blocos que tem.
  - Móvel alto (geladeira, estante, planta, servidor) só fica encostado na parede do fundo: a linha de fundo dele
    fica na linha da parede e o corpo cobre a face da parede, como na vida real. Solto no meio da sala ou numa
    parede do lado, um móvel alto de frente parece boiar.
  - No meio da sala e nas paredes do lado e da frente ficam só móveis baixos (tapete, pufe, mesinha, vaso pequeno,
    sofá, palete) ou de lado (poltrona de perfil). Exceções de propósito: mesas, cadeiras, o tripé da câmera e o
    guarda-sol da varanda, que na vida real ficam soltos.

  python central/escritorio/gerar_layout.py   ->  central/escritorio/layout-ciello.json
O número VERSAO sobe a cada layout novo: quem ainda usa um layout anterior da Ciello recebe este (com cópia do antigo).
"""
import json
from pathlib import Path

VERSAO = 6
COLS, ROWS = 27, 20
PAREDE, LISO, CIMENTO, TABUA, XADREZ, VAZIO = 0, 1, 4, 7, 9, 255
COR = {  # cores dos pisos (colorize do pixel-agents: h, s, b, c)
    "parede": {"h": 214, "s": 30, "b": -100, "c": -55},
    "gerente": {"h": 22, "s": 40, "b": -55, "c": -80},      # tábua de madeira escura
    "comercial": {"h": 25, "s": 48, "b": -43, "c": -88},    # madeira
    "social": {"h": 209, "s": 39, "b": -25, "c": -80},      # azul
    "vendas": {"h": 35, "s": 40, "b": -30, "c": -85},       # madeira clara
    "arquivos": {"h": 210, "s": 6, "b": -35, "c": -30},     # cimento
    "copa": {"h": 200, "s": 10, "b": -10, "c": -10},        # xadrez
    "lazer": {"h": 30, "s": 30, "b": -20, "c": -70},        # carpete bege
    "varanda": {"h": 28, "s": 55, "b": -38, "c": -60},      # deque
}
# sala: (rótulo, cor da área, piso, cor do piso, col0, col1, lin0, lin1). A última fileira de uma sala com parede
# embaixo fica atrás da parede (vira VAZIO em montar()), então o Gerente mostra 7x5 blocos e o Comercial também.
SALAS = [
    ("Gerente", "#E0A81C", TABUA, "gerente", 1, 7, 2, 7),
    ("Comercial", "#D9533B", TABUA, "comercial", 1, 7, 9, 14),
    ("Arquivos G", "#8A94A3", CIMENTO, "arquivos", 9, 15, 2, 5),
    ("Copa", "#2FB7C4", XADREZ, "copa", 9, 15, 7, 9),           # Copa e Área de lazer: um ambiente só (sem parede)
    ("Área de lazer", "#8E6BD8", LISO, "lazer", 9, 15, 10, 14),
    ("Varanda", "#3DBE6E", TABUA, "varanda", 1, 15, 16, 19),    # larga, embaixo do Comercial e da Área de lazer
    ("Produtor Social", "#EC70A0", LISO, "social", 17, 25, 2, 12),
    ("Vendas", "#5E92E6", TABUA, "vendas", 17, 25, 14, 19),
]
# portas: (col, lin, sala cujo piso a porta usa)
PORTAS = ([(8, r, "Gerente") for r in (3, 4)]                   # Gerente <-> Arquivos G
          + [(4, 8, "Gerente")]                                 # Gerente <-> Comercial
          + [(8, r, "Comercial") for r in (10, 11)]             # Comercial <-> Área de lazer
          + [(c, 15, "Varanda") for c in (9, 10)]               # Área de lazer <-> Varanda
          + [(16, r, "Área de lazer") for r in (10, 11)]         # Área de lazer <-> Produtor Social
          + [(c, 13, "Produtor Social") for c in (21, 22)])     # Produtor Social <-> Vendas
CIELLO = {"h": 216, "s": 85, "b": -15, "c": 10, "colorize": True}         # azul Ciello (#263A59 clareado para o tapete)
OURO = {"h": 42, "s": 75, "b": 10, "c": 0, "colorize": True}
# tapetes: (col0, col1, lin0, lin1, variante, cor, cor de destaque)
TAPETES = [
    (2, 6, 2, 6, 0, CIELLO, OURO),                                                                                       # Gerente
    (10, 15, 10, 13, 1, {"h": 265, "s": 40, "b": -30, "c": 0, "colorize": True}, {"h": 34, "s": 60, "b": 20, "c": 0, "colorize": True}),  # lazer
    (19, 25, 15, 19, 2, {"h": 215, "s": 45, "b": -30, "c": 0, "colorize": True}, {"h": 200, "s": 40, "b": 25, "c": 0, "colorize": True}),  # Vendas
    (5, 7, 11, 13, 1, {"h": 18, "s": 70, "b": -30, "c": 0, "colorize": True}, {"h": 40, "s": 55, "b": 15, "c": 0, "colorize": True}),     # Comercial
    (25, 25, 2, 7, 0, {"h": 330, "s": 35, "b": -35, "c": 0, "colorize": True}, {"h": 330, "s": 30, "b": 25, "c": 0, "colorize": True}),   # set de gravação
    (2, 7, 16, 18, 2, {"h": 190, "s": 45, "b": -25, "c": 0, "colorize": True}, {"h": 40, "s": 50, "b": 20, "c": 0, "colorize": True}),    # varanda
]
# lugares que já nascem com dono: a poltrona atrás da mesa de mogno é do Gerente (as outras são de visita)
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
    uid = f"f-ciello-{len(moveis) + 1:03d}"
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


def sofas(c, r):
    """Mesa de centro com sofás em volta e um café (módulo do layout padrão)."""
    movel("COFFEE_TABLE", c, r)
    movel("SOFA_FRONT", c, r - 1)
    movel("SOFA_SIDE", c - 1, r)
    movel("SOFA_SIDE:left", c + 2, r)
    movel("SOFA_BACK", c, r + 2)
    movel("COFFEE", c, r + 1)


def montar():
    # paredes em volta de cada sala; depois os pisos por cima e as portas
    for nome, _, _, _, c0, c1, r0, r1 in SALAS:
        for c in range(c0 - 1, c1 + 2):
            for r in range(r0 - 1, r1 + 2):
                if r >= ROWS or (nome == "Varanda" and r > r1):
                    continue  # embaixo o prédio acaba; a varanda é aberta
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

    # Linha 1 é a parede do fundo do Gerente, dos Arquivos e do Produtor Social: a linha de fundo dos móveis encostados
    # fica nela. Gerente (premium): mesa de mogno de frente para a sala com a poltrona de couro dele atrás, o painel
    # da Ciello na parede, vaso grande e estante de mogno nos cantos do fundo, tapete azul Ciello com borda dourada,
    # duas poltronas de visita, e no canto uma poltrona de perfil com a mesinha
    movel("VASO_GRANDE", 1, 0)
    movel("PAINEL_CIELLO", 3, 0)
    movel("ESTANTE_ESCURA", 6, 0)
    LUGARES_FIXOS["Gerente"] = movel("POLTRONA_COURO_FRONT", 4, 1)
    movel("MESA_EXECUTIVA", 3, 3)
    movel("NOTEBOOK", 3, 3)
    movel("GLOBO", 5, 3)
    movel("POLTRONA_COURO_BACK", 3, 4)
    movel("POLTRONA_COURO_BACK", 5, 4)
    movel("POLTRONA_COURO_SIDE", 1, 3)
    movel("MESA_LATERAL", 1, 5)
    movel("VASO_PEQUENO", 7, 6)

    # Arquivos G: estantes de estoque, os servidores e o arquivo de aço colados na parede do fundo; no meio, só
    # paletes baixos com caixas (o que é alto e solto no meio parecia boiar)
    movel("ESTANTE_ARQUIVO", 9, 1)
    movel("ESTANTE_ARQUIVO", 11, 1)
    movel("SERVIDOR", 13, 1)
    movel("SERVIDOR", 14, 1)
    movel("ARQUIVO_ACO", 15, 1)
    movel("PALETE_CAIXAS", 11, 4)
    movel("PALETE_CAIXAS", 13, 4)

    # Copa e Área de lazer, um ambiente só: a cozinha e o fliperama encostados na parede do fundo (piso xadrez), a
    # mesinha de café no meio e, no carpete, os sofás em volta da mesa de centro, com um pufe e um vaso no canto
    movel("BALCAO_CAFE", 9, 6)
    movel("GELADEIRA", 11, 6)
    movel("MAQUINA_SALGADINHOS", 12, 6)
    movel("BEBEDOURO", 13, 6)
    movel("ARCADE", 14, 6)
    movel("PLANT_2", 15, 6)
    movel("SMALL_TABLE_FRONT", 12, 8)
    movel("COFFEE", 12, 8)
    movel("WOODEN_CHAIR_SIDE", 11, 8)
    movel("WOODEN_CHAIR_SIDE:left", 14, 8)
    movel("SOFA_FRONT", 12, 10)
    movel("SOFA_SIDE", 11, 11)
    movel("COFFEE_TABLE", 12, 11)
    movel("SOFA_SIDE:left", 14, 11)
    movel("SOFA_BACK", 12, 13)
    movel("COFFEE", 12, 12)
    movel("PUFE", 10, 12)
    movel("VASO_PEQUENO", 15, 13)

    # Comercial: 2 mesas coladas na parede de cima (a porta do Gerente fica entre elas), a 3ª embaixo e um canto de
    # conversa baixo (mesinha e pufes) sobre tapete, perto da porta da Área de lazer
    estacao(1, 8)
    estacao(5, 8)
    estacao(1, 11)
    movel("MESA_LATERAL", 6, 12)
    movel("PUFE", 5, 12)
    movel("PUFE", 7, 12)
    movel("VASO_PEQUENO", 7, 13)

    # Produtor Social: 6 mesas (a primeira fila colada na parede, com janela e painel de métricas acima) e o set de
    # gravação no canto: ring light na parede, cadeira de quem grava e a câmera no tripé de frente para ela
    for r in (1, 4, 7):
        for c in (18, 22):
            estacao(c, r)
    movel("JANELA", 17, 0)
    movel("PAINEL_METRICAS", 20, 0)
    movel("SMALL_PAINTING", 24, 0)
    movel("RING_LIGHT", 25, 1)
    movel("CUSHIONED_CHAIR_FRONT", 25, 3)
    movel("TRIPE_CAMERA", 25, 5)
    movel("BIN", 17, 2)
    movel("PUFE", 24, 11)
    movel("VASO_PEQUENO", 25, 11)

    # Vendas: na parede do fundo, vaso grande, a TV, o aparador com o troféu e o cavalete da meta; no meio, a mesa de
    # reunião do time (SDR, closer, sucesso do cliente) sobre tapete
    movel("VASO_GRANDE", 17, 12)
    movel("TV_PAREDE", 19, 12)
    movel("APARADOR", 23, 13)
    movel("TROFEU", 23, 13)
    movel("TROFEU", 24, 13)
    movel("CAVALETE_METAS", 25, 13)
    mesa_reuniao(21, 16)
    movel("VASO_PEQUENO", 17, 19)
    movel("VASO_PEQUENO", 25, 19)

    # Varanda: janelas e plantas na parede do prédio, espreguiçadeiras com mesinha, a mesa com guarda-sol, bancos
    # olhando a vista e o guarda-corpo na beirada
    movel("PLANT_2", 1, 15)
    movel("JANELA", 2, 14)
    movel("JANELA", 5, 14)
    movel("JANELA", 12, 14)
    movel("VASO_GRANDE", 14, 14)
    movel("ESPREGUICADEIRA", 2, 16)
    movel("MESA_LATERAL", 3, 16)
    movel("ESPREGUICADEIRA", 4, 16)
    movel("GUARDA_SOL_MESA", 6, 16)
    movel("WOODEN_CHAIR_SIDE", 5, 17)
    movel("WOODEN_CHAIR_SIDE:left", 8, 17)
    movel("WOODEN_BENCH", 12, 17)
    movel("WOODEN_BENCH", 13, 17)
    movel("VASO_PEQUENO", 15, 18)
    for c in range(1, 16):
        movel("GUARDA_CORPO", c, 19)

    return {
        "version": 1, "cols": COLS, "rows": ROWS, "tiles": tiles, "tileColors": cores,
        "furniture": moveis, "pets": [], "carpetTiles": tapetes,
        "areas": [{"label": n, "color": cor} for n, cor, *_ in SALAS],
        "areaTiles": areas, "cielloLayout": VERSAO, "lugaresFixos": LUGARES_FIXOS,
    }


if __name__ == "__main__":
    layout = montar()
    destino = Path(__file__).with_name("layout-ciello.json")
    destino.write_text(json.dumps(layout, ensure_ascii=False), encoding="utf-8")
    lugares = sum(1 for m in moveis if any(k in m["type"] for k in ("CHAIR", "BENCH", "SOFA", "ESPREGUICADEIRA", "POLTRONA", "PUFE")))
    print(f"{len(moveis)} móveis, {lugares} lugares -> {destino}")
