# Stüdyo: YouTube animasyon (eğitici / eğlenceli, 10–15 dk)

Genel akış `uretim-hatti`; eski animasyon hattı `/video`. Spec: `wiki/specs/youtube-animasyon-studyosu.md`.

## Format
1920x1080, 30 fps, −14 LUFS / −1 dBTP. Altyazı gömülü (standart `odak`, ADR 0014), SRT ayrıca üretilir. 10–15 dk; TR ~140, EN ~150 kelime/dk (12 dk ≈ TR 1700 kelime). Bölümler 1,5–3 dk, ayrı render + önbellek; bölüm sınırı = sahne sınırı.

## İçerik
- **Hook (15–30 sn):** sonuç, çarpıcı soru ya da en büyük yanlış inanış; "Merhaba arkadaşlar" yok; ardından ne öğrenileceği tek cümle.
- **Retention:** her 30–60 sn pattern interrupt (görsel dil, soru, sayı, chapter-card); açık döngüler kurulur ve kapatılır.
- **Eğitici:** önce göster sonra adlandır; önce yaygın yanlış; bölüm başına ≤ 5 kavram; ekranda tek cümle; emin olunmayan sayı yok.
- **Eğlenceli:** espri ve kontrast ("beklenen vs gerçek"); maskot varsa sabit oranlar.
- **Kapanış:** özet + sonraki videoya köprü; son 5–20 sn end screen alanı boş.

## Görsel
- Stil paketi zorunlu (`style-pack`, `styles/<ad>/`); `library/styles/default` yalnız test. `references/style-grammar.md` bir kez çıkarılır.
- Sahnelerin çoğu blok (`vedit blocks --tag animation`); hero (3D, harita, özel diyagram) `edit/custom/<sahne>.html`.
- 2–3 geçiş ailesi, tüm videoda yalnız bunlar.

## Yayın paketi (yt-* skill'leri)
Ses profili `references/voice.md` (şablon `.claude/skills/yt-script/voice-template.md`). Teslimden önce `yt-package` (başlık + thumbnail), `yt-seo`, `yt-chapters` → `Projeler/outputs/youtube-animasyon/<proje>/yayin.md`. Yayın sonrası `yt-retention`, `yt-comment`; Shorts için `yt-shorts`. Hiçbiri yayınlamaz.

## Referans
Linkler `references/links.md`, görseller `Projeler/inputs/_referanslar/youtube-animasyon/images/`. Analiz: `vedit reference --studio youtube-animasyon <linkler> --images Projeler/inputs/_referanslar/youtube-animasyon/images/*`.
