"""Tambah motion graphics, hook jualan & SFX pada video unboxing popcorn.

Guna:  python3 render.py assets/original.mp4 output/popcorn_hook.mp4
Perlu: ffmpeg, numpy, pillow
"""
import math
import os
import random
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_FUN = os.path.join(HERE, "assets", "LuckiestGuy-Regular.ttf")
FONT_BIG = os.path.join(HERE, "assets", "Anton-Regular.ttf")
FONT_EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

W, H, FPS = 576, 1024, 30
SR = 44100

YELLOW = (255, 214, 0)
RED = (240, 30, 45)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 110)

random.seed(7)


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_back(x, s=2.2):
    x = clamp(x) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def ease_out_elastic(x):
    x = clamp(x)
    if x in (0, 1):
        return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi / 3)) + 1


def ease_out_cubic(x):
    return 1 - (1 - clamp(x)) ** 3


def ease_in_out(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- sprites
_fonts = {}


def font(path, size):
    key = (path, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, size)
    return _fonts[key]


def emoji(ch, size):
    f = font(FONT_EMOJI, 109)
    im = Image.new("RGBA", (160, 160))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)


def text_img(txt, path, size, fill, stroke=BLACK, sw=None, shadow=True):
    f = font(path, size)
    sw = max(2, size // 9) if sw is None else sw
    l, t, r, b = f.getbbox(txt, stroke_width=sw)
    pad = sw + 8
    im = Image.new("RGBA", (r - l + pad * 2, b - t + pad * 2))
    d = ImageDraw.Draw(im)
    if shadow:
        sh = Image.new("RGBA", im.size)
        ImageDraw.Draw(sh).text((pad - l + 4, pad - t + 6), txt, font=f, fill=(0, 0, 0, 170),
                                stroke_width=sw, stroke_fill=(0, 0, 0, 170))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(3)))
        d = ImageDraw.Draw(im)
    d.text((pad - l, pad - t), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
    return im


def hstack(parts, gap=8):
    w = sum(p.width for p in parts) + gap * (len(parts) - 1)
    h = max(p.height for p in parts)
    im = Image.new("RGBA", (w, h))
    x = 0
    for p in parts:
        im.alpha_composite(p, (x, (h - p.height) // 2))
        x += p.width + gap
    return im


def vstack(parts, gap=0):
    w = max(p.width for p in parts)
    h = sum(p.height for p in parts) + gap * (len(parts) - 1)
    im = Image.new("RGBA", (w, h))
    y = 0
    for p in parts:
        im.alpha_composite(p, ((w - p.width) // 2, y))
        y += p.height + gap
    return im


def pill(content, bg, pad=(22, 10), border=BLACK, bw=5, radius=None, tilt=0):
    w, h = content.width + pad[0] * 2, content.height + pad[1] * 2
    radius = h // 2 if radius is None else radius
    im = Image.new("RGBA", (w + 16, h + 20))
    sh = Image.new("RGBA", im.size)
    ImageDraw.Draw(sh).rounded_rectangle((8, 14, w + 8, h + 14), radius, fill=(0, 0, 0, 150))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(4)))
    ImageDraw.Draw(im).rounded_rectangle((8, 6, w + 8, h + 6), radius, fill=bg, outline=border, width=bw)
    im.alpha_composite(content, (8 + pad[0], 6 + pad[1]))
    return im.rotate(tilt, Image.BICUBIC, expand=True) if tilt else im


def starburst(r, points, fill, border=BLACK):
    im = Image.new("RGBA", (r * 2 + 12, r * 2 + 12))
    c = r + 6
    pts = []
    for i in range(points * 2):
        a = math.pi * i / points
        rr = r if i % 2 == 0 else r * 0.74
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    ImageDraw.Draw(im).polygon(pts, fill=fill, outline=border, width=5)
    return im


def rays(r, n=16, color=(255, 230, 80, 120)):
    im = Image.new("RGBA", (r * 2, r * 2))
    d = ImageDraw.Draw(im)
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = a0 + math.pi / n
        d.polygon([(r, r), (r + r * math.cos(a0), r + r * math.sin(a0)),
                   (r + r * math.cos(a1), r + r * math.sin(a1))], fill=color)
    mask = Image.new("L", im.size)
    ImageDraw.Draw(mask).ellipse((0, 0, r * 2, r * 2), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(r // 4))
    im.putalpha(Image.fromarray((np.array(im.getchannel("A")) * (np.array(mask) / 255)).astype(np.uint8)))
    return im


def build_sprites():
    s = {}
    # HOOK
    s["hook1"] = hstack([text_img("POPCORN 1 KILO", FONT_FUN, 54, WHITE), emoji("😱", 52)])
    s["hook2"] = pill(text_img("HARGA TAK MASUK AKAL!", FONT_FUN, 34, YELLOW, sw=4, shadow=False), RED, tilt=-3)
    # TEKA HARGA
    s["teka"] = pill(hstack([text_img("TEKA HARGA?", FONT_FUN, 40, BLACK, stroke=WHITE, sw=3, shadow=False),
                             emoji("🤔", 42)]), YELLOW, tilt=4)
    s["rmq"] = text_img("RM ??", FONT_BIG, 92, WHITE, sw=7)
    # PROMOSI
    s["promo"] = pill(hstack([emoji("🔥", 40), text_img("PROMOSI", FONT_FUN, 46, WHITE, sw=4, shadow=False),
                              emoji("🔥", 40)]), RED, radius=14, tilt=-4)
    s["murah"] = pill(text_img("HARGA MURAH GILA", FONT_FUN, 30, BLACK, stroke=YELLOW, sw=1, shadow=False),
                      YELLOW, tilt=-4)
    # FREE
    burst = starburst(118, 14, YELLOW)
    lab = vstack([text_img("DAPAT", FONT_FUN, 38, WHITE, sw=4), text_img("FREE!", FONT_FUN, 62, RED, stroke=WHITE, sw=5)], gap=-12)
    burst.alpha_composite(lab, ((burst.width - lab.width) // 2, (burst.height - lab.height) // 2 + 4))
    gift = emoji("🎁", 62)
    burst.alpha_composite(gift, (burst.width - gift.width - 4, burst.height - gift.height - 4))
    s["free"] = burst
    # BESAR GILA
    s["besar"] = hstack([text_img("BESAR GILA!", FONT_FUN, 66, YELLOW, sw=7), emoji("🤯", 58)])
    # BANYAK
    s["banyak"] = pill(hstack([text_img("PUAS HATI MAKAN", FONT_FUN, 34, WHITE, sw=4, shadow=False),
                               emoji("🤤", 38)]), GREEN, tilt=3)
    # PRICE
    s["rays"] = rays(330)
    s["price_burst"] = starburst(170, 18, RED)
    s["rm18"] = text_img("RM18", FONT_BIG, 150, YELLOW, sw=10)
    s["sahaja"] = pill(text_img("SAHAJA!", FONT_FUN, 40, BLACK, stroke=WHITE, sw=2, shadow=False), WHITE, tilt=-6)
    s["kilo"] = pill(hstack([text_img("1 BEG = 1 KILO", FONT_FUN, 42, WHITE, sw=4, shadow=False),
                             emoji("💪", 42)]), (25, 25, 25), border=YELLOW, bw=5, tilt=-3)
    # CTA
    s["cta"] = pill(hstack([emoji("🛒", 46), text_img("TEKAN BAKUL KUNING", FONT_FUN, 36, BLACK, stroke=YELLOW, sw=1,
                                                          shadow=False)]), YELLOW, pad=(26, 16), bw=6)
    s["cta_sub"] = text_img("SEBELUM PROMOSI TAMAT!", FONT_FUN, 30, WHITE, sw=4)
    s["point"] = emoji("👇", 64)
    s["sparkle"] = emoji("✨", 40)
    s["corn"] = emoji("🍿", 44)
    return s


# ---------------------------------------------------------------- compositing
def place(canvas, spr, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    im = spr
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.05:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy()
        im.putalpha(a)
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    if x >= 0 and y >= 0 and x + im.width <= W and y + im.height <= H:
        canvas.alpha_composite(im, (x, y))
    else:
        paste_clipped(canvas, im, x, y)


def paste_clipped(canvas, im, x, y):
    layer = Image.new("RGBA", canvas.size)
    layer.paste(im, (x, y), im)
    canvas.alpha_composite(layer)


def pop(t, t0, t1, dur_in=0.35, dur_out=0.18, elastic=False):
    """(scale, alpha) untuk sticker yang 'pop' masuk & keluar."""
    if t < t0 or t > t1:
        return 0.0, 0.0
    a = (t - t0) / dur_in
    sc = ease_out_elastic(a) if elastic else ease_out_back(a)
    out = clamp((t1 - t) / dur_out)
    return sc * (0.6 + 0.4 * out), out


class Confetti:
    def __init__(self, t0, n=70):
        self.t0 = t0
        cols = [YELLOW, RED, WHITE, GREEN, (60, 140, 255), (255, 120, 200)]
        self.p = []
        for _ in range(n):
            ang = random.uniform(-math.pi, 0)
            spd = random.uniform(380, 900)
            self.p.append(dict(x=W / 2 + random.uniform(-40, 40), y=640, vx=math.cos(ang) * spd * 0.8,
                               vy=math.sin(ang) * spd, c=random.choice(cols), w=random.randint(8, 15),
                               h=random.randint(5, 9), r=random.uniform(0, 360), vr=random.uniform(-720, 720)))

    def draw(self, canvas, t):
        dt = t - self.t0
        if dt < 0 or dt > 3.0:
            return
        layer = Image.new("RGBA", canvas.size)
        d = ImageDraw.Draw(layer)
        fade = clamp((3.0 - dt) / 0.8)
        for p in self.p:
            x = p["x"] + p["vx"] * dt * (1 - 0.35 * dt / 3)
            y = p["y"] + p["vy"] * dt + 0.5 * 1500 * dt * dt * 0.55
            if not (-20 < x < W + 20 and -20 < y < H + 20):
                continue
            a = math.radians(p["r"] + p["vr"] * dt)
            wv = p["w"] * abs(math.cos(a * 1.7)) + 2
            hw, hh = wv / 2, p["h"] / 2
            ca, sa = math.cos(a), math.sin(a)
            pts = [(x + ca * dx - sa * dy, y + sa * dx + ca * dy) for dx, dy in
                   ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
            d.polygon(pts, fill=p["c"] + (int(255 * fade),))
        canvas.alpha_composite(layer)


def sparkles(canvas, spr, t, t0, t1, spots):
    if not (t0 <= t <= t1):
        return
    for i, (x, y) in enumerate(spots):
        ph = (t - t0) * 3.2 + i * 0.37
        s = 0.4 + 0.6 * abs(math.sin(ph * math.pi))
        place(canvas, spr, x, y, s, rot=ph * 40, alpha=clamp((t1 - t) / 0.3))


# ---------------------------------------------------------------- camera moves
PUNCHES = [  # (masa, kuat zoom, tempoh) – zoom 'punch' pada beat penting
    (0.00, 0.18, 0.55),
    (3.50, 0.07, 0.40),
    (12.70, 0.07, 0.40),
    (15.00, 0.14, 1.20),
    (22.25, 0.07, 0.40),
    (27.20, 0.20, 0.90),
    (29.00, 0.10, 0.50),
    (31.50, 0.06, 0.40),
    (33.00, 0.08, 0.50),
]
SHAKES = [(0.05, 0.35, 10), (15.0, 0.30, 7), (27.2, 0.45, 14)]
FLASHES = [(0.0, 0.18), (15.0, 0.12), (27.2, 0.22)]


def camera(t):
    z = 1.0
    for t0, k, d in PUNCHES:
        if t0 <= t <= t0 + d:
            x = (t - t0) / d
            z += k * (1 - ease_out_cubic(x)) if t0 != 15.0 else k * math.sin(math.pi * x) ** 0.6
    # 'ken burns' halus supaya tak statik
    z += 0.025 * (0.5 + 0.5 * math.sin(t * 0.45))
    dx = dy = 0.0
    for t0, d, amp in SHAKES:
        if t0 <= t <= t0 + d:
            f = 1 - (t - t0) / d
            dx += amp * f * math.sin(t * 95)
            dy += amp * f * math.cos(t * 77)
    return z, dx, dy


def apply_camera(frame, t):
    z, dx, dy = camera(t)
    cw, ch = W / z, H / z
    x0 = (W - cw) / 2 - dx / z
    y0 = (H - ch) / 2 - dy / z
    x0 = clamp(x0, 0, W - cw)
    y0 = clamp(y0, 0, H - ch)
    return frame.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)


# ---------------------------------------------------------------- overlay timeline
def draw_overlays(canvas, t, S, confetti, dur):
    # bar progress (retention)
    d = ImageDraw.Draw(canvas)
    d.rectangle((0, 0, W, 7), fill=(0, 0, 0, 110))
    d.rectangle((0, 0, int(W * t / dur), 7), fill=YELLOW + (255,))

    # 1) HOOK 0–3.2s
    sc, a = pop(t, 0.05, 3.2, elastic=True)
    place(canvas, S["hook1"], W / 2, 108, sc, rot=1.5 * math.sin(t * 6), alpha=a)
    sc, a = pop(t, 0.35, 3.2)
    place(canvas, S["hook2"], W / 2, 182, sc * (1 + 0.04 * math.sin(t * 14)), alpha=a)
    sparkles(canvas, S["sparkle"], t, 0.4, 3.2, [(60, 70), (520, 150), (500, 60)])

    # 2) TEKA HARGA 3.4–5.3s – tag RM?? berayun
    sc, a = pop(t, 3.45, 5.3)
    place(canvas, S["teka"], W / 2, 110, sc, alpha=a)
    sc, a = pop(t, 3.6, 5.3, elastic=True)
    place(canvas, S["rmq"], W / 2, 215, sc, rot=10 * math.sin((t - 3.6) * 7) * math.exp(-(t - 3.6) * 1.2), alpha=a)

    # 3) PROMOSI 5.4–8.6s – masuk dari kiri
    if 5.4 <= t <= 8.6:
        x = -300 + (W / 2 + 300) * ease_out_back(clamp((t - 5.4) / 0.4), 1.6)
        out = clamp((8.6 - t) / 0.2)
        place(canvas, S["promo"], x, 110, 1 + 0.05 * math.sin(t * 12), alpha=out)
        sc, a = pop(t, 6.1, 8.6)
        place(canvas, S["murah"], W / 2 + 20, 182, sc, alpha=a)

    # 4) DAPAT FREE 12.5–14.6s – starburst berpusing
    sc, a = pop(t, 12.5, 14.6, elastic=True)
    place(canvas, S["free"], 410, 175, sc, rot=-(t - 12.5) * 25, alpha=a)

    # 5) BESAR GILA 15.0–17.8s
    sc, a = pop(t, 15.05, 17.8, elastic=True)
    place(canvas, S["besar"], W / 2, 120, sc * (1 + 0.05 * math.sin(t * 10)), alpha=a)
    sparkles(canvas, S["corn"], t, 15.2, 17.8, [(70, 230), (505, 235), (120, 330), (460, 330)])

    # 6) PUAS HATI 22.2–24.6s
    sc, a = pop(t, 22.25, 24.6)
    place(canvas, S["banyak"], W / 2, 120, sc, alpha=a)

    # 7) TEASE sebelum harga 25.6–27.1s
    sc, a = pop(t, 25.6, 27.15)
    place(canvas, S["rmq"], W / 2, 140, sc * (1 + 0.08 * math.sin(t * 20)), rot=6 * math.sin(t * 13), alpha=a)

    # 8) PRICE REVEAL 27.2–31.0s – stamp + confetti
    if 27.2 <= t <= 31.0:
        out = clamp((31.0 - t) / 0.25)
        k = clamp((t - 27.2) / 0.22)
        place(canvas, S["rays"], 180, 665, 0.8 + 0.1 * math.sin(t * 3), rot=(t - 27.2) * 30, alpha=out * k)
        bs = ease_out_back(clamp((t - 27.25) / 0.3), 2.5)
        place(canvas, S["price_burst"], 180, 665, 0.85 * bs * (1 + 0.03 * math.sin(t * 9)), rot=-(t - 27.2) * 15,
              alpha=out)
        slam = 1 + 2.2 * (1 - ease_out_cubic(k)) if k < 1 else 1 + 0.06 * math.sin((t - 27.42) * 11) * math.exp(
            -(t - 27.42) * 1.5)
        place(canvas, S["rm18"], 180, 655, 0.9 * slam, rot=-8, alpha=out * clamp(k * 3))
        sc, a = pop(t, 27.6, 31.0, elastic=True)
        place(canvas, S["sahaja"], 225, 755, sc, alpha=a * out)
    confetti.draw(canvas, t)

    # 9) 1 BEG = 1 KILO 31.2–33.0
    sc, a = pop(t, 31.2, 33.0)
    place(canvas, S["kilo"], W / 2, 130, sc, alpha=a)

    # 10) CTA 33.0–akhir – butang berdenyut + jari
    if t >= 33.0:
        sc, _ = pop(t, 33.0, dur + 1, elastic=True)
        beat = 1 + 0.07 * max(0, math.sin((t - 33.0) * 2 * math.pi * 2.2))
        place(canvas, S["cta"], W / 2, 530, sc * beat)
        sc2, _ = pop(t, 33.25, dur + 1)
        place(canvas, S["cta_sub"], W / 2, 605, sc2)
        place(canvas, S["point"], W / 2, 675 + 14 * abs(math.sin((t - 33) * 7)), sc2)
        # kilauan lalu atas butang
        sx = -120 + ((t - 33.3) % 1.1) / 1.1 * (W + 240)
        shine = Image.new("RGBA", (W, H))
        ImageDraw.Draw(shine).polygon([(sx, 490), (sx + 26, 490), (sx - 14, 570), (sx - 40, 570)],
                                      fill=(255, 255, 255, 120))
        canvas.alpha_composite(shine)


def flash_alpha(t):
    a = 0.0
    for t0, d in FLASHES:
        if t0 <= t <= t0 + d:
            a = max(a, 1 - (t - t0) / d)
    return a * 0.85


# ---------------------------------------------------------------- SFX
def sfx_pop(f0=500, f1=1400, dur=0.09, vol=0.45):
    n = int(SR * dur)
    tt = np.arange(n) / SR
    freq = f0 + (f1 - f0) * (tt / dur)
    return vol * np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 40)


def sfx_whoosh(dur=0.35, vol=0.35):
    n = int(SR * dur)
    noise = np.random.default_rng(1).standard_normal(n)
    tt = np.arange(n) / SR
    env = np.sin(np.pi * tt / dur) ** 2
    # low-pass berubah (sweep) secara kasar guna purata bergerak
    out = np.zeros(n)
    acc = 0.0
    for i in range(n):
        k = 0.02 + 0.25 * (i / n)
        acc += k * (noise[i] - acc)
        out[i] = acc
    return vol * out / (np.abs(out).max() + 1e-9) * env


def sfx_boom(dur=0.6, vol=0.7):
    n = int(SR * dur)
    tt = np.arange(n) / SR
    freq = 120 * np.exp(-tt * 6) + 45
    return vol * np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 5)


def sfx_ching(vol=0.35):
    out = np.zeros(int(SR * 0.9))
    for start, f in ((0.0, 2093), (0.08, 2637), (0.08, 3136)):
        n = len(out) - int(start * SR)
        tt = np.arange(n) / SR
        tone = np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2.01 * tt)
        out[int(start * SR):] += tone * np.exp(-tt * 6)
    return vol * out / np.abs(out).max()


def sfx_ding(vol=0.3):
    tt = np.arange(int(SR * 0.6)) / SR
    return vol * (np.sin(2 * np.pi * 1318 * tt) + 0.5 * np.sin(2 * np.pi * 1976 * tt)) * np.exp(-tt * 7) / 1.5


def build_sfx(dur, path):
    track = np.zeros(int(SR * (dur + 1)))

    def add(t, s):
        i = int(t * SR)
        track[i:i + len(s)] += s[:len(track) - i]

    add(0.0, sfx_boom(vol=0.5))
    add(0.05, sfx_pop())
    add(0.35, sfx_whoosh())
    add(3.45, sfx_pop(400, 1100))
    add(3.6, sfx_pop(700, 1600, vol=0.3))
    add(5.35, sfx_whoosh())
    add(6.1, sfx_pop())
    add(12.5, sfx_ding())
    add(15.0, sfx_boom(vol=0.45))
    add(15.05, sfx_pop(500, 1500))
    add(22.25, sfx_pop())
    add(25.6, sfx_whoosh(0.5, 0.3))
    add(27.2, sfx_boom())
    add(27.25, sfx_ching())
    add(27.6, sfx_pop(600, 1700))
    add(31.2, sfx_pop())
    add(33.0, sfx_whoosh())
    add(33.05, sfx_ding())
    track = np.clip(track, -1, 1)
    pcm = (track * 32767).astype("<i2")
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- main
def main(src, dst):
    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]))
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    S = build_sprites()
    confetti = Confetti(27.22)
    sfx_path = os.path.splitext(dst)[0] + "_sfx.wav"
    build_sfx(dur, sfx_path)
    silent = os.path.splitext(dst)[0] + "_video.mp4"

    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", f"scale={W}:{H},fps={FPS}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                            "-crf", "18", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    white = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    i = 0
    while True:
        raw = dec.stdout.read(W * H * 3)
        if len(raw) < W * H * 3:
            break
        t = i / FPS
        frame = apply_camera(Image.frombytes("RGB", (W, H), raw), t).convert("RGBA")
        draw_overlays(frame, t, S, confetti, dur)
        fa = flash_alpha(t)
        if fa > 0:
            frame = Image.blend(frame, white, fa)
        enc.stdin.write(frame.convert("RGB").tobytes())
        i += 1
        if i % 150 == 0:
            print(f"  {t:5.1f}s / {dur:.1f}s", flush=True)
    enc.stdin.close()
    enc.wait()
    dec.wait()

    # gabung audio asal + SFX
    subprocess.check_call([
        "ffmpeg", "-v", "error", "-y", "-i", silent, "-i", src, "-i", sfx_path,
        "-filter_complex", "[1:a]volume=1.0[a1];[2:a]volume=0.8[a2];"
                           "[a1][a2]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart", dst])
    os.remove(silent)
    os.remove(sfx_path)
    print("Siap:", dst)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "assets", "original.mp4"),
         sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "output", "popcorn_hook.mp4"))
