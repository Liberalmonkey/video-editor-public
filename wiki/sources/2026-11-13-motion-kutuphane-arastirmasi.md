---
type: source
title: "Motion kütüphanesi araştırması: GitHub motion ve stil skill'leri"
tags: [motion, kutuphane, arastirma, skill]
created: 2026-11-13
updated: 2026-11-13
raw: "[[raw/notes/2026-11-13-motion-kutuphane-arastirmasi]]"
url: (kaynak adresleri ham notun kaynak tablosunda)
author: motion-arastirmaci (Antigravity, gemini-4-argon-medium) ve Claude
---

# Motion kütüphanesi araştırması

## Özet
Kullanıcının adını verdiği dört GitHub reposu ve benzerleri, bu projenin motion sözleşmesine (HTML kaynak, sanal saat, ağ yok, 0 USD) ne katabileceği açısından incelendi. Ham not on bir kaynağı, on iki teknik kartını ve yirmi sekiz kayıt adayını taşır ([[raw/notes/2026-11-13-motion-kutuphane-arastirmasi]]).

## Ana çıkarımlar
1. **Dört repo da MIT**, ama biri ücretli: `CK42BB/vox-explainer-skill` Atlas Cloud anahtarı ister ve README'sine göre 60 saniyelik film 3-8 USD tutar. Kurulmadı; yalnız kolaj dili alındı.
2. **`bangtutorial/bang-motion`** HTML, CSS, SVG ve GSAP ile çalışır; on stil yönü, on dokuz açılış kavramı ve "slayt gibi durmasın" denetimleri taşır. `vedit pano` GSAP ana zaman çizelgesini zaten sardığı için kaynakları doğrudan bizim hatta render edilir.
3. **`alchaincyf/huashu-art-motion`** otuz altı sanat tarifi ve dokuz explainer grameri (Kurzgesagt, Vox, beyaz tahta, 3Blue1Brown, kinetik yazı, finans grafiği) verir. MIT dışında kalan parçaları var: karakter kareleri, Clawd içeriği, `strokes.js` (Arphic), fontlar (SIL OFL).
4. **`cloveric/claude-drawing-skill`** görsel modeli olmadan numpy ve Pillow ile seksen üç stilde çizer; görsel kotası harcamadan illüstrasyon sağlar.
5. Antigravity araştırması yedi benzer kaynak ekledi: `heygen-com/hyperframes` (Apache-2.0), `iart-ai/web-animation-skills`, `charlie947/motion-graphics-skills`, `rough-stuff/rough-notation`, `maxwellito/vivus`, `shshaw/Splitting` (MIT) ve `kiselas/every-frame-is-code` (MIT; ajan doğrulayamamıştı, sonradan doğrulandı).

## Projeye etkisi
Karar [[0036-motion-kutuphanesi-ve-ajanlar]] içindedir: üç repo `library/vendor/` altına alındı, kütüphane kayıtları proje yapımı olarak yazıldı, stil yönleri on temaya çevrildi (tema adlarında marka adı yok).

## Çelişkiler ve açık sorular
> [!note] Güncellendi 2026-11-13
> Antigravity'nin eklediği yedi kaynağın lisansı Claude tarafından GitHub API ile (`repos/<repo>/license`) yeniden okundu. Sonuç: `heygen-com/hyperframes` Apache-2.0; `iart-ai/web-animation-skills`, `charlie947/motion-graphics-skills`, `rough-stuff/rough-notation`, `maxwellito/vivus`, `shshaw/Splitting`, `kiselas/every-frame-is-code` MIT. Ham nottaki "doğrulanmadı" satırı eskidir. Hiçbirinden kod kopyalanmadı; yalnız teknik fikir alındı.

## Lisans durumu (2026-11-13)
| Kaynak | Lisans | Depoda ne var |
|---|---|---|
| bangtutorial/bang-motion | MIT | `library/vendor/bang-motion/` (kılavuz, başlangıç HTML'leri, betikler; `LICENSE` ile) |
| alchaincyf/huashu-art-motion | MIT | `library/vendor/huashu-art-motion/` kılavuz ve motor kodu; MIT dışı parçalar (karakter kareleri, Clawd içeriği, `strokes.js`, fontlar) silindi |
| cloveric/claude-drawing-skill | MIT | `library/vendor/claude-drawing-skill/` (`lib/`, belgeler; `LICENSE` ile) |
| CK42BB/vox-explainer-skill | MIT, ücretli API ister | Depoda yok |
| Diğer yedi kaynak | altı MIT, bir Apache-2.0 | Depoda yok; yalnız fikir |

MIT ve Apache-2.0 ticari kullanıma izin verir; koşul, kopyanın lisans metnini taşımasıdır ve `vendor` klasörleri taşır. Kütüphanedeki motion kayıtları proje yapımıdır, dış kod ya da görsel içermez.

## Bağlantılar
[[0031-motion-grafik]], [[2026-11-12-motion-grafik-arastirmasi]], [[0023-coklu-ajan]]
