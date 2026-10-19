#!/usr/bin/env python3
"""
Gerador de reels da CIELLO — v5 (identidade escura atual + I.V.A. + exemplos na tela).

Identidade (posts atuais do @ciellotec): fundo carvão texturizado com luz quente, títulos em
Anton caixa alta (marfim / cinza / ouro), texto em serifa, rótulos espaçados em ouro, pílulas.
Mascote: I.V.A. (gerador/iva.py) — a nuvem do logo com rosto; o ponto dourado é o ponteiro dela.

Padrões de edição aplicados (retenção): gancho com palavras batendo na tela + zoom punch,
quebra de padrão a cada cena (~4-6 s): mockups mostrando o exemplo de verdade (busca no
celular, cards, chat, prompt, antes/depois), legenda dinâmica, efeitos sonoros em cada evento,
transição em chicote (whip).

Uso:
  python3 render_reel.py roteiro.json saida.mp4 [--total SEGUNDOS] [--silent | --sfx-only]
    --silent    sem áudio
    --sfx-only  só efeitos sonoros (para montar com narração + trilha no vidIQ com keepNativeAudio)
    (padrão)    efeitos + batida local (prévia)

Tipos de cena (campo "type"):
  hook      kicker, tag, lines:[[texto, cor]]            cor: marfim|cinza|ouro
  search    kicker, title:[[...]], query, results:[{name, meta, badge}], pick (índice)
  cards     kicker, title, cards:[{name, line, tags:[..]}]
  chat      kicker, title, contact, messages:[{me:true/false, text}]
  prompt    kicker, title, prompt, answer:[linhas]
  compare   kicker, title, left:{label, word, items}, right:{label, word, items}
  checklist kicker, title, items:[..]
  cta       kicker, lines, button, save
Todas aceitam "say" (fala da narração, vira legenda) e "iva" (idle|wave|point|think|happy).
"""
import json, math, subprocess, sys, os, wave, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import iva as IVA

W, H, FPS = 1080, 1920, 30
BG = (18, 18, 18)
MARFIM = (236, 231, 220)
CINZA = (112, 110, 106)
OURO = (224, 168, 28)
LINHA = (58, 56, 52)
CARD = (30, 29, 27)
CARD2 = (42, 40, 37)
VERDE = (46, 139, 71)
VERMELHO = (208, 52, 44)
CORES = {"marfim": MARFIM, "cinza": CINZA, "ouro": OURO, "verde": VERDE, "vermelho": VERMELHO}

