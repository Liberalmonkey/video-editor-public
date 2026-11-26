---
type: decision
title: "0064 · Yaratıcı yön kapısı (G0.5) ve şablondan özerkliğe geçiş"
tags: [ai-edit, swarm, yaraticilik, kurgu, motion, kalite]
status: accepted
created: 2026-11-26
updated: 2026-11-26
sources: []
---

# ADR 0064: Yaratıcı yön kapısı (G0.5) ve şablondan özerkliğe geçiş

## Bağlam
2026-11-26 denetiminde kurgu kararlarının üç yerde sabit tarife bağlandığı görüldü:
1. **Sabit "anlatı hiyerarşisi":** `aiedit.MOTION_KURALLARI`, `ekip_v3.paket` ve `editor-grafik` aynı eşlemeyi taşıyor: hook kinetik başlık, bölüm kapsül başlık, metrik rozet, zirve vurgu sözü, kapanış CTA kartı. Sonuç olarak her video aynı gramerle çıkıyordu.
2. **4 saniyelik yoğunluk kotası:** grafik seyrek kalınca ek tur açılıyor ve "grafik ekle" deniyordu.
3. **Zorunlu tarifler:** her bölümde SFX, her konuşan kafada `el_kamerasi`, her tipografi zirvesinde `odak_karart`.

Bunlara ek olarak videoya özgü bir yaratıcı fikir hiçbir yerde yazılmıyordu. G0 planı yalnız iş bölümü yapıyordu. `motion-brief.json` okunuyordu ama hiçbir adım onu yazmıyordu. Kalite kontrol yalnız kusur arıyor, "doğru ama sıradan" olan kurguyu yakalayamıyordu.

Kullanıcı ajanlardan şablon yerine içeriğe göre yaratıcı karar, öz eleştiri ve modern üretim değeri istedi. Yükseltme sekiz adımda, onaylı planla tek tek yapılır. Bu ADR ilk adımı kaydeder; sonraki adımlar buraya eklenir.

## Seçenekler
- **Kuralları gevşetmek:** tekdüzeliği azaltır ama fikir üretmez.
- **Ayrı bir yönetmen ajanı çağrısı:** her koşuya ek bir seri bekleme getirir.
- **Brifi mevcut çağrılara gömmek:** swarm'da plan çağrısına, hızlıda E1'e paralel tek kısa çağrıya, tek ajanda kurgu öncesi ilk işe. Seçilen budur.

## Karar
- **Brif dosyası:** `work/edit/yaratici-brif.json` (`ekip_sema.YaraticiBrif`) sekiz alan taşır: tez, görsel metafor, iplik öğe, enerji eğrisi (1–5), 1–3 imza anı (söze çapalı), ses fikri, bilinçli riskler, yasak klişeler.
- **Şema gevşektir:** bilinmeyen alan ve fazla öğe brifi düşürmez. Brif yalnız tez boşsa ya da enerji aralık dışındaysa geçersizdir. Brif yoksa ya da geçersizse edit bugünkü gibi sürer; brif edit'i hiçbir zaman durdurmaz.
- **Yeniden kullanım:** brif yazıldığı isteğe damgalanır (`istek`). Aynı istekle yeni koşu brifi yeniden kullanır, istek değişince brif yenilenir. Kullanıcı `"kilit": true` koyarsa brif hiç üzerine yazılmaz.
- **Swarm:** brif yoksa orkestratör onu plan JSON'unun `yaratici_brif` alanında, aynı çağrıda yazar. Plan bu alanı sözlük olarak taşır, brif ayrıca doğrulanır; biri bozuk olsa öteki düşmez.
- **Hızlı (`--hizli`):** brif yoksa orkestratör slotunda tek kısa çağrıyla yazılır. Bu çağrı E1 çalışırken yapılır; öteki editörler onu bekler.
- **Tek ajan (`vedit ai-edit`):** istem, kurgudan önce brifi yazmasını ister. vedit brifi doğrular ve damgalar (`yaratici.damgala`). Aralık düzeltmesinde yeni brif yazılmaz, var olan brif gösterilir.
- **Editör paketi:** brif bütün editörlere "Yaratıcı brif" bölümüyle gider. Editör kararlarını brife bağlar, aralığına düşen imza anını teslim eder ve raporda hangi brif maddesini taşıdığını yazar. P0 kuralları brifin üstündedir.
- **Bilinen sınır:** E1 plana paralel başladığı için ilk turda yalnız önceden var olan brifi görür; düzeltme turları yeni brifi görür.
- **Skill:** uzun biçim `yaratici-yon` skill'indedir. İstem skill'in gövdesini okur, skill yoksa `yaratici.KISA_KILAVUZ` kullanılır.

