---
type: decision
title: "Hazır efektler: klipte kayıt olarak duran zoom, punch, odak, ken burns, giriş/çıkış ve sarsıntı"
status: accepted
tags: [adr, kurgu, remotion, efekt, studyo, ai-edit]
created: 2026-11-12
updated: 2026-11-12
sources: []
---

# ADR: Hazır efektler

## Bağlam
Zoom ve vurgu hareketleri el keyframe'iyle yazılıyordu. Ajan (`vedit ai-edit`) her zoom için `donus.olcek` keyframe'lerini tek tek hesaplıyor, odak noktalı zoomda kaymayı telafi etmeyi unutuyor, art arda kesimlerde hep aynı ölçeği kullanıyordu. Stüdyoda da aynı hareketi her klipte yeniden kurmak gerekiyordu. Konuşmacı punch'ı yalnız sabit +%10 idi; ölçek, süre ve odak seçilemiyordu.

## Seçenekler
- El keyframe'inde kalmak, ajana daha uzun kural yazmak. Matematik her seferinde yeniden yazılır, hata aynı kalır.
- Efekti kaydederken keyframe'e açmak (Stüdyoda düğme). Kurguda niyet kaybolur; süre ya da ölçek değişince yeniden yazmak gerekir.
- Efekti klipte kayıt olarak tutmak (`hazir: [{ad, t, sure, ...}]`), keyframe'e render sırasında açmak. Seçilen.

## Karar
| Konu | Karar | Neden |
|---|---|---|
| Kayıt | `Klip.hazir: [{ad, t?, sure?, ses?, ...parametre}]`, `t` klibin başından sn; Python şemasında ham sözlük | Eski `kurgu.json` aynen yüklenir; niyet okunur kalır |
| Katalog | 13 efekt `studio/remotion/hazirEfekt.json`'da: `amac`, `ne_zaman`, `ses`, `rol`, `son`, `param` (min, max, secenek, degisim) | Arayüz, denetim ve ajan isteği tek dosyadan beslenir |
| Matematik | Yalnız `studio/remotion/hazirEfekt.ts` (`cozumle`, `genislet`, `deger`, `pisir`) | Önizleme (Player) ve render aynı `Kurgu.tsx` kodunu çalıştırır |
| Bileşim | El keyframe'i taban; hazır iz üstüne biner: ölçek ve opaklık çarpılır, x, y, açı, bulanıklık toplanır | Çakışma yok; el ile konum verilmiş klibe de efekt eklenir |
| Dönüşüm | `Donusum` ölçek, x, y, opaklık, açı ve bulanıklığı uygular; `donus.capa` dönüşüm merkezidir, `efekt.bulanik_kf` doluysa sabit bulanıklığın yerine geçer | `hazirEfekt.ts` bu alanları kullanıyor; hepsi isteğe bağlı |
| Varsayılan çözüm | `t` yoksa 0, `son: true` efektte klip sonu eksi süre; `sure` 0 ise klibin sonuna kadar; yazılan sayı aralığa sınırlanır | TS `cozumle` ve Python `hazir_efekt.cozumle` aynı kuralı izler |
| Değişim | Değer yazılmamışsa aynı izde art arda kliplerde `degisim` listesi sırayla kullanılır | Art arda aynı ölçekte punch ucuz görünür |
| Odak zoom | Nokta (x, y) çapaya göre ölçeklenirken aynı eğriyle geri itilir; el ölçeği hesaba katılır | Anlatılan düğme ya da sayı kadrajda yerinde kalır |
| Ken burns | Kayma her an büyümenin açtığı payın %90'ında kalır | Kenarda boşluk açılmaz |
| Denetim | `src/vedit/hazir_efekt.py`, `kurgu.denetle` içinden: bilinmeyen ad, bilinmeyen parametre, aralık dışı sayı, geçersiz seçenek, klip dışı `t`, görüntü olmayan klipte efekt | Render'da sessizce yanlış çıkmasın, hata Türkçe ve yerini söylesin |
| Ses | `ses: true` olan efekt (klipte `ses: false` yoksa) `olaysesi` rol olayı üretir: an `klip.bas + t`, `sure` hareket süresi, `tur` katalogdaki `rol`; `kurgu.olaylar_uret` çıktısına eklenir | Ajan ve kullanıcı ayrıca ses klibi koymaz; dosya seçimi `olaysesi.planla`'da kalır |
| Stüdyo | Klip panelinde "Hazır efekt" bölümü: oynatma kafasına ekle, parametre düzenle, sil, "Keyframe'e çevir" (`pisir`, kaydı siler); hepsi `duzenle` ile geri alınır | Bir iş tek yerde ([[0030-sade-arayuz\|ADR 0030]]) |
| Kurgu komutları | Bölmede efekt başladığı parçada kalır (anı yazılmamış çıkış efekti sağa geçer); baştan kırpma ve hız değişiminde `t` içerikle kayar | Efekt kesimden sonra yanlış yerde tekrar etmesin |
| Ajan isteği | `aiedit._hazir_katalogu` her çalışmada json'dan üretilir; kural: zoom ve vurgu için el keyframe'i değil `hazir` | İstek koddan sapmasın ([[0031-motion-grafik\|ADR 0031]] ile aynı kalıp) |
| Konuşmacı punch | `punches` sayı (eskisi gibi +%10) ya da nesne `{t, olcek, sure, x, y}`; odaklı punch ayrı katmanda kendi noktasına büyür | Her vurgu başka ölçek ve odak alabilsin; eski kurgular değişmez |

