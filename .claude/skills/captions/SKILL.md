---
disable-model-invocation: true
name: captions
description: Altyazı stilleri ve kuralları — bold-pop, karaoke, clean-sub, underline, SRT, satır kırma (TR/EN), güvenli alan, okuma hızı. Altyazı stili seçerken, captions.json/SRT sorunlarında ya da transkript düzeltirken kullan.
---

# Altyazı

Üretim: `vedit captions [--style …]` → `edit/captions.json` (render) + `edit/captions.srt`. Varsayılan `studio.yaml → captions`.

| Stil | Nerede | Davranış |
|---|---|---|
| `bold-pop` | UGC, Reels | 1–3 kelime, kalın display, kontur + gölge; konuşulan kelime vurgu renginde, küçük pop |
| `karaoke` | Reels, eğlenceli | 3–5 kelime; söylenenler dolar |
| `underline` | web/tanıtım | söylenen kelime beyaz + vurgu alt çizgi, sıradakiler soluk |
| `clean-sub` | YouTube | ≤ 42 kr/satır, ≤ 2 satır, yarı saydam kutu; genelde `burn: false`, SRT yüklenir |

## Kurallar
- **Konum:** dikeyde alt-orta (≈ %27 yükseklik), arayüz ikonlarının üstü; altyazı z=50; alt overlay'ler `position: top|center`.
- **Satır kırma:** karakter sınırı, 0.45 sn üstü duraklama ya da cümle sonu. Anlam birimi bölünmez ("10 / saniyede" kötü).
- **Okuma hızı:** clean-sub ≤ 22 kr/sn (QA); bold-pop/karaoke konuşmaya kilitli.
- **Büyük harf:** `studio.yaml → captions.uppercase`; TR'de `lang="tr"` (build ayarlar).
- **İsimler:** önce `vedit transcribe --prompt "Marka, Ürün, İsim"`; yine yanlışsa `build/transcript_cut.json` (çekim) ya da `analysis/transcript.json` (animasyon) içinde düzelt → `vedit captions`.
- Emoji yok; vurgu renkle.
- SRT her zaman üretilir (YouTube'a yüklenir; Instagram'da gömülü yeter).

## Sorun giderme
- Yüze/ürüne biniyorsa overlay konumunu ya da stil paketindeki alt boşluğu değiştir.
- Kelime vurgusu kayıyorsa `--model large-v3-turbo`.


## Standart: `odak` (ADR 0014)
Kullanıcı isteği, her videoda ve her motorda geçerli: okunan kelime `#FF7A00`, gerisi `#FFFFFF`, siyah kontur, Montserrat 800, kutu, pop, gölge ve solma yok. Yukarıdaki diğer stiller yalnız kullanıcı açıkça isterse kullanılır. Gömme YouTube'da da açıktır; SRT yine üretilir.

Motorlar: vedit `blocks/_base.css` `.cap-odak`; Remotion `CaptionOverlay.tsx` ve `SplitReel.tsx` (renk prop'ları yok sayılır). FFmpeg yedek yolu kelime renklendiremez, uyarı verir: bu yol teslimde kullanılmaz.
