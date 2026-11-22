---
type: concept
title: "Model yönlendirme (Opus / Sonnet / Haiku)"
tags: [maliyet, ajan, model]
created: 2026-10-20
updated: 2026-11-15
sources: ["[[2026-10-20-opus-animasyon-rehberi]]"]
---

# Model yönlendirme

> [!note] Güncellendi 2026-11-15
> Tablodaki `editor` ajanı kaldırıldı; edit ana oturumdadır ([[0017-terminal-hizli-hat]]). Güncel ajanlar: `writer`, `director`, `render-qc`, motion ajanları ([[0036-motion-kutuphanesi-ve-ajanlar]]) ve denetim ajanları `elestirmen`, `wiki-bakici`, `orkestrator` ([[0037-antigravity-orkestra]]). Araştırma ve denetim Antigravity'de, üretim Claude'da çalışır.

## Tanım
Her işi, kaliteyi düşürmeyen en ucuz modele verme ilkesi.

## Nasıl çalışır
Claude Code'da alt ajanların modeli `.claude/agents/<ad>.md` frontmatter'ındaki `model:` alanıyla sabitlenir. Ana oturum modeli kullanıcı tarafından seçilir (`/model`). Orkestratör, tek bir çağrı için `model` parametresiyle bu varsayılanı geçersiz kılabilir (ör. hero sahne → opus).

| Katman | Model | İşler |
|---|---|---|
| Ana oturum | Opus (kullanıcı kararı) | Kullanıcıyla konuşma, onay kapıları, orkestrasyon |
| Yaratıcı karar | opus | writer (araştırma, senaryo, humanizer), director (stil, sahne/çekim planı, eleştiri) |
| Uygulama | sonnet (hero: opus) | editor (EDL, timeline, hero sahne, ses/miks, kütüphane) |
| Sıfır token | script | Ölçüm, kesim, render, QA (`vedit`, `hyperframes`) |

Kaynakta da Opus için "orta effort varsayılan" önerisi var ([[2026-10-20-opus-animasyon-rehberi]]).

## Projede kullanımı
Karar: [[0003-model-yonlendirme]]. Yönlendirme tablosu: `.claude/skills/video/SKILL.md`.

> [!note] Güncellendi 2026-10-21
> Ajanlar 8'den 3'e indirildi: **writer** (opus; eski scriptwriter + script-polisher + researcher'ın konu araştırması), **director** (opus; eski director + critic + researcher'ın referans analizi), **editor** (sonnet, hero sahnede çağrı başına opus; eski editor + motion-designer + sound-designer + researcher'ın kütüphane işi). Haiku katmanı kaldırıldı. Yönlendirme tablosu artık `.claude/skills/video/SKILL.md` içinde.


## Alternatifler / trade-off'lar
Her şeyi Opus'a vermek kaliteyi az artırır ama maliyeti çok yükseltir. Her şeyi Sonnet'e vermek ise yaratıcı kararların (senaryo, yönetmenlik) kalitesini düşürür.

## Kaynaklar
- [[token-ekonomisi]] · [[0003-model-yonlendirme]]
