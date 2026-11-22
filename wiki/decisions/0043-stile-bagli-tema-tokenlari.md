---
type: decision
title: "Stile bağlı tema token'ları: her katman seçili stili izler"
status: accepted
tags: [adr, stil, tema, token, motion, altyazi, remotion]
created: 2026-11-19
updated: 2026-11-19
sources: []
---

# ADR 0043: Stile bağlı tema token'ları

## Bağlam
`instagram/1` projesinin AI edit'i (stil `temiz-kurumsal`) kötü çıktı. Kontak sayfası ve kod incelenince şu görüldü:

1. Tema CSS'i yalnız beş renk, font, `kose` ve `cizgi` taşıyordu. Stilin yapısı (kontur, gölge türü, doku, adımlı hareket) hiçbir grafiğe ulaşmıyordu.
2. `studio/remotion/MotionMetin.tsx` Montserrat'ı, `#FF7A00` vurguyu, koyu `PANEL`'i ve gri ara yazıyı sabit yazıyordu. Seçili stil ne olursa olsun metin grafikleri aynı görünüyordu.
3. Motion HTML şablonlarında 182 kez `#FF7A00` ve 87 kez Montserrat yedek değeri vardı.
4. Altyazı [[0014-altyazi-standardi-ve-repo-entegrasyonu|ADR 0014]] ile her videoda turuncuydu; mavi kurumsal stille çatışıyordu.
5. Katalogdaki 31 stilin 12'si kendi paleti olmadan başka bir temaya eşleniyordu: `piksel-8bit` `piksel-16bit`'e düşüyordu, `editoryal-acik` kartı `editorial-acik` temasını kullanıyordu.

Kullanıcı stil seçilince her katmanın (altyazı, metin grafiği, alt bant, ikon, ok, çerçeve, geçiş, sahne kartı, sayaç, grafik, tablo, CTA) o stile uymasını istedi.

## Seçenekler
- Her bileşene stil adına göre `if` yazmak: 31 stil × 9 metin türü, bakımı imkânsız. Reddedildi.
- Yalnız renk değişkenlerini genişletmek: yapı (köşe, kontur, adım) yine ulaşmaz. Reddedildi.
- **Tek token şeması** (seçildi): katalog kartı tek kaynak; `vedit stil-katalog kur` her stil için aynı token'ı CSS'e (motion HTML) ve JSON'a (Remotion, Python) yazar. Bileşenler token okur, sabit değer yazmaz.

## Karar

