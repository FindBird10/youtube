# Bölüm yazma rehberi — Gaming kanalı (İngilizce)

Kanal: oyun karakterlerinin hikâyelerini anlatan **İngilizce** Shorts · Günde **3** video.
Bölümler `episodes/gaming/` klasörüne yazılır; kanal, dil (`en`), stil (`cinematic`) ve format
(`lore`) klasörden otomatik gelir, bu alanları yazma. Ses: Andrew (otomatik).

## Günün karakteri

Her gün **tek bir karakter** seçilir ve o karakter hakkında 3 farklı açıdan 3 video yazılır.
Böylece izleyici bir videoyu beğenince aynı karakterin diğer videolarına da geçer.

| Sıra | Açı | Ne anlatır | ABD Doğu saati (ET) |
|---|---|---|---|
| 1 | `origin` | Karakter kim, nereden geldi, onu o yapan olay | 13:00 |
| 2 | `secret` | Çoğu oyuncunun kaçırdığı detay, karanlık sır, trajik an ya da gizli bağlantı | 17:00 |
| 3 | `fate` | Karakterin en büyük kararı / sonu / en güçlü teori | 21:00 |

`publish_at` UTC yazılır; ET saatini `zoneinfo("America/New_York")` ile çevir (yaz/kış saati
farkı otomatik hesaplansın). 21:00 ET ertesi gün UTC'ye düşebilir, bu normal.

### Karakter seçimi
- Geniş kitlesi olan, internette hakkında çok aranan karakterler: The Last of Us, God of War,
  Red Dead Redemption, GTA, The Witcher, Elden Ring / Dark Souls, Resident Evil, Valorant,
  League of Legends / Arcane, Overwatch, Mortal Kombat, Street Fighter, Cyberpunk 2077,
  Mass Effect, BioShock, Halo, Assassin's Creed, Final Fantasy, Persona, Genshin Impact,
  Hollow Knight, Undertale, Five Nights at Freddy's, Silent Hill, Metal Gear, Detroit: Become Human…
- **Nintendo oyunları ve karakterleri kullanılmaz** (Mario, Zelda, Pokémon, Kirby, Metroid,
  Smash, Fire Emblem, Xenoblade, Splatoon vb.).
- Son 60 günde işlenen karakteri tekrar seçme (`episodes/gaming/` dosya adlarına ve
  `state/published.json` başlıklarına bak). Art arda iki gün aynı oyun serisinden seçme.
- Yeni çıkan bir oyun, dizi uyarlaması, güncelleme ya da trend varsa o karaktere öncelik ver
  (WebSearch ile o haftanın gündemine bak).
- Hikâyesi güçlü olsun: trajedi, ihanet, sır, büyük bir seçim. Sadece "havalı" ama hikâyesi
  zayıf karakterleri seçme.

## Performans notları (6 Ekim 2026, ilk 5 gün)
- Video başına ~1.000–1.700 izlenme; en iyisi **GTA 4 / Niko Bellic** (3 videonun üçü de 1.500+ ve en yüksek
  beğeni oranı ~%4). Büyük, herkesin bildiği seriler (GTA, Gears, Street Fighter) yeni/niş oyunlardan iyi gidiyor.
- Karakter seçerken **çok bilinen serilere öncelik ver** (GTA, Red Dead, The Last of Us, God of War, Resident Evil,
  The Witcher, Elden Ring/Dark Souls, Halo, Mortal Kombat, Street Fighter, Mass Effect, BioShock); niş/yeni oyunları
  ancak gündemdeyse seç. GTA 6 çıkışına (19 Kasım) kadar GTA evreni karakterleri ekstra ilgi görüyor.
- Başlık kalıpları iyi çalışıyor: "Why <karakter> really …", "<karakter>'s impossible choice …", "The secret behind …".

## Görseller (wiki)

Görüntüler karakterin Fandom wiki sayfasındaki oyun içi görsellerden gelir.

```json
"wiki": {"site": "thelastofus.fandom.com", "page": "Ellie", "avoid": ["part ii", "abby"]}
```
- `site`: oyunun Fandom alan adı, `page`: wiki'deki sayfa adı **birebir** (ör. `Arthur Morgan`,
  `Kratos`, `Geralt of Rivia`). Sayfanın varlığını WebFetch (`https://<site>/wiki/<Sayfa_Adı>`)
  ya da WebSearch ile doğrula; yanlış ad yazılırsa video stok görüntüye düşer.
- `avoid`: istenmeyen görsellerin dosya adında geçebilecek kelimeler (başka oyun, spoiler vb.).
- Sahnede `"image": "anahtar kelimeler"` → o sahne için dosya adında bu kelimeleri arar
  (ör. `"Ellie Riley mall"`). Başka bir karakterin sayfasından görsel için `"image_page": "Joel"`.
- Sahnelerin her biri `image` ya da `trailer: true` olsun (Steam fragmanı yoksa çoğunda `image`); en fazla 1 sahnede atmosfer için `search`
  (stok video, İngilizce: "rainy dark forest").

