# İkinci repo dalgası: karşılaştırma notları (2026-11-16)

Kaynak: Antigravity alt ajanları (hyperframes, hat, motion, beceri), work/agy/2026-11-16-repolar2/sonuc/. Birleştirme aşaması kredi sınırı yüzünden çalışmadı; kararları Claude birleştirip doğruladı (ADR 0040). hat ve motion notları ikinci denemede gemini-3.8-flash-medium ile yazıldı. Not: herk-edit-kit klonu yarıda kaldı (çalışma ağacı boş); o repoya dair iddialar doğrulanamadı ve kullanılmadı.

---

## hyperframes

### 1. Upstream `hyperframes/skills/` İncelemesi (9 Skill)

Upstream `v0.8.204` sonrasında ([weekly-updates.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/weekly-updates.mdx#L232)) 21 eski skill'i daraltıp 9 yayınlanan skill'e indirmiştir ([README.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/README.md#L88-L128)). Bizde kurulu olan 6 skill (`hyperframes-{animation,audio,cli,core,creative,keyframes}`, [skills-lock.json](skills-lock.json#L1-L41)) eski ayrık alan mimarisidir. **Tüm yeni upstream skill'lerinde dikkat edilmesi gereken ortak sorun:** Her birinin başında `npx hyperframes events --skill=<ad>` telemetri beacon zorunluluğu ve `uretim-hatti` / Remotion hattımızla çakışan "varsayılan olarak HyperFrames kullan" talimatı vardır.

1. **`hyperframes`** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/hyperframes/SKILL.md#L1-L79))
   - **Ne yapar:** Bizdeki `hyperframes-core`, `hyperframes-creative`, `hyperframes-animation` ve `hyperframes-keyframes`'i tek giriş kapısında birleştirir; 12 maddelik render sözleşmesini ve `references/` altındaki `format.md`, `motion.md`, `look.md`, `spec.md`, `review.md` dosyalarını tutar.
   - **Bizde karşılığı:** `.claude/skills/hyperframes-{core,animation,creative,keyframes}/` ([hyperframes-core/SKILL.md](.claude/skills/hyperframes-core/SKILL.md#L1-L104)), ayrıca ana hattımızda [motion-design/SKILL.md](.claude/skills/motion-design/SKILL.md#L1-L78)ve [denetim/SKILL.md](.agents/skills/denetim/SKILL.md).
   - **Bizimkinden iyi mi:** Doğrudan skill olarak **hayır** (`disable-model-invocation: true` yok; her video isteğinde `uretim-hatti` ile çakışır ve HyperFrames masaüstü uygulamasını/telemetriyi dayatır). Ancak altındaki 3 referans dosyası bizim mevcut `hyperframes-*` referanslarımızdan daha sıkı ve ölçülüdür:
     - [motion.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/hyperframes/references/motion.md#L8-L43): `0.9.x` ile gelen `data-motion-blur="on"` / `data-motion-blur-tier` kullanımı, sönüm oranına göre yay (spring damping `0.7–0.85` premium, `<0.3` çizgi film) ve 9 nedenli geçiş tablosu (`Zoom through a button`, `Object becomes the world`, `Carry across`, `Dip cut`).
     - [spec.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/hyperframes/references/spec.md#L30-L76): Sıfatları (`premium`, `modern`, `clean`, `dynamic`) sayısal değerlere çevirme tablosu ve "medium-based look" (risograph gibi tek malzeme fiziğinden görünüm kurma).
     - [format.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/hyperframes/references/format.md#L138-L168): Yeni `data-layout-allow-*` denetim istisnaları ve `0.9.x` lint kuralları tablosu.

2. **`hyperframes-cli`** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/hyperframes-cli/SKILL.md#L1-L103))
   - **Ne yapar:** CLI komutlarını (`init`, `lint`, `check --json`, `snapshot`, `timeline move|trim|split|apply`, `render`, `history`) iş bazında özetler.
   - **Bizde karşılığı:** [.claude/skills/hyperframes-cli/SKILL.md](.claude/skills/hyperframes-cli/SKILL.md#L1-L128) + [SKILL.part2.md](.claude/skills/hyperframes-cli/SKILL.part2.md#L1-L79) ve Python sarmalayıcımız [hf.py](src/vedit/hf.py#L1-L50).
   - **Bizimkinden iyi mi:** **Kısmen.** 207 satırdan 103 satıra inmiş (daha az token) ve yeni `timeline move|trim|split|apply` komutlarını içeriyor; ancak telemetri (`events`, `feedback`) ve "projenin kendi script/wrapper'ını kullanma" ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/hyperframes-cli/SKILL.md#L12)) kuralı bizim `vedit` sarmalayıcımıza ters. Yalnız yeni CLI bayrakları mevcut `hyperframes-cli`'ye not düşülebilir.

3. **`hyperframes-registry`** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/hyperframes-registry/SKILL.md#L1-L60))
   - **Ne yapar:** `npx hyperframes catalog --query` ve `npx hyperframes add <name>` ile ~450 hazır blok ve bileşeni (geçiş, alt bant, kinetik tipografi, grafik, 3D) projeye kaynak kod olarak kurar.
   - **Bizde karşılığı:** `library/motion/custom/` (102 kayıt, [motion.py](src/vedit/motion.py#L1-L75)), `library/boards/` (267 pano, [katalog.md](library/boards/katalog.md#L1-L113)), ayrıca arama kuralları bizdeki [.claude/skills/hyperframes-cli/SKILL.md](.claude/skills/hyperframes-cli/SKILL.md#L90-L97) içinde zaten yazılı.
   - **Bizimkinden iyi mi:** **Hayır.** Bizde ayrı skill açmaya gerek yok; katalog araması zaten `hyperframes-cli` içinde anlatılıyor ve ana hattımız kendi `library/motion` + `library/boards` envanterini kullanıyor.

4. **`media-use` (Özel İnceleme)** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/media-use/SKILL.md#L1-L63))
   - **Ne yapar:** `npx hyperframes media-use resolve/generate` ile müzik, SFX, görsel, logo, seslendirme (TTS), avatar video, transkript, arka plan silme (`remove-background`), renk/LUT (`media-treatment`, `grade-compare`) ve ses miksajı (`data-fx-chain`, `data-automation`, `carve.mjs`) yapar.
   - **Bizde karşılığı:** Ses/miks için `olaysesi`, `earshot`, `sound-design`, `vedit miks`, `vedit ayristir`, [.claude/skills/hyperframes-audio/SKILL.md](.claude/skills/hyperframes-audio/SKILL.md#L1-L144); görsel için `gorsel-uret`, `vedit kapak`; transkript için `vedit hazirla` (faster-whisper); ritim için `vedit ritim` ([sistem.md](work/agy/2026-11-16-repolar2/sistem.md#L6-L16)).
   - **Bizimkinden iyi mi:** Skill olarak **hayır ve kabul ölçütüne aykırı**:
     - `npx hyperframes auth login` ile HeyGen oturumu açtırmayı ve HeyGen kredisi harcamayı zorlar; *"Use local tools only when the person asks, not as a fallback"* ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/media-use/SKILL.md#L34-L40)) ve TTS üretimi proje kurallarımıza (`CLAUDE.md`: bütçe 0 USD, TTS yok) doğrudan aykırıdır.
     - Ses miksajı kısmı ([mixing.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/media-use/references/mixing.md#L1-L72)) bizdeki `hyperframes-audio` skill'inin özetlenmiş halidir; bizdeki `hyperframes-audio` çok daha detaylıdır.
     - **Değerli tek yerel parça:** [local.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/media-use/references/local.md#L1-L25) ve [grading.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/media-use/references/grading.md#L48-L95) içindeki tamamen yerel çalışan `npx hyperframes media-treatment` (`data-color-grading` ve `--hf-color-grading-*` CSS değişkenleriyle seek-safe renk/pixelate/kuwahara/bloom/grain animasyonu) ile `npx hyperframes remove-background`. Bu iki yerel komut mevcut `hyperframes-cli`'ye eklenebilir; `media-use` skill'i alınmamalıdır.

5. **`reverse-any-video` (Özel İnceleme)** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/reverse-any-video/SKILL.md#L1-L39))
   - **Ne yapar:** Herhangi bir videoyu kare kare ölçerek düzenlenebilir HyperFrames projesine çevirir (`npx hyperframes reverse start`, `measure cuts`, `measure frames`, `diff <video> <out>`). Ekrandaki konuşmacıyı HeyGen ile yeniden çeker ([start.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/reverse-any-video/references/start.md#L28-L80)).
   - **Bizde karşılığı:** [video-izle/SKILL.md](.agents/skills/video-izle/SKILL.md), `vedit stil-uret`, [style-pack/SKILL.md](.claude/skills/style-pack/SKILL.md#L33-L44).
   - **Bizimkinden iyi mi:** Skill olarak **kabul ölçütüne takılır** çünkü **HyperFrames Pro (ücretli abonelik + HeyGen kredisi)** şart koşar (`npx hyperframes billing subscribe --feature reverse`, `billing add-credits`, [start.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/reverse-any-video/references/start.md#L46-L80)).
   - **Ancak içinden alınacak çok değerli kural/teknik var:** [match.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/reverse-any-video/references/match.md#L1-L39) tamamen ücretsiz/yerel CSS+SVG+GSAP reçeteleri ve ölçüm kuralları içerir:
     - Yazı boyutunu gözle değil kırpılan mürekkep kutusundan (`ink box`) ölçüp `letter-spacing` ile piksel eşleme ([match.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/reverse-any-video/references/match.md#L13-L15)),
     - Yönlü hareket bulanıklığı için simetrik CSS `blur()` yerine SVG `<feGaussianBlur stdDeviation="24 0">` tween'leme ([match.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/reverse-any-video/references/match.md#L34)),
     - Görüntü üstü cam yazı (`Glass type over footage`: SVG `<clipPath>` + `feTurbulence` + `feDisplacementMap`, [match.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/reverse-any-video/references/match.md#L32)),
     - Harf içi süpüren dolgu (`clip-path: inset(0 100% 0 0)` → `inset(0 0 0 0)`) ve ghost trail reçeteleri ([match.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/reverse-any-video/references/match.md#L29-L39)).

6. **`style-sampling` (Özel İnceleme)** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/style-sampling/SKILL.md#L1-L54))
   - **Ne yapar:** 5 hazır kanal şablonundan (`collage-explainer` [Vox], `finance-explainer` [小Lin说], `animated-science-explainer` [Kurzgesagt], `3d-brand-explainer` [Fern], `3d-true-crime` [Fern]) birini `npx hyperframes templates pull <slug>` ile çekip yeni bölüm üretir ([remix.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/style-sampling/references/remix.md#L1-L64)).
   - **Bizde karşılığı:** `vedit stil-uret <stüdyo> <ad>`, `studios/<stüdyo>/styles/<ad>/` ve [style-pack/SKILL.md](.claude/skills/style-pack/SKILL.md#L1-L46).
   - **Bizimkinden iyi mi:** **Hayır, kullanılamaz.** Şablon dosyaları repoda yoktur; `npx hyperframes templates pull <slug>` sunucuda **HyperFrames Pro** planı kontrol eder ve ücretsiz planda `npx hyperframes billing subscribe --feature templates` isteyerek durur ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/style-sampling/SKILL.md#L16-L46)). Üstelik seslendirme ve sunucuyu HeyGen TTS/Avatar IV ile üretir ([remix.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/style-sampling/references/remix.md#L24-L44)). Buna karşılık repodaki ücretsiz 13 tasarım önayarı (`skills/hyperframes/assets/frame-presets/*/FRAME.md`, [look.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/hyperframes/references/look.md#L27-L44)) zaten bizde `.claude/skills/hyperframes-creative/frame-presets/` altında mevcuttur.

7. **`slideshow` (Özel İnceleme)** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/slideshow/SKILL.md#L1-L64))
   - **Ne yapar:** MP4 video yerine `npx hyperframes present` ve `<hyperframes-slideshow>` web bileşeni ile tarayıcıda canlı sunulan, konuşmacı notlu ve tıklanabilir dallanmalı (`hotspots`, `slideSequences`) interaktif sunum destesi üretir; *"Never render a deck to MP4"* der ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/slideshow/SKILL.md#L12-L59)).
   - **Bizde karşılığı:** Video içi sunum panoları için `vedit pano` + `library/boards/` ([katalog.md](library/boards/katalog.md#L1-L6)) ve canlı slayt döngüleri için `loop-flow`.
   - **Bizimkinden iyi mi:** **Hayır.** Projemiz MP4 video üretim stüdyosudur; canlı Meet/Zoom sunum destesi kapsam dışıdır.

8. **`remotion-to-hyperframes`** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/remotion-to-hyperframes/SKILL.md#L1-L51))
   - **Ne yapar:** Remotion (veya Motion Canvas, Lottie, Three.js) kodunu HyperFrames HTML+GSAP kompozisyonuna çevirir ve `npx hyperframes diff` ile kare kare SSIM karşılaştırması yapar.
   - **Bizde karşılığı:** Bizim mimarimiz tam tersi yönde evrildi: ana render motorumuz Remotion 4.0.484 (`studio/remotion/Kurgu.tsx`) ve OpenMontage `SplitReel`'dir; HyperFrames yalnız eski `/video` hattında ve panolarda kullanılır ([sistem.md](work/agy/2026-11-16-repolar2/sistem.md#L8)).
   - **Bizimkinden iyi mi:** **Hayır**, yönü bizim mimarimize terstir.

9. **`figma`** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/figma/SKILL.md#L1-L57))
   - **Ne yapar:** `FIGMA_TOKEN` ile Figma REST API üzerinden varlık, marka token'ı ve bileşen çeker (`npx hyperframes figma asset|tokens|component`).
   - **Bizde karşılığı:** Yok (Görsel/UI üretiminde Stitch MCP ve HTML şablonları kullanıyoruz).
   - **Bizimkinden iyi mi:** Hesap ve kişisel erişim anahtarı (`FIGMA_TOKEN`, bazı özelliklerde Enterprise plan) gerektirir ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/figma/SKILL.md#L16-L23)); şu anki iş akışımızda ihtiyaç yoktur.

---

### 2. `0.8.181` → Güncel Sürüm (`0.9.56` / `0.9.57`) Farkları ve Pano Uyumluluğu

#### a) Kırıcı Değişiklik (Breaking Change) Var mı?
- **`v0.9.0` kırıcı değişikliği yalnız bulut/dağıtık render içindir:** AWS Lambda ve Google Cloud Run dağıtık render'larında `Plan v1` protokolü ve `planProtocol` seçeneği kaldırılıp yalnız `Plan v2` bırakılmıştır ([weekly-updates.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/weekly-updates.mdx#L118-L120)). Biz yerel CLI (`hf.render` / `hf.lint`, [hf.py](src/vedit/hf.py#L31-L50)) kullandığımız için **bizi etkileyen hiçbir kırıcı API değişikliği yoktur**.
- Node.js gereksinimi `>=22` olarak aynıdır ([packages/cli/package.json](work/agy/2026-11-16-repolar2/kaynak/hyperframes/packages/cli/package.json#L108)).

#### b) Yükseltme Bize Ne Kazandırır? (`0.8.181` → `0.9.56`)
1. **Windows Hata Düzeltmeleri (Çok Kritik):**
   - Windows'ta metin etrafındaki **ClearType renk saçaklanması (colour fringes)** düzeltildi (`v0.9.43`, [changelog.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/changelog.mdx#L395-L403)).
   - Windows'ta sesli klip oynayana kadar ses aygıtı açılmayarak uzun donmalar giderildi (`v0.9.43`, [changelog.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/changelog.mdx#L395)).
   - Windows'ta `Dawn DXC` devre dışı bırakılarak WebGPU `requestDevice` hatası çözüldü (`v0.8.193`, [changelog.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/changelog.mdx#L2921)).
   - Windows dosya kilitleri (`debug.log`, geçici tutulan dosyalar), `D:\` gibi kök dizine kayıt, konsol penceresi açılması ve boşluklu/aksanlı dosya adlarında sesin iki kez mikslenmesi düzeltildi (`v0.8.193`–`v0.9.47`, [weekly-updates.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/weekly-updates.mdx#L72), [weekly-updates.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/weekly-updates.mdx#L150), [changelog.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/changelog.mdx#L314-L317)).
2. **Deterministik Render ve GSAP `set` Düzeltmeleri:**
   - GSAP `tl.set()` çağrısının çalışan bir tween'i kesmesi, başka bir özellikteki tween'i başa sarması veya peşinden gelen fade-in'in sonunu silmesi hataları giderildi (`v0.9.6`–`v0.9.26`, [weekly-updates.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/weekly-updates.mdx#L32)). Bizim [build.py](src/vedit/build.py#L178-L293) yoğun biçimde `tl.set` + `tl.fromTo` kullandığı için bu doğrudan kararlılık artışıdır.
3. **Render Hızı ve Yeni Özellikler:**
   - **Gerçek Zamanlı Motion Blur (`data-motion-blur="on"`):** Kök elemana eklendiğinde hızlı hareket eden öğeleri hareket yönünde bulanıklaştırır (`v0.8.190`+, [weekly-updates.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/weekly-updates.mdx#L38-L42), [weekly-updates.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/weekly-updates.mdx#L192-L196)).
   - **Aralık Render'ı ve 1440p Preset:** `hyperframes render --start <s> --end <s>` ile yalnız belirli bir zaman aralığını render etme ve `--resolution 1440p` (`landscape-1440p`, `portrait-1440p`) desteği ([weekly-updates.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/weekly-updates.mdx#L64), [weekly-updates.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/weekly-updates.mdx#L124)).
   - **Performans:** Değişmeyen karelerde BeginFrame ekran görüntüsünü atlama ([weekly-updates.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/weekly-updates.mdx#L70)), doğrusal zamanlı CSS/tag taraması (`v0.9.50`–`v0.9.56`, [changelog.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/changelog.mdx#L70-L73)) ve değişmemiş projede ~1 saniyede çalışan önbellekli `check` ([weekly-updates.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/weekly-updates.mdx#L76)).
   - **9:16 Güvenli Alan Denetimi:** `check` artık 9:16 dikey videolarda güvenli alan dışına taşan metinleri uyarır (`v0.9.44`, [changelog.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/changelog.mdx#L370)).

#### c) Panolarımız (`library/boards`) ve HyperFrames HTML Kompozisyonlarımız Kırılır mı?
- **`library/boards/` (267 pano) kesinlikle kırılmaz:** Çünkü `vedit pano` ([pano.py](src/vedit/pano.py#L14-L129)) HyperFrames CLI'yi **hiç çağırmaz**; doğrudan Python Playwright + yerel Chrome/Edge + `ffmpeg` boru hattıyla `.ebs` sınıflı bağımsız HTML dosyalarını ([D44Line.html](library/boards/boards/D44Line.html#L1-L55)) kare kare yakalar. `library/motion/custom/` ([motion.py](src/vedit/motion.py#L151-L153)) da aynı `pano.render` motorunu kullanır.
- **Eski `/video` hattındaki HyperFrames kompozisyonları ([build.py](src/vedit/build.py#L342-L380)):** `build.py`'nin ürettiği `<div id="root" data-composition-id="main" data-start="0" data-duration="..." data-width="..." data-height="..." data-fps="...">`, `muted playsinline` videolar, `id="master"` ses etiketi ve `window.__timelines["main"] = tl;` yapısı `0.9.56` sözleşmesiyle ([format.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes/skills/hyperframes/references/format.md#L7-L64)) birebir uyumludur. Yalnız bir noktaya dikkat edilmelidir: `build.py` satır 189–197 ve 284–293'te aynı öğe üzerinde `tl.set` ve `tl.fromTo`/`tl.to` kullanıldığında, `0.9.x`'te yeni eklenen lint kuralı *"a `set` that fires inside a running tween on the same property"* ([weekly-updates.mdx](work/agy/2026-11-16-repolar2/kaynak/hyperframes/docs/weekly-updates.mdx#L36)) çakışan zamanlamalarda uyarı/hata verebilir. Ayrıca [package.json](package.json#L9) ile birlikte [src/vedit/hf.py](src/vedit/hf.py#L19) içindeki yedek `hyperframes@0.8.181` sabiti de aynı sürüme güncellenmelidir.

---


## Devamı (ayrı dosyalar)
- `2026-11-16-ikinci-repo-dalgasi.part2.md`
- `2026-11-16-ikinci-repo-dalgasi.part3.md`
- `2026-11-16-ikinci-repo-dalgasi.part4.md`
- `2026-11-16-ikinci-repo-dalgasi.part5.md`
- `2026-11-16-ikinci-repo-dalgasi.part6.md`
