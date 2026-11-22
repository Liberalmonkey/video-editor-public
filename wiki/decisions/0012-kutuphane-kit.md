---
type: decision
title: "Kütüphane kiti: kilitli ve her zaman kullanılan varlıklar (library/kit.json)"
status: accepted
tags: [adr, kutuphane, sfx, motion, arayuz]
created: 2026-11-01
updated: 2026-11-15
sources: []
supersedes:
superseded_by:
---

# 0012 — Kütüphane kiti: kilitli ve her zaman kullanılan varlıklar

> [!note] Güncellendi 2026-11-15
> Motion kaydı artık manifest'e elle yazılmaz: kayıt `library/motion/custom/<id>/` altındaki `meta.json`'dır, manifest'i `vedit motion kur` üretir. Kütüphane, Video Stüdyo'da Kütüphane alanında yeniden vardır (Kütüphane > Motion) ([[0036-motion-kutuphanesi-ve-ajanlar]], [[0021-video-studyo-nle]]).

## Bağlam
`library/` altında SFX (521 CC0), müzik ve motion manifest'leri vardı ([[0004-ses-efekti-stratejisi]], [[0008-harici-varlik-kaynaklari]]). Eksikler:
- Projeye özel üretilen grafikler (ör. "abone ol" animasyonu) kayıt altında değildi; her videoda yeniden üretiliyordu.
- Bazı varlıklar her videoda aynı olmalı (klavye sesi, fare tıklaması, abone ol), ama bunu söyleyen bir kayıt yoktu.
- Ajanın bir varlığı değiştirmemesini söylemenin yolu yoktu.
- Kütüphane yerel arayüzde ([[0011-yerel-arayuz]]) görünmüyordu.

## Seçenekler
1. Manifest kayıtlarına `locked` / `role` alanı eklemek. `src/vedit/schemas.py` içindeki SFX şemasını ve `vedit sfx` akışını etkiler.
2. Ayrı bir `library/kit.json` dosyası. Manifest'ler kayıt olarak kalır, kit yalnız kilit ve rolleri tutar.

## Karar
Seçenek 2.
- `library/kit.json`: `locked` (kimlik listesi) ve `always[stüdyo|*][rol] = kimlik | null`. Stüdyoya özel rol `*` rolünü ezer. `null` boş yuvadır: ilk ihtiyaçta bir kez üretilir, kaydedilir, kilitlenir.
- Başlangıç: `keyboard` → `typing-synth-typing-01`, `mouse_click` → `click-remotion-mouse-click` (tüm stüdyolar, kilitli); `youtube-animasyon.subscribe` boş yuva.
- Özel grafikler `library/motion/custom/<id>/` altında: şeffaf `<id>.webm` render + kaynak dosya. Motion manifest'ine `site: "custom"` ile kaydedilir. Bu klasör git'e girer (`.gitignore` istisnası), çünkü yeniden üretilmemesi gereken tek kopyadır.
- Ajan kuralı kök `CLAUDE.md`'de: önce kit ve manifest'lere bak, rolleri kullan, kilitli varlığı kullanıcı istemedikçe değiştirme.
- Arayüzde **Kütüphane** sekmesi: birleşik liste, arama, tür filtresi, önizleme, kilit düğmesi, rol atama ve kütüphaneye yükleme. Rol atanan varlık otomatik kilitlenir.

## Sonuçlar
- Manifest şemaları değişmedi; `vedit` etkilenmedi.
- Kilit bir sözleşmedir, dosya sistemi izni değildir. Uyum, ajanın `CLAUDE.md` kuralına uymasına dayanır.
- Kullanıcı kilit ve rolleri arayüzden değiştirebilir; ajan yalnız açık istekle değiştirir.

## İlgili kod
- `ui/server.mjs`: `library()`, `setKit()`, `GET /api/library`, `POST /api/library/kit`
- `ui/public/app.js`: kütüphane bölümü; `ui/test.mjs`: kütüphane testleri
- `library/kit.json`, `library/motion/manifest.json` (`_note`)

> [!note] Güncellendi 2026-11-04
> Kütüphane sekmesi kalktı; `library/kit.json` doğrudan düzenlenir: [[0017-terminal-hizli-hat]].