## Sonuçlar
- Her video bir fikir etrafında kurulur, dilim editörleri aynı enerji eğrisini ve iplik öğeyi izler.
- Swarm'da ek çağrı yoktur. Hızlı modda brif yalnız ilk koşuda tek kısa çağrıdır; ölçüm adım 1 pilotunda yapılır, gerileme %15'i geçerse hız kapısının arkasına alınır.
- Sonraki adımlar (şablon eşlemesinin kaldırılması, kotadan enerji eğrisine geçiş, editör rollerinin ilkeye çevrilmesi, kural deposu bakımı, QC etki ekseni, skill tazeleme, müzik öncülü yapı) brifi girdi olarak kullanır.

## Adım 2–7 (2026-11-26, agy paralel ajanlarıyla, Claude denetimiyle)
- **Şablon eşlemesi kaldırıldı:** `aiedit.MOTION_KURALLARI`, `ekip_v3.paket` ve `editor-grafik` artık bileşen adı şart koşmuyor. Seçim işleve (göster, karşılaştır, kanıtla, vurgula, geçiş, kapat), katalogdaki "Ne zaman" satırına ve brife dayanıyor. `_hf_katalogu` kompozisyonları tür ya da aile başlığıyla grupluyor. İkon %30 sınırı, yüz/ürün/altyazı koruması, tek hero, tema kilidi ve 3D sınırı aynen kaldı.
- **Kotadan enerji eğrisine:** `kurgu.motion_yogunlugu(k, hedef, enerji=None)` grafiksiz aralık eşiğini dilimin enerji seviyesine göre ölçekliyor (`ENERJI_CARPAN` = 1: ×2.0, 2: ×1.5, 3: ×1.0, 4: ×0.85, 5: ×0.7). Ortalama uyarısı ağırlıklı hedefe bakıyor. Seyreklik turu "söze bağlı grafik ekle ya da sakin bölümü raporda gerekçelendir; dolgu grafik koyma" diyor. Brif yoksa davranış birebir eskisi.
- **Tariften araç kutusuna:** her bölümde SFX, her konuşan kafada `el_kamerasi`+`hizli_zoom`, zirvede `odak_karart` ve hook'ta `kinetik-baslik` zorunlulukları "ne zaman işe yarar" diline çevrildi. Kurgu editörüne yaratıcı yetki verildi: match cut, speed ramp, J/L cut, pattern interrupt, sessizlik+vuruş; dilim başına en az bir bilinçli karar ve gerekçe. Geçişte %90 düz kesim ve en çok 2–3 aile ilkesi geçerli; stilin `gecis`/`kacin` listesi bağlayıcı.
- **Öz denetim ve etki ekseni:**
  - `Yama.oz_denetim` editörün imza anını nasıl teslim ettiğini, en zayıf anını ve taşıdığı brif maddesini taşır.
  - `Bulgu.kategori` artık `etki` değerini alır.
  - `KontrolCikti.uretim_puani` beş eksen taşır: hook, imza_ani, brif_uyumu, ozgunluk, ritim_enerji; değerler 1–5'e kırpılır, bozuk puan çıktıyı düşürmez.
  - QC istemi taslağı brife karşı okur. Triyaj `etki` bulgusunu zaman, kare kanıtı ve brif maddesine bağlıysa kabul eder.
  - Koşu özeti ve raporu QC puan ortalamasını taşır.
- **Kural yükü:** `ZORUNLU_EN_COK` 12'den 8'e indi (P0 her zaman girer). Kural deposunda kopya ve çatışan kurallar pasife alındı, silinmedi: K0036, K0043, K0058 birleşik K0063'e; K0039, K0054 birleşik K0064'e; K0038 K0035'in, K0046 K0028'in kopyası. Etkin kural 62'den 57'ye indi. Geri almak için `vedit kural ac <id>`.
- **Rol ve skill metinleri:**
  - Editör ve QC rolleri (`editor-*`, `kk-izleyici`, `kk-gorsel`, `kk-kurgu`, `kk-genel`) ve `ekip-orkestrator` (G0.5 ve etki triyajı) güncellendi.
  - Skill'ler: `denetim` rubriği 12 madde (özgünlük, brif uyumu); `usta-editor` "Modern kurgu dili" ve altyazı standardı düzeltmesi; `viral-kurgu` imza anı sorusu; `motion-design` "Fikir önce"; `sound-design` "Ses fikri". Sabit sayılar "başlangıç değeri; brif kazanır" diye etiketlendi.
