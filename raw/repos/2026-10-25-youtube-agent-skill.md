---
source_url: https://github.com/Jakeschincariol/youtube-agent-skill
accessed: 2026-10-25
license: MIT (Copyright (c) 2026 Jake Schincariol)
version_checked: plugin 1.0.0, commit a2feb2104981a375ffd4f87ee04f4f5344ac43c6 (2026-09-16)
note: LLM inceleme notu.
---

# youtube-agent-skill — inceleme notu

Bir YouTube kanalının yazı işlerini yürüten 11 Claude skill'i ve 6 Python aracı. Claude Code plugin'i olarak da kurulabiliyor (`.claude-plugin/plugin.json`, ad `youtube-agent`). API anahtarı, hesap bağlantısı ya da yayınlama yok: her skill bir kopyalanacak blok ve "ship it, or change it?" sorusuyla bitiyor.

## İçerik

- Skill'ler: `yt-script` (21 hook formülü + puanlama, retention vuruşlu senaryo), `yt-package` (başlık ve thumbnail tek birim, linter), `yt-edit` (transkriptten ölü boşluk/dolgu/tekrar EDL), `yt-comment` (yorum triyajı + yanıt), `yt-plan` (kapasiteye göre haftalık plan), `yt-viral` (kanalın kendi medyanına göre kat sayısı ile niş araştırması), `yt-retention` (Studio retention CSV: hook kaybı, uçurumlar, kayma), `yt-shorts` (uzun videodan Shorts adayı), `yt-seo` (açıklama, etiket, sorgu testi), `yt-chapters` (YouTube kurallarına göre doğrulanmış bölümler), `yt-audit` (kanal denetimi, tek düzeltme).
- Araçlar: `hookscore.py`, `title.py`, `deadair.py`, `chapters.py`, `retention.py`, `swipe.py`. Hepsi yalnız Python standart kütüphanesi; ağ, alt süreç ya da dosya yazımı yok (2026-10-25 incelemesi).
- `templates/voice.md`: kullanıcının ses profili (kime konuşuyor, kullandığı/kullanmadığı kelimeler, iddia etmeyeceği şeyler, format). Tüm skill'ler önce bunu okuyor.

## Gözlemler

- `hookscore.py` sezgisel bir puanlayıcı: özgüllük, hitap, risk, merak, kısalık. README'ye göre 74 gerçek hook ile kalibre edilmiş; kötü hook'u iyi hook'tan ayırıyor, bir yaratıcının kendi hit'ini kendi başarısızından ayıramıyor.
- Kelime listeleri ve tokenizer'lar yalnız İngilizce ve ASCII (`[a-z]`). Türkçe metinde harfler düşüyor ("İşletmenize" → "letmenize"), hitap/risk/merak sinyalleri sıfır kalıyor.
- Windows'ta `python3` Microsoft Store kısayolu; araçlar `python -X utf8` ile çalışmalı, yoksa konsol çıktısı ve dosya okuma cp1254 ile bozuluyor.
- `deadair.py` SRT, VTT ve Whisper JSON okuyor; vedit `analysis/transcript.json` yapısını (`files.<rol>.segments`) tanımıyor.
