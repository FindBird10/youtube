# Bölüm yazma rehberi — BirdsVault

Kanal: **BirdsVault** · Dil: Türkçe · Günde **3** video · Üç sabit format:
**"Neden?" soruları**, **"Ne olurdu?" senaryoları**, **gizemli gerçek hikâyeler**.

Amaç rastgele bilgi vermek değil: her video, insanların gerçekten merak ettiği **tek bir
soruya** cevap verir ya da tek bir hikâyeyi anlatır ve izleyiciyi cevaba kadar tutar.

Her Short, `episodes/` klasöründe tek bir JSON dosyasıdır. Dosya `main` dalına
gönderildiğinde GitHub Actions videoyu üretir ve YouTube'a yükler.

## Günlük akış

Her gün 3 bölüm yazılır ve `publish_at` ile zamanlanır (Türkiye saati = UTC+3).
Saatler Shorts izlenme verilerine göre seçildi: öğle arası ve akşam 18:00–23:00 en güçlü,
12:00–17:00 arası en zayıf pencere; hafta sonu sabah geç saatler de güçlü.

| Sıra | Format (`format` alanı) | Hafta içi (Pzt–Cum) TR → `publish_at` | Hafta sonu (Cmt–Paz) TR → `publish_at` |
|---|---|---|---|
| 1 | "Neden?" sorusu (`neden`) | 12:30 → `YYYY-AA-GGT09:30:00Z` | 11:30 → `YYYY-AA-GGT08:30:00Z` |
| 2 | "Ne olurdu?" senaryosu (`ne-olurdu`) | 18:30 → `YYYY-AA-GGT15:30:00Z` | 18:30 → `YYYY-AA-GGT15:30:00Z` |
| 3 | Gizemli gerçek hikâye (`gizem`) | 21:30 → `YYYY-AA-GGT18:30:00Z` | 21:30 → `YYYY-AA-GGT18:30:00Z` |

## Formatlar

### 1. "Neden?" soruları (`neden`)
Herkesin bir kez aklına gelmiş ama cevabını bilmediği gündelik sorular:
"Uçaklar neden beyaz?", "Neden esneriz ve esneme neden bulaşıcı?", "Deniz suyu neden tuzlu?".
- **Başlık = soru.** Kanca: soruyu sor + çoğu kişinin yanlış bildiği cevabı söyle
  ("Çoğu kişi … sanıyor ama asıl sebep bambaşka.").
- Akış: soru → yaygın yanlış cevap → gerçek sebep (kısaca) → şaşırtıcı bir ek bilgi → döngü cümlesi.
- Cevabı ilk 5 saniyede verme; ortaya doğru ver.

### 2. "Ne olurdu?" senaryoları (`ne-olurdu`)
Gerçek bilime dayanan düşünce deneyleri: "Dünya 1 saniyeliğine dönmeyi bıraksa?",
"Ay yok olsa?", "Bir yıl hiç uyumasan?", "Okyanuslar buharlaşsa?".
- **Başlık = senaryo sorusu.** Kanca: en çarpıcı sonucu ilk cümlede ima et.
- Akış **zaman çizelgesiyle tırmanır**: "İlk saniyede… 1 hafta sonra… 1 yıl sonra…" (en fazla 3–4 adım).
  Her adım bir öncekinden daha çarpıcı olmalı.
- Sonuçlar bilimsel kaynaklara dayanmalı (NASA, üniversiteler, ciddi bilim yayınları);
  kesin olmayanı "bilim insanlarına göre muhtemelen" diye söyle, uydurma.

