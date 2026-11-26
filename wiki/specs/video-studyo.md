---
type: spec
title: "Video Stüdyo"
status: done
tags: [arayuz, timeline, remotion]
created: 2026-11-05
updated: 2026-11-24
sources: []
---

# Spec: Video Stüdyo

> [!note] Güncellendi 2026-11-15
> Çalışma alanları üçtür: Kurgu, Teslim, Kütüphane ([[0030-sade-arayuz]]); Kapak alanı kaldırıldı ([[0056-kapak-kaldirildi]]). "Arayüz içinde Claude sohbeti" artık kapsam içindedir: Kurgu alanında AI paneli ([[0026-arayuzde-ajan]]). Sonradan eklenen paneller: Video stili ([[0029-stil-paneli]]), Çıktı ayarları ([[0035-teslim-ayarlari]]), Motion ([[0036-motion-kutuphanesi-ve-ajanlar]]).

> [!note] Güncellendi 2026-11-15
> AI paneli kurguyu da başlatır: stil, kapsam (seçili klipler ya da giriş-çıkış aralığı) ve "AI ile editle", ardından önce/sonra özeti ve geri alma ([[0028-ai-edit]]).

> [!note] Güncellendi 2026-11-22

## Problem
Kurgu yalnız terminalden yapılıyor; kullanıcı videoyu görerek düzeltemiyor, kütüphaneyi ve dosyaları görsel yönetemiyor.

## Kullanıcı hikâyeleri
- Projeyi açarım, videoyu oynatırım, izlerde kırpar, taşır, keserim; sonuç render ile aynı görünür.
- Dosya, ses efekti, müzik, motion yükler ve silerim; kilitli varlıklar korunur.
- Altyazı metnini ve stilini düzeltirim. Tek tuşla taslak ve final alırım.
- Terminalde Claude `kurgu.json`'u değiştirir, arayüz anında gösterir.

## Kapsam
> [!note] Güncellendi 2026-11-12
> Çalışma alanları üçe (Kurgu, Teslim, Kütüphane) indi; Öneriler Altyazı paneline, Grafik Kütüphane paneline katıldı. Ayrıntı: [[0030-sade-arayuz]].

Paneller: Proje, Medya, Kütüphane, Kaynak ve Program Monitör, Timeline, Efekt Kontrolleri, Altyazı, Ses Mikseri, İşler, Çıktılar, Denetim.
Kapsam dışı: çok kameralı senkron, renk LUT'ları, Premiere proje içe aktarımı, arayüz içinde Claude sohbeti.

## Tasarım
Karar: [[0021-video-studyo-nle]], ayırma, metre ve 16:9 için [[0022-av-ayirma-metre-yatay]].

- **Veri:** `work/edit/kurgu.json`, şema `schemas.Kurgu`. Kelimeler kaynak zamanında durur, klipten sekans zamanına izdüşürülür.
- **Render:** `kurgu.hazirla` üretir: `edit/kurgu.render.json` (ses klipleri ve `rev` hariç, `words` izdüşümlü), `edit/olaylar.json` (ses izlerinden). Ses düzeltmesi görüntüyü yeniden render ettirmez.
- **Önizleme:** `Kurgu.tsx` Player'da `medya` proxy eşlemesi ve `onizleme: true` ile çalışır; ses klipleri yalnız önizlemede çalar, render'da `olaysesi` miksler.
- **Reel düzeni:** `konusmaci: true` klip SplitReel `Speaker` davranışını, `sahne` klipleri `StageScene` ve `FullTitle` bileşenlerini kullanır. Eski projeler kayıpsız gelir.
- **Güvenlik:** yalnız `127.0.0.1`, `Host` + `Origin` denetimi, çerez token, kök içi yol, beyaz liste komut.

## Kabul kriterleri
- Önizleme karesi ile `ham.mp4` karesi aynı kompozisyondan gelir, fark ölçülür.
- `kurgu.json` olmayan projede `vedit` davranışı değişmez.
- `kit.json` `locked` varlık silinemez; silme geri dönüşüm kutusuna gider.
- Yabancı `Origin`, `..` yolu ve beyaz liste dışı komut reddedilir.

- **Ayırma:** Shift+A sesi bağlı `olay.konusma` klibine çıkarır; render'da konuşma busına girer, altyazı sesi izler.
- **Metre:** master gerçek önizleme çıkışı, kanal dosya tepesi çarpı kazanç. Ölçülmüş sayı "Son miks"tedir.
- **Sekans:** 9:16 ya da 16:9; boş kurguya ilk video oranı belirler. Yatayda sahne solda, konuşmacı sağda.

## Açık sorular
- ~~Yatay sekansta sahne şablonları uyarlanmadı.~~ Uyarlandı ([[0022-av-ayirma-metre-yatay]]).
- ~~Görüntüden ayrı ses izi yok.~~ İstekle ayrılır ([[0022-av-ayirma-metre-yatay]]).
- ~~Canlı ses metresi yok.~~ Önizleme metresi var; ducking ve loudnorm içermez.
- Hızı %100 olmayan klibin sesi ayrılamaz; çapraz geçiş kuyruğu ayrık sese geçmez.
- Yardımcılar [[0024-oneri-araclari]]: Öneriler paneli, kelimeden kesme, Demucs, reframe, kazanç keyframe'i, XML. Gerçek kayıtta kalite ve NLE'de açılma denenmedi.
