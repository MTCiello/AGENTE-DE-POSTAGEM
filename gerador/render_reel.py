#!/usr/bin/env python3
"""
Gerador de reels da Ciello (v2 — animado, com legendas sincronizadas).

Uso:
  python3 render_reel.py roteiro.json saida.mp4 [--total SEGUNDOS] [--silent]

  --total   distribui as cenas para somar exatamente esse tempo (ex.: duração da narração),
            proporcional ao tamanho do texto falado ("say") de cada cena.
  --silent  gera o vídeo sem áudio (a narração e a trilha entram depois, no vidIQ compose).

Roteiro (JSON):
{
  "scenes": [
    {"type":"hook","kicker":"DICA DE IA","text":"...","highlight":["palavra"],"sub":"...","say":"fala da narração"},
    {"type":"item","num":"1","title":"...","body":"...","prompt":"...","say":"..."},
    {"type":"cta","text":"...","sub":"...","say":"..."}
  ]
}
"""
import json, math, subprocess, sys, os, wave, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
BG = (22, 22, 22)
FG = (245, 245, 245)
TEAL = (22, 147, 165)
TEAL_L = (64, 196, 214)
MUTED = (160, 160, 160)
CARD = (34, 34, 34)
BORDER = (62, 62, 62)
RED = (230, 72, 72)
YELLOW = (245, 196, 66)

MX = 96
SAFE_RIGHT = 150
TEXT_W = W - MX - SAFE_RIGHT
CAPTION_Y = 1500

FP = "/usr/share/fonts/truetype/google-fonts/"
FI = "/usr/share/fonts/opentype/inter/"
_fc = {}
def font(name, size):
    size = max(8, int(round(size)))
    k = (name, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype({
            "bold": FP + "Poppins-Bold.ttf", "semi": FP + "Poppins-Medium.ttf",
            "reg": FI + "Inter-Regular.otf", "med": FI + "Inter-Medium.otf",
            "black": FI + "Inter-Black.otf",
        }[name], size)
    return _fc[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in(x): x = clamp(x); return x ** 3
def spring(x):
    """overshoot elástico 0→1"""
    x = clamp(x)
    if x >= 1: return 1.0
    return 1 - math.exp(-6 * x) * math.cos(10 * x)
def rgba(c, a): return (c[0], c[1], c[2], int(255 * clamp(a)))

def wrap(text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if f.getlength(t) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

# ---------------- fundo ----------------
class Background:
    def __init__(self, seed=3):
        base = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(base)
        for y in range(0, H, 54):
            for x in range(0, W, 54):
                d.ellipse([x - 1.6, y - 1.6, x + 1.6, y + 1.6], fill=(42, 42, 42))
        self.base = base.convert("RGBA")
        g = Image.new("L", (1400, 1400), 0)
        ImageDraw.Draw(g).ellipse([250, 250, 1150, 1150], fill=160)
        g = g.filter(ImageFilter.GaussianBlur(180))
        self.glow = Image.new("RGBA", g.size, TEAL + (0,)); self.glow.putalpha(g.point(lambda v: int(v * 0.6)))
        g2 = Image.new("L", (900, 900), 0)
        ImageDraw.Draw(g2).ellipse([150, 150, 750, 750], fill=120)
        g2 = g2.filter(ImageFilter.GaussianBlur(140))
        self.glow2 = Image.new("RGBA", g2.size, TEAL_L + (0,)); self.glow2.putalpha(g2.point(lambda v: int(v * 0.35)))
        rnd = random.Random(seed)
        self.parts = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(18, 60), rnd.uniform(2, 5), rnd.uniform(0.12, 0.38))
                      for _ in range(46)]

    def render(self, gt, pulse):
        fr = self.base.copy()
        fr.alpha_composite(self.glow, (int(-260 + 160 * math.sin(gt * 0.45)), int(220 + 280 * math.sin(gt * 0.31))))
        fr.alpha_composite(self.glow2, (int(520 + 120 * math.cos(gt * 0.6)), int(1100 + 160 * math.sin(gt * 0.5))))
        d = ImageDraw.Draw(fr)
        for (x, y, sp, r, a) in self.parts:
            yy = (y - gt * sp) % H
            xx = x + 14 * math.sin(gt * 0.8 + y)
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=rgba(TEAL_L, a * (0.7 + 0.3 * pulse)))
        return fr

