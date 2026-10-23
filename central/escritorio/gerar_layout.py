"""Gera o layout do escritório da Ciello no formato do pixel-agents (OfficeLayout v1), a partir do esboço do Mateus.

  +----------+---------+-----------+
  | Gerente ==Arquivos |  Produtor |
  |    ||    +---------+   Social  |
  |    ||    |  Copa   |           |
  +----||----+---||----+           |
  | Comercial == Lazer ==          |
  |          |         +----||-----+
  |          +---||----+  Vendas   |
  |          | Varanda |           |
  +----------+---------+-----------+

As portas são só estas (um caminho único, como o Mateus pediu):
  Arquivos G <-> Gerente <-> Comercial <-> Área de lazer <-> Copa
                                                    <-> Varanda
                                                    <-> Produtor Social <-> Vendas

Composição: cada sala tem um ponto focal (a mesa do Gerente de frente para a sala, com a logo atrás; o estoque e o
servidor; o balcão do café; os sofás; a mesa de reunião de Vendas; o set de gravação), um caminho livre de 1 quadrado
da porta até cada lugar, tapete marcando a zona de estar ou de reunião, plantas nos cantos e detalhes nas paredes
de fora (janelas, quadros). As salas têm o tamanho do que acontece nelas.

Móvel encostado na parede de cima: a parede limita a sala, mas o corpo do móvel cobre a face da parede, como na vida
real. No pixel-agents isso é a "linha de fundo" do móvel (backgroundTiles) em cima da linha da parede, com a base no
primeiro piso: a geladeira, a estante, a mesa e a planta ficam coladas na parede, não soltas no meio da sala.

  python central/escritorio/gerar_layout.py   ->  central/escritorio/layout-ciello.json
O número VERSAO sobe a cada layout novo: quem ainda usa um layout anterior da Ciello recebe este (com cópia do antigo).
"""
import json
from pathlib import Path

VERSAO = 4
COLS, ROWS = 28, 21
PAREDE, LISO, CIMENTO, TABUA, XADREZ, VAZIO = 0, 1, 4, 7, 9, 255
COR = {  # cores dos pisos (colorize do pixel-agents: h, s, b, c)
    "parede": {"h": 214, "s": 30, "b": -100, "c": -55},
    "gerente": {"h": 30, "s": 35, "b": -40, "c": -85},      # madeira escura
    "comercial": {"h": 25, "s": 48, "b": -43, "c": -88},    # madeira
    "social": {"h": 209, "s": 39, "b": -25, "c": -80},      # azul
    "vendas": {"h": 35, "s": 40, "b": -30, "c": -85},       # madeira clara
    "arquivos": {"h": 210, "s": 6, "b": -35, "c": -30},     # cimento
    "copa": {"h": 200, "s": 10, "b": -10, "c": -10},        # xadrez
    "lazer": {"h": 30, "s": 30, "b": -20, "c": -70},        # carpete bege
    "varanda": {"h": 28, "s": 55, "b": -38, "c": -60},      # deque
}
# sala: (rótulo, cor da área, piso, cor do piso, col0, col1, lin0, lin1)
SALAS = [
    ("Gerente", "#E0A81C", TABUA, "gerente", 1, 8, 2, 8),
    ("Comercial", "#D9533B", TABUA, "comercial", 1, 8, 10, 19),
    ("Arquivos G", "#8A94A3", CIMENTO, "arquivos", 10, 16, 2, 5),
    ("Copa", "#2FB7C4", XADREZ, "copa", 10, 16, 7, 9),
    ("Área de lazer", "#8E6BD8", LISO, "lazer", 10, 16, 11, 15),
    ("Varanda", "#3DBE6E", TABUA, "varanda", 10, 16, 17, 19),
    ("Produtor Social", "#EC70A0", LISO, "social", 18, 26, 2, 12),
    ("Vendas", "#5E92E6", TABUA, "vendas", 18, 26, 14, 19),
]
# portas: (col, lin, sala cujo piso a porta usa)
PORTAS = ([(9, r, "Gerente") for r in (4, 5)]                  # Gerente <-> Arquivos G
          + [(c, 9, "Gerente") for c in (4, 5)]                # Gerente <-> Comercial
          + [(9, r, "Comercial") for r in (13, 14)]            # Comercial <-> Área de lazer
          + [(c, 10, "Área de lazer") for c in (15, 16)]       # Área de lazer <-> Copa
          + [(c, 16, "Varanda") for c in (13, 14)]             # Área de lazer <-> Varanda
          + [(17, r, "Área de lazer") for r in (11, 12)]       # Área de lazer <-> Produtor Social
          + [(c, 13, "Produtor Social") for c in (22, 23)])    # Produtor Social <-> Vendas
