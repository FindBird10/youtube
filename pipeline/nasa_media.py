"""NASA Görsel ve Video Kütüphanesi'nden (images.nasa.gov) gerçek görüntü (Global kanal).

Bölümde sahne:  {"text": "...", "nasa": "earth from space"}
→ önce NASA videolarında aranır; videonun ortasından kısa, sessiz bir parça kesilir (yazı/kart içeren
  ya da kararmış kareler elenir). Video yoksa NASA fotoğrafı kullanılır. Hiçbiri yoksa sahne stok
  videoya düşer.

NASA içeriği genellikle telifsizdir (NASA medya kullanım kuralları); açıklamaya "NASA" atfı eklenir.
Üçüncü taraf telif notu taşıyan öğeler (©, "copyright", "all rights reserved") atlanır.
"""
from __future__ import annotations

import random
import re
import subprocess
from pathlib import Path

API = "https://images-api.nasa.gov/search"
UA = "BirdsVaultShorts/1.0 (+https://github.com/FindBird10/youtube)"
COPYRIGHT_RE = re.compile(r"©|copyright|all rights reserved", re.I)
SYNTH_RE = re.compile(r"artist'?s? (concept|impression|rendering)|illustration|animation|animated|simulation|"
                      r"visualization|conceptual|render(ing)?\b|explainer|cartoon|drawn|sketch|infographic", re.I)
TALK_RE = re.compile(r"interview|press conference|briefing|news conference|panel|lecture|talk\b|webinar|"
                     r"town hall|podcast|ceremony|award|explains|discusses|scientist|researcher|q&a|"
                     r"media resources|b-roll package|soundbite", re.I)
STOP = {"the", "a", "an", "of", "in", "on", "from", "and", "with", "to", "at"}
USED: set[str] = set()


def _log(msg: str) -> None:
    print(f"[nasa] {msg}", flush=True)


def _words(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 1}


def search(query: str, media: str) -> list[dict]:
    import requests

    r = requests.get(API, params={"q": query, "media_type": media, "page_size": 40},
                     headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    want = _words(query)
    out = []
    for k, it in enumerate(r.json().get("collection", {}).get("items", [])):
        d = (it.get("data") or [{}])[0]
        text = " ".join([d.get("title", ""), d.get("description", "")[:600], " ".join(d.get("keywords", []))])
        if COPYRIGHT_RE.search(text) or not it.get("href"):
            continue
        s = 3.0 * len(want & _words(d.get("title", ""))) + 1.0 * len(want & _words(text))
        s -= 2.5 if SYNTH_RE.search(text) else 0.0           # gerçek çekim öne
        s -= 4.0 if TALK_RE.search(d.get("title", "")) else 0.0  # konuşan kafalar geride
        s += 0.5 * (1 - k / 40)
        out.append({"id": d.get("nasa_id", ""), "title": d.get("title", ""), "href": it["href"], "score": s})
    out.sort(key=lambda x: x["score"], reverse=True)
    return out


def _assets(href: str) -> list[str]:
    import requests

    r = requests.get(href, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    return [u.replace("http://", "https://") for u in r.json() if isinstance(u, str)]


def _size(url: str) -> int:
    import requests

    try:
        return int(requests.head(url, headers={"User-Agent": UA}, timeout=20, allow_redirects=True)
                   .headers.get("Content-Length", 0))
    except Exception:
        return 0


def _pick(urls: list[str], prefs: list[str]) -> str | None:
    for p in prefs:
        for u in urls:
            if u.lower().endswith(p):
                return u.replace(" ", "%20")
    return None


def _duration(url: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", url],
                       capture_output=True, text=True, timeout=90)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _cut(url: str, start: float, length: float, out: Path) -> bool:
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.2f}", "-i", url, "-t", f"{length:.2f}",
                        "-an", "-sn", "-map", "0:v:0", "-vf", "scale=-2:1080,fps=30", "-c:v", "libx264",
                        "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(out)],
                       capture_output=True, text=True, timeout=300)
    return r.returncode == 0 and out.exists() and out.stat().st_size > 50_000


