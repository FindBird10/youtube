"""Yüklenmemiş bölümleri bulur, videolarını üretir ve YouTube'a yükler.

- episodes/*.json (BirdsVault) ve episodes/<kanal>/*.json içindeki, state/published.json'da
  kaydı olmayan her bölüm işlenir. Token'ı tanımlı olmayan kanalın bölümleri bekletilir.
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
from channels import CHANNELS, channel_of, episode_key  # noqa: E402
from upload import WrongChannel, have_credentials, token_fingerprint, upload  # noqa: E402

STATE = ROOT / "state" / "published.json"
# Yanlış kanala ait çıkan token'lar (parmak izi). Secret değişince engel kendiliğinden kalkar.
BLOCKED = ROOT / "state" / "blocked_tokens.json"


def load_blocked() -> dict:
    return json.loads(BLOCKED.read_text(encoding="utf-8")) if BLOCKED.exists() else {}


def is_blocked(ch: str, blocked: dict) -> bool:
    return bool(blocked.get(ch)) and blocked[ch] == token_fingerprint(ch)


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
    blocked = load_blocked()

    ep_dir = ROOT / "episodes"
    if a.episode:
        p = Path(a.episode)
        if not p.exists():
            p = ep_dir / (a.episode if a.episode.endswith(".json") else a.episode + ".json")
        pending = [p]
    else:
        files = sorted(ep_dir.glob("*.json"))
        for ch in CHANNELS:
            if (ep_dir / ch).is_dir():
                files += sorted((ep_dir / ch).glob("*.json"))
        pending = []
        for p in files:
            ch = channel_of(p, ep_dir)
            if p.name.startswith("_") or episode_key(ch, p.stem) in done:
                continue
            if not a.no_upload and not CHANNELS[ch].get("enabled", True):
                summary(f"- ⏸️ `{ch}/{p.name}`: {ch} kanalına yükleme geçici olarak kapalı (channels.py).")
                continue
            if not a.no_upload and have_credentials(ch) and is_blocked(ch, blocked):
                summary(f"- ⛔ `{ch}/{p.name}`: {CHANNELS[ch]['token_env']} yanlış kanala ait; "
                        f"secret yenilenene kadar yükleme yapılmıyor.")
                continue
            if not a.no_upload and not have_credentials(ch):
                summary(f"- ⏸️ `{ch}/{p.name}`: {CHANNELS[ch]['token_env']} tanımlı değil, bölüm bekletiliyor.")
                continue
            pending.append(p)
        pending = pending[: a.max]

    if not pending:
        summary("Bekleyen bölüm yok.")
        return 0

    if a.no_upload:
        summary("> Yükleme kapalı: videolar yalnızca üretilecek.")

    out = ROOT / "build"
    out.mkdir(exist_ok=True)
    failed = 0
    for p in pending:
        try:
            ep = load_episode(p)
            video = render(ep, out)
            if not a.no_upload and have_credentials(ep["_channel"]):
                if is_blocked(ep["_channel"], blocked):
                    summary(f"- ⛔ `{p.name}`: token yanlış kanala ait, yüklenmedi.")
                    continue
                try:
                    vid, channel = upload(video, ep)
                except WrongChannel as e:
                    blocked[ep["_channel"]] = token_fingerprint(ep["_channel"])
                    BLOCKED.write_text(json.dumps(blocked, indent=2) + "\n", encoding="utf-8")
                    raise
                state.append({
                    "slug": ep["_key"], "title": ep["title"], "video_id": vid,
                    "url": f"https://youtube.com/shorts/{vid}", "channel": channel, "account": ep["_channel"], "format": ep.get("format"),
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
