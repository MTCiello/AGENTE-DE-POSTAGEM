"""PNG para sprite: cada pixel vira "#RRGGBB" (ou "#RRGGBBAA"), transparente vira "".

Decodificador mínimo (zlib da biblioteca padrão) para os formatos dos ativos: 8 bits por canal, sem
entrelaçamento, cores RGBA, RGB, paleta (com tRNS), cinza e cinza com alfa. O resultado é o mesmo do pngjs
que a tela original usava, então os sprites saem pixel a pixel iguais.
"""
import struct
import zlib

LIMIAR_ALFA = 2  # abaixo disso o pixel é transparente
CANAIS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


class Imagem:
    def __init__(self, largura, altura, rgba):
        self.largura, self.altura, self.rgba = largura, altura, rgba

    def hex(self, x, y):
        i = (y * self.largura + x) * 4
        r, g, b, a = self.rgba[i:i + 4]
        return rgba_hex(r, g, b, a)

    def recorte(self, ox, oy, w, h):
        return [[self.hex(ox + x, oy + y) for x in range(w)] for y in range(h)]


def rgba_hex(r, g, b, a):
    if a < LIMIAR_ALFA:
        return ""
    cor = f"#{r:02X}{g:02X}{b:02X}"
    return cor if a >= 255 else f"{cor}{a:02X}"


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def ler(dados: bytes) -> Imagem:
    if dados[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("não é PNG")
    pos, idat, paleta, trns = 8, bytearray(), None, None
    largura = altura = prof = tipo = entrelacado = None
    while pos + 8 <= len(dados):
        tam, nome = struct.unpack(">I4s", dados[pos:pos + 8])
        corpo = dados[pos + 8:pos + 8 + tam]
        pos += 12 + tam
        if nome == b"IHDR":
            largura, altura, prof, tipo, _, _, entrelacado = struct.unpack(">IIBBBBB", corpo)
        elif nome == b"PLTE":
            paleta = corpo
        elif nome == b"tRNS":
            trns = corpo
        elif nome == b"IDAT":
            idat += corpo
        elif nome == b"IEND":
            break  # o que vier depois do IEND é lixo (alguns editores deixam bytes a mais)
    if prof != 8 or entrelacado or tipo not in CANAIS:
        raise ValueError(f"PNG não suportado (profundidade {prof}, tipo {tipo}, entrelaçado {entrelacado})")
    bpp = CANAIS[tipo]
    cru = zlib.decompress(bytes(idat))
    linha = largura * bpp
    anterior = bytearray(linha)
    pixels = bytearray()
    for y in range(altura):
        inicio = y * (linha + 1)
        filtro, atual = cru[inicio], bytearray(cru[inicio + 1:inicio + 1 + linha])
        if filtro == 1:
            for i in range(bpp, linha):
                atual[i] = (atual[i] + atual[i - bpp]) & 255
        elif filtro == 2:
            for i in range(linha):
                atual[i] = (atual[i] + anterior[i]) & 255
        elif filtro == 3:
            for i in range(linha):
                esq = atual[i - bpp] if i >= bpp else 0
                atual[i] = (atual[i] + ((esq + anterior[i]) >> 1)) & 255
        elif filtro == 4:
            for i in range(linha):
                esq = atual[i - bpp] if i >= bpp else 0
                diag = anterior[i - bpp] if i >= bpp else 0
                atual[i] = (atual[i] + _paeth(esq, anterior[i], diag)) & 255
        pixels += atual
        anterior = atual
    rgba = bytearray(largura * altura * 4)
    if tipo == 6:
        rgba[:] = pixels
    elif tipo == 2:
        chave = struct.unpack(">HHH", trns) if trns and len(trns) == 6 else None
        for i in range(largura * altura):
            r, g, b = pixels[i * 3:i * 3 + 3]
            rgba[i * 4:i * 4 + 4] = bytes((r, g, b, 0 if chave == (r, g, b) else 255))
    elif tipo == 3:
        for i, idx in enumerate(pixels):
            r, g, b = paleta[idx * 3:idx * 3 + 3]
            a = trns[idx] if trns and idx < len(trns) else 255
            rgba[i * 4:i * 4 + 4] = bytes((r, g, b, a))
    elif tipo == 0:
        chave = struct.unpack(">H", trns)[0] if trns and len(trns) == 2 else None
        for i, v in enumerate(pixels):
            rgba[i * 4:i * 4 + 4] = bytes((v, v, v, 0 if v == chave else 255))
    else:  # tipo 4: cinza com alfa
        for i in range(largura * altura):
            v, a = pixels[i * 2:i * 2 + 2]
            rgba[i * 4:i * 4 + 4] = bytes((v, v, v, a))
    return Imagem(largura, altura, bytes(rgba))
