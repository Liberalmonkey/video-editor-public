---
name: viral-kurgu
description: Videoyu platformların ölçtüğü sinyallere göre planlar ve kurar — YouTube, Reels/Shorts ve LinkedIn için hook, ritim, görsel değişim, kapanış, paylaşılabilirlik reçetesi ve Nick Saraev ölçümleri. Yeni video planında, taslak eleştirisinde; "viral", "izlenme", "algoritma", "tutma", "retention", "reach", "hook", "neden izlenmiyor" dendiğinde kullan. usta-editor ile birlikte çalışır.
---

# Viral kurgu

Hiçbir kurgu viral garanti etmez. Kurgu, konu ve paketin kazandığı izleyiciyi tutar. Karar sırası: konu ve vaat, paket (başlık, ilk kare), ilk saniyeler, tutma, kapanış. Konu zayıfsa önce bunu söyle; efektle kurtarmaya çalışma.

Kanıtlar ve kaynaklar: [[2026-11-04-platform-algoritmalari]]. Kesim hızının tutmayı artırdığını gösteren kontrollü bir çalışma bulunamadı. Aşağıdaki sayılar yasa değil, başlangıç değeridir; kanalın kendi verisi gelince o kazanır.

## Platformlar neyi ölçer

| Platform | Kaynağın söylediği sinyal | Kurguya çevirisi |
|---|---|---|
| YouTube uzun | Tıklama, izleme süresi, anketle "değerli izleme", paylaşım, beğeni, beğenmeme. Sabit formül yok. | Başlığın verdiği sözü hemen tut. Tıklatıp oyalamak anket ve tutmada geri döner. |
| Reels | İzleme süresi, erişim başına beğeni, erişim başına gönderim. Gönderim takipçi dışı kitlede biraz daha önemli. | Sonuna kadar izlenecek kadar kısa yap, arkadaşa gönderilecek tek bir şey koy. |
| Shorts | Akışta "izlendi / kaydırıldı" oranı, etkili izlenme, kalanların tutması. | İlk kare ve ilk cümle kaydırmayı durdurur. |
| LinkedIn | Akışta kalma süresi; gönderinin en az yarısı görünürken ölçülür. LinkedIn "viralite için tasarlanmadı" diyor. | Hedef erişim değil, doğru kitlenin durup izlemesi. Somut iş değeri ver. |

Instagram'ın resmî sayfası filigranlı, düşük çözünürlüklü, sessiz, çerçeveli ve çoğu yazıdan oluşan Reels'in önerilmekten kaçınıldığını söylüyor. Teslimde bunlara izin verme.

## Reels ve Shorts reçetesi (60 sn altı)

1. **İlk kare:** sonuç ya da iddia ekranda. Siyah, logo, kanal introsu yok.
2. **İlk cümle (0–3 sn):** `[bildiği şey] + [büyük sonuç] + [karşılığı]`. Söz ve ekran metni aynı vaadi taşır. Selamlama yok.
3. **Tek fikir:** video tek bir şey öğretir ya da gösterir. İkinci fikir ayrı videodur.
4. **Görsel değişim (başlangıç değeri):** hook'ta 1–2 saniye, gövdede 2–4 saniye; sakin bölüm brifte bilinçliyse bu aralık istisnadır. Her değişim yeni bilgi taşır: kanıt, ekran görüntüsü, sayı, B-roll. Yalnız sayı tutsun diye kesme.
5. **Konuşma:** dolgu ve nefes boşluğu temizlenir, ama cümle sonu nefesi kalır. Kelime anlaşılmıyorsa hızlandırma geri alınır.
6. **Sessizde anlaşılır:** altyazı ADR 0014 standardıdır. Ana iddia sessizde de okunur.
7. **Gönderme testi:** "Bunu kime, hangi cümleyle gönderirdim?" Cevap yoksa kapanmamış demektir. Hazır şablon, liste, kopyalanacak komut, şaşırtıcı sayı işe yarar.
8. **Kapanış:** söz biter bitmez biter. Tek CTA, en çok 3 sn. "Takip etmeyi unutmayın" gibi uzun veda yok. Mümkünse son cümle ilk kareye bağlanır.
9. **İlk kare:** serideki tüm videolarda tek düzen; ilk kare profil ızgarasında kapak gibi okunur (yüz ya da avatar, iki satır başlık).
10. **Temiz çıktı:** filigransız, 9:16, kenarsız, müziksiz bile anlaşılır.

## YouTube uzun reçetesi (8–30 dk)

