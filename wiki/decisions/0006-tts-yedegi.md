---
type: decision
title: "TTS yedeği: Chatterbox (TR/EN, ses klonlama), Kokoro (EN)"
status: superseded
tags: [adr, tts, seslendirme]
created: 2026-10-20
updated: 2026-10-21
sources: ["[[2026-10-20-sfx-ve-arac-arastirmasi]]"]
supersedes:
superseded_by: "[[0007-seslendirme-kullanici-harici-arac]]"
---

# ADR: TTS yedeği

> [!note] Güncellendi 2026-10-21
> Bu karar [[0007-seslendirme-kullanici-harici-arac]] ile geçersiz. Kullanıcı sesini harici bir araçta üretiyor; Chatterbox kodu, `vedit tts` ve `requirements-tts.txt` kaldırıldı. Aşağısı tarihsel kayıttır.

## Bağlam
Seslendirme kullanıcının kendi sesiyle yapılacak; kayıt yoksa ücretsiz bir TTS yedeği gerekiyor. İçerik Türkçe ve İngilizce, GPU 4 GB.

## Seçenekler
| Seçenek | Artıları | Eksileri |
|---|---|---|
| Chatterbox Multilingual | MIT, Türkçe, kullanıcının sesini klonlar | 4 GB VRAM'de çalışıp çalışmadığı doğrulanmadı |
| Kokoro (`hyperframes tts`) | Hızlı, kaliteli, yerleşik | Türkçe yok |
| Piper | CPU'da hızlı | Türkçe ses kalitesi orta |
| XTTS / F5-TTS | Kaliteli | Ağırlıklar ticari değil |
| ElevenLabs | En iyi Türkçe | Ücretli |

## Karar
- Türkçe ve İngilizce için Chatterbox Multilingual; kullanıcının 10–20 sn referans kaydından klonlanır.
- İngilizce için hızlı alternatif: Kokoro.
- Chatterbox GPU'da çalışmazsa CPU'ya, o da çok yavaşsa Piper'a düşülür.
- Kurulum opsiyonel: `requirements-tts.txt`, ayrı venv.

## Sonuçlar
TTS çıktısı da `transcribe` adımından geçer. Böylece sahne zamanlaması kullanıcı kaydıyla aynı yoldan yapılır ([[youtube-animasyon-studyosu]]).

## İlgili kod
~~`src/vedit/tts.py`~~ (2026-10-21'de silindi)
