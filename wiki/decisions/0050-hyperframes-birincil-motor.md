---
type: decision
title: "HyperFrames birincil motor, Remotion ikinci plan; Stüdyo hızlı açılış"
status: accepted
tags: [adr, renderer, hyperframes, remotion, motion, studio, performans]
created: 2026-11-22
updated: 2026-11-22
sources: ["[[2026-10-20-hyperframes]]"]
supersedes:
superseded_by:
---

# ADR 0050: HyperFrames birincil motor

## Bağlam
Kullanıcı 2026-11-21'de üç şey istedi:
- HyperFrames güncellensin ve sistemin ana motoru olsun. Video editleme, animasyon ve motion grafik önce HyperFrames'le yapılsın; Remotion yalnız HyperFrames'in yetmediği yerde kullanılsın.
- Dağıtım izni olmayan üçüncü taraf sanat yönetimi skill'i ve bütün izleri projeden çıksın; yerine bozulmayı önleyecek kendi karşılığımız konsun.
- Stüdyo çift tıklamadan sonra yaklaşık 10 sn'de açılıyordu; bu süre kısalsın.

Durum:
- HyperFrames 0.9.56 kuruluydu, güncel sürüm 0.9.77.
- Upstream skill seti değişmişti: eski parçalı set yerine tek `hyperframes` yönlendiricisi geldi.
- Stüdyo'nun timeline önizlemesi ve son birleştirmesi `studio/remotion/Kurgu.tsx` ile çalışıyor.
- Yeni grafikler native Remotion bileşeni olarak yazılıyordu (ADR 0045).

## Seçenekler
- **Tam geçiş:** Kurgu render motoru ve Stüdyo önizlemesi HyperFrames'e taşınır. Haftalar sürer, Stüdyo yeniden yazılır, bozulma riski yüksektir.
- **Karma (seçildi):** üretilen her görsel (motion grafik, metin grafiği, alt bant, tam ekran sahne, animasyon videosu) HyperFrames kompozisyonu olur ve saydam webm olarak kurguya girer. Timeline ve gerçek çekim birleştirmesi Remotion'da kalır. Kullanıcı bu seçeneği seçti.

## Karar
- **Sürüm:** `hyperframes` 0.9.77 (`package.json`, `src/vedit/hf.py`). Kırıcı değişiklik yok (araştırma `work/agy/2026-11-21-hf-hiz/hf-guncelleme.md`).
  - `HYPERFRAMES_RENDER_LOCK=off`: 0.9.7x hesap başına tek render kilidi alır; `render.py` bölümleri paralel render eder.
- **Skill'ler:** `hyperframes`, `hyperframes-cli`, `hyperframes-registry` (yalnız GitHub'daki ücretsiz bloklar), `remotion-to-hyperframes`.
  - Kurulmayanlar: `media-use`, `reverse-any-video`, `style-sampling` (HeyGen ya da Pro, ADR 0007/0008) ve `slideshow`. Eski parçalı set silindi.
  - Telemetri kapalı: `.claude/settings.json` env `HYPERFRAMES_NO_TELEMETRY`, `DO_NOT_TRACK`, `HYPERFRAMES_SKIP_SKILLS`. Upstream `hyperframes` skill'inin baştaki `npx hyperframes events` çağrısı bu değişkenlerle hiçbir şey göndermez; kurulmamış skill'lere (`media-use`, `slideshow`...) yönlendirmeleri atlanır.
- **Grafik yolu:** klipte `tur: "motion"`, `hf: {ad, param, tema}`.
  - Kompozisyon `work/edit/hf/<ad>/` (proje) ya da `library/motion/hf/<ad>/` (kütüphane). Sözleşme `library/motion/hf/SOZLESME.md`.
  - `src/vedit/hf_grafik.py` kopyada render eder; kopyaya seçili stilin token'ı `tema.css`, yazı tipleri `fonts/` ve gerekirse GSAP konur.
  - Çıktı `work/public/motion/hf-<ad>-<özet>.webm`; kompozisyon, tema ya da parametre değişince yeniden üretilir.
  - `kurgu.motion_bagla` bağlar, `kurgu.denetle` adı ve parametreleri denetler. CLI `vedit hf liste|kur`.
