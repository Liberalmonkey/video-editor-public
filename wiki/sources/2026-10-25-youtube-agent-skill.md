---
type: source
title: "youtube-agent-skill (Jakeschincariol)"
tags: [youtube, senaryo, yayin, skill]
created: 2026-10-25
updated: 2026-10-25
raw: raw/repos/2026-10-25-youtube-agent-skill.md
url: https://github.com/Jakeschincariol/youtube-agent-skill
author: Jake Schincariol
sources: []
---

# youtube-agent-skill

## Özet
YouTube kanalının yazı işleri için 11 skill ve 6 bağımlılıksız Python aracı (MIT). Hook puanlama, başlık/thumbnail linter, ölü boşluk EDL'i, retention okuma, Shorts adayı, SEO, bölümler, yorum, plan, niş araştırması ve kanal denetimi içeriyor. Hiçbir şey yayınlamıyor ([[raw/repos/2026-10-25-youtube-agent-skill]]).

## Ana çıkarımlar
- Başlık ve thumbnail tek birim olarak yazılıp birlikte denetleniyor: thumbnail başlığı tekrar etmemeli, en fazla üç kelime, masaüstünde 60, mobilde 40 karakter sınırı.
- Hook beş özellikle puanlanıyor (özgüllük, hitap, risk, merak, kısalık). Puan bir sezgi; yüksek puan başarı vaadi değil.
- Retention raporu üç ayrı soruna bakıyor: ilk 30 saniyedeki kayıp, tek noktadaki sert düşüşler ve ortadaki sürekli kayma.
- Viral araştırma ham izlenmeye değil, videonun kendi kanalının medyanına oranına bakıyor.

## Projeye etkisi
- 2026-10-25'te proje-yerel olarak `.claude/skills/yt-*` altına kuruldu (plugin olarak değil; proje skill'leriyle aynı yerde ve yamalanabilir).
- Türkçe yamaları: Unicode tokenizer (`İ` düzeltmesi dahil), TR dolgu kelimeleri (`ıı`, `yani`, `işte`, `şey`…), TR hitap (`sen/siz`, `-sın/-sin` eki), risk ve merak kökleri, TR süre birimleri. `hooks.json` formül sınıflandırması İngilizce kaldı; TR hook'ta formülü writer adlandırır. Kontrol: `.claude/skills/yt-script/test_tr.py`.
- `deadair.py` vedit `analysis/transcript.json` dosyasını (a-roll segmentleri) okuyor.
- Ses profili stüdyo düzeyinde: `studios/<stüdyo>/references/voice.md`. Yayın metinleri teslim klasöründe `yayin.md`.
- Bağlandığı yerler: `writer` ajanı (hook puanı), `scriptwriting` (yayın paketi), `footage-editing` (ilk kesim geçişi), youtube-animasyon stüdyosu, kök `CLAUDE.md`. Senaryo akışının sahibi `scriptwriting` olarak kalıyor; `yt-script` hook ve retention vuruşları için kullanılıyor.

## Çelişkiler / açık sorular
> [!question] Çıkarım
> `yt-script` İngilizce bir retention akışı öneriyor (hook 15 sn). `scriptwriting` ise TR için 15–30 sn hook ve 1,5–3 dk bölümler öneriyor. Projede `scriptwriting` kuralları önceliklidir. Hook puanının TR'deki isabeti henüz gerçek videolarla ölçülmedi.

- `yt-viral` için `yt-dlp` kurulu değil; ihtiyaç olursa `.venv` içine kurulacak.

## Bağlantılı sayfalar
- [[youtube-animasyon-studyosu]] · [[humanizer]] · [[0010-openmontage-edit-motoru]]
