---
type: decision
title: "Hazır stil kataloğu, stil silme ve videoya göre motion teması"
status: accepted
tags: [adr, stil, motion, tema, studio, katalog]
created: 2026-11-18
updated: 2026-11-18
sources: []
---

# ADR: Hazır stil kataloğu ve videoya göre motion teması

## Bağlam
Kullanıcı 2026-11-18'de üç şey istedi:
1. Stil sekmesinde eski stilleri silebilmek. [[0029-stil-paneli|ADR 0029]] yalnız referans dosyası silmeyi sağlıyordu.
2. Kurulu skill ve repolardaki video stillerini (anime vb.) görüp seçmek. Bu stiller diskte vardı ama arayüze bağlı değildi: `openmontage/styles/*.yaml` (5), `library/vendor/huashu-art-motion/references/风格配方/` (~55 tarif), `library/vendor/bang-motion/references/` ve `library/motion/tema/*.css` (20 tema).
3. Animasyonlar her videoda turuncu geliyordu. Nedeni: `Kurgu.motion_tema` varsayılanı `varsayilan` (turuncu `#FF7A00`), sabit motion klipleri (114 kaydın 85'i) `vedit motion kur` ile bu temayla pişiriliyor ve kurgu bu webm'i doğrudan kullanıyordu. 12 HTML'de renk değişkensiz yazılıydı.

İstenen: aynı animasyon tekniği her videoda korunsun, renk ve görünüm videoya göre değişsin.

## Seçenekler
- Her klibi her tema için önceden üretmek: 114 × 35 webm, depo şişer. Reddedildi.
- Temayı Remotion'da CSS filtresiyle değiştirmek: ton kaydırma paleti bozar, okunurluk ölçülemez. Reddedildi.
- **Render anında temalı kopya** (seçildi): sabit klip de şablon gibi `motion.sablon_uret` ile seçili temada üretilir, `work/public/motion/` önbelleğine yazılır. Kütüphane dosyası değişmez.

## Karar
| Konu | Karar | Neden |
|---|---|---|
| Stil silme | `stil.sil(studyo, ad)`: paket + `Projeler/inputs/_referanslar/<stüdyo>/<ad>/` + bu stili seçmiş projelerin `stil.txt`'si; `DELETE /api/stil/{s}/{ad}`; panelde çöp kutusu ve satır içi onay | Kullanıcı kararı: paket ve referanslar birlikte gider |
| Katalog | `library/stiller/katalog.json` (31 stil, 8 kategori); kart kaynak ve lisans taşır; ad genel ve Türkçe, belirli eserin karakteri kopyalanmaz | Kaynaklar MIT ve AGPL; esinlenme görsel dil düzeyinde |
| Paket | Katalogdan eklenirken `stil_katalog.paket` STYLE.md, MOTION.md, tokens.json yazar; var olan pakete dokunmaz | Kullanıcı sonra düzenler; üzerine yazma yok |
| Tema bağı | `tokens.json → motion_tema`; kendi paleti olan kart için `library/motion/tema/<id>.css` üretilir | Stil seçilince grafikler stilin renginde gelir |
| Tema sırası | `kurgu.etkin_tema`: açık tema > seçili stilin teması > proje teması > `varsayilan`. `varsayilan` artık "otomatik" demektir; açık turuncu `turuncu` teması | Eski kurgular `varsayilan` yazılı; şema değişmeden davranış düzelir |
| Proje teması | `vedit tema-cikar <proje>` girdinin baskın renklerinden `work/edit/motion_tema.css` yazar (k-ortalama, kontrast ≥3:1 vurgu, ≥4.5:1 yazı); soluk videoda vurgu baskın tonun karşıtıdır, turuncu bandına (20-45°) düşmez | Kullanıcı kararı: stil yoksa AI videoya göre kurar |
| Sabit klip | `kurgu.motion_bagla` sabit kütüphane klibini etkin temayla yeniden üretir; tema `varsayilan`a dönerse kütüphane dosyasına geri bağlar; `kit.json` `locked` kayıt temalanmaz | Aynı teknik, videoya göre renk |
| ai-edit | İstek "Motion teması" bölümü: stilin teması zorunlu; stil yoksa `tema-cikar` çalışır ve `"motion_tema": "proje"` istenir; `varsayilan`/`turuncu` yalnız kullanıcı isterse | Ajan turuncuya dönmesin |
| Altyazı | Değişmez: okunan kelime turuncu ([[0014-altyazi-standardi-ve-repo-entegrasyonu\|ADR 0014]]) | Proje sabiti; tema yalnız motion grafiğini etkiler |

## Sonuçlar
- Stüdyo API: `GET /api/stil-katalog`, `GET /api/stil-katalog/{id}/onizleme`, `POST /api/stil/{s}/katalogdan {id, proje?}`, `DELETE /api/stil/{s}/{ad}`. Stil panelinde "Stillerim / Hazır stiller" sekmesi, kategori süzgeci, önizleme kartı, "Ekle ve bu projede kullan".
- Önizleme: `vedit stil-katalog kur` her stil için örnek görselin (`library/stiller/ornek/<id>.*`, agy ile üretildi; yoksa paletten gradyan) üstüne başlık ve alt bant şablonunu stilin temasıyla basar: `library/stiller/onizleme/<id>.jpg`.
- `vedit kurgu-denetle` bilinmeyen `motion_tema`'yı hata sayar; `proje` geçerli addır.
- Sınır: tema renk, yazı tipi, köşe ve çizgi kalınlığını değiştirir; hareket eğrisi ve doku (gren, parlama) henüz temadan gelmiyor. Klipler bu değişkenleri okumaya geçince eklenecek.

## İlgili kod
- `src/vedit/stil.py` (`sil`, `motion_temasi`), `src/vedit/stil_katalog.py`, `src/vedit/tema.py`, `src/vedit/kurgu.py` (`etkin_tema`, `motion_bagla`), `src/vedit/motion.py` (`tema_yolu` Path kabul eder), `src/vedit/aiedit.py` (`_tema_bolumu`), `src/vedit/fizik.py`, `src/vedit/cli.py` (`stil-katalog`, `tema-cikar`)
- `src/vedit/studio/stil.py`, `src/vedit/studio/app.py` (`motion-sablon` otomatik tema), `studio/web/src/paneller/StilPaneli.tsx`, `studio/web/src/paneller/HazirStiller.tsx`
- `library/stiller/katalog.json`, `library/motion/tema/turuncu.css`, 12 motion HTML'inde renk değişkene çevrildi
- Testler: `tests/test_stil.py`, `tests/test_tema.py`, `tests/test_stil_katalog.py`
