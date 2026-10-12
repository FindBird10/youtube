"""Uzun gizem belgeselleri için telifsiz, koyu ve sakin fon müziği (tamamen kodla sentezlenir).

Kullanım:  python tools/make_doc_music.py  ->  assets/music/belgesel/belgesel_*.mp3

Alçak frekanslı minör akor yüzeyleri, derin bir dron, yavaş nefes alan rüzgâr gürültüsü ve
seyrek, uzak piyano notaları. Anlatımın altında kalacak şekilde yumuşak ve dinamik aralığı dar.
"""
from __future__ import annotations

import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

SR = 44100
OUT = Path(__file__).resolve().parent.parent / "assets" / "music" / "belgesel"


def hz(n: int) -> float:
    return 440.0 * 2 ** ((n - 69) / 12)


def smooth_noise(n: int, win: int, rng: np.random.Generator) -> np.ndarray:
    """Alçak geçiren (kayan ortalama) gürültü: rüzgâr/uğultu dokusu."""
    x = rng.standard_normal(n + win)
    c = np.cumsum(x)
    y = (c[win:] - c[:-win]) / win
    return y / (np.abs(y).max() + 1e-9)


def reverb(x: np.ndarray, rng: np.random.Generator, seconds: float = 3.5) -> np.ndarray:
    """Üstel sönen gürültü darbe yanıtıyla basit evrişim yankısı (FFT)."""
    n = int(seconds * SR)
    ir = rng.standard_normal(n) * np.exp(-np.linspace(0, 7, n))
    ir[0] = 1.0
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    return y / (np.abs(y).max() + 1e-9)


def track(seed: int, dur: float, prog: list[list[int]], chord_s: float, root: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)

    # 1) Akor yüzeyleri: her akor yumuşak giriş/çıkışla, hafif akortsuz iki katman
    step = int(chord_s * SR)
    fade = int(min(4.0, chord_s / 2) * SR)
    for k, start in enumerate(range(0, n, step)):
        chord = prog[k % len(prog)]
        end = min(n, start + step + fade)
        seg_t = t[start:end] - t[start]
        env = np.ones(end - start)
        head = min(fade, end - start)
        env[:head] = np.sin(np.linspace(0, np.pi / 2, head)) ** 2
        tail = min(fade, end - start)
        env[-tail:] *= np.cos(np.linspace(0, np.pi / 2, tail)) ** 2
        seg = np.zeros(end - start)
        for m in chord:
            f = hz(m)
            for det in (-0.6, 0.6):
                seg += np.sin(2 * np.pi * (f + det) * seg_t + rng.uniform(0, 6.28)) / len(chord)
            seg += 0.25 * np.sin(2 * np.pi * 2 * f * seg_t) / len(chord)   # hafif üst ton
        out[start:end] += 0.30 * seg * env

    # 2) Derin dron (kök ses, iki oktav aşağıda), çok yavaş titreşim
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * t / 23.0)
    out += 0.22 * lfo * (np.sin(2 * np.pi * hz(root - 24) * t) + 0.4 * np.sin(2 * np.pi * hz(root - 12) * t))

    # 3) Rüzgâr: nefes alan, koyu gürültü
    wind = smooth_noise(n, 400, rng)
    out += 0.10 * wind * (0.5 + 0.5 * np.sin(2 * np.pi * t / 17.0 + 1.3)) ** 2

    # 4) Seyrek, uzak piyano notaları (minör pentatonik), yankılı
    scale = [0, 3, 5, 7, 10, 12, 15]
    k = 6.0
    while k < dur - 6:
        f = hz(root + 12 + int(rng.choice(scale)))
        m = int(4.5 * SR)
        s = int(k * SR)
        e = min(n, s + m)
        tt = np.arange(e - s) / SR
        note = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)) * np.exp(-tt * 1.4)
        out[s:e] += 0.09 * note
        k += rng.uniform(7.0, 14.0)

    out = 0.55 * out + 0.45 * reverb(out, rng) * np.abs(out).max()
    # Baş/son yumuşak, tepe -3 dBFS
    f = int(3 * SR)
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    return out / (np.abs(out).max() + 1e-9) * 0.7


def save(x: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        wav = Path(d) / "t.wav"
        pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
        stereo = np.stack([pcm, np.roll(pcm, 220)], axis=1)        # hafif stereo genişlik
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(stereo.tobytes())
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "128k",
                        str(path)], check=True)


def main() -> None:
    A, B, C, D, E, F, G = 57, 59, 48, 50, 52, 53, 55
    # (ad, tohum, akorlar [MIDI], akor süresi, kök)
    specs = [
        ("belgesel_soguk_dosya", 11, [[A - 12, E, A], [F - 12, C, A], [D - 12, A - 12, F], [E - 12, E - 5, G + 1]], 12.0, A),
        ("belgesel_karanlik_yol", 23, [[D - 12, A - 12, F], [C - 12, G - 12, E], [G - 24, D - 12, A - 12], [A - 24, E - 12, C]], 14.0, D),
        ("belgesel_sis", 37, [[E - 12, B, G], [C - 12, G - 12, E], [A - 24, E - 12, C], [D - 12, A - 12, F + 1]], 13.0, E),
    ]
    for name, seed, prog, chord_s, root in specs:
        save(track(seed, 240.0, prog, chord_s, root), OUT / f"{name}.mp3")
        print("yazıldı:", OUT / f"{name}.mp3")


if __name__ == "__main__":
    main()
