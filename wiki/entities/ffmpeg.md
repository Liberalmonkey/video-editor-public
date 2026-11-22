---
type: entity
kind: tool
title: "FFmpeg"
tags: [ffmpeg, kurgu, ses]
created: 2026-10-20
updated: 2026-10-20
url: https://ffmpeg.org
sources: ["[[2026-10-20-ffmpeg]]"]
---

# FFmpeg

## Ne olduğu
Medya dönüştürme, kesme, filtreleme ve ölçme için standart araç ([[2026-10-20-ffmpeg]]).

## Yetenekler
- ffprobe envanteri
- trim/concat ile kesim
- loudnorm, ebur128, sidechaincompress, afftdn ile ses işleme
- blackdetect, freezedetect, scene select ile QA
- tile ile kontak sayfası
- NVENC ile donanım kodlama

## Lisans / maliyet
LGPL/GPL, ücretsiz.

## Entegrasyon notları
Kurulu sürüm 9.0.2 full build (winget, gyan.dev). Python tarafından `subprocess` ile çağrılır (`src/vedit/ff.py`).

## Projedeki rolü
`vedit` aracının ölçüm, kesim ve ses mastering katmanı. HyperFrames da render için kullanır. Hedef değerler: [[loudness-standartlari]].

## Kaynaklar
- [[2026-10-20-ffmpeg]]
