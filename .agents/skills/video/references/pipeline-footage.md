# Çekim hattı (UGC · Instagram footage · talking-head)

```
brief ─► (plan_shoot) ─► ingest ─► transcribe ─► digest ─► [editor] edl ─►(onay)
  ─► cut ─► audio ─► captions ─► (reframe) ─► [director] treatment ─► [editor] timeline
  ─► sfx cues ─► [editor] sound ─► sfx resolve ─► mix ─► build ─► render preview ─► qa
  ─► [director] critique ─►(düzelt ≤2 tur, onay) ─► render final ─► export
```

- **ingest:** `input/` = çekim, ekran kaydı, ses, logo, ürün görseli. Rol tahmini yanlışsa editor notta düzeltir.
- **transcribe:** `--prompt` ile marka/ürün/kişi adları; TR+EN karışıksa `--lang auto`.
- **digest:** editor yalnız bunu + kontak sayfalarını okur. `↻` = muhtemel kötü take; sonraki tekrar tutulur.
- **edl:** hook ilk 3 sn (gerekirse en güçlü cümle başa), dolgu/tekrar atılır, hedef `studio.yaml → target_duration`.
- **reframe:** yalnız yatay kaynak + dikey hedef; çıktı `reframe` alanıyla aroll'a bağlanır.
- **timeline:** punch-in her 2–4 sn (%100 ↔ %110–118); ekran kaydında anlatılan öğeye zoom + `callout`; B-roll konuşma üstüne (L-cut); overlay'ler `build/transcript_cut.json` zamanlarıyla anahtar cümleye (ana oturum bu dosyayı okumaz).
- **sfx:** `vedit sfx cues` (kural) + `vedit sfx suggest` (transkript olayları) → editor onaylar → `resolve`.
- **mix:** müzik `library/music/` ya da kullanıcının parçası, `duck: true`.
- **critique:** yalnız `qa/sheet.jpg` + `qa/report.json` + brief; aralık için `vedit sheet renders/preview.mp4 --start 6 --dur 4`.
- **export:** UGC'de 4:5 + 16:9 varyant, kapak adayları.

Tipik 45 sn UGC: ingest+transcribe 1–3 dk, cut+audio+captions < 1 dk, preview 2–3 dk, final 3–5 dk.
