# 2026-11-16-ikinci-repo-dalgasi (devam 2)

### 3. `hyperframes-community-skills` İncelemesi (8 Skill)

1. **`camera-3d-captions`** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/camera-3d-captions/SKILL.md#L1-L144))
   - **Ne yapar:** Konuşan kafa (talking head) videosunda konuşmacıyı arka plandan ayırıp (`person.webm` alfa matı) kelimeleri 3B uzayda farklı derinliklere (`D = 1250..2400`), konuşmacının **arkasına** (hero kelimeler) ve konuşmacının etrafında dönen 3B halkaya (`Ring3D`) yerleştirir; kamera kelimelerin arasından uçarken alan derinliği (DOF), 15 fps posterize adım ve 7 katmanlı ghost motion blur uygular ([recipes.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/camera-3d-captions/references/recipes.md#L1-L84)).
   - **Ücretli API / Hesap:** **Hayır.** Tamamen ücretsiz ve yerel (`npx hyperframes remove-background` ilk çalışmada ~170 MB yerel model indirir, Python `fonttools`, `brotli`, `numpy`, `pillow`).
   - **Bizde karşılığı:** Standart altyazımız ([sistem.md](work/agy/2026-11-16-repolar2/sistem.md#L13): turuncu `#FF7A00`, Montserrat 800) sabittir; ancak konuşmacının arkasına geçen derinlikli/3B kinetik tipografi ve `Ring3D` motoru bizde yoktur.
   - **Ne alınır:** **KISMEN AL (Motor/Şablon olarak).** Altyazı standardımızı bozmamak için tam skill olarak alınmaz; `assets/kit/{cam3d.js,tables.js,finish.js}`, `scripts/font-metrics.py` ve [recipes.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/camera-3d-captions/references/recipes.md#L1-L84) alınarak `sahne-motoru` / `library/motion` içinde özel "konuşmacı arkası 3B başlık / halka yazı" hero sahne şablonu olarak kullanılır (`prep-take.sh` bash betiği Windows/Python'a kolayca çevrilir).

2. **`day-in-my-life`** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/day-in-my-life/SKILL.md#L1-L111))
   - **Ne yapar:** Kullanıcının yerel `~/.claude/projects/*/*.jsonl` sohbet geçmişini okuyup ajanla geçirdiği bir günü `p5.brush` ile 8 fps kaynayan (boil) iki tonlu mürekkep çizimi ve `scipy` ile sentezlenen yaylı çalgı müziğiyle 60–75 saniyelik filme çevirir.
   - **Ücretli API / Hesap:** **Hayır.** Yerel çalışır; ancak `~/.claude/projects` özel geçmişini okur.
   - **Bizde karşılığı:** Çizim tarafında `claude-drawing` ve `huashu-art-motion` ([sistem.md](work/agy/2026-11-16-repolar2/sistem.md#L16)).
   - **Ne alınır:** **ALMA.** Tek kullanımlık oyuncak/meta senaryodur ("ajan olarak bir günüm"), bizim 3 stüdyomuzun (YouTube animasyon, UGC, Instagram Reels) üretim hattına hizmet etmez.

3. **`duo`** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/duo/SKILL.md#L1-L163))
   - **Ne yapar:** Elde tutulan katlanabilir telefon fotoğrafının (`assets/plate.png`, 1448×1086) sol ve sağ ekran yuvalarına iki HTML ekranı (TikTok vs Reels, ChatGPT vs Claude) gömer.
   - **Ücretli API / Hesap:** **Hayır.**
   - **Bizde karşılığı:** `C246Phone`, `C249VersusCards`, `Y165Devices` panoları ([katalog.md](library/boards/katalog.md#L25-L56)) ve `SplitReel`.
   - **Ne alınır:** **ALMA (Lisans/Telif sorunlu ve dar kapsamlı).** `assets/plate.png` X'te `@A_Kapustin` tarafından paylaşılan bir fotoğraftan izinsiz türetilmiştir ve TikTok/Instagram ticari marka ikonlarını içerir ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/duo/SKILL.md#L154-L162)).

4. **`p5-paint-animation`** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/p5-paint-animation/SKILL.md#L1-L150))
   - **Ne yapar:** `p5.js` (2.3.2, LGPL-2.1) + `p5.brush` (2.2.1, MIT) ile 100% deterministik kodla 3 akış üretir:
     - **Flow A (`handwriting.anim.js`):** Çizgili/düz kağıt üstüne kendi kendine yazılan karakalem/kömür/pastel el yazısı + kamera takibi için `out.track.json` kalem koordinatları ([flows.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/p5-paint-animation/references/flows.md#L6-L34)).
     - **Flow B (`repaint.anim.js`):** Bir fotoğrafı kabadan inceye doğru kendi kendini boyayan fırça darbeli tabloya çevirme (pastel/guaş/kömür, önce özneyi boyayıp `subject-done` karesinde kamerayı geri çekme, [flows.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/p5-paint-animation/references/flows.md#L36-L66)).
     - **Flow C (`render-video.mjs`):** Kısa video klibini ilk kareden kilitlenen fırça kafesi (stroke lattice) üzerinde "titremeyen yaşayan tablo" (living painting) olarak boyama ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/p5-paint-animation/SKILL.md#L114-L140)).
   - **Ücretli API / Hesap:** **Hayır.** Görsel modeli veya API kullanmaz, tamamen çevrimdışı headless Chromium üzerinde deterministik seed ile çalışır ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/p5-paint-animation/SKILL.md#L34-L44)).
   - **Bizde karşılığı:** `claude-drawing` ve `P200LineDraw` / `P227ScribbleFill` ([katalog.md](library/boards/katalog.md#L70-L81)) basit SVG çizgileridir; gerçek `p5.brush` fırça dokusu, fotoğrafı adım adım boyama ve videoyu sabit kafesle tabloya çevirme bizde **yoktur**.
   - **Ne alınır:** **KISMEN AL (Betikler ve Sketch'ler).** `scripts/{render.mjs,render-anim.mjs,render-video.mjs}`, `scripts/sketches/{handwriting.anim.js,repaint.anim.js,video-repaint.anim.js}` ve [flows.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/p5-paint-animation/references/flows.md#L1-L105) alınarak `sahne-motoru` / `claude-drawing` altına entegre edilir (`sh scripts/setup.sh` yerine standart `npm ci` ile Windows'ta doğrudan çalışır).

5. **`prod-by-claude`** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/prod-by-claude/SKILL.md#L1-L95))
   - **Ne yapar:** Strudel (`@strudel/web` 1.3.0) canlı kodlama müzik parçasını çevrimdışı kaydedip her nota çaldığında ilgili kod token'ının parladığı 1080×1080 kare video üretir.
   - **Ücretli API / Hesap:** Yerel render ücretsizdir; ancak dikkat: `snapshot` çağrısında `--describe false` unutulursa kareleri dış sunucudaki modele yükler ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/prod-by-claude/SKILL.md#L76-L77)) ve `@strudel/web` **AGPL-3.0** lisanslıdır ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/prod-by-claude/SKILL.md#L34)).
   - **Bizde karşılığı:** Yok (müzik kütüphaneden seçilir, `ADR 0007`).
   - **Ne alınır:** **ALMA.** AGPL-3.0 bağımlılığı ([sistem.md](work/agy/2026-11-16-repolar2/sistem.md#L21) kabul ölçütü: MIT/Apache-2.0/BSD/ISC/OFL) ve niş Strudel live-coding konusu nedeniyle kapsam dışıdır.

6. **`session-story`** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/session-story/SKILL.md#L1-L100))
   - **Ne yapar:** `day-in-my-life` gibi yerel Claude Code / Codex oturum geçmişini okuyup masa başındaki ajana kağıt uçak, tokmak ve kelebek olarak gelen mesajları suluboya (`p5.brush`) ile canlandırır. Ses için macOS `swift` ya da harici `fluidsynth` + `SOUNDFONT` ister ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/session-story/SKILL.md#L40)).
   - **Ücretli API / Hesap:** **Hayır** (`GEMINI_API_KEY` tanımlıysa `--describe false` verilmezse Gemini'ye kare gönderme riski var, [SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/session-story/SKILL.md#L48-L49)).
   - **Bizde karşılığı:** Yok.
   - **Ne alınır:** **ALMA.** Hem macOS `swift` / `fluidsynth` bağımlılığı Windows'ta kutudan çıktığı gibi çalışmaz hem de kişisel sohbet geçmişi animasyonu stüdyolarımızla ilgisizdir.

7. **`vox-explainer` (Özel İnceleme — Atlas Cloud Kontrolü)** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/vox-explainer/SKILL.md#L1-L232))
   - **Ne yapar:** 60–90 saniyelik Vox "Plain-Sight" kolaj tarzı açıklama videosu üretir: 5 parçalı "storyline mine", 8 adımlı ağırlıklı omurga (`FAMILIAR %15 → DIG %5 → STORY %15 → ARTIFACT %10 → MECHANISM %20 → SECOND WIND %15 → THESIS %10 → CLOSE %10`), gerçek kamu malı arşiv görselleri (Wikimedia Commons, LOC IIIF), 12 fps `stepEase` element hareketi + akıcı kamera, ve sayısal geçiş/ölü zaman kapıları (`seam-stamp.mjs`, `seam-gate.mjs`).
   - **Ücretli API / Hesap (Atlas Cloud durumu):** **Hayır! Bu sürümde Atlas Cloud tamamen kaldırılmıştır.** `skills/vox-explainer/` altındaki tüm dosyalar incelendiğinde hiçbir ücretli API zorunluluğu yoktur; görseller ücretsiz Wikimedia Commons API ve Library of Congress IIIF'ten çekilir ([vox-collage-layout.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/vox-explainer/references/vox-collage-layout.md#L44-L59)), ses ise kullanıcının kendi kaydıdır ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/vox-explainer/SKILL.md#L127-L137)).
   - **Bizde karşılığı:** `explainer-board-*`, [motion-design/SKILL.md](.claude/skills/motion-design/SKILL.md#L1-L78), `hikaye-matematigi` ve `denetim`.
   - **Bizimkinden iyi mi ve ne alınır:** **KISMEN AL (Yalnız Kural, Geçiş Reçeteleri ve Seam Betikleri).** Tam skill olarak alınırsa `uretim-hatti` ve `explainer-board-*` ile ikinci bir hat oluşturur ve TTS adımı içerir. Ancak içindeki şu 4 parça bizim mevcut `motion-design` ve `denetim` kurallarımızdan **ölçülebilir biçimde daha üstündür**:
     1. **Velocity-Matched Transitions & Vector Law** ([motion-continuity.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/vox-explainer/references/motion-continuity.md#L28-L111), [velocity-matched-transitions.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/vox-explainer/references/velocity-matched-transitions.md#L10-L227) ve `velocity-matched-transitions-gsap.md`): Kesim anında hız ve yön eşleme (`power4.in` çıkış + `power4.out` giriş), Z ekseninde ölçek türevi (`d(scale)/dt`) işaret uyumu, 7 somut geçiş/hareket reçetesi (`Zoom-Through`, `Inverse Zoom-Through`, `Continuation Cut`, `Word-Cascade Cut`, `Rack-Focus Blur-Cut`, `Cascade Entry`, `Three-Phase Slide`) ve otomatik geçiş damgalayıcı/doğrulayıcı `scripts/seam-stamp.mjs` + `scripts/seam-gate.mjs`.
     2. **12 fps `stepEase` + Kamera Ayrımı ve Event-Density Kapısı** ([vox-collage-motion.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/vox-explainer/references/vox-collage-motion.md#L3-L78)): Elementlerin 12 fps `stepEase` ile hareket ederken kameranın pürüzsüz akması; piksel farkı (MAD) taramasının yavaş kamera kaymalarında (creep) ölü zamanı kaçırmasını yakalayan **timeline event-density kapısı** (her 3.0 sn pencerede en az 1 ayrık timeline olayı).
     3. **Vox Kolaj Düzeni ve Zoom-in Sözleşmesi** ([vox-collage-layout.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/vox-explainer/references/vox-collage-layout.md#L17-L40), [SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/vox-explainer/SKILL.md#L156-L198)): `Evidence stack`, `Zoom-isolation pair`, `Specimen grid`, `Newsprint layering`, `Circle reveal` reçeteleri ve YouTube animasyon stüdyosu için bir stil paketi (`studios/youtube-animasyon/styles/vox-collage/`).
     4. **Kaynak Madenciliği (Storyline Mine) ve 8 Adımlı Omurga** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/vox-explainer/SKILL.md#L78-L98), [plain-sight-script.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/vox-explainer/references/plain-sight-script.md)): `scriptwriting` ve `hikaye-matematigi` skill'lerimize belgeden/makaleden explainer çıkarma kuralı olarak eklenebilir.

8. **`x-posting-license`** ([SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/x-posting-license/SKILL.md#L1-L103))
   - **Ne yapar:** Herhangi bir X (Twitter) profili için 10.3 saniyelik 3B dönen, parlayan ve imzası yazılan "POSTING LICENSE" kimlik kartı videosu üretir.
   - **Ücretli API / Hesap:** **Hayır** (`api.fxtwitter.com` üzerinden ücretsiz veri çeker; ancak macOS `Snell Roundhand` sistem fontuna ve `PRODUCER_BROWSER_GPU_MODE=hardware` ortamına güvenir, [SKILL.md](work/agy/2026-11-16-repolar2/kaynak/hyperframes-community-skills/skills/x-posting-license/SKILL.md#L25-L38)).
   - **Bizde karşılığı:** `library/motion/custom/` sosyal kartları ve `P209Flip` ([katalog.md](library/boards/katalog.md#L72)).
   - **Ne alınır:** **ALMA (veya yalnız GLSL/3D flip tekniği incelenebilir).** Tek bir X meme şablonudur; doğrudan skill olarak alınmaz.

---

### 4. Sonuç Tablosu

| Öğe | Karar | Neden | Maliyet (Dosya, Bağımlılık) |
|---|---|---|---|
| **npm `hyperframes` (`0.8.181` → `0.9.56`)** | **AL** | Windows ClearType metin saçaklanması, ses aygıtı donması, WebGPU DXC ve dosya kilidi hatalarını çözer; GSAP `tl.set` render tutarlılığı, `data-motion-blur="on"`, `--start/--end` aralık render'ı ve 1440p preset kazandırır. `library/boards` Playwright kullandığı için kırılmaz. | [package.json](package.json#L9) ve [src/vedit/hf.py](src/vedit/hf.py#L19) (2 dosya, yeni bağımlılık yok, mevcut npm paketi güncellenir). |
| **`vox-explainer` (`hyperframes-community-skills`)** | **KISMEN AL** | Atlas Cloud ücreti kaldırılmış (0 USD). Tam skill alınırsa `uretim-hatti` ile çakışır; ancak **Vector Law / 7 Velocity-Matched Transition** (`motion-continuity.md`, `velocity-matched-transitions*.md`), `seam-stamp.mjs` + `seam-gate.mjs`, **12 fps `stepEase` + Event-Density Gate** (`vox-collage-motion.md`) ve **Storyline Mine** kuralları bizdekilerden ölçülebilir biçimde iyidir. | `motion-design`, `denetim`, `scriptwriting` skill'lerine kural ekleme + `seam-stamp.mjs`/`seam-gate.mjs` + isteğe bağlı `vox-collage` stil paketi (~5–6 dosya, ek paket bağımlılığı yok). |
| **`p5-paint-animation` (`hyperframes-community-skills`)** | **KISMEN AL** | Ücretsiz, çevrimdışı ve deterministik (`p5.brush`). Bizde olmayan 3 yetenek katar: kalem takipli gerçek el yazısı (`handwriting.anim.js`), fotoğrafın kendi kendini boyaması (`repaint.anim.js`) ve videoyu sabit fırça kafesiyle titremeyen tabloya çevirme (`render-video.mjs`). | `scripts/render*.mjs` + `scripts/sketches/*.js` + `flows.md` (7 dosya; `p5@2.3.2` ve `p5.brush@2.2.1` npm paketi). |
| **`camera-3d-captions` (`hyperframes-community-skills`)** | **KISMEN AL** | Ücretsiz ve yerel. Standart altyazımızın yerine değil, konuşmacı arkası 3B derinlikli hero başlık, `Ring3D` dönen kelime halkası ve DOF/ghost blur sahneleri için `cam3d.js` motoru ve reçeteleri alınır. | `assets/kit/{cam3d.js,tables.js,finish.js}`, `scripts/font-metrics.py`, `recipes.md` (5 dosya; Python `fonttools`, `brotli`, `pillow` zaten standart/hafif). |
| **Upstream `reverse-any-video`** | **KISMEN AL** | Skill'in kendisi HyperFrames Pro aboneliği ve HeyGen kredisi istediği için **alınmaz**; ancak `references/match.md` içindeki ücretsiz CSS/SVG/GSAP reçeteleri (`ink box` yazı ölçümü, SVG `feGaussianBlur` yönlü motion blur, `feTurbulence` cam yazı) çok değerlidir. | `reverse-any-video/references/match.md`'den [motion-design/SKILL.md](.claude/skills/motion-design/SKILL.md)'ye 1 referans/bölüm ekleme (0 bağımlılık). |
| **Upstream `hyperframes` (ana skill)** | **KISMEN AL** | Tam skill alınırsa her video isteğinde `uretim-hatti` ile çakışır ve telemetri (`events`) çalıştırır. Yalnız `references/{motion.md,spec.md,format.md}` içindeki `0.9.x` `data-motion-blur`, `data-layout-allow-*`, sıfat→sayı tablosu ve 9 geçiş reçetesi mevcut `hyperframes-core`/`-animation` ve `motion-design`'a aktarılır. | Mevcut `.claude/skills/hyperframes-{core,animation}/` ve `motion-design` içinde 3 dosya güncellemesi (0 bağımlılık). |
| **Upstream `media-use`** | **KISMEN AL** | Tam skill HeyGen login/kredi ve TTS dayattığı için **alınmaz** (`CLAUDE.md`'ye aykırı). Yalnız `references/{local.md,grading.md}` içindeki ücretsiz yerel `npx hyperframes media-treatment` (`--hf-color-grading-*` seek-safe shader animasyonu) ve `remove-background` kullanımı mevcut `hyperframes-cli`'ye eklenir. | [.claude/skills/hyperframes-cli/SKILL.md](.claude/skills/hyperframes-cli/SKILL.md) içine kısa bölüm ekleme (0 bağımlılık). |
| **Upstream `hyperframes-cli`** | **KISMEN AL** | Tam skill telemetri ve "proje wrapper'ı (`vedit`) kullanma" dayatır. Yalnız `0.9.x` ile gelen yeni `timeline move|trim|split|apply`, `render --start/--end` ve `check --no-craft/--range` komutları mevcut `.claude/skills/hyperframes-cli/`'ye eklenir. | [.claude/skills/hyperframes-cli/SKILL.md](.claude/skills/hyperframes-cli/SKILL.md) güncellemesi (0 bağımlılık). |
| **Upstream `hyperframes-registry`** | **ALMA** | Katalog arama kuralları bizdeki `hyperframes-cli/SKILL.md` (satır 90–97) içinde zaten var; ana hattımız `library/motion` (102 kayıt) ve `library/boards` (267 pano) kullanıyor. | 0 |
| **Upstream `style-sampling`** | **ALMA** | Şablonlar repoda yok; `templates pull` sunucuda ücretli **HyperFrames Pro** aboneliği ve HeyGen TTS/Avatar kredisi zorunlu tutuyor. Bizde `vedit stil-uret` ve `style-pack` var. | 0 |
| **Upstream `slideshow`** | **ALMA** | MP4 video üretmez (`present` ile canlı tarayıcı sunumu yapar); video üretim hattımızın kapsamı dışındadır. | 0 |
| **Upstream `remotion-to-hyperframes`** | **ALMA** | Remotion'dan HyperFrames'e göç aracımız değil, tersine ana motorumuz Remotion 4.0.484 (`Kurgu.tsx`) ve OpenMontage'dır. | 0 |
| **Upstream `figma`** | **ALMA** | `FIGMA_TOKEN` (ve değişkenler için Enterprise plan) ile telemetri beacon'ı gerektirir; mevcut iş akışımızda Figma bağımlılığı yoktur. | 0 |
| **`day-in-my-life` (`hyperframes-community-skills`)** | **ALMA** | Kullanıcının yerel `~/.claude/projects` geçmişinden kişisel "ajanımla bir günüm" filmi yapan tek amaçlı senaryodur; stüdyolarımızla ilgisizdir. | 0 |
| **`session-story` (`hyperframes-community-skills`)** | **ALMA** | Yerel sohbet geçmişi animasyonudur; ses için macOS `swift` veya harici `fluidsynth` + `SOUNDFONT` ister, Windows'ta doğrudan çalışmaz. | 0 |
| **`duo` (`hyperframes-community-skills`)** | **ALMA** | Tek bir X fotoğrafından (`@A_Kapustin`) türetilmiş katlanabilir telefon meme şablonudur; fotoğraf ve TikTok/Instagram ikonları telif/marka açısından sorunludur. | 0 |
| **`prod-by-claude` (`hyperframes-community-skills`)** | **ALMA** | `@strudel/web` **AGPL-3.0** lisanslıdır (kabul ölçütümüze uymaz) ve yalnız Strudel live-coding müzik videoları içindir. | 0 |
| **`x-posting-license` (`hyperframes-community-skills`)** | **ALMA** | Yalnız X profili için sahte ehliyet kartı üreten tekil meme şablonudur; macOS fontuna ve X marka görsellerine bağımlıdır. | 0 |

---

## hat

`work/agy/2026-11-16-repolar2/sistem.md` envanteri, kabul ölçütleri ve `src/vedit/` kod tabanı karşılaştırılarak kurgu hattı ve araç repoları incelenmiştir.

---

### 1. open-edit (@veedstudio/openedit-cli)
* **Lisans:** Apache-2.0 (İzinli)
* **(1) Ne yapar, mimarisi, gereksinimleri:**
  * *Ne yapar:* Ajan güdümlü uçtan uca video kurgu CLI aracı. Word-level transkript ile kesim (`apply-edl`), headless Chrome üzerinde sanal saatle HTML render (`render`), platform güvenli alanları (`safe-zone`), konuşmacı merkezli dikey kırpma (`reframe`), ekran kaydında imleç/tıklama tespiti (`zoom`), olay/müzik miksi (`mix-audio`) ve teslimat kalite denetimi (`review`) sunar.
  * *Mimarisi:* Node.js CLI (TypeScript). Yan araçlar için Python (WhisperX, MediaPipe) ortamlarını `uv`/`pipx` ile yönetir; render için Headless Chrome Shell kullanır.
  * *Gereksinimleri:* Node.js, FFmpeg/FFprobe, Headless Chrome. Çevrimdışı modda (WhisperX, MediaPipe CPU, local render) tamamen ücretsiz ve hesapsızdır; VEED bulut transkripsiyonu ve fal.ai modelleri (arka plan silme, dudak senkronu) ücretli API/hesap gerektirir. Windows/macOS/Linux uyumludur.
* **(2) Bizim vedit hattında karşılığı:**
  * `src/vedit/reframe.py` (YuNet yüz takibi)
  * `src/vedit/slop.py` ve `src/vedit/kesimqa.py` (kalite, ritim ve slop denetimi)
  * `src/vedit/olaysesi.py` ve `src/vedit/miks.py` (SFX ve ducking)
  * `src/vedit/sessizlik.py` ve `src/vedit/kurgu.py` (transkript ve EDL kesimi)
* **(3) Bizden ölçülebilir biçimde iyi olduğu somut nokta:**
  * **End-Card / Dead-Tail Okuma Süresi Formülü (`README.md:345-355`):** Son konuşulan kelimeden sonraki durağanlık 1 saniyeden uzunsa hata sayılır; ancak yeni bir CTA/kapanış metni varsa bunu "end card" kabul eder. Ekranda kalma süresi deterministik formüle bağlıdır: `0.2s * kelime sayısı + arama payı (10 kelimeye kadar 2s, üstü 3s) + 1s vuruş`; alt sınır 4.0s, üst sınır 4.5s. Bizdeki `slop.py:STATIK_UZUN` ve `SES_NEFES_YOK` kurallarında bu matematiksel ayrım yoktur.
  * **Dead-Air Eşiği (`README.md:355-367`):** Ekranda metin yoksa hareketsiz durağanlık sınırı kesin olarak 3 saniyedir; 2 saniyeden uzun sessizlik olmayan konuşan kafa hariç tutulur.
  * **Yanmış Grafik / Altyazı Çakışması Tespiti (`README.md:409-417`, `477-488`):** Ham videodaki alt bant veya gömülü altyazıları OCR gerektirmeden kenar kararlılığıyla saptayıp yeni metinlerin bunların üzerine binmesini denetler.
* **(4) Alınacak en küçük parça ve nereye:**
  * End-card okuma süresi formülü (`0.2s/kelime + 2s/3s + 1s`, 4.0–4.5s penceresi) ve 3 saniyelik mutlak hareketsizlik sınırı `src/vedit/slop.py` içine (`BITIS_KARTI_SURESI` kontrolü) ve `library/checks.md`'ye kural olarak alınmalıdır.

---

### 2. rea-video (JuneYaooo/rea-video)
* **Lisans:** Apache-2.0 (İzinli)
* **(1) Ne yapar, mimarisi, gereksinimleri:**
  * *Ne yapar:* Referans videoları plan plan (shot-by-shot) tersine mühendislikle çözümler; her planın çekim türünü (gerçek kamera / AI video / 3D animasyon / kod / ekran kaydı) saptar. Çıktıyı insan için HTML rapor, LLM ajanları için ise katmanlı `VIDEO.md` açık standardında üretir.
  * *Mimarisi:* Python 3.10+ CLI. FFmpeg sahne kesimi, sensör gürültüsü ve kadans ölçümü, ses ayrıştırma (UVR MDX-Net ve BandIt v2).
  * *Gereksinimleri:* Python 3.10+, FFmpeg. Temel araç modu (Tools-only) tamamen yerel, ücretsiz ve hesapsızdır (%98.3 doğruluk). İsteğe bağlı Gemini API vision desteği vardır. Windows/Linux/macOS uyumludur.
* **(2) Bizim vedit hattında karşılığı:**
  * `.claude/skills/video-izle/SKILL.md` (mcp-video-analyzer ile sahne ve transkript izleme)
  * `src/vedit/hazirla.py` (sahne tespiti)
  * `.claude/skills/sahne-motoru/SKILL.md` (plan türüne göre Remotion / HyperFrames / Three.js ataması)
  * `src/vedit/ayristir.py` (Demucs ile ses ayrıştırma)
* **(3) Bizden ölçülebilir biçimde iyi olduğu somut nokta:**
  * **`VIDEO.md` Katmanlı Token Mimarisi (`README.md:226-233`):** Video analiz dökümlerini ajana tek seferde yüz binlerce token olarak yüklemek yerine hiyerarşik 4 katmana böler: (1) Birkaç yüz token'lık özet kartı, (2) Genel akış haritası, (3) Plan başına tek satırlık zaman çizelgesi, (4) Talep edilen planın ayrıntı dosyası. Objektif ekran verisi ile subjektif çıkarımı kesin çizgilerle ayırır. Bizim `video-izle` çıktısı (`work/izle/`) doğrudan monolitik JSON ve transkript vererek token bütçesini şişirebilmektedir.
* **(4) Alınacak en küçük parça ve nereye:**
  * `.claude/skills/video-izle/SKILL.md` ve `director` ajanının referans analizi çıktısı için `VIDEO.md` katmanlı format şablonu (kart -> tek satır plan listesi -> detay) alınmalıdır.

---

