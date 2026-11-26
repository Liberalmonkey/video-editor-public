---
type: overview
title: İşlem Günlüğü, bölüm 7 (2026-11-18 - 2026-11-22)
tags: [meta]
created: 2026-11-18
updated: 2026-11-22
---

# İşlem Günlüğü, bölüm 7

Arşiv: 2026-11-18 - 2026-11-22. Değiştirilmez; yeni girdi [[log]] sonuna eklenir.

## [2026-11-18] code | Stil silme, hazır stil kataloğu, videoya göre motion teması
- Stil panelinde çöp kutusu: paket, referanslar ve projedeki seçim birlikte silinir (`stil.sil`, `DELETE /api/stil/{s}/{ad}`). [[0042-stil-katalogu-ve-video-temasi]]
- "Hazır stiller" sekmesi: OpenMontage, huashu-art-motion, bang-motion ve tema kütüphanesinden 31 stil (anime, çizgi film, modern motion, editoryal, kurumsal, sinematik, retro, sanat akımı); `library/stiller/katalog.json`, `vedit stil-katalog liste|kur|ekle`.
- Turuncu kalktı: sabit motion klipleri render anında etkin temayla yeniden üretilir; tema sırası açık tema > stil > `vedit tema-cikar` proje teması > varsayilan. Açık turuncu `turuncu` teması.
- Doğrulandı: pytest (yeni `test_tema`, `test_stil_katalog`), arayüz tip denetimi, üç klip iki temada render edilip karede renk değişimi görüldü.

## [2026-11-19] code | Stile bağlı tema token'ları (ADR 0043)
- [[0043-stile-bagli-tema-tokenlari]]: katalog kartı tek kaynak; `tema_token.py` 31 stil için CSS + JSON yazar (renk, font, şekil, hareket, altyazı), kontrast ölçülür. `piksel-8bit` kendi teması (Pixelify Sans, VT323 rakam, köşe 0, sert gölge, 8 fps adım, piksel raster); `editoryal-acik` kanonik ad.
- Bağlanan yollar: `MotionMetin.tsx`, `Kurgu.tsx`, `FizikSahne.tsx`, SplitReel (`temaUygula`), motion HTML (yedek renk ve Montserrat kalktı), panolar (`vedit pano --tema`), Stüdyo önizlemesi. Paketten tema: `paket-ugc-ornek-marka`.
- Altyazı: stil seçiliyse stilin token'ı, değilse ADR 0014 (ADR 0014'e not). `kurgu-denetle` STIL_DISI_RENK; ai-edit klip rengi yazdırmaz.
- Doğrulandı: `tests/test_tema_token.py`, `tests/test_sabit_renk.py`, tüm pytest, arayüz tip denetimi; üç şablon iki stilde render edilip karede karşılaştırıldı.


## [2026-11-19] code | Ekip motoru, ikonlar, motion denetimi (ADR 0044)
- [[0044-ekip-motoru]]: `vedit ai-edit --ekip`; E1 kesim önce, E2 grafik ve E3 ses/stil paralel, K1-K3 salt okunur denetler, P0/P1 kalmayınca durur; yanıt vermeyen denetçinin bulgusu açık kalır. Stüdyo AI panelinde Ekip modu (6 slot, ön ayar, canlı durum, hepsini durdur).
- İkonlar arka şekilsiz yeniden çizildi (`tests/test_ikon_alfa.py`); `motion-denetci` (agy, 3 paralel görev) 114 kaydı denetledi: 14 P0 ve 10 P1 düzeltildi, 6 P1 açık (`work/agy/motion-denetim/`). Stil kartları `vedit stil-katalog kart`.
- `instagram/1` ekiple iki stilde editlendi: `piksel-8bit` 3 tur, 15 bulgu kapandı, 2 P1 açık; `temiz-kurumsal` 3 tur, kota bitince (agy 429, Claude 5 saat sınırı) K2/K3 son turlarda çalışmadı. Karşılaştırma `work/edit/karsilastirma-piksel-vs-temiz.jpg`.

