"""Ativos do escritório: lê a pasta assets/ do build da tela e monta as mensagens que ela espera.

Mesma ordem e mesmo formato do carregador original (personagens char_0..5, pets por pasta em ordem alfabética,
pisos floor_N, paredes wall_N, tapetes carpet_N, móveis pelos manifest.json e o default-layout-N mais novo).
"""
import json
import re
from pathlib import Path

from . import png

# medidas dos sprites (iguais às da tela)
PAREDE_W, PAREDE_H, PAREDE_COLS, PAREDE_PECAS = 16, 32, 4, 16
PISO = 16
DIRECOES = ("down", "up", "right")
PERS_W, PERS_H, PERS_QUADROS, PERS_QTD = 16, 32, 7, 6
PET_W, PET_W_LARGO, PET_H, PET_IMG = 16, 32, 32, 96
PET_ANDA, PET_PARADO, PET_ANDA_LADO = 3, 3, 3
PET_MAX_BYTES = 512 * 1024
TAPETE, TAPETE_COLS, TAPETE_CASOS = 16, 4, 16
CHAVE_REVISAO = "layoutRevision"


def _sprite(dados, w, h):
    """Um PNG inteiro como sprite w×h; se não bater, sai vazio (como o original)."""
    try:
        img = png.ler(dados)
        if img.largura < w or img.altura < h:
            raise ValueError("menor que o esperado")
        return img.recorte(0, 0, w, h)
    except (ValueError, IndexError, TypeError):
        return [[""] * w for _ in range(h)]


