# Bölüm yazma rehberi — BirdsVault

Kanal: **BirdsVault** · Dil: Türkçe · Günde **3** video · Üç sabit format:
**"Neden?" soruları**, **"Ne olurdu?" senaryoları**, **gizemli gerçek hikâyeler**.

Amaç rastgele bilgi vermek değil: her video, insanların gerçekten merak ettiği **tek bir
soruya** cevap verir ya da tek bir hikâyeyi anlatır ve izleyiciyi cevaba kadar tutar.

Her Short, `episodes/` klasöründe tek bir JSON dosyasıdır. Dosya `main` dalına
gönderildiğinde GitHub Actions videoyu üretir ve YouTube'a yükler.

## Günlük akış

Her gün 3 bölüm yazılır ve `publish_at` ile zamanlanır (Türkiye saati = UTC+3):

| Sıra | Türkiye saati | `publish_at` (UTC) | Format (`format` alanı) |
|---|---|---|---|
| 1 | 10:00 | `YYYY-AA-GGT07:00:00Z` | "Neden?" sorusu (`neden`) |
| 2 | 15:00 | `YYYY-AA-GGT12:00:00Z` | "Ne olurdu?" senaryosu (`ne-olurdu`) |
| 3 | 20:00 | `YYYY-AA-GGT17:00:00Z` | Gizemli gerçek hikâye (`gizem`) |

## Formatlar

### 1. "Neden?" soruları (`neden`)
Herkesin bir kez aklına gelmiş ama cevabını bilmediği gündelik sorular:
"Uçaklar neden beyaz?", "Neden esneriz ve esneme neden bulaşıcı?", "Deniz suyu neden tuzlu?".
- **Başlık = soru.** Kanca: soruyu sor + çoğu kişinin yanlış bildiği cevabı söyle
  ("Çoğu kişi … sanıyor ama asıl sebep bambaşka.").
- Akış: soru → yaygın yanlış cevap → gerçek sebep (adım adım) → şaşırtıcı bir ek bilgi → yorum sorusu.
- Cevabı ilk 5 saniyede verme; ortaya doğru ver.

### 2. "Ne olurdu?" senaryoları (`ne-olurdu`)
Gerçek bilime dayanan düşünce deneyleri: "Dünya 1 saniyeliğine dönmeyi bıraksa?",
"Ay yok olsa?", "Bir yıl hiç uyumasan?", "Okyanuslar buharlaşsa?".
- **Başlık = senaryo sorusu.** Kanca: en çarpıcı sonucu ilk cümlede ima et.
- Akış **zaman çizelgesiyle tırmanır**: "İlk saniyede… 1 saat sonra… 1 hafta sonra… 1 yıl sonra…".
  Her adım bir öncekinden daha çarpıcı olmalı.
- Sonuçlar bilimsel kaynaklara dayanmalı (NASA, üniversiteler, ciddi bilim yayınları);
  kesin olmayanı "bilim insanlarına göre muhtemelen" diye söyle, uydurma.

### 3. Gizemli gerçek hikâyeler (`gizem`)
Belgelenmiş, gerçekten yaşanmış tuhaf olaylar: çözülememiş vakalar, açıklanamayan sinyaller,
kayıp gemiler, tarihin garip kazaları (ör. Dyatlov Geçidi, Wow! sinyali, 1518 dans salgını,
Mary Celeste, Tunguska patlaması).
- **Soğuk açılış:** hikâyenin en tuhaf anıyla başla ("1518'de Strazburg'da bir kadın sokakta
  dans etmeye başladı ve 6 gün durmadı.").
- Akış: olay → neden tuhaf → ortaya atılan açıklamalar → hâlâ cevapsız kalan kısım → yorum sorusu
  ("Sence ne oldu?").
- Belgelenmiş gerçeklerle teorileri açıkça ayır. Kan, vahşet ve ayrıntılı ölüm tarifleri yok;
  kurbanlara saygılı dil kullan. Yaşayan kişiler hakkında suçlama yok.

## Konu bulma

Konu seçerken "ilginç olur" diye tahmin etme; **insanların zaten merak ettiğini gösteren**
kanıt ara (WebSearch):
- Google'da sık sorulan sorular / "insanlar bunu da sordu" kutuları, Reddit'te çok oy almış
  r/explainlikeimfive, r/NoStupidQuestions (`neden`), r/whatif, r/askscience (`ne-olurdu`),
  r/UnresolvedMysteries, r/HistoryMemes (`gizem`) başlıkları.
- O gün gündemde olan bir olay (tutulma, deprem, uzay görevi, yıldönümü) bir formata
  uyuyorsa ona öncelik ver.
- Türk izleyiciye yakın örnekler (Türkiye'den bir yer, olay, gündelik alışkanlık) bonus.
Seçtiğin konunun neden ilgi çekeceğini commit mesajında bir cümleyle yaz.

## Dosya adı

`episodes/YYYY-AA-GG-N-kisa-konu.json` — ör. `episodes/2026-09-29-1-ahtapot-kalp.json`
(N = gün içindeki sıra). Adı `_` ile başlayan dosyalar işlenmez (taslak/örnek için).

## Alanlar

| Alan | Zorunlu | Açıklama |
|---|---|---|
| `title` | ✔ | En fazla ~70 karakter. Merak uyandıran, abartısız, doğru. 1 emoji olabilir. |
| `format` | ✔ | `neden`, `ne-olurdu` veya `gizem` (günlük akış tablosuna göre). |
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
2. **Kanca ve tutma:** İlk cümle tek başına merak uyandırmalı; selamlama, "bugün size..." yok.
   İlk 3 saniyede bir soru/boşluk aç, cevabını sona doğru ver. Ortada bir kez yeniden kanca at
   ("Ama asıl tuhaf olan kısım…"). Dolgu cümle yok; her cümle bir sonrakini merak ettirmeli.
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
7. **Kapanış:** Son sahne yoruma davet eden doğal bir soru ("Sence ne oldu?", "Sen olsan…?").
8. Telif içeren isim/marka, yaşayan kişiler hakkında doğrulanmamış iddia, tıbbi/finansal tavsiye yok.

Örnek için `episodes/_ornek.json` dosyasına bak.
