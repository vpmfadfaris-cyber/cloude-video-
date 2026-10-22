"""Composite motion graphics, hook, zoom punches and shakes over the graded video."""
import math, subprocess, sys, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SRC, AUDIO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
T_START = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
T_END = float(sys.argv[5]) if len(sys.argv) > 5 else 52.56

BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
XBOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
YEL = (255, 200, 40)
WHITE = (255, 255, 255)
INK = (18, 18, 22)
GLASS = (14, 14, 18, 190)

CUTS = [0.0, 6.1, 9.4667, 14.5, 19.5333, 22.9, 28.3333, 31.7, 43.0333, 48.0667, 52.6]
SHAKES = [(0.0, 16), (14.45, 14), (44.0, 10), (50.5, 14)]


# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out_cubic(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in_out(x): x = clamp(x); return x * x * (3 - 2 * x)
def ease_out_back(x, s=1.9):
    x = clamp(x); x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


@functools.lru_cache(None)
def font(path, size): return ImageFont.truetype(path, size)


# ---------- sprite builders ----------
def shadowed(img, blur=14, offset=(0, 8), alpha=150, pad=40):
    w, h = img.size
    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    a = img.split()[3].point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 255)); sh.putalpha(a)
    out.alpha_composite(sh, (pad + offset[0], pad + offset[1]))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(img, (pad, pad))
    return out


@functools.lru_cache(None)
def text_sprite(text, size, color=WHITE, path=BLACK, stroke=0, stroke_col=INK, maxw=900, track=0):
    f = font(path, size)
    while f.getlength(text) + track * len(text) > maxw and size > 20:
        size -= 4; f = font(path, size)
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    w = int(f.getlength(text) + track * (len(text) - 1)) + 2 * stroke + 4
    img = Image.new("RGBA", (w, b - t + 2 * stroke + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = stroke + 2
    for ch in text:
        d.text((x, -t + stroke + 2), ch, font=f, fill=color, stroke_width=stroke, stroke_fill=stroke_col)
        x += f.getlength(ch) + track
    return shadowed(img)


@functools.lru_cache(None)
def pill_sprite(text, size, bg=YEL, fg=INK, path=XBOLD, padx=34, pady=18, radius=None, icon=None):
    f = font(path, size)
    l, t, r, b = f.getbbox(text)
    tw, th = int(f.getlength(text)), b - t
    iw = int(th * 1.15) + 16 if icon else 0
    w, h = tw + 2 * padx + iw, th + 2 * pady
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius if radius is not None else h // 2, fill=bg)
    if icon == "check":
        draw_check(d, padx + th * 0.575, h / 2, th * 0.575, fg, bg)
    d.text((padx + iw, pady - t), text, font=f, fill=fg)
    return shadowed(img, blur=16, alpha=120)


def draw_check(d, cx, cy, r, circle, mark, width=None):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=circle)
    wdt = width or max(4, int(r * 0.28))
    pts = [(cx - r * 0.45, cy + r * 0.02), (cx - r * 0.12, cy + r * 0.35), (cx + r * 0.5, cy - r * 0.32)]
    d.line(pts, fill=mark, width=wdt, joint="curve")


@functools.lru_cache(None)
def grad_top():
    a = np.zeros((H, W), np.uint8)
    ys = np.arange(H)
    a[:] = (np.clip(1 - ys / 900, 0, 1) ** 1.6 * 120).astype(np.uint8)[:, None]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); img.putalpha(Image.fromarray(a))
    return img


