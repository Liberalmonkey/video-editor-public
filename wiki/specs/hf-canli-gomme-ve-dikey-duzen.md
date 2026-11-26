---
type: spec
title: HyperFrames canlı gömme düzeltmesi ve dikey (9:16) düzen
tags: [hyperframes, motion, reels, kalite, render]
created: 2026-11-26
updated: 2026-11-26
sources: ["[[0064-yaratici-yon]]"]
status: done
---

# HyperFrames canlı gömme düzeltmesi ve dikey (9:16) düzen

## Problem
2026-11-26 yaratıcı yön pilotunda ([[0064-yaratici-yon]]) Reels taslağında iki kalite kaybı görüldü:
1. **P0, canlı gömmede bozuk bileşen:** `kamera-crash-zoom` (videonun doruğu, "0 HATA") taslakta tamamen boş çıktı. Aynı bileşenin WebM'i doğru çiziliyor.
   - Kök neden: kütüphanedeki 42 kompozisyon kök öğeyi `document.getElementById("root")` ile arıyor. Canlı gömmede (`paketle.ts grafikKopyasi`, `hf_grafik._sablon_sar`) kök kimliği klibe özgü bir adla değişiyor, ama betikteki bu sorgu değişmiyor.
   - Sorgu ya `null` döner ve betik çöker (zaman çizelgesi kaydedilmez, bileşen görünmez), ya da sayfadaki başka bir `root` öğesini yakalar ve yanlış öğeleri canlandırır.
   - Aynı sorun `window.__HF_PARAM.main` okumasında da var: parametre ana kompozisyonun alanından okunuyor.
2. **P1, dikeyde küçük grafik:** 47 kompozisyonun 46'sı 1920×1080 tanımlı.
   - Ölçüler `cqw`/`cqmin` birimleri ve 1920 genişliğe göre konmuş piksel tavanlarıyla (`clamp(…, 74px)`) yazılmış. 9:16'da içerik ortada küçük, yatay bir kutu olarak kalıyor ve okunmuyor.
   - WebM yolu (`hf_grafik.uret`) kompozisyonu sekans boyutunda değil, kendi 16:9 boyutunda üretiyor. Bu yol üç boyutlu (`uc-*`) ve `"canli": false` bileşenlerde kullanılıyor.
   - `library/motion/hf/SOZLESME.md` 11. madde iki oranı da şart koşuyor.

## Kullanıcı hikâyeleri
- Reels editinde seçilen her HyperFrames grafiği taslakta ve finalde görünür, doğru öğeyi canlandırır ve 9:16 karede okunur.
- 16:9 YouTube editinde mevcut görünüm değişmez.

## Kapsam
- **A. Canlı gömme (P0):** `grafikKopyasi` ve `_sablon_sar` betikteki kök sorgularını (`document.getElementById("root")`, `document.querySelector("#root")`) klibin kök öğesine (`__kok`), `__HF_PARAM.main` okumasını klibin parametresine çevirir. İki uygulama birebir aynı kalır.
  - Kütüphane şablonlarına dokunmadan 42 şablonun hepsi düzelir.
  - Test: Python dönüşüm testi ve pilot taslağın yeniden render'ı.