| Konu | Karar |
|---|---|
| Şema | `src/vedit/tema_token.py`: `renk` (vurgu, ikincil, ikincil_yazi, zemin, yazi, soluk, olumlu, olumsuz, ikon_kontur, ikon_golge), `font` (baslik, govde, mono, rakam, ağırlık, izleme, harf), `sekil` (kose, cizgi, kontur, golge yok/yumusak/sert/glow, doku yok/gren/kagit/halftone/tarama/piksel, piksel katsayısı), `hareket` (easing yumusak/keskin/yay/basamak, sure_kat, davranis titresim/titreme-giris, adim_fps), `altyazi`, `gecis`, `kacin` |
| Kaynak | `library/stiller/katalog.json`: her kartın kendi paleti ve `token` bloğu var; `motion_tema` alanı kalktı. Çıktı `library/motion/tema/<id>.css` ve `<id>.json` |
| Kontrast | `tema.kontrast` ile ölçülür: yazı/zemin en az 4,5:1, vurgu, soluk, olumlu, olumsuz en az 3:1. Tutmayan renk tonu korunarak kaydırılır, kayma çıktıda yazılır. `ikincil` stilin dolgu rengidir, kaydırılmaz; yazı olarak kullanılırsa `ikincil_yazi` |
| Font | Yalnız ücretsiz (OFL) ve `library/fonts/fonts.json`'da kayıtlı; Türkçe glif (ş ğ ı İ ç ö ü) fontTools ile denetlenir. Eklenen: Pixelify Sans, VT323, Caveat, Bungee. Silkscreen (Türkçe glifsiz) ve Monoton (küçük boyutta okunmaz) alınmadı |
| Kapı | `tema_token.eksik_temalar()` boş olmalı (`tests/test_tema_token.py`, `vedit kontrol`): her katalog stilinin CSS + JSON'u var ve kartla aynı; her stil paketinin `motion_tema`'sı çözülüyor |
| Paket teması | Elle ya da `stil-uret` ile yazılmış paket başka temaya eşlenmez: `tema_token.paketten_yaz` paketin `tokens.json` renklerinden `paket-<stüdyo>-<ad>` teması üretir (ilk örnek `paket-ugc-ornek-marka`) |
| Remotion | `studio/remotion/tema.ts`: `TemaSaglayici`, `useTema`, panel, gölge, doku, köşe, easing, `adimKare` (adımlı stil), `titresim`, `titremeOpaklik`. Token `kurgu.render.json → tema` (render) ve `GET /api/kurgu → tema` (Stüdyo önizlemesi) ile gelir; yoksa `varsayilan.json` |
| Metin grafikleri | `MotionMetin.tsx` sabitsiz: font, renk, köşe, kenar, gölge, doku, easing ve adım token'dan. Klipteki `metin_stil.renk/vurgu/arka` yalnız istisna |
| Motion HTML | Yedek renk ve Montserrat kalktı; her şablon `tema/varsayilan.css`'e bağlanır, seçili tema sonra eklenip onu ezer. Beyaz saydamlıklar `color-mix(var(--yazi))`. Rakamlar `--font-rakam` |
| Adım ve piksel | `pano.render` adımlı stilde zamanı `adim_fps`'e yuvarlar; piksel stilde kareyi küçültüp alfayı eşikler ve en yakın komşuyla büyütür (hale kalmaz). Önbellek anahtarı tema JSON'unu da içerir |
| Vendor | SplitReel: `temaUygula` giriş katmanı `T` ve `F`'yi ezer, köşe `rr()` ile çarpılır. Panolar: `vedit pano --tema <ad>` `.ebs` değişkenlerini ezer. Vendor'ın iç hex'leri tek tek yazılmadı (kullanıcı kararı) |
| Sabit renk testi | `tests/test_sabit_renk.py`: kendi render kodumuzda (studio/remotion, motion HTML, reel_kit, SplitReel, src/vedit) sabit renk ve font adı yalnız `scripts/renk_beyaz_liste.json`'daki gerekçeli sayıya kadar |
| Stil dışı renk | `kurgu_kalite.uyarilar(k, tema)`: klipteki hex stilin paletinden ΔE76 > 14 uzaksa `STIL_DISI_RENK` (uyarı, render'ı durdurmaz). ai-edit isteği klip rengi yazdırmaz |
| Altyazı | Stil seçili değilse ADR 0014 standardı aynen. Stil seçiliyse altyazı stilin `altyazi` token'ı: gövde beyaz, okunan kelime stilin vurgusu (kontur rengine 4,5:1'e kaydırılmış), koyu kontur; serif ve el yazısı başlık fontunda gövde fontu. Kutu, pop, solma yalnız token açıkça isterse |

**Kabul örneği `piksel-8bit`:** NES paletinden 5 renk (+ olumlu/olumsuz), Pixelify Sans her yerde (altyazı dahil), rakamlar VT323 (Pixelify'da 5 ile S aynı çiziliyor), köşe 0, kontur 6, sert gölge, `steps()` easing, 8 fps adımlı hareket, piksel katsayısı 2 (4'te küçük rakam okunmuyordu), `crispEdges`, geçiş `piksel-cozunme`. CSS'inde gradyan, blur ve Montserrat yok.

## Sonuçlar
- Aynı şablon iki stilde render edildiğinde font, renk, köşe ve piksel dokusu açıkça farklı (`grafik-cubuk`, `altbant-konu`, `baslik-acilis` ile denendi).
- Şablon gövdeleri `--kontur`, `--golge-filtre`, `.tema-doku` sınıflarını henüz kullanmıyor; gölge ve kontur yalnız Remotion metin grafiklerinde görünüyor. Motion kalite geçişi (ikon yeniden çizimi) şablonları bu sınıflara bağlar.
- Katalog kartı değişince `vedit stil-katalog kur` çalışmazsa kapı testi kırmızı olur (kart ile JSON karşılaştırılır).
- Kartı olmayan eski temalar (`kinetik-ui`, `pastel`, `duz-pop`, `termal-kizilotesi`, `xray-sema`, `analitik-uzay`, `seramik-mozaik`, `piksel-16bit`) CSS'lerinden türetilen JSON'la çalışır; `editorial-acik.css` silindi, ad `editoryal-acik`'e takma ad olarak gider.

## İlgili kod
`src/vedit/{tema_token,stil_katalog,stil,motion,pano,kurgu,kurgu_kalite,fizik,hizli,aiedit,cli}.py`, `src/vedit/studio/app.py`, `studio/remotion/{tema.ts,MotionMetin.tsx,Kurgu.tsx,fizik/FizikSahne.tsx}`, `openmontage/remotion-composer/src/SplitReel.tsx`, `studio/web/src/{zaman/depo.ts,paneller/Monitorler.tsx}`, `library/stiller/katalog.json`, `library/motion/tema/`, `library/fonts/`, `scripts/renk_beyaz_liste.json`, `tests/{test_tema_token,test_sabit_renk}.py`.