# ---------- compositing ----------
def place(canvas, spr, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.01: return
    s = spr
    if rot: s = s.rotate(rot, resample=Image.BICUBIC, expand=True)
    if abs(scale - 1) > 1e-3:
        s = s.resize((max(1, int(s.width * scale)), max(1, int(s.height * scale))), Image.BICUBIC)
    if alpha < 0.999:
        s = s.copy(); s.putalpha(s.split()[3].point(lambda v: int(v * alpha)))
    x, y = int(cx - s.width / 2), int(cy - s.height / 2)
    canvas.alpha_composite(s, (max(0, x), max(0, y)),
                           (max(0, -x), max(0, -y)))


def pop(t, t0, t1, d_in=0.28, d_out=0.2):
    """scale, alpha for an element visible in [t0, t1] with pop in / fade out."""
    if t < t0 or t > t1 + d_out: return 0, 0
    if t < t0 + d_in:
        p = (t - t0) / d_in
        return 0.55 + 0.45 * ease_out_back(p), ease_out_cubic(p * 1.6)
    if t > t1:
        p = (t - t1) / d_out
        return 1 - 0.12 * p, 1 - p
    return 1, 1


def slide(t, t0, t1, dx=-260, d_in=0.32, d_out=0.2):
    if t < t0 or t > t1 + d_out: return None
    if t < t0 + d_in:
        p = ease_out_cubic((t - t0) / d_in); return dx * (1 - p), p
    if t > t1:
        p = (t - t1) / d_out; return 0, 1 - p
    return 0, 1


# ---------- scenes ----------
def scene_overlays(c, t):
    # HOOK 0 - 2.7
    s, a = pop(t, 0.0, 2.6, 0.22)
    place(c, pill_sprite("JANGAN SCROLL DULU!", 44, bg=(230, 30, 40), fg=WHITE), W / 2, 250, s, a,
          rot=-3 * (1 - clamp(t / 0.3)))
    s, a = pop(t, 0.15, 2.6)
    place(c, text_sprite("RUMAH BAU", 138, WHITE), W / 2, 410, s, a)
    s, a = pop(t, 0.55, 2.6)
    wob = math.sin(t * 9) * 1.2 if 0.8 < t < 2.6 else 0
    place(c, text_sprite("PASIR KUCING?", 138, YEL), W / 2, 560, s, a, rot=wob)
    sl = slide(t, 0.95, 2.6, dx=0)
    if sl:
        _, a = sl
        place(c, text_sprite("INI JAWAPAN DIA  ↓", 50, WHITE, XBOLD, track=2), W / 2,
              700 + 20 * (1 - a) + 8 * math.sin(t * 7), 1, a)

    # Product intro 3.0 - 6.0
    s, a = pop(t, 3.0, 6.0)
    place(c, pill_sprite("PRODUK BARU", 40), W / 2, 260, s, a)
    s, a = pop(t, 3.15, 6.0)
    place(c, text_sprite("FROSTY PEARL", 118, WHITE, track=4), W / 2, 390, s, a)
    for i, (txt, tt) in enumerate([("MINERAL", 4.55), ("+", 4.7), ("CASSAVA", 4.85)]):
        s, a = pop(t, tt, 6.0)
        x = [W / 2 - 230, W / 2, W / 2 + 230][i]
        spr = text_sprite("+", 70, YEL) if txt == "+" else pill_sprite(txt, 38, bg=GLASS, fg=WHITE)
        place(c, spr, x, 530, s, a)

    # 3X absorption 8.5 - 11.8
    if 8.5 <= t <= 12.0:
        n = 1 if t < 8.95 else 2 if t < 9.35 else 3
        tn = [8.55, 8.95, 9.35][n - 1]
        bump = 1 + 0.25 * math.exp(-(t - tn) * 14)
        s, a = pop(t, 8.5, 11.8)
        place(c, text_sprite(f"{n}X", 280, YEL), W / 2, 380, s * bump, a)
        s, a = pop(t, 8.7, 11.8)
        place(c, pill_sprite("PENYERAPAN BAU", 44, bg=GLASS, fg=WHITE), W / 2, 580, s, a)

    # 3 kali ganda slam 14.45 - 16.4
    if 14.45 <= t <= 16.6:
        p = (t - 14.45) / 0.18
        s = 2.3 - 1.3 * ease_out_cubic(p)
        a = clamp(p * 2) * (1 - clamp((t - 16.4) / 0.2))
        place(c, pill_sprite("3X GANDA!", 96, bg=YEL, fg=INK, padx=46, pady=26, radius=26), W / 2, 380, s, a, rot=-6)
        a2 = clamp((t - 14.8) / 0.25) * (1 - clamp((t - 16.4) / 0.2))
        place(c, text_sprite("LEBIH KUAT SERAP BAU", 54, WHITE, XBOLD), W / 2, 540, 1, a2)

    # Bye bau busuk 17.5 - 20.0
    s, a = pop(t, 17.5, 19.9)
    if a > 0:
        spr = pill_sprite("BAU BUSUK", 72, bg=GLASS, fg=WHITE, padx=44, pady=24, radius=24)
        p = ease_in_out((t - 17.95) / 0.3)
        if p > 0:
            spr = spr.copy(); d = ImageDraw.Draw(spr)
            x0, x1 = 60, spr.width - 60
            d.line((x0, spr.height / 2 + 6, x0 + (x1 - x0) * p, spr.height / 2 - 6), fill=(235, 40, 50), width=12)
        place(c, pill_sprite("BYE-BYE", 40, bg=(235, 40, 50), fg=WHITE), W / 2, 270, s, a)
        place(c, spr, W / 2, 400, s, a)

    # Tekstur 20.5 - 22.4
    s, a = pop(t, 20.5, 22.4)
    place(c, pill_sprite("TEKSTUR PREMIUM", 46, bg=GLASS, fg=WHITE), W / 2, 300, s, a)

    # Tak berdebu 22.5 - 26.2
    s, a = pop(t, 22.5, 26.2)
    place(c, pill_sprite("TAK BERDEBU", 64, bg=YEL, fg=INK, icon="check", padx=40, pady=24), W / 2, 330, s, a)
    s, a = pop(t, 24.0, 26.2)
    place(c, text_sprite("Selamat untuk kucing & majikan", 46, WHITE, XBOLD), W / 2, 470, s, a)

    # Clumping 26.5 - 30.1
    s, a = pop(t, 26.5, 30.1)
    place(c, pill_sprite("CLUMPING", 42, bg=GLASS, fg=WHITE), W / 2, 260, s, a)
    s, a = pop(t, 28.45, 30.1)
    place(c, text_sprite("SUPER CEPAT", 130, YEL), W / 2, 400, s, a)

    # 5 second timer 30.5 - 33.5
    if 30.5 <= t <= 33.7:
        s, a = pop(t, 30.5, 33.5)
        draw_timer(c, t, W / 2, 400, s, a)

    # Checklist 34.5 - 42.3
    items = [("Kukuh", 34.5), ("Tak mudah hancur", 35.5), ("Tak melekat di box", 37.5), ("Senang nak cedok", 39.5)]
    sl = slide(t, 34.4, 42.2, dx=0, d_in=0.25)
    if sl:
        _, pa = sl
        panel = checklist_panel()
        place(c, panel, W / 2, 200 + panel.height / 2 - 40, 1, pa * 0.92)
        for i, (txt, tt) in enumerate(items):
            r = slide(t, tt, 42.2, dx=-120)
            if r:
                dx, a = r
                place(c, check_row(txt), W / 2 + dx, 250 + i * 118, 1, a * pa)

    # 4.5 KG 44.0 - 46.0
    if 43.95 <= t <= 46.3:
        v = 4.5 * ease_out_cubic((t - 44.0) / 0.55)
        s, a = pop(t, 44.0, 46.0, 0.2)
        place(c, text_sprite(f"{v:.1f}", 260, WHITE), W / 2 - 90, 400, s, a)
        place(c, text_sprite("KG", 130, YEL), W / 2 + 230, 440, s, a)

    # 1 beg = 2 minggu / 2 kucing 46.05 - 50.3
    s, a = pop(t, 46.05, 50.3)
    place(c, pill_sprite("1 BEG BOLEH TAHAN", 44, bg=YEL, fg=INK), W / 2, 260, s, a)
    for i, (big, small) in enumerate([("2", "MINGGU"), ("2", "KUCING")]):
        s, a = pop(t, 47.55 + i * 0.15, 50.3)
        place(c, stat_card(big, small), W / 2 + (-210 if i == 0 else 210), 470, s, a)

    # CTA 50.5 - end
    if t >= 50.45:
        draw_cta(c, t)


@functools.lru_cache(None)
def checklist_panel():
    w, h = 820, 540
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((0, 0, w - 1, h - 1), 40, fill=(14, 14, 18, 175))
    return shadowed(img, blur=20, alpha=110)


@functools.lru_cache(None)
def check_row(text):
    w, h = 720, 100
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    draw_check(d, 40, h / 2, 34, YEL, INK, 8)
    f = font(XBOLD, 54); l, t, r, b = f.getbbox(text)
    d.text((100, (h - (b - t)) / 2 - t), text, font=f, fill=WHITE)
    return img


@functools.lru_cache(None)
def stat_card(big, small):
    w, h = 360, 250
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(14, 14, 18, 200), outline=YEL, width=4)
    f = font(BLACK, 140); l, t, r, b = f.getbbox(big)
    d.text(((w - f.getlength(big)) / 2, 20 - t), big, font=f, fill=YEL)
    f2 = font(XBOLD, 48); l2, t2, r2, b2 = f2.getbbox(small)
    d.text(((w - f2.getlength(small)) / 2, 180 - t2), small, font=f2, fill=WHITE)
    return shadowed(img, blur=18, alpha=120)


