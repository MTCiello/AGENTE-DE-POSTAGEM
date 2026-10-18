#!/usr/bin/env python3
"""
Gerador de reels da CIELLO — v3, na identidade visual oficial.

Identidade (manual de marca): Tinta #0d0d0d, Ouro #C8960A (acento, usar pouco), Teal #1693A5 (secundária),
Branco, Cinza #888888, Carvão #1a1a1a. Fundo papel #F5F5F5 com blocos diagonais em tinta.
Tipografia: Barlow Condensed Black (títulos), Barlow Condensed Light (linhas de apoio em cinza),
Playfair Display Black Italic em ouro (ênfase), DM Sans (texto corrido). Logo: nuvem + CIELLO espaçado.

Uso:
  python3 render_reel.py roteiro.json saida.mp4 [--total SEGUNDOS] [--silent]

Cenas do roteiro (JSON):
  hook: {"type":"hook","kicker":"...","pre":"linha fina","big":"PALAVRA GRANDE","accent":"frase em ouro","post":"linha fina","say":"fala"}
  item: {"type":"item","num":"1","tag":"DICA 1 DE 3","title":"...","body":"...","prompt":"...","say":"fala"}
  cta:  {"type":"cta","kicker":"...","pre":"...","big":"...","accent":"...","button":"QUERO ...","save":"SALVA ESSE VÍDEO","say":"fala"}
"""
import json, math, subprocess, sys, os, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
PAPER = (245, 245, 245)
INK = (13, 13, 13)
CARVAO = (26, 26, 26)
GOLD = (200, 150, 10)
TEAL = (22, 147, 165)
CINZA = (136, 136, 136)
CLARO = (170, 170, 170)
WHITE = (255, 255, 255)

