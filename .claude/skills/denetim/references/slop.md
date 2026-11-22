# AI slop denetimi

Slop, kararsızlığın izidir: görüntü söylenene değil ortalamaya benzer. Soru "güzel mi?" değil, **"bu an bu videoya mı ait, yoksa herhangi bir AI videosundan mı kopmuş?"** sorusudur.

Bu skill bulur ve önerir. **Kullanıcı onayı olmadan videoyu değiştirmez.**

## Ne zaman

- Rubrik temizlendikten sonra, kullanıcıya önizleme gösterilmeden önce.
- Teslimden önce son render üzerinde.
- Düzeltme sonrası, yalnız değişen aralık için.

## 1. Ölç

```
.venv/Scripts/vedit slop renders/onizleme.mp4 --olaylar edit/olaylar.json --dil tr
```

Çıktı: `qa/slop-olcum.json` ve `qa/slop-kareler.jpg` (klişe testi kareleri + şüpheli anlar). Metin taraması konuşmayı yazıya döker; hazır metin için `--metin script/senaryo.md`, atlamak için `--yazisiz`.

Ölçüm **şüphedir, hüküm değildir**. Her bulgu kare ya da bağlamla doğrulanır, doğrulanmazsa rapora "elendi" diye yazılır.

| Kod | Ne ölçer |
|---|---|
| `RITIM_METRONOM`, `RITIM_ESIT_BLOK` | Plan süreleri fazla eşit |
| `STATIK_UZUN`, `ACILIS_YAVAS` | Kıpırdamayan görüntü, ölü açılış |
| `KEN_BURNS_HER_YERDE` | Planların çoğunda düzenli yavaş süzülme |
| `PALET_MOR`, `PALET_KOYU_SABLON` | Varsayılan AI paleti |
| `SES_NEFES_YOK`, `SES_DUZ_DINAMIK` | Hiç düşmeyen ses, düz miks |
| `OLAY_TEKDUZE`, `OLAY_TEK_TUR`, `OLAY_YOGUN` | Eşit aralıklı zoom, tek tip geçiş, olay yağmuru |
| `METIN_KLISE`, `METIN_KARSITLIK` | AI metin kalıpları |

Ölçüm yumuşak geçişi kesim saymaz, üretken görüntü kusurunu göremez, müziğin karakterini duyamaz. Bunlar 2. adımın işidir.

