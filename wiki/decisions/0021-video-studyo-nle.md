---
type: decision
title: "Video Stüdyo: yerel çok izli kurgu uygulaması"
status: accepted
tags: [adr, arayuz, remotion, timeline]
created: 2026-11-05
updated: 2026-11-05
sources: []
supersedes: "[[0020-panel-kaldirildi]] içindeki panel kararı"
---

# ADR: Video Stüdyo, yerel çok izli kurgu uygulaması

## Bağlam
Kullanıcı inputs, outputs ve kütüphaneyi yöneten, videoyu görerek editlemeyi sağlayan Premiere benzeri yerel bir uygulama istedi (2026-11-05). [[0020-panel-kaldirildi]] ile kaldırılan panel brif formu ve proje panosuydu, kurgu yapmıyordu. [[0017-terminal-hizli-hat]] agent'ı arayüzde çalıştırmayı yavaşlık nedeniyle kaldırmıştı; bu neden geçerlidir.

## Seçenekler
| Seçenek | Artıları | Eksileri |
|---|---|---|
| Hazır editör gömmek (OpenCut, designcombo, Twick) | Hızlı başlangıç | Yeniden yazımda timeline yok, klasik sürüm arşivde; lisans ve bulut anahtarı gerekir |
| Hatta bağlı görünüm (`kesim`, `props`, `olaylar`) | Az kod | Tek konuşmacı izi, serbest bindirme yok |
| Yeni `kurgu.json` + `Kurgu` kompozisyonu + kendi timeline | Tam çok izli, önizleme ile render aynı kod | En çok iş |

## Karar
- **Tam çok izli.** Kullanıcı seçti. `work/edit/kurgu.json` tek doğruluk kaynağıdır; varsa `sahne.mjs` çalışmaz, `olaylar.json` ondan üretilir. Yoksa SplitReel hattı aynen sürer.
- **AI terminalde kalır.** Kullanıcı seçti. Arayüz `vedit` adımlarını çalıştırır, yaratıcı editi agent `kurgu.json`'a yazar, arayüz izleyip yeniler. **Güncelleme 2026-11-08:** [[0026-arayuzde-ajan]] ile arayüz CLI ajanını (`claude -p`, `agy -p`) başlatabilir; ajan yine ayrı süreçte çalışır.
- **Tek render hattı.** `vedit final` kuyruğu (`olaysesi`, `teslim`, `denetim`) değişmez; yalnız görüntü motoru `Kurgu` olur.
- **Yığın.** Vite + React 18, dockview, `@remotion/player`, kendi canvas timeline; FastAPI + uvicorn, `send2trash`. Kabuk tarayıcı `--app` penceresi.
- **Sabitler.** Altyazı varsayılanı ADR 0014, render ADR 0016, denetim ADR 0015 aynen geçerlidir. Altyazı seçenekleri proje başına kullanıcı kararıdır, standart dışı stil rozetle görünür.

## Sonuçlar
- İkinci bir Remotion kurulumu (`studio/`): `openmontage/` git dışı, sürüm birebir 4.0.484. Webpack ve Vite takma adlarıyla tek kopya.
- `openmontage/remotion-composer/src/SplitReel.tsx` bileşenleri `export` edildi; bu klasör git dışı olduğu için temiz klonda elle gerekir.
- Terminal agent `kurgu.json` olan projede `sahne.mjs` ve `olaylar.json` yazmaz.

## Ölçüm (2026-11-05, 39,9 sn, 1080x1920, 30 fps, 12 çekirdek, GTX 1650)
Tek ölçümler, başsız Chrome. Gerçek pencere ve GPU ile sonraki aşamada yinelenecek.

