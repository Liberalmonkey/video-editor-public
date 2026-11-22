---
source_url: https://github.com/heygen-com/hyperframes
accessed: 2026-10-20
license: Apache-2.0
version_checked: hyperframes@0.8.181 (npm)
note: LLM inceleme notu + yerel kurulum doğrulaması (scratchpad'de init + render testi).
---

# HyperFrames — inceleme notu

"Write HTML. Render video. Built for agents." HeyGen'in açık kaynak HTML→MP4 framework'ü. bun monorepo: hyperframes (CLI), @hyperframes/core, engine (Puppeteer+FFmpeg), producer, studio, player, shader-transitions, aws-lambda.

## Kompozisyon sözleşmesi
- Kök: `<div id="root" data-composition-id data-width data-height data-duration>` doğrudan body içinde
- Zamanlı öğe: `class="clip"`, `id`, `data-start`, `data-duration`, (opsiyonel, sadece Studio şeridi) `data-track-index`
- Medya: `data-media-start` (trim), `data-volume` (1 = 0 dB, max 3.98), `data-fade-in/out`, `data-has-audio`, `data-playback-rate`, `data-automation` (volume/rate lane'leri)
- Her kompozisyon tek paused GSAP timeline'ı `window.__timelines["<id>"]`'e kaydeder
- Alt kompozisyon: `data-composition-src`, `<template>` sarmalı, değişkenler (`data-composition-variables`, `data-variable-values`, `--variables`)
- Render süresi kök data-duration'dan
- Determinizm: Date.now, seed'siz Math.random, ağ isteği yasak
- Her `<audio>` id ister (yoksa sessiz render); medyada crossorigin yasak; `.clip` üzerinde visibility/autoAlpha tween yasak; video ile atası aynı anda data-start taşıyamaz

## CLI
init, add, catalog, capture, preview, render, lint, check, beats, audio, inspect, keyframes, snapshot, media-treatment, normalize-audio, grade-compare, compare, info, compositions, timeline [--json], history, docs, benchmark, browser, doctor, skills, transcribe, models, tts (Kokoro-82M), remove-background, cloud/lambda/cloudrun.

## Render
`-f 24|30|60`, `-q draft|standard|high`, `-w` workers, `--crf`, `--gpu`, `--video-frame-format png` (UI kayıtları için), `-o`. Uzun render: `HF_SEGMENTED_CAPTURE=true` (3000 kare segment), `--resume`. Windows'ta çoklu worker disk üzerinden kare yazar (HF_CAPTURE_PARALLEL_STREAM=true ile stream).

## Yerel test (2026-10-20, bu makine)
`hyperframes doctor`: Node 24, FFmpeg 9.0.2 OK; sistem Chrome --version zaman aşımı → `hyperframes browser ensure` ile chrome-headless-shell 152 indirildi. 3 sn 1080p30 test: 90 kare, capture 5.2 sn (~17 fps), toplam 12.8 sn, drawelement capture + hardware gpu. Türkçe glifler (İŞĞÜÖÇ ı) doğru.

## Ajan entegrasyonu
CLAUDE.md, AGENTS.md, `.claude-plugin/marketplace.json`, 21 skill (router `hyperframes`; workflow: product-launch-video, faceless-explainer, pr-to-video, embedded-captions, talking-head-recut, motion-graphics, music-to-video, slideshow, general-video, remotion-to-hyperframes; domain: hyperframes-core, -animation, -keyframes, -creative, -cli, -audio, -registry, -studio, media-use, figma). Kılavuz: her düzenlemeden sonra lint+check; kullanıcı önizlemeyi onaylamadan render yok.

## Ses ve medya
hyperframes-audio: ducking, EQ/kompresör/limiter/reverb zinciri, volume automation, `<hf-audio-group>` bus. media-use resolve --type sfx: Openverse (CC0/CC BY) → 21 dosyalık paketli kütüphane. bgm HeyGen CLI ister.

## Gerçek çekim
Cut/trim/split/reorder/speed `<video data-media-start>` ile. Orta-klip freeze için önceden still çıkarılmalı. talking-head-recut / embedded-captions workflow'ları çekime dokunmaz, üstüne overlay koyar. Zoom/punch: zamanlı klibin içindeki `.inner` sarmalayıcıya GSAP scale.

## Altyazı
transcribe (whisper.cpp, Windows'ta Parakeet), ~20 altyazı stili katalogda.

## Registry
~400 blok/bileşen (`hyperframes add <ad>`, `catalog`).