def draw_timer(c, t, cx, cy, s, a):
    R = 150
    size = 2 * R + 60
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    o = 30
    d.ellipse((o, o, o + 2 * R, o + 2 * R), fill=(14, 14, 18, 190))
    d.arc((o + 10, o + 10, o + 2 * R - 10, o + 2 * R - 10), 0, 360, fill=(255, 255, 255, 60), width=16)
    p = clamp((t - 30.5) / 2.0)
    if p > 0:
        d.arc((o + 10, o + 10, o + 2 * R - 10, o + 2 * R - 10), -90, -90 + 360 * p, fill=YEL, width=16)
    if t < 32.5:
        n = 5 - int(clamp((t - 30.5) / 0.4, 0, 4.999))
        f = font(BLACK, 170); txt = str(n); l, tt, r, b = f.getbbox(txt)
        d.text((size / 2 - f.getlength(txt) / 2, size / 2 - (b - tt) / 2 - tt - 10), txt, font=f, fill=WHITE)
        tn = 30.5 + (5 - n) * 0.4
        bump = 1 + 0.12 * math.exp(-(t - tn) * 16)
    else:
        draw_check(d, size / 2, size / 2, 85, YEL, INK, 22)
        bump = 1 + 0.25 * math.exp(-(t - 32.5) * 12)
    place(c, shadowed(img, blur=18, alpha=120), cx, cy, s * bump, a)
    s2, a2 = pop(t, 30.7, 33.5)
    place(c, pill_sprite("BEKU DALAM 5 SAAT", 40), cx, cy + R + 70, s2, a2 * a)


