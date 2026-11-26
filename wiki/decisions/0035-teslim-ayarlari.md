---
type: decision
title: "Teslim ayarları: çözünürlük, kalite, kodek, kare hızı"
status: accepted
tags: [adr, teslim, render, studio, cozunurluk]
created: 2026-11-13
updated: 2026-11-25
sources: []
---

# ADR: Teslim ayarları

## Bağlam
Kullanıcı Stüdyo'nun Teslim alanından çıktı ayarı yapmak, kurgunun son halini 1080p ya da 2K olarak almak ve seçeneklerin teknik adlarıyla (HD, FHD, QHD, UHD) düzenlenmesini istedi (2026-11-13). O güne kadar final her zaman sekans boyutunda, H.264 CRF 16, 30 fps çıkıyordu ([[0016-earshot-render-standardi-ajan-duzeni]]); tek seçenek İşler panelindeki küçük diyalogdu.

## Karar
- **Tek kaynak `src/vedit/teslim.py`:** `COZUNURLUK`, `KALITE`, `KODEK`, `FPS` tabloları. CLI bayrakları, sunucunun beyaz listesi ve arayüz seçenekleri bu tablolardan okunur; arayüz listeyi `GET /api/teslim/<stüdyo>/<proje>` ile alır, kendi kopyasını tutmaz.
- **Çözünürlük (kısa kenar, sekans yönü korunur):** 720 HD, 1080 FHD, 1440 QHD (2K), 2160 UHD (4K). Seçilmezse sekans boyutu.
- **Büyütme motorda yapılır:** Remotion `--scale = hedef kısa kenar / sekans kısa kenarı`. Yazı, grafik ve altyazı gerçek çözünürlükte çizilir, klip görüntüsü büyütülür. Kaynak klip hedeften küçükse uyarı basılır, render durmaz (kullanıcı kararı).
- **Kalite:** `arsiv` CRF 14, `yayin` CRF 16 (varsayılan, ADR 0016 ile aynı), `hafif` CRF 20. H.265'te 18 / 20 / 24.
- **Kodek:** `h264` (libx264 High, varsayılan) ve `h265` (libx265 Main, `hvc1` etiketi). Preset `slow`, renk BT.709 sınırlı aralık, ses AAC 320 kbps 48 kHz ikisinde de sabit; renk kapısı aynı.
- **Kare hızı:** 30 ya da 60, yalnız `kurgu.json` projelerinde. `kurgu.json` değişmez; motor için `work/edit/kurgu.render.fps.json` yazılır.
- **Önbellek:** ölçek ve kare hızı `work/renders/ham.ayar` dosyasına yazılır ve `ham_imzasi`'na girer. Çözünürlük ya da kare hızı değişince motor yeniden çalışır; kalite ya da kodek değişince yalnız teslim kodlaması yeniden yapılır.
- **Arayüz:** Teslim alanında "Çıktı ayarları" paneli (`TeslimPaneli.tsx`): seçimler, salt okunur teknik özet, uyarılar, "Final başlat" ve son teslimin ölçülen değerleri. İşler panelindeki Final diyaloğu kaldırıldı; "Final" düğmesi bu paneli açar. "Önce AI ile edit yap" seçeneği panelde yok (bkz. Export ve indirme): export, kullanıcının elle yaptığı kurguyu yeniden yazmamalı.
- **CLI:** `vedit final <proje> --cozunurluk 1440 --kalite yayin --kodek h264 --fps 30`; aynı bayraklar `vedit ai-edit --final` için de geçer.

## Export ve indirme
- Düğme adı "EXPORT" (İşler panelinde "Export"); komut adı `vedit final` aynı kalır.
- **İndirme:** `GET /api/indir/<stüdyo>/<proje>?yol=...` dosyayı `Content-Disposition: attachment` ile verir; yalnız çıktılar kökü, `work/` hariç. Çıktı ayarlarında "Son export" bloğunda İndir düğmesi, Çıktılar panelinde her satırda indir ikonu. `/dosya/...` rotası satır içi ve `sandbox` başlıklı kaldığı için indirmeye uygun değildi.
- **Eşleşme:** son export'un ölçülen boyutu, kodeği ve kare hızı seçili ayarla karşılaştırılır; farklıysa panel "EXPORT ile yeniden üret" der. İndirilen dosyanın seçilen özellikleri taşıdığı böyle görünür.
- **Engel önceden görünür:** `GET /api/teslim/...` yanıtındaki `hatalar` alanı `kurgu.denetle` sonucudur. Hata varsa panel listeler ve EXPORT kapanır; kurgu kaydedilince yeniden sorulur. Önceden hata yalnız İşler günlüğündeydi ve export sessizce düşüyor gibi görünüyordu.
- **Saydam zemin:** sahne formu "Saydam"ı yalnız tam ekran yerleşimde sunar; bölünmüşe dönülünce zemin koyuya çekilir. Bu geçersiz seçim `avatar-reel` export'unu durdurmuştu.
- **Export ajan çağırmaz:** EXPORT her zaman düz `final` işidir (Remotion, ffmpeg, ölçüm). "Önce AI ile edit yap" kutusu panelden kaldırıldı; AI edit ayrı iştir (İşler > Diğer > AI Edit, terminalde `vedit ai-edit`). Kullanıcı export'un yapay zekâ kullandığını düşünmüştü (2026-11-13); kayıtlar düz `final` gösteriyordu, izlenimin nedeni dakikalarca sessiz geçen render'dı.
- **Görünür ilerleme:** `final` başta "yapay zekâ kullanılmıyor" satırını, sonra dört aşamayı (`1/4 Görüntü render` … `4/4 Denetim`) basar; motor her %5'te kare sayısını ve kalan süreyi yazar (`hizli.ilerleme_satiri`, Remotion'ın `Rendered N/T` satırından). Taslak sessiz kalır.
- Export sürerken düğme kapalıdır; bitince bildirim çıkar ve blok yenilenir. Otomatik indirme yok: tarayıcı tıklamasız indirmeyi engelleyebilir.

## Sonuçlar
- Motor ölçeği tam hassasiyetle verilir. `1.33334` gibi yuvarlanmış değerde Remotion 4.0.484 "height must be an integer, but is 2560.0128" diye durdu; ADR 0016'daki `--scale=1.33334` örneği bu sürümde geçerli değil. Tam piksel vermeyen sekans boyutunda render açık hatayla durur.
- Teslim kapısı beklenen boyutu da denetler; boyut tutmazsa dosya yazılmaz.
- Reels'te 1080x1920 dışı boyut ve H.265 yalnız uyarıdır; Instagram yüklemeyi 1080p'ye indirir.
- Bitrate rehberi H.265'te %60 alınır, 720p için 5 Mbps eklendi.

## Kapsam dışı
HDR, ProRes, VP9/AV1, hedef bitrate, iki geçişli kodlama, yapay zekâ ile görüntü büyütme, taslak ayarları.

## Doğrulama
`tests/test_teslim.py`, `tests/test_hizli.py`, `tests/test_studio_dosya.py`, `studio/web/src/paneller/TeslimPaneli.test.ts`, tarayıcı `studio/e2e/teslim_ayar.py`. Gerçek render (10 sn kopya proje): 1440x2560 H.264, aynı ham ile H.265 `hvc1` (motor atlandı), 1080x1920 60 fps (600 kare).

## Güncelleme (2026-11-25)
Master ön ayarı, kaynağa eşle, 10-bit H.265 ve sadakat ölçümü eklendi; teslim renk dönüşümü zscale'e geçti. Ayrıntı [[0060-proxy-master-conform]].
