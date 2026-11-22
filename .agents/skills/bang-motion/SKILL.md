---
name: bang-motion
description: bang-motion (MIT) ile HTML, CSS, SVG ve GSAP motion grafik yazmak için kılavuz - açılış kavramları, stil yönleri, "slayt gibi durmasın" denetimleri. Yalnız motion-tasarimci ya da kullanıcı /bang-motion ile çağırır.
disable-model-invocation: true
---

# bang-motion: bu projede kullanım

Kaynak `library/vendor/bang-motion/` altındadır (bangtutorial/bang-motion, MIT, sürüm c1aa65e, 2026-11-13). Asıl kılavuz oradaki `SKILL.md`; ayrıntı `references/`, başlangıç dosyaları `assets/`.

## Bu projede geçerli fark
- Çıktı tek `index.html` değil, kütüphane kaydıdır: `library/motion/custom/<id>/<id>.html` + `meta.json`. Sözleşme `.claude/agents/motion-tasarimci.md` içindedir ve bu kılavuzun önündedir.
- GSAP ve font CDN'den yüklenmez. GSAP `library/vendor/gsap.min.js`, font `library/fonts/Montserrat-Variable.ttf`.
- MP4 dışa aktarımı için buradaki `scripts/export-frames.mjs` kullanılmaz. Üretim `vedit motion kur <id>`; saydam webm, poster ve kontak sayfası çıkar. `vedit pano` GSAP ana zaman çizelgesini kare kare sarar.
- Renk ve yazı tipi tema değişkenlerinden gelir (`library/motion/tema/`). Buradaki on stil yönü tema kartı yazarken fikir kaynağıdır.
- After Effects köprüsü, görsel ve video MCP'leri kullanılmaz: bütçe 0 USD.
- `vendor` altındaki betikleri çalıştırmadan önce oku; dış koddur.

## Ne için aç
Açılış, bumper, kinetik yazı ya da explainer sahnesi tasarlarken `references/` içindeki açılış kavramları ve "anti-slide" denetimleri. Altyazı standardı (ADR 0014) bu kılavuzla değişmez.
