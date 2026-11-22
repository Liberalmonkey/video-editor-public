---
type: decision
title: "Video Stüdyo: görüntü ve sesi ayırma, canlı metre, 16:9 sahne"
status: accepted
tags: [adr, arayuz, ses, timeline, remotion]
created: 2026-11-05
updated: 2026-11-05
sources: []
---

# ADR: Görüntü ve sesi ayırma, canlı metre, 16:9 sahne

## Bağlam
Kullanıcı 2026-11-05'te dört şey istedi: klibin görüntüsü ile sesini ayırmak, canlı ses metresi ve yapay zekâsız ses kontrolü, sahne şablonlarının videoya göre 9:16 ya da 16:9 olması, Gemini CLI desteği (sonuncusu [[0023-coklu-ajan]]). İlk üçü [[video-studyo]] açık sorularıydı. [[0021-video-studyo-nle]] bağlı A/V'yi seçmiş, canlı metreyi tarayıcı sesi yanıltır diye ertelemişti.

Keşifte iki hata çıktı:
- Önizlemede 0 dB üstü kazanç duyulmuyordu. Remotion `useWebAudioApi` kapalıyken `volume`'ü 1'e kırpar; render'da kazanç vardı.
- Yeni projede bölünmüş sahne görünmüyordu. `konusmaci` işareti yalnız içe aktarmada geliyordu; normal video klibi en altta çizilen sahneyi örtüyordu.

## Seçenekler
| Konu | Seçenek | Neden seçilmedi ya da seçildi |
|---|---|---|
| Ayırma | Her video eklenince ayrı A izi (Premiere) | 0021'deki bağlı A/V kararını ve tüm eski projeleri değiştirirdi |
| Ayırma | İstekle ayır, bağlı kalsın | Seçildi: eski davranış aynı, ayırma geri alınır ve birleştirilir |
| Kanal metresi | İz başına Web Audio düğümü | Remotion iz başına düğüm vermiyor; ses yolunu yeniden yazmak gerekirdi |
| Kanal metresi | Dosya tepesi çarpı kazanç | Seçildi: mevcut dalga verisi, fader'ı anında gösterir, saf fonksiyon |
| Master metresi | Remotion ana düğümüne analizör | Seçildi: gerçek çıkış, `Internals` iç API'si, sürüm birebir sabit |
| Yatay sahne | SplitReel'i yatay için yeniden yazmak | `openmontage/` git dışı; sekiz sahne türü yeniden yazılırdı |
| Yatay sahne | 1080x998 sahne kutusunu ölçeklemek | Seçildi: tüm türler aynen çalışır, dikey kod yolu değişmez |

## Karar
- **Ayırma.** `Klip.ses_kapali`; ses `olay.konusma` taşıyan, aynı kaynak aralıklı, `bag` ile bağlı klip olur. İz kazancı klibe geçer, seviye sıçramaz. Hızı %100 olmayan klip ayrılmaz: render'da ayrık ses ffmpeg miksidir, hız uygulanmaz.
- **Bağlı eş.** Aynı bağ, aynı yer ve süre. Kırpma, ripple kırpma, rolling ve slip eşe aynı payı uygular; en dar pay kazanır. Bölme ortağı da böler, sağ parçalar `bag:t` ile birbirine bağlı kalır. Alt ile tek başına taşınan klip eş olmaktan çıkar, kırpımı ayrılır. Slide bağlı eşte çalışmaz, önce Ctrl+L.
- **Render.** `olaylar_uret` ayrık sesi `ses` listesine yazar: konuşma busına girer, ducking ve SFX geri çekilmesi aynen çalışır. Ayrılmamış sesli klip varsa ham.mp4 da listeye girer. Ayrık ses yoksa çıktı eskisiyle aynı. Ayırma bir kez görüntü render'ı ister, sonraki ses düzeltmeleri istemez.
- **Altyazı sesi izler.** Görüntüsü altyazı izinde olup sesi ayrılmış klip düşer, ayrık ses girer. Kural Python ve TS'de aynı.
- **Metre.** Master gerçek çıkış, kanal tahmindir. İkisi "önizleme" etiketi taşır: ducking ve loudnorm yoktur, ölçülmüş sayı "Son miks" kutusundadır. Dinleme sesi analizörden sonra gelir, metreyi etkilemez, render'a girmez.
- **Elle kontrol.** Timeline ses çizgisi (çift tık 0 dB), Alt+Yukarı/Aşağı ±1 dB, bağlı grupta tıklanan klibin Efekt paneli. Teslim -14 LUFS'a normalize edildiği için fader dengeyi değiştirir, toplam yüksekliği değil; ipucu bunu söyler.
- **16:9.** Sahne solda (1169 px), konuşmacı sağda (751 px). FullTitle 530 px yukarı, altyazı y=945; bölünmüşte konuşmacı sütununda ve %80. Boş kurguya gelen ilk video sekansı kurar; Program Monitör'de 9:16/16:9 seçimi, geri alınır.

## Sonuçlar
- `studio/remotion` değiştiği için `ham_imzasi` her projede bir kez yeniden render ister.
- Önizlemede tüm medya Web Audio'dan geçer. 150/150 kare akıcılık ölçüldü; çok izli yük yeniden ölçülmedi.
- Çapraz geçişte önceki klibin kuyruğu ayrık sese geçmez, yalnız giriş fade'i taşınır.

## Ölçüm (2026-11-05, başsız Chrome, `studio/e2e/yatay_ses.py`, `studio/e2e/yatay_render.py`)
| Konu | Sonuç |
|---|---|
| -12 dBFS ton, kanal ve master metresi | -11,9 ve -11,8 dB |
| +6 dB fader, master | -11,8'den -5,9'a (eski hata kapandı) |
| Metre açık, 5 sn oynatma | 150/150 kare |
| Ayrık ses 0,4 sn kaydırıldı, tam `final` | tık 7,415 sn, beklenen 7,4 |
| Aynı ses bağlı ve ayrık miks | yükseklik farkı en çok 0,1 LU (`test_kesin_ses.py`) |
| 8 şablon + hook + CTA, 16:9 ve 9:16 taslak | kontak sayfasında taşma yok, dikey önceki görünümle aynı |

Dikey render için piksel düzeyinde SSIM ölçülmedi. Dikey kod yolu değişmediği için kontak sayfası denetimi yapıldı.

## İlgili kod
`studio/web/src/zaman/komutlar.ts`, `studio/web/src/zaman/metre.ts`, `studio/web/src/paneller/SesMetresi.tsx`, `studio/remotion/Kurgu.tsx`, `studio/remotion/izdusum.ts`, `src/vedit/kurgu.py`, `src/vedit/olaysesi.py`, `src/vedit/schemas.py`
