"""Gera o layout do escritório da Ciello no formato do pixel-agents (OfficeLayout v1), a partir do esboço do Mateus:

  +-----------+---------+-----------+
  |  Gerente  |Arquivos |  Produtor |
  |           +---------+   Social  |
  |           |  Copa   |           |
  +-----------+---------+-----------+
  | Comercial | Área de |  Vendas   |
  |           |  lazer  |           |
  |           +---------+           |
  |           | Varanda |           |
  +-----------+---------+-----------+

  Gerente          a sala principal: é com ele que você fala; ele monta a esteira e delega
  Arquivos G       o armazenamento local (vídeos, métricas, o banco): estoque de caixas e o servidor
  Copa             máquina de café, pia e geladeira
  Área de lazer    sofás: onde os agentes parados conversam e tomam café
  Varanda          espreguiçadeiras e plantas: onde eles vão pensar na vida
  Produtor Social  a equipe da rede social (pesquisa, roteiro, vídeo, imagem, postagem, análise)
  Comercial        financeiro, anúncios, agenda e e-mail
  Vendas           SDR, closer e sucesso do cliente

  python central/escritorio/gerar_layout.py   ->  central/escritorio/layout-ciello.json
O número VERSAO sobe a cada layout novo: quem ainda usa o layout antigo da Ciello recebe o novo (com cópia do antigo).
"""
import json
from pathlib import Path

VERSAO = 2
COLS, ROWS = 33, 25
PAREDE, LISO, PISO_GRANDE, CIMENTO, TABUA, XADREZ, VAZIO = 0, 1, 2, 4, 7, 9, 255
COR = {  # (tipo de piso, cor) -> h, s, b, c do colorize do pixel-agents
    "parede": {"h": 214, "s": 30, "b": -100, "c": -55},
    "gerente": {"h": 352, "s": 40, "b": -45, "c": -80},     # carpete vinho
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
    ("Gerente", "#E0A81C", LISO, "gerente", 1, 11, 2, 9),
    ("Comercial", "#D9533B", TABUA, "comercial", 1, 11, 11, 23),
    ("Arquivos G", "#8A94A3", CIMENTO, "arquivos", 13, 19, 2, 6),
    ("Copa", "#2FB7C4", XADREZ, "copa", 13, 19, 8, 11),
    ("Área de lazer", "#8E6BD8", LISO, "lazer", 13, 19, 13, 19),
    ("Varanda", "#3DBE6E", TABUA, "varanda", 13, 19, 21, 23),
    ("Produtor Social", "#EC70A0", LISO, "social", 21, 31, 2, 13),
    ("Vendas", "#5E92E6", TABUA, "vendas", 21, 31, 15, 23),
]
# portas: (col, lin) que deixam de ser parede; o piso é o da sala do lado indicado
PORTAS = ([(12, r, "Gerente") for r in (4, 5, 8, 9)] + [(12, r, "Comercial") for r in (16, 17)]
          + [(20, r, "Produtor Social") for r in (4, 5, 9, 10)] + [(20, r, "Vendas") for r in (16, 17)]
          + [(c, 10, "Gerente") for c in (5, 6)] + [(c, 14, "Produtor Social") for c in (25, 26)]
          + [(c, 7, "Copa") for c in (14, 15)] + [(c, 12, "Área de lazer") for c in (15, 16, 17)]
          + [(c, 20, "Varanda") for c in (15, 16, 17)])

tiles = [VAZIO] * (COLS * ROWS)
cores = [None] * (COLS * ROWS)
areas = [None] * (COLS * ROWS)
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
    # paredes: contorno de cada sala; depois os pisos por cima e as portas
    for nome, _, _, _, c0, c1, r0, r1 in SALAS:
        for c in range(c0 - 1, c1 + 2):
            for r in range(r0 - 1, r1 + 2):
                if nome == "Varanda" and r > r1:
                    continue  # a varanda é aberta embaixo
                if r == ROWS - 1:
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

    # Gerente: a mesa dele no meio, quadro e quadro de avisos na parede, poltronas para quem vem falar com ele
    estacao(5, 4)
    movel("WHITEBOARD", 2, 0)
    movel("LARGE_PAINTING", 8, 0)
    movel("CLOCK", 6, 0)
    movel("LARGE_PLANT", 1, 7)
    movel("PLANT_2", 11, 2)
    movel("SOFA_FRONT", 8, 8)
    movel("CUSHIONED_CHAIR_FRONT", 4, 8)
    movel("BIN", 9, 4)

    # Arquivos G: estoque de caixas e o servidor (o cérebro: tudo o que é processado fica aqui)
    for c in (13, 15, 17):
        movel("ESTANTE_ARQUIVO", c, 2)
    movel("SERVIDOR", 19, 2)
    for c in (16, 17, 18):
        movel("CAIXAS", c, 5)

    # Copa: balcão com café e pia, geladeira, lixo e uma planta
    movel("BALCAO_CAFE", 16, 8)
    movel("GELADEIRA", 18, 8)
    movel("BIN", 13, 11)
    movel("POT", 19, 11)

    # Área de lazer: sofás em volta da mesa de centro
    sofas(15, 15)
    movel("LARGE_PLANT", 18, 17)
    movel("PLANT", 13, 13)
    movel("CACTUS", 19, 13)

    # Varanda: guarda-corpo embaixo, espreguiçadeiras e plantas
    for c in range(13, 20):
        movel("GUARDA_CORPO", c, 23)
    movel("ESPREGUICADEIRA", 13, 21)
    movel("ESPREGUICADEIRA", 19, 21)
    movel("POT", 14, 22)
    movel("POT", 18, 22)
    movel("WOODEN_BENCH", 16, 22)

    # Produtor Social: 6 estações (pesquisa, roteiro, vídeo, imagem, postagem, análise)
    for r in (3, 7, 11):
        for c in (22, 27):
            estacao(c, r)
    movel("WHITEBOARD", 25, 0)
    movel("HANGING_PLANT", 31, 0)
    movel("SMALL_PAINTING", 22, 0)

    # Comercial: 4 estações (financeiro, anúncios, agenda e e-mail, chefe de gabinete)
    for r in (12, 17):
        for c in (2, 7):
            estacao(c, r)
    movel("PLANT_2", 1, 21)
    movel("LARGE_PLANT", 9, 21)
    movel("BIN", 11, 12)

    # Vendas: mesa do time de vendas e um canto de demonstração
    mesa_reuniao(25, 16)
    movel("SOFA_FRONT", 22, 21)
    movel("CUSHIONED_CHAIR_FRONT", 21, 21)
    movel("LARGE_PLANT", 30, 21)
    movel("PLANT_2", 31, 15)

    return {
        "version": 1, "cols": COLS, "rows": ROWS, "tiles": tiles, "tileColors": cores,
        "furniture": moveis, "pets": [],
        "areas": [{"label": n, "color": cor} for n, cor, *_ in SALAS],
        "areaTiles": areas, "cielloLayout": VERSAO,
    }


if __name__ == "__main__":
    layout = montar()
    destino = Path(__file__).with_name("layout-ciello.json")
    destino.write_text(json.dumps(layout, ensure_ascii=False), encoding="utf-8")
    lugares = sum(1 for m in moveis if any(k in m["type"] for k in ("CHAIR", "BENCH", "SOFA", "ESPREGUICADEIRA")))
    print(f"{len(moveis)} móveis, {lugares} lugares -> {destino}")
