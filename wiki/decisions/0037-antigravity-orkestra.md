---
type: decision
title: "Antigravity 1.5.9: hazır ajan, aşamalı orkestra ve denetim ajanları"
status: accepted
tags: [adr, ajan, antigravity, denetim, wiki]
created: 2026-11-15
updated: 2026-11-20
sources: []
---

# ADR: Antigravity 1.5.9 ile hazır ajan ve orkestra

> [!note] Güncellendi 2026-11-20: üretim de agy'ye verilebilir: sözleşme önce, kart başına ayrık dosya, en çok 3 eşzamanlı, Claude incelemesi ([[0049-yapim-ekibi]]).

## Bağlam
Antigravity CLI 1.5.3'ten 1.5.9'a çıktı. Yeni yetenekler: `--agent` (çalışma klasöründeki `.agents/agents/<ad>.md`), `--effort`, `--json-schema`, `run_workflow` aracı (Python iş akışıyla alt ajanlara paralel ya da aşamalı dağıtım) ve Orchestrator modeli (`gemini-pro-orchestrator-g1-pro`). Kullanıcı ajanların Antigravity'de kurulmasını ve orkestratörün kullanılmasını istedi. Aynı gün graft kaldırıldı; proje denetimi ve wiki bakımı için kalıcı roller gerekiyordu ([[0023-coklu-ajan]], [[0036-motion-kutuphanesi-ve-ajanlar]]).

## Ölçüm (2026-11-15)
| Konu | Sonuç |
|---|---|
| `agy --agent render-qc -p` | Çalışıyor; girdi 47 bin yerine 15 bin token. Bilinmeyen ad `ERROR` döner ve var olan ajanları listeler |
| Araç adları | `read_file`, `write_file`, `edit_file`, `run_command`, `search_web`, `invoke_subagent`, `run_workflow`. Eski eşlemedeki `find_by_name` sessizce düşüyordu |
| `--json-schema` | Yanıt JSON'unda `structured_output` alanı geliyor |
| `run_workflow` headless | "command" izni istiyor ve reddediliyor (`denied_actions: RunWorkflow`). `--settings` ile `permissions.allow` kuralı ve `--sandbox` açmadı; dört deneme |

## Seçenekler
1. `run_workflow` için `--dangerously-skip-permissions`: her aracı onaysız açar; denetim işinde gereksiz risk.
2. Aşamaları Claude tarafındaki betik yürütür, birleştirmeyi Orchestrator modeli yapar: headless çalışır, izin gerektirmez.
3. Orkestrasyonu tümüyle Claude yapar (`paralel`): birleştirme Claude bağlamını doldurur.

## Karar
Seçenek 2. `~/.claude/skills/antigravity/scripts/agy_gorev.py`:
- `gorev --ajan <ad> --efor <düzey> --sema <şema>`: hazır ajanla tek görev.
- `orkestra plan.json`: `{"asamalar": [[görev...], [görev...]]}`. Aşama içi paralel, aşamalar sıralı; sonraki aşamanın isteğindeki `{onceki}` önceki aşamanın yanıtlarıyla dolar; bir aşama hata verirse durur. Son aşama Orchestrator modeliyle birleştirir.

Yeni ajanlar (kaynak `.claude/agents/`, kopyalar `scripts/ajan_esitle.py`):
| Ajan | İş | Yazar mı |
|---|---|---|
| `elestirmen` | Kod, belge ve akış denetimi; P0/P1/P2 | Hayır |
| `wiki-bakici` | Wiki'nin yedi denetimi, ciddiyet listesi | Hayır |
| `orkestrator` | Böl, dağıt, birleştir; etkileşimli `agy --agent orkestrator` oturumunda `run_workflow` kullanır | Hayır |

Orkestratör yalnız denetim, araştırma ve wiki bakımı içindir. Edit ve kod üretimi ana Claude oturumunda kalır ([[0003-model-yonlendirme]]). Çıktılar `work/agy/<tarih>-<konu>/`.

## Sonuçlar
- Alt ajan çıktısı veridir: Claude kanıtları örnekleyerek doğrular, sonra uygular.
- `run_workflow` headless izni ileride açılırsa `orkestra` aynı plan biçimiyle ona çevrilebilir.
- agy kotası dardır; orkestra en çok üç eşzamanlı görevle çalıştırılır.

## İlgili kod
`scripts/ajan_esitle.py` (`AGY_ARAC`), `.claude/agents/elestirmen.md`, `wiki-bakici.md`, `orkestrator.md`, `tests/test_ajan_esitle.py`, `.claude/skills/lint/SKILL.md`.
