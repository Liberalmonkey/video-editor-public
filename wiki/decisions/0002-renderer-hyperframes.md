---
type: decision
title: "Tek renderer: HyperFrames (+ FFmpeg ön-geçiş)"
status: accepted
tags: [adr, renderer]
created: 2026-10-20
updated: 2026-11-22
sources: ["[[2026-10-20-hyperframes]]", "[[2026-10-20-remotion]]", "[[2026-10-20-opus-animasyon-rehberi]]", "[[2026-10-20-ffmpeg]]"]
supersedes:
superseded_by:
---

# ADR: Tek renderer olarak HyperFrames

> [!note] Güncellendi 2026-11-22
> HyperFrames yeniden birincil motordur ([[0050-hyperframes-birincil-motor]]): yeni grafik, animasyon ve sahne HyperFrames kompozisyonu olarak saydam webm'e render edilir; timeline birleştirmesi Remotion'da kalır.

> [!note] Güncellendi 2026-11-15
> HyperFrames artık tek renderer değildir; yalnız açık istekle çalışan eski `/video` hattında kullanılır. Varsayılan motor OpenMontage ve Remotion'dır ([[0010-openmontage-edit-motoru]]); Video Stüdyo ve terminal hattı `studio/remotion/Kurgu.tsx` ile render eder ([[0021-video-studyo-nle]]).

## Bağlam
Animasyon (10–15 dk), çekim kurgusu (UGC) ve Reels için bir kompozisyon/render katmanı gerekiyor. Kullanıcı Remotion yerine HyperFrames kullanılabileceğini söyledi. [[2026-10-20-opus-animasyon-rehberi]] HTML/Canvas yaklaşımını öneriyor.

## Seçenekler
| Seçenek | Artıları | Eksileri |
|---|---|---|
| HyperFrames | Apache-2.0; HTML + GSAP (LLM için en ucuz format); lint/check/snapshot/`timeline --json`; ses mixing; altyazı stilleri; segmented uzun render; rehberin yaklaşımıyla uyumlu ([[2026-10-20-hyperframes]]) | Workflow'ları çekime dokunmuyor; Windows'ta çoklu worker diske yazıyor |
| Remotion | Gerçek çekimde biraz daha güçlü, olgun ekosistem ([[2026-10-20-remotion]]) | TSX yazımı daha pahalı; 4+ kişilik ekipte lisans gerekir |
| İkisi birlikte | Her işe en iyi araç | İki skill seti, iki bilgi tabanı, iki kat bakım ve token |
| Saf Canvas + Playwright (rehber) | Tam kontrol | Render, ses, altyazı ve QA araçlarını sıfırdan yazmak gerekir |

## Karar
Tek renderer olarak **HyperFrames 0.8.181** seçildi.
- Gerçek çekimdeki kesimleri FFmpeg ön-geçişi yapar (`vedit cut`, EDL → A-roll) ([[2026-10-20-ffmpeg]]).
- HyperFrames; overlay, punch-in/zoom, altyazı, motion graphics ve ses mix katmanını yönetir.
- Canvas veya Three.js hero sahneleri HyperFrames adaptörleriyle sarılır ([[render-sozlesmesi]]).

## Sonuçlar
- Remotion kullanılmıyor; yalnızca CC0 `@remotion/sfx` sesleri SFX kaynağı olarak alınıyor.
- Uzun videolar bölüm bölüm render edilir: her bölüm tek worker ile stream edilir, 2–3 bölüm paralel çalışır, sonra FFmpeg concat ve master ses mux yapılır.
- Bu makinede ölçülen hız: basit 1080p30 sahnede yaklaşık 17 fps.

## İlgili kod
`src/vedit/build.py`, `src/vedit/render.py`, `blocks/`
