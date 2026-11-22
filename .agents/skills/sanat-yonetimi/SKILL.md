---
name: sanat-yonetimi
description: Animasyon, motion grafik, kinetik tipografi, explainer, intro, Reels ve YouTube animasyonu için işe özgü sanat yönetimi kurar — brief, iki üç görsel yön, stil kartı (work/edit/stil-karti.md), hareket çizelgesi, klişe testi ve Türkçe glif denetimi. Üretim HyperFrames'te yapılır (ADR 0050). Animasyonlu bir iş planlanırken, "stil kartı", "görsel yön", "şablon gibi duruyor", "klişe", "sanat yönetimi" dendiğinde kullan.
---

# Sanat yönetimi

Amaç: her animasyonlu işte görünümü bilinçli seçmek. Seçilmeyen her ayar (yazı tipi, renk, eğri, düzen) en sık görülen değere kayar; sonuç şablon kokar. Bu skill seçimleri yazılı ve denetlenebilir hale getirir.

Üretim motoru HyperFrames'tir (`hyperframes` skill'i, ADR 0050). Renk ve yazı tipi seçili stilin token'ından gelir (`library/motion/tema/<id>.{css,json}`, ADR 0043); bu skill token'ı değiştirmez, nasıl kullanılacağına karar verir.

## 1. Brief
Üç soruyu yanıtla. Eksik olanı kendin seç ve seçimi tek satırla söyle.
1. **Tek cümle:** video izleyiciye ne bıraksın?
2. **Format:** 9:16 ya da 16:9, süre, yayın yeri (Reels, YouTube, sunum).
3. **Malzeme:** ekran kaydı, fotoğraf, logo, veri, ses. Varsa görsel dil malzemenin etrafında kurulur.

## 2. Yönler
İki ya da üç yön yaz. Her yön dört satırdır:
- **Fikir:** konuyu hangi görsel yöntem anlatır (diyagram, nesne, harita, belge, sayaç, el çizimi...).
- **Yüzey:** zemin dokusu ve derinlik (düz, kâğıt, cam, ızgara, fotoğraf).
- **Yazı:** başlık ve gövde rolü, büyüklük oranı, harf aralığı.
- **Hareket:** bir giriş, bir vurgu, bir çıkış davranışı ve hangi eğri.

Yönler birbirinden en az üç eksende ayrılmalı. Önerini gerekçesiyle söyle; seçim kullanıcınındır, kullanıcı yoksa önerini uygula.

## 3. Stil kartı
Seçilen yön `work/edit/stil-karti.md` dosyasına yazılır. Kart şunları içerir:
- Stil kimliği (`work/edit/stil.txt`) ve kullanılan token adları (renk rolleri, yazı tipi, eğriler).
- Izgara: kenar boşluğu, güvenli alan (9:16'da alt %20 altyazıya ayrılır), hizalama ekseni.
- Yazı ölçeği: en fazla üç boy; en küçük yazı 1080 genişlikte 42 px altına inmez.
- Hareket dili: süre aralığı (giriş 300-600 ms), eğri adları, aynı anda en çok iki hareketli öğe.
- Yasaklar: bu iş için bilinçli olarak kullanılmayacak üç şey.
- Aynı serinin önceki kartından en az üç eksende fark (zemin, düzen, hareket, yazı, renk rolü).

## 4. Hareket çizelgesi
Her sahne için tek satır: zaman aralığı, söylenen söz (kelime çapası), görünen öğe, hareketi, eğrisi. Hareket söze bağlanır; söz yoksa hareket yoktur. HyperFrames kompozisyonunda bu çizelge GSAP zaman çizelgesine bire bir çevrilir.

## 5. Klişe testi
Render sonrası 0., 1., 3., 6., 10. saniye ve son kare açılır. Her kare `references/klise-listesi.md` ile karşılaştırılır. Gerekçesi kartta yazılı olmayan her eşleşme bulgudur. Sonuç `qa/critique.md` dosyasına yazılır. Ayrıntılı slop denetimi `denetim` skill'indedir.

## 6. Türkçe glif denetimi
Kullanılan her yazı tipinde `ğ Ğ ş Ş ı İ ç Ç ö Ö ü Ü` karşılığı olmalı. Kontrol: kompozisyonda bu harfleri içeren bir satır render edilir ve kare açılıp bakılır. Eksik glifte yedek yazı tipine düşen harf bulgudur (P1). Büyük harfe çevirmede `i → İ` kuralı için `text-transform` yerine metin önceden çevrilir (`lang="tr"` tek başına yeterli değildir).

## 7. HyperFrames'e devir
- Kart ve çizelge hazırsa kompozisyon `hyperframes` skill'inin kurallarıyla yazılır.
- Bindirme (alt bant, ikon, metin grafiği) saydam kökle yazılır ve `--format webm` ile render edilir.
- HyperFrames'in karşılamadığı iş (gerçek fizik simülasyonu, kare başına yüz takipli yerleşim) Remotion'a gider; gerekçe karta yazılır.
