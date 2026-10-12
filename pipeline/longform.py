"""Uzun (16:9) gizem belgeseli üretici — "vaka dosyası" görünümü (Global kanal, episodes/longform/).

Bölüm yapısı:
  {
    "title": "...", "description": "...", "tags": [...], "publish_at": "...",
    "case_no": 7, "case_title": "The Dyatlov Pass Incident", "case_meta": "Ural Mountains · February 1959",
    "status": "UNSOLVED",                       # kapanış damgası (UNSOLVED / DISPUTED / CLOSED)
    "wiki": {"site": "en.wikipedia.org", "page": "Dyatlov Pass incident"},
    "thumbnail": {"text": "THEY CUT THE TENT FROM INSIDE", "highlight": "INSIDE", "image": "tent"},
    "chapters": [
      {"title": "The Last Photograph",           # 1. bölüm = soğuk açılış (bölüm kartı yok)
       "scenes": [{"text": "...", "image": "tent", "card": "Kholat Syakhl · 2 February 1959"},
                  {"text": "...", "search": "snowy mountain night"}]},
      {"title": "Nine Hikers", "scenes": [...]}, ...
    ]
  }

Akış: soğuk açılış → vaka kartı (CASE FILE #07) → BÖLÜM kartı + bölüm ... → kapanış damgası.
Her bölüm ayrı seslendirilir; görüntüler Wikipedia (kamu malı/CC) arşiv fotoğrafları ve yatay stok videodur.
"""
from __future__ import annotations

import random
import re
import subprocess
import wave
from pathlib import Path

import numpy as np

import make_video as mv
from make_video import ROOT, Scene, Word, log, probe_duration, run

LW, LH, FPS = 1920, 1080, 30
CW, CH = 2112, 1188            # kompozit görsel %10 büyük: kaydırma/yakınlaşma payı
XF = 0.6                       # sahne geçişi (sn)
DOC_VOICE = ("en-US-DavisNeural", "-8%", "-4%")     # kullanıcı seçimi (13 Eki): Davis, derin ve sakin
SENT_PAUSE_MS = 450            # belgesel: cümle arası daha uzun nefes
FONT_TYPE = "Special Elite"    # daktilo yazısı (Apache 2.0)
FONT_SUB = "Poppins Medium"
INK = "&H00D6E6ED&"            # kirli beyaz (#EDE6D6, ASS BGR)
AMBER = "&H0040B0E8&"          # kehribar (#E8B040)
RED = "&H002D28C8&"            # damga kırmızısı (#C8282D)
CARD_CASE_S, CARD_CHAPTER_S, CARD_END_S = 6.0, 3.6, 7.5
MUSIC_VOL = 0.15
GRADE = ("eq=contrast=1.07:saturation=0.70:brightness=-0.02,"
         "colorbalance=rs=-0.04:gs=-0.01:bs=0.05:rh=0.05:gh=0.01:bh=-0.04,"
         "vignette=angle=PI/5,noise=alls=6:allf=t")
ENC_V = ["-c:v", "libx264", "-preset", "faster", "-crf", "21", "-pix_fmt", "yuv420p", "-r", str(FPS)]
ENC_A = ["-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2"]


# ------------------------------------------------------------------ görseller
def _imread(path: Path, work: Path):
    import cv2

    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:  # webp/gif/tif vb.: ffmpeg ile png'ye çevir
        png = work / f"{path.stem}_conv.png"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-frames:v", "1", str(png)],
                       capture_output=True)
        img = cv2.imread(str(png), cv2.IMREAD_COLOR)
    return img


def _cover(img, w: int, h: int, cx: float = 0.5, cy: float = 0.5):
    import cv2

    ih, iw = img.shape[:2]
    s = max(w / iw, h / ih)
    r = cv2.resize(img, (max(w, round(iw * s)), max(h, round(ih * s))), interpolation=cv2.INTER_LANCZOS4)
    rh, rw = r.shape[:2]
    x = int(min(max(cx * rw - w / 2, 0), rw - w))
    y = int(min(max(cy * rh - h / 2, 0), rh - h))
    return r[y:y + h, x:x + w]