## Adım 8: müzik öncülü yapı (2026-11-26)
- `src/vedit/muzik_once.py`: parça editörlerden önce, LLM çağrısı olmadan seçilir. Seçim, manifest'teki ruh hâli ve tür kelimelerinin brifin `ses`/`tez`/`metafor` alanlarıyla ve kullanıcı isteğiyle örtüşmesine, enerji yakınlığına (brifin süreye göre ağırlıklı enerjisi) ve sürenin yetmesine göre puanlanır.
- Parçanın ritmi `ritim.analiz` ile bir kez ölçülür. Önbellek projeler arasında paylaşılır: `work/ritim-muzik/`, git dışı.
- Harita `work/edit/muzik-once.json` dosyasına yazılır: tempo, her 8 beat'te bir cümle başı, enerji yükselişleri ve manifest'teki yapı notu. Swarm'da sözleşmenin `muzik_once` alanıyla ve "Müzik öncülü" bölümüyle bütün editörlere, tek ajanda istemin ritim bölümünden sonra gider.
- Müzik editörü başka parça seçebilir, ama raporda gerekçesini yazar. Kesim, bölüm geçişi ve imza anı mümkünse cümle başına ya da yükselişe oturur. Söz ve anlatı müziğin önündedir.
- Hata ya da boş kütüphane durumunda adım atlanır, edit sürer. Aralık düzeltmesinde müzik yeniden seçilmez. Test: `tests/test_muzik_once.py`.

## Pilot (2026-11-26)
`instagram/arvelior-hiz` ve öteki gerçek projeler diskte yok (`Projeler/` 2026-11-25'te boşaltılmış). Bu yüzden pilot, videosuz bir test senaryosuyla tek ajan yolunda yapıldı: `instagram/pilot-yaratici`. Senaryodaki sayılar test verisidir, teslim edilmez. `--hizli` ve swarm videosuz projeyi desteklemiyor ("Kurguda görüntü klibi yok").

Sonuç: 9 dk, 28 klip, 40 sn taslak, 0 kurgu hatası.
- **Brif:** somut ve videoya özgü. Tez, kart üçlüsü metaforu ve iplik öğesi var. Enerji eğrisi 5-3-2-4-5-3 biçiminde: bir nefes ve bir doruk içeriyor. Üç imza anı yazıldı, yasak klişeler listelendi.
- **Karelerde doğrulanan:**
  - 6. saniyede işaretsiz kartlar 30,7. saniyede işaretli dönüyor (match cut ve iplik öğe).
  - 9,4–11,6 sn nefes anı var.
  - Hook'ta sonuç ilk saniyede veriliyor.
  - Geçiş ailesi üç ile sınırlı.

Pilotta bulunan, bu ADR'dan önce de var olan iki kusur var:
1. **P0, canlı gömmede boş doruk:** `kamera-crash-zoom` HyperFrames motoruyla canlı gömülünce 25,8–28,3 sn tamamen boş çıkıyor. Aynı bileşenin önceden üretilmiş WebM'i "0 HATA"yı doğru çiziyor.
2. **P1, dikey sekansta küçük grafik:** kütüphanedeki 47 HyperFrames kompozisyonunun 46'sı 1920×1080 tanımlı. 9:16 sekansta canlı gömmede okunmayacak kadar küçük kalıyorlar. `SOZLESME.md` 11. madde iki oranı da şart koşuyor.

Bu iki kusur HyperFrames gömme hattı ve şablon düzeni işidir. Ayrı bir plan gerektirir.

## İlgili kod

## İlgili kod
- `src/vedit/yaratici.py`: okuma, yazma, damgalama, istem bölümleri.
- `src/vedit/ekip_sema.py`: `YaraticiBrif`, `EnerjiDilimi`, `ImzaAni`, `Plan.yaratici_brif`.
- `src/vedit/ekip_v3.py`: `plan_paketi(brif_iste=)`, `paket`, `_akis_govde` G0.5, `_stil_ozeti`.
- `src/vedit/aiedit.py`: `_istek_yaz` Yaratıcı Yön bölümü, `calistir` damgalama.
- `tests/test_yaratici.py`.
