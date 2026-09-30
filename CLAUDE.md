# Bu repo

**BirdsVault** YouTube kanalı için Shorts otomasyonu (Türkçe, genel ilginç bilgiler, günde 3 video).
Claude'un görevi genellikle yeni bölüm dosyaları yazmaktır: `episodes/YYYY-AA-GG-N-konu.json`.
`main` dalına gönderilen her bölümü GitHub Actions (`.github/workflows/shorts.yml`) videoya
çevirip YouTube'a yükler.

- Bölüm biçimi, günlük saatler ve içerik kuralları: `docs/BOLUM_REHBERI.md` — yazmadan önce oku.
- Daha önce yayınlananlar: `state/published.json` (Actions günceller, elle düzenleme).
- Kanal dili Türkçe; `search` alanları İngilizce.
- Bu bulut ortamından YouTube/Pexels'e erişilemez; video üretimi ve yükleme yalnızca Actions'ta olur.
- Kod değişikliği yaparsan `python pipeline/make_video.py episodes/_ornek.json --offline` ile dene.
- Commit mesajlarını Türkçe yaz; `build/` klasörünü commit etme.
- Görünüm stilleri (`birdsvault`, `global`, `cinematic`) ve kullanıcının stil tercihleri: `docs/STILLER.md`.
