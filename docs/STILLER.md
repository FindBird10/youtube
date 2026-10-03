# Görünüm stilleri ve kanal tercihleri

Bölüm dosyasında `"style"` alanıyla seçilir. Kod: `pipeline/make_video.py` → `STYLES`.

| Stil | Nerede | Altyazı | Görüntü akışı | Ses |
|---|---|---|---|---|
| `birdsvault` (varsayılan) | BirdsVault (Türkçe bilgi) | 2–3 kelimelik beyaz satır, o an söylenen kelime **sarı** | Sahne başına 1 görüntü, 0,4 sn yumuşak geçiş, hafif yakınlaşma | Müzik (konuşmada kısılır) |
| `global` | Global İngilizce kanal | Poppins ExtraBold, o anki kelimenin arkasında **mor kutu** | Açılış başlık kartı (1,3 sn), ~2,2 sn'de bir keskin kesme, rakam/`emphasis` kelimelerinde ani yakınlaşma | Müzik + çok kısık whoosh (yalnızca sahne değişimi, ≥4 sn arayla), vurguda "pop", açılışta "boom" |
| `cinematic` | Gaming kanalının varsayılanı | Klasik: beyaz satır + sarı kelime | Sıcak turuncu-kahve renk tonu, kenar karartması, üst/alt siyah sinema bantları, kesmesiz sakin tempo, yavaş kaydırma/yakınlaşma | Müzik, ses efekti yok |

İsteğe bağlı bölüm alanları: `caption_style` (`group` / `box` / `word` / `reveal`), `emphasis` (ani yakınlaşma kelimeleri),
`music_mood` (`lore` / `gizem` / `genel` → `assets/music/<klasör>`), `wiki` (`site`, `page`, `avoid`: istenmeyen görsel kelimeleri).

## Kullanıcı tercihleri (geri bildirimlerden)
- Whoosh belirgin ve sık olmasın; ancak sahne değişiminde, çok kısık.
- `cinematic` stilinde harf harf beliren "reveal" yazı animasyonu **beğenilmedi**; renk tonu, bantlar ve tempo beğenildi.
- Klasik altyazıyla yeniden denenen `cinematic` onaylandı: gaming kanalının varsayılan stili.
- Oyun kanalı İngilizce; Nintendo oyunları kullanılmaz.
- YouTube'dan video/ara sahne indirilmez (kullanım şartları ve telif). Hareketli oyun görüntüsü: oyunun resmî
  **Steam mağaza fragmanlarından** sessiz kısa klipler (`trailer.steam_appid`, sahnede `trailer: true`); yazı kartı ve
  menü görüntüleri otomatik elenir. Ara sahne (cutscene) ancak kullanıcının kendi kayıtlarıyla eklenebilir.
- Wiki görsellerinde oyun içi görüntüler tercih edilir; çizim/konsept/çizgi roman dosyaları geri plana atılır.