# ---------------- elementos ----------------
def draw_chrome(d, gt, total):
    d.rounded_rectangle([MX, 150, W - MX, 160], radius=5, fill=(50, 50, 50, 255))
    d.rounded_rectangle([MX, 150, MX + (W - 2 * MX) * clamp(gt / total), 160], radius=5, fill=TEAL + (255,))
    f = font("bold", 40)
    d.text((MX, 196), "ciello", font=f, fill=FG + (255,))
    tw = f.getlength("ciello")
    d.ellipse([MX + tw + 8, 226, MX + tw + 20, 238], fill=TEAL + (255,))
    fh = font("med", 30)
    d.text((W - MX - fh.getlength("@ciellotec"), 204), "@ciellotec", font=fh, fill=MUTED + (255,))

def text_scaled(layer, xy, txt, fname, size, scale, color, anchor_center=True):
    """desenha texto com escala (pop) a partir do centro da palavra"""
    d = ImageDraw.Draw(layer)
    f0 = font(fname, size)
    w0 = f0.getlength(txt)
    fs = font(fname, size * max(0.05, scale))
    ws = fs.getlength(txt)
    x, y = xy
    if anchor_center:
        x = x + (w0 - ws) / 2
        y = y + size * (1 - scale) * 0.55
    d.text((x, y), txt, font=fs, fill=color)

def kinetic_words(layer, words_spec, t, x0, y0, size, maxw, hl, start=0.15, step=0.09, out=1.0, fname="bold"):
    """palavras entrando uma a uma com pop elástico; retorna (y final, último tempo)"""
    d = ImageDraw.Draw(layer)
    f = font(fname, size)
    lh = int(size * 1.17); sp = f.getlength(" ")
    lines, cur, cw = [], [], 0
    for w in words_spec:
        ww = f.getlength(w); pad = 26 if w.lower().strip(".,!?:") in hl else 0
        need = ww + pad + (sp if cur else 0)
        if cur and cw + need > maxw:
            lines.append(cur); cur, cw = [], 0; need = ww + pad
        cur.append((w, ww, pad)); cw += need
    if cur: lines.append(cur)
    i = 0
    for li, line in enumerate(lines):
        x = x0
        for (w, ww, pad) in line:
            st = start + i * step
            p = spring((t - st) / 0.45)
            a = clamp((t - st) / 0.12) * out
            y = y0 + li * lh
            if a > 0:
                if pad:
                    bw = (ww + pad) * clamp(p, 0, 1.15)
                    cx = x + (ww + pad) / 2 - 6
                    d.rounded_rectangle([cx - bw / 2, y + size * 0.1, cx + bw / 2, y + size * 1.12], radius=20,
                                        fill=rgba(TEAL, a))
                    text_scaled(layer, (x + pad / 2 - 6, y), w, fname, size, p, rgba(FG, a))
                else:
                    text_scaled(layer, (x, y), w, fname, size, p, rgba(FG, a))
            x += ww + pad + sp; i += 1
    return y0 + len(lines) * lh, start + i * step

def ring(d, cx, cy, r, prog, width, color):
    if prog <= 0: return
    d.arc([cx - r, cy - r, cx + r, cy + r], start=-90, end=-90 + 360 * clamp(prog), fill=color, width=width)

def check_icon(d, cx, cy, s, p, color):
    if p <= 0: return
    pts = [(cx - s * 0.45, cy), (cx - s * 0.12, cy + s * 0.33), (cx + s * 0.5, cy - s * 0.35)]
    seg1 = clamp(p / 0.4); seg2 = clamp((p - 0.4) / 0.6)
    a = pts[0]; b = (pts[0][0] + (pts[1][0] - pts[0][0]) * seg1, pts[0][1] + (pts[1][1] - pts[0][1]) * seg1)
    d.line([a, b], fill=color, width=int(s * 0.16), joint="curve")
    if seg2 > 0:
        c = (pts[1][0] + (pts[2][0] - pts[1][0]) * seg2, pts[1][1] + (pts[2][1] - pts[1][1]) * seg2)
        d.line([pts[1], c], fill=color, width=int(s * 0.16), joint="curve")

def draw_bookmark(d, x, y, s, c):
    d.polygon([(x, y), (x + s, y), (x + s, y + s * 1.3), (x + s / 2, y + s * 0.95), (x, y + s * 1.3)], fill=c)

