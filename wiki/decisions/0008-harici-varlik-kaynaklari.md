---
type: decision
title: "Müzik, SFX ve motion grafik: kullanıcı 6 siteden indirir; teslim Projeler/ klasörüne"
status: accepted
tags: [adr, muzik, sfx, motion, lisans, teslim]
created: 2026-10-21
updated: 2026-10-21
sources: ["[[2026-10-20-sfx-ve-arac-arastirmasi]]"]
supersedes:
superseded_by:
---

# ADR: Harici varlık kaynakları ve teslim klasörü

## Bağlam
`library/music/` boştu. [[0004-ses-efekti-stratejisi]] SFX'i CC0 kütüphane, API çekme ve sentezle çözüyor, ama müzik ve motion grafik için kaynak yoktu. Kullanıcı 2026-10-21'de sürekli kullandığı 6 siteyi verdi ve dosyaları kendisinin indirmek istediğini söyledi; ajan neyin gerektiğini ayrıntılı tarif edecek. Kullanıcı ayrıca bitmiş videolar için kökte `Projeler/` klasörü açmıştı.

## Seçenekler
| Seçenek | Artıları | Eksileri |
|---|---|---|
| Ajan API/scraping ile indirir | Hızlı | Sitelerin çoğunda API yok, giriş/indirme kuralları var; lisans riski |
| **Kullanıcı indirir, ajan tarif eder** | Lisans kontrolü kullanıcıda, siteler onun hesabıyla çalışır | Bir kullanıcı adımı eklenir |

## Karar
- **Siteler:** Pixabay, Mixkit (atıfsız) · Bensound, NCS, Uppbeat, Audio Library (atıf zorunlu).
- **Talep:** ajan önce kütüphaneye bakar; eksikler için `direction/assets-request.md` yazar.
  - Müzik: tür, ruh hâli, BPM, enstrüman, vokal, enerji eğrisi, süre, kullanım aralığı.
  - SFX: ses karakteri, süre, adet, tetikleyen olay.
  - Motion: stil + somut görsel özellikler, çözünürlük, alpha, süre.
  - Format: `.claude/skills/video/references/asset-request.md`.
- **Yerler:** `library/music/<site>/`, `library/sfx/raw/<site>/` (`source.json` lisansı taşır → `vedit sfx index`), `library/motion/<site>/`. Müzik ve motion `manifest.json` ile kaydedilir; lisans alanı boş dosya kullanılmaz.
- **Atıf:** manifest `attribution` alanı → `vedit export` `renders/credits.txt` yazar.
- **Teslim:** `vedit export` çıktıları `Projeler/<stüdyo>/<proje>/` klasörüne konur (aynı diskte hardlink, ek yer kaplamaz). `final.mp4` → `<proje-id>.mp4`.
- **Yeni adım:** iki hatta da `design` ile `sfx` arasında `assets` (kullanıcı adımı, `vedit mark assets`).

> [!question] Çıkarım
> NCS, Bensound ücretsiz lisansı, Uppbeat ücretsiz planı ve Audio Library içerik üreticisi kullanımı içindir; ücretli reklamda genelde geçerli değildir. Bu yüzden [[ugc-studyosu]] satış videolarında yalnızca Pixabay/Mixkit önerilir. Lisans metni her parçanın sayfasında kontrol edilmeli (kaynakta doğrulanmadı).

## Sonuçlar
- Müzik kütüphanesi kullanım arttıkça büyür; aynı parça birden çok videoda kullanılabilir.
- Stil tarifi için ortak sözlük: `.claude/skills/style-pack/references/stil-arketipleri.md`.

## İlgili kod
`src/vedit/export.py` (credits, deliver), `src/vedit/paths.py` (DELIVERY, MOTION_DIR), `src/vedit/project.py` (assets adımı), `library/*/manifest.json`
