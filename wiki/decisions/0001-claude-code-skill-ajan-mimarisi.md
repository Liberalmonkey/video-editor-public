---
type: decision
title: "Claude Code içinde skill + alt ajan mimarisi"
status: accepted
tags: [adr, mimari, ajan]
created: 2026-10-20
updated: 2026-11-15
sources: ["[[2026-10-20-opus-animasyon-rehberi]]", "[[2026-10-20-hyperframes]]"]
supersedes:
superseded_by:
---

# ADR: Claude Code içinde skill + alt ajan mimarisi

> [!note] Güncellendi 2026-11-15
> Sekiz ajan ve orkestratör `video` skill'i ilk tasarımdır. Bugün her video işi `uretim-hatti` ile başlar ve edit ana oturumdadır ([[0017-terminal-hizli-hat]]); ajanlar `writer`, `director`, `render-qc`, motion ajanları ([[0036-motion-kutuphanesi-ve-ajanlar]]) ve denetim ajanlarıdır ([[0037-antigravity-orkestra]]). `/video` yalnız açık istekte çalışır.

## Bağlam
Kullanıcı Reels, UGC ve YouTube animasyon videolarını profesyonel biçimde kurgulayan, token tasarruflu bir sistem istiyor. Ayrı bir uygulama ve API anahtarı yerine Claude aboneliğiyle çalışmalı. [[2026-10-20-opus-animasyon-rehberi]] iyi bir motion design metodolojisi sunuyor ama Claude Code entegrasyonu, gerçek çekim ve uzun video içermiyor.

## Seçenekler
| Seçenek | Artıları | Eksileri |
|---|---|---|
| Claude Code skill + alt ajan + yerel script'ler | Ek API maliyeti yok; model frontmatter ile yönlendirme; araçlar zaten kurulu | Arayüz terminal ve Studio önizlemesiyle sınırlı |
| Bağımsız uygulama + Anthropic API | Tam kontrol, ileride web arayüzü | Kullanım başına ücret, çok daha fazla yazılım işi |

## Karar
Claude Code içinde çalışan bir sistem kuruluyor (kullanıcı kararı, 2026-10-20):
- **Skill'ler:** `video` (orkestratör), `motion-design`, `scriptwriting`, `humanizer`, `directing`, `footage-editing`, `sound-design`, `captions`, `render-qa`, `style-pack`; bunlara ek olarak HyperFrames domain skill'leri.
- **8 alt ajan:** [[0003-model-yonlendirme]].
- **`vedit`:** sıfır token harcayan Python CLI.
- **Klasörler:** üç ayrı stüdyo klasörü (`studios/youtube-animasyon`, `studios/ugc`, `studios/instagram`). Her birinin kendi `CLAUDE.md` ve `studio.yaml` dosyası var.

## Sonuçlar
- Ölçüm ve render script'te, karar LLM'de ([[token-ekonomisi]]).
- Script katmanı modüler tutulduğu için ileride bir uygulamaya taşınabilir.
- Opsiyonel alt sistemler (TTS, reframe) ayrı bağımlılık dosyalarıyla kurulur.

## İlgili kod
`.claude/skills/video/SKILL.md`, `.claude/agents/`, `src/vedit/cli.py`, `studios/`
