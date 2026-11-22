---
type: source
title: "Motion grafik araştırması: Remotion ekosistemi ve açık kaynak şablonlar"
tags: [motion, remotion, arastirma]
created: 2026-11-12
updated: 2026-11-12
url: (ana kaynakların listesi gövdede, "Kaynak tablosu" bölümü)
author: Claude (araştırma ajanı)
---

# Motion grafik araştırması: Remotion ekosistemi ve açık kaynak şablonlar

## Özet

Amaç, kurgulara profesyonel motion grafik eklemek için bu motorun (Remotion 4.0.484, `studio/remotion/Kurgu.tsx`, `SplitReel.tsx`, HTML pano) üstüne ücretsiz ve lisansı net kaynaklardan ne alınabileceğini bulmaktı. Sonuç: en az riskli ve en çok getirili yol, Remotion'un kendi paketlerini (`@remotion/transitions`, `rough-notation`, `shapes`, `paths`, `layout-utils`, `rounded-text-box`, `motion-blur`) kullanmak ve MIT lisanslı topluluk şablonlarından (özellikle `reactvideoeditor/remotion-templates`) yalnızca fikir ve matematik almaktır. Her şablon Kurgu.tsx'in `keyframe` ve `SplitReel` yardımcılarına (`Reveal`, `ez`, `OUT4`) yeniden yazılmalıdır; paket olarak içeri almak gereksiz bağımlılık ve görünüş tutarsızlığı getirir. Doğrulamalar 2026-11-12'de sayfalar açılarak yapıldı; açılamayanlar "(doğrulanmadı)" ile işaretli.

## Ana çıkarımlar

1. **Remotion lisansı şirket maddesi taşır.** Ücretsiz: bireyler, 3 veya daha az çalışanlı işletmeler, kâr amacı gütmeyenler, değerlendirenler. Profesyonel kullanım ve ticari video üretmek serbest; Remotion kodunu kopyalayıp kendi türev ürününü satmak yasak. Daha büyük işletme ücretli Company License ister. Üç kişiyi aşarsanız bütçe 0 USD kuralı bozulur. Kaynak: <https://github.com/remotion-dev/remotion/blob/main/LICENSE.md>. 5.0'da koşullar hafifçe değişecek.
2. **Kurulu sürüm eski.** `rough-notation` 4.0.490, `@remotion/effects` (lightLeak) 4.0.500, `mac-cursors` 4.0.513 ve sonrası; projede 4.0.484 var. Bu üçü için `npx remotion upgrade` gerekir; yükseltme ayrı bir karar ve test işidir.
3. **Hazır "profesyonel" paket yok; bileşen kütüphanesi var.** Topluluk repoları (81 şablon, kütüphane, sahne seti) tek tek MIT, ama çoğu İngilizce-ASCII varsayar ve Remotion'un 4.x API'sine bağlıdır. Türkçe glifi (İ ı ş ğ ç ö ü) Montserrat 800 ile bizim yazı tipi hattımız sağlar; şablonlardan font kodu alınmaz.
4. **Hera'nın pratik rehberi** kısa dikeyde grafiği "işe göre" kullanmayı söyler: açılışta konu etiketi, bağlam kartı, 1-2 callout, ilgi sıfırlamak için grafik/zoom, son karede CTA. Görsel durum her 2-4 saniyede değişmeli, her grafiğin bir işi olmalı (göster, karşılaştır, vurgula, geçiş, kapat). Kaynak: <https://hera.video/blog/motion-graphics-for-youtube-shorts-and-reels>.
5. **GSAP artık ücretsiz** (Webflow sonrası), eklentileri dahil; tek kısıtlama Webflow'un animasyon oluşturucusuyla yarışan kodsuz görsel araç yapmaktır. Pano (HTML) hattında GSAP güvenle kullanılır. Kaynak: <https://gsap.com/community/standard-license/>.
6. **Lottie dosyaları kopyalama hakkı taşır:** LottieFiles Simple License ticari kullanıma izin verir, atıf gerekmez, ama dosyayı aynı lisansla dağıtmak ve LottieFiles'tan toplu derleyip rakip hizmet kurmak yasak. Tek tek animasyon seçip videoya gömmek serbest. Her dosyanın sayfasındaki kendi lisansı kontrol edilmeli.

## Kaynak tablosu

