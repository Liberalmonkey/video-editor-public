---
name: scriptwriting
description: Video senaryosu yazımı — YouTube uzun video (10–15 dk) retention mimarisi, UGC/satış çerçeveleri (hook-problem-demo-kanıt-CTA, PAS, AIDA), Reels hook formülleri, konuşma dili, outline → senaryo → teleprompter. Senaryo, outline, hook, CTA ya da seslendirme metni yazarken kullan (TR/EN).
---

# Senaryo yazımı

Akış: `script/outline.md` → (onay) → `script/script.md` → humanizer (writer, polish) → (onay) → `script/teleprompter.md`.
Hikâye iskeleti (Story Circle, hook, "ama / bu yüzden", soru işareti testi, CTA): her senaryoda `hikaye-matematigi` skill'ini birlikte kullan.
Girdi: `brief.md`, `studios/<s>/references/style-grammar.md`, `analysis/reference/digest.md`, `script/voice-sample.md` (varsa).

## Evrensel kurallar
- **Kulak için:** cümle ≤ 18 kelime, tek fikir, konuşma dili; "-mektedir", "söz konusu", "bu bağlamda" yok.
- **Süre:** TR ~140, EN ~150 kelime/dk (Reels/UGC +%10); outline'da bölüm başına kelime bütçesi.
- **Somut:** "çok hızlı" değil "10 saniyede".
- **Uydurma yok:** veri yalnız brief/kaynaktan; yoksa `[KAYNAK?]`.
- **Ekran/ses:** `[EKRAN: …]` notu; ekran metni kısa ve rakamlı, ses okunuşa göre.
- Her bölümün tek işi var, köprüyle biter.

## YouTube (10–15 dk)
Hook puanı `yt-script` (`hookscore.py`), başlık + thumbnail `yt-package`, açıklama/bölümler `yt-seo`/`yt-chapters` → `Projeler/outputs/<stüdyo>/<proje>/yayin.md`.
1. **Hook (0–30 sn):** sonuç, çarpıcı soru, yaygın yanlış ya da merak boşluğu; "merhaba arkadaşlar" yok; 15–30. sn'de vaat ("sonunda X'i anlayacaksın").
2. **Bağlam (30–90 sn):** neden önemli, kısa.
3. **Bölümler (5–8 × 1,5–3 dk):** mini-hook → göster → adlandır → örnek → köprü; her 30–60 sn pattern interrupt; açık döngüler mutlaka kapanır.
4. **Doruk:** en büyük içgörü sona doğru.
5. **Kapanış (30–60 sn):** 3 cümle özet + sonraki video köprüsü + tek CTA; son 10–20 sn sakin (end screen).
- Eğitici: önce yaygın yanlış, sonra doğru model; bölüm başına ≤ 5 kavram; analojinin sınırını söyle.
- Eğlenceli: kontrast, callback, 3'lü kural (gerçekten komikse).

## UGC / satış (20–60 sn)
İskelet: hook (0–3 sn) → problem → demo → kanıt → teklif + tek CTA. Alternatif: PAS, AIDA, önce/sonra, "3 neden", itiraz kırma ("Pahalı mı? Hesaplayalım.").
- Samimi, birinci şahıs; spiker değil arkadaş.
- Fayda önce; abartı yok ("en iyi", "garanti"); fiyat yalnız brief'te varsa.
- 3 hook varyantı (sonuç-önce / problem / merak).

## Reels (15–90 sn)
İlk 1 sn'de görsel + metinle bağlam (sessiz izleyen anlamalı). Formüller: "X'i bırak, Y yap", "Bunu bilmeden Z alma", "3 saniyede X", liste ("3 hata"), POV, önce/sonra. Son cümle başa bağlanırsa loop.

## Formatlar
**Outline:**
```
# <başlık> — hedef <süre> · <kelime bütçesi>
Tek cümle vaat: …
Hook seçenekleri: A) … B) … C) …
## Bölüm 1 — <başlık> (~X sn, ~Y kelime)
- İş: … · Ana fikir: … · Görsel: … · Köprü: …
Açık döngüler: [B2→B5] …
```
**Senaryo:** bölüm başlıkları `## `; paragraf = nefes ≈ sahne; görsel not satır sonunda `[EKRAN: …]`; paragrafların ilk 5–7 kelimesi ayırt edici (`vo_from`), aynı cümle başı tekrarlanmaz.

## Kontrol
- [ ] Kelime sayısı bütçenin ±%10'unda, hook ve vaat net
- [ ] Köprüler var, döngüler kapandı, tek CTA
- [ ] Uydurma veri yok, `[KAYNAK?]` listelendi
- [ ] humanizer geçişi yapıldı