1. **Önce paket:** başlık yazılmadan kurguya başlama (`/yt-package`). Video o vaadi doğrular. Vaatle içerik uyuşmazsa izleyici çıkar.
2. **İlk 30 sn:** sırayla kanıt (neden dinlenmeli), kazanç (sonunda ne olacak), yol haritası (ne göreceğiz). YouTube "intro" tutmasını ilk 30 sn üzerinden raporlar. Konu güncel bir araç ya da olaysa konuşmacıyla değil kanıt ekranıyla aç: repo, gönderi, sonuç. Kuru başlık kartıyla açılmaz.
3. **İlk 3 dakika en sıkı bölümdür.** En çok kayıp ilk dakikadadır. Kurulumu kes, ilk somut sonucu erkene al.
4. **Yaklaşık 3. dakikada yeniden kazan:** en güçlü demo, sonuç ya da şaşırtma burada. 3–6 dk arası basit ve ilginç içerik; uzun açıklamalar 6. dakikadan sonra.
5. **Bölümle:** 10–25 dakikalık videoda dakikada yaklaşık bir bölüm hedefi. Liste videosunda madde başına bir bölüm, her bölüm kendi küçük vaadiyle açılır.
6. **Kart yağdırma, düzen değiştir:** dört düzen döner: tam kadraj konuşmacı, adım adım dolan şema + küçük konuşmacı, ekran kaydı + küçük konuşmacı, tam ekran kanıt. Konuşmacının yüzüne kart koyma. Başlangıç değeri: ilk dakikada yaklaşık 6, sonra dakikada yaklaşık 3 düzen değişimi; görsel yoğunluk önde, son bölüm konuşmacıya kalabilir. Şema `library/boards`, kod sahnesi `sahne-motoru`.
7. **Anlamlı değişim:** ekranda yeni şey olmadan 20 sn geçmez (`usta-editor`). Ekran kaydında imleç, kaydırma ve yeni pencere de değişimdir; ayrıca kesim eklemek gerekmez.
8. **Kapanış:** son içerik cümlesinden sonra uzun özet yok. Ödül verildiyse hemen sıradaki videoya bağla, end screen'e geç.

## Tam kurs (1 saat üstü)

Saraev'in en çok izlenenleri burada. Kurgu sade: konuşma + ekran kaydı + köşede konuşmacı. İlk 15 sn kanıt ve vaat, sonra ekranda yazılı müfredat. Bölüm adları net, kurulum ve araç konuları ayrı. Kurs ucuz kurgu demek değildir: dolgu ve hata temizliği yapılır, süs eklenmez. Bu format YouTube dışındaki platformlara kırpılarak gider.

## LinkedIn reçetesi

Bu kurallar çoğunlukla üçüncü taraf gözlemidir; ayrı bir LinkedIn render'ı açmadan önce Reels çıktısıyla dene (`--platform reels`).

1. Doğrudan yükle, dış video linki paylaşma. Dış bağlantıyı gönderi metnine koyma; gerekiyorsa ilk yoruma yaz.
2. 30–90 sn, dikey, altyazılı. Eğitim içeriği 2–5 dk olabilir.
3. İlk cümle iş sonucu: para, zaman, müşteri. Kesim sakin, kanıt bol.
4. Gönderi metni de kalma süresi üretir: ilk iki satır videonun vaadi, altı kısa bağlam.
5. Emoji anketi ve yorum grubu (pod) kullanma; LinkedIn ikisini de hedef aldığını söylüyor.
6. Başarı ölçütü izlenme değil, hedef kitleden yorum, profil ziyareti ve gelen mesaj.

## Nick Saraev'den alınacak ve alınmayacak

| Gözlem | Karar |
|---|---|
| Kanalda büyük vuruş kısa klip değil, tam kurs ve "denedim" videosu | **Al:** kısa videoyu tek büyüme yolu sayma |
| Son 80 videonun en iyi 15'inin 7'si 2 saat üstü, 8'i 30 dk altı | **Al:** iki format birlikte: kurs ve sıcak konu |
| Başlıkta yeni araç, somut sonuç, açık vaat | **Al:** `/yt-package` girdisi |
| Sıcak uzun videolarda sık bölüm (14 dk'da 33, 13 dk'da 13) | **Al:** yukarıdaki bölüm hedefi |
| Yüze kart yok, düzen değişimi; 1,76 M izlenen 10 dk videoda açılış kanıt ekranı, el çizimi şema, demo sonucu ekranda | **Al** |
| Reels'te ücretsiz araç + "Yorum yaz, göndereyim" hunisi | **Kullanıcı kararı:** DM otomasyonu gerekir; yorum sinyali Mosseri'nin ilk üç listesinde yok, hedef liste büyütmedir |
| Reels'te adı konan repo ve yıldız sayısı | **Alma:** `checks.md` kullanıcı istemedikçe yasaklıyor |
| Tek kelime beyaz altyazı | **Alma:** ADR 0014 sabit |
| Kendi yüzü | **Uyarla:** konuşmacı Flow avatarı; avatar mümkün olduğunca gerçek ekran kanıtıyla dengelenir |

## Yayın paketi

Her teslimde videonun yanına `Projeler/outputs/<stüdyo>/<proje>/yayin.md` yazılır: kopyalanacak açıklama, hashtag, paylaşım öncesi kontrol, riskler. Metin videoda söylenenle aynı vaadi taşır, tam düzyazıdır (`humanizer`). Platform sorulmaz, stüdyodan çıkar; birden çok platform isteniyorsa her biri için ayrı bölüm.

