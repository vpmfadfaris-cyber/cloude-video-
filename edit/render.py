"""Render the edited, colour-graded preview.

usage: python3 render.py SOURCE.mp4 OUT.mp4 [--still T]
"""
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import audio

W, H, FPS = 1080, 1920, 30
HOOK = (21.4, 23.0)          # cold-open clip taken from the squeeze shot
HL = HOOK[1] - HOOK[0]
SRC_END = 43.5
TOTAL = HL + SRC_END

FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

GRADE = ("hqdn3d=1.5:1.5:4:4,"
         "eq=contrast=1.06:saturation=1.30:gamma=1.05,"
         "curves=master='0/0 0.08/0.02 0.30/0.27 0.62/0.67 0.86/0.93 1/1',"
         "colorbalance=rs=-0.04:bs=0.05:rm=0.04:bm=-0.03:rh=0.04:gh=0.015:bh=-0.03,"
         "vibrance=intensity=0.12,"
         "scale=1080:1920:flags=lanczos,unsharp=5:5:0.55,"
         "vignette=angle=0.50")


def o(src_t):
    """source time in the main section -> output time"""
    return src_t + HL


# ------------------------------------------------------------- text sprites
def emoji_img(ch, size):
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new("RGBA", (140, 140))
    ImageDraw.Draw(im).text((4, 4), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    s = size / im.height
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)


