"""Edit for the magnetic car phone holder video: cold-open hook, jump cut,
word-highlight captions, motion text, SFX, lo-fi bed and a brightening grade.

usage: python3 holder.py SOURCE.mp4 OUT.mp4 [--still T]
"""
import math
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import audio
from render import FONT, W, H, FPS, YELLOW, ease_out_back, emoji_img, stack, text_sprite  # noqa: F401

HOOK = (48.7, 50.6)                       # phone snapping onto the mount
MAIN = [(0.0, 20.8), (23.55, 66.3)]       # drop the silent bag-opening gap
SEGMENTS = [HOOK] + MAIN
HL = HOOK[1] - HOOK[0]

OFFSETS = []
_acc = 0.0
for _s, _e in SEGMENTS:
    OFFSETS.append(_acc)
    _acc += _e - _s
TOTAL = _acc
CUTS = OFFSETS[1:]                        # output times of the hard cuts

# the car interior is dark: lift mids/shadows, keep the window from clipping, warm the skin
GRADE = ("hqdn3d=2:2:5:5,"
         "eq=gamma=1.22:contrast=1.05:saturation=1.22:brightness=0.015,"
         "curves=master='0/0 0.06/0.03 0.25/0.31 0.55/0.64 0.85/0.91 1/0.97',"
         "colorbalance=rs=-0.03:bs=0.04:rm=0.05:gm=0.01:bm=-0.04:rh=0.03:bh=-0.02,"
         "vibrance=intensity=0.10,"
         "scale=1080:1920:flags=lanczos,unsharp=5:5:0.6,"
         "vignette=angle=0.42")


def o(src_t):
    """source time in the main section -> output time"""
    for (s, e), off in zip(MAIN, OFFSETS[1:]):
        if s <= src_t <= e:
            return off + src_t - s
    raise ValueError(src_t)


# ------------------------------------------------------------- transcript (src times, cleaned by hand)
SPEECH = [
    (0.09, 6.33, "Korang tengok, struggle lah kalau aku nak buat video dekat dalam kereta. Sempit-sempit macam ni, kena pegang macam ni."),
    (7.19, 8.87, "Nah, dah sampai!"),
    (9.59, 10.73, "Jom kita unboxing."),
    (11.26, 14.50, "Nampak bergerak-gerak. Sabar sekejap, sabar sekejap. Kita unboxing sekejap."),
    (14.71, 19.55, "Lepas tu nanti baru korang tahu apa benda, dan kenapa aku beli benda ni."),
    (23.67, 29.44, "Dah sampai. Haa, ni kita beli dua. Satu kat kereta satu, satu kat kereta lagi satu."),
    (31.80, 39.87, "Macam mana nak pakai dia? Korang sabar sekejap. Sabar sekejap. Dalam kotak tu nanti korang akan dapat ring macam ni. Korang tampal je kat sini. Tampal bagi center betul-betul eh."),
    (40.25, 44.86, "Kisahlah korang nak letak kat casing korang ke, kat telefon ke. Macam aku sayang telefon, aku letak kat casing."),
    (44.95, 50.59, "Macam ni kan, korang dah pusing-pusing, dah tampal, dia lekat macam tu. Korang ambil telefon korang ni, korang lekat je."),
    (51.35, 55.32, "Sebab ada stand ni, kita boleh buat video dekat sini. Dekat sini."),
    (55.74, 57.64, "Ataupun dekat..."),
    (57.94, 63.26, "Dekat sini. Ada yang ni senang, boleh ubah-ubah. Tak ada melekat dekat gam ke apa ke, tak ada."),
    (63.54, 66.27, "So korang pergi kat beg kuning, korang pergi check out!"),
]
KEYWORDS = {"STRUGGLE", "KERETA", "SAMPAI", "UNBOXING", "DUA", "RING", "TAMPAL", "CENTER", "CASING", "LEKAT",
            "STAND", "SENANG", "GAM", "KUNING", "CHECK", "OUT", "APA", "BENDA", "KENAPA"}


