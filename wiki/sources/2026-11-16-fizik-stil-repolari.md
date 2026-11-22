---
type: source
title: "Fizik, ritim ve stil repoları: on deponun lisansı, tekniği ve projeye katkısı"
tags: [fizik, 3d, ritim, senkron, motion, stil, tema, antigravity, lisans]
created: 2026-11-16
updated: 2026-11-16
raw: "[[raw/notes/2026-11-16-fizik-stil-repolari]]"
author: Antigravity alt ajanları (3 araştırma + 1 birleştirme), Claude doğrulaması
sources: ["[[2026-11-13-motion-kutuphane-arastirmasi]]"]
---

# Fizik, ritim ve stil repoları

## Özet
Kullanıcının verdiği on repo 2026-11-16'da Antigravity orkestrasıyla incelendi: teknik (librosa, three.js, react-postprocessing, react-three-rapier), dil (video-shotcraft, ClaudeAnimationBase, pixelfx) ve stil (opus-video-prompts, awesome-opus5-5-videos, lemo-opuscar). Birleşik rapor ham notta durur.

## Ana çıkarımlar
- **Lisans (Claude yerel LICENSE dosyalarından doğruladı):** three.js, react-postprocessing, react-three-rapier, ClaudeAnimationBase, pixelfx MIT; librosa ISC; video-shotcraft Apache-2.0. opus-video-prompts lisanssız; awesome-opus5-5-videos derlemesi MIT ama içerik yazarlarına ait; lemo-opuscar belgeleri CC BY-NC 4.0 (ticari kullanım yasak). Son üçünden yalnız fikir alındı. pixelfx'in `gallery/fonts` yazı tipi lisans dışıdır, kopyalanmadı.
- **Sürüm:** klonların ana dalları React 19 ve fiber 9 ister; proje React 18.3.1'de kalır. Kurulan: three 0.172.0, @react-three/fiber 8.18.0, @react-three/postprocessing 2.19.1, @remotion/three 4.0.484, @dimforge/rapier3d-compat 0.19.0, librosa 1.0.1.
- **Determinizm:** Rapier gerçek zamanlı adımlar, Remotion kareleri sırasız çizer; simülasyon önceden bake edilmelidir. Postprocessing'de Noise ve uyarlanır ToneMapping paralel render'da titrer; Bloom, Vignette, SMAA ve ACES ToneMapping güvenlidir. `preserveDrawingBuffer` olmadan kare siyah çıkabilir. Hazır motion blur yoktur.
- **Gizli kurallar:** 30 maddelik fizik, ışık ve ses yasası (hazırlık ve ezilme, temasın tek karede buluşması, kaymasız yuvarlanma, yük aktarımı, temas gölgesi, toplamsal ışık, tepe hizası, havada sessizlik, dudak sesten önce açılır).
- **Aday efektler ve stiller:** 10 efekt ve geçiş, 10 stil kartı (tema değerleriyle).

## Projeye etkisi
[[0039-fizik-ritim-galeri|ADR 0039]]: fizik ve karakter sahnesi, ritim ve senkron ölçümü, `fizik-sezgisi` skill'i, 10 yeni tema, 8 yeni geçiş, 3 fiziksel hazır efekt, Stüdyo galerisi.

## Çelişkiler ve açık sorular
- Araç fiziği: araştırma kapalı form `f(t)` ister, teknik not Rapier önerir. Çözüm: araba kinematik kapalı formla sürülür, çarptığı dubalar Rapier'de.
- Motion blur için alt-kare `tmix` önerisi render süresini 4-8 kat uzatır; yerine kare içi 3 hayaletli hız izi seçildi.
- `glitch` efektleri `motion-design` klişe yasağıyla çelişir; alınmadı.

## Bağlantılar
- [[0036-motion-kutuphanesi-ve-ajanlar]], [[0037-antigravity-orkestra]], [[0033-hazir-efektler]], [[0031-motion-grafik]]
