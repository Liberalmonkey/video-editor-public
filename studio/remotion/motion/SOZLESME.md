# Native motion bileşen sözleşmesi (ADR 0045)

Bu klasördeki her grafik bu sözleşmeye göre yazılır. Örnek bileşen: `ikon/tik/` (Tik.tsx, meta.json). Önce onu oku.

## Dosya düzeni
- `<aile>/<ad>/<Ad>.tsx`: bileşen ve Zod şeması. `export default tanimla({ meta, sema, Bilesen })`.
- `<aile>/<ad>/meta.json`: `cekirdek/tipler.ts` içindeki `MotionMeta` biçimi. `ad` alanı `"<aile>/<ad>"`.
- `<aile>/index.ts`: ailenin dizisi. Yeni bileşen buraya eklenir.
- Dokunulmaz dosyalar: `cekirdek/**`, `kayit.ts`, `sema-yaz.ts`, `../tema.ts`, `../Kurgu.tsx`. Eksik bir yardımcı gerekiyorsa kendi bileşen dosyanda yaz ve raporda "çekirdeğe önerilir" diye belirt.

## Zorunlu kurallar (testler ölçer)
- **Şema:** `z.strictObject({...})`. Her alanın `.default(...)` değeri vardır, yani `sema.parse({})` geçer. Renk parametresi onaltılık değil, tema rengi adıdır (`z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"])`).
- **Animasyon:**
  - Yalnız `useAkis` (cekirdek/zaman.ts), `spring` ve `interpolate` kullanılır, açık eğriyle.
  - CSS `@keyframes`, `transition`, `animation` ve `Easing.linear` yasaktır.
  - Eğriler `a.e.enter`, `a.e.exit`, `a.e.emphasis`, `a.e.settle` alanlarından gelir.
- **Hareket dili:**
  - Anticipation yalnız `a.ters` ile (0→1→0, ilk `a.hazirlikKare` karede; ana giriş `a.gir` ondan sonra başlar). Ters hazırlık ana hareketin **tersine** işaretlenir: `konum = yon * (-genlik * a.ters + mesafe * (1 - a.gir))`. Hazırlıkta öğe görünür olmalı: opaklık `a.belir`, `a.gir` değil. Kendi `f < 2 ? ...` formülünü yazma.
  - Taşma %4-8, tek sönüm (`a.takip`).
  - Follow-through: ikincil öğe 2-4 kare gecikir.
  - Stagger 2-4 kare (`a.sirali(i)`).
  - Her grafik aynı scale-pop olmaz. Aile içinde maske, çizim (`strokeDashoffset`), kaydırma ve ölçek dönüşümlü kullanılır.
- **Zamanlama:**
  - Giriş 0.3-0.5 sn.
  - Çıkış girişten kısadır.
  - Süre sınırları: ikon 1-1.6 sn, alt bant 2.5-4 sn, kart en çok 3 sn.
- **Renk, font, köşe, gölge, doku:** yalnız `useTema()` ve `../tema.ts` yardımcıları kullanılır (`golge`, `panelArka`, `kenar`, `yigin`, `harf`, `rgba`). Sabit renk ve font yazılmaz; `tests/test_sabit_renk.py` yakalar.
- **İkon:**
  - Yalnız ikon çizilir; disk, halka, kutu ya da rozet zemin konmaz.
  - Okunurluk koyu dış kontur (`t.renk.ikon_kontur`, `KONTUR_EK`) ve tema gölgesiyle sağlanır.
  - Çizgi kalınlığı `ikonKalinlik()` (cekirdek/olcu.ts), uç `round`.
  - `meta.en_kucuk_px` en az 180.
- **Kutu:** bileşen yalnız kendisine verilen `kutu` içine çizer; konumu yerleşim seçer. `hedef` verilirse (call-out ve çizim) ona işaret eder.
- **Kart:** zemin varsa `panelArka(t)` kullanılır; düz siyah zemin yasaktır. Varsayılan saydam zemin üstüne panel.
- **Geçiş (`gecis` ailesi):** `@remotion/transitions` sunumu (`TransitionPresentation`) yazılır. Bir sonraki çekim her karede görünür olmalı; düz tam kare renk en çok 2 kare sürer.

## Bitti ölçütü
1. `cd studio && npx tsc --noEmit` temiz.
2. `npm run sema`, ardından `npx vitest run --config web/vite.config.ts remotion/motion` geçer.
3. Raporda her bileşen için tek satır: ad, ne zaman, hareket fikri (hangi aile tekniği), lisans kaynağı.
