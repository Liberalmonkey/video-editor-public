---
type: decision
title: "Arayüzde yapım akışı ve motordan bağımsız olay sesi"
status: accepted
tags: [adr, arayuz, ses, kurgu, openmontage]
created: 2026-11-02
updated: 2026-11-02
sources: ["[[2026-11-02-kalem]]", "[[2026-11-02-loop-slayt]]"]
supersedes:
superseded_by:
---

# 0013 — Yapım akışı ve olay sesi

## Bağlam
Denetim: [[2026-11-02-usta-editor-denetimi]]. Kullanıcı sistemin 15 yıllık bir editör seviyesinde çalışmasını, arayüzün konu ya da hazır senaryodan başlayıp internetten konu önermesini, Story Circle senaryosu yazmasını, malzemeyi tek klasörde istemesini ve edit yapmasını istedi. Zoom, kesme ve geçiş seslerine özellikle dikkat istedi.

İncelemede iki boşluk çıktı. Varsayılan edit hattı OpenMontage'da SFX katmanı yoktu; 521 seslik kütüphane yalnız eski `vedit` hattına bağlıydı. Son teslim notunda ([php2shell]) "SFX yok" yazıyordu. Arayüz ise yalnız sohbet metni dolduran kısayollar sunuyordu, yapımın durumunu bilmiyordu.

## Seçenekler
1. Kalem'in tamamını (Tone.js sentezi, gl-transitions, yakalayıcı, motorlar) kopyalayıp kurmak.
2. OpenMontage Remotion kompozisyonuna ses katmanı eklemek. Yalnız Remotion çıktısına çalışır ve OpenMontage ayrı git deposudur.
3. Motordan bağımsız bir `olaylar.json` sözleşmesi ve var olan örnek kütüphaneyi kullanan `vedit olaysesi` komutu. Geçişler FFmpeg ile.

## Karar
Seçenek 3. Kalem'den fikirler alındı: görüntü olayı ile ses olayının aynı kareye yazılması, sahneye göre motor tablosu, ortak görsel dil dosyası, videoyu görmemiş denetçi.

- `src/vedit/olaysesi.py`: olay türü başına kategori, yön, tepe noktası, seviye. Görünmez kesme ve punch-in varsayılan sessizdir.
- `src/vedit/loop.py`: Flow klipleri için mühür ve sarma ölçümü.
- Skill'ler: `usta-editor`, `sahne-motoru`, `loop-flow`, `konu-arastirma`, `uretim-hatti`.
- Arayüz: **Yapım** sekmesi. Durum dosyalardan okunur: `uretim.json`, `girdi.md`, `script/senaryo.md`, `malzeme/istek.json`, `renders/`, `Projeler/`. Claude dosyaya yazar, arayüz okur; ayrı veritabanı yok.
- Proje `openmontage/projects/<tarih-slug>/`, malzeme `malzeme/<tür>/`. Dosya adı istek kimliğiyle başlıyorsa isteği karşılar.
- Konu önerileri tek dosya: `studios/konu-onerileri.json`. Web'den gelen bağlantılar yalnız http(s) ise tıklanabilir.
- Üretim aracı Google Flow'un bağlı API'si yok; klibi kullanıcı üretir, sistem prompt verir ve mühürler.
- higgsfield-studio deposunda lisans dosyası yok. Bu yüzden metin kopyalanmadı, yöntem kendi sözlerimizle yazıldı. Kalem MIT'tir, kod yine de kopyalanmadı.

## Sonuçlar
- Yeni bağımlılık yok. Geçişlerde gl-transitions'ın 125 shader'ı yerine FFmpeg `xfade` var.
- Paper.js, PixiJS, Manim, Matter.js, Rapier kurulu değil; sahne tablosu bunları "kurulum gerekli" gösterir, kullanıcı onayıyla kurulur.
- Ses kalitesi kütüphaneye bağlı. Whoosh ailesi zayıf: `library/sfx/INDIRME-LISTESI.md`.
- Ses kararları kurala dayalı ve testler yerleşimi ölçüyor; kulakla denenmedi. İlk gerçek videoda kullanıcı onayı gerekir.

## İlgili kod
- `src/vedit/olaysesi.py`, `src/vedit/loop.py`, `src/vedit/cli.py`, `scripts/test_olaysesi.py`
- `ui/server.mjs`, `ui/uretim.json`, `ui/public/app.js`, `ui/test.mjs`

> [!note] Güncellendi 2026-11-04
> Arayüz sekmesi ve `uretim.json` kalktı; akış ve olay sesi terminalde sürer: [[0017-terminal-hizli-hat]].
