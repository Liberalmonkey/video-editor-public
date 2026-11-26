---
name: hf-gsap-uc
description: HyperFrames motion şablonunda GSAP eklentileri (SplitText, DrawSVG, MorphSVG, MotionPath, CustomEase, Physics2D) ve three.js 3D sahne (uc.js, window.HFUC) kullanma kuralları. Yeni motion grafik, kinetik tipografi, SVG çizim, geçiş ya da 3D sahne (ekstrüde başlık, parçacık, küre, 3D grafik, cam kart, kamera dalışı) yazarken, "GSAP", "three.js", "3D", "SplitText", "bloom" dendiğinde kullan.
---

# GSAP eklentileri ve three.js, HyperFrames içinde (ADR 0063)

Sözleşme `library/motion/hf/SOZLESME.md`. Bu skill yalnız hangi aracın ne zaman ve nasıl kullanılacağını söyler. Derin başvuru elle çağrılan skill'lerdedir: `/gsap-plugins`, `/gsap-timeline`, `/gsap-utils`, `/gsap-core`, `/gsap-performance`, `/threejs-fundamentals`, `/threejs-materials`, `/threejs-lighting`, `/threejs-shaders`, `/threejs-postprocessing`, `/threejs-geometry`, `/threejs-textures`, `/threejs-animation`, `/threejs-performance`. Bu skill'ler three.js r186'yı anlatır; projede 0.172.0 vardır (WebGPU/TSL bölümlerini kullanma).

## GSAP: ne zaman hangi eklenti
| İş | Eklenti | Not |
|---|---|---|
| Harf/kelime girişi, maskeli satır | `SplitText` (`type: "words,chars"`) | `lines` kullanma (font yüklenmeden satır kırılır). Parametre metnini SplitText'ten önce yaz. |
| Çizgi, kontur, ok, el yazısı | `drawSVG` | `fromTo(el, {drawSVG: "0%"}, {drawSVG: "100%"})` |
| Şekil dönüşümü (daire → kare, ikon → ikon) | `morphSVG` | iki yolun nokta sayısı yakın olsun |
| Kavisli yol boyunca hareket | `motionPath` | `{path: "#yol", align: "#yol", autoRotate: true}` |
| Fırlatma, düşme | `physics2D` | analitik, tekrarlanabilir |
| Marka eğrisi | adlı ease: `giris`, `cikis`, `vurgu`, `oturma` | `tema.css` token'ından, stile göre değişir |

Paket: `library/vendor/gsap.min.js` = çekirdek + eklentiler, `scripts/gsap_paketle.py` üretir. ScrambleText, CustomWiggle, EasePack yok (tohumsuz rastgele); karıştırma efekti tohumlu ve `t`'den yazılır.

## three.js: ne zaman
3D yalnız kazandığında: ürün ya da tek nesne kahramansa, açıklayan bir simülasyon varsa, açılış ve kapanışta. Videoda en çok iki 3D sahne (render maliyeti ve görsel yorgunluk); art arda iki 3D sahne yok. Kullanıcının ürün ekranı 3D'de eğilmez.

## three.js: nasıl
```html
<script src="gsap.min.js"></script>
<script src="uc.js"></script>
<script>
  const U = window.HFUC, THREE = U.THREE;
  const ctx = U.kur({ fov: 30, kamera: [0, 0, 10], bloom: { guc: 0.5, yaricap: 0.3, esik: 1.0 } });
  // sahneyi ctx.sahne'ye kur; renk yalnız ctx.tema.vurgu / ikincil / yazi / zemin / soluk
  const durum = { k: 0 };
  const tl = gsap.timeline({ paused: true }).to(durum, { k: 1, duration: 1, ease: "giris" }, 0);
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;
  U.sur(ctx, tl, (t) => { /* durumdan sahneyi güncelle */ });
</script>
```
- `uc.js` kullanan şablon canlı gömülmez; `vedit` onu bir kez saydam WebM'e render eder ve önbellekte tutar (`hf_grafik.canli_mi`).
- Saydamlık: `U.kur` alfa korur, bloom sonrası alfa yeniden kurulur. Bloom eşiği 1.0: yalnız rengi 1'in üstüne itilmiş `toneMapped:false` öğe parlar. Beyaz yazıyı parlatma.
- Işık hazırdır (sıcak ana, soğuk kontur, oda ortamı). Parlak metalde `roughness >= 0.45`.
- Zaman yalnız `U.sur` içinden: `THREE.Clock`, `setAnimationLoop`, `requestAnimationFrame` yok (`kurgu_kalite.hf_determinizm_hatalari` reddeder). Simülasyonu kurulumda bir kez hesapla, karede oku.
- Yardımcılar: `katmanliYazi` (her fontla ekstrüde yazı + `parilti` bandı), `yaziDokusu`, `metinNoktalari`, `noktaDokusu`, `panel`, `yay`, `dalis`, `tohum`.
- Çekirdek kaynağı `studio/hf/uc/uc.ts`; değişince `studio` içinde `npm run uc`.

## Bitti ölçütü
`vedit hf kur --ad <ad>` üretir, kare açılıp bakılır (koyu ve açık zemin üstünde alfa, Türkçe glif, 9:16 güvenli alan). Test: `tests/test_hf_uc.py`.
