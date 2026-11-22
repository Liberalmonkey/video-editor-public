# AI Video Editor: Antigravity CLI, Codex ve diğer ajanlar

Proje kuralları `CLAUDE.md` içindedir. Antigravity onu aşağıdaki satırla buraya alır; Codex ve diğerleri dosyayı önce okur. Orada "Claude" ya da "ajan" geçen yerler, bu projede çalışan ajan sensin demektir. Her video işi `uretim-hatti` ile başlar.

@[CLAUDE.md](CLAUDE.md)

## Bu ajan için
- Kullanıcıyla Türkçe konuş. Video dosyaları yalnız `Projeler/inputs` ve `Projeler/outputs` altında durur.
- Skill'ler `.agents/skills/<ad>/SKILL.md` altındadır; Antigravity CLI her birini `/<ad>` komutu yapar. Kaynak `.claude/skills/`'tir; kopyalar `python scripts/ajan_esitle.py` ile üretilir, elle düzenlenmez.
- Alt ajanlar: `writer`, `director`, `render-qc`, `motion-arastirmaci`, `motion-tasarimci`, `motion-denetci`, `elestirmen`, `wiki-bakici`, `orkestrator`, `skill-arastirmaci`, `kurulum-denetci` (ADR 0037, 0038). Tek ajan: `agy --agent <ad> -p "..."`. Antigravity `.agents/agents/`, Codex `.codex/agents/`, Claude `.claude/agents/`.
- `vedit` aracı, Video Stüdyo ve render hattı modelden bağımsızdır; her ajan aynı komutları çalıştırır.
- Ham medya, `work/`, `openmontage/`, `raw/`, `node_modules/` klasörlerini okuma: token disiplini.

## Araç adları
| CLAUDE.md'de | Antigravity | Codex |
|---|---|---|
| Read | read_file | dosya okuma |
| Write, Edit | write_file, edit_file | apply_patch |
| Grep, Glob | read_file (ayrı arama aracı yok) | rg |
| Bash | run_command | kabuk |
| WebFetch, WebSearch | search_web | web araması |
| Agent (alt ajan) | invoke_subagent, run_workflow; `.agents/agents/` ajanı | `.codex/agents/` ajanı |

## Antigravity kurulumu
- Kur: PowerShell'de `irm https://antigravity.google/cli/install.ps1 | iex`, sonra yeni pencerede `agy --version`.
- İlk girişi etkileşimli `agy` ile yap; `agy -p "..."` saklanan girişi kullanır. `agy inspect` yüklenen skill ve ajanları gösterir.
- Gemini CLI'nin ücretsiz ve Google AI Pro/Ultra erişimi 18 Haziran 2026'da kapandı; bu projede Gemini CLI yerine Antigravity kullanılır.

Bu akış en çok Claude Code ile denendi. Başka araçta sonuç değişebilir.
