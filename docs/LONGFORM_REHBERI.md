# Bölüm yazma rehberi — Global kanal uzun videoları ("Case Files", İngilizce)

Kanal: **BirdsVaultGlobal**, Shorts'larla aynı kanal · **Haftada 3 uzun video (Pazartesi, Çarşamba, Cuma)** ·
**8–10 dakika** · Konu: **gerçek, belgelenmiş gizemli olaylar ve vakalar**.
Bölümler `episodes/longform/` klasörüne yazılır. Dil (`en`), görünüm ("vaka dosyası"), ses (Davis, derin ve sakin),
müzik ve kapak görseli otomatik gelir. `style`, `voice`, `rate`, `language`, `privacy` alanlarını **yazma**.

Video şöyle akar: **soğuk açılış** (1. bölüm, bölüm kartı yok) → **CASE FILE #NN** vaka kartı → her bölümden
önce **CHAPTER N** kartı → sonda kırmızı damgalı **CASE STATUS** kartı. Açıklamaya YouTube bölüm zamanları
otomatik eklenir. Kapak görseli otomatik üretilir (`thumbnail` alanından).

## Günlük akış

| Gün | Yayın saati (ABD Doğu) | `publish_at` |
|---|---|---|
| Pazartesi, Çarşamba, Cuma | 15:00 ET | ET saatini `zoneinfo("America/New_York")` ile UTC'ye çevir |

Dosya adı: `episodes/longform/YYYY-AA-GG-kisa-konu.json` (tarih = yayın günü, ET). `_` ile başlayanlar işlenmez.
Örnek: `episodes/longform/_ornek.json` (Dyatlov Geçidi).

## Konu seçimi

- **Gerçek ve belgelenmiş**: hakkında güvenilir kaynak (Britannica, Smithsonian, BBC, resmî raporlar, hakemli
  çalışmalar, Wikipedia ve kaynakları) bulunan vakalar. Efsane ağırlıklı konular ancak "gerçekte ne biliyoruz"
  açısıyla.
- **Görsel malzemesi olan**: tercihen 1990 öncesi olaylar; Wikipedia makalesinde kamu malı/CC fotoğraf, harita,
  belge bulunur. Makaleyi WebFetch ile aç ve görsellerin varlığını kontrol et.
- **Uygun türler**: açıklanamayan kayboluşlar (gemi, uçak, kişi grupları), tuhaf ölümler (vahşet ayrıntısı
  olmadan), açıklanamayan sinyaller/sesler/ışıklar, çözülemeyen şifreler ve belgeler, terk edilmiş yerler,
  tarihin tuhaf olayları.
- **Aday listesi**: Mary Celeste, Flannan Isles deniz feneri, Roanoke kolonisi, Somerton Man / Tamam Shud,
  Isdal Woman, Yuba County Five, Flight 19, SS Waratah, Carroll A. Deering, Amelia Earhart, Kaspar Hauser,
  Lead Masks vakası, Max Headroom yayın korsanlığı, Taos Hum, Hessdalen ışıkları, Oak Island, Wow! sinyali,
  Voynich el yazması, Bennington Üçgeni, Kentucky et yağmuru, Tunguska, 1518 dans salgını, Franklin keşif seferi.
- **Kaçın**: yaşayan kişilerin suçlandığı ya da beraat ettiği vakalar, süren davalar, çocuk kurbanlar, son 15
  yılın taze acıları (aileler hâlâ yasta), açık şiddet ağırlıklı cinayetler, intihar ayrıntıları.
- Daha önce işlenen vakaları tekrarlama (`episodes/longform/`, `state/published.json`).

## Yapı (6–7 bölüm, toplam 1.250–1.450 kelime ≈ 8–10 dk)

| Bölüm | İçerik | Kelime |
|---|---|---|
| 0 — soğuk açılış | Vakanın en tuhaf anı; sonunda "Tonight, we open the file." gibi bir kapanış | 100–140 |
| 1 | Kimler, nerede, ne zaman: arka plan | 180–230 |
| 2 | Olay: ne oldu, nasıl fark edildi | 180–230 |
| 3 | Soruşturma ve arama: kanıtlar | 180–230 |
| 4 | Tuhaf ayrıntılar: açıklanamayan kısımlar | 150–200 |
| 5 | Teoriler: her biri lehine ve aleyhine kanıtla | 180–230 |
| 6 | En iyi cevap ve hâlâ açık kalanlar; son cümle açılışa göndermede bulunur | 150–220 |