def compose_still(src: Path, dst: Path, idx: int, work: Path) -> bool:
    """Arşiv görselinden 16:9 kompozit üretir.

    Geniş ve net görsel: tam ekran (yüz varsa ona ortalı). Dikey/küçük görsel: bulanık arka plan
    üstünde, kenarlıklı ve hafif eğik "dosyaya iliştirilmiş fotoğraf".
    """
    import cv2

    from faces import focus

    img = _imread(src, work)
    if img is None:
        return False
    ih, iw = img.shape[:2]
    face = focus(src)
    fx, fy = (face[0], face[1]) if face and face[2] >= 0.05 else (0.5, 0.45)
    if iw / ih >= 1.55 and iw >= 1400:
        out = _cover(img, CW, CH, fx, fy)
    else:
        bg = _cover(img, CW, CH, fx, fy)
        bg = cv2.GaussianBlur(bg, (0, 0), 30)
        bg = (bg.astype(np.float32) * 0.30).astype(np.uint8)
        box_w, box_h = int(CW * 0.66), int(CH * 0.78)
        s = min(box_w / iw, box_h / ih, 2.6)
        fg = cv2.resize(img, (max(1, round(iw * s)), max(1, round(ih * s))), interpolation=cv2.INTER_LANCZOS4)
        b = 14
        fg = cv2.copyMakeBorder(fg, b, b, b, b, cv2.BORDER_CONSTANT, value=(214, 230, 237))
        fh, fw = fg.shape[:2]
        angle = [-1.4, 1.1, -0.8, 1.3][idx % 4]
        pad = int(0.05 * max(fw, fh)) + 40
        canvas = np.zeros((fh + 2 * pad, fw + 2 * pad, 3), np.uint8)
        alpha = np.zeros((fh + 2 * pad, fw + 2 * pad), np.float32)
        canvas[pad:pad + fh, pad:pad + fw] = fg
        alpha[pad:pad + fh, pad:pad + fw] = 1.0
        m = cv2.getRotationMatrix2D((canvas.shape[1] / 2, canvas.shape[0] / 2), angle, 1.0)
        canvas = cv2.warpAffine(canvas, m, (canvas.shape[1], canvas.shape[0]), flags=cv2.INTER_LINEAR)
        alpha = cv2.warpAffine(alpha, m, (alpha.shape[1], alpha.shape[0]), flags=cv2.INTER_LINEAR)
        shadow = cv2.GaussianBlur(alpha, (0, 0), 18) * 0.75
        ox = (CW - canvas.shape[1]) // 2
        oy = (CH - canvas.shape[0]) // 2
        out = bg.astype(np.float32)
        x0, y0 = max(ox, 0), max(oy, 0)
        x1, y1 = min(ox + canvas.shape[1], CW), min(oy + canvas.shape[0], CH)
        cx0, cy0 = x0 - ox, y0 - oy
        reg = out[y0:y1, x0:x1]
        sh = shadow[cy0 + 14:cy0 + 14 + (y1 - y0), cx0 + 10:cx0 + 10 + (x1 - x0)]
        if sh.shape[:2] == reg.shape[:2]:
            reg *= (1 - sh[..., None])
        a = alpha[cy0:cy0 + (y1 - y0), cx0:cx0 + (x1 - x0)][..., None]
        reg[:] = reg * (1 - a) + canvas[cy0:cy0 + (y1 - y0), cx0:cx0 + (x1 - x0)].astype(np.float32) * a
        out = np.clip(out, 0, 255).astype(np.uint8)
    cv2.imwrite(str(dst), out)
    return True


