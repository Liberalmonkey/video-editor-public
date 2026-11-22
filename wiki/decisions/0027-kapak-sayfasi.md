---
type: decision
title: "Kapak sayfası: YouTube ve Instagram için Antigravity ile 1-5 aday, iki platform skill'i"
status: accepted
tags: [adr, kapak, thumbnail, youtube, instagram, antigravity, studio]
created: 2026-11-09
updated: 2026-11-15
sources: ["[[2026-11-09-kapak-arastirmasi]]", "[[2026-11-15-kapak-kalip-analizi]]"]
---

# ADR: Kapak sayfası

## Bağlam
Kullanıcı projeye bir kapak (thumbnail) sayfası istedi (2026-11-09): her video için kapak, istenirse 2, 3, 4 ya da 5 aday; üretim Antigravity ile; yalnız YouTube ve Instagram. Her iki platform için ayrı skill, en çok izlenen kanalların (MrBeast, Nick Saraev, Iman Gadzhi vb.) araştırmasına dayanacak. [[0025-gorsel-uretimi-google]] kapak adayını 3 ile sınırlıyordu ve kapağı elle akışla (`vedit gorsel` + şablon + `vedit pano`) kuruyordu.

## Seçenekler
- Yalnız terminal komutu ve kontak sayfası.
- Ayrı bağımsız sayfa.
- Video Stüdyo içinde yeni çalışma alanı. Kullanıcı bunu seçti.

## Karar
| Konu | Karar | Neden |
|---|---|---|
| Sayfa | Video Stüdyo'da **Kapak** çalışma alanı (Alt+4): kapak paneli, program, işler. [[0030-sade-arayuz]] ile Teslim alanına gizli sekme olarak taşınmıştı; bulunamadığı için 2026-11-15'te yeniden kendi alanı oldu | Kullanıcı seçimi; iş kuyruğu, dosya sunumu ve proje seçimi zaten var |
| Komut | `vedit kapak <ref> --platform --adet --metin --prompt --zemin --yeni-brief --sec` | Terminal hattı sürer ([[0020-panel-kaldirildi]]); sayfa aynı komutu iş kuyruğunda çalıştırır |
| Aday sayısı | Varsayılan 1, en çok 5; yeni adaylar eskilerin üzerine yazmaz | Kullanıcı isteği; 0025'teki 3 sınırı kapak için kalktı |
| Motor | Brief metni ve zemin görseli agy ile (`gorsel.agy`, `gorsel.uret`); `--zemin` ile eldeki kare | Bütçe 0 USD; kota dar olduğundan eldeki kare yolu açık |
| Yazı | `library/kapak/sablon.html` + `pano.render` tek kare; vurgu turuncu `#FF7A00` | Modeller Türkçe harfi bozar; altyazı standardı (ADR 0014) |
| Platform | YouTube 1280×720; Instagram Reels 1080×1920, ızgarada orta 1080×1440 güvenli alan | Instagram ızgarası Reels'i 3:4 kırpar ([[2026-11-09-kapak-arastirmasi]]) |
| Bilgi | İki skill: `kapak-youtube`, `kapak-instagram`; brief isteği ilgili SKILL.md'yi agy'ye verir | Kurallar tek yerde; agy ve Claude aynı kuralı okur |
| Seçim | Kullanıcı seçer; `--sec` adayı `kapak.jpg` (YouTube) ya da `kapak-reels.jpg` (Instagram) olarak teslim klasörüne kopyalar, varsa `-v2` | Teslim dosyasının üzerine yazılmaz |