| Konu | Sonuç |
|---|---|
| `Kurgu` ile SplitReel `ham.mp4`, aynı proje | SSIM 0,9988 (Y 0,9985) |
| Önizleme karesi ile render karesi | Gözle aynı, kesim iki tarafta kareye tam; SSIM 0,94-0,96, oynatıcı kontrolleri ve 521 px ekran görüntüsü dahil. 540p proxy tabanı 0,988 |
| Uzak sarma, proxy (`requestVideoFrameCallback`) | Medyan 48 ms, en çok 138 ms |
| Kesimde oynatma | 2,5 sn'de 73/75 kare, en uzun video boşluğu 112 ms |
| İlk `final` | motor 173 sn, ses 9 sn, teslim 57 sn, denetim 17 sn; SplitReel motoru 152 sn |

Kapı geçti, önizleme yöntemi değişmedi. mediabunny eklenmedi. Çok izli eşzamanlı video yükü ölçülmedi.

## 2. aşama: dosya sistemleri (2026-11-05)
- **Kabuk.** `dockview-react` 8.8.3 (`dockview` 8 paketinde React bileşeni yok). Yerleşim tarayıcıda saklanır, üst şeritten sıfırlanır.
- **Silme.** 1 GB'a kadar geri dönüşüm kutusu; üstü `Projeler/.cop/<zaman>/` altına taşınır. Neden: `send2trash` Windows'ta `FOFX_RECYCLEONDELETE` kullanır, kutuya sığmayan öğe sessizce kalıcı silinebilir. `.cop` elle boşaltılır.
- **Kilit.** `kit.json` `locked` varlık `zorla` ile de silinmez. Kit yuvası ya da projede kullanılan varlık önce uyarır; kullanım `kurgu.json` ve `olaylar.json` içinde metin aramasıyla bulunur.
- **SFX yükleme.** Mevcut `sfx.index` kullanılır: normalize, tepe, LUFS. Ham dosya `raw/kullanici/<lisans>/` altına gider, silmede ham dosya ve `source.json` kaydı da kalkar; yoksa sonraki `index` kaydı geri getirir.
- **Kullanıcı dosyası.** Medya yanıtları `CSP: sandbox` ve `nosniff` taşır, pano `sandbox allow-scripts` ile açılır: yüklenen HTML aynı kökten API'ye ulaşamaz.
- **İş kuyruğu.** Tek işçi, beyaz liste, argüman listesi. İptal `taskkill /T`: Remotion ve ffmpeg alt süreçleri de kapanır.
- **Yazı tipi.** Arayüz Inter; `impeccable` denetleyicisi "çok kullanılan font" uyarısı verdi, bilerek kaldı: araç arayüzünde tanıdık yazı işe yarar ve Inter zaten kütüphanede.

## 3. aşama: timeline çekirdeği (2026-11-05)
- **Komutlar saf.** `studio/web/src/zaman/komutlar.ts` immer taslağı üzerinde çalışır. Sürükleme önizlemesi aynı komutu geçici kopyada çalıştırır, bırakınca işlenir; oynatıcı sürüklerken yenilenmez.
- **Değişmez.** Aynı izde çakışma ve sıfır süre yok. 3000 rastgele komutluk test sınar.
- **Ripple kuralı.** Diğer izler kaydırılmaz, aynı zaman aralığı onlardan da çıkar ya da açılır: kesilebilir klip bölünür, sürekli içerik (müzik, sahne, metin, görsel) kısalır ya da uzar, aralıktaki SFX olayı gider. Yalnız kaydırmak, uzun klibin altına sonraki klibi sokardı.
- **Bağlı A/V.** Ayrı A1 izi yok: video klibi sesini kendi taşır, dalga formu klibin altında çizilir. Remotion görüntüyle birlikte render eder, A izleri `olaylar.json`'a gider. `bag` alanı klipleri birlikte seçtirip taşıtır.
- **Çakışma.** `rev` yetmez: agent dosyayı rev artırmadan yazabilir. `PUT` içerik özetini `If-Match` ile denetler, SSE dış yazımı bildirir. Bekleyen düzenleme yoksa arayüz yenilenir ve geri al geçmişi silinir; varsa kullanıcıya sorulur.
- **Kare hassasiyeti.** Önizleme bazı karelerde render'dan bir kare gerideydi: `currentTime` kare sınırına düşünce tarayıcı önceki kareyi gösteriyordu. Önizlemede yarım kare eklenir (`kirpBas`), render etkilenmez. Yedi karenin yedisi en iyi kendi karesiyle eşleşti; önce dördü `-1` ile eşleşiyordu.
- **Ses olayı.** `olaylar_uret` müziğe `start`, `in`, `dur` yazar: kırpılan müzik render'da da kırpılır.