# ---------------- cenas ----------------
def render_hook(layer, sc, t, dur):
    d = ImageDraw.Draw(layer)
    out = clamp((dur - t) / 0.15)
    kick = sc.get("kicker", "DICA DE IA")
    fk = font("bold", 34); kw = fk.getlength(kick) + 64
    kp = spring(t / 0.5); ka = clamp(t / 0.15) * out
    ky = 560
    bw = kw * clamp(kp, 0, 1.1)
    d.rounded_rectangle([MX, ky, MX + bw, ky + 72], radius=36, fill=rgba(TEAL, ka))
    if kp > 0.6:
        d.ellipse([MX + 22, ky + 28, MX + 38, ky + 44], fill=rgba(YELLOW, ka))
        d.text((MX + 48, ky + 14), kick, font=fk, fill=rgba(FG, ka * clamp((kp - 0.6) / 0.3)))
    size = sc.get("size", 108)
    hl = set(w.lower().strip(".,!?:") for w in sc.get("highlight", []))
    yend, tend = kinetic_words(layer, sc["text"].split(), t, MX, 680, size, TEXT_W, hl, start=0.2, step=0.1, out=out)
    if sc.get("sub"):
        fs = font("med", 46)
        sa = ease_out((t - tend - 0.05) / 0.35) * out
        dy = 30 * (1 - ease_out((t - tend - 0.05) / 0.35))
        for k, ln in enumerate(wrap(sc["sub"], fs, TEXT_W)):
            d.text((MX, yend + 40 + dy + k * 60), ln, font=fs, fill=rgba(MUTED, sa))
    # sublinhado animado
    ul = ease_out((t - tend) / 0.4) * out
    if ul > 0:
        d.rounded_rectangle([MX, yend + 8, MX + 260 * ul, yend + 18], radius=5, fill=rgba(YELLOW, ul))

def render_item(layer, sc, t, dur):
    d = ImageDraw.Draw(layer)
    out = clamp((dur - t) / 0.15)
    # número com anel
    cx, cy, r = MX + 110, 560, 104
    rp = ease_out(t / 0.7)
    ring(d, cx, cy, r, rp, 12, rgba(TEAL, out))
    d.ellipse([cx - r + 18, cy - r + 18, cx + r - 18, cy + r - 18], fill=rgba((30, 50, 54), out * clamp(t / 0.2)))
    np_ = spring((t - 0.05) / 0.45)
    fnum = font("black", 150)
    fsz = 150 * max(0.05, np_)
    fn = font("black", fsz)
    nw = fn.getlength(sc["num"])
    bb = fn.getbbox(sc["num"])
    d.text((cx - nw / 2, cy - (bb[1] + bb[3]) / 2), sc["num"], font=fn, fill=rgba(FG, clamp(t / 0.12) * out))
    # título palavra por palavra
    hl = set(w.lower().strip(".,!?:") for w in sc.get("highlight", []))
    yend, tend = kinetic_words(layer, sc["title"].split(), t, MX, 720, 82, TEXT_W, hl, start=0.25, step=0.07, out=out)
    y = yend + 18
    if sc.get("body"):
        fb = font("med", 44)
        ba = ease_out((t - tend) / 0.3) * out
        dy = 24 * (1 - ease_out((t - tend) / 0.3))
        bl = wrap(sc["body"], fb, TEXT_W)
        for k, ln in enumerate(bl):
            d.text((MX, y + dy + k * 60), ln, font=fb, fill=rgba(MUTED, ba))
        y += len(bl) * 60 + 44
    if sc.get("prompt"):
        st = tend + 0.2
        pa = ease_out((t - st) / 0.3) * out
        sy = 40 * (1 - ease_out((t - st) / 0.35))
        fl = font("bold", 30)
        d.text((MX, y + sy), "VOCÊ PEDE:", font=fl, fill=rgba(TEAL_L, pa))
        fp = font("reg", 40)
        bx0, by0 = MX, y + 50 + sy
        full = wrap(sc["prompt"], fp, TEXT_W - 140)
        bh = len(full) * 54 + 60
        d.rounded_rectangle([bx0, by0, W - SAFE_RIGHT, by0 + bh], radius=30,
                            fill=rgba(CARD, pa), outline=rgba(TEAL if t > st + 0.3 else BORDER, pa), width=3)
        n_all = len(sc["prompt"])
        type_win = max(0.9, min(2.2, dur - (st - 0) - 1.3))
        n = int(clamp((t - st - 0.2) / type_win) * n_all)
        typed = sc["prompt"][:n]
        tl = wrap(typed, fp, TEXT_W - 140) if typed else [""]
        for k, ln in enumerate(tl):
            d.text((bx0 + 32, by0 + 30 + k * 54), ln, font=fp, fill=rgba(FG, pa))
        if n < n_all and int(t * 3) % 2 == 0:
            lw = fp.getlength(tl[-1]); cyy = by0 + 30 + (len(tl) - 1) * 54
            d.rectangle([bx0 + 36 + lw, cyy + 6, bx0 + 41 + lw, cyy + 48], fill=rgba(TEAL_L, pa))
        # botão enviar → check
        bx, byy = W - SAFE_RIGHT - 60, by0 + bh / 2
        done_t = st + 0.2 + type_win
        if t < done_t:
            d.ellipse([bx - 34, byy - 34, bx + 34, byy + 34], fill=rgba(TEAL, pa))
            d.polygon([(bx - 10, byy - 16), (bx - 10, byy + 16), (bx + 16, byy)], fill=rgba(FG, pa))
        else:
            cp = spring((t - done_t) / 0.4)
            rr = 34 * clamp(cp, 0, 1.2)
            d.ellipse([bx - rr, byy - rr, bx + rr, byy + rr], fill=rgba((46, 170, 110), out))
            check_icon(d, bx, byy, 40, clamp((t - done_t) / 0.35), rgba(FG, out))

