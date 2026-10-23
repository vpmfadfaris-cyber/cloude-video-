#!/usr/bin/env python3
"""Tambah hook jualan + animasi overlay pada video iklan makanan kucing Catto Premium.

Guna:  python3 edit_video.py INPUT.mp4 OUTPUT.mp4
Perlu: ffmpeg, Pillow, numpy, font Inter Black + Noto Color Emoji.
"""
import math
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 576, 1024, 30
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

YELLOW = (255, 214, 0, 255)
RED = (235, 30, 60, 255)
PINK = (214, 40, 160, 255)
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_back(t, s=1.9):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def ease_out_cubic(t):
    return 1 - (1 - clamp(t)) ** 3


def prog(t, start, dur):
    return clamp((t - start) / dur)


# ---------------------------------------------------------------- drawing helpers
def font(size):
    return ImageFont.truetype(FONT, size)


def emoji(ch, size):
    f = ImageFont.truetype(EMOJI_FONT, 109)
    img = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((0, 0), ch, font=f, embedded_color=True)
    img = img.crop(img.getbbox())
    return img.resize((size, int(size * img.height / img.width)), Image.LANCZOS)


def text_img(text, size, fill=WHITE, stroke=6, stroke_fill=BLACK, shadow=True):
    f = font(size)
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    pad = 12
    img = Image.new("RGBA", (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l + 4, pad - t + 6), text, font=f, fill=(0, 0, 0, 170),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(4)))
        d = ImageDraw.Draw(img)
    d.text((pad - l, pad - t), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return img


def pill(parts, size, bg, fg=WHITE, pad=(22, 12), radius=None, outline=None, tilt=0):
    """parts: list of str (text) or Image (emoji). Draw on rounded box."""
    f = font(size)
    imgs = []
    for p in parts:
        if isinstance(p, str):
            l, t, r, b = f.getbbox(p)
            im = Image.new("RGBA", (r - l, size + 6), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((-l, 0), p, font=f, fill=fg)
            imgs.append(im)
        else:
            imgs.append(p)
    gap = 10
    cw = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
    ch = max(i.height for i in imgs)
    bw, bh = cw + pad[0] * 2, ch + pad[1] * 2
    radius = bh // 2 if radius is None else radius
    m = 14
    img = Image.new("RGBA", (bw + m * 2, bh + m * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m + 3, m + 7, m + bw + 3, m + bh + 7), radius, fill=(0, 0, 0, 140))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(5)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((m, m, m + bw, m + bh), radius, fill=bg,
                        outline=outline, width=4 if outline else 0)
    x = m + pad[0]
    for i in imgs:
        img.alpha_composite(i, (x, m + pad[1] + (ch - i.height) // 2))
        x += i.width + gap
    if tilt:
        img = img.rotate(tilt, resample=Image.BICUBIC, expand=True)
    return img


def place(frame, img, cx, cy, scale=1.0, alpha=1.0, angle=0.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    im = img
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if abs(angle) > 0.05:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy()
        im.putalpha(a)
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    frame.alpha_composite(im, (max(0, x), max(0, y)),
                          (max(0, -x), max(0, -y)))


def starburst(r, points=16, fill=YELLOW):
    s = r * 2 + 8
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    c = s / 2
    pts = []
    for i in range(points * 2):
        rr = r if i % 2 == 0 else r * 0.80
        a = math.pi * i / points
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    ImageDraw.Draw(img).polygon(pts, fill=fill, outline=BLACK, width=4)
    return img


def rays(r, n=14):
    s = r * 2
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = a0 + math.pi / n
        d.polygon([(r, r), (r + r * math.cos(a0), r + r * math.sin(a0)),
                   (r + r * math.cos(a1), r + r * math.sin(a1))], fill=(255, 240, 150, 90))
    return img.filter(ImageFilter.GaussianBlur(2))


def sparkle(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c, r, w = size / 2, size / 2, size / 9
    d.polygon([(c, 0), (c + w, c - w), (size, c), (c + w, c + w), (c, size),
               (c - w, c + w), (0, c), (c - w, c - w)], fill=(255, 250, 210, 255))
    glow = img.filter(ImageFilter.GaussianBlur(size / 8))
    return Image.alpha_composite(glow, img)


# ---------------------------------------------------------------- assets
A = {
    "h1": text_img("KUCING KORANG", 50),
    "h2": pill(["KURUS & BULU", "TAK GEBU?"], 33, RED, tilt=-3),
    "h_sad": emoji("😿", 84),
    "h3": text_img("INI RAHSIA DIA", 54, fill=YELLOW),
    "h_down": emoji("👇", 64),
    "burst": starburst(92),
    "rays": rays(170),
    "pct_lbl": text_img("PROTEIN", 22, stroke=0, fill=BLACK, shadow=False),
    "pct_lbl2": text_img("HAIWAN", 22, stroke=0, fill=BLACK, shadow=False),
    "tag1": pill([emoji("🐔", 34), "AYAM", "+", emoji("🐟", 34), "SALMON SEGAR"], 28, WHITE, fg=BLACK,
                 outline=PINK),
    "tag2": pill([emoji("✅", 32), "SESUAI SEMUA UMUR"], 28, PINK),
    "gebu": text_img("BULU GEBU", 64, fill=WHITE),
    "gebu2": pill(["& SIHAT BERKILAT"], 32, YELLOW, fg=BLACK),
    "sparkle": sparkle(48),
    "suka": pill(["KUCING PUN SUKA!", emoji("😻", 44)], 38, WHITE, fg=BLACK, outline=YELLOW),
    "cta_top": text_img("TEKAN BAKUL KUNING", 40, fill=YELLOW),
    "cta_btn": pill([emoji("🛒", 46), "BELI SEKARANG"], 44, (255, 70, 30, 255), pad=(34, 20),
                    outline=WHITE),
    "cta_down": emoji("👇", 70),
    "stok": pill([emoji("🔥", 30), "STOK TERHAD!"], 28, BLACK, fg=YELLOW, tilt=4),
}
PCT_FONT = font(64)


def pct_img(n):
    txt = f"{n}%"
    l, t, r, b = PCT_FONT.getbbox(txt)
    img = Image.new("RGBA", (r - l + 4, b - t + 4), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((2 - l, 2 - t), txt, font=PCT_FONT, fill=RED)
    return img


SPARKLES = [(0.13, 0.12, 0.0), (0.86, 0.10, 0.4), (0.92, 0.33, 0.8), (0.08, 0.36, 1.1),
            (0.25, 0.55, 0.3), (0.78, 0.58, 0.9), (0.50, 0.05, 0.6), (0.65, 0.42, 1.3),
            (0.18, 0.80, 0.5), (0.85, 0.82, 1.0)]

# punch-in zoom moments (time, strength) and white flashes
PUNCHES = [(0.0, 0.10), (5.0, 0.08), (14.0, 0.06), (19.4, 0.05), (22.0, 0.07)]
FLASHES = [0.0, 5.0, 22.0]


# ---------------------------------------------------------------- per-frame compositing
def zoom_factor(t):
    z = 1.0
    for t0, s in PUNCHES:
        dt = t - t0
        if 0 <= dt < 0.6:
            z += s * (1 - ease_out_cubic(dt / 0.6))
    return z


def overlays(frame, t):
    # ---- HOOK 0 - 4.8s
    if t < 2.5:
        p = ease_out_back(prog(t, 0.05, 0.35))
        shake = math.sin(t * 40) * 4 * (1 - prog(t, 0.3, 0.6))
        place(frame, A["h1"], W / 2 + shake, 130, scale=p)
        p2 = ease_out_back(prog(t, 0.35, 0.4))
        pulse = 1 + 0.04 * math.sin(t * 9) * prog(t, 0.8, 0.2)
        place(frame, A["h2"], W / 2, 210, scale=p2 * pulse)
        pe = ease_out_back(prog(t, 0.75, 0.35))
        place(frame, A["h_sad"], W / 2, 305 + 8 * math.sin(t * 6), scale=pe, angle=10 * math.sin(t * 5))
    elif t < 4.9:
        p = ease_out_back(prog(t, 2.5, 0.35))
        shake = math.sin(t * 45) * 5 * (1 - prog(t, 2.8, 0.5))
        alpha = 1 - prog(t, 4.6, 0.3)
        place(frame, A["h3"], W / 2 + shake, 150, scale=p, alpha=alpha)
        bounce = abs(math.sin((t - 2.5) * 6)) * 18
        place(frame, A["h_down"], W / 2, 235 + bounce, scale=ease_out_back(prog(t, 2.8, 0.3)), alpha=alpha)

    # ---- 85% PROTEIN BADGE 5.8 - 13.6s
    if 5.8 <= t < 13.6:
        p = ease_out_back(prog(t, 5.8, 0.45))
        a = 1 - prog(t, 13.3, 0.3)
        cx, cy = W - 108, 190
        place(frame, A["rays"], cx, cy, scale=p, alpha=a, angle=-t * 30)
        pulse = 1 + 0.05 * math.sin(t * 7) * prog(t, 7.3, 0.2)
        place(frame, A["burst"], cx, cy, scale=p * pulse, alpha=a, angle=t * 12)
        n = int(round(85 * ease_out_cubic(prog(t, 6.0, 1.2))))
        place(frame, pct_img(n), cx, cy - 18, scale=p * pulse, alpha=a)
        place(frame, A["pct_lbl"], cx, cy + 26, scale=p * pulse, alpha=a)
        place(frame, A["pct_lbl2"], cx, cy + 48, scale=p * pulse, alpha=a)

    # ---- tags slide in
    if 8.3 <= t < 13.6:
        e = ease_out_back(prog(t, 8.3, 0.45), 1.4)
        a = 1 - prog(t, 13.3, 0.3)
        x = -A["tag1"].width / 2 + (A["tag1"].width / 2 + 24 + A["tag1"].width / 2) * e
        place(frame, A["tag1"], x, 82, alpha=a)
    if 9.8 <= t < 13.6:
        e = ease_out_back(prog(t, 9.8, 0.45), 1.4)
        a = 1 - prog(t, 13.3, 0.3)
        w = A["tag2"].width
        x = W + w / 2 - (w + 30) * e
        place(frame, A["tag2"], x, 330, alpha=a)

    # ---- BULU GEBU 14 - 19.2s
    if 14.0 <= t < 19.3:
        a = 1 - prog(t, 19.0, 0.3)
        p = ease_out_back(prog(t, 14.0, 0.4))
        wob = 3 * math.sin(t * 4)
        place(frame, A["gebu"], W / 2, 140, scale=p * (1 + 0.03 * math.sin(t * 8)), alpha=a, angle=wob)
        place(frame, A["gebu2"], W / 2, 215, scale=ease_out_back(prog(t, 14.4, 0.4)), alpha=a)
        for sx, sy, ph in SPARKLES:
            tw = math.sin((t - 14.0) * 5 + ph * 6)
            s = clamp(tw) * prog(t, 14.2, 0.3)
            place(frame, A["sparkle"], sx * W, sy * H, scale=0.4 + 0.8 * s, alpha=s * a, angle=t * 90)

    # ---- KUCING PUN SUKA 19.4 - 22
    if 19.4 <= t < 22.1:
        a = 1 - prog(t, 21.8, 0.3)
        p = ease_out_back(prog(t, 19.4, 0.4))
        place(frame, A["suka"], W / 2, 150 + 6 * math.sin(t * 5), scale=p, alpha=a, angle=-2)

    # ---- CTA 22 - end
    if t >= 22.0:
        p = ease_out_back(prog(t, 22.0, 0.4))
        # darken lower part for legibility
        dim = int(110 * prog(t, 22.0, 0.3))
        if dim:
            grad = GRAD.copy()
            grad.putalpha(GRAD.getchannel("A").point(lambda v: v * dim // 255))
            frame.alpha_composite(grad, (0, H - grad.height))
        place(frame, A["cta_top"], W / 2, 620, scale=p)
        pulse = 1 + 0.07 * max(0, math.sin((t - 22.4) * 6.5)) * prog(t, 22.4, 0.1)
        place(frame, A["cta_btn"], W / 2, 715, scale=ease_out_back(prog(t, 22.2, 0.45)) * pulse)
        bounce = abs(math.sin((t - 22.0) * 5.5)) * 22
        place(frame, A["cta_down"], W / 2, 830 + bounce, scale=ease_out_back(prog(t, 22.6, 0.3)))
        blink = 1.0 if int(t * 3) % 2 == 0 else 0.55
        place(frame, A["stok"], W - A["stok"].width / 2 - 16, 548, scale=ease_out_back(prog(t, 22.8, 0.35)) * (0.95 + 0.05 * blink),
              alpha=blink)


def make_grad():
    h = 560
    a = np.linspace(0, 255, h).astype(np.uint8)[:, None].repeat(W, 1)
    img = Image.new("RGBA", (W, h), (0, 0, 0, 255))
    img.putalpha(Image.fromarray(a))
    return img


GRAD = make_grad()


def process_frame(rgb, t):
    img = Image.fromarray(rgb).convert("RGBA")
    z = zoom_factor(t)
    if z > 1.001:
        cw, ch = W / z, H / z
        x0, y0 = (W - cw) / 2, (H - ch) / 2
        img = img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    overlays(img, t)
    for f0 in FLASHES:
        dt = t - f0
        if 0 <= dt < 0.25:
            fl = Image.new("RGBA", (W, H), (255, 255, 255, int(200 * (1 - dt / 0.25))))
            img.alpha_composite(fl)
    return np.asarray(img.convert("RGB"))


# ---------------------------------------------------------------- sound effects
SR = 44100
POPS = [0.05, 0.4, 0.8, 2.5, 5.8, 8.3, 9.8, 14.0, 19.4, 22.2, 22.8]
WHOOSH = [0.0, 4.9, 13.9, 21.9]


def make_sfx(path, dur):
    out = np.zeros(int(SR * (dur + 1)))
    for t0 in POPS:  # short pitched pop
        n = int(SR * 0.12)
        tt = np.arange(n) / SR
        f = 900 * np.exp(-tt * 18) + 300
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 35) * 0.35
        i = int(t0 * SR)
        out[i:i + n] += s[: len(out) - i]
    rng = np.random.default_rng(1)
    for t0 in WHOOSH:  # filtered noise swell
        n = int(SR * 0.45)
        noise = rng.standard_normal(n)
        k = 40
        noise = np.convolve(noise, np.ones(k) / k, mode="same") * 4
        env = np.sin(np.linspace(0, np.pi, n)) ** 2 * 0.25
        i = int(t0 * SR)
        out[i:i + n] += (noise * env)[: len(out) - i]
    pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- main
def main(src, dst):
    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]))
    sfx = dst + ".sfx.wav"
    make_sfx(sfx, dur)

    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", f"scale={W}:{H},fps={FPS}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", src, "-i", sfx,
        "-filter_complex", "[2:a]volume=0.8[s];[1:a][s]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.97[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "160k", "-shortest", dst], stdin=subprocess.PIPE)

    fsize = W * H * 3
    i = 0
    while True:
        buf = dec.stdout.read(fsize)
        if len(buf) < fsize:
            break
        rgb = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        enc.stdin.write(process_frame(rgb, i / FPS).tobytes())
        i += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    subprocess.run(["rm", "-f", sfx])
    print(f"done: {i} frames -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
