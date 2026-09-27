"""Bir bölüm JSON dosyasından dikey (1080x1920) YouTube Shorts videosu üretir.

Adımlar:
  1. Her sahnenin metnini Edge-TTS ile seslendirir (kelime zamanlarıyla birlikte).
  2. Her sahne için Pexels'ten dikey stok video indirir (yoksa düz renk arka plan).
  3. Sahneleri FFmpeg ile birleştirir, kelime kelime vurgulanan altyazıyı yakar.
  4. İsteğe bağlı olarak assets/music içindeki bir müziği kısık sesle ekler.

Kullanım:
  python pipeline/make_video.py episodes/2026-09-29.json --out build/
  python pipeline/make_video.py episodes/ornek.json --offline   # internetsiz test
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

W, H, FPS = 1080, 1920, 30
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VOICE = "tr-TR-AhmetNeural"
FALLBACK_COLORS = ["0x14213d", "0x1b263b", "0x2b2d42", "0x3a0ca3", "0x264653", "0x5f0f40"]


@dataclass
class Word:
    start: float  # saniye (videonun başından itibaren)
    end: float
    text: str


@dataclass
class Scene:
    text: str
    search: str
    audio: Path | None = None
    duration: float = 0.0
    words: list[Word] = field(default_factory=list)
    clip: Path | None = None


# ----------------------------------------------------------------- yardımcılar
def run(cmd: list[str]) -> None:
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.stderr.write(res.stderr[-3000:])
        raise RuntimeError(f"Komut başarısız: {' '.join(cmd[:6])} ...")


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def tr_upper(s: str) -> str:
    """Türkçe'ye uygun büyük harf (i -> İ, ı -> I)."""
    return s.replace("i", "İ").replace("ı", "I").upper()


def log(msg: str) -> None:
    print(f"[make_video] {msg}", flush=True)


# --------------------------------------------------------------- seslendirme
async def _tts(text: str, voice: str, rate: str, out: Path) -> list[tuple[float, float, str]]:
    import edge_tts

    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    words: list[tuple[float, float, str]] = []
    with open(out, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append((start, start + chunk["duration"] / 1e7, chunk["text"]))
    return words


def synthesize(scenes: list[Scene], voice: str, rate: str, work: Path, offline: bool) -> None:
    for i, sc in enumerate(scenes):
        mp3 = work / f"voice_{i:02d}.mp3"
        if offline:
            # İnternetsiz test: kelime başına ~0.4 sn sessizlik + sahte zamanlar
            tokens = sc.text.split()
            dur = max(1.5, 0.4 * len(tokens))
            run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                 "-t", f"{dur:.2f}", "-q:a", "9", str(mp3)])
            step = dur / len(tokens)
            raw = [(k * step, (k + 1) * step, t) for k, t in enumerate(tokens)]
        else:
            raw = []
            for attempt in range(3):
                try:
                    raw = asyncio.run(_tts(sc.text, voice, rate, mp3))
                    break
                except Exception as e:  # ağ hatalarında tekrar dene
                    log(f"TTS hatası (deneme {attempt + 1}): {e}")
                    if attempt == 2:
                        raise
        sc.audio = mp3
        sc.duration = probe_duration(mp3) + 0.25  # sahneler arası kısa nefes
        sc.words = [Word(a, b, t) for a, b, t in raw]
        log(f"Sahne {i + 1}: {sc.duration:.1f} sn, {len(sc.words)} kelime")


