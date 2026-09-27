# Bölüm yazma rehberi

Her Short, `episodes/` klasöründe tek bir JSON dosyasıdır. Dosya `main` dalına
gönderildiğinde GitHub Actions videoyu üretir ve YouTube'a yükler.

## Dosya adı

`episodes/YYYY-AA-GG-kisa-konu.json` — ör. `episodes/2026-09-29-ahtapot-kalp.json`.
Adı `_` ile başlayan dosyalar işlenmez (taslak/örnek için).

## Alanlar

| Alan | Zorunlu | Açıklama |
|---|---|---|
| `title` | ✔ | En fazla ~70 karakter. Merak uyandıran, abartısız, doğru. |
| `description` | | 1–3 cümle + kaynak. `#Shorts` otomatik eklenir. |
| `tags` | | 5–10 etiket. |
| `scenes` | ✔ | 6–10 sahne. Her sahne: `text` (seslendirilecek metin) ve `search` (Pexels için **İngilizce** 2–3 kelime). |
| `voice` | | Varsayılan `tr-TR-AhmetNeural`. Kadın sesi: `tr-TR-EmelNeural`. |
| `rate` | | Konuşma hızı, varsayılan `+8%`. |
| `privacy` | | `private` / `unlisted` / `public`. Boşsa depo ayarı (varsayılan `private`). |
| `publish_at` | | ISO saat (ör. `2026-09-29T15:00:00Z`) — zamanlanmış yayın. |
| `synthetic_media` | | Gerçekçi görünen yapay/değiştirilmiş görüntü varsa `true`. |
| `music` | | `false` ise arka plan müziği eklenmez. |

## İçerik kuralları

1. **Süre:** Toplam 90–130 kelime (≈35–55 sn). 60 saniyeyi geçme.
2. **Kanca:** İlk sahne tek başına merak uyandırmalı; selamlama, "bugün size..." yok.
3. **Doğruluk:** Her iddia güvenilir bir kaynakla doğrulanmış olmalı; kaynağı açıklamaya yaz.
   Emin olmadığın bilgiyi kullanma.
4. **Tekrar yok:** `state/published.json` ve mevcut `episodes/` dosyalarındaki konuları tekrarlama.
   Anlatım kalıbını da çeşitlendir (soru, liste, karşılaştırma, mini hikâye...).
5. **Sahne metni:** Kısa, konuşma diliyle cümleler. Rakamları yazıyla değil rakamla yaz ("3 kalp").
6. **Görsel arama:** `search` somut ve görüntülenebilir olmalı ("octopus crawling seabed"),
   soyut olmamalı ("biology fact").
7. **Kapanış:** Son sahne yoruma veya takibe davet eden doğal bir soru.
8. Telif içeren isim, marka, gerçek kişiler hakkında iddia, tıbbi/finansal tavsiye yok.

Örnek için `episodes/_ornek.json` dosyasına bak.
