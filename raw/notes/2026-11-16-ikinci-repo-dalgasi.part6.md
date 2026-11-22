# 2026-11-16-ikinci-repo-dalgasi (devam 6)

### 3. Sonuç Tablosu

| Repo | Parça / Teknik | Karar | Neden |
|---|---|:---:|---|
| **claude-motion-design** | `Animated Beam` & `Border Beam` (21st.dev portları) | **AL** | UI kartları arasında akıcı enerji bağı ve modern kenar parıltısı sağlar; bizde benzeri yoktur, saf HTML/CSS ile sıfır bağımlılıkla çalışır. |
| **claude-motion-design** | `seek(t)` render hijyeni (2 rAF + getAnimations kill + log-space zoom) | **AL** | Stüdyomuzun `vedit pano` ve Playwright render kararlılığını artırır; titreme ve font gecikmelerini sıfırlar. |
| **claude-motion-design** | `launch20` tam film şablonu ve Mixkit ses indirme betikleri | **ALMA** | Bizim zaten `vedit final`, `olaysesi` ve `earshot` ses hattımız mevcuttur; paralel ikinci bir render/ses hattı kurmak gereksizdir. |
| **product-launch-motion** | `odometer` (mekanik dikey sayı sayacı) | **AL** | Bizim kütüphanemizde mekanik dönen sayı sayacı eksiktir; slit-clip ve basamak slotu matematiği son derece stabildir. |
| **product-launch-motion** | `edge-split stretch` (çift yaylı uzama) | **AL** | Toggle ve sekmelerin ön/arka kenarının farklı sönümlü yaylarla hareket etmesi arayüze profesyonel kauçuk esnekliği katar. |
| **product-launch-motion** | `one-shape morph` (11 duruma evrilen tek kap) | **KISMEN AL** | Tüm film yerine bağımsız şablon parçaları (örneğin buton → arama → onay hapı) olarak kütüphaneye dahil edilmelidir. |
| **product-launch-motion** | cheeful.ai özel görselleri ve marka renkleri | **ALMA** | Telifli ve projeye özel varlıklardır; kurallarımız gereği marka varlıkları kütüphaneye alınmaz. |
| **motion-video-kit** | 16 Mekanizma Kataloğu (Card stack, Exploded layers, Perspective fold) | **AL** | Kurgu gramerimiz için eşsiz bir referanstır; özellikle kart yelpazesi ve iskelet dolum şablonları kütüphanemizi zenginleştirir. |
| **motion-video-kit** | Three.js telefon donanım spec şablonları | **KISMEN AL** | Three.js modelleri ağırlaşabilir; yalnız 2D düzleme yansıtılan etiketleme (`projected-overlays.js`) mantığı alınmalıdır. |
| **motion-video-kit** | İş teklifi ve fiyatlandırma belgeleri (`business-offers.md`) | **ALMA** | Projemizin teknik motion ve kurgu hattıyla ilgisi olmayan pazarlama metinleridir. |
| **motion-graphics** | B-roll kadraj paylaşım disiplini (cutaway vs saydam panel kuralı) | **AL** | `footage-editing` ve `usta-editor` becerilerimizin konuşan kafa üzerine B-roll ve hareketli grafik yerleştirme kurallarını mükemmelleştirir. |
| **motion-graphics** | `M.scene` / `motion.js` sürükle-bırak ve elastik slider etkileşimleri | **AL** | Saydam B-roll panelleri için parametrik HTML şablonları olarak doğrudan `library/motion/custom/` formatına çevrilebilir. |
| **motion-graphics** | `object-separation` (yerel nesne ayırma betiği) | **ALMA** | Bizde zaten arka plan temizliği ve ayırma işlemleri için ffmpeg/remotion hattı ve remotion-composer mevcuttur. |
| **saas-motion-kit** | 101 Görsel Tema ve 24 Anlatısal Geçiş Atlası | **AL** | `sahne-motoru` becerilerimiz için devasa bir stil kütüphanesidir; tema çeşitliliğini artırır. |
| **saas-motion-kit** | `variety_audit.py` (çeşitlilik denetimi) | **KISMEN AL** | `denetim` becerimize kural olarak eklenip arka arkaya aynı geçişin/yönün kullanılmasını engelleyen bir kontrol mantığı olarak benimsenebilir. |
| **saas-motion-kit** | HyperFrames tam film üretim şablonları | **ALMA** | Projemiz ADR 0021 gereğince Remotion ve `kurgu.json` merkezli çalışmaktadır; HyperFrames yalnızca eski pano hattında sınırlı tutulmalıdır. |
| **snapcn** | `agent-steps`, `terminal-simulator`, `word-flip`, `answer-highlight` | **AL** | Remotion/React ve HTML ortamına en hızlı uyarlanabilecek, yazılım ve AI tanıtımlarında en çok ihtiyaç duyulan bileşenlerdir. |
| **snapcn** | `baseline-pivoted text scaling` ve `geometricPrecision` kuralı | **AL** | Büyüyen ve küçülen tipografideki 0.284px'lik titreme (judder) sorununu 0.014px'e indirir; altyazı ve kinetik tipografimize doğrudan uygulanmalıdır. |
| **snapcn** | Next.js / FumaDocs dokümantasyon altyapısı | **ALMA** | Video editor projemizin çekirdeğiyle ilgisi olmayan web sitesi altyapısıdır. |

