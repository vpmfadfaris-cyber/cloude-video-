"""Synthesised SFX + lo-fi music bed + mix for the edit (no external assets)."""
import numpy as np
import subprocess
import wave

SR = 48000
rng = np.random.default_rng(7)


def t_(dur):
    return np.arange(int(dur * SR)) / SR


def onepole_lp(x, fc):
    """Time-varying one-pole low-pass; fc may be scalar or array."""
    fc = np.broadcast_to(np.asarray(fc, dtype=np.float64), x.shape)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def lp_fast(x, fc):
    # static low-pass via FFT brickwall-ish with soft rolloff
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (f / fc) ** 4)
    return np.fft.irfft(X, len(x))


def hp_fast(x, fc):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (fc / np.maximum(f, 1)) ** 4)
    return np.fft.irfft(X, len(x))


def env_ar(n, a, r):
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-np.maximum(t - a, 0) / r)
    return e


# ---------------------------------------------------------------- SFX
def whoosh(dur=0.55, rev=False):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    p = np.linspace(0, 1, n)
    fc = 300 + 5000 * np.sin(np.pi * p) ** 2
    y = onepole_lp(x, fc)
    y = y - onepole_lp(y, 150)
    e = np.sin(np.pi * p) ** 1.5
    if rev:
        e = p ** 2.5 * (p < 0.97) + (p >= 0.97) * (1 - (p - 0.97) / 0.03)
    y = y * e
    return 0.9 * y / np.abs(y).max()


def impact(dur=0.9):
    t = t_(dur)
    f = 38 + 70 * np.exp(-t * 18)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 4.5)
    click = lp_fast(rng.standard_normal(len(t)), 3500) * np.exp(-t * 60)
    y = np.tanh(2.2 * body) * 0.9 + 0.5 * click
    return 0.95 * y / np.abs(y).max()


def pop(f0=1100, f1=320, dur=0.12):
    t = t_(dur)
    f = f1 + (f0 - f1) * np.exp(-t * 45)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 32)
    return 0.8 * y


def ding(f=1568, dur=1.1):
    t = t_(dur)
    y = (np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t * 3)
         + 0.2 * np.sin(2 * np.pi * f * 3.02 * t) * np.exp(-t * 6))
    y *= env_ar(len(t), 0.003, 0.35)
    return 0.55 * y / np.abs(y).max()


def sparkle(dur=1.0):
    out = np.zeros(int(dur * SR))
    for i in range(9):
        f = rng.uniform(2400, 5200)
        d = ding(f, 0.5) * rng.uniform(0.3, 0.6)
        s = int(i * 0.065 * SR)
        out[s:s + len(d)] += d[: len(out) - s]
    return 0.8 * out / np.abs(out).max()


def squish(dur=0.5):
    t = t_(dur)
    f = 260 * np.exp(-t * 2.5) + 40 * np.sin(2 * np.pi * 18 * t)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR)
    nz = lp_fast(rng.standard_normal(len(t)), 900)
    wob = 0.6 + 0.4 * np.sin(2 * np.pi * 22 * t)
    y = (0.6 * tone + 0.8 * nz / np.abs(nz).max()) * wob * np.sin(np.pi * t / dur) ** 0.7
    return 0.7 * y / np.abs(y).max()


def boing(dur=0.6):
    t = t_(dur)
    f = 180 * (1 + 0.35 * np.sin(2 * np.pi * 11 * t) * np.exp(-t * 4)) + 120 * t
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ar(len(t), 0.005, 0.22)
    return 0.75 * y


def crunch(dur=0.35):
    n = int(dur * SR)
    y = np.zeros(n)
    for i in range(6):
        s = int(rng.uniform(0, dur * 0.7) * SR)
        b = hp_fast(rng.standard_normal(2400), 1500) * env_ar(2400, 0.001, 0.012)
        y[s:s + 2400] += b[: n - s] * rng.uniform(0.4, 1)
    return 0.6 * y / np.abs(y).max()


