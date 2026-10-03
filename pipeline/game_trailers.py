"""Oyunun resmî Steam mağaza fragmanlarından kısa, sessiz klipler keser (gaming kanalı).

Bölümde:
  "trailer": {"steam_appid": 1888930}
  sahnelerde: "trailer": true   → o sahnenin arka planı fragmandan bir klip olur

Kaynak yalnızca Steam mağazasının herkese açık fragman yayınlarıdır (YouTube'dan indirme yok).
Ses alınmaz; anlatım ve müzik bizim. Logo/derecelendirme kartlarına denk gelmemek için
fragmanın ilk ve son saniyeleri atlanır, karanlık ya da tek renkli (yazı kartı) kareler elenir.
"""
from __future__ import annotations

import random
import re
import subprocess
from pathlib import Path

UA = "BirdsVaultShorts/1.0 (+https://github.com/FindBird10/youtube)"
HEAD_SKIP = 4.0      # fragman başı (yayıncı logoları)
TAIL_SKIP = 12.0     # fragman sonu (çıkış tarihi, derecelendirme kartları)
BAD_NAME = re.compile(r"pc features|accolade|pre-?order|dlc|bundle|sale|update|patch|esrb|pegi|"
                      r"launch date|price|subscription|season pass|teaser 15", re.I)
GOOD_NAME = re.compile(r"story|cinematic|launch|reveal|official trailer|announce", re.I)


def _log(msg: str) -> None:
    print(f"[trailers] {msg}", flush=True)


def list_trailers(appid: int) -> list[dict]:
    import requests

    r = requests.get("https://store.steampowered.com/api/appdetails",
                     params={"appids": appid, "filters": "movies", "cc": "us", "l": "english"},
                     headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    data = (r.json().get(str(appid)) or {}).get("data") or {}
    out = []
    for m in data.get("movies", []):
        url = m.get("hls_h264") or (m.get("mp4") or {}).get("max")
        name = m.get("name", "")
        if not url or BAD_NAME.search(name):
            continue
        score = (2 if GOOD_NAME.search(name) else 0) + (1 if m.get("highlight") else 0)
        out.append({"name": name, "url": url, "score": score})
    out.sort(key=lambda m: m["score"], reverse=True)
    _log(f"Steam {appid}: {len(out)} uygun fragman ({', '.join(m['name'] for m in out[:4])})")
    return out


def _best_variant(url: str) -> str:
    """HLS ana listesinden en fazla 1080p olan en yüksek kaliteli video akışını seçer."""
    import requests

    if ".m3u8" not in url:
        return url
    text = requests.get(url, headers={"User-Agent": UA}, timeout=30).text
    best, best_bw = url, -1
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("#EXT-X-STREAM-INF") and i + 1 < len(lines):
            bw = int((re.search(r"BANDWIDTH=(\d+)", line) or [0, 0])[1])
            res = re.search(r"RESOLUTION=(\d+)x(\d+)", line)
            if res and int(res[2]) > 1080:
                continue
            if bw > best_bw:
                best_bw = bw
                best = requests.compat.urljoin(url, lines[i + 1].strip())
    return best


def _duration(url: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", url],
                       capture_output=True, text=True, timeout=90)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _frame_ok(clip: Path, work: Path) -> tuple[bool, Path | None]:
    """Klibin ortasındaki kare yeterince aydınlık ve dolu mu (siyah/yazı kartı değil)?"""
    import numpy as np

    frame = work / f"{clip.stem}_mid.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-50%", "-i", str(clip), "-frames:v", "1",
                    "-vf", "scale=320:-2", str(frame)], capture_output=True, timeout=60)
    if not frame.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(clip), "-frames:v", "1",
                        "-vf", "scale=320:-2", str(frame)], capture_output=True, timeout=60)
    try:
        import cv2

        g = cv2.imread(str(frame), cv2.IMREAD_GRAYSCALE)
        if g is None:
            return True, None
        mean, std = float(np.mean(g)), float(np.std(g))
        return (mean >= 28 and std >= 22), frame
    except Exception:
        return True, frame if frame.exists() else None


def assign(scenes: list, appid: int, work: Path, seed: str = "") -> int:
    """sc.trailer olan sahnelere fragman klibi koyar. Konulan klip sayısını döndürür."""
    want = [sc for sc in scenes if getattr(sc, "trailer", False) and sc.image is None]
    if not want:
        return 0
    try:
        trailers = list_trailers(appid)[:3]
    except Exception as e:
        _log(f"Steam fragman listesi alınamadı ({type(e).__name__}); stok/wiki'ye düşülecek")
        return 0
    pool: list[tuple[str, float, str]] = []   # (akış url, başlangıç sn, ad)
    for t in trailers:
        try:
            src = _best_variant(t["url"])
            dur = _duration(src)
        except Exception as e:
            _log(f"{t['name']}: okunamadı ({type(e).__name__})")
            continue
        if dur < HEAD_SKIP + TAIL_SKIP + 6:
            continue
        span = dur - HEAD_SKIP - TAIL_SKIP
        n = max(3, int(span // 6))
        pool += [(src, HEAD_SKIP + span * k / n, t["name"]) for k in range(n)]
    if not pool:
        _log("Kullanılabilir fragman yok")
        return 0
    random.Random(f"{appid}:{seed}").shuffle(pool)

    from faces import focus

    placed = 0
    for i, sc in enumerate(want):
        length = min(12.0, max(2.5, sc.duration + 0.8))
        for _ in range(4):
            if not pool:
                break
            src, start, name = pool.pop()
            out = work / f"trailer_{i:02d}_{int(start)}.mp4"
            r = subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.2f}", "-i", src, "-t", f"{length:.2f}", "-an",
                 "-vf", "scale=-2:1080,fps=30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                 "-pix_fmt", "yuv420p", str(out)], capture_output=True, text=True, timeout=240)
            if r.returncode != 0 or not out.exists() or out.stat().st_size < 50_000:
                continue
            ok, frame = _frame_ok(out, work)
            if not ok:
                _log(f"Sahne klibi elendi (karanlık/yazı kartı): {name} @{start:.0f}s")
                continue
            sc.clip = out
            if frame is not None:
                CLIP_FOCUS[str(out)] = focus(frame)
            placed += 1
            _log(f"Sahne → {name} @{start:.0f}s ({length:.1f} sn)"
                 + (" yüz odaklı" if CLIP_FOCUS.get(str(out)) else ""))
            break
    return placed


# Klip yolu → yüz odağı (x, y, h); render_scene_video kırpmayı buna göre ortalar
CLIP_FOCUS: dict[str, tuple[float, float, float] | None] = {}