def texture_bg(dst: Path, base: Path | None, work: Path) -> Path:
    """Kart arka planı: ana görselin koyu, bulanık hali ya da koyu kâğıt dokusu."""
    import cv2

    rng = np.random.default_rng(3)
    img = _imread(base, work) if base else None
    if img is not None:
        bg = _cover(img, LW, LH)
        bg = cv2.GaussianBlur(bg, (0, 0), 22)
        bg = (bg.astype(np.float32) * 0.18)
    else:
        bg = np.full((LH, LW, 3), (14, 17, 20), np.float32)
    bg += rng.normal(0, 6, (LH, LW, 1)).astype(np.float32)
    yy, xx = np.mgrid[0:LH, 0:LW]
    d = np.sqrt(((xx - LW / 2) / (LW / 2)) ** 2 + ((yy - LH / 2) / (LH / 2)) ** 2)
    bg *= np.clip(1.15 - 0.55 * d, 0.35, 1.0)[..., None]
    cv2.imwrite(str(dst), np.clip(bg, 0, 255).astype(np.uint8))
    return dst


# ------------------------------------------------------------------ sahne parçaları
def render_still_segment(png: Path, length: float, idx: int, out: Path) -> Path:
    """Durağan görsele yavaş hareket: yakınlaşma / uzaklaşma / sağa / sola kaydırma (sırayla).

    Görsel bir kez çözülür (zoompan d=kare sayısı ya da loop süzgeci); ara dosya hızlı kodlanır.
    """
    frames = max(1, round(length * FPS))
    kind = idx % 4
    if kind in (0, 2):
        z = (f"1+0.07*on/{frames}" if kind == 0 else f"1.07-0.07*on/{frames}")
        vf = (f"scale=2880:-2,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:"
              f"s={LW}x{LH}:fps={FPS},setsar=1,format=yuv420p")
    else:
        x = (f"(iw-ow)/2+(iw-ow)/2*(2*t/{length:.3f}-1)" if kind == 1
             else f"(iw-ow)/2-(iw-ow)/2*(2*t/{length:.3f}-1)")
        vf = (f"loop=loop={frames - 1}:size=1:start=0,setpts=N/{FPS}/TB,"
              f"crop={LW}:{LH}:x='{x}':y='(ih-oh)/2',setsar=1,format=yuv420p")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(png), "-vf", vf, "-frames:v", str(frames), "-r", str(FPS),
         "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "15", str(out)])
    return out


def render_clip_segment(clip: Path, length: float, out: Path) -> Path:
    frames = max(1, round(length * FPS))
    vf = (f"fps={FPS},scale={LW}:{LH}:force_original_aspect_ratio=increase,crop={LW}:{LH},"
          f"setsar=1,format=yuv420p")
    run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", str(clip), "-vf", vf,
         "-frames:v", str(frames), "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "15", str(out)])
    return out


# ------------------------------------------------------------------ ses efektleri
SR = 44100


def _write_wav(x: np.ndarray, path: Path) -> None:
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.stack([pcm, pcm], axis=1).tobytes())


def typewriter_track(times: list[float], dur: float, path: Path, stamp_at: float | None = None) -> Path:
    """Daktilo tuş sesleri (ve istenirse damga vuruşu); tamamen kodla sentezlenir."""
    rng = np.random.default_rng(5)
    x = np.zeros(int(dur * SR) + SR)
    for t in times:
        n = int(0.018 * SR)
        tt = np.arange(n) / SR
        click = np.diff(rng.standard_normal(n + 1)) * np.exp(-tt * 380)          # tiz tık
        click += 0.6 * np.sin(2 * np.pi * rng.uniform(140, 190) * tt) * np.exp(-tt * 160)  # gövde
        s = int(t * SR)
        x[s:s + n] += click * rng.uniform(0.25, 0.45)
    if stamp_at is not None:
        n = int(0.5 * SR)
        tt = np.arange(n) / SR
        thud = (np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 9) + 0.5 * rng.standard_normal(n) * np.exp(-tt * 40))
        s = int(stamp_at * SR)
        x[s:s + n] += 0.8 * thud
    _write_wav(x[: int(dur * SR)], path)
    return path


