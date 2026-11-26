---
type: decision
title: "Kasa ve Keşif: hibrit motion kütüphanesi, videodan kaydetme, tam silme ve doğru önizleme"
status: accepted
tags: [adr, kutuphane, motion, galeri, studio, onizleme]
created: 2026-11-25
updated: 2026-11-25
sources: ["[[0012-kutuphane-kit]]", "[[0036-motion-kutuphanesi-ve-ajanlar]]", "[[0045-native-motion]]", "[[0050-hyperframes-birincil-motor]]"]
---

# ADR 0061: Kasa ve Keşif

## Bağlam
Kullanıcı Stüdyo'daki Kütüphane > Motion ve Galeri sekmelerinde üç sorun gördü (2026-11-25):
- Eski kayıtlar düz ve eski görünüyordu.
- Önizlemeler bozuktu: "Zil" ve "Turuncu-koyu silme" siyah kutu gibiydi, şablonlar mikroskobikti.
- Kütüphane kişisel biçimde yönetilemiyordu: kilitli varlıkta 403 çıkmaz yoldu, toplu silme ve videodan kaydetme yoktu.

İki yol karşılaştırıldı:
- **A:** stile göre her videoda AI üretimi. Uzun videoda grafik başına 8-20k token harcar ve kalitesi değişkendir.
- **B:** modern paket ve kişisel kasa.

Kullanıcı **hibriti** seçti.

## Karar
- **Üç görünüm:**
  - **Kasam** (varsayılan): yalnız kullanıcının kaydettikleri, `library/kasa/manifest.json` (`kasa.py`).
  - **Keşif:** tema token'ıyla yeniden üretilen 18 şablon ve içe aktarılmış dış varlıklar. Native bileşenler Grafik sekmesinde.
  - **Arşiv:** native karşılığı olan 79 kayıt ve 17 sabit eski grafik. Silinmez; görünümden iner.

  Kullanıcı "114 kaydın hepsi Arşiv'e" demişti. 18 şablon Keşif'te tutuldu, çünkü öbür türlü Keşif boş kalırdı. Sabit eski grafikler (`eski`) AI edit kataloğundan çıkarılmadı: Keşif paketi yerini alana kadar ai-edit yetenek kaybetmez.
- **Videodan kaydet:** timeline klibine sağ tık > "Kütüphaneye kaydet" (`POST /api/kasa/kaydet/{stüdyo}/{proje}`). Niyet saklanır:
  - Şablon `sablon` ile, kompozisyon `hf` ile kaydedilir. Projeye özel kompozisyon `library/motion/hf/kasa-<id>/`'e taşınır.
  - Bileşen `bilesen` ile kaydedilir; posteri son taslaktan alınır.
  - Motion ve görsel dosya kopyalanır.
  - Ses efekti dosyası lisansıyla kopyalanır. Dosyasız rol olayı kaydedilmez, hata mesajı verir.
- **AI edit sırası:** motion kataloğunun başında "Kasam" bölümü durur. Sıra Kasam, sonra kütüphane ve native bileşenler; hiçbiri uymazsa seçili stilin token'ıyla HyperFrames kompozisyonu üretilir.
- **Silme:**
  - Kilitli varlıkta 403 yerine 423 döner. Arayüz "Kilidi kaldır ve sil" onayı sorar (`kilit_ac`); kilit `kit.json`'dan, kimlik yuvalardan kalkar.
  - Toplu silme `POST /api/kutuphane/toplu-sil`: kilitli ve kullanımdaki kayıtlar atlanır, nedenleriyle raporlanır.
  - Kilit ucu `PUT /api/kit/kilit`.
  - Kodla tanımlı galeri öğesi (fizik, ışık, karakter, efekt, stil) silinemez; `library/kasa/gizli.json` ile gizlenir. "Gizlenenleri göster" anahtarıyla geri gelir.
- **Önizleme** (`onizleme.py`):
  - Alfa kaplaması kare kare ölçülür. Kısa klipte 30 fps, uzunda 8 fps kullanılır.
  - Geçişte kaplaması 0,5'e en yakın an seçilir ve dama zemin kullanılır (koyu panel koyu zeminde kaybolmasın). Diğerlerinde tam kaplama olmayan, oturmuş tepe kare seçilir.
  - Grafik alfa sınır kutusuna %12 payla kırpılır; 480 px kare poster ve 320 px döngü (`onizleme.mp4`) üretilir.
  - `vedit motion onizleme [id]` render etmeden yeniler; 114 kayıt yenilendi.

## Sonuçlar
- Keşif paketini registry blokları ve GSAP ile ajans düzeyine çıkarmak ayrı bir üretim işidir (`motion-tasarimci` + `motion-denetci`). Bu ADR altyapıyı kurar.
- HyperFrames kompozisyonunu zip ile yükleme eklenmedi. Kompozisyon videodan kaydedilerek kasaya girer.
