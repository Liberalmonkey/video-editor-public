---
type: decision
title: "Stil paneli: referanstan STYLE.md üretimi ve projeye stil seçimi"
status: accepted
tags: [adr, stil, style-pack, studio, referans]
created: 2026-11-12
updated: 2026-11-18
sources: []
---

# ADR: Stil paneli

## Bağlam
Kullanıcı Video Stüdyo'da bir stil bölümü istedi (2026-11-12): referans görsel ve video verince bir STYLE.md oluşsun, stili seçince edit ona göre yapılsın. Stil paketi düzeni (`studios/<stüdyo>/styles/<ad>/`), `style-pack` skill'i ve `vedit reference` vardı; eksik olan arayüz, yerel video analizi (yalnız YouTube linki ölçülüyordu) ve kurgu hattının seçili stili okumasıydı.

## Karar
| Konu | Karar | Neden |
|---|---|---|
| Depo | Referanslar `Projeler/inputs/_referanslar/<stüdyo>/<stil>/`, paket `studios/<stüdyo>/styles/<stil>/{STYLE.md, MOTION.md, tokens.json}` | Mevcut düzen; girdi yalnız `Projeler/inputs` altında |
| Üretim | `vedit stil-uret <stüdyo> <ad> [--motor] [--model]`: `reference.run` ölçer (tempo, kontak sayfası, görsel ızgarası), ajan `style-pack` şablonlarıyla üç dosyayı yazar | Ölçüm deterministik, yorum ajanın; [[0028-ai-edit]] ile aynı iş bölümü |
| Yerel video | `reference.analyze_file`; `analyze_url` indirdikten sonra onu çağırır | Kullanıcı dosya yüklüyor, link vermiyor |
| Seçim | Proje başına `work/edit/stil.txt`; yoksa `studio.yaml → style` | Kurgu şemasına alan eklemeden; `ai-edit` isteğe STYLE.md ve MOTION.md yolunu koyar |
| Doğrulama | Üç dosya yoksa ya da `tokens.json` geçersizse çıkış kodu 1 | Yarım paket seçilemez |
| Sabit | Altyazı standardı ([[0014-altyazi-standardi-ve-repo-entegrasyonu\|ADR 0014]]) stil paketiyle ezilmez | Proje sabiti |
| Arayüz | Stil paneli: stil listesi, referans yükleme, "Stil üret", STYLE.md düzenleme, "Bu projede kullan" | Kullanıcı isteği |

## Sonuçlar
- Stüdyo API: `GET /api/stil/{s}?proje=`, `PUT|DELETE /api/stil/{s}/{ad}/referans`, `PUT /api/stil/{s}/{ad}`, `POST /api/stil/{s}/sec`; üretim iş kuyruğu beyaz listesinde `stil-uret`.
- Stil şu an editi ajan isteği üzerinden yönlendirir (kesim temposu, geçiş ailesi, renk düzeltme, ses). `tokens.json` kurgu render'ına otomatik bağlanmaz.

> [!note] Güncellendi 2026-11-18
> Stil silme, hazır stil kataloğu ve `tokens.json → motion_tema` bağı eklendi: [[0042-stil-katalogu-ve-video-temasi]].

## İlgili kod
- `src/vedit/stil.py`, `src/vedit/reference.py` (`analyze_file`), `src/vedit/cli.py` (`cmd_stil_uret`)
- `src/vedit/studio/stil.py`, `src/vedit/studio/isler.py`, `studio/web/src/paneller/StilPaneli.tsx`, `studio/web/src/main.tsx`
- Testler: `tests/test_stil.py`, `tests/test_studio_dosya.py`