# tapetes: (col0, col1, lin0, lin1, variante, cor, cor de destaque)
TAPETES = [
    (2, 6, 3, 7, 0, {"h": 352, "s": 55, "b": -35, "c": 0, "colorize": True}, {"h": 42, "s": 70, "b": 15, "c": 0, "colorize": True}),   # Gerente
    (11, 14, 11, 14, 1, {"h": 265, "s": 40, "b": -30, "c": 0, "colorize": True}, {"h": 34, "s": 60, "b": 20, "c": 0, "colorize": True}),  # lazer
    (20, 24, 15, 19, 2, {"h": 215, "s": 45, "b": -30, "c": 0, "colorize": True}, {"h": 200, "s": 40, "b": 25, "c": 0, "colorize": True}),  # Vendas
    (4, 7, 14, 17, 1, {"h": 20, "s": 45, "b": -35, "c": 0, "colorize": True}, {"h": 40, "s": 55, "b": 15, "c": 0, "colorize": True}),     # Comercial
    (25, 26, 2, 7, 0, {"h": 330, "s": 35, "b": -35, "c": 0, "colorize": True}, {"h": 330, "s": 30, "b": 25, "c": 0, "colorize": True}),   # set de gravação
]

tiles = [VAZIO] * (COLS * ROWS)
cores = [None] * (COLS * ROWS)
areas = [None] * (COLS * ROWS)
tapetes = [None] * (COLS * ROWS)
moveis = []
SALA = {s[0]: s for s in SALAS}


def pos(c, r):
    return r * COLS + c


