---
name: kapak-instagram
description: Instagram Reels kapağı (9:16, 1080×1920, profil ızgarasında 3:4) için brief yazar ve Antigravity ile 1-5 aday üretir. Nick Saraev, Iman Gadzhi, Alex Hormozi ve en çok izlenen sayfaların araştırılmış kalıplarına dayanır; yazı her zaman kodla eklenir. "reels kapağı", "instagram kapak", "kapak yap", "ızgara", "grid kapağı" dendiğinde kullan.
---

# Instagram Reels kapağı

Kaynak: `wiki/sources/2026-11-09-kapak-arastirmasi.md`, kalıplar `wiki/sources/2026-11-15-kapak-kalip-analizi.md`. Karar: `wiki/decisions/0027-kapak-sayfasi.md`. Motor sırası ve yazı katmanı kuralı `gorsel-uret` skill'indedir; bu skill Reels'e özgü içeriği verir. Kalıp ve stil seçimi: `references/kaliplar.md` (brief isteğine eklenir). Sayfa örnekleri: `references/kanallar.md`.

## Komut
```
.venv/Scripts/vedit kapak instagram/<proje> --adet 1                  # varsayılan tek aday
.venv/Scripts/vedit kapak <ref> --platform instagram --adet 4         # kullanıcı isterse 2-5
.venv/Scripts/vedit kapak <ref> --metin "satır1|satır2" --prompt "..." # brief'i elle ver
.venv/Scripts/vedit kapak <ref> --zemin work/kare.jpg --adet 2        # eldeki kare, agy yok
.venv/Scripts/vedit kapak <ref> --sec 1                               # outputs/kapak-reels.jpg
.venv/Scripts/vedit kapak <ref> --duzenle 1 --metin "satır1|satır2" --vurgu kelime   # yazıyı agy'siz yeniden çiz
.venv/Scripts/vedit kapak <ref> --duzenle 1 --yerlesim alt --kutu --karart --kopya   # aynı zeminle yeni aday
.venv/Scripts/vedit kapak <ref> --kalip seri --ek "Claude" --stil kirmizi-kutu       # seri şablonu
.venv/Scripts/vedit kapak <ref> --adet 3 --elestir                                   # üret, sonra agy puanlasın
.venv/Scripts/vedit kapak <ref> --video "inputs:2.mp4" --gelistir "fikrim..." --model gemini-4-argon-medium  # fikri prompt'a geliştir (oneri.json)
.venv/Scripts/vedit kapak <ref> --video "inputs:2.mp4" --oneri --adet 2 --gorsel-model gemini-3.8-flash-medium  # öneriyle üret
.venv/Scripts/vedit kapak <ref> --gorsel-duzelt 2 --istek "arka planı koyulaştır" --bolge 50,10,95,60          # görseli düzelt, yeni aday
.venv/Scripts/vedit kapak <ref> --master 2 --hedef nano-banana-21                                           # dış platform master prompt
.venv/Scripts/vedit kapak <ref> --ice-al indirilen.png [--yazili]                                           # dış görseli aday yap
```
**İş akışı v2 (ADR 0052):** Stüdyo Kapak alanı 5 adımdır: Video, Fikir ve prompt, Üret, Düzelt, Master prompt ve teslim. `--video` kareleri tek videodan alır; oynatıcıda durdurulan an kare olarak eklenir. Yüz ve stil referansı `work/gorsel/kapak/referans/` altındadır; stil yalnız düzen ve renk verir. `--gelistir` kullanıcının fikrini bu kurallarla yapılı brief'e çevirir (boşsa videodan önerir); `--oneri` onunla üretir. `--model` brief'i yazan, `--gorsel-model` generate_image'ı çağıran agy modelidir; görsel modelinin kendisi agy'de sabittir (loglarda `gemini-3.1-flash-image`). `--gorsel-duzelt N` zemini kırmızı kutu tekniğiyle düzeltir; kutu dışı piksel korunur, sonuç yeni adaydır. `--master` Nano Banana Pro, Nano Banana 2.1, ChatGPT, Midjourney, Ideogram ve Leonardo için yazılı ve boş zemin prompt'u verir; teslimde `<kapak>-master-prompt.md` yazılır. Dış platformda üretilen görsel `--ice-al` ile döner; boş zeminse yazı kodla eklenir.
**Kalıp** (`--kalip klasik|seri|yazisiz`): `seri` referans sayfaların tek şablonudur: `--ek` marka sözü üstte ve başın arkasında (zeminden özne kesiti, `rembg`; kurulu değilse klasik kalıba düşer), iki satır altta, girdi klasöründeki `logo1.png` ve `logo2.png` iki yanda. **Stil** (`--stil`, `library/kapak/stiller/`): varsayılan `turuncu`, referans seri `kirmizi-kutu`; stüdyo `studios/instagram/kapak.json` (`{"stil": "..."}`) ile sabitlenir. Kapak yazısı altyazı standardına bağlı değildir (ADR 0027). Her çizimde kelime sayısı, harf yüksekliği ve güvenli alan ölçülür; `--elestir` agy'ye 1-10 puan ve tek düzeltme yazdırır, seçim kullanıcıdadır.
Yazı üretimden sonra düzenlenir: zemin bir kez üretilir, `--duzenle N` yalnız yazıyı yeniden çizer ve agy kotası harcamaz; `--kopya` adayın üzerine yazmaz. Yerleşim `--yerlesim ust|alt` (varsayılan `ust`; yüz ortadaysa `alt`), boyut `--olcek 0.6-1.4`, `--karart` yönlü gradyan, `--kutu` vurguyu renkli kutuya alır. İki yerleşim de 3:4 ızgara ve 4:5 akış alanının içindedir.

