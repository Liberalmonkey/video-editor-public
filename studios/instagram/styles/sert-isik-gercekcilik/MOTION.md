# MOTION — sert-isik-gercekcilik

> Kaynak: `Projeler/inputs/_referanslar/instagram/sert-isik-gercekcilik/analysis/digest.md`, `images-grid.jpg` (39 kare) ve önceki katalog hareket kuralları · Güncelleme: 2026-11-23.
> Hareket kişiliği tek cümle: "Arayüz penceresi gibi net, çabuk oturan keskin girişler; koyu grafik ile açık belge kesmeleri arasında ani kontrast ritmi ve vurgu kelimesinde anlık parıltı."

## 1. Ritim (digest.md kontrolü)
- Ölçüm notu: `digest.md` içinde video zamanlaması yok, yalnız durağan referans ızgarası (`images-grid.jpg`) bulunuyor; bu nedenle aşağıdaki Reels süreleri `(çıkarım)` olarak işaretlenmiştir.
- Ortalama sahne süresi: 1.8–3.0 sn `(çıkarım)` · kesme/dk: 20–32 `(çıkarım)` · görsel kırılım (konuşan kafa ↔ koyu arayüz ↔ açık belge kesmesi) aralığı: 3–5 sn `(çıkarım)`.
- Duraklama: kritik rakam, damga veya kriz başlığından sonra 0.4–0.6 sn nefes; bölüm sonlarında 0.8 sn duruş `(çıkarım)`.

## 2. Anlam haritası (hareket = anlam)
| Anlam | Hareket | Süre (sn) | Easing (tokens.ease) |
|---|---|---|---|
| yeni bilgi girer | 18–24 px dikey kayma ile net opaklık açılışı `(çıkarım)` | 0.35 | text |
| vurgu | anahtar kelimenin `#2EE87A` parıltıya geçişi veya damga basımı `(çıkarım)` | 0.25 | ui |
| karşılaştırma | koyu arayüzden açık belge kesmesine sert kesme veya iki sütunlu açılış `(çıkarım)` | 0.40 | camera |
| sayı / veri | çizgi/çubuk grafik büyümesi ve mono sayaç artışı `(çıkarım)` | 0.65–0.90 | ui |
| çıkış | hızlı sönümleme, giriş süresinin yarısı kadar `(çıkarım)` | 0.20 | exit |
| neden-sonuç | akış şeması düğümleri arasında ince bağlantı çizgisinin çizilmesi `(çıkarım)` | 0.45 | ui |

## 3. Easing tablosu
- `ui` (`power3.out`), `text` (`power4.out`), `camera` (`power2.inOut`), `exit` (`power2.in`), `logo` (`expo.out`) varsayılan değerlerde kalır; `overshoot` ise arayüz disiplinini korumak için `back.out(1.2)` olarak sıkılaştırılır `(çıkarım)`.
- Yasaklar: doğrusal (`linear`) yalnız sürekli kayan ince ızgara veya sayaç akışında kullanılır; aşırı zıplayan `bounce` yasaktır.

## 4. Geçiş aileleri (en fazla 2–3 ana aile)
1. Sert kesme — konuşan kafa, koyu arayüz ve açık belge kesmeleri arasında varsayılan geçiş `(çıkarım)`.
2. Yönlü perde / kaydırma (`gecis-perde-dikey`, `gecis-perde-yatay`, V1 `kay`) — bölüm ve ekran katmanı değişimlerinde.
3. Işık geçişi ve odak kırbacı (`gecis-isik-sizintisi-dikey`, `gecis-isik-sizintisi-yatay`, V1 `isik`, `zoom_kirbac`) — tema veya ton değişiminde (önceki katalog kuralı korundu).
- Kural: aynı geçiş art arda iki kez kullanılmaz; geçişler konu değişiminde kullanılır, cümle içi kesimlerde uygulanmaz (önceki kural korundu).

## 5. Kamera dili
- Konuşan kafa karelerinde jump cut gizlemek ve vurgu vermek için %6–10 oranında kısa punch-in; sakin deneme sahnelerinde %3–5 yavaş `ken_burns` `(çıkarım)`.
- Arayüz ve diyagram sahnelerinde kamera odak noktasına kademeli yaklaşır; konuşan kafa üstü cam rozetlerde hafif derinlik ayrımı korunur, aşırı 3B sallantı yapılmaz `(çıkarım)`.

## 6. Kinetik tipografi
- Metinler kelime veya kısa öbek bazlı `stagger: 0.05` sn aralığıyla girer `(çıkarım)`; aynı anda ekranda en fazla 10 kelime bulunur (`images-grid.jpg` ölçümü).
- Vurgu kelimesi cümle içinde renk (`#2EE87A`, krizde `#E63939`) ve ince parıltıyla ayrılır; harfleri bozan büyük ölçek sıçraması yapılmaz.

## 7. Ses-hareket senkronu
- Cam rozet ve arayüz kartı belirmesi = kısa kuru tık (`pop`/`tick`), damga basımı = mekanik mühür/darbe, büyük ekran kayması = yumuşak kısa `whoosh`, kriz başlığı = sert alt frekans vuruşu `(çıkarım)`.
- Açık belge kesmeleri ve bölüm geçişleri müzik vuruşuna kilitlenir `(çıkarım)`.

## 8. Öncelikli kütüphane klipleri
- Katalogdan korunan öncelikli klipler: `isik-demeti`, `alinti-karti`, `altbant-serit`, `tipografi/kinetik-baslik`, `tipografi/bolum-baslik`, `tipografi/vurgu-soz`, `kart/cta-karti`.
- Bu klipler ve şablonlar `vedit` tarafından paketin paletinden üretilen özel motion temasıyla yeniden renklenir (ADR 0043).

## Dersler
- 2026-11-23 Referans güncellemesi (`images-grid.jpg`, 39 kare): Konuşan kafa üstü cam kart girişleri, akış şeması çizgi çizimi, onay/uyarı damgası, koyu-açık ani kesme ritmi ve `0.35 / 0.20 / 0.05` sn Reels zamanlama hedefleri (`çıkarım`) eklendi.
- 2026-11-23 Önceki katalog kuralları (korundu, silinmedi): Yavaş 3.5–6 sn tempo, ışık lekesinin yüz üstünden yavaş geçişi, sabit kadraj, nadir kesim, sert kenarlı güneş süpürmesiyle geçiş ve `film_yanigi` geçişi sakin deneme sahneleri için geçerliliğini korur.
