"""Kanal tanımları. Bölümün kanalı, bulunduğu klasörden anlaşılır:

  episodes/*.json          → birdsvault (Türkçe gizem ve karanlık tarih)
  episodes/gaming/*.json   → gaming     (İngilizce oyun karakteri hikâyeleri)
  episodes/global/*.json   → global     (İngilizce genel kanal)
  episodes/news/*.json     → news       (İngilizce günlük oyun haberleri)

Her kanal kendi YouTube refresh token'ı ile yüklenir (aynı OAuth istemcisi).
"""
from __future__ import annotations

from pathlib import Path

CHANNELS: dict[str, dict] = {
    "birdsvault": {
        "token_env": "YT_REFRESH_TOKEN",
        "expect_title": "BirdsVault",        # yükleme bu adlı kanala gitmezse durdurulur
        "channel_id": "UC5w1LBA7sE_U9taLW0kuKYA",
        "category": "27",                     # Eğitim
        # 5 Eki: konu gizem ve karanlık tarih; görünüm ve ses gaming kanalıyla aynı
        "defaults": {"language": "tr", "style": "cinematic", "format": "gizem"},
        "hashtags": [],
        "tags": ["BirdsVault"],
    },
    "gaming": {
        "token_env": "YT_REFRESH_TOKEN_GAMING",
        "expect_title": "BirdsVaultGaming",
        "channel_id": "UC-Ady9DQ8uTMpZfV_GeDKIA",  # aynı başlıklı video var mı kontrolü (RSS)
        "category": "20",                     # Oyun
        "defaults": {"language": "en", "style": "cinematic", "format": "lore"},
        "hashtags": ["#gaming", "#lore", "#videogames"],
        "tags": ["game lore", "video game story", "gaming", "character story", "video games"],
    },
    "global": {
        "token_env": "YT_REFRESH_TOKEN_GLOBAL",
        "expect_title": "BirdsVaultGlobal",
        "channel_id": "UCp2rjdN1M1z0GMJ2Gshzdfw",
        "category": "27",
        "defaults": {"language": "en", "style": "global"},
        "hashtags": [],
        "tags": [],
    },
    "news": {
        "token_env": "YT_REFRESH_TOKEN_NEWS",
        "expect_title": None,                # kanal adı belli olunca yaz
        "channel_id": None,
        "category": "20",                     # Oyun
        "defaults": {"language": "en", "style": "cinematic", "format": "news"},   # gaming ile aynı görünüm
        "max_age_hours": 12,                  # yayın saatinden 12 saat sonra hâlâ yüklenmediyse bayat haber: atla
        "hashtags": ["#gamingnews", "#gaming"],
        "tags": ["gaming news", "video game news", "gaming", "new games", "game news today"],
    },
}
DEFAULT_CHANNEL = "birdsvault"


def channel_of(path: Path, episodes_dir: Path) -> str:
    """Bölüm dosyasının kanalı (klasör adına göre)."""
    try:
        rel = path.resolve().relative_to(episodes_dir.resolve())
    except ValueError:
        return DEFAULT_CHANNEL
    if len(rel.parts) > 1 and rel.parts[0] in CHANNELS:
        return rel.parts[0]
    return DEFAULT_CHANNEL


def episode_key(channel: str, stem: str) -> str:
    """state/published.json'daki benzersiz anahtar (BirdsVault için eski biçim korunur)."""
    return stem if channel == DEFAULT_CHANNEL else f"{channel}/{stem}"


def check_channel(channel: str, title: str) -> str | None:
    """Yüklemenin gittiği kanal adı yanlışsa açıklama döndürür, doğruysa None."""
    t = (title or "").strip().lower()
    exp = CHANNELS[channel].get("expect_title")
    if exp and t != exp.lower():
        return f"'{title}' kanalına gitti, beklenen '{exp}'"
    for other, cfg in CHANNELS.items():
        if other != channel and cfg.get("expect_title") and t == cfg["expect_title"].lower():
            return f"'{title}' kanalına gitti; bu {other} kanalı"
    return None
