---
type: spec
title: "SFX kütüphanesi (library/sfx)"
status: active
tags: [spec, sfx, ses]
created: 2026-10-20
updated: 2026-10-20
sources: ["[[2026-10-20-sfx-ve-arac-arastirmasi]]", "[[2026-10-20-remotion]]"]
decisions: ["[[0004-ses-efekti-stratejisi]]"]
---

# SFX kütüphanesi

## Problem
Kurguda kullanılacak ses efektlerinin (zil, dokunma, klavye, whoosh…) lisans güvenli biçimde bulunması, ölçülmesi, etiketlenmesi ve doğru kareye yerleştirilmesi gerekiyor ([[sfx-stratejisi]]).

## Kullanıcı hikâyeleri
- Bir editör olarak "burada telefon çalsın" dediğimde uygun sesin doğru anda, doğru seviyede çalmasını istiyorum.
- Aynı whoosh sesinin her geçişte tekrar etmemesini istiyorum.

## Kapsam
### Dahil
- `vedit sfx index`: klasördeki sesleri ölçer, normalize eder, kırpar, peak offset hesaplar ve manifest yazar
- `vedit sfx fetch`: [[freesound]] (CC0) ve Openverse; `@remotion/sfx` içindeki CC0 sesler
- `vedit sfx synth`: whoosh, riser, pop, click, tick, beep, impact
- `vedit sfx search` / `resolve`: etiketle arar, tekrar etmeden seçer
- Kategoriler: ui, transition, impact, riser, typing, phone, notification, ambience, foley, cash, camera

### Hariç
- Ücretli AI üretimi

## Tasarım
`library/sfx/manifest.json` kayıt şeması:

```json
{ "id": "whoosh-air-03", "file": "processed/whoosh-air-03.wav", "category": "transition",
  "tags": ["whoosh","fast","airy"], "duration_s": 0.62, "peak_offset_s": 0.21, "lufs": -18.0,
  "license": "CC0", "source": "kenney|remotion|freesound|openverse|synth|user",
  "source_url": "...", "attribution": null }
```

İpucu çözümleme: `{t, type, intensity}` → manifest → dosya. Dosyanın başlangıç zamanı `t - peak_offset_s` olur.

## Kabul kriterleri
- [ ] Manifest'te her kaydın `license` alanı dolu
- [ ] Kategori başına en az 3 varyant
- [ ] Peak, hedef kareye ±1 kare hizalı
- [ ] Ses dosyaları git'e girmiyor; manifest giriyor

## Açık sorular
- Kenney zip'leri elle mi indirilecek yoksa script mi indirecek? Script'le indirilip indirilemeyeceği kontrol edilecek.
