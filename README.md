# cloude-video-

Video jualan dengan motion graphics, hook jualan dan SFX.

| Video | Asal | Siap | Skrip |
|---|---|---|---|
| Popcorn 1 kilo RM18 | `assets/original.mp4` | `output/popcorn_hook.mp4` | `popcorn.py` |
| Gel mandian D'HERBS | `assets/dherbs_original.mp4` | `output/dherbs_hook.mp4` | `dherbs.py` |
| Meja belajar budak 3 in 1 | `assets/meja_original.mp4` | `output/meja_hook.mp4` | `meja.py` |

`motion.py` ialah enjin yang dikongsi (sticker, animasi, zoom/shake/flash, confetti, SFX, render).
Setiap skrip video hanya tentukan sticker, timeline dan SFX sendiri.

Jana semula: `python3 popcorn.py`, `python3 dherbs.py` atau `python3 meja.py` (perlu ffmpeg, numpy, pillow)