MX = 80
SAFE_R = 130
TW = W - MX - SAFE_R
CAP_Y = 1540

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "fonts")
FONTS = {
    "anton": "anton-latin-400-normal.woff",
    "label": "oswald-latin-500-normal.woff",
    "labelb": "oswald-latin-600-normal.woff",
    "cap": "oswald-latin-600-normal.woff",
    "serif": "source-serif-4-latin-400-normal.woff",
    "serifb": "source-serif-4-latin-600-normal.woff",
    "serifi": "source-serif-4-latin-400-italic.woff",
}
_fc = {}
def font(n, s):
    s = max(8, int(round(s))); k = (n, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(os.path.join(FD, FONTS[n]), s)
    return _fc[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x):
    x = clamp(x); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def rgba(c, a=1.0): return (c[0], c[1], c[2], int(255 * clamp(a)))
def col(name): return CORES.get(name, MARFIM)

def tlen(t, f, sp=0): return f.getlength(t) + sp * max(0, len(t) - 1)
def spaced(d, xy, t, f, fill, sp):
    x, y = xy
    for ch in t:
        d.text((x, y), ch, font=f, fill=fill); x += f.getlength(ch) + sp
def wrap(text, f, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if f.getlength(t) <= maxw: cur = t
        else:
            if cur: out.append(cur)
            cur = w
    if cur: out.append(cur)
    return out
def fit(t, n, s, maxw):
    while s > 30 and font(n, s).getlength(t) > maxw: s -= 3
    return s

# ---------------- fundo ----------------
class Backdrop:
    def __init__(self):
        rnd = np.random.default_rng(5)
        base = np.zeros((H, W, 3), np.float32); base[:] = BG
        yy, xx = np.mgrid[0:H, 0:W]
        vig = 1 - 0.55 * (((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2)
        base *= np.clip(vig, 0.55, 1)[..., None]
        self.base = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
        d = ImageDraw.Draw(self.base)
        for x in range(0, W, 90): d.line([(x, 0), (x, H)], fill=(26, 26, 25, 255), width=1)
        for y in range(0, H, 90): d.line([(0, y), (W, y)], fill=(26, 26, 25, 255), width=1)
        self.grain = []
        for _ in range(4):
            n = rnd.integers(0, 255, (H // 2, W // 2), dtype=np.uint8)
            g = Image.fromarray(n).resize((W, H), Image.NEAREST)
            gi = Image.new("RGBA", (W, H), (255, 255, 255, 0)); gi.putalpha(g.point(lambda v: int(v * 0.045)))
            self.grain.append(gi)
        L = Image.new("L", (1300, 1300), 0)
        ImageDraw.Draw(L).ellipse([150, 150, 1150, 1150], fill=150)
        L = L.filter(ImageFilter.GaussianBlur(210))
        self.lamp = Image.new("RGBA", L.size, (255, 196, 110, 0)); self.lamp.putalpha(L.point(lambda v: int(v * 0.42)))
    def render(self, gt, fi):
        fr = self.base.copy()
        a = 0.85 + 0.15 * math.sin(gt * 1.3)
        lp = self.lamp if a > 0.99 else self.lamp.copy()
        if a <= 0.99: lp.putalpha(self.lamp.getchannel("A").point(lambda v: int(v * a)))
        fr.alpha_composite(lp, (-650 + int(30 * math.sin(gt * .4)), -620))
        fr.alpha_composite(self.grain[(fi // 2) % 4])
        return fr

# ---------------- peças ----------------
_logo = {}
def logo(layer, x, y, h=40):
    if h not in _logo:
        im = Image.open(os.path.join(HERE, "..", "marca", "logo-simbolo-marfim.png")).convert("RGBA")
        _logo[h] = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    im = _logo[h]; layer.alpha_composite(im, (int(x), int(y)))
    d = ImageDraw.Draw(layer)
    spaced(d, (x + im.width + 16, y - h * 0.18), "CIELLO", font("labelb", h * 0.95), rgba(MARFIM), h * 0.28)

def pill_outline(d, x1, y, text, color=MARFIM, a=1.0, size=26):
    f = font("label", size); w = tlen(text, f, 4) + 56; h = size * 2.1
    d.rounded_rectangle([x1 - w, y, x1, y + h], radius=h / 2, outline=rgba(color, a), width=2)
    spaced(d, (x1 - w + 28, y + h * 0.2), text, f, rgba(color, a), 4)

def kicker(layer, x, y, txt, t):
    d = ImageDraw.Draw(layer); p = eo(t / 0.4)
    d.line([(x, y + 18), (x + 46 * p, y + 18)], fill=rgba(OURO), width=4)
    a = clamp((t - 0.1) / 0.3)
    spaced(d, (x + 64 + 16 * (1 - a), y), txt.upper(), font("labelb", 30), rgba(OURO, a), 7)

def slam_line(layer, x, y, txt, f, color, t, start):
    """palavra/linha que 'bate' na tela: entra grande e assenta"""
    p = (t - start) / 0.32
    if p <= 0: return
    s = 1 + 0.35 * (1 - eo(p)); a = clamp(p * 2.5)
    w = int(f.getlength(txt) + 20); bb = f.getbbox(txt + "Á"); h = int(bb[3] + 20)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(im).text((4, 0), txt, font=f, fill=rgba(color, a))
    if s != 1: im = im.resize((int(w * s), int(h * s)), Image.LANCZOS)
    layer.alpha_composite(im, (int(x - (im.width - w) * 0.15), int(y - (im.height - h) * 0.5)))

def title_block(layer, sc, t, y=250, size=118):
    if sc.get("kicker"): kicker(layer, MX, y, sc["kicker"], t); y += 70
    lines = sc.get("title", [])
    if isinstance(lines, str): lines = [[lines, "marfim"]]
    for i, (txt, c) in enumerate(lines):
        f = font("anton", fit(txt.upper(), "anton", size, TW))
        slam_line(layer, MX, y, txt.upper(), f, col(c), t, 0.12 + 0.12 * i)
        y += int(f.size * 1.12)
    return y + 20

def phone(layer, x, y, w, h, a=1.0):
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x - 8, y - 8, x + w + 8, y + h + 8], radius=64, fill=rgba((8, 8, 8), a), outline=rgba((70, 68, 64), a), width=3)
    d.rounded_rectangle([x, y, x + w, y + h], radius=56, fill=rgba((246, 244, 238), a))
    d.rounded_rectangle([x + w / 2 - 70, y + 16, x + w / 2 + 70, y + 50], radius=17, fill=rgba((8, 8, 8), a))
    return d

def stars(d, x, y, n, s, a):
    for i in range(5):
        cx = x + i * s * 1.15; c = (240, 170, 20) if i < n else (200, 200, 200)
        pts = []
        for k in range(10):
            r = s / 2 if k % 2 == 0 else s / 4.5; ang = -math.pi / 2 + k * math.pi / 5
            pts.append((cx + r * math.cos(ang), y + r * math.sin(ang)))
        d.polygon(pts, fill=rgba(c, a))

# ---------------- cenas ----------------
EVENTS = []   # (tempo_global, tipo) — preenchido no planejamento para os efeitos sonoros

def ev_hook(sc, dur): return [(0.12 + 0.16 * i, "thump") for i in range(len(sc.get("lines", [])))]
def scene_hook(L, sc, t, dur, ctx):
    d = ImageDraw.Draw(L)
    if sc.get("tag"): pill_outline(d, W - MX, 96, sc["tag"].upper(), a=clamp(t / 0.3))
    y = 430
    if sc.get("kicker"): kicker(L, MX, y, sc["kicker"], t); y += 80
    for i, (txt, c) in enumerate(sc["lines"]):
        f = font("anton", fit(txt.upper(), "anton", 200, TW))
        slam_line(L, MX, y, txt.upper(), f, col(c), t, 0.12 + 0.16 * i)
        y += int(f.size * 1.1)
    if sc.get("sub"):
        fs = font("serif", 44); a = eo((t - 0.25 - 0.16 * len(sc["lines"])) / 0.4)
        for k, ln in enumerate(wrap(sc["sub"], fs, TW)):
            d.text((MX, y + 10 + k * 58 + 20 * (1 - a)), ln, font=fs, fill=rgba(MARFIM, a))

def ev_search(sc, dur):
    e = [(0.15, "thump"), (0.5, "whoosh")]
    q = sc.get("query", ""); e += [(0.9 + i * 0.045, "tick") for i in range(0, len(q), 2)]
    t0 = 0.9 + len(q) * 0.045 + 0.2
    e += [(t0 + 0.25 * i, "pop") for i in range(len(sc.get("results", [])))]
    e += [(t0 + 0.25 * len(sc.get("results", [])) + 0.3, "ding")]
    return e
def scene_search(L, sc, t, dur, ctx):
    y0 = title_block(L, sc, t)
    a = eo((t - 0.4) / 0.4); py = y0 + 60 * (1 - a) + 10
    px, pw, ph = 190, 700, 1300 - y0
    d = phone(L, px, py, pw, ph, a)
    # barra de busca
    q = sc.get("query", ""); n = int(clamp((t - 0.9) / max(0.1, len(q) * 0.045)) * len(q))
    d.rounded_rectangle([px + 36, py + 80, px + pw - 36, py + 150], radius=35, fill=rgba((255, 255, 255), a), outline=rgba((220, 220, 220), a), width=2)
    d.ellipse([px + 62, py + 100, px + 88, py + 126], outline=rgba((120, 120, 120), a), width=3)
    d.line([(px + 85, py + 123), (px + 96, py + 134)], fill=rgba((120, 120, 120), a), width=3)
    d.text((px + 112, py + 96), q[:n], font=font("serif", 34), fill=rgba((40, 40, 40), a))
    if n < len(q) and int(t * 4) % 2 == 0:
        cx = px + 112 + font("serif", 34).getlength(q[:n]); d.rectangle([cx + 2, py + 98, cx + 5, py + 134], fill=rgba((30, 100, 220), a))
    t0 = 0.9 + len(q) * 0.045 + 0.2
    ry = py + 180
    pick = sc.get("pick", 0)
    for i, r in enumerate(sc.get("results", [])):
        p = back((t - t0 - 0.25 * i) / 0.35)
        if p <= 0: continue
        cy = ry + i * 158 + 40 * (1 - clamp(p))
        if cy + 140 > py + ph - 20: break
        d.rounded_rectangle([px + 30, cy, px + pw - 30, cy + 140], radius=22, fill=rgba((255, 255, 255), clamp(p)), outline=rgba((228, 226, 220), clamp(p)), width=2)
        d.rounded_rectangle([px + 50, cy + 20, px + 150, cy + 120], radius=16, fill=rgba((215, 205, 185), clamp(p)))
        d.text((px + 82, cy + 38), r["name"][0], font=font("anton", 54), fill=rgba((90, 80, 60), clamp(p)))
        d.text((px + 172, cy + 18), r["name"], font=font("serifb", 34), fill=rgba((25, 25, 25), clamp(p)))
        stars(d, px + 185, cy + 80, r.get("stars", 4), 22, clamp(p))
        d.text((px + 320, cy + 64), r.get("meta", ""), font=font("serif", 26), fill=rgba((110, 110, 110), clamp(p)))
        if r.get("badge"):
            fb = font("labelb", 22); bw = fb.getlength(r["badge"]) + 30
            d.rounded_rectangle([px + pw - 50 - bw, cy + 22, px + pw - 50, cy + 58], radius=18, fill=rgba(VERMELHO, clamp(p)))
            d.text((px + pw - 35 - bw, cy + 25), r["badge"], font=fb, fill=rgba((255, 255, 255), clamp(p)))
        if i == pick:
            hp = eo((t - t0 - 0.25 * len(sc["results"]) - 0.3) / 0.4)
            if hp > 0:
                d.rounded_rectangle([px + 22, cy - 8, px + pw - 22, cy + 148], radius=28, outline=rgba(OURO, hp), width=6)
                ctx["dot_target"] = (px + pw - 40, cy - 10)

def ev_cards(sc, dur):
    e = [(0.15, "thump"), (0.5, "whoosh")]
    for i, c in enumerate(sc.get("cards", [])):
        e.append((0.7 + 0.55 * i, "pop"))
        e += [(1.0 + 0.55 * i + 0.15 * k, "tick") for k in range(len(c.get("tags", [])))]
    e.append((0.7 + 0.55 * len(sc.get("cards", [])) + 0.2, "ding"))
    return e
def scene_cards(L, sc, t, dur, ctx):
    y = title_block(L, sc, t) + 20
    d = ImageDraw.Draw(L)
    # barra "analisando"
    pr = clamp((t - 0.5) / (0.55 * len(sc["cards"]) + 0.6))
    d.text((MX, y), "ANALISANDO" if pr < 1 else "ANÁLISE PRONTA", font=font("labelb", 26), fill=rgba(OURO if pr >= 1 else CINZA))
    d.rounded_rectangle([MX + 230, y + 14, W - SAFE_R, y + 24], radius=5, fill=rgba(LINHA))
    d.rounded_rectangle([MX + 230, y + 14, MX + 230 + (W - SAFE_R - MX - 230) * pr, y + 24], radius=5, fill=rgba(OURO))
    y += 60
    for i, c in enumerate(sc["cards"]):
        p = back((t - 0.7 - 0.55 * i) / 0.4)
        if p <= 0: continue
        x = MX + 60 * (1 - clamp(p)); a = clamp(p)
        d.rounded_rectangle([x, y, W - SAFE_R, y + 190], radius=26, fill=rgba(CARD, a), outline=rgba(LINHA, a), width=2)
        d.ellipse([x + 26, y + 30, x + 116, y + 120], fill=rgba(CARD2, a), outline=rgba(OURO, a), width=3)
        d.text((x + 56, y + 46), c["name"][0], font=font("anton", 48), fill=rgba(MARFIM, a))
        d.text((x + 140, y + 26), c["name"], font=font("serifb", 36), fill=rgba(MARFIM, a))
        d.text((x + 140, y + 74), c.get("line", ""), font=font("serif", 28), fill=rgba(CINZA, a))
        tx = x + 140
        for k, tag in enumerate(c.get("tags", [])):
            tp = back((t - 1.0 - 0.55 * i - 0.15 * k) / 0.3)
            if tp <= 0: continue
            ft = font("labelb", 22); tw = ft.getlength(tag) + 28
            bad = tag.lower().startswith(("sem", "parado", "não"))
            cc = VERMELHO if bad else VERDE
            d.rounded_rectangle([tx, y + 124, tx + tw * clamp(tp, 0, 1.1), y + 162], radius=19, fill=rgba(cc, clamp(tp)))
            if tp > 0.6: d.text((tx + 14, y + 128), tag, font=ft, fill=rgba((255, 255, 255), clamp(tp)))
            tx += tw + 12
        if i == len(sc["cards"]) - 1 and pr >= 1: ctx["dot_target"] = (W - SAFE_R - 30, y + 20)
        y += 214

def ev_chat(sc, dur):
    e = [(0.15, "thump"), (0.5, "whoosh")]
    for i in range(len(sc.get("messages", []))): e.append((0.9 + 1.0 * i + 0.45, "ding" if not sc["messages"][i].get("me") else "send"))
    return e
def scene_chat(L, sc, t, dur, ctx):
    y0 = title_block(L, sc, t)
    a = eo((t - 0.4) / 0.4); py = y0 + 60 * (1 - a) + 10
    px, pw, ph = 190, 700, 1300 - y0
    d = phone(L, px, py, pw, ph, a)
    d.rectangle([px + 4, py + 70, px + pw - 4, py + 150], fill=rgba((24, 24, 24), a))
    d.ellipse([px + 30, py + 84, px + 82, py + 136], fill=rgba(CARD2, a), outline=rgba(OURO, a), width=2)
    d.text((px + 100, py + 84), sc.get("contact", "Cliente"), font=font("serifb", 30), fill=rgba(MARFIM, a))
    d.text((px + 100, py + 118), "online", font=font("serif", 22), fill=rgba((140, 200, 150), a))
    d.rectangle([px + 4, py + 150, px + pw - 4, py + ph - 4], fill=rgba((236, 229, 216), a))
    y = py + 180
    fm = font("serif", 30)
    for i, m in enumerate(sc.get("messages", [])):
        st = 0.9 + 1.0 * i
        if t < st: break
        me = m.get("me", True)
        lines = wrap(m["text"], fm, pw * 0.62)
        bh = len(lines) * 40 + 50; bw = max(fm.getlength(l) for l in lines) + 50
        x = px + pw - 30 - bw if me else px + 30
        if t < st + 0.45:   # digitando...
            tw = 110; x2 = px + pw - 30 - tw if me else px + 30
            d.rounded_rectangle([x2, y, x2 + tw, y + 60], radius=26, fill=rgba((255, 255, 255) if not me else (224, 200, 140), a))
            for k in range(3):
                jump = 6 * math.sin(t * 12 + k)
                d.ellipse([x2 + 24 + k * 24, y + 26 - jump, x2 + 38 + k * 24, y + 40 - jump], fill=rgba((120, 120, 120), a))
            break
        p = back((t - st - 0.45) / 0.3)
        d.rounded_rectangle([x, y + 20 * (1 - clamp(p)), x + bw, y + bh], radius=24,
                            fill=rgba((224, 200, 140) if me else (255, 255, 255), clamp(p)))
        for k, ln in enumerate(lines):
            d.text((x + 25, y + 18 + k * 40), ln, font=fm, fill=rgba((30, 30, 30), clamp(p)))
        if me:
            d.text((x + bw - 50, y + bh - 34), "✓✓", font=font("label", 20), fill=rgba((40, 110, 200), clamp(p)))
        y += bh + 18
        if y > py + ph - 120: break

def type_rate(q): return min(0.04, 1.5 / max(1, len(q)))
def ev_prompt(sc, dur):
    q = sc.get("prompt", ""); e = [(0.15, "thump"), (0.5, "whoosh")]; r = type_rate(q)
    e += [(0.8 + i * r, "tick") for i in range(0, len(q), 2)]
    t1 = 0.8 + len(q) * r + 0.2
    e += [(t1, "send")] + [(t1 + 0.4 + 0.3 * i, "pop") for i in range(len(sc.get("answer", [])))]
    return e
def scene_prompt(L, sc, t, dur, ctx):
    y = title_block(L, sc, t) + 20
    d = ImageDraw.Draw(L)
    a = eo((t - 0.4) / 0.35)
    q = sc.get("prompt", "")
    fp = font("serif", 36); lines = wrap(q, fp, TW - 120)
    bh = len(lines) * 50 + 110
    d.rounded_rectangle([MX, y, W - SAFE_R, y + bh], radius=30, fill=rgba(CARD, a), outline=rgba(LINHA, a), width=2)
    IVA.dot(L, MX + 44, y + 40, 12, glow=0.5 * a)
    d.text((MX + 70, y + 24), "Você pede", font=font("labelb", 26), fill=rgba(CINZA, a))
    r = type_rate(q); n = int(clamp((t - 0.8) / max(0.1, len(q) * r)) * len(q))
    for k, ln in enumerate(wrap(q[:n], fp, TW - 120) if n else []):
        d.text((MX + 36, y + 70 + k * 50), ln, font=fp, fill=rgba(MARFIM, a))
    t1 = 0.8 + len(q) * r + 0.2
    sx, sy = W - SAFE_R - 60, y + bh - 50
    d.ellipse([sx - 28, sy - 28, sx + 28, sy + 28], fill=rgba(OURO if t > t1 else CARD2, a))
    d.polygon([(sx - 9, sy - 13), (sx - 9, sy + 13), (sx + 14, sy)], fill=rgba(BG, a))
    y += bh + 30
    for i, ln in enumerate(sc.get("answer", [])):
        p = eo((t - t1 - 0.4 - 0.3 * i) / 0.35)
        if p <= 0: continue
        d.rounded_rectangle([MX, y, W - SAFE_R, y + 92], radius=20, fill=rgba(CARD2, p))
        d.ellipse([MX + 26, y + 30, MX + 58, y + 62], fill=rgba(OURO, p))
        d.line([(MX + 33, y + 46), (MX + 40, y + 54), (MX + 52, y + 38)], fill=rgba(BG, p), width=4)
        fa = font("serif", 32)
        d.text((MX + 80 + 20 * (1 - p), y + 26), wrap(ln, fa, TW - 120)[0], font=fa, fill=rgba(MARFIM, p))
        y += 108
    if t > t1 + 0.5: ctx["dot_target"] = (W - SAFE_R - 40, y - 60)

def ev_compare(sc, dur):
    e = [(0.15, "thump"), (0.5, "whoosh"), (0.9, "thump"), (1.7, "thump")]
    e += [(1.1 + 0.25 * i, "x") for i in range(len(sc["left"].get("items", [])))]
    e += [(1.9 + 0.25 * i, "pop") for i in range(len(sc["right"].get("items", [])))]
    return e
def scene_compare(L, sc, t, dur, ctx):
    y0 = title_block(L, sc, t, size=104)
    d = ImageDraw.Draw(L)
    half = (W - 2 * MX) / 2 - 10
    for side, key, st in ((0, "left", 0.8), (1, "right", 1.6)):
        s = sc[key]; p = eo((t - st) / 0.4)
        if p <= 0: continue
        x = MX + side * (half + 20); y = y0 + 20 + 40 * (1 - p)
        fill = (14, 14, 14) if side == 0 else (236, 229, 214)
        fg = MARFIM if side == 0 else (25, 25, 25)
        d.rounded_rectangle([x, y, x + half, 1330], radius=26, fill=rgba(fill, p), outline=rgba(LINHA if side == 0 else OURO, p), width=2)
        spaced(d, (x + 28, y + 30), s.get("label", "").upper(), font("labelb", 22), rgba(CINZA if side == 0 else (120, 100, 50), p), 5)
        fw = font("anton", fit(s["word"].upper(), "anton", 92, half - 56))
        wc = MARFIM if side == 0 else OURO
        d.text((x + 28, y + 70), s["word"].upper(), font=fw, fill=rgba(wc, p))
        if side == 0:
            ww = fw.getlength(s["word"].upper()); sp = eo((t - st - 0.3) / 0.3)
            d.line([(x + 20, y + 70 + fw.size * 0.62), (x + 20 + (ww + 20) * sp, y + 70 + fw.size * 0.62)], fill=rgba(VERMELHO), width=7)
        iy = y + 100 + fw.size
        fi = font("serif", 30)
        for k, it in enumerate(s.get("items", [])):
            q = eo((t - st - 0.3 - 0.25 * k) / 0.3)
            if q <= 0: continue
            if side == 0:
                d.line([(x + 30, iy + 10), (x + 52, iy + 32)], fill=rgba(VERMELHO, q), width=5); d.line([(x + 52, iy + 10), (x + 30, iy + 32)], fill=rgba(VERMELHO, q), width=5)
            else:
                d.ellipse([x + 26, iy + 6, x + 58, iy + 38], fill=rgba((30, 70, 60), q))
                d.line([(x + 33, iy + 22), (x + 40, iy + 30), (x + 52, iy + 14)], fill=rgba((255, 255, 255), q), width=4)
            for j, ln in enumerate(wrap(it, fi, half - 110)):
                d.text((x + 72 + 16 * (1 - q), iy + j * 38), ln, font=fi, fill=rgba(fg, q))
            iy += 38 * len(wrap(it, fi, half - 110)) + 26

def ev_checklist(sc, dur):
    return [(0.15, "thump"), (0.5, "whoosh")] + [(0.8 + 0.6 * i, "pop") for i in range(len(sc.get("items", [])))]
def scene_checklist(L, sc, t, dur, ctx):
    y = title_block(L, sc, t) + 30
    d = ImageDraw.Draw(L)
    for i, it in enumerate(sc.get("items", [])):
        p = back((t - 0.8 - 0.6 * i) / 0.35)
        if p <= 0: continue
        a = clamp(p)
        d.rounded_rectangle([MX, y, W - SAFE_R, y + 130], radius=24, fill=rgba(CARD, a), outline=rgba(LINHA, a), width=2)
        d.text((MX + 30, y + 22), f"{i + 1:02d}", font=font("anton", 70), fill=rgba(OURO, a))
        fi = font("serif", 36)
        for j, ln in enumerate(wrap(it, fi, TW - 190)[:2]):
            d.text((MX + 150 + 20 * (1 - a), y + 22 + j * 46 + (23 if len(wrap(it, fi, TW - 190)) == 1 else 0)), ln, font=fi, fill=rgba(MARFIM, a))
        y += 152

def ev_cta(sc, dur): return [(0.12 + 0.16 * i, "thump") for i in range(len(sc.get("lines", [])))] + [(1.0, "pop"), (1.3, "ding")]
def scene_cta(L, sc, t, dur, ctx):
    d = ImageDraw.Draw(L)
    y = 360
    if sc.get("kicker"): kicker(L, MX, y, sc["kicker"], t); y += 80
    for i, (txt, c) in enumerate(sc["lines"]):
        f = font("anton", fit(txt.upper(), "anton", 170, TW))
        slam_line(L, MX, y, txt.upper(), f, col(c), t, 0.12 + 0.16 * i); y += int(f.size * 1.1)
    y += 30
    bp = back((t - 0.95) / 0.4)
    if bp > 0 and sc.get("button"):
        fb = font("anton", 54); lbl = sc["button"].upper()
        bw = fb.getlength(lbl) + 120; bh = 116; pul = 1 + 0.03 * math.sin(max(0, t - 1.4) * 6)
        w2 = bw * clamp(bp, 0, 1.08) * pul
        d.rounded_rectangle([MX, y, MX + w2, y + bh], radius=bh / 2, fill=rgba(OURO))
        if bp > 0.7: d.text((MX + 60, y + 20), lbl, font=fb, fill=rgba(BG))
        ctx["dot_target"] = (MX + w2 + 40, y + bh / 2)
        y += bh + 30
    sp = eo((t - 1.3) / 0.4)
    if sp > 0 and sc.get("save"):
        f2 = font("labelb", 30); lbl = sc["save"].upper(); bw = tlen(lbl, f2, 4) + 110
        d.rounded_rectangle([MX, y, MX + bw, y + 80], radius=40, outline=rgba(MARFIM, sp), width=3)
        bx, by = MX + 36, y + 22
        d.polygon([(bx, by), (bx + 24, by), (bx + 24, by + 36), (bx + 12, by + 27), (bx, by + 36)], fill=rgba(OURO, sp))
        spaced(d, (MX + 82, y + 16), lbl, f2, rgba(MARFIM, sp), 4)

SCENES = {k: (globals()["scene_" + k], globals()["ev_" + k]) for k in
          ["hook", "search", "cards", "chat", "prompt", "compare", "checklist", "cta"]}

# ---------------- legenda ----------------
def caption(L, sc, t, dur):
    say = sc.get("say")
    if not say: return
    w = say.split(); cs = [" ".join(w[i:i + 3]) for i in range(0, len(w), 3)]
    lens = [len(c) + 2 for c in cs]; tot = sum(lens); acc = 0.05; idx = len(cs) - 1; cst = acc
    span = max(0.1, dur - 0.1)
    for i, Lc in enumerate(lens):
        seg = span * Lc / tot
        if t < acc + seg: idx = i; cst = acc; break
        acc += seg
    txt = cs[idx].upper(); q = back((t - cst) / 0.25); s = 0.8 + 0.2 * clamp(q, 0, 1.1)
    f = font("anton", 66 * s); tw = f.getlength(txt)
    d = ImageDraw.Draw(L); x = (W - tw) / 2 - 10; y = CAP_Y
    parts = txt.rsplit(" ", 1)
    first = parts[0] + " " if len(parts) == 2 else ""
    d.text((x, y), first, font=f, fill=rgba(MARFIM), stroke_width=6, stroke_fill=(0, 0, 0, 255))
    d.text((x + f.getlength(first), y), parts[-1], font=f, fill=rgba(OURO), stroke_width=6, stroke_fill=(0, 0, 0, 255))

# ---------------- áudio ----------------
SR = 44100
def sfx(kind):
    rnd = np.random.default_rng(hash(kind) % 1000)
    if kind == "whoosh":
        n = int(0.38 * SR); x = np.linspace(0, 1, n); s = rnd.standard_normal(n)
        s = np.convolve(s, np.ones(18) / 18, mode="same"); return 0.32 * s * np.sin(np.pi * x) ** 2
    if kind == "thump":
        n = int(0.28 * SR); x = np.arange(n) / SR; f = 55 + 120 * np.exp(-x * 40)
        return 0.75 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 14)
    if kind == "pop":
        n = int(0.09 * SR); x = np.arange(n) / SR; f = 900 - 500 * x / 0.09
        return 0.25 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 45)
    if kind == "tick":
        n = int(0.025 * SR); return 0.08 * rnd.standard_normal(n) * np.exp(-np.arange(n) / SR * 260)
    if kind in ("ding", "send"):
        n = int(0.5 * SR); x = np.arange(n) / SR
        fr = (1318, 1760) if kind == "ding" else (880, 1174)
        return 0.16 * (np.sin(2 * np.pi * fr[0] * x) * np.exp(-x * 9) + 0.7 * np.sin(2 * np.pi * fr[1] * x) * np.exp(-x * 11) * (x > 0.07))
    if kind == "x":
        n = int(0.12 * SR); x = np.arange(n) / SR
        return 0.18 * np.sign(np.sin(2 * np.pi * 180 * x)) * np.exp(-x * 30)
    return np.zeros(10)

def build_audio(path, total, events, with_beat):
    n = int(total * SR); out = np.zeros(n)
    if with_beat:
        beat = 60 / 118
        for b in np.arange(0, total, beat):
            i0 = int(b * SR); s = sfx("thump") * 0.5; L_ = min(len(s), n - i0); out[i0:i0 + L_] += s[:L_]
    for (tm, k) in events:
        s = sfx(k); i0 = int(tm * SR)
        if i0 >= n: continue
        L_ = min(len(s), n - i0); out[i0:i0 + L_] += s[:L_]
    out = np.tanh(out * 1.1); m = max(1e-6, np.max(np.abs(out))); out = out / m * 0.85
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((out * 32767).astype(np.int16).tobytes())

# ---------------- principal ----------------
def plan(scenes, total):
    if total is None: return [s.get("dur", 5.0) for s in scenes]
    w = [max(10, len(s.get("say", ""))) for s in scenes]
    u = total - 0.6; ds = [u * x / sum(w) for x in w]; ds[-1] += 0.6
    return ds

def main():
    a = sys.argv[1:]
    mode = "silent" if "--silent" in a else ("sfx" if "--sfx-only" in a else "full")
    total = float(a[a.index("--total") + 1]) if "--total" in a else None
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] != "--total")]
    cfg = json.load(open(pos[0], encoding="utf-8")); out = pos[1]
    sc = cfg["scenes"]; ds = plan(sc, total); total = sum(ds)
    st, acc = [], 0.0
    for x in ds: st.append(acc); acc += x
    events = []
    for i, s in enumerate(sc):
        events.append((st[i], "whoosh") if i > 0 else (0.0, "thump"))
        events += [(st[i] + tm, k) for tm, k in SCENES[s["type"]][1](s, ds[i]) if tm < ds[i]]
    bd = Backdrop(); nf = int(round(total * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    wav = out + ".wav"
    if mode != "silent":
        build_audio(wav, total, events, mode == "full"); cmd += ["-i", wav, "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    dot = [W - 200.0, 1300.0]
    n = len(sc)
    for fi in range(nf):
        gt = fi / FPS
        i = max(k for k in range(n) if st[k] <= gt + 1e-9); lt = gt - st[i]; s = sc[i]
        fr = bd.render(gt, fi)
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ctx = {}
        SCENES[s["type"]][0](L, s, lt, ds[i], ctx)
        # zoom punch no começo da cena
        if lt < 0.3:
            z = 1 + 0.07 * (1 - eo(lt / 0.3))
            Lz = L.resize((int(W * z), int(H * z)), Image.BILINEAR)
            L = Lz.crop(((Lz.width - W) // 2, (Lz.height - H) // 2, (Lz.width - W) // 2 + W, (Lz.height - H) // 2 + H))
        # chicote (whip) entre cenas
        if i > 0 and lt < 0.16:
            k = lt / 0.16
            sm = L.resize((max(1, W // 14), H), Image.BILINEAR).resize((W, H), Image.BILINEAR)
            off = int(W * 0.5 * (1 - eo(k)))
            L2 = Image.new("RGBA", (W, H), (0, 0, 0, 0)); L2.alpha_composite(Image.blend(sm, L, eo(k)), (off, 0)); L = L2
        fr.alpha_composite(L)
        # I.V.A.
        state = s.get("iva", "idle")
        if s["type"] == "cta" and lt > 1.0: state = "happy"
        if s["type"] in ("prompt",) and lt < 1.5: state = "think"
        iw = 250 if s["type"] not in ("hook", "cta") else 300
        enter = back((gt - 0.35) / 0.6)
        im, (bcx, bcy) = IVA.render(state, gt, iw, talking=(state not in ("happy",)))
        ix = W - im.width + 40 if s["type"] in ("hook", "cta") else 10
        iy = 1210 if s["type"] in ("hook", "cta") else 1250
        iy += int((1 - clamp(enter)) * 500)
        top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        top.alpha_composite(im, (int(ix), int(iy)))
        # Pontinho (ponto dourado) — orbita a I.V.A. ou voa até o que ela mostra
        home = IVA.orbit_pos(ix + bcx, iy + bcy, iw, gt)
        tgt = ctx.get("dot_target", home)
        dot[0] += (tgt[0] - dot[0]) * 0.22; dot[1] += (tgt[1] - dot[1]) * 0.22
        IVA.dot(top, dot[0], dot[1], iw * 0.075, glow=1.0)
        # cabeçalho
        dh = ImageDraw.Draw(top)
        logo(top, MX, 100, 40)
        dh.rectangle([0, 0, W * clamp(gt / total), 6], fill=rgba(OURO))
        fu = font("label", 24); u = "ciellotec.com"
        fx = MX if s["type"] in ("hook", "cta") else W - MX - tlen(u, fu, 3) - 30
        spaced(dh, (fx, 1475), u, fu, rgba(CINZA), 3)
        caption(top, s, lt, ds[i])
        fr.alpha_composite(top)
        ff.stdin.write(fr.convert("RGB").tobytes())
    ff.stdin.close(); ff.wait()
    if os.path.exists(wav): os.remove(wav)
    print(json.dumps({"out": out, "total": round(total, 2), "durations": [round(x, 2) for x in ds]}))

if __name__ == "__main__":
    main()
