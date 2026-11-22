---
type: concept
title: "Loudness standartları ve ses mix seviyeleri"
tags: [ses, loudness, mastering]
created: 2026-10-20
updated: 2026-10-20
sources: ["[[2026-10-20-ffmpeg]]", "[[2026-10-20-sfx-ve-arac-arastirmasi]]"]
---

# Loudness standartları

## Tanım
Teslim edilen videonun algılanan ses yüksekliği (LUFS) ve tepe değeri (dBTP) hedefleri.

## Nasıl çalışır
- **Ölçüm:** EBU R128 / ITU BS.1770 entegre loudness (LUFS), true peak (dBTP) ve loudness range (LRA) ([[2026-10-20-ffmpeg]]).
- **Teslim hedefi:** YouTube, Instagram ve TikTok için -14 LUFS entegre, en fazla -1 dBTP.
- **Mix katmanları (göreli):**
  - Konuşma: ana referans, yaklaşık -16…-14 LUFS konuşma bölümü.
  - Müzik yatağı: konuşma varken sesin yaklaşık 18–22 dB altında (ducking). Konuşma yokken yükselir.
  - SFX: konuşmanın 8–14 dB altında ([[2026-10-20-sfx-ve-arac-arastirmasi]]).
- **Konuşma zinciri:** highpass 80 Hz → gürültü azaltma → EQ (gerekiyorsa 200–300 Hz çamur kesme, 3–5 kHz netlik) → kompresör (3:1) → 2 geçişli loudnorm.

## Projede kullanımı
`vedit audio master` bu zinciri uygular. `vedit qa` sonucu ölçer; kabul aralığı -14 ±1 LUFS ve TP ≤ -1 dBTP.

> [!question] Çıkarım
> Konuşma zinciri değerleri sektör pratiğinden alındı, kaynakta yazmıyor.

## Alternatifler / trade-off'lar
-16 LUFS (Apple ve podcast standardı) daha fazla dinamik bırakır. Sosyal medyada -14 LUFS, platform normalizasyonuyla en uyumlu değer.

## Kaynaklar
- [[2026-10-20-ffmpeg]] · [[sfx-stratejisi]]
