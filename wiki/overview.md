---
type: overview
title: Proje Genel Bakış
tags: [meta, overview]
created: 2026-10-20
updated: 2026-10-20
sources: ["[[2026-10-20-opus-animasyon-rehberi]]", "[[2026-10-20-hyperframes]]", "[[2026-10-20-sfx-ve-arac-arastirmasi]]"]
---

# AI Video Editor — Genel Bakış

> [!info] Bu sayfa projenin yaşayan sentezidir. Her ingest, karar ve spec sonrası LLM tarafından güncellenir.

## Vizyon
Kullanıcının kendi video projelerini profesyonel kalitede kurgulayan, Claude Code içinde çalışan bir "yapım stüdyosu". Sistem üç uzman rolü üstlenir:
- **Senarist:** hook, retention yapısı, humanizer ile insan sesi.
- **Yönetmen:** ışık, ses, çekim açısı, stil grameri, sahne listesi.
- **Editör/motion designer:** kesim, altyazı, motion graphics, ses tasarımı.

Kalite birinci öncelik, token tasarrufu ikinci ([[0001-claude-code-skill-ajan-mimarisi]]).

## Hedef kullanıcılar
Tek bir içerik üreticisi (kullanıcının kendisi). İçerik Türkçe ve İngilizce.

## Temel özellikler
Üç ayrı stüdyo klasörü:
- [[youtube-animasyon-studyosu]]: 10–15 dk eğitici/eğlenceli animasyon.
- [[ugc-studyosu]]: ürün tanıtımı ve satış odaklı çekim kurgusu.
- [[instagram-studyosu]]: Reels.

Ortak altyapı: [[sfx-kutuphanesi]], altyazı, ses mastering ([[loudness-standartlari]]), otomatik QA ve eleştirmen döngüsü.

## Teknik yön
- **Renderer:** [[hyperframes]] (HTML+GSAP); kesim ve ses için [[ffmpeg]] ([[0002-renderer-hyperframes]]).
- **Veri:** [[timeline-json]] tek doğruluk kaynağı; LLM JSON yazar, HTML üretilir ([[0005-timeline-json-tek-dogruluk-kaynagi]]).
- **Modeller:** ana oturum Opus, alt ajanlar opus/sonnet/haiku ([[0003-model-yonlendirme]], [[model-yonlendirme]]).
- **Maliyet ilkeleri:** [[token-ekonomisi]].
- **Motion design zevki:** [[motion-design-ilkeleri]] ve [[render-sozlesmesi]]; ilham kaynağı [[opus-animasyon-rehberi]].
- **SFX:** [[sfx-stratejisi]] ([[0004-ses-efekti-stratejisi]]).
- **Seslendirme:** kullanıcı harici araçta kendi klon sesiyle üretir, TTS yok ([[0007-seslendirme-kullanici-harici-arac]]).
- **Müzik/SFX/motion:** kullanıcı 6 siteden indirir, ajan ayrıntılı tarif eder; teslim `Projeler/` ([[0008-harici-varlik-kaynaklari]]).
- **Bütçe:** yalnızca ücretsiz araç ve kaynaklar (kullanıcı kararı, 2026-10-20).

## Donanım
Windows 11, GTX 1650 4 GB, 16 GB RAM, i5-11400H. ~~NVIDIA sürücüsü 462.75 (CUDA 11.2) → transkripsiyon CPU int8.~~

> [!note] Güncellendi 2026-10-21
> Sürücü 617.42'ye güncellendi (CUDA 13.4). CUDA 12 cuBLAS + cuDNN 9 pip paketleriyle (`pip install -e .[gpu]`) faster-whisper GPU'da `int8_float16` çalışıyor. Render ~17 fps (basit 1080p30 sahne), bölüm başına tek worker.

## Durum (2026-10-20)
v1 hattı uçtan uca test edildi: UGC 9:16 (cut → reframe → overlay → bold-pop altyazı → SFX + ducking → -14 LUFS) ve animasyon 16:9 (scenes → align → bölüm render + önbellek). 17 blok, 517 CC0 SFX, 10 skill, 8 ajan. Kullanıcı rehberi: README.md.

> [!note] Güncellendi 2026-10-21
> Ajanlar 3'e indirildi (writer, director, editor; [[0003-model-yonlendirme]]). Codex kopyaları (`.agents/`, `.codex/`, `AGENTS.md`), test projeleri ve kullanılmayan `media-use` + `hyperframes-registry` skill'leri silindi.

## Açık sorular
- Platform referans görselleri bekleniyor (her stüdyonun `references/` klasörüne).
- 12 dk render süresi ölçülecek.
- Stüdyo stil paketleri (STYLE.md/MOTION.md) kullanıcının referanslarıyla yazılacak.

## İlgili
- [[index]] · [[log]]