# ------------------------------------------------------------------ altyazı / kartlar (ASS)
def _ass_header(w: int, h: int) -> str:
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{FONT_SUB},52,&H00FFFFFF,&H00FFFFFF,&H00101010,&H90000000,0,0,0,0,100,100,0,0,1,2.6,1.2,2,200,200,62,1
Style: Card,{FONT_TYPE},44,{INK},{INK},&H00000000,&H78000000,0,0,0,0,100,100,1,0,3,14,0,7,0,0,0,1
Style: Amber,{FONT_TYPE},50,{AMBER},{AMBER},&H00000000,&H00000000,0,0,0,0,100,100,4,0,1,0,0,5,0,0,0,1
Style: Big,{FONT_TYPE},98,{INK},{INK},&H00000000,&H80000000,0,0,0,0,100,100,1,0,1,0,3,5,0,0,0,1
Style: Meta,{FONT_TYPE},40,&H00A8B4BA&,&H00A8B4BA&,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,0,0,5,0,0,0,1
Style: Stamp,{FONT_TYPE},150,{RED},{RED},{RED},&H00000000,0,0,0,0,100,100,6,0,1,5,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ev(start: float, end: float, style: str, text: str, layer: int = 0) -> str:
    return f"Dialogue: {layer},{mv.ts(start)},{mv.ts(max(end, start + 0.05))},{style},,0,0,0,,{text}"


def _typed(start: float, end: float, style: str, text: str, pos: str, cps: float = 0.05,
           fade_out: int = 300) -> tuple[list[str], list[float]]:
    """Daktilo gibi harf harf beliren yazı. (olaylar, tuş zamanları) döner."""
    evs, keys = [], []
    n = len(text)
    for i in range(1, n + 1):
        t0 = start + (i - 1) * cps
        t1 = start + i * cps if i < n else end
        tag = pos + (f"\\fad(0,{fade_out})" if i == n and fade_out else "")
        evs.append(_ev(t0, t1, style, "{" + tag + "}" + mv.ass_escape(text[:i])))
        if text[i - 1].strip():
            keys.append(t0)
    return evs, keys


def _subtitle_events(words: list[Word], total: float) -> list[str]:
    """Alt orta, tek satır altyazı: cümle parçaları (en fazla ~7 kelime / 44 harf)."""
    evs, cur = [], []

    def flush(next_start: float | None) -> None:
        if not cur:
            return
        text = " ".join(w.text for w in cur).strip()
        end = min(cur[-1].end + 0.35, next_start if next_start else total)
        evs.append(_ev(cur[0].start, end, "Sub", mv.ass_escape(text)))
        cur.clear()

    for k, w in enumerate(words):
        cur.append(w)
        length = len(" ".join(x.text for x in cur))
        nxt = words[k + 1].start if k + 1 < len(words) else None
        gap = (nxt - w.end) if nxt is not None else 9
        if getattr(w, "brk", False) or len(cur) >= 7 or length >= 44 or gap > 0.6:
            flush(nxt)
    flush(None)
    return evs