# ---------------------------------------------------------------- music
def music(total):
    bpm = 88
    beat = 60 / bpm
    n = int(total * SR)
    out = np.zeros(n + SR * 2)

    def put(sig, at, g=1.0):
        s = int(at * SR)
        if s >= len(out):
            return
        e = min(len(out), s + len(sig))
        out[s:e] += g * sig[: e - s]

    kick_t = t_(0.35)
    kick = np.sin(2 * np.pi * np.cumsum(48 + 90 * np.exp(-kick_t * 30)) / SR) * np.exp(-kick_t * 9)
    snr_t = t_(0.25)
    snare = (lp_fast(rng.standard_normal(len(snr_t)), 5000) * 0.5 + np.sin(2 * np.pi * 190 * snr_t)) * np.exp(-snr_t * 18)
    hat = hp_fast(rng.standard_normal(int(0.05 * SR)), 7000) * env_ar(int(0.05 * SR), 0.001, 0.012)

    # Fmaj7, Em7, Dm7, Cmaj7  (two beats each... four beats each)
    chords = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]
    bars = int(total / (4 * beat)) + 2
    for b in range(bars):
        t0 = b * 4 * beat
        ch = chords[b % 4]
        ct = t_(4 * beat)
        pad = np.zeros(len(ct))
        for m in ch:
            f = 440 * 2 ** ((m - 69) / 12)
            pad += np.sin(2 * np.pi * f * ct) + 0.3 * np.sin(2 * np.pi * 2 * f * ct) * np.exp(-ct * 2)
        pad *= env_ar(len(ct), 0.02, 2.2) * (0.85 + 0.15 * np.sin(2 * np.pi * 4.5 * ct))
        put(pad, t0, 0.06)
        bass_f = 440 * 2 ** ((ch[0] - 12 - 69) / 12)
        bt = t_(2 * beat)
        bass = np.sin(2 * np.pi * bass_f * bt) * env_ar(len(bt), 0.01, 0.6)
        put(bass, t0, 0.22)
        put(bass, t0 + 2.5 * beat, 0.16)
        for k in range(4):
            sw = 0.04 if k % 2 else 0
            if k in (0,):
                put(kick, t0 + k * beat, 0.55)
            if k == 2:
                put(kick, t0 + (k + 0.5) * beat, 0.4)
            if k in (1, 3):
                put(snare, t0 + k * beat, 0.22)
            put(hat, t0 + k * beat + sw, 0.09)
            put(hat, t0 + (k + 0.5) * beat + sw, 0.06)
    out = lp_fast(out, 6000)  # warm / lo-fi
    out += 0.004 * lp_fast(rng.standard_normal(len(out)), 3000)  # vinyl hiss
    return out[:n]


def read_wav(path):
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    return a


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    st = (np.stack([x, x], 1) * 32767).astype(np.int16)
    with wave.open(path, "w") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())


def build(src_video, out_wav, segments, sfx_events, total):
    """segments: list of (src_start, src_end, out_start, gain)."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src_video, "-vn", "-ac", "1", "-ar", str(SR),
                    "-af", "highpass=f=80,afftdn=nf=-30,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2,"
                    "equalizer=f=3000:t=q:w=1:g=2.5,equalizer=f=250:t=q:w=1:g=-2",
                    "voice.wav"], check=True)
    v = read_wav("voice.wav")
    n = int(total * SR)
    voice = np.zeros(n)
    for s0, s1, o, g in segments:
        seg = v[int(s0 * SR):int(s1 * SR)] * g
        a = int(o * SR)
        seg = seg[: n - a]
        fade = min(len(seg), int(0.01 * SR))
        seg[:fade] *= np.linspace(0, 1, fade)
        seg[-fade:] *= np.linspace(1, 0, fade)
        voice[a:a + len(seg)] += seg

    lib = {"whoosh": whoosh(), "whoosh_rev": whoosh(0.7, rev=True), "impact": impact(), "pop": pop(),
           "pop_hi": pop(1600, 600, 0.1), "ding": ding(), "sparkle": sparkle(), "squish": squish(),
           "boing": boing(), "crunch": crunch()}
    sfx = np.zeros(n)
    for name, at, g in sfx_events:
        if name.startswith("ding@"):
            sig = ding(float(name[5:]), 0.9)
        else:
            sig = lib[name]
        a = int(at * SR)
        if a >= n:
            continue
        e = min(n, a + len(sig))
        sfx[a:e] += g * sig[: e - a]

    mus = music(total)
    # duck music under voice
    venv = np.sqrt(np.maximum(lp_fast(voice ** 2, 6), 0))
    venv = np.clip(venv / (np.percentile(venv, 95) + 1e-9), 0, 1)
    duck = 1 - 0.6 * venv
    fade_in = np.minimum(np.arange(n) / (0.8 * SR), 1)
    fade_out = np.clip((n - np.arange(n)) / (1.2 * SR), 0, 1)
    mix = voice * 1.0 + sfx * 0.32 + mus * 0.22 * duck * fade_in * fade_out
    mix = np.nan_to_num(np.tanh(mix * 1.1) / np.tanh(1.1))
    write_wav("mix_raw.wav", mix)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "mix_raw.wav", "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", str(SR), out_wav], check=True)
