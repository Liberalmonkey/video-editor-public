# Referans analizi — Nick Saraev Reels (9 video)

Kaynak: `references/*.mp4` (WhatsApp'tan, 478x850, 30 fps). İnceleme 2026-10-23: her videodan 2 sn aralıklı kontak sayfası ve ffmpeg sahne değişimi sayımı (`select='gt(scene,0.3)'`). Not: `16.50.58` ile `16.51.41 (1)` aynı video (aynı süre ve kareler), yani fiilen 8 farklı video var.

## Sayılar

| Video | Süre | Kesim | Ort. çekim | Konu |
|---|---|---|---|---|
| 16.50.52 | 57 sn | 26 | 2.2 sn | Claude Code için 5 plugin |
| 16.50.58 / 16.51.41 (1) | 50 sn | 20 | 2.5 sn | Claude Code için 4 plugin (token, Omni, Agent Skills) |
| 16.51.40 (1) | 48 sn | 20 | 2.4 sn | Google'ın 15 ücretsiz aracı (Stitch, Opal, Antigravity, Mixboard) |
| 16.51.40 (2) | 36 sn | 11 | 3.2 sn | Claude Code'da sınırsız model (OmniRoute) |
| 16.51.40 (3) | 30 sn | 11 | 2.7 sn | Google Pomelli (pazarlama otomasyonu) |
| 16.51.40 | 36 sn | 16 | 2.3 sn | Claude Code ücretsiz modeller, 1.6 milyar token |
| 16.51.41 (2) | 53 sn | 23 | 2.3 sn | 10 AI vibe coding aracı (Google) |
| 16.51.41 | 45 sn | 16 | 2.8 sn | Claude Code tasarım skill'leri (Taste, Vercel, DESIGN.md, Playwright) |

Ortalama: 30–57 sn, her 2.2–3.2 sn'de bir kesim.

## Kadraj ve düzen
- **Bölünmüş ekran (ana kalıp)**: üst %50–55 içerik kartı (ekran görüntüsü, logo, terminal, grafik), alt %45 konuşmacı. Konuşmacı karesi yuvarlatılmış üst köşeli bir "pencere" içinde, arka plan açık gri/bej degrade.
- **Tam ekran konuşmacı**: göğüs planı, mikrofon (Shure tipi) kadrajın altında görünür. Duygusal ya da vurgu cümlelerinde, hook'ta ve CTA'da.
- **Tam ekran içerik**: koyu ya da açık zeminde tek ekran görüntüsü, turuncu çerçeveli vurgu kutusu (önemli bölgeyi çevreler), altında büyük italik tek kelime.
- **Liste başlık kartı**: "THE SECOND / THE THIRD / THE FIFTH" pembe-turuncu serif italik üst yazı + ortada uygulama ikonu (iOS ikon şeklinde, beyaz yuvarlak kare). Her liste maddesinin girişi bu kart.
- Açılış kartı tekrar eden marka öğesi: bej zemin, "1 2 3 4 5" rakamlarının bir ikona ok attığı "Claude Code plugin installer" illüstrasyonu.

## Tipografi ve altyazı
- **İki altyazı katmanı**: (1) sans-serif kalın, beyaz, 1–2 kelime, kelime kelime değişir (normal konuşma); (2) serif italik, büyük harf, tek kelime vurgu ("UNLIMITED", "1.6 BILLION", "MEMORY", "RUNS OUT"). Vurgu kelimeleri pembe-turuncu degrade ya da beyaz.
- Bazı videolarda (Google serisi) altyazı yarı saydam gri kutu içinde.
- Sayı ve büyüklükler ekranda büyük yazılır (7 BILLION, 300, OF 18, 50%), ama sayaç animasyonu yok, sabit yazı.
- Altyazı konumu: tam ekran konuşmacıda alt-orta (çene/mikrofon hizası), bölünmüş ekranda iki panelin birleşim çizgisi.

## Renk
- Sabit marka rengi: Claude turuncusu (#D97757 civarı) piksel maskot, çerçeve ve vurgu.
- Zemin: açık (beyaz/bej/gri degrade) ve koyu (lacivert-siyah) dönüşümlü; her 2–3 kesimde zemin değişir, ritmi bu sağlar.
- Grafiklerde çok renkli bar (mor/sarı/yeşil), "↓ 50% ↓" gibi ok ikonlu büyük sayı.

## Hareket
- Kesimler sert (cut); geçişte kısa zoom ve bulanıklıktan netleşme.
- Ekran görüntüleri hafif yaklaşarak (Ken Burns) girer, turuncu kutu sonradan çizilir.
- Model değiştirme gibi kavramlar küçük UI animasyonlarıyla anlatılır ("Switching model…" kartları kayar).

## Senaryo yapısı
1. **Hook (0–3 sn)**: tam ekran konuşmacı + başlık kartı. Kalıp: "Claude Code ... UNLESS", "15 NEW TOOLS COMPLETELY FREE", "Meet Pomelli".
2. **Liste gövdesi**: 4–5 madde (ya da 1 araç ve 3 özelliği). Her madde: başlık kartı → 1 cümle ne yapar → 1 kanıt (sayı, ekran görüntüsü) → konuşmacıya dönüş.
3. **CTA (son 3–5 sn)**: "comment 'Claude'" / "comment 'Google'" / "comment 'Design'", tek kelime anahtar sözcük; ekran kararır ve Instagram logosu + @nick_saraev görünür (kaynağı DM ile gönderme kalıbı).
- Konuşma hızlı ve dolgusuz; ses yakın mikrofon, müzik yok ya da çok alçak.

## Bizim için çıkarımlar
- Alınacak: bölünmüş ekran, 2–3 sn kesim ritmi, liste başlık kartları, tek kelime anahtar CTA, açık/koyu zemin dönüşümü.
- Farklılaşacak (kopya olmaması için): turuncu yerine kendi rengimiz, sayıların sabit değil sayarak gelmesi, kelime kelime sarı vurgulu altyazı, grafik ve tabloların animasyonlu çizilmesi, serif italik yerine kendi vurgu tipi. Ayrıntı: `styles/ai-reels/STYLE.md`.

Atlanan: transkript çıkarılmadı; hook ve CTA metinleri ekrandaki altyazılardan okundu.
