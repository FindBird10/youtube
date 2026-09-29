"""Oyun/dizi wiki'lerinden (Fandom vb. MediaWiki siteleri) karakter görselleri çeker.

Bölümde:
  "wiki": {"site": "thelastofus.fandom.com", "page": "Ellie"}
  sahnelerde: "image": "anahtar kelimeler"   (dosya adında aranır; "" = herhangi bir görsel)
"""
from __future__ import annotations

import re
from pathlib import Path

UA = "BirdsVaultShorts/1.0 (+https://github.com/FindBird10/youtube)"
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
# Simge, logo, harita vb. küçük/alakasız dosyaları ele
SKIP_RE = re.compile(r"icon|logo|sprite|symbol|emblem|badge|map|wordmark|favicon|button|trophy|achievement|"
                     r"signature|flag|site-|wiki|placeholder|\.svg|\.gif", re.I)


def _log(msg: str) -> None:
    print(f"[wiki_images] {msg}", flush=True)


def list_images(site: str, page: str, min_w: int = 600, min_h: int = 400) -> list[dict]:
    import requests

    api = f"https://{site}/api.php"
    s = requests.Session()
    s.headers["User-Agent"] = UA
    r = s.get(api, timeout=30, params={"action": "query", "titles": page, "prop": "images", "imlimit": 500,
                                       "redirects": 1, "format": "json"})
    r.raise_for_status()
    titles = []
    for p in r.json().get("query", {}).get("pages", {}).values():
        titles += [i["title"] for i in p.get("images", [])]
    titles = [t for t in titles if t.lower().endswith(IMG_EXT) and not SKIP_RE.search(t)]
    out = []
    for k in range(0, len(titles), 50):
        r = s.get(api, timeout=30, params={"action": "query", "titles": "|".join(titles[k:k + 50]),
                                           "prop": "imageinfo", "iiprop": "url|size|mime", "format": "json"})
        r.raise_for_status()
        for p in r.json().get("query", {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [{}])[0]
            if ii.get("url") and ii.get("width", 0) >= min_w and ii.get("height", 0) >= min_h:
                out.append({"name": p["title"], "url": ii["url"], "w": ii["width"], "h": ii["height"]})
    _log(f"{site}/{page}: {len(out)} uygun görsel")
    return out


def assign(scenes: list, pools: dict[str, list[dict]], main_page: str, subject: str, work: Path) -> None:
    """image_query'si olan sahnelere görsel indirir (dosya adı eşleşmesine göre, tekrar etmeden).

    Sahnenin image_page'i varsa önce o sayfanın görsellerine, yoksa bölümün ana sayfasına bakılır.
    """
    import requests

    used: set[str] = set()
    subj = {w for w in re.findall(r"[a-z]+", subject.lower()) if len(w) > 2}

    def score(img: dict, want: set[str]) -> float:
        name = img["name"].lower()
        s = 3.0 * sum(1 for w in want if w in name)
        s += 1.0 * sum(1 for w in subj if w in name)          # karakterin adı geçen görseller öne
        s += 0.5 if img["w"] >= 1200 else 0.0                    # net görsel
        return s

    for i, sc in enumerate(scenes):
        if sc.image_query is None:
            continue
        want = {w for w in re.findall(r"[a-z0-9]+", sc.image_query.lower()) if len(w) > 1}
        images = pools.get(sc.image_page or main_page) or pools.get(main_page, [])
        cands = [im for im in images if im["url"] not in used] or images
        if not cands:
            _log(f"Sahne {i + 1}: görsel yok, stok görüntüye düşülecek")
            sc.image_query = None
            continue
        ranked = sorted(cands, key=lambda im: score(im, want), reverse=True)
        best = ranked[0]
        used.add(best["url"])
        # Hızlı kesme: sahneye ek görseller
        for j, im in enumerate([im for im in ranked[1:] if im["url"] not in used][: max(0, getattr(sc, "n_shots", 1) - 1)]):
            ext2 = Path(im["url"].split("?")[0]).suffix.lower()
            dst2 = work / f"img_{i:02d}_{j + 1}{ext2 if ext2 in IMG_EXT else '.jpg'}"
            try:
                with requests.get(im["url"], headers={"User-Agent": UA}, timeout=60) as r:
                    r.raise_for_status()
                    dst2.write_bytes(r.content)
                used.add(im["url"])
                sc.extra_images.append(dst2)
            except Exception as e:
                _log(f"Sahne {i + 1}: ek görsel indirilemedi ({type(e).__name__})")
        ext = Path(best["url"].split("?")[0]).suffix.lower() or ".jpg"
        dst = work / f"img_{i:02d}{ext if ext in IMG_EXT else '.jpg'}"
        try:
            with requests.get(best["url"], headers={"User-Agent": UA}, timeout=60) as r:
                r.raise_for_status()
                dst.write_bytes(r.content)
            sc.image = dst
            _log(f"Sahne {i + 1}: {best['name']} ({best['w']}x{best['h']})")
        except Exception as e:
            _log(f"Sahne {i + 1}: indirme hatası ({type(e).__name__}), stok görüntüye düşülecek")
            sc.image_query = None
