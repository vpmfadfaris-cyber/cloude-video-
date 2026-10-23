"""Video 1: unboxing popcorn 1 kilo RM18.

Guna:  python3 popcorn.py [assets/original.mp4] [output/popcorn_hook.mp4]
"""
import math
import os
import sys

from motion import *  # noqa: F401,F403
from motion import Image, ImageDraw, render

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



PUNCHES = [  # (masa, kuat zoom, tempoh) – zoom 'punch' pada beat penting
    (0.00, 0.18, 0.55),
    (3.50, 0.07, 0.40),
    (12.70, 0.07, 0.40),
    (15.00, 0.14, 1.20, "hold"),
    (22.25, 0.07, 0.40),
    (27.20, 0.20, 0.90),
    (29.00, 0.10, 0.50),
    (31.50, 0.06, 0.40),
    (33.00, 0.08, 0.50),
]
SHAKES = [(0.05, 0.35, 10), (15.0, 0.30, 7), (27.2, 0.45, 14)]
FLASHES = [(0.0, 0.18), (15.0, 0.12), (27.2, 0.22)]


CONFETTI = Confetti(27.22)
SFX_VOLUME = 0.8
SFX_EVENTS = [
    (0.0, "boom", dict(vol=0.5)),
    (0.05, "pop", {}),
    (0.35, "whoosh", {}),
    (3.45, "pop", dict(f0=400, f1=1100)),
    (3.6, "pop", dict(f0=700, f1=1600, vol=0.3)),
    (5.35, "whoosh", {}),
    (6.1, "pop", {}),
    (12.5, "ding", {}),
    (15.0, "boom", dict(vol=0.45)),
    (15.05, "pop", dict(f0=500, f1=1500)),
    (22.25, "pop", {}),
    (25.6, "whoosh", dict(dur=0.5, vol=0.3)),
    (27.2, "boom", {}),
    (27.25, "ching", {}),
    (27.6, "pop", dict(f0=600, f1=1700)),
    (31.2, "pop", {}),
    (33.0, "whoosh", {}),
    (33.05, "ding", {}),
]


def draw_overlays(canvas, t, S, dur):
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
    CONFETTI.draw(canvas, t)

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



if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    render(sys.modules[__name__],
           sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "assets", "original.mp4"),
           sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "output", "popcorn_hook.mp4"))
