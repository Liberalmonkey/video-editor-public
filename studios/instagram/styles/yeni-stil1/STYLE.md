# STYLE — yeni-stil1

> Kaynak referanslar: `Projeler/inputs/_referanslar/instagram/yeni-stil1/analysis/images-grid.jpg`, `digest.md` · Onay: 2026-11-23, beklemede
> Tek cümlelik kimlik: "Koyu terminal-UI zeminini açık belge slaytlarıyla kıran, parlak yeşil tek vurgulu, konuşan kafa ile teknik açıklayıcıyı birleştiren keskin teknoloji stili."

## 1. Ruh hâli ve kitle
- 3 sıfat: keskin ama soğuk değil · teknik ama sıkıcı değil · ironik ama dağınık değil.
- İzleyici: Instagram Reels üzerinde mobil dikey ekranda hızlı tüketim yapan teknoloji, yazılım ve yapay zekâ meraklısı kitle; ilk 1,5 saniyede görsel kanca ister `(çıkarım)`.

## 2. Palet (tokens.json → colors)
| Rol | Hex | Nerede | Not |
|---|---|---|---|
| bg | `#0B0F14` | ana koyu zemin, terminal sahneleri | `images-grid.jpg` ölçüldü; kontrast belge slaytlarında `#F1F0EC` açılır |
| surface | `#151B22` | UI penceresi, düğüm kartı, cam panel | `images-grid.jpg` ölçüldü; `1 px` `#242D38` ince kenarlık |
| fg | `#F4F7F5` | ana başlık ve gövde metni | `bg` ile kontrast ~17,8:1 (açık slaytta `#14181D`) |
| muted | `#8B949E` | kod yorumu, ızgara çizgisi, alt etiket | `bg` ile kontrast ~6,2:1 |
| accent | `#2CE66D` | anahtar kelime, onay damgası, yükselen grafik | `bg` ile kontrast ~11,6:1; sahne başına en fazla 1 ana vurgu |
| on_accent | `#0B0F14` | yeşil rozet ve düğme üstü metin | `accent` ile kontrast ~11,6:1 |
- Renk oranı: %68 koyu zemin (`bg`) · %18 panel ve kart (`surface`) · %10 ana metin (`fg`) · %4 vurgu (`accent`); kontrast anlarında açık belge slaytı (`#F1F0EC`) toplam sürenin en çok %20'si `(çıkarım)`.
- Veri ve uyarı renkleri (grafik/hikâye anı): kritik uyarı/hata `#E8453C`, grafik/yol haritası `#5B8DEF`, dikkat bandı `#E8C547`, maskot vurgu `#D97757`.

## 3. Tipografi (`library/fonts/fonts.json`, TR glif doğrulanmış)
- Display: `Space Grotesk`, ağırlık `700`, sıkı harf aralığı `-0.02em`, cümle düzeni (yalnız kısa damga ve kritik uyarı kartlarında BÜYÜK HARF).
- Body: `Inter` (`400–600`); Mono/rakam: `JetBrains Mono` (`tabular-nums` zorunlu; kod satırı, kronometre, saat ve metriklerde). Kenar notlarında ikincil el yazısı `Caveat` kullanılabilir.
- Ölçek (1080×1920 dikey, px): başlık `72–96` · ara başlık `44–56` · gövde `30–36` · mono etiket `20–24` `(çıkarım)`.
- Ekranda aynı anda en fazla `8` büyük anahtar kelime; satır ≤ `26` karakter (arka plandaki silik kod/UI mikro metni hariç).

## 4. Kompozisyon ve kadraj
- Izgara ve güvenli alan: referans kareleri 16:9 olsa da Instagram 9:16 çıktıda üst/alt %14 ve sağ %12 arayüz güvenli alanı korunur `(çıkarım)`.
- Yerleşim: konuşan kafada merkez göğüs planı ve iki yanda yüzen kartlar; açıklayıcı grafiklerde sol hizalı başlık + sağda/altta UI penceresi ya da merkez tek kahraman nesne.
- Boşluk kuralı: kenarlardan ≥ %6 boşluk, öğeler arası `1u = 24 px`, kart içi boşluk `16–24 px`.
- Derinlik: koyu zeminde ince ızgara + yumuşak yeşil radyal parıltı; gerçek çekim üstünde yarı saydam koyu cam (`surface`, `%82` opaklık) kartlar.

## 5. Doku, ışık, görsel dil
- Doku: temiz vektör UI yüzeyi, hafif vinyet ve çok ince film dokusu (`grain: 0.015`).
- Çizim dili: `1–1.5 px` net konturlu pencereler, `radius_u: 1.4` keskin-yumuşak köşeler, ince çizgili teknik ikonlar ve kesikli akış bağlantıları.
- Çekim kullanımı: temiz stüdyo konuşan kafa; hafif soğuk-nötr renk derecelendirme, kameranın üstünde yüzen UI rozetleri ve ekran kesitleri.
- İllüstrasyon/karakter: anlatı sahnelerinde sade geometrik blok figürler (`#D97757`), kalın damga çerçeveleri ve kritik anlarda yüksek kontrastlı kırmızı uyarı kartları.

## 6. Altyazı ve ekran metni
- Stil (ADR 0043): kutusuz, pop ve solma olmadan gömülü temiz altyazı; gövde `#FFFFFF` (`cap_fg`), okunan aktif kelime `#2CE66D` (`cap_hl`), kontur `#000000` (`cap_stroke`), alt-orta güvenli alanda. Referanstaki koyu altyazı bandı ADR 0043 gereği kullanılmaz.

## 7. Yasaklar
- Gökkuşağı/mor-pembe yapay zekâ neon gradyanları yok · kalın gölgeli plastik 3B butonlar yok · aynı karede iki farklı baskın vurgu rengi (acil hata anı dışında) yok · stok emoji yağmuru yok · 3'ten fazla font ağırlığı yok · okunamayan sıkışık kod duvarı yok.

## 8. Ses kimliği `(çıkarım)`
- Müzik ailesi: düşük profilli modern elektronik / synth-pulse, `105–122 BPM`, temiz alt bas ve kısa perküsyon; konuşma altında net ducking.
- SFX karakteri: kuru ve hassas dijital-mekanik sesler (klavye tıklaması, kısa UI pop, ince geçiş whoosh, onay ding, hata buzzer); yoğunluk orta, her önemli görsel değişime bağlı.

## Dersler
- 2026-11-23 İlk sürüm `images-grid.jpg` görsel gramerinden üretildi; video ritmi bulunmadığı için süre ve ses kuralları `(çıkarım)` olarak işaretlendi.
