# Bölüm yazma rehberi — Oyun haberleri kanalı (İngilizce)

Kanal: oyun dünyasındaki **bir önceki günün** gelişmelerini anlatan **İngilizce** Shorts · Günde **3** video.
Bölümler `episodes/news/` klasörüne yazılır; dil (`en`), stil (`cinematic`: gaming kanalıyla aynı görünüm —
sıcak renk tonu, sinema bantları, klasik altyazı, sakin tempo), format (`news`) ve ses (gaming ile aynı:
Andrew) klasörden otomatik gelir.

## Günlük akış

Her sabah (ABD Doğu saati) **dünün** (son 24–36 saatin) oyun haberleri taranır, en güçlü 3 haber seçilir.

| Sıra | Haber | ABD Doğu saati (ET) |
|---|---|---|
| 1 | Günün en büyük haberi | 09:00 |
| 2 | İkinci haber | 13:00 |
| 3 | Üçüncü haber (farklı platform/tür olsun) | 18:00 |

`publish_at` UTC yazılır; ET saatini `zoneinfo("America/New_York")` ile çevir.

## Haber seçimi ve doğruluk
- Kaynaklar: **resmî** duyurular (yayıncı/stüdyo blogları, Rockstar Newswire, PlayStation Blog, Xbox Wire,
  Steam duyuruları, kazanç raporları) ve **güvenilir** yayınlar (IGN, GameSpot, Eurogamer, VGC, Game Informer,
  The Verge, Bloomberg, Polygon, PC Gamer). Her iddiayı en az bir resmî ya da güvenilir kaynakla doğrula.
- Söylenti/sızıntı ancak büyük ölçüde konuşuluyorsa ve **açıkça "rumor"/"reportedly" diye** söylenerek işlenir;
  kesin bilgi gibi anlatılmaz. Kaynağı belirsiz sızıntı kullanılmaz.
- Öncelik: büyük çıkışlar ve tarih/fiyat duyuruları, yeni fragman ve oynanış gösterimleri, büyük güncellemeler,
  stüdyo/şirket haberleri, satış rekorları, gecikmeler. Aynı haberi iki gün üst üste işleme (`episodes/news/`).
- **Nintendo oyunları ve görselleri kullanılmaz** (telif konusunda çok katılar).
- Kişiler hakkında doğrulanmamış iddia yok; işten çıkarma, dava gibi konularda tarafsız dil.

## Görseller
- Oyun Steam'deyse `"trailer": {"steam_appid": N}` ve sahnelerin 2–3'ünde `"trailer": true`
  (Steam numarası: WebFetch `https://store.steampowered.com/api/storesearch/?term=<oyun>&l=english&cc=US`).
- Oyunun Fandom wiki'si varsa `"wiki": {"site": "...fandom.com", "page": "..."}` ve sahnelerde `"image"`
  (resmî ekran görüntüleri ve kapak görselleri). Karakter sayfası için `"image_page"`.
- Hiçbiri yoksa ya da konu genel ise (ör. şirket haberi) `"search"` ile somut stok görüntü
  ("gamer playing console dark room", "game controller close up").
- 1. sahne haberi hemen anlatan görsel olsun (oyunun kapak görseli ya da ana karakter).

## Alanlar

| Alan | Zorunlu | Açıklama |
|---|---|---|
| `title` | ✔ | En fazla ~55 karakter; oyunun adı başta geçsin ("GTA 6 has hurricanes and 170+ animals 🌀"). |
| `hook` | | Kullanılmıyor (sinematik stilde açılış kartı yok); yazmak zorunlu değil. |
| `subject` | ✔ | Ana özne, küçük harf tek kelime (`gta6`, `hollowknight`). |
| `description` | ✔ | İlk satır yorum sorusu ("Are you pre-ordering? 👇"), sonra 1–2 anahtar kelimeli cümle, sonra `Sources: ...`. Görsel kullanıldıysa en sonda: `Game footage/images © their respective owners.` |
| `tags` | ✔ | 10–15 arama ifadesi: oyun adı, kısaltmalar (gta 6, gta vi), "<oyun> news", "<oyun> release date" vb. |
| `hashtags` | ✔ | 2–4 hashtag (`#gta6`, `#rockstargames`). `#Shorts #gamingnews #gaming` otomatik. |
| `publish_at` | ✔ | Tablodaki saatin UTC karşılığı. |
| `wiki` / `trailer` | | Yukarıya bak. |
| `scenes` | ✔ | 4–6 sahne; her sahnede `image`, `trailer: true` ya da `search`. |

`style`, `language`, `format`, `voice`, `rate`, `privacy` **yazma**.

## İçerik kuralları
1. **Süre:** 55–85 kelime (≈20–30 sn; ses hızlı). Bir videoya tek haber.
2. **Kanca:** İlk cümle en fazla 10 kelime, haberin en çarpıcı kısmı ("Hurricanes are coming to GTA 6.").
   "Hey guys", "breaking news", "in today's video" yok.
3. **Ton:** akıcı haber anlatımı, kısa cümleler, konuşma dili; ama abartma ve tıklama tuzağı yok — başlık ve ilk cümle
   haberin gerçek içeriğini söyler.
4. **Rakamlar** rakamla ("November 19", "$79.99", "170"). Tarih göreli değil kesin yazılır
   (video gecikerek yayınlanabilir: "tomorrow" yerine tarih).
5. **Kapanış = tam cümle:** son cümle **mutlaka tamamlanmış** bir cümledir (". ! ?" ile biter); yarım
   bırakma yok (izleyici şikâyeti, 9 Eki). "Subscribe", "comment below" yok; soru açıklamada.
6. Görüş değil haber: "fans think…", "reportedly…" ayrımı net.

## Dosya adı
`episodes/news/YYYY-AA-GG-N-kisa-konu.json` (tarih = yayın günü, ABD Doğu saati). Örnek: `episodes/news/_ornek.json`.
