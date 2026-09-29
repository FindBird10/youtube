"""Kodla sentezlenen ses efektleri (telifsiz): whoosh, pop, impact.

build_sfx_track(events, total, path): events = [(saniye, "whoosh"|"pop"|"impact"), ...]
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 44100
_rng = np.random.default_rng(7)


def _env(n: int, peak: float = 0.6) -> np.ndarray:
    """0'dan yükselip peak konumunda tepe yapan, sonra sönen yumuşak zarf."""
    t = np.linspace(0, 1, n)
    rise = np.clip(t / peak, 0, 1)
    fall = np.clip((1 - t) / (1 - peak), 0, 1)
    return np.sin(np.pi / 2 * np.minimum(rise, fall)) ** 2


def whoosh(dur: float = 0.42) -> np.ndarray:
    n = int(dur * SR)
    x = _rng.standard_normal(n)
    c = np.concatenate([[0.0], np.cumsum(x)])
    # Değişken pencereli ortalama = zamanla açılıp kapanan alçak geçiren filtre (süpürme etkisi)
    t = np.linspace(0, 1, n)
    win = (60 - 52 * np.sin(np.pi * t)).astype(int)
    idx = np.arange(1, n + 1)
    lo = np.maximum(0, idx - win)
    y = (c[idx] - c[lo]) / np.maximum(1, idx - lo)
    y *= _env(n, 0.55)
    return y / (np.max(np.abs(y)) + 1e-9) * 0.9


def pop(dur: float = 0.09) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 950 * np.exp(-t * 18) + 380          # hızla düşen perde
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t * 45)
    return y / (np.max(np.abs(y)) + 1e-9) * 0.8


def impact(dur: float = 0.8) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 42 + 60 * np.exp(-t * 9)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 4.5)
    noise = _rng.standard_normal(n)
    k = 30
    noise = np.convolve(noise, np.ones(k) / k, mode="same") * np.exp(-t * 20) * 0.6
    y = body + noise
    return y / (np.max(np.abs(y)) + 1e-9) * 0.95


GEN = {"whoosh": (whoosh, 0.55, -0.20), "pop": (pop, 0.35, 0.0), "impact": (impact, 0.7, 0.0)}
# tür: (üretici, seviye, olay zamanına göre kaydırma — whoosh kesmeden biraz önce başlar)


def build_sfx_track(events: list[tuple[float, str]], total: float, path: Path) -> None:
    out = np.zeros(int((total + 1) * SR))
    for t, kind in events:
        fn, level, shift = GEN[kind]
        y = fn() * level
        i = max(0, int((t + shift) * SR))
        j = min(len(out), i + len(y))
        out[i:j] += y[: j - i]
    out = np.clip(out, -1, 1)
    pcm = (out * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
