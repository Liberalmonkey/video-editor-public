# Varlık talebi (müzik · SFX · motion) — kullanıcı indirir

Ajan dosya indirmez; kullanıcının sitede 1–2 aramayla doğru dosyayı bulacağı netlikte tarif eder (ADR 0008).

## Ne zaman
- Animasyon: `scenes` onayı + timeline sonrası (`design` → `assets`). Çekim: `design` sonrası.
- Önce kütüphane: `library/music/manifest.json`, `library/motion/manifest.json`, `vedit sfx search <ifade>`. Uygun dosya varsa isteme (517 CC0 SFX var).
- Talep tek seferde, toplu. Kullanıcı indirince `vedit mark assets`.

## Siteler
| Site | Ne için | Atıf |
|---|---|---|
| pixabay.com | müzik, SFX, stok video | gerekmez |
| mixkit.co | SFX, müzik, stok video, motion | gerekmez |
| bensound.com | müzik | zorunlu (metin + lisans kodu) |
| ncs.io | enerjik elektronik | zorunlu |
| uppbeat.io | müzik, SFX, motion | zorunlu (credit metni) |
| audiolibrary.com.co | müzik (YouTube) | zorunlu |

- **UGC / ücretli reklam:** yalnız Pixabay + Mixkit. Diğerleri içerik üreticisi lisansı; emin değilsen kullanıcıya parça sayfasındaki lisansı kontrol ettir.
- **Instagram:** atıflı parçada atıf açıklamaya yazılır; hatırlat.

## Dosya yerleri
| Tür | Klasör | Ad |
|---|---|---|
| Müzik | `library/music/<site>/` | `<ID>-<kisa-ad>.mp3` |
| SFX | `library/sfx/raw/<site>/` | `<ID>-<kisa-ad>.wav\|mp3` |
| Motion | `library/motion/<site>/` | `<ID>-<kisa-ad>.mp4\|mov\|webm` |

Kullanıcı dosyaları koyunca:
1. Atıflı parça için atıf metnini iste (ya da yanında `<ID>.txt`).
2. Müzik/motion → `manifest.json` kaydı (id, file, title, mood, bpm, license, source_url, attribution); BPM: `node_modules/.bin/hyperframes beats <dosya>`.
3. SFX → `vedit sfx index` (gerekirse `source.json → files` ile kategori/etiket).
4. `vedit mark assets`; `vedit export` atıfları `credits.txt`'e yazar.

## Talep formatı (`direction/assets-request.md`)
Belirsiz sıfat ("güzel", "uygun") yasak; ölçülebilir, aranabilir tarif.

```
### M1 — Ana fon müziği (giriş + 1.–3. bölüm)
- Site: Pixabay Music (yedek: Uppbeat) · Arama: "lofi chill hip hop" · filtre: Instrumental, 2–4 dk
- Tür: lo-fi hip hop, jazzy akorlar · Ruh hâli: sakin, meraklı, hafif nostaljik
- Tempo: 80–90 BPM · Enstrüman: Rhodes, yumuşak davul, kontrbas; vokal YOK
- Enerji: düz, ani drop yok · Süre: ≥ 2:30 (temiz döngü artı)
- Kullanım: 00:00–04:30, konuşma altında −14 dB, ducking · Kaçın: lead synth, vokal chop, sert bas
- Dosya: library/music/pixabay/M1-sakin-lofi.mp3 · Lisans: atıf gerekmez
```
- **Müzik zorunlu alanlar:** tür, 2–3 ruh hâli sıfatı, BPM aralığı, enstrüman, vokal var/yok, enerji eğrisi, min. süre, zaman aralığı, kaçınılacaklar (referans parça benzetmesi serbest).
- **SFX:** ne sesi, karakter (kuru/yankılı, metalik/plastik, yumuşak/sert), süre, varyasyon adedi, videodaki anlar + tetikleyen görsel olay. Ör. `S3 — Klavye tek tuş · Mixkit "keyboard single key click" · kuru, ≤ 0.3 sn · 3 varyasyon · 01:12, 01:15, 02:40 typewriter · library/sfx/raw/mixkit/S3-klavye-tek-tus-{1,2,3}.wav`.
- **Motion:** stil adı + somut özellikler (doku, palet, çizgi, hareket karakteri; bkz. `style-pack/references/stil-arketipleri.md`), çözünürlük/oran, alpha (.mov/.webm tercih), süre, döngü, kullanım yeri.

Motion dosyası yalnız bizim üretemeyeceğimiz ya da pahalı olan şeyler için: gerçek B-roll, karmaşık 3D/partikül döngüsü, el çizimi doku/kağıt geçişi, grain/light leak overlay.

## Kullanıcıya mesaj
1. Tek cümle bağlam ("2 müzik, 6 SFX, 1 motion lazım; gerisi kütüphaneden").
2. Tablo: ID · tür · site · arama · tek satır tarif · dosya yolu.
3. Altında tam tarifler (dosyayla aynı).
4. Atıflı kalemler için: "parça sayfasındaki atıf metnini de yapıştır."