def build_captions():
    """Split each speech chunk into words timed by length, grouped into short phrases."""
    phrases = []
    for s, e, text in SPEECH:
        words = text.split()
        weights = np.array([len(re.sub(r"\W", "", w)) + 2 for w in words], float)
        edges = s + (e - s) * np.concatenate([[0], np.cumsum(weights) / weights.sum()])
        cur = []
        for i, w in enumerate(words):
            cur.append((w, edges[i], edges[i + 1]))
            if len(cur) == 3 or re.search(r"[.,!?]$", w) or i == len(words) - 1:
                phrases.append(cur)
                cur = []
    return phrases


CAP_CACHE = {}


def caption_sprite(phrase, active):
    key = (tuple(w for w, _, _ in phrase), active)
    if key not in CAP_CACHE:
        font = ImageFont.truetype(FONT, 76)
        sw = 7
        words = [w.upper().rstrip(",.") for w, _, _ in phrase]
        space = font.getlength(" ") * 1.1
        widths = [font.getlength(w) for w in words]
        wid = int(sum(widths) + space * (len(words) - 1) + 2 * sw + 20)
        im = Image.new("RGBA", (wid, 130))
        shadow = Image.new("RGBA", im.size)
        sd, d = ImageDraw.Draw(shadow), ImageDraw.Draw(im)
        x = sw + 10
        for i, w in enumerate(words):
            core = re.sub(r"\W", "", w)
            col = YELLOW if i == active else ((120, 230, 255) if core in KEYWORDS else (255, 255, 255))
            sd.text((x + 4, 30), w, font=font, fill=(0, 0, 0, 170), stroke_width=sw, stroke_fill=(0, 0, 0, 170))
            d.text((x, 22), w, font=font, fill=col, stroke_width=sw, stroke_fill=(10, 10, 10))
            x += widths[i] + space
        im = Image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(6)), im)
        if im.width > W - 60:
            s = (W - 60) / im.width
            im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        CAP_CACHE[key] = im
    return CAP_CACHE[key]


# ------------------------------------------------------------- overlays
OVERLAYS = []
WHITE = (255, 255, 255)
DARK = (20, 20, 20)


def add(sprite, t0, t1, cx, cy, anim="pop"):
    OVERLAYS.append((sprite, t0, t1, cx, cy, anim))


def build_overlays():
    # HOOK
    add(stack(text_sprite("STRUGGLE RAKAM", 72, WHITE),
              text_sprite("DALAM KERETA?", 96, YELLOW, emoji="😩")), 0.05, HL - 0.02, W / 2, 300, "slam")
    add(text_sprite("SEKALI LEKAT, TERUS STEADY", 52, DARK, emoji="🧲", box=(255, 255, 255, 235), rot=-3),
        0.45, HL - 0.02, W / 2, 1180, "pop")
    # body
    add(text_sprite("SUSAH NAK PEGANG", 62, WHITE, emoji="🙄", box=(230, 40, 50, 235), rot=-3), o(3.4), o(6.4), W / 2, 230)
    add(text_sprite("DAH SAMPAI!", 92, YELLOW, emoji="📦"), o(7.2), o(9.4), W / 2, 230, "slam")
    add(text_sprite("UNBOXING TIME", 64, DARK, emoji="✂️", box=(255, 214, 10, 240), rot=2), o(9.6), o(14.5), W / 2, 230)
    add(text_sprite("APA BENDA NI?", 88, WHITE, emoji="🤔"), o(16.6), o(20.7), W / 2, 230, "wobble")
    add(text_sprite("BELI 2 SET", 70, DARK, emoji="✌️", box=(255, 214, 10, 240), rot=-3), o(25.2), o(29.4), W / 2, 230)
    add(text_sprite("1 KERETA, 1 SET", 58, WHITE, emoji="🚗", box=(30, 120, 255, 235), rot=2), o(26.9), o(29.4), W / 2, 360)
    add(text_sprite("CARA PAKAI", 104, YELLOW, emoji="👇"), o(31.8), o(34.2), W / 2, 230, "slam")
    add(text_sprite("STEP 1: TAMPAL RING", 60, WHITE, emoji="⭕", box=(20, 20, 20, 215)), o(35.0), o(40.2), W / 2, 230)
    add(text_sprite("PASTIKAN CENTER", 56, DARK, emoji="🎯", box=(255, 214, 10, 240), rot=-2), o(37.9), o(40.2), W / 2, 360)
    add(text_sprite("CASING / TELEFON", 60, WHITE, emoji="📱", box=(20, 20, 20, 215)), o(40.3), o(44.9), W / 2, 230)
    add(text_sprite("STEP 2: LEKAT JE", 60, WHITE, emoji="🧲", box=(20, 20, 20, 215)), o(45.0), o(48.9), W / 2, 230)
    add(text_sprite("SNAP!", 130, YELLOW, emoji="💥"), o(49.05), o(50.6), W / 2, 260, "slam")
    add(text_sprite("LETAK MANA-MANA", 64, DARK, emoji="✅", box=(255, 255, 255, 235), rot=-2), o(51.6), o(57.6), W / 2, 230)
    add(text_sprite("TAK PAYAH GAM", 62, WHITE, emoji="❌", box=(230, 40, 50, 235), rot=2), o(60.6), o(63.4), W / 2, 230)
    add(stack(text_sprite("TEKAN BEG KUNING", 84, YELLOW, emoji="🛒"),
              text_sprite("CHECK OUT SEKARANG!", 62, WHITE)), o(63.6), TOTAL, W / 2, 300, "slam")


