# STYLE — sert-isik-gercekcilik

> Kaynak referanslar: `Projeler/inputs/_referanslar/instagram/sert-isik-gercekcilik/analysis/images-grid.jpg` (39 kare), `analysis/digest.md` ve önceki katalog kaydı (`huashu-art-motion 风格配方/24_hopper.md`, MIT, ADR 0042) · Güncelleme: 2026-11-23.
> Tek cümlelik kimlik: "Koyu arayüz zemininde sert ışık-gölge kontrastı, parlak terminal yeşili tek ana vurgu, kriz anlarında kırmızı uyarı katmanı ve ara sıra gelen açık belge kesmeleriyle yüksek kontrastlı teknik anlatım."

## 1. Ruh hâli ve kitle
- Sıfatlar: keskin ama soğuk/mekanik değil · teknik ama kuru değil · yüksek kontrastlı ama karmaşık değil (`images-grid.jpg` gözlemi).
- İzleyici ve izleme ortamı: Instagram Reels izleyicisi, mobil dikey ekranda hızlı tarayan, teknik ya da fikir odaklı anlatımları yüksek görsel netlikle takip eden kitle `(çıkarım)`.

## 2. Palet (tokens.json → colors)
| Rol | Hex | Nerede | Not |
|---|---|---|---|
| bg | `#0B0F13` | koyu arayüz ve sahne zemini | `images-grid.jpg` koyu karelerden ölçüldü |
| surface | `#141B22` | yüzen cam kartlar, terminal ve pencere panelleri | `images-grid.jpg` arayüz panellerinden ölçüldü |
| fg | `#F2F4F7` | ana başlık ve beyaz gövde metni | `bg` ile kontrast > 17:1 |
| muted | `#8B98A5` | pencere üst çubuğu, teknik etiketler, ince ızgara çizgileri | `bg` ile kontrast > 6:1 |
| accent | `#2EE87A` | aktif vurgu kelimesi, onay damgası, yükseliş grafiği | sahne başına tek ana vurgu, lokal parıltılı |
| accent2 | `#E63939` | kriz anı, alarm saati, kırmızı damga ve kenar notu | yalnız gerilim veya hata anında kullanılır |
| on_accent | `#0B0F13` | `accent` dolgusu üzerindeki koyu metin | yüksek okunurluk kontrastı |
- Renk oranı: koyu sahnelerde yaklaşık %72 `bg`, %15 `surface`, %9 `fg`, %4 `accent`/`accent2`; kontrast kırılımı için karelerin yaklaşık %18'inde açık kâğıt/belge kesmesi (`#ECEEEB` zemin, `#141B22` koyu metin) kullanılır (`images-grid.jpg` 39 kareden 7'si).
- Veri ve vurgu renkleri: `#2EE87A` (olumlu/aktif), `#E63939` (uyarı/kriz), `#E07843` (izometrik maskot ve sıcak blok), `#F2C14E` (ikaz şeridi ve sıcak vurgu).

## 3. Tipografi (fonts.json'dan, TR glif doğrulanmış)
- Display: `Space Grotesk` 700 (referanstaki kalın geometrik sans başlık karşılığı `(çıkarım)`), dar harf aralığı (`-0.02em` `(çıkarım)`), normal cümle düzeni; kriz ekranlarında tamamı büyük harf.
- Body ve Mono: gövde ve arayüz kartlarında `Inter` 500–600; terminal başlıkları, zaman damgaları, metrik etiketleri ve kod bloklarında `JetBrains Mono` (tabular rakam); el yazısı kenar notu gerekirse `Caveat` `(çıkarım)`.
- Ölçek (1080p kısa kenar `(çıkarım)`): başlık 72–96 px, ara başlık 48–60 px, gövde/kart 28–36 px, mono etiket 20–24 px.
- Metin yoğunluğu: kare başına ortalama 2–10 kelime, satır uzunluğu en çok 28 karakter (`images-grid.jpg` tipografi karelerinden ölçüldü).

