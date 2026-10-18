#!/usr/bin/env python3
"""
Gerador de reels da Ciello.
Uso: python3 render_reel.py roteiro.json saida.mp4

O roteiro é um JSON com uma lista de cenas. Tipos de cena:
  hook  -> {"type":"hook","kicker":"DICA DE IA","text":"...","highlight":["palavra"],"dur":3.2}
  item  -> {"type":"item","num":"1","title":"...","body":"...","prompt":"...","dur":5}
  cta   -> {"type":"cta","text":"...","sub":"...","dur":4}
"""
import json, math, subprocess, sys, os, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
BG = (22, 22, 22)          # #161616
FG = (245, 245, 245)       # #F5F5F5
TEAL = (22, 147, 165)      # #1693A5
MUTED = (150, 150, 150)
CARD = (32, 32, 32)
BORDER = (58, 58, 58)
RED = (230, 72, 72)
YELLOW = (245, 196, 66)

MX = 96                      # margem lateral
SAFE_RIGHT = 150             # área dos ícones do Instagram à direita
TEXT_W = W - MX - SAFE_RIGHT

FONT_DIR_P = "/usr/share/fonts/truetype/google-fonts/"
FONT_DIR_I = "/usr/share/fonts/opentype/inter/"
_font_cache = {}
def font(name, size):
    key = (name, int(size))
    if key not in _font_cache:
        path = {
            "bold": FONT_DIR_P + "Poppins-Bold.ttf",
            "semi": FONT_DIR_P + "Poppins-Medium.ttf",
            "reg": FONT_DIR_I + "Inter-Regular.otf",
            "med": FONT_DIR_I + "Inter-Medium.otf",
            "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        }[name]
        _font_cache[key] = ImageFont.truetype(path, int(size))
    return _font_cache[key]

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

# ---------- texto ----------
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

def rgba(c, a): return (c[0], c[1], c[2], int(255 * clamp(a)))

# ---------- fundo ----------
def make_background():
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)
    for y in range(0, H, 54):
        for x in range(0, W, 54):
            d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(40, 40, 40))
    glow = Image.new("L", (1400, 1400), 0)
    ImageDraw.Draw(glow).ellipse([250, 250, 1150, 1150], fill=150)
    glow = glow.filter(ImageFilter.GaussianBlur(170))
    glow_rgba = Image.new("RGBA", glow.size, TEAL + (0,))
    glow_rgba.putalpha(glow.point(lambda v: int(v * 0.55)))
    return base.convert("RGBA"), glow_rgba

def draw_progress(layer, p):
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([MX, 150, W - MX, 158], radius=4, fill=(48, 48, 48, 255))
    d.rounded_rectangle([MX, 150, MX + (W - 2 * MX) * clamp(p), 158], radius=4, fill=TEAL + (255,))

def draw_wordmark(layer, a=1.0):
    d = ImageDraw.Draw(layer)
    f = font("bold", 40)
    d.text((MX, 196), "ciello", font=f, fill=rgba(FG, a))
    tw = f.getlength("ciello")
    d.ellipse([MX + tw + 8, 226, MX + tw + 20, 238], fill=rgba(TEAL, a))
    fh = font("med", 30)
    handle = "@ciellotec"
    d.text((W - MX - fh.getlength(handle), 204), handle, font=fh, fill=rgba(MUTED, a))

# ---------- cenas ----------
def scene_alpha(t, dur):
    """fade-in rápido, fade-out no último 0.18s"""
    return clamp(t / 0.2) * clamp((dur - t) / 0.18)

def render_hook(layer, sc, t):
    d = ImageDraw.Draw(layer)
    dur = sc["dur"]; out = clamp((dur - t) / 0.18)
    # kicker
    kick = sc.get("kicker", "DICA DE IA")
    fk = font("bold", 34)
    kw = fk.getlength(kick) + 56
    ka = ease_out(t / 0.3) * out
    ky = 600 + 30 * (1 - ease_out(t / 0.3))
    d.rounded_rectangle([MX, ky, MX + kw, ky + 70], radius=35, fill=rgba(TEAL, ka))
    d.text((MX + 28, ky + 13), kick, font=fk, fill=rgba(FG, ka))
    # palavras
    size = sc.get("size", 104)
    f = font("bold", size)
    words = sc["text"].split()
    hl = set(w.lower().strip(".,!?:") for w in sc.get("highlight", []))
    lh = int(size * 1.18)
    space = f.getlength(" ")
    # layout
    lines, cur, curw = [], [], 0
    for w in words:
        ww = f.getlength(w)
        pad = 24 if w.lower().strip(".,!?:") in hl else 0
        need = ww + pad + (space if cur else 0)
        if cur and curw + need > TEXT_W:
            lines.append(cur); cur, curw = [], 0; need = ww + pad
        cur.append((w, ww, pad)); curw += need
    if cur: lines.append(cur)
    y0 = 720
    i = 0
    for li, line in enumerate(lines):
        x = MX
        for (w, ww, pad) in line:
            st = 0.25 + i * 0.11
            p = ease_back((t - st) / 0.28)
            a = clamp((t - st) / 0.15) * out
            y = y0 + li * lh + 40 * (1 - p)
            if pad:
                d.rounded_rectangle([x - 6, y + size * 0.12, x + ww + pad - 6, y + size * 1.12],
                                    radius=18, fill=rgba(TEAL, a))
                d.text((x + pad / 2 - 6, y), w, font=f, fill=rgba(FG, a))
            else:
                d.text((x, y), w, font=f, fill=rgba(FG, a))
            x += ww + pad + space
            i += 1
    # sublinha
    if sc.get("sub"):
        fs = font("med", 44)
        sa = clamp((t - (0.3 + i * 0.11)) / 0.3) * out
        sy = y0 + len(lines) * lh + 50
        for k, ln in enumerate(wrap(sc["sub"], fs, TEXT_W)):
            d.text((MX, sy + k * 58), ln, font=fs, fill=rgba(MUTED, sa))

