# checks.md

<!-- ÜRETİLMİŞ DOSYA: elle düzenleme. Tek kaynak library/kurallar/kurallar.json (ADR 0047). Kural eklemek için: vedit kural ekle "YAP: ..." ya da Stüdyo > Kurallar. -->

Kullanıcının her düzeltmesi ve kalite kontrolün genelleşmiş bulgusu burada tek satırlık YAP ya da YAPMA kuralıdır. Ajan editten önce okur; `denetim` her kontrol karesini buna göre denetler. Aynı düzeltme ikinci kez gelirse kural koda kapı olarak yazılır (ADR 0041). Köşeli parantez: kimlik, önem, tekrar.

## Altyazı
- YAP: stil seçilmemişse okunan kelime turuncu `#FF7A00`, diğer kelimeler beyaz, siyah kontur, Montserrat 800. Her motorda. [K0001 P0] (global)
- YAP: stil seçiliyse altyazı stilin token'ını alır (font, okunan kelime rengi, kontur); kontrast ölçülür. [K0002 P0] (global; kapı: `tema_token.altyazi_tokeni`, `Kurgu.tsx temaAltyazisi`)
- YAPMA: stil açıkça istemedikçe altyazıya kutu, pop, gölge ya da solgun kelime koyma. [K0003 P0] (global)

## Kadraj
- YAP: konuşmacı kadrajdaysa kamera alanını boş bırak; okunur hiçbir şey oraya girmesin. [K0004 P1 ×3] (global)
- YAP: stüdyonun güvenli alanı dışına okunur öğe koyma. [K0005 P1] (global)
- YAP: okunur yazı 1080p'de en az 28 px. Sığmıyorsa küçültme, kelime kes. [K0006 P1 ×2] (global)
- YAPMA: gerçek görüntüyü oranını bozarak kırpma. [K0007 P1] (global)

## Kesim
- YAP: örnek veya B-roll klipler içinde 0.8 saniyeyi aşan konuşmasız ölü boşlukları ve yüzün kadraj dışına taştığı anları keserek ritmi koru. [K0029 P1 ×6] (global; instagram/1)
- YAPMA: ikili diyalog planlarında yüzleri kadraj kenarından kesecek sabit zoom veya sure: 0 değerinde hazır efekt kullanma. [K0030 P1] (global; instagram/1)
- YAP: konuşan kafa kliplerinde ilk kelimenin Whisper başlangıcı 0.0 sn olsa bile konuşmacının ağzını açmadığı baştaki nefes ve bekleme payını giris zamanını ileri alarak kes. [K0036 P1 ×5] (global; instagram/1)
- YAPMA: konuşan kafa kliplerini 4.5 saniyeden uzun süre hiçbir ölçek değişimi, hazır efekt veya kesim olmadan durağan bırakma. [K0039 P1] (global; instagram/1)
- YAPMA: klipteki punch veya hazır efekt başlangıç zamanını (t) kaynak videonun mutlak zamanına göre yazma; her zaman klip içi göreli zamana (0 <= t < sure) göre tanımla. [K0034 P2 ×2] (global; instagram/1)
- YAPMA: ilk kelimenin Whisper başlangıcı 0.0 sn olan kliplerde baştaki nefes payını keserken giris değerini kelimenin bitişine (e) 0.70 saniyeden daha fazla yaklaştırıp ilk heceyi yutma. [K0043 P2] (global; instagram/1)

## Grafik
- YAPMA: ikonun ya da rozetin arkasına disk, halka, rozet ya da kutu koyma; ikonun kendisi stilin vurgusuyla çizilir, okunurluk yalnız ince kontur ve gölgeyle. [K0024 P0] (global; kapı: `tests/test_ikon_alfa.py`; instagram/1)
- YAPMA: alfalı motion kaynağını (VP9 `alpha_mode=1`, ProRes 4444) H.264 proxy'ye çevirme; önizlemede siyah kutu olur. [K0025 P0] (global; kapı: `studio/app.py medya_eslemesi`, `tests/test_alfa_seffaf.py`; instagram/1)
- YAPMA: alt bant kartını ürün yakın çekiminin merkezine ya da aynı sözü gösteren gömülü altyazının hemen üstüne yerleştirme. [K0031 P1] (global; instagram/1)
- YAPMA: konuşmacı yakın çekimdeyken ikonu ya da yön okunu orta yükseklikte yüz ve gözlük kenarına değecek biçimde yerleştirme. [K0032 P1 ×3] (global; instagram/1)
- YAPMA: konuşmacı çekiminde mikrofon kolu ya da ön plandaki nesnelerin bulunduğu orta-sol/alt kuşağa yön oku veya ikon yerleştirme; temiz üst boşluğu seç. [K0044 P1] (global; instagram/1)