---

## beceri

### 1. `opus-video-skills` (`tuzhechen2005/opus-video-skills`, MIT; `ClaudeAnimationBase` türevi MIT)

**(1) Ne yapar, içindeki skill/araç listesi, gereksinimleri**
Kodla (görsel/video/ses modeli kullanmadan, her kare `t` zamanının saf fonksiyonu olarak) baştan sona video üreten iki Claude Code skill'i içerir:
- **`painted-animation`** (`skills/painted-animation/`): `p5.js` + `p5.brush` ile suluboya ve kaynayan mürekkep (boiling ink) çizgi film/müzik videosu üretir.
  - Araçlar/şablonlar: `template/` (`ClaudeAnimationBase` klonu: `render.mjs` Puppeteer paralel kare/sheet/strip/crop render + ffmpeg encode, `src/core.js`, `src/clawd.js`, `src/karaoke.js` KTV tipi iki satırlı ve kelime şakalı/üstünü çizen karaoke katmanı), `scripts/beat_grid.py` (ffmpeg + numpy ile spektral akıdan BPM, vuruş fazı ve `.lrc` satırlarının vuruş indeksini ölçer), `scripts/new_project.sh` (Bash proje kurucu).
- **`kinetic-reel`** (`skills/kinetic-reel/`): 2D Canvas tipografi + Three.js WebGL katmanları (parçacık arazisi, domain-warped sıvı mermer, matcap + ters kabuk konturlu krom torus düğümü, 9k parçacıklı 3D silüet bulutu) + WebGL post-pass (RGB split, slice glitch, grain, vignette, flash) + Node üzerinde sıfırdan sentezlenen vuruş kilitli müzik (`music/score.mjs`) ile portfolyo/showreel üretir.
  - Araçlar/şablonlar: `template/reel/reel.js` (sahne ve geçiş motoru), `template/music/score.mjs` (örneksiz/bağımlılıksız WAV sentezleyici, Freeverb, kick sidechain ducking), `template/render.mjs`, `examples/site-intro/` (web sitesi giriş videosu + Cloudflare Worker HTTP 206 Range).