def text_sprite(text, size, fill=(255, 255, 255), emoji=None, box=None, stroke=None, rot=0):
    f = ImageFont.truetype(FONT, size)
    sw = stroke if stroke is not None else max(4, size // 11)
    l, t, r, b = f.getbbox(text, stroke_width=sw)
    tw, th = r - l, b - t
    em = emoji_img(emoji, int(size * 1.05)) if emoji else None
    gap = int(size * 0.18)
    pad = int(size * 0.35) if box else sw + 10
    cw = tw + (em.width + gap if em else 0) + 2 * pad
    ch = max(th, em.height if em else 0) + 2 * pad
    im = Image.new("RGBA", (cw + 30, ch + 30))
    d = ImageDraw.Draw(im)
    ox, oy = 15, 15
    if box:
        # shadow + rounded pill
        sh = Image.new("RGBA", im.size)
        ImageDraw.Draw(sh).rounded_rectangle((ox + 6, oy + 10, ox + cw + 6, oy + ch + 10), radius=ch // 3, fill=(0, 0, 0, 120))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(8)))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((ox, oy, ox + cw, oy + ch), radius=ch // 3, fill=box)
    else:
        sh = Image.new("RGBA", im.size)
        ImageDraw.Draw(sh).text((ox + pad - l + 4, oy + (ch - th) // 2 - t + 8), text, font=f, fill=(0, 0, 0, 170),
                                stroke_width=sw, stroke_fill=(0, 0, 0, 170))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(6)))
        d = ImageDraw.Draw(im)
    d.text((ox + pad - l, oy + (ch - th) // 2 - t), text, font=f, fill=fill,
           stroke_width=0 if box else sw, stroke_fill=(10, 10, 10))
    if em:
        im.alpha_composite(em, (ox + pad + tw + gap, oy + (ch - em.height) // 2))
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    return im


def stack(*sprites, gap=-10):
    w = max(s.width for s in sprites)
    h = sum(s.height for s in sprites) + gap * (len(sprites) - 1)
    im = Image.new("RGBA", (w, h))
    y = 0
    for s in sprites:
        im.alpha_composite(s, ((w - s.width) // 2, y))
        y += s.height + gap
    return im


def ease_out_back(x, k=2.2):
    x = min(max(x, 0), 1)
    return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2


YELLOW = (255, 214, 10)
RED = (255, 70, 70)

# (sprite, t_in, t_out, cx, cy, anim)
OVERLAYS = []


def add(sprite, t0, t1, cx, cy, anim="pop"):
    OVERLAYS.append((sprite, t0, t1, cx, cy, anim))


def build_overlays():
    # HOOK
    add(stack(text_sprite("PEANUT BUTTER", 74, (255, 255, 255)),
              text_sprite("TANPA SUDU?!", 118, YELLOW, emoji="🥄")), 0.05, HL - 0.02, W / 2, 300, "slam")
    add(text_sprite("BOLEH PICIT JE", 66, (20, 20, 20), emoji="😱", box=(255, 255, 255, 235), rot=-4),
        0.55, HL - 0.02, W / 2, 1330, "pop")
    # body
    add(text_sprite("JAGA PEMAKANAN?", 70, (255, 255, 255), emoji="💪"), o(7.0), o(8.55), W / 2, 200)
    add(text_sprite("TRY THIS ONE!", 96, YELLOW, emoji="👇"), o(8.6), o(10.3), W / 2, 210, "slam")
    add(text_sprite("TAK PAYAH SUDU", 68, (255, 255, 255), emoji="❌", box=(230, 40, 50, 235), rot=-3),
        o(11.2), o(14.8), W / 2, 1240)
    add(text_sprite("TAK PAYAH SAPU", 68, (255, 255, 255), emoji="❌", box=(230, 40, 50, 235), rot=2),
        o(12.5), o(14.8), W / 2, 1380)
    add(stack(text_sprite("TAKDE ALASAN", 92, (255, 255, 255)),
              text_sprite("LAGI!", 120, YELLOW, emoji="🔥")), o(15.0), o(17.15), W / 2, 1290, "slam")
    add(text_sprite("SENANG JE", 70, (20, 20, 20), emoji="👌", box=(255, 214, 10, 240), rot=-3),
        o(19.0), o(20.9), W / 2, 1330)
    add(text_sprite("PICIT!", 104, YELLOW, emoji="🤏"), o(21.1), o(23.2), W / 2, 1330, "slam")
    add(text_sprite("SO SOFT", 96, (255, 255, 255), emoji="✨"), o(25.2), o(27.0), W / 2, 1330)
    add(text_sprite("DAH TERLIUR", 80, YELLOW, emoji="🤤"), o(27.2), o(29.1), W / 2, 210)
    add(text_sprite("PEKAT GILA!", 104, YELLOW, emoji="🔥"), o(29.2), o(31.2), W / 2, 210, "slam")
    add(text_sprite("COMOT", 100, (255, 255, 255), emoji="😂", rot=-6), o(35.6), o(36.9), W / 2, 1300, "wobble")
    add(text_sprite("RATING", 84, (255, 255, 255), box=(20, 20, 20, 210)), o(37.4), o(40.6), W / 2, 1190)
    star = emoji_img("⭐", 120)
    for i in range(5):
        add(star, o(37.9 + 0.22 * i), o(40.6), W / 2 + (i - 2) * 150, 1350, "pop")
    add(stack(text_sprite("NAK TRY?", 96, YELLOW),
              text_sprite("KOMEN “NAK”", 72, (255, 255, 255), emoji="👇")), o(40.8), TOTAL, W / 2, 1270, "slam")


SFX = []


def build_sfx():
    S = SFX.append
    S(("whoosh_rev", 0.0, 0.7)); S(("impact", 0.08, 1.0)); S(("pop_hi", 0.55, 0.8))
    S(("whoosh", HL - 0.28, 0.9)); S(("impact", HL, 0.5))
    S(("whoosh", o(1.85), 0.5))
    S(("pop", o(7.0), 0.8)); S(("whoosh", o(8.45), 0.6)); S(("ding@1568", o(8.62), 0.8))
    S(("pop", o(11.2), 0.9)); S(("pop", o(12.5), 0.9))
    S(("impact", o(15.0), 1.0))
    S(("whoosh", o(17.0), 0.9))
    S(("pop_hi", o(19.0), 0.7))
    S(("squish", o(21.1), 0.9)); S(("squish", o(23.4), 0.6))
    S(("sparkle", o(25.2), 0.8))
    S(("pop", o(27.2), 0.8))
    S(("impact", o(29.2), 0.8))
    S(("crunch", o(30.9), 0.6))
    S(("boing", o(35.6), 0.9))
    S(("whoosh", o(37.3), 0.4))
    for i, f in enumerate([1047, 1175, 1319, 1568, 2093]):
        S((f"ding@{f}", o(37.9 + 0.22 * i), 0.55))
    S(("whoosh", o(40.7), 0.6)); S(("pop_hi", o(40.85), 0.8))


# ------------------------------------------------------------- camera moves
PUNCH = [(0.0, 1.18), (HL, 1.12), (o(8.6), 1.12), (o(15.0), 1.14), (o(21.1), 1.08), (o(29.2), 1.15), (o(40.8), 1.08)]
SHAKE = [0.08, o(15.0), o(29.2)]


def camera(t):
    z, cy = 1.0, 0.5
    # slow push-ins
    if t < HL:
        z *= 1.0 + 0.06 * t / HL
    if o(17.2) <= t < o(27.0):
        p = (t - o(17.2)) / (o(27.0) - o(17.2))
        z *= 1.0 + 0.10 * (0.5 - 0.5 * math.cos(math.pi * p))
        cy = 0.5 + 0.08 * p
    if o(36.6) <= t:
        z *= 1.0 + 0.05 * (t - o(36.6)) / (TOTAL - o(36.6))
    # punch zooms (fast in, eased out over 0.5s)
    for pt, pz in PUNCH:
        if pt <= t < pt + 0.6:
            x = (t - pt) / 0.6
            z *= 1 + (pz - 1) * (1 - x) ** 2
    dx = dy = 0.0
    for st in SHAKE:
        if st <= t < st + 0.35:
            a = 22 * (1 - (t - st) / 0.35)
            dx += a * math.sin(t * 97)
            dy += a * math.cos(t * 83)
    return z, cy, dx, dy


# ------------------------------------------------------------- lighting
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
# soft "key light" on the face area (upper-centre) to lift the subject off the white wall
KEY = 1.0 + 0.07 * np.exp(-(((xx - W * 0.5) / (W * 0.42)) ** 2 + ((yy - H * 0.36) / (H * 0.28)) ** 2))
KEY = KEY[..., None]


def process(frame, t):
    f = np.minimum(frame.astype(np.float32) * KEY, 255).astype(np.uint8)
    img = Image.fromarray(f)
    z, cy, dx, dy = camera(t)
    if z > 1.001 or dx or dy:
        cw, ch = W / z, H / z
        x0 = (W - cw) / 2 - dx / z
        y0 = min(max(H * cy - ch / 2 - dy / z, 0), H - ch)
        x0 = min(max(x0, 0), W - cw)
        img = img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
    img = img.convert("RGBA")

    for sp, t0, t1, cx, cyy, anim in OVERLAYS:
        if not (t0 <= t < t1):
            continue
        age = t - t0
        rem = t1 - t
        if anim == "slam":
            s = 1.0 + 0.9 * max(0, 1 - age / 0.16) ** 2 if age < 0.16 else ease_out_back(0.6 + (age - 0.16) / 0.25 * 0.4, 1.5)
            alpha = min(1, age / 0.08)
        else:
            s = ease_out_back(age / 0.28)
            alpha = min(1, age / 0.06)
        rot = 0
        if anim == "wobble":
            rot = 8 * math.sin(age * 18) * math.exp(-age * 2.5)
        if rem < 0.15:
            alpha *= rem / 0.15
            s *= 0.9 + 0.1 * rem / 0.15
        bob = 6 * math.sin(age * 4)
        s = max(s, 0.05)
        spr = sp.resize((max(1, int(sp.width * s)), max(1, int(sp.height * s))), Image.BILINEAR)
        if rot:
            spr = spr.rotate(rot, resample=Image.BILINEAR, expand=True)
        if alpha < 1:
            a = spr.getchannel("A").point(lambda v: int(v * alpha))
            spr.putalpha(a)
        img.alpha_composite(spr, (int(cx - spr.width / 2), int(cyy + bob - spr.height / 2)))

    out = np.asarray(img.convert("RGB")).copy()
    # white flash transitions
    for ft, dur, strength in [(HL, 0.22, 0.85), (o(17.2), 0.18, 0.45)]:
        if ft <= t < ft + dur:
            k = strength * (1 - (t - ft) / dur)
            out = (out * (1 - k) + 255 * k).astype(np.uint8)
    # fade out tail
    if t > TOTAL - 0.4:
        out = (out * max(0, (TOTAL - t) / 0.4)).astype(np.uint8)
    # progress bar
    pw = int(W * min(1, t / TOTAL))
    out[H - 14:H, :pw] = YELLOW
    return out


def main():
    src, dst = sys.argv[1], sys.argv[2]
    still = float(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[3] == "--still" else None
    build_overlays()
    fc = (f"[0:v]trim={HOOK[0]}:{HOOK[1]},setpts=PTS-STARTPTS[h];"
          f"[0:v]trim=0:{SRC_END},setpts=PTS-STARTPTS[m];[h][m]concat=n=2:v=1:a=0,fps={FPS},{GRADE}[v]")
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-filter_complex", fc, "-map", "[v]",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    fsize = W * H * 3
    if still is not None:
        n = 0
        while True:
            buf = dec.stdout.read(fsize)
            if len(buf) < fsize:
                break
            if n == int(still * FPS):
                fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
                Image.fromarray(process(fr, n / FPS)).save(dst)
                dec.kill()
                return
            n += 1
        return

    build_sfx()
    audio.build(src, "mix.wav",
                [(HOOK[0], HOOK[1], 0.0, 0.6), (0.0, SRC_END, HL, 1.0)], SFX, TOTAL)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-i", "mix.wav", "-map", "0:v", "-map", "1:a",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                            "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-shortest",
                            "-movflags", "+faststart", dst], stdin=subprocess.PIPE)
    n = 0
    while True:
        buf = dec.stdout.read(fsize)
        if len(buf) < fsize:
            break
        fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        enc.stdin.write(process(fr, n / FPS).tobytes())
        n += 1
        if n % 150 == 0:
            print(f"frame {n}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("done", n, "frames")


if __name__ == "__main__":
    main()
