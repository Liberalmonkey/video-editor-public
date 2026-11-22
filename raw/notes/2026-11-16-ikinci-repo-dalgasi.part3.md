# 2026-11-16-ikinci-repo-dalgasi (devam 3)

### 3. herk-edit-kit (nateherkai/herk-edit-kit)
* **Lisans:** LİSANS YOK (All Rights Reserved varsayılanı — yalnız fikir alınabilir, kod alınmaz).
* **(1) Ne yapar, mimarisi, gereksinimleri:**
  * *Ne yapar:* Konuşan kafa, reels ve YouTube Shorts için 15 skill'lik AI kurgu iş akışı; transcript güdümlü sessizlik (`cut-silences`) ve hata/kekemelik temizliği (`cut-mistakes`), 406 adet HyperFrames/GSAP hareketli grafik kartı (`registry.json`) ve hareket felsefesi (`MOTION_PHILOSOPHY.md`).
  * *Mimarisi:* Node.js (v22+), Python, HyperFrames, GSAP, FFmpeg.
  * *Gereksinimleri:* Node.js 22+, FFmpeg/FFprobe, Chrome, Git.
* **(2) Bizim vedit hattında karşılığı:**
  * `src/vedit/sessizlik.py` (`oneriler`) ve `src/vedit/oneri.py`
  * `library/checks.md`, `.claude/skills/usta-editor/`, `.claude/skills/motion-design/`
  * `library/motion/` (102 kayıt) ve `studio/remotion/hazirEfekt.json`
* **(3) Bizden ölçülebilir biçimde iyi olduğu somut nokta:**
  * **Onay Kapılı Kekemelik ve Hata Ayıklama (`cut-mistakes`):** Bizim `sessizlik.py:19` yalnız sessizlik ve anlamsız sesleri (`ııı`, `eee`) eler. `cut-mistakes`, transkript üzerindeki kekelemeleri (`kelime- kelime`), anlık kelime tekrarlarını ve yarım kalan cümleleri saptar; retorik vurguları bozmamak için otomatik kesmek yerine bağlamıyla onay kapısına sunar.
  * **Nefes Kuralı ve Kadans Sınırları (`MOTION_PHILOSOPHY.md`):** Ortalama plan uzunluğu 1.0–2.0 saniye ($\le 2$s); her 0.3–0.6 saniyede bir yeni öğe girişi; en kritiği: **7–8 saniyelik yoğun kinetik hareketten sonra mutlaka 1.0 saniyelik durağan dinlenme/nefes anı** bırakılması kuralı.
* **(4) Alınacak en küçük parça ve nereye:**
  * `library/checks.md` içine kural: "YAP: 7-8 saniyelik yoğun kinetik hareketten sonra izleyiciye 1 saniyelik durağan nefes aralığı bırak."
  * `src/vedit/sessizlik.py` içine transkriptteki ardışık kelime tekrarlarını aday listesine `tekrar` türüyle ekleme fikri (kod kopyalanmadan, kendi mantığımızla).

---

### 4. onetake (feitangyuan/onetake)
* **Lisans:** PolyForm Noncommercial 1.0.0 (Ticari kullanım kısıtlı — yalnız fikir alınabilir, kod alınmaz).
* **(1) Ne yapar, mimarisi, gereksinimleri:**
  * *Ne yapar:* Sahnelerin slayt gibi kesilip birbirinin yerine geçmesini önleyen; her sahnenin bir önceki sahnedeki bir elemandan filizlendiği kesintisiz tek plan (one continuous take) ürün lansman ve demo animasyonları üreten Claude Agent Skill'i. 180° sanal örtücü ile gerçek hareket bulanıklığı (motion blur) ve `probe.py` ile sahneler arası süreklilik/taşınma puanı (`carry score`) denetimi yapar.
  * *Mimarisi:* Python 3, Playwright (Chromium), Node.js, FFmpeg, NumPy, SciPy, Pillow, Matplotlib.
  * *Gereksinimleri:* Python 3, Chrome, FFmpeg, Node.js. GPU gerekmez.