Ses için ek ölçüm (`sound-design` skill'i, earshot bölümü): `measure` ve `timeline --cues`. Sonucu raporda "Ses" alt başlığıyla, rakamla ver; earshot yoksa "ölçülmedi" yaz.

## 2. Gözle denetle

`qa/slop-kareler.jpg` dosyasını oku, `script/senaryo.md` ve varsa `edit/stil-karti.md` ile karşılaştır. Her şüpheli aralıkta `vedit sheet <video> --start S --dur D --grid 4x2` ile yakından bak. `slop-katalogu.md` listesini tara:

- **A. Üretken kusur:** bozuk el, kayan yüz, anlamsız yazı, plastik cilt, eriyen nesne
- **B. Bağlam kopukluğu:** görüntü söyleneni göstermiyor, jenerik metafor
- **C. Şablon düzen:** ortalı başlık, eş kart ızgarası, süs etiket
- **D. Hareket:** aynı giriş, aynı eğri, sebepsiz hareket
- **E. Tutarlılık:** karakter, ışık, stil ya da font planlar arasında kayıyor
- **F. Ses ve yapı:** her kesimde efekt, jenerik müzik, kanca-sorun-3 kart-CTA kalıbı

Üç göz testi:
1. **Logo testi:** Logo kapalıyken bu video rakibin olabilir mi?
2. **Rastgele kare testi:** Üç rastgele kare herhangi bir AI videosundan ayırt ediliyor mu?
3. **Sessiz izleme testi:** Ses kapalıyken ilk 3 saniyede ne olduğu anlaşılıyor mu?

Mümkünse denetimi, planı bilmeyen taze bir denetçi yapar: yalnız bu skill, kareler, ölçüm ve senaryo verilir.

## 3. Sayılmayanlar

Şunlar bulgu değildir, listeye yazma:
- **Altyazı standardı** (ADR 0014): turuncu okunan kelime, Montserrat, kelime kelime vurgu kullanıcı kararıdır.
- `library/kit.json` içindeki `locked` varlıklar ve `always` rolleri. Varlığın kendisi sayılmaz, yoğunluğu sayılabilir.
- `edit/stil-karti.md` içinde gerekçesi yazılı bilinçli seçimler.
- Kullanıcının açıkça istediği şey, `library/checks.md` içindeki kararlar.
- Formatın doğası: Reels'te hızlı kesim tek başına slop değildir; eşit süreli kesim olabilir.

## 4. Raporla

`qa/slop-raporu.md` yaz:

```
# AI slop raporu
Video: renders/onizleme.mp4 · Tur 1
Hüküm: DÜZELTİLMELİ · P0 1 · P1 2 · P2 1
Göz testleri: Logo kaldı · Rastgele kare kaldı · Sessiz geçti

## Bulgular
P0 00:14.2–00:17.0 · A · Kanıt: konuşmacının sol eli 6 parmak
   Neden: üretim izi, izleyici anında fark eder
   Öneri: planı yeniden üret ya da 00:14.2–00:17.0 aralığını ekran kaydına çevir
   Bedel: yeni Flow klibi

P1 00:22.0–00:48.0 · RITIM_ESIT_BLOK · Kanıt: art arda 7 plan 3.2–3.6 sn
   Neden: slayt gösterisi hissi, süre bilgiye göre değil
   Öneri: edit/edl.json s7 ile s8'i birleştir (6.8 sn), s10'u 1.5 sn'ye indir
   Bedel: küçük, yeniden render

## Elenen şüpheler
SES_DUZ_DINAMIK: konuşma odaklı kısa video, müzik yok; bilinçli.

## Doğrulanamayanlar
Müziğin karakteri dinlenmedi; kulak testi kullanıcıda.
```

Kurallar:
- Her bulguda **zaman, kanıt, neden, öneri, bedel** olur. Zaman damgası olmayan bulgu yazılmaz (palet gibi tüm videoya yayılanlar "tümü" der ve örnek zaman verir).
- Öneri teknik ve tek anlamlıdır: dosya, alan, eski değer → yeni değer ya da somut işlem. "Daha dinamik yap" yasak.
- Önce en az değişiklikle en çok farkı yaratan öneriyi yaz. Bulgu 10'u aşarsa en kötü 10'u yaz, gerisini sayı olarak belirt.
- Görmediğin kare ve duymadığın ses hakkında yazma; "doğrulanamadı" de.

### Şiddet ve hüküm

| Şiddet | Anlam |
|---|---|
| P0 | İzleyicinin ilk bakışta AI anlayacağı kusur ya da uydurma içerik. Yayınlanmaz. |
| P1 | Video boyunca şablon hissi veren kalıp. Düzeltilmeli. |
| P2 | Tek başına küçük; birikirse hissedilir. |

Hüküm: **TEMİZ** (P0 ve P1 yok, göz testleri geçti) · **DÜZELTİLMELİ** (P1 var ya da göz testi kaldı) · **YAYINLANAMAZ** (P0 var).

## 5. Öner, onay al, uygula

Kullanıcıya hükmü ve kısa listeyi göster, hangilerinin uygulanacağını sor. Dosyayı işaret et: `qa/slop-raporu.md`.

- Onaylananları `usta-editor` ile uygula, `olaylar.json` değiştiyse `vedit olaysesi`'ni yeniden çalıştır, sonra değişen aralığı tekrar denetle.
- En çok 2 tur. Sonra kalanlar kullanıcıya bırakılır.
- Kullanıcı bir bulguyu reddederse bu bir karardır: sebebini `library/checks.md`'ye yaz, bir daha bulgu sayma.
- Yeni bir slop kalıbı görüldüyse `slop-katalogu.md`'ye değil önce `library/checks.md`'ye ekle; iki projede tekrarlarsa kataloğa taşı.
