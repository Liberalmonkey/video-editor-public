# YouTube kapak kalıpları

Kaynak: `wiki/sources/2026-11-15-kapak-kalip-analizi.md` (114 referans kapak, Antigravity analizi). `vedit kapak` brief isteğine bu dosyayı ekler; brief her aday için `kalip`, `ek` ve `stil` seçer. Yalnız kalıp alınır: kişi yüzü, logo ve tasarım kopyalanmaz.

## Kalıp seçimi
| `kalip` | Ne zaman | `satir1` / `satir2` | `ek` | Zemin |
|---|---|---|---|---|
| `klasik` | Varsayılan: tek araç, haber, merak. Referansların %25'i | 2-4 kelime, öznenin karşı yanında | yok | Özne bir yanda, karşı üçte bir boş |
| `dev-yazi` | Kısa ürün ya da model adı duyurusu | Altta 1-3 kelime | Öznenin arkasındaki dev söz: 1 kelime ya da sayı ("4K!") | Özne ortada, başın üstü ve yanları boş, sade zemin |
| `alt-bant` | İfşa, sonuç, vaka: tek güçlü söz | Altta dev 1-3 kelime ("İFŞA OLDU") | Sol üstte küçük yardımcı satır, isteğe bağlı | Özne üst üçte ikide, alt üçte bir koyu ve boş |
| `bolunmus` | Önce/sonra, ucuz/pahalı, iki modelin karşılaştırması | `satir1` sol yarının, `satir2` sağ yarının etiketi; 1-2 kelime | yok | Kare ortadan ikiye bölünmüş iki zıt sahne |
| `rozet` | Gün ya da bölüm sayan seri, sahnenin kendini anlattığı video | Sağ üstte 1-2 kelime ("115. GÜN") | yok | Tek dramatik eylem, özne büyük, sağ üst sakin |
| `not` | Bir şeyi işaret eden açıklama, kanıt | Altta 1-2 kelime | 1-3 kelimelik el yazısı not ("hepsi burada") | Alt üçte bir koyu, sol üst boş |
| `yazisiz` | Görsel aksiyon tek başına anlatıyorsa | çizilmez | yok | Özne karenin çoğunu doldurur |

## Ölçülü kurallar (referanslardan)
- Yazılı kapaklarda ortalama 3 kelime; toplam (iki satır + ek) en çok 5. Daha fazlası `vedit kapak` ölçümünde uyarı verir.
- En büyük yazının harf yüksekliği kare yüksekliğinin en az %8'i (akışta 168×94 px'e iner).
- Özne karenin %35-55'i; yazı %15-30'u. `rozet` ve `yazisiz` kalıbında özne %50-85.
- İfade: sakin, ciddi ya da hafif gülümseme. Abartılı şok ifadesi varsayılan değil (referansların çoğunda yok).
- Bir kapakta tek ok. Sağ alt köşe (süre rozeti) her kalıpta boş.
- Başlık kapağı tekrar etmez: kapak sözü başlığın açtığı soruyu keskinleştirir.

## Yazı stili (`stil`)
| `stil` | Görünüm | Zemin |
|---|---|---|
| `turuncu` | Beyaz yazı, turuncu vurgu, siyah kontur (proje varsayılanı) | her zemin |
| `kirmizi-kutu` | Beyaz yazı, ikinci satır kırmızı kutuda | koyu |
| `beyaz-kontur` | Tek renk beyaz, kalın siyah kontur; `rozet` ve `bolunmus` ile | gerçek sahne |
| `sari-vurgu` | Beyaz yazı, sarı vurgu | koyu ya da sahne |
| `mavi-kutu` | Beyaz yazı, son söz mavi kutuda | koyu |
| `acik-siyah` | Siyah yazı, vurgu mavi kutuda, kontursuz | yalnız açık zemin |
| `serif-karisik` | Sade sans + italik serif vurgu, küçük harf, kontursuz | koyu, sade |

Aynı kanalın kapakları aynı stili kullanır: stüdyo `studios/<stüdyo>/kapak.json` (`{"stil": "..."}`) ile stilini sabitlerse brief'in önerisi ezilir.
