---
name: sahne-motoru
description: Kodla üretilen video sahnelerini içeriğine göre doğru motora atar, ajanlara dağıtır ve tek görsel dilde birleştirir. Kalem'in "her sahnenin kendi kalemi var" yöntemi bu projenin araçlarına uyarlandı. Animasyon sahnesi planlarken, "hangi motorla yapalım", "videolar birbirine benziyor", "AI slop gibi duruyor" dendiğinde ya da edit öncesi sahne tablosu gerektiğinde kullan.
---

# Sahne motoru

Kaynak: leodavincs/kalem (MIT) ve anlatım videosu, bkz. `wiki/sources/2026-11-02-kalem.md`.

Tek motorla çizilen videolar birbirine benzer. Bu yüzden önce sahnenin **içinde ne olduğuna** bakılır, sonra motor seçilir. Bir sahne bir motordur; yan işler yardımcı olarak girer.

## Sahnenin içinde ne var

| İçerik | Motor | Durum |
|---|---|---|
| Yazı, sayı, sayaç, bilgi kartı, alt bant, motion grafik, tam ekran sahne, animasyon videosu | **HyperFrames (HTML + GSAP), birincil motor** (ADR 0050) | Kurulu |
| Konuşmacı + kart, altyazı, timeline birleştirmesi, Stüdyo önizlemesi | HyperFrames: kurgu `studio/hf/derle.ts` ile derlenir (ADR 0051); Remotion yalnız derleyici yapamazsa | Kurulu |
| Gerçek 3D: kamera, ışık, gölge | Three.js, HyperFrames içinde (`hyperframes` skill'i) | Kurulu |
| Yay gibi zıplayan giriş | Anime.js adaptörü | Kurulu |
| Hazır vektör animasyon | Lottie adaptörü | Kurulu |
| Kurgu, çapraz geçişler, zoom | FFmpeg (`xfade`, `zoompan`) | Kurulu |
| Kendini çizen çizgi, eskiz | Paper.js | Kurulum gerekli |
| Patlama, toz, ışık, binlerce parça | PixiJS | Kurulum gerekli |
| Formül, grafik, şema | Manim | Kurulum gerekli |
| Hafif ya da ağır nesne fiziği | Matter.js / Rapier | Kurulum gerekli |
| 100'den fazla hazır shader geçişi | gl-transitions | Kurulum gerekli |

Varsayılan HyperFrames'tir: kurguya giren grafik `library/motion/hf/SOZLESME.md`'ye göre saydam kompozisyon olarak yazılır, klipte `hf: {ad, param}`. Native bileşenler (`bilesen`), metin grafikleri, sahneler, V1 geçişleri ve altyazı da HyperFrames'te derlenir (ADR 0051). Fizik ve karakter sahnesi render'da Remotion'dan ön render edilip HyperFrames'e video olarak gömülür; `dis/lottie` Remotion'da kalır. Seçim ve neden `work/edit/motor.json`, Stüdyo'da monitör rozeti.

Kurulum gerekliyse önce kullanıcıya sor, sonra motoru yalnız o proje için kur. Kurulu motorla aynı işi yapabiliyorsan ek motor kurma. Tablo bir zevk kararıdır; kullanıcı bir motoru beğenirse ya da beğenmezse tabloyu güncelle.

## Akış

1. **Sahnelere böl.** Senaryoyu 4–8 ana sahneye ayır. Kullanıcıya tablo göster: sahne, gündelik dille içerik, motor, neden. Örnek: "Bu sahnede artan bir sayı var, HyperFrames ile yapalım." Onay almadan üretim yok.
2. **Ortak dili yaz.** `<proje>/BRIEF.md`: palet, yazı tipi, doku, hareket karakteri, doğrulanmış gerçekler, her sahnenin tarifi. `<proje>/zaman.json`: fps, boyut, geçiş kare sayısı, sahne listesi. Farklı motorların tek elden çıkmış gibi görünmesi buna bağlıdır.
3. **Sahneleri üret.** Her sahne `sahneler/<NN-motor>/` altında: kaynak, `video.mp4`, `kontrol.png`, `olaylar.json`. Sahneler bağımsız olduğu için kullanıcı isterse paralel ajanlara dağıtılır. Dağıtmadan önce en az bir sahneyi kendin bitir: alt ajanlar stil ve API için çalışan bir örneğe bakar (ADR 0040, opus-video-skills). Her ajan kendi sahnesinin ilk ve son karesini ve giriş-çıkış kesimlerini kontak sayfasıyla verir.
4. **Kendi karelerine bak.** Üreten ajan kontrol karelerini inceler: taşan yazı, boş kare, Türkçe harf, anlamı yanlış çizim.
5. **Birleştir.** Görüntü: `ffmpeg xfade` ya da seçilen geçiş. Ses: sahnelerin `olaylar.json` listeleri ofsetlenip tek dosyada toplanır, `vedit olaysesi` çalışır.
6. **Kesim denetimi.** Birleştirmeden sonra her sahne sınırının iki yanındaki kareleri yan yana aç: palet, karakter ölçeği, ekran yönü ve hareket yönü (`motion-design` `references/kesim-surekliligi.md` vektör yasası) sürüyor mu.
7. **Taze denetçi.** Videoyu hiç görmemiş ajana yalnız kontrol karelerini ve BRIEF'i ver: "İzleyici burada 'olmaz öyle şey' der mi? Yanlış bilgi, eksik Türkçe harf, göz yoran parlama var mı?" Bulunanları düzelt, sonra kullanıcıya aç.

## Teknik sözleşme

- **Zaman kare numarasından gelir.** `Math.random` yok, tohumlu rastgele. Aynı komut aynı kareyi verir.
- **Görüntü olayı = ses olayı.** Bir şey düşüyor, sayı değişiyor, çizgi başlıyorsa motor aynı kare numarasını `olaylar.json`'a yazar. Ses bu listeden üretildiği için kaymaz.
- `olaylar.json`: `[{"kare": 12, "tur": "tik", "guc": "soft"}]`. Türler için `vedit olaysesi` tablosu: `sound-design`.
- **İlk kare dolu.** Siyahtan açılış yok. Son ~15 kare sakin; geçiş oraya biner.
- **Ani parlama yok.** Kareler arası parlaklık sıçraması küçük kalır.
- **Yazı motorun içinde çizilir.** FFmpeg `drawtext` kullanılmaz. Türkçe büyük harf: `toLocaleUpperCase('tr')`. Rakamlar 1 ve I karışmayan yazı tipiyle.
- Dikey video: üst ~250 px, alt ~420 px, sağ ~150 px'e anlam taşıyan öğe koyma.
- Tarayıcı JS'ini yakalamadan önce `node --check` ile sına.

## Doğru beklenti

Kalem'in yazarının notu projede de geçerlidir: skill başlangıç noktasıdır. Prompt yazıp çıkanı paylaşmak kişisel zevk olmadan slop üretir. Her videodan sonra kullanıcının "şurası daha iyi olurdu" dediği yeri kurala çevir.


## Hazır pano (ADR 0014)
Grafik, diyagram, karşılaştırma ya da açıklama sahnesi için önce `library/boards/katalog.md`: transkriptteki cümle "şunu derken" etiketiyle eşleşir. Görünüm `--css` ile stüdyoya çekilir, `vedit pano` ile klip olur, her motora girer. Kelimeye kilit gerekirse `board-sync`.
