"""Bölüm metninde yapay zekâ izi bırakan kalıpları ve zayıf yazımı yakalar.

  python tools/check_episode.py episodes/global/2026-10-14-1-....json [başka dosyalar...]

HATA: mutlaka düzelt (kalıp cümle, yasak ifade). UYARI: gözden geçir (aşırı kullanılan kelime,
somut ayrıntı eksikliği, son günlerle aynı açılış). Çıkış kodu: HATA varsa 1.

13 Eki 2026: bir izleyici Global Shorts'una "narrator, texts and video is AI. This is AI slop" yazdı;
son 12 Global videosunun 10'unda "But here's…" geçiyordu.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Kesin yasak: yapay zekâ metninin en bilinen kalıpları (İngilizce + Türkçe)
BANNED = [
    r"\bbut here'?s\b", r"\bhere'?s the (thing|kicker|twist|catch|strange|wild|crazy|scary)",
    r"\bhere'?s where it gets\b", r"\bbut that'?s not (all|the worst|the strangest|even)",
    r"\bbut that was not the (worst|strangest)", r"\bthe (strangest|weirdest|craziest|scariest) part\b",
    r"\byou won'?t believe\b", r"\bdid you know\b", r"\blet'?s dive\b", r"\bdive (in|into)\b", r"\bdelve",
    r"\blittle did (they|he|she|anyone) know\b", r"\bbuckle up\b", r"\bstay tuned\b", r"\bin today'?s video\b",
    r"\bthe answer (may|might|will) (surprise|shock)", r"\bsends? shivers\b", r"\bspine[- ]chilling\b",
    r"\bmind[- ]?blowing\b", r"\bshrouded in mystery\b", r"\btapestry\b", r"\ba testament to\b",
    r"\bunravel", r"\bwe open the file\b", r"\bwhat happened next\b", r"\bplot twist\b",
    r"\bbiliyor muydunuz\b", r"\binanamayacaksınız\b", r"\bgelin birlikte\b", r"\bbugün sizlere\b",
    r"\basıl (ilginç|şaşırtıcı|korkunç|tuhaf) (olan|kısım)", r"\bama asıl\b", r"\bişte asıl\b",
    r"\bpeki ya\b", r"\bpeki ama\b", r"\bkimse bunu beklemiyordu\b",
]
# Video başına en fazla 1 kez
LIMITED = [
    r"\bto this day\b", r"\bremains? (a )?myster", r"\bstill (a )?myster", r"\bno one knows\b",
    r"\bnobody knows\b", r"\bchilling\b", r"\beerie\b", r"\bterrifying\b", r"\bimagine\b",
    r"\bfor (over|more than) \w+ (years|decades)\b", r"\bgizemini koruyor\b", r"\bhâlâ (bir )?gizem",
    r"\bkimse bilmiyor\b", r"\btüyler? ürpertici\b", r"\bdüşünün\b",
]
NUM_RE = re.compile(r"\d|\b(one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million)\b", re.I)


def texts(ep: dict) -> list[str]:
    if ep.get("chapters"):
        return [s.get("text", "") for c in ep["chapters"] for s in c.get("scenes", [])]
    return [s.get("text", "") for s in ep.get("scenes", [])]


def first_words(ep: dict, n: int = 3) -> str:
    t = texts(ep)
    return " ".join(re.findall(r"[\w'’]+", t[0].lower())[:n]) if t else ""


def check(path: Path) -> tuple[list[str], list[str]]:
    ep = json.loads(path.read_text(encoding="utf-8"))
    body = " ".join(texts(ep))
    low = body.lower()
    errs, warns = [], []
    seen: set[int] = set()
    for pat in BANNED:
        for m in re.finditer(pat, low):
            if any(abs(m.start() - k) < 30 for k in seen):
                continue
            seen.add(m.start())
            errs.append(f"kalıp ifade: \"{body[max(0, m.start() - 20):m.end() + 25].strip()}\"")
    for pat in LIMITED:
        n = len(re.findall(pat, low))
        if n > 1:
            warns.append(f"'{pat.strip(chr(92) + 'b')}' {n} kez geçiyor (en fazla 1)")
    if not NUM_RE.search(body):
        warns.append("hiç somut sayı/tarih yok: en az bir kesin rakam, tarih ya da ölçü ekle")
    caps = set(re.findall(r"(?<![.!?]\s)(?<!^)\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]{2,}", body))
    if len(caps) < 2:
        warns.append("özel isim çok az: kişi/yer/kurum adıyla somutlaştır")
    # Aynı klasördeki son bölümlerle aynı açılış kalıbı
    fw = first_words(ep)
    sibs = sorted(p for p in path.parent.glob("*.json") if not p.name.startswith("_") and p != path)[-9:]
    same = [p.name for p in sibs if fw and first_words(json.loads(p.read_text(encoding="utf-8"))) == fw]
    if same:
        warns.append(f"açılış \"{fw}…\" son bölümlerle aynı ({', '.join(same[:3])}): farklı başla")
    starts = [first_words({"scenes": [{"text": t}]}, 2) for t in texts(ep)]
    for w in set(starts):
        if w and starts.count(w) >= 3:
            warns.append(f"{starts.count(w)} sahne \"{w}…\" ile başlıyor: cümle yapılarını çeşitlendir")
    return errs, warns


def main() -> int:
    bad = 0
    for arg in sys.argv[1:]:
        p = Path(arg)
        errs, warns = check(p)
        print(f"== {p.name}: {len(errs)} hata, {len(warns)} uyarı")
        for e in errs:
            print("  HATA  ", e)
        for w in warns:
            print("  UYARI ", w)
        bad += bool(errs)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