- **B. WebM boyutu:** `hf_grafik.uret(..., sekans=(w, h))` kompozisyonu sekans boyutunda üretir. Önbellek adı boyutu içerir. Çağıranlar sekansı verir: `kurgu.motion_bagla` ve `ekip_v3.OnUretim`.
- **C. Doğrulama aracı:** `scripts/hf_dikey_kontak.py <ad...>` her kompozisyonu 1080×1920 ve 1920×1080'de render eder, üç kareyi (%30, %60, %90) yan yana kontak sayfasına koyar (`work/hf-dikey/<ad>.jpg`).
- **D. Dikey düzen (P1, agy paralel alt ajanları):** her aile için kompozisyona dikey kural eklenir (`@container (max-aspect-ratio: 1/1)` ya da JS'te `w < h` dalı).
  - Dikeyde ana öğe karenin genişliğinin en az %70'ini kullanır, yazı 1080 genişlikte en az 42 px olur, öğeler gerekiyorsa alt alta dizilir.
  - Güvenli alan korunur: alt %22 altyazıya ayrılır, üst %10 ve sağ sütun %14 platform arayüzüne.
  - Yatay görünüm birebir korunur.
  - Aileler: akış ve arayüz; tipografi; veri; derinlik, efekt, geçiş, kamera, kapanış, kart ve ritim; `uc-*` (three.js kamera oranı).
- **E. Kapı:** yeni kompozisyonda `getElementById("root")` hâlâ çalışır (A çevirir), ama `hf_determinizm_hatalari` dikey kuralı olmayan kompozisyonu uyarır. Bu kapı D bittikten sonra açılır.

## Tasarım
- A, B, C ve E'yi Claude yazar; küçük ve çekirdek değişikliklerdir.
- D'yi aileye göre bölünmüş beş agy alt ajanı paralel yapar (Gemini Hydrogen ve Neon). Her ajan yalnız kendi kompozisyon klasörlerine yazar, C aracıyla kendi kontak sayfalarını üretir ve bakar.
- Claude her kontak sayfasını açıp kabul ya da red verir. Reddedilen kompozisyon gerekçeyle aynı ajana geri döner, en çok bir tur.
- Kilitli varlık kuralı: `library/kit.json` `locked` listesindeki kompozisyona dokunulmaz.

## Kabul kriterleri
- Pilot taslağın (`instagram/pilot-yaratici`) yeniden render'ında 25,8–28,3 sn "0 HATA" görünür. 2,8, 12 ve 22 saniyelerdeki bileşenler doğru öğeyi canlandırır.
- Her kompozisyonun dikey kontak sayfasında yazı okunur, ana öğe geniş, taşma ve güvenli alan ihlali yok. Yatay kontak sayfası değişiklik öncesiyle aynı görünür.
- `vedit kontrol` geçer.

## Açık sorular
- `uc-*` sahnelerinde dikey kamera kadrajı her sahnede anlamlı mı? Anlamsız olan sahne dikeyde `kart` meta'sıyla "yalnız yatay" işaretlenir ve katalogda dikey sekansta gösterilmez.

## Sonuç (2026-11-26)
- **A:** `hf_grafik.kok_sorgusu_cevir` ve `paketle.ts grafikKopyasi` kök ve parametre okumalarını klibe çeviriyor. Ayrıca bileşenin kendi kök kuralı sarmalın kaplama kuralını ezip yüksekliği sıfırlıyordu; kaplama kuralı artık stillerden sonra `!important` ile geliyor.
- **B ve canlı gömme kuralı:** canlı gömmede şablon kökünün ve dış kutunun aynı kimliği taşıması gibi çalışma zamanı farkları dikey düzeni yarım bırakıyordu. Bu yüzden kural şöyle değişti: kompozisyon sekansla aynı yönde değilse canlı gömülmez. Sekans boyutunda WebM'i kullanılır; bu WebM kontak render'ıyla birebir aynıdır. Kural `hf_grafik.ayni_yon`, `kurgu.motion_bagla` ve `derle.ts` içinde aynı. Aynı yönde (16:9 YouTube) canlı gömme sürüyor.
- **C:** `scripts/hf_dikey_kontak.py` (`--etiket`, `--hepsi`, `--yalniz-dikey`).
- **D:** beş agy aile ajanı paralel çalıştı (Hydrogen ve Neon). 46 kompozisyonun hepsi dikey kural aldı, `yalniz_yatay` işaretlenen yok.
  - D3 bir saatlik süre sınırına takıldı, ama dosyaları tamamdı.
  - Claude 46 kontak sayfasını yeniden üretip denetledi. Yatay görünüm farkı 45 kompozisyonda ≤ 0,5 (gürültü düzeyi); `uc-parcacik-kelime` 3,5, yalnız parçacık dağılımı. Red turu gerekmedi.
- **E:** `test_yatay_kompozisyonun_dikey_kurali_var` kapısı ve 9:16 katalogda `yalniz_yatay` süzgeci; kullanılırsa `HF_YALNIZ_YATAY` uyarısı.
- **Pilot:** `instagram/pilot-yaratici` taslağında 4,2, 13,5, 23,5 ve 26,6. saniyelerdeki grafikler artık kareyi dolduruyor ve okunuyor; "0 HATA" doruğu görünüyor. `vedit kontrol` geçti.

