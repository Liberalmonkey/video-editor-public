# MOTION — yeni-stil1

> Kaynak: `Projeler/inputs/_referanslar/instagram/yeni-stil1/analysis/images-grid.jpg`, `digest.md` (video zaman damgası yok; ritim ve süreler Instagram Reels için çıkarımdır) · Onay: 2026-11-23, beklemede
> Hareket kişiliği tek cümle: "Terminal komutu kadar net giren, kısa duraklarla ritim kuran, koyu-açık sahne kırılımlarıyla dikkati tazeleyen yüksek tempolu teknik kurgu." `(çıkarım)`

## 1. Ritim `(çıkarım)`
- Ortalama sahne süresi: `1.8–2.6 sn` · kesme/dk: `22–32` · pattern interrupt aralığı: `3–4 sn` (konuşan kafa ↔ koyu UI sahnesi ↔ açık belge slaytı değişimi).
- Duraklama: vurgu kelimesi, damga ya da kritik uyarı kartından sonra `0.25–0.4 sn` nefes; bölüm/fikir sonu `0.45 sn`.

## 2. Anlam haritası (hareket = anlam) `(çıkarım)`
| Anlam | Hareket | Süre (sn) | Easing (`tokens.ease`) |
|---|---|---|---|
| yeni bilgi girer | alttan `18 px` kayma + opaklık, UI penceresi çerçeve açılışı | `0.35` | `text` |
| vurgu | anahtar kelime `#2CE66D` parlar veya damga hafif ölçekle oturur | `0.25` | `overshoot` |
| karşılaştırma | koyu terminalden açık belge slaytına sert kesme veya iki kolon açılışı | `0.35` | `camera` |
| sayı / veri | tabular sayaç artışı, çizgi grafiği ve düğüm hattı soldan sağa çizilir | `0.6–0.9` | `ui` |
| çıkış | hızlı aşağı kayma veya keskin opaklık düşüşü (girişin yarısı) | `0.20` | `exit` |
| neden-sonuç | akış şemasında kesikli ok çizilir, hedef kart kenarlığı aydınlanır | `0.45` | `ui` |

## 3. Easing tablosu `(çıkarım)`
- `ui: power3.out`, `text: power4.out`, `camera: power2.inOut`, `exit: power2.in`, `logo: expo.out` (varsayılandan devralınır; hızlı başlangıç ve temiz sönümleme sağlar).
- `overshoot: back.out(1.3)` (`tokens.json` içinde varsayılan `1.5`'ten sıkılaştırıldı): onay damgası, yüzen UI rozeti ve maskot girişinde kontrollü mekanik oturma verir.
- Asla: yaylanan çocuksu `bounce` yok; `linear` yalnız kronometre ibresi, akış noktaları ve sürekli kayan dikkat bandında kullanılır.

## 4. Geçiş aileleri `(çıkarım)`
1. Sert kesme — konuşan kafa ile grafik ekranları arasında varsayılan geçiş.
2. Kontrast kırılımı (koyu `#0B0F14` ↔ açık `#F1F0EC`) — fikir dönüşlerinde ve ironik ters köşe anlarında tam ekran renk sıçraması.
3. Hızlı kamera itmesi / UI zoom-in (`0.25–0.35 sn`) — genel panelden tek kod satırına, grafiğe veya uyarı penceresine odaklanırken.

## 5. Kamera dili `(çıkarım)`
- Konuşan kafada jump cut gizlemek için `%6–10` punch-in; statik grafik ve belge slaytlarında `3–5 sn` boyunca `%3–5` yavaş yaklaşma.
- Paralaks: konuşan kafa önündeki yüzen cam kartlar ana kadrajdan `1.15×` hafif ayrık katmanda durur; terminal arka plan ızgarası sabit veya `0.3×` ağır sürüklenir.

## 6. Kinetik tipografi `(çıkarım)`
- Giriş: kelime veya kısa öbek bazlı satır açılışı; aralık `stagger: 0.05 sn` (`tokens.durations.stagger`), giriş `0.35 sn`, çıkış `0.20 sn`.
- Vurgu kelimesi davranışı: beyaz satır içindeki tek anahtar kelime `#2CE66D` rengine döner ve hafif yumuşak parıltı alır; acil hata anlarında `#E8453C` vurguya veya tam ekran büyük harf uyarı kartına geçilir.

## 7. Ses-hareket senkronu `(çıkarım)`
- Eşleşme: UI penceresi/rozet açılışı = kısa kuru pop/tık · akış hattı çizimi veya terminal satırı = yumuşak mekanik tik · büyük slayt değişimi = kısa sıkı whoosh · damga/uyarı = tok mühür darbesi veya kısa alarm bipi.
- Müzik kilidi: bölüm kırılımları, açık belge slaytına geçişler ve son darbe cümlesi vuruş başına kilitlenir; kritik uyarı anında müzik `0.3 sn` kesilip sessizlik boşluğu bırakılır.

## Dersler
- 2026-11-23 `digest.md` yalnız görsel ızgara içerdiğinden tüm süre, kesme sıklığı ve ses-hareket kuralları Instagram Reels standardına göre `(çıkarım)` olarak tanımlandı; video referansı eklendiğinde ölçümle güncellenecek.
