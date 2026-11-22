# Nick Saraev ölçüm notu (2026-11-04)

Yöntem: `yt-dlp` ile herkese açık meta veri, 360p örnek, `ffmpeg select=gt(scene,E)` ile görüntü değişimi. Örnekler yalnız ölçüm için geçici klasöre indirildi, repoya girmedi. Instagram girişsiz okunamadı. İkinci turda YouTube 429 verdiği için yeni istek atılmadı.

## Kanal (son 80 uzun video, 19 Shorts)

- Abone: 587 bin. Uzun video medyan izlenme 94.500, medyan süre 14:56. Shorts medyan izlenme 10.000.
- En iyi 15 uzun videonun 7'si 2 saat üstü, 8'i 30 dk altı.

| Kat (medyana göre) | İzlenme | Süre | Başlık |
|---|---|---|---|
| 29.6 | 2,8 M | 250 dk | CLAUDE CODE FULL COURSE 4 HOURS: Build & Sell (2026) |
| 18.0 | 1,7 M | 10 dk | I Tested The Viral Github Repo That Reverse Engineers Anything |
| 10.6 | 1,0 M | 133 dk | AI Agents Full Course 2026: Master Agentic AI (2 Hours) |
| 6.0 | 564 B | 198 dk | CLAUDE CODE ADVANCED FULL COURSE (3 HOURS) |
| 5.6 | 530 B | 24 dk | Here's What I'd Learn Instead of AI Automation in 2027 |
| 5.1 | 486 B | 14 dk | 31 Life-Changing Ways to Use Claude in 2027 |
| 4.4 | 417 B | 13 dk | How to Survive the Next 2 Years of AI |

## Bölüm yoğunluğu (meta veri)

| Video | Süre | Bölüm |
|---|---|---|
| 31 Life-Changing Ways | 14 dk | 33 |
| How to Survive | 13 dk | 13 |
| What I'd Learn Instead | 23 dk | 19 |
| Viral Github Repo | 10 dk | 6 |
| Claude Code Full Course | 250 dk | 35 |

## Kurgu ölçümü

### Claude Code Full Course, ilk 10 dk (`QoQBzR1NIqI`)

| Eşik | Değişim/dk | Medyan plan | En uzun plan |
|---|---|---|---|
| 0.3 | 0.4 | 41.9 sn | 417 sn |
| 0.1 | 1.5 | 27.9 sn | 160 sn |
| 0.05 | 3.3 | 9.0 sn | 160 sn |

- Konuşma hızı yaklaşık 225 kelime/dk (tüm video, otomatik altyazı).
- Kontak sayfası: yaklaşık ilk 45 sn tam kadraj konuşmacı, sonra ekran kaydı + sol altta konuşmacı. Ekranda yazılı müfredat kayarak geçiyor.
- En çok izlenen anlar açılışta değil, 22., 35., 37. ve 95. dakika civarı, ayrıca 5. dakika.
- Açılış (otomatik altyazı): "Hey, this is the definitive course on Claude Code for beginners. I use Claude Code every day to manage a business that does over $4 million a year in profit. I also teach over 2,000 people…"

### I Tested The Viral Github Repo, tam video (`dAzs_rU6080`, 10 dk, 1,76 M izlenme)

| Eşik | Değişim toplamı | İlk 60 sn | Medyan plan | En uzun plan |
|---|---|---|---|---|
| 0.3 | 29 (2,9/dk) | 6 | 10,2 sn | 93 sn |
| 0.1 | 77 (7,7/dk) | 6 | 2,8 sn | 60 sn |
| 0.05 | 235 | 7 | 0,5 sn | 60 sn |

Kontak sayfası (15 sn'de bir kare), yalnız yapı gözlemi:

- Video yüzle değil kanıtla açılıyor: ilk iki örnek karede repo sayfası ve sosyal medya gönderisi, sağ üstte küçük yüz.
- Dört düzen dönüyor: tam kadraj konuşmacı, adım adım dolan el çizimi şema + sağda küçük yüz, terminal + sağda küçük yüz, tam ekran kanıt.
- Demo sonucu terminalin üstüne pencere olarak açılıyor. Büyüme grafiği adım adım doluyor.
- Görsel yoğunluk önde: ilk 7 dakika çoğunlukla ekran, son 3 dakika çoğunlukla konuşmacı.

### Why Saturation Doesn't Matter, Shorts (`aIflIQMacV4`, 13 sn, 53 bin izlenme)

| Eşik | Değişim/dk | Medyan plan | En uzun plan |
|---|---|---|---|
| 0.3 | 46.2 | 0.8 sn | 4 sn |
| 0.1 | 87.7 | 0.1 sn | 4 sn |

- Yaklaşık 212 kelime/dk. Çok yakın kadraj, mikrofon önde, tek kelimelik beyaz altyazı, kısa meme B-roll, beyaz ekranda serif "Peak" kelimesi.
- Eski ve tek örnek; güncel Reels stilini temsil ettiği kanıtlanmadı.

## Sınırlar

Sahne eşiği ekran kaydında kaydırmayı da yakalar, aynı kadrajdaki jump cut'ı kaçırabilir. Sayılar kaba göstergedir. Örnek küçüktür; hiçbiri tutma verisi değildir, çünkü kanalın Analytics'ine erişim yok.