def draw_cta(c, t):
    s, a = pop(t, 50.5, 99, 0.3)
    pulse = 1 + 0.035 * math.sin((t - 50.5) * 2 * math.pi * 2.2) if t > 50.9 else 1
    place(c, text_sprite("JANGAN TUNGGU LAGI!", 62, WHITE), W / 2, 260, s, a)
    place(c, cta_button(), W / 2, 420, s * pulse, a)
    s2, a2 = pop(t, 50.8, 99)
    place(c, text_sprite("Frosty Pearl  •  Pawmised Land", 38, (235, 235, 235), XBOLD), W / 2, 560, s2, a2)
    # bouncing arrow toward the yellow basket (bottom-left on TikTok)
    s3, a3 = pop(t, 51.0, 99)
    bounce = 18 * abs(math.sin((t - 51.0) * math.pi * 2.4))
    place(c, arrow_sprite(), 150 - bounce * 0.5, 1620 + bounce, s3, a3)


@functools.lru_cache(None)
def cta_button():
    f = font(BLACK, 66); txt = "TEKAN BEG KUNING"
    l, t, r, b = f.getbbox(txt)
    icon = 80
    w, h = int(f.getlength(txt)) + icon + 110, 150
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 40, fill=YEL)
    # basket icon
    bx, by = 45, h / 2 - 32
    d.polygon([(bx, by + 20), (bx + icon, by + 20), (bx + icon - 10, by + 64), (bx + 10, by + 64)], fill=INK)
    d.arc((bx + 18, by - 12, bx + icon - 18, by + 40), 180, 360, fill=INK, width=8)
    d.text((bx + icon + 25, (h - (b - t)) / 2 - t), txt, font=f, fill=INK)
    return shadowed(img, blur=22, alpha=150)


