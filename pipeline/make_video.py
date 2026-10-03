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
# Azure çok dilli sesler (Türkçe okutulur). Formata göre ses: enerjik Brian soru/senaryo,
# daha doğal/duygulu Andrew gizem hikâyeleri. Bölümde "voice" yazılırsa o kullanılır.
VOICE_BY_FORMAT = {
    "neden": ("en-US-BrianMultilingualNeural", "+8%"),
    "ne-olurdu": ("en-US-BrianMultilingualNeural", "+8%"),
    "gizem": ("en-US-AndrewMultilingualNeural", "+8%"),
    # İngilizce kanallar
    "lore": ("en-US-AndrewMultilingualNeural", "+0%"),
    "what-if": ("en-US-BrianMultilingualNeural", "+5%"),
    "dark-history": ("en-US-AndrewMultilingualNeural", "+3%"),
    "psychology": ("en-US-BrianMultilingualNeural", "+5%"),
    "business": ("en-US-AndrewMultilingualNeural", "+5%"),
    # Oyun haberleri: enerjik (ses örneklerinden kullanıcı seçene kadar Brian, hızlı)
    "news": ("en-US-BrianMultilingualNeural", "+14%"),
}
# Formata göre ek ses ayarları: perde ve Azure konuşma stili (yalnızca stil destekleyen seslerde)
VOICE_EXTRA = {
    "news": {"pitch": "+3%", "style": "", "style_degree": 1.0},
}
DEFAULT_AZURE_VOICE = ("en-US-AndrewMultilingualNeural", "+8%")
EDGE_FALLBACK_VOICE = "tr-TR-AhmetNeural"  # Azure çalışmazsa Türkçe yerel sesle devam
FALLBACK_COLORS = ["0x14213d", "0x1b263b", "0x2b2d42", "0x3a0ca3", "0x264653", "0x5f0f40"]
STOPWORDS = {"a", "an", "the", "of", "in", "on", "and", "with", "at", "to", "for", "from", "by", "video",
              "stock", "footage", "free", "hd", "4k", "is", "are", "its", "it", "up", "view", "shot"}
# Gerçek çekim videoların arasına çizim/animasyon girmesin: bu etiketlerden biri varsa aday elenir.
ANIMATION_WORDS = {"animation", "animated", "animate", "cartoon", "anime", "illustration", "drawing", "drawn",
                   "sketch", "clipart", "vector", "render", "rendering", "cgi", "3d", "2d", "infographic",
                   "hologram", "fractal"}
TOKEN_RE = re.compile(r"[\w'’]+", re.UNICODE)


@dataclass
class Word:
    start: float  # saniye (videonun başından itibaren)
    end: float
    text: str
    brk: bool = False  # metinde bu kelimeden sonra noktalama var (altyazı satırı burada biter)
    pos: int = -1      # kelimenin tam metindeki karakter konumu (bulunamadıysa -1)


@dataclass
class Scene:
    text: str
    search: str
    start: float = 0.0
    duration: float = 0.0
    clip: Path | None = None
    words: list[Word] = field(default_factory=list)
    image_query: str | None = None   # wiki görseli istenen sahne (anahtar kelimeler)
    image: Path | None = None
    image_page: str | None = None    # görselin aranacağı wiki sayfası (boşsa bölümün sayfası)
    n_shots: int = 1                 # sahnedeki çekim sayısı (hızlı kesme stilinde >1)
    extra_clips: list[Path] = field(default_factory=list)
    extra_images: list[Path] = field(default_factory=list)
    trailer: bool = False            # arka plan oyunun Steam fragmanından kesilsin (gaming)


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


CAPTION_LANG = "tr"  # render() bölümün diline göre ayarlar


def tr_upper(s: str) -> str:
    """Büyük harf; Türkçe'de i -> İ, ı -> I (İngilizce vb. dillerde normal)."""
    if CAPTION_LANG == "tr":
        return s.replace("i", "İ").replace("ı", "I").upper()
    return s.upper()


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


def _azure_tts(text: str, voice: str, rate: str, out: Path, pitch: str = "+0%",
               speak_lang: str = "tr-TR", style: str = "", style_degree: float = 1.0) -> list[Word]:
    """Azure Speech (resmi servis). AZURE_SPEECH_KEY ve AZURE_SPEECH_REGION gerekir.

    Çok dilli sesler (ör. en-US-AndrewMultilingualNeural) de kullanılabilir; ses kendi
    dilinden farklıysa metin <lang xml:lang="tr-TR"> ile Türkçe okutulur.
    """
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
    body = f'<prosody rate="{rate}" pitch="{pitch}">{escape(text)}</prosody>'
    if lang.lower() != speak_lang.lower():
        body = f'<lang xml:lang="{speak_lang}">{body}</lang>'
    if style:  # ör. "excited" — yalnızca stil destekleyen seslerde (Davis, Tony, Jason...)
        body = f'<mstts:express-as style="{style}" styledegree="{style_degree}">{body}</mstts:express-as>'
    # Cümle arası duraksama kısaltılır; kesik kesik değil akıcı okunur.
    ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            f'xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="{lang}">'
            f'<voice name="{voice}"><mstts:silence type="Sentenceboundary-exact" value="{SENTENCE_PAUSE_MS}ms"/>'
            f'{body}</voice></speak>')
    res = synth.speak_ssml_async(ssml).get()
    del synth  # dosyanın diske yazılmasını garanti et
    if res.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        detail = getattr(res, "cancellation_details", None)
        raise RuntimeError(f"Azure TTS başarısız: {res.reason} {getattr(detail, 'error_details', '')}")
    return words


