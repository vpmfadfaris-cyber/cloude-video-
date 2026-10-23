"""Video 3 (Redchef unboxing): reuses render.py helpers, swaps in this video's timeline.
No transcript available, so overlays follow the visuals. Faces sit in the upper half here,
so graphics live in the lower third (over the desk).
usage: python3 scenes3.py graded.mp4 mix.wav out.mp4"""
import math, sys, functools
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import render as R
from render import (W, H, YEL, WHITE, INK, GLASS, BLACK, XBOLD, clamp, ease_out_cubic,
                    pop, slide, place, text_sprite, pill_sprite, shadowed, cta_button, arrow_sprite)
import numpy as np
from PIL import Image, ImageDraw

PINK = (255, 150, 190)
RED = (232, 36, 48)
CUTS = [0.0, 3.7667, 15.7333, 22.0333, 26.2333, 27.7667, 29.7333, 35.8667, 50.4333, 53.5333, 55.3333,
        61.6667, 80.7333, 103.1333, 117.2]
HITS = [(0.0, 16, 0.0), (22.03, 12, 0.1), (50.43, 8, 0.08), (72.0, 8, 0.08), (91.6, 12, 0.1), (110.3, 8, 0.08)]
Y1, Y2, Y3 = 1380, 1520, 1660  # lower-third rows


@functools.lru_cache(None)
def grad_bottom():
    ys = np.arange(H)
    a = (np.clip((ys - 1050) / 870, 0, 1) ** 1.4 * 150).astype(np.uint8)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.putalpha(Image.fromarray(np.repeat(a[:, None], W, 1)))
    return img


@functools.lru_cache(None)
def sparkle(size=90):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img); c = size / 2; r = size / 2; k = size * 0.11
    d.polygon([(c, 0), (c + k, c - k), (size, c), (c + k, c + k), (c, size), (c - k, c + k), (0, c), (c - k, c - k)],
              fill=WHITE)
    return img


def sparkles(c, t, t0, t1, pts):
    if not (t0 <= t <= t1 + 0.3): return
    for i, (x, y) in enumerate(pts):
        ph = (t - t0) * 3 + i * 0.7
        s = 0.4 + 0.6 * abs(math.sin(ph * math.pi / 2))
        a = clamp((t - t0) / 0.2) * (1 - clamp((t - t1) / 0.3))
        place(c, sparkle(), x, y, s, a, rot=ph * 40)


def stamp(c, t, t0, t1, spr, cy, rot=-6):
    if not (t0 - 0.05 <= t <= t1 + 0.2): return
    p = (t - t0) / 0.18
    sc = 2.3 - 1.3 * ease_out_cubic(p)
    al = clamp(p * 2) * (1 - clamp((t - t1) / 0.2))
    place(c, spr, W / 2, cy, sc, al, rot=rot)


def label(c, t, t0, t1, kicker, big, kcol=PINK, bcol=WHITE, kfg=INK, size=104):
    s, a = pop(t, t0, t1)
    place(c, pill_sprite(kicker, 42, bg=kcol, fg=kfg), W / 2, Y1 + 20, s, a)
    s, a = pop(t, t0 + 0.2, t1)
    place(c, text_sprite(big, size, bcol), W / 2, Y2 + 30, s, a)


