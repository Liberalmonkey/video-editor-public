---
type: overview
title: İşlem Günlüğü
tags: [meta]
created: 2026-10-20
updated: 2026-10-20
---

# İşlem Günlüğü

Sadece sona ekleme yapılır. Başlık formatı: `## [YYYY-MM-DD] <işlem> | <başlık>`
Son girdiler: `grep "^## \[" wiki/log.md | tail -5`
Bölünme: dosya 150 satırı aşınca en eski girdiler `log.partN.md` olarak arşivlenir, içerik eksilmez. Tüm girdiler: `grep -h "^## \[" wiki/log.part*.md wiki/log.md`
Arşiv: [[log.part1]] (2026-10-20 - 2026-11-03), [[log.part2]] (2026-11-03 - 2026-11-05), [[log.part3]] (2026-11-08 - 2026-11-12), [[log.part4]] (2026-11-12), [[log.part5]] (2026-11-13 - 2026-11-15), [[log.part6]] (2026-11-15 - 2026-11-17), [[log.part7]] (2026-11-18 - 2026-11-22)

## [2026-11-23] setup | HyperFrames 0.9.84
- `vedit hf-guncelle`: duman testi geçti, 0.9.80 → 0.9.84. Rapor `work/hf-aday/0.9.84/rapor.md`.

## [2026-11-23] code | HyperFrames güncellemesi haftalık ve işi bekler
- Sorun: `vedit-hf-guncelle` görevi (Pazartesi 10:00) `instagram/reel-video` ekip koşusunun G3 taslak render'ı sürerken 0.9.80 → 0.9.84 sabitledi; render düştü, `durum.json` G3'te asılı kaldı.
- `hf_guncel`: zamanlama Cuma 13:00 (`son_pencere`, `vakti_geldi`), Stüdyo zamanlayıcısı 10 dakikada bir `bir_tur`; `mesgul()` Stüdyo kuyruğunu ve `vedit`/ffmpeg/HyperFrames/Remotion süreçlerini tarar, iş varsa erteler; sabitleme öncesi `_bosta_bekle`, sırasında `kuruluyor.kilit` (kuyruk bekler), `deneme.kilit` çift denemeyi önler. CLI `--bekle DAKIKA`; görev betiği Cuma 13:00 + `--bekle 240` ile yeniden kaydedildi.
- `ekip_v3.calistir`: çökünce açık kapıyı `kaldi` yapar, `hata` ve `asama` yazar. Test `tests/test_hf_guncel.py`. Sayfa: [[0051-uctan-uca-hyperframes]].

## [2026-11-23] code | G5 kural adayı slotu rol sınıfına çevirir
- Sorun: `instagram/reel-video` ekip koşusu (medium) G5'te düştü: `ValidationError ... hedef_rol Input should be 'E1', 'E2', 'E3' or 'hepsi' [input_value='E4']`. QC bulgusunun `hedef`i slottu (medium'da ses-stil editörü E4), `kural.qc_isle` onu doğrudan `Kural.hedef_rol`'a yazıyordu; depo rol sınıfı (E1-E3) bekler. Low'da slotlar E1-E2 olduğu için görünmüyordu; test medium'u ve E3 üstü hedefi hiç denemiyordu.
- `ekip_v3`: `Atama.kural_rolu(slot, katman)` ve ortak `bulgu_sinifi`; G5 adayı rol sınıfıyla depoya işler, bulgunun slot hedefi G6 için değişmez. `kural.qc_isle`: geçersiz hedef `hepsi` olur, tek aday triyajı düşürmez.
- Test `tests/test_ekip.py`: seviyeli akışa `medium` ve ses-stil slotuna giden ikinci kural adayı; `test_slot_kural_rolu_ve_qc_isle`. Sayfa: [[0053-seviyeli-ekip-orkestrator]].

