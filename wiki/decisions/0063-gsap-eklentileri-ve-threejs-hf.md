---
type: decision
title: "0063 · GSAP eklentileri, three.js 3D sahneler ve yönetmen katmanı"
tags: [hyperframes, motion, gsap, threejs, 3d, swarm, stil]
status: accepted
created: 2026-11-25
updated: 2026-11-25
sources: ["[[2026-11-25-motion-kaynaklari]]"]
---

# ADR 0063: GSAP eklentileri, three.js 3D sahneler ve yönetmen katmanı

## Bağlam
Motion katmanı HyperFrames'te tek GSAP zaman çizelgesiyle çalışıyordu (ADR 0050, 0062), ama iki sınır vardı:
1. `library/vendor/gsap.min.js` yalnız çekirdekti. SplitText, DrawSVG, MorphSVG, MotionPath, CustomEase ve Physics2D 3.13'ten beri ücretsiz olduğu halde kullanılamıyordu; harf bölme, kontur çizme ve şekil dönüşümü elle yazılıyordu.
2. 3D yalnız CSS `perspective` ile taklit ediliyordu. three.js projede vardı (`studio`, 0.172.0) ama yalnız Remotion fizik sahnesindeydi.

Kullanıcı altı kaynak verdi: prompt-motion.com, CloudAI-X/threejs-skills, pascalorg/editor, greensock/gsap-skills, LottieFiles/motion-design-skill, Vincentwei1021/video-shotcraft. Seçimi: tam dalga, 3D'de raster + bloom (path tracing yok).

## Karar
- **GSAP eklentileri tek dosyada:** `scripts/gsap_paketle.py`, `library/vendor/gsap/` altındaki npm `gsap@3.14.2` dosyalarını (çekirdek + CustomEase, CustomBounce, SplitText, DrawSVG, MorphSVG, MotionPath, Physics2D, PhysicsProps, Text) `library/vendor/gsap.min.js` içinde birleştirir. Render, Stüdyo önizlemesi, tek kompozisyon kopyası ve motion kayıtları zaten bu dosyayı yüklediği için ek bağlantı gerekmez. Sonunda tema eğrileri adlı ease olur: `--ease-enter/exit/emphasis/settle` → `giris`, `cikis`, `vurgu`, `oturma` (CustomEase; token yoksa yedek eğri). ScrambleText, CustomWiggle ve EasePack alınmadı: içlerinde tohumsuz `Math.random` var.
- **three.js çekirdeği `uc.js`:** `studio/hf/uc/uc.ts` esbuild ile `library/vendor/uc.js` IIFE paketine (`window.HFUC`, `studio` içinde `npm run uc`) çevrilir. `HFUC.kur` saydam WebGL, sıcak ana + soğuk kontur ışık, oda ortamı, ACES ton eşleme ve **alfayı koruyan seçici bloom** kurar (taban alfası `SavePass` ile saklanır, bloom sonrası alfa = taban ile parıltının büyüğü; eşik 1.0, yalnız `toneMapped:false` ve 1 üstü renk parlar). `HFUC.sur` duraklatılmış GSAP zaman çizelgesini `hf-seek` zamanına bağlar, ağır kurulumu `__hf.buildReady` sözüne koyar. Yardımcılar: `katmanliYazi` (her fontla ekstrüde yazı ve harf içi parıltı bandı), `yaziDokusu`, `metinNoktalari`, `noktaDokusu`, `panel`, `yay`, `dalis`, `tohum`. Tema rengi CSS token'ından tarayıcı çözücüsüyle `THREE.Color`'a geçer.
- **3D canlı gömülmez:** `<template>` sarmalı dış betiği atar ve WebGL ağırdır. `hf_grafik.canli_mi` `uc.js` yükleyen ya da `"canli": false` taşıyan kompozisyonu canlı haritadan çıkarır; `kurgu.motion_bagla` bunları bir kez saydam WebM'e render eder, önbellek anahtarına `uc.js` girer. `paketle.ts grafikHarita` aynı kuralı uygular.
- **Kapılar:** `hf_determinizm_hatalari` `THREE.Clock`, `setAnimationLoop`, `performance.now` ve ScrambleText'i reddeder. `kurgu_kalite` `UC_FAZLA` (videoda 2'den çok 3D) ve `UC_ART_ARDA` (iki 3D sahne 8 sn içinde) uyarır.
- **Şablonlar:** 10 three.js şablonu (`uc-*`) ve 12 GSAP eklentili şablon. Eklentili olanların 9'u video-shotcraft çekim kartlarından tekniği alınarak sıfırdan yazıldı (kod kopyalanmadı). Her şablonun `data-hf-meta.kart` alanı çekim kartıdır: `amac`, `sure_sn`, `beat`, `yasak`.
- **Yönetmen katmanı:** LottieFiles'ın duygu → hareket tablosu, dört hareket kişiliği, koreografi ve 1/3 kuralı `motion-design/references/yonetmen-katmani.md`'ye Türkçe indirildi. Stil kataloğunun her kartı `motion_kisilik` (`oyuncu|premium|kurumsal|enerjik`) taşır, `stil_katalog.dogrula` denetler. prompt-motion'daki 240 prompt'un ortak yapısı brif biçimi oldu: girdi, yön (tek iplik öğe ve yasak listesi), yapı, kurulum, tuzaklar. `ekip_v3._motion_brif_ozeti` bunu ve kişiliği G0.5 brifine yazar; `aiedit` HF kataloğu `[3D]` işaretini ve kartın `yasak` alanını gösterir; `editor-grafik` ajanı yeni aileleri bilir.
- **Skill'ler:** gsap-skills'ten `gsap-core|timeline|plugins|utils|performance`, threejs-skills'ten 11 skill elle çağrılır olarak (`disable-model-invocation`). Köprü skill `hf-gsap-uc` otomatik çağrılır ve projeye özgü kuralları verir.
- **Alınmayan:** pascalorg/editor (AECO bina editörü; React Three Fiber + WebGPU). Video üretimine doğrudan katkısı yok; WebGPU renderer kurulumu ileride başvuru. gsap-scrolltrigger/react/frameworks ve threejs-interaction (videoda kaydırma ve etkileşim yok).

## Sonuçlar
- Bir 3D sahne bir kez render edilir (4 sn sahne bu makinede yaklaşık 60 sn), sonra önbellekten gelir. Taslakta 3D maliyeti tek seferliktir.
- Remotion native bileşenlerin HyperFrames kopyaları (`sahne.html`) değiştirilmedi: iki motorun aynı kareyi çizmesi kuralı (ADR 0051) DrawSVG gibi eklentilerle bozulurdu.
- Test: `tests/test_hf_uc.py`.

## İlgili
[[0050-hyperframes-birincil-motor]] · [[0051-uctan-uca-hyperframes]] · [[0062-modern-hyperframes-motion-mimarisi]] · [[0043-stile-bagli-tema-tokenlari]] · [[0046-dis-varlik-ve-lisans]] · [[0059-swarm-edit]]