- **Gereksinimler:** Node.js, Google Chrome (Puppeteer), ffmpeg, Python 3 + `numpy` (`beat_grid.py` için), Bash (`new_project.sh` Windows'ta doğrudan çalışmaz ve ayrı render hattı kurar).

**(2) Bizde karşılığı (`sistem.md`)**
- Render hattı ve kontak sayfası/şerit incelemesi: `vedit` (`hazirla`, `taslak`, `final`, `pano`), Remotion (`studio/remotion/Kurgu.tsx`), `video-izle`, `fizik-sezgisi` (`library/vendor/ClaudeAnimationBase` zaten 2026-11-16'da referans alındı).
- Kinetik tipografi, 3D ve kod sahnesi: `sahne-motoru`, `motion-design`, `bang-motion`, `huashu-art-motion`, `claude-drawing`, 102 kayıtlı `library/motion/custom/`, Three.js + Rapier fizik sahneleri.
- Ritim ve ses: `vedit ritim` (librosa onset/beat), `olaysesi`, `sound-design`, `earshot`.

**(3) Bizden iyi olan somut kural, şablon ya da araç (`dosya:satır`)**
1. **Şekilden şekle süreklilik geçişleri ve 3D→2D ekran izdüşümü (`skills/kinetic-reel/template/reel/reel.js:177-181`, `345-351`, `371-394`):**
   - `trZoom(rect)` (`reel.js:376-382`): Çıkan sahne (A) çizilirken odaklanılan UI kutusunu `RECT` içine kaydeder; geçiş sırasında A son karesinde dondurulup efektleri (`FX`) kapatılır (`reel.js:488`), kamera o kutunun içinden geçerek yeni sahneyi (B) kutunun içinden büyütür.
   - `texWindow(draw, src)` (`reel.js:345-351`): `globalCompositeOperation = 'source-in'` ile 2D tipografiyi WebGL shader katmanına (sıvı mermer vb.) pencere/maske yapar.
   - `cloud.project(i, t, o)` (`reel.js:177-181`): Three.js içindeki 3D parçacığın dünya matrisi ve kamera izdüşümünü hesaplayıp `[x, y]` 2D ekran koordinatı döndürür; böylece 2D Canvas üzerindeki bilgi çizgileri (`thread()`) 3D parçacığa milimetrik değer.
2. **Dürüst veri, uydurma metin yasağı ve `SCHEMATIC` kuralı (`skills/kinetic-reel/SKILL.md:34-37`, `reel.js:352-355`):**
   - Yalnız kaynaktaki gerçek sayılar kapsamıyla yazılır; temsili diyagram/veri gösteriliyorsa HUD'da açıkça `SCHEMATIC` etiketlenir. Gerçek metin uydurmak yerine `redacted(x, y, w, h, seed, col)` (`reel.js:352-355`) ile deterministik yuvarlatılmış blok şeritleri çizilir.
3. **Geçişlerde gürültü (noise whoosh) yasağı ve müzikal geçiş ipuçları (`skills/kinetic-reel/references/sound.md:14-24`):**
   - Uzun videoda her geçişe gürültülü whoosh koymak kulağı yorar (84 saniyede 29 whoosh hatası). Yerine: bölüm başında kesimde bıçak gibi duran ters pad (`swell`), iris geçişte akor çanı (`bloom`), zoom-through'da üçgen dalga kayması (`glide`), panjurda arp (`harp`), kesmelerin yarısında ise **sıfır geçiş efekti** (yalnızca downbeat ve yeni sahnenin kendi giriş tıkı).
4. **Çoklu alt-ajan (subagent) ile uzun kod videosu bölme protokolü (`skills/painted-animation/references/music-video.md:37-50`):**
   - Uzun videoda alt-ajanlara bölüm dağıtırken: önce ana ajan paylaşılan dosyaları ve **en az 1 bitmiş bölümü** referans olarak yazar; alt-ajanlar yalnız kendi IIFE sahne dosyasını düzenler, paylaşılan dosyada hata bulursa düzenlemez raporlar; iş bitince ana ajan tüm **bölüm birleşim yerlerinden (seam)** kontak sayfası alıp palet, karakter ölçeği ve ekran yönü sürekliliğini kendisi düzeltir.
5. **LRC + vuruş fazı tarغı (`skills/painted-animation/scripts/beat_grid.py:24-45`):**
   - Otokorelasyon + tarak filtresiyle (`comb`) şarkının ilk vuruş fazını bulup `.lrc` satırlarının hangi vuruşa (pickup dahil) düştüğünü listeler.

**(4) Alınacak en küçük parça ve nereye**
- `new_project.sh`, `render.mjs` ve `score.mjs` **alınmaz** (`ClaudeAnimationBase` zaten referans alındı, ayrı render hattı kurmak `sistem.md` kabul ölçütüne ve TTS/gerçek kayıt ilkelerine aykırı).
- Yalnız yukarıdaki 4 somut kural/kod deseni mevcut skill dosyalarına eklenir:
  - `trZoom(rect)`, `texWindow`, `cloud.project`, `redacted` ve `SCHEMATIC` kuralı → `.claude/skills/sahne-motoru/SKILL.md` (veya `motion-design` referanslarına).
  - Geçişlerde "noise whoosh yorgunluğu ve %50 boş bırakma / müzikal geçiş" kuralı → `.claude/skills/sound-design/SKILL.md`.
  - Uzun sahnelerde alt-ajan "1 bitmiş bölüm referansı + yalnız kendi dosyasını yazma + seam (birleşim) denetimi" protokolü → `.claude/skills/sahne-motoru/SKILL.md`.

---

### 2. `brag` (`latent-spaces/brag`, MIT; sesler Kenney CC0, müzikler Sascha Ende CC BY 4.0)

**(1) Ne yapar, içindeki skill/araç listesi, gereksinimleri**
Bir yazılım projesinin kaynak kodunu veya canlı web sitesini okuyup 15–25 saniyelik paylaşılabilir ürün tanıtım/lansman videosu (`brag.mp4`), poster karesi (`brag.jpg`) ve sosyal medya paylaşım metni (`share-copy.txt`) üreten iki ajan skill'i içerir:
- **`/brag`** (`skills/brag/`): 4 adımlı (İncele → Planla → Hyperframes'e devret → Doğrula/Render/Teslim et) tam hat.
  - Araçlar ve varlıklar: `scripts/analyze_music_cues.py` (librosa ile tempo, beat ve birleşik yoğunluk puanlı `strongCues` / `windowStrongCues` çıkarıcı), `assets/sfx/` (228 adet Kenney CC0 `.ogg` ses efekti + 32 adet CC0 `keyboard/keypress-*.wav` tekil tuş sesi), `assets/sfx/sfx-analysis.json` ve `sfx-analysis.md` (her SFX için spektral parlaklık, yüksek frekans riski `highFrequencyRisk`, `brightBurden`, `transient.sharpness` analizi), `assets/music/` (5 adet CC BY 4.0 parça ve önceden hesaplanmış `.music-cues.json` dosyaları).
- **`/brag-slim`** (`skills/brag-slim/SKILL.md`): Opus 5.5 / Sonnet 5.5 için Hyperframes veya paketlenmiş varlık olmadan, makinedeki mevcut araçlarla çalışan tek dosyalık yalın sürüm.
- **Gereksinimler:** Node.js 22+, FFmpeg, Hyperframes CLI (`npx hyperframes`), isteğe bağlı Python + `uv` (`librosa`, `numpy`, `scipy`, `soundfile`).

**(2) Bizde karşılığı (`sistem.md`)**
- Hat ve motor: `uretim-hatti`, `vedit` (`hazirla`, `taslak`, `final`, `kapak`, `ritim`), Remotion + OpenMontage (HyperFrames `0.8.181` bizde eski hatta/panolarda var; ana hattımız `vedit` + `kurgu.json`).
- Senaryo, kurgu ve sosyal medya metni: `scriptwriting`, `hikaye-matematigi`, `viral-kurgu` (`yayin.md`), `humanizer`.
- Ses ve SFX: `sound-design`, `olaysesi`, `earshot`, `library/sfx/`.

**(3) Bizden iyi olan somut kural, şablon ya da araç (`dosya:satır`)**
1. **SFX Yüksek Frekans Yorgunluğu (`highFrequencyRisk` / `brightBurden`) Sınıflandırması ve 32'li Tuş Sesi Seti (`skills/brag/assets/sfx/sfx-analysis.md:7-16`, `68-75`, `skills/brag/assets/sfx/sfx-analysis.json`, `skills/brag/assets/sfx/keyboard/`):**
   - Ses efektlerini yalnız "tık / darbe" diye değil, `highFrequencyRisk` (low/medium/high), `brightBurden` (süre × parlaklık) ve `envelopeShape` (transient/textured/continuous) olarak ölçmüş. Kural: Tekrarlanan UI eylemlerinde, metin tıklarında ve sıralı kart girişlerinde **high-risk** ve **continuous bright** sesler kulak yorar; yalnız `low-risk` seçilir (`sfx-analysis.md:69-74`). Ayrıca yazım animasyonunda robotikliği kıran 32 farklı hızda CC0 tuş sesi (`keypress-001..032.wav`) hazır.
2. **Bölgesel Güçlü Vuruş (`windowStrongCues`) Formülü ve Okuma Süresi vs. Beat Grid Kuralı (`skills/brag/scripts/analyze_music_cues.py:86-93`, `117-122` ve `skills/brag/references/step-2-plan.md:126-139`):**
   - `intensity = 0.45 * onset + 0.25 * local_onset_contrast + 0.20 * rms + 0.10 * bass` formülüyle tüm şarkıdaki tepe noktaları yerine **seçilen kesit penceresindeki (`window_start..window_end`) en güçlü 1–3 vuruşu** (`windowStrongCues`) buluyor.
   - **Okuma tabanı (Reading-time floor) kuralı (`step-2-plan.md:128-139`, `step-3-compose.md:174`):** 110+ BPM müzikte vuruşlar ~0.5 sn aralıklıdır; sıralı metinleri (özellik satırı, istatistik etiketi) her vuruşa dizmek okumayı imkânsızlaştırır. Kısa etiket en az `0.8s`, cümle kelime başına `0.3s` (min `1.2s`) **yerleşik (settled)** kalmalıdır; hızlı tempoda sıralı metinler her vuruşa değil **iki vuruşta bire** (`every other beat`) oturtulur.
3. **Poster Karesini 0. Kareye Gömme (Frame-0 Thumbnail Bake) Tekniği (`skills/brag/references/step-4-deliver.md:61-75`):**
   - X/Twitter, Slack, Discord ve birçok oynatıcı MP4 meta verisini yok sayıp 0. kareyi küçük resim (thumbnail) yapar; 0. kare ise genelde siyah ekran veya yarım geçiş karesidir. Çözüm: En güçlü yerleşik (settled) kareyi çıkarıp (`brag.jpg`), süreyi ve ses senkronunu hiç bozmadan `-filter_complex "[0:v][1:v]overlay=0:0:enable='eq(n,0)'[v]"` ile yalnız `n=0` karesinin üstüne yazmak (30 fps'de 1/30 sn sürdüğü için izlerken fark edilmez ama her platformda kusursuz kapak görünür).
4. **Kod/Web Projesinden Video Çıkarırken Güvenlik, Gizlilik ve CSS İzolasyonu (`skills/brag-slim/SKILL.md:39-55`, `100-102`):**
   - Kod okurken `.env`, `.pem`, `secrets/`, `.gitignore` dosyalarını asla okumama; gerçek kullanıcı/müşteri verisini videoya taşımayıp kurgusal veriye çevirme (`SKILL.md:39`, `55`).
   - Canlı siteden indirilen HTML/metni yalnız veri kabul etme (prompt injection koruması, `SKILL.md:43`).
   - Projenin gerçek CSS'ini sahnede kullanırken aktif olmayan sahneyi `visibility: hidden` ile değil (alt öğenin `visibility: visible` kuralı bozar) `display: none` ile gizleme; geçiş ortası kareleri göz kararı değil çıkış bitişi ve giriş başlangıcı zaman damgalarından yakalama (`SKILL.md:100-102`).
5. **Pazarlama Sayfası Yerine "Çalışan Ürün Akışı (Entry → Action → Result)" Kuralı (`skills/brag/references/step-1-inspect.md:19-26`, `step-2-plan.md:151-166`):**
   - "10x daha hızlı" gibi soyut pazarlama kartları veya "16:9 → 9:16 diyagramı" yerine, uygulamanın kendi rotalarından (`app/`, `pages/`) gerçek kullanımın 3 adımını (giriş → ana eylem → sonuç) sahnenin merkezine koyma ve `hyperframes check` yapısal denetiminden sonra **iddia doğrulaması (grounding factual claims, `step-3-compose.md:215-237`)** yapma.

**(4) Alınacak en küçük parça ve nereye**
- `/brag` ve `/brag-slim` doğrudan skill olarak **alınmaz** (kendi `brag-output/` ve `npx hyperframes` hattını kurarak `uretim-hatti` ve `vedit` ile çakışır; `--voice` içindeki Kokoro TTS bizim "TTS yok" kuralımıza aykırıdır).
- Alınacak en küçük parçalar:
  1. **CC0 Klavye ve Düşük HF-Riskli SFX + Analiz Özeti:** `skills/brag/assets/sfx/keyboard/keypress-001..032.wav` (CC0) ve Kenney CC0 seçkisi + `sfx-analysis.json` içindeki `highFrequencyRisk` / `brightBurden` mantığı → `library/sfx/` ve `src/vedit/olaysesi.py` (tekrarlı olaylarda yüksek HF riskli sesleri filtrelemek için) + `.claude/skills/sound-design/SKILL.md`.
  2. **Frame-0 Poster Gömme (`enable='eq(n,0)'`):** Sosyal medya teslimlerinde seçilen kapağı veya en güçlü yerleşik kareyi MP4'ün 0. karesine gömme seçeneği → `src/vedit/` (`teslim` / `final` adımı) ve `.claude/skills/viral-kurgu/SKILL.md`.
  3. **Okuma Tabanı (0.8s / kelime başı 0.3s settled) vs. Hızlı Beat Grid (iki vuruşta bir) ve Ürün Akışı / İddia Doğrulama kuralları:** → `.claude/skills/motion-design/SKILL.md`, `.claude/skills/scriptwriting/SKILL.md` ve `.claude/skills/sanat-yonetimi/SKILL.md`.
  4. **Bölgesel Güçlü Vuruş (`windowStrongCues` birleşik puanlama formülü):** `0.45*onset + 0.25*local_contrast + 0.20*rms + 0.10*bass` → `src/vedit/ritim.py` içine pencere bazlı ana vurgu (`strong_cues`) çıktısı olarak eklenir.

---

### Sonuç Tablosu

| repo | parça | karar (AL / KISMEN AL / ALMA) | neden |
|---|---|---|---|
| `opus-video-skills` | `painted-animation` & `kinetic-reel` tam skill'leri, `new_project.sh`, `render.mjs` | **ALMA** | İkinci bir bağımsız render hattı (Puppeteer + özel klasör) kurar (`sistem.md` kabul ölçütüne aykırı); `ClaudeAnimationBase` motoru zaten `library/vendor/` altında referans alındı; Bash scriptleri Windows'ta doğrudan çalışmaz. |
| `opus-video-skills` | `kinetic-reel/template/music/score.mjs` (Node.js prosedürel müzik sentezleyici) | **ALMA** | Bizde müzikler `library/music/` içinden gerçek parçalarla ve `earshot` denetimiyle seçilir; kodla sentezlenen müzik yapay (AI slop) tınlama riski taşır. |
| `opus-video-skills` | `kinetic-reel` görsel süreklilik desenleri (`trZoom` dondurulmuş A + `RECT` içinden geçme, `texWindow` shader maskeleme, `cloud.project` 3D→2D ekran izdüşümü, `redacted` + `SCHEMATIC` dürüst veri kuralı) | **KISMEN AL** | `reel.js:177-181, 345-394` içindeki 2D+WebGL birleşim ve şekil sürekliliği teknikleri bizdeki `sahne-motoru` ve `motion-design` için doğrudan uygulanabilir, hafif ve somut kod desenleridir. |
| `opus-video-skills` | `kinetic-reel/references/sound.md` geçiş sesi kuralı + `painted-animation/references/music-video.md` alt-ajan (subagent) seam denetim protokolü | **AL** | Geçişlerde "noise whoosh yorgunluğu / kesmelerin yarısını boş bırakma" kuralı (`sound-design`'a) ve uzun kod videolarında alt-ajanların "1 bitmiş referans sahne + seam kontak sayfası" protokolü (`sahne-motoru`'na) mevcut kurallarımızı ölçülebilir biçimde iyileştirir. |
| `brag` | `/brag` ve `/brag-slim` tam skill akışı + Kokoro TTS (`--voice`) | **ALMA** | `uretim-hatti` ve `vedit` yerine `brag-output/` + `npx hyperframes` hattını zorlar; Kokoro TTS kullanımı projedeki kesin "TTS yok" (`CLAUDE.md`) kuralına aykırıdır. |
| `brag` | `assets/sfx/keyboard/` (32 CC0 tuş sesi), Kenney CC0 seçkisi ve `sfx-analysis` (`highFrequencyRisk` / `brightBurden` yorgunluk ölçütü) | **AL** | Tamamı CC0; tekrarlı UI/metin seslerinde kulak yoran yüksek frekanslı (`high-risk` / `continuous bright`) SFX'leri elemek `olaysesi` ve `sound-design` için bizde olmayan çok değerli bir kalite ölçütüdür. |
| `brag` | `step-4-deliver.md:61-75` Frame-0 poster gömme (`overlay=0:0:enable='eq(n,0)'`) | **AL** | Süreyi ve ses senkronunu bozmadan MP4'ün yalnız 0. karesine en güçlü yerleşik kareyi/kapağı gömmek, X/Discord/Slack gibi kapak meta verisini ezen platformlar için `vedit teslim`/`final` adımına eklenecek çok pratik bir çözümdür. |
| `brag` | `scripts/analyze_music_cues.py:76-122` (`windowStrongCues` formülü) + `step-2-plan.md:126-166` (Okuma süresi tabanı vs. hızlı beat-grid kuralı, ürün akışı ve iddia doğrulama) | **KISMEN AL** | Ayrı script kurmak yerine birleşik yoğunluk formülünü (`onset + local_contrast + rms + bass`) `src/vedit/ritim.py`'a; "hızlı tempoda sıralı metni her vuruşa değil iki vuruşta bire diz (min 0.8s settled)" ve "gizlilik/CSS `display:none`" kurallarını `motion-design` ve'a eklemek mevcut hattı çoğaltmadan kaliteyi artırır. |
