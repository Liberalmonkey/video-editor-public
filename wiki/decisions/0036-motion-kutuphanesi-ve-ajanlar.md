---
type: decision
title: "Motion kütüphanesi: kaynaktan üretim, parametrik şablon, tema, yoğunluk hedefi ve motion alt ajanları"
status: accepted
tags: [adr, motion, kutuphane, ai-edit, studyo, ajan, antigravity]
created: 2026-11-13
updated: 2026-11-25
sources: ["[[2026-11-13-motion-kutuphane-arastirmasi]]", "[[2026-11-12-motion-grafik-arastirmasi]]"]
---

# ADR: Motion kütüphanesi ve motion alt ajanları

> [!note] Güncellendi 2026-11-20: native bileşenler `studio/remotion/motion/` altındadır, galeri `vedit motion kontak`; dış varlıklar `library/motion/dis/` ([[0045-native-motion]], [[0046-dis-varlik-ve-lisans]]). Native karşılığı onaylanan HTML kayıtları `library/motion/arsiv/`'e taşınır, render sürer.

## Bağlam
[[0031-motion-grafik|ADR 0031]] ile dokuz saydam motion klibi geldi. Kullanıcı 2026-11-13'te daha fazlasını istedi: zengin ve profesyonel bir kütüphane, AI edit'in bunu sık kullanması, kullanıcının Stüdyo'dan istediği grafiği ekleyebilmesi, GitHub'daki motion ve stil skill'lerinin projeye girmesi, işin farklı alt ajanlara bölünmesi. Eski yapıda klipler sabitti (yazı, renk değişmezdi), manifest elle yazılıyordu, Stüdyo'da düz satır listesi vardı ve ajan isteğinde sıklık hedefi yoktu.

## Seçenekler
- Yeni `MotionMetin` türleri yazmak (Remotion). Her tür motor kodu ister, alt ajanlar aynı dosyada çakışır, stil çeşidi kodla çoğalır.
- Dış skill'lerin kendi render hatlarını kullanmak (bang-motion puppeteer, huashu motoru). Üç ayrı hat, üç ayrı bağımlılık.
- Mevcut `vedit pano` hattında HTML kaynak + `meta.json` sözleşmesi; parametre ve tema sayfaya dışarıdan verilir. Seçilen.