## Renk
- YAP: motion grafiğinin rengi seçili stilden ya da videonun kendi renklerinden gelsin; kullanıcı istemedikçe turuncu (`varsayilan`/`turuncu`) tema yazma. [K0022 P0 ×2] (global; kapı: `kurgu.etkin_tema`, ai-edit tema bölümü.; stil-paneli)
- YAPMA: klip başına `metin_stil.renk/vurgu/arka` yazma; renk, font, köşe ve hareket seçili stilin token'ından gelir. [K0023 P0] (global; kapı: `kurgu-denetle` STIL_DISI_RENK, `tests/test_sabit_renk.py`; instagram/1)
- YAPMA: V2 grafiğini bağlı olduğu V1 klibinin kesim sınırından sonraki sahneye taşırma. [K0026 P0 ×3] (global; instagram/1)
- YAPMA: konuşan kafa planları arasında yüzleri üst üste bindiren ışık veya erime geçişi kullanma; düz kesim yap. [K0028 P1] (global; instagram/1)
- YAP: karşılaştırmalı veya çok adımlı kısa videolarda her kademeyi seçili stilin token'ıyla üretilmiş, anahtar kelimeye çapalı kısa bir V2 grafik öğesiyle görsel olarak ayır. [K0037 P1 ×2] (global; instagram/1)
- YAPMA: videodaki tüm V2 grafiklerini art arda yalnız ikon ailesinden kurma; en geç üçüncü öğede seçili stilin tipografisini gösteren farklı bir bileşen ailesiyle görsel çeşitlilik sağla. [K0045 P1] (global; instagram/1)
- YAPMA: konuşmacının doğrudan kameraya konuştuğu planda yüzü bulanıklaştıran odak_karart efektiyle tam genişlikli orta kartı aynı anda kullanma. [K0048 P1] (global; instagram/1)
- YAPMA: ardışık konuşan kafa kliplerinde üç kez üst üste aynı hazır efekti tekrarlama; punch ile zoom_in/odak_zoom arasında çeşitlilik kur. [K0041 P2 ×3] (global; instagram/1)

## Hareket
- YAPMA: sahneyi boş açma. İlk karede gerçek bir şey ekranda olsun. [K0011 P1] (global)
- YAP: öğe kendi kelimesinde girsin. Kelimeden önce değil, en geç 2 sn sonra. [K0012 P1 ×3] (global)
- YAPMA: konuşma sürerken ekran 5 sn'den uzun durağan kalmasın. [K0013 P1 ×5] (global)

## Ses
- YAPMA: geçiş ve sayaç sesinde `synth-*` örneklerini kullanma; kütüphaneden gerçek kayıt seç (mixkit, kenney, remotion). Sentetikler "pırt" gibi duyuluyor. [K0015 P1] (global; 01-php2shell)
- YAPMA: slop ölçümündeki `OLAY_TEK_TUR` bulgusunu sayma; tek geçiş ailesi `usta-editor` kuralıdır, çeşitlilik eksikliği değil. [K0016 P1] (global; 08-claude-code-5-skill)
- YAP: girdide müzik yoksa atlamadan önce `library/music/manifest.json` ve klasörüne bak, uygun parçayı kullan. [K0020 P1] (global; instagram-reels-video)

## İçerik
- YAPMA: panoya paragraf koyma. Çiz ve tek fikir göster. [K0008 P1] (global)
- YAP: pano başına tek iddia, başlık olarak yaz. [K0009 P1] (global)
- YAPMA: sayı, logo, alıntı ya da görüntü uydurma. Eksik varlık kesik çizgili "bekliyor" kartı olur. [K0010 P1] (global)
- YAPMA: senaryoda ya da malzeme listesinde kullanıcının kamera karşısına geçtiğini varsayma; konuşmacı kullanıcının Google Flow'da ürettiği avatardır, malzeme listesi klip başına prompt verir. [K0017 P1] (global; 09-claude-code-video-edit)
- YAP: nasıl yapılır Reels'inde izleyiciye doğrudan seslen, adımları emir kipiyle ver, harekete geçir; yalnız "ben şunu yaptım" diye anlatma. [K0018 P1] (global; 09-claude-code-video-edit)
- YAPMA: kullanıcı istemedikçe senaryoda üçüncü taraf repo adı ve yıldız sayısı kullanma. [K0019 P1] (global; 09-claude-code-video-edit)

## AI slop
- YAP: edit sonrası `denetim` çalıştır, bulguları kullanıcıya öner. Reddedilen bulguyu sebebiyle buraya yaz, bir daha sayma. [K0014 P1] (global)

## Yayın
- YAP: her teslimde videoyla birlikte platforma uygun açıklama ve hashtag ver (`yayin.md`). [K0021 P1] (global; instagram-reels-video)

## Teknik
- YAPMA: müzik klibinin süresini son V1 klibinin bitişinden uzun bırakıp video sonunda siyah ekran üretme. [K0035 P0 ×2] (global; instagram/1)
- YAPMA: A3 müzik klibini son V1 klibinin bitiş süresinden uzun bırakarak video sonunda boş kare oluşturma. [K0038 P0] (global; instagram/1)
- YAPMA: V1 kesimlerinde stil token'ının gecis listesinde olmayan geçiş türlerini kullanma. [K0027 P1 ×2] (global; instagram/1)
- YAP: son V1 klibini son kelimenin bitiminden en çok 0.15 saniye sonra kes ve V1 bitişiyle sekans sonu arasında boş ekran bırakma. [K0040 P1 ×2] (global; instagram/1)
- YAPMA: konuşmacının başı kadrajın üst sınırına yakınsa kafayı üst kenardan kesecek 1.05 üstü punch veya zoom_in efekti uygulama. [K0042 P1 ×3] (global; instagram/1)

## Genel
- YAP: vurgu ikonunu yardımcı fiile değil anlamı taşıyan anahtar kelimeye çapala ve sonraki cümle başlamadan ekrandan çıkar. [K0033 P1 ×2] (global; instagram/1)
- YAPMA: kademe veya bölüm etiketini örnek B-roll klibinin ortasındaki rastgele bir kelimeye çapalama; kademenin başladığı ilk kelimeye veya geçiş anına çapala. [K0047 P1] (global; instagram/1)
- YAPMA: ilk kelimesi 0.0 saniyede başlayan konuşmalı klibin girişine iki konuşmacının yüzünü üst üste bindiren geçiş efekti koyma; düz kesim yap. [K0046 P2] (global; instagram/1)
