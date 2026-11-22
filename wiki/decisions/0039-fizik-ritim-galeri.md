---
type: decision
title: "Fizik ve karakter sahnesi, ritim ve senkron ölçümü, fizik sezgisi kuralları ve Stüdyo galerisi"
status: accepted
tags: [adr, fizik, 3d, ritim, senkron, viseme, karakter, galeri, tema, motion, ai-edit, antigravity]
created: 2026-11-16
updated: 2026-11-16
sources: ["[[2026-11-16-fizik-stil-repolari]]"]
---

# ADR: Fizik, ritim, karakter ve galeri

## Bağlam
Kullanıcı 2026-11-16'da istedi: yapay zekâ söylenmeden içeriği anlasın ve kurguda uygulasın. Düşen ya da yuvarlanan top, hızlanan araba gibi fizik olayları; ışık, ses ve görüntü özellikleri doğru olsun; tasarlattığı animasyon karakterle yapılan videolarda ses ile görüntü kaymasın; çok farklı video stili ve motion seçeneğini bir arada görebilsin. On repo verdi (bkz. kaynak sayfası). Karakter hem Flow/Veo klibi hem kodla çizilen karakter olabilir; galeri Stüdyo içinde olacak (kullanıcı kararı). Alt ajanlar Antigravity CLI ile.

## Seçenekler
- Fiziği Remotion içinde gerçek zamanlı koşturmak (react-three-rapier `<Physics>`). Remotion kareleri sırasız ve paralel çizer; kare n her seferinde farklı çıkar.
- Her fizik olayını elle keyframe ile canlandırmak. Ajan yerçekimini, sekmeyi ve temas anını tutturamaz; "yapay" görüntünün ana kaynağı budur.
- Simülasyonu bir kez, sabit adımla Node'da bake etmek; Remotion yalnız okur. Seçilen.

