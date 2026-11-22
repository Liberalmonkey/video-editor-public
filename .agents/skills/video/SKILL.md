---
disable-model-invocation: true
name: video
description: Eski vedit + HyperFrames yapım hattı (UGC, Reels, YouTube animasyon). YALNIZ kullanıcı "/video", "vedit" ya da eski hattı açıkça istediğinde kullan. Diğer tüm video edit/üretim istekleri openmontage/ içinde OpenMontage ile yapılır (ADR 0010).
argument-hint: "new <ugc|instagram|youtube-animasyon> \"başlık\" | next | status | fix \"geri bildirim\" | plan-shoot"
---

# /video — yapım orkestratörü

Sen (ana oturum, Opus) yapımcısın: kullanıcıyla konuşur, onay kapılarını yönetir, gerektiğinde `writer` ve `director` ajanına verirsin. Ölçme, kesme, render ve QA'yı `vedit` yapar (sıfır token).

Argüman: $ARGUMENTS

## Altın kurallar
1. **Ham medya ve büyük JSON okuma** (transcript.json, captions.json). Yalnız `vedit` çıktıları, `analysis/digest.txt`, kontak sayfaları (`*.jpg`).
2. **Kod değil veri:** kurgu `edit/edl.json` + `edit/timeline.json`; HTML'i `vedit build` üretir. Özel sahne: `edit/custom/<id>.html`.
3. **Delege et:** ajana yalnız gerekli dosya yollarını ver; ajan detayı dosyaya yazar, ≤ 30 satır özet döner. Aynı dosyayı iki kez okutma.
4. **Onay kapıları:** brief → (senaryo) → kurgu/sahne planı → önizleme. "Sormadan yap" denirse `project.yaml → auto_approve: true`. Kapı: `vedit mark <adım> --approve`.
5. **Önce `vedit qa`, sonra eleştiri.** Cilalama en fazla 2 tur.
6. **Hedefli düzeltme:** "logo 12 kare geç" → yalnız o alan (12/fps sn) → build → render.
7. **Uydurma yok:** fiyat, istatistik, iddia yalnız brief/kaynakta varsa.
8. **Önce stil paketi:** stüdyoda referanstan yazılmış `styles/<ad>/STYLE.md` + `MOTION.md` yoksa tasarıma geçme; referans iste, `style-pack` ile yaz, onaylat. `library/styles/default` yalnız test.
9. **Seslendirme kullanıcıda:** `script/teleprompter.md` verilir, kullanıcı klon sesiyle harici araçta okuyup `input/vo.wav` verir. TTS yok.
10. **Müzik/SFX/motion'ı kullanıcı indirir:** ajan `references/asset-request.md` formatında talep listesi yazar.

## Komutlar
| Argüman | Yapılacak |
|---|---|
| `new <stüdyo> "başlık"` | `vedit new …` (Instagram: `--pipeline footage\|animation` sor) → `brief.md` (`references/brief-interview.md`) |
| `next` / boş | `vedit status -p <proje>` → sıradaki adım |
| `status` | `vedit status` özeti |
| `fix "…"` | timeline/edl yaması → `validate` → `build` → `render preview` → `qa` |
| `plan-shoot` | `director` (shoot-plan) → `direction/shoot-plan.md` |

Proje: `Projeler/outputs/<stüdyo>/<tarih-slug>/work/` (girdiler `Projeler/inputs/<stüdyo>/<tarih-slug>/`). Stüdyo kuralları `studios/<stüdyo>/CLAUDE.md` (otomatik yüklenir).

## Ajanlar ve model (ADR 0003)
| Ajan | Model | Görevler |
|---|---|---|
| `writer` | opus | research · outline · script · polish (humanizer) · teleprompter |
| `director` | opus | reference (stil grameri + paket) · shoot-plan · scenes · treatment · critique |
| ana oturum (`references/editor-gorevleri.md`) | oturum modeli; büyük hero işi: `general-purpose`, `model="opus"` | edl · timeline · hero · sound (SFX+müzik+mix) · assets · library |

Bir adımın çıktısı iki kez reddedilirse o çağrı bir üst modelle tekrarlanır; kalıcıysa ajan frontmatter'ı + ADR 0003 güncellenir.

## Adım → kim
| Adım | Yürütücü |
|---|---|
| brief | sen + kullanıcı (onay) |
| plan_shoot | director (opsiyonel) |
| ingest · transcribe · digest | `vedit` (transcribe `--prompt "marka, ürün"`) |
| edit_plan | editor (edl) → kullanıcıya 5–8 satır özet, onay |
| cut · audio · captions · reframe | `vedit` (reframe yalnız yatay → dikey) |
| reference | `vedit reference` → director (style-grammar varsa tekrar kullan) |
| outline · script | writer (outline → onay → script + polish → onay → teleprompter) |
| voiceover | kullanıcı → `input/vo.wav` |
| scenes · align | director (scenes) → `vedit align` + `scenes2timeline` |
| design | footage: director (treatment) → editor (timeline) · animasyon: editor (hero) |
| assets | editor (assets) → kullanıcı indirir → `vedit sfx index`, manifest, `vedit mark assets` |
| sfx | `vedit sfx cues` → editor (sound) → `vedit sfx resolve` |
| mix · build · preview · qa | `vedit` |
| critique | director (critique) → P0/P1 düzelt, ≤ 2 tur, onay |
| final · export | `vedit` → `Projeler/outputs/<stüdyo>/<proje>/` |

Hat ayrıntısı: `references/pipeline-footage.md` · `references/pipeline-animation.md` · CLI: `references/cli.md`.

## Çağrı kalıbı
```
Agent(subagent_type="general-purpose", prompt="Önce .claude/skills/video/references/editor-gorevleri.md oku. Görev: edl. Proje: Projeler/outputs/ugc/X/work. Oku: analysis/digest.txt, brief.md,
analysis/sheets/*.jpg. Yaz: edit/edl.json + edit/edit-notes.md. Dön: ≤20 satır.")
```
Claude dışı ajanda aynı istemi kendi alt ajan aracına ver (`AGENTS.md`). Uzun videoda editor (hero) bölüm başına ayrı çağrılır; bağımsız bölümler tek mesajda paralel.

## Teslimden önce
- [ ] `vedit qa` 0 hata (−14 ±1 LUFS, TP ≤ −1, siyah kare yok, TR glif tam)
- [ ] Rubrik puanları ≥ 8 ya da kullanıcı "yeterli" dedi
- [ ] `vedit export`: varyantlar, SRT, (YouTube) bölümler, kapaklar
- [ ] Atıflı varlık varsa `credits.txt` metnini kullanıcıya ver
- [ ] Kalıcı ders → stil/skill/blok güncelle + `wiki/log.md`'ye `code` kaydı
