---
source_url: https://github.com/eraycoskunai/opus-animasyon-rehberi
accessed: 2026-10-20
author: Eray Coşkun (@AIMevzulari)
license: YOK (repoda LICENSE dosyası yok → tüm hakları saklı). Metin kopyalanmaz; fikirler kendi sözlerimizle uygulanır.
note: Bu dosya repo içeriğinin LLM tarafından çıkarılmış ÖZET notudur, birebir kopya değildir.
---

# opus-animasyon-rehberi — inceleme notu

Tek commit (main, 9215ed8e). "Opus 5.5 Animasyon Full Kurs" YouTube kursunun yazılı eşlikçisi. Kod yok; prompt + kural rehberi.

## Dosyalar
- README.md — temel fikir, MP4'e çıkış yolları, 5 adımlı akış, sorun giderme tablosu, kontrol listesi
- MOTION_RULES.md — proje klasörüne konan kural dosyası (render sözleşmesi, görünüm yasakları, ses, inceleme döngüsü)
- kutuphaneler.md — ~22 JS/Python kütüphanesi ve ne zaman kullanılacağı
- promptlar/01..11 — kural dosyası, yönetmen brifi (7 bölüm), kısa yol brifi, tarifler (Canvas2D hikâye, eğitici/Fourier, ürün filmi, müzikten klip, Shorts, Three.js 3D, 4D tesseract), cilalama döngüsü, stili skill'e çevirme

## Temel fikir
"Opus videoyu çizmez; videoyu çizen makineyi yazar." Ekran = saf fonksiyon draw(t). Video = bu fonksiyonun saniyede 30/60 örneklenmesi. Avantaj: sayıyı değiştir, yeniden üretme; tekrarlanabilir; metin/UI/grafik piksel hassas. Zayıf yan: gerçekçi yüz ve doğal kamera görüntüsü (video modellerinin işi).

## Render sözleşmesi
- Tüm görsel durum draw(t)'nin saf fonksiyonu; önceki kareye bağlı biriken durum yok
- Sadece seed'li rastgelelik (mulberry32), Math.random yasak
- window.__duration ve window.__setTime(t) dışa açılır; ?t=3.2 tek kare çizer
- Sabit çözünürlük/fps; tek dosya HTML
- MP4: Playwright ile her kareyi __setTime üzerinden PNG → FFmpeg H.264

## Görünüm yasakları (özet)
- Ortalanmış başlık + mor/mavi gradyan şablonu yok
- Anlamsız parçacık, lens flare, neon parlama, RGB kayması, sürekli kamera sallantısı yok
- Her şeyin zıpladığı elastik easing yok; easing işe göre seçilir
- En fazla 2 yazı tipi, tek vurgu rengi
- Her sahnenin tek işi var; metin en az ~1.2 sn ekranda
- Geçişler önceki sahnede görünen bir nesneden doğar
- Büyük anlardan önce 300–600 ms durgunluk

## Easing işe göre
UI'da sıkı yay; kamerada yumuşak gir-çık; taşma sadece etkileşimde ve küçük; logoda kontrollü yavaşlama; hepsine aynı yay verilmez.

## Ürün filmi varsayılanları
Sahne 1.5–3 sn, sert kesim yok (morph); kelimeler maskenin altından ~80 ms stagger ile kayarak girer; sahne başına %3–5 kamera push-in; tek yumuşak üst ışık, %3 kâğıt greni; 110 BPM, büyük değişimler vuruşta; her 1–2 sn anlamlı görsel değişim; "tek konteyner" ilkesi (bir nesne kesmeden morph ederek hikâyeyi taşır); referansın içeriği değil grameri alınır.

## Eğitici
Önce göster sonra adlandır; önce en yaygın yanlış anlamayı tespit et; en fazla 5 kavram; sahte değil gerçek hesap; ekranda aynı anda en fazla bir cümle; sonda her şeyi birleştir.

## Shorts
Sessiz anlaşılır olmalı; ilk kare kapak olabilmeli; üst %12 ve alt %20 güvenli alan dışı; metin yüksekliği ≥ ekran genişliğinin %7'si; tabular rakamlar; son kare ilk kareye döner (loop).

## 3D
Her kamera hareketi açıkça tarif edilir; gerçek veri; tam render öncesi test kareleri; bloom çok hafif.

## Müzik
librosa → music_map.json (bpm, beats, downbeats, enerji, bölümler); küçük hareket vuruşta, geçiş downbeat'te, en büyük an ilk nakaratın ilk downbeat'inde.

## Seslendirme/altyazı
Whisper kelime zaman damgaları sahne sürelerini ve altyazıyı belirler; sahne süreleri değişken tutulur. SFX Web Audio ile sentezlenir; "her ses ekranda görünen bir olaya bağlı".

## Akış
Kural dosyası → brief (kısa = sürpriz, uzun = kontrol) → önce sahne listesi onayı, kod sonra → düzeltmeleri kare cinsinden ver ("logoyu 12 kare geciktir") → kontak sayfası/test kareleri → cilalama döngüsü → stili skill'e paketle.

## Brief (7 bölüm)
Rol · tek cümle hedef (izleyici ne hatırlayacak) · format · zaman damgalı sahne listesi (efekt değil fikir dizisi: hook → problem → dönüşüm → çözüm) · sanat yönetimi (arka plan, palet + tek vurgu, font, doku, referans) · hareket dili (sağa = ilerleme, büyüme = önem, dönme = durum değişikliği) · yasaklar ve inceleme.

## Cilalama rubriği
1–10 puan: hikâye netliği, zamanlama/ritim, easing, tipografi, hiyerarşi, kompozisyon, geçiş sürekliliği, renk, okunabilirlik. Ayrıca "AI şablonu gibi duran anlar", aceleye gelen anlar, ölü zaman (>0.5 sn hiçbir şey olmuyor) — saniye ve kare numarasıyla. P0/P1/P2 sırala, P0+P1 uygula; tüm puanlar ≥ 8 olana kadar, en fazla 3 tur.

## Stil → skill
Her stile ayrı paket: SKILL.md (ne zaman), STYLE.md (palet hex, font, doku, ışık, kompozisyon, yasaklar), MOTION.md (anlam haritası, easing tablosu, geçiş aileleri, ritim), PIPELINE.md, template.html, CHECKLIST.md, examples/. "Her şeyi bilen tek dev skill hiçbirini iyi yapmaz." Öğrenilen dersler pakete geri eklenir.

## Token/maliyet
Opus 5.5 orta effort varsayılan; kütüphane adını vermek yüzlerce satır kodu önler; kod öncesi sahne listesi onayı; aynı sohbette sayı düzeltme; tam render yerine ?t= tek kare / kontak sayfası; cilalama en fazla 3 tur.

## Eksikler (bizim sistemin dolduracağı)
Gerçek çekim kurgusu yok (hibrit "konu dışı"); uzun video yok (en uzun 90 sn); ses mühendisliği yok (LUFS, ducking, gürültü); SFX kütüphanesi yok; TTS yok; SRT/VTT yok; çalışan kod/şablon yok; Claude Code entegrasyonu (CLAUDE.md, skills, agents) yok; marka kiti/varlık hattı yok; platform teslim presetleri yok.
