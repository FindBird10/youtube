"""Aynı metni farklı Azure sesleriyle seslendirip karşılaştırma örnekleri üretir.

GitHub Actions'ta 'Ses örnekleri' iş akışıyla çalışır (AZURE_SPEECH_KEY gerekir);
çıktılar voice-samples dalına konur.

  python tools/voice_samples.py episodes/_test_ucak_neden_beyaz.json samples/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
from make_video import _azure_tts  # noqa: E402

# (dosya adı, ses, hız, perde)
VOICES = [
    ("01_ahmet_simdiki", "tr-TR-AhmetNeural", "+5%", "+0%"),
    ("02_ahmet_canli", "tr-TR-AhmetNeural", "+12%", "+6%"),
    ("03_emel", "tr-TR-EmelNeural", "+8%", "+0%"),
    ("04_andrew_cokdilli", "en-US-AndrewMultilingualNeural", "+8%", "+0%"),
    ("05_brian_cokdilli", "en-US-BrianMultilingualNeural", "+8%", "+0%"),
    ("06_florian_cokdilli", "de-DE-FlorianMultilingualNeural", "+8%", "+0%"),
    ("07_ava_cokdilli", "en-US-AvaMultilingualNeural", "+8%", "+0%"),
    ("08_andrew_hd", "en-US-Andrew:DragonHDLatestNeural", "+5%", "+0%"),
    ("09_ava_hd", "en-US-Ava:DragonHDLatestNeural", "+5%", "+0%"),
]


# Oyun haberleri kanalı için enerjik İngilizce sesler: (ad, ses, hız, perde, stil)
NEWS_VOICES = [
    ("01_brian_hizli", "en-US-BrianMultilingualNeural", "+14%", "+3%", ""),
    ("02_andrew_hizli", "en-US-AndrewMultilingualNeural", "+14%", "+2%", ""),
    ("03_davis_heyecanli", "en-US-DavisNeural", "+10%", "+0%", "excited"),
    ("04_tony_heyecanli", "en-US-TonyNeural", "+10%", "+0%", "excited"),
    ("05_jason_heyecanli", "en-US-JasonNeural", "+10%", "+0%", "excited"),
    ("06_guy_haberci", "en-US-GuyNeural", "+10%", "+0%", "newscast"),
    ("07_andrew_hd", "en-US-Andrew:DragonHDLatestNeural", "+10%", "+0%", ""),
]
NEWS_TEXT = ("Okay, gamers, this is big. Yesterday a brand new trailer dropped, and fans already found "
             "three secrets hiding in the background. But the craziest part? Nobody noticed the last one "
             "until this morning. Here's everything you need to know in thirty seconds.")


def main() -> None:
    import os

    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    if os.environ.get("VOICE_SET") == "news":
        text, voices, lang = NEWS_TEXT, NEWS_VOICES, "en-US"
    else:
        ep = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        text = " ".join(s["text"] for s in ep["scenes"][:4])
        voices, lang = [v + ("",) for v in VOICES], "tr-TR"
    report = [f"Metin: {text}\n"]
    for name, voice, rate, pitch, style in voices:
        try:
            _azure_tts(text, voice, rate, out / f"{name}.mp3", pitch=pitch, speak_lang=lang, style=style,
                       style_degree=1.4 if style else 1.0)
            report.append(f"OK    {name}: {voice} hız {rate} perde {pitch} stil {style or '-'}")
        except Exception as e:
            (out / f"{name}.mp3").unlink(missing_ok=True)
            report.append(f"HATA  {name}: {voice} -> {str(e)[:160]}")
        print(report[-1], flush=True)
    (out / "RAPOR.txt").write_text("\n".join(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
