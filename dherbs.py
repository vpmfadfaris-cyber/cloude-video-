"""Video 2: unboxing gel mandian D'HERBS (Madu Bidara, Kemuning Hitam, Aura 7 Bunga).

Guna:  python3 dherbs.py [assets/dherbs_original.mp4] [output/dherbs_hook.mp4]
"""
import math
import os
import sys

from motion import *  # noqa: F401,F403
from motion import Image, ImageDraw, render

HERB = (20, 150, 95)
PINK = (235, 60, 130)
AMBER = (255, 170, 0)


def tag(label, emo, bg):
    """Chip nama produk dengan ekor segi tiga menghala ke bawah."""
    body = pill(hstack([emoji(emo, 38), text_img(label, FONT_FUN, 34, WHITE, sw=4, shadow=False)]), bg)
    im = Image.new("RGBA", (body.width, body.height + 26))
    cx = body.width // 2
    ImageDraw.Draw(im).polygon([(cx - 18, body.height - 18), (cx + 18, body.height - 18), (cx, body.height + 20)],
                               fill=bg, outline=BLACK, width=5)
    im.alpha_composite(body)
    return im


def build_sprites():
    s = {}
    # HOOK
    s["hook1"] = text_img("BILIK AIR SAYA", FONT_FUN, 50, WHITE)
    s["hook2"] = hstack([text_img("PENUH SABUN NI!", FONT_FUN, 54, YELLOW, sw=7), emoji("😍", 52)])
    s["brand_chip"] = pill(hstack([emoji("🌿", 34), text_img("D'HERBS", FONT_FUN, 32, WHITE, sw=4, shadow=False)]),
                           HERB, tilt=-3)
    s["order"] = pill(hstack([text_img("TAPI SAYA ORDER LAGI", FONT_FUN, 34, BLACK, stroke=YELLOW, sw=1,
                                       shadow=False), emoji("🤭", 38)]), YELLOW, tilt=3)
    # STOK BARU
    s["stok"] = pill(hstack([emoji("📦", 44), text_img("STOK BARU SAMPAI!", FONT_FUN, 40, WHITE, sw=4,
                                                         shadow=False)]), RED, radius=14, tilt=-3)
    s["sekotak"] = hstack([text_img("SEKOTAK PENUH!", FONT_FUN, 58, YELLOW, sw=7), emoji("😱", 52)])
    s["parcel"] = pill(hstack([emoji("🚚", 40), text_img("ADA PARCEL LAGI!", FONT_FUN, 38, BLACK, stroke=WHITE,
                                                           sw=2, shadow=False)]), WHITE, tilt=2)
    s["kemas"] = pill(hstack([emoji("✅", 34), text_img("BALUT KEMAS", FONT_FUN, 34, WHITE, sw=4, shadow=False)]),
                      HERB, tilt=-2)
    # BRAND STAMP
    burst = starburst(150, 16, YELLOW)
    lab = vstack([text_img("D'HERBS", FONT_FUN, 52, HERB, stroke=WHITE, sw=5),
                  text_img("TERLAJAK", FONT_FUN, 34, RED, stroke=WHITE, sw=4),
                  text_img("LARIS!", FONT_FUN, 44, RED, stroke=WHITE, sw=4)], gap=-10)
    burst.alpha_composite(lab, ((burst.width - lab.width) // 2, (burst.height - lab.height) // 2 + 4))
    fire = emoji("🔥", 60)
    burst.alpha_composite(fire, (burst.width - fire.width - 6, 6))
    s["brand"] = burst
    s["lagi"] = hstack([text_img("BANYAK LAGI?!", FONT_FUN, 58, WHITE, sw=7), emoji("😳", 52)])
    # PRODUK
    s["kemuning"] = tag("KEMUNING HITAM", "🌼", AMBER)
    s["bidara"] = tag("MADU BIDARA", "🍯", HERB)
    s["aura"] = tag("AURA 7 BUNGA", "🌸", PINK)
    s["tiga"] = vstack([text_img("3 BAU WANGI", FONT_FUN, 60, YELLOW, sw=7),
                        hstack([text_img("PILIH KEGEMARAN!", FONT_FUN, 40, WHITE, sw=5), emoji("✨", 40)])], gap=-6)
    s["rays"] = rays(330)
    # CTA
    s["nak"] = vstack([text_img("NAK MANDI WANGI", FONT_FUN, 50, WHITE, sw=6),
                       hstack([text_img("MACAM NI?", FONT_FUN, 58, YELLOW, sw=7), emoji("🤩", 52)])], gap=-6)
    s["cta"] = pill(hstack([emoji("🛒", 46), text_img("TEKAN BAKUL KUNING", FONT_FUN, 36, BLACK, stroke=YELLOW, sw=1,
                                                          shadow=False)]), YELLOW, pad=(26, 16), bw=6)
    s["cta_sub"] = text_img("CUBA SENDIRI!", FONT_FUN, 34, WHITE, sw=5)
    s["point"] = emoji("👇", 64)
    s["sparkle"] = emoji("✨", 40)
    s["bubble"] = emoji("🫧", 40)
    s["flower"] = emoji("🌸", 40)
    return s


PUNCHES = [  # (masa, kuat zoom, tempoh[, 'hold'])
    (0.00, 0.18, 0.55),
    (3.70, 0.06, 0.40),
    (10.20, 0.10, 0.50),
    (13.00, 0.12, 1.20, "hold"),
    (16.20, 0.07, 0.40),
    (30.00, 0.16, 0.70),
    (35.20, 0.07, 0.40),
    (39.50, 0.06, 0.40),
    (44.20, 0.06, 0.40),
    (47.80, 0.06, 0.40),
    (50.20, 0.14, 1.40, "hold"),
    (54.00, 0.10, 0.50),
    (55.80, 0.06, 0.40),
]
SHAKES = [(0.05, 0.35, 10), (10.2, 0.3, 8), (30.0, 0.4, 12), (50.2, 0.3, 8)]
FLASHES = [(0.0, 0.18), (10.2, 0.10), (30.0, 0.18), (50.2, 0.15), (54.0, 0.12)]

CONFETTI = Confetti(50.25, y0=560)
SFX_VOLUME = 0.6
SFX_EVENTS = [
    (0.0, "boom", dict(vol=0.5)),
    (0.05, "pop", {}),
    (0.4, "pop", dict(f0=600, f1=1600)),
    (1.0, "whoosh", {}),
    (3.7, "pop", dict(f0=400, f1=1100)),
    (10.15, "whoosh", {}),
    (10.25, "boom", dict(vol=0.4)),
    (13.0, "pop", dict(f0=500, f1=1500)),
    (16.2, "whoosh", {}),
    (22.6, "pop", dict(vol=0.3)),
    (30.0, "boom", {}),
    (30.05, "ding", {}),
    (35.2, "pop", {}),
    (39.5, "pop", dict(f0=700, f1=1500, vol=0.35)),
    (44.2, "pop", dict(f0=700, f1=1500, vol=0.35)),
    (47.8, "pop", dict(f0=700, f1=1500, vol=0.35)),
    (50.2, "boom", dict(vol=0.5)),
    (50.25, "ching", {}),
    (54.0, "whoosh", {}),
    (55.8, "ding", {}),
]


def draw_overlays(canvas, t, S, dur):
    # bar progress (retention)
    d = ImageDraw.Draw(canvas)
    d.rectangle((0, 0, W, 7), fill=(0, 0, 0, 110))
    d.rectangle((0, 0, int(W * t / dur), 7), fill=YELLOW + (255,))

    # 1) HOOK 0–3.6s
    sc, a = pop(t, 0.05, 3.6, elastic=True)
    place(canvas, S["hook1"], W / 2, 360, sc, rot=1.5 * math.sin(t * 6), alpha=a)
    sc, a = pop(t, 0.4, 3.6, elastic=True)
    place(canvas, S["hook2"], W / 2, 432, sc * (1 + 0.04 * math.sin(t * 12)), alpha=a)
    sc, a = pop(t, 1.0, 3.6)
    place(canvas, S["brand_chip"], W / 2, 510, sc, alpha=a)
    sparkles(canvas, S["bubble"], t, 0.4, 3.6, [(60, 320), (520, 300), (500, 520), (80, 520)])

    # 2) TAPI ORDER LAGI 3.7–7.2s
    sc, a = pop(t, 3.7, 7.2)
    place(canvas, S["order"], W / 2, 400, sc * (1 + 0.03 * math.sin(t * 10)), alpha=a)

    # 3) STOK BARU SAMPAI 10.2–12.8s – masuk dari kanan
    if 10.2 <= t <= 12.8:
        x = W + 300 - (W / 2 + 300) * ease_out_back(clamp((t - 10.2) / 0.4), 1.6)
        place(canvas, S["stok"], x, 160, 1 + 0.04 * math.sin(t * 12), alpha=clamp((12.8 - t) / 0.2))

    # 4) SEKOTAK PENUH 13.0–15.8s
    sc, a = pop(t, 13.0, 15.8, elastic=True)
    place(canvas, S["sekotak"], W / 2, 150, sc * (1 + 0.05 * math.sin(t * 10)), alpha=a)
    sparkles(canvas, S["sparkle"], t, 13.2, 15.8, [(80, 260), (500, 250), (300, 300)])

    # 5) ADA PARCEL LAGI 16.2–19.5s
    sc, a = pop(t, 16.2, 19.5)
    place(canvas, S["parcel"], W / 2, 160, sc, alpha=a)

    # 6) BALUT KEMAS 22.6–25.8s
    sc, a = pop(t, 22.6, 25.8)
    place(canvas, S["kemas"], W / 2, 160, sc, alpha=a)

    # 7) BRAND STAMP 30.0–33.8s
    if 30.0 <= t <= 33.8:
        out = clamp((33.8 - t) / 0.25)
        k = clamp((t - 30.0) / 0.22)
        slam = 1 + 2.0 * (1 - ease_out_cubic(k)) if k < 1 else 1 + 0.05 * math.sin((t - 30.22) * 11) * math.exp(
            -(t - 30.22) * 1.5)
        place(canvas, S["brand"], 395, 205, 0.8 * slam, rot=-(t - 30.0) * 12, alpha=out * clamp(k * 3))

    # 8) BANYAK LAGI 35.2–38.6s
    sc, a = pop(t, 35.2, 38.6, elastic=True)
    place(canvas, S["lagi"], W / 2, 150, sc * (1 + 0.04 * math.sin(t * 11)), alpha=a)

    # 9) NAMA PRODUK – chip melantun di atas botol
    for key, t0, t1, x in (("kemuning", 39.5, 43.6, 400), ("bidara", 44.2, 47.6, 200), ("aura", 47.8, 50.1, 170)):
        sc, a = pop(t, t0, t1, elastic=True)
        x = clamp(x, S[key].width / 2 + 10, W - S[key].width / 2 - 10)
        place(canvas, S[key], x, 410 + 8 * math.sin((t - t0) * 5), sc, alpha=a)

    # 10) 3 BAU WANGI 50.2–53.8s – sinar + confetti
    if 50.2 <= t <= 53.8:
        out = clamp((53.8 - t) / 0.25)
        place(canvas, S["rays"], W / 2, 250, 0.9 + 0.1 * math.sin(t * 3), rot=(t - 50.2) * 30,
              alpha=out * clamp((t - 50.2) / 0.2))
        sc, a = pop(t, 50.25, 53.8, elastic=True)
        place(canvas, S["tiga"], W / 2, 250, sc * (1 + 0.04 * math.sin(t * 9)), alpha=a)
        # kilauan melintasi botol
        sx = -100 + ((t - 50.4) % 1.3) / 1.3 * (W + 200)
        shine = Image.new("RGBA", (W, H))
        ImageDraw.Draw(shine).polygon([(sx, 480), (sx + 40, 480), (sx - 30, 1000), (sx - 70, 1000)],
                                      fill=(255, 255, 255, int(70 * out)))
        canvas.alpha_composite(shine)
    CONFETTI.draw(canvas, t)

    # 11) CTA 54.0–akhir
    sc, a = pop(t, 54.0, dur + 1, elastic=True)
    place(canvas, S["nak"], W / 2, 120, sc * (1 + 0.03 * math.sin(t * 8)), alpha=a)
    sparkles(canvas, S["flower"], t, 54.3, dur + 1, [(70, 60), (510, 190)])
    if t >= 55.8:
        sc, _ = pop(t, 55.8, dur + 1, elastic=True)
        beat = 1 + 0.07 * max(0, math.sin((t - 55.8) * 2 * math.pi * 2.2))
        place(canvas, S["cta"], W / 2, 820, sc * beat)
        sc2, _ = pop(t, 56.05, dur + 1)
        place(canvas, S["cta_sub"], W / 2, 742, sc2)
        place(canvas, S["point"], W / 2, 920 + 14 * abs(math.sin((t - 55.8) * 7)), sc2)
        sx = -120 + ((t - 56.1) % 1.1) / 1.1 * (W + 240)
        shine = Image.new("RGBA", (W, H))
        ImageDraw.Draw(shine).polygon([(sx, 780), (sx + 26, 780), (sx - 14, 860), (sx - 40, 860)],
                                      fill=(255, 255, 255, 120))
        canvas.alpha_composite(shine)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    render(sys.modules[__name__],
           sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "assets", "dherbs_original.mp4"),
           sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "output", "dherbs_hook.mp4"))
