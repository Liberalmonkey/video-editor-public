---
name: usta-editor
description: 15 yıllık kıdemli video editörü gibi kurgu kararı verme — kesim sebebi, ritim eğrisi, zoom ve geçiş disiplini, ses önceliği, J/L cut, yayın öncesi göz ve kulak denetimi. Bir videoyu editlerken, kurguyu eleştirirken, "profesyonel görünmüyor", "ritim yok", "ses oturmamış" dendiğinde kullan. footage-editing ve sound-design ile birlikte çalışır.
---

# Usta editör

Sıra her zaman aynıdır: hikâye, ritim, ses, görüntü süsü. Bir efekt hikâyeye hizmet etmiyorsa kesilir. Amatör kurgu ne eklediğiyle, usta kurgu neyi eklemediğiyle anlaşılır.

## Bir kesimin altı sebebi

Walter Murch'ün önem sırası. Üstteki için alttakinden vazgeçilir, tersi yapılmaz.

1. Duygu: bu anda izleyici ne hissetmeli?
2. Hikâye: kesim anlatıyı ilerletiyor mu?
3. Ritim: doğru anda mı geliyor?
4. Bakış: izleyicinin gözü nerede, kesimden sonra orayı bulabiliyor mu?
5. Ekran düzlemi: yön ve kadraj tutarlı mı?
6. Mekân sürekliliği: nesneler ve konumlar tutuyor mu?

Bir kesimin bu listeden sebebi yoksa o kesim yapılmaz.

## Karar kuralları

- **Sesle kes, görüntüyle örtme.** Önce konuşmayı bitir. Görüntü kurgusu temiz ses kurgusunun üstüne yapılır.
- **Düşünce biterken kes.** Cümle bittikten sonra gelen 4–8 karelik nefes, izleyicinin anlamasını sağlar. Her boşluğu silmek metni acele ettirir.
- **Harekette kes.** Tıklama, el, kaydırma, başlık girişi gibi bir hareketin ilk üçte birinde kesilen geçiş görünmez olur.
- **Bakış yönünü hazırla.** Yeni görüntüde önemli öğe, önceki karede gözün kaldığı yere yakın olsun. Ekran kaydında imleci takip et.
- **J-cut ile yeni fikri aç, L-cut ile eski fikri bitir.** Ses önce gelince izleyici kesimi fark etmez. Düz kesim vurgu içindir.
- **Bir kurala üç kez uy, sonra kır.** Beklenti kurulmadan kırılan kural hata gibi görünür.

## Ritim: düz çizgi yasak

Aynı uzunlukta art arda kesimler slayt gösterisi hissi verir. Süreyi bilgi yoğunluğu belirler.

| Bölüm | Görüntü değişimi | Not |
|---|---|---|
| Hook (0–15 sn) | 1–3 sn | En sıkı yer, tek söz bile boş kalmaz |
| Bağlam | 3–6 sn | İzleyiciyi yerleştir, nefes ver |
| Gövde | 4–8 sn, her 30–60 sn kırılma | Yeni görsel dil, soru ya da sayı |
| Doruk öncesi | 2–4 sn | Hızlan |
| Doruk | 6–10 sn | Yavaşla. Büyük an tek başına durur |
| Kapanış | 5–10 sn | Sakin, son 10–20 sn end screen |

Karmaşık bilgi ekrandayken kesim yavaşlar. Duygu ya da heyecan anında hızlanır. Müziksiz sessizlik de ritim aracıdır: büyük andan önce 0.3–0.6 sn sessizlik, sonraki sesi iki kat güçlü duyurur.

## Zoom disiplini

Zoom bir cümledir, süs değildir. Her zoom "şuna bak" der; söylenecek bir şey yoksa yapılmaz.

- **Punch-in (anlık %110–118):** jump cut gizler, sessizdir. Üst üste iki kez aynı ölçek kullanılmaz.
- **Yavaş itiş (3–8 sn, %100→%106):** konuşan kafada gerilim kurar, duyulmaz. Ses eklenmez.
- **Odak zoom'u (0.4–0.7 sn, ease-out):** ekran kaydında anlatılan öğeye gider. Söylenen kelimeden 2–4 kare önce başlar, sesi vardır.
- **Geri çıkış (0.3–0.5 sn):** konu bitince yapılır, girişten kısa ve kısıktır. Her zoom'un çıkışı olmak zorunda değil; yeni kesim de çıkıştır.
- Bir ekran kaydında dakikada en çok 4–6 duyulur zoom. Üst üste zoom in + zoom out + zoom in baş döndürür.
- Keyframe hiçbir zaman lineer olmaz. Hedefi önce belirle: zoom bittiğinde öğe kadrajın üçte birinde durmalı ve yazı okunur olmalı.

## Geçiş disiplini

Videonun %90'ı düz kesimdir. Geçiş, anlam değişimini söyler.

| İhtiyaç | Geçiş | Ses |
|---|---|---|
| Aynı konu, yeni görüntü | Düz kesim | Yok |
| Aynı konu, zaman atlaması | Kısa çapraz geçiş (8–12 kare) | Yok ya da çok alçak |
| Yeni bölüm | Tek aile: whip, push ya da bölüm kartı | Whoosh, tepe kesme karesinde |
| Enerji sıçraması | Whip / hızlı slide (6–10 kare) | Kısa whip |
| Sayfa çevirme, defter vb. | Yalnız görsel dil bunu taşıyorsa | Sayfa sesi |