| Ölçüm (başsız Chrome) | Sonuç |
|---|---|
| 500 klip, 4 iz, 15 dk, sığmış | Kare başına medyan 7 ms, p95 8,5 ms |
| 500 klip, yakın, kaydırırken | Medyan 6,9 ms, p95 8 ms |
| Düzenlenmiş kurguyla tam `final` | motor 155 sn, ses 8 sn, teslim 48 sn, denetim 18 sn; -14,3 LUFS |

## 4. aşama: efekt, altyazı, motion (2026-11-05)
- **Keyframe.** `donus.anim` sabit değerle animasyonu ayırır: kapalıysa tek değer, açıksa oynatma kafasına keyframe. Kesimde ve baş kırpmada uç değer korunur, animasyon sıçramaz.
- **Geri alma.** `duzenle(ad, f, birlestir)`: aynı alanda 700 ms içindeki değişiklikler tek adım; sürükleme geçmişi doldurmaz.
- **Geçiş.** Aynı izde çakışma yasak olduğu için çapraz ve kaydırma önceki klibin kuyruğunu `Sequence` süresini uzatarak altta sürdürür, kaynakta kalan kadar; ses de birlikte geçer. Kuyruk yoksa boşluğa açılır. Çıkış geçişi yalnız kararma.
- **Altyazı.** `stil` boşken SplitReel `Captions` çalışır: ADR 0014 kodda sabit kalır. Özel stil proje başınadır, rozetle görünür, SRT aynı sayfalamayı kullanır. Python ve TS sayfalaması `tests/sayfala_ornek.json` ile sınanır.
- **Sahne.** 8 tür form ve şablonla, kalan alanlar JSON. Eksik alan önizlemede kırmızı uyarı, render'da hata: bozuk sahne sessizce teslime gitmez.
- **Üst katman.** Metin ve motion aralığı boş en üst ize, yoksa yeni ize gider; konuşmacıyı ezmez. Sahne şablonu sahne izine yazar: o iz bitişik sahne düzenini taşır.
- **Pano.** Her zaman 1920x1080 render edilir, `work/public/pano/` altında aynı pano ve süre önbellekten gelir. Dikey sekansta sığdırılır. Şablonlar yatay sekansta uyarlanmadı.

## 5. aşama: ses ve teslim (2026-11-05)
- **Kesin olay.** Kaynaklı ses klibi `olaylar.json`'a `kesin: true` ile gider: yerinde, kırpımı ve fade'iyle çalar. `min_aralik` düşürmesi ve ±%3 perde uygulanmaz. Terminal hattının olayları eskisi gibi. Konuşma üstünde 4 dB geri çekilme iki hatta da geçerlidir ve önizlemede yoktur.
- **İçe alma.** Eski olay `t`'si sesin tepesiydi; klip artık sesin başladığı yerde durur (`_ses_basi`).
- **Doğrulama.** `instagram-reels-video` içe alındı, miks yeniden alındı: klipler eski miksin gerçek başlangıçlarına en çok 4 ms uzakta, loudness birebir aynı (-14,36 LUFS, LRA 1,5). Kesin olayda ±%3 perde uygulanmaz, bu bilinçli farktır.
- **Hız.** Ses izinde kaldırıldı: render ffmpeg miksidir, hızı uygulamaz.
- **Ölçüm.** Mikser sayıları `olaylar.rapor.json`'dan gelir, tahmin edilmez; kurgu sonradan değiştiyse "Eski" işareti çıkar. `vedit miks` görüntü render etmez. Canlı metre yok: önizleme tarayıcı sesidir, ducking ve loudnorm içermez, oradan sayı göstermek yanıltır.
- **Hüküm.** `hukum_ver`: P0 ya da eşik dışı ses YAYINLANAMAZ. Bu ölçüme dayalı alt kümedir; görsel rubrik `denetim` skill'indedir. Dosya final'de yazıldığı için arayüz engellemez, kararı `qa/onay.json`'a kaydeder.
- **Ön denetim.** `kurgu.denetle`: çakışma, eksik dosya, görselsiz sahne render'dan önce anlaşılır mesajla durur. Terminalden `vedit kurgu-denetle`.

