---
type: source
title: "SFX, müzik, TTS ve çekim araçları araştırması"
tags: [sfx, muzik, tts, lisans, arac]
created: 2026-10-20
updated: 2026-10-20
raw: raw/notes/2026-10-20-sfx-ve-arac-arastirmasi.md
url:
author: LLM araştırması (alt ajan)
sources: []
---

# SFX, müzik, TTS ve çekim araçları araştırması

## Özet
Ticari YouTube ve Instagram kullanımına uygun ücretsiz SFX/müzik kaynakları, AI ses üretiminin lisans durumu, ücretsiz TTS seçenekleri ve çekim kurgusu araçlarının karşılaştırması ([[raw/notes/2026-10-20-sfx-ve-arac-arastirmasi]]).

## Ana çıkarımlar
- **Ücretsiz ve güvenli SFX kaynakları:**
  - Kenney (CC0)
  - Freesound (yalnızca CC0 filtresiyle) → [[freesound]]
  - Openverse
  - `@remotion/sfx` içindeki CC0 sesler
  - Mixkit
  - Sonniss GDC paketleri
- **Kaçınılacaklar:** BBC SFX, CC-BY-NC sesler, YouTube Audio Library'nin standart lisanslı parçaları (Instagram'da), ağırlıkları ticari olmayan AI modelleri (MMAudio, AudioCraft, F5-TTS, XTTS).
- **Önerilen yöntem:** yerel kürate kütüphane + isteğe bağlı çekme + sentez. Yerleştirme büyük ölçüde deterministik; LLM yalnızca anlamsal ipuçlarını ekler → [[sfx-stratejisi]].
- **Türkçe TTS:** ücretsiz seçenekler içinde en iyisi Chatterbox Multilingual (MIT, ses klonlama). Kokoro Türkçe desteklemiyor. (Güncellendi 2026-10-21: TTS kullanılmıyor, bkz. [[0007-seslendirme-kullanici-harici-arac]].)
- **Transkripsiyon:** [[faster-whisper]] (kurulu). WhisperX Türkçe hizalama modeli sunuyor.

## Projeye etkisi
Kararlar: [[0004-ses-efekti-stratejisi]] ve [[0006-tts-yedegi]]. Spec: [[sfx-kutuphanesi]].

## Çelişkiler / açık sorular
- Zapsplat ve BBC lisans bilgileri ikincil kaynaktan geldi, doğrulanmadı.
- Chatterbox'ın 4 GB VRAM'de çalışıp çalışmadığı doğrulanmadı.

## Bağlantılı sayfalar
- [[sfx-stratejisi]] · [[kenney-audio]] · [[freesound]] · [[yt-dlp]]
