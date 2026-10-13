# Bölüm yazma rehberi — Gaming kanalı (İngilizce)

Kanal: oyun karakterlerinin hikâyelerini anlatan **İngilizce** Shorts · Günde **3** video.
Bölümler `episodes/gaming/` klasörüne yazılır; kanal, dil (`en`), stil (`cinematic`) ve format
(`lore`) klasörden otomatik gelir, bu alanları yazma. Ses: Andrew (otomatik).

## Yapay zekâ izi bırakmayan yazım (13 Ekim 2026) — her bölümde uygula

Bir izleyici Global Shorts'una "narrator, texts and video is AI. This is AI slop" yazdı. Son 12 Global videosunun
10'unda aynı kalıp cümle ("But here's the strange part.") vardı. Kurallar:

1. **Kalıp geçiş cümlesi yok:** "But here's the strange part", "Here's the thing", "But that's not all",
   "the strangest part", "you won't believe", "Did you know", "little did they know", "buckle up",
   "Tonight, we open the file" vb. (tam liste: `tools/check_episode.py`). Dönüm noktası bir kalıpla duyurulmaz,
   doğrudan somut bilgiyle gelir.
   ✗ "But here's the strange part. It wasn't one eruption." ✓ "The eruption didn't stop. It went on for eight months."
2. **Somutluk:** her videoda en az 2 özel isim (kişi, yer, kurum, gemi…), en az 2 kesin rakam ya da tarih ve
   araştırmadan gelen, çoğu videonun atladığı **1 ayrıntı** (bir tanığın sözü, bir raporun bulgusu, bir ölçüm).
3. **Abartı sıfatı en fazla 1:** chilling, eerie, terrifying, mind-blowing, shocking. Olayın kendisi korkutsun.
4. **Yapıyı çeşitlendir:** son günlerin bölümleriyle aynı açılış kalıbı yok; sahneler aynı kelimelerle başlamaz;
   kanca türünü değiştir (bir an, bir rakam, bir alıntı, bir yer, bir nesne).
5. **Konuşur gibi yaz:** kısa ve uzun cümleler karışık; ders kitabı, reklam ya da "içerik" dili değil, olayı
   anlatan gerçek bir anlatıcının cümleleri.
6. Yazdıktan sonra `python tools/check_episode.py <dosya>` çalıştır: **HATA** kalmayana kadar düzelt,
   **UYARI**'ları gözden geçir.

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
- Sahnelerin her biri `image` içersin (Steam fragmanı varsa 2. sahneden itibaren otomatik klibe döner); en fazla 1 sahnede atmosfer için `search`
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
  **Karakterin hikâyesini gösteren fragmanların bulunduğu sürümü seç.** Örnek: GTA V Enhanced (3240220)
  sürümünün fragmanları GTA Online güncellemeleri (Michael'ı göstermiyor). Seçmeden önce
  `https://store.steampowered.com/api/appdetails?appids=<N>&filters=movies` ile fragman adlarına bak;
  birden fazla sürüm varsa adları hikâyeye en uygun olanı al.
- Oyun Steam'de yoksa (ör. yalnızca PlayStation/Xbox) `trailer` alanını yazma; tüm sahneler wiki görseli olur.
  Eşit adaylar arasında **Steam'de olan oyunu seç**: hareketli oyun içi görüntü videoyu belirgin şekilde
  canlandırıyor.
- **Otomatik dolum (12 Ekim):** `trailer` alanı varsa **1. sahne dışındaki bütün sahneler** otomatik olarak
  fragman klibi alır (oynanış fragmanları öncelikli). Yine de her sahneye `image` yaz: klip bulunamazsa o
  wiki görseli kullanılır. `"trailer": true` yazmak artık zorunlu değil.
- **1. sahne her zaman karakterin wiki görseli** (`image`: karakterin adı; izleyici kimin anlatıldığını hemen
  görsün).
- Belirli bir sahnede klip değil mutlaka wiki görseli istiyorsan (ör. karakterin yüzünün göründüğü kritik an)
  o sahneye `"still": true` ekle. Bunu en fazla 1 sahnede kullan.

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
   kesme. Ortada bir dönüm noktası olsun, kalıp cümleyle değil doğrudan olayla ("Then Joel found the hospital.").
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