# ------------------------------------------------------------------ parçalar
def _chapter_video(scenes: list[Scene], raws: list[dict], words: list[Word], total: float, narration: Path,
                   work: Path, out: Path, offset: int) -> Path:
    segs = []
    for i, sc in enumerate(scenes):
        length = sc.duration + (XF if i < len(scenes) - 1 else 0.0)
        seg = work / f"seg_{offset + i:03d}.mp4"
        if sc.image is not None:
            png = work / f"still_{offset + i:03d}.png"
            if compose_still(sc.image, png, offset + i, work):
                segs.append(render_still_segment(png, length, offset + i, seg))
                continue
        if sc.clip is not None:
            segs.append(render_clip_segment(sc.clip, length, seg))
            continue
        png = texture_bg(work / f"tex_{offset + i:03d}.png", None, work)
        segs.append(render_still_segment(png, length, offset + i, seg))

    ass = work / "chapter.ass"
    evs = _subtitle_events(words, total)
    keys: list[float] = []
    for sc, raw in zip(scenes, raws):
        card = (raw.get("card") or "").strip()
        if not card:
            continue
        t0, t1 = sc.start + 0.3, min(sc.start + sc.duration - 0.2, sc.start + 6.0)
        bar = (f"{{\\an7\\pos(108,104)\\p1\\c{AMBER}\\bord0\\shad0\\fad(150,300)}}"
               "m 0 0 l 9 0 9 58 0 58{\\p0}")
        evs.append(_ev(t0, t1, "Card", bar, layer=2))
        e, k = _typed(t0 + 0.1, t1, "Card", card, "\\an7\\pos(132,100)", cps=0.045)
        evs += e
        keys += k
    ass.write_text(_ass_header(LW, LH) + "\n".join(evs) + "\n", encoding="utf-8")

    vchain, last = [], "0:v"
    for k in range(1, len(segs)):
        vchain.append(f"[{last}][{k}:v]xfade=transition=fade:duration={XF}:offset={scenes[k].start:.3f}[x{k}]")
        last = f"x{k}"
    fonts = (ROOT / "assets" / "fonts").as_posix()
    vchain.append(f"[{last}]{GRADE},subtitles={ass.as_posix()}:fontsdir={fonts}[v]")
    n = len(segs)
    inputs: list[str] = []
    for p in segs:
        inputs += ["-i", str(p)]
    inputs += ["-i", str(narration)]
    achain = f"[{n}:a]aresample=44100,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100,apad[nar]"
    if keys:
        clicks = typewriter_track([t - 0.0 for t in keys], total, work / "keys.wav")
        inputs += ["-i", str(clicks)]
        achain += f";[{n + 1}:a]volume=0.35[k];[nar][k]amix=inputs=2:duration=first:normalize=0[a]"
    else:
        achain += ";[nar]anull[a]"
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(vchain + [achain]),
         "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", *ENC_V, *ENC_A, str(out)])
    return out


def _card_video(bg: Path, dur: float, events: list[str], keys: list[float], out: Path, work: Path,
                stamp_at: float | None = None) -> Path:
    ass = work / f"{out.stem}.ass"
    ass.write_text(_ass_header(LW, LH) + "\n".join(events) + "\n", encoding="utf-8")
    clicks = typewriter_track(keys, dur, work / f"{out.stem}.wav", stamp_at=stamp_at)
    frames = round(dur * FPS)
    fonts = (ROOT / "assets" / "fonts").as_posix()
    vf = (f"scale=2304:-2,zoompan=z='1+0.03*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:"
          f"s={LW}x{LH}:fps={FPS},noise=alls=6:allf=t,subtitles={ass.as_posix()}:fontsdir={fonts},"
          f"fade=t=in:d=0.35,fade=t=out:st={dur - 0.35:.2f}:d=0.35,format=yuv420p")
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", str(bg), "-i", str(clicks),
         "-vf", vf, "-af", "volume=0.6", "-frames:v", str(frames), "-t", f"{dur:.3f}", *ENC_V, *ENC_A, str(out)])
    return out


def case_card(ep: dict, bg: Path, work: Path) -> Path:
    no = f"CASE FILE #{int(ep.get('case_no', 1)):02d}"
    title = (ep.get("case_title") or ep["title"]).upper()
    meta = ep.get("case_meta", "")
    evs, keys = _typed(0.4, CARD_CASE_S, "Amber", no, "\\an5\\pos(960,370)", cps=0.06, fade_out=0)
    e, k = _typed(1.3, CARD_CASE_S, "Big", title, "\\an5\\pos(960,520)", cps=0.055, fade_out=0)
    evs += e
    keys += k
    if meta:
        evs.append(_ev(1.3 + len(title) * 0.055 + 0.3, CARD_CASE_S, "Meta",
                       "{\\an5\\pos(960,650)\\fad(400,0)}" + mv.ass_escape(meta)))
    line = "{\\an7\\pos(700,590)\\p1\\c" + AMBER + "\\bord0\\shad0\\fad(300,0)}m 0 0 l 520 0 520 3 0 3{\\p0}"
    evs.append(_ev(1.0, CARD_CASE_S, "Amber", line))
    return _card_video(bg, CARD_CASE_S, evs, keys, work / "card_case.mp4", work)


