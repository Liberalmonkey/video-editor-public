---
type: concept
title: "timeline.json — tek doğruluk kaynağı"
tags: [mimari, timeline, veri]
created: 2026-10-20
updated: 2026-10-20
sources: ["[[2026-10-20-hyperframes]]"]
---

# timeline.json

## Tanım
Bir projenin son kurgusunu tanımlayan, şemayla doğrulanan JSON dosyası. LLM bu dosyaya parametre yazar; `vedit build` buradan deterministik olarak HyperFrames kompozisyonu üretir.

## Nasıl çalışır
- **Kök alanlar:** `format` (w, h, fps), `duration`, `style` (stil paketi), `tracks`.
- **İzler:**
  - `video`: A-roll / B-roll / ekran kaydı klipleri (src, start, dur, in, punch keyframe'leri)
  - `overlay`: blok örnekleri (block adı + props)
  - `captions`: captions.json referansı + stil
  - `audio`: konuşma, müzik (ducking), sfx ipuçları
- Çekim kurgusunda kesimler önce `edl.json` → `vedit cut` ile A-roll'a uygulanır. timeline.json kesilmiş A-roll'u tek klip olarak görür ([[2026-10-20-hyperframes]]: HyperFrames workflow'ları çekime dokunmaz, overlay odaklıdır).
- Animasyon projelerinde `scenes.json` (yönetmenin sahne listesi), bölüm başına timeline bölümlerine dönüşür.
- Hero sahneler `custom` blokla, elle yazılmış bir alt kompozisyon dosyasına işaret eder.

## Projede kullanımı
Şema: `src/vedit/schemas.py`. Karar: [[0005-timeline-json-tek-dogruluk-kaynagi]].

## Alternatifler / trade-off'lar
LLM'in doğrudan HTML yazması esnektir ama her düzenlemede tüm HTML'in okunması ve yazılması gerekir; pahalı ve hataya açık. JSON + bloklar yaklaşımı daha ucuz ve tutarlı. Hero sahneler için kaçış yolu bırakılır.

## Kaynaklar
- [[token-ekonomisi]] · [[hyperframes]]
