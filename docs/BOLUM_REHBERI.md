# Bölüm yazma rehberi — BirdsVault (Türkçe gizem ve karanlık tarih)

Kanal: **BirdsVault** · Dil: Türkçe · Günde **3** video · Konu: **gerçek, belgelenmiş gizemler ve tarihin
karanlık/tuhaf olayları**. (5 Ekim 2026'da "genel ilginç bilgiler"den bu konuya geçildi.)

Görünüm ve ses gaming kanalıyla aynıdır ve otomatik gelir: `cinematic` stil (sıcak koyu renk tonu, sinema
bantları, klasik altyazı, sakin tempo), Andrew sesi (Türkçe okur), gizem müziği. `style`, `voice`, `rate`
yazma.

Her Short, `episodes/` klasöründe tek bir JSON dosyasıdır. Dosya `main` dalına gönderildiğinde GitHub
Actions videoyu üretir ve YouTube'a yükler.

## Günlük akış

Her gün 3 bölüm yazılır ve `publish_at` ile zamanlanır (Türkiye saati = UTC+3). Gizem içeriği akşam ve
gece daha çok izlenir.

| Sıra | Format (`format` alanı) | TR saati → `publish_at` (her gün) |
|---|---|---|
| 1 | Çözülememiş gizem (`gizem`) | 18:00 → `YYYY-AA-GGT15:00:00Z` |
| 2 | Tarihin karanlık/tuhaf olayı (`karanlik-tarih`) | 21:00 → `YYYY-AA-GGT18:00:00Z` |
| 3 | Türkiye'den ya da Anadolu'dan gizem (`turkiye-gizem`) | 23:30 → `YYYY-AA-GGT20:30:00Z` |

## Formatlar

### 1. Çözülememiş gizem (`gizem`)
Belgelenmiş ama hâlâ açıklanamayan olaylar: kayıp uçak/gemi/kişiler, açıklanamayan sinyaller ve
buluntular, çözülemeyen şifreler (ör. Somerton Adamı, Voynich El Yazması, Flannan Adaları deniz feneri,
Hinterkaifeck, Baltık Denizi anomalisi, Antikythera düzeneği).
- **Soğuk açılış:** en tuhaf an ilk cümlede ("Masasında oturan adamın cebinde tek bir kelime vardı.").
- Akış: olay → neden tuhaf → en güçlü 1–2 açıklama → hâlâ cevapsız kalan kısım → döngü cümlesi.

### 2. Tarihin karanlık/tuhaf olayı (`karanlik-tarih`)
Gerçekten yaşanmış, şaşırtıcı ve karanlık olaylar: felaketler, salgınlar, tuhaf kazalar, deneyler
(ör. Radyum Kızları, Büyük Londra Sisi, Yaz Olmayan Yıl, Cesur Hayvanat Bahçesi kaçışları, Titanik'in
kardeşi Britannic).
- Kanca: olayın en inanılmaz rakamı ya da anı. Akış: ne oldu → neden oldu → ne değişti → döngü.

### 3. Türkiye'den gizem (`turkiye-gizem`)
Türkiye ve Anadolu'dan gizemli yerler, buluntular, olaylar ve belgelenmiş efsaneler (ör. Göbeklitepe,
Hierapolis'teki Cehennem Kapısı, Sümela, Ani Harabeleri, Kaymaklı, Yerebatan'ın Medusa başları, Nemrut).
- Efsane ile belgelenmiş gerçeği açıkça ayır ("Efsaneye göre…", "Arkeologlara göre…").
- Not: Derinkuyu daha önce işlendi; aynı yeri başka açıdan ancak yeni ve güçlü bir bilgiyle işle.

### Ortak kurallar
- Belgelenmiş gerçekleri teorilerden açıkça ayır; kesin olmayanı "bir teoriye göre…" diye söyle.
- Kan, vahşet ve ayrıntılı ölüm tarifleri yok; kurbanlara saygılı dil. Yaşayan kişiler hakkında suçlama yok.
- Doğaüstü iddiaları gerçek gibi sunma; "insanlar … olduğuna inanıyor" de.