| Kaynak | URL | Lisans | Sinyal | Ne alınır |
|---|---|---|---|---|
| Remotion çekirdek + lisans | https://github.com/remotion-dev/remotion | Remotion License (şirket maddesi) | resmî | Zaten kullanılıyor; `packages/` listesinde light-leaks, mac-cursors, rough-notation, rounded-text-box, starburst, shapes, motion-blur, noise, paths, lottie, rive, gsap, animated-emoji, sfx, captions, layout-utils var |
| `@remotion/transitions` | https://www.remotion.dev/docs/transitions/presentations | Remotion License | resmî | fade, slide, wipe, flip, clockWipe, iris, cube; ek olarak pushCut, zoomBlur, dissolve, ripple, swap, none (doğrulandı) |
| `@remotion/rough-notation` | https://www.remotion.dev/docs/rough-notation/api | MIT (sayfada) | resmî, 4.0.490 | Box, Circle, Underline, Highlight, Bracket, CrossedOff, StrikeThrough: el çizimi vurgu |
| `@remotion/rounded-text-box` | https://www.remotion.dev/docs/rounded-text-box | MIT | resmî | `createRoundedTextBox()` çok satırlı yuvarlak köşeli SVG kutu; "altyazı kutusu" yasak (ADR 0014), ama başlık/etiket arkası için uygun |
| `@remotion/layout-utils` fitText | https://www.remotion.dev/docs/layout-utils/fit-text | Remotion License | resmî | Metni genişliğe sığdırır; font yüklenmeden çağrılmamalı, Türkçe uzun kelimelerde taşmayı önler |
| `@remotion/motion-blur` | https://www.remotion.dev/docs/motion-blur | Remotion License | resmî | `Trail`, `CameraMotionBlur` (shutterAngle, samples); kare kopyalayıp harmanladığı için render yavaşlar (doğrulanmadı: ölçü yok) |
| `@remotion/effects` lightLeak | https://www.remotion.dev/docs/light-leaks | belirtilmemiş (doğrulanmadı) | 4.0.500+ | WebGL ışık sızıntısı geçişi; `TransitionSeries.Overlay` ile |
| `@remotion/mac-cursors` | https://www.remotion.dev/docs/mac-cursors | Remotion License | 4.0.513+ | `<MacOSCursor>` imleç/tıklama animasyonu |
| `@remotion/animated-emoji` | https://www.remotion.dev/docs/animated-emoji | paket Remotion; varlıklar CC BY 4.0 | 4.0.187+ | Animasyonlu emoji; CC BY atıf ister (yayın.md'ye not) |
| `@remotion/lottie` | https://www.remotion.dev/docs/lottie | sayfa 404 (doğrulanmadı) | `packages/` içinde var | Lottie JSON oynatma |
| `template-tiktok` | https://github.com/remotion-dev/template-tiktok | lisans belirtmez, Remotion maddesine yollar | 308 yıldız | Whisper tabanlı altyazı; bizde altyazı hattı hazır, yalnız "kelime vurgu" fikri |
| `reactvideoeditor/remotion-templates` | https://github.com/reactvideoeditor/remotion-templates | MIT | 291 yıldız, yalnız 5 commit | 81 şablon: Stat Counter, Progress Bars/Steps, Text Highlight, Lower Third, Chapter Title, Quote Card, Zoom Pulse, Camera Shake, Notification Pop, Picture in Picture, Split Screen. Kod değil matematik/yapı alınır |
| `av/remotion-bits` | https://github.com/av/remotion-bits | MIT | 516 yıldız, 149 commit | AnimatedText, GradientTransition, particle-system; `jsrepo` ile tek bileşen kopyalanabilir |
| `Curvable/motion` | https://github.com/Curvable/motion | MIT | 22 yıldız, 2 commit | Typewriter, Slide reveal, Cascading text, StatsGrid; zayıf bakım, yalnız ilham |
| Motion Canvas | https://github.com/motion-canvas/motion-canvas | MIT | 19,8 bin yıldız | Generator tabanlı zaman çizelgesi; ayrı motor, port yerine kavram (sıralı animasyon) |
| GSAP lisansı | https://gsap.com/community/standard-license/ | GSAP Standard (ticari ücretsiz) | resmî | Pano HTML'inde zaman çizelgesi, SplitText |
| Magic UI | https://github.com/magicuidesign/magicui | MIT | 23,2 bin yıldız | Number ticker, text efektleri; framer-motion/Tailwind'e bağlı, Remotion'da çalışmaz, yalnız görsel fikir |
| React Bits | https://github.com/DavidHDev/react-bits | MIT + Commons Clause | 51,8 bin yıldız | Ticari satış kısıtı var; kod alma, yalnız bakış |
| Aceternity UI | (doğrulanmadı) | (doğrulanmadı) | - | Sayfa açılmadı; kullanma |
| Rive | https://github.com/rive-app/rive-react | MIT (çalışma zamanı) | 1,2 bin yıldız | `@remotion/rive` var; `.riv` dosyası üretmek editör gerektirir, atlanır |
| LottieFiles lisansı | https://lottiefiles.com/page/license | Lottie Simple License | resmî | Tek tek ticari kullanım serbest; toplu derleme yok |
| OpenScreen | https://github.com/siddharthvaddem/openscreen | MIT | 40 bin yıldız, arşivlendi; devamı getopenscreen/openscreen | Otomatik zoom, imleç yumuşatma, tık efekti fikirleri |
| Reframed | https://github.com/jkuri/reframed | MIT | 172 yıldız, yalnız macOS | Tık kümesinden otomatik zoom anahtarı fikri |
| Cap | https://github.com/CapSoftware/Cap | çoğu AGPLv3 | 24,9 bin yıldız | Kodu alma (AGPL); yalnız ürün fikri |

