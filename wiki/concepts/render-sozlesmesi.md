---
type: concept
title: "Render sözleşmesi (deterministik kare)"
tags: [render, determinizm, motion-design]
created: 2026-10-20
updated: 2026-10-20
sources: ["[[2026-10-20-opus-animasyon-rehberi]]", "[[2026-10-20-hyperframes]]"]
---

# Render sözleşmesi

## Tanım
Her karenin yalnızca zamanın (t) saf bir fonksiyonu olması kuralı. Aynı t her zaman aynı görüntüyü üretir. Kaynakta özü şu: "Opus videoyu çizmez, çizen makineyi yazar" ([[2026-10-20-opus-animasyon-rehberi]]).

## Nasıl çalışır
- Görsel durum önceki karelerden birikmez; `draw(t)` ya da seek edilebilir bir timeline kullanılır.
- Rastgelelik yalnızca seed'li olur (ör. mulberry32). `Math.random`, `Date.now` ve ağ istekleri yasaktır.
- Tek kare inceleme mümkündür: rehberde `?t=`, HyperFrames'te `snapshot --at` ([[2026-10-20-hyperframes]]).
- HyperFrames'te bunu tek paused GSAP timeline ve framework'ün yönettiği medya oynatma sağlar. Canvas tabanlı bir sahne, timeline `onUpdate` içinden `draw(tl.time())` çağırarak sözleşmeye uyar.

## Projede kullanımı
- `motion-design` skill'inin ilk kuralı.
- `vedit build` yalnızca deterministik HTML üretir.
- Hero sahnelerde `editor` ajanı (hero) bu sözleşmeye uymak zorundadır.
- `hyperframes lint` ihlalleri yakalar.

## Alternatifler / trade-off'lar
Gerçek zamanlı ekran kaydı (MediaRecorder) ucuzdur ama tekrarlanabilir değildir ve kare düşürür. Reddedildi.

## Kaynaklar
- [[2026-10-20-opus-animasyon-rehberi]] · [[2026-10-20-hyperframes]] · [[motion-design-ilkeleri]]