## Fragman klipleri (Steam)

Hareketli görüntü için oyunun **resmî Steam mağaza fragmanlarından** kısa, sessiz klipler kesilir
(YouTube'dan indirme yapılmaz; ses alınmaz).

```json
"trailer": {"steam_appid": 1888930}
```
- `steam_appid`: oyunun Steam numarası. Bul: WebFetch ile
  `https://store.steampowered.com/api/storesearch/?term=<oyun adı>&l=english&cc=US` → `items[].id`.
  Doğru oyun olduğundan emin ol (DLC, soundtrack, demo değil; karakterin geçtiği oyun).
  Seri birden fazla oyunsa karakterin hikâyesinin geçtiği oyunu seç.
- Oyun Steam'de yoksa (ör. yalnızca PlayStation/Xbox) `trailer` alanını yazma; tüm sahneler wiki görseli olur.
- Sahnede `"trailer": true` → o sahnenin arka planı fragmandan bir klip olur (o sahneye `image` yazma).
- Dağılım: **1. sahne her zaman karakterin wiki görseli** (`image`: karakterin adı; izleyici kimin
  anlatıldığını hemen görsün). Ortadaki sahnelerin **2–4 tanesi `trailer: true`**, kalanlar wiki görseli.
  Karakterin yüzünün önemli olduğu sahnelerde (ör. son sahne) wiki görselini tercih et.

## Alanlar

| Alan | Zorunlu | Açıklama |
|---|---|---|
| `title` | ✔ | En fazla ~60 karakter. **Karakter adı + oyun adı** geçsin (aranırlar): "Arthur Morgan's last ride in Red Dead 2". Cevabı vermez. |
| `angle` | ✔ | `origin`, `secret` veya `fate`. |
| `subject` | ✔ | Karakterin adı, küçük harf tek kelime (`ellie`, `kratos`). |
| `wiki` | ✔ | Yukarıya bak. |
| `trailer` | (Steam'de varsa ✔) | `{"steam_appid": N}`, yukarıya bak. |
| `description` | ✔ | İlk satır yorum sorusu ("Would you have forgiven Joel? 👇"). Sonra 1 cümle özet + spoiler uyarısı ("Spoilers for …"). En sonda **her zaman**: `Fan-made content. Not affiliated with or endorsed by <stüdyo/yayıncı>. Game images © their respective owners.` |
| `tags` | ✔ | 10–15 arama ifadesi: karakter adı, oyun adı, kısaltma (tlou, rdr2), "<karakter> story", "<karakter> explained", "<oyun> lore". Kanal etiketleri otomatik eklenir. |
| `hashtags` | ✔ | 2–4 hashtag: oyun ve karakter (`#thelastofus`, `#ellie`). `#Shorts #gaming #lore #videogames` otomatik. |
| `publish_at` | ✔ | Tablodaki ET saatinin UTC karşılığı. |
| `scenes` | ✔ | 5–7 sahne: `text` + `image` (+ isteğe bağlı `image_page`) ya da `trailer: true` (ya da nadiren `search`). |

`style`, `language`, `format`, `voice`, `rate`, `privacy` **yazma**.

## İçerik kuralları

1. **Süre:** 70–100 kelime (≈30–40 sn). 110'u asla geçme. Tek bir hikâye anı, yan bilgileri at.
2. **Kanca:** İlk cümle en fazla 12 kelime ve en çarpıcı gerçekle başlar ("Ellie was 14 when one
   bite made her the most important person on Earth."). Selamlama, "Did you know", oyun adıyla
   açılış yok.
3. **Akış:** sinematik, sakin ve duygulu anlatım; kısa cümleler ama arka arkaya noktalarla
   kesme. Ortada bir kez yeniden kanca ("But that's not the worst part.").
4. **Kapanış = tam cümle:** son cümle **mutlaka tamamlanmış** bir cümledir (". ! ?" ile biter). Yarım
   bırakma ("And back then," gibi) yok: 9 Ekim'de izleyiciler cümle ortasında biten anlatımdan şikâyet
   etti. Döngü istenirse son cümle tam bir cümle olarak açılışa göndermede bulunur ("And it all started
   with one bite."). "Comment below", "subscribe" yok; yorum sorusu açıklamada.
5. **Doğruluk:** Olayları resmî oyun içeriğine ve wiki/fandom kaynaklarına göre yaz; fan teorisini
   "fans believe…" diye açıkça ayır. Spoiler veren videoda açıklamaya spoiler uyarısı koy.
6. Kan ve vahşet ayrıntısı yok; ölümler saygılı ve kısa anlatılır. Gerçek kişilerle (seslendirme
   sanatçıları, geliştiriciler) ilgili iddia yok.

## Dosya adı

`episodes/gaming/YYYY-AA-GG-N-karakter-aci.json` — ör. `episodes/gaming/2026-10-02-1-ellie-origin.json`
(tarih = ABD Doğu saatine göre o gün). Örnek: `episodes/gaming/_ornek.json`.
