---
name: kapak-youtube
description: YouTube kapağı (thumbnail, 16:9, 1280×720) için brief yazar ve Antigravity ile 1-5 aday üretir. MrBeast, Nick Saraev, Iman Gadzhi ve en çok izlenen kanalların araştırılmış kalıplarına dayanır; yazı her zaman kodla eklenir. "youtube kapağı", "thumbnail", "kapak yap", "kapak adayı", "CTR", "tıklanma" dendiğinde kullan.
---

# YouTube kapağı

Kaynak: `wiki/sources/2026-11-09-kapak-arastirmasi.md`, kalıplar `wiki/sources/2026-11-15-kapak-kalip-analizi.md`. Karar: `wiki/decisions/0027-kapak-sayfasi.md`. Motor sırası ve yazı katmanı kuralı `gorsel-uret` skill'indedir; bu skill YouTube'a özgü içeriği verir. Kalıp ve stil seçimi: `references/kaliplar.md` (brief isteğine eklenir). Kanal örnekleri: `references/kanallar.md`.

## Komut
```
.venv/Scripts/vedit kapak youtube-animasyon/<proje> --adet 1          # varsayılan tek aday
.venv/Scripts/vedit kapak <ref> --platform youtube --adet 3           # kullanıcı isterse 2-5
.venv/Scripts/vedit kapak <ref> --metin "satır1|satır2" --prompt "..." # brief'i elle ver
.venv/Scripts/vedit kapak <ref> --zemin work/kare.jpg --adet 2        # eldeki kare, agy yok
.venv/Scripts/vedit kapak <ref> --sec 2                               # outputs/kapak.jpg
.venv/Scripts/vedit kapak <ref> --duzenle 2 --metin "satır1|satır2" --vurgu kelime   # yazıyı agy'siz yeniden çiz
.venv/Scripts/vedit kapak <ref> --duzenle 2 --yerlesim alt --karart --kopya          # aynı zeminle yeni aday
.venv/Scripts/vedit kapak <ref> --kalip dev-yazi --ek "4K!" --stil kirmizi-kutu      # kalıp ve yazı stili elle
.venv/Scripts/vedit kapak <ref> --duzenle 2 --kalip alt-bant --kopya                 # aynı zemin, başka kalıp
.venv/Scripts/vedit kapak <ref> --adet 3 --elestir                                   # üret, sonra agy puanlasın
.venv/Scripts/vedit kapak <ref> --adet 0 --elestir                                   # yalnız eldeki adayları puanlat
.venv/Scripts/vedit kapak <ref> --video "inputs:2.mp4" --gelistir "fikrim..." --model gemini-4-argon-medium  # fikri prompt'a geliştir (oneri.json)
.venv/Scripts/vedit kapak <ref> --video "inputs:2.mp4" --oneri --adet 2 --gorsel-model gemini-3.8-flash-medium  # öneriyle üret
.venv/Scripts/vedit kapak <ref> --gorsel-duzelt 2 --istek "arka planı koyulaştır" --bolge 50,10,95,60          # görseli düzelt, yeni aday
.venv/Scripts/vedit kapak <ref> --master 2 --hedef nano-banana-21                                           # dış platform master prompt
.venv/Scripts/vedit kapak <ref> --ice-al indirilen.png [--yazili]                                           # dış görseli aday yap
```
**İş akışı v2 (ADR 0052):** Stüdyo Kapak alanı 5 adımdır: Video, Fikir ve prompt, Üret, Düzelt, Master prompt ve teslim. `--video` kareleri tek videodan alır; oynatıcıda durdurulan an kare olarak eklenir. Yüz ve stil referansı `work/gorsel/kapak/referans/` altındadır; stil yalnız düzen ve renk verir. `--gelistir` kullanıcının fikrini bu kurallarla yapılı brief'e çevirir (boşsa videodan önerir); `--oneri` onunla üretir. `--model` brief'i yazan, `--gorsel-model` generate_image'ı çağıran agy modelidir; görsel modelinin kendisi agy'de sabittir (loglarda `gemini-3.1-flash-image`). `--gorsel-duzelt N` zemini kırmızı kutu tekniğiyle düzeltir; kutu dışı piksel korunur, sonuç yeni adaydır. `--master` Nano Banana Pro, Nano Banana 2.1, ChatGPT, Midjourney, Ideogram ve Leonardo için yazılı ve boş zemin prompt'u verir; teslimde `<kapak>-master-prompt.md` yazılır. Dış platformda üretilen görsel `--ice-al` ile döner; boş zeminse yazı kodla eklenir.
**Kalıp** (`--kalip klasik|dev-yazi|alt-bant|bolunmus|rozet|not|yazisiz`): kapağın düzeni. `--ek` kalıbın ek sözüdür (dev yazıda arkadaki söz, alt bantta üst satır, notta el yazısı). `dev-yazi` zeminden özne kesiti alır (`rembg`, agy kotası harcamaz; kurulu değilse aday klasik kalıpla çizilir). **Stil** (`--stil`, `library/kapak/stiller/`): yazının rengi ve yazı tipi; varsayılan `turuncu`. Stüdyo `studios/<stüdyo>/kapak.json` (`{"stil": "..."}`) ile stilini sabitler. Kapak yazısı altyazı standardına bağlı değildir (ADR 0027); altyazı videoda aynen kalır.
**Ölçüm:** her çizimde kelime sayısı, harf yüksekliği (en az karenin %8'i), güvenli alan ve kontursuz yazıda zemin kontrastı ölçülür; uyarılar komut çıktısında ve Stüdyo'da adayın yanında görünür. `--elestir` agy'ye 1-10 puan ve tek düzeltme yazdırır; seçim yine kullanıcıdadır.
Yazı üretimden sonra düzenlenir: zemin bir kez üretilir, `--duzenle N` yalnız yazıyı yeniden çizer ve agy kotası harcamaz; `--kopya` adayın üzerine yazmaz. Yerleşim `--yerlesim sol|sag|ust|alt` (varsayılan `sol`; yüz hangi taraftaysa yazı karşısına), boyut `--olcek 0.6-1.4`, okunmuyorsa `--karart` (yönlü gradyan), vurguyu turuncu kutuya almak için `--kutu`. `alt` yerleşimi süre etiketinin alanına girmez.
Aynı iş Video Stüdyo'da **Kapak** sekmesindedir (`vedit studio`): adayın kalem düğmesi yazı düzenleyicisini açar (canlı önizleme, kenar payı ve süre rozeti alanı, varyasyon, indir). Brief yoksa `vedit kapak` bu dosyayı ve videonun metnini (senaryo.md, yayin.md ya da digest) agy'ye verir; agy aşağıdaki biçimde brief yazar, sonra her aday için zemin üretir. Adaylar `work/gorsel/kapak/youtube/`, brief `brief.json`.

## Önce paket
1. Kapak ve başlık tek birimdir (`/yt-package`). Başlık yazılmadan kapak yazılmaz.
2. Kapak, videonun en heyecan verici anını ya da vaadini gösterir ve video ilk 30 saniyede o vaadi karşılar. Kapakta olmayan şeyi vaat etme, videoda olmayan şeyi gösterme (MrBeast rehberi: sarı şato vaat edip kırmızı şato göstermek izleyiciyi kaçırır).
3. YouTube Test & Compare kazananı tıklamayla değil izleme süresi payıyla seçer. Tıklama tuzağı kapak bu ölçüde kaybeder.

## Kurallar
YAP
- Tek odak: bir yüz ya da bir nesne. Toplam en çok 3 öğe (yüz/avatar, ana nesne, yazı).
- Yazı en çok 3-4 kelime (ek sözle toplam 5); başlığı tekrar etmez, başlığın açtığı soruyu keskinleştirir. Referans ortalaması 3 kelime.
- Varsayılan stil `turuncu`: vurgu kelimesi turuncu `#FF7A00` (`<em>`), gerisi beyaz, siyah kontur, Montserrat 800. Başka stil `references/kaliplar.md` tablosundan seçilir. Yazı görsele gömülmez.
- Yüksek kontrast: koyu sade zemin üzerinde parlak ana nesne ya da tersi. Arka plan bulanık ya da düz.
- Yüz varsa duygu net ve tek: merak, şaşkınlık, kararlılık. Kapalı ağızlı ifade MrBeast testlerinde daha uzun izleme verdi; ağız açık şaşkınlığı varsayılan yapma.
- Sol üçte bir ya da sağ üçte bir yazı için boş kalır; yüz/avatar karşı tarafta.
- Sağ alt köşe boş: YouTube süre etiketi orayı örter.
- Seri tutarlılığı: aynı kanalda aynı yerleşim, aynı yazı stili, aynı vurgu rengi (`viral-kurgu` madde 9).
- Küçük boyut testi: kapağı 168×94 px'e indirip bak; yazı okunmuyor ya da odak kayboluyorsa aday düşer.

YAPMA
- Gerçek kişinin yüzünü, kanal logosunu ya da başkasının kapağını kopyalama; yalnız kalıp alınır. Konuşmacı kullanıcının Flow avatarıdır (`yuz.png` gerçek kareden).
- Ok, daire, emoji yığını, üç satırdan uzun yazı, küçük ayrıntı.
- Görselde harf, logo, sahte arayüz yazısı (agy'ye "no text" zaten verilir).
- Aynı açıdan beş aday: her aday farklı bir açı dener.

## Açılar (adaylar arasında çeşitleme)
Aday sayısı kadar farklı açı seç, sırayla:
1. **Sonuç:** vaadin bittiği an (bitmiş ürün, büyük sayı, önce/sonra).
2. **Karşıtlık:** iki şey yan yana, biri kazanıyor (eski/yeni, pahalı/ücretsiz).
3. **Merak:** bir şey saklı ya da yarım; izleyici ne olduğunu sormalı.
4. **Duygu:** yüz/avatar büyük, tek güçlü ifade, nesne küçük.
5. **Nesne:** yüz yok, tek ikonik nesne çok yakın (1of10: iş nişinde yüzsüz kapak da iyi çalışır).

## Brief biçimi
`brief.json` bir JSON dizisidir; her nesne:
```json
{"sahne": "English: one subject, what it does, where", "ifade": "English facial expression, empty if no person",
 "kompozisyon": "subject on the right third, chest-up, large", "isik": "warm key light, cool rim light",
 "palet": "deep navy with one orange accent", "yazi_alani": "the left third",
 "satir1": "kısa ilk satır", "satir2": "vurgulu ikinci satır", "vurgu": "satir2 içinden tek kelime", "aci": "sonuç"}
```
- Sahne alanları (`sahne`, `ifade`, `kompozisyon`, `isik`, `palet`, `yazi_alani`) İngilizce, kısa cümle. agy prompt'u ve dış platform master prompt'u bunlardan kurulur (ADR 0052). Görselde yazı yok; sağ alt köşe boş. 16:9.
- `prompt` yalnız elle verilir ve sahne alanlarını ezer. Eski yalnız-`prompt` brief aynen çalışır.
- `satir1`, `satir2` videonun dilinde (TR ya da EN); toplam en çok 6 kelime, ideal 3-4. Türkçe harfler kodla yazılır, sorun yok.
- `vurgu` `satir2`'de geçen tek kelime; boşsa tüm ikinci satır vurgu rengini alır.
- `kalip`, `ek`, `stil`: `references/kaliplar.md` tablosundan. Her aday farklı açı ve, videoya uyuyorsa, farklı kalıp dener. Geçersiz kalıp ya da stil sessizce varsayılana düşer.

## Seçim ve teslim
1. Adayları kullanıcıya göster (Stüdyo Kapak sekmesi ya da yolları ver); ölçüm uyarısı olan adayı ve varsa eleştiri puanını söyle. Kullanıcı seçer; ajan seçmez.
2. Beğenilmezse: sorun yazıda ya da düzendeyse `--duzenle N` (`--kalip`, `--stil`, `--ek`; zemin kalır), zemindeyse brief'i düzelt (`--prompt` ya da `brief.json`); toptan yeniden üretme. agy kotası dar (5 saatte birkaç görsel); kota dolarsa `--zemin` ile eldeki kareye geç ya da Flow'a (`gorsel-uret`).
3. `--sec N` adayı `Projeler/outputs/<stüdyo>/<proje>/kapak.jpg` yapar (varsa `-v2`). Test & Compare en çok 3 kapak alır: YouTube'a en iyi 3 aday gider, seçilen birincidir.
4. `yayin.md` kapak bölümüne dosya adı ve kapak yazısı yazılır.
5. `denetim` üretilmiş zemini AI slop açısından da değerlendirir: yapay parlaklık, bozuk el, anlamsız şekil, şablon kompozisyon.
