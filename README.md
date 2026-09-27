# YouTube Shorts otomasyonu

Bölüm dosyası (`episodes/*.json`) → seslendirme → stok görüntü → kelime kelime altyazı → dikey video → YouTube.

```
Claude (zamanlanmış görev)          GitHub Actions
  konu + senaryo yazar   ──push──▶   Edge-TTS seslendirme
  episodes/…json                     Pexels dikey stok video
                                     FFmpeg montaj + altyazı
                                     YouTube Data API yükleme
                                     state/published.json kaydı
```

## Kurulum (bir kez)

### 1. Pexels anahtarı (ücretsiz, 2 dk)
<https://www.pexels.com/api/> → hesap aç → **Your API Key**. Anahtarı kopyala.

### 2. Google Cloud (yaklaşık 10 dk)
1. <https://console.cloud.google.com/> → yeni proje oluştur (ör. `shorts-otomasyon`).
2. **APIs & Services → Library** → *YouTube Data API v3* → **Enable**.
3. **Google Auth Platform** (eski adı *OAuth consent screen*):
   - Uygulama adı ve e-posta gir, kullanıcı türü **External**.
   - **Audience** bölümünde **Publish app** ile durumu **In production** yap.
     *Testing* modunda kalırsa izin 7 günde düşer ve otomasyon durur.
     "Doğrulanmamış uygulama" uyarısı kendi kullanımın için sorun değil.
4. **Clients → Create client** → tür: **Web application** →
   *Authorized redirect URIs* kısmına şunu ekle: `https://developers.google.com/oauthplayground`
   → oluştur, **Client ID** ve **Client secret**'ı kopyala.

### 3. Kalıcı izin anahtarı (refresh token)
1. <https://developers.google.com/oauthplayground> aç.
2. Sağ üstteki ⚙️ → **Use your own OAuth credentials** → Client ID ve secret'ı yapıştır.
3. Soldaki kutuya şunu yaz ve **Authorize APIs**'e bas:
   `https://www.googleapis.com/auth/youtube.upload`
4. Kanalın bağlı olduğu Google hesabını seç (kanal bir marka hesabıysa onu seç), izin ver.
5. **Exchange authorization code for tokens** → çıkan **Refresh token**'ı kopyala.

> Python kullanmayı tercih edersen: Desktop app türünde istemci oluşturup
> `python tools/get_refresh_token.py` çalıştırabilirsin.

### 4. GitHub Secrets
Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Ad | Değer |
|---|---|
| `PEXELS_API_KEY` | Pexels anahtarı |
| `YT_CLIENT_ID` | Google Client ID |
| `YT_CLIENT_SECRET` | Google Client secret |
| `YT_REFRESH_TOKEN` | Playground'dan aldığın refresh token |

İsteğe bağlı **Variables** (aynı sayfada *Variables* sekmesi):
`YT_DEFAULT_PRIVACY` (`private`/`unlisted`/`public`, varsayılan `private`), `MAX_PER_RUN` (varsayılan 3).

### 5. İlk test
**Actions → Shorts üret ve yükle → Run workflow** → `episode` kutusuna `_ornek` yaz →
*upload* işaretini kaldır → çalıştır. Bitince sayfanın altındaki **Artifacts**'tan videoyu indirip izle.

## Önemli: API denetimi
Google'ın denetiminden geçmemiş projelerden yüklenen videolar YouTube tarafından
**gizli** tutulur. Denetim onaylanana kadar videoları Studio'dan elle "Herkese açık"
yaparsın (bu aynı zamanda iyi bir kalite kontrolüdür). Herkese açık otomatik yayın için:
<https://support.google.com/youtube/contact/yt_api_form> (YouTube API Services – Audit and Quota Extension).

## Arka plan müziği
Telifsiz parçaları (ör. YouTube Studio → Ses Kitaplığı) `assets/music/` klasörüne koy;
her videoda biri rastgele, kısık sesle eklenir.

## Yerelde deneme
```bash
pip install -r requirements.txt   # + ffmpeg
python pipeline/make_video.py episodes/_ornek.json            # gerçek ses + Pexels
python pipeline/make_video.py episodes/_ornek.json --offline  # internetsiz hızlı test
```

Bölüm yazma kuralları: [docs/BOLUM_REHBERI.md](docs/BOLUM_REHBERI.md)
