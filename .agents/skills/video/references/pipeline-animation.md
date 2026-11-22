# Animasyon hattı (YouTube 10–15 dk · Reels animasyon)

```
brief ─► reference (style-grammar varsa atla) ─► [writer] outline ─►(onay)
  ─► [writer] script + polish ─►(onay) ─► teleprompter.md
  ─► kullanıcı seslendirir → input/vo.wav ─► transcribe ─► audio
  ─► [director] scenes ─►(onay) ─► align ─► scenes2timeline ─► [editor] hero sahneler
  ─► captions ─► [editor] assets → kullanıcı indirir ─► sfx ─► mix ─► build
  ─► render preview (bölüm bölüm) ─► qa ─► [director] critique ─► render final (önbellek) ─► export
```

## Uzun video
- **Bölümler:** 5–8 × 1,5–3 dk; her biri ayrı HyperFrames projesi (`comp/chapters/chNN`), 2'şer paralel render, hash değişmeyen bölüm yeniden render edilmez.
- **Ajanlar:** director sahne listesini tek çağrıda yazar (≤ ~120 sahne); editor yalnız hero/custom sahneler için bölüm başına çağrılır (bağımsızsa paralel).
- **Yoğunluk:** eğitici 4–8 sn/sahne (12 dk ≈ 100–150 sahne); %80+ blok, %10–20 hero.
- **Ritim:** her 30–60 sn pattern interrupt (chapter-card, stat, compare, renk/kompozisyon değişimi).
- **Seslendirme önce:** sahne süreleri sesten türetilir (`vedit align`). Senaryo değişirse kayıt yenilenir, align yeniden çalışır.

## Seslendirme dosyası
`input/vo.wav` (48 kHz WAV tercih, MP3 olur). Başta/sonda ~1 sn sessizlik, bölümler arası doğal duraklama, içinde müzik/efekt yok. Bölüm bölüm verilirse `vo_01.wav`, `vo_02.wav`… sırayla birleştirilir.

## Kayıtta tekrar varsa
`vedit digest` çalıştırılabilir; kötü take'ler için `edit/edl.json` + `vedit cut`, ardından `vedit audio --src build/aroll.mp4` (transcript_cut hizalaması: gelecek iyileştirme).
