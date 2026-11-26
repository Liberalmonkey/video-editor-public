---
type: decision
title: "0062 · Modern HyperFrames Motion Mimarisi ve 24 Bileşen Kütüphanesi"
tags: [hyperframes, motion, stil, swarm, kamera, gecis]
status: accepted
created: 2026-11-25
updated: 2026-11-25
---

# ADR 0062: Modern HyperFrames Motion Mimarisi

## Bağlam
HyperFrames `0.9.84` uçtan uca birincil motor olsa da (ADR 0050, 0051) stüdyo kalitesini engelleyen yedi somut darboğaz vardı:
1. Özel `hf: {ad, param}` kompozisyonları `data-composition-src` ile canlı gömülmek yerine çevrimdışı VP9 WebM olarak ön-render ediliyordu (~25-30 sn soğuk başlangıç).
2. `library/motion/hf/` altında yalnızca 1 özgün şablon (`alt-bant`) bulunuyordu; 60 native bileşen Remotion 1:1 portuna kilitli tek tip bir zarf kullanıyordu.
3. Bağımsız HF kompozisyonları `tema.css` üzerinden 4'lü easing, RGB kanal ve cam/ızgara yüzey token'larını alamıyordu.
4. 4-düzen kurgu disiplini (Nick Saraev), sürekli-dünya kamera zoom/pan (Nate Herk) ve tıklamadan tetiklenen optik geçişler kurgu sözleşmesinde yoktu.
5. Swarm `editor-grafik` ajanı `SOZLESME.md`, stil hareket kuralları, Kasam ve komşu dilim sınır grafiklerinden habersizdi.

## Karar
- **Canlı HF Alt-Kompozisyon Gömme (`derle.ts`, `cli.ts`, `paketle.ts`, `hf_grafik.py`, `app.py`, `hfOnizleme.ts`):** Özel tema ezmesi olmayan `hf` klipleri çevrimdışı WebM üretmeden doğrudan `data-composition-src="hf/g/<kok>.html"` (`<template>` sarıcı + `HF_CTX` + kapsamlı GSAP proxy) ile hem render'da hem Stüdyo önizlemesinde (`/hfg/`) canlı çalışır.
- **Tema Token v2 (`tema_token.py`):** `tema.css` çıktısına `--*-rgb`, `--yuzey-cam`, `--kenar-ince`, `--yukselti-golge`, `--izgara-desen`, `--ease-enter/exit/emphasis/settle`, `--adim-fps` eklendi (`piksel-8bit.css` gradyan ve bulanıklık olmadan korunur).
- **HFN Çekirdek & Ses Senkronu (`cekirdek.ts`, `hf_grafik.py`, `kurgu.py`):** Kapalı-form deterministik yay çözücüsü (`yayCoz`) ve hız bulanıklığı (`yonBulaniklik`) eklendi; kompozisyonlardaki `data-sound-cues` bildirimleri `+1 kare` gecikmeyle `olaysesi` olaylarına otomatik aktarılır.
- **4-Düzen, Sürekli-Dünya Kamera, 5 Optik Geçiş & BPM Kilidi (`zaman.ts`, `gecis.ts`, `hazirEfekt.ts`, `ritim.py`):** `duzen: konusmaci | diyagram-pip | ekran-pip | tam-kanit`, `ekran_odak` ve `dunya_kaydir` hazır kamera efektleri, 5 optik geçiş (`tikla_iris`, `buton_zoom`, `kart_dunyaya`, `bulanik_takas`, `dip_kesim`) ve sıfır-kaymalı `ritim.bpm_izgara()` eklendi.
- **24 Modern HyperFrames Şablonu + 5 Referans Stil (`library/motion/hf/`, `library/stiller/katalog.json`):** 6 ailede (SaaS UI, İş Akışı, Editoryal Tipografi, Veri Hikâyeciliği, 3B Derinlik, Mikro-Fizik) 24 yeni deterministik, Türkçe glifli, `16:9` + `9:16` uyumlu şablon ve 5 referans stil (`saas-izgara`, `kod-hud`, `beyaz-tahta-pro`, `editoryal-belgesel`, `urun-lansman`) eklendi.
- **Swarm v4 & Anti-Slop Kapıları (`ekip_v3.py`, `kurgu_kalite.py`, `.claude/agents/`):** G0.5 Motion Brifi, `tema.css` v2 özeti, komşu dilim sınır grafikleri, `YUZ_USTU_KART` yüz hijyeni uyarısı ve determinizm statik kapısı (`hf_determinizm_hatalari`) eklendi.

## Sonuçlar
- `library/motion/hf/` 1 şablondan 25 özgün şablona, hazır stil kataloğu 31'den 36'ya çıktı.
- Tüm yeni şablonlar sıfır sabit renk/font, sıfır determinizm ihlali ve canlı alt-kompozisyon testleriyle (`tests/test_hf_motion_kalite.py`) korunur.

## İlgili
[[0050-hyperframes-birincil-motor]] · [[0051-uctan-uca-hyperframes]] · [[0043-stile-bagli-tema-tokenlari]] · [[0059-swarm-edit]]
