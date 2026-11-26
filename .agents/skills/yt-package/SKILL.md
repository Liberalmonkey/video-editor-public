---
disable-model-invocation: true
name: yt-package
description: >-
  Write and lint the title and thumbnail for a YouTube video as one pairing,
  checking truncation, duplication and vagueness before publish. Use for
  "title ideas", "what should I call this", "thumbnail text", "my CTR is
  bad", packaging, or any request to rename or repackage an existing video.
---

# yt-package

The title and the thumbnail are ONE unit. Writing them separately is why most packaging fails: the
thumbnail repeats the title, and half the click surface says the same thing twice.

```bash
python -X utf8 .claude/skills/yt-package/title.py --title "..." --thumb "AI RAN IT"
python -X utf8 .claude/skills/yt-package/title.py titles.txt            # one per line, ranked
```

## Before you write

1. Read `studios/<stüdyo>/references/voice.md` if it exists (fallback `~/.claude/youtube/voice.md`; template `.claude/skills/yt-script/voice-template.md`). That is the user's voice profile: how they talk
   on camera, the words they never use, who they are talking to, what they will not claim. If it
   does not exist, ask for **three of their own videos**, read or transcribe them, infer the voice,
   and write the file. A script in the wrong voice is worse than no script, because they have to
   read it out loud.
2. Never invent a number, a result or a source. If a figure would strengthen it and you do not have
   one, ask for it or write the line without it.

## Rules the tool enforces, and why

- **60 characters** is where desktop search truncates, **40** is a mobile home feed. Both are
  reported because they fail differently: a desktop cut loses the tail, a mobile cut can lose the
  subject.
- **The thumbnail must not repeat the title.** Different words, same promise.
- **Three words maximum on the thumbnail.** At feed size a fourth word is a grey smear.
- **A number, a name or a date** beats every adjective available to you.
- **Two all-caps words is the ceiling** before a title reads as spam.

## Write ten, keep two

Generate ten titles, run them all through `title.py`, show the user the top three with their scores
and the specific issue on each. For the winner, write the thumbnail brief: the expression, the
framing, the three words, and what the background has to do to hold contrast at feed size.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user
copies, and the last line of every run is the question: **Yayınla mı, değiştir mi?**

## Bu projede

- Kullanıcıyla Türkçe konuş; içeriğin dili brief'ten gelir (TR/EN).
- Araçlar proje kökünden `python -X utf8 .claude/skills/...` ile çalışır (Windows'ta `python3` yok; `-X utf8` Türkçe karakterleri korur). TR desteği yerel yamadır, kontrolü `.claude/skills/yt-script/test_tr.py`.
- Uydurma sayı yok: eksik veri `[KAYNAK?]` olarak işaretlenir.
- Yayın metinleri (başlık, thumbnail brief, açıklama, bölümler) teslim klasöründe tek dosyada toplanır: `Projeler/outputs/<stüdyo>/<proje>/yayin.md`.
- Kapak görseli bu projede üretilmez (ADR 0056); paket kapak metni önerisini yalnız metin olarak verir, görseli kullanıcı kendi aracıyla hazırlar.