## 4. Kompozisyon ve kadraj
- Konuşan kafa kareleri: konuşmacı merkezde, mikrofon alt köşede; sol ve sağ yanlarda yarı saydam koyu cam bilgi rozetleri yüzü kapatmadan asılır (`images-grid.jpg` 1–6. kareler).
- Grafik ve arayüz kareleri: üstte ince uygulama/terminal çubuğu, merkez odaklı diyagram ya da iki sütunlu yerleşim (solda kalın cümle, sağda liste/grafik/diyalog); 9:16 dikey kurguda kenarlardan en az %6 güvenli boşluk bırakılır `(çıkarım)`.
- Derinlik: düz koyu zemin üzerinde ince teknik kılavuz çizgileri, 1–2 px çerçeveli kartlar ve yalnız aktif öğede yumuşak renk parıltısı (`glow`).

## 5. Doku, ışık, görsel dil
- Doku: temiz koyu dijital yüzey üzerinde çok hafif film greni (`grain: 0.015` `(çıkarım)`), ince perspektif/plan ızgarası ve açık kesme slaytlarında mat belge yüzeyi.
- Çizim dili: 1–2 px ince konturlu teknik çizimler, köşe yarıçapı `radius_u: 0.8`, açılı dikdörtgen onay/uyarı damgaları ve sade izometrik blok illüstrasyonlar.
- Fotoğraf/çekim kullanımı: gerçek çekim konuşan kafa üzerinde koyu yarı saydam cam rozetler; akış şemaları ve belge kesmeleri tam ekran katman olarak girer.
- Üretilen görsel soneki (`gorsel-uret`, yazı gömülmez): koyu arayüz sahnelerinde `high-contrast dark technical studio aesthetic, crisp hard-edged light and deep shadow, clean minimal dark slate surfaces, subtle emerald accent glow, no text`; sakin iç mekân denemelerinde önceki katalog soneki korunur.

## 6. Altyazı ve ekran metni
- Altyazı stilin token'ını alır (ADR 0043): okunan kelime stilin vurgusu (`#2EE87A`), gövde beyaz (`#FFFFFF`), koyu siyah kontur (`#000000`); kutu, pop ve solma yok.
- Ekran içi büyük anlatım cümlelerinde tek anahtar kelime `accent` (`#2EE87A`) ile parlatılır; kriz vurgusunda `accent2` (`#E63939`) devreye girer.

## 7. Yasaklar
- Referans görsellerin kendi içeriğini, marka adlarını veya birebir metinlerini kopyalamak yasak; yalnız görsel gramer alınır.
- Aynı karede ikiden fazla vurgu rengini yarıştırmak, ucuz neon gökkuşağı gradyanı, kalın renkli altyazı kutusu, stok emoji ve 3'ten fazla font ağırlığı kullanmak yasak.
- Konuşmacının yüzünü kapatan arayüz kartı veya güvenli alan dışına taşan etiket yasak.

## 8. Ses kimliği
- Müzik ailesi: düşük yoğunluklu modern elektronik, lo-fi synth veya ritmik minimalist fon, 95–115 BPM `(çıkarım)`.
- SFX karakteri: kuru ve net arayüz tıkları, kısa mekanik damga/bildirim sesi, kriz kesmelerinde sert düşük frekanslı vuruş `(çıkarım)`.

## Dersler
- 2026-11-23 Referans güncellemesi (`images-grid.jpg`, 39 kare): Koyu arayüz zemin (`#0B0F13`), parlak yeşil ana vurgu (`#2EE87A`), kriz kırmızısı (`#E63939`), açık belge kesmeleri (`#ECEEEB`), konuşan kafa üstü cam rozetler ve `Space Grotesk 700` başlık grameri aktif pakete işlendi.
- 2026-11-23 Önceki katalog kuralları (korundu, silinmedi — `huashu-art-motion 风格配方/24_hopper.md`, ADR 0042): Amerikan gerçekçi resminin yalnız ışığı, sert kenarlı ışık bloğu, keskin gölge, düz boyanmış yüzey, sıcak ışık/soğuk gölge yaklaşımı; önceki palet (`#F2C14E` vurgu, `#2A9D8F` ikincil, `#13202B` zemin, `#F4EDE1` yazı, `#7D8C99` soluk), `Playfair Display 700`, yavaş 3.5–6 sn deneme kurgusu, konfeti/neon yasağı ve `quiet realist interior painting style, hard-edged sunlight patches across walls, crisp shadows, flat painted surfaces, warm light and cool shade, solitary mood, no text` soneki sakin deneme varyantı olarak kayıtta tutulur.