* **(2) Bizim vedit hattında karşılığı:**
  * `studio/remotion/Kurgu.tsx`, `library/motion/`, `studio/remotion/hazirEfekt.json`
  * `src/vedit/slop.py` (`RITIM_METRONOM`, `RITIM_ESIT_BLOK`, `STATIK_UZUN`)
  * `.claude/skills/motion-design/SKILL.md`
* **(3) Bizden ölçülebilir biçimde iyi olduğu somut nokta:**
  * **Süreklilik / Taşınma Puanı (Carry Score) Ölçümü (`README.md:58-71`):** İki sahne arasındaki geçişte ekrandaki en az bir nesnenin (çizgi, kutu, kart, metin) biçim değiştirerek bir sonraki sahneye aktarılıp aktarılmadığını puanlar (0.00–1.00; $\ge 0.70$ geçer, $< 0.50$ slayt gösterisi sayılarak reddedilir).
  * **Kadans Çeşitliliği Kuralı (`README.md:70-71`):** Video içindeki en kısa plan ile en uzun plan arasında en az 4 kat ($\ge 4\times$) süre farkı bulunması zorunluluğu.
* **(4) Alınacak en küçük parça ve nereye:**
  * `src/vedit/slop.py` içine `SLAYT_ETKISI` denetimi mantığı: Sahne geçişlerinde hiçbir ortak öğe/yön bağlantısı yoksa ve sahneler birbirini doğrudan ikame ediyorsa uyarı verme fikri.
  * `.claude/skills/motion-design/SKILL.md` ve `library/checks.md` içine kural: "YAP: Sahne geçişlerinde önceki sahneden en az bir görsel öğeyi sonraki sahnenin başlangıcına dönüştürerek taşı."

---

### 5. ffmpeg-skill (kajisho5/ffmpeg-skill)
* **Lisans:** MIT (İzinli)
* **(1) Ne yapar, mimarisi, gereksinimleri:**
  * *Ne yapar:* 42 bağımsız Python script'i ile yerel FFmpeg CLI işlemlerini (kesme, birleştirme, sessizlik temizleme, ses senkronu, LUFS normalizasyonu, renk dönüşümü, altyazı yakma, platform denetimi) yürüten ajan becerisi.
  * *Mimarisi:* Python 3.10+ standart kütüphane sarmalayıcısı + FFmpeg 6.1+.
  * *Gereksinimleri:* FFmpeg 6.1+, FFprobe, Python 3.10+. Bulut ve harici paket gerektirmez.
* **(2) Bizim vedit hattında karşılığı:**
  * `src/vedit/ff.py`, `sessizlik.py`, `teslim.py`, `audio.py`, `kesimqa.py`, `reframe.py`, `olaysesi.py`.
  * ADR 0038 gereği bu skill daha önce reddedilmiştir; çünkü video üretim hattımızın (`uretim-hatti`, `vedit`) üzerine ikinci bir kontrol katmanı açıp çakışma yaratmaktadır.
* **(3) Bizden ölçülebilir biçimde iyi olduğu somut nokta:**
  * **Smart Cut (Akıllı Ara Kare Kesimi) Mantığı (`SKILL.md:100` -> `cut.py --smart`):** Kesim noktaları I-frame (keyframe) üzerine denk gelmediğinde tüm videoyu yeniden kodlamak yerine yalnızca kesim ucundaki açık GOP'u (birkaç kare) yeniden kodlayıp gövdeyi `-c copy` ile kayıpsız ve milisaniyeler içinde birleştirmesi.
  * **iPhone HDR -> SDR Ton Eşleme Parametreleri (`SKILL.md:126-128` -> `color.py --to-sdr`, `--retag bt709`):** iPhone HLG / Dolby Vision çekimlerin standart BT.709 SDR'a solma ve renk bozulması yaşamadan çevrilmesini sağlayan net FFmpeg ton haritalama zinciri. Bizim `teslim.py:56` HDR tespit edip uyarır ama otomatik ton eşleme yapmaz.
