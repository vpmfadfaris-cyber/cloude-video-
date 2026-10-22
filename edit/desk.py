"""Edit for the 3-in-1 kids study desk unboxing (captions are already burned in).

usage: python3 desk.py SOURCE.mp4 OUT.mp4 [--still T]
"""
import sys

import engine
from render import W, YELLOW, stack, text_sprite

SEGMENTS = [(23.9, 25.6),                 # hook: the finished desks with the kids using them
            (0.0, 9.75), (11.5, 74.6)]    # drop the silent box-wrestling gap
KEY_Y = 0.5

# footage leans blue/cyan: warm it back up, add contrast and a touch of saturation
GRADE = ("hqdn3d=1.5:1.5:4:4,"
         "eq=contrast=1.07:saturation=1.22:gamma=1.10:brightness=0.02,"
         "curves=master='0/0 0.06/0.03 0.30/0.31 0.65/0.71 0.90/0.95 1/0.99',"
         "colorbalance=rs=0.03:bs=-0.06:rm=0.08:gm=-0.01:bm=-0.09:rh=0.05:bh=-0.06,"
         "vibrance=intensity=0.12,"
         "scale=1080:1920:flags=lanczos,unsharp=5:5:0.55,"
         "vignette=angle=0.38")

WHITE = (255, 255, 255)
DARK = (20, 20, 20)
RED_BOX = (230, 40, 50, 235)
YEL_BOX = (255, 214, 10, 240)
BLK_BOX = (20, 20, 20, 215)
TOP, CHIP = 230, 370


def overlays(e):
    o, hl = e.o, e.hl
    # HOOK
    e.add(stack(text_sprite("MEJA BELAJAR ANAK", 72, WHITE),
                text_sprite("3 IN 1?!", 132, YELLOW, emoji="🤯")), 0.05, hl - 0.02, W / 2, 300, "slam")
    e.add(text_sprite("MEJA + KERUSI + STORAGE", 52, DARK, box=(255, 255, 255, 235), rot=-3),
          0.45, hl - 0.02, W / 2, 1250, "pop")
    # body
    e.add(text_sprite("BELI 3 SET!", 96, YELLOW, emoji="🛒"), o(3.9), o(6.4), W / 2, TOP, "slam")
    e.add(text_sprite("SANGAT FUNCTION", 62, DARK, emoji="👌", box=YEL_BOX, rot=-2), o(6.6), o(8.9), W / 2, TOP)
    e.add(text_sprite("BOX 1", 110, WHITE, emoji="📦"), o(9.0), o(9.75), W / 2, TOP, "slam")
    e.add(text_sprite("BOX 2", 110, WHITE, emoji="📦"), o(11.6), o(13.3), W / 2, TOP, "slam")
    e.add(text_sprite("BUKA DEPAN KORANG", 58, WHITE, emoji="👀", box=BLK_BOX, rot=2), o(14.3), o(17.3), W / 2, TOP)
    e.add(text_sprite("BOX 3", 110, YELLOW, emoji="📦"), o(18.9), o(20.3), W / 2, TOP, "slam")
    e.add(text_sprite("PASANG SENANG", 64, WHITE, emoji="✅", box=BLK_BOX, rot=-2), o(20.5), o(23.4), W / 2, TOP)
    e.add(text_sprite("HASIL DIA...", 104, YELLOW, emoji="✨"), o(23.6), o(26.3), W / 2, TOP, "slam")
    e.add(text_sprite("KUKUH", 110, WHITE, emoji="💪"), o(26.6), o(28.3), W / 2, TOP, "slam")
    e.add(text_sprite("BESAR / KECIK, SESUAI", 56, DARK, emoji="👧", box=YEL_BOX, rot=-2), o(28.4), o(31.2), W / 2, TOP)
    e.add(text_sprite("ESTETIK", 112, YELLOW, emoji="😍"), o(33.4), o(35.0), W / 2, TOP, "slam")
    e.add(text_sprite("RUANG TAMU", 62, WHITE, emoji="🛋️", box=BLK_BOX, rot=-2), o(35.1), o(39.6), W / 2, TOP)
    e.add(text_sprite("BILIK BELAJAR", 62, DARK, emoji="📚", box=YEL_BOX, rot=2), o(36.7), o(39.6), W / 2, CHIP)
    e.add(text_sprite("1. MEJA", 64, WHITE, emoji="✏️", box=BLK_BOX), o(40.0), o(54.5), W / 2, TOP)
    e.add(text_sprite("2. KERUSI", 64, WHITE, emoji="🪑", box=BLK_BOX), o(43.0), o(54.5), W / 2, TOP + 120)
    e.add(text_sprite("BUKAN 2 IN 1", 70, WHITE, emoji="❌", box=RED_BOX, rot=-3), o(46.9), o(49.5), W / 2, 1250, "wobble")
    e.add(text_sprite("3 IN 1!", 150, YELLOW, emoji="🤯"), o(49.6), o(52.0), W / 2, 1180, "slam")
    e.add(text_sprite("3. STORAGE", 64, DARK, emoji="📦", box=YEL_BOX), o(52.0), o(54.5), W / 2, TOP + 240)
    e.add(text_sprite("JIMAT SPACE", 92, YELLOW, emoji="✅"), o(54.6), o(56.3), W / 2, TOP, "slam")
    e.add(text_sprite("HARGA OFFER", 100, YELLOW, emoji="🔥"), o(58.6), o(61.9), W / 2, TOP, "slam")
    e.add(text_sprite("TEKAN BEG KUNING", 76, WHITE, emoji="🛒"), o(62.0), o(65.2), W / 2, TOP, "slam")
    e.add(text_sprite("SANGAT BERBALOI", 70, DARK, emoji="💯", box=YEL_BOX, rot=-2), o(65.3), o(67.9), W / 2, TOP)
    e.add(text_sprite("PENAT NAK PUJUK", 66, WHITE, emoji="😂", box=BLK_BOX, rot=3), o(68.0), o(69.9), W / 2, TOP, "wobble")
    e.add(stack(text_sprite("BELI SEKARANG", 92, YELLOW, emoji="🛒"),
                text_sprite("CHECK OUT DI BEG KUNING", 56, WHITE)), o(70.0), e.total, W / 2, 300, "slam")

    e.punch += [(0.05, 1.14), (hl, 1.10), (o(9.0), 1.08), (o(11.6), 1.08), (o(18.9), 1.08), (o(26.6), 1.06),
                (o(33.4), 1.06), (o(49.6), 1.14), (o(58.6), 1.08), (o(62.0), 1.08)]
    e.shake += [0.05, o(49.6)]
    e.push += [(o(23.6), o(40.0), 0.07), (o(54.6), o(74.6), 0.06)]


