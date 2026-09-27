# Bu repo

YouTube Shorts otomasyonu. Claude'un görevi genellikle yeni bölüm dosyaları yazmaktır:
`episodes/YYYY-AA-GG-konu.json`. `main` dalına gönderilen her bölümü GitHub Actions
(`.github/workflows/shorts.yml`) videoya çevirip YouTube'a yükler.

- Bölüm biçimi ve içerik kuralları: `docs/BOLUM_REHBERI.md` — yazmadan önce oku.
- Daha önce yayınlananlar: `state/published.json` (Actions günceller, elle düzenleme).
- Kanal dili Türkçe; `search` alanları İngilizce.
- Bu bulut ortamından YouTube/Pexels'e erişilemez; video üretimi ve yükleme yalnızca Actions'ta olur.
- Kod değişikliği yaparsan `python pipeline/make_video.py episodes/_ornek.json --offline` ile dene.
