---
type: decision
title: "Panel kaldırıldı, terminal hattı ve ölçülmüş hız değişiklikleri"
status: accepted
tags: [adr, arayuz, hiz, render]
created: 2026-11-05
updated: 2026-11-15
sources: []
supersedes: "[[0019-arayuz-ve-efekt-motoru-birlesimi]] içindeki panel kararları"
---

# ADR: Panel kaldırıldı, terminal hattı ve ölçülmüş hız değişiklikleri

> [!note] Güncellendi 2026-11-15
> Silindiği yazan `kur.bat` sıfırdan kurulum için geri geldi. `vedit taslak|final` artık `work/edit/kurgu.json` varsa onu `Kurgu` kompozisyonuyla render eder; `sahne.mjs` yalnız kurgu yokken çalışır ([[0021-video-studyo-nle]]).

> [!note] Güncellendi 2026-11-05
> Kullanıcı aynı gün görerek kurgu yapılan çok izli bir uygulama istedi: [[0021-video-studyo-nle]]. Hız ölçümleri ve terminal hattı geçerlidir.

## Bağlam
Kullanıcı paneli denedi ve istemedi (2026-11-05). İstenen akış: her şey `Projeler/inputs/<stüdyo>/<proje>/` altına konur, editlenmiş video `Projeler/outputs/<stüdyo>/<proje>/` altından alınır. Kullanıcı ayrıca editin projeye zarar vermeden hızlanmasını istedi.

## Seçenekler
| Seçenek | Artıları | Eksileri |
|---|---|---|
| Paneli isteğe bağlı bırakmak | Kod durur | Kullanıcı istemiyor, bakım ve belge yükü sürer |
| Panel ve motoru birlikte silmek | En az kod | Efekt katmanı kaybolur, son gerçek proje onu kullandı |
| Yalnız paneli silmek | Hat ve efektler aynen sürer | Yok denecek kadar az |

## Karar
- **Panel silindi:** `ui/`, `baslat.*`, `baslat-arac.*`, `ayarlar/`. Son hali `panel-son` git etiketinde durur.
- **Kalanlar:** `motor/`, `kur.*`, `ortam.bat`, `hiz`, `sessiz_hiz`, `zoomlar`, `bulanik`, altyazı kip ve konumu.
- **Forma bağlı kod silindi:** `kapi.json` ve `sira.json` okuyan kod. `kesim.json` yoksa `vedit kes` videoları doğal ad sırasıyla uç uca alır.
- **Değişmeyenler:** altyazı (ADR 0014), teslim kodlaması (ADR 0016), PNG ara render.

## Repodan gelenlerin tamamen silinmesi (2026-11-05)
> [!note] Güncellendi 2026-11-05
> Üstteki "Kalanlar" maddesi artık geçerli değil: `motor/`, `kur.*`, `ortam.bat`, `zoomlar`, `bulanik` ve altyazı kip ve konumu da kalktı. Aşağıdaki ölçümler silinmeden önceki motor hattına aittir.

Kullanıcı `omergocmen/ai-video-edit-workflow` reposundan gelen her şeyin silinmesini istedi. Son hali `motor-son` git etiketinde durur.

- **Silindi:** `motor/`, `src/vedit/katman.py`, `tests/test_katman.py`, `efekt-katmani` skill'i (`.claude`, `.agents`), `kur.bat`, `kur.ps1`, `kur.sh`, `ortam.bat`, `GEMINI.md`.
- **Taşındı:** `sayfala` ve `ARA_KODLAMA` `hizli.py`'ye; SRT ve SplitReel bunlara bağlı.
- **Kalan hat:** `vedit taslak|final` yalnız `work/edit/sahne.mjs` + `SplitReel` (`openmontage/remotion-composer`) kullanır. `olaylar.json` yoksa final uyarır, sessizce devam eder.
- **Bilerek kaldı:** `AGENTS.md`, `.gitattributes`. İkisi de repodan geldi ama içerikleri genel: `AGENTS.md` Codex kopyalarının (`.agents`, `.codex`) girişi, `.gitattributes` `board-sync/setup.sh` satır sonunu korur. `hiz`, `sessiz_hiz` ve `hiz_parcalari` bu projenin kodudur, `vedit kes` içinde sürer.
- **Geçmiş kayıt kaldı:** [[0019-arayuz-ve-efekt-motoru-birlesimi]], [[2026-11-04-ai-video-edit-workflow]], log satırları. Git geçmişi yeniden yazılmadı.
- **Kaybedilen yetenek:** şeffaf efekt olayları (logo, sayaç, arama, çerçeve vb.), yatay kaydı 9:16 kırp-takip, sesli anlatım sahne modu, `zoomlar`, `bulanik`. SplitReel kendi sahne türleriyle çalışır: `shot`, `stat`, `text`, `chips`, `timeline`, `steps`, `hook`, `cta`.
- **Eski proje:** `instagram-reels-video` `katman.json` kullanıyordu, yeniden render edilemez. Teslim dosyaları durur.
- **Temiz klon:** `openmontage/` git dışıdır; hat artık ona tamamen bağlıdır. Elle kurulum README'dedir.
- **Doğrulama:** aynı 40 sn kayıtla `kes`, `taslak`, `final` SplitReel üzerinden çalıştı; altyazı ADR 0014'e uydu, tekrar finalde motor atlandı. Sahne türlerinin içeriği denenmedi.
- **Hız bedeli:** SplitReel ilk final 214 sn (motor 152 sn, teslim 48 sn, 1080x1920). Silinen motor aynı kayıtta 98-137 sn idi (720x1280). Çözünürlük farklı olduğu için birebir karşılaştırma değildir.