SFX = []


def build_sfx():
    S = SFX.append
    S(("whoosh_rev", 0.0, 0.6)); S(("impact", 0.36, 1.0)); S(("pop_hi", 0.4, 0.9))
    S(("pop_hi", 0.45, 0.6)); S(("whoosh", HL - 0.28, 0.9)); S(("impact", HL, 0.45))
    S(("pop", o(3.4), 0.8))
    S(("ding@1568", o(7.2), 0.8)); S(("pop", o(9.6), 0.8))
    S(("whoosh", CUTS[1] - 0.2, 0.7))
    S(("boing", o(16.6), 0.6))
    S(("pop", o(25.2), 0.8)); S(("pop_hi", o(26.9), 0.8))
    S(("whoosh", o(31.6), 0.7)); S(("impact", o(31.8), 0.7))
    S(("pop", o(35.0), 0.8)); S(("ding@2093", o(37.9), 0.6))
    S(("pop", o(40.3), 0.8)); S(("pop", o(45.0), 0.8))
    S(("impact", o(49.05), 0.9)); S(("pop_hi", o(49.05), 0.9))
    S(("sparkle", o(51.6), 0.6))
    S(("pop", o(60.6), 0.8))
    S(("whoosh", o(63.45), 0.7)); S(("ding@2093", o(63.6), 0.6)); S(("ding@2637", o(63.75), 0.6))


# ------------------------------------------------------------- camera moves
PUNCH = [(0.36, 1.16), (HL, 1.10), (CUTS[1], 1.08), (o(7.2), 1.08), (o(31.8), 1.10), (o(49.05), 1.14), (o(63.6), 1.08)]
SHAKE = [0.36, o(49.05)]


def camera(t):
    z = 1.0
    if t < HL:
        z *= 1.0 + 0.05 * t / HL
    if o(51.4) <= t < o(63.4):
        z *= 1.0 + 0.06 * (t - o(51.4)) / (o(63.4) - o(51.4))
    for pt, pz in PUNCH:
        if pt <= t < pt + 0.6:
            x = (t - pt) / 0.6
            z *= 1 + (pz - 1) * (1 - x) ** 2
    dx = dy = 0.0
    for st in SHAKE:
        if st <= t < st + 0.35:
            a = 20 * (1 - (t - st) / 0.35)
            dx += a * math.sin(t * 97)
            dy += a * math.cos(t * 83)
    return z, 0.5, dx, dy


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
KEY = (1.0 + 0.09 * np.exp(-(((xx - W * 0.5) / (W * 0.42)) ** 2 + ((yy - H * 0.33) / (H * 0.26)) ** 2)))[..., None]
PHRASES = []


