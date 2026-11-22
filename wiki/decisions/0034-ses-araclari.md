---
type: decision
title: "Ses araçları: ses çıkarma, 2 ve 4 kanallı ayırma, tek panel"
status: accepted
tags: [adr, ses, demucs, ayristir, studio]
created: 2026-11-12
updated: 2026-11-12
sources: []
---

# ADR: Ses araçları

## Bağlam
Kullanıcı verilen videolardaki sesi videodan ayırma, arka plan müziğini ve sesleri ayırma gibi araçları hem AI'ın hem kendisinin kullanabilmesini istedi (2026-11-12). Demucs kuruluydu ([[0024-oneri-araclari]]) ama yalnız iki kanal veriyordu, HTTP isteğini bloke ediyordu, müzik kanalı arayüze dönmüyordu, toplu işlem ve sesi dosya olarak çıkarma yoktu; düğmeler Klip panelinde dağınıktı.

## Karar
| Konu | Karar | Neden |
|---|---|---|
| Ayırma | `ayristir.ayir(kaynak, hedef, stem=2\|4)`: 2 kanal vokal ve müzik; 4 kanal vokal, davul, bas, diğer ve bunların toplamı olan müzik. Aynı `htdemucs` ağırlığı | Ek indirme yok; "konuşmasız müzik" her kipte var |
| Önbellek | Kip başına ayrı dosya adı (`<ad>.s4.<kanal>.wav`) | İki kip birbirini ezmez |
| Komut | `vedit ayristir <proje> [yol] [--stem 2\|4] [--hepsi]`, `vedit ses-cikar <proje> [yol] [--bicim wav\|mp3\|m4a] [--hepsi]` | Terminal hattı ve ajan aynı aracı kullanır |
| Ses çıkarma | Çıktı `Projeler/outputs/<stüdyo>/<proje>/ses/`, 48 kHz stereo, var olanın üzerine yazmaz | Çıktı düzeni; teslim dosyası ezilmez |
| Kuyruk | Ayırma ve ses çıkarma iş kuyruğunda; `POST /api/ayristir` önbellek varsa hemen döner, yoksa iş kimliği verir; `GET` sonucu alır | CPU'da ayırma sesin yaklaşık 2,5 katı sürer; ilerleme ve iptal gerekir |
| Arayüz | Hepsi **Ses** panelindeki "Ses araçları" bölümünde: sesi videodan ayır ya da birleştir, sesi dosyaya çıkar, konuşmayı müzikten ayır, arka plan müziğini kaldır (tek tık, tek geri alma), ayrılanları timeline'a ekle (sessiz izler), konuşmayı temizle | Tek iş tek yer ([[0030-sade-arayuz]]) |

## Sonuçlar
- Klip panelinde yalnız klip düzeyi ayarlar kaldı (kazanç, fade, keyframe, konuşmada kıs).
- İş kuyruğu beyaz listesi `yol`u `inputs:` ya da `public:` kökünde ve var olan dosya olarak doğrular.
- Hızı %100 olmayan klipte ayırma dosyaları üretilir ama kurguya uygulanmaz; kullanıcı uyarılır.
- Doğrulandı 2026-11-12: `avatar-reel` `1.mp4` (14,9 sn) 4 kanal ayırma 24 sn; `ses-cikar` mp3 çıktısı. Arayüz akışı tarayıcıda ayrıca denenir.
- DeepFilterNet kurulmadı; konuşma temizliği mevcut `afftdn` ile kalır.

## İlgili kod
- `src/vedit/ayristir.py`, `src/vedit/cli.py` (`cmd_ayristir`, `cmd_ses_cikar`), `src/vedit/studio/isler.py` (`ses_arguman`), `src/vedit/studio/app.py`
- `studio/web/src/paneller/MikserPaneli.tsx`, `studio/web/src/paneller/sesAraclari.ts`, `studio/web/src/zaman/komutlar.ts` (`stemEkle`)
- Testler: `tests/test_ayristir.py`, `tests/test_studio_dosya.py`
