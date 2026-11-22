# Kaizen günlüğü

Her teslimde `vedit kaizen` bir satır ekler: tarih, proje, araç süresi, render sayısı, en yavaş üç adım. Satırların altına uygulanan iyileştirme elle yazılır. Hedef: video başına daha az dakika ve render.

- 2026-11-04 · 08-claude-code-5-skill · araç 11.9 dk · taslak 1 · final 1 · en yavaş: final 7.5 dk · taslak 2.5 dk · hazirla 1.3 dk
  - Ders: Tek başına transkribe edilen kısa kayıtta Whisper baştaki "iki" sözünü yuttu; birleşik seste duyuldu. Sıra sayısı gibi kritik sözleri birleşik sesle doğrula.
  - Sonraki iyileştirme: en yavaş adım `final` (7,5 dk; PNG kare + CRF 16). Kare formatı JPEG q95 ile görsel kayıpsız kısalıyor mu ölç.
  - Ölçüldü (2026-11-04): JPEG q95 videolu sahnede kayıplı (SSIM 0,979), alınmadı. Uygulanan: ara render PNG + veryfast, SplitReel 4 sn'de 24,7'den 19,1 sn'ye. Sıradaki gerçek Reels finali süreyi doğrular.
- 2026-11-05 · instagram-reels-video · araç 5.1 dk · taslak 1 · final 2 · en yavaş: final 3.3 dk · hazirla 1.0 dk · taslak 0.7 dk
  - Ders: Kontak sayfası 1 karelik altyazı çakışmasını taslakta değil finalde yakaladı; motor olay süresini başlangıçtan bağımsız yuvarlıyordu. Bitiş kareye göre hesaplanacak biçimde düzeltildi, ikinci final bu yüzden alındı.
  - Sonraki iyileştirme: `list` kutusu son boyutta boş açılıyor; maddeler göründükçe büyüsün.
  - Uygulanan (ADR 0020): görüntü değişmediyse `vedit final` motoru atlar, tekrar final 98-137 sn'den 48-54 sn'ye indi; kontak sayfası 4,9 sn'den 2,4 sn'ye indi. Sıradaki en yavaş adım motor (56-76 sn).
- 2026-11-05 · instagram-reels-video · araç 10.2 dk · taslak 4 · final 3 · en yavaş: final 7.0 dk · taslak 2.1 dk · hazirla 1.0 dk
  - Ders: SplitReel `chips` sahnesi `banner` olmadan render'ı düşürüyor, `reel_kit` bunu ve `at("3.")` eşleşmesini (nokta atılır, ilk `3`e gider) yakalamıyor. Kontak sayfası sayaçta "3" denirken "2" görünmesini de yakaladı: 1,2 sn'lik sahnede `stat` kullanma.
  - Sonraki iyileştirme: `reel_kit.yaz` sahne türüne göre zorunlu alanı render'dan önce denetlesin; 37 sn'lik boş render'ı önler.
- 2026-11-05 · instagram-reels-video · araç 11.6 dk · taslak 4 · final 4 · en yavaş: final 8.4 dk · taslak 2.1 dk · hazirla 1.0 dk
- 2026-11-05 · video-studyo (geliştirme, teslim değil) · yeni proje yolculuğu: hazirla 15 sn, 15 sn'lik final 93 sn; en yavaş adım motor
  - Ders: eski projelerle yapılan testler boş proje hatasını göstermedi; arayüz değişikliği yeni proje yolculuğuyla da sınanır.
  - Sonraki iyileştirme: uzun projede proxy üretimi 15 dk için 136 sn; hazırlanırken timeline'da ilerleme gösterilsin.
- 2026-11-07 · studio-deneme · araç 4.6 dk · taslak 1 · final 1 · en yavaş: final 4.3 dk · taslak 0.3 dk · kurgu-al 0.0 dk
- 2026-11-08 · kilavuz-demo · araç 3.9 dk · taslak 0 · final 1 · en yavaş: final 3.8 dk · kes 0.1 dk · kurgu-al 0.0 dk
- 2026-11-13 · avatar-reel · araç 35.9 dk · taslak 1 · final 2 · en yavaş: final 13.5 dk · ai-edit 9.4 dk · kapak 6.3 dk
- 2026-11-19 · 1 · araç 178.0 dk · taslak 0 · final 0 · en yavaş: ai-edit 178.0 dk · kurgu-denetle 0.0 dk
