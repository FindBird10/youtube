"""Kanalların herkese açık video istatistiklerini toplar (API anahtarı gerekmez).

İki kaynak:
  1. Kanalın Shorts sekmesi (tüm Shorts, yuvarlanmış izlenme: "1.6K views")
  2. RSS akışı (son 15 video, kesin izlenme ve beğeni)
state/published.json ile eşleştirip TSV yazar:
kanal, slug, format, publish_at, izlenme(kesin|yaklaşık), beğeni, başlık
Yalnızca GitHub Actions'ta çalışır (bulut ortamından YouTube'a erişim yok).
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CHANNEL_IDS = {
    "birdsvault": "UC5w1LBA7sE_U9taLW0kuKYA",
    "gaming": "UC-Ady9DQ8uTMpZfV_GeDKIA",
    "global": "UCp2rjdN1M1z0GMJ2Gshzdfw",
}
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/129.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": "CONSENT=YES+1; SOCS=CAI",
}
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
      "media": "http://search.yahoo.com/mrss/"}


def parse_count(s: str) -> int | None:
    m = re.search(r"([\d.,]+)\s*([KMB]?)", s or "")
    if not m:
        return None
    n = float(m.group(1).replace(",", ""))
    return int(n * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9}[m.group(2)])


def rss(cid: str) -> dict[str, tuple[int, str]]:
    out = {}
    try:
        root = ET.fromstring(requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}",
                                          headers=H, timeout=30).content)
        for e in root.findall("a:entry", NS):
            st = e.find("media:group/media:community/media:statistics", NS)
            rt = e.find("media:group/media:community/media:starRating", NS)
            out[e.findtext("yt:videoId", "", NS)] = (int(st.get("views")) if st is not None else None,
                                                     rt.get("count") if rt is not None else "?")
    except Exception as ex:
        print(f"RSS {cid}: {ex}", file=sys.stderr)
    return out


def _walk(o, found: dict) -> None:
    if isinstance(o, dict):
        for key in ("shortsLockupViewModel", "reelItemRenderer"):
            if key in o:
                blob = json.dumps(o[key], ensure_ascii=False)
                vid = re.search(r'"videoId":\s*"([\w-]{11})"', blob)
                views = re.search(r'"(?:content|simpleText)":\s*"([\d.,]+[KMB]? views?)"', blob) \
                    or re.search(r'"accessibilityText":\s*"[^"]*?, ([\d.,]+[KMB]? views?)', blob)
                if vid:
                    found[vid.group(1)] = views.group(1) if views else "?"
        for v in o.values():
            _walk(v, found)
    elif isinstance(o, list):
        for v in o:
            _walk(v, found)


def shorts_tab(cid: str) -> dict[str, str]:
    found: dict[str, str] = {}
    try:
        html = requests.get(f"https://www.youtube.com/channel/{cid}/shorts", headers=H, timeout=30).text
        m = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S)
        if not m:
            print(f"Shorts sekmesi {cid}: ytInitialData yok ({len(html)} bayt)", file=sys.stderr)
            return found
        data = json.loads(m.group(1))
        _walk(data, found)
        # devamı (48'den fazla Shorts varsa)
        key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
        ver = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html)
        for _ in range(5):
            tok = re.findall(r'"continuationCommand":\{"token":"([^"]+)"', json.dumps(data))
            if not (tok and key and ver):
                break
            data = requests.post(f"https://www.youtube.com/youtubei/v1/browse?key={key.group(1)}", headers=H,
                                 json={"context": {"client": {"clientName": "WEB", "clientVersion": ver.group(1),
                                                              "hl": "en", "gl": "US"}},
                                       "continuation": tok[-1]}, timeout=30).json()
            before = len(found)
            _walk(data, found)
            if len(found) == before:
                break
    except Exception as ex:
        print(f"Shorts sekmesi {cid}: {type(ex).__name__} {ex}", file=sys.stderr)
    return found


def main() -> None:
    pub = json.loads((ROOT / "state/published.json").read_text())
    tab, feed = {}, {}
    for ch, cid in CHANNEL_IDS.items():
        t, f = shorts_tab(cid), rss(cid)
        print(f"{ch}: Shorts sekmesi {len(t)} video, RSS {len(f)} video", file=sys.stderr)
        tab.update(t)
        feed.update(f)
    print("kanal\tslug\tformat\tpublish_at\tizlenme\tkaynak\tbegeni\tbaslik")
    known = set()
    for p in pub:
        vid, slug = p["video_id"], p["slug"]
        known.add(vid)
        ch = slug.split("/")[0] if "/" in slug else "birdsvault"
        if vid in feed and feed[vid][0] is not None:
            views, src, likes = feed[vid][0], "rss", feed[vid][1]
        elif vid in tab:
            views, src, likes = parse_count(tab[vid]), "sekme", "?"
        else:
            views, src, likes = None, "yok(gizli/silinmiş?)", "?"
        print(ch, slug, p.get("format", ""), (p.get("publish_at") or "")[:16], views if views is not None else "?",
              src, likes, p.get("title", ""), sep="\t")
    extra = [v for v in list(tab) + list(feed) if v not in known]
    for v in dict.fromkeys(extra):
        print("?", v, "", "", tab.get(v, feed.get(v, ("?",))[0]), "kayıtta-yok", "?", "", sep="\t")


if __name__ == "__main__":
    main()
