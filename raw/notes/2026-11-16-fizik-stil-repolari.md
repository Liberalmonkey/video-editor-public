# Fizik, ritim ve stil repoları araştırması (2026-11-16)

Kaynak: Antigravity orkestrası (teknik, dil, stil + birleştirme), work/agy/2026-11-16-repolar/sonuc/. Repolar: Vincentwei1021/video-shotcraft, librosa/librosa, pmndrs/react-postprocessing, pmndrs/react-three-rapier, JohnHeibel/ClaudeAnimationBase, joeseesun/opus-video-prompts, yihui-dev/awesome-opus5-5-videos, patch-gg/pixelfx, mrdoob/three.js, lemomo-ai/lemo-opuscar. Aşağıdaki metin birleşik raporun birebir kopyasıdır; lisans satırları Claude tarafından yerel LICENSE dosyalarından yeniden doğrulandı (lemo-opuscar belgeleri CC BY-NC 4.0).

# Üç Araştırma Notunun Birleştirilmiş Teknik, Görsel Dil ve Stil Raporu

Bu rapor; **teknik** (`react-postprocessing`, `react-three-rapier`, `librosa`), **dil** (`video-shotcraft`, `ClaudeAnimationBase`, `pixelfx`) ve **stil** (`opus-video-prompts`, `awesome-opus5-5-videos`, `lemo-opuscar`) araştırma notlarını tek bir referans belgede birleştirir, tekilleştirir ve çelişkileri işaretler.

---

## (1) Lisans Tablosu