Aynı iş Video Stüdyo'da **Kapak** sekmesindedir; sekme 3:4 ızgara ve 4:5 akış kırpmasını kesik çizgiyle gösterir, adayın kalem düğmesi yazı düzenleyicisini açar (canlı önizleme, varyasyon, indir). Brief yoksa `vedit kapak` bu dosyayı ve videonun metnini agy'ye verir, agy aşağıdaki biçimde brief yazar. Adaylar `work/gorsel/kapak/instagram/`.

## Ölçü ve güvenli alan
- Kapak 1080×1920 yüklenir. Profil ızgarası ortadaki 3:4 alanı (1080×1440) gösterir: üstten ve alttan yaklaşık 240 px kırpılır. Akışta 4:5 görünür.
- Yazı ve yüz ortadaki 1080×1440 alanda kalır. Reels arayüzü alt kısmı (açıklama, düğmeler) ve sağ kenarı da örter; kritik öğe orada durmaz.
- Şablon (`library/kapak/sablon.html`) dikeyde başlığı `ust` yerleşiminde üstten %18'e (y≈345), `alt` yerleşiminde alt kenarı %84'e koyar; ikisi de güvenli alanın içidir. Yüz/avatar alttadır; çene ızgarada kesilebilir, gözler kesilmez.

## Kalıp: tek şablon seri
Nick Saraev'in Reels kapakları tek şablondur: yüz ortada, iki yanda iki araç logosu, iki satır başlık, ikinci satır renkli kutuda. "Her kapak aynı görünür"; izleyici başlığı okumadan kimin videosu olduğunu bilir. Bu projede karşılığı (`viral-kurgu` madde 9): yüz ya da Flow avatarı, gerekiyorsa iki araç logosu (kullanıcı verir, girdi klasöründe `logo1.png`, `logo2.png`; üretilmez), iki satır başlık; bunu `seri` kalıbı kurar. Vurgu rengi stil paketinden gelir (varsayılan turuncu `#FF7A00`). Profilde ızgaranın bütün olarak tek seri gibi görünmesi tek tek kapaktan önemlidir.