def assign_scenes(scenes: list[Scene], words: list[Word], audio_dur: float) -> float:
    """TTS kelimelerini sahnelere dağıtır, sahne başlangıç/sürelerini ayarlar. Toplam süreyi döner."""
    counts = [max(1, len(TOKEN_RE.findall(s.text))) for s in scenes]
    found = sum(1 for w in words if w.pos >= 0)
    if words and sum(counts) != len(words) and found >= 0.8 * len(words):
        # Kelimeleri metindeki konumlarına göre sahnelere yerleştir (sayılar vb. TTS'te
        # farklı bölündüğünde bile doğru sahneye düşer)
        spans, c = [], 0
        for sc_ in scenes:
            spans.append((c, c + len(sc_.text)))
            c += len(sc_.text) + 1
        owner, cur = [], 0
        for w in words:
            if w.pos >= 0:
                cur = next((k for k, (a, b) in enumerate(spans) if a <= w.pos <= b), cur)
            owner.append(cur)
        counts = [owner.count(k) for k in range(len(scenes))]
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


def mark_breaks(words: list[Word], text: str) -> None:
    """TTS kelimelerini metinde sırayla bulur; ardından noktalama gelenleri işaretler."""
    low, pos = text.lower(), 0
    for w in words:
        t = w.text.strip().lower()
        if not t:
            continue
        i = low.find(t, pos)
        if i < 0 or i - pos > 40:  # bulunamadı / çok uzakta: atla
            continue
        w.pos = i
        pos = i + len(t)
        j = pos
        while j < len(low) and low[j] in "\"'’”»)":
            j += 1
        w.brk = j < len(low) and low[j] in ".!?,;:…"


SPEAK_LANG = {"tr": "tr-TR", "en": "en-US"}
EDGE_FALLBACK = {"tr": "tr-TR-AhmetNeural", "en": "en-US-AndrewMultilingualNeural"}


def synthesize(scenes: list[Scene], voice: str, rate: str, work: Path, offline: bool, pitch: str = "+0%",
               language: str = "tr", speak_style: str = "", style_degree: float = 1.0
               ) -> tuple[Path, list[Word], float]:
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
                words = _azure_tts(full_text, voice, rate, mp3, pitch=pitch,
                                   speak_lang=SPEAK_LANG.get(language, "tr-TR"),
                                   style=speak_style, style_degree=style_degree)
                log(f"Seslendirme: Azure Speech ({voice}, {rate})")
            except Exception as e:
                log(f"Azure TTS hatası, Edge-TTS'e geçiliyor: {e}")
                words = []
        if not words:
            for attempt in range(3):
                try:
                    native = voice.lower().startswith(SPEAK_LANG.get(language, "tr-TR").lower()[:2] + "-")
                    edge_voice = voice if native else EDGE_FALLBACK.get(language, EDGE_FALLBACK_VOICE)
                    words = asyncio.run(_tts(full_text, edge_voice, rate, mp3))
                    log(f"Seslendirme: Edge-TTS ({edge_voice}, {rate})")
                    break
                except Exception as e:  # ağ hatalarında tekrar dene
                    log(f"TTS hatası (deneme {attempt + 1}): {e}")
                    if attempt == 2:
                        raise
    audio_dur = probe_duration(mp3)
    mark_breaks(words, full_text)
    total = assign_scenes(scenes, words, audio_dur)
    for i, sc in enumerate(scenes):
        log(f"Sahne {i + 1}: {sc.start:.1f}–{sc.start + sc.duration:.1f} sn, {len(sc.words)} kelime")
    return mp3, words, total