* **(4) Alınacak en küçük parça ve nereye:**
  * Skill'in kendisi **KESİNLİKLE ALINMAZ** (ADR 0038 kararı korunur; ajan skill'i olarak eklenmez).
  * Yalnızca `color.py`'deki HDR -> SDR FFmpeg filtre zinciri `src/vedit/ff.py` veya `src/vedit/teslim.py` içine tek bir yardımcı fonksiyon (`sdr_ton_esle`) olarak aktarılabilir.

---

### Sonuç Tablosu

| Repo | Alınacak Parça | Karar | Neden | Lisans Uygun mu |
|---|---|---|---|---|
| **open-edit** | End-card okuma süresi formülü (`0.2s*kelime + 2s/3s + 1s`), 3s dead-air eşiği, yanmış grafik çakışma kuralı | **KISMEN AL** | CLI veya VEED bağımlılığı alınmaz; deterministik kalite denetim matematik formülleri `slop.py` ve `checks.md`'ye doğrudan değer katar. | Evet (Apache-2.0) |
| **rea-video** | `VIDEO.md` katmanlı token mimarisi (özet kartı $\rightarrow$ tek satır plan listesi $\rightarrow$ detay plan) | **KISMEN AL** | Kod veya ağır model bağımlılıkları gereksizdir; katmanlı token yapısı `video-izle` ve `director` analizinde token tasarrufu sağlar. | Evet (Apache-2.0) |
| **herk-edit-kit** | Onay kapılı kekemelik/tekrar temizliği fikri; 7–8s kinetik sonrası 1s nefes kuralı | **KISMEN AL** | Lisansı olmadığı için tek satır kod alınamaz; ancak kurgu ve ritim kuralları `checks.md`'ye fikir olarak aktarılır. | Hayır (Lisans yok, yalnız fikir) |
| **onetake** | Sahneler arası taşınma/süreklilik (carry) ilkesi; plan sürelerinde en az 4x kadans farkı kuralı | **KISMEN AL** | PolyForm Noncommercial lisansı nedeniyle kod alınamaz; "slayt etkisi" uyarısı ve sahne sürekliliği ilkesi `motion-design` ve `slop.py`'ye fikir olarak aktarılır. | Hayır (Noncommercial, yalnız fikir) |
| **ffmpeg-skill** | Yalnızca iPhone HDR $\rightarrow$ BT.709 SDR FFmpeg filtre parametresi | **KISMEN AL** | Skill'in kendisi ADR 0038 gereği reddedilmiştir (`uretim-hatti` ile çakışır); yalnızca eksik olan HDR-SDR dönüşüm filtre parametresi `ff.py`/`teslim.py` için faydalıdır. | Evet (MIT, skill reddedildi / filtre kodu uygun) |

---

## motion

### 1. Klonlanan Repoların İncelemesi

---

#### 1. `claude-motion-design` (Raphaël Aubry / Howseen — MIT)
- **(1) Ne Yapar & Motor:** After Effects veya ücretli araçlar olmadan, tarayıcı içinde saf kodla (deterministic `seek(t)` fonksiyonu) kare kare render alan, ffmpeg ile subframe hareket bulanıklığı (motion blur) uygulayan ve müziğin ölçülen vuruşlarına (beat map / drop) kilitlenen lansman ve tanıtım videosu üretim hattıdır.
  - **Motor:** Saf HTML5, CSS, Canvas/SVG, JavaScript (`window.seek(t)`), Playwright (Chromium) ve ffmpeg `tmix`.
  - **React / Remotion Sürümü:** Yok (Saf JS/Python betikleri).
