---
type: decision
title: "Seslendirme: kullanıcı harici ses aracında üretir, TTS yok"
status: accepted
tags: [adr, seslendirme, tts]
created: 2026-10-21
updated: 2026-10-21
sources: []
supersedes: "[[0006-tts-yedegi]]"
superseded_by:
---

# ADR: Seslendirme kullanıcıdan gelir

## Bağlam
[[0006-tts-yedegi]] kayıt yoksa Chatterbox/Kokoro ile TTS yedeği öngörüyordu. Kullanıcı 2026-10-21'de sesini profesyonel bir harici programda klonladığını, oradan daha net ve temiz çıktı aldığını bildirdi ve Chatterbox ile ilgili her şeyin kaldırılmasını istedi.

## Seçenekler
| Seçenek | Artıları | Eksileri |
|---|---|---|
| Yerel TTS yedeği (Chatterbox) korunur | Kayıt yoksa hat durmaz | Ağır torch ortamı, 4 GB VRAM belirsiz, kullanıcının aracından düşük kalite |
| **Seslendirmeyi her zaman kullanıcı verir** | En temiz ses, kod ve bağımlılık azalır | Hat, kullanıcı dosyayı verene kadar bekler |

## Karar
- Akış: senaryo onayı → `script/teleprompter.md` kullanıcıya verilir → kullanıcı harici araçta seslendirir → `input/vo.wav` (WAV 48 kHz tercih; MP3 ise ffmpeg ile çevrilir; bölüm bölüm dosyalar sırayla birleştirilir).
- `vedit tts`, `src/vedit/tts.py`, `requirements-tts.txt` ve `.venv-tts` kaldırıldı.
- Ses yine `transcribe` → `audio` → `align` yolundan geçer; sahne zamanlaması değişmedi ([[youtube-animasyon-studyosu]]).

## Sonuçlar
- `voiceover` adımı tamamen kullanıcı adımıdır.
- Kullanıcıdan istenen dosya özellikleri: başta/sonda ~1 sn sessizlik, bölümler arasında doğal duraklama, içinde müzik/efekt yok.

## İlgili kod
`src/vedit/project.py` (ANIMATION_STEPS → voiceover), `.claude/skills/video/references/pipeline-animation.md`