## Karar
| Konu | Karar | Neden |
|---|---|---|
| Kaynak sözleşmesi | `library/motion/custom/<id>/<id>.html` + `meta.json` (`title, kind, tags, ne_zaman, sure, w, h, loop, tam, param`) | Her kayıt kendi klasöründe; paralel ajanlar aynı dosyaya yazmaz |
| Üretim | `vedit motion kur [id...]`: saydam webm, `poster.jpg`, altı karelik `kontak.jpg`, manifest kaydı. `--onizle` manifesti yazmaz, `--manifest` yalnız manifesti yeniler | Manifest elle yazılmaz; kilitli kayıt yeniden üretilmez ([[0012-kutuphane-kit\|ADR 0012]]) |
| Ölçüm | `vedit motion olc`: alfa kanalı, boyut, kare sayısı, son karenin boşluğu (döngü hariç), geçişte orta karenin tam kapalılığı | Kontak sayfası son kareyi göstermez; gözle yakalanmayan kusur ölçülür |
| Render | Chrome `--disable-threaded-animation` ile açılır; motion klibinde son kare tam süre anında alınır (`pano.render(son_tam=True)`) | Bileşimci iş parçacığı sarılan kareyi bazen eski hâliyle çiziyordu (16 denemede 4); çıkışı süre sonunda biten klip yarı saydam karede kalıyordu |
| Şablon | `meta.json`'da `param` olan kayıt şablondur; sayfa `window.PARAM` okur (`pano.ac`, `add_init_script`) | Yazısı ve değeri değişen grafik: alt bant, grafik, alıntı, sayaç |
| Kurguda şablon | `tur: "motion"` + `sablon: {ad, param, tema}`; `kurgu.motion_bagla` webm'i `work/public/motion/<ad>-<özet>.webm` olarak üretir, kaynağı bağlar | Ajan kabuk komutu çalıştıramaz; `shot_bagla` ile aynı kalıp. Özet (HTML, tema, parametre, boyut) değişmedikçe yeniden render yok |
| Tam kare | `tam: true` şablon sekans boyutunda çizilir, sayfa `vw`/`vh` kullanır | Tek kaynak 9:16 ve 16:9'da çalışır |
| Tema | `library/motion/tema/<ad>.css`, CSS değişkenleri (`--vurgu, --ikincil, --zemin, --yazi, --soluk, --font, --agirlik, --kose, --cizgi`); `kurgu.motion_tema`, klipte `sablon.tema` ezer | Şablon sayısı tema sayısıyla çarpılır; on tema |
| Okunurluk | Yazı her zaman `--zemin` ya da `--vurgu` dolgulu panel üstünde | Açık temada koyu yazı videonun üstünde kaybolur |
| Denetim | `kurgu._motion_hatalari`: bilinmeyen şablon, bilinmeyen parametre, uzun metin, aralık dışı sayı, bilinmeyen tema | Render'da sessizce yanlış çıkmasın |
| Yoğunluk | `kurgu.motion_yogunlugu`: grafik olayı (sahne, motion metin, motion klibi, hazır efekt) ortalama aralığı ve hedefin iki katını aşan boşluklar. Hedef `yogun` 4 sn (dikey) / 8 sn (YouTube), `orta` 6,5 / 12, `az` denetimsiz | Kullanıcı "sık sık kullansın" dedi; ölçülmeyen hedef tutulmaz |
| AI edit | `vedit ai-edit --motion az\|orta\|yogun` (varsayılan `yogun`). Katalog türe göre gruplanır, `ne_zaman` ve şablon parametreleri yazılır. Seyrekse bir ek tur istenir; ikinci kez seyrekse yalnız uyarı basılır, kurgu geri alınmaz | Yoğunluk hata değil tercihtir |
| Stüdyo | Kütüphane > Motion: poster ızgarası, üstüne gelince oynatma, tür çipleri, arama, şablon parametre formu, tema seçimi, oynatma kafasına ekleme. `POST /api/motion-sablon/{stüdyo}/{ad}`. AI Edit penceresinde yoğunluk seçimi | Kullanıcı istediği grafiği kendisi ekler |
| Dış repolar | `bang-motion`, `huashu-art-motion`, `claude-drawing-skill` (hepsi MIT) `library/vendor/` altında; `.claude/skills/` içinde ince sarmalayıcılar, `disable-model-invocation: true` | Çıktı yine bizim sözleşmeye çevrilir; tek render hattı kalır |
| Alınmayanlar | `vox-explainer-skill` kurulmadı (Atlas Cloud, film başına 3-8 USD); editoryal kolaj dili `kupur-kolaj` temasına kendi değerlerimizle yazıldı. huashu'nun MIT dışı parçaları (`demos/` karakter kareleri ve Clawd içeriği, `reference_films/` içindeki `strokes.js`, `lib/fonts/`) `vendor` kopyasından silindi | Bütçe 0 USD; telif ve lisans riski taşıyan dosya depoda durmaz |
| Lisans denetimi | Kullanılan ve fikir alınan on bir kaynağın `LICENSE` dosyası 2026-11-13'te GitHub API ile okundu: on MIT, bir Apache-2.0. `vendor` kopyaları kendi `LICENSE` dosyasını taşır. Tema ve kayıt adlarında marka adı kullanılmaz; kütüphanede gerçek marka logosu, telifli karakter ve dış görsel yoktur | Kullanıcı 2026-11-13: telif ve lisans sorunu çıkarmayacak kaynak |
| Alt ajanlar | `motion-arastirmaci`, `motion-tasarimci`, `motion-denetci`; kaynak `.claude/agents/`, kopyalar `scripts/ajan_esitle.py` ([[0023-coklu-ajan\|ADR 0023]]) | Araştırma, üretim ve denetim ayrı bağlamda |
| Motor | Araştırma ve denetim Antigravity (Gemini), üretim Claude `Agent` aracı. agy iki kez hata verirse kullanıcıya söylenir, adım Claude'a geçer | Kullanıcı kararı 2026-11-13; ikinci göz farklı model olsun |