def render_cta(layer, sc, t, dur):
    d = ImageDraw.Draw(layer)
    hl = set(w.lower().strip(".,!?:") for w in sc.get("highlight", []))
    yend, tend = kinetic_words(layer, sc["text"].split(), t, MX, 640, sc.get("size", 96), TEXT_W, hl, start=0.1, step=0.08)
    y = yend + 30
    if sc.get("sub"):
        fs = font("med", 46)
        sa = ease_out((t - tend) / 0.35)
        for k, ln in enumerate(wrap(sc["sub"], fs, TEXT_W)):
            d.text((MX, y + 24 * (1 - sa) + k * 62), ln, font=fs, fill=rgba(MUTED, sa))
        y += len(wrap(sc["sub"], fs, TEXT_W)) * 62 + 64
    bp = spring((t - tend - 0.25) / 0.5)
    if bp > 0:
        pulse = 1 + 0.045 * math.sin(max(0, t - tend - 0.8) * 7)
        fb = font("bold", 42)
        label = sc.get("save_label", "Salva pra testar depois")
        bw = (fb.getlength(label) + 150) * clamp(bp, 0, 1.1) * pulse
        bh = 104 * pulse
        d.rounded_rectangle([MX, y, MX + bw, y + bh], radius=bh / 2, fill=TEAL + (255,))
        if bp > 0.7:
            draw_bookmark(d, MX + 44, y + bh / 2 - 26, 34, YELLOW + (255,))
            d.text((MX + 104, y + bh / 2 - 30), label, font=fb, fill=FG + (255,))
        # setinha apontando
        ax = MX + bw + 40 + 14 * math.sin(t * 8)
        d.polygon([(ax + 40, y + bh / 2 - 26), (ax + 40, y + bh / 2 + 26), (ax, y + bh / 2)], fill=YELLOW + (255,))
    tga = ease_out((t - tend - 0.8) / 0.4)
    d.text((MX, y + 170), sc.get("tagline", "Ciello · Tecnologia que eleva"), font=font("semi", 36), fill=rgba(MUTED, tga))

RENDER = {"hook": render_hook, "item": render_item, "cta": render_cta}

# ---------------- legendas ----------------
def caption_chunks(say, n=3):
    words = say.split(); return [" ".join(words[i:i + n]) for i in range(0, len(words), n)] if words else []

