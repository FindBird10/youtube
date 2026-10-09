# Bölüm yazma rehberi — Global kanal (İngilizce)

Kanal: dünya geneline **İngilizce** merak videoları · Günde **3** video · Bölümler
`episodes/global/` klasörüne yazılır; dil (`en`) ve stil (`global`: açılış başlık kartı, mor kutulu
altyazı, hızlı kesmeler) klasörden otomatik gelir.

## Performans notları (7 Ekim 2026) — önce bunu oku

İlk 21 videonun izlenmeleri (1–5 günlük): çoğu 0–20 izlenmede kaldı, yalnızca şunlar itildi:
"It snowed in June" / Yaz Olmayan Yıl **499**, Dünya dönmeyi bıraksa **272**, uyurken vücudun sıçraması
(hypnic jerk) **164**, Yellowstone patlasa **112 (ilk 1 saatte)**, 1859 güneş fırtınası **55**.
Aynı "uzayda skafandrasız" videosu yanlışlıkla gaming kanalına yüklendiğinde **1.400**, burada **16** aldı:
sorun büyük ölçüde içerikte değil, kanalın henüz belirli bir kitlesi olmamasında. Kitleyi bulmak için konu
yelpazesi daraltıldı:

- **Kazanan tema:** bütün gezegeni ya da *senin vücudunu* etkileyen fiziksel, büyük ölçekli olay.
  "Dünya / Güneş / Ay / volkan / uzay / senin vücudun" — herkesin kendini koyabileceği bir sonuç.
- **Ölü formatlar:** `business` (Blockbuster 7, Kodak 0, IKEA 7) **kaldırıldı**. Soyut beyin konuları
  (doorway effect 11, earworm 5) zayıf; `psychology` yerine fiziksel his anlatan `body` geldi.
- **Yerel felaket hikâyeleri** (Boston pekmez seli 2, Nyos Gölü 1, Peshtigo 6, Radyum Kızları 8,
  dans salgını 4) tutmadı. Karanlık tarih slotunda yalnızca **dünyayı/milyonları etkilemiş, tuhaf ve
  büyük ölçekli** olaylar (Yaz Olmayan Yıl gibi).
- **Kanca:** kazananların ilk cümlesi ya çok kısa ve imkânsız bir görüntü ("It snowed in June.") ya da
  "you" ile başlayan fiziksel sonuç ("…you'd fly at 1,000 mph", "…you'd see ash in Miami",
  "Your whole body jolts…"). Soyut ya da kurumsal ilk cümle yok.

## Formatlar ve günlük akış

| Sıra | Format (`format`) | ABD Doğu saati (ET) |
|---|---|---|
| 1 | `what-if` — Dünya/uzay/doğa ölçeğinde bilime dayalı "What if…?" | 11:00 |
| 2 | `body` — senin vücudunun yaptığı ya da başına gelebilecek fiziksel şey | 15:00 |
| 3 | `dark-history` — gerçek, büyük ölçekli ve tuhaf felaket/doğa olayı | 19:00 |

`publish_at` UTC yazılır; ET saatini `zoneinfo("America/New_York")` ile çevir.
Ses formata göre otomatik (Brian: what-if/body, Andrew: dark-history).

