---
type: decision
title: "Video Stüdyo paneli ve efekt motoru: ai-video-edit-workflow birleşimi"
status: superseded
tags: [adr, arayuz, remotion, efekt, birlesim]
created: 2026-11-04
updated: 2026-11-05
sources: ["[[2026-11-04-ai-video-edit-workflow]]"]
supersedes: "[[0017-terminal-hizli-hat]] içindeki arayüz kararı"
---

# ADR: Panel ve efekt motoru birleşimi

> [!note] Güncellendi 2026-11-05
> Panel ve motor kaldırıldı: [[0020-panel-kaldirildi]]. Bu sayfa geçmiş kaydıdır. Yalnız ara render hız ölçümleri (PNG + veryfast CRF 14) sürer.

## Bağlam
Kullanıcı `omergocmen/ai-video-edit-workflow` reposunun projeyle birleşmesini, eksik yerlerin bu projeyle geliştirilmesini ve gelişmiş bir arayüz istedi (2026-11-04). Aynı gün ADR 0017 eski arayüzü kaldırmıştı: kök neden render ve bağlam yüküydü, arayüz içinde Claude çalıştırmak işleri yavaşlatıyordu. Yeni panel bu nedeni geri getirmemeli.

## Seçenekler
| Seçenek | Artıları | Eksileri |
|---|---|---|
| Repoyu olduğu gibi kök dizine kopyalamak | Hızlı | `materyaller/`, `out/`, ikinci hat; altyazı ve teslim standardı ezilir |
| Eski `ui/` (`pre-kaizen`) geri almak | Hazır | Agent'ı arayüzde çalıştırır, ADR 0017'nin kaldırma nedeni |
| Yeni ince panel + motor ayrı klasör | Hat tek kalır, her şey `vedit`'ten geçer | Kod bakımı |

## Karar
- **Panel ince kalır.** `ui/sunucu.mjs` bağımlılıksız Node sunucusudur. Agent barındırmaz: yaratıcı iş için terminal açar, hattı beyaz listeli `vedit` komutlarıyla çalıştırır. Terminal hattı aynen geçerlidir, panel isteğe bağlıdır.
- **Motor ayrı klasör.** `motor/`: Remotion `Overlay`, `Dikey`, `Grafik`, plan kapıları. Kendi `package.json`'ı vardır. `openmontage/` git dışı olduğu için oraya konmadı; temiz klonda çalışması için repoda durur.
- **Tek hat.** `vedit taslak` ve `final`, `work/edit/katman.json` görürse motoru kullanır. Son adımlar ortaktır: `olaysesi`, `teslim`, `denetim`, `kaizen`. Olmayan projelerde SplitReel akışı değişmedi.
- **Tek düzen.** Form dosyaları `Projeler/inputs/<stüdyo>/<proje>/` altına yazar; `materyaller/` ve `out/` alınmadı.
- **Sabitler kazanır.** Altyazı (ADR 0014) motorda koda gömüldü, tema ezemez. Formda stil seçimi kalktı, yalnız aç/kapat kaldı. `checks.md`, kütüphane ve denetim aynen geçerlidir.
- **Varsayılan onay.** Formda varsayılan "plan önce görülsün". Repodaki "soru sorma" kuralı alınmadı; slop önerisi onaysız uygulanmaz.

## Reponun verdiği, projenin verdiği
| Konu | Alınan | Geliştirilen |
|---|---|---|
| Arayüz | 25 efekt önizlemeli brif formu, ayar kayıtları | Proje panosu, oynatıcı, iş günlüğü, efekt çizelgesi, taslak kapısı, slop, kütüphane, kurallar, sistem |
| Render | Şeffaf katman, dikey kırp-takip, sahne modu | BT.709, `teslim`, loudness ölçümü, kelimeye kilitli altyazı, olay sesi |
| Kapı | `kontrol.mjs plan|sahne` | Render'dan önce otomatik; çıktı denetimi `vedit denetim` |
| Kurulum | Tek tık, PATH'e yazmaz, Mac başlatıcı | `.venv` ve `motor` kurulumu |
| Güvenlik | Yerel bağlanma, Host denetimi | Token çerezi, Origin, var olan projeye yazmama, geçici dosyadan taşıma, CSP |

