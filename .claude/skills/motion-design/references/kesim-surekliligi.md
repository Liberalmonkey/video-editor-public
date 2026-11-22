# Kesim sürekliliği ve teknik reçeteler

Kaynak ve gerekçe: `wiki/decisions/0040-ikinci-repo-dalgasi.md`. Kural fikirleri hyperframes-community-skills `vox-explainer` (Apache-2.0: `references/motion-continuity.md`, `velocity-matched-transitions.md`), HyperFrames `reverse-any-video/references/match.md` (Apache-2.0), snapcn `motion-quality` (MIT), onetake (PolyForm Noncommercial: yalnız fikir, metin kopyalanmadı). Metinler bizim yazımımız.

## 1. Vektör yasası (kesimin iki yanı)
Sahne nasıl çıkıyorsa sonraki öyle girer. Sahneler tek tek tasarlanınca gözün ivmesi her kesimde ölür.
1. **Eksen:** x yine x, y yine y, derinlik yine derinlik. Kesimde eksen değişmez.
2. **Yön:** aynalanmaz. Derinlikte yön ölçeğin işaretidir: büyüyen ileri itiş, küçülen geri çekiliş. En sık hata, geri çekilen çıkışa küçükten büyüyen girişle cevap vermektir (varsayılan giriş animasyonu budur). Kesimden sonraki ~0,5 sn içinde gelen sahnenin kendi girişleri de bu işarete uyar.
3. **Hız:** girişin ilk hızı çıkışın son hızına eşit. Aynalı eğri: çıkış `power4.in`, giriş `power4.out`, aynı mesafe ve süre; gelen taraf yolun en az yarısından başlar.
4. **Evre:** kesim iki yanda da hareketin ortasına düşer. Kesimden önce durmak ya da kesimden sonra durgundan başlamak ölü vuruştur.

## 2. Beş kesim, iki iç hareket
| Teknik | Nerede | Eksen | Ne için |
|---|---|---|---|
| İçinden zoom | Aynı sahnede yazı değişimi | Derinlik, ileri | Aynı düşüncede derine inmek |
| Ters içinden zoom | Varış, büyük an | Derinlik, geri | Daha büyük bir şey yerine oturur |
| Devam kesimi | Sahneler arası | x / y | Varsayılan sınır; filmin akıntısı |
| Kelime çağlayanı | Yazıdan yazıya | x, kelime kelime | Büyük yazı vuruşları arası el değiştirme |
| Netlik kaydırma kesimi | Aynı yüzeyde durum değişimi | x / y / derinlik | Görünmesi istenen tek kesim; en çok bir iki kez |
| Çağlayan giriş | Sahne içi varış | y, aşağıdan | Başlık kartı, bölüm açılışı, liste |
| Üç evreli kayma | Sahne içi grup kayması | x / y | Yer açmak için grubu taşımak |
Bizde karşılığı: devam kesimi `gecis_giris.tur: "it"` aynı `yon` ile; içinden zoom `zoom` geçişi; netlik kaydırma `bulanik`. `vedit kurgu-denetle` art arda üç aynı geçişi uyarır (`GECIS_TEKRAR`).

## 3. Süreklilik ve kadans
- **Taşıyıcı:** bir öğe (renk, şekil, çizgi, karakter) bir sahneden ötekine taşınır; izleyici kesimi değil öğenin yolculuğunu görür.
- **Kadans farkı:** planların süreleri arasında belirgin fark olsun; en uzun plan en kısanın en az dört katı. Hepsi aynı uzunlukta olunca slayt gösterisi gibi durur (`slop` `RITIM_METRONOM` bunu ölçer).
- **Hızlı tempoda okunacak yazı:** sıralı metin her vuruşa değil iki vuruşta bire dizilir; her parça oturduktan sonra en az 0,8 sn durur.

## 4. Teknik reçeteler (Remotion, HyperFrames, pano HTML)
- **Yönlü hareket bulanıklığı:** hareket eden sarmalayıcıya SVG `feGaussianBlur`, `stdDeviation` iki değerli ve canlandırılır (`"24 0"` yatay sürtünme). CSS `blur()` her yöne yayar, hareket yönünü göstermez. HyperFrames'te kökte `data-motion-blur="on"` hızlı 2B harekette aynı işi yapar.
- **Ölçeklenen yazı titremesi:** tarayıcı harf başlangıcını dikeyde tam piksele yuvarlar. Taban çizgisini oynatan ölçek, yazıyı piksel piksel zıplatır (dur, zıpla, dur). Ölçeğin dayanak noktası taban çizgisidir: `transform-origin: 0% <taban>px`; taban satırın içine konan sıfır boyutlu bir `inline-block` ile ölçülür, satır yüksekliğinden tahmin edilmez.
- **Yazı boyunu mürekkeple eşle:** referansı taklit ederken yazıyı gözle değil mürekkep kutusuyla boyutla. Kaynak karedeki satırı ve kendi karendeki satırı kırp, yükseklik ve genişliği birkaç piksele kadar eşle; sonra harf aralığı, sonra kalınlık.
- **Cam yazı:** harflerin içinde arkadaki görüntünün bükülmüş kopyası: SVG `clipPath` içinde `<text>`, `feTurbulence` (baseFrequency ≈ 0,02, sabit tohum) → `feDisplacementMap` (40-60), üstüne %15-35 koyu kopya, 2-3 px koyu kontur, açık üst kenar.
- **Gren:** sabit tohumlu `feTurbulence`, kare başına adımlanır; rastgele değil.
- **Yay:** yay hareketi kapalı formdur (her kare kendi başına hesaplanır); hedef birkaç kez değişiyorsa her değişim için bir yay toplanır. CSS geçişi ya da zamanlayıcı kullanılmaz.
- **Uydurma sayı yok:** gerçek rakam verilmediyse çubuk göreli boy, yazı iskelet çizgiyle gösterilir.