# ------------------------------------------------------------- stok görüntü
def fetch_clips(scenes: list[Scene], work: Path, offline: bool, subject: str = "") -> None:
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
                for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS and len(w) > 1}

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
            out.append({"key": f"pexels:{v['id']}", "rank": len(out),
                        "words": stems(slug + " " + " ".join(v.get("tags", []))),
                        "duration": v.get("duration", 0), "w": f["width"], "h": f["height"], "url": f["link"]})
        return out

    def pixabay(query: str) -> list[dict]:
        r = requests.get("https://pixabay.com/api/videos/", timeout=30,
                         params={"key": pixabay_key, "q": query[:100], "per_page": 20, "safesearch": "true",
                                 "video_type": "film"})
        r.raise_for_status()
        out = []
        for v in r.json().get("hits", []):
            files = [f for f in (v.get("videos") or {}).values() if f.get("url") and f.get("height")]
            if not files:
                continue
            # Dikeye kırpılınca bulanık olmasın: yeterince yüksek olan en küçük dosya
            files.sort(key=lambda f: (f["height"] < 1900, f["height"] if f["height"] >= 1900 else -f["height"]))
            f = files[0]
            out.append({"key": f"pixabay:{v['id']}", "rank": len(out), "words": stems(v.get("tags", "")),
                        "duration": v.get("duration", 0), "w": f["width"], "h": f["height"], "url": f["url"]})
        return out

    def score(c: dict, want: set[str], key: set[str], need: float) -> float:
        # Önce konu: ana özne (ör. "octopus") eşleşmesi her şeyden önemli, sonra diğer kelimeler.
        s = 6.0 if key & c["words"] else 0.0
        s += 3.0 * len(want & c["words"]) / max(1, len(want))
        s += 1.0 * (1 - min(c.get("rank", 19), 19) / 20)          # sitenin kendi uygunluk sırası
        s += 0.8 if c["h"] >= c["w"] else 0.0                    # dikey video kırpılmaz
        s += 0.5 if c["duration"] >= need else 0.0               # döngüye girmez
        s += 0.3 if min(c["w"], c["h"]) >= 1080 else 0.0         # net görüntü
        return s + random.uniform(0, 0.2)                          # her seferinde aynı video çıkmasın

    sources = [("Pexels", pexels)] if pexels_key else []
    sources += [("Pixabay", pixabay)] if pixabay_key else []

    subj = stems(subject)
    for i, sc in enumerate(scenes):
        need = sc.duration + XFADE
        want = stems(sc.search)
        # Ana özne: bölümün 'subject' alanı aramada geçiyorsa o, yoksa aramanın ilk kelimesi
        key = (subj & want) or set(list(stems((sc.search.split() or [""])[0]))[:1])
        words = sc.search.split()
        queries = [sc.search, " ".join(words[:2]), words[0] if words else "", subject]
        best, best_score = None, -1.0
        ranked: dict[str, tuple[float, dict]] = {}
        for q in dict.fromkeys(q for q in queries if q):
            cands = []
            for name, fn in sources:
                try:
                    cands += [c for c in fn(q) if c["key"] not in used]
                except Exception as e:
                    # Hata metni URL'yi (Pixabay'de anahtarı) içerebilir; yalnızca durum kodunu yaz
                    code = getattr(getattr(e, "response", None), "status_code", type(e).__name__)
                    log(f"{name} arama hatası '{q}': {code}")
            cands = [c for c in cands if not (c["words"] & ANIMATION_WORDS)]
            for c in cands:
                sc_ = score(c, want, key, need)
                ranked[c["key"]] = (sc_, c)
                if sc_ > best_score:
                    best, best_score = c, sc_
            # Ana özneyi içeren bir sonuç bulunduysa daha kısa sorgulara inme
            if best and key & best["words"]:
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
        # Hızlı kesme: aynı sahne için ek, farklı klipler (öncelik ana özneyi içerenlerde)
        extras = sorted((v for k, v in ranked.items() if k != best["key"] and k not in used),
                        key=lambda v: (bool(key & v[1]["words"]), v[0]), reverse=True)
        for j, (_, c) in enumerate(extras[: max(0, sc.n_shots - 1)]):
            dst2 = work / f"clip_{i:02d}_{j + 1}.mp4"
            try:
                with requests.get(c["url"], stream=True, timeout=180) as r:
                    r.raise_for_status()
                    with open(dst2, "wb") as f:
                        for part in r.iter_content(1 << 20):
                            f.write(part)
                used.add(c["key"])
                sc.extra_clips.append(dst2)
            except Exception as e:
                log(f"Sahne {i + 1}: ek klip indirilemedi ({type(e).__name__})")
        if sc.extra_clips:
            log(f"Sahne {i + 1}: +{len(sc.extra_clips)} ek klip (hızlı kesme)")


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
HIGHLIGHT = "&H00E5FF&"  # parlak sarı: o an söylenen kelime
# Açılış kancası: ilk bu kadar saniye, üst kenardan bu kadar aşağıda (Shorts'un üst simgelerinin altı).
HOOK_SECONDS = 2.6
HOOK_MARGIN_V = 300
# İlerleme çubuğu (üst kenar)
BAR_HEIGHT = 12
BAR_COLOR = "white@0.85"
# Arka plan müziği seviyesi (assets/music/*); konuşma sırasında ayrıca kısılır
MUSIC_VOLUME = 0.28

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,{font},112,&H00FFFFFF,&H00FFFFFF,&H00202020,&H80000000,-1,0,0,0,100,100,1,0,1,6,3,2,60,60,{mv},1
Style: Cap,{font},82,&H00FFFFFF,&H00FFFFFF,&H00202020,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,2,80,80,{mv},1
Style: Hook,{font},92,&H00FFFFFF,&H00FFFFFF,&H50000000,&H00000000,-1,0,0,0,100,100,0,0,3,22,0,8,110,110,{hook_mv},1
Style: Box,Poppins ExtraBold,94,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,6,3,2,60,60,{mv},1
Style: Title,Anton,150,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,2,0,1,8,5,5,80,80,0,1
Style: Dim,Poppins ExtraBold,10,&H60000000,&H60000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Reveal,Poppins Medium,56,&H20FFFFFF,&H20FFFFFF,&H90000000,&H90000000,0,0,0,0,100,100,7,0,1,1.5,3,2,90,90,{cine_mv},1

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