# ------------------------------------------------------------- stok görüntü
def fetch_clips(scenes: list[Scene], work: Path, offline: bool) -> None:
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    if offline or not key:
        if not offline:
            log("PEXELS_API_KEY yok; düz renk arka plan kullanılacak.")
        return
    import requests

    used: set[int] = set()
    sess = requests.Session()
    sess.headers["Authorization"] = key

    def search(query: str) -> list[dict]:
        r = sess.get("https://api.pexels.com/videos/search", timeout=30, params={
            "query": query, "orientation": "portrait", "size": "medium", "per_page": 20})
        r.raise_for_status()
        return r.json().get("videos", [])

    for i, sc in enumerate(scenes):
        queries = [sc.search, " ".join(sc.search.split()[:2]), sc.search.split()[0]]
        chosen = None
        for q in dict.fromkeys(q for q in queries if q):
            try:
                vids = [v for v in search(q) if v["id"] not in used]
            except Exception as e:
                log(f"Pexels arama hatası '{q}': {e}")
                continue
            # Sahneden uzun olanları tercih et, ilk birkaç sonuç arasından rastgele seç
            long_enough = [v for v in vids if v.get("duration", 0) >= sc.duration]
            pool = (long_enough or vids)[:5]
            if pool:
                chosen = random.choice(pool)
                break
        if not chosen:
            log(f"Sahne {i + 1}: görüntü bulunamadı, düz renk kullanılacak.")
            continue
        used.add(chosen["id"])
        files = [f for f in chosen["video_files"] if f.get("height") and f.get("width")]
        portrait = [f for f in files if f["height"] >= f["width"]] or files
        # 1080 genişliğe en yakın, ondan küçük olmayanı seç
        portrait.sort(key=lambda f: (f["width"] < 1080, abs(f["width"] - 1080)))
        url = portrait[0]["link"]
        dst = work / f"clip_{i:02d}.mp4"
        with sess.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(dst, "wb") as f:
                for part in r.iter_content(1 << 20):
                    f.write(part)
        sc.clip = dst
        log(f"Sahne {i + 1}: Pexels #{chosen['id']} ({sc.search})")


# ------------------------------------------------------------------ altyazı
def ass_escape(s: str) -> str:
    return s.replace("\\", "").replace("{", "").replace("}", "")


def ts(t: float) -> str:
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def build_ass(words: list[Word], total: float, font: str, path: Path,
              max_words: int = 3, max_chars: int = 18) -> None:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,3,5,80,80,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    # Kelimeleri kısa gruplara böl
    groups: list[list[Word]] = []
    cur: list[Word] = []
    for w in words:
        clean = w.text.strip()
        if not clean:
            continue
        chars = sum(len(x.text) + 1 for x in cur) + len(clean)
        if cur and (len(cur) >= max_words or chars > max_chars):
            groups.append(cur)
            cur = []
        cur.append(w)
        if re.search(r"[.!?…,;:]$", clean):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)

    lines = []
    for gi, g in enumerate(groups):
        g_end = groups[gi + 1][0].start if gi + 1 < len(groups) else min(total, g[-1].end + 0.4)
        # Çok uzun sessizliklerde altyazı ekranda asılı kalmasın
        g_end = min(g_end, g[-1].end + 0.6)
        for wi, w in enumerate(g):
            start = w.start
            end = g[wi + 1].start if wi + 1 < len(g) else g_end
            if end <= start:
                continue
            parts = []
            for k, x in enumerate(g):
                t = ass_escape(tr_upper(x.text))
                parts.append("{\\c&H00E5FF&}" + t + "{\\c&HFFFFFF&}" if k == wi else t)
            pop = "{\\fscx108\\fscy108\\t(0,90,\\fscx100\\fscy100)}" if wi == 0 else ""
            lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},Cap,,0,0,0,,{pop}{' '.join(parts)}")
    path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


