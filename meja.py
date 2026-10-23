"""Video 3: unboxing meja belajar budak 3 in 1 (meja, kerusi, storage).

Guna:  python3 meja.py [assets/meja_original.mp4] [output/meja_hook.mp4]
"""
import math
import os
import sys

from motion import *  # noqa: F401,F403
from motion import Image, ImageDraw, render

BLUE = (40, 120, 255)
PINK = (235, 60, 130)
GREY = (90, 90, 90)


def slot(label, emo, bg, faded=False):
    content = vstack([emoji(emo, 44), text_img(label, FONT_FUN, 26, WHITE, sw=3, shadow=False)], gap=2)
    im = pill(content, GREY if faded else bg, pad=(12, 8), radius=18, border=(40, 40, 40) if faded else BLACK)
    if faded:
        im.putalpha(im.getchannel("A").point(lambda v: int(v * 0.55)))
    return im


def number_badge(n):
    im = Image.new("RGBA", (130, 130))
    ImageDraw.Draw(im).ellipse((8, 8, 122, 122), fill=RED, outline=WHITE, width=7)
    txt = text_img(str(n), FONT_BIG, 74, WHITE, sw=5, shadow=False)
    im.alpha_composite(txt, ((130 - txt.width) // 2, (130 - txt.height) // 2 - 2))
    return im


def build_sprites():
    s = {}
    # HOOK
    s["hook1"] = hstack([text_img("MEJA BELAJAR", FONT_FUN, 54, WHITE), emoji("📚", 50)])
    s["hook2"] = hstack([text_img("3 IN 1", FONT_BIG, 96, YELLOW, sw=8), emoji("🤯", 64)])
    s["hook3"] = pill(text_img("MEJA + KERUSI + STORAGE", FONT_FUN, 30, WHITE, sw=4, shadow=False), RED, tilt=-3)
    s["jom"] = pill(hstack([emoji("📦", 40), text_img("JOM UNBOXING!", FONT_FUN, 40, BLACK, stroke=YELLOW, sw=1,
                                                       shadow=False)]), YELLOW, tilt=3)
    # BELI 3 SET
    s["tiga_set"] = pill(hstack([emoji("🔥", 40), text_img("SAMPAI BELI 3 SET!", FONT_FUN, 40, WHITE, sw=4,
                                                            shadow=False)]), RED, radius=14, tilt=-3)
    for n in (1, 2, 3):
        s[f"n{n}"] = number_badge(n)
    s["pasang"] = pill(hstack([emoji("🔧", 36), text_img("SENANG PASANG", FONT_FUN, 36, WHITE, sw=4,
                                                          shadow=False)]), GREEN, tilt=2)
    # HASIL
    s["hasil"] = hstack([text_img("NI HASIL DIA!", FONT_FUN, 64, YELLOW, sw=7), emoji("✨", 54)])
    s["rays"] = rays(330)
    s["kukuh"] = pill(hstack([emoji("💪", 38), text_img("CANTIK & KUKUH", FONT_FUN, 38, WHITE, sw=4,
                                                         shadow=False)]), BLUE, tilt=-2)
    s["saiz"] = pill(hstack([emoji("👧", 36), text_img("BUDAK BESAR PUN MUAT", FONT_FUN, 32, BLACK, stroke=WHITE, sw=1,
                                                        shadow=False)]), WHITE, tilt=2)
    s["estetik"] = hstack([text_img("ESTETIK GILA!", FONT_FUN, 62, PINK, stroke=WHITE, sw=6), emoji("😍", 54)])
    s["tamu"] = pill(hstack([emoji("🛋️", 36), text_img("RUANG TAMU", FONT_FUN, 34, WHITE, sw=4, shadow=False),
                             emoji("✅", 32)]), GREEN, tilt=-3)
    s["bilik"] = pill(hstack([emoji("📖", 36), text_img("BILIK BELAJAR", FONT_FUN, 34, WHITE, sw=4, shadow=False),
                              emoji("✅", 32)]), GREEN, tilt=3)
    # 3 IN 1
    for key, label, emo, bg in (("meja", "MEJA", "📝", BLUE), ("kerusi", "KERUSI", "🪑", PINK),
                                ("storage", "STORAGE", "📦", GREEN)):
        s[key] = slot(label, emo, bg)
        s[key + "_off"] = slot(label, emo, bg, faded=True)
    s["bukan"] = hstack([text_img("BUKAN MEJA JE...", FONT_FUN, 46, WHITE, sw=6), emoji("👀", 44)])
    two = text_img("2 IN 1?", FONT_BIG, 80, WHITE, sw=7)
    ImageDraw.Draw(two).line((10, two.height * 0.55, two.width - 10, two.height * 0.45), fill=RED, width=12)
    s["two"] = two
    burst = starburst(150, 18, RED)
    lab = text_img("3 IN 1!", FONT_BIG, 96, YELLOW, sw=8)
    burst.alpha_composite(lab, ((burst.width - lab.width) // 2, (burst.height - lab.height) // 2))
    s["three"] = burst
    s["jimat"] = pill(hstack([emoji("🏠", 40), text_img("JIMAT RUANG RUMAH", FONT_FUN, 36, BLACK, stroke=YELLOW, sw=1,
                                                         shadow=False)]), YELLOW, tilt=-2)
    # CTA
    s["offer"] = pill(hstack([emoji("🔥", 44), text_img("HARGA OFFER!", FONT_FUN, 50, WHITE, sw=5, shadow=False),
                              emoji("🔥", 44)]), RED, radius=14, tilt=-4)
    s["cta"] = pill(hstack([emoji("🛒", 46), text_img("TEKAN BEG KUNING", FONT_FUN, 38, BLACK, stroke=YELLOW, sw=1,
                                                          shadow=False)]), YELLOW, pad=(26, 16), bw=6)
    s["checkout"] = text_img("TERUS CHECK OUT!", FONT_FUN, 36, WHITE, sw=5)
    s["berbaloi"] = hstack([text_img("SANGAT BERBALOI", FONT_FUN, 54, YELLOW, sw=7), emoji("💯", 50)])
    s["beli_je"] = hstack([text_img("BELI JE, NANTI TAHU!", FONT_FUN, 46, WHITE, sw=6), emoji("😉", 46)])
    s["point"] = emoji("👇", 60)
    s["sparkle"] = emoji("✨", 40)
    s["star"] = emoji("⭐", 36)
    return s


PUNCHES = [  # (masa, kuat zoom, tempoh[, 'hold'])
    (0.00, 0.18, 0.55),
    (4.10, 0.06, 0.40),
    (7.00, 0.08, 0.45),
    (9.30, 0.05, 0.35),
    (11.80, 0.05, 0.35),
    (18.40, 0.07, 0.40),
    (23.30, 0.14, 1.40, "hold"),
    (32.60, 0.07, 0.45),
    (49.80, 0.18, 0.80),
    (52.10, 0.06, 0.40),
    (58.30, 0.10, 0.50),
    (65.00, 0.08, 0.50),
    (68.50, 0.07, 0.50),
]
SHAKES = [(0.05, 0.35, 10), (23.3, 0.3, 8), (49.8, 0.45, 14), (58.3, 0.3, 8)]
FLASHES = [(0.0, 0.18), (23.3, 0.15), (49.8, 0.2), (58.3, 0.1)]

CONFETTI = Confetti(49.85, y0=330)
SFX_VOLUME = 0.6
SFX_EVENTS = [
    (0.0, "boom", dict(vol=0.5)),
    (0.05, "pop", {}),
    (0.45, "boom", dict(vol=0.35)),
    (1.2, "whoosh", {}),
    (4.1, "pop", dict(f0=400, f1=1100)),
    (7.0, "whoosh", {}),
    (9.3, "pop", dict(f0=500, f1=1200)),
    (11.8, "pop", dict(f0=600, f1=1400)),
    (18.4, "pop", dict(f0=700, f1=1700)),
    (21.0, "pop", dict(vol=0.3)),
    (23.3, "boom", dict(vol=0.45)),
    (23.35, "ding", {}),
    (25.5, "pop", {}),
    (28.5, "pop", dict(vol=0.3)),
    (32.6, "pop", dict(f0=600, f1=1700)),
    (35.3, "pop", dict(f0=700, f1=1500, vol=0.35)),
    (37.0, "pop", dict(f0=800, f1=1700, vol=0.35)),
    (40.4, "whoosh", {}),
    (40.6, "pop", {}),
    (43.0, "pop", dict(f0=600, f1=1500)),
    (46.3, "pop", dict(f0=300, f1=200, vol=0.5)),
    (49.8, "boom", {}),
    (49.85, "ching", {}),
    (52.1, "pop", dict(f0=700, f1=1700)),
    (53.3, "pop", dict(vol=0.3)),
    (56.3, "whoosh", {}),
    (58.3, "boom", dict(vol=0.4)),
    (58.35, "ching", dict(vol=0.25)),
    (60.5, "ding", {}),
    (63.0, "pop", {}),
    (65.0, "ding", {}),
    (68.5, "whoosh", {}),
    (68.6, "pop", {}),
]


def cta_button(canvas, t, S, t0, y):
    sc, _ = pop(t, t0, 99, elastic=True)
    beat = 1 + 0.07 * max(0, math.sin((t - t0) * 2 * math.pi * 2.2))
    place(canvas, S["cta"], W / 2, y, sc * beat)
    sx = -120 + ((t - t0 - 0.3) % 1.1) / 1.1 * (W + 240)
    shine = Image.new("RGBA", (W, H))
    ImageDraw.Draw(shine).polygon([(sx, y - 40), (sx + 26, y - 40), (sx - 14, y + 40), (sx - 40, y + 40)],
                                  fill=(255, 255, 255, 120))
    canvas.alpha_composite(shine)


def draw_overlays(canvas, t, S, dur):
    # bar progress (retention)
    d = ImageDraw.Draw(canvas)
    d.rectangle((0, 0, W, 7), fill=(0, 0, 0, 110))
    d.rectangle((0, 0, int(W * t / dur), 7), fill=YELLOW + (255,))

    # 1) HOOK 0–4.0s
    sc, a = pop(t, 0.05, 4.0, elastic=True)
    place(canvas, S["hook1"], W / 2, 250, sc, rot=1.5 * math.sin(t * 6), alpha=a)
    sc, a = pop(t, 0.45, 4.0, elastic=True)
    place(canvas, S["hook2"], W / 2, 350, sc * (1 + 0.05 * math.sin(t * 12)), alpha=a)
    sc, a = pop(t, 1.2, 4.0)
    place(canvas, S["hook3"], W / 2, 450, sc, alpha=a)
    sparkles(canvas, S["sparkle"], t, 0.5, 4.0, [(60, 200), (520, 300), (80, 400), (500, 470)])

    # 2) JOM UNBOXING 4.1–6.3
    sc, a = pop(t, 4.1, 6.3)
    place(canvas, S["jom"], W / 2, 200, sc, alpha=a)

    # 3) BELI 3 SET 7.0–9.2 – masuk dari kiri, lepas tu kiraan 1-2-3
    if 7.0 <= t <= 9.2:
        x = -300 + (W / 2 + 300) * ease_out_back(clamp((t - 7.0) / 0.4), 1.6)
        place(canvas, S["tiga_set"], x, 130, 1 + 0.04 * math.sin(t * 12), alpha=clamp((9.2 - t) / 0.2))
    for n, t0, t1 in ((1, 9.3, 11.6), (2, 11.8, 14.0), (3, 18.4, 20.8)):
        sc, a = pop(t, t0, t1, elastic=True)
        place(canvas, S[f"n{n}"], 480, 130, sc, rot=-12 * math.sin((t - t0) * 6) * math.exp(-(t - t0) * 2), alpha=a)

    # 4) SENANG PASANG 21.0–23.0
    sc, a = pop(t, 21.0, 23.1)
    place(canvas, S["pasang"], W / 2, 130, sc, alpha=a)

    # 5) HASIL 23.3–25.4 – sinar + sparkle
    if 23.3 <= t <= 25.4:
        out = clamp((25.4 - t) / 0.25)
        place(canvas, S["rays"], W / 2, 150, 0.8, rot=(t - 23.3) * 30, alpha=out * clamp((t - 23.3) / 0.2))
    sc, a = pop(t, 23.3, 25.4, elastic=True)
    place(canvas, S["hasil"], W / 2, 150, sc * (1 + 0.04 * math.sin(t * 10)), alpha=a)
    sparkles(canvas, S["star"], t, 23.5, 25.4, [(60, 260), (510, 250), (290, 60)])

    # 6) CANTIK & KUKUH / BUDAK BESAR
    sc, a = pop(t, 25.5, 28.4)
    place(canvas, S["kukuh"], W / 2, 140, sc, alpha=a)
    sc, a = pop(t, 28.5, 31.6)
    place(canvas, S["saiz"], W / 2, 140, sc, alpha=a)

    # 7) ESTETIK 32.6–35.0
    sc, a = pop(t, 32.6, 35.1, elastic=True)
    place(canvas, S["estetik"], W / 2, 150, sc * (1 + 0.05 * math.sin(t * 10)), alpha=a)
    sparkles(canvas, S["sparkle"], t, 32.8, 35.1, [(50, 70), (520, 240)])

    # 8) RUANG TAMU / BILIK BELAJAR 35.3–39.8
    sc, a = pop(t, 35.3, 39.8)
    place(canvas, S["tamu"], W / 2 - 40, 120, sc, alpha=a)
    sc, a = pop(t, 37.0, 39.8)
    place(canvas, S["bilik"], W / 2 + 30, 200, sc, alpha=a)

    # 9) 3 IN 1 – slot menyala ikut apa yang disebut
    if 40.4 <= t <= 55.8:
        out = clamp((55.8 - t) / 0.25)
        sc_row, _ = pop(t, 40.4, 99)
        for i, (key, t_on) in enumerate((("meja", 40.6), ("kerusi", 43.0), ("storage", 52.1))):
            x = W / 2 + (i - 1) * 172
            if t >= t_on:
                s2 = ease_out_elastic((t - t_on) / 0.6)
                place(canvas, S[key], x, 640, s2 * out * (1 + 0.03 * math.sin(t * 8 + i)))
            else:
                place(canvas, S[key + "_off"], x, 640, sc_row * out)
    sc, a = pop(t, 40.4, 43.0)
    place(canvas, S["bukan"], W / 2, 140, sc, alpha=a)
    sc, a = pop(t, 46.3, 49.6)
    place(canvas, S["two"], W / 2, 140, sc, rot=4 * math.sin((t - 46.3) * 9) * math.exp(-(t - 46.3) * 2), alpha=a)
    if 49.8 <= t <= 53.2:
        out = clamp((53.2 - t) / 0.25)
        k = clamp((t - 49.8) / 0.22)
        slam = 1 + 2.0 * (1 - ease_out_cubic(k)) if k < 1 else 1 + 0.05 * math.sin((t - 50.02) * 11) * math.exp(
            -(t - 50.02) * 1.5)
        place(canvas, S["rays"], W / 2, 200, 0.75, rot=(t - 49.8) * 30, alpha=out * k)
        place(canvas, S["three"], W / 2, 200, 0.85 * slam, rot=-(t - 49.8) * 12, alpha=out * clamp(k * 3))
    CONFETTI.draw(canvas, t)

    # 10) JIMAT RUANG 53.3–56.0
    sc, a = pop(t, 53.3, 56.0)
    place(canvas, S["jimat"], W / 2, 150, sc, alpha=a)

    # 11) CTA 56.3–68.3: harga offer + beg kuning + check out
    if 56.3 <= t <= 68.3:
        cta_button(canvas, t, S, 56.3, 620)
    sc, a = pop(t, 58.3, 62.8, elastic=True)
    place(canvas, S["offer"], W / 2, 150, sc * (1 + 0.04 * math.sin(t * 12)), alpha=a)
    sc, a = pop(t, 63.0, 64.9)
    place(canvas, S["checkout"], W / 2, 150, sc, alpha=a)
    if 56.6 <= t <= 68.3:
        place(canvas, S["point"], W / 2, 705 + 10 * abs(math.sin((t - 56.6) * 7)), pop(t, 56.6, 99)[0])

    # 12) BERBALOI 65.0–68.3 dan penutup 68.5–akhir
    sc, a = pop(t, 65.0, 68.3, elastic=True)
    place(canvas, S["berbaloi"], W / 2, 240, sc * (1 + 0.04 * math.sin(t * 10)), alpha=a)
    if t >= 68.5:
        sc, _ = pop(t, 68.5, dur + 1, elastic=True)
        place(canvas, S["beli_je"], W / 2, 150, sc * (1 + 0.03 * math.sin(t * 8)))
        cta_button(canvas, t, S, 68.8, 620)
        place(canvas, S["point"], W / 2, 705 + 10 * abs(math.sin((t - 68.8) * 7)), pop(t, 69.0, 99)[0])
        sparkles(canvas, S["star"], t, 68.8, dur + 1, [(60, 80), (510, 230)])


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    render(sys.modules[__name__],
           sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "assets", "meja_original.mp4"),
           sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "output", "meja_hook.mp4"))
