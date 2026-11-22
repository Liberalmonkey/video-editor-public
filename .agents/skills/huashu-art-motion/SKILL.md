---
name: huashu-art-motion
description: huashu-art-motion (MIT) ile sanat stili tarifleri ve explainer gramerleri (Kurzgesagt, Vox, beyaz tahta, 3B1B, kinetik yazı, finans grafiği) için kılavuz. Yalnız motion-tasarimci ya da kullanıcı /huashu-art-motion ile çağırır.
disable-model-invocation: true
---

# huashu-art-motion: bu projede kullanım

Kaynak `library/vendor/huashu-art-motion/` altındadır (alchaincyf/huashu-art-motion, MIT, sürüm 1468196, 2026-11-13). Asıl kılavuz oradaki `SKILL.md` (Çince); tarif ve gramer kartları `references/`, motor `scripts/engine/`.

## Bu projede geçerli fark
- Kütüphaneye giren her şey bizim sözleşmemize çevrilir: `library/motion/custom/<id>/<id>.html` + `meta.json`, üretim `vedit motion kur <id>`. Sözleşme `.claude/agents/motion-tasarimci.md` içindedir.
- Tarif ve gramer kartları fikir ve teknik kaynağıdır. Motorun kendisi (`scripts/engine/render.py`, uv, kendi Chromium'u) yalnız kullanıcı uzun bir sanat filmi istediğinde çalıştırılır; önce betikleri oku, dış koddur.
- MIT dışında kalan parçalar bu kopyadan silindi (2026-11-13): `scripts/engine/demos/` (karakter kareleri, Clawd içeriği), `scripts/engine/reference_films/` (`strokes.js`, Arphic lisansı), `scripts/engine/lib/fonts/` (SIL OFL fontlar), `scripts/engine/examples/assets/`. Bunları geri indirme; yazı tipi Montserrat'tır. Motorun bu dosyalara dayanan örnekleri çalışmaz.
- Görsel üretim modeli isteyen adımlar (`画面中的人物`) bu projede `gorsel-uret` skill'iyle, ücretsiz araçlarla yapılır.
- Çıktı metni Türkçedir; Çince örnek metinleri kopyalama.

## Ne için aç
Bir tema kartı ya da explainer bölümü tasarlarken ilgili gramer kartı; bir sanat stilinde zemin ya da geçiş yazarken ilgili tarif kartı.
