---
type: source
title: "Motion kaynakları: prompt-motion, gsap-skills, threejs-skills, LottieFiles, video-shotcraft, pascal editor"
tags: [motion, gsap, threejs, kaynak]
created: 2026-11-25
updated: 2026-11-25
raw: "[[raw/repos/2026-11-25-motion-kaynaklari]]"
sources: []
---

# Motion kaynakları (2026-11-25)

## Özet
Kullanıcının motion katmanını modernleştirmek için verdiği altı kaynak. Beşi kullanıldı, pascalorg/editor alınmadı.

## Ana çıkarımlar
- GSAP eklentileri 3.13'ten beri ücretsiz; HyperFrames'in tek zaman çizelgesi modeline doğrudan oturur.
- three.js HyperFrames'te `hf-seek` olayıyla sürülebilir; zorluk saydamlık ve bloom'un alfayı bozmasıdır.
- İyi motion prompt'unun ortak yapısı: girdiler, yön (tek iplik öğe + yasaklar), yapı, kurulum, tuzaklar.
- Hareket kişiliği (oyuncu, premium, kurumsal, enerjik) süre, eğri ve aşmayı tek kararda bağlar.
- Çekim kartı biçimi (amaç, süre, beat, yasak) editörün şablonu adıyla değil işiyle seçmesini sağlar.

## Projeye etkisi
[[0063-gsap-eklentileri-ve-threejs-hf]]: GSAP eklenti paketi, `uc.js` three.js çekirdeği, 22 yeni şablon, yönetmen katmanı ve brif biçimi.

## Çelişkiler / açık sorular
- threejs-skills r186'yı anlatır, proje 0.172.0 kullanır; WebGPU/TSL bölümleri geçersiz.
- video-shotcraft Remotion tabanlıdır; teknik alınır, kod alınmaz (ADR 0050).

## Bağlantılar
[[0050-hyperframes-birincil-motor]] · [[0062-modern-hyperframes-motion-mimarisi]]