MX = 92
SAFE_R = 140
TW = W - MX - SAFE_R
CAP_Y = 1560

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
FONTS = {
    "black": "barlow-condensed-latin-900-normal.woff",
    "xbold": "barlow-condensed-latin-800-normal.woff",
    "light": "barlow-condensed-latin-300-normal.woff",
    "thin": "barlow-condensed-latin-200-normal.woff",
    "serif": "playfair-display-latin-900-italic.woff",
    "sans": "dm-sans-latin-400-normal.woff",
    "sansm": "dm-sans-latin-500-normal.woff",
    "sansb": "dm-sans-latin-700-normal.woff",
}
_fc = {}
def font(name, size):
    size = max(8, int(round(size))); k = (name, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(os.path.join(FD, FONTS[name]), size)
    return _fc[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def spring(x):
    x = clamp(x)
    return 1.0 if x >= 1 else 1 - math.exp(-6 * x) * math.cos(9 * x)
def rgba(c, a=1.0): return (c[0], c[1], c[2], int(255 * clamp(a)))

def wrap(text, f, maxw, spacing=0):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if tlen(t, f, spacing) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def tlen(txt, f, spacing=0):
    return f.getlength(txt) + spacing * max(0, len(txt) - 1)

def spaced(d, xy, txt, f, fill, spacing):
    x, y = xy
    for ch in txt:
        d.text((x, y), ch, font=f, fill=fill); x += f.getlength(ch) + spacing

def fit_size(txt, fname, size, maxw, spacing=0):
    while size > 40 and tlen(txt, font(fname, size), spacing) > maxw: size -= 4
    return size

# ---------- logo (nuvem + CIELLO) ----------
_cloud_cache = {}
def cloud_icon(h, color):
    """nuvem em contorno, como no logo da CIELLO"""
    key = (h, color)
    if key in _cloud_cache: return _cloud_cache[key]
    S = 8; w = int(h * 1.6)
    big = Image.new("L", (w * S, h * S), 0); d = ImageDraw.Draw(big)
    U = h * S
    def circ(cx, cy, r): d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    circ(0.42 * U, 0.66 * U, 0.26 * U); circ(0.80 * U, 0.50 * U, 0.38 * U); circ(1.18 * U, 0.70 * U, 0.22 * U)
    d.rounded_rectangle([0.18 * U, 0.62 * U, 1.40 * U, 0.92 * U], radius=0.15 * U, fill=255)
    stroke = max(2, int(0.075 * U))
    inner = big.filter(ImageFilter.MinFilter(stroke * 2 + 1))
    ring = Image.fromarray(np.clip(np.array(big, dtype=np.int16) - np.array(inner, dtype=np.int16), 0, 255).astype(np.uint8))
    ring = ring.resize((w, h), Image.LANCZOS)
    im = Image.new("RGBA", (w, h), color + (0,)); im.putalpha(ring)
    _cloud_cache[key] = im
    return im

def draw_logo(layer, x, y, color, a=1.0, size=34):
    ic = cloud_icon(int(size * 1.0), color)
    if a < 1:
        ic = ic.copy(); ic.putalpha(ic.getchannel("A").point(lambda v: int(v * a)))
    layer.alpha_composite(ic, (int(x), int(y)))
    d = ImageDraw.Draw(layer)
    spaced(d, (x + ic.width + 14, y - size * 0.12), "CIELLO", font("xbold", size * 1.05), rgba(color, a), size * 0.22)

# ---------- fundo ----------
class Paper:
    def __init__(self):
        self.base = Image.new("RGBA", (W, H), PAPER + (255,))
        g = Image.new("L", (1200, 1200), 0)
        ImageDraw.Draw(g).ellipse([200, 200, 1000, 1000], fill=120)
        g = g.filter(ImageFilter.GaussianBlur(190))
        self.glow = Image.new("RGBA", g.size, (238, 214, 150, 0)); self.glow.putalpha(g.point(lambda v: int(v * 0.55)))
    def render(self, gt):
        fr = self.base.copy()
        fr.alpha_composite(self.glow, (int(260 + 120 * math.sin(gt * 0.35)), int(-200 + 140 * math.sin(gt * 0.27))))
        return fr

def corners(d, color):
    L, m, w = 46, 36, 3
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line([(x, y), (x + sx * L, y)], fill=color, width=w); d.line([(x, y), (x, y + sy * L)], fill=color, width=w)

# ---------- revelação de linha (texto sobe de dentro de uma máscara) ----------
def reveal_line(layer, x, y, txt, f, color, p, spacing=0, stroke=None):
    if p <= 0 or not txt: return
    bb = f.getbbox(txt + "Ág")
    h = int(bb[3] + 12); w = int(tlen(txt, f, spacing) + 30)
    li = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(li)
    if stroke:
        d.text((4, 0), txt, font=f, fill=stroke[0], stroke_width=stroke[1], stroke_fill=stroke[2])
    elif spacing: spaced(d, (4, 0), txt, f, color, spacing)
    else: d.text((4, 0), txt, font=f, fill=color)
    off = int(h * (1 - eo(p)))
    if h - off <= 0: return
    layer.alpha_composite(li.crop((0, 0, w, h - off)), (int(x - 4), int(y + off)))

def kicker(layer, x, y, txt, t, color=GOLD):
    d = ImageDraw.Draw(layer)
    p = eo(t / 0.45)
    d.line([(x, y + 17), (x + 64 * p, y + 17)], fill=rgba(color), width=3)
    f = font("sansm", 28)
    a = clamp((t - 0.15) / 0.3)
    spaced(d, (x + 84 + 20 * (1 - a), y), txt.upper(), f, rgba(color, a), 7)

# ---------- cenas ----------
def ink_bottom(d, t, y_left=1390, y_right=1300, enter=True):
    p = eio(t / 0.6) if enter else 1
    dy = (H - y_right) * (1 - p)
    d.polygon([(0, y_left + dy), (W, y_right + dy), (W, H), (0, H)], fill=INK + (255,))
    d.line([(0, y_left + dy - 6), (W, y_right + dy - 6)], fill=rgba(TEAL, p), width=4)

def scene_hook(layer, sc, t, dur, idx, n):
    d = ImageDraw.Draw(layer)
    ink_bottom(d, t)
    y = 430
    if sc.get("kicker"): kicker(layer, MX, y, sc["kicker"], t); y += 80
    if sc.get("pre"):
        f = font("light", fit_size(sc["pre"].upper(), "light", 128, TW))
        for ln in wrap(sc["pre"].upper(), f, TW):
            reveal_line(layer, MX, y, ln, f, rgba(CLARO), (t - 0.15) / 0.5); y += int(f.size * 0.98)
    if sc.get("big"):
        sz = fit_size(sc["big"].upper(), "black", 230, TW)
        f = font("black", sz)
        for k, ln in enumerate(wrap(sc["big"].upper(), f, TW)):
            reveal_line(layer, MX, y, ln, f, rgba(INK), (t - 0.35 - 0.12 * k) / 0.5); y += int(sz * 0.95)
    if sc.get("accent"):
        f = font("serif", fit_size(sc["accent"], "serif", 96, TW))
        for k, ln in enumerate(wrap(sc["accent"], f, TW)):
            reveal_line(layer, MX, y + 6, ln, f, rgba(GOLD), (t - 0.75 - 0.1 * k) / 0.5); y += int(f.size * 1.18)
    if sc.get("post"):
        f = font("light", fit_size(sc["post"].upper(), "light", 92, TW))
        for ln in wrap(sc["post"].upper(), f, TW):
            reveal_line(layer, MX, y, ln, f, rgba(CLARO), (t - 1.0) / 0.5); y += int(f.size * 1.0)

def scene_item(layer, sc, t, dur, idx, n):
    d = ImageDraw.Draw(layer)
    # bloco de tinta diagonal (como nos posts da marca)
    p = eio(t / 0.55)
    bx = -W * 0.9 * (1 - p)
    poly = [(bx, 0), (bx + W * 0.80, 0), (bx + W * 0.63, 860), (bx, 860)]
    d.polygon(poly, fill=INK + (255,))
    d.line([(bx + W * 0.80 + 8, 0), (bx + W * 0.63 + 8, 860)], fill=rgba(TEAL, p), width=6)
    # número gigante em contorno
    sz = 560
    fn = font("black", sz * (0.85 + 0.15 * spring((t - 0.15) / 0.6)))
    na = clamp((t - 0.15) / 0.3)
    nl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(nl).text((MX - 20 + bx * 0.2, 150), sc["num"], font=fn, fill=INK + (255,), stroke_width=4, stroke_fill=rgba((110, 110, 110), na))
    if na > 0: layer.alpha_composite(nl)
    if sc.get("tag"): kicker(layer, MX, 780, sc["tag"], t - 0.3)
    # título e corpo na área clara
    y = 930
    f = font("black", 112)
    tl = wrap(sc["title"].upper(), f, TW)
    if len(tl) > 2: f = font("black", 96); tl = wrap(sc["title"].upper(), f, TW)
    for k, ln in enumerate(tl):
        reveal_line(layer, MX, y, ln, f, rgba(INK), (t - 0.35 - 0.1 * k) / 0.45); y += int(f.size * 0.96)
    y += 14
    if sc.get("body"):
        fb = font("sans", 40)
        ba = eo((t - 0.7) / 0.35)
        for k, ln in enumerate(wrap(sc["body"], fb, TW)):
            d.text((MX, y + 18 * (1 - ba) + k * 54), ln, font=fb, fill=rgba((95, 95, 95), ba))
        y += len(wrap(sc["body"], fb, TW)) * 54 + 34
    if sc.get("prompt"):
        st = 0.95
        pa = eo((t - st) / 0.35); sy = 36 * (1 - pa)
        fp = font("sansm", 36)
        lines_all = wrap(sc["prompt"], fp, TW - 150)
        bh = len(lines_all) * 50 + 92
        x0, y0, x1 = MX, y + sy, W - SAFE_R
        d.rectangle([x0, y0, x1, y0 + bh], fill=rgba(CARVAO, pa))
        d.rectangle([x0, y0, x0 + 6, y0 + bh], fill=rgba(GOLD, pa))
        spaced(d, (x0 + 34, y0 + 18), "VOCÊ PEDE", font("sansb", 22), rgba(GOLD, pa), 5)
        win = max(0.9, min(2.0, dur - st - 1.4))
        nchar = len(sc["prompt"]); k = int(clamp((t - st - 0.25) / win) * nchar)
        typed = sc["prompt"][:k]
        tl2 = wrap(typed, fp, TW - 150) if typed else [""]
        for j, ln in enumerate(tl2):
            d.text((x0 + 34, y0 + 52 + j * 50), ln, font=fp, fill=rgba(WHITE, pa))
        if k < nchar and int(t * 3) % 2 == 0:
            lw = fp.getlength(tl2[-1]); cy = y0 + 52 + (len(tl2) - 1) * 50
            d.rectangle([x0 + 37 + lw, cy + 4, x0 + 41 + lw, cy + 42], fill=rgba(TEAL, pa))
        cx, cyy = x1 - 56, y0 + bh / 2
        done = st + 0.25 + win
        if t < done:
            d.ellipse([cx - 30, cyy - 30, cx + 30, cyy + 30], outline=rgba(GOLD, pa), width=3)
            d.polygon([(cx - 8, cyy - 13), (cx - 8, cyy + 13), (cx + 14, cyy)], fill=rgba(GOLD, pa))
        else:
            q = spring((t - done) / 0.4); r = 30 * clamp(q, 0, 1.2)
            d.ellipse([cx - r, cyy - r, cx + r, cyy + r], fill=GOLD + (255,))
            c = clamp((t - done) / 0.3)
            pts = [(cx - 13, cyy + 1), (cx - 3, cyy + 11), (cx + 14, cyy - 10)]
            if c > 0:
                mid = (pts[0][0] + (pts[1][0] - pts[0][0]) * min(1, c * 2), pts[0][1] + (pts[1][1] - pts[0][1]) * min(1, c * 2))
                d.line([pts[0], mid], fill=INK + (255,), width=5)
                if c > 0.5:
                    e = (c - 0.5) * 2
                    d.line([pts[1], (pts[1][0] + (pts[2][0] - pts[1][0]) * e, pts[1][1] + (pts[2][1] - pts[1][1]) * e)], fill=INK + (255,), width=5)

def scene_cta(layer, sc, t, dur, idx, n):
    d = ImageDraw.Draw(layer)
    ink_bottom(d, t, 1420, 1330)
    y = 400
    if sc.get("kicker"): kicker(layer, MX, y, sc["kicker"], t); y += 80
    if sc.get("pre"):
        f = font("light", fit_size(sc["pre"].upper(), "light", 112, TW))
        for ln in wrap(sc["pre"].upper(), f, TW):
            reveal_line(layer, MX, y, ln, f, rgba(CLARO), (t - 0.1) / 0.45); y += int(f.size * 0.98)
    if sc.get("big"):
        sz = fit_size(sc["big"].upper(), "black", 190, TW); f = font("black", sz)
        for k, ln in enumerate(wrap(sc["big"].upper(), f, TW)):
            reveal_line(layer, MX, y, ln, f, rgba(INK), (t - 0.3 - 0.1 * k) / 0.45); y += int(sz * 0.95)
    if sc.get("accent"):
        f = font("serif", fit_size(sc["accent"], "serif", 84, TW))
        for k, ln in enumerate(wrap(sc["accent"], f, TW)):
            reveal_line(layer, MX, y + 6, ln, f, rgba(GOLD), (t - 0.6) / 0.45); y += int(f.size * 1.2)
    y += 40
    # botão principal (retangular, como nos posts)
    bp = eo((t - 0.9) / 0.4)
    if bp > 0 and sc.get("button"):
        fb = font("xbold", 46); lbl = sc["button"].upper(); sp = 4
        bw = tlen(lbl, fb, sp) + 110; bh = 104
        pulse = 1 + 0.03 * math.sin(max(0, t - 1.4) * 6)
        x0 = MX; y0 = y + 30 * (1 - bp)
        d.rectangle([x0, y0, x0 + bw * pulse, y0 + bh], fill=rgba(INK, bp))
        spaced(d, (x0 + 55, y0 + 24), lbl, fb, rgba(WHITE, bp), sp)
        ax = x0 + bw * pulse + 36 + 12 * math.sin(t * 7)
        d.line([(ax, y0 + bh / 2), (ax + 70, y0 + bh / 2)], fill=rgba(GOLD, bp), width=4)
        d.polygon([(ax + 70, y0 + bh / 2 - 12), (ax + 88, y0 + bh / 2), (ax + 70, y0 + bh / 2 + 12)], fill=rgba(GOLD, bp))
        y = y0 + bh + 34
    sp2 = eo((t - 1.25) / 0.4)
    if sp2 > 0 and sc.get("save"):
        fs = font("sansb", 30)
        lbl = sc["save"].upper()
        bw = tlen(lbl, fs, 4) + 120
        d.rectangle([MX, y, MX + bw, y + 74], outline=rgba(INK, sp2), width=3)
        # ícone salvar
        bx, by = MX + 34, y + 20
        d.polygon([(bx, by), (bx + 24, by), (bx + 24, by + 34), (bx + 12, by + 25), (bx, by + 34)], fill=rgba(GOLD, sp2))
        spaced(d, (MX + 80, y + 19), lbl, fs, rgba(INK, sp2), 4)

SCENES = {"hook": scene_hook, "item": scene_item, "cta": scene_cta}

# ---------- legendas ----------
def chunks(say, n=3):
    w = say.split(); return [" ".join(w[i:i + n]) for i in range(0, len(w), n)] if w else []

def draw_caption(layer, sc, t, dur):
    say = sc.get("say")
    if not say: return
    cs = chunks(say); lens = [len(c) + 2 for c in cs]; tot = sum(lens)
    span = max(0.1, dur - 0.1); acc = 0.05; idx = len(cs) - 1; cst = acc
    for i, L in enumerate(lens):
        seg = span * L / tot
        if t < acc + seg: idx = i; cst = acc; break
        acc += seg
    txt = cs[idx]
    q = spring((t - cst) / 0.3); s = 0.88 + 0.12 * clamp(q, 0, 1.1)
    f = font("sansb", 54 * s); tw = f.getlength(txt)
    d = ImageDraw.Draw(layer)
    x = (W - tw) / 2 - 20; y = CAP_Y
    d.rectangle([x - 26, y - 12, x + tw + 26, y + 74 * s], fill=(26, 26, 26, 235))
    parts = txt.rsplit(" ", 1)
    if len(parts) == 2:
        d.text((x, y), parts[0] + " ", font=f, fill=WHITE + (255,))
        d.text((x + f.getlength(parts[0] + " "), y), parts[1], font=f, fill=GOLD + (255,))
    else:
        d.text((x, y), txt, font=f, fill=GOLD + (255,))

# ---------- cabeçalho ----------
def draw_header(layer, sc, idx, n, gt, total, lt):
    d = ImageDraw.Draw(layer)
    d.rectangle([0, 0, W * clamp(gt / total), 7], fill=GOLD + (255,))
    on_ink = sc["type"] == "item" and lt > 0.3
    col = WHITE if on_ink else INK
    draw_logo(layer, MX, 110, col, 1.0, 34)
    cnt = f"{idx + 1:02d} · {n:02d}"
    fc = font("sansm", 26)
    d.text((W - MX - fc.getlength(cnt) - 20, 112), cnt, font=fc, fill=rgba(CINZA))
    corners(d, rgba((185, 185, 185)))
    if sc["type"] != "item":
        fu = font("sansm", 24); u = "CIELLOTEC.COM"
        spaced(d, (W - MX - tlen(u, fu, 4) - 20, 1440 if sc["type"] == "cta" else 1410), u, fu, rgba((120, 120, 120)), 4)

# ---------- áudio local (fallback) ----------
def synth_audio(path, total, sr=44100):
    n = int(total * sr); out = np.zeros(n); beat = 60 / 118
    for b in np.arange(0, total, beat):
        i0 = int(b * sr); L = min(int(0.35 * sr), n - i0); x = np.arange(L) / sr
        out[i0:i0 + L] += 0.9 * np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-x * 30)) / sr) * np.exp(-x * 9)
    out = np.tanh(out); out = out / max(1e-6, np.max(np.abs(out))) * 0.7
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes((out * 32767).astype(np.int16).tobytes())