- **(2) Bileşen ve Sahne Listesi:**
  - `core.js` / `launch20`: Kare bazlı deterministik hareket motoru.
  - `macOS cursor`: Hıza göre eğilen ve basma tepkisi veren sentetik imleç.
  - `makeBadge`: Rozet ve etiket animasyonu.
  - `makeField`: Dairesel ekrana taşma (color flood) alanı.
  - `ui.js`: macOS maketleri (chat, call, notes, files, board, dock ikonları).
  - `Liquid glass`: Canvas displacement ile kırılmalı cam efekti.
  - `Goo / SVG filter`: Sıvı morfolojisi ve eriyerek birleşen şekiller.
  - `6-blade iris`: Diyafram açılış/kapanış geçişi.
  - `Archivo wdth squeeze`: Değişken font genişlik animasyonu (kinetik tipografi).
  - `3D cube`: CSS 3D dönen küp sahnesi.
  - `Equalizer`: Frekans/ses dalgası çubukları.
  - `Blob mask`: Organik sıvı maskeleme.
  - `Animated Beam`: İki UI kartı/noktası arasında akan ışık huzmesi (21st.dev portu).
  - `Border Beam`: Kart sınırında dönen parıltı çizgisi (21st.dev portu).
  - `Masked word-by-word text rise`: Taşma maskesi içinden kelime kelime yükselen metin.
- **(3) Bizim 102 Kaydımızda ve Hazır Efektlerde Karşılığı Olmayanlar:**
  - `isik-demeti` (Animated Beam: iki nokta/kart arası kavisli akan enerji çizgisi).
  - `kenar-isiltisi` (Border Beam: kart etrafında dönen ışık çizgisi).
  - `sivi-morfoloji` (Goo/Blob mask: iki şeklin eriyerek birleşmesi).
  - `renk-tasma-dalgasi` (Color flood: bir noktadan doğup tüm ekranı kaplayan dairesel dalga geçişi).
  - `ses-esitleyici-cubuklar` (Equalizer: ses seviye çubukları).