## Karar
| Konu | Karar | Neden |
|---|---|---|
| Fizik sahnesi | `tur: "sahne"`, `sahne.kind: "fizik"`, `preset`, `param`, `isik.preset`, `olcum`. Yedi preset: `top-dusme`, `yuvarlanma`, `araba-ivme`, `domino`, `sarkac`, `firlatma`, `kule-cokus` (`studio/remotion/fizik/presetler.json`) | Anlatıda en sık geçen fiziksel olaylar; mecazlar da (domino etkisi, çöküş, gaza basmak) |
| Bake | `studio/remotion/fizik/bake.mjs`: @dimforge/rapier3d-compat 0.19.0, kare başına 4 alt adım, sürekli çarpışma (CCD). Çıktı kare kare konum ve dönüş, temas anları (kare, gövde çifti, çarpma hızı, güç), kamera yolu ve ölçüm. `vedit` bunu `work/public/fizik/<preset>-<özet>.json` yazar, klibin kaynağına bağlar (`fizik.bagla`, `motion_bagla` kalıbı) | Aynı girdi her zaman aynı kare: önizleme ile render aynı, testle sabitlendi. Özet bake betiği, katalog, parametre ve tema değişince değişir |
| Araç | Araba kinematik kapalı formla sürülür (v = a·t, en yüksek hızda sabit; süspansiyon sönümlü yay), tekerlek dönmesi yola kilitli; çarptığı dubalar Rapier'de | Araç fiziği motor çarpıştırıcısıyla kararsızdır (araştırma notu); çarpışmanın kendisi gerçek kalır |
| Çizim | `FizikSahne.tsx`: @remotion/three `ThreeCanvas`, `preserveDrawingBuffer`, gölge, sis, Bloom + Vignette + ACES ToneMapping. Noise ve uyarlanır ToneMapping kullanılmaz. Hız izi: hızlı gövdede yarım kare içinde 3 hayalet (180° obtüratör). Topta temas karesinde ezilme, sert temasta kamera sarsıntısı aynı karede | Paralel render'da titreyen efektler dışarıda; alt-kare `tmix` render'ı 4-8 kat uzatırdı |
| Işık | Altı preset (`studyo`, `gun-isigi`, `gun-batimi`, `neon`, `sinematik`, `laboratuvar`): yön, şiddet, ortam, renk sıcaklığı (Kelvin), bloom, vinyet, gölge sertliği. Gökyüzü ve sis ışık rengini taşır, vurgu rengi ışık yayar | Işığın içeriğe göre seçilmesi; tek anahtar ışık, tek gölge yönü |
| Renk | Fizik sahnesi paleti ve yazı tipi kurgunun motion temasından gelir | Fizik sahnesi videonun geri kalanıyla aynı dilde |
| Temas sesi | `fizik.ses_olaylari`: temas sekans zamanına taşınır, hafif temas `tik`, orta ve sert `vurgu` rol olayı; sahne başına en çok 8 darbe (0,1 sn aralık), en çok 2 sert, tık zinciri en çok 24 | Çarpma sesi temas karesine kendiliğinden oturur; kule çöküşünün 60 teması gürültü olmaz |
| WebGL | Kurguda fizik sahnesi varsa render `--gl=angle` ile | Headless Chrome'un varsayılan GL'i Windows'ta three.js'i çizmeyebilir; 2B kurguların render'ı değişmez |
| Ritim | `vedit ritim` (`ritim.py`, librosa 1.0.1): konuşma ve müzikte onset (5,8 ms çözünürlük), beat, tempo ve vurgu anları, kaynaktan sekans zamanına izdüşüm, `work/edit/ritim.json`. ai-edit isteğine özet ve kurallar girer | Ajan sesi duyamaz; kesim, punch ve olay sesi ölçülmüş anlara oturur |
| Senkron | `vedit senkron [--uygula]` (`senkron.py`): ses onset zarfı ile görüntü hareket başlangıcının çapraz ilişkisi, ±12 kare. Genel hareket zayıfsa YuNet yüz tespitinin ağız köşelerinden ağız bölgesi ölçülür. Ağız ölçümünde 0-110 ms "ses geç" doğaldır (dudak sesten önce açılır), düzeltilmez. Belirsiz ölçüm uygulanmaz; `--uygula` aynı bağdaki ayrık sesin `giris`ini kaydırır | Flow/Veo kliplerinde ses kayabiliyor; doğal dudak öncülüğünü kusur saymak yapay sonuç verirdi |
| Viseme | `vedit viseme` (`viseme.py`): sekans karesi başına K, U, A, E, O; enerji ve spektral ağırlık merkezi, ağız bir kare önden açılır, en az iki kare tutulur | Ücretsiz ve kurulumsuz; açılma zamanı sesle birebir |
| Karakter | `sahne.kind: "karakter"`, `library/karakter/<ad>/karakter.json` (renk, oran). `Karakter.tsx`: SVG düzenek, nefes, tohumlu göz kırpma, sesle açılan ağız, vurguda baş sallama, gövde 2, kol 3 kare geriden (takip), iki kol farklı fazda. `karakter.bagla` klip aralığının viseme ve vurgu verisini kaynağa bağlar | Kodla karakterde dudak senkronu ölçümden gelir, elle zamanlanmaz |
| Fizik sezgisi | `.claude/skills/fizik-sezgisi/` (SKILL.md + `references/kurallar.md`); ai-edit kural listesinde; istekte fizik ve karakter kataloğu | Kullanıcı istemeden uygulanacak kurallar tek yerde |
| Hazır efekt | `giris_dus` (yerçekimiyle düşüş, e² ile alçalan sekmeler, ilk temas sürenin %45'i), `carp_zoom` (hazırlıklı çarpma zoom'u), `giris_carp` (ağır iniş). Katalogda `ses_an` ve `ses_kare`: ses efekt başında değil temas anında | [[0033-hazir-efektler|ADR 0033]] çerçevesinde fizik doğru giriş |
| Temalar | On yeni tema (`kinetik-ui`, `altin-fintech`, `murekkep-zen`, `piksel-16bit`, `termal-kizilotesi`, `gravur-el-yazmasi`, `analitik-uzay`, `xray-sema`, `seramik-mozaik`, `golge-kukla`); yazı/zemin kontrastı en az 13:1, vurgu/zemin en az 3,7:1. Tema `--font` ile kütüphanedeki her yazı tipini seçebilir (`pano.kutuphane_fontlari`); EB Garamond ve Fraunces eklendi (OFL) | Kayıt sayfaları yalnız Montserrat tanımlıyordu, tema fontu sessizce yedeğe düşüyordu |
| Geçişler | Sekiz yeni kayıt: `gecis-crt-kapanis`, `gecis-firca-darbesi`, `gecis-pencere`, `gecis-piksel-cozunme` (dikey ve yatay). Motion kütüphanesi 94 → 102 | pixelfx, ClaudeAnimationBase ve shotcraft fikirlerinden, kod kendi yazımımız |
| Galeri | Stüdyo Kütüphane > Galeri: stil paketi, tema, fizik, ışık, karakter, motion ve hazır efekt tek ızgarada; üstüne gelince oynatma, tür çipleri, arama, en çok 4 seçeneği yan yana karşılaştırma, türüne göre tek eylem (oynatma kafasına ekle, proje teması yap, projeye stil seç, seçili fizik sahnesine ışık, seçili klibe efekt). `GET /api/galeri`, `POST /api/sahne-bagla/{stüdyo}/{ad}`. Önizlemeler `vedit galeri kur` ile `library/galeri/` altına; fizik, ışık ve karakter tek Remotion render'ında çizilip ffmpeg ile parçalanır | Kullanıcı seçenekleri yan yana görmek istedi; önizleme başına ayrı paketleme dakikalar sürerdi |
| Dış repolar | Kod ve metin kopyası yalnız izinli lisansta: `library/vendor/video-shotcraft` (Apache-2.0, `references/` ve `assets/lib`), `ClaudeAnimationBase` (MIT), `pixelfx` (MIT, yazı tipi hariç). npm/pip paketleri: three, fiber, postprocessing, @remotion/three, rapier3d-compat, librosa. react-three-rapier kurulmadı: motoru (rapier3d-compat) doğrudan kullanılır. opus-video-prompts, awesome-opus5-5-videos ve lemo-opuscar (CC BY-NC) yalnız fikir | Ticari kullanımda telif ve lisans riski taşıyan dosya depoda durmaz |
| Alt ajanlar | Araştırma: agy orkestrası (3 `motion-arastirmaci` + Orchestrator birleştirme). Üretim: agy paralel (tema yazımı; `motion-tasarimci` ile 8 geçiş, `--onizle`). Çekirdek kod ana oturumda Claude. Her agy iddiası yeniden ölçüldü (kontrast, `vedit motion olc`, kontak sayfası) | [[0037-antigravity-orkestra|ADR 0037]]; alt ajan çıktısı veridir |