## Sonuçlar
- Adaylar `work/gorsel/kapak/<platform>/`: `brief.json`, `zemin-N`, `kapak-N.html`, `kapak-N.jpg`, `kapak-N.json` (o adayın brief'i), `secim.json`. Her üretim ve seçim `work/gorsel/log.md`'ye yazılır.
- agy kotası dolarsa üretilen adaylar kalır, kalan sayı bildirilir.
- Stüdyo API: `GET /api/kapak/{s}/{a}?platform=`, `POST /api/kapak/{s}/{a}/sec`; üretim iş kuyruğu beyaz listesinde `kapak` (platform, adet 1-5, tek satır metin ≤120, prompt ≤800).
- Doğrulandı 2026-11-09: agy 1.5.3 ile tek Instagram adayı 48 sn (brief hazırken).
- YouTube Test & Compare en çok 3 kapak alır; daha fazla aday seçim içindir.

> [!note] Güncellendi 2026-11-12
> Kapak videodaki kareye dayanır. `kapak.kareler` teslim videosundan (yoksa `ham.mp4`, yoksa girdi videoları) 6 kare çıkarır (`work/gorsel/kapak/kareler/`); brief her aday için bir kare seçer ya da kullanıcı `--kare N` verir. Kare ve girdideki `karakter*` görseli agy `generate_image`'a referans gider (`gorsel.uret(refler=)`): özne korunur, zemin ve ışık brief'e göre yeniden kurulur. agy üretemezse kare doğrudan zemin olur ve aday yine çıkar. `kapak-N.json` `kare` ve `zemin_kaynagi` alanlarını taşır. Neden: metinden üretilen zeminler videoyla ilgisiz çıkıyordu (kullanıcı bildirimi).

> [!note] Güncellendi 2026-11-14
> Yazı üretimden sonra düzenlenir. Zemin bir kez üretilir; `vedit kapak <ref> --duzenle N` adayı agy çağırmadan yeniden çizer (`kapak.duzenle`), `--kopya` aynı zeminle yeni aday açar (yerleşim varyasyonu, kota harcamaz). `kapak-N.json` artık `zemin` yolunu ve yazı stilini taşır; eski adayda zemin `kapak-N.html`'den bulunur. Dış `--zemin` dosyası `zemin-N` olarak aday klasörüne kopyalanır. Neden: tek kelime değiştirmek yeni aday ve yeni kota demekti; Stüdyo adayın yazısını gösteremiyordu.
>
> | Konu | Karar | Neden |
> |---|---|---|
> | Yerleşim | YouTube `sol` (varsayılan), `sag`, `ust`, `alt`; Instagram `ust` (varsayılan), `alt`. `--olcek` 0.6-1.4, `--karart` yönlü gradyan, `--kutu` vurgu turuncu kutuda beyaz | 138 referans kapakta (114 YouTube, 24 Instagram; Antigravity analizi) YouTube'da sol blok 31, üst 26, alt 22, sağ 19; Instagram'da 22/24 başlık altta, ikinci satır renkli kutuda. Yalnız kalıp alındı, tasarım ve yazı kopyalanmadı |
> | Güvenli alan | `kapak.GUVENLI` tek kaynak: YouTube kenar payı `4,5,96,95` ve süre rozeti `80,82,100,100` (yazı girmez); Instagram ızgara 3:4 `0,12.5,100,87.5`, akış 4:5 `0,14.8,100,85.2` | Stüdyo aynı veriyi çizer; `tests/test_kapak.py` şablonu gerçek tarayıcıda bu alanlara karşı ölçer |
> | Önizleme | `POST /api/kapak/{s}/{a}/onizle` şablonu doldurup döner; panel onu gerçek ölçüde bir `iframe srcDoc` içinde küçültür | Render'la aynı şablon ve aynı motor; CSS iki yerde tutulmaz |
> | Kalıcı çizim | Panel "Yazıyı uygula" ve "Varyasyon olarak kaydet" iş kuyruğunda `vedit kapak --duzenle` çalıştırır | Sayfa terminalle aynı komutu kullanır (bu ADR'ın komut satırı) |
> | Teslim | Aday teslimden sonra düzenlenirse `durum.secim.eski` olur, panel "Yeniden teslim et" gösterir; YouTube dosyası 2 MB'ı aşarsa `sec` uyarır | Teslim dosyasının üzerine yazılmaz, yeni sürüm `-v2` olur |
>
> Süre rozetinin ölçüsü YouTube'un yayımladığı bir sabit değildir (metne göre değişir); `80,82` payı ölçülen rozetten geniş tutuldu. Kapsam dışı: Shorts kapağı, 4K çıktı (agy zemini 1376×768), sürükleyerek konumlama, serbest yazı tipi ve renk ([[0014-altyazi-standardi-ve-repo-entegrasyonu]] korunur).

> [!note] Güncellendi 2026-11-15
> Kullanıcı kapakların yeterince iyi olmadığını bildirdi ve 138 referans kapağın incelenmesini istedi. Şablon tek kalıptı (zemin + iki satır); referanslardaki düzenlerin çoğu yoktu ([[2026-11-15-kapak-kalip-analizi]]).
>
> | Konu | Karar | Neden |
> |---|---|---|
> | Kalıp | `kapak.KALIP` tek kaynak: YouTube `klasik`, `dev-yazi`, `alt-bant`, `bolunmus`, `rozet`, `not`, `yazisiz`; Instagram `klasik`, `seri`, `yazisiz`. `--kalip`, kayıt alanı `kalip`; eski kayıt `klasik` açılır | Referanslarda klasik yalnız %25; rozet, bölünmüş ve alt bant en çok izlenen kalıplar arasında |
> | Ek söz | Tek yeni yazı alanı `ek`; işi kalıba göre değişir (arkadaki dev söz, üst satır, el yazısı not, marka sözü) | Her kalıba ayrı alan açmak kaydı ve arayüzü şişirirdi |
> | Yazı stili | `library/kapak/stiller/<ad>.json` CSS değişkeni paketi; `--stil`, stüdyo varsayılanı `studios/<stüdyo>/kapak.json`. Kapak yazısı [[0014-altyazi-standardi-ve-repo-entegrasyonu\|ADR 0014]] standardına bağlı değildir; varsayılan paket `turuncu` aynı görünümü verir | Kullanıcı kararı: referansların çoğu kırmızı kutu, beyaz kontur ya da sarı vurgu kullanıyor. Önceki "serbest renk kapsam dışı" maddesi kalktı |
> | Özne kesiti | `kapak.kesit` zeminin kendisinden özne keser (`rembg`, model `u2net`), kesit zeminle aynı ölçüde üst katmandır; `dev-yazi` ve `seri` kalıbında ek söz araya girer | Hizalama sorunu ve ikinci özne olmaz; agy kotası harcamaz. `rembg` varsayılan modeli (bria-rmbg) ticari kullanıma kapalı olduğu için model sabitlendi |
> | Kare | `kapak.kareler` önce girdi videolarını kullanır, yüz varsa en büyük ve net yüzlü anları seçer (YuNet) | Teslim videosundan alınan karede gömülü altyazı ve grafik kapağa giriyordu |
> | Ölçüm | Her çizimde `kapak.olc`: kelime sayısı, harf yüksekliği (YouTube en az %8), güvenli alan, kontursuz yazıda kontrast; sonuç `kapak-N.json` `olcum` | Küçük boyut testi skill'de yazılıydı ama elle yapılıyordu |
> | Eleştiri | `--elestir`: agy adayları 1-10 puanlar, tek düzeltme yazar (`puan`, `elestiri`). Seçim kullanıcıda kalır | İkinci göz; kota harcadığı için isteğe bağlı |
>
> Kalıp listesi referans analizinden daraltıldı: sık görülen `ekran-vitrin` (özne + ekran kartı) ve çoklu simge kalıpları alınmadı; ikinci görsel ister ve referanslarda en düşük izlenme ortalamasını verdi. `rembg` isteğe bağlı bağımlılıktır (`pip install -e ".[kapak]"`, ilk çalıştırmada 176 MB model); yoksa kesit isteyen kalıp `klasik`e düşer ve bunu yazar. El yazısı notu sistem yazı tipini kullanır (Windows: Segoe Print).

> [!note] Güncellendi 2026-11-22
> Devamı [[0052-kapak-is-akisi-v2]]: video ve an seçimi, fikir geliştirme, agy modeli seçimi, bölgesel görsel düzeltme, dış platform master prompt'u ve dış görsel içe alma.

## İlgili kod
- `src/vedit/kapak.py`, `src/vedit/gorsel.py` (`agy`), `src/vedit/cli.py` (`cmd_kapak`), `library/kapak/sablon.html`, `library/kapak/stiller/`
- `src/vedit/studio/isler.py` (`kapak_arguman`), `src/vedit/studio/app.py`
- `studio/web/src/paneller/KapakPaneli.tsx`, `studio/web/src/main.tsx`, `studio/web/src/zaman/kisayol.ts`
- Testler: `tests/test_kapak.py`, `tests/test_studio_dosya.py`, `tests/test_studio_kurgu_api.py`
