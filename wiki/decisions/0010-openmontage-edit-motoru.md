---
type: decision
title: "OpenMontage varsayılan edit motoru; /video hattı yalnız açık istekte"
status: accepted
tags: [adr, openmontage, pipeline, video, maliyet]
created: 2026-10-23
updated: 2026-11-22
sources: []
supersedes:
superseded_by:
---

# 0010 — OpenMontage varsayılan edit motoru

> [!note] Güncellendi 2026-11-22
> Grafik ve animasyon üretiminde birincil motor HyperFrames'tir ([[0050-hyperframes-birincil-motor]]); OpenMontage ve Remotion ikinci plandadır.

## Bağlam
Kullanıcı 2026-10-23'te "bundan sonra OpenMontage ile editler yapacağız" dedi. OpenMontage (calesthio/OpenMontage), kendi pipeline tanımları (`pipeline_defs/`), aşama yönetmeni skill'leri ve araç kayıt defteri olan ajan tabanlı bir video yapım çalışma alanıdır. Skill kütüphanesinden şablon olarak `openmontage/` klasörüne kuruldu; ayrı bir git deposudur ve ana repoda `.gitignore` ile dışarıda tutulur.

Mevcut `/video` skill'i her video isteğini yakalayıp `vedit` + HyperFrames hattına yönlendiriyordu. İki giriş noktası aynı isteği farklı hatlara götürürdü.

## Seçenekler
1. İki hattı yan yana bırakmak: istek hangi skill'in tetiklendiğine göre rastgele bir hatta gider.
2. `/video` hattını silmek: stil paketleri, SFX/müzik kütüphanesi ve ADR'lerdeki birikim kaybolur.
3. OpenMontage'ı varsayılan yapmak, `/video` hattını yalnız kullanıcı açıkça istediğinde çalıştırmak, ortak varlıkları (müzik kütüphanesi, stiller) paylaşmak.

## Karar
Seçenek 3.
- Edit ve üretim istekleri `openmontage/` içinde, onun `AGENT_GUIDE.md` kurallarıyla (Rule Zero: her üretim bir pipeline'dan geçer) yürütülür.
- `/video` skill'i yalnız kullanıcı "/video", "vedit" ya da eski hattı açıkça istediğinde kullanılır.
- Yalnız ücretsiz kaynak kuralı OpenMontage'da `config.yaml` içinde `budget.mode: cap`, `total_usd: 0.00` ile zorlanır. Ücretli sağlayıcı anahtarları `.env`'de bilerek boş bırakılır.
- Seslendirme kullanıcıdadır ([[0007-seslendirme-kullanici-harici-arac]]); OpenMontage'ın TTS araçları (`piper_tts` dahil) kurulmaz ve kullanılmaz.
- Müzik ortak kütüphaneden gelir ([[0008-harici-varlik-kaynaklari]]): OpenMontage `.env` içinde `MUSIC_LIBRARY_DIR` → `library/music`.
- HyperFrames sürümü ortaktır: `openmontage/` ana proje ağacının içinde olduğu için `npx hyperframes` sabitlenmiş 0.8.181'i çözer.

## Sonuçlar
- Donanım GTX 1650 (4 GB VRAM). CUDA'lı torch kuruldu; CLIP tabanlı klip arama/korpus, video anlama ve transkripsiyon yerel çalışır. Yerel görsel/video üretim modelleri (Wan, LTX, Hunyuan, CogVideo, Qwen Image) bu VRAM'de pratikte çalışmaz.
- Ücretsiz ama kayıt isteyen anahtarlar (Pexels, Pixabay, Unsplash, Freesound, Hugging Face) kullanıcı tarafından `.env`'e eklenmelidir.
- `openmontage/config.yaml` ve `.env` yerel değişikliktir; OpenMontage `git pull` ile güncellenirken `config.yaml` çakışması elle çözülür.

## İlgili kod
- `openmontage/config.yaml` (budget), `openmontage/.env` (`MUSIC_LIBRARY_DIR`)
- `.claude/skills/video/SKILL.md` (tetikleme daraltıldı), `CLAUDE.md` (OpenMontage bölümü)