def chapter_card(n: int, title: str, bg: Path, work: Path) -> Path:
    evs, keys = _typed(0.3, CARD_CHAPTER_S, "Amber", f"CHAPTER {n}", "\\an5\\pos(960,450)", cps=0.06, fade_out=0)
    e, k = _typed(1.0, CARD_CHAPTER_S, "Big", title.upper(), "\\an5\\pos(960,575)", cps=0.05, fade_out=0)
    return _card_video(bg, CARD_CHAPTER_S, evs + e, keys + k, work / f"card_ch{n:02d}.mp4", work)


def end_card(ep: dict, bg: Path, work: Path) -> Path:
    status = (ep.get("status") or "UNSOLVED").upper()
    evs, keys = _typed(0.4, CARD_END_S, "Meta", "CASE STATUS", "\\an5\\pos(960,330)", cps=0.07, fade_out=0)
    stamp_t = 1.6
    evs.append(_ev(stamp_t, CARD_END_S, "Stamp",
                   "{\\an5\\pos(960,520)\\frz-8\\alpha&H20&\\fscx135\\fscy135\\t(0,120,\\fscx100\\fscy100)}"
                   + mv.ass_escape(status)))
    line = ep.get("end_line") or "New case files every Monday, Wednesday and Friday."
    evs.append(_ev(3.0, CARD_END_S, "Meta", "{\\an5\\pos(960,760)\\fad(500,0)}" + mv.ass_escape(line)))
    return _card_video(bg, CARD_END_S, evs, keys, work / "card_end.mp4", work, stamp_at=stamp_t)


# ------------------------------------------------------------------ kapak görseli
def make_thumbnail(ep: dict, image: Path | None, work: Path) -> Path | None:
    import cv2

    th = ep.get("thumbnail") or {}
    text = (th.get("text") or ep.get("case_title") or ep["title"]).upper()
    words = text.split()
    if len(words) > 3:
        mid = (len(words) + 1) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    else:
        lines = [text]
    hl = (th.get("highlight") or "").upper()
    W_, H_ = 1280, 720
    if image is not None and (img := _imread(image, work)) is not None:
        from faces import focus

        f = focus(image)
        cx = min(0.75, max(0.55, f[0])) if f and f[2] >= 0.05 else 0.62
        bg = _cover(img, W_, H_, cx, f[1] if f else 0.45).astype(np.float32)
    else:
        bg = np.full((H_, W_, 3), (20, 22, 26), np.float32)
    # Sol tarafı karart (yazı okunsun), hafif soğuk ton
    grad = np.clip((np.arange(W_) / W_ - 0.62) / 0.38, 0, 1) * 0.75 + 0.25
    bg *= grad[None, :, None]
    bg[..., 0] *= 1.05
    bg[..., 2] *= 0.95
    png = work / "thumb_bg.png"
    cv2.imwrite(str(png), np.clip(bg, 0, 255).astype(np.uint8))

    def mark(s: str) -> str:
        out = []
        for wd in s.split():
            esc = mv.ass_escape(wd)
            out.append("{\\c&H0040D8FF&}" + esc + "{\\c&HFFFFFF&}" if hl and wd.strip(".,!?") == hl else esc)
        return " ".join(out)

    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W_}
