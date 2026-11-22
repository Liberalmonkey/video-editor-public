---
type: decision
title: "Çoklu ajan: Antigravity CLI ve Codex için tek kaynak"
status: accepted
tags: [adr, ajan, antigravity, codex]
created: 2026-11-05
updated: 2026-11-15
sources: []
---

# ADR: Çoklu ajan desteği

## Bağlam
Kullanıcı sistemin Gemini CLI ile de çalışmasını istedi (2026-11-05). Codex için `.agents/skills` ve `.codex/agents` kopyaları vardı, ama kör "Claude -> Codex" değişimiyle üretildikleri için `.Codex/wiki-kurallari.md`, `Codex mcp add` gibi var olmayan yollar içeriyordu.

Google, Gemini CLI'yi Antigravity CLI (`agy`) ile değiştirdi; ücretsiz ve Google AI Pro/Ultra erişimi 18 Haziran 2026'da kapandı. Bu makinede ölçüldü: Gemini CLI 0.42.0 `IneligibleTierError` veriyor. Kullanıcı aynı gün Gemini CLI yerine Antigravity CLI istedi.

> [!note] Güncellendi 2026-11-05
> İlk sürüm `.gemini/` (ayarlar, komutlar, ajanlar) ve `GEMINI.md` üretiyordu. Antigravity'ye geçince kaldırıldı.

## Seçenekler
| Seçenek | Artıları | Eksileri |
|---|---|---|
| Her ajan için elle kopya | Basit | Kayar; bozuk kopyanın kendisi bu yüzden çıktı |
| Kaynak `.claude/`, üretici betik ve test | Tek doğruluk kaynağı, fark testte yakalanır | Kopyaları elle düzenlemek yasak |

## Karar
- **Kaynak `.claude/`.** `scripts/ajan_esitle.py` skill'leri `.agents/skills`'e birebir kopyalar, ajanları `.agents/agents/*.md` (Antigravity) ve `.codex/agents/*.toml` (Codex) olarak üretir. `tests/test_ajan_esitle.py` fark varsa kırılır.
- **Kurallar.** Antigravity `AGENTS.md`'yi okur ([belge](https://antigravity.google/docs/rules/)). `@dosya` içe almaz, yalnız `@[ad](yol)` içe alır; `AGENTS.md` `@[CLAUDE.md](CLAUDE.md)` taşır. Dosya başına sınır 24 000 bayt, test denetler.
- **Alt ajan.** Antigravity `name`, `description`, `tools`, `model` (`inherit|flash|pro`) okur. Belge yanlış araç adının alt ajanı kilitleyebileceğini söylüyor. Belgede geçen adlar: `view_file`, `replace_file_content`, `grep_search`, `run_command`. Diğerleri (`write_to_file`, `find_by_name`, `read_url_content`, `search_web`) IDE adıdır, `agy inspect` ile doğrulanmalı.

> [!note] Güncellendi 2026-11-15
> agy 1.5.9'da araç adları ölçüldü: `read_file`, `write_file`, `edit_file`, `run_command`, `search_web`, `invoke_subagent`, `run_workflow`. `view_file` `read_file`'a çevriliyor, `find_by_name` sessizce düşüyordu; ayrı arama aracı yok. Model katmanı `inherit|flash_lite|flash|pro`. `scripts/ajan_esitle.py` eşlemesi buna göre düzeltildi ([[0037-antigravity-orkestra]]).
- **Skill.** Antigravity her skill'i `/ad` komutu yapar. Elle çağrılan skill bayrağı yok; Claude'daki `disable-model-invocation` orada etkisizdir.
- **Hesap kullanıcınındır.** Ajan API anahtarı ya da abonelik kurmaz. `agy` kurulumunu otomatik izin denetimi reddetti, kurulum kullanıcıda.

## Sonuçlar
- `vedit`, Video Stüdyo ve render hattı modelden bağımsız; değişmedi.
- Skill ya da ajan değişince `python scripts/ajan_esitle.py` çalıştırılır.
- Antigravity ile gerçek görev, alt ajan ve skill yükleme denenmedi: `agy` kurulu değil. (Güncellendi 2026-11-15: `agy` kuruldu; 1.5.9'da `--agent` ile proje ajanı ve aşamalı orkestra gerçek görevde çalıştı, [[0037-antigravity-orkestra]].)

## İlgili kod
`scripts/ajan_esitle.py`, `tests/test_ajan_esitle.py`, `AGENTS.md`, `.agents/`