## 6. aşama: çalışma alanları ve sağlamlık (2026-11-05)
- **Çalışma alanları.** Kurgu, Ses, Altyazı, Teslim; her alanın yerleşimi ayrı saklanır, oynatma karesi korunur.
  > [!note] Güncellendi 2026-11-12
  > Alanlar artık Kurgu, Teslim, Kütüphane; Ses ve Altyazı sağ paneldeki sekmeler. Bkz. [[0030-sade-arayuz]].
- **Panel koruması.** Hata tek panelde kalır, "Yeniden dene" var. Kaynak dosyası silinen klip timeline'da kırmızı "Dosya yok" görünür, önizleme düşmez, render `kurgu.denetle` ile durur.
- **Boş proje.** Timeline en az 30 sn ölçekle açılır, ilk klipte sığar. Önceden en yüksek zoom'da açılıp ilk klibi ekran dışında bırakıyordu; yalnız yeni proje yolculuğu testi gösterdi.
- **Erişilebilirlik.** axe taraması (WCAG 2 A, AA) üç çalışma durumunda: ciddi ihlal yalnız dockview sekmesinde `nested-interactive` (kapatma düğmesi sekme içinde). Kütüphane yapısı, değiştirilmedi. Timeline canvas'tır, ekran okuyucuya klip düzeyinde açık değildir; klavye kısayollarıyla kullanılır.

| Yük (gerçek pencere, GTX 1650; 15 dk 1080x1920, 461 klip, 2500 kelime, kurgu.json 519 KB) | Sonuç |
|---|---|
| Proxy üretimi | 136 sn (1,01 GB → 101 MB) |
| Kurgu açılışı | 1,44 sn |
| Çizim, kafa ve kaydırma | Kare başına medyan 6,9 ms, p95 8 ms |
| Uzak sarma, ilk kare | Medyan 147 ms, en çok 229 ms; 15 ölçümün biri zaman aşımı |
| 12 sn oynatma, 3 sn'de bir kesim, üst iz | 358/360 kare, en uzun duraklama 202 ms |
| Düzenleme, geri alma, kaydetme | 8,6 ms, 0,8 ms, 147 ms |
| 10 sn aralıklı taslak render | 44 sn |

Test videosu yapay desendir. Gerçek çekimin kodeği, yüksek bit hızı ve çok kameralı izler bu sayıları kötüleştirebilir. 15 dk tam `final` çalıştırılmadı; süreyi ölçek veriyor: 40 sn için motor 155 sn.

## Açılış (2026-11-09)
Uygulama `studio.vbs` ya da masaüstü kısayoluyla terminal penceresi göstermeden açılır; çıktı `%TEMP%\vedit-studio-log.txt`. Edge/Chrome porta özel ayrı profille başlar, pencere kapanınca sunucu da kapanır. `studio.bat` terminalden açmak için kalır.

## İlgili kod
`src/vedit/kurgu.py`, `src/vedit/schemas.py`, `src/vedit/hizli.py`, `src/vedit/studio/`, `studio/`, [[video-studyo]]
