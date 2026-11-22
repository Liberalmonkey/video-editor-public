---
type: entity
kind: library
title: "HyperFrames"
tags: [renderer, html, gsap]
created: 2026-10-20
updated: 2026-11-15
url: https://github.com/heygen-com/hyperframes
sources: ["[[2026-10-20-hyperframes]]"]
---

# HyperFrames

> [!note] Güncellendi 2026-11-15
> [!note] Güncellendi 2026-11-22
> HyperFrames yeniden birincil motordur: grafik, animasyon ve sahne HyperFrames kompozisyonu, timeline birleştirmesi Remotion ([[0050-hyperframes-birincil-motor]]). Aşağıdaki not eski durumdur.

> "Tek renderer" 2026-10-20 durumudur. HyperFrames yalnız açık istekle çalışan eski `/video` hattında kullanılır; varsayılan motor Remotion'dır ([[0010-openmontage-edit-motoru]], [[0021-video-studyo-nle]]).

## Ne olduğu
HeyGen'in HTML → MP4 framework'ü. Kompozisyonlar HTML ve `data-*` zamanlama nitelikleriyle yazılır, animasyonlar seek edilebilir GSAP timeline'larıdır. Render headless Chrome ve FFmpeg ile yapılır ([[2026-10-20-hyperframes]]).

## Yetenekler
- Kompozisyon ve alt kompozisyon, değişkenler, `<video>`/`<audio>` trim/hız/volume automation
- CLI: `lint`, `check`, `snapshot`, `timeline --json`, `render`, `transcribe`, `tts`, `beats`, `audio`, `normalize-audio`
- ~400 registry bloğu, shader geçişler, ~20 altyazı stili
- Segmented capture ile uzun render, Lambda/Cloud Run ile dağıtık render

## Lisans / maliyet
Apache-2.0, ücretsiz.

## Entegrasyon notları
- Sürüm 0.9.77 (2026-11-21). `package.json` ve `src/vedit/hf.py` sabit sürümü kullanır.
- Render tarayıcısı: `~/.cache/hyperframes/chrome/...chrome-headless-shell.exe` (`hyperframes browser ensure`).
- Telemetri kapalı (`hyperframes telemetry disable`).
- Her `<audio>` için `id` zorunlu. Zoom ve punch-in efektleri `.inner` sarmalayıcıya uygulanır.

## Projedeki rolü
Tek renderer ([[0002-renderer-hyperframes]]). `vedit build`, [[timeline-json]] dosyasından HyperFrames kompozisyonu üretir.

## Kaynaklar
- [[2026-10-20-hyperframes]]