def sfx(e):
    o, hl = e.o, e.hl
    e.sfx("whoosh_rev", 0.0, 0.6); e.sfx("impact", 0.05, 1.0); e.sfx("pop_hi", 0.45, 0.8)
    e.sfx("whoosh", hl - 0.28, 0.9); e.sfx("impact", hl, 0.45)
    e.sfx("pop", o(3.9), 0.9); e.sfx("pop_hi", o(6.6), 0.7)
    e.sfx("ding@1047", o(9.0), 0.7); e.sfx("whoosh", e.cuts[1] - 0.2, 0.6); e.sfx("ding@1319", o(11.6), 0.7)
    e.sfx("pop", o(14.3), 0.7); e.sfx("ding@1568", o(18.9), 0.8); e.sfx("pop", o(20.5), 0.7)
    e.sfx("whoosh", o(23.4), 0.7); e.sfx("sparkle", o(23.6), 0.8)
    e.sfx("impact", o(26.6), 0.6); e.sfx("pop", o(28.4), 0.7)
    e.sfx("sparkle", o(33.4), 0.8); e.sfx("pop", o(35.1), 0.7); e.sfx("pop_hi", o(36.7), 0.7)
    e.sfx("ding@1047", o(40.0), 0.6); e.sfx("ding@1319", o(43.0), 0.6)
    e.sfx("boing", o(46.9), 0.7)
    e.sfx("whoosh", o(49.4), 0.7); e.sfx("impact", o(49.6), 1.0); e.sfx("ding@1568", o(52.0), 0.6)
    e.sfx("pop", o(54.6), 0.8)
    e.sfx("impact", o(58.6), 0.6); e.sfx("whoosh", o(61.85), 0.6); e.sfx("pop_hi", o(62.0), 0.8)
    e.sfx("sparkle", o(65.3), 0.6); e.sfx("boing", o(68.0), 0.6)
    e.sfx("whoosh", o(69.85), 0.7); e.sfx("ding@2093", o(70.0), 0.6); e.sfx("ding@2637", o(70.15), 0.6)


if __name__ == "__main__":
    engine.main(sys.modules[__name__])