# -------------------------------------------------------------------- montaj
def render_scene_video(sc: Scene, idx: int, work: Path) -> Path:
    out = work / f"seg_{idx:02d}.mp4"
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"fps={FPS},setsar=1,format=yuv420p")
    if sc.clip:
        src = ["-stream_loop", "-1", "-i", str(sc.clip)]
        # %8 yakınlaştırıp ortadan kırp: kenarlardaki filigran/siyah bantlar gitsin
        vf = (f"scale={int(W * 1.08)}:{int(H * 1.08)}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H}:(iw-{W})/2:(ih-{H})/2,fps={FPS},setsar=1,format=yuv420p")
    else:
        color = FALLBACK_COLORS[idx % len(FALLBACK_COLORS)]
        src = ["-f", "lavfi", "-i", f"color=c={color}:s={W}x{H}:r={FPS}"]
    run(["ffmpeg", "-y", *src, "-t", f"{sc.duration:.3f}", "-vf", vf, "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(out)])
    return out


def render(episode: dict, out_dir: Path, offline: bool = False) -> Path:
    slug = episode["_slug"]
    work = out_dir / f"{slug}_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    scenes = [Scene(text=s["text"].strip(), search=s.get("search", "").strip())
              for s in episode["scenes"] if s.get("text", "").strip()]
    if not scenes:
        raise ValueError("Bölümde hiç sahne yok.")

    synthesize(scenes, episode.get("voice", DEFAULT_VOICE), episode.get("rate", "+8%"), work, offline)
    total = sum(s.duration for s in scenes)
    if total > 59:
        log(f"UYARI: video {total:.1f} sn; Shorts için 60 saniyenin altı önerilir.")
    fetch_clips(scenes, work, offline)

    # Kelime zamanlarını videonun geneline taşı
    all_words: list[Word] = []
    t0 = 0.0
    for sc in scenes:
        all_words += [Word(w.start + t0, w.end + t0, w.text) for w in sc.words]
        t0 += sc.duration

    # Ses: sahne seslerini tam sahne süresine uzatıp birleştir
    wavs = []
    for i, sc in enumerate(scenes):
        wav = work / f"voice_{i:02d}.wav"
        run(["ffmpeg", "-y", "-i", str(sc.audio), "-af", "apad", "-t", f"{sc.duration:.3f}",
             "-ar", "44100", "-ac", "2", str(wav)])
        wavs.append(wav)
    (work / "audio.txt").write_text("".join(f"file '{p.name}'\n" for p in wavs))
    narration = work / "narration.wav"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "audio.txt"),
         "-c", "copy", str(narration)])

    # Görüntü: sahne parçalarını üret ve birleştir
    segs = [render_scene_video(sc, i, work) for i, sc in enumerate(scenes)]
    (work / "video.txt").write_text("".join(f"file '{p.name}'\n" for p in segs))
    video = work / "video.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "video.txt"),
         "-c", "copy", str(video)])

    ass = work / "subs.ass"
    build_ass(all_words, total, episode.get("font", "DejaVu Sans"), ass)

    # Arka plan müziği (varsa)
    music_dir = ROOT / "assets" / "music"
    tracks = sorted(p for p in music_dir.glob("*") if p.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg"}) \
        if music_dir.exists() and episode.get("music", True) else []

    final = out_dir / f"{slug}.mp4"
    cmd = ["ffmpeg", "-y", "-i", str(video), "-i", str(narration)]
    if tracks:
        cmd += ["-stream_loop", "-1", "-i", str(random.choice(tracks))]
        afilter = ("[2:a]volume=0.12,afade=t=out:st={st:.2f}:d=1.2[m];"
                   "[1:a][m]amix=inputs=2:duration=first:dropout_transition=0,"
                   "loudnorm=I=-14:TP=-1.5:LRA=11[a]").format(st=max(0.0, total - 1.2))
    else:
        afilter = "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    fonts_dir = ROOT / "assets" / "fonts"
    sub_opts = f"subtitles={ass.as_posix()}" + (f":fontsdir={fonts_dir.as_posix()}" if fonts_dir.exists() else "")
    cmd += ["-filter_complex", f"[0:v]{sub_opts}[v];{afilter}",
            "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(final)]
    run(cmd)
    log(f"Hazır: {final} ({total:.1f} sn)")
    return final


def load_episode(path: Path) -> dict:
    ep = json.loads(path.read_text(encoding="utf-8"))
    ep["_slug"] = path.stem
    for k in ("title", "scenes"):
        if k not in ep:
            raise ValueError(f"{path}: '{k}' alanı eksik")
    return ep


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", type=Path)
    ap.add_argument("--out", type=Path, default=ROOT / "build")
    ap.add_argument("--offline", action="store_true", help="İnternetsiz test (sessiz ses, düz renk)")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    render(load_episode(a.episode), a.out, offline=a.offline)


if __name__ == "__main__":
    main()