## Sonuçlar
- [[0031-motion-grafik|ADR 0031]]'in "dış kod kopyalanmadı" satırı kütüphane için hâlâ doğru: `vendor` altındaki repolar kılavuz ve fikir kaynağıdır, kütüphane kayıtları proje yapımıdır. Remotion 4.0.484'te kalır, yeni `MotionMetin` türü eklenmedi.
- Şablon ilk kullanımda render edilir (kare kare, birkaç saniye ile yirmi saniye arası); sonraki kullanımlar önbellekten gelir. Stüdyo'da "Oynatma kafasına ekle" bu süre boyunca bekler.
- Şablon klibinin süresi şablonun süresini aşarsa klip son karede (boş) kalır; şablon süresi parametreyle uzamaz.
- `kit.json` motion yuvaları (`zoom_in`, `zoom_out`, `gecis`, `subscribe`) yine boş; kilit kararı kullanıcıda.
- Yoğunluk ölçümü grafiğin anlamını ölçmez; anlamsız grafik `denetim` skill'inin slop denetimine kalır.
- Favori işaretleme ve temanın Stüdyo'da proje düzeyinde seçimi yapılmadı; tema şablon eklerken seçilir ya da `kurgu.json`'da `motion_tema` yazılır.

> [!note] Güncellendi 2026-11-18
> `motion_tema: varsayilan` artık otomatik demektir; sabit klipler de render anında etkin temayla yeniden renklenir: [[0042-stil-katalogu-ve-video-temasi]].

## İlgili kod
- `src/vedit/motion.py`, `src/vedit/pano.py` (`ac`, `render`: `param`), `src/vedit/kurgu.py` (`motion_bagla`, `motion_yogunlugu`, `YOGUNLUK`, `_motion_hatalari`), `src/vedit/schemas.py` (`Klip.sablon`, `Kurgu.motion_tema`), `src/vedit/aiedit.py` (`_motion_katalogu`, `_yogunluk_kurali`, `calistir`), `src/vedit/cli.py` (`motion`, `ai-edit --motion`)
- `src/vedit/studio/app.py` (`motion_sablon`), `src/vedit/studio/kutuphane.py`, `src/vedit/studio/isler.py`
- `studio/web/src/paneller/MotionPaneli.tsx`, `KutuphanePaneli.tsx`, `IslerPaneli.tsx`, `studio/remotion/tipler.ts`
- `library/motion/custom/`, `library/motion/tema/`, `library/vendor/{bang-motion,huashu-art-motion,claude-drawing-skill}/`
- `.claude/agents/motion-*.md`, `.claude/skills/{bang-motion,huashu-art-motion,claude-drawing}/`, `tests/test_motion.py`

> [!note] Güncellendi 2026-11-19
> İkonların "`--vurgu` disk + `--zemin` çizgi" ortak dili kalktı ([[0043-stile-bagli-tema-tokenlari]]): 12 `ikon-*` ve `onay-tik` arka şekilsiz yeniden çizildi; gövde `--vurgu`, ikincil parça `--ikincil`, okunurluk tek SVG filtresiyle (`--ikon-kontur` ince dış çizgi, `--ikon-golge` gölge). Giriş ve çıkış stilin easing'ini (`--ease`, `--ease-cik`), çizgi ucu `--ucu` token'ını kullanır; ikonun kendi hareketi korundu. Kapı `tests/test_ikon_alfa.py`: ikon şeklinin (kontur ve gölge payı dahil) dışında alfa 0. Bütün motion HTML'den sabit yedek renk ve Montserrat kalktı; şablonlar `tema/varsayilan.css`'e bağlanır.

## Güncelleme (2026-11-25)
Kütüphane Kasam / Keşif / Arşiv olarak ayrıldı; kilitli varlık onayla kilidi kaldırılarak silinir, poster alfa kırpımlı doğru kareden üretilir. Ayrıntı [[0061-kasa-ve-kesif]].
