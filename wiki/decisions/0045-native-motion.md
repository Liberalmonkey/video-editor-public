---
type: decision
title: "Native motion: tema token'ına bağlı Remotion bileşenleri, orta noktalı geçişler, alfa düzeltmesi"
status: accepted
tags: [adr, motion, remotion, gecis, alfa, yerlesim]
created: 2026-11-20
updated: 2026-11-22
sources: []
---

# ADR 0045: Native motion

> [!note] Güncellendi 2026-11-22
> Native Remotion bileşenleri ikinci plana alındı ([[0050-hyperframes-birincil-motor]]): mevcutlar kullanılır, yeni grafik önce HyperFrames kompozisyonudur.

## Bağlam
`instagram/1` editinde altı kusur vardı:
- Her bindirmenin arkasında siyah kutu.
- `gecis-*` geçişleri kareyi düz renkle örtüyor, sonraki çekim görünmüyor.
- Kartlar siyah zeminde duruyor.
- İkonlar alında ve yüzde, küçük ve ince.
- Renk bir video içinde kayıyor.
- Her grafik aynı scale-pop hareketiyle giriyor.

Grafikler HTML'den webm'e render ediliyordu (ADR 0031, 0036). Webm dosyalarının alfası sağlamdı (VP9 `alpha_mode=1`, libvpx ile ölçüldü), taslak render de temizdi.

Siyah kutunun nedeni önizlemedeydi. `studio/app.py medya_eslemesi` motion kliplerini (`public:motion/...`) H.264 `yuv420p` proxy'ye çeviriyordu; yorum bunu yasaklıyor ama koşul yalnız `library:` kökünü dışlıyordu.

## Seçenekler
- **HTML şablonlarını düzeltmek:** her yazı değişikliği webm üretimi gerektiriyor. Yerleşim kare başına yüzü ve altyazıyı bilmiyor.
- **Native Remotion bileşenleri (seçildi):**
  - kareye bağlı, tema token'ından renk ve eğri alır;
  - yerleşimi o karenin yüz ve altyazı bölgesine göre seçilir;
  - parametre değişince yeniden render gerekmez.

## Karar
- **Alfa:**
  - Motion kaynağı ve alfalı her webm/mov proxy'ye girmez; alfa `ff.probe` içinde `video.alfa` alanıyla tespit edilir.
  - Kapı: `tests/test_alfa_seffaf.py` (önizleme eşlemesi, Chromium `<video>` ve Remotion render piksel örneği).
- **Bileşen:** `studio/remotion/motion/<aile>/<ad>/<Ad>.tsx` + `meta.json`.
  - Sözleşme `studio/remotion/motion/SOZLESME.md`; çekirdek `cekirdek/` (Claude'a aittir).
  - Kurguda `tur: "motion"` + `bilesen: {ad, param}`. Zod şeması `npm run sema` ile `library/motion/native/sema.json`'a yazılır; `kurgu-denetle` parametreyi bununla doğrular.
- **Hareket:**
  - Yalnız `useAkis`: adlı eğriler enter/exit/emphasis/settle, `ters` (anticipation, 0→1→0), `belir`, `takip` (follow-through, tek sönüm), `sirali` (2-4 kare stagger).
  - Eğriler stilden gelir: `token.hareket.egri`, piksel stilde `adim`.
  - CSS animasyonu, `Easing.linear` ve elle `a.f < N` formülü yasaktır (`tests/test_motion_kurallari.py`).
- **Yerleşim** (`cekirdek/yerlesim.ts`):
  - Güvenli alan, 9:16 platform arayüzü, altyazı bandı ve yüz kutuları cezalandırılır; tercih sırası 0.05/adım.
  - Yüz kutuları YuNet ile ölçülür (`yuz_bolge.py`, önbellekli) ve render props'una `bolgeler.yuzler` olarak girer.
- **Ölçü:**
  - İkon en az 180 px (1080 kısa kenar).
  - Çizgi kalınlığı kutunun %7'si ya da stilin `ikon_cizgi` değeri; bütün ikonlar aynı kalınlıkta.
  - Yazı alt sınırı 28 px (kapı).
- **Geçiş** (`studio/remotion/gecisler.tsx`):
  - `sil`, `kay`, `saat` ve `iris` `@remotion/transitions` sunumlarıdır; `kirbac`, `isik` ve `piksel` özeldir.
  - Orta nokta kesimin üstündedir: giren klip yarım süre önden başlar, çıkan klip yarım süre uzar.
  - Geçiş sesi kendiliğinden kesime gelir (`gecis`, `gecis_guclu`).
  - `flip` alınmadı: sürenin yarısında gelen çekim görünmüyor.
  - Kapı: `tests/test_gecis_olcum.py` (gelen çekim karelerin en az %80'inde görünür, düz tam kare en çok 2 kare).
- **Eski bindirme:** `ESKI_GECIS` uyarısı verir; `vedit kurgu-gecis <proje> --uygula` bindirmeyi V1 kesimine taşır.
- **Zanaat kapıları** (`kurgu_kalite`): `MOTION_SURE`, `MOTION_ART_ARDA`, `HERO_CAKISMA`.
- **Galeri:** `vedit motion kontak [adlar] --tema --kare` her evreyi (giriş, tutma, çıkış) dama zeminde (alfa) ve gerçek karede (okunurluk) render eder.

## Sonuçlar
- 40'tan fazla native bileşen: ikon, çizim, kart ve alt bant, CTA, veri; çerçeve, parçacık ve zemin yolda. Her aile `motion-gozden-gecirici` incelemesinden geçer.
- Eski webm kayıtları render edilmeye devam eder. Native karşılığı onaylananlar `library/motion/arsiv/` altına taşınır (kullanıcı kararı).
- Remotion lisansı: bireyler ve en çok 3 kişilik şirketler için ücretsizdir; 4 ve üstünde Company License gerekir (`THIRD_PARTY_NOTICES.md`).

## İlgili kod
`studio/remotion/motion/**`, `studio/remotion/gecisler.tsx`, `studio/remotion/Kurgu.tsx`, `src/vedit/native_motion.py`, `src/vedit/yuz_bolge.py`, `src/vedit/gecis_donustur.py`, `src/vedit/studio/app.py`, `src/vedit/kurgu_kalite.py`
