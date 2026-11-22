---
name: loop-flow
description: Google Flow (Veo) ile sürekli dönen "canlı slayt" loop videoları üretir. Karakter ve stil tutarlılığı, görsel prompt'u, Flow kare ayarı, hareket prompt'u, kesintisiz loop mührü (ping-pong / çapraz geçiş), sarma ölçümü, kurguya yerleştirme ve kliplerden uzun sahne kurma. "loop video", "canlı slayt", "sunum gibi hareketli arka plan", "Flow", "Veo" dendiğinde kullan.
---

# Google Flow ile loop

Yöntem kaynağı: Avenox'un videosu ve notları, bkz. `wiki/sources/2026-11-02-loop-slayt.md`. Üretim aracı Higgsfield/Seedance yerine Google Flow'dur. Flow'un API'si projeye bağlı olmadığı için **üretimi kullanıcı yapar**: Claude prompt'u hazırlar, klip `malzeme/loop/` klasörüne gelir, Claude mühürler ve kurguya koyar.

Fikir basit: tek görsel + kısa, küçük hareket + kesintisiz dönüş. Ekranda durgun slayt yerine canlı bir sahne durur. Kalite iki kaynaktan gelir: görsellerin aynı elden çıkması ve dönüş noktasının görünmemesi.

## 1. Stil kilidi

Önce tek paragraflık stil tanımı yaz: teknik, zemin, çizgi, palet (2–3 renk), kompozisyon, yazı yasağı. Bu paragraf **her prompt'a kelimesi kelimesine** girer. "Önceki gibi" denmez; model önceki işi hatırlamaz.

- İlk turdan en iyi kareyi seç, sonraki üretimlere referans görsel olarak ekle.
- Tekrarlayan karakter varsa siluet, ifade, oranlar ve bir yasak liste yaz ("asla: gerçekçi yüz, ek uzuv…").
- Yazıyı görsele gömme. Metin kurguda eklenir; görsel içi Türkçe en kırılgan parçadır.
- Stil dosyası: `<proje>/BRIEF.md` ya da `studios/<s>/styles/<ad>/`.
- Başlangıç görseli `gorsel-uret` skill'inin motor sırasıyla hazırlanır (Antigravity CLI ya da Flow Nano Banana).

## 2. Karakter tutarlılığı

1. Görsel üretiminde varyasyon deneyip tarzı yakala.
2. Aynı karakter için karakter sayfası üret: önden, yandan, arkadan, 3–4 ifade.
3. Flow'da "Ingredients" alanına karakter sayfasını referans olarak ekle.

Yalnız yüz değil kıyafet ve renkler de aynı kalmalı.

## 3. Klip ayarı

