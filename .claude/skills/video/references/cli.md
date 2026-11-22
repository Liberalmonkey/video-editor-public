# vedit CLI kısa başvuru

Çalıştırma: `.venv/Scripts/vedit <komut>` (Windows). Proje dışındaysan `-p <slug-parçası>` ekle; proje klasöründeysen gerekmez.

| Komut | Ne yapar | Çıktı |
|---|---|---|
| `new <stüdyo> "başlık" [--pipeline footage\|animation] [--lang tr\|en]` | Proje iskeleti | `Projeler/outputs/<s>/<tarih-slug>/work/` (girdiler `Projeler/inputs/<s>/<tarih-slug>/`) |
| `status` | Adım tablosu + sıradaki | — |
| `mark <adım> [--approve\|--skip]` | Adımı/kapıyı işaretle | project.yaml |
| `ingest` | ffprobe, rol tahmini, kontak sayfası, 16 kHz wav | analysis/media_index.json, sheets/*.jpg |
| `transcribe [--model M] [--prompt "isimler"] [--files a.mp4] [--force]` | faster-whisper kelime zamanları (varsayılan large-v3-turbo; NVIDIA GPU'da cuda/int8_float16, yoksa CPU int8; `VEDIT_DEVICE=cpu` zorlar) | analysis/transcript.json |
| `digest` | LLM için kompakt transkript + tekrar take/dolgu işaretleri | analysis/digest.txt |
| `cut` | edl.json → A-roll (kelime sınırına yaslanır) | build/aroll.mp4, edit/timemap.json, build/transcript_cut.json |
| `reframe [--src build/aroll.mp4] [--size 1080x1920]` | YuNet yüz takibi → kırpma yolu | build/reframe_WxH.json |
| `audio [--denoise off\|light\|medium\|strong]` | Konuşma temizleme | build/voice.wav |
| `captions [--style bold-pop\|clean-sub\|karaoke]` | Altyazı sayfaları + SRT | edit/captions.json, edit/captions.srt |
| `align` · `scenes2timeline` | (animasyon) sahneleri seslendirmeye hizala → timeline | direction/scenes.aligned.json, edit/timeline.json |
| `validate` | edl/scenes/timeline şeması + blok prop kontrolü | çıkış kodu |
| `blocks [--tag animation\|ugc\|…]` | Blok kataloğu (tek satır/blok) | — |
| `sfx cues` | Kural tabanlı SFX ipuçları (elle eklenenler korunur) | timeline.audio.sfx |
| `sfx suggest` | Transkriptte ses olayı geçen yerler (öneri) | audio/sfx_suggestions.txt |
| `sfx catalog` · `sfx search <ifade>` | Kütüphane kategorileri / arama | — |
| `sfx resolve` | İpuçları → dosya (tekrarsız, peak hizalı) | audio/sfx_resolved.json |
| `sfx fetch kenney\|remotion\|freesound <q>\|openverse <q>` · `sfx synth` · `sfx index` | Kütüphane büyütme (kullanıcının indirdiği `library/sfx/raw/<site>/` dosyaları da `sfx index` ile girer) | library/sfx/ |
| `mix [--duck-db -11]` | Konuşma + müzik (ducking) + SFX → -14 LUFS | build/master.wav |
| `build` | timeline → HyperFrames (+ bölümler) + lint | comp/index.html, comp/chapters/* |
| `render preview\|final [--parallel 2]` | Taslak/final render; bölümler önbellekli | renders/preview.mp4, final.mp4 |
| `qa [--video X]` | Otomatik kontroller + kontak sayfası | qa/report.json, qa/sheet.jpg |
| `export [--variants 4x5 16x9]` | Varyant render, SRT, YouTube bölümleri, kapaklar, atıf listesi (credits.txt); teslim dosyalarını `Projeler/outputs/<stüdyo>/<proje>/` klasörüne koyar | work/renders/ + Projeler/outputs/ |
| `reference <url…> [--images …] (--project P \| --studio S) [--minutes 5]` | Referans tempo/kontak digest'i | analysis/reference/ ya da Projeler/inputs/_referanslar/S/analysis/ |
| `sheet <video> [--start s --dur d --grid 4x4]` · `still <video> <t>` | Herhangi bir aralığın kontak sayfası / tek kare | — |

HyperFrames önizleme (kullanıcı Studio'da görmek isterse): `node_modules/.bin/hyperframes preview <proje>/comp --background`, işin sonunda `--stop`.
