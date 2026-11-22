---
type: query
title: "Sistem 15 yıllık editör seviyesinde mi? Denetim"
tags: [denetim, kurgu, ses, yol-haritasi]
created: 2026-11-02
updated: 2026-11-02
sources: ["[[2026-11-02-kalem]]", "[[2026-11-02-loop-slayt]]"]
---

# Sistem 15 yıllık editör seviyesinde mi?

## Soru
Bu proje kıdemli bir video editörü gibi çalışıyor mu? En iyi yönleri, en kötü yönleri ve geliştirilecek yerler neler?

## Cevap
Hayır, henüz değil. Teknik altyapı ve kural birikimi güçlü, ama sistem bir editörün kulak ve göz tecrübesini kanıtlayacak kadar video üretmedi. Bugünkü durum: titiz bir asistan editör. Fark en çok ses ve ritim kararlarında kapanacak.

### En iyi yönler
- **Hikâye katmanı:** Story Circle, ayna çiftleri, soru işareti testi ve çalışan `hookscore.py`. Birçok editörün yazıda sahip olmadığı bir disiplin.
- **Teknik ses zinciri:** konuşma temizliği, ducking, iki geçişli loudnorm, örnek doğruluğunda yerleştirme.
- **Otomatik denetim:** siyah kare, donuk kare, sessizlik, Türkçe glif, loudness. Token harcamadan çalışıyor.
- **Tekrar üretilebilirlik:** şemalı timeline, sabit sürümler, kilitli kit.
- **Lisans disiplini:** 521 kayıtlı SFX ve kayıtsız parçayı kullanmama kuralı.

### En kötü yönler
1. **Varsayılan hat ile ses kütüphanesi kopuktu.** OpenMontage kurgusu SFX almıyordu; son Reels notunda "SFX yok" yazıyor. **Düzeltildi:** `vedit olaysesi`.
2. **Zoom sesi yoktu.** `auto_cues` yalnız overlay, B-roll ve bölüm olaylarına bakıyor. **Yeni hatta düzeltildi;** eski `/video` hattında durum aynı.
3. **Kanıt az.** `Projeler/youtube` boş, YouTube stil paketi yok, `references/voice.md` yok. 10–15 dk video hiç teslim edilmedi. Hedef format denenmemiş.
4. **Malzeme zayıf.** 2 müzik, 0 motion, 5 whoosh. Swoosh'un çoğu kısa arayüz sesi.
5. **Editörlük bilgisi dağınıktı.** Tek bir karar öğretisi yoktu. **Eklendi:** `usta-editor`.
6. **Denetim kurguyu ölçmüyor.** Kesim sıklığı, ritim eğrisi, ses-hareket uyumu rapor edilmiyor. Ses raporu bir kısmını kapatır.
7. **Geri bildirim döngüsü yok.** `yt-retention` var ama gerçek tutma verisi kurallara dönmüyor.
8. **Veri hatası:** bazı riser kayıtlarında `peak_offset_s` süreden büyük (`riser-synth-riser-01`: 1,26 sn tepe, 1,04 sn süre). Eski `resolve` hattında yerleşim kayar. Yeni motor tepeyi dosyadan ölçtüğü için etkilenmez.
9. **Git riski:** tek commit ve 743 satırlık işlenmemiş durum. Bir hata birçok işi geri döndürülemez yapar.

### Öneriler (öncelik sırasıyla)
1. Değişiklikleri parça parça commit et.
2. `library/sfx/INDIRME-LISTESI.md`'deki 11 zoom ve geçiş sesini ve 5 müziği indir, kulakla seçip rollere ata.
3. 2–3 dakikalık bir pilot video yap. Yalnız ses kararlarına not ver, kuralları düzelt.
4. YouTube stil paketini ve `voice.md`'yi pilot sırasında çıkar.
5. Referans videoları ölç: kesim sıklığı, zoom sayısı, efekt yoğunluğu. Kuralları sayıyla kalibre et.
6. `vedit` denetimine ritim raporu ekle: dakika başına kesim, en uzun değişimsiz an.
7. Yayın sonrası `yt-retention` çıktısını kural değişikliğine bağla.
8. Eski SFX manifest tepe değerlerini yeniden hesapla (`vedit sfx index --rescan` etkisini önce sına).
9. İki hat uzun süre kalmamalı: `/video` hattının kalan değerli parçalarını OpenMontage tarafına taşı ya da kapat.

## Kullanılan sayfalar
[[0010-openmontage-edit-motoru]] · [[0012-kutuphane-kit]] · [[0013-uretim-akisi-ve-olay-sesi]]

## Takip soruları
- Whoosh seviyeleri kulakta doğru mu? Pilot videoda ölçülecek.
- Kalem motorlarından hangisi gerçekten fark yaratıyor?
