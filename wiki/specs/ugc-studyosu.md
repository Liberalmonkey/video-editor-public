---
type: spec
title: "UGC stüdyosu — ürün tanıtımı ve satış odaklı video"
status: active
tags: [spec, ugc, satis, cekim]
created: 2026-10-20
updated: 2026-10-20
sources: ["[[2026-10-20-opus-animasyon-rehberi]]", "[[2026-10-20-hyperframes]]", "[[2026-10-20-sfx-ve-arac-arastirmasi]]"]
decisions: ["[[0002-renderer-hyperframes]]", "[[0005-timeline-json-tek-dogruluk-kaynagi]]"]
---

# UGC stüdyosu

## Problem
Kullanıcı kendini çektiği videoları, ekran kayıtlarını ve ses dosyalarını veriyor. Bunlardan satış odaklı, profesyonel ürün tanıtım videoları çıkmalı.

## Kullanıcı hikâyeleri
- Bir içerik üreticisi olarak ham çekimlerimi `input/` klasörüne koymak ve hook → problem → demo → kanıt → CTA yapısında kurgulanmış bir video almak istiyorum, böylece reklam veya organik olarak kullanabileyim.
- Çekimden önce bir çekim planı (ışık, mikrofon, açı, çekilecek planlar listesi) istiyorum, böylece kurguda eksik plan kalmasın.
- Aynı kurgunun 9:16, 4:5 ve 16:9 varyantlarını istiyorum.

## Kapsam
### Dahil
- Konuşan kafa çekimi, ekran kaydı, ürün B-roll'u
- Take seçimi, dolgu ve sessizlik temizliği, punch-in, J/L cut
- Altyazı (kelime vurgulu), ürün kartı, fiyat/teklif kartı, CTA, end card
- Ses temizleme ve mastering, müzik, SFX
- 3 en-boy varyantı, otomatik reframe

### Hariç
- AI ile üretilen insan/avatar videosu
- Ücretli stok görüntü

## Tasarım
`studios/ugc/` klasörü:
- `CLAUDE.md`: satış kuralları. İlk 3 sn hook, fayda önce, sosyal kanıt, tek CTA, abartılı iddia yok.
- `studio.yaml`: varsayılan format 1080x1920, 30 fps; varyantlar.
- `references/`, `styles/`, `projects/`

**Akış:**
1. `plan-shoot` (opsiyonel)
2. `ingest`, `transcribe`, `digest`
3. `editor` → `edl.json` (onay)
4. `cut`, `audio`, `reframe`
5. `director` (treatment) + `editor` → `timeline.json`
6. SFX ve müzik
7. Önizleme → QA → `director` (critique) → final + varyantlar

## Kabul kriterleri
- [ ] 1–2 dk ham çekimden, 30–60 sn'lik 9:16 video
- [ ] -14 ±1 LUFS, TP ≤ -1 dBTP
- [ ] Siyah/donuk kare yok
- [ ] Altyazı güvenli alanda
- [ ] Critic rubriğinde tüm puanlar ≥ 8
- [ ] 4:5 ve 16:9 varyantları tek komutla üretiliyor

## Açık sorular
- Kullanıcının referans görselleri `studios/ugc/references/` klasörüne gelecek. Stil grameri ondan sonra çıkarılacak.