- Bölüm başlıkları kısa ve merak uyandırıcı (2–5 kelime): "The Empty Tent", "The Ravine", "An Answer?".
- Her bölüm küçük bir merak kancasıyla biter ("But that was not the strangest part.").
- Her sahne 1–3 cümle, **20–35 kelime**. Bölüm başına 5–8 sahne.

## Yazım üslubu

- Sakin, kesin, belgesel anlatımı; geçmiş zaman. Abartma, tıklama tuzağı ve "you won't believe" yok.
- Tarihler, yerler ve isimler net: "On the 26th of February, 1959…". Sayılar rakamla ya da okunduğu gibi.
- Gerçek / teori ayrımı her zaman açık: "investigators concluded…", "some researchers believe…",
  "there is no evidence that…".
- Kurbanlara saygılı dil; yaraları yalnızca genel olarak anlat ("severe chest injuries"), ayrıntıya girme.
- İzleyiciye doğrudan seslenme az ve doğal. "Like and subscribe" yok (kapanış kartı bunu yapıyor).
- Her cümle **tam** biter; yarım bırakılmış cümle yok.

## Görseller

- `wiki`: vakanın İngilizce Wikipedia makalesi. Sahnede `"image": "anahtar kelimeler"` (dosya adında aranır:
  "tent", "map", "memorial"). Başka makalenin görseli için `"image_page": "<makale>"` (kişi, yer, gemi).
- `"search"`: atmosfer için somut, İngilizce stok video ("snowy mountain night", "old documents desk lamp",
  "foggy coast lighthouse"). Aynı aramayı art arda iki sahnede kullanma.
- Dağılım: sahnelerin ~%40'ı `image`, ~%60'ı `search`. Arşiv görselleri en güçlü anlara: olay yeri, kişiler,
  belgeler.
- `"card": "Yer · Tarih"`: önemli anlarda sol üstte daktiloyla yazılan tarih/yer kartı. Video başına 4–8 kart,
  her bölümün ilk sahnesinde bir tane.

## Alanlar

| Alan | Zorunlu | Açıklama |
|---|---|---|
| `title` | ✔ | En fazla ~70 karakter; vakanın aranan adı başta: "The Dyatlov Pass Incident: Why Did 9 Hikers Run Into the Snow?" |
| `case_no` | ✔ | Sıra numarası: `episodes/longform/` içindeki en büyük `case_no` + 1. |
| `case_title` | ✔ | Kartta görünen vaka adı ("The Dyatlov Pass Incident"). |
| `case_meta` | ✔ | "Yer · Tarih" ("Kholat Syakhl, Ural Mountains · February 1959"). |
| `status` | ✔ | `UNSOLVED`, `DISPUTED`, `UNEXPLAINED` ya da `CLOSED`; kapanış damgası ve kapakta görünür. |
| `subject` | ✔ | Küçük harf tek kelime (`dyatlov`). |
| `description` | ✔ | İlk satır yorum sorusu, sonra 2–3 cümle özet, sonra `Sources: ...`. |
| `tags` | ✔ | 12–15 arama ifadesi (vaka adı, yer, "… explained", "… mystery"). Kanal etiketleri otomatik. |
| `hashtags` | ✔ | 2–3 konuya özel hashtag. |
| `wiki` | ✔ | `{"site": "en.wikipedia.org", "page": "<makale>"}` |
| `thumbnail` | ✔ | `{"text": "3–6 KELİME", "highlight": "TEK KELİME", "image": "anahtar kelime"}`: kapak yazısı, sarı vurgulanan kelime, kapak fotoğrafı. Kapak yazısı başlığı tekrar etmez, merak uyandırır ("THEY CUT THE TENT FROM INSIDE"). |
| `chapters` | ✔ | Yukarıdaki yapı; her bölüm `{"title", "scenes": [...]}`. |
| `publish_at` | ✔ | Tablodaki saat (UTC). |
| `end_line` | | Kapanış kartındaki satır (varsayılan: "New case files every Monday, Wednesday and Friday."). |
