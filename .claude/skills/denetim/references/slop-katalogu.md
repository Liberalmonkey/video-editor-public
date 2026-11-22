# Slop kataloğu

Her satır: işaret → düzeltme. Liste gerekçe zorunluluğudur; bilinçli ve gerekçeli seçim bulgu değildir. Tipografi, renk ve düzen klişelerinin tam listesi: `sanat-yonetimi/references/klise-listesi.md`.

## A. Üretken görüntü kusurları (genelde P0)

| İşaret | Düzeltme |
|---|---|
| Fazla ya da birleşik parmak, bozuk el, kırık eklem | Klibi yeniden üret; eli kadraj dışında bırakan prompt; o aralığı başka malzemeyle kapat |
| Plan içinde kayan yüz, göz, diş | Kısa kes, sağlam kısmı kullan; `loop-flow` karakter referansıyla yeniden üret |
| Anlamsız harfler, bozuk tabela, uydurma logo | Yazısız yeniden üret; yazıyı kurguda gerçek font ile bindir |
| Plastik cilt, aşırı pürüzsüz doku | Gerçek çekim tercih et; yoksa daha kısa ve uzak plan |
| Eriyen nesne, fiziği bozuk hareket | Hareket prompt'unu sadeleştir (tek hareket), ping-pong loop'u gözden geçir |
| Kaynağı olmayan sayı, grafik, ekran görüntüsü | Kaldır ya da gerçek veriyle değiştir; kesik çizgili "bekliyor" kartı (kesin P0) |

## B. Bağlam kopukluğu

| İşaret | Düzeltme |
|---|---|
| Görüntü söyleneni göstermiyor, süs olarak duruyor | Kelimeyi gösteren malzeme: ekran kaydı, belge, ürün, gerçek veri |
| Jenerik metafor: robot eli, parlayan beyin, dijital ağ, kod yağmuru, el sıkışma | Konunun gerçek nesnesi ya da kanıtı (`sanat-yonetimi` klişe listesi) |
| Stok gülümseyen ofis insanları | Kendi çekimin, müşteri ekranı ya da ürün yakın planı |
| Aynı görsel farklı konularda tekrar | Her görseli tek fikre bağla, tekrarı sil |

## C. Şablon düzen

| İşaret | Düzeltme |
|---|---|
| Her sahne ortalı başlık + alt metin | Kenara yasla, ölçek kullan, görseli kadrajdan taşır |
| Eş boy üçlü kart ızgarası | Önem sırasıyla farklı boy; tek kartı öne çıkar ya da `library/boards/katalog.md`'den uygun pano |
| Büyük sayı + küçük etiket + gradyan | Sayıyı ölçekle göster (`P198Odometer`, `C248KPIFocus`), gradyanı kaldır |
| Sebepsiz 01/02/03, süs monospace etiket, cam kart | Sil |
| Mor/çivit gradyan, neon parıltı | Rengi malzemeden türet: çekim, marka, baskı |
| Her sahnede aynı düzen | Bölüm başına bir kez düzen ailesini değiştir |

## D. Hareket

| İşaret | Düzeltme |
|---|---|
| Her öğe aşağıdan fade + slide-up | Girişi anlama göre seç: `motion-design` anlam haritası |
| Her şeyde aynı eğri ve süre | Ağır öğe yavaş kalkar, etiket çabuk gelir; süreleri ayır |
| Back/bounce/elastic pop her yerde | Yalnız tek vurguda bırak |
| Her görselde Ken Burns | Çoğunu sabit tut; gerçek hareketli malzeme ya da düz kesim |
| Arka plan sürekli nefes alıyor, parçacık | Durdur; her sahnede en az 1 sn durgunluk |
| Öğe kelimeden önce ya da çok sonra giriyor | Kelimesine kilitle (en geç 2 sn), `board-sync` ya da elle |

## E. Tutarlılık

| İşaret | Düzeltme |
|---|---|
| Karakter planlar arasında değişiyor | `loop-flow` stil kilidi + karakter referansı ile yeniden üret |
| Her klip ayrı ışık ve renk | Tek renk ayarı; stil kilidini sabitle |
| 2'den fazla font ailesi, karışık vurgu rengi | `STYLE.md` token'larına dön |
| Her motordan farklı görsel dil | `sahne-motoru` görsel dil kuralına dön |

## F. Ses, ritim, yapı

| İşaret | Düzeltme |
|---|---|
| Her kesimde whoosh, her cümlede zoom | `edit/olaylar.json`'dan sil, yalnız kilit vurgu kalsın |
| Eşit süreli planlar | `usta-editor` ritim tablosuna göre yeniden kes |
| Sessizlik yok, müzik baştan sona aynı | Büyük andan önce 0.3–0.6 sn boşluk; müziği bir yerde kes |
| Jenerik motivasyon müziği | Konuya uygun tek enstrüman ya da müziksiz (kulak testi kullanıcıda) |
| Kanca, sorun, üç özellik, logo, CTA; eşit süre | Yapıyı `hikaye-matematigi` ile kır, en güçlü kanıtı öne al |
| "Oyunun kuralları", "bir üst seviye", "hayal edin" | Somut bilgiyle yeniden yaz (`humanizer`); kayıt değişmiyorsa kes |
| Ekrandaki metin sesi birebir tekrar ediyor | Ekrana yalnız sayı ya da anahtar kelime |