## [2026-11-20] code | Native motion, varlık içe aktarma, kural deposu, ekip motoru v2 (ADR 0045-0049)
- [[0045-native-motion]]: 55 native Remotion bileşeni tema token'ına bağlı. Native karşılığı onaylanan HTML kayıtları `library/motion/arsiv/`'e taşındı (Stüdyo Arşiv sekmesi), AI edit onları seçmez, eski kurgular render olur. [[0046-dis-varlik-ve-lisans]]: `vedit motion ice-al`, lisans zorunlu. [[0047-kural-deposu]]: `library/kurallar/kurallar.json`, Kurallar sayfası, mezar taşı. [[0049-yapim-ekibi]]: yapım ekibi kartları.
- [[0048-ekip-motoru-v2]]: sözleşme, paralel E1-E3, deterministik birleştirme, tek QC, tek düzeltme. `instagram/1` iki stilde yalnız native setle yeniden editlendi. Token v1'e göre %50 (`temiz-kurumsal`) ve %70 (`piksel-8bit`) az. Duvar saati 7836 sn yerine 1108 sn, 5481 sn yerine 849 sn.
- Ölçüm koşularında bulunan birleştirme kusurları kapatıldı. Tek bozuk öğe artık bütün katmanı düşürmüyor. `bas` ve `sure` çapadan ya da meta'dan geliyor. Sekans V1 ile bitiyor. İkon başladığı çekimi aşmıyor. Sözleşme kelime dizinlerini taşıyor. Native yerleşim klip boyunca görünen yüzlere bakıyor.
- Açık bulgu: yakın planda konfeti yüze biniyor (`temiz-kurumsal` 36 sn).

## [2026-11-22] decision | HyperFrames birincil motor (ADR 0050)
- [[0050-hyperframes-birincil-motor]]: kullanıcı karma geçişi seçti. Yeni grafik, animasyon ve sahne HyperFrames kompozisyonu; timeline ve gerçek çekim birleştirmesi Remotion'da kalır.
- Dağıtım izni olmayan üçüncü taraf sanat yönetimi skill'i ve bütün izleri kullanıcı kararıyla silindi (log ve `raw/` dahil); yerine kendi `sanat-yonetimi` skill'imiz.

## [2026-11-22] code | HyperFrames 0.9.77, hf klibi, Stüdyo hızlı açılış
- `hyperframes` 0.9.77, upstream `hyperframes`, `hyperframes-cli`, `hyperframes-registry`, `remotion-to-hyperframes` skill'leri; eski parçalı set silindi. Telemetri proje env'inde kapalı.
- Yeni: `src/vedit/hf_grafik.py`, `vedit hf liste|kur`, klipte `hf: {ad, param, tema}`, `library/motion/hf/SOZLESME.md`, `library/motion/hf/alt-bant/`. Test: `tests/test_hf_grafik.py`. Saydam webm, değişken ve Türkçe glif render karesinde doğrulandı.
- Stüdyo: `src/vedit/studio/baslat.py` (erken soket, pencere hemen), `src/vedit/tembel.py`, tek Python süreçli `studio.bat`, tembel paneller ve kütüphane parçaları, `ff.probe_ob`. Sunucu ilk isteğe yaklaşık 0,9 sn'de yanıt veriyor; soğuk açılış ölçülmedi.

## [2026-11-22] setup | HyperFrames 0.9.78
- `vedit hf-guncelle`: duman testi geçti, 0.9.77 → 0.9.78. Rapor `work/hf-aday/0.9.78/rapor.md`.

## [2026-11-22] decision | Uçtan uca HyperFrames (ADR 0051)
- [[0051-uctan-uca-hyperframes]]: kullanıcı edit, motion ve stilin tamamen HyperFrames'e geçmesini, Remotion'un son çare kalmasını ve güncellemelerin otomatik + duman testiyle alınmasını istedi; geçiş çift motorlu ve aşamalı.

## [2026-11-22] code | HyperFrames güncelleme sistemi ve derleyici iskeleti
- `vedit hf-guncelle` (`src/vedit/hf_guncel.py`), `tests/hf_duman/`, `/api/hf/durum`, Stüdyo `HF` rozeti, `scripts/hf_guncelle_gorev.ps1`. İlk canlı koşu 0.9.77 → 0.9.78, duman farkı 0,0.
- `studio/hf/derle.ts`, `calisma.ts`, `cli.ts`, `zaman.ts`; `src/vedit/hf_kurgu.py` motor seçimi; kurguda `motor` alanı; taslak, final ve parçalı render seçimle. Test: `studio/hf/derle.test.ts`, `tests/test_hf_guncel.py`.
- `instagram/1` 9-14 sn: HyperFrames ve Remotion kareleri aynı; hız kapısı kapalı (5 sn için 78 sn).

