---
type: concept
title: "SFX stratejisi (katmanlı, ücretsiz)"
tags: [sfx, ses, lisans]
created: 2026-10-20
updated: 2026-10-20
sources: ["[[2026-10-20-sfx-ve-arac-arastirmasi]]", "[[2026-10-20-remotion]]", "[[2026-10-20-opus-animasyon-rehberi]]"]
---

# SFX stratejisi

## Tanım
Zil, dokunma, klavye, whoosh, pop, riser, impact gibi ses efektlerinin ücretsiz ve ticari kullanıma uygun biçimde bulunması, yönetilmesi ve videoya yerleştirilmesi yöntemi.

## Nasıl çalışır
Kaynaklar dört katmanda kullanılır:
1. **Yerel kürate kütüphane.**
   - Kaynaklar: [[kenney-audio]] (CC0), `@remotion/sfx` içindeki CC0 sesler ([[2026-10-20-remotion]]), Mixkit, isteğe bağlı Sonniss.
   - `vedit sfx index` her sesi -18 LUFS'a normalize eder, baştaki sessizliği kırpar ve peak offset değerini ölçer. Sonuç `manifest.json` dosyasına yazılır.
2. **İsteğe bağlı çekme.** [[freesound]] (yalnızca CC0) ve Openverse'ten indirilip manifest'e eklenir.
3. **Prosedürel sentez (numpy).** whoosh, riser, pop, click, beep, tick; sınırsız varyasyon. Kaynaktaki "Web Audio sentez" fikrinin offline karşılığı ([[2026-10-20-opus-animasyon-rehberi]]).
4. **Yerleştirme.**
   - Kurallar timeline olaylarından deterministik ipucu üretir:
     - kesim → whoosh (peak kesim karesine hizalanır)
     - metin girişi → pop
     - punch-in → impact
     - liste maddesi → click
     - reveal öncesi → riser
     - yazma sahnesi → klavye
   - `editor` ajanı (sound görevi) yalnızca anlamsal ipuçlarını ekler. Örnek: "telefonum çaldı" → `phone_ring`.
   - Resolver dosyayı seçer; aynı ses arka arkaya kullanılmaz.

**Kurallar:**
- Her ses ekranda görünen bir olaya bağlı olmalı.
- Yaklaşık 0.4 sn'de en fazla 1 SFX.
- SFX, konuşmanın 8–14 dB altında.

## Projede kullanımı
Karar: [[0004-ses-efekti-stratejisi]] · Spec: [[sfx-kutuphanesi]] · Skill: `.claude/skills/sound-design/`.

## Alternatifler / trade-off'lar
- **AI SFX üretimi:** ElevenLabs ücretli. Açık kaynak modellerin çoğunun ağırlıkları ticari kullanıma kapalı. Stable Audio Open Small ileride yerel yedek olarak denenebilir.
- **HyperFrames media-use:** Openverse + 21 ses sunuyor. Ek kaynak olarak kullanılabilir ama manifest ve lisans kontrolü bizim tarafımızda kalıyor.

## Kaynaklar
- [[2026-10-20-sfx-ve-arac-arastirmasi]] · [[loudness-standartlari]]