PlayResY: {H_}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: T,Anton,{112 if len(lines) == 2 else 128},&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,1,0,1,6,4,4,70,40,0,1
Style: N,{FONT_TYPE},36,{AMBER},{AMBER},&H00000000,&H00000000,0,0,0,0,100,100,3,0,1,2,0,7,0,0,0,1
Style: S,{FONT_TYPE},70,{RED},{RED},{RED},&H00000000,0,0,0,0,100,100,4,0,1,4,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    y0 = 400 if len(lines) == 2 else 470
    evs = [_ev(0, 5, "N", "{\\pos(70,56)}" + f"CASE FILE #{int(ep.get('case_no', 1)):02d}")]
    for k, ln in enumerate(lines):
        evs.append(_ev(0, 5, "T", "{\\an1\\pos(70," + str(y0 + k * 128) + ")}" + mark(ln)))
    evs.append(_ev(0, 5, "S", "{\\pos(1040,600)\\frz-12\\alpha&H18&}" + mv.ass_escape((ep.get("status") or "UNSOLVED").upper())))
    ass = work / "thumb.ass"
    ass.write_text(head + "\n".join(evs) + "\n", encoding="utf-8")
    out = work / "thumbnail.jpg"
    fonts = (ROOT / "assets" / "fonts").as_posix()
    run(["ffmpeg", "-y", "-v", "error", "-i", str(png), "-vf",
         f"subtitles={ass.as_posix()}:fontsdir={fonts}", "-frames:v", "1", "-q:v", "3", str(out)])
    return out


# ------------------------------------------------------------------ müzik
def _music_mix(joined: Path, total: float, out: Path, ep: dict) -> Path:
    folder = ROOT / "assets" / "music" / "belgesel"
    tracks = sorted(folder.glob("*.mp3")) if folder.exists() else []
    if not tracks or not ep.get("music", True):
        run(["ffmpeg", "-y", "-v", "error", "-i", str(joined), "-c", "copy", "-movflags", "+faststart", str(out)])
        return out
    rnd = random.Random(ep.get("_slug", ""))
    order = tracks[:]
    rnd.shuffle(order)
    need, seq, acc = total + 10, [], 0.0
    while acc < need:
        for t in order:
            seq.append(t)
            acc += probe_duration(t) - 6
            if acc >= need:
                break
    inputs = ["-i", str(joined)]
    for t in seq:
        inputs += ["-i", str(t)]
    chain, last = [], "1:a"
    for k in range(2, len(seq) + 1):
        chain.append(f"[{last}][{k}:a]acrossfade=d=6:c1=qsin:c2=qsin[m{k}]")
        last = f"m{k}"
    chain.append(f"[{last}]aresample=44100,volume={MUSIC_VOL},afade=t=in:d=3,"
                 f"afade=t=out:st={max(0.0, total - 5):.2f}:d=5[mraw]")
    chain.append("[0:a]asplit=2[nar][key]")
    chain.append("[mraw][key]sidechaincompress=threshold=0.03:ratio=5:attack=60:release=900:mix=0.55[m]")
    chain.append("[nar][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]")
    log(f"Müzik: {', '.join(t.name for t in seq)}")
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(chain), "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", *ENC_A, "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)])
    return out