def render_item(layer, sc, t):
    d = ImageDraw.Draw(layer)
    dur = sc["dur"]; out = clamp((dur - t) / 0.18)
    # número grande
    fnum = font("bold", 260)
    pn = ease_back(t / 0.35)
    na = clamp(t / 0.15) * out
    d.text((MX - 8, 450 + 60 * (1 - pn)), sc["num"], font=fnum, fill=rgba(TEAL, na))
    # título
    ft = font("bold", 80)
    ta = ease_out((t - 0.15) / 0.3) * out
    ty = 800 + 36 * (1 - ease_out((t - 0.15) / 0.3))
    tl = wrap(sc["title"], ft, TEXT_W)
    for k, ln in enumerate(tl):
        d.text((MX, ty + k * 96), ln, font=ft, fill=rgba(FG, ta))
    y = ty + len(tl) * 96 + 26
    # corpo
    if sc.get("body"):
        fb = font("med", 44)
        ba = ease_out((t - 0.35) / 0.3) * out
        for k, ln in enumerate(wrap(sc["body"], fb, TEXT_W)):
            d.text((MX, y + k * 60), ln, font=fb, fill=rgba(MUTED, ba))
        y += len(wrap(sc["body"], fb, TEXT_W)) * 60 + 50
    # bolha de prompt digitando
    if sc.get("prompt"):
        st = 0.7
        pa = ease_out((t - st) / 0.3) * out
        fl = font("bold", 30)
        d.text((MX, y), "VOCÊ PEDE:", font=fl, fill=rgba(TEAL, pa))
        fp = font("reg", 40)
        bx0, by0 = MX, y + 50
        full_lines = wrap(sc["prompt"], fp, TEXT_W - 64)
        bh = len(full_lines) * 54 + 56
        d.rounded_rectangle([bx0, by0, W - SAFE_RIGHT, by0 + bh], radius=28,
                            fill=rgba(CARD, pa), outline=rgba(BORDER, pa), width=2)
        # typewriter
        chars_total = len(sc["prompt"])
        speed = max(28.0, chars_total / max(0.8, dur - st - 1.2))
        n = int(clamp((t - st - 0.15) * speed, 0, chars_total))
        typed = sc["prompt"][:n]
        tl2 = wrap(typed, fp, TEXT_W - 64) if typed else [""]
        for k, ln in enumerate(tl2):
            d.text((bx0 + 32, by0 + 28 + k * 54), ln, font=fp, fill=rgba(FG, pa))
        if n < chars_total or int(t * 2) % 2 == 0:
            lastw = fp.getlength(tl2[-1])
            cy = by0 + 28 + (len(tl2) - 1) * 54
            d.rectangle([bx0 + 34 + lastw, cy + 6, bx0 + 38 + lastw, cy + 46], fill=rgba(TEAL, pa))

def draw_bookmark(d, x, y, s, c):
    d.polygon([(x, y), (x + s, y), (x + s, y + s * 1.3), (x + s / 2, y + s * 0.95), (x, y + s * 1.3)], fill=c)

