---
type: entity
kind: service
title: "Freesound"
tags: [sfx, api, cc0]
created: 2026-10-20
updated: 2026-10-20
url: https://freesound.org/docs/api/
sources: ["[[2026-10-20-sfx-ve-arac-arastirmasi]]"]
---

# Freesound

## Ne olduğu
Topluluk tarafından oluşturulan, API sunan ses efekti veritabanı ([[2026-10-20-sfx-ve-arac-arastirmasi]]).

## Yetenekler
- APIv2 metin araması, lisans ve süre filtresi, etiketler, LUFS loudness.
- Önizleme dosyaları (mp3/ogg) token ile indirilebilir; orijinal dosya OAuth2 gerektirir.

## Lisans / maliyet
- API anahtarı ücretsiz.
- Her sesin lisansı ayrı (CC0 / CC-BY / CC-BY-NC). **Sadece CC0 kullanılır.**

## Entegrasyon notları
- `vedit sfx fetch` komutu ortam değişkeninden `FREESOUND_API_KEY` okur.
- Arama filtresi: `license:"Creative Commons 0"`.
- HQ önizleme indirilir, işlenir ve manifest'e yazılır.

## Projedeki rolü
SFX kütüphanesinin 2. katmanı: isteğe bağlı çekme ([[sfx-stratejisi]], [[sfx-kutuphanesi]]).

## Kaynaklar
- [[2026-10-20-sfx-ve-arac-arastirmasi]]
