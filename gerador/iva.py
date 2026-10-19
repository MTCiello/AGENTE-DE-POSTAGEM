"""
I.V.A. (Inteligência Visual Ativa) — mascote animada da CIELLO.

Corpo: a nuvem do símbolo oficial (marfim), preenchida.
Rosto: visor carvão com olhos dourados (o mesmo ouro do ponto da logo).
Pontinho: o ponto dourado do logo vira o "ponteiro" dela — orbita e voa até o que ela mostra.

Estados: idle, talk, blink (automático), happy, think, wave, point.
"""
import math, os, io
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
MARFIM = (236, 231, 220)
CARVAO = (18, 18, 18)
OURO = (224, 168, 28)

_body_cache = {}

def _masks(w):
    """(anel marfim do logo, interior carvão) — o vão interno da nuvem vira o rosto"""
    import cairosvg, re
    svg = open(os.path.join(HERE, "..", "marca", "logo-simbolo-marfim.svg")).read()
    path = re.search(r'<path[^>]*d="([^"]+)"', svg).group(1)
    W0 = int(w * 3)
    sv = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-20 -20 740 520"><path fill="#fff" fill-rule="evenodd" d="{path}"/></svg>'
    png = cairosvg.svg2png(bytestring=sv.encode(), output_width=W0)
    ring = Image.open(io.BytesIO(png)).getchannel("A")
    # fecha o vão da direita do símbolo (entre o arco e a base) só para achar o interior
    sc = W0 / 740.0
    patch = ring.copy(); ImageDraw.Draw(patch).rectangle([(600 + 20) * sc, (300 + 20) * sc, (700 + 20) * sc, (400 + 20) * sc], fill=255)
    from scipy.ndimage import binary_fill_holes
    solid = (binary_fill_holes(np.array(patch) > 100) * 255).astype(np.uint8)
    solid[np.array(patch) > 100] = 0
    ImageDraw.Draw(Image.fromarray(solid))
    inner = Image.fromarray(solid).filter(ImageFilter.MaxFilter(5))
    size = (w, int(w * ring.height / ring.width))
    return ring.resize(size, Image.LANCZOS), inner.resize(size, Image.LANCZOS)

def body(w):
    if w in _body_cache: return _body_cache[w]
    ring, inner = _masks(w)
    im = Image.new("RGBA", ring.size, CARVAO + (0,)); im.putalpha(inner)
    r = Image.new("RGBA", ring.size, MARFIM + (0,)); r.putalpha(ring)
    im.alpha_composite(r)
    _body_cache[w] = im
    return im

def render(state="idle", t=0.0, w=320, talking=False, look=(0.0, 0.0)):
    """retorna (RGBA da I.V.A., (dx, dy) do centro do corpo dentro da imagem)"""
    b = body(w)
    pad = int(w * 0.35)
    can = Image.new("RGBA", (b.width + pad * 2, b.height + pad * 2), (0, 0, 0, 0))
    # flutuação + squash
    bob = math.sin(t * 2.6) * w * 0.025
    sq = 1 + 0.025 * math.sin(t * 5.2)
    if state == "happy": bob -= abs(math.sin(t * 9)) * w * 0.06; sq = 1 + 0.06 * math.sin(t * 18)
    bw, bh = int(b.width * (2 - sq)), int(b.height * sq)
    bb = b.resize((bw, bh), Image.LANCZOS)
    tilt = 0
    if state == "wave": tilt = 6 * math.sin(t * 6)
    if state == "think": tilt = -5
    if state == "point": tilt = 4
    if tilt: bb = bb.rotate(tilt, resample=Image.BICUBIC, expand=True)
    ox = (can.width - bb.width) // 2; oy = int((can.height - bb.height) // 2 + bob)
    # sombra
    d = ImageDraw.Draw(can)
    sw = w * (0.62 - 0.04 * math.sin(t * 2.6))
    d.ellipse([can.width / 2 - sw / 2, can.height - pad * 0.75, can.width / 2 + sw / 2, can.height - pad * 0.55], fill=(0, 0, 0, 90))
    can.alpha_composite(bb, (ox, oy))
    # visor (rosto)
    cx = ox + bb.width * 0.47; cy = oy + bb.height * 0.62
    vw, vh = w * 0.50, w * 0.25
    # olhos
    lx, ly = look
    ex = w * 0.105; eh = w * 0.085; ew = w * 0.055
    blink = (t % 3.7) < 0.12
    for s in (-1, 1):
        x = cx + s * ex + lx * w * 0.03; y = cy - w * 0.012 + ly * w * 0.025
        if state == "happy":
            d.arc([x - ew, y - eh * 0.5, x + ew, y + eh * 0.9], start=200, end=340, fill=OURO + (255,), width=max(3, int(w * 0.022)))
        elif blink:
            d.rounded_rectangle([x - ew / 2, y - 2, x + ew / 2, y + 3], radius=2, fill=OURO + (255,))
        else:
            h = eh * (0.75 if state == "think" else 1)
            d.rounded_rectangle([x - ew / 2, y - h / 2, x + ew / 2, y + h / 2], radius=ew / 2, fill=OURO + (255,))
            # brilho
            d.ellipse([x - ew * 0.25, y - h * 0.35, x - ew * 0.02, y - h * 0.12], fill=(255, 236, 180, 220))
    # boca
    my = cy + vh * 0.28
    if talking or state == "talk":
        o = abs(math.sin(t * 15)) * 0.7 + abs(math.sin(t * 9.3)) * 0.3
        mh = w * (0.012 + 0.035 * o); mw = w * (0.07 + 0.02 * o)
        d.rounded_rectangle([cx - mw / 2, my - mh / 2, cx + mw / 2, my + mh / 2], radius=mh / 2, fill=OURO + (255,))
    elif state == "happy":
        d.arc([cx - w * 0.05, my - w * 0.04, cx + w * 0.05, my + w * 0.02], start=20, end=160, fill=OURO + (255,), width=max(3, int(w * 0.018)))
    else:
        d.rounded_rectangle([cx - w * 0.035, my - 2, cx + w * 0.035, my + 3], radius=2, fill=OURO + (200,))
    # brilho no visor
    return can, (can.width / 2, oy + bb.height * 0.5)

def dot(layer, x, y, r, glow=1.0):
    """o ponto dourado (Pontinho), com brilho suave"""
    if glow:
        g = Image.new("RGBA", (int(r * 8), int(r * 8)), OURO + (0,))
        m = Image.new("L", g.size, 0)
        ImageDraw.Draw(m).ellipse([r * 2.2, r * 2.2, r * 5.8, r * 5.8], fill=int(110 * glow))
        g.putalpha(m.filter(ImageFilter.GaussianBlur(r * 0.9)))
        layer.alpha_composite(g, (int(x - r * 4), int(y - r * 4)))
    d = ImageDraw.Draw(layer)
    d.ellipse([x - r, y - r, x + r, y + r], fill=OURO + (255,))
    d.ellipse([x - r * 0.5, y - r * 0.55, x - r * 0.1, y - r * 0.2], fill=(255, 232, 160, 210))

def orbit_pos(cx, cy, w, t):
    a = t * 1.8
    return cx + w * 0.5 + math.cos(a) * w * 0.12, cy + w * 0.12 + math.sin(a * 1.3) * w * 0.06