- **Alfa:** HyperFrames webm'i `ALPHA_MODE=1` etiketiyle yazar, `ff._alfa_mi` artık büyük ve küçük harfi tanır. `hf.render_saydam` alfasız çıktıyı reddeder; siyah kutu kurguya girmez.
- **İstemler:** ai-edit, ekip E2 ve K2, `uretim-hatti`, `sahne-motoru`, `motion-design` ve CLAUDE.md önce HyperFrames der. E2 dosya yazmaz; yeni kompozisyonu yamanın `hf: {ad: html}` alanında döndürür, vedit `work/edit/hf/<ad>/` altına yazar (`ekip_v2.hf_yaz`). Tek ajanlı ai-edit bu yolu doğrudan yazabilir.
- **Remotion ne zaman:** gerçek fizik (ADR 0039), yüz takipli native yerleşim (ADR 0045), V1 `gecis_giris` geçişleri, timeline birleştirmesi. Mevcut native bileşenler çalışır; yeni bileşen yalnız HyperFrames yetmezse yazılır.
- **Sanat yönetimi:** üçüncü taraf sanat yönetimi skill'i silindi. Yerine kendi `sanat-yonetimi` skill'imiz geldi: brief, yönler, stil kartı, hareket çizelgesi, klişe testi, Türkçe glif denetimi; `references/klise-listesi.md`. Wiki, log ve `raw/` dahil izler kullanıcı kararıyla silindi; git geçmişi yeniden yazılmadı.
- **Stüdyo açılışı:**
  - `src/vedit/studio/baslat.py` tek süreçte hazırlık denetimini yapar ve soketi en başta `bind` + `listen` eder.
  - Pencereyi hemen açar. İstek, modüller yüklenene kadar backlog'da bekler.
  - Eski port yoklaması (`connect_ex`) Windows'ta kapalı portta yaklaşık 2 sn sürüyordu; pencere bekleme döngüsü de aynı gecikmeyi ekliyordu.
  - `studio.bat` tek Python süreci çalıştırır; 11 kurulum, 12 derleme kodudur.
  - cv2, numpy, soundfile ve requests `vedit.tembel.Tembel` ile ilk kullanımda yüklenir; send2trash `studio/ortak.py` içindeki sarmalayıcıda ilk silmede.
  - Arayüzde altı yan panel tembel yüklenir; kütüphaneler ayrı parçadır (`remotion`, `dockview`, `react`, `uc-boyut`, `kutuphane`). Hash'li `assets/` dosyaları `immutable` önbellek başlığıyla gelir.
  - `ff.probe_ob` mtime ve boyut anahtarlı ffprobe önbelleğidir (Teslim özeti, şerit).
  - AI panelinin motor taraması açılıştan 3 sn sonra arka planda ısınır.

## Sonuçlar
- Ölçüm (2026-11-21, sıcak):
  - `vedit.studio.app` importu numpy ve cv2 olmadan yaklaşık 1,0 sn (fastapi yaklaşık 0,45 sn).
  - Sunucu ilk isteğe yaklaşık 0,9 sn'de yanıt veriyor; eskiden yalnız port yoklaması 2 sn sürüyordu.
  - Ana JS parçası 3,0 MB'tan 470 KB'a indi; kütüphaneler ayrı parçalarda önbelleğe giriyor.
  - Soğuk açılış (yeniden başlatma sonrası, Defender taraması) ölçülmedi.
- HyperFrames bir saydam grafiği yaklaşık 25-30 sn'de render ediyor (Chrome açılışı dahil). Önbellek aynı grafiği yeniden üretmez.
- Kütüphanede şimdilik tek HyperFrames şablonu var (`alt-bant`). Native set (55 bileşen) HyperFrames'e taşınana kadar ajanlar çoğu anda native kataloğa düşer. Taşıma `remotion-to-hyperframes` ile aşamalı yapılır.
- Montserrat TTF (745 KB) arayüzde tam kalır: alt küme ş, ğ, İ harflerini kaybeder (ADR 0014).