Videonun tamamında en çok 2–3 geçiş ailesi olur. Rastgele geçiş, editörün en belirgin amatör izidir.

## Ses: kulak gözden önce karar verir

İzleyici kötü görüntüyü affeder, kötü sesi affetmez. Öncelik: konuşma > anlamlı efekt > müzik > ortam.

Her olay için `edit/olaylar.json` yazılır, ses `vedit olaysesi` ile eklenir. Kurallar:

| Olay | Ses | Yerleşim | Seviye |
|---|---|---|---|
| Görünmez kesme | Yok | — | — |
| Punch-in | Yok, açık vurgu istenirse çok alçak | Kesme karesi | Soft −12 |
| Odak zoom'u | Yükselen whoosh | Tepe, varışın %90'ında | Soft −6 |
| Geri çıkış | Düşen, kısa whoosh | Tepe, hareketin başında | Soft −9 |
| Geçiş | Whoosh | Tepe, kesme karesinde | Medium −3 |
| Bölüm değişimi | Whoosh + kısa müzik değişimi | Kesme karesinde | Medium |
| Tıklama, yazma | Kitteki sabit ses | Görüntüyle aynı kare | Soft |
| Reveal | Riser + sessizlik ya da vuruş | Riser reveal'de biter | Medium |

- **Efekt konuşmayı asla örtmez.** Konuşma üstünde 4 dB geri çekilir (otomatik). Kelimenin anlaşılmadığı yer hatadır.
- **Duyulmayan ses en iyi sestir.** Efekti kapatınca eksikliği hissediliyorsa doğru seviyededir. Fark ediliyorsa fazladır.
- **Süre hareketle eşleşir.** 0.5 sn zoom'a 2 sn whoosh konmaz. Motor en yakın süreyi seçer ve kırpar.
- **Yön anlam taşır.** Yaklaşan hareket yükselen, uzaklaşan hareket düşen sesle gider.
- **Tekrar kulağa takılır.** Motor perdeyi ±%3 değiştirir ama aynı türü dakikada 6'dan çok kullanma.
- **Sessizlik bırak.** Sürekli ses, hiçbir sesin önemli olmaması demektir.
- **Oda tonu kesilmez.** Kesimde arka plan sesi sıçrıyorsa kısa çapraz geçiş ver. Kesim sıfır geçişte yapılır; 10–20 ms geçiş tık sesini önler.
- **Müzik yapıyla konuşur.** Bölüm değişimi müzik cümlesine denk gelir. Konuşmada −12…−16 dB ve ducking. Bir parçayı ortasından kesip atlama; zorunluysa vuruşta geçir.

## Yeni başlayan izleri

Bunlardan biri varsa düzelt: her kesimde whoosh · her cümlede zoom · kesimsiz 20 sn statik ekran · farklı aile geçişler · cümle ortası kesim · boşlukları tamamen silinmiş nefessiz konuşma · müzik konuşmayla aynı seviyede · yazı okunamadan kayboluyor · sürekli aynı ölçekte punch-in · siyahtan açılış · sonda ani bitiş.

## Yayın öncesi üç geçiş

1. **Gözsüz:** görüntüye bakmadan dinle. Anlaşılmayan kelime, tık, sıçrayan oda tonu, fazla efekt var mı?
2. **Sessiz:** sesi kapatıp izle. Akış ve ekran metni sessizde anlaşılıyor mu?
3. **Taze göz:** videoyu hiç görmemiş bir denetçi ajana yalnız kontak sayfası, ses raporu ve senaryoyu ver. Soru: "İzleyici burada neden çıkar?" Bulguyu P0/P1/P2 yaz (`denetim`).

Son geçiş: `denetim`. Slop anları zaman damgası ve öneriyle kullanıcıya gösterilir, onaysız uygulanmaz.

Ölçümler: `vedit qa` (veya OpenMontage çıktısında `ffprobe`), `<olaylar>.rapor.json` (yerleşen, düşen, uyarılar), −14 ±1 LUFS, ≤ −1 dBTP. Otomatik denetim temiz diye video iyi sayılmaz; son söz kullanıcının gözünündür.

## Teslim notu

`renders/` önizlemesiyle birlikte kullanıcıya 5 satır ver: süre, hook, en güçlü an, bilinçli verilen kararlar, kararsız kalınan yer. Zevk kararı gerektiren yeri sor, tahmin etme. Yeni bir zevk kararı verilirse kuralı buraya ya da stil paketine yaz.


## Altyazı ve düzeltme defteri (ADR 0014)
- Altyazı her videoda aynıdır: okunan kelime turuncu, gerisi beyaz, siyah kontur, Montserrat 800. Stil seçilmez.
- Editten önce `library/checks.md` okunur. Kullanıcının her düzeltmesi oraya tek satır YAP / YAPMA olarak eklenir.
- Kesim sonrası `vedit kesimqa` çalışır.