## Kurallar
YAP
- İki satır, toplam en çok 6 kelime. Kapak videoyu anlatmaz, değer ya da sonuç vaat eder ("Claude artık kurgu yapıyor", "ücretsiz").
- Kanca kalıbı kapakta da çalışır: "[zaten kullandığın şey] + [büyük sonuç]".
- Yüksek kontrast, sade zemin; ızgarada küçük karede tek odak okunur.
- Yüz/avatar varsa göz hizası güvenli alanın ortasında, ifade net ve tek.
- Seri: aynı stüdyoda tüm kapaklar aynı yerleşim, yazı stili ve renk; yalnız yazı ve zemin değişir.
- Izgara testi: kapağı 3:4 kırpıp 360 px genişliğe indir, yanına önceki iki kapağı koy; okunmuyorsa ya da seriden kopuyorsa aday düşer.
- Kapak yazısı videonun ilk saniyesindeki kancayla aynı vaadi taşır.

YAPMA
- Gerçek kişinin yüzünü, sayfa logosunu ya da başkasının kapağını kopyalama; yalnız kalıp alınır.
- Üst ya da alttaki 240 px'e yazı, yüz, logo koyma.
- Rastgele video karesini kapak bırakma (ızgarada dağınık görünür).
- Görselde harf, logo, emoji yığını; üç satırdan uzun yazı.

## Açılar (adaylar arasında çeşitleme)
Aday sayısı kadar farklı açı seç, sırayla:
1. **Sonuç:** vaadin bittiği an, tek büyük nesne ya da ekran.
2. **Yüz + iki araç:** avatar ortada, iki araç simgesi iki yanda (seri şablonu).
3. **Karşıtlık:** eski/yeni, pahalı/ücretsiz, yavaş/hızlı yan yana.
4. **Merak:** yarım ya da saklı bir şey.
5. **Duygu:** yüz yakın, tek güçlü ifade.

## Brief biçimi
`brief.json` bir JSON dizisidir; her nesne:
```json
{"sahne": "English: one subject, what it does, where", "ifade": "English facial expression, empty if no person",
 "kompozisyon": "subject centered in the middle 3:4 area, head and shoulders", "isik": "soft side light, dark simple background",
 "palet": "one main colour and one accent", "yazi_alani": "the upper part of the central area",
 "satir1": "kısa ilk satır", "satir2": "vurgulu ikinci satır", "vurgu": "satir2 içinden tek kelime", "aci": "sonuç"}
```
- Sahne alanları (`sahne`, `ifade`, `kompozisyon`, `isik`, `palet`, `yazi_alani`) İngilizce, kısa cümle. agy prompt'u ve dış platform master prompt'u bunlardan kurulur (ADR 0052). Görselde yazı yok; alt 240 px'te önemli şey yok.
- `prompt` yalnız elle verilir ve sahne alanlarını ezer. Eski yalnız-`prompt` brief aynen çalışır.
- `satir1`, `satir2` videonun dilinde; toplam en çok 6 kelime.
- `vurgu` `satir2`'de geçen tek kelime; boşsa tüm ikinci satır vurgu rengini alır.
- `kalip`, `ek`, `stil`: `references/kaliplar.md` tablosundan. Geçersiz kalıp ya da stil sessizce varsayılana düşer.

## Seçim ve teslim
1. Adayları kullanıcıya göster (Stüdyo Kapak sekmesi ızgara çerçevesiyle). Kullanıcı seçer; ajan seçmez.
2. Beğenilmezse: sorun yazıdaysa `--duzenle N` (zemin kalır), zemindeyse brief'i düzelt; toptan yeniden üretme. agy kotası dolarsa `--zemin` ile eldeki kare (avatar klibinden kare) ya da Flow (`gorsel-uret`).
3. `--sec N` adayı `Projeler/outputs/<stüdyo>/<proje>/kapak-reels.jpg` yapar (varsa `-v2`).
4. `yayin.md` kapak bölümüne dosya adı yazılır; Instagram'da yüklerken "Kapak düzenle > Film rulosundan ekle" ile bu dosya seçilir ve ızgara önizlemesi kontrol edilir.
5. `denetim` üretilmiş zemini AI slop açısından da değerlendirir.
