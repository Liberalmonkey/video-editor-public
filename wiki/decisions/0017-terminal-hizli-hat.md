---
type: decision
title: "Terminalden hızlı hat: arayüz kalktı, tek girdi/çıktı düzeni, kaizen döngüsü"
status: accepted
tags: [adr, hiz, token, kaizen]
created: 2026-11-04
updated: 2026-11-15
sources: []
supersedes: "[[0011-yerel-arayuz]]"
superseded_by:
---

# ADR: Terminalden hızlı hat

> [!note] Güncellendi 2026-11-15
> Aşağıda kaldırıldığı yazan `.agents/`, `.codex/` ve `AGENTS.md` [[0023-coklu-ajan]] ile geri geldi; kopyalar `scripts/ajan_esitle.py` ile üretilir. Arayüz bugün Video Stüdyo'dur ([[0021-video-studyo-nle]]); [[0019-arayuz-ve-efekt-motoru-birlesimi]] geçersizdir.

> [!note] Güncellendi 2026-11-04
> Arayüz kararı [[0019-arayuz-ve-efekt-motoru-birlesimi]] ile değişti: kullanıcı isteğiyle ince panel eklendi. Hızlı hat, düzen ve kaizen geçerlidir.

## Bağlam
Kullanıcı editlerin uzadığını, arayüzden her şeyi yürütmenin işleri bozduğunu bildirdi (2026-11-04). Ölçümler: 08 Reels'te her düzeltme ~7 dk'lık tam kalite render istedi (üç final, 12:36–12:51). 48 skill açıklama bütçesini doldurduğu için `usta-editor` ve `uretim-hatti` listede açıklamasız kalıyordu. Graphify hook'u her araç çağrısına metin ekliyordu. Proje medyası dört ayrı yere dağılmıştı. Her Reels için `at()`, doğrulama ve altyazı düzeltmesi elle yeniden yazılıyordu.

## Seçenekler
| Seçenek | Artıları | Eksileri |
|---|---|---|
| Arayüzü onarmak | Görsel kullanım kalır | Kök neden (render ve bağlam yükü) çözülmez, bakım sürer |
| Terminal + ince hat, seyrek skill'ler elle | Az kod, az bağlam, ölçülebilir | Görsel panel yok |
| Her şeyi tek skill'de birleştirmek | Liste çok kısalır | Kural kaybı riski yüksek, skill şişer |

## Karar
- **Arayüz kaldırıldı.** `ui/`, masaüstü kısayolu. Teleprompter `teleprompter` skill'ine, hazır istekler `uretim-hatti`'ye taşındı. Yapım akışı sözleşmesi (ADR 0013) `uretim.json` ve `istek.json` olmadan sürer; `ISTEK.md` kalır.
- **Tek düzen.** `Projeler/inputs/<stüdyo>/<proje>/` ve `Projeler/outputs/<stüdyo>/<proje>/` (ara dosyalar `work/`). `src/vedit/paths.py` tek kaynak; `input/…` yolları `paths.pj` ile girdi klasörüne çözülür.
- **Hızlı hat.** `vedit hazirla`, `kes`, `taslak`, `final`, `denetim`. Düzeltme taslakta, tam render bir kez. Reels sahnesi `reel_kit.mjs` ile; Remotion `--public-dir work/public` alır, proje başına küçük bundle.
- **Skill katmanları.** Sık 16 skill otomatik, seyrek 29 skill `disable-model-invocation: true` ile elle. `render-qa` ve `ai-slop-denetimi` kural kaybı olmadan `denetim` altında birleşti. `.agents/`, `.codex/`, `AGENTS.md` kaldırıldı (Codex kullanılmıyor).
- **Ajanlar 5 → 3.** `writer`, `director`, `render-qc`. Edit ana oturumda; `editor` metni `video/references/editor-gorevleri.md`'ye, `sound` kuralları `sound-design`'a taşındı.
- **Graf isteğe bağlı.** Proje hook'u kaldırıldı; `graphify` yalnız kod işinde.
- **Kaizen ve 6S.** Her komut `work/sure.jsonl` yazar. `vedit kaizen` satırı `library/kaizen.md`'ye ekler, `vedit duzen` düzeni denetler.

## Sonuçlar
- Her videoda süre verisi birikir; en yavaş adım görünür.
- `vedit` proje kökü `work/` oldu; `/video` hattı aynı komutlarla çalışır, teslim `work/` üstüne düşer.
- Görsel panel yok. Kütüphane düzenleme `library/kit.json` üzerinden yapılır.
- Token kullanımı `vedit` tarafından ölçülmez; `library/kaizen.md` yalnız araç süresi ve render sayısı tutar.
- Geri dönüş: git etiketi `pre-kaizen` (ana depo ve `openmontage`).

## İlgili kod
`src/vedit/hizli.py`, `src/vedit/paths.py`, `openmontage/remotion-composer/reel_kit.mjs`, `.claude/skills/uretim-hatti/SKILL.md`, `.claude/skills/denetim/`, `library/kaizen.md`.
