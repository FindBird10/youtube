"""Bir bölüm JSON dosyasından dikey (1080x1920) YouTube Shorts videosu üretir.

Adımlar:
  1. Tüm metni tek parça halinde seslendirir (kelime zamanlarıyla): AZURE_SPEECH_KEY
     tanımlıysa Azure Speech, değilse Edge-TTS.
  2. Kelime zamanlarından sahne sınırlarını bulur.
  3. Her sahne için Pexels'ten dikey stok video indirir (yoksa düz renk arka plan).
  4. Sahneleri hafif yakınlaşma ve yumuşak geçişlerle birleştirir,
     kelime kelime altyazıyı yakar, isteğe bağlı arka plan müziği ekler.

Kullanım:
  python pipeline/make_video.py episodes/2026-09-29-konu.json --out build/
  python pipeline/make_video.py episodes/_ornek.json --offline   # internetsiz test
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
XFADE = 0.4          # sahne geçişi (sn)
TAIL = 0.5           # son kelimeden sonra bırakılan süre (sn)
ZOOM = 0.06          # sahne boyunca yakınlaşma miktarı
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VOICE = "tr-TR-AhmetNeural"
SENTENCE_PAUSE_MS = 300  # Azure: cümleler arası sessizlik (ms)
DEFAULT_RATE = "+5%"      # +12% aceleci duruyordu; +5% daha doğal ve akıcı
FALLBACK_COLORS = ["0x14213d", "0x1b263b", "0x2b2d42", "0x3a0ca3", "0x264653", "0x5f0f40"]
STOPWORDS = {"a", "an", "the", "of", "in", "on", "and", "with", "at", "to", "for", "from", "by", "video",
              "stock", "footage", "free", "hd", "4k", "is", "are", "its", "it", "up", "view", "shot"}
TOKEN_RE = re.compile(r"[\w'’]+", re.UNICODE)


@dataclass
class Word:
    start: float  # saniye (videonun başından itibaren)
    end: float
    text: str


@dataclass
class Scene:
    text: str
    search: str
    start: float = 0.0
    duration: float = 0.0
    clip: Path | None = None
    words: list[Word] = field(default_factory=list)


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
async def _tts(text: str, voice: str, rate: str, out: Path) -> list[Word]:
    import edge_tts

    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    words: list[Word] = []
    with open(out, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append(Word(start, start + chunk["duration"] / 1e7, chunk["text"]))
    return words


def _azure_tts(text: str, voice: str, rate: str, out: Path) -> list[Word]:
    """Azure Speech (resmi servis). AZURE_SPEECH_KEY ve AZURE_SPEECH_REGION gerekir."""
    from xml.sax.saxutils import escape

    import azure.cognitiveservices.speech as speechsdk

    cfg = speechsdk.SpeechConfig(subscription=os.environ["AZURE_SPEECH_KEY"].strip(),
                                 region=os.environ.get("AZURE_SPEECH_REGION", "northeurope").strip())
    cfg.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio24Khz96KBitRateMonoMp3)
    synth = speechsdk.SpeechSynthesizer(speech_config=cfg,
                                        audio_config=speechsdk.audio.AudioOutputConfig(filename=str(out)))
    words: list[Word] = []

    def on_boundary(evt) -> None:
        if evt.boundary_type == speechsdk.SpeechSynthesisBoundaryType.Word:
            start = evt.audio_offset / 1e7
            words.append(Word(start, start + evt.duration.total_seconds(), evt.text))

    synth.synthesis_word_boundary.connect(on_boundary)
    lang = "-".join(voice.split("-")[:2])
    # Cümle arası duraksama kısaltılır; kesik kesik değil akıcı okunur.
    ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            f'xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="{lang}">'
            f'<voice name="{voice}"><mstts:silence type="Sentenceboundary-exact" value="{SENTENCE_PAUSE_MS}ms"/>'
            f'<prosody rate="{rate}">{escape(text)}</prosody></voice></speak>')
    res = synth.speak_ssml_async(ssml).get()
    del synth  # dosyanın diske yazılmasını garanti et
    if res.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        detail = getattr(res, "cancellation_details", None)
        raise RuntimeError(f"Azure TTS başarısız: {res.reason} {getattr(detail, 'error_details', '')}")
    return words


def assign_scenes(scenes: list[Scene], words: list[Word], audio_dur: float) -> float:
    """TTS kelimelerini sahnelere dağıtır, sahne başlangıç/sürelerini ayarlar. Toplam süreyi döner."""
    counts = [max(1, len(TOKEN_RE.findall(s.text))) for s in scenes]
    if sum(counts) != len(words):
        # Sayılar tutmuyorsa (ör. TTS bir kelimeyi bölmüşse) karakter oranına göre dağıt
        chars = [max(1, len(s.text)) for s in scenes]
        total_c, acc, bounds = sum(chars), 0, [0]
        for c in chars:
            acc += c
            bounds.append(round(acc / total_c * len(words)))
        counts = [b - a for a, b in zip(bounds, bounds[1:])]
        log(f"Uyarı: kelime sayısı eşleşmedi, orana göre dağıtıldı {counts}")

    idx = 0
    for sc, n in zip(scenes, counts):
        sc.words = words[idx: idx + n]
        idx += n
    total = audio_dur + TAIL
    for i, sc in enumerate(scenes):
        sc.start = 0.0 if i == 0 else (sc.words[0].start if sc.words else scenes[i - 1].start + 1.0)
    for i, sc in enumerate(scenes):
        nxt = scenes[i + 1].start if i + 1 < len(scenes) else total
        sc.duration = max(0.8, nxt - sc.start)
    return total


def synthesize(scenes: list[Scene], voice: str, rate: str, work: Path, offline: bool) -> tuple[Path, list[Word], float]:
    mp3 = work / "narration.mp3"
    full_text = " ".join(s.text for s in scenes)
    if offline:
        tokens = TOKEN_RE.findall(full_text)
        dur = 0.36 * len(tokens)
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
             "-t", f"{dur:.2f}", "-q:a", "9", str(mp3)])
        words = [Word(k * 0.36, k * 0.36 + 0.3, t) for k, t in enumerate(tokens)]
    else:
        words = []
        if os.environ.get("AZURE_SPEECH_KEY", "").strip():
            try:
                words = _azure_tts(full_text, voice, rate, mp3)
                log(f"Seslendirme: Azure Speech ({voice}, {rate})")
            except Exception as e:
                log(f"Azure TTS hatası, Edge-TTS'e geçiliyor: {e}")
                words = []
        if not words:
            for attempt in range(3):
                try:
                    words = asyncio.run(_tts(full_text, voice, rate, mp3))
                    log(f"Seslendirme: Edge-TTS ({voice}, {rate})")
                    break
                except Exception as e:  # ağ hatalarında tekrar dene
                    log(f"TTS hatası (deneme {attempt + 1}): {e}")
                    if attempt == 2:
                        raise
    audio_dur = probe_duration(mp3)
    total = assign_scenes(scenes, words, audio_dur)
    for i, sc in enumerate(scenes):
        log(f"Sahne {i + 1}: {sc.start:.1f}–{sc.start + sc.duration:.1f} sn, {len(sc.words)} kelime")
    return mp3, words, total


# ------------------------------------------------------------- stok görüntü
def fetch_clips(scenes: list[Scene], work: Path, offline: bool) -> None:
    if offline:
        # İnternetsiz test: tek sahnelere test deseni klibi ver (geçiş/zoom görülsün)
        for i, sc in enumerate(scenes):
            if i % 2 == 0:
                p = work / f"clip_{i:02d}.mp4"
                run(["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=s=1280x720:r=25",
                     "-t", "3", "-pix_fmt", "yuv420p", str(p)])
                sc.clip = p
        return
    pexels_key = os.environ.get("PEXELS_API_KEY", "").strip()
    pixabay_key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not pexels_key and not pixabay_key:
        log("PEXELS_API_KEY / PIXABAY_API_KEY yok; düz renk arka plan kullanılacak.")
        return
    import requests

    used: set[str] = set()

    def stems(text: str) -> set[str]:
        return {w[:-1] if len(w) > 4 and w.endswith("s") else w
                for w in re.findall(r"[a-z]+", text.lower()) if w not in STOPWORDS and len(w) > 1}

    def pexels(query: str) -> list[dict]:
        r = requests.get("https://api.pexels.com/videos/search", timeout=30,
                         headers={"Authorization": pexels_key},
                         params={"query": query, "orientation": "portrait", "size": "medium", "per_page": 20})
        r.raise_for_status()
        out = []
        for v in r.json().get("videos", []):
            files = [f for f in v.get("video_files", []) if f.get("height") and f.get("width") and f.get("link")]
            if not files:
                continue
            portrait = [f for f in files if f["height"] >= f["width"]] or files
            # 1080 genişliğe en yakın, ondan küçük olmayanı seç
            portrait.sort(key=lambda f: (f["width"] < 1080, abs(f["width"] - 1080)))
            f = portrait[0]
            slug = v.get("url", "").rstrip("/").rsplit("/", 1)[-1]
            out.append({"key": f"pexels:{v['id']}", "words": stems(slug + " " + " ".join(v.get("tags", []))),
                        "duration": v.get("duration", 0), "w": f["width"], "h": f["height"], "url": f["link"]})
        return out

    def pixabay(query: str) -> list[dict]:
        r = requests.get("https://pixabay.com/api/videos/", timeout=30,
                         params={"key": pixabay_key, "q": query[:100], "per_page": 20, "safesearch": "true"})
        r.raise_for_status()
        out = []
        for v in r.json().get("hits", []):
            files = [f for f in (v.get("videos") or {}).values() if f.get("url") and f.get("height")]
            if not files:
                continue
            # Dikeye kırpılınca bulanık olmasın: yeterince yüksek olan en küçük dosya
            files.sort(key=lambda f: (f["height"] < 1900, f["height"] if f["height"] >= 1900 else -f["height"]))
            f = files[0]
            out.append({"key": f"pixabay:{v['id']}", "words": stems(v.get("tags", "")),
                        "duration": v.get("duration", 0), "w": f["width"], "h": f["height"], "url": f["url"]})
        return out

    def score(c: dict, want: set[str], need: float) -> float:
        rel = len(want & c["words"]) / max(1, len(want))          # konuya uygunluk (0–1)
        s = 3.0 * rel
        s += 1.5 if c["h"] >= c["w"] else 0.0                    # dikey video kırpılmaz
        s += 1.0 if c["duration"] >= need else 0.0               # döngüye girmez
        s += 0.5 if min(c["w"], c["h"]) >= 1080 else 0.0         # net görüntü
        return s + random.uniform(0, 0.4)                          # her seferinde aynı video çıkmasın

    sources = [("Pexels", pexels)] if pexels_key else []
    sources += [("Pixabay", pixabay)] if pixabay_key else []

    for i, sc in enumerate(scenes):
        need = sc.duration + XFADE
        want = stems(sc.search)
        queries = [sc.search, " ".join(sc.search.split()[:2]), (sc.search.split() or [""])[0]]
        best, best_score = None, -1.0
        for q in dict.fromkeys(q for q in queries if q):
            cands = []
            for name, fn in sources:
                try:
                    cands += [c for c in fn(q) if c["key"] not in used]
                except Exception as e:
                    # Hata metni URL'yi (Pixabay'de anahtarı) içerebilir; yalnızca durum kodunu yaz
                    code = getattr(getattr(e, "response", None), "status_code", type(e).__name__)
                    log(f"{name} arama hatası '{q}': {code}")
            for c in cands:
                s = score(c, want, need)
                if s > best_score:
                    best, best_score = c, s
            # Konuyla eşleşen bir sonuç bulunduysa daha kısa sorgulara inme
            if best and want & best["words"]:
                break
        if not best:
            log(f"Sahne {i + 1}: görüntü bulunamadı, düz renk kullanılacak.")
            continue
        used.add(best["key"])
        dst = work / f"clip_{i:02d}.mp4"
        try:
            with requests.get(best["url"], stream=True, timeout=180) as r:
                r.raise_for_status()
                with open(dst, "wb") as f:
                    for part in r.iter_content(1 << 20):
                        f.write(part)
        except Exception as e:
            log(f"Sahne {i + 1}: indirme hatası ({type(e).__name__}), düz renk kullanılacak.")
            continue
        sc.clip = dst
        log(f"Sahne {i + 1}: {best['key']} {best['w']}x{best['h']} puan {best_score:.1f} ({sc.search})")


# ------------------------------------------------------------------ altyazı
def ass_escape(s: str) -> str:
    return s.replace("\\", "").replace("{", "").replace("}", "")


def ts(t: float) -> str:
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


# Altyazı alt kenardan bu kadar yukarıda durur (1920 px'lik dikey video).
# Shorts arayüzü (başlık, butonlar) en alttaki ~%25'i kapladığı için 560 px güvenli bölge.
CAPTION_MARGIN_V = 560
# Vurgu rengi (ASS biçimi &HBBGGRR): yumuşak açık turkuaz; göz yormayan, beyazla uyumlu.
HIGHLIGHT = "&HE8D9A8&"
# Açılış kancası: ilk bu kadar saniye, üst kenardan bu kadar aşağıda (Shorts'un üst simgelerinin altı).
HOOK_SECONDS = 2.6
HOOK_MARGIN_V = 300
# İlerleme çubuğu (üst kenar)
BAR_HEIGHT = 12
BAR_COLOR = "white@0.85"

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,{font},112,&H00FFFFFF,&H00FFFFFF,&H00202020,&H80000000,-1,0,0,0,100,100,1,0,1,6,3,2,60,60,{mv},1
Style: Cap,{font},88,&H00FFFFFF,&H00FFFFFF,&H00202020,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,2,80,80,{mv},1
Style: Hook,{font},92,&H00FFFFFF,&H00FFFFFF,&H50000000,&H00000000,-1,0,0,0,100,100,0,0,3,22,0,8,110,110,{hook_mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _word_events(words: list[Word], total: float) -> list[str]:
    """Tek kelime, beyaz, ekranın alt-ortasında; hafif 'pop'."""
    lines = []
    for i, w in enumerate(words):
        text = ass_escape(tr_upper(w.text.strip()))
        if not text:
            continue
        nxt = words[i + 1].start if i + 1 < len(words) else total
        end = min(nxt, w.end + 0.5, total)
        if end - w.start < 0.05:
            continue
        # Uzun kelimeler ekrandan taşmasın
        fs = min(112, int(960 / (0.72 * max(1, len(text)))))
        pop = "{\\fs%d\\fscx108\\fscy108\\t(0,80,\\fscx100\\fscy100)}" % fs
        lines.append(f"Dialogue: 0,{ts(w.start)},{ts(end)},Word,,0,0,0,,{pop}{text}")
    return lines


def _group_events(words: list[Word], total: float, max_words: int = 3, max_chars: int = 18) -> list[str]:
    """2–3 kelimelik beyaz grup, konuşulan kelime yumuşak vurgu renginde."""
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
    if cur:
        groups.append(cur)
    lines = []
    for gi, g in enumerate(groups):
        g_end = groups[gi + 1][0].start if gi + 1 < len(groups) else total
        g_end = min(g_end, g[-1].end + 0.6)
        for wi, w in enumerate(g):
            end = g[wi + 1].start if wi + 1 < len(g) else g_end
            if end <= w.start:
                continue
            parts = []
            for k, x in enumerate(g):
                t = ass_escape(tr_upper(x.text))
                parts.append("{\\c" + HIGHLIGHT + "}" + t + "{\\c&HFFFFFF&}" if k == wi else t)
            lines.append(f"Dialogue: 0,{ts(w.start)},{ts(end)},Cap,,0,0,0,,{' '.join(parts)}")
    return lines


EMOJI_RE = re.compile("[\U0001F000-\U0001FFFF☀-➿️‍]+")


def hook_text(episode: dict) -> str:
    """Açılışta gösterilecek kısa kanca yazısı: 'hook' alanı ya da kısa başlık."""
    text = (episode.get("hook") or "").strip()
    if not text:
        title = EMOJI_RE.sub("", episode.get("title", "")).strip()
        text = title if len(title) <= 48 else ""
    return EMOJI_RE.sub("", text).strip()


def _hook_events(text: str, until: float) -> list[str]:
    """İlk ~2,5 sn üst bölümde yarı saydam kutu içinde büyük başlık."""
    if not text:
        return []
    t = ass_escape(tr_upper(text))
    anim = "{\\q0\\fad(120,300)\\fscx92\\fscy92\\t(0,160,\\fscx100\\fscy100)}"
    return [f"Dialogue: 1,{ts(0)},{ts(until)},Hook,,0,0,0,,{anim}{t}"]


def build_ass(words: list[Word], total: float, font: str, path: Path, style: str = "word",
              hook: str = "") -> None:
    events = _group_events(words, total) if style == "group" else _word_events(words, total)
    events = _hook_events(hook, min(HOOK_SECONDS, total)) + events
    header = ASS_HEADER.format(W=W, H=H, font=font, mv=CAPTION_MARGIN_V, hook_mv=HOOK_MARGIN_V)
    path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


# -------------------------------------------------------------------- montaj
def render_scene_video(sc: Scene, idx: int, length: float, work: Path) -> Path:
    """Sahne parçasını üretir: ortadan kırpma + yavaş yakınlaşma."""
    out = work / f"seg_{idx:02d}.mp4"
    frames = max(1, round(length * FPS))
    bw, bh = int(W * 1.1) // 2 * 2, int(H * 1.1) // 2 * 2
    zoom = (f"zoompan=z='1+{ZOOM}*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d=1:s={W}x{H}:fps={FPS}")
    if sc.clip:
        src = ["-stream_loop", "-1", "-i", str(sc.clip)]
        vf = (f"fps={FPS},scale={bw}:{bh}:force_original_aspect_ratio=increase,"
              f"crop={bw}:{bh},{zoom},setsar=1,format=yuv420p")
    else:
        color = FALLBACK_COLORS[idx % len(FALLBACK_COLORS)]
        src = ["-f", "lavfi", "-i", f"color=c={color}:s={bw}x{bh}:r={FPS}"]
        vf = f"{zoom},setsar=1,format=yuv420p"
    run(["ffmpeg", "-y", *src, "-vf", vf, "-frames:v", str(frames), "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out)])
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

    narration, words, total = synthesize(
        scenes, episode.get("voice", DEFAULT_VOICE), episode.get("rate", DEFAULT_RATE), work, offline)
    if total > 59:
        log(f"UYARI: video {total:.1f} sn; Shorts için 60 saniyenin altı önerilir.")
    fetch_clips(scenes, work, offline)

    # Son sahne dışındaki parçalar geçiş süresi kadar uzun üretilir, böylece
    # xfade sonrası toplam süre sesle birebir aynı kalır.
    segs = []
    for i, sc in enumerate(scenes):
        length = sc.duration + (XFADE if i < len(scenes) - 1 else 0.0)
        segs.append(render_scene_video(sc, i, length, work))

    ass = work / "subs.ass"
    build_ass(words, total, episode.get("font", "DejaVu Sans"), ass, episode.get("caption_style", "word"),
              hook=hook_text(episode) if episode.get("show_hook", True) else "")

    # Görüntü zinciri: seg0 x seg1 x ... -> altyazı
    vchain, last = [], "0:v"
    for k in range(1, len(segs)):
        label = f"x{k}"
        vchain.append(f"[{last}][{k}:v]xfade=transition=fade:duration={XFADE}:offset={scenes[k].start:.3f}[{label}]")
        last = label
    fonts_dir = ROOT / "assets" / "fonts"
    sub = f"subtitles={ass.as_posix()}" + (f":fontsdir={fonts_dir.as_posix()}" if fonts_dir.exists() else "")
    if episode.get("progress_bar", True):
        # Üst kenarda soldan sağa dolan ince ilerleme çubuğu
        vchain.append(f"color=c={BAR_COLOR}:s={W}x{BAR_HEIGHT}:r={FPS}:d={total:.3f},format=rgba[bar]")
        vchain.append(f"[{last}]{sub}[vs]")
        vchain.append(f"[vs][bar]overlay=x='-w+W*t/{total:.3f}':y=0:eval=frame:shortest=1,format=yuv420p[v]")
    else:
        vchain.append(f"[{last}]{sub}[v]")

    # Ses: anlatım (+ varsa kısık müzik)
    n = len(segs)
    music_dir = ROOT / "assets" / "music"
    tracks = sorted(p for p in music_dir.glob("*") if p.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg"}) \
        if music_dir.exists() and episode.get("music", True) else []
    inputs = []
    for p in segs:
        inputs += ["-i", str(p)]
    inputs += ["-i", str(narration)]
    if tracks:
        inputs += ["-stream_loop", "-1", "-i", str(random.choice(tracks))]
        achain = (f"[{n}:a]apad[nar];[{n + 1}:a]volume=0.12,afade=t=out:st={max(0.0, total - 1.2):.2f}:d=1.2[m];"
                  f"[nar][m]amix=inputs=2:duration=first:dropout_transition=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    else:
        achain = f"[{n}:a]apad,loudnorm=I=-14:TP=-1.5:LRA=11[a]"

    final = out_dir / f"{slug}.mp4"
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(vchain + [achain]),
         "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", str(final)])
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
    ap.add_argument("--offline", action="store_true", help="İnternetsiz test (sessiz ses, test deseni)")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    render(load_episode(a.episode), a.out, offline=a.offline)


if __name__ == "__main__":
    main()