def _pecas(img, lado_w, lado_h, cols, qtd):
    return [img.recorte((n % cols) * lado_w, (n // cols) * lado_h, lado_w, lado_h) for n in range(qtd)]


def personagem(dados):
    img = png.ler(dados)
    return {d: [img.recorte(f * PERS_W, i * PERS_H, PERS_W, PERS_H) for f in range(PERS_QUADROS)]
            for i, d in enumerate(DIRECOES)}


def pet(dados):
    try:
        img = png.ler(dados)
        if img.largura != PET_IMG or img.altura != PET_IMG:
            raise ValueError("pet com tamanho errado")
        linha = lambda y, ini, n, w: [img.recorte((ini + f) * w, y, w, PET_H) for f in range(n)]
        return {"walkDown": linha(0, 0, PET_ANDA, PET_W), "idleDown": linha(0, PET_ANDA, PET_PARADO, PET_W),
                "walkUp": linha(PET_H, 0, PET_ANDA, PET_W), "idleUp": linha(PET_H, PET_ANDA, PET_PARADO, PET_W),
                "walkRight": linha(PET_H * 2, 0, PET_ANDA_LADO, PET_W_LARGO)}
    except ValueError:
        vazio = lambda w: [[""] * w for _ in range(PET_H)]
        return {k: [vazio(PET_W) for _ in range(3)] for k in ("walkDown", "idleDown", "walkUp", "idleUp")} | \
               {"walkRight": [vazio(PET_W_LARGO) for _ in range(3)]}


def _numerados(pasta: Path, prefixo):
    if not pasta.is_dir():
        return []
    achados = []
    for f in pasta.iterdir():
        m = re.fullmatch(rf"{prefixo}_(\d+)\.png", f.name, re.I)
        if m:
            achados.append((int(m.group(1)), f))
    return [f for _, f in sorted(achados)]


def achatar(no, herdado):
    """Achata a árvore do manifest de um móvel (rotação, estado, animação) em itens do catálogo."""
    if no.get("type") == "asset":
        orient = no.get("orientation") or herdado.get("orientation")
        estado = no.get("state") or herdado.get("state")
        item = {"id": no["id"], "name": herdado["name"], "label": herdado["name"], "category": herdado["category"],
                "file": no["file"], "width": no["width"], "height": no["height"], "footprintW": no["footprintW"],
                "footprintH": no["footprintH"], "isDesk": herdado["category"] == "desks",
                "canPlaceOnWalls": herdado["canPlaceOnWalls"], "canPlaceOnSurfaces": herdado["canPlaceOnSurfaces"],
                "backgroundTiles": herdado["backgroundTiles"], "groupId": herdado["groupId"]}
        if orient:
            item["orientation"] = orient
        if estado:
            item["state"] = estado
        if no.get("mirrorSide"):
            item["mirrorSide"] = True
        if herdado.get("rotationScheme"):
            item["rotationScheme"] = herdado["rotationScheme"]
        if herdado.get("animationGroup"):
            item["animationGroup"] = herdado["animationGroup"]
        if no.get("frame") is not None:
            item["frame"] = no["frame"]
        return [item]
    itens = []
    for membro in no.get("members", []):
        filho = dict(herdado)
        tipo = no.get("groupType")
        if tipo == "rotation" and no.get("rotationScheme"):
            filho["rotationScheme"] = no["rotationScheme"]
        if tipo == "state":
            if no.get("orientation"):
                filho["orientation"] = no["orientation"]
            if no.get("state"):
                filho["state"] = no["state"]
        if tipo == "animation":
            orient = no.get("orientation") or herdado.get("orientation") or ""
            est = no.get("state") or herdado.get("state") or ""
            filho["animationGroup"] = f"{herdado['groupId']}_{orient}_{est}".upper()
            if no.get("state"):
                filho["state"] = no["state"]
        if no.get("orientation") and not filho.get("orientation"):
            filho["orientation"] = no["orientation"]
        itens += achatar(membro, filho)
    return itens


def moveis(pasta: Path):
    catalogo, sprites = [], {}
    if not pasta.is_dir():
        return None
    for item_dir in sorted(p for p in pasta.iterdir() if p.is_dir()):
        manifesto = item_dir / "manifest.json"
        if not manifesto.exists():
            continue
        try:
            m = json.loads(manifesto.read_text(encoding="utf-8"))
            herdado = {"groupId": m["id"], "name": m["name"], "category": m["category"],
                       "canPlaceOnWalls": m.get("canPlaceOnWalls"), "canPlaceOnSurfaces": m.get("canPlaceOnSurfaces"),
                       "backgroundTiles": m.get("backgroundTiles")}
            if m.get("type") == "asset":
                itens = [{"id": m["id"], "name": m["name"], "label": m["name"], "category": m["category"],
                          "file": m.get("file") or f"{m['id']}.png", "width": m.get("width"), "height": m.get("height"),
                          "footprintW": m.get("footprintW"), "footprintH": m.get("footprintH"),
                          "isDesk": m["category"] == "desks", "canPlaceOnWalls": m.get("canPlaceOnWalls"),
                          "canPlaceOnSurfaces": m.get("canPlaceOnSurfaces"), "backgroundTiles": m.get("backgroundTiles"),
                          "groupId": m["id"]}]
            else:
                if m.get("rotationScheme"):
                    herdado["rotationScheme"] = m["rotationScheme"]
                itens = achatar({"type": "group", "groupType": m.get("groupType"), "rotationScheme": m.get("rotationScheme"),
                                 "members": m.get("members") or []}, herdado)
        except (OSError, ValueError, KeyError, TypeError):
            continue
        for it in itens:
            arq = (item_dir / it["file"]).resolve()
            if not arq.is_relative_to(item_dir.resolve()):
                continue
            if arq.is_file():
                sprites[it["id"]] = _sprite(arq.read_bytes(), it["width"], it["height"])
        catalogo += itens
    return {"catalog": catalogo, "sprites": sprites}


def layout_padrao(pasta: Path):
    melhor, rev = None, 0
    for f in pasta.glob("default-layout-*.json") if pasta.is_dir() else []:
        m = re.fullmatch(r"default-layout-(\d+)\.json", f.name)
        if m and int(m.group(1)) > rev:
            melhor, rev = f, int(m.group(1))
    if not melhor and (pasta / "default-layout.json").exists():
        melhor = pasta / "default-layout.json"
    if not melhor:
        return None
    layout = json.loads(melhor.read_text(encoding="utf-8"))
    if rev > 0 and not layout.get(CHAVE_REVISAO):
        layout[CHAVE_REVISAO] = rev
    return layout


class Ativos:
    """Lê tudo uma vez e guarda pronto para mandar a cada tela que conecta."""

    def __init__(self, raiz: Path):
        a = raiz / "assets"
        self.personagens = None
        arquivos = [a / "characters" / f"char_{i}.png" for i in range(PERS_QTD)]
        if all(f.exists() for f in arquivos):
            self.personagens = [personagem(f.read_bytes()) for f in arquivos]
        self.pets, self.nomes_pets = [], []
        pets_dir = a / "pets"
        for d in sorted(p for p in pets_dir.iterdir() if p.is_dir()) if pets_dir.is_dir() else []:
            man, img = d / "manifest.json", d / "pet.png"
            if not (man.exists() and img.exists()) or img.stat().st_size > PET_MAX_BYTES:
                continue
            try:
                dados = json.loads(man.read_text(encoding="utf-8"))
            except ValueError:
                continue
            if dados.get("id") and dados.get("name"):
                self.pets.append(pet(img.read_bytes()))
                self.nomes_pets.append(dados["name"])
        self.pisos = [_sprite(f.read_bytes(), PISO, PISO) for f in _numerados(a / "floors", "floor")] or None
        self.paredes = [_pecas(png.ler(f.read_bytes()), PAREDE_W, PAREDE_H, PAREDE_COLS, PAREDE_PECAS)
                        for f in _numerados(a / "walls", "wall")] or None
        self.tapetes = [_pecas(png.ler(f.read_bytes()), TAPETE, TAPETE, TAPETE_COLS, TAPETE_CASOS)
                        for f in _numerados(a / "carpets", "carpet")] or None
        self.moveis = moveis(a / "furniture")
        self.layout_padrao = layout_padrao(a)

    @property
    def qtd_paletas(self):
        return len(self.personagens) if self.personagens else PERS_QTD

    def mensagens(self):
        """As mensagens de ativos, na ordem em que a tela original as recebe."""
        msgs = []
        if self.personagens:
            msgs.append({"type": "characterSpritesLoaded", "characters": self.personagens})
        if self.pets:
            msgs.append({"type": "petSpritesLoaded", "pets": self.pets, "petNames": self.nomes_pets})
        if self.pisos:
            msgs.append({"type": "floorTilesLoaded", "sprites": self.pisos})
        if self.paredes:
            msgs.append({"type": "wallTilesLoaded", "sets": self.paredes})
        if self.tapetes:
            msgs.append({"type": "carpetTilesLoaded", "sets": self.tapetes})
        if self.moveis:
            msgs.append({"type": "furnitureAssetsLoaded", "catalog": self.moveis["catalog"], "sprites": self.moveis["sprites"]})
        return msgs
