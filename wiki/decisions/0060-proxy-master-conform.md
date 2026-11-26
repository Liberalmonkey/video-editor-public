---
type: decision
title: "Proxy ve master conform: ağır kaynakta proxy ile kurgu, teslimde orijinale dönüş, Master ön ayarı ve sadakat ölçümü"
status: accepted
tags: [adr, render, teslim, proxy, kalite, renk, studio]
created: 2026-11-25
updated: 2026-11-25
sources: ["[[0016-earshot-render-standardi-ajan-duzeni]]", "[[0019-arayuz-ve-efekt-motoru-birlesimi]]", "[[0035-teslim-ayarlari]]", "[[0040-ikinci-repo-dalgasi]]", "[[0051-uctan-uca-hyperframes]]"]
---

# ADR 0060: Proxy ve master conform

## Bağlam
Kullanıcı en yüksek teslim kalitesini ve 4K, HEVC, 10-bit, HDR ya da VFR kaynakta akıcı kurgu istedi (2026-11-25). Denetimde şu açıklar çıktı:
- Stüdyo'da 540p önizleme proxy'si vardı, ama taslak ve QC render'ı 4K orijinali yarım ölçekte çiziyordu. HyperFrames her klibin karesini çıkardığı için en pahalı adım buydu.
- Final zaten orijinali bağlıyordu, ama bunu doğrulayan bir kapı yoktu.
- Teslime kadar 2 kayıplı nesil vardı, HDR kaynakta 3: HDR→SDR CRF 14, ara render CRF 14 4:2:0, teslim CRF 16.
- Teslim renk dönüşümü swscale ile, dither'sız yapılıyordu. 10-bit seçeneği ve nesnel sadakat ölçümü yoktu.

## Karar
- **Proxy modülü `vekil.py`.** Ölçüt (`vekil.neden`): kısa kenar 1080'den büyük, HEVC/ProRes/DNxHD/AV1/VP9, 10/12-bit, HDR, VFR ya da 50 Mbps üstü. Alfalı kaynak asla proxy'lenmez. İki katman var:
  - `onizleme`: 540p, Stüdyo Player'ı için. Adı eski Stüdyo proxy'siyle aynı.
  - `taslak`: 1080p kısa kenar, CRF 18, taslak ve QC render'ı için.

  İkisinde de anahtar kare aralığı 12 kare ve B-kare yok. HDR ton eşlenir, VFR sabit hıza çevrilir. Proxy süresi kaynaktan 0,1 sn'den fazla saparsa reddedilir. Kayıt `work/proxy/vekil.json`'a yazılır. `vedit hazirla` proxy'yi transkriptle paralel üretir; `vedit vekil <proje> [--uret]` durumu gösterir ya da üretir.
- **Bağlama modu.** `kurgu.hazirla(p, mod=)` ve `_public_bagla` üç mod alır:
  - `taslak`: hazır taslak proxy'sini bağlar.
  - `final`: orijinali bağlar; HDR kaynakta bugünkü CRF 14 SDR kopyasını.
  - `master`: orijinali bağlar; HDR kaynakta CRF 6 medium SDR kopyasını.

  Bağlantı adı `_k/<id><uzantı>` moddan bağımsızdır, derleyici değişmez. `ham_imzasi` `work/public`'i dosya kimliğiyle özetler; taslak render'ı bu yüzden final önbelleği sayılmaz.
- **Conform kapısı.** `final` ve `master` modunda her bağlantının beklenen master dosyası olduğu (`samefile`) doğrulanır. Proxy bağlıysa render başlamaz. Sonuç `work/edit/conform.json`'a yazılır ve teslimde "Master conform: n/n klip orijinal kaynaktan" diye basılır.
- **Master ön ayarı** (`teslim.KALITE["master"]`):
  - Ara render kayıpsız 4:4:4: HyperFrames `--crf 0 --chroma-subsampling 444`. Remotion H.264'te CRF 0'ı reddettiği için orada CRF 1 4:4:4 kullanılır (görsel olarak kayıpsız).
  - Teslim H.264 CRF 10 ya da H.265 CRF 14; H.265'te Main10 `yuv420p10le`.
  - Kaynağa eşle varsayılan açık. Çözünürlük en büyük kaynağın kısa kenarını aşmaz; kaynak 50+ fps ise 60 fps seçilir.
  - Varsayılan teslim Yayın kalır (kullanıcı kararı); Master yalnız seçilince çalışır.
- **Renk zinciri.** Teslim swscale yerine zscale kullanır: aralık ve matris dönüşümü, kroma alt örneklemede spline36, `dither=error_diffusion`. HDR→SDR zincirinin son adımı da dither'lıdır. Kapı `pix_fmt`'i bit derinliğine göre denetler.
- **Sadakat ölçümü** (`teslim.sadakat`): teslim ara render'la saniyede bir karede karşılaştırılır (SSIM ve PSNR); `--vmaf` istenirse VMAF da ölçülür. SSIM 0,97'nin altındaysa uyarı verilir. Rapor `work/renders/kalite.json`'a yazılır.
- **Stüdyo Teslim paneli:**
  - Ön ayar seçimi; kayıpsız ara render ve 10-bit etiketleri.
  - Kaynağa eşle ve VMAF anahtarları.
  - Kaynak ve proxy listesi (proxy hazır, proxy hazırlanıyor, proxy gerekmez).
  - Son teslimin conform ve sadakat satırı.

## Ölçüm (sentetik 4K, 2026-11-25)
3 sn'lik 3840x2160 HEVC 10-bit kaynak, 1920x1080 sekans:
- Taslak proxy'den 19,5 sn'de çizildi.
- `final --kalite master --kodek h265`, kaynağa eşle ile 2160p çıktı verdi. Klip 1/1 orijinal kaynaktan geldi. Ara render yuv444p, çıktı yuv420p10le Main10, 42 Mbps.
- SSIM 0,9972, PSNR 46,9 dB, VMAF 97,54.

## Sonuçlar
- Sekans 1080p iken 2160p teslimde motor ölçeği >1 olur. HyperFrames derleyicisi bunu henüz yapamadığı için render Remotion'a düşer (ADR 0051); 3 sn 4K, 160 sn sürdü. Sonraki iş: tam sayı ölçeği HyperFrames `--resolution` (deviceScaleFactor) ile karşılamak.
- Kayıpsız ara render diski büyütür (1080p'de 10 dk için 10-20 GB). Dosya `work/renders/ham.mp4` olarak önbellekte kalır, `vedit duzen` temizlemez; boyutu teslim satırında yazılır.
- Yayın ön ayarına platform bitrate tavanı (`maxrate`) eklenmedi. CRF tavanı karmaşık sahnede kaliteyi düşürür; YouTube zaten yeniden kodlar.
