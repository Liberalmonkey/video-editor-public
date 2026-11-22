---
type: overview
title: İşlem Günlüğü (arşiv 4)
tags: [meta]
created: 2026-11-17
updated: 2026-11-17
---

# İşlem Günlüğü: arşiv 4 (2026-11-12)

Yeni girdiler [[log]] içindedir.

## [2026-11-12] code | Motion grafik: metin türleri, tam ekran sahneler, saydam pano
- `metin_stil.tip` ile 9 metin türü (`anahtar`, `altbant`, `etiket`, `cagri`, `daktilo`, `sayac`, `ilerleme`, `bolum`, `vurgu`), `layout: "full"` tam ekran sahneler, `vedit pano -o x.webm` saydam çıktı. [[0031-motion-grafik]]
- `library/motion/custom/` altında proje yapımı 9 kayıt (ok, daire, alt çizgi, üstünü çiz, vurgu patlaması, konfeti, onay, iki silme geçişi). `kit.json` yuvaları doldurulmadı, kilit kararı kullanıcıda.
- `aiedit.MOTION_OZETI` ve manifest'ten üretilen motion kataloğu ajan isteğine girdi; `kurgu.shot_bagla` sahne görselini `hazirla`'da bağlar.
- Doğrulandı: her tür için Remotion kare render'ı (dikey ve yatay), saydam webm `alpha_mode=1`; pytest 130, vitest 104.

## [2026-11-12] code | Ses araçları: ses çıkarma, 2 ve 4 kanallı ayırma
- `vedit ayristir <proje> [yol] [--stem 2|4] [--hepsi]` ve `vedit ses-cikar <proje> [yol] [--bicim wav|mp3|m4a] [--hepsi]`; ayırma ve ses çıkarma iş kuyruğunda. [[0034-ses-araclari]]
- Arayüzde hepsi Ses panelindeki "Ses araçları" bölümünde: sesi videodan ayır, dosyaya çıkar, konuşmayı müzikten ayır, arka plan müziğini kaldır, ayrılanları timeline'a ekle.
- Doğrulandı: `avatar-reel` `1.mp4` (14,9 sn) 4 kanal ayırma 24 sn; `ses-cikar` mp3 çıktısı.

## [2026-11-12] code | Hazır efektler ve yeni geçişler
- Klipte `hazir: [{ad, t, sure, ...}]`: 13 efekt (`zoom_in`, `zoom_out`, `punch`, `odak_zoom`, `ken_burns`, giriş ve çıkışlar, `sarsinti`, `nabiz`, `egim`, `bulanik_gir`). Matematik `studio/remotion/hazirEfekt.ts`, katalog `hazirEfekt.json`; önizleme ve render aynı kodu kullanır, el keyframe'i taban kalır. [[0033-hazir-efektler]]
- `src/vedit/hazir_efekt.py` ad ve aralık denetimi (`kurgu.denetle`) ve ses olayı (`kurgu.olaylar_uret`); Klip panelinde "Hazır efekt" bölümü ve "Keyframe'e çevir"; AI edit isteğine katalog her çalışmada json'dan girer.
- Giriş geçişine `zoom`, `it`, `savur`, `bulanik` türleri bağlandı (yalnız giren klip hareket eder).
- Doğrulandı: `odak_zoom` ve `punch` Remotion kare render'ı; pytest 147, vitest 110, `tsc` 0 hata, derleme geçti. Stüdyo paneli tarayıcıda elle denenmedi.

## [2026-11-12] code | Ses katmanı: kombolar, güç adları, Wyzowl kiti
- `olaysesi`: `KOMBOLAR` (`gecis_guclu`, `vurgu_guclu`, `acilis`), `yumusak|orta|sert` güç adları, sert olayda `light` darbe geri plana, ±1 dB ve ±%3 tohumlu çeşitleme, vuruş öncesi müzik çekme (`dip_egrisi`), baş ve son fade. Kaynaksız rol olayında `gain_db` artık tablo seviyesine eklenen fark. [[0032-ses-katmani]]
- `vedit sfx fetch wyzowl`: CC0, kodla sentezlenmiş 261 ses; kütüphane 610 → 871. earshot ölçümüyle 40 kayıt `aday`a alındı. `kit.json` yuvaları doldurulmadı, adaylar kullanıcıya sunuldu.
- AI edit ses kuralı: ajan dosya seçmez, `A2` izine kaynaksız rol olayı yazar; rol ve kombo adları koddan üretilir.
- Gerçek kayıt sinematik riser, sub drop, ters whoosh, tape stop için doğrulanmış CC0 bulunamadı: `library/sfx/INDIRME-LISTESI.md`.