## Konu bulma
İnsanların merak ettiğine dair kanıt ara (WebSearch): Reddit r/UnresolvedMysteries, r/history,
r/todayilearned, Türkçe forum/haber gündemi, o günün yıldönümleri ("bugün tarihte"). Daha önce işlenen
konuları tekrarlama (`state/published.json`, `episodes/` dosya adları: Derinkuyu, Wow! sinyali, 1518 dans
salgını, Mary Celeste, Dyatlov, Roanoke, Tunguska işlendi). Seçtiğin konunun neden ilgi çekeceğini commit
mesajında bir cümleyle yaz.

## Görseller
- **Wikipedia (kamu malı)**: `"wiki": {"site": "en.wikipedia.org", "page": "<İngilizce makale adı>"}`.
  Yalnızca kamu malı/CC0 görseller otomatik seçilir (eski fotoğraflar, gravürler, haritalar, belgeler).
  Makale adını WebFetch ile doğrula (`https://en.wikipedia.org/wiki/<Makale>`).
  Sahnede `"image": "anahtar kelimeler"` (dosya adında aranır), başka makale için `"image_page"`.
- **Stok görüntü**: atmosfer sahneleri için `"search"` (İngilizce, somut: "foggy forest night",
  "old lighthouse storm", "candle old manuscript"). Sinematik renk tonu stok görüntüyü de karartır.
- Dağılım: 1. sahne konunun gerçek görseli (Wikipedia), kalan sahnelerin yarısı Wikipedia yarısı stok.
  Wikipedia makalesinde uygun görsel yoksa tüm sahneler stok olabilir.

## Dosya adı
`episodes/YYYY-AA-GG-N-kisa-konu.json` — ör. `episodes/2026-10-06-1-somerton-adami.json` (N = gün içindeki sıra).
Adı `_` ile başlayan dosyalar işlenmez (taslak/örnek için).

## Alanlar

| Alan | Zorunlu | Açıklama |
|---|---|---|
| `title` | ✔ | **En fazla ~50 karakter**. Merak uyandıran, abartısız, doğru; cevabı vermez. 1 emoji olabilir. |
| `format` | ✔ | `gizem`, `karanlik-tarih` veya `turkiye-gizem` (tabloya göre). |
| `subject` | ✔ | Ana özne, **İngilizce** tek kelime (görsel seçimi için: `lighthouse`, `manuscript`). |
| `description` | ✔ | İlk satır yorum sorusu ("Sence ne oldu? 👇"), sonra konunun anahtar kelimelerini geçiren 1–2 cümle + `Kaynak: ...`. |
| `tags` | ✔ | **10–15 etiket**, Türkçe aramalar (konu adı, yer, "… gizemi", "… nedir"). Format etiketleri otomatik. |
| `hashtags` | ✔ | **2–4 konuya özel** hashtag. `#Shorts` ve format hashtag'leri otomatik. |
| `wiki` | | Yukarıya bak (Wikipedia). |
| `scenes` | ✔ | 4–6 sahne: `text` + `image` ya da `search`. |
| `publish_at` | ✔ | Tablodaki saat (UTC). |

`style`, `language`, `voice`, `rate`, `privacy` alanlarını **yazma**.

## İçerik kuralları
1. **Süre:** 60–90 kelime (≈28–38 sn; Andrew sakin okur). 95'i geçme. Tek hikâye.
2. **Kanca:** İlk cümle en fazla 10 kelime ve tek başına kaydırmayı durdurur. Selamlama, "biliyor muydunuz",
   tarih/yer girişi yok — tuhaf an önce, tarih/yer sonra.
3. **Kapanış = döngü:** son cümle yarım kalıp ilk cümleye bağlanır; "yorumlara yaz", "abone ol" yok,
   yorum sorusu açıklamada.
4. **Doğruluk:** Her iddiayı güvenilir kaynakla (Britannica, Smithsonian, BBC, National Geographic,
   üniversiteler, müzeler, Wikipedia'nın kaynakları) web aramasıyla doğrula; kaynağı açıklamaya yaz.
5. **Dil:** Konuşma diliyle akıcı Türkçe; sayıları rakamla yaz. Birbirine bağlı fikirleri tek cümlede
   birleştir (her nokta seste duraksama yaratır).

Örnek için `episodes/_ornek.json` dosyasına bak.
