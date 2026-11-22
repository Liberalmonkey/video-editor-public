---
type: decision
title: "Sabit altyazı standardı ve Sirio Berati kaynaklarının entegrasyonu"
status: accepted
tags: [adr, altyazi, motion, pano, skill]
created: 2026-11-03
updated: 2026-11-21
sources: ["[[2026-11-03-sirio-berati-repolari]]"]
supersedes:
superseded_by:
---

# 0014 — Altyazı standardı ve repo entegrasyonu

## Bağlam
Kullanıcı her videoda aynı altyazıyı istedi: okunan kelime yalnız turuncu, diğer kelimeler beyaz, siyah konturlu, net okunur yazı tipi. Aynı istekte dört GitHub reposunun işe yarayan kısımlarının alınmasını ve uygun skill'lerin kütüphaneye konmasını söyledi.

## Seçenekler
- **Altyazı:** stil paketine göre renk (eski durum) ya da motorlarda sabit tek stil. Stil paketine bırakmak, "her videoda" isteğini her yeni pakette yeniden riske atar.
- **Kaynaklar:** hepsini kurmak ya da yalnız ücretsiz, Windows'ta çalışan, API istemeyen kısımları almak.

## Karar
1. **`odak` stili her videonun standardıdır:** beyaz `#FFFFFF`, okunan kelime `#FF7A00`, siyah kontur, Montserrat 800, kutu, pop ve solma yok. Değerler marka token'ından alınmaz. YouTube dahil gömme açıktır, SRT üretimi sürer. Stil paketlerindeki farklı altyazı tarifleri bunu ezmez.
2. **Motion Graphics ve Video Editing System alınır:** pano kütüphanesi (`library/boards/`), `vedit pano`, `checks.md` yöntemi, brief ve board skill'leri, `board-sync`, teleprompter (`library/vendor/eyeline-teleprompter/`), kesim denetimi (`vedit kesimqa`).
3. **Stil kartı ve klişe testi Yapım akışına bağlanır:** 2026-11-21'den beri kendi `sanat-yonetimi` skill'imizle ([[0050-hyperframes-birincil-motor]]).
4. **Genjustsu alınmaz:** Enhancor/Replicate ücretli API ister, medyayı herkese açık sunuculara yükler, Windows'ta WSL2 ister. Yalnız iki kural alınır: taslak önce, HD sonra; üretilen sesi at, özgün sesi geri koy.
5. **Emotion-Control alınmaz:** skill içermez, çıktısı ücretli video modeline girdi olan maskedir, FLAME/SPECTRE lisansı ticari olmayan kullanımla sınırlıdır.
6. **Alınmayan kurallar:** `board-sync`'in "müzik/SFX yok" ve "zoom yok" kuralları ADR 0013 ile çeliştiği için panonun iç hareketiyle sınırlıdır, projenin kurgu sesini ve zoom kararını bağlamaz.

> [!note] Güncellendi 2026-11-15
> Kapak yazısı bu standardın dışındadır: renk ve yazı tipi `library/kapak/stiller/` paketlerinden seçilir ([[0027-kapak-sayfasi]]). Videodaki altyazı için bu karar değişmedi.

> [!note] Güncellendi 2026-11-19
> Kullanıcı kararıyla 1. madde koşullu oldu ([[0043-stile-bagli-tema-tokenlari]]): **stil seçilmemiş** videoda bu standart aynen sürer. **Stil seçiliyse** altyazı o stilin `altyazi` token'ını alır (font, okunan kelimenin rengi, kontur); kontrast yine ölçülür (okunan kelime konturuna en az 4,5:1). Kutu, pop ve solma stil açıkça istemedikçe yoktur.

## Sonuçlar
- Altyazı rengi tek yerde değil, iki motorda sabittir: `blocks/_base.css` ve `openmontage/remotion-composer/src/components/CaptionOverlay.tsx`. Değiştirmek gerekirse ikisi birlikte değişir, `SplitReel.tsx` de.
- Remotion'da `LATIN` unicode aralığı ş, ğ, İ harflerini kapsamadığı için Montserrat tam TTF olarak ayrı yüklenir.
- FFmpeg yedek yolu (`remotion_caption_burn._render_ffmpeg`) okunan kelimeyi renklendiremez; beyaz + siyah kontur yapar ve uyarı döner.
- Eski projeler `studio_overrides` ile kendi stilini korur; `vedit qa` bunlarda uyarı verir, render etmez.
- `openmontage/` ayrı bir git deposudur; yerel değişiklik `skill-lib update` sırasında çakışabilir.
- `board-sync` Türkçe metinle tek panolu örnekte uçtan uca çalıştı, ama yalnız `.m-root` kapsayıcılı panoları okur ve fiyat kuralı `$` odaklıdır. Uzun Türkçe videoda denenmedi.

## İlgili kod
`src/vedit/{build,captions,qa,pano,kesimqa,cli}.py`, `blocks/_base.css`, `studios/*/studio.yaml`, `library/boards/`, `library/checks.md`, `tests/test_kesimqa.py`.