### 3. Gizemli gerçek hikâyeler (`gizem`)
Belgelenmiş, gerçekten yaşanmış tuhaf olaylar: çözülememiş vakalar, açıklanamayan sinyaller,
kayıp gemiler, tarihin garip kazaları (ör. Dyatlov Geçidi, Wow! sinyali, 1518 dans salgını,
Mary Celeste, Tunguska patlaması).
- **Soğuk açılış:** hikâyenin en tuhaf anıyla başla, tarih/yer sonra gelsin
  ("Bir kadın sokakta dans etmeye başladı ve günlerce duramadı." — "14 Temmuz 1518'de
  Strazburg'da…" diye başlama).
- Akış: olay → neden tuhaf → en güçlü 1–2 açıklama → hâlâ cevapsız kalan kısım → döngü cümlesi.
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
| `title` | ✔ | **En fazla ~50 karakter** (Shorts akışında uzun başlık kesilir). Merak uyandıran, abartısız, doğru; cevabı vermez ve ilk cümlenin aynısı olmaz. 1 emoji olabilir. |
| `format` | ✔ | `neden`, `ne-olurdu` veya `gizem` (günlük akış tablosuna göre). |
| `description` | | İlk satır yorum sorusu ("Sence ne oldu? 👇"), sonra 1–2 cümle + `Kaynak: ...`. `#Shorts` otomatik eklenir. |
| `tags` | | 5–10 etiket. |
| `scenes` | ✔ | 4–6 sahne. Her sahne: `text` (seslendirilecek metin) ve `search` (Pexels için **İngilizce** 2–3 kelime). |
| `publish_at` | | ISO UTC saat, yukarıdaki tabloya göre. |
| `voice` | | **Yazma.** Ses formata göre otomatik seçilir: `neden`/`ne-olurdu` → Brian, `gizem` → Andrew (Azure çok dilli sesler, Türkçe okur). |
| `rate` | | **Yazma.** Konuşma hızı sese göre otomatik (+8%). |
| `caption_style` | | `group` (varsayılan: 2–3 kelimelik beyaz satır, o an söylenen kelime sarı yanar; ekranın alt-ortasında) veya `word` (tek kelime). |
| `privacy` | | `private` / `unlisted` / `public`. Boşsa depo ayarı (varsayılan `private`). |
| `synthetic_media` | | Gerçekçi görünen yapay/değiştirilmiş görüntü varsa `true`. |
| `music` | | `false` ise arka plan müziği eklenmez. |
| `subject` | ✔ | Videonun ana öznesi, **İngilizce** tek kelime (ör. `octopus`, `honey`, `venus`). Görüntü seçiminde bu kelimeyi içeren videolar öne alınır. |
| `progress_bar` | | `false` ise üstteki ilerleme çubuğu kapatılır (varsayılan açık). |
| `show_hook` | | `true` ise ilk saniyelerde üstte başlık kutusu gösterilir (varsayılan kapalı). |

Seslendirme tüm sahneleri **tek parça** okur; sahneler yalnızca görüntünün değiştiği
yerleri belirler. Bu yüzden sahne metinleri birbirinin devamı gibi akmalı.

## İçerik kuralları

1. **Süre:** Toplam **55–85 kelime** (≈22–33 sn), asla 90'ı geçme. Shorts akışında yeni bir
   kanal için en önemli ölçü izlenme yüzdesi; kısa ve tamamı izlenen video, uzun ve yarıda
   bırakılan videodan çok daha fazla gösterilir. Bir videoya tek fikir: yan bilgileri at.
2. **Kanca ve tutma:** İlk cümle **en fazla 10 kelime** ve tek başına kaydırmayı durdurmalı:
   en şaşırtıcı iddia/an doğrudan söylenir. Selamlama, "bugün size…", "biliyor muydunuz",
   tarih/yer girişi yok. Cevabı sona doğru ver; ortada bir kez yeniden kanca at
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
7. **Kapanış = döngü:** Son cümle bitmemiş gibi kalır ve ilk cümleye bağlanır; video başa
   sardığında anlatım kesintisiz devam eder ve izleyici farkında olmadan ikinci kez izler
   (ör. son: "…ve bütün bunların sebebi şu:" → ilk: "Ahtapotun tam 3 kalbi var…").
   "Yorumlara yaz", "abone ol" gibi kapanışlar yok; yorum sorusu açıklamanın ilk satırına.
8. Telif içeren isim/marka, yaşayan kişiler hakkında doğrulanmamış iddia, tıbbi/finansal tavsiye yok.

Örnek için `episodes/_ornek.json` dosyasına bak.
