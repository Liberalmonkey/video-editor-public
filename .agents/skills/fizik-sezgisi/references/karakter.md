# Karakter ve dudak senkronu

Gerekçe: `wiki/decisions/0039-fizik-ritim-galeri.md`.

## İki yol
| Karakter nereden | Senkron nasıl | Komut |
|---|---|---|
| Flow/Veo klibi (görüntüde konuşan karakter) | Ses ile ağız hareketi klipte birlikte gelir; kayma ölçülür, gerekirse ayrık ses kaydırılır | `vedit senkron <proje> [klip] [--uygula]` |
| Kodla çizilen karakter (`sahne.kind: "karakter"`) | Ağız kare başına konuşma sesinden üretilir; elle zamanlanmaz | `vedit viseme <proje>`; veri `karakter.bagla` ile klibe bağlanır |

## Flow/Veo klibi
- Önce ölç: `vedit senkron`. Genel hareket zayıfsa ölçüm ağız bölgesinden yapılır (YuNet yüz tespiti, `ölçüm ağız`).
- Ağız ölçümünde 0-110 ms "ses geç" doğaldır: konuşmada dudak sesten önce açılır. Rapor "doğal" der, `--uygula` dokunmaz.
- "Belirsiz" ölçüm uygulanmaz. Klipte belirgin hareket ya da ses vurgusu azdır; kareye `video-izle` ile bakılır.
- `--uygula` için ses görüntüden ayrılmış olmalı (Stüdyo'da Shift+A). Görüntüye değil ayrık sesin `giris`ine uygulanır.
- Birden çok klip birleştirilirken her klip ayrı ölçülür; bir klipte bulunan kayma diğerine taşınmaz.

## Kodla çizilen karakter
- Tanım `library/karakter/<ad>/karakter.json`: `renk` (govde, govde_golge, yuz, goz, ag, dil, yanak, vurgu), `oran` (en, boy, goz_aralik, goz_r), `title`, `ne_zaman`.
- Ağız sınıfları: K kapalı, U yarı açık, A geniş, E yayvan, O yuvarlak. Enerji ve spektral ağırlık merkezinden; ağız bir kare önden açılır, en az iki kare tutulur.
- Vurgu anlarında (konuşma vurgusu, `ritim.json`) baş sallanır; gövde 2, kollar 3-4 kare geriden gelir. İki kol aynı fazda oynamaz.
- Göz kırpma tohumludur (karakter adı ve klip kimliği): her render aynı karede kırpar.
- Karakter yalnız seslendirme varken kullanılır; sessiz videoda ağzı kapalı kalır ve ölü görünür.
- Üst izde `bg: "saydam"`, `olcek` 0,4-0,7 ve `donus` ile köşeye; tam ekranda karakterin kendi zemin rengi.

## Denetim
- Konuşma başında ağzın ilk açıldığı kare sesin ilk hecesinden en çok 2 kare önce olmalı, sonra olmamalı.
- Uzun sessizlikte ağız kapalı mı, kırpma doğal aralıkta mı (2-5 sn) kareyle bak.
- Fonem tanınmaz: "m, b, p" kapalı ağız sesle gelir ama A/E/O ayrımı yaklaşıktır. Daha doğrusu gerekirse Rhubarb Lip Sync (MIT) kullanıcı onayıyla eklenir.
