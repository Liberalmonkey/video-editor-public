# Motion Grafik Kütüphanesi Kaynak ve Teknik Araştırması (2026-11-13)

Bu araştırma notu, projenin sıfır bütçeli (0 USD), ağdan bağımsız ve sanal saatle deterministik çalışan (`window.seek` / GSAP / CSS) motion sözleşmesine (ADR 0036) uygun yeni teknikleri ve kayıt adaylarını belirlemek için hazırlanmıştır. Mevcut `library/motion/manifest.json` içindeki on kayıt (`ok-ciz`, `daire-ciz`, `alt-cizgi`, `ustunu-ciz`, `onay-tik`, `vurgu-patlama`, `konfeti`, `gecis-sil-dikey`, `gecis-sil-yatay`, `baslik-acilis`) kapsam dışı bırakılmış ve tekrardan kaçınılmıştır.

## 1. Kaynak Tablosu

| Repo | Lisans (Doğrulandı mı) | Maliyet | Ne Alınır | Ne Alınmaz |
| :--- | :--- | :--- | :--- | :--- |
| [bangtutorial/bang-motion](https://github.com/bangtutorial/bang-motion) | MIT ([LICENSE](https://github.com/bangtutorial/bang-motion/blob/main/LICENSE) doğrulandı) | 0 USD (Ücretsiz) | Slayt hissini önleyen sahne sürekliliği kuralları, 5 explainer stili, GSAP kamera (`pan`/`push`) kurgusu ve iki seviyeli tipografi hiyerarşisi. | CDN üzerinden GSAP/font çağrıları ve üçüncü parti telifli karakter görselleri. |
| [alchaincyf/huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion) | MIT ([LICENSE](https://github.com/alchaincyf/huashu-art-motion/blob/main/LICENSE) doğrulandı) | 0 USD (Ücretsiz) | 9 anlatı grameri (Vox, Kurzgesagt, 3B1B, tahta), `CAM.track` kamera ritmi, yaşayan zemin dokuları ve kadraj/altyazı QA kontrol mantığı. | Harici ses/video varlıkları ve çevrimiçi font bağımlılıkları. |
| [cloveric/claude-drawing-skill](https://github.com/cloveric/claude-drawing-skill) | MIT ([LICENSE](https://github.com/cloveric/claude-drawing-skill/blob/main/LICENSE) doğrulandı) | 0 USD (Ücretsiz) | Tohumlu (seeded) deterministik çizim adımları, fırça/mürekkep darbesi sıralaması ve aşamalı çizim (draw-on) kompozisyon kuralları. | Python/Pillow tabanlı raster üretim hattı (projemizde doğrudan HTML/SVG/Canvas kullanılır). |
| [CK42BB/vox-explainer-skill](https://github.com/CK42BB/vox-explainer-skill) | MIT ([LICENSE](https://github.com/CK42BB/vox-explainer-skill/blob/main/LICENSE) doğrulandı) | **Ücretli API** (Atlas Cloud, Seedream, xAI, MiniMax) | **Yalnız fikir alınır:** Vox tarzı yırtık kağıt kenarı, halftone nokta dokusu, kırmızı ip/ok bağlantısı ve gazete kupürü vurgu grameri. | Kod, API çağrıları, TTS/müzik üretim betikleri (bütçe 0 USD kuralı gereği). |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | Apache-2.0 ([LICENSE](https://github.com/heygen-com/hyperframes/blob/main/LICENSE) doğrulandı) | 0 USD (Ücretsiz) | Deterministik kare yakalama mimarisi, sayı sayacı (stat counter), veri görselleştirme ve alt bant (lower-third) zaman çizelgesi kalıpları. | Bulut tabanlı HeyGen servis entegrasyonları. |
| [iart-ai/web-animation-skills](https://github.com/iart-ai/web-animation-skills) | MIT ([LICENSE](https://github.com/iart-ai/web-animation-skills/blob/main/LICENSE) doğrulandı) | 0 USD (Ücretsiz) | Yalnız `transform` ve `opacity` ile 60fps disiplin, SVG `stroke-dashoffset` çizim, yol izleme ve parıltılı cam (`glassmorphism`) panel tekniği. | Next.js/React sayfa geçiş bileşenleri ve uzak Lottie CDN yükleyicileri. |
| [charlie947/motion-graphics-skills](https://github.com/charlie947/motion-graphics-skills) | MIT ([LICENSE](https://github.com/charlie947/motion-graphics-skills/blob/main/LICENSE) doğrulandı) | 0 USD (Ücretsiz) | Lansman kalitesinde sahne ayrıştırma, referans videodan yalnız ritim/tempo çıkarma ve deterministik kodla sahne kurma şablonları. | Marka logolu hazır demo sahneleri. |
| [rough-stuff/rough-notation](https://github.com/rough-stuff/rough-notation) | MIT ([LICENSE](https://github.com/rough-stuff/rough-notation/blob/master/LICENSE) doğrulandı) | 0 USD (Ücretsiz) | El çizimi kutu (`box`), fosforlu kalem (`highlight`) ve köşeli ayraç (`bracket`) için tohumlu çift geçişli SVG bezier sapma algoritması. | Harici paket bağımlılığı (küçük SVG yol üreteci doğrudan şablona gömülür). |
| [maxwellito/vivus](https://github.com/maxwellito/vivus) | MIT ([LICENSE](https://github.com/maxwellito/vivus/blob/master/LICENSE) doğrulandı) | 0 USD (Ücretsiz) | SVG yollarını gecikmeli (`delayed`), eşzamanlı (`sync`) ve tek tek (`oneByOne`) çizdirme zamanlama matematiği. | `requestAnimationFrame` sayacına dayalı eski çalışma zamanı (GSAP/sanal saate çevrilir). |
| [shshaw/Splitting](https://github.com/shshaw/Splitting) | MIT ([LICENSE.md](https://github.com/shshaw/Splitting/blob/master/LICENSE.md) doğrulandı) | 0 USD (Ücretsiz) | Metni kelime/karakter bazında `<span>` öğelerine bölüp `--char-index` CSS değişkeniyle basamaklı (`stagger`) kinetik tipografi kurma tekniği. | Altyazı bandına uygulanması (ADR 0014 gereği altyazı sabittir, yalnız başlıklarda kullanılır). |
| [kiselas/every-frame-is-code](https://github.com/kiselas/every-frame-is-code) | **Doğrulanmadı** ( yalnız dizin sitelerinde MIT yazıyor, repo kökünde doğrulanmadı) | 0 USD (Ücretsiz) | **Yalnız fikir alınır:** UI alt bantları ve kod tabanlı HUD/veri katmanı yerleşim fikirleri. | Doğrudan kaynak kod ve şablon dosyaları (lisans doğrulanmadığı için). |

## 2. Teknik Kartları

### T01 — Fosforlu Kalemle Metin Vurgulama (Marker Highlight Sweep)
- **Ne zaman kullanılır:** Ekrandaki bir alıntı, belge ya da gazete kupürü üzerindeki kritik ifadeyi okurken dikkat çekmek için ([rough-notation](https://github.com/rough-stuff/rough-notation), [vox-explainer-skill](https://github.com/CK42BB/vox-explainer-skill)).
- **Hareketin tarifi:** 1.8 sn toplam süre; 0.0–0.45 sn `power3.out` ile soldan sağa hafif dalgalı iki katmanlı şerit çizimi, 0.45–1.45 sn bekleme, 1.45–1.8 sn `power2.in` ile sağa doğru `clip-path` ile silinerek boş karede bitiş.
- **HTML/CSS/SVG kurulumu:** Saydam zeminde `var(--vurgu)` renginde, `opacity: 0.85` ve `stroke-linecap: square` olan iki üst üste SVG `<path>` öğesi tohumlu hafif Y sapmasıyla üretilir; `stroke-dasharray` ve `stroke-dashoffset` GSAP ana zaman çizelgesiyle sürülür.

### T02 — Yırtık Kağıt ve Halftone Kupür Açılışı (Vox Paper Collage Reveal)
- **Ne zaman kullanılır:** Haber, araştırma ya da kanıt cümlesi ekrana gelirken belgesel/editoryal ağırlık katmak için ([vox-explainer-skill](https://github.com/CK42BB/vox-explainer-skill), [huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion)).
- **Hareketin tarifi:** 2.6 sn; 0.0–0.5 sn `back.out(1.2)` ile hafif eğik (`-2deg`) kağıt katmanının aşağıdan sürülmesi, 0.2–0.6 sn üstündeki metin panelinin belirmesi, 2.2–2.6 sn `power2.in` ile aşağı çekilip saydam kapanış.
- **HTML/CSS/SVG kurulumu:** SVG `<filter>` içinde sabit `seed` değerli `feTurbulence` + `feDisplacementMap` yalnızca giriş karesinde değil statik bir SVG polygon kırpma maskesinde (`clip-path`) kullanılır; zemin `var(--zemin)` dolgulu, üstünde CSS `radial-gradient` ile halftone nokta dokusu ve `var(--yazi)` metin yer alır.

### T03 — Köşeli Ayraç ile Bölge Çerçeveleme (Hand-Drawn Bracket Callout)
- **Ne zaman kullanılır:** Ekran kaydında ya da tabloda birden fazla satırı veya bir paragraf bloğunu gruplayıp göstermek için ([rough-notation](https://github.com/rough-stuff/rough-notation)).
- **Hareketin tarifi:** 2.0 sn; 0.0–0.4 sn sol ve sağ köşeli ayraçların (`[` ve `]`) ortadan uçlara doğru `power2.out` ile çizilmesi ve 8px dışa esnemesi, 0.4–1.6 sn sabit tutuş, 1.6–2.0 sn `power2.in` ile içe kapanıp kaybolma.
- **HTML/CSS/SVG kurulumu:** İki simetrik SVG `<path>` öğesi (`stroke: var(--vurgu)`, `stroke-width: var(--cizgi)`, `fill: none`) `pathLength="1"` tanımlanarak `stroke-dashoffset: 1 -> 0` ile çizilir; yanındaki kısa etiket `var(--zemin)` dolgulu kapsül içinde yer alır.

### T04 — Basamaklı Kelime Maskesi ve Kinetik Başlık (Staggered Split-Mask Typography)
- **Ne zaman kullanılır:** Bölüm başlangıcında ya da vurucu bir iddiayı iki satırlık büyük tipografiyle ekrana sokarken ([Splitting](https://github.com/shshaw/Splitting), [bang-motion](https://github.com/bangtutorial/bang-motion)).
- **Hareketin tarifi:** 2.4 sn; her kelime kendi taşma maskesi (`overflow: hidden`) içinden `0.06 sn` basamak farkıyla (`stagger`) `translateY(110%)` konumundan `0%` konumuna `expo.out` (0.45 sn) ile fırlar, 1.9–2.4 sn yukarı kayarak çıkar.
- **HTML/CSS/SVG kurulumu:** Panelsiz çıplak yazı yasağına uymak için kelimeler `var(--zemin)` dolgulu ve `border-radius: var(--kose)` olan satır kutularının içinde `display: inline-block` olarak dizilir; Türkçe büyük harf dönüşümü `toLocaleUpperCase("tr-TR")` ile yapılır.

### T05 — Odometer Rakam Yuvarlama ve İstatistik Kartı (Deterministic Slot Counter)
- **Ne zaman kullanılır:** Yüzde, para, büyüme oranı ya da sıralama gibi tek bir çarpıcı sayıyı söylerken ([hyperframes](https://github.com/heygen-com/hyperframes), [bang-motion](https://github.com/bangtutorial/bang-motion)).
- **Hareketin tarifi:** 2.5 sn; 0.0–0.35 sn kart `scale(0.92)` -> `1` (`power3.out`) ile açılır, 0.1–1.2 sn rakam sütunları `cubic-bezier(0.16, 1, 0.3, 1)` ile hedef değere yuvarlanır, 1.2–2.1 sn okunur, 2.1–2.5 sn kapanır.
- **HTML/CSS/SVG kurulumu:** Her basamak için `0-9` rakamlarını dikey bir şeritte (`flex-direction: column`) tutan maskeli kutu kurulur; GSAP ile `translateY` değeri hedef basamağın yüksekliği kadar kaydırılır, altında `var(--vurgu)` renkli ince ilerleme çubuğu dolar.

### T06 — Kademeli SVG İkon ve Diyagram Çizimi (Sequential Stroke-Draw Iconography)
- **Ne zaman kullanılır:** Soyut bir kavramı (kilit, grafik, büyüteç, dişli, terazi) konuşma anında sıfırdan çizerek somutlaştırmak için ([vivus](https://github.com/maxwellito/vivus), [web-animation-skills](https://github.com/iart-ai/web-animation-skills)).
- **Hareketin tarifi:** 1.8 sn; dış kontur 0.0–0.5 sn içinde `power2.out` ile çizilirken iç detay çizgileri `0.12 sn` gecikmeyle (`oneByOne` / `stagger`) tamamlanır, 0.5–1.4 sn hafif ölçek nefesi (`1.0 -> 1.03`), 1.4–1.8 sn çözülerek çıkış.
- **HTML/CSS/SVG kurulumu:** Koyu `var(--zemin)` dairesel rozet üstüne yerleşen SVG içindeki tüm `<path>` ve `<circle>` öğelerine `pathLength="100"` verilir; GSAP `stagger: 0.12` ile `strokeDashoffset: 0` hedeflenir, vurgu parçası `var(--vurgu)` ile renklendirilir.

### T07 — Kırmızı İp ve İğne Bağlantı Çizgisi (Red-String Evidence Connector)
- **Ne zaman kullanılır:** Ekranın iki ayrı noktasındaki kavram, kişi ya da veri arasındaki gizli ilişkiyi veya sebep-sonuç bağını gösterirken ([huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion), [vox-explainer-skill](https://github.com/CK42BB/vox-explainer-skill)).
- **Hareketin tarifi:** 2.2 sn; 0.0–0.2 sn A noktasında pim halkası açılır, 0.15–0.7 sn gergin eğrisel çizgi `power2.inOut` ile B noktasına uzanır ve B halkası kapanır, 0.7–1.8 sn sabit kalır, 1.8–2.2 sn B'ye doğru toplanarak silinir.
- **HTML/CSS/SVG kurulumu:** İki uçta `<circle>` (`fill: var(--vurgu)`, `stroke: var(--zemin)`) ve aralarında ikinci dereceden bezier `<path d="M... Q... ...">` kullanılır; kesikli veya düz çizgi animasyonu `stroke-dashoffset` ile sanal saate bağlanır.

### T08 — Parıltılı Koyu Panel ve Alt Bant (Specular Sweep Lower-Third)
- **Ne zaman kullanılır:** Konuşmacı adı, kaynak atfı, bölüm numarası ya da kısa tanım gösterilirken ([web-animation-skills](https://github.com/iart-ai/web-animation-skills), [hyperframes](https://github.com/heygen-com/hyperframes)).
- **Hareketin tarifi:** 3.0 sn; 0.0–0.4 sn sol dikey `var(--vurgu)` barı yukarıdan iner ve `var(--zemin)` panel sağa doğru `expo.out` ile açılır, 0.4–0.9 sn panel üzerinden 45 derecelik ince bir ışık şeridi (`specular sweep`) geçer, 2.5–3.0 sn sola kapanır.
- **HTML/CSS/SVG kurulumu:** `backdrop-filter` yerine her karede deterministik sonuç veren opak `var(--zemin)` (`#0B0D12`) kutu, `1px solid rgba(255,255,255,0.14)` çerçeve ve içinden `translateX(-120% -> 220%)` ile geçen `linear-gradient` parıltı katmanı kullanılır.

### T09 — Çok Katmanlı Geometrik Panjur ve Iris Geçişi (Multi-Layer Shutter & Iris Wipe)
- **Ne zaman kullanılır:** Konu başlığı değişirken ya da "öncesi/sonrası" kurgu kesiminde kesim noktasını (orta kareyi) gizlemek için ([bang-motion](https://github.com/bangtutorial/bang-motion), [motion-graphics-skills](https://github.com/charlie947/motion-graphics-skills)).
- **Hareketin tarifi:** 0.8 sn; 0.0–0.4 sn arasında 4 paralel diyagonal şerit veya dairesel iris `power3.inOut` ile ekranı tamamen kapatır (0.40 sn tam örtme anı), 0.4–0.8 sn aynı yönün devamıyla açılarak son karede tamamen saydamlaşır.
- **HTML/CSS/SVG kurulumu:** Sekans boyutunda (`1080x1920` veya `1920x1080`) `var(--zemin)` ve `var(--vurgu)` renkli SVG `<polygon>` / `<circle>` katmanları `0.04 sn` basamak farkıyla ölçeklenir; orta karede (`t = sure / 2`) alfa boşluğu kalmaması garanti edilir.

### T10 — Kamera İtme ve Odak Penceresi (Active Camera Push & Spotlight Frame)
- **Ne zaman kullanılır:** Bir arayüz, tablo ya da belge üzerindeki tek bir satıra izleyici gözünü kilitlemek için ([bang-motion](https://github.com/bangtutorial/bang-motion), [huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion)).
- **Hareketin tarifi:** 2.2 sn; 0.0–0.45 sn dış çerçeve karartması (%55 opak `var(--zemin)`) ve ortadaki parlak odak penceresi `expo.out` ile hedef bölgeye daralır, 0.45–1.75 sn pencere kenarında `var(--vurgu)` çerçeve parlar, 1.75–2.2 sn açılır.
- **HTML/CSS/SVG kurulumu:** SVG `<mask>` içinde tam ekran beyaz `<rect>` ve odak bölgesini delen siyah `<rect rx="18">` kullanılır; odak penceresinin üst köşesinde `var(--zemin)` dolgulu küçük bilgi etiketi (`window.PARAM.metin`) yer alır.

### T11 — 3B1B Tarzı Denklem ve Şekil Dönüşümü (Morphing Formula & Vector State)
- **Ne zaman kullanılır:** Finansal bir kuralı, matematiksel oranı (`A -> B`) ya da iki kavram arasındaki dönüşümü anlatırken ([huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion)).
- **Hareketin tarifi:** 2.8 sn; 0.0–0.5 sn ilk durum/formül kartı açılır, 0.9–1.5 sn aradaki dönüşüm oku uzarken eski terim `scale(0.8)` + `opacity: 0` ile çekilir ve yeni terim `var(--vurgu)` rengiyle yerine oturur, 2.3–2.8 sn çıkış yapar.
- **HTML/CSS/SVG kurulumu:** Güvenli alanda (`%14–%68` dikey) `var(--zemin)` dolgulu geniş bir kart üzerinde eşit sayıda noktaya sahip iki SVG `<path>` veya CSS `transform` ile eşlenen metin kutuları GSAP zaman çizelgesiyle senkronize edilir.

### T12 — Yaşayan Arka Plan Izgarası ve Hareketli Topografya (Living Blueprint & Grid Loop)
- **Ne zaman kullanılır:** Tam ekran açıklama panolarının, istatistiklerin veya kod sahnelerinin altında statik zemin hissini kırmak için ([huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion), [bang-motion](https://github.com/bangtutorial/bang-motion)).
- **Hareketin tarifi:** 4.0 sn kesintisiz döngü (`loop: true`); izometrik nokta/çizgi ızgarası ve eşyükselti eğrileri 4 saniyede tam bir periyot (`linear` eğri) kayarak başlangıç karesine kusursuz bağlanır (`t=0` ve `t=4.0` aynıdır).
- **HTML/CSS/SVG kurulumu:** Opak `var(--zemin)` katmanı üstüne düşük opaklıklı (`0.08`) SVG `<pattern>` ızgarası ve `var(--vurgu)` (`opacity: 0.18`) renkli `stroke-dasharray` kesişim artıları yerleştirilir; `patternTransform` tam desen boyutu kadar kaydırılır.

## 3. Kütüphaneye Girecek Kayıt Adayları (Öneri Listesi)

| ID | Tür | Ne Zaman Kullanılır (`ne_zaman`) | Süre | Kaynak Fikir |
| :--- | :--- | :--- | :--- | :--- |
| `fosforlu-vurgu` | `overlay` | Ekrandaki bir cümle, alıntı ya da belge satırının üstünü fosforlu kalemle çizerken. | 1.8 sn | `rough-notation` (highlight), T01 |
| `kutu-cerceve` | `overlay` | Bir ekran görüntüsündeki kartı, paragrafı ya da fiyatı el çizimi dikdörtgenle içine alırken. | 2.0 sn | `rough-notation` (box), T01 |
| `koseli-ayrac` | `overlay` | Liste maddelerini veya bir metin bloğunu sol-sağ köşeli ayraçla gruplayıp gösterirken. | 2.0 sn | `rough-notation` (bracket), T03 |
| `kirmizi-ip-bag` | `overlay` | İki ayrı veri, kavram ya da görsel arasındaki sebep-sonuç ilişkisini birbirine bağlarken. | 2.2 sn | `huashu-art-motion`, `vox-explainer-skill`, T07 |
| `odak-pencere` | `overlay` | Kalabalık bir ekran kaydında yalnız tek bir satırı aydınlatıp çevresini hafif karartırken. | 2.2 sn | `bang-motion` (camera spotlight), T10 |
| `buyutec-odak` | `overlay` | Küçük bir detay, ince şart ya da gizli rakamdan bahsederken o noktayı büyütüp vurgularken. | 2.0 sn | `vivus`, `bang-motion`, T06 |
| `soru-isareti-pop` | `icon` | Konuşmada bir ikilem, merak ya da açık soru bırakıldığı anda. | 1.6 sn | `vivus`, `rough-notation`, T06 |
| `unlem-uyari` | `icon` | Kritik bir hata, risk ya da dikkat edilmesi gereken tuzak söylenirken. | 1.6 sn | `vivus`, `web-animation-skills`, T06 |
| `kilit-acilis` | `icon` | Bir sırrın çözülmesi, erişim açılması ya da engelin kalkması anlatılırken. | 1.8 sn | `vivus` (stroke draw), T06 |
| `ampul-fikir` | `icon` | Yeni bir yöntem, ipucu ya da çözüm fikri ortaya atıldığı anda. | 1.8 sn | `vivus`, `claude-drawing-skill`, T06 |
| `artis-ok-grafik` | `icon` | Gelir, hız, verim ya da büyüme artışı vurgulandığında. | 1.8 sn | `hyperframes`, `vivus`, T06 |
| `dusus-ok-grafik` | `icon` | Maliyet düşüşü, kayıp ya da azalma anlatılırken. | 1.8 sn | `hyperframes`, `vivus`, T06 |
| `kronometre-sure` | `icon` | Zaman tasarrufu, geri sayım ya da hız rekoru vurgulanırken. | 1.8 sn | `vivus`, `web-animation-skills`, T06 |
| `terazi-kiyas` | `icon` | İki seçeneğin avantaj ve dezavantajları tartılırken. | 2.0 sn | `vivus`, `huashu-art-motion`, T06 |
| `alt-bant-isim` | `lower-third` | Konuşmacı adını ve unvanını sol vurgulu koyu panelde tanıtırken (`isim`, `unvan` parametreli). | 3.0 sn | `hyperframes`, `web-animation-skills`, T08 |
| `alt-bant-kaynak` | `lower-third` | İddianın dayandığı rapor, makale ya da veri kaynağını sol üst/alt köşede gösterirken. | 2.8 sn | `vox-explainer-skill`, `bang-motion`, T08 |
| `adim-sayaci-etiket` | `lower-third` | Çok adımlı anlatımda "Adım 01 / 03" gibi sıra numarasını ve kısa başlığı gösterirken. | 2.6 sn | `bang-motion`, `hyperframes`, T08 |
| `sayi-sayac-kart` | `overlay` | Tek bir büyük istatistik veya yüzdeyi yuvarlanan rakamlarla ekrana basarken (`deger`, `birim`, `etiket`). | 2.5 sn | `hyperframes` (stat counter), T05 |
| `kupur-alinti-kart` | `overlay` | Haber başlığı ya da kanıt cümlesini yırtık kağıt dokulu ve fosforlu vurgulu kartta gösterirken. | 2.8 sn | `vox-explainer-skill`, `huashu-art-motion`, T02 |
| `kinetik-iki-satir` | `lower-third` | Vurucu bir iddiayı iki satırlık basamaklı kelime maskesiyle güvenli alanda açarken. | 2.4 sn | `Splitting`, `bang-motion`, T04 |
| `karsilastirma-etiket` | `overlay` | "Eski / Yeni" veya "Önce / Sonra" ikilisini yan yana iki koyu rozet olarak gösterirken. | 2.6 sn | `huashu-art-motion` (3B1B/Vox), T11 |
| `formul-donusum` | `overlay` | Bir girdinin çıktıya dönüşümünü (`X -> Y`) ok ve terim değişimiyle gösterirken. | 2.8 sn | `huashu-art-motion` (3B1B), T11 |
| `gecis-panjur-dikey` | `transition` | 9:16 videoda diyagonal çok katmanlı panjur şeritleriyle hızlı sahne geçişi yaparken (ortası 0.4 sn). | 0.8 sn | `bang-motion`, `motion-graphics-skills`, T09 |
| `gecis-panjur-yatay` | `transition` | 16:9 videoda diyagonal çok katmanlı panjur şeritleriyle sahne geçişi yaparken (ortası 0.4 sn). | 0.8 sn | `bang-motion`, `motion-graphics-skills`, T09 |
| `gecis-iris-daire` | `transition` | Odak noktasından büyüyüp kapanan dairesel iris ile dramatik konu geçişi yaparken (ortası 0.4 sn). | 0.8 sn | `huashu-art-motion`, `bang-motion`, T09 |
| `gecis-kagit-yirtik` | `transition` | Belgesel ve explainer kurgusunda yırtık kağıt dokulu katmanla sahne değiştirirken (ortası 0.45 sn). | 0.9 sn | `vox-explainer-skill`, `huashu-art-motion`, T02 |
| `zemin-izgara-akis` | `background` | Açıklama grafikleri ve sayılar altında kesintisiz akan koyu teknik ızgara döngüsü (`loop: true`). | 4.0 sn | `huashu-art-motion`, `bang-motion`, T12 |
| `zemin-nokta-dalga` | `background` | Tam ekran metin ve kartların altında hafif nefes alan halftone nokta matrisi döngüsü (`loop: true`). | 4.0 sn | `vox-explainer-skill`, `web-animation-skills`, T12 |
