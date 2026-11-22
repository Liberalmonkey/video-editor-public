# Fizik, ışık ve ses kuralları (ayrıntı)

Kaynak: `work/agy/2026-11-16-repolar/sonuc/birlesik.md` bölüm 7 (üç Antigravity araştırma notunun birleşimi, 2026-11-16). Fikir kaynakları: video-shotcraft (Apache-2.0), ClaudeAnimationBase (MIT), lemo-opuscar (belgeleri CC BY-NC 4.0, yalnız fikir alındı, metin kopyalanmadı). Sayılar 30 fps içindir.

## Kütle, çarpışma, hareket
- **Hazırlık ve ezilme.** Zıplayan ya da fırlayan nesne kalkıştan 3-4 kare önce hafifçe çömelir. Düşüşte hız yönünde uzar, temas karesinde hacmini koruyarak ezilir (genişlik 1 + 0,6·e, yükseklik 1 − e), 4-5 karede sönümlü yayla toparlanır. Katı cisimde (kutu, araba) ezilme yoktur; yalnız top, damla, karakter.
- **Darbe donması.** Çok sert yıkımda 2-3 karelik donma (hit-stop) gücü artırır; videoda en çok bir kez.
- **Sıralı okuma.** Sebep ve tepki aynı karede başlamaz. Biçim değiştiren kutuda eski yazı tamamen çıkmadan yenisi girmez.
- **Gecikmeli takip.** Parçalar aynı karede durmaz: önce göz, sonra gövde, en son aksesuar ve gölge (2-4 kare geriden).
- **Yuvarlanma.** θ(t) = s(t) / r. Domino taşı ağırlık merkezi tabanı geçince hızlanır; zincir ilerledikçe taşlar arası süre kısalır.
- **Kapalı form.** Kodla yazılan hareket zamanın işlevidir (konum = f(t)), kare kare biriken hız değil; böylece her kare bağımsız ve aynı çizilir. Çoklu çarpışma (domino, yıkım) için fizik sahnesi bake edilir.

## Araç ve kamera
- **İvme eğrisi.** Durgundan kalkış: hız doğrusal artar (v = a·t), konum karesel. En yüksek hıza varınca sabit hız.
- **Yük aktarımı.** Gazda arka çöker (burun kalkar), frende öne eğilir, virajda dışa yatar; sönümlü yay, 0,3-0,6 sn.
- **Tekerlek.** Dönme yola kilitli; yüksek hızda hız izi. Lastik izi ve duman yalnız kayma olunca.
- **Kamera.** Hedefin o anki yerine değil biraz ilerisine bakar; hız arttıkça geri çekilir. Takip kamerası nesneden 2-4 kare geriden gelir (hız hissi).

## Sıvı ve esnek öğe
- Hareket eden damla ya da gösterge öncü kenarda hızlı, artçı kenarda yavaş yayla uzar.
- Sınırın ötesine çekilen öğe artan dirençle esner, bırakılınca yayla oturur.

## Işık ve gölge
- **Temas gölgesi.** Yükselen nesnenin gölgesi yerinde kalır, büyür, bulanıklaşır, solar.
- **Toplamsal ışık.** Parlayan nesne boya gibi karışmaz; parlama toplanır (bloom), çevresini aydınlatır.
- **Cam ve su.** Dik bakışta saydam, yatık açıda ayna gibi yansıtır. Alçak güneşte küçük çıkıntı bile uzun gölge düşürür.
- **Kenar ışığı.** Karanlık sahnede yanan kaynak yakındaki konturda 1-2 piksellik ışık bırakır.
- **Tek yön.** Bir sahnede tek anahtar ışık; dolgu ışığı gölgeyi yumuşatır, yönünü değiştirmez.
- **Renk sıcaklığı.** Sabah ve gün batımı sıcak (3000-3500 K), öğle nötr (5500-6500 K), gece ve teknoloji soğuk (7500 K üstü).

## Ses ve kurgu senkronu
- **Tepe hizası.** Ses efekti dosyanın başından değil ölçülen tepesinden olay karesine oturur (`olaysesi` bunu yapar).
- **Uzaklık ve yoğunluk.** Uzak olay alçak; çok sayıda küçük çarpışma tek doku. Fizik sahnesinde sahne başına en çok 8 darbe, en çok 2 sert darbe, tık zinciri en çok 24 (`src/vedit/fizik.py`).
- **Havada boşluk.** Nesne havadayken ya da sert geçişten hemen önce müzik bir an çekilir, temasta geri girer.
- **Beat.** Müzikli kurguda büyük olay (sahne girişi, ana çarpma) en yakın beat'e (en çok 2 kare) oturur; her beat'e kesme konmaz, 4 ya da 8 beatlik öbekler kurulur.
- **Konuşma.** Punch ve grafik vurgulu hecenin başında başlar; vurgulu hecenin üstüne ses efekti binmez.

## Karakter
- Yere basan ayak kaymaz. Dururken bile hafif nefes hareketi vardır.
- İfade bir karede birden değişmez: göz önce kısılır, ifade değişir, 3-4 karede açılır.
- Ağız şekli kare başına sesten gelir (`references/karakter.md`).

## Kişiliğe göre hareket
- Finans ve güven: taşma yok, 18-24 kare, yumuşak çıkış.
- Lüks: taşma en çok %2, 40-50 kare, ağır.
- Enerjik ve oyun: taşma %10-12, belirgin ezilme, 15-18 kare.

## Döngü ve denetim
- Döngü videosunda ilk ve son karede konum, hız, kamera açısı ve parçacık fazı aynıdır.
- Kod sahnesi denetiminde kontak sayfası yetmez: hızlı anlarda ardışık kare şeridine, temas anında yakın kırpmaya bakılır.
