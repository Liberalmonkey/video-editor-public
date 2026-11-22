# Veri sözleşmeleri: edl.json · timeline.json · scenes.json

Şema kaynağı: `src/vedit/schemas.py`. Her değişiklikten sonra `vedit validate` çalıştır; hata varsa build'e geçme. Zamanlar saniye cinsindendir. "N kare" düzeltmesi = N / fps saniye.

## edit/edl.json (çekim kesimi — editor yazar)
```json
{"version": 1, "sources": {"A": "input/talking.mp4"},
 "segments": [
   {"src": "A", "in": 5.7, "out": 8.3, "note": "S004 hook"},
   {"src": "A", "in": 9.2, "out": 11.3, "note": "S005"}],
 "audio_xfade_ms": 12}
```
- Segmentler A-roll'un sırasıdır; sıra değiştirilebilir (hook'u başa almak gibi).
- in/out değerleri digest'teki segment zamanlarından alınır; `vedit cut` kelime sınırına yaslar (+60 ms ön, +100 ms son pay).
- B-roll ve ekran kaydı EDL'ye değil timeline'a konur (A-roll sesi altta devam eder, L-cut).

## edit/timeline.json (son kurgu — editor yazar)
```json
{"version": 1, "format": {"width": 1080, "height": 1920, "fps": 30}, "duration": 14.28, "style": "default",
 "chapters": [],
 "video": [
  {"id": "aroll", "src": "build/aroll.mp4", "start": 0, "dur": 14.28, "in": 0, "role": "aroll",
   "reframe": "build/reframe_1080x1920.json",
   "keys": [{"t": 2.82, "scale": 1.14}, {"t": 5.04, "scale": 1.0}]},
  {"id": "scr1", "src": "input/screen.mp4", "start": 6.78, "dur": 3.4, "in": 1.0, "role": "screen",
   "layout": "full", "z": 2,
   "keys": [{"t": 0.6, "scale": 1.35, "x": -10, "y": -8, "dur": 0.6, "ease": "power2.inOut"}]}],
 "overlays": [
  {"id": "hook", "block": "kinetic-text", "start": 0, "dur": 2.7,
   "props": {"text": "Bu öğütücü sabahlarımı değiştirdi", "highlight": "sabahlarımı", "position": "top", "size": "l"}},
  {"id": "hero1", "block": "custom", "src": "edit/custom/hero1.html", "start": 3, "dur": 4, "z": 5}],
 "captions": {"src": "edit/captions.json", "style": null, "enabled": true},
 "audio": {"voice": [],
  "music": [{"id": "bgm", "src": "library/music/x.mp3", "start": 0, "dur": 14.28, "gain_db": -12, "duck": true}],
  "sfx": [{"id": "s1", "t": 7.06, "type": "tap", "intensity": "medium", "reason": "ekranda dokunma"}]}}
```

- **video[]:** `role` aroll|broll|screen|image|bg · `layout` full|pip-br|pip-bl|top-half|bottom-half|card · `fit` cover|contain · `keys` klibe göre yerel zaman (`dur: 0` anlık punch, `dur > 0` yumuşak zoom/pan, `x`/`y` yüzde) · büyük `z` üstte. Videolar sessiz; ses master.wav'dan.
- **overlays[]:** `block` = `vedit blocks` listesinden ya da `custom`; `props` blok şemasına uyar (`*` zorunlu); `z` varsayılan 10, altyazı z=50.
- **audio:** `voice` boşsa `build/voice.wav`; `music[].duck=true` konuşmada ~−11 dB; `sfx[].t` = peak anı (resolver hizalar); `auto: true` olanları `vedit sfx cues` yeniden üretir, elle eklenenlere dokunmaz.
- **Kurallar:** id'ler benzersiz; hiçbir öğe `duration` dışına taşmaz; altyazıyla çakışan alt overlay'lerde `position: top|center`.

## direction/scenes.json (animasyon — director yazar)
```json
{"version": 1, "style": "default", "transition_families": ["cut", "match"],
 "scenes": [
  {"id": "s01", "chapter": "ch01", "vo_from": "Why is the sky blue", "intent": "Merak sorusu",
   "visual": "Büyük soru", "complexity": "block",
   "blocks": [{"block": "kinetic-text", "props": {"text": "Why is the sky blue?", "highlight": "blue", "size": "xl"}}]},
  {"id": "s03", "chapter": "ch02", "vo_from": "Sunlight looks white", "intent": "Beyaz ışık = tüm renkler",
   "visual": "Prizma ayrışması (hero)", "complexity": "hero",
   "blocks": [{"block": "chapter-card", "props": {"index": "01", "title": "White light"}, "dur": 2.2}]}]}
```
- `vo_from`: o sahneyi başlatan seslendirme cümlesinin ilk 4–7 kelimesi, senaryodaki ile birebir aynı. `vedit align` bunu transkriptte bulur.
- `blocks[].at`: sahne içi başlangıç (sn). `dur` verilmezse sahne sonuna kadar sürer.
- `complexity: hero|custom` → `edit/custom/<id>.html` yazılmalı. Yoksa yer tutucu kinetic-text konur.
- Bölüm (chapter) sınırları sahne sınırıdır. Her bölüm ayrı render edilir ve önbelleğe alınır.
- `vedit align` → `vedit scenes2timeline` sonrası müzik ve elle eklenen SFX timeline'da korunur.

## edit/custom/<id>.html (hero sahne — editor, opus)
HyperFrames alt kompozisyon kuralları (`hyperframes` skill'i): `<template>` sarmalı, kök `data-composition-id="<id>-custom"` (overlay id ile aynı); tek paused GSAP timeline `window.__timelines["<id>-custom"]`; deterministik (seed'li rastgelelik, Date/Math.random yok); `<style>`/`<script>` template içinde; renk/font kök değişkenleri (`var(--c-accent)`, `var(--f-display)`, `var(--u)`). Sonra `vedit build` → lint → `vedit sheet`/`still` ile kontrol.
