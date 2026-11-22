---
type: decision
title: "Uçtan uca HyperFrames: tek derleyici, çift motor geçişi, sürekli güncelleme"
status: accepted
tags: [adr, renderer, hyperframes, remotion, studio, guncelleme]
created: 2026-11-22
updated: 2026-11-22
sources: ["[[2026-10-20-hyperframes]]"]
supersedes:
superseded_by:
---

# ADR 0051: Uçtan uca HyperFrames

## Bağlam
ADR 0050 karma geçişi yaptı: yeni grafikler HyperFrames kompozisyonu oldu, ama önizleme, taslak ve final render, altyazı, sahneler, hazır efekt, geçişler ve native bileşenler Remotion'da kaldı.

Kullanıcı 2026-11-22'de editin uçtan uca HyperFrames'le yapılmasını istedi. Motion ve stil bölümleri de buna uyarlanacak. Remotion silinmeyecek; HyperFrames bir işi yapamazsa son çare olarak kullanılacak. HyperFrames güncellemeleri de repodan sürekli alınacak.

Kullanıcının kararları:
- Güncelleme: otomatik, duman testi ve geri almayla.
- Geçiş: çift motor, aşamalı; Stüdyo hiç bozulmaz.

## Karar
- **Sürekli güncelleme (`src/vedit/hf_guncel.py`, `vedit hf-guncelle`):**
  1. `npm view` ile kontrol.
  2. Aday kurulum `work/hf-aday/<sürüm>/`.
  3. Duman paketi `tests/hf_duman/` (lint, boyut, süre, alfa, altın kareye fark).
  4. Geçerse `package.json`, `node_modules`, skill'ler ve `skills-lock.json` güncellenir, `wiki/log.md`'ye `setup` satırı düşer. Kalırsa eski sürüm kalır.
  - Geri alma: `--geri`.
  - Tetikler: Stüdyo açılışında günde bir; isteğe bağlı haftalık görev `scripts/hf_guncelle_gorev.ps1`.
  - Stüdyo başlığında `HF <sürüm>` rozeti (`/api/hf/durum`). Sabit sürüm tek yerde, `package.json` (`hf.surum()`).
- **Tek derleyici (`studio/hf/derle.ts`):** render props'u (`kurgu.render.json`) HyperFrames kompozisyonuna çevirir. Saf TypeScript olduğu için önizlemede (tarayıcı, `srcdoc`) ve render'da (`studio/hf/cli.ts`, vite-node) aynı kod çalışır.
  - Medya HyperFrames klibidir: zaman, kırpma, hız ve ses motordadır.
  - Dönüşüm, efekt ve punch çalışma zamanında hesaplanır (`studio/hf/calisma.ts`): tek paused GSAP zaman çizelgesinin `onUpdate`'i. Hesap Remotion'la paylaşılan saf modüllerden gelir (`hazirEfekt.ts`, `izdusum.ts`), iki motor aynı sayıyı üretir.
  - Proje klasörü `work/public`'tir (`_k/` medya, `fonts/`, `hf/tema.css`).
- **Motor seçimi (`src/vedit/hf_kurgu.py`):**
  - Kurguda `motor: oto | hf | remotion`.
  - `oto`: derleyicinin `desteklenmeyen` listesi boşsa ve hız kapısı açıksa (`library/hf_motor.json` `oto_hf`) HyperFrames, değilse Remotion. `hf` hız kapısını atlar ama desteklenmeyen özellik varken yine Remotion'a düşer.
  - Karar ve nedeni `work/edit/motor.json`'a yazılır.
  - `hizli._goruntu` taslak ve finali, `ekip_v2.parcali_render` parçaları bu seçimle render eder. Parçalar birleştirmede taslak boyutuna eşitlenir.
- **Aşamalar** (plan: `wiki/specs` değil, ADR bölümleri):
  - Faz 0, güncelleme sistemi: tamam.
  - Faz 1, derleyici; özellik özellik, her adım `desteklenmeyen`den bir madde siler:
    1. İskelet: tamam.
    2. Altyazı.
    3. Hazır efekt: çalışma zamanında hazır; ölçümle doğrulanacak.
    4. Geçişler (orta noktalılar).
    5. Metin grafik ve sahneler.
    6. `hf` kliplerinin gömülmesi.
    7. Native bileşenler.
    8. Fizik ve karakter.
  - Faz 2: Stüdyo önizlemesi `<hyperframes-player>`.
  - Faz 3: hız kapısı.
  - Faz 4: motion ve stil bölümleri.
  - Faz 5: varsayılan ve belgeler.

## Hız (2026-11-22, Faz 3 öne alındı)
- Ölçüm `instagram/1`: 51,7 sn, 1080x1920, 17 video klip.
- Darboğaz yakalamaydı: kare başına medyan 280 ms. Sabit maliyet de vardı: kare çıkarma, özetleme ve ses, aralık ne olursa olsun bütün kliplerde ödeniyordu.
- Çözüm 1, taslak yarım ölçek: derleyici `olcek`, `#sahne` CSS ölçeği.
- Çözüm 2, aralık ve parça render'ında pencereli derleme: yalnız pencereye değen klipler.
- Otomatik işçi sayısı (4) en hızlısı; 8 işçi bellek yüzünden 1,8 kat yavaş.
- Sonuç tablosu (`library/hf_motor.json`):

