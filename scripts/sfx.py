"""Synthesize SFX and mix them over the original audio at cue times."""
import numpy as np, wave, subprocess, sys

SR = 44100
rng = np.random.default_rng(7)


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def lowpass(x, cut):
    # one-pole lowpass with per-sample cutoff (array or scalar)
    cut = np.broadcast_to(np.asarray(cut, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * cut / SR)
    y = np.zeros_like(x); s = 0.0
    for i in range(len(x)):
        s += a[i] * (x[i] - s); y[i] = s
    return y


def whoosh(d=0.45, lo=300, hi=4000):
    n = int(d * SR); t = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    cut = lo + (hi - lo) * np.sin(np.pi * t) ** 2
    y = lowpass(noise, cut) - lowpass(noise, cut * 0.25)
    y *= np.sin(np.pi * t) ** 1.5
    return y / np.abs(y).max() * 0.55


def pop(f0=500, f1=1300, d=0.09):
    n = int(d * SR); t = np.arange(n) / SR
    f = f0 + (f1 - f0) * (t / d)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.025)
    return y * 0.5


def impact(d=1.1):
    n = int(d * SR); t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / 0.06)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.32)
    click = lowpass(rng.standard_normal(n), 2500) * env_exp(n, 0.012) * 2
    y = np.tanh((body + click) * 1.6)
    return y * 0.8


def ding(f=1318.5, d=1.2):
    n = int(d * SR); t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 2 * f * t)
         + 0.2 * np.sin(2 * np.pi * 3.01 * f * t)) * env_exp(n, 0.28)
    y[:200] *= np.linspace(0, 1, 200)
    return y * 0.28


def tick(d=0.03):
    n = int(d * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2400 * t) * env_exp(n, 0.006)) * 0.45


def riser(d=1.6):
    n = int(d * SR); t = np.linspace(0, 1, n)
    noise = lowpass(rng.standard_normal(n), 300 + 6000 * t ** 2)
    tone = np.sin(2 * np.pi * np.cumsum(180 + 900 * t ** 2) / SR)
    y = (noise * 0.6 + tone * 0.25) * t ** 2.2
    return y / np.abs(y).max() * 0.5


def swipe(d=0.22):
    return whoosh(d, 1200, 7000) * 0.7


def shutter():
    n = int(0.12 * SR)
    y = lowpass(rng.standard_normal(n), 5000) * env_exp(n, 0.015)
    y2 = np.roll(y, int(0.05 * SR)) * 0.7
    return (y + y2) * 0.6


S = dict(whoosh=whoosh(), pop=pop(), pop2=pop(700, 1700), impact=impact(),
         ding=ding(), ding2=ding(1760), tick=tick(), riser=riser(),
         swipe=swipe(), shutter=shutter(), whoosh_s=whoosh(0.3, 500, 5000))

# (time, sound, gain)
CUES = [
    (0.00, "impact", 1.0), (0.00, "whoosh", 0.8), (0.55, "pop2", 0.8), (0.95, "swipe", 0.7),
    (3.05, "pop", 0.8), (4.55, "pop", 0.7), (4.85, "pop2", 0.7),
    (6.05, "whoosh_s", 0.6),
    (8.55, "tick", 1), (8.95, "tick", 1), (9.35, "ding", 0.9),
    (9.42, "whoosh_s", 0.5),
    (14.45, "impact", 0.85), (14.45, "whoosh", 0.6),
    (17.55, "swipe", 0.8), (18.1, "pop", 0.6),
    (19.5, "whoosh_s", 0.5),
    (20.55, "pop", 0.6),
    (22.55, "ding2", 0.8), (22.85, "whoosh_s", 0.5),
    (26.55, "pop", 0.7), (28.3, "whoosh_s", 0.5),
    (30.5, "pop2", 0.7), (30.9, "tick", 1), (31.3, "tick", 1), (31.7, "tick", 1), (32.1, "tick", 1),
    (32.5, "ding", 1.0),
    (34.55, "ding2", 0.6), (35.6, "ding2", 0.6), (37.55, "ding2", 0.6), (39.55, "ding2", 0.6),
    (43.0, "whoosh", 0.6),
    (44.0, "impact", 0.8), (44.05, "shutter", 0.6),
    (46.05, "pop", 0.8), (47.55, "pop2", 0.8), (48.05, "whoosh_s", 0.5),
    (48.9, "riser", 0.8), (50.5, "impact", 1.0), (50.5, "ding", 0.7), (51.5, "pop2", 0.6),
]


def main(src, dst, dur):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-f", "s16le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    orig = np.frombuffer(raw, np.int16).reshape(-1, 2).astype(np.float32) / 32768
    n = max(len(orig), int(dur * SR))
    mix = np.zeros((n, 2), np.float32)
    mix[:len(orig)] = orig * 0.62  # original is ~-8.6 LUFS, leave headroom for SFX
    sfx = np.zeros(n, np.float32)
    for t, name, g in CUES:
        s = S[name] * g; i = int(t * SR); j = min(n, i + len(s))
        sfx[i:j] += s[: j - i]
    mix += sfx[:, None] * 0.9
    out = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(dst, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]))
