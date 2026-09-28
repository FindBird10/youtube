"""Yüklenmemiş bölümleri bulur, videolarını üretir ve YouTube'a yükler.

- episodes/*.json içindeki, state/published.json'da kaydı olmayan her bölüm işlenir.
- Adı "_" ile başlayan dosyalar (ör. _ornek.json) atlanır.
- YouTube anahtarları tanımlı değilse yalnızca video üretilir (önizleme için).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_video import ROOT, load_episode, render  # noqa: E402
from upload import have_credentials, upload  # noqa: E402

STATE = ROOT / "state" / "published.json"


def load_state() -> list[dict]:
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else []


def save_state(items: list[dict]) -> None:
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def summary(line: str) -> None:
    print(line, flush=True)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", help="Yalnızca bu bölümü işle (yol veya ad)")
    ap.add_argument("--no-upload", action="store_true")
    ap.add_argument("--max", type=int, default=int(os.environ.get("MAX_PER_RUN", "3")))
    a = ap.parse_args()

    state = load_state()
    done = {x["slug"] for x in state}

    if a.episode:
        p = Path(a.episode)
        if not p.exists():
            p = ROOT / "episodes" / (a.episode if a.episode.endswith(".json") else a.episode + ".json")
        pending = [p]
    else:
        pending = [p for p in sorted((ROOT / "episodes").glob("*.json"))
                   if not p.name.startswith("_") and p.stem not in done][: a.max]

    if not pending:
        summary("Bekleyen bölüm yok.")
        return 0

    can_upload = have_credentials() and not a.no_upload
    if not can_upload:
        summary("> YouTube anahtarları tanımlı değil ya da yükleme kapalı: videolar yalnızca üretilecek "
                "(Actions > bu çalıştırma > Artifacts altından indirebilirsin).")

    out = ROOT / "build"
    out.mkdir(exist_ok=True)
    failed = 0
    for p in pending:
        try:
            ep = load_episode(p)
            video = render(ep, out)
            if can_upload:
                vid, channel = upload(video, ep)
                state.append({
                    "slug": ep["_slug"], "title": ep["title"], "video_id": vid,
                    "url": f"https://youtube.com/shorts/{vid}", "channel": channel, "format": ep.get("format"),
                    "publish_at": ep.get("publish_at"),
                    "uploaded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                })
                save_state(state)
                when = f", yayın: {ep['publish_at']}" if ep.get("publish_at") else ""
                summary(f"- ✅ **{ep['title']}** → https://youtube.com/shorts/{vid} (kanal: **{channel}**{when})")
            else:
                summary(f"- 🎬 **{ep['title']}** üretildi: `build/{video.name}`")
        except Exception as e:
            failed += 1
            traceback.print_exc()
            summary(f"- ❌ `{p.name}`: {e}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