## [2026-11-23] code | Ekip max seviye dayanıklılığı
- Kayıtlı koşu çıktıları şemadan yeniden geçirildi: reel-video G2'de E3'ün kapı düzeltmesi `pano.0.metin:string_too_long` ile bütünüyle reddedilmiş, kapı yine "düzeltilen: E3" yazmıştı.
- `ekip_sema.Kirp`: serbest metin kırpılır, reddedilmez. `ekip.bulgu_dogrula` bulgu bulgu doğrular ve kimliği slota göre numaralar. G2 notu gerçek düzeltmeyi sayar. G5 triyajı çözümlenemezse aday depoya girmez. `hf_ad_ayir` paralel grafik editörlerinin kompozisyon adını ayırır. Pano kilitli ve atomik. `ajan_eszamanlilik` boş belleğe göre. `kurgu._atomik` Windows'ta `PermissionError`'da yeniden dener.
- `hf_kurgu.ayar` `hf_motor.json` yolunu çağrı anında çözer; `test_hf_onizleme_native_ve_sahne` tam pakette sıraya bağlı düşüyordu.
- Test `tests/test_ekip.py` (`test_max_dayaniklilik`, `test_triyaj_cozumlenemezse_aday_islenmez`, bulgu doğrulama). Sayfa: [[0053-seviyeli-ekip-orkestrator]].

## [2026-11-23] code | Ekip birleştirmesinde iz çakışması ve ekip rozeti
- Sorun: `instagram/reel-video` ekip koşusu (medium) G3'te düştü: `V3: e3hikaye01 ile e3bolum03 çakışıyor (34.830 sn)`. E1'in kesimi sonrası çapalar yeniden eşlenince E3'ün iki grafiği 0,11 sn üst üste bindi. Birleşen kurgu denetimden geçmeden diske yazıldığı için Stüdyo önizlemesi ve sonraki her edit aynı hatayla düşüyordu.
- `ekip_v3.iz_cakisma_coz`: `birlestir` sonunda aynı izdeki örtüşmeyi çözer (küçükse önceki klip kısalır, büyükse sonraki boş ya da yeni ize taşınır, sahibine bulgu). G3 denetimi geçmeyen birleşimi yazmaz; G6 bozuk düzeltmeyi düşürür. `aiedit._kurgu_hazirla` diskteki eski çakışmayı da onarır; reel-video kurgusu rev 101'de temizlendi.
- Üst rozet ekip koşusunda tek ajan seçimini (claude) gösteriyordu. İş kuyruğu ekip işine `motor: ekip` yazar; rozet çalışan slotları ekip durumundan okur. Slot kartı yedekte gerçek yedek motoru gösterir.
- Test `tests/test_ekip.py::test_iz_cakisma_coz_kirpar_ya_da_tasir`. Sayfa: [[0053-seviyeli-ekip-orkestrator]].

## [2026-11-23] code | Hızlı edit: yalın ajan çağrısı, QC paftası, koşullu orkestratör ve render
- Ölçüm (instagram/arvelior, medium): eski koşu 20,8 dk. Her ajan 269 araç, 15 MCP sunucusu, CLAUDE.md ve hook yüklüyordu; QC 53 kareyi tek tek okuyordu; G6 render'ı kullanılmıyordu.
- `motorlar.yalin_komut` + `ekip.ajan(metin=…)`: istem stdin'den, rol sistem isteminden, araç ve ayar kaynağı yok. Editör çağrısı 1 tur, ~12k token. `ekip.pafta_yap`: QC 12'lik paftalardan okur; metin girdileri ve `kurgu_ozeti` istemde.
- G2'de O yalnız ihlal varsa; G6'dan sonra render yalnız ikinci QC gerekince. `oto_duzelt` zoom yoğunluğunu ve kısa grafik süresini render'dan önce düzeltir. Bozuk iç içe alan öğeyi düşürmez.
- Yeni koşu (aynı istek, kopya proje): medium 13,4 dk. `--hizli` (low, orkestratörsüz) 15,3 dk: iki editöre yığılan iş G1 ve G6'yı uzattı. En büyük kalem hâlâ QC (agy, ~5 dk).
- Sayfalar: [[0054-hizli-edit]], [[0053-seviyeli-ekip-orkestrator]].