def render_cta(layer, sc, t):
    d = ImageDraw.Draw(layer)
    dur = sc["dur"]
    f = font("bold", sc.get("size", 92))
    lines = wrap(sc["text"], f, TEXT_W)
    y = 700
    for k, ln in enumerate(lines):
        p = ease_out((t - k * 0.12) / 0.35)
        d.text((MX, y + k * 108 + 40 * (1 - p)), ln, font=f, fill=rgba(FG, p))
    y += len(lines) * 108 + 40
    if sc.get("sub"):
        fs = font("med", 46)
        sa = ease_out((t - 0.4) / 0.35)
        for k, ln in enumerate(wrap(sc["sub"], fs, TEXT_W)):
            d.text((MX, y + k * 62), ln, font=fs, fill=rgba(MUTED, sa))
        y += len(wrap(sc["sub"], fs, TEXT_W)) * 62 + 70
    # botão salvar pulsando
    ba = ease_out((t - 0.8) / 0.3)
    pulse = 1 + 0.04 * math.sin(max(0, t - 1.1) * 6)
    fb = font("bold", 42)
    label = sc.get("save_label", "Salva pra testar depois")
    bw = (fb.getlength(label) + 150) * pulse
    bh = 104 * pulse
    d.rounded_rectangle([MX, y, MX + bw, y + bh], radius=bh / 2, fill=rgba(TEAL, ba))
    draw_bookmark(d, MX + 44, y + bh / 2 - 26, 34, rgba(FG, ba))
    d.text((MX + 104, y + bh / 2 - 30), label, font=fb, fill=rgba(FG, ba))
    # tagline
    ftg = font("semi", 36)
    tga = ease_out((t - 1.2) / 0.4)
    d.text((MX, y + bh + 60), sc.get("tagline", "Ciello · Tecnologia que eleva"), font=ftg, fill=rgba(MUTED, tga))

RENDER = {"hook": render_hook, "item": render_item, "cta": render_cta}

# ---------- áudio ----------
def synth_audio(path, total, cuts, bpm=118, sr=44100):
    n = int(total * sr); t = np.arange(n) / sr
    out = np.zeros(n)
    beat = 60 / bpm
    def env(x, a, d): return np.where(x < a, x / a, np.exp(-(x - a) / d))
    # kick
    for b in np.arange(0, total, beat):
        i0 = int(b * sr); L = int(0.35 * sr); x = np.arange(min(L, n - i0)) / sr
        f = 50 + 90 * np.exp(-x * 30)
        out[i0:i0 + len(x)] += 0.9 * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-x * 9)
    # hats no contratempo
    rng = np.random.default_rng(7)
    for b in np.arange(beat / 2, total, beat):
        i0 = int(b * sr); L = int(0.06 * sr); L = min(L, n - i0)
        noise = rng.standard_normal(L); noise = np.diff(np.concatenate([[0], noise]))
        out[i0:i0 + L] += 0.12 * noise * np.exp(-np.arange(L) / sr * 60)
    # pad Am F C G
    chords = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [196.0, 261.63, 329.63], [196.0, 246.94, 293.66]]
    bar = beat * 4
    for ci, b in enumerate(np.arange(0, total, bar)):
        i0 = int(b * sr); L = min(int(bar * sr), n - i0); x = np.arange(L) / sr
        e = np.minimum(1, x / 0.4) * np.minimum(1, (bar - x) / 0.4)
        for fr in chords[ci % 4]:
            for det in (-0.6, 0.6):
                out[i0:i0 + L] += 0.045 * e * np.sin(2 * np.pi * (fr + det) * x)
    # whoosh nas trocas de cena
    for c in cuts:
        i0 = int(max(0, c - 0.25) * sr); L = min(int(0.4 * sr), n - i0)
        noise = rng.standard_normal(L); x = np.arange(L) / L
        out[i0:i0 + L] += 0.18 * noise * np.sin(np.pi * x) ** 2
    # fade final
    fo = int(0.8 * sr); out[-fo:] *= np.linspace(1, 0, fo)
    out = np.tanh(out * 1.2); out = out / np.max(np.abs(out)) * 0.8
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())

# ---------- principal ----------
def main(script_path, out_path):
    cfg = json.load(open(script_path, encoding="utf-8"))
    scenes = cfg["scenes"]
    total = sum(s["dur"] for s in scenes)
    starts, acc = [], 0.0
    for s in scenes: starts.append(acc); acc += s["dur"]
    base, glow = make_background()
    wav = out_path + ".wav"
    synth_audio(wav, total, starts[1:])
    nframes = int(total * FPS)
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
        out_path], stdin=subprocess.PIPE)
    for fi in range(nframes):
        gt = fi / FPS
        si = max(i for i in range(len(scenes)) if starts[i] <= gt)
        sc, lt = scenes[si], gt - starts[si]
        frame = base.copy()
        gx = int(-160 + 120 * math.sin(gt * 0.5)); gy = int(260 + 260 * math.sin(gt * 0.33 + si))
        frame.alpha_composite(glow, (gx, gy))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_progress(layer, gt / total)
        draw_wordmark(layer)
        RENDER[sc["type"]](layer, sc, lt)
        frame.alpha_composite(layer)
        # wipe teal nas trocas
        if si > 0 and lt < 0.14:
            k = lt / 0.14
            ImageDraw.Draw(frame).rectangle([0, 0, W * (1 - ease_out(k)), H], fill=TEAL + (255,))
        ff.stdin.write(frame.convert("RGB").tobytes())
    ff.stdin.close(); ff.wait()
    os.remove(wav)
    print(f"ok {out_path} {total:.1f}s {nframes} frames")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
