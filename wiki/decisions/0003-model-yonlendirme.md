---
type: decision
title: "Model yönlendirme: ana Opus, ajanlar opus/sonnet/haiku"
status: accepted
tags: [adr, maliyet, ajan]
created: 2026-10-20
updated: 2026-11-20
sources: ["[[2026-10-20-opus-animasyon-rehberi]]"]
supersedes:
superseded_by:
---

# ADR: Model yönlendirme

> [!note] Güncellendi 2026-11-20: kod artık yalnız Claude'da değil; sözleşmeye karşı sınırlı kod ve inceleme işi agy Gemini 4 Neon'a verilir, Claude entegre eder ([[0049-yapim-ekibi]]).

> [!note] Güncellendi 2026-11-15
> Üç ajana motion ajanları ([[0036-motion-kutuphanesi-ve-ajanlar]]) ve denetim ajanları ([[0037-antigravity-orkestra]]) eklendi. Araştırma ve denetim Antigravity'de (Gemini), üretim Claude'da çalışır.

## Bağlam
Asıl amaç profesyonel kurgu, ama token maliyeti de düşük tutulmalı. Kullanıcı ana oturumun Opus'ta çalışmasını seçti (2026-10-20).

## Seçenekler
| Seçenek | Artıları | Eksileri |
|---|---|---|
| Ana Opus + katmanlı alt ajanlar | Kullanıcıyla en iyi muhakeme; ağır işler ucuz modelde | Ana bağlam şişerse pahalı (çözüm: digest ve alt ajan izolasyonu) |
| Ana Sonnet + Opus alt ajanlar | En ucuz orkestrasyon | Kullanıcı tercih etmedi |
| Her şey Opus | En basit | En pahalı |

## Karar
> [!note] Güncellendi 2026-10-21
> Ajanlar 8'den 3'e indirildi: **writer** (opus; eski scriptwriter + script-polisher + researcher'ın konu araştırması), **director** (opus; eski director + critic + researcher'ın referans analizi), **editor** (sonnet, hero sahnede çağrı başına opus; eski editor + motion-designer + sound-designer + researcher'ın kütüphane işi). Haiku katmanı kaldırıldı. Yönlendirme tablosu artık `.claude/skills/video/SKILL.md` içinde.

~~Aşağıdaki 8 ajanlık tablo 2026-10-21'e kadar geçerliydi.~~

| Ajan | Model | Gerekçe |
|---|---|---|
| scriptwriter | opus | Hikâye yapısı ve hook kalitesi kritik |
| director | opus | Stil grameri ve sahne/çekim kararları |
| critic | opus | Görsel yargı ve rubrik |
| editor | sonnet | Digest üzerinden kesim kararları (yapılandırılmış iş) |
| motion-designer | sonnet (hero sahnede çağrı başına opus) | Bloklara parametre yazmak |
| sound-designer | sonnet | Anlamsal SFX ipuçları |
| script-polisher | sonnet | humanizer kurallarını uygulamak |
| researcher | haiku | Özetleme ve etiketleme |

Ana Opus kuralları:
- Büyük dosyaları kendisi okumaz; digest, özet ve kontak sayfası okur.
- Ağır okuma işini alt ajanlara verir.
- Alt ajan çıktıları en fazla ~30 satır özet olur, detay dosyaya yazılır.

## Sonuçlar
Yönlendirme tablosu `.claude/skills/video/SKILL.md` ("Ajanlar ve model") içinde tutulur. Kalite düşükse ilgili adım bir üst modele yükseltilir ve tablo güncellenir ([[model-yonlendirme]]).

## İlgili kod
`.claude/agents/*.md` (frontmatter `model:`)

> [!note] Güncellendi 2026-10-21
> Token maliyetini düşüren ek önlemler (Caveman, inceltilmiş CLAUDE.md): [[0009-token-optimizasyonu]].

> [!note] Güncellendi 2026-11-03
> Ajan sayısı ve çağrı başına model kuralı [[0016-earshot-render-standardi-ajan-duzeni]] ile genişledi.

> [!note] Güncellendi 2026-11-04
> Ajanlar 3'e indi (`writer`, `director`, `render-qc`), edit ana oturumda: [[0017-terminal-hizli-hat]].

> [!note] Güncellendi 2026-11-19
> Ekip motoru ([[0044-ekip-motoru]]) model seçimini slot başına kullanıcıya verir: üç editör (`editor-kurgu`, `editor-grafik`, `editor-ses-stil`) ve üç kalite kontrol ajanı (`kk-kurgu`, `kk-gorsel`, `kk-ses`), her biri ayrı motor, model, akıl yürütme seviyesi ve yedek motorla. Varsayılan ön ayar `library/ekip.json`: E1 Opus, E2 ve E3 Sonnet, K1-K3 Antigravity Gemini. Edit kararı tek ajanla değil ekip turunda verilir; tek ajan akışı `--ekip` olmadan sürer.