Alınmadı: `Grafik` kompozisyonu ve `scripts/kamera.mjs` (kullanılmıyor), `site/` tanıtım sayfası, `tools/altyazi*.mjs`, `tools/transcribe.py`, `talimat/` (skill'e taşındı), `tools/plan.mjs` (tek projeye özel).

## Hız ölçümü (2026-11-04, 20 sn 1080p, 12 çekirdek, GTX 1650)
| Adım | Önce | Sonra | Kalite |
|---|---|---|---|
| Şeffaf katman render | VP8 157 sn | ProRes 4444 62 sn | VP8 kaybı kalktı |
| Birleşim (final) | medium 15,6–18,7 sn | veryfast 12,5 sn | SSIM 0,9985 |
| Opak ara render (sahne) | PNG + slow CRF 16: 79 sn | PNG + veryfast CRF 14: 58 sn | SSIM 0,9986 |
| SplitReel, 4 sn | PNG + slow CRF 16: 24,7 sn | PNG + veryfast CRF 14: 19,1 sn | SSIM 0,998 |
| Birleşim (taslak) | x264 | h264_nvenc, olmazsa x264 | Yalnız önizleme |

- Son kalite kodlaması `teslim`te kaldı: x264 slow, CRF 16, BT.709.
- Eşzamanlılık artırılmadı: varsayılan 34,7 sn, 9 çekirdek 39,3 sn, 12 çekirdek 37,4 sn. Varsayılan en hızlısı.
- JPEG q95 alınmadı. Düz sahnede kayıpsız görünse de videolu SplitReel'de SSIM 0,979'a düştü; kazancı yalnız 1,6 sn idi.
- Ölçümler sentetik içerikle yapıldı; gerçek projede kaizen doğrular.

## Sonuçlar
- Remotion iki sürüm: `motor` 4.0.540, `openmontage` 4.0.484. Bilinçli; birbirine bağlı değiller.
- Codex ve Gemini seçeneği denenmedi; `AGENTS.md`, `GEMINI.md` kural dosyasına yönlendirir.
- Temiz makine kurulumu (`kur.ps1`, `kur.sh`) ve Mac akışı bu makinede çalıştırılmadı.
- Reels `SplitReel` akışı `openmontage/` gerektirir, o klasör git dışıdır.

## Panel sadeleştirmesi (2026-11-05)
> [!note] Güncellendi 2026-11-05
> Üstteki "25 efekt önizlemeli form", "taslak kapısı, kurallar, sistem" ve "ayar kayıtları" artık geçerli değil.

Kullanıcı formun çalışmadığını bildirdi. Kök neden `brif.html`'de kaçışsız bir tırnaktı: tüm form script'i ilk commit'ten beri ölüydü, sunucu testleri tarayıcı kodunu denemediği için görmedi. `ui/test.mjs` artık tarayıcı script'lerini ayrıştırır.

- **Yükleme yalnız Başlat'ta.** Arka plan eşitlemesi stüdyo değişince videoyu eski stüdyoda bırakıyor, her ad için yarım klasör açıyordu. `/api/move` kalktı.
- **Materyaller.** Seçimler birikir, seçici hep görünür. Video seçilince tarayıcıda 8 kare alınır, `materyal/video-kareleri/` altına yazılır. Tarayıcının çözemediği videoda kare alınmaz; kontak sayfasını `vedit hazirla` üretir. Proje sayfası `materyal/` içeriğini gösterir.
- **Form sade.** Efekt seçenekleri yalnız `motor/src/types.ts` tipleri (20). Motorda karşılığı olmayanlar kalktı: yakınlaştırma, altını çizme, çeviri, bulanıklaştırma, pencere görünümü. Hız seçeneği kalktı: hatta hız değiştiren kod yok. Palet, stil, ayar kayıtları, önizleme sahnesi, tema ve dekor kalktı; renk ve stili yapay zeka seçer.
- **Brif kısa.** Akış ve kurallar `uretim-hatti`'nde durur, `brief.md` yalnız videoya özgü bilgiyi taşır.
- **Sayfalar.** Projeler, Yeni video, Kütüphane. Kurallar ve Sistem kullanıcı kararıyla kalktı; düzeltmeler terminalden `library/checks.md`'ye yazılır, kurulum `baslat.bat`'ta denetlenir. Taslak kapısı paneli kalktı: `kapi.json`'u hiçbir kod okumuyordu, kapı `viral-kurgu` akışında sürer.
- **Hız.** Günlük metni eklemeli yazılır, süreli animasyon ve araç denetimleri kalktı, medya akışı `pipeline` ile kapanır. Render hattına dokunulmadı.

## Repo görünümüne dönüş (2026-11-05)
> [!note] Güncellendi 2026-11-05
> Üstteki "Panel sadeleştirmesi"nin form, Kurallar, Sistem ve kapı maddeleri geri alındı. Yalnız Başlat'ta yükleme, 8 kare ve birikmeli materyal kalıyor.

Kullanıcı arayüzün repodaki gibi olmasını, eksik kalmamasını ve bizim kısımların da bulunmasını istedi.

- **Form.** `form.html`'nin tüm alanları geri geldi: hero, zaman çizelgesi, 25 efekt ön izlemesi, palet, stil, hız, yoğunluk, Ayarlarım, Dosya durumu, elle kopyalama, Cursor ve Başka araç.
- **Görünüm.** Repodaki sarı vurgu ve Archivo / IBM Plex tüm panelde. Fontlar yerel (`ui/public/fonts/`, OFL): CSP dış kaynağa kapalı. Videodaki altyazı turuncu kalır.
- **Yükleme.** Kullanıcı kararıyla yalnız Başlat'ta ya da Dosya durumu düğmesiyle. Repodaki anında eşitleme alınmadı, yarım klasör bırakıyordu. Düğme, Başlat'ı olmayan Cursor ve Başka araç için gerekir.
- **Altyazı.** Formda kelime, tam, vurgu ve yok; konum alt, orta, üst. Stil her kipte ADR 0014. Motor hattında geçerlidir, `SplitReel` değişmedi.
- **Formdaki her seçim çalışır.** Motorda karşılığı olmayanlar hatta bağlandı: `kesim.json` `hiz` ve `sessiz_hiz`, `katman.json` `zoomlar` ve `bulanik`. Test penceresi için `shot` yeterliydi, çeviri için `card`. Eşleme `efekt-katmani`'nda.
- **Zoom yöntemi.** `zoompan`. ffmpeg `crop` genişliği kare başına değişmez. Zoom ve bulanıklık tabana bir kez işlenir (veryfast CRF 14), aynı ayarda önbellekten gelir.
- **Bizim kısımlar.** Projeler, proje sayfası, iş günlüğü ve Kütüphane sürer; Kurallar, Sistem ve taslak kapısı döndü. Sistem denetimi yalnız o sayfa açılınca çalışır.
- **Kapı artık gerçek.** `work/edit/kapi.json` içinde "hayır" varsa `vedit final` durur. Dosya yoksa terminal hattı değişmez. Taslak yenilense de eski cevap durur, panelden güncellenir.
- **Alınmadı.** `site/` tanıtım sayfası, `file://` klasör seçici (panel yalnız token'lı sunucudan açılır), `/api/move`, `/api/ping`, `/api/baslat`.
- Doğrulama: tarayıcıda form uçtan uca, 25 ön izleme, tema, ayar kaydı; sentetik videoyla `vedit kes`, `taslak`, `final`. Mac ve Codex/Gemini başlatması denenmedi.

## Sıralı çoklu video (2026-11-05)
Kullanıcı parça parça en az 10 video yükleyip edit'in o sırayla yapılmasını istedi.

- **Form.** Video alanı birikir, üst sınır yok. Sıra seçim sırasıdır, ↑ ↓ × ile değişir. Aynı seçimdeki dosyalar ada göre doğal sıralanır. Kopyalanınca sıra kilitlenir, yoksa aynı video ikinci adla yeniden kopyalanır.
- **Dosya adı.** `01-<slug>.mp4`: alfabetik sıra kurgu sırasıyla aynı olur, `hazirla` ve panel değişmeden doğru sıralar.
- **`sira.json`.** İki ve üstü videoda yazılır. `vedit kes` parçaların bu sırayı izlediğini denetler; `kesim.json` yoksa hepsini uç uca alan dosyayı kendi yazar. Tek videoda ve terminal hattında yazılmaz, hook öne alma serbest kalır.
- **Karışık kaynak.** Boyut farklıysa ilk videoya `scale` + `pad`; sesi olmayan videoya sessizlik. Yön karışıksa form uyarır.
- **Kareler.** İlk videodan 8, diğerlerinden 3; 10 videoda 35 kare.

## İlgili kod
`ui/sunucu.mjs`, `ui/public/`, `ui/test.mjs`, `ayarlar/stiller.json`, `motor/`, `src/vedit/katman.py`, `src/vedit/hizli.py`, `baslat.bat`, `baslat.command`, `kur.ps1`, `kur.sh`, `.claude/skills/efekt-katmani/`
