# cat-cut: AI Video Editor

Claude Code içinde çalışan AI video stüdyosu: **YouTube animasyon** (10–15 dk), **UGC** (ürün/satış), **Instagram Reels**. Edit ana oturumda yapılır; senaryo ve taze göz için alt ajanlar (writer, director, render-qc) var; ölçüm, kesim, render ve QA `vedit` CLI ile token harcamadan yapılır. Proje bilgisi `wiki/` (LLM Wiki, Obsidian vault), kod yapısı graphify grafiğinde.

## Başlamak
Önce aşağıdaki **Kurulum** bölümü (bir kez, `kur.bat`).

1. Videoları, senaryoyu ve görselleri `Projeler/inputs/<stüdyo>/<proje>/` altına koy. Stüdyolar: `instagram`, `ugc`, `youtube-animasyon`. Birden çok video doğal dosya adı sırasıyla kullanılır (`01-giris.mp4`, `02-demo.mp4`).
2. Bu klasörde terminal açıp `claude` yaz, projeyi editlemesini iste.
3. Editlenmiş videoyu `Projeler/outputs/<stüdyo>/<proje>/` altından al.

## Video Stüdyo

Yerel, Premiere benzeri kurgu uygulaması. Kök klasörde `studio.vbs`'yi (ya da masaüstündeki Video Stüdyo kısayolunu) çift tıkla; terminal penceresi görünmez. Terminalden açmak için `studio.bat`. İlk açılışta eksik bağımlılıkları kurar, arayüzü derler, Edge ya da Chrome penceresi açar. Sunucu yalnız `127.0.0.1` üzerinde çalışır; uygulama penceresini kapatınca sunucu da kapanır. Hata çıktısı `%TEMP%\vedit-studio-log.txt`.

- **Çalışma alanları:** Kurgu, Ses, Altyazı, Teslim (`Alt+1` … `Alt+4`). Paneller sürüklenir, her alanın düzeni saklanır.
- **Akış:** Proje oluştur, videoları Medya'ya bırak, İşler'den Hazırla, Medya'dan timeline'a sürükle, düzenle, Final. Tuş listesi üst şeritte, değiştirilebilir.
- **Terminalle birlikte:** Claude `work/edit/kurgu.json` yazar, arayüz anında gösterir; kaydedilmemiş düzenlemen varsa sorar.
- **OpenMontage:** `openmontage/` git dışıdır; `kur.bat` onu sabit sürümden indirip `patches/openmontage.patch` yamasını uygular. Stüdyo arayüzü ve Reels motoru `openmontage/remotion-composer/src/SplitReel.tsx` dosyasını kullanır.
- **Testler:** `.venv\Scripts\pytest tests`, `cd studio && npm test`. Tarayıcı senaryoları `studio/e2e/` altında, sunucu açıkken elle çalışır.
- **Karar ve ölçümler:** `wiki/decisions/0021-video-studyo-nle.md`.

Hat: `uretim-hatti` skill'i ile `.venv/Scripts/vedit hazirla` → `kes` → `taslak` → `final` → `kaizen`. Eski `/video` hattı yalnız açık istekte.

## Mimari
| Katman | Yer |
|---|---|
| Orkestrasyon | `.claude/skills/video/` (ana oturum, Opus) |
| Uzmanlık | `.claude/skills/*` |
| Ajanlar | `.claude/agents/` — writer, director, render-qc |
| Pipeline | `src/vedit/` (`.venv/Scripts/vedit --help`) |
| Renderer | Grafik, animasyon ve sahne: HyperFrames 0.9.77 (birincil, ADR 0050) · timeline birleştirmesi ve Reels: Remotion |
| Varlık | `library/sfx/` (kurulumda inen ~530 CC0 ses), `library/music/`, `library/motion/` |
| Teslim | `Projeler/outputs/<stüdyo>/<proje>/` (`vedit final`) |
| Bilgi | `wiki/`, `raw/` (ADR 0001–0009) |

## Kurulum
Yalnız **Windows 10/11**. Başlatıcılar (`kur.bat`, `studio.bat`, `studio.vbs`) Mac ve Linux'ta çalışmaz.

**Gerekenler** (eksikse `kur.bat` kurulum komutunu yazar):

| Program | Kurulum |
|---|---|
| Python 3.11+ | `winget install -e --id Python.Python.3.12` |
| Node.js LTS | `winget install -e --id OpenJS.NodeJS.LTS` |
| Git | `winget install -e --id Git.Git` |
| FFmpeg | `winget install -e --id Gyan.FFmpeg` |
| Edge ya da Chrome | Windows'ta Edge hazır gelir |
| [Claude Code](https://claude.com/claude-code) | Terminal hattı için; Stüdyo onsuz da açılır |

**Kur:**
```
git clone https://github.com/Liberalmonkey/video-editor-public.git
cd video-editor
kur.bat
```
`kur.bat` sırayla Python ortamını (`.venv`), OpenMontage'ı (sabit sürüm + yama), Remotion ve Stüdyo bağımlılıklarını, HyperFrames'i ve CC0 ses efektlerini kurar, masaüstüne **Video Stüdyo** kısayolu koyar. İlk kurulum internet hızına göre 5–10 dk sürer. Tekrar çalıştırmak güvenlidir. İlk `vedit hazirla` konuşma modelini (~1,5 GB) bir kez indirir.

**Müzik ve motion** repoda yok (lisans): `library/music/manifest.json` ve `library/motion/manifest.json` listesindeki dosyaları kendin indir; ses efektleri için `library/sfx/INDIRME-LISTESI.md`.

**İsteğe bağlı:**
- NVIDIA GPU ile hızlı transkripsiyon: `.venv\Scripts\pip install -e .[gpu]` (sürücü ≥ 528). Kurulu değilse CPU kullanılır.
- Yüz takibi (`vedit kurgu-reframe`): `.venv\Scripts\pip install -e .[reframe]`.
- Açıklama panosu render'ı (`vedit pano`): `.venv\Scripts\pip install -e .[boards]`.
- Ses ölçümü `earshot`, görsel üretimi Antigravity CLI (`agy`) ve kod grafiği `graphify` ayrı araçlardır; skill'lerde `<SKILL_LIB>` kendi skill kütüphanenin yoludur. Bunlar olmadan temel hat (hazırla, kes, taslak, final) çalışır.
- Freesound araması: `FREESOUND_API_KEY` ortam değişkeni.

**Lisans:** özgün kod ve belgeler MIT (`LICENSE`). Üçüncü taraf skill, pano, font ve kütüphaneler kendi lisanslarıyla gelir: `THIRD_PARTY_NOTICES.md`. `patches/openmontage.patch`, AGPL-3.0 lisanslı [OpenMontage](https://github.com/calesthio/OpenMontage) üzerindeki değişikliklerdir ve AGPL-3.0 ile gelir.

## Wiki
`/ingest`, `/ask`, `/lint`, `/wiki-index`, `/decide` · `graphify update .` (git hook'u commit'te kendisi çalıştırır) · `python scripts/wiki_lint.py` · `vedit kontrol` (tüm denetimler tek komut)