## [2026-11-22] code | HyperFrames hız kapısı, altyazı ve orta noktalı geçişler (ADR 0051)
- Derleyiciye `olcek` (taslak yarım ölçek) ve `pencere` (aralık ve parça render'ında yalnız pencereye değen klipler). Tam taslak 132 sn (Remotion 101), 5 sn aralık 87 sn'den 34 sn'ye; `library/hf_motor.json` `oto_hf: true`.
- `studio/hf/altyazi.ts` (ADR 0014/0043) ve `studio/hf/gecis.ts` (12 orta noktalı geçiş). `instagram/1` karelerinde iki motor eşleşti. Testler `studio/hf/derle.test.ts`.

## [2026-11-22] code | HyperFrames React adası: metin grafikleri ve sahneler (ADR 0051)
- `studio/hf/ada.tsx` (ayrı paket `hf/ada.js`, yalnız ada varsa yüklenir) ve `studio/hf/remotion-taklit.tsx`: `MotionMetin` türleri ve SplitReel sahneleri aynı React bileşenleriyle, Remotion'un kare bağlamı taklit edilerek her karede `flushSync` ile çizilir. Saf yardımcılar gerçek `remotion` paketinden.
- Bölünmüş düzen: `layoutP` (`studio/hf/zaman.ts`), konuşmacı paneli, altyazı konumu (`altyaziKonum`). `desteklenmeyen` listesinden metin, görsel vurgu ve sahneler çıktı; fizik ve karakter kaldı.
- `instagram/reel-video` motoru artık HyperFrames. 0-4,6 sn ve sentetik sahne testinde (stat bölünmüş, text, hook) kareler Remotion'la aynı; video karesi en çok bir kaynak karesi (24 fps kaynak) farklı.

## [2026-11-22] code | Native motion bileşenleri HyperFrames'te (ADR 0051)
- 60 native bileşen `library/motion/hf/<aile>-<ad>/sahne.html` olarak taşındı; çekirdek `studio/hf/native/cekirdek.ts` (`window.HFN`), `akisHesapla` (`studio/remotion/motion/cekirdek/zaman.ts`). Derleyici yerleşimi seçip sahneyi alt kompozisyon olarak bağlar; `desteklenmeyen` yalnız taşınmamış bileşeni listeler.
- Doğrulama aracı `scripts/hf_native_karsilastir.py` (gruplu, sıralı, kalıcı sonuç, `--eksik`, `--onayla`); 60/60 geçti. Testler `tests/test_hf_native.py`, `studio/hf/derle.test.ts`.
- `instagram/1` motoru HyperFrames. agy betiğine kota/limit yedeği eklendi (Neon, sonra Sonnet 5.5).

## [2026-11-22] code | Stüdyo önizlemesi HyperFrames oynatıcısında (ADR 0051)
- Program monitörü `<hyperframes-player>`; derleyici tarayıcıda (`studio/web/src/zaman/hfOnizleme.ts`), oynatıcı soyutlaması motor bağımsız (`zaman/oynatici.ts`), motor rozeti. Paketler `studio/hf/paketle.ts` (render ve `npm run build` ortak).
- Sunucu: `/api/hf/onizleme`, `/hfs/...` sahne kopyası, önizleme `tema.css`, kurgu yanıtında yüz bölgeleri. `ses.kf` HyperFrames ses zarfıyla. React adasında SplitReel font yükleyicisi taklitle değişti (404 veriyordu).
- Doğrulama: instagram/1 ve reel-video Stüdyo'da HyperFrames'le; oynatma, kare adımı, yeniden derlemede konum korunması, yerleşim render'la aynı. Testler `tests/test_studio_kurgu_api.py`, `studio/hf/derle.test.ts`.

## [2026-11-22] code | Motion ve stil bölümleri HyperFrames'te (ADR 0051)
- Motion kayıtları (`library/motion/custom`) `vedit hf_motion` ile üretilir: kayıt HTML'i değişmeden HyperFrames projesine sarılır, CSS animasyonları WAAPI'ye çevrilip tek sürücüyle zamanlanır (adımlı zaman, `son_tam`, piksel stil korunur). 35 etkin kayıt Playwright çıktısıyla birebir (`scripts/hf_motion_karsilastir.py`, `work/hf-motion/sonuc.json`).
- `vedit motion kontak` HyperFrames sahne bağlamaları ve `hyperframes snapshot` ile (`studio/hf/kontak.ts`); Galeri tema kartı ve stil kataloğu önizlemeleri HyperFrames'ten. Tema kartının düzeni kapsayıcıya taşındı.
- `tema-cikar` tam token yazar (JSON + `css_metni`); eskiden 5 renk yazıyor, öteki değişkenler turuncu yedeğe düşüyordu. motion-tasarimci, E2 ve ai-edit yeni grafiği HyperFrames kompozisyonu olarak ister.
- Bulunan tuzaklar: HyperFrames `CSSAnimation`'ı kendi saatiyle sürer; `getKeyframes()` örtük uç kareyi açık kareye çevirir; `"İ".lower()` iki karakterdir.

## [2026-11-22] code | Fizik ve karakter ön render; uçtan uca HyperFrames belgeleri (ADR 0051)
- `hf_kurgu.on_render`: fizik/karakter klibi Remotion'da saydam webm'e alınıp HyperFrames'e video klibi olarak gömülür (önbellekli). Stüdyo önizlemesi bu projelerde Remotion. Test `studio/hf/derle.test.ts`.
- Göreli çıktı yolu hatası: `hf.render`, `hf.render_saydam` ve `hizli._remotion` yolları mutlak yapar (araçlar kendi klasöründe çalışıyordu).
- CLAUDE.md, `uretim-hatti`, `sahne-motoru`, `motion-design`, motion-tasarimci, motion-gelistirici, E2 ve ai-edit güncellendi.

## [2026-11-22] setup | HyperFrames 0.9.80
- `vedit hf-guncelle`: duman testi geçti, 0.9.78 → 0.9.80. Rapor `work/hf-aday/0.9.80/rapor.md`.

## [2026-11-22] code | Kapak iş akışı v2 (ADR 0052)
- Stüdyo Kapak alanı 5 adım oldu: Video, Fikir ve prompt, Üret, Düzelt, Master prompt ve teslim (`studio/web/src/paneller/kapak/`).
- `kapak_prompt.py`: yapılı brief, agy zemin prompt'u, altı platform için yazılı ve boş zemin master prompt'u. `kapak.py`: video seçimi, elle kare, yüz ve stil referansı, `gelistir`, `gorsel_duzelt` (kırmızı kutu ve geri yapıştırma), `ice_al`, `master`; teslimde master prompt dosyası.
- `gorsel.agy` model, efor ve zaman aşımı alır; `gorsel.kota` görsel modelini ve kota açılışını loglardan okur. agy görsel modeli seçtirmez (`gemini-3.1-flash-image`).
- Testler: `test_kapak_prompt.py`, `test_kapak_v2.py`, iş kuyruğu ve API uçları, `yardimci.test.ts`. Sayfalar: [[0052-kapak-is-akisi-v2]], [[2026-11-22-kapak-arastirmasi-v2]], [[0027-kapak-sayfasi]], [[video-studyo]].

## [2026-11-22] code | Seviyeli ekip, orkestratör ve sade AI paneli (ADR 0053)
- Ekip v3 (`ekip_v3.py`): seviye ajan sayısını belirler (low 2+1 … max 10+5), orkestratör kartları dağıtır, kapılar G0-G7 paralel işi bağlar. Kural kapısı `kural_uyum`'u ve deterministik denetimi ölçer, triyaj QC kural adayını depoya işleyip doğrular.
- Eski turlu motor (`--ekip-v1`), 6 slot şeması, Bölüş ve Tur kaldırıldı; `library/ekip.json` ve eski proje ayarları gruplara göçer. `zaman_araliklari` kısa videoda sıfır uzunlukta dilim üretmiyor.
- Stüdyo AI paneli Edit/Sohbet sekmeli: seviye segmenti, katlanır ekip ayarları, kapı adımları ve ajan kartları (`studio/web/src/paneller/ai/`). `/cikti/{slot}` v2'den beri boş dönen dosya düzeni düzeltildi.
- Rol dosyaları: yeni `ekip-orkestrator`, `kk-genel`, `kk-kural`, `kk-izleyici`; editör ve QC rolleri görev kartına göre güncellendi.
- Sayfalar: [[0053-seviyeli-ekip-orkestrator]], [[0048-ekip-motoru-v2]] (superseded).

## [2026-11-22] code | HyperFrames render işçisi boş belleğe göre
- `hf_kurgu.isci_sec`: boş RAM 3 GB altında 1, 6 GB altında 2 işçi, üstünde otomatik (4). Açık `isci` ve `VEDIT_HF_ISCI` kazanır. Render satırı seçilen işçiyi ve boş belleği yazar.
- Neden: `instagram/1` ekip koşusu (low) G3 taslak render'ında bellek doldu ve Claude Code arka plan işini öldürdü (15,8 GB makine). Test `tests/test_hf_kurgu.py`. Sayfa: [[0053-seviyeli-ekip-orkestrator]].
