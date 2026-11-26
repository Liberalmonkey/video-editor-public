# Yönetmen katmanı: duygu, kişilik, koreografi, brif (ADR 0063)

Kaynaklar (ilke olarak alındı, metin kopyalanmadı): LottieFiles `motion-design-skill` (MIT; director/ ve reference/), video-shotcraft (Apache-2.0; çekim kartı biçimi, estetik ve beat kuralları), prompt-motion.com (240 prompt'un ortak yapısı; prompt'lar kopyalanmadı).

## 1. Üç sütun, üç katman
Her animasyon önce üç soruyu cevaplar: izleyici ne **hissetmeli** (eğri, süre, genlik), mikro-hikâye ne (**kur → eylem → çözüm**), nasıl **inandırıcı** olur (fizik, ikincil hareket, yol). Hareket üç katmandır: ana (izleyicinin takip ettiği), ikincil (gölge, eşlik eden ikon), ortam (zemin nabzı). Düz görünen animasyonda katman eksiktir.

## 2. Hareket kişiliği (stil başına bir tane)
Stil kartına (`library/stiller/katalog.json`, alan `motion_kisilik`) yazılır, her şablon ona uyar.
| Kişilik | Süre | Eğri | Aşma | Ne zaman |
|---|---|---|---|---|
| `oyuncu` | 150-300 ms | `vurgu` (back.out) | %10-20 | eğlence, çocuk, meme, hafif UGC |
| `premium` | 350-600 ms | `oturma` / (0.4,0,0.2,1) | %0 | lüks, belgesel, editoryal, finans |
| `kurumsal` | 200-400 ms | `giris` / (0.2,0,0,1) | %0-3 | SaaS, eğitim, panolar |
| `enerjik` | 100-250 ms | `giris` (expo.out) | %15-30 | Reels hook, spor, lansman |
Marka imzası üç sabittir: tek imza eğrisi (hareketlerin %80'i), üç süre (hızlı/standart/yavaş), tek giriş kalıbı.

## 3. Duygu → hareket
| Duygu | Yol | Eğri | Süre |
|---|---|---|---|
| Sevinç | yukarı kavis, aşma | `vurgu` | 200-400 ms |
| Sakinlik | yumuşak eğri | sine inOut | 500-1000 ms |
| Aciliyet | düz çizgi | `giris` | 100-200 ms |
| Ağırlık, hüzün | aşağı, sarkan | cubic inOut | 600-1200 ms |
| Şaşkınlık, etki | radyal dışa | expo.out | 150-300 ms |
| Zarafet | uzun düz yay | `oturma` | 400-700 ms |
| Güven | düz yatay | `giris` | 200-400 ms |
Yol dili: köşeli = gergin, kavisli = dost, dikey yukarı = büyüme, radyal içe = odak, yatay = ilerleme. Malzeme: rijit 1.2x süre aşmasız, kâğıt 1.0x %3-5 aşma, sıvı 1.5x, gaz 2.0x.

## 4. Koreografi
- Kahraman önce ve en büyük yer değiştirmeyle; destek öğeleri her boyutta daha sakin.
- Tüm öğeler aynı yönden ya da ortak bir kökten girer. Karışık yön kaostur.
- Karşı hareket: kahraman sola girerken zemin %20-30 hızla sağa; kahraman büyürken gölge küçülür.
- Sekans payı: kurulum %20-30, eylem %30-40, çözüm %30-40; çözümden sonra 100-200 ms durgunluk.
- **1/3 kuralı:** hiçbir hareket ara anahtar olmadan ekranın 1/3'ünden fazla yol almaz; 3+ öğede aynı anda en çok 1/3'ü hareket eder.
- Stagger'da tüm öğeler aynı eğri ailesi; yalnız başlangıç değişir, sonuncusu hafif aşmayla noktalanabilir.
- Giriş, çıkıştan %30-50 uzun. Mesafe süreyi ölçekler: 100 px taban, 200 px 1.3x, 400 px 1.6x.

## 5. Motion brifi (prompt-motion yapısı)
Her motion işi (G0.5 Motion Brifi, tek grafik ya da tam sahne) beş bölümle yazılır:
1. **girdi:** kullanıcıdan gelen değişkenler (metin, sayı, renk, ses).
2. **yön:** görsel dil tek paragrafta, bir **iplik öğe** (tüm sahneleri bağlayan tek motif: bir nokta, çizgi, şekil, renk) ve **yasak listesi** (ör. stok görüntü, rastgele geçiş, ekranda zaten olmayan bir öğeye bağlı olmayan hareket).
3. **yapı:** saniye saniye sahne listesi; her büyük beat'te görsel değişim.
4. **kurulum:** teknik kurallar (kare yalnız t'den, kapalı-form yay, aynı fonksiyon hem nesneyi hem grafiği sürer, beat'e kilit).
5. **tuzaklar:** bu işte bozulması olası yer (iplik öğe kopması, Türkçe glif, 9:16 güvenli alan).
İplik öğe ilk kareden son kareye kesilmez; son kare ilk kareye eşlenirse döngü temiz olur.

## 6. Çekim kartı (shotcraft biçimi)
Her şablonun `data-hf-meta.kart` alanı: `amac` (tek iş), `sure_sn`, `beat` (vuruşa kilitli an), `yasak` (bu şablonla yapılmayacak). Editör şablonu adıyla değil kartıyla seçer.

## 7. Estetik ve beat
- Beat'e kilit: tıklama, iniş, grafik tepe noktası ve başlık ölçülen vuruşa oturur (`vedit ritim`); render öncesi her beat için tek kare açılıp bakılır.
- Ekrandaki her hareket ekranda zaten olan bir öğeden doğar; boşluktan gelen parçacık patlaması yok.
- Parıltı, degrade ve bloom en parlak tek noktaya; her şeyi parlatmak ucuz görünür.
- 3D yalnız kazandığında (bkz. `hf-gsap-uc`).
