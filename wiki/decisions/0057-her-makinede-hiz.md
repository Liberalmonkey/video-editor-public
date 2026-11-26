---
type: decision
title: "Her makinede hız: tembel Remotion yolu, doğru parçalanmış JS, tembel CLI içe aktarması, ölü kod ve paket temizliği"
status: accepted
tags: [adr, hiz, studio, cli, bagimlilik, olcum]
created: 2026-11-24
updated: 2026-11-24
sources: ["[[0050-hyperframes-birincil-motor]]", "[[0051-uctan-uca-hyperframes]]", "[[0056-kapak-kaldirildi]]"]
---

# ADR 0057: Her makinede hız

## Bağlam
Kullanıcı uygulamanın her makinede hızlı olmasını istedi (2026-11-24). Şart: değişiklikten önce ölçülür, hiçbir özellik kaybolmaz, her metrik daha hızlı ya da eşit kalır.

Ölçüm makinesi: i5-11400H (6 çekirdek), 16 GB, GTX 1650. Ölçüm anında boş bellek 2,7-3,7 GB'tı. Ölçüm aracı `scripts/hiz_olc.py`; iki ölçüm `--karsilastir` ile tabloya döner.

## Bulgular
- **İlk yükte gereksiz 1,8 MB JS.** Önizleme HyperFrames'te olduğu hâlde `Monitorler.tsx` Remotion oynatıcısını ve kurgusunu statik içe aktarıyordu. Bu yüzden `remotion` (329 KB) ve `uc-boyut` (three.js, 781 KB) her açılışta iniyordu.
- **Vite yardımcısı yanlış parçada.** `manualChunks` yardımcıları hiçbir parçaya atamadığı için rollup Vite'ın preload yardımcısını `remotion` parçasına koymuştu. Giriş parçası tembel parçayı bu yüzden statik içe aktarıyordu.
- **Yanlış gruptaki paketler.** `kutuphane` parçasında yalnız tembel yolların kullandığı `lottie-web` (642 KB, `@remotion/lottie`) ve `react-reconciler` (595 KB, `@react-three/fiber`) vardı.
- **Çift oynatıcı.** Proje açılırken önizleme verisi gelene kadar önce Remotion oynatıcısı kuruluyor, sonra HyperFrames'e geçiliyordu.
- **Çift kütüphane isteği.** Altyazı paneli yalnız font listesi için 566 KB'lık `/api/kutuphane`'yi her açılışta ikinci kez çekiyordu.
- **CLI açılışı.** `cli.py` modül düzeyinde `project` içe aktarıyordu. `project` da pydantic şemalarını yüklüyor (~280 ms); `vedit --help` bile bunu bekliyordu.
- **Arka plan yoklamaları.** Pencere gizliyken de ekip durumu, ajan durumu ve proxy için 1,5-4 sn'lik yoklamalar sürüyordu.
- **Ölü kod.** Grep ve testle kanıtlananlar: `cut.map_time`, `galeri._gecici_proje`, `pano.geri_sarma_ayni_mi`, `project.copy_into`. Ayrıca kullanılmayan importlar vardı: `fizik.re`, `hizli.shutil`, `kurgu`'nun modül düzeyi `yuz_bolge`'si, `stil.motion`, `studio.kutuphane.hizli`.
- **Gizli bağımlılık.** `native_motion.param_hatalari` `jsonschema` kullanıyordu, ama paket pyproject'te yoktu; yalnız rembg (kapak extra'sı) dolaylı kuruyordu. `kur.bat` kapak extra'sını kurmadığı için temiz kurulumda native bileşen doğrulaması çalışmıyordu.
- **Zaten doğru olanlar.**
  - Whisper CUDA varsa GPU'da, yoksa CPU int8'de çalışıyor.
  - Stüdyo açılışı pencereyi importtan önce açıyor ([[0050-hyperframes-birincil-motor]]).
  - Render işçi sayısı boş belleğe göre seçiliyor. Eşikler ölçümle konmuştu, değiştirilmedi.
  - depcheck: Stüdyo'da kullanılmayan npm paketi yok.

