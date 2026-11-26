---
type: decision
title: "Görsel üretimi: ücretsiz Google araçları ve kodla yazı katmanı"
status: accepted
tags: [adr, gorsel, kapak, google, flow, antigravity]
created: 2026-11-08
updated: 2026-11-24
sources: []
---

# ADR: Görsel üretimi Google araçlarıyla

> [!note] Güncellendi 2026-11-24: kapak üretimi kaldırıldı ([[0056-kapak-kaldirildi]]). Yazı şablonu `library/gorsel/sablon.html`'e taşındı; görsel üretimi (sunum, B-roll, loop karesi) sürer.

## Bağlam
Kullanıcı kapak (YouTube, Instagram), sunum grafiği ve videoda kullanılacak görselin ajan tarafından üretilmesini istedi; üretimin dengeli olmasını şart koştu (2026-11-08). Bütçe 0 USD kuralı sürüyor. Araştırma ikinci beyinde: `knowledge/sources/2026-11-08-google-araclari.md`.

Bulgular: Gemini API'nin görsel modelleri (Nano Banana 2, Nano Banana Pro, Imagen 4) Ekim 2026 itibarıyla ücretsiz katman sunmuyor. Ücretsiz yollar Antigravity CLI'nin yerleşik `generate_image` aracı (dar kota), Google Flow (Nano Banana 2 görseli çoğunlukla kredisiz, günde 50 kredi) ve Gemini uygulaması (günde ~20 görsel). Flow'un API'si yok.

## Karar
| Konu | Karar | Neden |
|---|---|---|
| Biçim | Ajan değil, iki skill: kasada genel `google-araclari`, projede `gorsel-uret` | Kısa, sıralı iş; ADR 0003 ve 0017 kısa işte ajan istemiyor |
| Motor sırası | Eldeki kare, Antigravity CLI, Flow (Chrome), Gemini uygulaması | Ücretsiz olandan başla, kotası dar olanı tek görsele sakla |
| Ücretli API | Kullanılmaz | Bütçe 0 USD; kullanıcı açıkça isterse bu ADR güncellenir |
| Yazı | Görsele gömülmez; `library/kapak/sablon.html` + `vedit pano -o kapak.jpg` | Modeller Türkçe harfi bozar; altyazıyla aynı Montserrat ve turuncu |
| `vedit pano` | `-o` .png/.jpg olunca `--sure` anındaki tek kareyi çeker, Montserrat'ı kütüphaneden bağlar | Yeni komut yerine mevcut Playwright hattı |
| Denge | Kapak en çok 3 aday (> [!note] Güncellendi 2026-11-09: kapak varsayılan 1, en çok 5 aday, bkz. [[0027-kapak-sayfasi]]); B-roll görseli dakikada en çok 1 ve yalnız gerçek ya da kodla çizilmiş görsel yoksa; her üretim `work/gorsel/log.md` | Kullanıcının "dengeli" şartı, AI slop riski |

## Sonuçlar
- `vedit gorsel` (`src/vedit/gorsel.py`): agy headless modda dosya taşıyamadığı için görsel `~/.gemini/antigravity-cli/brain/<conversation_id>/` altından alınıp hedefe kopyalanır, log satırı yazılır. Doğrulandı 2026-11-08, agy 1.5.3: 77-98 sn, 16:9 için 1376×768.
- Stitch bu projede kullanılmaz; arayüz işleri için kasadaki skill'de durur.
- Resmi olmayan Antigravity OAuth eklentileri hesap riski nedeniyle kurulmaz.
