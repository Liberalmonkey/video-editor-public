---
type: source
title: "opus-animasyon-rehberi (Eray Coşkun)"
tags: [motion-design, animasyon, prompt, opus]
created: 2026-10-20
updated: 2026-10-20
raw: raw/repos/2026-10-20-opus-animasyon-rehberi.md
url: https://github.com/eraycoskunai/opus-animasyon-rehberi
author: Eray Coşkun (@AIMevzulari)
sources: []
---

# opus-animasyon-rehberi

## Özet
Opus ile kodla animasyon üretmeyi anlatan Türkçe prompt ve kural rehberi ([[raw/repos/2026-10-20-opus-animasyon-rehberi]]). Kod yok. Ana fikri şu: Opus videoyu çizmez, videoyu çizen deterministik `draw(t)` makinesini yazar. **Lisans dosyası yok**, bu yüzden metni kopyalamıyoruz; fikirleri [[motion-design-ilkeleri]] ve [[render-sozlesmesi]] sayfalarında kendi sözlerimizle genişletiyoruz.

## Ana çıkarımlar
- **Render sözleşmesi:** saf `draw(t)`, seed'li rastgelelik, tek kare (`?t=`) inceleme → [[render-sozlesmesi]].
- **"AI şablonu" yasakları:** mor gradyan, anlamsız parçacık, her şeye elastik easing. Ayrıca easing işe göre seçilir, geçiş önceki sahnedeki nesneden doğar, büyük andan önce 300–600 ms durgunluk bırakılır → [[motion-design-ilkeleri]].
- **Akış:** brief → sahne listesi onayı → kod → kontak sayfası → eleştiri (rubrik, P0/P1/P2, en fazla 3 tur). Düzeltmeler kare cinsinden verilir.
- **Stil paketleri:** her stil ayrı paket (STYLE/MOTION/PIPELINE). "Tek dev skill hiçbirini iyi yapmaz."
- **Senkron:** Whisper kelime zamanları sahne sürelerini belirler; librosa müzik haritası çıkarır.

## Projeye etkisi
Sistemin motion design "zevk katmanı" bu kaynaktan doğuyor: `motion-design` ve `render-qa` skill'leri ile eleştirmen ajanının rubriği. Repo gerçek çekim, uzun video, ses mühendisliği, SFX kütüphanesi, TTS, SRT ve Claude Code entegrasyonu içermiyor; bu boşlukları biz dolduruyoruz ([[0001-claude-code-skill-ajan-mimarisi]]).

## Çelişkiler / açık sorular
> [!warning] Çelişki
> Repo varsayılan olarak saf Canvas/SVG tek dosya HTML öneriyor ve Remotion/HyperFrames'i yalnızca "framework" seçeneği olarak anıyor. Biz HyperFrames'i tek renderer seçtik ([[0002-renderer-hyperframes]]). HyperFrames, Canvas `draw(t)` fonksiyonunu GSAP ile seek edilebilir biçimde sarabildiği için yaklaşım korunuyor.

- Lisans yok: içerik kullanımı için yazara sorulabilir. Şimdilik sadece fikir düzeyinde yararlanıyoruz.

## Bağlantılı sayfalar
- [[opus-animasyon-rehberi]] · [[motion-design-ilkeleri]] · [[render-sozlesmesi]] · [[token-ekonomisi]]