# ------------------------------------------------------------------ ana akış
def render_long(episode: dict, out_dir: Path, offline: bool = False) -> Path:
    import shutil

    slug = episode.get("_slug", "longform")
    work = out_dir / f"{slug}_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    mv.CLIP_ORIENTATION = "landscape"
    mv.SENTENCE_PAUSE_MS = int(episode.get("sentence_pause_ms", SENT_PAUSE_MS))
    voice = episode.get("voice") or DOC_VOICE[0]
    rate = episode.get("rate") or DOC_VOICE[1]
    pitch = episode.get("pitch") or (DOC_VOICE[2] if voice == DOC_VOICE[0] else "+0%")
    lang = voice[:5] if voice[:2] == "en" else "en"

    # 1) Her bölümü ayrı seslendir (zamanlamalar bölüm içinde)
    chapters = []
    for k, ch in enumerate(episode["chapters"]):
        raws = [s for s in ch["scenes"] if s.get("text", "").strip()]
        scenes = [Scene(text=s["text"].strip(), search=s.get("search", "").strip(),
                        image_query=(s.get("image") if isinstance(s.get("image"), str) else None),
                        image_page=s.get("image_page")) for s in raws]
        cdir = work / f"ch{k:02d}"
        cdir.mkdir()
        narration, words, total = mv.synthesize(scenes, voice, rate, cdir, offline, pitch=pitch, language=lang)
        chapters.append({"title": ch.get("title", f"Chapter {k}"), "scenes": scenes, "raws": raws,
                         "words": words, "total": total, "narration": narration, "dir": cdir})
        log(f"Bölüm {k}: {ch.get('title', '')} — {total:.1f} sn, {len(scenes)} sahne")

    # 2) Görseller: bütün sahneler tek seferde (aynı fotoğraf art arda tekrar etmesin)
    flat = [sc for c in chapters for sc in c["scenes"]]
    wiki = episode.get("wiki") or {}
    if wiki.get("site") and wiki.get("page") and not offline:
        from wiki_images import CREDITS, assign, list_images

        CREDITS.clear()
        pools: dict[str, list[dict]] = {}
        for page in dict.fromkeys([wiki["page"]] + [sc.image_page for sc in flat if sc.image_page]):
            try:
                pools[page] = list_images(wiki["site"], page)
            except Exception as e:
                log(f"Wiki görselleri alınamadı: {page} ({type(e).__name__})")
                pools[page] = []
        assign(flat, pools, wiki["page"], episode.get("subject", wiki["page"]), work,
               avoid=wiki.get("avoid"), game_site=False)
        episode["_credits"] = list(dict.fromkeys(CREDITS))
    for sc in flat:
        if sc.image is None:
            sc.image_query = None
            if not sc.search:
                sc.search = episode.get("fallback_search") or "dark forest fog night"
    mv.fetch_clips([sc for sc in flat if sc.image is None], work, offline, episode.get("subject", ""))

    # 3) Parçalar: soğuk açılış → vaka kartı → (bölüm kartı + bölüm)… → kapanış
    base_img = next((sc.image for sc in flat if sc.image is not None), None)
    bg = texture_bg(work / "card_bg.png", base_img, work)
    parts: list[tuple[Path, str | None]] = []
    offset = 0
    for k, c in enumerate(chapters):
        if k == 1:
            parts.append((case_card(episode, bg, work), None))
        if k >= 1:
            parts.append((chapter_card(k, c["title"], bg, work), c["title"]))
        vid = _chapter_video(c["scenes"], c["raws"], c["words"], c["total"], c["narration"], c["dir"],
                             work / f"chapter_{k:02d}.mp4", offset)
        parts.append((vid, c["title"] if k == 0 else None))
        offset += len(c["scenes"])
    parts.append((end_card(episode, bg, work), None))

    # 4) Birleştir, bölüm zamanları
    lst = work / "parts.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p, _ in parts), encoding="utf-8")
    joined = work / "joined.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])
    marks, t = [], 0.0
    for p, title in parts:
        if title:
            marks.append((t, title))
        t += probe_duration(p)
    total = probe_duration(joined)
    episode["_chapters"] = marks
    episode["_long"] = True

    final = out_dir / f"{slug}.mp4"
    _music_mix(joined, total, final, episode)
    thumb = make_thumbnail(episode, next((sc.image for sc in flat
                                          if sc.image is not None and sc.image_query and
                                          (episode.get("thumbnail") or {}).get("image", "~").lower()
                                          in sc.image_query.lower()), base_img), work)
    if thumb:
        shutil.copy(thumb, out_dir / f"{slug}_thumbnail.jpg")
        episode["_thumbnail"] = str(out_dir / f"{slug}_thumbnail.jpg")
    log(f"Hazır: {final} ({total / 60:.1f} dk, {len(marks)} bölüm)")
    for t0, title in marks:
        log(f"  {int(t0 // 60)}:{int(t0 % 60):02d} {title}")
    return final