## Sonuçlar
- Fizik sahnesi render'ı WebGL ister; ilk kare paketleme dahil 30-45 sn sürer. Bake 0,1-0,7 sn.
- Senkron ölçümü kamera sabitken güvenilirdir; kamera hareketli klipte genel hareket sesle ilişkisiz çıkabilir ve rapor "belirsiz" der. Üç Flow avatar klibinde ağız ölçümü +2/+3 kare verdi (doğal aralıkta).
- Viseme fonem tanımaz: A/E/O ayrımı yaklaşıktır, açılıp kapanma zamanı kesindir. Daha doğrusu gerekirse Rhubarb Lip Sync (MIT) kullanıcı onayıyla eklenir.
- Kodla karakter iki örnekle gelir; kullanıcının tasarlattığı karakter görseli şimdilik SVG düzeneğe çevrilmez (renk ve oranla yaklaşılır).
- Galeri önizlemeleri kütüphane düzeyindedir; yeni preset ya da tema eklenince `vedit galeri kur` çalıştırılır.

## İlgili kod
- `studio/remotion/fizik/{bake.mjs,presetler.json,FizikSahne.tsx,fizik.test.ts}`, `studio/remotion/karakter/Karakter.tsx`, `studio/remotion/Kurgu.tsx`, `studio/remotion/hazirEfekt.{json,ts}`
- `src/vedit/{fizik,karakter,ritim,senkron,viseme,galeri}.py`, `src/vedit/kurgu.py` (`hazirla`, `denetle`, `olaylar_uret`), `src/vedit/aiedit.py` (`_ritim_bolumu`, kataloglar), `src/vedit/hizli.py` (`_remotion` GL bayrağı), `src/vedit/pano.py` (`kutuphane_fontlari`), `src/vedit/hazir_efekt.py` (`ses_an`), `src/vedit/cli.py` (`ritim`, `senkron`, `viseme`, `galeri`)
- `src/vedit/studio/galeri.py`, `studio/web/src/paneller/GaleriPaneli.tsx`, `KutuphanePaneli.tsx`
- `library/motion/tema/`, `library/motion/custom/gecis-{crt-kapanis,firca-darbesi,pencere,piksel-cozunme}-{dikey,yatay}/`, `library/karakter/`, `library/galeri/`, `library/fonts/`, `library/vendor/{video-shotcraft,ClaudeAnimationBase,pixelfx}/`
- `.claude/skills/fizik-sezgisi/`, `tests/test_senkron.py`, `tests/test_fizik.py`
