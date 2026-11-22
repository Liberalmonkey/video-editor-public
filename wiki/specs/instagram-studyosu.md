---
type: spec
title: "Instagram stüdyosu — Reels"
status: active
tags: [spec, instagram, reels, kisa-video]
created: 2026-10-20
updated: 2026-10-20
sources: ["[[2026-10-20-opus-animasyon-rehberi]]", "[[2026-10-20-hyperframes]]"]
decisions: ["[[0002-renderer-hyperframes]]"]
---

# Instagram stüdyosu

## Problem
Instagram Reels için 15–90 sn'lik, ilk saniyede durduran, sessiz izlendiğinde de anlaşılan videolar gerekiyor. Kaynak çekim, animasyon ya da ikisinin karışımı olabilir.

## Kullanıcı hikâyeleri
- Bir içerik üreticisi olarak çekimimi veya bir konuyu verip Reels formatında, kapak karesi güçlü ve loop'a uygun bir video almak istiyorum.
- Referans Reels görsellerime göre tutarlı bir seri stili istiyorum.

## Kapsam
### Dahil
- 9:16 1080x1920 format
- Güvenli alanlar: Instagram arayüzü nedeniyle üst ~%12 ve alt ~%20 içerikten boş bırakılır ([[2026-10-20-opus-animasyon-rehberi]])
- Kinetik altyazı, hızlı tempo (her 1–2 sn'de anlamlı değişim)
- Beat senkronu, SFX, loop sonu
- Kapak karesi önerisi

### Hariç
- Instagram'a otomatik yükleme

## Tasarım
`studios/instagram/`:
- `CLAUDE.md`: Reels kuralları
- `studio.yaml`: 1080x1920, 30 fps, -14 LUFS, kinetik altyazı stili

Kaynak çekimse UGC akışı, animasyonsa kısa animasyon akışı kullanılır (`video` skill'i → `references/pipelines/reels.md`).

## Kabul kriterleri
- [ ] İlk kare tek başına kapak olarak okunuyor
- [ ] Önemli metinlerin hiçbiri güvenli alan dışında değil (QA ölçer)
- [ ] Sessiz izlendiğinde anlaşılıyor (altyazı/metin)
- [ ] Loudness hedefte

## Açık sorular
- Kullanıcının platform referans görselleri bekleniyor.
