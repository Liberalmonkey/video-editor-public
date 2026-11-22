---
type: decision
title: "Ses efekti stratejisi: yerel CC0 kütüphane + çekme + sentez"
status: accepted
tags: [adr, sfx, ses]
created: 2026-10-20
updated: 2026-10-20
sources: ["[[2026-10-20-sfx-ve-arac-arastirmasi]]", "[[2026-10-20-remotion]]"]
supersedes:
superseded_by:
---

# ADR: Ses efekti stratejisi

## Bağlam
Videolarda zil, dokunma, klavye, whoosh gibi SFX'lere ihtiyaç var. Kullanıcı yalnızca ücretsiz kaynak istiyor. GPU 4 GB olduğu için yerel AI üretimi sınırlı.

## Seçenekler
| Seçenek | Artıları | Eksileri |
|---|---|---|
| Yerel CC0 kütüphane + Freesound/Openverse çekme + prosedürel sentez | Ücretsiz, lisans güvenli, hızlı, deterministik yerleştirme | İlk kurulumda kürasyon emeği |
| ElevenLabs SFX | En esnek | Ücretli (kapsam dışı) |
| Açık kaynak AI (MMAudio, AudioGen) | Videodan sese | Ağırlıklar ticari değil (CC-BY-NC) |
| Sadece HyperFrames media-use | Hazır | Lisans/manifest kontrolü zayıf, 21 dosyalık yedek |

## Karar
Katmanlı strateji ([[sfx-stratejisi]]):
- **Kaynaklar:** [[kenney-audio]], CC0 `@remotion/sfx` ([[2026-10-20-remotion]]), [[freesound]] (CC0 filtreli), Openverse, numpy sentezi.
- **Manifest:** her sesin lisansı kayıtlı; lisans alanı boş olan ses kullanılmaz.
- **Yerleştirme:** kural tabanlı; peak, kesim karesine hizalanır. LLM yalnızca anlamsal ipuçlarını ekler.

## Sonuçlar
- `library/sfx/manifest.json` git'e girer, ses dosyaları girmez. Dosyalar `vedit sfx` komutlarıyla yeniden indirilebilir ve üretilebilir.
- Stable Audio Open Small ileride yerel yedek olarak değerlendirilebilir.

## İlgili kod
`src/vedit/sfx.py`, `src/vedit/synth.py`, `library/sfx/`