- **(4) Bizimkinden İyi Kurallar (Dosya:Satır):**
  - `skill/motion-design/SKILL.md:35`: **Logaritmik Kamera Zoomu:** Z ekseninde lineer zoom sahte hissettirir; zoom mutlaka log uzayında enterpole edilmeli (`zoom interpolated in log space`), her vuruşta `+0.012`, drop sonrası bar başına `+0.03` üstel sönen itiş verilmelidir.
  - `skill/motion-design/SKILL.md:38`: **Renk Taşması Geometrisi:** Dairesel dolum sahneyi temizlerken en uzak köşeye olan mesafe `hypot(w, h) * 1.05` formülüyle hesaplanmalı ve tam 0.30–0.35 saniyede ekranı temizleyip bir sonraki nesneye büzülmelidir.
  - `skill/motion-design/SKILL.md:46`: **Render Hijyeni:** `document.fonts.ready` beklenmeli, `document.getAnimations()` durdurulmalı, CSS geçişleri sıfırlanmalı ve her `seek(t)` sonrası **2 requestAnimationFrame (rAF)** beklenmelidir (Chromium headless'ta font ve WebGL kaymasını önler).
  - `skill/motion-design/SKILL.md:78`: **Easing Sıfır Koruması:** Bisection ile çözülen cubic-bezier'lerde x=0 sınırında dönen `1e-9` hatasını önlemek için uç noktalarda kesin 0 ve 1 döndürülmelidir (erken tetiklenen mantık hatalarını önler).
  - `skill/motion-design/SKILL.md:140`: **Adaptif Subframe ve Sert Kesim Koruması:** Piksel hızına göre subframe sayısı dinamik seçilmeli (`ceil(px/5)` ila 64) ve `CUTS` listesiyle **sert kesimlerin üzerinden asla hareket bulanıklığı (blur) geçirilmemelidir**.

---

#### 2. `product-launch-motion` (Muhammad Abubakr / Cheerful — MIT)
- **(1) Ne Yapar & Motor:** Web sitesi ya da ürün hikayesinden, sahneyi hiç kesmeden tek bir kabın (one shape, never cut) durumdan duruma morfolojik olarak evrildiği, müziğin kick/drop ızgarasına kilitli, mikro etkileşimli premium lansman filmleri üretir.
  - **Motor:** Saf HTML5 / JS (`seek(t)`), kapalı form sönümlü yaylar (closed-form damped springs), Playwright subframe yakalama ve ffmpeg `tmix`. (v1'deki GSAP + HyperFrames v2'de saf koda dönüştürülmüştür).
  - **React / Remotion Sürümü:** Yok (Saf JS/Python betikleri).
- **(2) Bileşen ve Sahne Listesi:**
  - `one-shape morph container`: 11 duruma dönüşen tek nesne: Düğme → yükleyici (loader) → onay tiki → dynamic island → video kartı → oran kaydırıcı (slider) → toggle switch → sekme çubuğu (tabs) → mini grafik (chart) → ⌘K komut paleti → toast bildirimi.
  - `odometer`: Rakam genişlikleri oynamayan, dikey yuvarlanan gerçek sayı sayacı.
  - `agent-cursor`: Hıza göre eğilen (lean), isim etiketi ("Cheerful") arkasından gelen, basma ölçeği (`press-scale`) ve yaylanarak sönen ripple halkası üreten dinamik imleç.
  - `cursor trail`: İmlecin hızına göre arkasında beliren şeffaflaşan gradyan iz.
  - `edge-split stretch`: İki kenarı farklı yaylarla hareket ederek uzayan toggle düğmesi ve sekme göstergesi.
  - `content swap with blur`: Eski içeriğin erken bulanıklaşıp çıkması, yenisinin yayla oturması (`vis` fonksiyonu).
  - `logo slam wall`: Müzik vuruşunda tek tek ekrana çarpan müşteri logoları.
- **(3) Bizim 102 Kaydımızda ve Hazır Efektlerde Karşılığı Olmayanlar:**
  - `odometre-sayac` (Odometer: basamak basamak mekanik dönen sayı sayacı).
  - `tek-sekil-morfoloji` (One-shape UI morph: buton → arama → onay → kart dönüşümü).
  - `akilli-imlec-izli` (Agent cursor with trail & lean: dinamik eğilen, iz bırakan, isim etiketli imleç).
  - `esnek-sekme-anahtar` (Edge-split stretch toggle/tabs: ön/arka kenar bağımsız yaylanan sekme/switch).
  - `komut-paleti` (⌘K Command palette arama ve filtreleme kutusu).
  - `dinamik-ada-hap` (Dynamic island / pill morphing notification).
- **(4) Bizimkinden İyi Kurallar (Dosya:Satır):**
  - `references/technique.md:19-24` & `48-51`: **Çift Yaylı Kenar Ayrımı (Edge-split stretch):** `T.tgL` ve `T.tgR` ile ön kenara sert yay (`w:34, z:0.9`), arka kenara yumuşak yay (`w:19, z:0.9`) verilerek arayüz nesnelerine sıvı/lastik esnekliği kazandırılması.
  - `references/technique.md:37-40`: **Bulanık İçerik Takası (`vis`):** İçerik değişirken eski metnin erken ve kısa bulanıklaşarak çıkması, yenisinin yayla gelmesi; metinlerin asla üst üste binmemesi.
  - `references/technique.md:65-68`: **Odometre Basamak Disiplini:** Oransal rakamların zıplamasını engellemek için her basamağa kendi genişliğinde slot ayrılması, dikeyde `clip-path: inset(0 -80px)` ile yalnız dikey kırpılması ve `floor(v/10^p)%10 + max(0, (v%10^p) - (10^p-1))` aktarım formülü.
  - `SKILL.md:31-35`: **Tek Şekil Prensibi:** Sahne kesmek yerine aynı kabın boyut, köşe yarıçapı ve renk değiştirerek yeni sahneye dönüşmesi; boş karelerin hata sayılması.
  - `SKILL.md:108`: **`will-change` Yasağı:** Kameranın ölçeklediği hiçbir elemana `will-change` verilmez; aksi takdirde Chromium metni bulanık rasterize eder.

---