BOX_COLOR = "&HF65C8B&"  # mor vurgu kutusu (global stil)


def _group_events(words: list[Word], total: float, max_words: int = 3, max_chars: int = 16,
                  box: bool = False) -> list[str]:
    """2–3 kelimelik beyaz grup; o an söylenen kelime sarı yanar (karaoke)."""
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
        if w.brk:  # cümle/virgül sonunda satırı bitir; iki cümle aynı satıra karışmasın
            groups.append(cur)
            cur = []
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
                if k != wi:
                    parts.append(t)
                elif box:  # o anki kelimenin arkasında renkli kutu (kalın renkli kontur)
                    parts.append("{\\3c" + BOX_COLOR + "\\bord16\\shad0}" + t + "{\\3c&H000000&\\bord6\\shad3}")
                else:
                    parts.append("{\\c" + HIGHLIGHT + "}" + t + "{\\c&HFFFFFF&}")
            # Satır ekrana sığsın: uzun gruplarda yazı boyutu küçülür
            n_chars = sum(len(x.text) for x in g) + len(g) - 1
            top = 94 if box else 82
            fs = min(top, int(920 / (0.72 * max(1, n_chars))))
            st = "Box" if box else "Cap"
            lines.append(f"Dialogue: 0,{ts(w.start)},{ts(end)},{st},,0,0,0,,{{\\fs{fs}}}{' '.join(parts)}")
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


CINE_MARGIN_V = 600   # sinematik altyazı: alt bandın ve Shorts arayüzünün üstünde


def _reveal_events(words: list[Word], total: float, max_words: int = 5, max_chars: int = 28) -> list[str]:
    """Sinematik altyazı: ince, harf aralığı açık; harfler konuşmayla birlikte tek tek belirir."""
    groups: list[list[Word]] = []
    cur: list[Word] = []
    for w in words:
        if not w.text.strip():
            continue
        chars = sum(len(x.text) + 1 for x in cur) + len(w.text)
        if cur and (len(cur) >= max_words or chars > max_chars):
            groups.append(cur)
            cur = []
        cur.append(w)
        if w.brk:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    lines = []
    for gi, g in enumerate(groups):
        g0 = g[0].start
        g_end = groups[gi + 1][0].start if gi + 1 < len(groups) else total
        g_end = min(g_end, g[-1].end + 0.8)
        out = []
        for w in g:
            t = ass_escape(tr_upper(w.text.strip()))
            dur_ms = max(60.0, (w.end - w.start) * 1000)
            base = (w.start - g0) * 1000
            letters = []
            for k, ch in enumerate(t):
                a = int(base + dur_ms * k / max(1, len(t)))
                letters.append(f"{{\\alpha&HFF&\\t({a},{a + 140},\\alpha&H20&)}}{ch}")
            out.append("".join(letters))
        lines.append(f"Dialogue: 0,{ts(g0)},{ts(g_end)},Reveal,,0,0,0,,{{\\fad(0,220)}}{' '.join(out)}")
    return lines


def _title_events(text: str, until: float) -> list[str]:
    """Açılış başlık kartı: kararan arka plan + ortada büyük, 'vurarak' gelen başlık."""
    if not text:
        return []
    t = ass_escape(tr_upper(text))
    dim = f"{{\\p1\\fad(0,150)}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\\p0}}"
    anim = "{\\q0\\fad(0,180)\\fscx135\\fscy135\\t(0,140,\\fscx100\\fscy100)}"
    return [f"Dialogue: 3,{ts(0)},{ts(until)},Dim,,0,0,0,,{dim}",
            f"Dialogue: 4,{ts(0)},{ts(until)},Title,,0,0,0,,{anim}{t}"]