- Tür: **Frames to video** (Flow'da "Video Frames"). Başlangıç karesi seçilen görsel.
- **Yöntem A, doğal dönüş:** başlangıç ve bitiş karesine **aynı görseli** koy. Tek yönlü hareket de mümkün olur; önce bunu dene.
- **Yöntem B, mühür:** yalnız başlangıç karesi ver, küçük hareket üret, sonra ping-pong ile mühürle.
- Süre: en kısa yeterli süre (4–6 sn). Sessiz kullanılır, Flow'un ürettiği ses atılır.
- Model: önce hızlı ya da ekonomik seçenek, tutan kareyi kaliteli seçenekle yeniden üret. Kredi ve süre seçenekleri değişir; arayüzde gördüğünü esas al.

Flow'un bu kullanımda sarmayı gerçekten kapatıp kapatmadığı doğrulanmadı. Bu yüzden her klip `vedit loop kontrol` ile ölçülür.

## 4. Hareket prompt'u

Sahneyi yeniden tarif etme; **yalnız hareketi** söyle. Kilitli kamera loop'un en büyük dostudur.

```
Animate only subtle idle motion: [karakter hafifçe nefes alır ve göz kırpar],
[arka plandaki ışık yavaşça titrer], [toz zerreleri süzülür].
Camera locked, no zoom, no pan, no cuts, no new elements, no text.
The final frame matches the first frame exactly. Seamless loop.
```

- Ping-pong'a uygun: nefes, salınım, ışık, duman, su, yaprak.
- Ping-pong'a uygun değil: yürüme, akan yazı, dökülen sıvı, tek yönlü araba. Bunlar geri geri gider; Yöntem A ya da `--mod capraz` kullan.
- Prompt'u İngilizce yaz. Türkçe açıklamayı `aciklama` alanında kullanıcıya ver.

## 5. Mühür ve ölçüm

```bash
.venv/Scripts/vedit loop kontrol malzeme/loop/L01-sahne.mp4
.venv/Scripts/vedit loop muhur malzeme/loop/L01-sahne.mp4
```

- `otomatik`: sarma temizse sesi atıp bırakır, değilse ping-pong yapar. Çıktı `L01-sahne.loop.mp4`.
- `--mod capraz --capraz 0.6`: kuyruğu başa eritir; tek yönlü hareket için.
- `--sure 24`: kurgudaki sahne uzunluğuna kadar yeniden kodlamadan sarar.
- Sarma farkı, ardışık kare farkı medyanının 1,5 katını aşıyorsa rapor "SARMA GÖRÜNÜR" der. Yeniden üret ya da modu değiştir. Son söz gözündür: dönüşü birkaç kez izle.

## 6. Kurguda kullanım

- **Canlı slayt:** tam ekran loop + üstünde kısa başlık. Konuşma sürerken 8–20 sn durabilir, ama fikir değişince görüntü de değişir.
- **Kart içinde:** kenarlıklı "baskı plakası" olarak açık zemin görsel, koyu sayfada. Karartma ya da çarpma karışımı görseli yutar.
- **Geçiş:** loop'tan loop'a geçişte tek aile kullan. Ses için `gecis` ya da `slayt` olayı yaz (`sound-design`).
- Sahne içinde küçük itiş (%100→%104) loop'u daha canlı gösterir; hareketi loop süresinden bağımsız tut.
- Çok şey oynuyorsa hiçbir şey oynamıyordur. Ekranda tek bir canlı öge, kalanı sakin.

## 7. Birden çok klipten sahne

Kısa klipler birleştirilirse dikişler gizlenmeli. Yüksekten düşüğe verim sırası:

1. **Bir sonraki klibin sesini 0,5 sn önce başlat.** Kulak geçişi önce kabul eder.
2. **Son kareyi sonraki klibin başlangıç karesi yap.** Karakter ve mekân kaymasını en çok bu azaltır (Flow'da Extend de son saniyeden devam eder).
3. **Hareket bulanıklığında kes:** iki klibi aynı yönde hızlı kamera hareketiyle bitir ve başlat.
4. **Nesnenin içinden geç:** duman, kapı, el kadrajı kaplar, kesim orada yapılır.
5. **Şekil eşleme:** daire biter, daire başlar. En zor olanı.
6. **Tek renk düzeltmesi:** tüm kliplere aynı renk ayarı. Üretim izini en ucuz azaltan adım.

Üretilen süreyi aynen kullanma; ritme göre kırp. Girişte daha uzun, ortada kısa, doruğu tutan, kapanışta kısa kesimler (`usta-editor`).

## 8. Üretim listesi

Her loop projenin `ISTEK.md` dosyasında ayrı bir kalemdir (tür `loop`, kimlik `L01`…). Prompt olarak stil kilidi + hareket prompt'unu yaz, açıklamaya Flow'da yapılacakları Türkçe yaz:

```json
{ "id": "L01", "tur": "loop", "sahne": "Hook", "sure": "4–6 sn, 16:9",
  "aciklama": "Flow > Frames to video. Başlangıç ve bitiş karesine L01-gorsel.png koy, prompt'u yapıştır.",
  "prompt": "..." }
```

Görsel de üretilecekse ayrı kalem aç (`L01-gorsel`, tür `loop`, prompt'ta tam stil kilidi). Toplu üretimde aynı dosyadan iki tane gelmiş olabilir; `certutil -hashfile` ya da benzer karşılaştırmayla kontrol et.

## Kontrol

- [ ] Stil paragrafı tüm prompt'larda aynen var
- [ ] Görsellerde yazı yok, karakter aynı
- [ ] Kamera kilitli, hareket küçük
- [ ] `vedit loop` raporu temiz ve dönüş gözle izlendi
- [ ] Ses atıldı, kurgudaki süre doğru


## Üretilen klipte ses ve kalite (ADR 0014)
- Üretilen klibin sesi atılır; kurgu sesi özgün kaynaktan gelir.
- Önce taslak üret, onaydan sonra yüksek kaliteye geç.