## Hız değişiklikleri
Ölçüm: `instagram-reels-video` kopyası, 39,9 sn, 720x1280, 24 fps, 12 çekirdek, GTX 1650. Tek ölçümler; adımlar arası oynama yaklaşık ±%15.

### Alınanlar
| Değişiklik | Önce | Sonra |
|---|---|---|
| Görüntü değişmediyse `vedit final` motoru atlar, `--yenile` zorlar | 98-137 sn | 48-54 sn |
| Kontak sayfası paralel, en çok 8 iş parçacığı | 4,9 sn | 2,4 sn |
| `denetim` loudness'ı bir kez ölçer | 2 geçiş | 1 geçiş |
| `vedit duzen` `node_modules` gezmez | Ölçülmedi | Ölçülmedi |
| `final:motor`, `final:ses`, `final:teslim`, `final:denetim` süreleri `sure.jsonl`'a yazılır | Yok | Var |

Motor imzası şunları kapsar: `katman.json` ya da `props.json`, transkript, motor kaynağı, `work/public`, proje girdisi, ara kodlama ayarı. `olaylar.json` kapsam dışıdır: ses düzeltmesi görüntüyü yeniden render ettirmez. Girdi klasöründeki ilgisiz bir dosya da render'ı tetikler; bu güvenli yöndeki hatadır.

`final` dağılımı: motor 56-76 sn, teslim 28-38 sn, denetim 9-12 sn, ses 8-11 sn.

### Alınmayanlar
| Deneme | Sonuç | Neden |
|---|---|---|
| Taslakta yarı fps | 41,5 → 32,7 sn (%21) | Eşik %30 |
| Remotion `--gl=angle` | 57,9 → 76,6 sn, SSIM 0,9966 | Yavaşlattı |
| Parça başına `-ss` girişi | Sentetikte 69 → 47,5 sn, birebir kare. Gerçek konuşma kaydında SSIM 0,9895, süre 33 ms farklı, ses kesimden sonra hizadan çıktı | Kaynak fps'i çıktıdan farklıysa kare sayısı değişiyor |
| Whisper `beam_size=1` | 5,9 → 4,8 sn (%19), benzerlik 1,0 | Eşik %30 |
| Whisper batched | 5,9 → 5,5 sn (%7), benzerlik 1,0 | Eşik %30 |

Whisper örneği 114 kelimeydi; kısa kayıtta paralelliğin kazancı az görünür. Uzun YouTube kaydında yeniden ölçmeye değer.

## Sonuçlar
- Teslim, kod değişikliği sonrası gerçek teslimle birebir çıktı: SSIM 1,0, ses farkı 0, süre ve format aynı.
- Sentetik test `-ss` sorununu göstermedi. Kesim değişikliği gerçek konuşma kaydında da karşılaştırılmalı.
- Motor en yavaş adım olarak kalıyor. Ayrıca baştan sona sürenin yaklaşık yarısı model süresi; bu ADR onu ölçmedi.
- Windows Defender istisnasının etkisi yönetici yetkisi gerektirdiği için ölçülmedi.
- Mac tarafı ve `kur.sh` denenmedi.

## İlgili kod
`src/vedit/hizli.py`, `src/vedit/ff.py`, `src/vedit/slop.py`, `src/vedit/cli.py`, `tests/test_hizli.py`, `.claude/skills/uretim-hatti/`, `.claude/skills/efekt-katmani/`