## [2026-11-23] code | Teslimde yayın metni
- İstek: Teslim sayfasında her video için platforma göre profesyonel başlık, açıklama ve hashtag. Varsayılan Claude Opus 5.5; Codex, Antigravity ve OpenCode da seçilebilir.
- `vedit yayin` (`src/vedit/yayin.py`): SRT'den kanıt paketi, ajan `work/yayin/<video>.json` yazar, vedit reçeteye göre doğrular (bir düzeltme turu), `yayin.md`'ye video başına işaretli blok yazar. Atıf bölümü ve elle yazılmış metin korunur.
- Reçete `library/yayin/platformlar.json` (reels, youtube, shorts, tiktok, linkedin; sınırlar 2026-11-23'te doğrulandı). Stüdyo Teslim alanında "Yayın metni" paneli: motor, model, seviye, platform, video başına üret, düzenle, kopyala, kaydet.
- Test `tests/test_yayin.py`, `YayinPaneli.test.ts`. Sayfa: [[0055-teslimde-yayin-metni]].

## [2026-11-23] code | Stillerim kart ızgarası
- Stillerim, Hazır stiller gibi kapaklı kart ızgarası; kapak katalog önizlemesi, ilk görsel referans ya da token paleti (`stil.kapak_yolu`, `/api/stil/{stüdyo}/{ad}/kapak`). Sayfa: [[0029-stil-paneli]].

## [2026-11-24] code | Kapak özelliği kaldırıldı
- `vedit kapak`, `teslim --kapak-kare`, Stüdyo Kapak alanı (Alt+4) ve `/api/kapak/*`, `export.covers`, `kapak-youtube` ve `kapak-instagram` skill'leri, `library/kapak/stiller/`, `rembg` extra'sı ve kapak testleri silindi.
- `library/kapak/sablon.html` `library/gorsel/sablon.html`'e, font tablosu `pano.FONTLAR`'a taşındı; `gorsel-uret` ve `vedit pano -o x.jpg` çalışmaya devam eder.
- Stil kartı önizlemesi (`stil.kapak_yolu`) kapak özelliği değildir, kaldı. Sayfalar: [[0056-kapak-kaldirildi]], [[0027-kapak-sayfasi]], [[0052-kapak-is-akisi-v2]] (superseded), [[video-studyo]].

## [2026-11-24] code | Her makinede hız
- Program monitörünün Remotion yolu tembel parça (`RemotionMonitor.tsx`); Vite preload yardımcısı, `lottie-web` ve `react-reconciler` doğru parçada: ilk yükte JS 2706 → 890 KB, FCP 696 → 474 ms.
- `vedit` CLI `project`'i tembel yükler (`import vedit.cli` 272 → 90 ms); kütüphane listesi oturumda bir kez iner; yoklamalar gizli pencerede durur.
- Ölü fonksiyonlar ve importlar silindi; `jsonschema` bağımlılığa eklendi (yalnız rembg dolaylı kuruyordu); rembg zinciri `.venv`'den kaldırıldı. Ölçüm aracı `scripts/hiz_olc.py`. Sayfa: [[0057-her-makinede-hiz]].

## [2026-11-25] code | Hızlı ve kaliteli edit
- Ölçüm (instagram/arvelior-swarm, 53 sn, aynı istek): `--ekip --hizli` 672 → 419 sn, kurgu-denetle uyarısı 1 → 0, slop 0, QC P0/P1 0/5. 240 sn hedefi tutmadı; kalite seçildi (G1 ~110, G6 ~150 sn kalıyor).
- Tema kilidi denetimi `tema_denetim.py` (ajan kompozisyonu ve şablon parametresi); Claude QC görselleri stream-json ile tek turda; QC render'ı 15 fps önbellekli; OCR en çok 5 sn; motion ön üretimi; G2 sert ihlal paralel.
- Hızlı modda QC zaman dilimine bölünür (G4 154 → 69 sn). Tekrar uyarıları klip id'si taşır, geçiş tekrarı kodla düzelir, G6 uyarı kapısı düzeltmenin doğurduğu uyarıyı sahibine bir kez yollar.
- E1'i low seviyede çalıştırmak kazanç getirmedi (G1'i E2 bekliyor), uygulanmadı. Sayfalar: [[0058-hizli-ve-kaliteli-edit]], [[0054-hizli-edit]].