## Karar
- `paneller/RemotionMonitor.tsx`: Remotion oynatıcısı ve kurgusu `React.lazy` ile yüklenir. Önizleme verisi gelene kadar "Önizleme hazırlanıyor" gösterilir. Motor seçildikten sonra yalnız seçilen oynatıcı kurulur. Oynatıcı ref'i kararlı geri çağrıyla bağlanır.
- `vite.config.ts`:
  - `preload-helper` ve `commonjsHelpers` `react` parçasına gider.
  - `@remotion/three`, `react-reconciler` ve yardımcıları `uc-boyut` parçasına gider.
  - `lottie-web` `remotion` parçasına gider.
- `api.kutuphaneAl`: kütüphane listesi oturumda bir kez iner. Kütüphane panelindeki her değişiklik listeyi tazeler.
- `yokla.ts`: yoklama pencere gizliyken istek atmaz, görünür olunca hemen bir kez okur.
- `cli.py`: `project = Tembel("vedit.project")`.
- Ölü kod ve kullanılmayan importlar silindi. `jsonschema` bağımlılıklara eklendi. Kapak zincirine özel paketler `.venv`'den kaldırıldı: rembg, pymatting, scikit-image, imageio, tifffile, networkx. `pip check` temiz.
- Değiştirilmeyenler:
  - Teslim kodlaması: x264 slow CRF 16 ([[0016-earshot-render-standardi-ajan-duzeni]]).
  - Render işçi eşikleri.
  - `/video`, OpenMontage ve reel_kit hatları: kullanıcı kararıyla yalnız kanıtla ölü kod silindi.

## Ölçüm (önce / sonra)
Arayüz metrikleri eski ve yeni derlemeyle dönüşümlü 10'ar tur ölçüldü (medyan, ilk tur ısınma). CLI ve sunucu metrikleri eski ve yeni Python koduyla 7 ve 5 tur ölçüldü.

| Metrik | Önce | Sonra | Fark |
|---|---|---|---|
| `import vedit.cli` | 272 ms | 90 ms | -67% |
| `vedit --help` | 328 ms | 164 ms | -50% |
| Stüdyo sunucu ilk yanıt | 876 ms | 894 ms | eşit (gürültü; süre FastAPI içe aktarmasında, ~480 ms) |
| İlk yükte JS | 2706 KB | 890 KB | -67% |
| İlk yükte istek | 20 | 17 | -15% |
| İlk boyama (FCP) | 696 ms | 474 ms | -32% |
| DOMContentLoaded (tek koşu) | 459 ms | 221 ms | -52% |
| Proje açma | 318 ms | 327 ms | eşit (gürültü, ±100 ms) |
| Önizleme hazır (HyperFrames `ready`) | 1514 ms | 1511 ms | eşit |
| Timeline kaydırma kare süresi p95 | 20,8 ms | 20,8 ms | eşit |
| Proje açılışında kütüphane JSON | 2 × 566 KB | 1 × 566 KB | -50% |
| Taslak render (53 sn video) | 81-188 sn | 86 sn | render kodu değişmedi; oynama boş bellekten (1-2 işçi) |

## Sonuçlar
- Remotion yolu (`motor: remotion` ya da derleyicinin desteklemediği özellik) aynı oynatıcıyı tembel parçadan açar. Doğrulandı: rozet Remotion, oynatma ilerliyor, konsolda hata yok.
- Yeni kurulumda `jsonschema` doğrudan kurulur.
- Render hızı ai-edit hızlandırması kapsamında ele alınır (değişmeyen render'ı atlamak, parçalı render).

## İlgili kod
`studio/web/src/paneller/Monitorler.tsx`, `studio/web/src/paneller/RemotionMonitor.tsx`, `studio/web/vite.config.ts`, `studio/web/src/api.ts`, `studio/web/src/yokla.ts`, `studio/web/src/paneller/AltyaziPaneli.tsx`, `studio/web/src/paneller/KutuphanePaneli.tsx`, `studio/web/src/paneller/AjanPaneli.tsx`, `studio/web/src/paneller/ai/EkipIlerleme.tsx`, `src/vedit/cli.py`, `pyproject.toml`, `scripts/hiz_olc.py`.
