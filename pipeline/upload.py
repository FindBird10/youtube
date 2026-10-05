"""Hazır videoyu YouTube Data API v3 ile yükler.

Gerekli ortam değişkenleri (GitHub Secrets):
  YT_CLIENT_ID, YT_CLIENT_SECRET ve kanalın refresh token'ı
  (BirdsVault: YT_REFRESH_TOKEN, gaming: YT_REFRESH_TOKEN_GAMING, global: YT_REFRESH_TOKEN_GLOBAL)

Not: Google'ın denetiminden (audit) geçmemiş API projelerinden yüklenen
videolar YouTube tarafından zorunlu olarak "gizli" (private) tutulur.
"""
from __future__ import annotations

import datetime as dt
import os
import time
from pathlib import Path

from channels import CHANNELS, DEFAULT_CHANNEL, check_channel


class UploadLimit(RuntimeError):
    """Kanalın (hesabın) günlük video yükleme sınırı doldu (uploadLimitExceeded)."""


class WrongChannel(RuntimeError):
    """Token beklenen kanala ait değil. video_id doluysa video yanlış kanala yüklenmiştir."""

    def __init__(self, msg: str, video_id: str | None = None):
        super().__init__(msg)
        self.video_id = video_id

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


# Formata göre her videoya otomatik eklenen hashtag ve etiketler (bölümdekilerle birleştirilir)
BASE_HASHTAGS = {
    "tr": {"neden": ["#bilgi", "#ilginçbilgiler", "#neden", "#bilim"],
           "ne-olurdu": ["#neolurdu", "#bilim", "#ilginçbilgiler", "#uzay"],
           "gizem": ["#gizem", "#tarih", "#gizemliolaylar", "#çözülemeyengizemler"],
           "karanlik-tarih": ["#tarih", "#karanlıktarih", "#gerçekhikaye", "#gizem"],
           "turkiye-gizem": ["#gizem", "#türkiye", "#tarih", "#efsane"],
           "": ["#bilgi", "#ilginçbilgiler"]},
    "en": {"lore": [],
           "what-if": ["#whatif", "#science", "#facts"],
           "dark-history": ["#history", "#mystery", "#darkhistory"],
           "psychology": ["#psychology", "#brain", "#facts"],
           "business": ["#business", "#entrepreneur", "#history"],
           "": ["#facts", "#didyouknow"]},
}
BASE_TAGS = {
    "tr": ["gizem", "gizemli olaylar", "tarih", "shorts", "gerçek hikayeler"],
    "en": ["shorts"],
}
FORMAT_TAGS = {
    "neden": ["neden", "bilim", "merak edilenler", "günlük bilgiler", "yanlış bilinen doğrular"],
    "ne-olurdu": ["ne olurdu", "bilim", "senaryo", "uzay", "düşünce deneyi"],
    "gizem": ["gizem", "tarih", "çözülemeyen gizemler", "gizemli olaylar", "gerçek hikayeler"],
    "karanlik-tarih": ["karanlık tarih", "tarih", "gerçek hikaye", "tarihin karanlık yüzü", "ilginç tarih"],
    "turkiye-gizem": ["türkiye gizemleri", "gizem", "tarih", "anadolu efsaneleri", "gizemli yerler"],
    "lore": [],
    "what-if": ["what if", "science", "hypothetical", "space", "facts", "did you know"],
    "dark-history": ["dark history", "history", "unsolved mysteries", "true story", "creepy history"],
    "psychology": ["psychology", "psychology facts", "brain", "human behavior", "mind tricks"],
    "business": ["business", "business story", "entrepreneur", "company history", "success story"],
}
MAX_HASHTAGS = 8          # çok fazla hashtag spam sayılır (60'ı aşınca YouTube hepsini yok sayar)
TAGS_CHAR_LIMIT = 480     # YouTube sınırı 500 karakter (boşluklu etiketler tırnakla sayılır)


def _norm_hashtag(h: str) -> str:
    h = "".join(ch for ch in h.strip().lstrip("#") if ch.isalnum() or ch == "_")
    return f"#{h}" if h else ""


def build_hashtags(episode: dict) -> list[str]:
    lang = episode.get("language", "tr")
    base = BASE_HASHTAGS.get(lang, BASE_HASHTAGS["tr"])
    fmt = episode.get("format", "")
    out, seen = [], set()
    chan = CHANNELS.get(episode.get("_channel", DEFAULT_CHANNEL), CHANNELS[DEFAULT_CHANNEL])
    for h in ["#Shorts"] + list(episode.get("hashtags", [])) + base.get(fmt, base[""]) + chan["hashtags"]:
        h = _norm_hashtag(h)
        if h and h.lower() not in seen:
            seen.add(h.lower())
            out.append(h)
    return out[:MAX_HASHTAGS]


def build_tags(episode: dict) -> list[str]:
    lang = episode.get("language", "tr")
    chan = CHANNELS.get(episode.get("_channel", DEFAULT_CHANNEL), CHANNELS[DEFAULT_CHANNEL])
    cand = list(episode.get("tags", [])) + FORMAT_TAGS.get(episode.get("format", ""), []) \
        + chan["tags"] + BASE_TAGS.get(lang, BASE_TAGS["tr"])
    out, seen, used = [], set(), 0
    for t in cand:
        t = t.strip().lstrip("#").replace("<", "").replace(">", "")
        if not t or t.lower() in seen:
            continue
        cost = len(t) + (2 if " " in t else 0) + (1 if out else 0)
        if used + cost > TAGS_CHAR_LIMIT:
            continue
        seen.add(t.lower())
        out.append(t)
        used += cost
    return out


