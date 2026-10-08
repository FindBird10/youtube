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
from upload import UploadLimit, WrongChannel, find_existing, have_credentials, token_fingerprint, upload  # noqa: E402

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


def remote_done() -> set[str]:
    """origin/main'deki en güncel kayıttaki anahtarlar (başka çalıştırmanın az önce yüklediği dahil)."""
    import subprocess

    if os.environ.get("GITHUB_ACTIONS") != "true":
        return set()
    subprocess.run(["git", "fetch", "-q", "origin", "main"], cwd=ROOT, capture_output=True)
    r = subprocess.run(["git", "show", "origin/main:state/published.json"], cwd=ROOT,
                       capture_output=True, text=True)
    try:
        return {x["slug"] for x in json.loads(r.stdout)}
    except Exception:
        return set()


def push_state(note: str) -> None:
    """Kaydı her yüklemeden hemen sonra main'e gönderir (yalnızca GitHub Actions'ta).

    Çalıştırma yarıda kesilse bile yüklenen video kayıtta kalır ve bir sonraki çalıştırma
    aynı videoyu tekrar yüklemez. Ayrı bir worktree'de uzak kayıtla birleştirilir.
    """
    import subprocess

    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    wt = Path("/tmp/state_wt")
    sh = lambda *c, **k: subprocess.run(list(c), cwd=k.get("cwd", ROOT), capture_output=True, text=True)  # noqa: E731
    for attempt in range(5):
        sh("git", "worktree", "remove", "--force", str(wt))
        sh("git", "fetch", "-q", "origin", "main")
        r = sh("git", "worktree", "add", "-q", "--detach", str(wt), "origin/main")
        if r.returncode != 0:
            print(f"[state] worktree açılamadı: {r.stderr.strip()}", flush=True)
            return
        sh("python", str(ROOT / "tools" / "merge_state.py"), str(STATE),
           str(BLOCKED) if BLOCKED.exists() else "-", cwd=wt)
        sh("git", "add", "state/", cwd=wt)
        if sh("git", "diff", "--cached", "--quiet", cwd=wt).returncode == 0:
            return
        sh("git", "-c", "user.name=shorts-bot", "-c", "user.email=shorts-bot@users.noreply.github.com",
           "commit", "-qm", f"Yayın kaydı: {note} [skip ci]", cwd=wt)
        if sh("git", "push", "-q", "origin", "HEAD:main", cwd=wt).returncode == 0:
            print(f"[state] kayıt gönderildi ({note})", flush=True)
            sh("git", "worktree", "remove", "--force", str(wt))
            return
        import time
        time.sleep(3 * (attempt + 1))
    print("[state] kayıt gönderilemedi; çalıştırma sonundaki adım tekrar deneyecek", flush=True)


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
    limited: set[str] = set()   # bu çalıştırmada günlük yükleme sınırına takılan kanallar

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
            until = CHANNELS[ch].get("paused_until")
            if not a.no_upload and until and dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(
                    until.replace("Z", "+00:00")):
                summary(f"- ⏸️ `{ch}/{p.name}`: {ch} yüklemeleri {until} sonrasına kadar bekletiliyor.")
                continue
            max_age = CHANNELS[ch].get("max_age_hours")
            if not a.no_upload and max_age:
                try:
                    pa = json.loads(p.read_text()).get("publish_at")
                    if pa and dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(
                            pa.replace("Z", "+00:00")) > dt.timedelta(hours=max_age):
                        summary(f"- 🗓️ `{ch}/{p.name}`: yayın saati {max_age} saatten eski (bayat haber), yüklenmiyor.")
                        continue
                except (ValueError, OSError):
                    pass
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
            if not a.no_upload and not a.episode and ep["_key"] in remote_done():
                summary(f"- ↩️ `{p.name}`: başka bir çalıştırma az önce yüklemiş, atlandı.")
                continue
            if not a.no_upload and ep["_channel"] in limited:
                summary(f"- ⏳ `{p.name}`: {ep['_channel']} günlük yükleme sınırında, atlandı.")
                continue
            if not a.no_upload and have_credentials(ep["_channel"]):
                dup = find_existing(ep["_channel"], ep["title"])
                if dup:
                    state.append({
                        "slug": ep["_key"], "title": ep["title"], "video_id": dup,
                        "url": f"https://youtube.com/shorts/{dup}", "channel": CHANNELS[ep["_channel"]]["expect_title"],
                        "account": ep["_channel"], "format": ep.get("format"), "publish_at": ep.get("publish_at"),
                        "uploaded_at": None, "note": "kanalda zaten vardı (RSS), yeniden yüklenmedi",
                    })
                    save_state(state)
                    summary(f"- ♻️ **{ep['title']}** kanalda zaten var → https://youtube.com/shorts/{dup}")
                    continue
            video = render(ep, out)
            if not a.no_upload and have_credentials(ep["_channel"]):
                if is_blocked(ep["_channel"], blocked):
                    summary(f"- ⛔ `{p.name}`: token yanlış kanala ait, yüklenmedi.")
                    continue
                if ep["_channel"] in limited:
                    summary(f"- ⏳ `{p.name}`: {ep['_channel']} kanalının günlük yükleme sınırı doldu, sonraki çalıştırmaya kaldı.")
                    continue
                try:
                    vid, channel = upload(video, ep)
                except UploadLimit:
                    limited.add(ep["_channel"])
                    summary(f"- ⏳ `{p.name}`: YouTube günlük yükleme sınırı doldu ({ep['_channel']}); "
                            f"bölüm bekletiliyor, sonraki çalıştırmada denenecek.")
                    continue
                except WrongChannel as e:
                    blocked[ep["_channel"]] = token_fingerprint(ep["_channel"])
                    BLOCKED.write_text(json.dumps(blocked, indent=2) + "\n", encoding="utf-8")
                    push_state(f"{ep['_channel']} token engellendi")
                    raise
                except Exception as e:  # geçersiz/iptal edilmiş token: kanal bekletilir, çalıştırma bozulmaz
                    if "invalid_grant" not in str(e) and "unauthorized_client" not in str(e):
                        raise
                    limited.add(ep["_channel"])
                    summary(f"- 🔑 `{p.name}`: {CHANNELS[ep['_channel']]['token_env']} geçersiz "
                            f"({'invalid_grant' if 'invalid_grant' in str(e) else 'unauthorized_client'}); "
                            f"token yenilenene kadar {ep['_channel']} bekletiliyor.")
                    continue
                state.append({
                    "slug": ep["_key"], "title": ep["title"], "video_id": vid,
                    "url": f"https://youtube.com/shorts/{vid}", "channel": channel, "account": ep["_channel"], "format": ep.get("format"),
                    "publish_at": ep.get("publish_at"),
                    "uploaded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                })
                save_state(state)
                push_state(ep["_key"])
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
