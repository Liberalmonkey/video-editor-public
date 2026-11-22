---
name: claude-drawing
description: claude-drawing-skill (MIT) ile görsel modeli kullanmadan, numpy ve Pillow ile kodla illüstrasyon çizmek için kılavuz - 83 stil, aşama aşama çizilme. Yalnız motion-tasarimci ya da kullanıcı /claude-drawing ile çağırır.
disable-model-invocation: true
---

# claude-drawing: bu projede kullanım

Kaynak `library/vendor/claude-drawing-skill/` altındadır (cloveric/claude-drawing-skill, MIT, sürüm 6af36dc, 2026-11-13). Asıl kılavuz oradaki `SKILL.md`; çizim kütüphanesi `lib/`, stil notları `docs/`.

## Bu projede geçerli fark
- Görsel kotası harcamaz: Antigravity görsel üretimi dar kotalıdır, kodla çizim sınırsızdır. Açıklama görseli, B-roll illüstrasyonu ya da sahne zemini için önce bunu dene (`gorsel-uret` sırasında "eldeki kare"den sonra).
- Çalıştırma: `.venv/Scripts/python` ile; `numpy` ve `Pillow` gerekir (`library/vendor/claude-drawing-skill/requirements.txt`). `lib/` dış koddur, çalıştırmadan önce oku.
- Çıktı yeri: proje görseli `Projeler/outputs/<stüdyo>/<proje>/work/gorsel/`, log `work/gorsel/log.md` (ADR 0025). Kütüphaneye girecek yeniden kullanılabilir çizim `library/motion/custom/<id>/` altına, sözleşmeye uygun girer.
- Çizilerek gelen hareket: aşamaları (`--stages`) PNG olarak al, kareleri bir HTML'de sırayla göster ve `vedit motion kur` ile webm yap; ya da durağan görseli `tur: "gorsel"` klibi olarak kullan, hareketi `hazir` efektle ver.
- Yazı görsele gömülmez; yazı kurguda motion metin ya da şablonla eklenir. `INKPAINT_FONT` gerekmez.

## Ne için aç
Kullanıcı "çiz", "illüstrasyon", "kodla resim" dediğinde ya da görsel kotası bittiğinde.
