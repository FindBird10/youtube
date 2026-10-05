"""Oyun/dizi wiki'lerinden (Fandom vb. MediaWiki siteleri) karakter görselleri çeker.

Bölümde:
  "wiki": {"site": "thelastofus.fandom.com", "page": "Ellie"}
  sahnelerde: "image": "anahtar kelimeler"   (dosya adında aranır; "" = herhangi bir görsel)
"""
from __future__ import annotations

import re
from pathlib import Path

import faces

CREDITS: list[str] = []   # atıf gerektiren (CC BY/BY-SA) kullanılan görseller; açıklamaya eklenir
UA = "BirdsVaultShorts/1.0 (+https://github.com/FindBird10/youtube)"
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
# Simge, logo, harita vb. küçük/alakasız dosyaları ele
SKIP_RE = re.compile(r"icon|logo|sprite|symbol|emblem|badge|map|wordmark|favicon|button|trophy|achievement|"
                     r"signature|flag|site-|wiki|placeholder|\.svg|\.gif", re.I)


def _log(msg: str) -> None:
    print(f"[wiki_images] {msg}", flush=True)


def list_images(site: str, page: str, min_w: int = 600, min_h: int = 400) -> list[dict]:
    import requests

    wikimedia = "wikipedia.org" in site or "wikimedia.org" in site
    # Wikipedia/Commons'un API yolu /w/api.php; Fandom'unki /api.php
    api = f"https://{site}/w/api.php" if wikimedia else f"https://{site}/api.php"
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
                                           "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata",
                                           "iiextmetadatafilter": "LicenseShortName|NonFree|Artist", "format": "json"})
        r.raise_for_status()
        for p in r.json().get("query", {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [{}])[0]
            if not (ii.get("url") and ii.get("width", 0) >= min_w and ii.get("height", 0) >= min_h):
                continue
            meta = ii.get("extmetadata") or {}
            lic = (meta.get("LicenseShortName") or {}).get("value", "")
            if wikimedia:
                # Yalnızca kamu malı / CC0: atıf gerektirmez, telif riski yok. "Fair use" görseller elenir.
                nonfree = str((meta.get("NonFree") or {}).get("value", "")).lower() in ("true", "1")
                if nonfree or not FREE_LICENSE_RE.search(lic):
                    continue
            artist = re.sub(r"<[^>]+>", "", (meta.get("Artist") or {}).get("value", "")).strip()
            out.append({"name": p["title"], "url": ii["url"], "w": ii["width"], "h": ii["height"],
                        "license": lic, "artist": re.sub(r"\s+", " ", artist)[:80]})
    _log(f"{site}/{page}: {len(out)} uygun görsel")
    return out


# Kamu malı / CC0 (atıf gerekmez) ve CC BY / CC BY-SA (atıf açıklamaya otomatik eklenir).
# NC/ND (ticari olmayan / türetilemez) ve "fair use" görseller elenir.
FREE_LICENSE_RE = re.compile(r"public domain|^pd|pd-|cc0|no restrictions|copyrighted free use|^cc[ -]by(?![ -]?n[cd])", re.I)
NEEDS_CREDIT_RE = re.compile(r"^cc[ -]by", re.I)

NON_GAME_RE = re.compile(r"drawing|sketch|concept|comic|american dreams|artwork|illustration|poster|"
                         r"cover|fan ?art|render|model|cosplay|merch|figure|statue|funko|book", re.I)


def assign(scenes: list, pools: dict[str, list[dict]], main_page: str, subject: str, work: Path,
           avoid: list[str] | None = None, game_site: bool = True) -> None:
    """image_query'si olan sahnelere görsel indirir (dosya adı eşleşmesine göre, tekrar etmeden).

    Sahnenin image_page'i varsa önce o sayfanın görsellerine, yoksa bölümün ana sayfasına bakılır.
    """
    import requests

    used: set[str] = set()
    subj = {w for w in re.findall(r"[a-z]+", subject.lower()) if len(w) > 2}
    avoid = [a.lower() for a in (avoid or [])]

    def score(img: dict, want: set[str]) -> float:
        name = img["name"].lower()
        s = 3.0 * sum(1 for w in want if w in name)
        s += 1.0 * sum(1 for w in subj if w in name)          # karakterin adı geçen görseller öne
        s += 0.5 if img["w"] >= 1200 else 0.0                    # net görsel
        if game_site and NON_GAME_RE.search(name):                # oyun wiki'sinde çizim/konsept geri planda
            s -= 4.0
        if avoid and any(a in name for a in avoid):               # ör. başka oyunun görselleri
            s -= 6.0
        return s

    def fetch(im: dict, dst: Path) -> bool:
        try:
            with requests.get(im["url"], headers={"User-Agent": UA}, timeout=60) as r:
                r.raise_for_status()
                dst.write_bytes(r.content)
            return True
        except Exception as e:
            _log(f"indirme hatası: {im['name']} ({type(e).__name__})")
            return False

    def ext_of(im: dict) -> str:
        ext = Path(im["url"].split("?")[0]).suffix.lower()
        return ext if ext in IMG_EXT else ".jpg"

    for i, sc in enumerate(scenes):
        if sc.image_query is None:
            continue
        want = {w for w in re.findall(r"[a-z0-9]+", sc.image_query.lower()) if len(w) > 1}
        page = sc.image_page or main_page
        page_words = {w for w in re.findall(r"[a-z]+", page.lower()) if len(w) > 2}
        images = pools.get(page) or pools.get(main_page, [])
        cands = [im for im in images if im["url"] not in used] or images
        if not cands:
            _log(f"Sahne {i + 1}: görsel yok, stok görüntüye düşülecek")
            sc.image_query = None
            continue
        ranked = sorted(cands, key=lambda im: score(im, want), reverse=True)
        # Karakter sahnelerinde (ilk sahne ya da karakter adı geçen sorgu) yüzü görünen görsel seç:
        # dikey kırpmada karakter kadraj dışında kalırsa izleyici kimin anlatıldığını anlamaz.
        wants_face = i == 0 or bool(want & (subj | page_words))
        tries = (6 if i == 0 else 4) if wants_face else 1
        chosen, first_ok = None, None
        for k, im in enumerate(ranked[:tries]):
            dst = work / f"img_{i:02d}_c{k}{ext_of(im)}"
            if not fetch(im, dst):
                continue
            if first_ok is None:
                first_ok = (im, dst)
            if not wants_face:
                chosen = (im, dst)
                break
            f = faces.focus(dst)
            if f and f[2] >= 0.08:                       # yeterince büyük bir yüz
                chosen = (im, dst)
                break
        chosen = chosen or first_ok
        if not chosen:
            _log(f"Sahne {i + 1}: indirilemedi, stok görüntüye düşülecek")
            sc.image_query = None
            continue
        best, sc.image = chosen
        if NEEDS_CREDIT_RE.search(best.get("license", "")):
            CREDITS.append(f"{best['name'].removeprefix('File:')} — {best.get('artist') or 'Wikimedia Commons'}, "
                           f"{best['license']}")
        used.add(best["url"])
        f = faces.focus(sc.image)
        _log(f"Sahne {i + 1}: {best['name']} ({best['w']}x{best['h']})"
             + (f", yüz x={f[0]:.2f} y={f[1]:.2f}" if f else ", yüz yok (ortadan kırpılacak)"))
        # Hızlı kesme: sahneye ek görseller
        extra = [im for im in ranked if im["url"] not in used][: max(0, getattr(sc, "n_shots", 1) - 1)]
        for j, im in enumerate(extra):
            dst2 = work / f"img_{i:02d}_{j + 1}{ext_of(im)}"
            if fetch(im, dst2):
                used.add(im["url"])
                sc.extra_images.append(dst2)