def draw_sprite(img, sp, age, rem, cx, cy, anim):
    if anim == "slam":
        s = 1.0 + 0.9 * max(0, 1 - age / 0.16) ** 2 if age < 0.16 else ease_out_back(0.6 + (age - 0.16) / 0.25 * 0.4, 1.5)
        alpha = min(1, age / 0.08)
    else:
        s = ease_out_back(age / 0.28)
        alpha = min(1, age / 0.06)
    rot = 8 * math.sin(age * 18) * math.exp(-age * 2.5) if anim == "wobble" else 0
    if rem < 0.15:
        alpha *= rem / 0.15
        s *= 0.9 + 0.1 * rem / 0.15
    bob = 6 * math.sin(age * 4)
    s = max(s, 0.05)
    spr = sp.resize((max(1, int(sp.width * s)), max(1, int(sp.height * s))), Image.BILINEAR)
    if rot:
        spr = spr.rotate(rot, resample=Image.BILINEAR, expand=True)
    if alpha < 1:
        spr.putalpha(spr.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(spr, (int(cx - spr.width / 2), int(cy + bob - spr.height / 2)))


def process(frame, t):
    f = np.minimum(frame.astype(np.float32) * KEY, 255).astype(np.uint8)
    img = Image.fromarray(f)
    z, cy, dx, dy = camera(t)
    if z > 1.001 or dx or dy:
        cw, ch = W / z, H / z
        x0 = min(max((W - cw) / 2 - dx / z, 0), W - cw)
        y0 = min(max(H * cy - ch / 2 - dy / z, 0), H - ch)
        img = img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
    img = img.convert("RGBA")

    for sp, t0, t1, cx, cyy, anim in OVERLAYS:
        if t0 <= t < t1:
            draw_sprite(img, sp, t - t0, t1 - t, cx, cyy, anim)

    # captions (not over the hook)
    if t >= HL:
        for ph in PHRASES:
            s, e = ph[0][1], ph[-1][2]
            try:
                os_, oe = o(s), o(e) + 0.12
            except ValueError:
                continue
            if os_ <= t < oe:
                src = t - os_ + s
                active = max([i for i, (_, ws, _) in enumerate(ph) if ws <= src] or [0])
                spr = caption_sprite(ph, active)
                age = t - os_
                sc = 0.85 + 0.15 * ease_out_back(age / 0.15)
                spr = spr.resize((int(spr.width * sc), int(spr.height * sc)), Image.BILINEAR)
                img.alpha_composite(spr, (int(W / 2 - spr.width / 2), int(1500 - spr.height / 2)))
                break

    out = np.asarray(img.convert("RGB")).copy()
    for ft, dur, strength in [(HL, 0.22, 0.85), (CUTS[1], 0.12, 0.35)]:
        if ft <= t < ft + dur:
            k = strength * (1 - (t - ft) / dur)
            out = (out * (1 - k) + 255 * k).astype(np.uint8)
    if t > TOTAL - 0.4:
        out = (out * max(0, (TOTAL - t) / 0.4)).astype(np.uint8)
    pw = int(W * min(1, t / TOTAL))
    out[H - 14:H, :pw] = YELLOW
    return out


def main():
    src, dst = sys.argv[1], sys.argv[2]
    still = float(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[3] == "--still" else None
    build_overlays()
    PHRASES.extend(build_captions())
    trims = "".join(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[s{i}];" for i, (s, e) in enumerate(SEGMENTS))
    fc = trims + "".join(f"[s{i}]" for i in range(len(SEGMENTS))) + f"concat=n={len(SEGMENTS)}:v=1:a=0,fps={FPS},{GRADE}[v]"
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-filter_complex", fc, "-map", "[v]",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    fsize = W * H * 3
    if still is not None:
        n = 0
        while True:
            buf = dec.stdout.read(fsize)
            if len(buf) < fsize:
                return
            if n == int(still * FPS):
                Image.fromarray(process(np.frombuffer(buf, np.uint8).reshape(H, W, 3), n / FPS)).save(dst)
                dec.kill()
                return
            n += 1

    build_sfx()
    audio.build(src, "mix.wav", [(s, e, off, 1.0) for (s, e), off in zip(SEGMENTS, OFFSETS)], SFX, TOTAL)
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
        enc.stdin.write(process(np.frombuffer(buf, np.uint8).reshape(H, W, 3), n / FPS).tobytes())
        n += 1
        if n % 300 == 0:
            print(f"frame {n}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("done", n, "frames")


if __name__ == "__main__":
    main()