| İş | Remotion | HyperFrames |
|---|---|---|
| Tam taslak | 101 sn | 132 sn (oran 1,31) |
| Final, tam çözünürlük | 238 sn | ~281 sn (oran 1,18) |
| 5 sn aralık | — | 87 sn'den 34 sn'ye |

- Hız kapısı açıldı (`oto_hf: true`).

## İlerleme
- Faz 1 adım 2, altyazı: tamam. ADR 0014 standardı ve stil token'ı; sayfalama SplitReel ile birebir (`studio/hf/altyazi.ts`).
- Faz 1 adım 4, orta noktalı geçişler: tamam, 12 geçiş (`studio/hf/gecis.ts`). Resmi sunumların matematiği ve Remotion `random` birebir taşındı; zoom kırbaç ve bölünme kareleri eşleşti.
- Faz 1 adım 5, metin grafik ve sahneler: tamam (2026-11-22). Yeniden yazmak yerine "React adası": `studio/hf/ada.tsx` aynı bileşenleri (`MotionMetin`, SplitReel `StageScene`, `FullTitle`, Kurgu.tsx `TamSahne`) çalıştırır. `remotion` modülü paketlemede `studio/hf/remotion-taklit.tsx`'e yönlenir: kare ve video ayarı bağlamı oradan gelir, Easing/interpolate gerçek paketten. Her karede görünür adalar `flushSync` ile çizilir; kare yalnız t'ye bağlıdır. Ada yoksa React yüklenmez. Bölünmüş düzen (`layoutP`, panel, altyazı konumu) çalışma zamanında. Sonuç: `instagram/reel-video` tamamen HyperFrames; iki motorun kareleri aynı.
- Faz 1 adım 7, native bileşenler: tamam (2026-11-22), 60 bileşen (`dis/lottie` hariç, o Remotion'da kalır). Her biri saf HyperFrames sahnesi: `library/motion/hf/<aile>-<ad>/sahne.html` (`<template>`, duraklatılmış GSAP zaman çizelgesi, değişkenler). Kare matematiği `window.HFN`'den (`studio/hf/native/cekirdek.ts`): `useAkis`'in saf hesabı `akisHesapla`, tema yardımcıları, Remotion'un kendi easing/interpolate/spring dosyaları. React ve wall-clock kodu pakete girmez (HyperFrames lint 0). Derleyici yerleşimi Katman.tsx kuralıyla seçer ve sahneyi `data-composition-src` ile bağlar; her bağlama kendi kopyasıdır (`hf/n/<kök>.html`). Meta ve varsayılan `library/motion/native/sema.json`'dan.
  - Taşıma: 2 pilot elle, 58'i agy (gemini-4-argon-high, 4 dalga, en çok 3 paralel), kurallar `library/motion/hf/SOZLESME.md`.
  - Doğrulama: `scripts/hf_native_karsilastir.py` iki motorda render eder, öğe kutusunda piksel farkı ve kutu kayması ölçer, kontak yazar; sonuç `work/hf-native/sonuc.json`. 60/60 geçti (1'i gözle onaylı: metnin alt piksel kayması).
  - Bulunan hatalar: ana kompozisyonun genel sınıf adı (`.panel`) sahneye sızıyordu, sınıflar `kz-` önekli; native host'u kare ızgarasına oturtuldu (Remotion `round(bas·fps)`). Ölçüm tuzağı: saniyeyle kare arama iki videonun farklı zaman tabanında farklı kareye düşüyor; araç kare numarasıyla okur.
  - Sonuç: `instagram/1` tamamen HyperFrames; 12 native klibin hepsi Remotion'la aynı.
- Faz 2, Stüdyo önizlemesi: tamam (2026-11-22). Program monitörü derleyiciyi tarayıcıda çalıştırır ve `<hyperframes-player srcdoc>` ile oynatır; kurgu değişince 150 ms sonra yeniden derler, oynatma kafası korunur. Çalışma zamanı paketleri `npm run build` ile `dist/hf/`'e yazılır (`studio/hf/paketle.ts`, render de aynı modülü kullanır); HyperFrames runtime'ı ve oynatıcı yerel kopyadır. Proje dosyaları `/pub/` altından (`<base href>`), native sahneler `/hfs/<aile-ad>/<kök>/<w>x<h>.html` ucundan, bileşen haritası `/api/hf/onizleme`'den. Motor seçimi `hf_kurgu.motor_sec` kuralıyla tarayıcıda yapılır; monitör çubuğunda `HF` ya da `Remotion` rozeti, üzerine gelince neden. Derleyici yapamıyorsa Remotion oynatıcısı (Stüdyo bozulmaz).
  - Ses anahtar karesi (`ses.kf`, ducking) artık desteklenir: Remotion `sesEgrisi` kare kare örneklenip `data-automation` volume şeridine yazılır.
  - Önizleme yüz bölgelerini de alır (`kurgu.yuz_bolgeleri`); native yerleşimi render'la aynı.
  - Sınırlar: HyperFrames önizlemesinde ses metresi yok ve geri oynatma (J) yok (hız 0,1-5). Oynatıcı iframe'i `allow-scripts allow-same-origin` ile açar (HyperFrames'in kendi tercihi); içerik yalnız yerel derleyicinin ve kütüphanenin ürettiği HTML'dir.
- Faz 4, motion ve stil bölümleri: tamam (2026-11-22).
  - Motion kayıtları (`library/motion/custom/<id>/<id>.html`) `src/vedit/hf_motion.py` ile üretilir. Kayıt HTML'i değişmez: HyperFrames projesine sarılır (içerik kök öğeye alınır), duraklatılmış tek GSAP zaman çizelgesi her karede animasyonları ve `window.seek`'i sürer. HyperFrames `CSSAnimation`'ı kendi saatiyle sürdüğü için her CSS animasyonu aynı anahtar kare ve zamanlamayla WAAPI'ye çevrilir; `@keyframes`'te yazılmamış uç kare örtük bırakılır, tek bölümde bölüm eğrisi animasyona taşınır. Adımlı zaman, `son_tam` ve piksel stil (ffmpeg) korunur. 35 etkin kayıt Playwright çıktısıyla birebir.
  - `vedit motion kontak` sahne bağlamalarıyla (`studio/hf/kontak.ts`) ve `hyperframes snapshot` ile; eski Remotion kontağıyla aynı. Galeri tema kartı (`hf_motion.kare`) ve stil kataloğu önizlemesi (`hf_motion.kare_saydam`) HyperFrames'ten. Playwright (`pano`) yalnız pano ve kapak işinde kaldı.
  - `tema-cikar` tam token yazar: palet stil kartı gibi `tema_token.karttan`'dan geçer, `motion_tema.json` ve tam `css_metni`.
  - Ajan talimatları: motion-tasarimci yeni grafiği `library/motion/hf/<ad>/index.html` yazar; E2 ve ai-edit için native bileşen HyperFrames sahnesidir, eski şablon son çaredir.
- Faz 1 adım 8, fizik ve karakter: tamam (2026-11-22). React Three Fiber ve post-processing sahnesini HyperFrames'te yeniden yazmak bloom, gölge ve sarsıntıyı riske atardı; planın son çare yolu uygulandı. `hf_kurgu.on_render` render'da her fizik ve karakter klibini tek başına Remotion'da saydam webm'e alır (klip, bake verisi, tema ve ölçek özetiyle önbellek `work/public/hf/onrender/`), derleyici onu video klibi olarak gömer (`DerleOrtam.onRender`, dönüşüm Remotion'da çizildi). Motor kararı fizik/karakteri render için destekli sayar; Stüdyo önizlemesi bu projelerde Remotion oynatıcısıdır, rozet nedeni söyler. instagram/1 kopyasında top düşme sahnesi iki motorda aynı.
- Faz 5, belgeler: CLAUDE.md, `uretim-hatti`, `sahne-motoru`, `motion-design`, motion-tasarimci, motion-gelistirici, E2 ve ai-edit metni güncellendi.
- Kalan Remotion yolları: fizik/karakter ön render'ı, `dis/lottie`, derleyicinin henüz yapamadığı yeni özellik ve `motor: remotion` isteyen kurgu. Stüdyo önizlemesinde ses metresi ve geri oynatma yalnız Remotion oynatıcısında.

## Sonuçlar
- İlk canlı güncelleme 2026-11-22: 0.9.77'den 0.9.78'e. Duman farkı 0,0; skill'ler güncellendi.
- Haftalık görev kullanıcı onayıyla kaydedildi (2026-11-22): Görev Zamanlayıcı `vedit-hf-guncelle`, her pazartesi 10:00, `scripts/hf_guncelle_gorev.ps1`; günlük `work/hf-aday/gorev.log`. Kaldırma: `Unregister-ScheduledTask -TaskName vedit-hf-guncelle -Confirm:$false`.
- İskelet doğrulaması (`instagram/1`, 9-14 sn): video, çapraz geçiş ve zoom Remotion taslağıyla gözle aynı. `hyperframes lint` 0 hata, 0 uyarı.
- Hız: HyperFrames 5 sn'lik 1080x1920 aralığı draft kalitede 78 sn'de render etti. Chrome BeginFrame yakalaması düştü, ekran görüntüsü yoluna geçti. Remotion taslağı yarım çözünürlükte çok daha hızlı. Bu yüzden `oto_hf` kapalı; Faz 3 hız işi bitmeden `oto` HyperFrames'i seçmez.
- 2026-11-22 sonu: `instagram/1` ve `instagram/reel-video` render ve Stüdyo önizlemesinde tamamen HyperFrames.