def _footage_ok(clip: Path, work: Path, length: float) -> tuple[bool, str]:
    """NASA'ya özgü ek eleme: röportaj/konuşan kişi ve tüm karedeki isim yazıları (alt bant).

    Karede büyük bir yüz varsa (röportaj) ya da tam genişlikte yazı oranı yüksekse klip kullanılmaz.
    """
    from faces import focus
    from text_detect import text_ratio

    for k, frac in enumerate((0.2, 0.5, 0.8)):
        frame = work / f"{clip.stem}_n{k}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{length * frac:.2f}", "-i", str(clip),
                        "-frames:v", "1", "-vf", "scale=640:-2", str(frame)], capture_output=True, timeout=60)
        if not frame.exists():
            continue
        f = focus(frame)
        if f and f[2] >= 0.16:
            return False, "konuşan kişi"
        if text_ratio(frame) > 0.012:
            return False, "isim/yazı bandı"
    return True, ""


def _video_clips(item: dict, n: int, length: float, work: Path, tag: str) -> list[Path]:
    from game_trailers import _frame_ok

    urls = _assets(item["href"])
    src = None
    for pref in ("~large.mp4", "~medium.mp4", "~mobile.mp4", "~orig.mp4"):
        u = _pick(urls, [pref])
        if u and (pref != "~orig.mp4" or 0 < _size(u) < 800_000_000):
            src = u
            break
    if not src:
        return []
    dur = _duration(src)
    if dur < length + 4:
        return []
    # Baş ve son (başlık/jenerik kartları) atlanır; aday başlangıçlar karıştırılır
    lo, hi = max(3.0, dur * 0.12), max(3.5, dur * 0.88 - length)
    starts = [lo + (hi - lo) * k / 9 for k in range(10)]
    random.Random(item["id"]).shuffle(starts)
    clips: list[Path] = []
    for k, st in enumerate(starts):
        if len(clips) >= n:
            break
        if any(abs(st - float(c.stem.rsplit("_", 1)[-1])) < length for c in clips):
            continue
        out = work / f"nasa_{tag}_{k}_{int(st)}.mp4"
        if not _cut(src, st, length, out):
            continue
        ok, mid, why = _frame_ok(out, work, length)
        if ok:
            ok, why = _footage_ok(out, work, length)
        if not ok:
            _log(f"{item['title'][:50]} @{st:.0f}s elendi ({why})")
            continue
        clips.append(out)
    return clips


def _image(item: dict, work: Path, tag: str) -> Path | None:
    import requests

    urls = _assets(item["href"])
    u = _pick(urls, ["~orig.jpg", "~orig.jpeg", "~orig.png"])
    if not u or not (0 < _size(u) < 25_000_000):
        u = _pick(urls, ["~large.jpg", "~large.jpeg", "~large.png", "~medium.jpg"])
    if not u:
        return None
    dst = work / f"nasa_{tag}{Path(u).suffix.lower()}"
    try:
        r = requests.get(u, headers={"User-Agent": UA}, timeout=90)
        r.raise_for_status()
        dst.write_bytes(r.content)
        return dst
    except Exception as e:
        _log(f"görsel indirilemedi ({type(e).__name__})")
        return None


def assign(scenes: list, work: Path) -> int:
    """sc.nasa sorgusu olan sahnelere NASA videosu ya da fotoğrafı koyar. Konulan sahne sayısı."""
    placed = 0
    for i, sc in enumerate(scenes):
        q = getattr(sc, "nasa", None)
        if not q or sc.image is not None or sc.clip is not None:
            continue
        shots = max(1, getattr(sc, "n_shots", 1))
        length = max(2.5, min(10.0, sc.duration / shots + 0.6))
        done = False
        try:
            for item in search(q, "video")[:8]:
                if item["id"] in USED or item["score"] <= 0:
                    continue
                clips = _video_clips(item, shots, length, work, f"{i:02d}")
                if clips:
                    sc.clip, sc.extra_clips = clips[0], clips[1:]
                    USED.add(item["id"])
                    _log(f"Sahne {i + 1}: video '{item['title'][:60]}' ({len(clips)} parça)")
                    done = True
                    break
            if not done:
                imgs = [it for it in search(q, "image") if it["id"] not in USED and it["score"] > 0][: shots + 2]
                for k, item in enumerate(imgs):
                    p = _image(item, work, f"{i:02d}_{k}")
                    if p is None:
                        continue
                    USED.add(item["id"])
                    if sc.image is None:
                        sc.image = p
                        _log(f"Sahne {i + 1}: fotoğraf '{item['title'][:60]}'")
                        done = True
                    else:
                        sc.extra_images.append(p)
                    if 1 + len(sc.extra_images) >= shots:
                        break
        except Exception as e:
            _log(f"Sahne {i + 1}: NASA araması başarısız ({type(e).__name__}); stoka düşülecek")
        if done:
            placed += 1
        elif not sc.search:
            sc.search = q
    return placed
