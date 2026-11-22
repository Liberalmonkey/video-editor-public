# checks.md

Kullanıcının her düzeltmesi buraya tek satırlık bir YAP ya da YAPMA kuralı olarak eklenir. Ajan bu dosyayı sahne ya da pano yazmadan önce okur, `denetim` her kontrol karesini buna göre denetler. Yöntem: YouTube-AI-Motion-Graphics `checks.md` (MIT).

Biçim: `- YAP / YAPMA: kural (kuralı doğuran proje)`

Kapı kuralı (Avenox, MIT; ADR 0041): yazmadan önce burada ara. Aynı düzeltme ikinci kez geliyorsa kural not olarak kalmaz, koda yazılır (`vedit kurgu-denetle` uyarısı, `denetim` ölçümü ya da test); satırın sonuna `(kapı: <kod>)` eklenir. Transkriptte yanlış yazılan ad `library/sozluk.json`'a girer.

## Altyazı
- YAP: stil seçilmemişse okunan kelime turuncu `#FF7A00`, diğer kelimeler beyaz, siyah kontur, Montserrat 800. Her motorda. (kullanıcı isteği, 2026-11-03)
- YAP: stil seçiliyse altyazı stilin token'ını alır (font, okunan kelime rengi, kontur); kontrast ölçülür. Kapı: `tema_token.altyazi_tokeni`, `Kurgu.tsx temaAltyazisi` (kullanıcı isteği, 2026-11-19, ADR 0043)
- YAPMA: stil açıkça istemedikçe altyazıya kutu, pop, gölge ya da solgun kelime koyma. (kullanıcı isteği, 2026-11-03)

## Kadraj
- YAP: konuşmacı kadrajdaysa kamera alanını boş bırak; okunur hiçbir şey oraya girmesin.
- YAP: stüdyonun güvenli alanı dışına okunur öğe koyma.
- YAP: okunur yazı 1080p'de en az 28 px. Sığmıyorsa küçültme, kelime kes.
- YAPMA: gerçek görüntüyü oranını bozarak kırpma.

## İçerik
- YAPMA: panoya paragraf koyma. Çiz ve tek fikir göster.
- YAP: pano başına tek iddia, başlık olarak yaz.
- YAPMA: sayı, logo, alıntı ya da görüntü uydurma. Eksik varlık kesik çizgili "bekliyor" kartı olur.

## Hareket
- YAPMA: sahneyi boş açma. İlk karede gerçek bir şey ekranda olsun.
- YAP: öğe kendi kelimesinde girsin. Kelimeden önce değil, en geç 2 sn sonra.
- YAPMA: konuşma sürerken ekran 5 sn'den uzun durağan kalmasın.

## AI slop
- YAP: edit sonrası `denetim` çalıştır, bulguları kullanıcıya öner. Reddedilen bulguyu sebebiyle buraya yaz, bir daha sayma.

## Düzeltmeler
<!-- Yeni kurallar bu satırın altına, en yenisi en altta. -->
- YAPMA: geçiş ve sayaç sesinde `synth-*` örneklerini kullanma; kütüphaneden gerçek kayıt seç (mixkit, kenney, remotion). Sentetikler "pırt" gibi duyuluyor. (01-php2shell, 2026-11-04)
- YAPMA: slop ölçümündeki `OLAY_TEK_TUR` bulgusunu sayma; tek geçiş ailesi `usta-editor` kuralıdır, çeşitlilik eksikliği değil. (08-claude-code-5-skill, 2026-11-04)
- YAPMA: senaryoda ya da malzeme listesinde kullanıcının kamera karşısına geçtiğini varsayma; konuşmacı kullanıcının Google Flow'da ürettiği avatardır, malzeme listesi klip başına prompt verir. (09-claude-code-video-edit, 2026-11-04)
- YAP: nasıl yapılır Reels'inde izleyiciye doğrudan seslen, adımları emir kipiyle ver, harekete geçir; yalnız "ben şunu yaptım" diye anlatma. (09-claude-code-video-edit, 2026-11-04)
- YAPMA: kullanıcı istemedikçe senaryoda üçüncü taraf repo adı ve yıldız sayısı kullanma. (09-claude-code-video-edit, 2026-11-04)
- YAP: girdide müzik yoksa atlamadan önce `library/music/manifest.json` ve klasörüne bak, uygun parçayı kullan. (instagram-reels-video, 2026-11-05)
- YAP: her teslimde videoyla birlikte platforma uygun açıklama ve hashtag ver (`yayin.md`). (instagram-reels-video, 2026-11-05)
- YAP: motion grafiğinin rengi seçili stilden ya da videonun kendi renklerinden gelsin; kullanıcı istemedikçe turuncu (`varsayilan`/`turuncu`) tema yazma. Kapı: `kurgu.etkin_tema`, ai-edit tema bölümü. (stil-paneli, 2026-11-18)
- YAPMA: klip başına `metin_stil.renk/vurgu/arka` yazma; renk, font, köşe ve hareket seçili stilin token'ından gelir. Kapı: `kurgu-denetle` STIL_DISI_RENK, `tests/test_sabit_renk.py` (instagram/1, 2026-11-19, ADR 0043)
- YAPMA: ikonun ya da rozetin arkasına disk, halka, rozet ya da kutu koyma; ikonun kendisi stilin vurgusuyla çizilir, okunurluk yalnız ince kontur ve gölgeyle. Kapı: `tests/test_ikon_alfa.py` (instagram/1, 2026-11-19, ADR 0043)
- YAPMA: alfalı motion kaynağını (VP9 `alpha_mode=1`, ProRes 4444) H.264 proxy'ye çevirme; önizlemede siyah kutu olur. Kapı: `studio/app.py medya_eslemesi`, `tests/test_alfa_seffaf.py` (instagram/1, 2026-11-19)