## [2026-11-25] code | Swarm edit
- Sabit seviye tablosu ajan tavanına döndü: orkestratör tavan içinde ajan sayısını, kartları ve her ajanın motor/modelini seçer; kurgu editörü plana paralel başlar. CLI `--suru`, `--orkestrator`, `--en-cok`; `--ekip --seviye` çalışmaya devam eder.
- Stüdyo AI paneli "Tek ajan | Swarm": orkestratör modeli, en çok ajan, canlı kartlarda model.
- Ölçüm koşuları üç eski açığı gösterdi (id'siz yama öğesi, tek bozuk grafiğin G3'ü durdurması, `gecis_giris` kısa yazımı); üçü de düzeltildi. agy (Gemini 4 Neon) kod incelemesinin 12 bulgusu uygulandı.
- arvelior-swarm: eski medium 778 sn → swarm 692 sn, uyarı 2 = 2, slop 0. Sayfalar: [[0059-swarm-edit]], [[0053-seviyeli-ekip-orkestrator]] ve [[0054-hizli-edit]] (superseded).

## [2026-11-25] code | Proxy ve master conform
- `vekil.py`: ağır kaynağa (4K, HEVC, 10-bit, HDR, VFR, 50+ Mbps) önizleme ve taslak proxy'si; `vedit hazirla` paralel üretir, `vedit vekil` durumu gösterir. Taslak ve QC proxy'yi bağlar; final ve master orijinali bağlar, conform kapısı proxy sızıntısında durur.
- Master ön ayarı: kayıpsız 4:4:4 ara render, H.265 Main10, kaynağa eşle. Teslim zscale ile renk ve kroma dönüşümü yapar (dither'lı); SSIM/PSNR (isteğe bağlı VMAF) `work/renders/kalite.json`. Stüdyo Teslim paneli ön ayar, kaynağa eşle, proxy ve sadakat satırını gösterir.
- Sentetik 4K ölçüm: SSIM 0,9972, VMAF 97,54, 1/1 klip orijinal. 2160p ölçeği hâlâ Remotion'a düşüyor (sonraki iş). Sayfalar: [[0060-proxy-master-conform]], [[0035-teslim-ayarlari]].

## [2026-11-25] code | Kasa ve Keşif
- Hibrit kütüphane: Motion sekmesi Kasam (varsayılan) · Keşif (18 şablon + dış) · Arşiv (96, silinmez). Timeline'da sağ tık "Kütüphaneye kaydet" şablonu, kompozisyonu, bileşeni ve ses efektini niyetiyle `library/kasa/`'ya yazar; AI edit kataloğu önce Kasam'ı gösterir.
- Kilitli varlık 423 + "Kilidi kaldır ve sil" onayı; toplu silme; galeride kodla tanımlı öğe gizlenir.
- `onizleme.py`: alfa kaplamasıyla kare seçimi, sınır kutusuna kırpım, geçişte dama zemin; `vedit motion onizleme` 114 kaydı yeniledi (Zil, silme geçişi, şablonlar okunur). Sayfalar: [[0061-kasa-ve-kesif]], [[0012-kutuphane-kit]], [[0036-motion-kutuphanesi-ve-ajanlar]].

## [2026-11-25] code | Modern HyperFrames motion mimarisi ve 24 yeni şablon
- `studio/hf/` + `hf_grafik.py` + `app.py`: özel `hf` kompozisyonları çevrimdışı WebM olmadan doğrudan `data-composition-src` ile canlı gömülür; `data-sound-cues` `+1 kare` senkron SFX üretir; `HFN.yayCoz` ve `HFN.yonBulaniklik` eklendi.
- `tema_token.py`: `tema.css` v2 (`--*-rgb`, `--yuzey-cam`, `--kenar-ince`, `--yukselti-golge`, `--izgara-desen`, `--ease-enter/exit/emphasis/settle`). `stil_katalog.py` `hf_grafik.adlar()` tanır; 5 yeni referans stil (`saas-izgara`, `kod-hud`, `beyaz-tahta-pro`, `editoryal-belgesel`, `urun-lansman`, toplam 36 stil).
- `gecis.ts`, `zaman.ts`, `hazirEfekt.ts`, `ritim.py`: 4-düzen (`diyagram-pip`, `ekran-pip`), 2 sürekli-dünya kamera (`ekran_odak`, `dunya_kaydir`), 5 optik geçiş (`tikla_iris`, `buton_zoom`, `kart_dunyaya`, `bulanik_takas`, `dip_kesim`) ve `ritim.bpm_izgara()`.
- `library/motion/hf/`: 4 paralel yapım ajanıyla 6 ailede 24 yeni deterministik, Türkçe glifli, `16:9`/`9:16` uyumlu HyperFrames şablonu. `ekip_v3.py`, `kurgu_kalite.py`, `editor-grafik.md`, `ekip-orkestrator.md`: G0.5 Motion Brifi, komşu dilim hafızası, `YUZ_USTU_KART` ve determinizm kapısı. Test: `tests/test_hf_motion_kalite.py`. Sayfa: [[0062-modern-hyperframes-motion-mimarisi]].

## [2026-11-25] code | GSAP eklentileri, three.js 3D sahneler ve yönetmen katmanı
- `scripts/gsap_paketle.py` + `library/vendor/gsap/`: `gsap.min.js` artık çekirdek + SplitText, DrawSVG, MorphSVG, MotionPath, Physics2D, CustomEase ve tema eğrileri (`giris`, `cikis`, `vurgu`, `oturma`). ScrambleText, CustomWiggle, EasePack tohumsuz rastgele yüzünden alınmadı.
- `studio/hf/uc/uc.ts` → `library/vendor/uc.js` (`window.HFUC`): saydam WebGL, ışık, alfa koruyan seçici bloom, `hf-seek` sürücüsü, katmanlı ekstrüde yazı. `hf_grafik.canli_mi`, `kurgu.motion_bagla`, `paketle.ts`: 3D canlı gömülmez, önbellekli WebM. `kurgu_kalite`: `THREE.Clock`/`setAnimationLoop` kapısı, `UC_FAZLA`, `UC_ART_ARDA`.
- 22 yeni şablon (10 `uc-*`, 12 GSAP eklentili; 21'i agy paralel ajanlarıyla, Claude kare denetimiyle). Stil kataloğuna `motion_kisilik`, motion brifine beş bölüm ve iplik öğe, `editor-grafik` yeni aileler. Skill'ler: gsap-*, threejs-* (elle), `hf-gsap-uc`. Test: `tests/test_hf_uc.py`. Sayfa: [[0063-gsap-eklentileri-ve-threejs-hf]], [[2026-11-25-motion-kaynaklari]].

## [2026-11-26] code | Yaratıcı yön kapısı (G0.5), şablondan özerkliğe 1. adım
- Denetim: kurgu kararları sabit şablon eşlemesine (`aiedit.MOTION_KURALLARI`, `ekip_v3.paket`, `editor-grafik`), 4 sn yoğunluk kotasına ve zorunlu tariflere bağlıydı; videoya özgü yaratıcı fikir hiçbir yerde yazılmıyordu, `motion-brief.json` okunuyor ama yazılmıyordu. Sekiz adımlı plan onaylandı.
- `src/vedit/yaratici.py` + `ekip_sema.YaraticiBrif`: `work/edit/yaratici-brif.json` (tez, metafor, iplik, enerji eğrisi, imza anları, ses, riskler, yasak klişeler); gevşek şema, isteğe damga, `kilit`. Swarm'da plan çağrısında (`plan_paketi(brif_iste=)`), hızlıda E1'e paralel tek çağrı, tek ajanda kurgudan önce; brif bütün editör paketlerine girer. Test: `tests/test_yaratici.py`. Sayfa: [[0064-yaratici-yon]].

## [2026-11-26] code | Şablondan özerkliğe 2-7. adımlar (agy paralel ajanlarıyla)
- Dört agy ajanı paralel çalıştı (Hydrogen: `aiedit.py`+`kurgu.py`, `ekip_v3.py`+`ekip_sema.py`; Neon: ajan rolleri, skill'ler); Claude dosya kapsamını, farkı ve testleri denetledi. Sabit bileşen eşlemesi kaldırıldı, yoğunluk brifin enerji eğrisine bağlandı (`ENERJI_CARPAN`), zorunlu tarifler araç kutusuna çevrildi, editöre `oz_denetim`, QC'ye `etki` kategorisi ve `uretim_puani`, `ZORUNLU_EN_COK` 12 → 8. Kural deposunda 7 kopya/çatışan kural pasife alındı, K0063 ve K0064 birleşik kural eklendi (etkin 62 → 57). Test: `tests/test_enerji.py`, `tests/test_etki.py`, `tests/test_motion.py`. Sayfa: [[0064-yaratici-yon]].

## [2026-11-26] code | Müzik öncülü yapı (8. adım) ve yaratıcı yön pilotu
- `src/vedit/muzik_once.py`: parça editörlerden önce LLM çağrısı olmadan seçilir (brifin ses fikri, enerji, süre), ritmi bir kez ölçülür (`work/ritim-muzik/`, git dışı); tempo, 8 beatlik cümle başları ve enerji yükselişleri sözleşmeyle bütün editörlere gider. Test: `tests/test_muzik_once.py`.
- Pilot `instagram/pilot-yaratici` (videosuz test senaryosu, tek ajan; gerçek projeler diskte yok): brif somut, match cut ve iplik öğe karelerde doğrulandı. Önceden var olan iki kusur bulundu: canlı gömülen `kamera-crash-zoom` boş çıkıyor (P0), 47 HF şablonunun 46'sı 16:9 tanımlı ve 9:16'da küçük kalıyor (P1). Sayfa: [[0064-yaratici-yon]].

## [2026-11-26] code | HyperFrames canlı gömme düzeltmesi ve 46 şablonun dikey düzeni
- Kök neden: 42 şablon kökü `document.getElementById("root")` ile arıyordu; canlı gömmede null ya da yabancı kök dönüyordu (pilot doruğu boştu). Bileşenin kök kuralı sarmalı ezip yüksekliği sıfırlıyordu. 46 şablon 16:9 tanımlıydı, 9:16'da okunmuyordu.
- `hf_grafik.kok_sorgusu_cevir` + `paketle.ts`, kaplama kuralı, `hf_grafik.uret(sekans=)`, `hf_grafik.ayni_yon` (yönü uymayan şablon canlı değil sekans boyutunda WebM: `kurgu.motion_bagla`, `derle.ts`), `scripts/hf_dikey_kontak.py`, 9:16 katalogda `yalniz_yatay` süzgeci ve `HF_YALNIZ_YATAY` uyarısı, dikey kural kapısı testi. 46 şablonun dikey düzenini beş agy ajanı (Hydrogen, Neon) yazdı, Claude kontak sayfalarıyla denetledi. Sayfa: [[hf-canli-gomme-ve-dikey-duzen]].
