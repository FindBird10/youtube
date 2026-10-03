# Bu repo

Dört YouTube kanalı için Shorts otomasyonu; Claude bölüm dosyalarını yazar, GitHub Actions
(`.github/workflows/shorts.yml`) videoya çevirip ilgili kanala yükler. Kanal, bölümün klasöründen anlaşılır
(`pipeline/channels.py`):

| Kanal | Klasör | Dil | Rehber | Token secret'ı |
|---|---|---|---|---|
| **BirdsVault** (genel ilginç bilgiler) | `episodes/*.json` | Türkçe | `docs/BOLUM_REHBERI.md` | `YT_REFRESH_TOKEN` |
| **Gaming** (oyun karakteri hikâyeleri) | `episodes/gaming/` | İngilizce | `docs/GAMING_REHBERI.md` | `YT_REFRESH_TOKEN_GAMING` |
| **Global** (what-if, psikoloji, iş, karanlık tarih) | `episodes/global/` | İngilizce | `docs/GLOBAL_REHBERI.md` | `YT_REFRESH_TOKEN_GLOBAL` |
| **News** (günlük oyun haberleri) | `episodes/news/` | İngilizce | `docs/NEWS_REHBERI.md` | `YT_REFRESH_TOKEN_NEWS` |

Token'ı tanımlı olmayan kanalın bölümleri yüklenmez, bekletilir. Her kanal günde 3 video.

- Bölüm biçimi, günlük saatler ve içerik kuralları: ilgili kanalın rehberi — yazmadan önce oku.
- Daha önce yayınlananlar: `state/published.json` (Actions günceller, elle düzenleme).
- BirdsVault dili Türkçe, diğer iki kanal İngilizce; `search` alanları her zaman İngilizce.
- Bu bulut ortamından YouTube/Pexels'e erişilemez; video üretimi ve yükleme yalnızca Actions'ta olur.
- Kod değişikliği yaparsan `python pipeline/make_video.py episodes/_ornek.json --offline` ile dene.
- Commit mesajlarını Türkçe yaz; `build/` klasörünü commit etme.
- Görünüm stilleri (`birdsvault`, `global`, `cinematic`) ve kullanıcının stil tercihleri: `docs/STILLER.md`.