## Sonuçlar
- Python yalnız ad, aralık ve ses olayıyla ilgilenir; keyframe açılımı yoktur. Python ile TS arasındaki ortak kural (varsayılan `t` ve `sure`) iki yerde yazılıdır, testleri ikisini de sınar.
- "Keyframe'e çevir" el izi zaten animasyonluysa bileşimi yalnız keyframe anlarında örnekler; iki eğrinin arası yaklaşıktır (`hazirEfekt.ts` içinde not).
- Efekt kaldırılınca ya da çevrilince aynı izdeki sonraki kliplerin değişim sırası kayabilir; değeri yazılmış efekt etkilenmez.
- Klibin sonu kırpılıp `t` klip dışında kalırsa `kurgu.denetle` render'ı durdurur; kullanıcı efekti siler ya da taşır.
- Stüdyoda değeri yazılmamış parametre katalog varsayılanını gösterir; değişim listesinden gelen gerçek değeri göstermez.
- Bu ADR'a bağlı yeni eğriler (`geri`, `expo`, `yay`) `izdusum.ts` ve şemadadır. Şemadaki yeni geçiş türleri (`zoom`, `it`, `savur`, `bulanik`) `Kurgu.tsx` `Donusum` içinde çizilir ve Klip panelinden seçilir. Yalnız giren klip hareket eder, çıkan klibin kuyruğu altta sabit kalır. Yumuşak güçte susan rolün (`punch_in`) sesi açık hazır efektte duyulması için ses olayı `guc: orta` ile yazılır; klipteki `guc` bunu ezer.
- Doğrulandı 2026-11-12: Remotion kare render'ı (`remotion still`, 1080x1920) ile `odak_zoom` (işaret noktası 0. ve 25. karede aynı yerde, iki kat büyük) ve `punch` (merkezden 1,12); pytest 139, vitest 110, `tsc` 0 hata, `npm run build` geçti.

## İlgili kod
- `studio/remotion/hazirEfekt.json`, `studio/remotion/hazirEfekt.ts`, `studio/remotion/hazirEfekt.test.ts`
- `studio/remotion/Kurgu.tsx` (`Donusum`, `Konusmaci`), `studio/remotion/tipler.ts` (`Hazir`, `Punch`)
- `src/vedit/hazir_efekt.py`, `src/vedit/kurgu.py` (`denetle`, `olaylar_uret`), `src/vedit/aiedit.py` (`_hazir_katalogu`), `src/vedit/schemas.py` (`Klip.hazir`, `Punch`, `Donus.capa`, `Efekt.bulanik_kf`), `src/vedit/olaysesi.py` (rol olayı sözleşmesi)
- `studio/web/src/paneller/EfektPaneli.tsx` (`HazirEfektler`), `studio/web/src/zaman/komutlar.ts` (`hazirEkle`, `hazirYaz`, `hazirSil`, `hazirPisir`, `bol`)
- `tests/test_hazir_efekt.py`
