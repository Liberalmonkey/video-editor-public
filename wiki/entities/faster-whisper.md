---
type: entity
kind: library
title: "faster-whisper"
tags: [transkripsiyon, whisper]
created: 2026-10-20
updated: 2026-10-20
url: https://github.com/SYSTRAN/faster-whisper
sources: ["[[2026-10-20-sfx-ve-arac-arastirmasi]]"]
---

# faster-whisper

## Ne olduğu
CTranslate2 tabanlı hızlı bir Whisper uygulaması ([[2026-10-20-sfx-ve-arac-arastirmasi]]).

## Yetenekler
Kelime düzeyinde zaman damgaları (`word_timestamps=True`), VAD filtresi, Türkçe ve İngilizce. large-v3 ve large-v3-turbo modelleri Türkçede iyi sonuç veriyor.

## Lisans / maliyet
MIT, ücretsiz, yerel çalışır.

## Entegrasyon notları
- Bu makinede 1.2.1 kurulu.
- GTX 1650 (4 GB) için int8 GPU kullanılır; olmazsa CPU int8'e düşülür.

> [!note] Güncellendi 2026-10-21
> Sürücü 617.42 ile GPU doğrulandı: `cuda/int8_float16`, large-v3-turbo ~8 sn yükleme. Gereken DLL'ler (`cublas64_12`, `cudnn64_9`) `nvidia-cublas-cu12` + `nvidia-cudnn-cu12` paketlerinden gelir; `transcribe._cuda_dlls()` bunları yükler. `VEDIT_DEVICE=cpu` CPU'yu zorlar.
- Daha hassas kelime sınırları gerekirse WhisperX hizalaması (Türkçe wav2vec2 modeli) opsiyonel olarak eklenir.

## Projedeki rolü
`vedit transcribe` komutu bunu kullanır. Çıktısı digest, altyazı ve sahne zamanlamasının temelidir ([[token-ekonomisi]]).

## Kaynaklar
- [[2026-10-20-sfx-ve-arac-arastirmasi]]
