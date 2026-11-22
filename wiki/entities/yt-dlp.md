---
type: entity
kind: tool
title: "yt-dlp"
tags: [referans, indirme]
created: 2026-10-20
updated: 2026-10-20
url: https://github.com/yt-dlp/yt-dlp
sources: ["[[2026-10-20-sfx-ve-arac-arastirmasi]]"]
---

# yt-dlp

## Ne olduğu
YouTube ve benzeri sitelerden video, altyazı ve metadata indiren CLI aracı ([[2026-10-20-sfx-ve-arac-arastirmasi]]).

## Yetenekler
`--skip-download --write-auto-subs --sub-format json3` ile yalnızca altyazı indirir. `-f "bv*[height<=480]"` ile düşük çözünürlüklü video indirir.

## Lisans / maliyet
Unlicense, ücretsiz. Kurulu sürüm 2026.08.19.

## Entegrasyon notları
`vedit reference` komutu kullanır. İndirilen videolar yalnızca analiz içindir (kesim temposu, kontak sayfası); içerik kopyalanmaz, sadece "gramer" alınır.

## Projedeki rolü
Referans analizi → stil grameri ([[token-ekonomisi]], [[youtube-animasyon-studyosu]]).

## Kaynaklar
- [[2026-10-20-sfx-ve-arac-arastirmasi]]
