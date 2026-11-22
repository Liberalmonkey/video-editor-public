# STYLE — <paket adı>

> Kaynak referanslar: <link/görsel listesi, references/style-grammar.md> · Onay: <tarih, kullanıcı>
> Tek cümlelik kimlik: "<ör. Vox açıklayıcı dilinde, kağıt dokulu, sıcak ve meraklı>"

## 1. Ruh hâli ve kitle
- 3 sıfat (ve karşıtları — "X ama Y değil"): <ör. meraklı ama çocuksu değil · sıcak · güvenilir>
- İzleyici kim, nerede izliyor (mobil/TV), ne kadar dikkat: <…>

## 2. Palet (tokens.json → colors)
| Rol | Hex | Nerede | Not |
|---|---|---|---|
| bg | | arka plan | referansta ölçülen |
| surface | | kart, panel | |
| fg | | ana metin | bg ile kontrast ≥ 7:1 |
| muted | | ikincil metin, eksen | |
| accent | | tek vurgu (rakam, ok, aktif öğe) | sahne başına en fazla 1 vurgu |
| on_accent | | accent üstündeki metin | |
- Renk oranı: <ör. %70 bg · %20 surface · %8 fg · %2 accent>
- Veri renkleri (grafik): <en fazla 3–4 kategorik renk>

## 3. Tipografi (fonts.json'dan, TR glif doğrulanmış)
- Display: <font, ağırlık, harf aralığı, büyük/küçük harf kuralı>
- Body: <font, ağırlık>; Mono/rakam: <tabular rakam gerekir mi>
- Ölçek: başlık / ara başlık / gövde / etiket (1080p px): <…>
- Ekranda aynı anda en fazla <N> kelime; satır ≤ <N> karakter.

## 4. Kompozisyon ve kadraj
- Izgara / güvenli alan: <…>; ana öğe yerleşimi (merkez / üçte bir / sol hizalı)
- Boşluk kuralı: <ör. kenarlardan ≥ 6 %, öğeler arası 1u = 24px>
- Derinlik: düz / hafif gölge / paralaks katmanları

## 5. Doku, ışık, görsel dil
- Doku: <kağıt / grain / temiz vektör / gradient>; grain değeri: <tokens.grain>
- Çizim dili: çizgi kalınlığı, köşe yarıçapı (radius_u), ikon stili (dolu / kontur)
- Fotoğraf/çekim kullanımı: <kolaj kesik, renk derecelendirme, çerçeve>
- İllüstrasyon/karakter: <varsa sabit oranlar, renk>

## 6. Altyazı ve ekran metni
- Stil: <clean-sub | bold-pop | karaoke>, renk (cap_fg / cap_hl / cap_stroke), konum

## 7. Yasaklar
- <ör. neon gradient yok · stok "teknoloji" mavisi yok · 3'ten fazla font ağırlığı yok · emoji yok>

## 8. Ses kimliği (editor — sound için)
- Müzik ailesi: <tür, BPM aralığı, enstrümanlar> · SFX karakteri: <kuru/organik/dijital, yoğunluk>

## Dersler
- <YYYY-MM-DD> <kullanıcının iki kez istediği düzeltme → kalıcı kural>