def draw_caption(layer, sc, t, dur):
    say = sc.get("say");
    if not say: return
    chunks = caption_chunks(say, 3)
    lead = 0.08
    span = max(0.1, dur - lead - 0.05)
    # tempo proporcional ao nº de caracteres
    lens = [len(c) + 2 for c in chunks]; tot = sum(lens)
    acc = lead; idx = len(chunks) - 1; cst = acc
    for i, L in enumerate(lens):
        seg = span * L / tot
        if t < acc + seg: idx = i; cst = acc; break
        acc += seg
    txt = chunks[idx]
    f = font("bold", 56)
    tw = f.getlength(txt)
    p = spring((t - cst) / 0.3)
    s = 0.85 + 0.15 * clamp(p, 0, 1.1)
    fs = font("bold", 56 * s); tws = fs.getlength(txt)
    d = ImageDraw.Draw(layer)
    x = (W - tws) / 2 - 20; y = CAPTION_Y
    d.rounded_rectangle([x - 26, y - 14, x + tws + 26, y + 76 * s], radius=22, fill=(0, 0, 0, 170))
    # última palavra em destaque
    parts = txt.rsplit(" ", 1)
    if len(parts) == 2:
        d.text((x, y), parts[0] + " ", font=fs, fill=FG + (255,))
        d.text((x + fs.getlength(parts[0] + " "), y), parts[1], font=fs, fill=YELLOW + (255,))
    else:
        d.text((x, y), txt, font=fs, fill=YELLOW + (255,))

# ---------------- áudio (fallback local) ----------------
def synth_audio(path, total, cuts, bpm=118, sr=44100):
    n = int(total * sr); out = np.zeros(n); beat = 60 / bpm
    for b in np.arange(0, total, beat):
        i0 = int(b * sr); L = min(int(0.35 * sr), n - i0); x = np.arange(L) / sr
        f = 50 + 90 * np.exp(-x * 30)
        out[i0:i0 + L] += 0.9 * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-x * 9)
    fo = int(0.8 * sr); out[-fo:] *= np.linspace(1, 0, fo)
    out = np.tanh(out); out = out / max(1e-6, np.max(np.abs(out))) * 0.7
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes((out * 32767).astype(np.int16).tobytes())

# ---------------- principal ----------------
def plan_durations(scenes, total):
    if total is None:
        return [s.get("dur", 4.0) for s in scenes]
    w = [max(8, len(s.get("say", "")) ) for s in scenes]
    # cena final ganha 0.6s extra de respiro
    usable = total - 0.6
    durs = [usable * x / sum(w) for x in w]
    durs[-1] += 0.6
    return durs

def main():
    args = sys.argv[1:]
    silent = "--silent" in args
    total = None
    if "--total" in args:
        total = float(args[args.index("--total") + 1])
    pos = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] != "--total")]
    script_path, out_path = pos[0], pos[1]
    cfg = json.load(open(script_path, encoding="utf-8"))
    scenes = cfg["scenes"]
    durs = plan_durations(scenes, total)
    total = sum(durs)
    starts, acc = [], 0.0
    for dd in durs: starts.append(acc); acc += dd
    bg = Background()
    nframes = int(round(total * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-"]
    wav = out_path + ".wav"
    if not silent:
        synth_audio(wav, total, starts[1:]); cmd += ["-i", wav, "-c:a", "aac", "-b:a", "160k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    TR = 0.22
    for fi in range(nframes):
        gt = fi / FPS
        si = max(i for i in range(len(scenes)) if starts[i] <= gt + 1e-9)
        lt = gt - starts[si]
        pulse = 0.5 + 0.5 * math.cos(gt * 2 * math.pi * 118 / 60)
        frame = bg.render(gt, pulse)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        RENDER[scenes[si]["type"]](layer, scenes[si], lt, durs[si])
        # push de entrada
        if si > 0 and lt < TR:
            k = ease_out(lt / TR)
            shifted = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            shifted.paste(layer, (int(W * 0.35 * (1 - k)), 0)); layer = shifted
        frame.alpha_composite(layer)
        top = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dt = ImageDraw.Draw(top)
        draw_chrome(dt, gt, total)
        draw_caption(top, scenes[si], lt, durs[si])
        frame.alpha_composite(top)
        if si > 0 and lt < 0.16:
            k = ease_out(lt / 0.16)
            dw = ImageDraw.Draw(frame)
            dw.rectangle([W * k, 0, W, H], fill=TEAL + (255,))
            dw.rectangle([W * k - 30, 0, W * k, H], fill=YELLOW + (255,))
        ff.stdin.write(frame.convert("RGB").tobytes())
    ff.stdin.close(); ff.wait()
    if os.path.exists(wav): os.remove(wav)
    print(json.dumps({"out": out_path, "total": round(total, 2), "durations": [round(x, 2) for x in durs]}))

if __name__ == "__main__":
    main()
