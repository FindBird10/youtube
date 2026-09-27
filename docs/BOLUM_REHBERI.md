# Bölüm yazma rehberi — BirdsVault

Kanal: **BirdsVault** · Konu: **genel ilginç bilgiler** · Dil: Türkçe · Günde **3** video.

Her Short, `episodes/` klasöründe tek bir JSON dosyasıdır. Dosya `main` dalına
gönderildiğinde GitHub Actions videoyu üretir ve YouTube'a yükler.

## Günlük akış

Her gün 3 bölüm yazılır ve `publish_at` ile zamanlanır (Türkiye saati = UTC+3):

| Sıra | Türkiye saati | `publish_at` (UTC) |
|---|---|---|
| 1 | 10:00 | `YYYY-AA-GGT07:00:00Z` |
| 2 | 15:00 | `YYYY-AA-GGT12:00:00Z` |
| 3 | 20:00 | `YYYY-AA-GGT17:00:00Z` |

Üç bölüm **farklı kategorilerden** olmalı. Kategoriler: hayvanlar, uzay, insan vücudu,
tarih, bilim, coğrafya/doğa olayları, teknoloji/icatlar, yemek/gündelik hayat.
Son 10 yayında sık geçen kategorileri o gün kullanma.

## Dosya adı

`episodes/YYYY-AA-GG-N-kisa-konu.json` — ör. `episodes/2026-09-29-1-ahtapot-kalp.json`
(N = gün içindeki sıra). Adı `_` ile başlayan dosyalar işlenmez (taslak/örnek için).

## Alanlar

| Alan | Zorunlu | Açıklama |
|---|---|---|
| `title` | ✔ | En fazla ~70 karakter. Merak uyandıran, abartısız, doğru. 1 emoji olabilir. |
| `description` | | 1–3 cümle + `Kaynak: ...`. `#Shorts` otomatik eklenir. |
| `tags` | | 5–10 etiket. |
| `scenes` | ✔ | 6–9 sahne. Her sahne: `text` (seslendirilecek metin) ve `search` (Pexels için **İngilizce** 2–3 kelime). |
| `publish_at` | | ISO UTC saat, yukarıdaki tabloya göre. |
| `voice` | | Varsayılan `tr-TR-AhmetNeural`. |
| `rate` | | Konuşma hızı, varsayılan `+5%` (doğal ve akıcı). Gerekmedikçe değiştirme. |
| `caption_style` | | `word` (varsayılan: tek kelime, beyaz, ekranın alt-ortasında) veya `group`. |
| `privacy` | | `private` / `unlisted` / `public`. Boşsa depo ayarı (varsayılan `private`). |
| `synthetic_media` | | Gerçekçi görünen yapay/değiştirilmiş görüntü varsa `true`. |
| `music` | | `false` ise arka plan müziği eklenmez. |
| `subject` | ✔ | Videonun ana öznesi, **İngilizce** tek kelime (ör. `octopus`, `honey`, `venus`). Görüntü seçiminde bu kelimeyi içeren videolar öne alınır. |
| `progress_bar` | | `false` ise üstteki ilerleme çubuğu kapatılır (varsayılan açık). |
| `show_hook` | | `true` ise ilk saniyelerde üstte başlık kutusu gösterilir (varsayılan kapalı). |

Seslendirme tüm sahneleri **tek parça** okur; sahneler yalnızca görüntünün değiştiği
yerleri belirler. Bu yüzden sahne metinleri birbirinin devamı gibi akmalı.

## İçerik kuralları

1. **Süre:** Toplam 90–130 kelime (≈35–50 sn). 60 saniyeyi geçme.
2. **Kanca:** İlk sahne tek başına merak uyandırmalı; selamlama, "bugün size..." yok.
3. **Doğruluk:** Her iddiayı güvenilir bir kaynakla (ansiklopedi, üniversite, NASA, NatGeo,
   Smithsonian vb.) web aramasıyla doğrula; kaynağı açıklamaya yaz. Emin olmadığın bilgiyi kullanma.
4. **Tekrar yok:** `state/published.json` ve mevcut `episodes/` dosyalarındaki konuları tekrarlama.
   Anlatım kalıbını da çeşitlendir (soru, liste, karşılaştırma, mini hikâye, "yanlış bilinen"...).
5. **Sahne metni:** Konuşma diliyle, akıcı cümleler. Sayıları rakamla yaz ("3 kalp").
   Arka arkaya çok kısa cümle dizme; her nokta seste duraksama yaratır. Birbirine bağlı
   fikirleri virgülle ya da "ve, ama, çünkü" ile tek cümlede birleştir.
6. **Görsel arama:** `search` somut ve görüntülenebilir olmalı ("octopus crawling seabed"),
   soyut olmamalı ("biology fact"). Her sahnede farklı bir görüntü iste.
   Sahnelerin çoğunda `search` **ana özneyle başlamalı** ("octopus ..."); izleyici konuyu
   görmeli. Özneden ancak metin gerçekten başka bir şeyi anlatıyorsa uzaklaş ve o zaman da
   gerçek çekim olarak kolay bulunacak somut bir şey iste. Çizim/animasyon isteyen kelimeler
   ("cartoon", "3d", "illustration") kullanma.
7. **Kapanış:** Son sahne yoruma veya takibe davet eden doğal bir soru.
8. Telif içeren isim, marka, gerçek kişiler hakkında iddia, tıbbi/finansal tavsiye yok.

Örnek için `episodes/_ornek.json` dosyasına bak.
