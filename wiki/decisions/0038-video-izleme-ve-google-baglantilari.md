---
type: decision
title: "Video izleme skill'i, yeni kütüphane kayıtları ve Google uygulamaları bağlantısı"
status: accepted
tags: [adr, skill, video, ses, google, mcp, antigravity]
created: 2026-11-15
updated: 2026-11-15
sources: []
---

# ADR: Video izleme, kütüphane kayıtları, Google bağlantıları

## Bağlam
Kullanıcı üç şey istedi: projeye yarayacak skill'lerin GitHub'dan bulunması, ajanın videoyu izleyip sesi denetleyebilmesi için doğrulanmış skill'lerin kütüphaneye kaydı, Google uygulamalarının (Stitch, Workspace, YouTube, Flow, NotebookLM, AI Studio) Claude Code'a bağlanması. İş Antigravity ajanlarıyla yürütüldü ([[0037-antigravity-orkestra]]).

## Yöntem
1. Üç `skill-arastirmaci` ajanı paralel aradı (proje skill'leri, video ve ses algısı, Google); Orchestrator modeli birleştirdi.
2. Claude her adayı `gh api` ile doğruladı (yıldız, son push, lisans, arşiv). 22 adayın hepsi vardı; sayılar tuttu.
3. Seçilenler kütüphaneye klonlandı, skill ve betikleri riskli kurulum kalıbı için tarandı; temiz çıktı.
4. `kurulum-denetci` ajanları kurulanı denetledi; bulguları Claude doğruladı.

## Karar

### Kütüphaneye kaydedilenler (12)
| Kayıt | Yıldız | Lisans | Ne için |
|---|---|---|---|
| `agent-skills` (addyosmani) | 117 bin | MIT | Mühendislik kalite kapıları; tek skill kopyalanır |
| `video-use` (browser-use) | 31 bin | MIT | Konuşmayla video kurgu |
| `google-workspace-cli` (`gws`) | 32 bin | Apache-2.0 | Drive, Docs, Sheets, Gmail, Takvim komut satırı |
| `stitch-skills` (Google Labs) | 9 bin | Apache-2.0 | Stitch tasarımını koda çevirme |
| `ffmpeg-skill` | 5,8 bin | MIT | 42 FFmpeg aracı, ölç ve doğrula döngüsü |
| `google-mcp` (Google) | 4,7 bin | Apache-2.0 | Google MCP dizini, başvuru |
| `google-workspace-mcp` | 3,5 bin | MIT | Topluluk Workspace MCP'si |
| `claude-remotion-skill` | 1 bin | MIT | Remotion motion grafik |
| `youtube-mcp` | 598 | MIT | YouTube Data API okuma |
| `simplify-codebase` | 515 | MIT | Kanıtlı sadeleştirme |
| `kinocut` | 268 | Apache-2.0 | Yerel video kalite kapıları |
| `mcp-video-analyzer` | 124 | MIT | Video izleme: kare, OCR, transkript |

### Bu projeye kurulan (1)
`video-izle` skill'i: `mcp-video-analyzer` `video` skill'inden uyarlandı. Ad değişti (eski `/video` hattıyla çakışmasın), npm sürümü `0.11.0` sabitlendi, çıktı `work/izle/`. `denetim` skill'i artık kusur yazmadan önce kareyi açtırır. Ses ölçümü için `earshot` yeterli; yeni ses skill'i kurulmadı.

Diğer 11 kayıt projeye kurulmadı: `ffmpeg-skill`, `video-use` ve `kinocut` `vedit` ile aynı işi yapar ve her video isteğinde tetiklenerek `uretim-hatti` kuralıyla çelişir; `agent-skills` ve `simplify-codebase` global `ponytail` ve `karpathy` ile örtüşür.

### Google bağlantıları
| Uygulama | Yol | Durum |
|---|---|---|
| Gmail, Drive, Takvim | claude.ai hesap bağlayıcıları | Kullanıcı `/mcp` ekranından açar |
| Docs, Sheets, Slides | `gws` 0.22.5 (kuruldu) | Kullanıcı girişi bekliyor |
| Stitch | Uzak MCP `https://stitch.googleapis.com/mcp` (yoklandı, yanıt veriyor) | Kullanıcı anahtarı bekliyor |
| YouTube okuma | `zubeid-youtube-mcp-server@1.0.2` | Kullanıcı anahtarı bekliyor |
| YouTube yükleme | Kurulmadı: resmi MCP yok, topluluk sunucusu 32 yıldız ve yazma izni istiyor | `/yt-*` + YouTube Studio |
| Flow, NotebookLM | Resmi ücretsiz MCP ya da CLI yok | Claude in Chrome |
| AI Studio, Vertex Veo | Ücretli API | Kurulmaz ([[0025-gorsel-uretimi-google]]) |

Yol ve komutlar global `google-uygulamalari` skill'indedir.

## Düşen adaylar
| Aday | Neden |
|---|---|
| `token-saver` (166), `claude-rolling-context` (34) | Araç çıktısını ve bağlamı kanca ile değiştirir; yıldız düşük |
| `remotion-ffmpeg-skill`, `color-grading-skill` (7), `audio-mcp` (0) | Yıldız çok düşük |
| `popcorn`, `twelve-labs` eklentisi | Son 6 ayda commit yok; TwelveLabs ücretli ve videoyu buluta yükler |
| `video-vision-mcp` | Görsel analiz ücretli bulut API ister |
| `whisper-windows-mcp` | Lisans ticari kullanımı yasaklıyor |
| `mcp-veo-go` | Ücretli Vertex AI |
| Flow ve NotebookLM topluluk MCP'leri | Tarayıcı çerezi otomasyonu, hesap engeli riski |

## Denetim sonucu
`kurulum-denetci` ajanlarının bulguları kaynakta doğrulandı ve giderildi:
- `mcp-video-analyzer`, yerel Whisper bulamazsa ve `OPENAI_API_KEY` tanımlıysa sesi OpenAI'a, `TWELVELABS_API_KEY` tanımlıysa video adresini TwelveLabs'e gönderir. `video-izle` komutu iki değişkeni boş verir. Deneme çalışmasında ikisi de tanımlı değildi; ses dışarı gitmedi.
- `stitch-skills` içindeki iki skill ajana anahtarı ayar dosyalarından okuyup komut satırına yazmasını söyler. `google-uygulamalari` bunu yasaklar.
- `gws` gönderim skill'leri onay adımı içermez. Tek skill `gws-shared` ile birlikte kopyalanır; onay kuralı `google-uygulamalari`ndadır.
- `skill-router` kütüphane kaynağı global kopyayla eşitlendi (güncelleme üzerine yazıyordu). Proje kilidinden diskte olmayan `ai-slop-denetimi` kaydı çıkarıldı. "Resmi" ifadeleri düzeltildi.
- İlk denetim çalışması boş döndü: ajanlar çalışma klasörü dışındaki kütüphaneyi okuyamadı ve betik bunu başarı saydı. Betik artık bunu `DENIED` sayar; plan `add_dir` ile yeniden çalıştırıldı.
- Açık: proje kilidindeki `youtube-agent-skill` kaydının kütüphanede karşılığı yok (önceki kurulumdan).

## Sonuçlar
- Anahtar ve giriş kullanıcıdadır; o adımlar tamamlanana kadar Stitch, `gws` ve YouTube "kuruldu, doğrulanmadı" durumundadır.
- `gws` kendi ifadesiyle resmi olarak desteklenen bir Google ürünü değildir; Google Workspace GitHub hesabında yayımlanır.
- `mcp-video-analyzer` 124 yıldızlı bir topluluk paketidir. Sürüm sabit tutulur; yükseltmeden önce değişiklikler okunur.
- Video izleme kare örneklemesidir: iki kare arasındaki tek karelik kusur kaçabilir.

## İlgili dosyalar
`.claude/skills/video-izle/SKILL.md`, `.claude/skills/denetim/SKILL.md`, `.claude/agents/skill-arastirmaci.md`, `.claude/agents/kurulum-denetci.md`, `~/.claude/skills/google-uygulamalari/SKILL.md`, `~/.claude/skills/skill-router/SKILL.md`, kütüphane `catalog/registry.json`.