## Öncelikli 10 şablon

Yollar: (a) Remotion bileşeni, (b) `metin` klibi animasyon stili, (c) HTML pano, saydam webm, (d) Lottie. Emek: S küçük, M orta, L büyük. Her şablon `kurgu.json`'da mevcut klip türleriyle ifade edilir; keyframe x, y, scale, opacity yetmiyorsa bileşen kendi prop'unu alır.

| # | Şablon | Amaç, ne zaman | İlham | Yol | Emek | Gerekli prop'lar |
|---|---|---|---|---|---|---|
| 1 | Anahtar kelime pop | Konuşmadaki tek kelimeyi vurgula; cümle başına en çok 1 | Hera "vurgula" işi; remotion-templates Popping Scale Text | (b) | S | `metin`, `renk` (turuncu #FF7A00 yalnız okunan kelime kuralını bozmasın), `baslangic`, `sure`, `giris` (pop/slide), `konum` |
| 2 | Sayaç / rakam | İstatistik, fiyat, yüzde; kanıt anı | remotion-templates Stat Counter | (a) `stat` türünü genişlet | S | `deger`, `onEk`, `sonEk`, `ondalik`, `sure`, `bicim` (tr: 1.250,5) |
| 3 | Vurgu kutusu / daire ekran görüntüsünde | Ekran kaydı veya ekran görüntüsünde yeri göster | `@remotion/rough-notation` Box/Circle/Underline | (a) | M | `hedef` {x,y,g,y}, `tur` (kutu/daire/alt çizgi), `renk`, `ilerleme`, `kalinlik` |
| 4 | Ok callout etiketi | Üründe/UI'da bir ayrıntıyı adlandır; 1-2 adet | Hera callout etiketleri | (a) | M | `metin`, `hedef` {x,y}, `yon`, `renk`, `giris` |
| 5 | Adım listesi | "3 adımda..." anlatımı | remotion-templates Progress Steps/Animated List | (a) `steps` türü hazır, tema ve zamanlama ekle | S | `maddeler[]`, `vurguIndeksi`, `adimSuresi` |
| 6 | İlerleme çubuğu | Uzun videoda sürüyü göster, tutma | remotion-templates Progress Bars | (a) | S | `oran` veya `baslangic/bitis`, `konum` (üst güvenli alan), `renk` |
| 7 | Bölüm başlık kartı | YouTube 16:9 bölüm geçişi | remotion-templates Chapter Title | (a) + `@remotion/transitions` | M | `numara`, `baslik`, `altBaslik`, `sure`, `gecis` (wipe/slide) |
| 8 | Alt bant (lower third) | Konuşmacı/konu adı, ilk 5 sn | remotion-templates Lower Third; Remotion elements sayfası (açılmadı, doğrulanmadı) | (a), fitText ile | M | `ad`, `unvan`, `renk`, `sure`, `taraf` |
| 9 | Zoom vuruşu + ekran vurgusu | Kesim sertliğini gizle, cümle vurgusu | remotion-templates Zoom Pulse; OpenScreen otomatik zoom | (b) keyframe preseti `scale 1 → 1.12 → 1.0` | S | `merkez` {x,y}, `guc`, `sure`, `ez` (OUT4) |
| 10 | Emoji / çıkartma pop | Duygu vurgusu, sosyal ton | `@remotion/animated-emoji`; Lottie | (d) veya (a) | M | `emoji` ya da `lottie` dosyası, `konum`, `boyut`, `donme` |

Sıra mantığı: 1, 2, 5, 6, 9 küçük ve her videoda işe yarar; 3, 4, 8 en çok görsel fark yaratır; 7 YouTube için; 10 lisans/atıf nedeniyle sonda. İmleç tıklaması (`@remotion/mac-cursors`) yükseltme sonrası 11. aday.

## Kullanma listesi (yapma)

- **Aceternity, Magic UI, framer-motion bileşenleri doğrudan:** Tailwind/framer bağımlılığı, Remotion'un kare-deterministik modeliyle çelişir; framer animasyonları `useCurrentFrame` ile sürülmez. Aceternity lisansı doğrulanmadı.
- **React Bits:** MIT + Commons Clause; ticari kısıt riski, 51,8 bin yıldız ikna etmesin.
- **Cap:** AGPLv3; koda dokunma.
- **Pazarlama paketleri (RenderComp 1.400+ bileşen, 299 USD):** ücretli, özel repo. Bütçe 0.
- **Ağır bağımlılıklar:** `@remotion/three`, Skia, particle-system, WebGL ışık sızıntısı render süresini şişirir; taslak hızı (ADR 0019) bozulur.
- **AI slop görünümü:** parıltılı gradient + glitch + her kelimede pop + 3D dönen kart; Matrix Rain, Bokeh, Starfield türü arka planlar. Bizim kuralımız: tek renk, tek yazı tipi, bir grafik bir iş.
- **Altyazıya kutu/gölge/pop:** ADR 0014 yasak; `rounded-text-box` altyazıda kullanılmaz.
- **Lottie dosyasını toplu indirip kütüphane yapmak:** LottieFiles lisansı toplu derlemeyi yasaklar.
- **CC BY emojiyi atıfsız yayınlamak.**

## Projeye etkisi

- `library/motion/manifest.json` boş; `always[stüdyo][rol]` yuvaları bu şablonlarla dolar. Yeniden kullanılabilir olan (sayaç, alt bant, ilerleme çubuğu) `library/motion/custom/<id>/` altında kaydedilmeli (ADR 0012); lisans notu `kaynak` alanına yazılır.
- Her şablon önce `studio/remotion/Kurgu.tsx` içine değil, ayrı bileşen dosyasına yazılmalı; SplitReel'deki `Reveal`, `ez`, `OUT4` paylaşılır ki ritim tek dilde kalsın.
- Yeni `kurgu.json` klip alanları için `vedit kurgu-denetle` şeması genişletilmeli (hedef, ilerleme, deger).
- Karar önerisi: wiki'ye ADR (ör. 0030 "Motion şablon kitaplığı") açılmalı; lisans tablosu ekli. Bu araştırma kodu değiştirmedi.
- Remotion şirket lisansı: ekip 3 kişiyi aşarsa maliyet doğar; ADR'a yazılmalı.

## Açık sorular

1. `npx remotion upgrade` ile 4.0.513+'a çıkmak kabul mü? (rough-notation, lightLeak, mac-cursors için gerekli; CLI hızı ve ADR 0016 renk testi tekrar koşulmalı.)
2. `@remotion/lottie` ve `@remotion/rive` sayfaları açılamadı veya incelenmedi; Lottie yolu (d) için küçük bir deneme gerekir.
3. `@remotion/effects` ve `rough-notation` kullanım lisansı: sayfada MIT yazan yalnız rough-notation ve rounded-text-box; diğerleri Remotion License ya da belirtilmemiş. Kesin metin LICENSE dosyasından okunmalı.
4. Remotion resmi "elements" sayfası (alt bant): URL 404 verdi; arama sonucu var ama içerik doğrulanmadı.
5. Profesyonel pratik için sayılara dayalı kaynak zayıf: pop süresi, zoom sıklığı, alt bant yeri için Hera dışında doğrulanmış kaynak bulunamadı. `viral-kurgu` ve `usta-editor` skill'lerindeki ölçümlerle çapraz kontrol gerekir.
6. Panodaki 267 kartın hangileri şeffaf webm olarak yeniden kullanılabilir? (Bu araştırma `library/boards` içeriğini incelemedi.)
7. Motion blur render maliyeti ölçülmedi; deneme çıktısıyla `vedit kaizen` süresine bakılmalı.