### `what-if`
Gezegen ve uzay ölçeğinde senaryolar: "What if Earth stopped spinning?", "What if Yellowstone erupted?",
"What if a solar storm hit today?", "What if the oceans drained?". İlk cümle izleyicinin başına gelecek en
çarpıcı fiziksel sonucu söyler ("you'd…"); akış zaman çizelgesiyle tırmanır ("In the first second… a week
later…", en fazla 3–4 adım). Kaynak: NASA, USGS, NOAA, üniversiteler; kesin olmayanı "scientists think…" diye
söyle.

### `body`
Vücudunun yaptığı tuhaf şeyler ve uç koşullarda vücuduna ne olur: "Why your body jolts as you fall asleep",
"Why you can't tickle yourself", "What happens to your body if you stop sleeping", "What 15 seconds in space
does to you", "Why you get goosebumps". Kanca: izleyicinin bugün hissettiği bir şey ya da vücuduna olacak
fiziksel sonuç. Kaynak: hakemli çalışmalar, NIH, üniversiteler. Tıbbi tavsiye ve teşhis yok; korku/iğrenç
ayrıntı yok.

### `dark-history`
Gerçek, belgelenmiş ve **büyük ölçekli** tuhaf olaylar: Yaz Olmayan Yıl (Tambora), Carrington olayı,
Krakatoa'nın 4.800 km öteden duyulan sesi, Toba süpervolkanı, 536 yılı ("the worst year to be alive"),
Büyük Londra Sisi. Ölçütler: (1) çok sayıda insanı ya da bütün dünyayı etkiledi, (2) tek cümlede imkânsız
gibi duran bir görüntüsü var ("It snowed in June."), (3) bugün de olabilir mi sorusunu doğuruyor. Soğuk açılış:
en tuhaf görüntü önce, tarih/yer sonra. Kan/vahşet ayrıntısı yok, kurbanlara saygılı dil.

### Konu bulma
İnsanların zaten merak ettiğine dair kanıt ara (WebSearch): Google "People also ask", Reddit r/whatif,
r/askscience, r/todayilearned, r/HumanBody, r/history; o haftanın gündemi (güneş fırtınası, volkan, uzay
görevi, yıldönümü). Daha önce işlenen konuları (`episodes/global/`, `state/published.json`) tekrarlama.
Seçmeden önce test: "Bu konunun ilk karesi ve ilk cümlesi, hiç bilmeyen birine 1 saniyede imkânsız bir
fiziksel görüntü gösteriyor mu?" Hayırsa başka konu seç.

## Alanlar

| Alan | Zorunlu | Açıklama |
|---|---|---|
| `title` | ✔ | En fazla ~55 karakter, merak uyandıran, doğru, cevabı vermez. 1 emoji olabilir. |
| `hook` | ✔ | Açılış başlık kartında görünen **2–5 kelime**, büyük harfle okunur ("WHAT IF THE SUN VANISHED?"). |
| `format` | ✔ | Tablodaki format (`what-if`, `body`, `dark-history`). |
| `subject` | ✔ | Ana özne, İngilizce tek kelime (görüntü seçimi için). |
| `description` | ✔ | İlk satır yorum sorusu, sonra anahtar kelimeli 1–2 cümle + `Sources: ...`. |
| `tags` | ✔ | 10–15 arama ifadesi (konu adı, soru biçimi, eş anlamlılar). Format etiketleri otomatik. |
| `hashtags` | ✔ | 2–4 konuya özel hashtag. `#Shorts` ve format hashtag'leri otomatik. |
| `publish_at` | ✔ | Tablodaki saat (UTC). |
| `scenes` | ✔ | 4–6 sahne: `text` + `search` (stok video için somut İngilizce 2–4 kelime, çoğu ana özneyle başlar). |

`style`, `language`, `voice`, `rate`, `privacy` **yazma**.

## İçerik kuralları

1. **Süre:** 55–85 kelime (≈22–33 sn), asla 90'ı geçme. Tek fikir.
2. **Kanca:** İlk cümle en fazla 10 kelime ve kaydırmayı durdurur; "Did you know", selamlama yok.
3. Cevabı/sonucu sona doğru ver; ortada bir kez yeniden kanca ("But here's the strange part.").
4. **Kapanış = tam cümle:** son cümle **mutlaka tamamlanmış** bir cümledir (". ! ?" ile biter). Yarım
   bırakma ("And back then," gibi) yok: 9 Ekim'de izleyiciler cümle ortasında biten anlatımdan şikâyet
   etti. Döngü istenirse son cümle tam bir cümle olarak açılışa göndermede bulunur ("That's how loud
   one volcano can be."). "Comment", "subscribe" yok.
5. Sayıları rakamla yaz ("8 minutes"); İngilizce sade, konuşma dili.
6. Her iddiayı güvenilir kaynakla doğrula; kaynakları açıklamaya yaz.

## Dosya adı

`episodes/global/YYYY-AA-GG-N-kisa-konu.json` (tarih = ABD Doğu saatine göre o gün).
Örnek: `episodes/global/_ornek.json`.
