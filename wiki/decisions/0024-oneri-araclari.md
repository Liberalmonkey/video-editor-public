---
type: decision
title: "Video Stüdyo: konuşma temizliği, kesim önerisi, metinden kurgu, ayrıştırma, reframe, ses keyframe, XML"
status: accepted
tags: [adr, arayuz, ses, timeline, disa-aktarim]
created: 2026-11-05
updated: 2026-11-05
sources: []
---

# ADR: Kurgu yardımcıları

## Bağlam
[[0022-av-ayirma-metre-yatay]] sonrası önerilen yedi geliştirmeyi kullanıcı sırayla istedi (2026-11-05). Ortak ilke [[0015-ai-slop-denetimi]] ile aynı: araç aday üretir, kurguyu kullanıcı değiştirir, her uygulama tek geri alma adımıdır. Bütçe 0 USD, yalnız açık kaynak.

## Karar
| Özellik | Nasıl | Neden |
|---|---|---|
| Konuşma temizliği | `KlipSes.temizle`; `olaylar.json` `temizle` aralıkları, konuşma busunda `highpass` + `afftdn` | Model yok, ffmpeg yeter. `afftdn` yalnız `nf` gerçek tabana yakınsa çalışır: `tn=1` ölçüldü, 0,3 dB. Taban her aralıkta ölçülür, azaltma 12 dB'de durur |
| Sessizlik ve dolgu önerisi | `sessizlik.oneriler`: kelime arası boşluk + enerji, tutucu dolgu listesi (`ıı`, `ee`, `hmm`, `um`) | "şey", "yani" anlam taşıyabilir, listede yok. Öneriler paneli adayı cetvelde gösterir, seçileni keser |
| Metinden kurgu | Altyazı panelinde kelimeyi ya da aramada bulunanları kes: `araliklariCikar` | Kelime zamanı zaten kaynak zamanında; ayrık seste görüntü ve ses birlikte kesilir |
| Konuşmayı müzikten ayırma | Demucs `htdemucs --two-stems vocals`, ayrı `.venv-ayristir` (CPU torch) | Torch ana ortamı ağırlaştırmasın. Sonuç `work/public/ayrisan/`, kaynak içeriğiyle önbellekli |
| Otomatik reframe | `kurgu_reframe`: YuNet yüz izleme, `donus.x` keyframe ve dolduran `olcek` | Mevcut `reframe.py` modeli. Yalnız klip sekansla farklı yöndeyse önerilir |
| Ses keyframe'i | `KlipSes.kf` (dB, klip başından); önizleme `sesEgrisi`, render `zarf` | Önizleme ve render aynı eğri; bölme, kırpma ve hız eğriyi taşır |
| XML dışa aktarma | `disa`: FCPXML 1.10 (Resolve, Final Cut) ve xmeml 5 (Premiere) | Kodla çizilen sahne ve metin taşınamaz, işaret olarak geçer ve listelenir |

## Sonuçlar
- Temizlik ve ses keyframe'i olmayan projede `olaylar.json` eskisiyle aynı kalır.
- Demucs CPU'da sesin yaklaşık 2,5 katı sürer; istek bitene kadar açık kalır. Uzun videoda iş kuyruğuna taşınmalı.
- Reframe yalnız yatay ekseni izler. Konuşmacı düzenindeki kliplere uygulanmaz.
- XML'de geçiş, efekt, altyazı ve hız rampası yok; sabit hız var. Gerçek NLE'de açılması denenmedi.
- Ayrıştırılan ses görüntüye geri birleştirilemez, çünkü kaynağı değişti.

## Ölçüm (2026-11-05)
| Konu | Sonuç |
|---|---|
| Temizlik, -34 dBFS beyaz gürültü + ton | taban en az 6 dB iner, ton ±1,5 dB içinde (`test_ses_zarf_temizle.py`) |
| Kazanç zarfı 0'dan -20 dB'ye | miksteki fark 20 ±1,5 dB |
| Öneri, 1,5 sn sessizlik içeren 10 sn | 1 aday, kesimden sonra 8,74 sn, tek Ctrl+Z geri alır (`studio/e2e/oneri_araclari.py`) |
| Reframe, 1280x720 klip 9:16 sekansta | ölçek 3,1605 |
| Demucs, 8 sn mp4 (ton + gürültü, konuşma yok) | 15,9 sn; vokal -64,6 LUFS, müzik -27,4 LUFS; ikinci çağrı önbellekten 0,01 sn |
| `.venv-ayristir` | 778 MB, model 81 MB (`~/.cache/huggingface`) |

Gerçek konuşma kaydında temizlik ve ayrıştırma kalitesi, gerçek yüzde reframe ve XML'in Premiere/Resolve'da açılması denenmedi.

## İlgili kod
`src/vedit/sessizlik.py`, `src/vedit/ayristir.py`, `src/vedit/kurgu_reframe.py`, `src/vedit/disa.py`, `src/vedit/audio.py`, `src/vedit/olaysesi.py`, `src/vedit/kurgu.py`, `studio/web/src/paneller/OnerilerPaneli.tsx`, `studio/web/src/paneller/EfektPaneli.tsx`, `studio/web/src/zaman/komutlar.ts`
