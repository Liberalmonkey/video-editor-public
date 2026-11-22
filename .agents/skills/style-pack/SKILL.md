---
disable-model-invocation: true
name: style-pack
description: Marka/seri stil paketi oluşturma ve güncelleme — referans görsel/video ve stil gramerinden tokens.json, STYLE.md ve MOTION.md üretir; öğrenilen dersleri pakete ekler. Kullanıcı "bu kanalın stili", "marka renkleri", "her videoda aynı görünüm" dediğinde ya da yeni platform referansları verdiğinde kullan.
---

# Stil paketi

```
studios/<stüdyo>/styles/<ad>/
  tokens.json   build'in okuduğu tek dosya (renk, font, easing, süre, grain, radius)
  STYLE.md      ruh hâli, palet, tipografi, kompozisyon, doku, altyazı, yasaklar, ses (≤ 80 satır)
  MOTION.md     ritim, anlam haritası, easing, geçiş aileleri, kamera, kinetik tipografi (≤ 80 satır)
  examples/     onaylı videolardan 2–3 kare
```
Seçim: `project.yaml → style` ya da `studio.yaml → style`. Arama: stüdyo stilleri → `library/styles/<ad>` → `library/styles/default`.

## tokens.json
`library/styles/default/tokens.json`'dan yalnız farklı alanları yaz:
```json
{"name": "kanal-x", "colors": {"bg": "#101418", "surface": "#1A2027", "fg": "#F2F4F5", "muted": "#9AA5AE",
  "accent": "#3DDC97", "on_accent": "#0B0F12", "cap_fg": "#FFFFFF", "cap_hl": "#3DDC97", "cap_stroke": "#000000"},
 "fonts": {"display": "Space Grotesk", "body": "Inter", "mono": "JetBrains Mono"},
 "weights": {"display": 700}, "radius_u": 1.6, "grain": 0.02,
 "ease": {"ui": "power3.out", "text": "power4.out", "camera": "power2.inOut", "exit": "power2.in",
          "logo": "expo.out", "overshoot": "back.out(1.3)"},
 "durations": {"in": 0.45, "out": 0.25, "stagger": 0.06}}
```
- Fontlar yalnız `library/fonts/fonts.json`'dan (OFL, TR glif doğrulanmış). Yeni font: TTF → `library/fonts/` + `fonts.json` + `vedit qa` glif kontrolü.
- Tek accent, metin olarak kullanılacaksa bg kontrastı ≥ 4.5:1; `on_accent` buton yazısı.
- Easing karakteri: kurumsal = yumuşak, uzun · Reels = kısa (in 0.35, stagger 0.05) · eğlenceli = overshoot back.out(1.7), UI'da sınırlı.

## Önce paket, sonra proje
İlk video tasarımından önce paket **kullanıcının referanslarından** yazılır ve onaylanır (`default` yalnız test). Referans yoksa iste: 2–5 video linki (zaman damgalı) → `references/links.md`; görseller → `Projeler/inputs/_referanslar/<s>/images/`; beğendiği motion örnekleri + kısa tarif; marka renkleri, logo, font.

## Üretim
1. `vedit reference --studio <s> <linkler> --images Projeler/inputs/_referanslar/<s>/images/*`
2. director (reference) + `directing` → `references/style-grammar.md`
3. Arketip verildiyse (`references/stil-arketipleri.md`) başlangıç al, değerleri referanstan ölç (palet hex'i kontak sayfasından, gerekirse `vedit still`; süreler reference digest'ten).
4. Yaz: `tokens.json` (farklar), `STYLE.md` (`references/STYLE.template.md`), `MOTION.md` (`references/MOTION.template.md`). Her kural ölçülmüş ya da kullanıcı söylemiş olmalı; değilse "(çıkarım)".
5. `studio.yaml → style: <ad>`.
6. Test: `style` değiştir → `vedit build` → kısa `render preview`; kontak sayfasını referansınkiyle yan yana göster, farkları maddele, onay al.
7. Yeni referansla güncellenir; eski kural silinmez, "Dersler"e tarihli not.

## Ders döngüsü
Kullanıcı bir düzeltmeyi iki kez isterse değeri tokens.json/MOTION.md'ye yaz, STYLE.md "Dersler"e tarihli not ekle.
