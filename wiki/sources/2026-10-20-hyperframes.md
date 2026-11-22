---
type: source
title: "HyperFrames (HeyGen) repo ve yerel test"
tags: [renderer, html, gsap, ajan]
created: 2026-10-20
updated: 2026-10-20
raw: raw/repos/2026-10-20-hyperframes.md
url: https://github.com/heygen-com/hyperframes
author: HeyGen
sources: []
---

# HyperFrames repo ve yerel test

## Özet
HTML + GSAP kompozisyonlarını headless Chrome ve FFmpeg ile deterministik MP4'e çeviren, ajanlar için tasarlanmış açık kaynak framework (Apache-2.0) ([[raw/repos/2026-10-20-hyperframes]]). 21 Claude skill'i, kapsamlı bir CLI (`lint`, `check`, `snapshot`, `timeline --json`, `transcribe`, `tts`, `beats`) ve ses mixing katmanı içeriyor. Bu makinede 0.8.181 sürümüyle test edildi: 1080p30 basit sahnede yaklaşık 17 fps; Türkçe glifler doğru.

## Ana çıkarımlar
- **Kompozisyon:** `data-start`, `data-duration`, `data-media-start` ve tek paused GSAP timeline'ı. Bu yapı LLM'in yazması en ucuz formatlardan biri.
- **`timeline --json`:** HTML okumadan izleri ve klipleri listeler → [[token-ekonomisi]].
- **Gerçek çekim:** cut, trim, split, reorder ve hız destekleniyor. Workflow'ları çekime dokunmuyor, overlay odaklı. Bu yüzden kesimleri FFmpeg ön-geçişi yapacak ([[0005-timeline-json-tek-dogruluk-kaynagi]]).
- **Ses:** `data-automation` volume lane'i (ducking), efekt zinciri ve bus'lar var. SFX `media-use` ile Openverse'ten geliyor.
- **Uzun render:** segmented capture ve `--resume` var. Windows'ta çoklu worker diske kare yazar, bu yüzden bölüm başına tek worker + paralel bölüm planlandı.

## Projeye etkisi
Tek renderer olarak seçildi ([[0002-renderer-hyperframes]]). İlk kurulumda domain skill'leri hyperframes-core, -animation, -keyframes, -creative, -cli, -audio idi; -registry ve media-use 2026-10-21'de kaldırıldı (HeyGen'e bağlı, ADR 0007/0008). 2026-11-21'de 0.9.77 ile upstream set değişti: kurulanlar `hyperframes`, `hyperframes-cli`, `hyperframes-registry` (yalnız GitHub'daki ücretsiz bloklar), `remotion-to-hyperframes`; `media-use`, `reverse-any-video`, `style-sampling` (HeyGen ya da Pro) ve `slideshow` kurulmadı ([[0050-hyperframes-birincil-motor]]).

## Çelişkiler / açık sorular
- Sistem Chrome'u `--version` çağrısında zaman aşımına uğradı; `hyperframes browser ensure` ile indirilen headless shell kullanılıyor.
- 10–15 dk render süresi henüz ölçülmedi (Faz 4'te).

## Bağlantılı sayfalar
- [[hyperframes]] · [[remotion]] · [[0002-renderer-hyperframes]] · [[render-sozlesmesi]]