def overlays(c, t):
    # HOOK 0 - 3.6 (car park walk-in)
    s, a = pop(t, 0.0, 3.55, 0.22)
    place(c, pill_sprite("PARCEL BARU SAMPAI!", 44, bg=RED, fg=WHITE), W / 2, Y1 - 20, s, a,
          rot=-3 * (1 - clamp(t / 0.3)))
    s, a = pop(t, 0.15, 3.55)
    place(c, text_sprite("SET PERIUK PINK", 120, WHITE), W / 2, Y2, s, a)
    s, a = pop(t, 0.55, 3.55)
    wob = math.sin(t * 9) * 1.2 if 0.8 < t < 3.55 else 0
    place(c, text_sprite("PALING AESTHETIC?", 116, PINK), W / 2, Y3, s, a, rot=wob)

    # Intro with the box
    s, a = pop(t, 4.0, 8.0)
    place(c, pill_sprite("UNBOXING", 40, bg=GLASS, fg=WHITE), W / 2, Y1 + 40, s, a)
    s, a = pop(t, 4.2, 8.0)
    place(c, text_sprite("REDCHEF", 130, WHITE, track=8), W / 2, Y2 + 40, s, a)
    s, a = pop(t, 13.8, 15.6)
    place(c, pill_sprite("JOM BUKA!", 64, bg=PINK, fg=INK, padx=44, pady=22), W / 2, Y2, s, a, rot=-4)

    # Opening the box → reveal
    s, a = pop(t, 16.0, 21.9)
    dots = "." * (1 + int((t - 16.0) * 2) % 3) if t >= 16 else ""
    place(c, text_sprite("BUKA KOTAK" + dots.ljust(3), 84, WHITE), W / 2, Y2 + 40, s, a)
    stamp(c, t, 22.05, 24.6, pill_sprite("WAAAH!", 120, bg=PINK, fg=INK, padx=50, pady=26, radius=26), Y2)
    sparkles(c, t, 22.05, 24.6, [(200, 1250), (880, 1300), (300, 1750), (820, 1720)])

    # Unwrapping
    label(c, t, 28.0, 34.8, "PACKAGING", "SUPER KEMAS")

    # Pots come out
    label(c, t, 36.4, 42.8, "WARNA", "PINK PASTEL", bcol=PINK)
    sparkles(c, t, 36.6, 42.8, [(160, 1330), (920, 1380)])
    label(c, t, 43.6, 50.2, "DALAM KOTAK", "SET LENGKAP")
    stamp(c, t, 50.45, 53.4, pill_sprite("CANTIK GILA!", 104, bg=PINK, fg=INK, padx=46, pady=26, radius=26), Y2)
    sparkles(c, t, 50.45, 53.4, [(180, 1300), (900, 1290), (240, 1740), (860, 1760)])
    s, a = pop(t, 53.6, 55.2)
    place(c, pill_sprite("DETAIL PREMIUM", 54, bg=GLASS, fg=WHITE, padx=40, pady=22), W / 2, Y2, s, a)
    label(c, t, 56.0, 61.5, "JIMAT RUANG", "BOLEH SUSUN")

    # Close-ups
    s, a = pop(t, 62.0, 67.5)
    place(c, pill_sprite("CLOSE-UP", 50, bg=GLASS, fg=WHITE, padx=40, pady=22), W / 2, Y2, s, a)
    s, a = pop(t, 72.0, 80.5)
    place(c, pill_sprite("FEATURE BEST", 42, bg=PINK, fg=INK), W / 2, Y1 + 20, s, a)
    s, a = pop(t, 72.2, 80.5)
    place(c, text_sprite("HANDLE BOLEH", 112, WHITE), W / 2, Y2 + 20, s, a)
    s, a = pop(t, 72.5, 80.5)
    place(c, text_sprite("TANGGAL!", 132, PINK), W / 2, Y3 + 20, s, a)

    # Handle demo
    s, a = pop(t, 82.0, 90.8)
    place(c, pill_sprite("CARA PASANG HANDLE", 50, bg=GLASS, fg=WHITE, padx=40, pady=22), W / 2, Y2, s, a)
    stamp(c, t, 91.6, 93.4, pill_sprite("KLIK!", 130, bg=PINK, fg=INK, padx=50, pady=26, radius=26), Y2)
    label(c, t, 93.8, 102.8, "SATU HANDLE", "SEMUA PERIUK", size=110)

    # Lids
    label(c, t, 104.0, 109.8, "SIAP DENGAN", "PENUTUP")

    # CTA
    if t >= 110.2:
        s, a = pop(t, 110.3, 999, 0.3)
        pulse = 1 + 0.035 * math.sin((t - 110.3) * 2 * math.pi * 2.2) if t > 110.7 else 1
        place(c, text_sprite("NAK SET NI?", 92, WHITE), W / 2, Y1, s, a)
        place(c, cta_button(), W / 2, Y2 + 20, s * pulse, a)
        s3, a3 = pop(t, 110.9, 999)
        bounce = 18 * abs(math.sin((t - 110.9) * math.pi * 2.4))
        place(c, arrow_sprite(), 150 - bounce * 0.5, 1760 + bounce * 0.4, s3 * 0.85, a3)


def camera(t):
    i = max(k for k in range(len(CUTS) - 1) if CUTS[k] <= t + 1e-6)
    st, en = CUTS[i], CUTS[i + 1]
    z = 1.0 + 0.035 * ((t - st) / (en - st))
    if t < 0.75:
        z *= 1.0 + 0.22 * (1 - ease_out_cubic(t / 0.75))
    elif t - st < 0.3 and st > 0:
        z *= 1.0 + 0.07 * (1 - ease_out_cubic((t - st) / 0.3))
    dx = dy = 0.0
    for ts, amp, zp in HITS:
        if ts <= t < ts + 0.4:
            if ts > 0: z *= 1.0 + zp * (1 - ease_out_cubic((t - ts) / 0.4))
            k = amp * math.exp(-(t - ts) * 9)
            dx += k * math.sin(t * 97); dy += k * math.cos(t * 83)
    return z, dx, dy


def flash(t):
    v = 0.0
    for ts, d in [(0.0, 0.25), (22.03, 0.18), (50.43, 0.12), (110.3, 0.18)]:
        if ts <= t < ts + d: v = max(v, 0.85 * (1 - (t - ts) / d))
    return v


R.scene_overlays, R.camera, R.flash, R.grad_top = overlays, camera, flash, grad_bottom
if __name__ == "__main__":
    R.T_END = 117.2
    R.main()