@functools.lru_cache(None)
def arrow_sprite():
    img = Image.new("RGBA", (150, 180), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((55, 0, 95, 100), fill=YEL)
    d.polygon([(10, 95), (140, 95), (75, 175)], fill=YEL)
    return shadowed(img.rotate(-25, resample=Image.BICUBIC, expand=True), blur=12, alpha=150)


# ---------- camera ----------
def camera(t):
    """zoom, dx, dy"""
    i = max(k for k in range(len(CUTS) - 1) if CUTS[k] <= t + 1e-6)
    st, en = CUTS[i], CUTS[i + 1]
    z = 1.0 + 0.035 * ((t - st) / (en - st))  # slow push-in per shot
    if t < 0.75:
        z *= 1.0 + 0.22 * (1 - ease_out_cubic(t / 0.75))  # hook punch
    elif t - st < 0.3 and st > 0:
        z *= 1.0 + 0.07 * (1 - ease_out_cubic((t - st) / 0.3))  # cut punch
    for ts, amp in [(14.45, 0.12), (44.0, 0.07), (50.5, 0.1)]:
        if ts <= t < ts + 0.4:
            z *= 1.0 + amp * (1 - ease_out_cubic((t - ts) / 0.4))
    dx = dy = 0.0
    for ts, amp in SHAKES:
        if ts <= t < ts + 0.4:
            k = amp * math.exp(-(t - ts) * 9)
            dx += k * math.sin(t * 97); dy += k * math.cos(t * 83)
    return z, dx, dy


def flash(t):
    v = 0.0
    for ts, d in [(0.0, 0.25), (50.5, 0.22), (14.45, 0.12)]:
        if ts <= t < ts + d: v = max(v, 0.85 * (1 - (t - ts) / d))
    return v


def main():
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(T_START), "-i", SRC, "-t", str(T_END - T_START),
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-ss", str(T_START), "-t", str(T_END - T_START), "-i", AUDIO,
                            "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart",
                            "-shortest", OUT], stdin=subprocess.PIPE)
    fsz = W * H * 3; k = 0
    gt = grad_top()
    while True:
        buf = dec.stdout.read(fsz)
        if len(buf) < fsz: break
        t = T_START + k / FPS; k += 1
        img = Image.frombuffer("RGB", (W, H), buf)
        z, dx, dy = camera(t)
        if z > 1.0005 or dx or dy:
            cw, ch = W / z, H / z
            x0 = (W - cw) / 2 - dx / z; y0 = (H - ch) / 2 - dy / z
            img = img.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)
        c = img.convert("RGBA")
        c.alpha_composite(gt)
        scene_overlays(c, t)
        fl = flash(t)
        if fl > 0:
            c = Image.blend(c, Image.new("RGBA", (W, H), (255, 255, 255, 255)), fl)
        enc.stdin.write(c.convert("RGB").tobytes())
        if k % 150 == 0: print(f"t={t:.1f}", flush=True)
    enc.stdin.close(); enc.wait(); dec.wait()


if __name__ == "__main__":
    main()
