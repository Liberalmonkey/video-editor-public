---
name: motion-design
description: Profesyonel motion design kuralları — render sözleşmesi, "AI şablonu" yasakları, işe göre easing, geçiş aileleri, ritim, tipografi, renk, güvenli alan, hero sahne yazımı. timeline.json overlay'leri, blok props'ları, custom/hero HyperFrames sahneleri yazarken ya da bir animasyonu eleştirirken kullan.
---

# Motion design kuralları

Kaynak: `wiki/concepts/motion-design-ilkeleri.md`. Uygulama: `blocks/*.block.html` + `vedit build`.

## 1. Render sözleşmesi (pazarlıksız)
- Motor HyperFrames'tir (ADR 0050); kurguya giren grafik `library/motion/hf/SOZLESME.md`'ye uyar: saydam kök, `tema.css` token'ı, değişkenler.
- Her kare yalnız t'nin fonksiyonu: birikmiş durum, `Date.now`, seed'siz `Math.random`, ağ isteği, CSS `transition` yok. Rastgelelik: `HF.mulberry32(seed)`.
- Tüm hareket tek paused GSAP timeline'da; Canvas `onUpdate: () => draw(tl.time())`.
- Başlangıç `fromTo` ile; CSS'te verilen `transform`'u GSAP ile tween etme (lint hatası).

## 2. Yasaklar ("AI şablonu")
- Ortalanmış başlık + mor/mavi gradyan, neon, lens flare, anlamsız parçacık, RGB kayması, sürekli kamera sallantısı.
- Her şeye aynı elastik easing; her öğenin aynı anda zıplaması.
- 2'den fazla font ailesi, 1'den fazla vurgu rengi.
- Her metin ≥ **1.2 sn** okunur (uzun cümlede ≥ kelime × 0.3 sn).
- Anlamsız hareket.

## 3. Easing (S.ease token'ları)
| İş | Token | Varsayılan |
|---|---|---|
| UI/kart/buton girişi | `ui` | power3.out |
| Metin maskeli giriş | `text` | power4.out |
| Kamera (zoom, pan) | `camera` | power2.inOut |
| Çıkış | `exit` | power2.in |
| Logo / büyük an | `logo` | expo.out |
| Pop (yalnız etkileşim) | `overshoot` | back.out(1.5) |

Giriş 0.35–0.6 sn, çıkış 0.2–0.3 sn (hep girişten kısa), stagger 0.05–0.09 sn.

## 4. Anlam haritası
Sağ/yukarı = ilerleme · sol/aşağı = geri · büyüme = önem · küçülme = arka plan · dönme = durum değişimi · renk vurgusu = önemli. Videoda sabit; director `scenes.json → motion_language`'e yazar.

## 5. Ritim
- Büyük andan (reveal, stat, CTA) önce 300–600 ms durgunluk.
- Kısa formatta her 1–2 sn, uzunda her 3–8 sn anlamlı değişim; ölü zaman ≤ 0.5 sn.
- 2–3 geçiş ailesi (`cut`, `match`, `push`, `mask`, `dissolve`); her sahne birini kullanır.
- Tek konteyner: bir nesne kesmeden şekil değiştirip hikâyeyi taşıyabilir (hero).
- Müzik varsa küçük hareket vuruşta, geçiş downbeat'te.
- **Kesimin iki yanı (vektör yasası, ADR 0040):** çıkış ve giriş aynı eksen, aynı yön (derinlikte ölçeğin işareti), eşit hız, kesim iki yanda hareketin ortasında. Geri çekilen çıkışa küçükten büyüyen giriş yanlıştır. Ayrıntı, yedi kesim tekniği ve teknik reçeteler (yönlü bulanıklık, ölçeklenen yazıda taban çizgisi dayanağı, cam yazı, mürekkep kutusuyla boyutlama): `references/kesim-surekliligi.md`.

## 6. Tipografi
- Başlık: display, 800–900, harf aralığı −0.02/−0.03em, satır 1.0–1.1. Gövde: 500–600, satır 1.25–1.35.
- 1080p: gövde ≥ 48 px, başlık 90–160 px; dikeyde metin yüksekliği ≥ genişliğin %7'si.
- Ekranda tek fikir; uzun metin `bullet-list`.
- Tabular rakam (`t-num`); TR biçim: 1.250 ₺, %40.
- TR glif (İ ı Ş ğ) fontta olmalı (`vedit qa`); `uppercase` yalnız `lang="tr"` ile. `<br>` yok, `max-width: Nch`.

## 7. Renk ve kompozisyon
- Palet: bg, surface, fg, muted, tek accent (≤ %10 alan). Kontrast ≥ 4.5:1.
- Üçler kuralı ya da güçlü merkez; negatif alan tasarım öğesidir.
- Güvenli alan `--safe-*`: dikeyde üst %12, alt %22, sağ %12. Altyazı z=50; alt overlay çakışırsa `position: top|center`.

