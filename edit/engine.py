"""Generic short-form edit renderer shared by the per-video project files.

A project module defines:
  SEGMENTS   list of (src_start, src_end); the first one is the cold-open hook
  GRADE      ffmpeg filter chain applied before the per-frame work (must end at 1080x1920)
  overlays(e)  adds text/sticker overlays via e.add(...)
  sfx(e)       adds sound effects via e.sfx(...)
optional: PUNCH [(t_out, zoom)], SHAKE [t_out], FLASHES [(t_out, dur, strength)],
          PUSH [(t0_out, t1_out, zoom_gain)], KEY_Y (key-light centre, 0..1)
"""
import math
import subprocess
import sys

import numpy as np
from PIL import Image

import audio
from render import W, H, FPS, YELLOW, ease_out_back


class Edit:
    def __init__(self, project):
        self.p = project
        self.segments = project.SEGMENTS
        self.offsets = []
        acc = 0.0
        for s, e in self.segments:
            self.offsets.append(acc)
            acc += e - s
        self.total = acc
        self.hl = self.segments[0][1] - self.segments[0][0]
        self.cuts = self.offsets[1:]
        self.overlays = []
        self.sfx_events = []
        self.punch = []
        self.shake = []
        self.flashes = [(self.hl, 0.22, 0.85)] + [(c, 0.12, 0.35) for c in self.cuts[1:]]
        self.push = []
        ky = getattr(project, "KEY_Y", 0.35)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        self.key = (1.0 + 0.06 * np.exp(-(((xx - W * 0.5) / (W * 0.45)) ** 2 + ((yy - H * ky) / (H * 0.3)) ** 2)))[..., None]

    def o(self, src_t):
        """source time in the main section -> output time"""
        for (s, e), off in zip(self.segments[1:], self.offsets[1:]):
            if s <= src_t <= e:
                return off + src_t - s
        raise ValueError(f"{src_t} is cut out of the edit")

    def add(self, sprite, t0, t1, cx, cy, anim="pop"):
        self.overlays.append((sprite, t0, t1, cx, cy, anim))

    def sfx(self, name, t, gain=0.8):
        self.sfx_events.append((name, t, gain))

    # ---------------------------------------------------------------- frame work
    def camera(self, t):
        z = 1.0
        if t < self.hl:
            z *= 1.0 + 0.05 * t / self.hl
        for t0, t1, g in self.push:
            if t0 <= t < t1:
                z *= 1.0 + g * (t - t0) / (t1 - t0)
        for pt, pz in self.punch:
            if pt <= t < pt + 0.6:
                x = (t - pt) / 0.6
                z *= 1 + (pz - 1) * (1 - x) ** 2
        dx = dy = 0.0
        for st in self.shake:
            if st <= t < st + 0.35:
                a = 20 * (1 - (t - st) / 0.35)
                dx += a * math.sin(t * 97)
                dy += a * math.cos(t * 83)
        return z, dx, dy

    @staticmethod
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

    def process(self, frame, t):
        f = np.minimum(frame.astype(np.float32) * self.key, 255).astype(np.uint8)
        img = Image.fromarray(f)
        z, dx, dy = self.camera(t)
        if z > 1.001 or dx or dy:
            cw, ch = W / z, H / z
            x0 = min(max((W - cw) / 2 - dx / z, 0), W - cw)
            y0 = min(max((H - ch) / 2 - dy / z, 0), H - ch)
            img = img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
        img = img.convert("RGBA")
        for sp, t0, t1, cx, cy, anim in self.overlays:
            if t0 <= t < t1:
                self.draw_sprite(img, sp, t - t0, t1 - t, cx, cy, anim)
        out = np.asarray(img.convert("RGB")).copy()
        for ft, dur, strength in self.flashes:
            if ft <= t < ft + dur:
                k = strength * (1 - (t - ft) / dur)
                out = (out * (1 - k) + 255 * k).astype(np.uint8)
        if t > self.total - 0.4:
            out = (out * max(0, (self.total - t) / 0.4)).astype(np.uint8)
        out[H - 14:H, :int(W * min(1, t / self.total))] = YELLOW
        return out

    # ---------------------------------------------------------------- render
    def decoder(self, src):
        trims = "".join(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[s{i}];" for i, (s, e) in enumerate(self.segments))
        fc = (trims + "".join(f"[s{i}]" for i in range(len(self.segments)))
              + f"concat=n={len(self.segments)}:v=1:a=0,fps={FPS},{self.p.GRADE}[v]")
        return subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-filter_complex", fc, "-map", "[v]",
                                 "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)

    def run(self, argv):
        src, dst = argv[1], argv[2]
        still = float(argv[4]) if len(argv) > 4 and argv[3] == "--still" else None
        self.p.overlays(self)
        self.p.sfx(self)
        dec = self.decoder(src)
        fsize = W * H * 3
        if still is not None:
            n = 0
            while True:
                buf = dec.stdout.read(fsize)
                if len(buf) < fsize:
                    return
                if n == int(still * FPS):
                    Image.fromarray(self.process(np.frombuffer(buf, np.uint8).reshape(H, W, 3), n / FPS)).save(dst)
                    dec.kill()
                    return
                n += 1

        audio.build(src, "mix.wav", [(s, e, off, 1.0) for (s, e), off in zip(self.segments, self.offsets)],
                    self.sfx_events, self.total)
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
            enc.stdin.write(self.process(np.frombuffer(buf, np.uint8).reshape(H, W, 3), n / FPS).tobytes())
            n += 1
            if n % 300 == 0:
                print(f"frame {n}", flush=True)
        enc.stdin.close()
        enc.wait()
        print("done", n, "frames")


def main(project):
    Edit(project).run(sys.argv)
