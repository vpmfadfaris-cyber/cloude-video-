"""Video 3 SFX cues; reuses synth + mixer from ../sfx.py."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import sfx as X
X.ORIG_GAIN = 0.8

CUTS = [3.7667, 15.7333, 26.2333, 27.7667, 29.7333, 35.8667, 53.5333, 55.3333, 61.6667, 80.7333, 103.1333]
X.CUES = [
    (0.00, "impact", 1.0), (0.00, "whoosh", 0.8), (0.15, "pop", 0.8), (0.55, "pop2", 0.8),
    (4.0, "pop", 0.6), (4.2, "swipe", 0.6), (13.8, "pop2", 0.7),
    (16.0, "pop", 0.5), (20.4, "riser", 0.7), (22.03, "impact", 0.9), (22.05, "ding", 0.8),
    (28.0, "pop", 0.6), (28.2, "swipe", 0.5),
    (36.4, "pop", 0.6), (36.6, "ding2", 0.6), (43.6, "pop", 0.6), (43.8, "swipe", 0.5),
    (50.43, "impact", 0.7), (50.45, "ding", 0.8), (53.6, "pop2", 0.5), (56.0, "pop", 0.6), (56.2, "swipe", 0.5),
    (62.0, "pop", 0.5), (72.0, "impact", 0.7), (72.0, "ding2", 0.7), (72.5, "pop2", 0.6),
    (82.0, "pop", 0.6), (91.6, "tick", 1.2), (91.62, "pop2", 0.9), (93.8, "pop", 0.6), (94.0, "swipe", 0.5),
    (104.0, "pop", 0.6), (104.2, "ding2", 0.5),
    (108.7, "riser", 0.7), (110.3, "impact", 1.0), (110.3, "ding", 0.7), (110.9, "pop2", 0.6),
] + [(t - 0.05, "whoosh_s", 0.35) for t in CUTS]
X.main(sys.argv[1], sys.argv[2], float(sys.argv[3]))
