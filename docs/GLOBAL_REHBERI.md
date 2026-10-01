# Bölüm yazma rehberi — Global kanal (İngilizce)

Kanal: dünya geneline **İngilizce** merak videoları · Günde **3** video · Bölümler
`episodes/global/` klasörüne yazılır; dil (`en`) ve stil (`global`: açılış başlık kartı, mor kutulu
altyazı, hızlı kesmeler, vurgu yakınlaşması) klasörden otomatik gelir.

## Formatlar ve günlük akış

| Sıra | Format (`format`) | ABD Doğu saati (ET) |
|---|---|---|
| 1 | `what-if` — bilime dayalı "What if…?" senaryosu | 11:00 |
| 2 | Tek günler `psychology`, çift günler `business` (ayın gününe göre) | 15:00 |
| 3 | `dark-history` — gerçek, belgelenmiş karanlık/gizemli tarih | 19:00 |

`publish_at` UTC yazılır; ET saatini `zoneinfo("America/New_York")` ile çevir.
Ses formata göre otomatik (Brian: what-if/psychology, Andrew: dark-history/business).

### `what-if`
"What if the Moon disappeared?", "What if you fell into a black hole?", "What if humans stopped
sleeping?". İlk cümle en çarpıcı sonucu ima eder; akış zaman çizelgesiyle tırmanır
("In the first second… a week later… a year later…", en fazla 3–4 adım). Kaynak: NASA, üniversiteler,
ciddi bilim yayınları; kesin olmayanı "scientists think…" diye söyle.

### `psychology`
Beynin hileleri ve gerçek deneyler: "Why you remember embarrassing moments at 3 a.m.",
"The experiment that made people obey", "Why your brain hates unfinished tasks". Kanca: izleyicinin
kendinde tanıyacağı bir an ("You've done this today without noticing."). Kaynak: hakemli çalışmalar,
APA, üniversiteler; çalışmanın adını/yılını söyle. Tıbbi/terapi tavsiyesi yok, teşhis koyma.

### `business`
Şirketlerin ve kararların şaşırtıcı hikâyeleri: "The company that turned down buying Netflix",
"Why IKEA makes you build it yourself", "The $1 decision that saved Apple". Kanca: kararın ya da
sonucun en çarpıcı kısmı. Rakamları doğrula ve kaynağını yaz. Yaşayan kişiler hakkında suçlama
yok; yatırım tavsiyesi yok.

### `dark-history`
Belgelenmiş, gerçek ve tuhaf/karanlık olaylar: Dyatlov Pass, Radium Girls, the Great Molasses
Flood, the Year Without a Summer. Soğuk açılış: en tuhaf an, tarih/yer sonra gelir. Gerçekleri
teorilerden ayır; kan/vahşet ayrıntısı yok, kurbanlara saygılı dil.

### Konu bulma
İnsanların zaten merak ettiğine dair kanıt ara (WebSearch): Google "People also ask", Reddit
r/whatif, r/askscience, r/psychology, r/todayilearned, r/UnresolvedMysteries, r/history,
r/business; o haftanın gündemi (uzay görevi, yıldönümü, haber). Daha önce işlenen konuları
(`episodes/global/`, `state/published.json`) tekrarlama.

## Alanlar

| Alan | Zorunlu | Açıklama |
|---|---|---|
| `title` | ✔ | En fazla ~55 karakter, merak uyandıran, doğru, cevabı vermez. 1 emoji olabilir. |
| `hook` | ✔ | Açılış başlık kartında görünen **2–5 kelime**, büyük harfle okunur ("WHAT IF THE SUN VANISHED?"). |
| `format` | ✔ | Tablodaki format. |
| `subject` | ✔ | Ana özne, İngilizce tek kelime (görüntü seçimi için). |
| `emphasis` | | Vurgu yakınlaşması yapılacak 2–5 kelime (rakamlar otomatik). |
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
4. **Kapanış = döngü:** son cümle ilk cümleye bağlanır; "comment", "subscribe" yok.
5. Sayıları rakamla yaz ("8 minutes"); İngilizce sade, konuşma dili.
6. Her iddiayı güvenilir kaynakla doğrula; kaynakları açıklamaya yaz.

## Dosya adı

`episodes/global/YYYY-AA-GG-N-kisa-konu.json` (tarih = ABD Doğu saatine göre o gün).
Örnek: `episodes/global/_ornek.json`.