def _token_env(channel: str) -> str:
    return CHANNELS.get(channel, CHANNELS[DEFAULT_CHANNEL])["token_env"]


def find_existing(channel: str, title: str) -> str | None:
    """Kanalın herkese açık son videolarında (RSS) aynı başlık varsa video kimliğini döndürür.

    Kayıt kaybolursa (ör. yarıda kalan çalıştırma) aynı videonun ikinci kez yüklenmesini önler.
    Zamanlanmış/gizli videolar RSS'te görünmez.
    """
    import re
    import xml.etree.ElementTree as ET

    import requests

    cid = CHANNELS.get(channel, {}).get("channel_id")
    if not cid:
        return None
    try:
        r = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", timeout=20)
        r.raise_for_status()
        ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
        norm = lambda t: re.sub(r"\s+", " ", t or "").strip().lower()  # noqa: E731
        for e in ET.fromstring(r.content).findall("a:entry", ns):
            if norm(e.findtext("a:title", "", ns)) == norm(title[:100]):
                return e.findtext("yt:videoId", "", ns) or None
    except Exception as e:
        print(f"[upload] RSS kontrolü yapılamadı ({type(e).__name__}); devam ediliyor", flush=True)
    return None


def token_fingerprint(channel: str) -> str:
    """Token'ın kısa özeti (token'ın kendisi kaydedilmez)."""
    import hashlib

    tok = os.environ.get(_token_env(channel), "").strip()
    return hashlib.sha256(tok.encode()).hexdigest()[:16] if tok else ""


def have_credentials(channel: str = DEFAULT_CHANNEL) -> bool:
    return all(os.environ.get(k, "").strip() for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", _token_env(channel)))


def _service(channel: str = DEFAULT_CHANNEL):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(
        None,
        refresh_token=os.environ[_token_env(channel)].strip(),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YT_CLIENT_ID"].strip(),
        client_secret=os.environ["YT_CLIENT_SECRET"].strip(),
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload(video: Path, episode: dict) -> tuple[str, str]:
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    desc = episode.get("description", "").strip()
    if episode.get("_credits"):  # CC BY / CC BY-SA görseller için zorunlu atıf
        head = "Görseller (Wikimedia Commons):" if episode.get("language") == "tr" else "Images (Wikimedia Commons):"
        desc += "\n\n" + head + "\n" + "\n".join(f"• {c}" for c in episode["_credits"][:8])
    present = {w.lower() for w in desc.split() if w.startswith("#")}
    tags_line = " ".join(h for h in build_hashtags(episode) if h.lower() not in present)
    if tags_line:
        desc = (desc + "\n\n" + tags_line).strip()
    privacy = episode.get("privacy") or os.environ.get("YT_DEFAULT_PRIVACY", "private")
    status = {
        "privacyStatus": privacy,
        "selfDeclaredMadeForKids": bool(episode.get("made_for_kids", False)),
        "containsSyntheticMedia": bool(episode.get("synthetic_media", False)),
    }
    pub = episode.get("publish_at")
    if pub:
        when = dt.datetime.fromisoformat(pub.replace("Z", "+00:00"))
        if when.tzinfo is None:
            when = when.replace(tzinfo=dt.timezone.utc)
        if when > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=10):
            # Zamanlanmış yayın yalnızca "private" durumla çalışır
            status["privacyStatus"] = "private"
            status["publishAt"] = when.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            # Yayın saati geçmiş (ör. bölüm geç yazıldı): bekletmeden hemen herkese açık yayınla
            if not episode.get("privacy"):
                status["privacyStatus"] = "public"
            print(f"[upload] publish_at geçmişte ({pub}); hemen yayınlanıyor "
                  f"({status['privacyStatus']}).", flush=True)

    lang = episode.get("language", "tr")
    body = {
        "snippet": {
            "title": episode["title"][:100],
            "description": desc[:4900],
            "tags": build_tags(episode),
            "categoryId": str(episode.get("category_id") or CHANNELS.get(episode.get("_channel", DEFAULT_CHANNEL),
                                                                        CHANNELS[DEFAULT_CHANNEL])["category"]),
            "defaultLanguage": lang,
            "defaultAudioLanguage": lang,
        },
        "status": status,
    }

    ch = episode.get("_channel", DEFAULT_CHANNEL)
    yt = _service(ch)
    # Ön kontrol: token youtube.readonly iznine sahipse yüklemeden önce kanal adını doğrula
    try:
        items = yt.channels().list(part="snippet", mine=True).execute().get("items", [])
        if items:
            problem = check_channel(ch, items[0]["snippet"]["title"])
            if problem:
                raise WrongChannel(f"{ch} token'ı yanlış kanala ait: {problem}")
    except HttpError as e:
        if e.resp.status not in (401, 403):
            raise
        # Yalnızca upload izni var: kontrol yükleme yanıtıyla yapılacak
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
            if "uploadLimitExceeded" in str(e):
                raise UploadLimit(str(e)) from e
            raise
    vid = response["id"]
    channel = response.get("snippet", {}).get("channelTitle") or response.get("snippet", {}).get("channelId", "?")
    print(f"[upload] Yüklendi: https://youtube.com/shorts/{vid} kanal: {channel} "
          f"(durum: {status['privacyStatus']})", flush=True)
    problem = check_channel(ch, response.get("snippet", {}).get("channelTitle", ""))
    if problem:
        raise WrongChannel(f"{ch} videosu yanlış kanala yüklendi ({problem}). "
                           f"Studio'dan sil: https://youtube.com/shorts/{vid}", video_id=vid)
    return vid, channel