| Repo / Paket | Lisans | Kopyalanabilir mi? | Kapsam, İstisnalar ve Çelişki Notları |
|---|---|---|---|
| `react-postprocessing` | **MIT** ([LICENSE](work/agy/2026-11-16-repolar/kaynak/react-postprocessing/LICENSE#L1-L21)) | **Evet** | `Copyright (c) 2020 react-spring`. Kod doğrudan kullanılabilir. |
| `react-three-rapier` | **MIT** ([LICENSE](work/agy/2026-11-16-repolar/kaynak/react-three-rapier/LICENSE#L1-L21)) | **Evet** | `Copyright (c) 2022 Poimandres`. Kod doğrudan kullanılabilir. |
| `three` | **MIT** | **Evet** | Standart Three.js MIT lisansı. |
| `librosa` | **ISC** | **Evet** | Açık kaynak ses analizi kütüphanesi, kısıtsız kullanım. |
| `video-shotcraft` | **Apache-2.0** ([LICENSE](work/agy/2026-11-16-repolar/kaynak/video-shotcraft/LICENSE)) | **Evet** *(Yalnız kod/belge)* | Kod ve çekim kartları (`Wei Yihao, 2026`) kopyalanabilir. **İstisna:** Müzik/SFX varlıkları kendi CC0/CC BY lisanslarına, Remotion ise kendi şirket lisansına tabidir ([README.md](work/agy/2026-11-16-repolar/kaynak/video-shotcraft/README.md#L252-L260)). |
| `ClaudeAnimationBase` | **MIT** ([LICENSE](work/agy/2026-11-16-repolar/kaynak/ClaudeAnimationBase/LICENSE)) | **Evet** | `John Heibel, 2026`. Tüm kod ve belgeler ticari/kişisel kullanıma açıktır. |
| `pixelfx` | **MIT** ([LICENSE](work/agy/2026-11-16-repolar/kaynak/pixelfx/LICENSE)) | **Evet** *(Font hariç)* | `Patch & Hugo Duprez, 2026`. Kod ve 244 efekt kopyalanabilir. **İstisna:** `gallery/fonts` altındaki *Patch Pixel* yazı tipi lisans kapsamı dışındadır, kopyalanamaz ([NOTICE.md](work/agy/2026-11-16-repolar/kaynak/pixelfx/NOTICE.md#L10-L11)). |
| `opus-video-prompts` | **Lisanssız** (`LICENSE` yok) | **Hayır, yalnız fikir** | `README.md` sonunda tüm prompt ve videoların telifinin orijinal yazarlarına ait olduğu belirtilmiştir; yalnız indeks/fikir kaynağıdır. |
| `awesome-opus5-5-videos` | **MIT** *(Repo)* / **Kısıtlı** *(İçerik)* | **Hayır, yalnız fikir** | **`[ÇELİŞKİ]`** Repo kökünde `MIT License (2026 yihui-dev)` vardır ancak `README.md` her videonun ve promptun kendi üreticisine ait olduğunu belirtir. Derleme şeması dışındaki tekil eserlerden yalnız fikir alınmalıdır. |
| `lemo-opuscar` | **Yerelde Lisanssız** *(Uzakta MIT)* | **Hayır, yalnız fikir** | **`[ÇELİŞKİ]`** Uzak repo (`lemomo-ai/lemo-opuscar`) MIT lisanslıdır ancak yerel klon (`ref: refs/heads/.invalid`) boş bir `.git` iskeleti olduğundan çalışma ağacında `LICENSE` dosyası yoktur. Doğrulanmış yerel kaynak olmadan yalnız mimari fikir alınmalıdır. |

---

## (2) Kurulacak npm / pip Sürümleri (Tek Liste)

Mevcut [studio/package.json](studio/package.json#L13-L21) içindeki `react: "18.3.1"`, `react-dom: "18.3.1"` ve `remotion: "4.0.484"` sabitleriyle `peerDependencies` çakışması yaşamayan **tek uyumlu sürüm listesi**:

### npm (`studio/` dizini için)
* `@remotion/three@4.0.484` — `remotion` ile birebir aynı sürüm zorunludur (`peerDependencies`: `@react-three/fiber >=8.0.0`, `three >=0.145.0`).
* `@react-three/fiber@8.18.0` — React 18 destekleyen son v8 dalı sürümüdür (`>=18 <19`); v9+ yalnızca React 19 ister.
* `@react-three/postprocessing@2.16.3` *(veya R18/R19 geçiş sürümü `2.19.1`)* — R3F v8 ve React 18 uyumlu v2 dalı; klonlanan `3.2.2` ([package.json](work/agy/2026-11-16-repolar/kaynak/react-postprocessing/package.json#L68-L73)) React 19 ister.
* `postprocessing@6.39.3` (`^6.36.0`) — React bağımsız çekirdek kütüphane (`three >=0.156.0 <1.0.0`).
* `@react-three/rapier@1.5.0` — R3F v8 ve React 18 uyumlu son v1 dalı; klonlanan `2.2.0` ([package.json](work/agy/2026-11-16-repolar/kaynak/react-three-rapier/packages/react-three-rapier/package.json#L22-L31)) React 19 ister.
* `@dimforge/rapier3d-compat@0.19.2` — Node/ön-simülasyon (bake) için doğrudan kullanımda `0.19.2` *(Not: `@react-three/rapier@1.5.0` ile aynı ortamda çakışmaması için bkz. Bölüm 8)*.
* `three@0.182.0` *(veya `@types/three` ile eşleşen `0.172.0+`)* — Her iki paketin `>=0.156.0` / `>=0.159.0` alt sınırını karşılar.

### pip (Windows, Python 3.11 / 3.12 ortamı için)
* `librosa==0.10.2.post1` *(veya NumPy 2 kullanılıyorsa `librosa==0.11.0`)*
* `soundfile>=0.12.1` *(Windows `.whl` içinde `libsndfile` DLL gömülüdür; WAV/FLAC/OGG/MP3 okur)*
* `numba>=0.58.0` *(Python 3.11/3.12 ve NumPy 1.26/2.x prebuilt binary wheel desteği)*
* `audioread>=3.0.1` *(`soundfile` açamadığında `.m4a`/`.aac` için Media Foundation / `ffmpeg.exe` yedeği)*

```powershell
# Kurulum komutları (tercihen --only-binary=:all: ile)
pip install --only-binary=:all: "librosa>=0.10.2.post1" "soundfile>=0.12.1" "numba>=0.58.0" "audioread>=3.0.1"
```

---

## (3) Fizik Bake Mimarisi Özeti

Remotion kareleri çoklu iş parçacığında (concurrency) sırasız render ettiği için, çalışma anında `<Physics>` bileşenini `useFrame` ile koşturmak yerine **kare `0`'dan başlayan deterministik ön-simülasyon (bake)** uygulanır:

1. **Çalışma Yeri ve Çıktı:** Simülasyon bir Node ön-hazırlık script'inde veya Remotion `calculateMetadata` aşamasında `@dimforge/rapier3d-compat` ile koşturulur. Çıktı olarak:
   * `frames`: Her kare için tüm gövdelerin konum ve dönüş kuaterniyonu (`{ [id]: { p: [x,y,z], q: [x,y,z,w] } }`) — bileşen içinde `useCurrentFrame()` ile $O(1)$ sürede okunur.
   * `contacts`: Çarpışma zamanı, karesi, gövde çifti, bağıl hızı ve kuvveti (`{ time, frame, pair, impactSpeed, force }`) — doğrudan `work/edit/olaylar.json` içine rol olayı (`vurgu_guclu` vb.) ve kamera sarsıntısı olarak aktarılır.
2. **%100 Determinizm İçin 4 Zorunlu Şart:**
   * **Sabit `timestep`:** `world.timestep = 1 / (fps * substeps)` (örn. `fps = 30`, `substeps = 4` için `dt = 1/120s`) sabitlenmeli, değişken `delta` asla kullanılmamalıdır ([Physics.tsx](work/agy/2026-11-16-repolar/kaynak/react-three-rapier/packages/react-three-rapier/src/components/Physics.tsx#L602-L608)).
   * **Sabit Ekleme Sırası:** `RigidBody` ve `Collider` nesneleri her çalışmada birebir aynı sırayla oluşturulmalıdır (`HashMap` yerine deterministik handle sırası).
   * **Temas Olay Bayrakları:** Collider üzerinde `ActiveEvents.COLLISION_EVENTS | ActiveEvents.CONTACT_FORCE_EVENTS` ve `setContactForceEventThreshold(1.0)` açılmalı; her alt adımda `eventQueue.drainCollisionEvents` ve `drainContactForceEvents` ile olaylar toplanmalıdır ([Physics.tsx](work/agy/2026-11-16-repolar/kaynak/react-three-rapier/packages/react-three-rapier/src/components/Physics.tsx#L709-L839)).
   * **WASM Bellek Temizliği:** `await RAPIER.init()` ile başlatılan dünya, bake bitiminde `eventQueue.free()` ve `world.free()` ile mutlaka temizlenmelidir ([Physics.tsx](work/agy/2026-11-16-repolar/kaynak/react-three-rapier/packages/react-three-rapier/src/components/Physics.tsx#L502-L505)).
3. **Kapalı-Form (`f(t)`) Tamamlayıcısı:** Çoklu cisim çarpışması gerektirmeyen UI, karakter zıplaması (`ClaudeAnimationBase`) ve araç süspansiyonu (`lemo-opuscar`) hareketlerinde WASM bake yerine doğrudan `t = frame / fps` üzerinden hesaplanan sönümlü harmonik osilatörler (`exp(-k*t) * cos(w*t)`) kullanılır.

---

## (4) Işık / Postprocessing Presetleri ve Deterministiklik Notları

### 4.1. `react-postprocessing` Efektlerinin Deterministiklik Tablosu ([src/index.ts](work/agy/2026-11-16-repolar/kaynak/react-postprocessing/src/index.ts#L8-L48))

| Efekt | Deterministik mi? | Teknik Gerekçe ve Remotion Kuralı |
|---|---|---|
| `Bloom` ([Bloom.tsx](work/agy/2026-11-16-repolar/kaynak/react-postprocessing/src/effects/Bloom.tsx#L15-L34)) | **Evet** | Salt uzamsal (spatial) mipmap konvolüsyonu yapar; zamansal durumu yoktur. |
| `Vignette` ([Vignette.tsx](work/agy/2026-11-16-repolar/kaynak/react-postprocessing/src/effects/Vignette.tsx#L4-L7)) | **Evet** | UV tabanlı statik matematiksel fonksiyondur. |
| `ChromaticAberration` ([ChromaticAberration.tsx](work/agy/2026-11-16-repolar/kaynak/react-postprocessing/src/effects/ChromaticAberration.tsx#L19-L22)) | **Evet** | `offset` vektörü doğrudan prop olarak verilir, iç durumu yoktur. |
| `SMAA` ([SMAA.tsx](work/agy/2026-11-16-repolar/kaynak/react-postprocessing/src/effects/SMAA.tsx#L14-L20)) | **Evet** | Uzamsal kenar algılama yapar (TAA gibi önceki kare geçmişine bakmaz). |
| `DepthOfField` ([DepthOfField.tsx](work/agy/2026-11-16-repolar/kaynak/react-postprocessing/src/effects/DepthOfField.tsx#L54-L112)) | **Koşullu Evet** | `target` (autoFocus) verilirse derinlik okumasında zamansal yumuşatma devreye girer. Determinizm için `focusDistance` / `worldFocusDistance` doğrudan `useCurrentFrame()` ile sürülmelidir. |
| `Noise` ([Noise.tsx](work/agy/2026-11-16-repolar/kaynak/react-postprocessing/src/effects/Noise.tsx#L14-L16)) | **Dikkat (Müdahale Şart)** | `EffectPass` her `composer.render(delta)` çağrısında `time` biriktirip `rand(uv * time)` içinde kullanır. Paralel render'da `effectPass.time = frame / fps` sabitlenmeli veya `uSeed: frame` alan özel shader kullanılmalıdır. |
| `ToneMapping` ([ToneMapping.tsx](work/agy/2026-11-16-repolar/kaynak/react-postprocessing/src/effects/ToneMapping.tsx#L16-L19)) | **Koşullu Evet** | `adaptive={false}` (`ACES_FILMIC`, `REINHARD2`) iken deterministiktir. `adaptive={true}` (`REINHARD2_ADAPTIVE`) önceki karelerin parlaklığını `deltaTime` ile biriktirdiği için paralel render'da **yasaktır**. |
| `MotionBlur` | **Yok** | Pakette yerleşik `MotionBlur` yoktur. `@remotion/motion-blur` (`<Trail>`), hıza bağlı hayalet izi (`f-1.6, f-3.2`) veya alt-kare `tmix` kullanılır. |

### 4.2. `@remotion/three` `<ThreeCanvas>` ve Işık Preset Kuralları
1. **İlk Kare (`frame 0`) Siyah Ekran Önlemi:** `@remotion/three` `frameloop="never"` kullanır; [EffectComposer.tsx](work/agy/2026-11-16-repolar/kaynak/react-postprocessing/src/EffectComposer.tsx#L207-L287) ise `composerState`'i `useEffect` içinde kurup `useFrame(..., renderPriority = 1)` ile çizer. İlk karede efektlerin atlanmaması veya siyah çıkmaması için `EffectComposer` mount olduktan sonra `useLayoutEffect` içinde `advance()` çağrılmalı ya da `delayRender()` / `continueRender()` kullanılmalıdır.
2. **FBO Buffer Koruma:** Headless Chromium'da ekran tamponunun silinmemesi için `<ThreeCanvas gl={{ preserveDrawingBuffer: true, alpha: true }}>` zorunludur ([EffectComposer.tsx](work/agy/2026-11-16-repolar/kaynak/react-postprocessing/src/EffectComposer.tsx#L280-L284)).
3. **ACES Filmic Zorunluluğu:** `EffectComposer` otomatik olarak `gl.toneMapping = NoToneMapping` yapar ([EffectComposer.tsx](work/agy/2026-11-16-repolar/kaynak/react-postprocessing/src/EffectComposer.tsx#L335-L342)); renklerin soluklaşmaması için zincirin sonuna `<ToneMapping mode={ToneMappingMode.ACES_FILMIC} />` eklenmelidir.
4. **2D / Canvas Toplamsal Işık Preseti (`pixelfx` & `ClaudeAnimationBase`):** 2D sahnelerde parlama efektleri boya gibi karıştırılmaz (mavi üstüne sarı = çamurlu gri); ayrı bir `light: Uint32Array` tamponunda ([fx.js](work/agy/2026-11-16-repolar/kaynak/pixelfx/src/core/fx.js#L100-L130)) veya kağıt dokusunun altında `blendMode(ADD)` ([core.js](work/agy/2026-11-16-repolar/kaynak/ClaudeAnimationBase/src/core.js#L105-L110)) ile toplamsal ışık olarak basılır.

---

## (5) Yeni Efekt ve Geçiş Adayları (En Çok 10)

Mevcut [hazirEfekt.json](studio/remotion/hazirEfekt.json) ve [manifest.json](library/motion/manifest.json) ile çakışmayan, en yüksek katma değerli **6 hazır efekt + 4 geçiş (toplam 10 aday)**:

| # | Tür | Aday ID | Kısa Tarif ve Kullanım Yeri | Parametreler (`param`) | Kaynak |
|---|---|---|---|---|---|
| 1 | Efekt | `carp_zoom` | **Hazırlıklı Çarpma Zoom'u:** 6f `%3.5` geri çekilir (anticipation), 6f `ease-in` ile hedefe `(x,y)` çarparak büyür, 6f `exp(-t/1.8)` sarsıntıyla mıhlanır (videoda ≤ 2 kez, P0 kanıt anında). | `sure: 1.2`, `s: 1.8 (1.25..2.8)`, `x: 0.5`, `y: 0.5`, `sarsinti: 12` | `video-shotcraft` ([crash-zoom-punch.md](work/agy/2026-11-16-repolar/kaynak/video-shotcraft/references/shots/camera/crash-zoom-punch.md#L15-L43)) |
| 2 | Efekt | `sicrama_kes` | **Sıfır Ara Kareli Üçlü Sıçrama (Jump-Cut Punch-In):** Tween olmadan vuruş anlarında `1.0 -> s1 -> s2` şeklinde 2–3 kademe anında büyür (art arda 3 kısa kelimede ritim kırmak için). | `sure: 1.2`, `kademe: 2 (2..3)`, `s: 1.35`, `x: 0.5`, `y: 0.5` | `video-shotcraft` (`jump-cut-punch-in`) |
| 3 | Efekt | `perspektif_egim` | **2.5D Perspektif ve Kaldırma:** Ekran görüntüsünü `perspective` içinde `rotX`/`rotY` ile yatırıp `bezier(0.33, 0, 0.15, 1)` ile düzleştirerek yaklaştırır. | `sure: 1.5`, `rotX: 28`, `rotY: -18`, `s: 1.15` | `video-shotcraft` ([PageCam.tsx](work/agy/2026-11-16-repolar/kaynak/video-shotcraft/assets/lib/PageCam.tsx#L42-L148)) |
| 4 | Efekt | `golge_kalk` | **Temas Gölgeli Yükselme:** Kart/görsel `1.0 -> s` oranında yükselirken altındaki yumuşak gölge genişleyip soluklaşır, kapanışta yerine oturur. | `sure: 1.8`, `s: 1.06`, `yukseklik: 18 (6..48)` | `video-shotcraft` (`contact-shadow-lift`) & [clawd.js](work/agy/2026-11-16-repolar/kaynak/ClaudeAnimationBase/src/clawd.js#L76) |
| 5 | Efekt | `giris_carp` | **Ağır Çarpma Girişi (Score Slam):** V2 kart/rozet `scale: 2.2` ve hafif açıdan 6 karede (`ease-in-quad`) yere çarparak iner ve sönümlü yayla titrer. | `sure: 0.45`, `s: 2.2`, `aci: 4 (-12..12)` | `video-shotcraft` (`score-slam`) |
| 6 | Efekt | `baski_kayma` | **Riso Baskı Kalıbı Çarpması:** Dijital RGB glitch yasağını delmeden, öğeyi 2 renk baskı kalıbına (`multiply`) ayırıp 2 kez titreyerek üst üste oturtur. | `sure: 0.35`, `mesafe: 14`, `renk1: "#FF2E63"`, `renk2: "#2563EB"` | `video-shotcraft` (`riso-misregistration-hit`) |
| 7 | Geçiş | `gecis-savurma` | **Yönlü Savrulma (Whip-Pan):** Kamera `in-out-expo` ile yana savrulur; kesim anındaki 4 karede yoğun yönlü hareket bulanıklığı + kenar tekrarı kesimi gizler. | `sure: 0.35` (10–12f), `yon: "sol"|"sag"|"yukari"|"asagi"`, `bulaniklik: 32` | `video-shotcraft` (`whip-pan`) |
| 8 | Geçiş | `gecis-crt-kapanis` | **Tüplü Ekran Kapanış/Açılış:** Ekran `inCubic` ile 2px beyaz çizgiye ve merkezde fosfor noktasına büzülüp kapanır; yeni sahne tarama çizgileriyle açılır. | `sure: 0.9` (kesim `0.45s`), `parlama_rengi: "#8CC4F0"` | `pixelfx` ([crt-off.js](work/agy/2026-11-16-repolar/kaynak/pixelfx/src/fx/transitions/crt-off.js#L20-L87)) |
| 9 | Geçiş | `gecis-firca-darbesi` | **El Boyaması 5 Şeritli Fırça Geçişi:** `-6°` eğik 5 kuru fırça darbesi stagger (`[0, 0.14, 0.06, 0.18, 0.1]`) ile ekranı boyayarak kapatır ve çekilerek yeni sahneyi açar. | `sure: 0.8` (kesim `0.40s`), `renk1`, `renk2` (temadan) | `ClaudeAnimationBase` ([timeline.js](work/agy/2026-11-16-repolar/kaynak/ClaudeAnimationBase/src/timeline.js#L36-L53)) |
| 10 | Geçiş | `gecis-pencere-icinden` | **Çerçeve/Kart İçinden Geçiş (Portal Wipe):** Hedef pencere `(x,y,w,h)` `expo.inOut` ile tam ekrana büyürken yeni sahne o pencerenin içinden 1:1 ölçeğe genişler. | `sure: 0.75` (22f), `x: 0.5, y: 0.5, w: 0.35, h: 0.25, kose_r: 16` | `video-shotcraft` (`mask-wipe` / `letterform-zoom`) |

*(Not: 10 aday sınırı nedeniyle `darbe_karesi`, `kare_adimla`, `gecis-piksel-cozunme` ve `gecis-carpma-bol` ikinci faz yedek listesine ayrılmıştır.)*

---

## (6) Stil Kartı Adayları (10 Aday, Tema Değerleriyle)

Mevcut 10 temayla çakışmayan, `library/motion/tema/*.css` şemasına ve ücretsiz Google Fonts standartlarına uyumlu **10 yeni stil kartı adayı**:

| # | Dosya Adı | İçerik / Kullanım Alanı | `:root` Tema Değerleri (`library/motion/tema/`) |
|---|---|---|---|
| 1 | `kinetik-ui.css` | SaaS lansmanı, arayüz turu, kesintisiz UI morph videoları | `--vurgu:#FF5500; --ikincil:#1ED760; --zemin:#F3F3F0; --yazi:#111111; --soluk:#86868B; --font:'Plus Jakarta Sans',sans-serif; --agirlik:700; --kose:20px; --cizgi:2px` |
| 2 | `altin-fintech.css` | Finans, yatırım, kurumsal B2B, prestijli ürün gösterimi | `--vurgu:#E8B84B; --ikincil:#34D399; --zemin:#0C0F1A; --yazi:#F6F4EB; --soluk:#8B93B5; --font:'Plus Jakarta Sans',sans-serif; --agirlik:700; --kose:14px; --cizgi:3px` |
| 3 | `murekkep-zen.css` | Felsefe, tarih, psikoloji, strateji, kitap özetleri (Sumi-e) | `--vurgu:#C83E2B; --ikincil:#4A4A48; --zemin:#F4EFE6; --yazi:#1C1C1C; --soluk:#8C857B; --font:'Noto Serif',serif; --agirlik:700; --kose:4px; --cizgi:6px` |
| 4 | `piksel-16bit.css` | Oyun kültürü, retro teknoloji, algoritma meydan okumaları | `--vurgu:#FFB703; --ikincil:#38B6FF; --zemin:#120E24; --yazi:#F4F1DE; --soluk:#6D6875; --font:'Press Start 2P',monospace; --agirlik:400; --kose:0px; --cizgi:4px` |
| 5 | `termal-kizilotesi.css` | Biyoloji, spor bilimi, savunma/enerji analizi, Reels hook'ları | `--vurgu:#F77F00; --ikincil:#D90429; --zemin:#050507; --yazi:#EAE2B7; --soluk:#7A3E3E; --font:'Space Grotesk',sans-serif; --agirlik:700; --kose:8px; --cizgi:4px` |
| 6 | `gravur-el-yazmasi.css` | Harita rotaları, tarihsel keşif/savaş belgeselleri, kronoloji | `--vurgu:#B83A2D; --ikincil:#8A7968; --zemin:#EFE6D5; --yazi:#1E1B18; --soluk:#9E907E; --font:'EB Garamond',serif; --agirlik:700; --kose:2px; --cizgi:5px` |
| 7 | `analitik-uzay.css` | AI mimarisi (Transformer), matematik/fizik kanıtları (3B1B) | `--vurgu:#29ABCA; --ikincil:#FFFF00; --zemin:#000000; --yazi:#ECECEC; --soluk:#6C757D; --font:'Lora',serif; --agirlik:600; --kose:8px; --cizgi:5px` |
| 8 | `xray-sema.css` | Donanım (çip/motor/batarya), mimari ve patlatılmış CAD şeması | `--vurgu:#2ED3B1; --ikincil:#FF4D00; --zemin:#181A1F; --yazi:#E0E1CC; --soluk:#5C6370; --font:'Chakra Petch',sans-serif; --agirlik:700; --kose:6px; --cizgi:3px` |
| 9 | `seramik-mozaik.css` | Sanat tarihi, kültür-miras, lüks el işçiliği ve mozaik açılışlar | `--vurgu:#D4AF37; --ikincil:#C85A32; --zemin:#191716; --yazi:#F5F3EF; --soluk:#7D746D; --font:'Fraunces',serif; --agirlik:800; --kose:4px; --cizgi:6px` |
| 10 | `golge-kukla.css` | Arkadan aydınlatmalı kağıt kukla, geleneksel/dramatik hikâye | `--vurgu:#F2A65A; --ikincil:#D94E34; --zemin:#1A110B; --yazi:#F5E6D3; --soluk:#2B9EB3; --font:'Playfair Display',serif; --agirlik:800; --kose:4px; --cizgi:4px` |

---

## (7) Fizik-Işık-Ses Gizli Kuralları (Tekilleştirilmiş 30 Madde)

Üç araştırma notundaki (`stil` 28 kural + araç fiziği, `dil` kapalı-form animasyon ilkeleri ve `teknik` ses/fizik kuralları) örtüşen maddeler birleştirilerek **30 temel yasaya** indirilmiştir:


## Devamı (ayrı dosyalar)
- `2026-11-16-fizik-stil-repolari.part2.md`
