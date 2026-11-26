---
name: yaratici-yon
description: Kurgudan önce videoya özgü yaratıcı yönü kurar — tez, enerji eğrisi, imza anları, görsel metafor, iplik öğe, ses fikri, bilinçli riskler ve yasak klişeler (work/edit/yaratici-brif.json). ai-edit ve swarm'da G0.5 kapısıdır; bütün editörler ve kalite kontrol bu brife göre karar verir. Yeni bir edit başlarken, "yaratıcı yön", "konsept", "imza anı", "sıradan duruyor", "şablon gibi", "akılda kalmıyor" dendiğinde kullan. sanat-yonetimi, hikaye-matematigi ve usta-editor ile birlikte çalışır.
---

# Yaratıcı yön

Kural listesi kötü kurguyu önler, iyi kurguyu yaratmaz. İyi kurgu bir fikirden çıkar. Bu skill her video için o fikri tek sayfada yazdırır. Böylece editörler aynı hikâyeye hizmet eder ve kalite kontrol "doğru ama sıradan" olan sonucu yakalayabilir.

Brif kısa ve somut olur. Her madde bu videonun malzemesine dayanır: söylenen söz, görünen ürün, ekrandaki arayüz, sayı. "Dinamik ve modern" gibi her videoya uyan söz brif değildir.

## Brifin sekiz alanı

1. **Tez (`tez`):** izleyici videodan çıkınca aklında kalacak tek cümle. Konuşmanın özeti değil, videonun vaadi.
2. **Görsel metafor (`metafor`):** fikri izleyicinin gözünde canlandıran tek imge ya da nesne. Örnekler: zaman kazancı için eriyen kum saati; karmaşadan düzene giden bir masa; birbirine bağlanan düğümler. Metafor konuşmadan çıkar, kütüphaneden değil.
3. **İplik öğe (`iplik`):** bütün grafikleri birbirine bağlayan tek tasarım öğesi: bir çizgi, bir şekil, bir renk rolü ya da bir hareket. Videonun başında tanıtılır, sonunda geri döner.
4. **Enerji eğrisi (`enerji`):** videoyu 3–7 bölüme ayır, her bölüme 1–5 arası enerji ver ve nedenini yaz. Düz çizgi yasak: yüksek enerjiden önce bir nefes, doruktan sonra bir iniş olur. Grafik yoğunluğu, kesim hızı ve ses bu eğriyi izler. Sakin bölüm bilinçli bir seçimdir, eksik değildir.
5. **İmza anları (`imza_anlari`):** izleyicinin paylaşacağı ya da hatırlayacağı 1–3 an. Her biri söylenen bir söze çapalanır (`soz`, yaklaşık `t`) ve ne olacağı tek cümleyle yazılır. İmza anı kataloğun ilk satırı olmaz; bu videoya özgü bir birleşimdir: metaforun ekranda gerçekleşmesi, sessizlikten sonra gelen bir vuruş, bir match cut, sayının fiziksel bir nesneye dönüşmesi.
6. **Ses fikri (`ses`):** müziğin karakteri, sessizliğin nerede kullanılacağı ve vuruşun nereye düşeceği. Ses görüntüyü taşır: büyük andan önceki 0,3–0,6 saniyelik boşluk, ardından gelen sesi iki kat güçlü duyurur.
7. **Bilinçli riskler (`riskler`):** bu videoda kalıbın dışına çıkılan 1–3 karar ve gerekçesi. Örnekler: hook'u sessiz bir kareyle açmak; tek bir grafiği 6 saniye tutmak; doruğu yavaşlatmak; konuşmacıyı tamamen ekrandan çıkarıp yalnız metaforu göstermek. Risk, kuralları çiğnemek değildir; P0 kuralları her zaman geçerlidir.
8. **Yasak klişeler (`yasak`):** bu video için bilerek kullanılmayacak 3–5 şey. Örnekler: her bölüm başında aynı kapsül başlık, her kesimde whoosh, ortalanmış büyük başlık, anlamsız ikon serpme, her konuşan kafa klibinde aynı zoom.

## Nasıl düşünülür

- **Önce malzeme:** transkripti oku ve en güçlü üç cümleyi bul. Tez ve imza anları çoğu zaman bu cümlelerdedir.
- **Seçenek kur, sonra seç:** aklına gelen ilk fikir genellikle herkesin aklına gelendir. İki farklı metafor düşün; konuya en özgü ve ekranda en kolay okunanı seç.
- **Kontrast ara:** önce / sonra, yavaş / hızlı, kalabalık / boş, ses / sessizlik. Enerji eğrisi ve imza anları kontrastla çalışır.
- **Platformu unutma:** Reels'te ilk 1–2 saniye ve gönderme isteği, YouTube'da ilk 30 saniye ve bölüm vaatleri belirleyicidir (`viral-kurgu`).
- **Stil çerçevedir, kafes değil:** renk, font ve eğri seçili stilin token'ından gelir (ADR 0043). Yaratıcılık bu token'ların nasıl kullanıldığında, zamanlamada, kompozisyonda ve fikirdedir.

## Kendi brifini sına

Brifi teslim etmeden önce dört soruya yanıt ver:
1. Bu brif başka bir videoya da uyuyor mu? Uyuyorsa fazla geneldir; malzemeye in.
2. İmza anlarının her biri tek kareyle tarif edilebiliyor mu?
3. Enerji eğrisinde en az bir sakin, en az bir yüksek bölüm var mı?
4. Riskler izleyiciye hizmet ediyor mu, yoksa yalnız farklı olmak için mi alındı?

## Biçim

`work/edit/yaratici-brif.json` (vedit doğrular; alan adları sabittir):

```json
{"tez": "<tek cümle>",
 "metafor": "<tek imge ve neden>",
 "iplik": "<tek tasarım öğesi>",
 "enerji": [{"aralik": [0, 3.5], "seviye": 5, "neden": "hook: sonuç önce"}],
 "imza_anlari": [{"t": 12.4, "soz": "<söylenen söz>", "ne": "<ekranda ve seste ne olur>"}],
 "ses": "<müzik karakteri, sessizlik ve vuruş anları>",
 "riskler": ["<karar: gerekçe>"],
 "yasak": ["<bu videoda kullanılmayacak klişe>"]}
```

`istek` ve `kilit` alanlarını vedit yönetir. Kullanıcı brifi elle yazıp `"kilit": true` koyarsa brif yeniden üretilmez. Brif yoksa ya da geçersizse edit bugünkü gibi sürer; brif hiçbir zaman edit'i durdurmaz.

## Ekipte

- Orkestratör brifi G0 planıyla aynı çağrıda yazar. `--hizli`'de brif E1'e paralel tek kısa çağrıdır. Tek ajan (`vedit ai-edit`) önce brifi, sonra kurguyu yazar.
- Editörler kararlarını brife bağlar ve raporda hangi brif maddesini nasıl taşıdıklarını söyler. Kartının aralığına düşen imza anı o editörün sorumluluğudur.
- Kalite kontrol taslağı brife karşı da okur: imza anı teslim edildi mi, enerji eğrisi hissediliyor mu, yasak klişe kullanıldı mı?
