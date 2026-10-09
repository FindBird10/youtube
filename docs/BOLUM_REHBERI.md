# Bölüm yazma rehberi — BirdsVault (Türkçe gizem ve karanlık tarih)

Kanal: **BirdsVault** · Dil: Türkçe · Günde **3** video · Konu: **gerçek, belgelenmiş gizemler ve tarihin
karanlık/tuhaf olayları**. (5 Ekim 2026'da "genel ilginç bilgiler"den bu konuya geçildi.)

Görünüm ve ses gaming kanalıyla aynıdır ve otomatik gelir: `cinematic` stil (sıcak koyu renk tonu, sinema
bantları, klasik altyazı, sakin tempo), Andrew sesi (Türkçe okur), gizem müziği. `style`, `voice`, `rate`
yazma.

Her Short, `episodes/` klasöründe tek bir JSON dosyasıdır. Dosya `main` dalına gönderildiğinde GitHub
Actions videoyu üretir ve YouTube'a yükler.

## Güncelleme (9 Ekim 2026): Türkiye videoları kanalın motoru

Yeni kurallarla yazılan 9 videoda (6–8 Ekim), formata göre izlenmeler:
- `turkiye-gizem`: Pamukkale **998**, Yerebatan Medusa **1.140**, Nemrut **1.125** (3'te 3, ortalama ~1.100)
- `karanlik-tarih`: Londra bira seli **952**, Eyam veba köyü **1.032**, Şikago/Peshtigo yangını 126
- `gizem`: Voynich 218, Poe 313, Hessdalen ışıkları 404 (en zayıf slot)

Kanal 2 günde izlenmesini ikiye katladı (4,7 bin → 9,8 bin) ve 9 abone kazandı. Bu yüzden zayıf `gizem`
slotu da **Türkiye** oldu: artık günde 2 `turkiye-gizem` + 1 `karanlik-tarih`. İki Türkiye videosu aynı gün
farklı türden olsun: biri **tarihî yapı/şehir** (İstanbul, antik kentler), biri **doğa** (dağ, göl, mağara,
volkan). Şikago yangını gibi Türk izleyicinin bilmediği yabancı olaylar karanlık-tarih slotunda da zayıf kaldı.

## Performans notları (7 Ekim 2026) — konu seçmeden önce oku

İlk 32 videonun izlenmeleri: 28 Eyl–4 Eki arası neredeyse hepsi **4–45** izlenmede kaldı. Son 3 günde kanal
itilmeye başladı ve şunlar kazandı:

| Video | İzlenme | İlk cümle |
|---|---|---|
| Arılar yok olsa | **863** | "Arılar yok olsa önce manavdaki renkler kaybolurdu." |
| Tunguska | **814** | "Bir adam 65 kilometre uzaktaki sandalyesinden fırlatıldı." |
| Londra bira seli | **455** | "Bir Londra mahallesini dev bir bira dalgası yuttu." |
| Vombatın küp dışkısı | 337 | "Doğada küp şeklinde dışkı yapan bir hayvan var…" |
| Pamukkale Cehennem Kapısı | **316** | "Bu mağaraya atılan kuşlar anında ölüp yere düşüyordu." |

Tutmayanlar: Voynich el yazması **4**, Roanoke/CROATOAN **1**, dans salgını 7, Wow! sinyali 13, Derinkuyu 25,
ve "X neden olur? Çoğu kişi … sanıyor" kalıbındaki bütün `neden` videoları (4–41).

Çıkarımlar (bundan sonraki bütün bölümlerde uygula):
1. **Fiziksel ve gözle görülür olay kazanır.** Patlama, sel, dalga, ölen kuşlar, devrilen ağaçlar — ilk
   karede *görülebilen* bir şey. Bir kitabı okuyamamak, bir kelime, bir sinyal, bir kişinin ortadan
   kaybolması gibi **soyut/yazıya dayalı** gizemler tutmadı; bunları seçme.
2. **Türk izleyicinin tanıdığı bir şeye bağla.** Manav, arı, Pamukkale, Londra: izleyici 1 saniyede
   "bunu biliyorum" diyor. Roanoke, CROATOAN, Voynich gibi Türkiye'de bilinmeyen adlar başlıkta ve ilk
   cümlede kullanılmaz; gerekirse olay anlatılır, ad sonra söylenir.
3. **Kanca = imkânsız görünen tek bir görüntü**, 6–10 kelime. Soru ile açma ("… neden …?"), tarih/yer ile
   açma ("14 Temmuz 1518'de…") ve "çoğu kişi … sanıyor" kalıbı kullanılmaz.
4. **Ölçek:** rakamla anlatılan büyüklük (80 milyon ağaç, 65 km, 1,4 milyon litre) izlenmeyi taşıyor.
5. Seçmeden önce test: "Hiç duymamış biri ilk karede ve ilk cümlede neyi *görecek*?" Cevap bir nesne ya da
   olay değil de bir fikirse, başka konu seç.

## Günlük akış

Her gün 3 bölüm yazılır ve `publish_at` ile zamanlanır (Türkiye saati = UTC+3). Gizem içeriği akşam ve
gece daha çok izlenir.

| Sıra | Format (`format` alanı) | TR saati → `publish_at` (her gün) |
|---|---|---|
| 1 | Türkiye'den gizem — tarihî yapı/şehir (`turkiye-gizem`) | 18:00 → `YYYY-AA-GGT15:00:00Z` |
| 2 | Tarihin karanlık/tuhaf olayı (`karanlik-tarih`) | 21:00 → `YYYY-AA-GGT18:00:00Z` |
| 3 | Türkiye'den gizem — doğa: dağ, göl, mağara (`turkiye-gizem`) | 23:30 → `YYYY-AA-GGT20:30:00Z` |

`gizem` formatı (dünyadan fiziksel gizemler) şimdilik günlük akışta yok; Türkiye konusu bulunamayan
istisnai bir günde 1. slotta kullanılabilir.

## Formatlar

### 1. Çözülememiş gizem (`gizem`)
Belgelenmiş ama hâlâ tam açıklanamayan **fiziksel** olaylar ve buluntular: gökten düşen/patlayan şeyler,
açıklanamayan ışıklar ve sesler, tuhaf doğa olayları, hayalet gemiler, imkânsız buluntular (ör. Antikythera
düzeneği, Hessdalen ışıkları, Kırmızı Yağmur (Kerala), Baltık Denizi anomalisi, Flannan Adaları deniz feneri,
"Gökten balık yağması"). Yazıya/şifreye dayalı gizemler (Voynich, Somerton) seçilmez.
- **Soğuk açılış:** en tuhaf fiziksel görüntü ilk cümlede ("Bir adam 65 kilometre uzaktaki sandalyesinden
  fırlatıldı.").
- Akış: olay → neden tuhaf → en güçlü 1–2 açıklama → hâlâ cevapsız kalan kısım → tam bir kapanış cümlesi.

### 2. Tarihin karanlık/tuhaf olayı (`karanlik-tarih`)
Gerçekten yaşanmış, şaşırtıcı ve **absürt ya da büyük ölçekli** olaylar: tuhaf seller ve dalgalar, felaketler,
tuhaf kazalar (ör. Londra bira seli ✓, Boston pekmez seli, Yaz Olmayan Yıl, Büyük Londra Sisi, Krakatoa'nın
4.800 km öteden duyulan sesi, Halifax patlaması). İlk cümlede gözle görülebilen bir olay olsun.
- Kanca: olayın en inanılmaz rakamı ya da anı. Akış: ne oldu → neden oldu → ne değişti → tam bir kapanış cümlesi.

### 3. Türkiye'den gizem (`turkiye-gizem`)
Türkiye ve Anadolu'dan **izleyicinin tanıdığı ya da gezdiği** yerlerin gizemli/tehlikeli yanları
(işlenenler ✓: Pamukkale Cehennem Kapısı, Yerebatan Medusa, Nemrut, Ağrı'daki gemi tepesi, Derinkuyu).
- **Tarihî yapı/şehir adayları:** Göbeklitepe, Sümela, Ani Harabeleri, Kaymaklı, Ayasofya, Kız Kulesi,
  Efes, Truva, Hattuşa, Zeugma, Çatalhöyük, Hasankeyf, Likya kaya mezarları, Topkapı'nın gizli geçitleri.
- **Doğa adayları:** Olimpos Yanartaş (sönmeyen alevler), Van Gölü canavarı efsanesi, Salda Gölü (Mars'a
  benzeyen göl), Kapadokya peri bacaları, Damlataş/Karain mağaraları, Erciyes, Nemrut Kalderası, Tuz Gölü,
  Kelebekler Vadisi, Yedigöller.
- Yerin adı başlıkta geçsin. Başlıkta soru ya da gizemli vaat işe yarıyor ("…neden ters?", "…altında ne
  saklı?").
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
salgını, Mary Celeste, Dyatlov, Roanoke, Tunguska, Voynich, Londra bira seli, Cehennem Kapısı, Poe, Eyam, Yerebatan Medusa işlendi). Seçtiğin konunun neden ilgi çekeceğini commit
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
3. **Kapanış = tam cümle:** son cümle **mutlaka tamamlanmış** bir cümledir (nokta, soru ya da ünlem
   işaretiyle biter). Yarım bırakma ("…ve o gece," gibi) yok: 9 Ekim'de izleyiciler cümle ortasında biten
   anlatımdan şikâyet etti. Döngü istenirse son cümle tam bir cümle olarak açılışa göndermede bulunur
   ("Ve o sandalye hâlâ 65 kilometre uzakta duruyordu."). "Yorumlara yaz", "abone ol" yok; yorum sorusu
   açıklamada.
4. **Doğruluk:** Her iddiayı güvenilir kaynakla (Britannica, Smithsonian, BBC, National Geographic,
   üniversiteler, müzeler, Wikipedia'nın kaynakları) web aramasıyla doğrula; kaynağı açıklamaya yaz.
5. **Dil:** Konuşma diliyle akıcı Türkçe; sayıları rakamla yaz. Birbirine bağlı fikirleri tek cümlede
   birleştir (her nokta seste duraksama yaratır).

Örnek için `episodes/_ornek.json` dosyasına bak.
