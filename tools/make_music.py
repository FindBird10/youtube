"""Telifsiz, sakin arka plan müzikleri üretir (tamamen kodla sentezlenir).

Kullanım:  python tools/make_music.py   ->  assets/music/birdsvault_*.mp3
Kendi parçalarını (ör. YouTube Ses Kitaplığı) assets/music/ klasörüne eklersen
onlar da rastgele seçime katılır.
"""
from __future__ import annotations

import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

SR = 44100
OUT = Path(__file__).resolve().parent.parent / "assets" / "music"


def note(n: int) -> float:
    """MIDI nota numarası -> frekans."""
    return 440.0 * 2 ** ((n - 69) / 12)


def env(length: int, attack: float, release: float) -> np.ndarray:
    a, r = int(attack * SR), int(release * SR)
    e = np.ones(length)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def pad(freqs: list[float], dur: float, rng: np.random.Generator) -> np.ndarray:
    t = np.arange(int(dur * SR)) / SR
    sig = np.zeros((len(t), 2))
    for f in freqs:
        for det, pan in ((-0.12, 0.3), (0.12, 0.7)):
            ph = rng.uniform(0, 2 * np.pi)
            w = np.sin(2 * np.pi * (f + det) * t + ph) + 0.25 * np.sin(2 * np.pi * 2 * (f + det) * t + ph)
            sig[:, 0] += w * (1 - pan)
            sig[:, 1] += w * pan
    trem = 1 + 0.06 * np.sin(2 * np.pi * 0.25 * t)
    return sig * (trem * env(len(t), 1.2, 1.2))[:, None] / (len(freqs) * 2)


def pluck(f: float, dur: float) -> np.ndarray:
    t = np.arange(int(dur * SR)) / SR
    w = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.12 * np.sin(2 * np.pi * 3 * f * t))
    return w * np.exp(-t * 3.2) * env(len(t), 0.005, 0.05)


def reverb(x: np.ndarray, delays=(0.031, 0.047, 0.061, 0.083), fb: float = 0.55) -> np.ndarray:
    y = x.copy()
    for d in delays:
        k = int(d * SR)
        buf = np.zeros_like(x)
        for i in range(k, len(x), k):  # blok halinde geri besleme
            buf[i:i + k] = (x[i - k:i] + buf[i - k:i] * fb)[: len(buf[i:i + k])]
        y += buf * 0.25
    return y


def render_track(prog: list[list[int]], bpm: float, bars_per_chord: int, repeats: int, arp: list[int],
                 seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    chord_dur = beat * 4 * bars_per_chord
    total = int(chord_dur * len(prog) * repeats * SR) + SR * 2
    mix = np.zeros((total, 2))
    pos = 0.0
    for _ in range(repeats):
        for ch in prog:
            i0 = int(pos * SR)
            p = pad([note(n) for n in ch], chord_dur + 1.0, rng)
            mix[i0:i0 + len(p)] += p * 0.8
            b = pad([note(ch[0] - 12)], chord_dur + 0.5, rng) * 0.6          # bas
            mix[i0:i0 + len(b)] += b
            steps = int(chord_dur / (beat / 2))
            for s in range(steps):                                           # yumuşak arpej
                n = ch[arp[s % len(arp)] % len(ch)] + 12
                pl = pluck(note(n), beat * 1.5) * 0.18
                j = int((pos + s * beat / 2) * SR)
                pan = 0.35 + 0.3 * ((s % 4) / 3)
                mix[j:j + len(pl), 0] += pl[: len(mix) - j] * (1 - pan)
                mix[j:j + len(pl), 1] += pl[: len(mix) - j] * pan
            pos += chord_dur
    mix = reverb(mix)
    # Döngüye girdiğinde kesik duyulmasın: baş ve sona yumuşak geçiş
    mix *= env(len(mix), 1.5, 2.0)[:, None]
    mix /= np.max(np.abs(mix)) + 1e-9
    return mix * 0.5


TRACKS = {
    # ad: (akor dizisi [MIDI], bpm, akor başına ölçü, tekrar, arpej sırası)
    "birdsvault_merak": ([[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]], 84, 1, 6, [0, 1, 2, 1]),
    "birdsvault_uzay": ([[50, 53, 57, 60], [46, 50, 53, 57], [43, 46, 50, 53], [45, 49, 52, 57]], 70, 1, 5, [0, 2, 1, 3]),
    "birdsvault_kesif": ([[52, 55, 59], [48, 52, 55], [55, 59, 62], [50, 54, 57]], 96, 1, 7, [0, 1, 2, 3, 2, 1]),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for i, (name, (prog, bpm, bpc, rep, arp)) in enumerate(TRACKS.items()):
        audio = render_track(prog, bpm, bpc, rep, arp, seed=i + 7)
        pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
        with tempfile.TemporaryDirectory() as td:
            wav = Path(td) / "t.wav"
            with wave.open(str(wav), "wb") as w:
                w.setnchannels(2)
                w.setsampwidth(2)
                w.setframerate(SR)
                w.writeframes(pcm.tobytes())
            dst = OUT / f"{name}.mp3"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", "loudnorm=I=-20:TP=-2",
                            "-ar", "44100", "-b:a", "160k", str(dst)], check=True)
        print(f"{dst.name}: {len(audio) / SR:.0f} sn")


if __name__ == "__main__":
    main()