Araç: `vedit yayin <proje> [--hepsi] [--platform reels,youtube,shorts,tiktok,linkedin] [--motor] [--model]` ya da Stüdyo > Teslim > Yayın metni (ADR 0055). Varsayılan Claude Opus 5.5. Teslim videosu başına `yayin.md`'de ayrı blok yazar; sınırlar ve platform kuralları `library/yayin/platformlar.json`'dadır, vedit doğrular. Aşağıdaki kurallar o dosyanın kaynağıdır; birini değiştirirsen ikisini birlikte güncelle.

**Instagram Reels:**
1. İlk cümle videonun vaadidir ve konunun anahtar kelimesini doğal biçimde içerir. Selamlama yok.
2. Açıklama videonun değerini metinle de verir: adımlar, liste, sonuç. Kaydedilecek ya da gönderilecek bir şey olsun.
3. En çok 5 hashtag, açıklamanın içinde, konuya özgü. Alakasız ya da genel popüler etiket yok. Hashtag erişim yaratmaz, konuyu ve aramayı destekler.
4. Tek çağrı. Önce gönderme ("... birine gönder"). "Yorumlara yaz" çağrısı kullanıcı kararıdır: Instagram "engagement bait"i öneri için sorunlu sayıyor, tanımını vermiyor; riski pakette yaz.
5. Video 3 dakikayı geçmez; filigran, çerçeve, düşük çözünürlük, sessiz video yok. Yapay zekâ avatarında paylaşım ekranındaki etiket hatırlatılır.
6. Keşfet garantisi verilmez. Sonuç ölçülür: ortalama izleme süresi, erişim başına gönderim, takipçi dışı erişim.

**YouTube:** `/yt-package`, `/yt-seo`, `/yt-chapters`. **LinkedIn:** yukarıdaki LinkedIn reçetesi. **Diğer platformlar:** kuralları araştırılmadıysa genel metin yazıp bunu söyle, kural uydurma.

## Üretim hattındaki yeri

- **Senaryo:** hook ve kapanışı reçeteye göre öner. Kullanıcının metni onaysız değişmez; öneri `oneriler.md`'ye.
- **Edit planı:** `sahne.mjs` yazmadan önce format reçetesini seç, değişim noktalarını konuşma satırlarına bağla.
- **Taslak kapısı:** `vedit taslak` sonrası kontak sayfasıyla aşağıdaki soruları cevapla.
- **Denetim:** `denetim` skill'i biter, sonra bulguları zaman damgası ve öneriyle göster. Yaratıcı öneri onaysız uygulanmaz.

### Taslak kapısı

Her "hayır" için zaman damgası ve tek cümle düzeltme öner. Cevabı ölçemiyorsan "bilinmiyor" yaz.

1. İlk karede konu anlaşılıyor mu?
2. İlk cümle selamlama ya da bağlam değil, vaat mi?
3. Başlık ve kapağın sözü ilk 30 sn içinde (Reels'te 3 sn) tutuluyor mu?
4. Bir sonraki bölümü izletecek açık soru var mı?
5. Yeni bilgi taşımayan görsel değişim var mı? Varsa kes.
6. 60 sn altı videoda atılabilecek tek cümle kaldı mı?
7. Sessizde ana fikir anlaşılıyor mu?
8. Son cümleden sonra boş süre var mı?
9. Gönderme testinin cevabı ne?
10. İmza anı var mı, paylaşılacak kare hangisi?

## Yayın sonrası ölçüm

Ölçmeden kural değiştirme. Kullanıcıdan şunları iste, ham veriyi `/yt-retention` ile oku:

- **YouTube:** ilk 30 sn tutma, anahtar anlardaki düşüşler, benzer süreli son 10 videoya göre tipik tutma, CTR.
- **Shorts:** gösterim, izlendi / kaydırıldı, etkili izlenme, tutma.
- **Reels:** ortalama izleme süresi, erişim başına gönderim ve beğeni, takipçi dışı erişim.
- **LinkedIn:** izleme süresi, hedef kitleden yorum ve mesaj.

Aynı anda tek değişken dene (ör. hook türü) ve kanalın benzer konu ve süredeki kendi videolarıyla karşılaştır. Sektör ortalaması kullanma. Kalıcı sonuç bu dosyaya, tek satır ders `library/kaizen.md`'ye.

## Dürüstlük

- İzlenme tahmini ya da "bu viral olur" sözü verme.
- Uydurma sayı yok; eksik veri `[KAYNAK?]`.
- Merak uyandıran başlık gerçek içerikle örtüşmeli. İçeride karşılığı olmayan vaat, kurguyla düzeltilemez.
- Başkasının kurgusundan yöntem alınır; videosu, grafiği, sesi alınmaz.