def movel(tipo, c, r):
    moveis.append({"uid": f"f-ciello-{len(moveis) + 1:03d}", "type": tipo, "col": c, "row": r})


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
                if r >= ROWS - 1 or (nome == "Varanda" and r > r1):
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
    for c0, c1, r0, r1, variante, cor, destaque in TAPETES:
        for c in range(c0, c1 + 1):
            for r in range(r0, r1 + 1):
                tapetes[pos(c, r)] = {"variant": variante, "color": cor, "accentColor": destaque}

    # Linha da parede de cima de cada sala: é nela que fica a linha de fundo dos móveis encostados.
    # Gerente: a mesa dele de frente para a sala (ele senta atrás dela), a logo da Ciello na parede atrás,
    # duas poltronas de visita, estante, janela, luminária encostada e plantas nos cantos
    movel("DESK_FRONT", 3, 4)
    movel("CUSHIONED_CHAIR_FRONT", 4, 3)  # de frente para a sala: ele olha para quem entra
    movel("PC_SIDE", 3, 4)
    movel("COFFEE", 5, 4)
    movel("CUSHIONED_CHAIR_BACK", 3, 6)
    movel("CUSHIONED_CHAIR_BACK", 5, 6)
    movel("DOUBLE_BOOKSHELF", 1, 0)
    movel("QUADRO_CIELLO", 3, 0)
    movel("CLOCK", 5, 0)
    movel("JANELA", 6, 0)
    movel("LUMINARIA", 8, 1)
    movel("LARGE_PLANT", 1, 6)
    movel("PLANT_2", 8, 6)
    movel("BIN", 6, 4)

    # Arquivos G: estantes de estoque e o servidor colados na parede do fundo; na frente, arquivo de aço e caixas
    for c in (10, 12, 14):
        movel("ESTANTE_ARQUIVO", c, 1)
    movel("SERVIDOR", 16, 1)
    movel("ARQUIVO_ACO", 12, 3)
    for c in (14, 15, 16):
        movel("CAIXAS", c, 3)

    # Copa: balcão com café e pia, geladeira e bebedouro colados na parede; mesinha com café e cadeira no meio
    movel("BALCAO_CAFE", 10, 6)
    movel("GELADEIRA", 12, 6)
    movel("BEBEDOURO", 16, 6)
    movel("SMALL_TABLE_FRONT", 13, 8)
    movel("COFFEE", 13, 8)
    movel("WOODEN_CHAIR_SIDE", 12, 8)

    # Área de lazer: sofás em volta da mesa de centro (tapete embaixo), luminária no canto e fliperama
    movel("SOFA_FRONT", 12, 11)
    movel("SOFA_SIDE", 11, 12)
    movel("COFFEE_TABLE", 12, 12)
    movel("SOFA_SIDE:left", 14, 12)
    movel("SOFA_BACK", 12, 14)
    movel("COFFEE", 12, 13)
    movel("LUMINARIA", 10, 10)
    movel("ARCADE", 16, 13)

    # Varanda: guarda-corpo, espreguiçadeiras nas pontas, vasos e um banco
    for c in range(10, 17):
        movel("GUARDA_CORPO", c, 19)
    movel("ESPREGUICADEIRA", 10, 17)
    movel("ESPREGUICADEIRA", 16, 17)
    movel("POT", 11, 18)
    movel("WOODEN_BENCH", 12, 18)
    movel("POT", 15, 18)

    # Produtor Social: 6 mesas (a primeira fila colada na parede) e o set de gravação no canto:
    # ring light na parede, cadeira de quem grava e a câmera no tripé de frente para ela
    for r in (1, 4, 7):
        for c in (18, 22):
            estacao(c, r)
    movel("JANELA", 19, 0)
    movel("WHITEBOARD", 22, 0)
    movel("SMALL_PAINTING", 24, 0)
    movel("RING_LIGHT", 25, 1)
    movel("CUSHIONED_CHAIR_FRONT", 25, 3)
    movel("TRIPE_CAMERA", 25, 5)
    movel("HANGING_PLANT", 26, 0)
    movel("LARGE_PLANT", 25, 9)
    movel("BIN", 21, 11)

    # Comercial: 2 mesas coladas na parede de cima (a porta do Gerente fica entre elas), a 3ª embaixo,
    # arquivo de aço e uma mesinha de atendimento sobre tapete
    estacao(1, 9)
    estacao(6, 9)
    estacao(1, 13)
    movel("SMALL_TABLE_FRONT", 5, 14)
    movel("WOODEN_CHAIR_SIDE", 4, 14)
    movel("WOODEN_CHAIR_SIDE:left", 7, 14)
    movel("ARQUIVO_ACO", 8, 16)
    movel("PLANT_2", 1, 18)
    movel("PLANT_2", 8, 18)

    # Vendas: a mesa de reunião do time (SDR, closer, sucesso do cliente) e o cavalete com a meta, encostado
    mesa_reuniao(21, 15)
    movel("CAVALETE_METAS", 19, 13)
    movel("LARGE_PLANT", 25, 17)
    movel("PLANT_2", 18, 18)

    return {
        "version": 1, "cols": COLS, "rows": ROWS, "tiles": tiles, "tileColors": cores,
        "furniture": moveis, "pets": [], "carpetTiles": tapetes,
        "areas": [{"label": n, "color": cor} for n, cor, *_ in SALAS],
        "areaTiles": areas, "cielloLayout": VERSAO,
    }


if __name__ == "__main__":
    layout = montar()
    destino = Path(__file__).with_name("layout-ciello.json")
    destino.write_text(json.dumps(layout, ensure_ascii=False), encoding="utf-8")
    lugares = sum(1 for m in moveis if any(k in m["type"] for k in ("CHAIR", "BENCH", "SOFA", "ESPREGUICADEIRA")))
    print(f"{len(moveis)} móveis, {lugares} lugares -> {destino}")
