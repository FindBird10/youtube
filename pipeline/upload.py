"""Hazır videoyu YouTube Data API v3 ile yükler.

Gerekli ortam değişkenleri (GitHub Secrets):
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN

Not: Google'ın denetiminden (audit) geçmemiş API projelerinden yüklenen
videolar YouTube tarafından zorunlu olarak "gizli" (private) tutulur.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def have_credentials() -> bool:
    return all(os.environ.get(k, "").strip() for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"))


def _service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(
        None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"].strip(),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YT_CLIENT_ID"].strip(),
        client_secret=os.environ["YT_CLIENT_SECRET"].strip(),
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload(video: Path, episode: dict) -> str:
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    desc = episode.get("description", "").strip()
    if "#shorts" not in desc.lower():
        desc = (desc + "\n\n#Shorts").strip()
    privacy = episode.get("privacy") or os.environ.get("YT_DEFAULT_PRIVACY", "private")
    status = {
        "privacyStatus": privacy,
        "selfDeclaredMadeForKids": bool(episode.get("made_for_kids", False)),
        "containsSyntheticMedia": bool(episode.get("synthetic_media", False)),
    }
    if episode.get("publish_at"):
        # Zamanlanmış yayın yalnızca "private" durumla çalışır
        status["privacyStatus"] = "private"
        status["publishAt"] = episode["publish_at"]

    lang = episode.get("language", "tr")
    body = {
        "snippet": {
            "title": episode["title"][:100],
            "description": desc[:4900],
            "tags": episode.get("tags", [])[:30],
            "categoryId": str(episode.get("category_id", os.environ.get("YT_CATEGORY_ID", "22"))),
            "defaultLanguage": lang,
            "defaultAudioLanguage": lang,
        },
        "status": status,
    }

    yt = _service()
    media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response, retries = None, 0
    while response is None:
        try:
            _, response = req.next_chunk()
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and retries < 5:
                retries += 1
                time.sleep(2 ** retries)
                continue
            raise
    vid = response["id"]
    print(f"[upload] Yüklendi: https://youtube.com/shorts/{vid} (durum: {status['privacyStatus']})", flush=True)
    return vid