def plan(scenes, total):
    if total is None: return [s.get("dur", 4.0) for s in scenes]
    w = [max(8, len(s.get("say", ""))) for s in scenes]
    u = total - 0.6; ds = [u * x / sum(w) for x in w]; ds[-1] += 0.6
    return ds

def main():
    a = sys.argv[1:]; silent = "--silent" in a; total = None
    if "--total" in a: total = float(a[a.index("--total") + 1])
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] != "--total")]
    cfg = json.load(open(pos[0], encoding="utf-8")); out = pos[1]
    sc = cfg["scenes"]; ds = plan(sc, total); total = sum(ds)
    st, acc = [], 0.0
    for x in ds: st.append(acc); acc += x
    bg = Paper(); nf = int(round(total * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    wav = out + ".wav"
    if not silent: synth_audio(wav, total); cmd += ["-i", wav, "-c:a", "aac", "-b:a", "160k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = len(sc)
    for fi in range(nf):
        gt = fi / FPS
        i = max(k for k in range(n) if st[k] <= gt + 1e-9); lt = gt - st[i]
        fr = bg.render(gt)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        SCENES[sc[i]["type"]](layer, sc[i], lt, ds[i], i, n)
        fr.alpha_composite(layer)
        top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_header(top, sc[i], i, n, gt, total, lt)
        draw_caption(top, sc[i], lt, ds[i])
        fr.alpha_composite(top)
        # transição: painel de tinta diagonal varrendo a tela
        if i > 0 and lt < 0.28:
            k = eio(lt / 0.28); dd = ImageDraw.Draw(fr)
            x = -500 + 2900 * k
            dd.polygon([(x - 950, 0), (x, 0), (x - 320, H), (x - 1270, H)], fill=INK + (255,))
            dd.line([(x, 0), (x - 320, H)], fill=GOLD + (255,), width=8)
        ff.stdin.write(fr.convert("RGB").tobytes())
    ff.stdin.close(); ff.wait()
    if os.path.exists(wav): os.remove(wav)
    print(json.dumps({"out": out, "total": round(total, 2), "durations": [round(x, 2) for x in ds]}))

if __name__ == "__main__":
    main()
