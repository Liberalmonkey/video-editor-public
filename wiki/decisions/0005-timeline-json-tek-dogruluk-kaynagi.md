---
type: decision
title: "timeline.json tek doğruluk kaynağı; HTML üretilir"
status: accepted
tags: [adr, mimari, timeline]
created: 2026-10-20
updated: 2026-11-15
sources: ["[[2026-10-20-hyperframes]]", "[[2026-10-20-ffmpeg]]"]
supersedes:
superseded_by:
---

# ADR: timeline.json tek doğruluk kaynağı

> [!note] Güncellendi 2026-11-15
> `timeline.json` yalnız eski `/video` hattının tek kaynağıdır. Güncel hatta `work/edit/kurgu.json` varsa tek kaynak odur; `olaylar.json` ondan üretilir ([[0021-video-studyo-nle]], [[0017-terminal-hizli-hat]]).

## Bağlam
LLM'in her düzenlemede HTML okuyup yazması pahalı ve tutarsız sonuç veriyor. HyperFrames kompozisyonları ise belirli kurallara uyan HTML gerektiriyor (id'ler, `.clip`, timeline kaydı) ([[2026-10-20-hyperframes]]).

## Seçenekler
| Seçenek | Artıları | Eksileri |
|---|---|---|
| JSON (şemalı) → üretici → HTML | Ucuz düzenleme, doğrulama, tutarlı stil | Blok kütüphanesinin bakımı gerekir |
| Doğrudan HTML | Esnek | Pahalı, hataya açık |

## Karar
- Her projede `edit/timeline.json` (pydantic şeması, `src/vedit/schemas.py`) ve çekim kurgusu için `edit/edl.json` bulunur.
- `vedit cut` EDL'yi FFmpeg ile A-roll'a uygular ([[2026-10-20-ffmpeg]]) ve eski → yeni zaman eşlemesini yazar.
- `vedit build`, timeline'ı `blocks/` şablonlarıyla HyperFrames kompozisyonuna çevirir. `custom` bloklar elle yazılmış alt kompozisyonlara işaret eder.
- Elle yapılan HTML düzenlemeleri bir sonraki build'de kaybolur. Kalıcı değişiklik ya JSON'a ya da `custom` bloğa yapılır.

## Sonuçlar
Düzeltmeler JSON yaması olarak verilir (ör. `overlays[3].start += 0.4`). HyperFrames `lint`/`check` hâlâ son kapıdır ([[timeline-json]]).

## İlgili kod
`src/vedit/schemas.py`, `src/vedit/build.py`, `src/vedit/cut.py`
