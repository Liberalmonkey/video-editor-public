---
disable-model-invocation: true
name: yt-edit
description: >-
  Turn a raw recording's transcript into an edit decision list - dead air,
  filler cues and retakes, with timecodes. Use for "edit this", "cut the
  dead space", "tighten this video", "I rambled", or any request to shorten
  footage from a transcript.
---

# yt-edit

An edit decision list from a timestamped transcript. It prints the cuts. You apply them.

```bash
python -X utf8 .claude/skills/yt-edit/deadair.py transcript.srt              # srt, vtt or whisper json
python -X utf8 .claude/skills/yt-edit/deadair.py transcript.srt --floor 0.35 --json
```

No transcript yet? Ask for one, or produce one first - `whisper`, `faster-whisper`, or the caption
track YouTube generates on an unlisted upload all work. Do not guess at timings.

## What it finds

- **DEAD** - gaps longer than the floor, trimmed from the MIDDLE so both sides keep a breath.
  Cutting flush against speech is what makes a tightened take sound gasping.
- **FILLER** - cues that are nothing but "um", "so yeah", "basically".
- **REPEAT** - a sentence restarted. Compared against the last cue that was actually speech, not
  the literal previous cue, because most retakes have an "um" between the two attempts.

## What it will not do

It does not touch media. It has no opinion about your B-roll. A 40% cut on the report is a 40% cut
of SPEECH, and if the video has a long silent demo in it that number is wrong - check the report
against the footage before you trust the runtime at the bottom.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user
copies, and the last line of every run is the question: **Yayınla mı, değiştir mi?**

## Bu projede

- Kullanıcıyla Türkçe konuş; içeriğin dili brief'ten gelir (TR/EN).
- Araçlar proje kökünden `python -X utf8 .claude/skills/...` ile çalışır (Windows'ta `python3` yok; `-X utf8` Türkçe karakterleri korur). TR desteği yerel yamadır, kontrolü `.claude/skills/yt-script/test_tr.py`.
- Uydurma sayı yok: eksik veri `[KAYNAK?]` olarak işaretlenir.
- Girdi: vedit `analysis/transcript.json` (a-roll segmentleri) ya da `edit/captions.srt`.
- Çıktı yalnız öneridir, medyaya dokunmaz. Kesimleri `footage-editing` kurallarıyla (kelime sınırı, J/L cut, punch-in) `edl.json`'a ya da OpenMontage kurgusuna uygula.