## 8. Gerçek çekimle
- Jump cut: punch-in %100 ↔ %112–118, `dur: 0`. Duygusal anda yavaş push-in %100 → %105 (3–6 sn).
- Ekran kaydı zoom 0.5–0.7 sn `camera`; 2 sn'den uzun bekleme yok.
- Overlay yüzü kapatmaz; konuşmacı ortadaysa üst ya da yan.

## 9. Blok mu, hero mu?
- Önce `vedit blocks` (ucuz, tutarlı, test edilmiş).
- Hero yalnız: 3D, harita, özel diyagram/illüstrasyon, karakter, tek-konteyner morph, veri simülasyonu. Yazım: `video/references/timeline.md` + `hyperframes` skill'i.
- Tekrar kullanılacaksa `blocks/<ad>.block.html`; projeye özelse `edit/blocks/`.

## 10. Kontrol
- [ ] Metinler ≥ 1.2 sn, güvenli alanda, TR glif tam
- [ ] Easing işe göre, elastik yok, çıkış kısa
- [ ] Geçişler tutarlı, ölü zaman yok, büyük andan önce nefes
- [ ] ≤ 2 font, 1 accent, kontrast yeterli
- [ ] `vedit build` lint 0; kontak sayfasında taşma/çakışma yok

## 11. Kelimeye kilit (Motion Graphics, ADR 0014)
- Öğe, onu adlandıran kelimede girer: kelimeden önce değil, en geç 2 sn sonra.
- Sahne boş açılmaz; ilk karede gerçek bir şey ekrandadır.
- Konuşma sürerken ekran 5 sn'den uzun durağan kalmaz.
- Uydurma sayı, logo, görüntü yok; eksik varlık kesik çizgili "bekliyor" kartıdır.
- Pano gerekiyorsa önce `library/boards/katalog.md`; render `vedit pano`. Stil kararları `sanat-yonetimi`, düzeltme geçmişi `library/checks.md`.

## 12. Native motion zanaatı (ADR 0045)
Native bileşeni yazarken ya da kurguya koyarken. Bileşenler iki biçimde durur: Remotion kaynağı `studio/remotion/motion/` (sözleşme `SOZLESME.md`) ve HyperFrames sahnesi `library/motion/hf/<aile>-<ad>/sahne.html` (ADR 0051, `library/motion/hf/SOZLESME.md` "Native bileşen taşıma"); render ikincisini kullanır, ikisi `scripts/hf_native_karsilastir.py` ile birebir tutulur. Kurallar ikisinde de aynı; ölçülebilenler kapıdır (`tests/test_motion_kurallari.py`, `kurgu_kalite`).
- **Amaç:** her grafik söylenen bir kelimeye çapalıdır (`capa`), giriş kelimeden 2-4 kare önce.
- **Zaman:** giriş 0,3-0,5 sn; iki kez okunacak kadar tut; çıkış girişten kısa. İkon 1-1,6 sn, alt bant 2,5-4 sn, kart en çok 3 sn.
- **Eğri:** doğrusal yok. Stilin adlı eğrileri enter, exit, emphasis, settle; piksel stilde basamak.
  - Anticipation `a.ters` ile ana hareketin tersine yapılır (%8-15 genlik, 2-4 kare).
  - Taşma %4-8, tek sönüm (`a.takip`).
  - Follow-through: ikincil öğe 2-4 kare gecikir.
  - Stagger 2-4 kare; aynı anda rakip hareket olmaz.
- **Hiyerarşi:** ekranda aynı anda tek hero. Her bileşende tek "patron" öğe; ikincil öğe 0,55-0,65 ölçek ve +3-4 kare.
- **Yerleşim:** konum yazma; yerleşim güvenli alanı, 9:16 platform arayüzünü, altyazı bandını ve yüz kutusunu (göz, ağız) kendisi kaçırır.
- **Boyut:** ikon en az 180 px (1080 kısa kenar), çizgi kutunun %7'si, aile içinde aynı kalınlık; yazı en az 28 px.
- **Geçiş:** hep sonraki çekimi gösterir: `sil`, `kay`, `saat`, `iris`, `kirbac`, `isik`, `piksel`.
  - Reels'te 6-12 kare; orta nokta kesimde, geçiş sesi kendiliğinden.
  - Düz tam kare renk en çok 2 kare; V2'ye `gecis-*` bindirmesi konmaz.
- **Çeşitlilik:** aynı grafik art arda gelmez. Yoğunluk `--motion` seviyesine göre.
- **Kaynaklar (yalnız ilke, kopya yok):** School of Motion (graph editor, anticipation/follow-through, transitions), Ben Marriott (smooth transitions, overshoot-settle), Jake In Motion (easing eğrileri). Notlar: `work/agy/2026-11-19-motion/A/A3-zanaat.md`.
