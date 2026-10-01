"""Kanal tanımları. Bölümün kanalı, bulunduğu klasörden anlaşılır:

  episodes/*.json          → birdsvault (Türkçe bilgi kanalı)
  episodes/gaming/*.json   → gaming     (İngilizce oyun karakteri hikâyeleri)
  episodes/global/*.json   → global     (İngilizce genel kanal)

Her kanal kendi YouTube refresh token'ı ile yüklenir (aynı OAuth istemcisi).
"""
from __future__ import annotations

from pathlib import Path

CHANNELS: dict[str, dict] = {
    "birdsvault": {
        "token_env": "YT_REFRESH_TOKEN",
        "category": "27",                     # Eğitim
        "defaults": {"language": "tr"},
        "hashtags": [],
        "tags": ["BirdsVault"],
    },
    "gaming": {
        "token_env": "YT_REFRESH_TOKEN_GAMING",
        "category": "20",                     # Oyun
        "defaults": {"language": "en", "style": "cinematic", "format": "lore"},
        "hashtags": ["#gaming", "#lore", "#videogames"],
        "tags": ["game lore", "video game story", "gaming", "character story", "video games"],
    },
    "global": {
        "token_env": "YT_REFRESH_TOKEN_GLOBAL",
        "category": "27",
        "defaults": {"language": "en", "style": "global"},
        "hashtags": [],
        "tags": [],
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