def build_ass(words: list[Word], total: float, font: str, path: Path, style: str = "group",
              hook: str = "", title: str = "", title_until: float = 0.0) -> None:
    if style in ("group", "box"):
        events = _group_events(words, total, box=(style == "box"))
    elif style == "reveal":
        events = _reveal_events(words, total)
    else:
        events = _word_events(words, total)
    events = _title_events(title, title_until) + events
    events = _hook_events(hook, min(HOOK_SECONDS, total)) + events
    header = ASS_HEADER.format(W=W, H=H, font=font, mv=CAPTION_MARGIN_V, hook_mv=HOOK_MARGIN_V,
                               cine_mv=CINE_MARGIN_V)
    path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


# -------------------------------------------------------------------- montaj
def render_scene_video(sc: Scene, idx: int, length: float, work: Path) -> Path:
    """Sahne parçasını üretir: ortadan kırpma + yavaş yakınlaşma."""
    out = work / f"seg_{idx:02d}.mp4"
    frames = max(1, round(length * FPS))
    bw, bh = int(W * 1.1) // 2 * 2, int(H * 1.1) // 2 * 2
    zoom = (f"zoompan=z='1+{ZOOM}*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d=1:s={W}x{H}:fps={FPS}")
    if sc.image:
        # Wiki görseli: yataysa soldan sağa yavaş kaydırma (Ken Burns), dikeyse yakınlaşma
        iw, ih = (int(x) for x in subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
             "-of", "csv=p=0", str(sc.image)], capture_output=True, text=True, check=True).stdout.strip().split(",")[:2])
        src = ["-loop", "1", "-framerate", str(FPS), "-i", str(sc.image)]
        from faces import focus
        face = focus(sc.image)
        if face and face[2] < 0.05:      # çok küçük (muhtemelen yanlış) yüz: dikkate alma
            face = None
        if iw / ih >= 0.8 and face:
            # Yüzü kadrajın ortasına al; yüz küçükse biraz yakınlaş (en fazla 1,5 kat), hafif kaydır
            fx, fy, fh = face
            s = min(1.5, max(1.0, 0.20 / max(fh, 1e-3)))
            sh = int(bh * s) // 2 * 2
            scaled_w = iw * sh / ih
            amp = max(0.0, min((scaled_w - bw) / 2, 70.0))
            direction = 1 if idx % 2 == 0 else -1
            vf = (f"scale=-2:{sh},crop={bw}:{bh}:"
                  f"x='clip({fx:.4f}*iw-ow/2+{direction * amp:.1f}*(2*t/{length:.3f}-1),0,iw-ow)':"
                  f"y='clip({fy:.4f}*ih-oh*0.42,0,ih-oh)',"
                  f"scale={W}:{H},setsar=1,format=yuv420p")
        elif iw / ih >= 0.8:
            scaled_w = iw * bh / ih
            amp = max(0.0, min((scaled_w - bw) / 2, 260.0))
            direction = 1 if idx % 2 == 0 else -1
            vf = (f"scale=-2:{bh},crop={bw}:{bh}:x='(iw-ow)/2+{direction * amp:.1f}*(2*t/{length:.3f}-1)':y=0,"
                  f"scale={W}:{H},setsar=1,format=yuv420p")
        else:
            vf = (f"scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh},"
                  f"{zoom},setsar=1,format=yuv420p")
    elif sc.clip:
        src = ["-stream_loop", "-1", "-i", str(sc.clip)]
        from game_trailers import CLIP_FOCUS
        face = CLIP_FOCUS.get(str(sc.clip))
        if face and face[2] >= 0.05:
            # Fragman klibi: dikey kırpmayı karakterin yüzüne ortala
            vf = (f"fps={FPS},scale=-2:{bh},crop={bw}:{bh}:x='clip({face[0]:.4f}*iw-ow/2,0,iw-ow)':y=0,"
                  f"{zoom},setsar=1,format=yuv420p")
        else:
            vf = (f"fps={FPS},scale={bw}:{bh}:force_original_aspect_ratio=increase,"
                  f"crop={bw}:{bh},{zoom},setsar=1,format=yuv420p")
    else:
        color = FALLBACK_COLORS[idx % len(FALLBACK_COLORS)]
        src = ["-f", "lavfi", "-i", f"color=c={color}:s={bw}x{bh}:r={FPS}"]
        vf = f"{zoom},setsar=1,format=yuv420p"
    run(["ffmpeg", "-y", *src, "-vf", vf, "-frames:v", str(frames), "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out)])
    return out


AUDIO_EXT = {".mp3", ".wav", ".m4a", ".ogg"}
# Video türüne göre müzik klasörü: assets/music/<ruh hali>/ (boşsa assets/music/ kökü)
MOOD_BY_FORMAT = {"lore": "lore", "gizem": "gizem", "neden": "genel", "ne-olurdu": "genel",
                  "what-if": "genel", "dark-history": "gizem", "psychology": "genel", "business": "genel",
                  "news": "news"}


def pick_music_tracks(episode: dict) -> list[Path]:
    if not episode.get("music", True):
        return []
    music_dir = ROOT / "assets" / "music"
    mood = episode.get("music_mood") or MOOD_BY_FORMAT.get(episode.get("format", ""), "genel")
    for folder in (music_dir / mood, music_dir):
        if folder.exists():
            tracks = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXT)
            if tracks:
                return tracks
    return []


# Kanal/görünüm profilleri. Bölümde "style" alanıyla seçilir (varsayılan: birdsvault).
STYLES = {
    "birdsvault": {"captions": "group", "title_card": False, "cut_every": 0.0, "punch": False, "sfx": False},
    # Vurgu yakınlaşması ve onunla gelen "pop" sesi kullanıcı isteğiyle kapatıldı (4 Eki)
    "global": {"captions": "box", "title_card": True, "cut_every": 2.2, "punch": False, "sfx": True},
    # Oyun karakteri 'edit' havası: sıcak renk, sinema bantları, harf harf altyazı, sakin tempo
    # Altyazı: klasik (beyaz satır, o an söylenen kelime sarı). Harf harf açılan "reveal"
    # animasyonu beğenilmedi; istenirse bölümde caption_style: "reveal" ile hâlâ seçilebilir.
    "cinematic": {"captions": "group", "title_card": False, "cut_every": 0.0, "punch": False, "sfx": False,
                  "grade": True, "bars": True},
}
TITLE_CARD_S = 1.3      # açılış kartı süresi (anlatım bu kadar gecikmeli başlar)
CINE_BAR = 170          # sinematik stilde üst/alt siyah bant yüksekliği (px)
PUNCH = 0.10            # vurguda ani yakınlaşma miktarı
SFX_VOLUME = 0.6


def punch_times(words: list[Word], episode: dict, min_gap: float = 2.0) -> list[float]:
    """Ani yakınlaşma anları: rakam içeren kelimeler + bölümün 'emphasis' listesi."""
    emph = {e.lower() for e in episode.get("emphasis", [])}
    out: list[float] = []
    for w in words:
        t = w.text.strip().lower().strip(".,!?\"'")
        if (any(ch.isdigit() for ch in t) or t in emph) and (not out or w.start - out[-1] >= min_gap):
            out.append(w.start)
    return out[:12]


def punch_filter(times: list[float]) -> str:
    """Belirtilen anlarda 80 ms'de yakınlaşıp 420 ms'de geri dönen ölçek ifadesi."""
    if not times:
        return ""
    terms = "+".join(f"between(t,{t:.2f},{t + 0.08:.2f})*(t-{t:.2f})/0.08"
                     f"+between(t,{t + 0.08:.2f},{t + 0.5:.2f})*(1-(t-{t + 0.08:.2f})/0.42)" for t in times)
    z = f"(1+{PUNCH}*({terms}))"
    return f"scale=w='2*trunc({W // 2}*{z})':h='2*trunc({H // 2}*{z})':eval=frame,crop={W}:{H}"


def pick_voice(episode: dict) -> tuple[str, str]:
    """Bölümün sesi ve hızı: açıkça yazılmışsa o; değilse Azure varsa formata göre çok dilli ses."""
    if episode.get("voice"):
        return episode["voice"], episode.get("rate", DEFAULT_RATE)
    if os.environ.get("AZURE_SPEECH_KEY", "").strip():
        voice, rate = VOICE_BY_FORMAT.get(episode.get("format", ""), DEFAULT_AZURE_VOICE)
        return voice, episode.get("rate", rate)
    return DEFAULT_VOICE, episode.get("rate", DEFAULT_RATE)


def render(episode: dict, out_dir: Path, offline: bool = False) -> Path:
    slug = episode["_slug"]
    work = out_dir / f"{slug}_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    global CAPTION_LANG
    language = episode.get("language", "tr")
    CAPTION_LANG = language
    scenes = [Scene(text=s["text"].strip(), search=s.get("search", "").strip(),
                    image_query=(s.get("image") if isinstance(s.get("image"), str) else None),
                    image_page=s.get("image_page"), trailer=bool(s.get("trailer")))
              for s in episode["scenes"] if s.get("text", "").strip()]
    if not scenes:
        raise ValueError("Bölümde hiç sahne yok.")

    style = STYLES.get(episode.get("style", "birdsvault"), STYLES["birdsvault"])
    extra = {} if episode.get("voice") else VOICE_EXTRA.get(episode.get("format", ""), {})
    narration, words, total = synthesize(
        scenes, *pick_voice(episode), work, offline,
        pitch=episode.get("pitch", extra.get("pitch", "+0%")), language=language,
        speak_style=episode.get("speak_style", extra.get("style", "")),
        style_degree=float(extra.get("style_degree", 1.0)))
    # Açılış başlık kartı: her şey kart süresi kadar ileri kayar, anlatım kartın ardından başlar
    title_s = TITLE_CARD_S if style["title_card"] else 0.0
    if title_s:
        for w in words:
            w.start += title_s
            w.end += title_s
        scenes[0].duration += title_s
        for sc in scenes[1:]:
            sc.start += title_s
        total += title_s
    if style["cut_every"]:
        for sc in scenes:
            sc.n_shots = max(1, round(sc.duration / style["cut_every"]))
    if total > 59:
        log(f"UYARI: video {total:.1f} sn; Shorts için 60 saniyenin altı önerilir.")
    wiki = episode.get("wiki") or {}
    trailer = episode.get("trailer") or {}
    if trailer.get("steam_appid") and any(sc.trailer for sc in scenes) and not offline:
        from game_trailers import assign as assign_trailers
        n = assign_trailers(scenes, int(trailer["steam_appid"]), work, seed=slug)
        log(f"Fragman klibi: {n}/{sum(sc.trailer for sc in scenes)} sahne")
    # Fragmandan temiz klip çıkmayan sahne stoka değil, karakterin wiki görseline düşsün
    for sc in scenes:
        if sc.trailer and sc.clip is None and sc.image_query is None and wiki.get("page"):
            sc.image_query = episode.get("subject") or wiki["page"]
    if wiki.get("site") and wiki.get("page") and any(sc.image_query is not None for sc in scenes) and not offline:
        from wiki_images import assign, list_images
        pools: dict[str, list[dict]] = {}
        for page in dict.fromkeys([wiki["page"]] + [sc.image_page for sc in scenes if sc.image_page]):
            try:
                pools[page] = list_images(wiki["site"], page)
            except Exception as e:
                log(f"Wiki görselleri alınamadı: {page} ({type(e).__name__})")
                pools[page] = []
        assign(scenes, pools, wiki["page"], episode.get("subject", wiki["page"]), work,
               avoid=wiki.get("avoid"))
    for sc in scenes:  # görseli bulunamayan sahneler stoka düşer
        if sc.image is None:
            sc.image_query = None
    fetch_clips([sc for sc in scenes if sc.image is None and sc.clip is None], work, offline,
                episode.get("subject", ""))

    segs = []
    cuts: list[float] = []  # kesme anları (ses efekti için)
    if style["cut_every"]:
        # Hızlı kesme: her sahne ~2 sn'lik çekimlere bölünür, çekimler keskin kesmeyle birleşir
        shot_paths = []
        for i, sc in enumerate(scenes):
            sources = ([("image", p) for p in ([sc.image] if sc.image else []) + sc.extra_images]
                       or [("clip", p) for p in ([sc.clip] if sc.clip else []) + sc.extra_clips])
            f0, f1 = round(sc.start * FPS), round((sc.start + sc.duration) * FPS)
            bounds = [f0 + round((f1 - f0) * j / sc.n_shots) for j in range(sc.n_shots + 1)]
            for j in range(sc.n_shots):
                kind, path = sources[j % len(sources)] if sources else ("color", None)
                shot = Scene(text="", search="", image=path if kind == "image" else None,
                             clip=path if kind == "clip" else None)
                shot_paths.append(render_scene_video(shot, i * 10 + j, (bounds[j + 1] - bounds[j]) / FPS, work))
                if bounds[j] > 0:
                    cuts.append(bounds[j] / FPS)
        (work / "shots.txt").write_text("".join(f"file '{p.name}'\n" for p in shot_paths))
        cat = work / "video_cat.mp4"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "shots.txt"), "-c", "copy", str(cat)])
        segs = [cat]
    else:
        # Son sahne dışındaki parçalar geçiş süresi kadar uzun üretilir, böylece
        # xfade sonrası toplam süre sesle birebir aynı kalır.
        for i, sc in enumerate(scenes):
            length = sc.duration + (XFADE if i < len(scenes) - 1 else 0.0)
            segs.append(render_scene_video(sc, i, length, work))

    ass = work / "subs.ass"
    build_ass(words, total, episode.get("font", "DejaVu Sans"), ass,
              episode.get("caption_style", style["captions"]),
              hook=hook_text(episode) if episode.get("show_hook", False) else "",
              title=(hook_text(episode) or EMOJI_RE.sub("", episode.get("title", "")).strip()) if title_s else "",
              title_until=title_s)

    # Görüntü zinciri: seg0 x seg1 x ... -> (vurgu yakınlaşması) -> altyazı
    vchain, last = [], "0:v"
    punches = punch_times(words, episode) if style["punch"] else []
    if punches and len(segs) == 1:
        vchain.append(f"[0:v]{punch_filter(punches)}[pz]")
        last = "pz"
        log(f"Vurgu yakınlaşması: {len(punches)} an")
    for k in range(1, len(segs)):
        label = f"x{k}"
        vchain.append(f"[{last}][{k}:v]xfade=transition=fade:duration={XFADE}:offset={scenes[k].start:.3f}[{label}]")
        last = label
    if style.get("grade") or style.get("bars"):
        fx = []
        if style.get("grade"):
            # Sıcak turuncu-kahve ton, hafif soluk renk, koyu gölgeler, kenar karartması
            fx.append("eq=contrast=1.10:saturation=0.82:brightness=-0.03,"
                      "lutrgb=r='clip(val*1.07+3\\,0\\,255)':b='clip(val*0.88\\,0\\,255)',"
                      "vignette=angle=PI/4.5")
        if style.get("bars"):
            fx.append(f"drawbox=x=0:y=0:w=iw:h={CINE_BAR}:color=black:t=fill,"
                      f"drawbox=x=0:y=ih-{CINE_BAR}:w=iw:h={CINE_BAR}:color=black:t=fill")
        vchain.append(f"[{last}]{','.join(fx)}[gr]")
        last = "gr"
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
    tracks = pick_music_tracks(episode)
    inputs = []
    for p in segs:
        inputs += ["-i", str(p)]
    inputs += ["-i", str(narration)]
    delay = f"adelay={int(title_s * 1000)}:all=1," if title_s else ""
    sfx_label, sfx_path = "", None
    if style["sfx"]:
        from sfx import build_sfx_track
        # Whoosh yalnızca sahne değişimlerinde (ara kesmelerde değil) ve en az 4 sn arayla
        whooshes: list[float] = []
        for sc in scenes[1:]:
            if not whooshes or sc.start - whooshes[-1] >= 4.0:
                whooshes.append(sc.start)
        if title_s:
            whooshes = [title_s] + [t for t in whooshes if t - title_s >= 4.0]
        events = ([(0.0, "impact")] if title_s else []) + [(t, "whoosh") for t in whooshes] \
            + [(t, "pop") for t in punches]
        sfx_path = work / "sfx.wav"
        build_sfx_track(events, total, sfx_path)
        sfx_idx = n + 1 + (1 if tracks else 0)
        sfx_label = f"[{sfx_idx}:a]aresample=44100,volume={SFX_VOLUME}[fx];"
        log(f"Ses efektleri: {len(events)} olay")
    if tracks:
        track = random.choice(tracks)
        # Parçanın hep aynı yerinden başlamasın
        start = random.uniform(0, max(0.0, probe_duration(track) - total - 1))
        inputs += ["-ss", f"{start:.2f}", "-stream_loop", "-1", "-i", str(track)]
        log(f"Müzik: {track.name} ({start:.0f}. sn'den)")
        # Müzik kısık çalar; konuşma sırasında ayrıca otomatik kısılır (sidechain ducking)
        # Önce anlatım normalize edilir, müzik ona göre sabit seviyede eklenir (sonradan
        # loudnorm uygulansaydı sessiz anlarda müziği yükseltirdi).
        achain = (f"[{n}:a]aresample=44100,loudnorm=I=-14:TP=-2:LRA=11,aresample=44100,{delay}apad,asplit=2[nar][key];"
                  f"[{n + 1}:a]aresample=44100,volume={MUSIC_VOLUME},afade=t=in:d=0.6,"
                  f"afade=t=out:st={max(0.0, total - 1.5):.2f}:d=1.5[mraw];"
                  f"[mraw][key]sidechaincompress=threshold=0.02:ratio=8:attack=30:release=500:mix=0.65[m];"
                  + sfx_label +
                  f"[nar][m]{'[fx]' if sfx_label else ''}amix=inputs={3 if sfx_label else 2}:duration=first:"
                  f"dropout_transition=0:normalize=0,alimiter=limit=0.9[a]")
    elif sfx_label:
        achain = (f"[{n}:a]aresample=44100,loudnorm=I=-14:TP=-2:LRA=11,aresample=44100,{delay}apad[nar];"
                  + sfx_label + "[nar][fx]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
                  "alimiter=limit=0.9[a]")
    else:
        achain = f"[{n}:a]{delay}apad,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    if sfx_path:
        inputs += ["-i", str(sfx_path)]

    final = out_dir / f"{slug}.mp4"
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(vchain + [achain]),
         "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", str(final)])
    log(f"Hazır: {final} ({total:.1f} sn)")
    return final


def load_episode(path: Path) -> dict:
    from channels import CHANNELS, DEFAULT_CHANNEL, channel_of, episode_key

    ep = json.loads(path.read_text(encoding="utf-8"))
    ch = channel_of(path, ROOT / "episodes")
    ep["_channel"] = ch
    for k, v in CHANNELS[ch]["defaults"].items():   # kanalın varsayılan dil/stil/formatı
        ep.setdefault(k, v)
    ep["_key"] = episode_key(ch, path.stem)
    ep["_slug"] = path.stem if ch == DEFAULT_CHANNEL else f"{ch}__{path.stem}"
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
