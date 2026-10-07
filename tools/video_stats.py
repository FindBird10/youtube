"""Yayınlanan her videonun herkese açık izlenme/beğeni/durum bilgisini çeker (API anahtarı gerekmez).

state/published.json'daki her video için YouTube izleme sayfası okunur; çıktı TSV:
kanal, slug, format, publish_at, durum, izlenme, beğeni, süre_sn, başlık
Yalnızca GitHub Actions'ta çalışır (bulut ortamından YouTube'a erişim yok).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/129.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": "CONSENT=YES+1; SOCS=CAI",
}


def first(pat: str, text: str, default: str = "?") -> str:
    m = re.search(pat, text)
    return m.group(1) if m else default


def stats(vid: str) -> dict:
    t = requests.get(f"https://www.youtube.com/watch?v={vid}", headers=H, timeout=30).text
    status = first(r'"playabilityStatus":\{"status":"(\w+)"', t)
    views = first(r'"videoDetails":\{.*?"viewCount":"(\d+)"', t)
    likes = first(r'"likeCount":"?(\d+)', t, "")
    if not likes:
        likes = first(r'like this video along with ([\d,\.]+) other', t, "")
        likes = likes.replace(",", "").replace(".", "") if likes else first(r'"label":"([\d,\.]+) likes"', t).replace(",", "")
    return {
        "status": status + ("/unlisted" if '"isUnlisted":true' in t else ""),
        "views": views,
        "likes": likes,
        "length": first(r'"lengthSeconds":"(\d+)"', t),
        "channel_id": first(r'"channelId":"(UC[\w-]{22})"', t, ""),
    }


def main() -> None:
    pub = json.loads((ROOT / "state/published.json").read_text())
    print("kanal\tslug\tformat\tpublish_at\tdurum\tizlenme\tbegeni\tsure\tbaslik")
    seen_ids: dict[str, str] = {}
    for p in pub:
        slug = p["slug"]
        ch = slug.split("/")[0] if "/" in slug else "birdsvault"
        try:
            s = stats(p["video_id"])
        except Exception as e:
            s = {"status": f"hata:{type(e).__name__}", "views": "?", "likes": "?", "length": "?", "channel_id": ""}
        if s["channel_id"]:
            seen_ids.setdefault(ch, s["channel_id"])
        print(ch, slug, p.get("format", ""), (p.get("publish_at") or "")[:16], s["status"], s["views"],
              s["likes"], s["length"], p.get("title", ""), sep="\t", flush=True)
        time.sleep(0.7)
    print("\n# kanal kimlikleri:", json.dumps(seen_ids), file=sys.stderr)


if __name__ == "__main__":
    main()
