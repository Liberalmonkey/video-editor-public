---
type: decision
title: "Kapak iş akışı v2: video seç, fikri geliştir, üret, bölgesel düzelt, master prompt ve dış görsel"
status: superseded
tags: [adr, kapak, thumbnail, youtube, instagram, antigravity, nano-banana, studio]
created: 2026-11-22
updated: 2026-11-24
sources: ["[[2026-11-22-kapak-arastirmasi-v2]]", "[[0027-kapak-sayfasi]]"]
---

# ADR: Kapak iş akışı v2

> [!note] Güncellendi 2026-11-24: kapak özelliği kaldırıldı, bu karar `superseded`. Bkz. [[0056-kapak-kaldirildi]].

## Bağlam
Kullanıcı Kapak sayfasının profesyonel bir YouTube ve Instagram kapak aracına dönüşmesini istedi (2026-11-22). İstekleri şunlardı:
- Önce kapağın videosu seçilsin.
- Kapak o videodan üretilsin.
- Beğenilmeyen kısım düzeltilebilsin.
- Kullanıcı kendi fikrini yazabilsin ve sistem onu prompt'a geliştirsin.
- Antigravity'de hangi modelin kullanılacağı seçilebilsin.
- Başka platformda üretmek için referanslı bir master thumbnail prompt'u verilsin: Nano Banana Pro, Nano Banana 2.1, ChatGPT, Midjourney, Ideogram ve Leonardo için. Her biri yazılı ve boş zemin sürümüyle.

[[0027-kapak-sayfasi]]'nda şu eksikler vardı:
- Kareler projedeki bütün videolardan karışık geliyordu.
- `gorsel.agy` model geçmiyordu.
- Görsel beğenilmezse tek yol yeniden üretmekti.
- Dış platform yolu yoktu.

## Seçenekler
- **Görsel modelini seçmek.** agy'nin `generate_image` aracı görsel modelini kendisi seçer (loglarda `gemini-3.1-flash-image`); CLI'da bayrağı yok. Topluluk betikleri Antigravity OAuth jetonunu başka araçla kullanıyor. Bu ToS riski taşıdığı için reddedildi. Ücretli Gemini API de bütçe kuralı (0 USD) nedeniyle reddedildi.
- **Hazır repo kurmak.** Adaylar: jordicor/youtube_thumbnail_generator_with_AIs, ohvignas/ThumbGen, ThumbAI, thumbforge. Hepsi ücretli API ister ya da ağır bağımlılık getirir (Redis, ticari kullanıma kapalı InsightFace modelleri). Reddedildi; yalnız fikirleri alındı.
- **Mevcut hattı genişletmek.** Seçilen yol.

## Karar
| Konu | Karar | Neden |
|---|---|---|
| Akış | Stüdyo Kapak alanı 5 adımlı şerit olur: Video, Fikir ve prompt, Üret, Düzelt, Master prompt ve teslim. Açılışta sıradaki adım açılır | Kullanıcının istediği sıra; adım atlanabilir |
| Video | `kapak.videolar` girdi videolarını, `ham.mp4`'ü ve teslim videolarını listeler. `--video "inputs:1.mp4"` verilince kareler yalnız o videodan gelir (`kareler/<video>/`). `kare_ekle` oynatıcıda durdurulan anı `el-<ms>.jpg` olarak ekler | Kare karışıklığı biter; tam an seçilir |
| Referans | `work/gorsel/kapak/referans/yuz-*` ve `stil-*` dosyaları ile girdideki `karakter*` görselleri. agy'ye sırası: kare, en çok 3 yüz, en çok 1 stil. Numaralı tarif `kapak_prompt.ref_metni` ile gider | Stil referansı yalnız düzen ve renk verir; içerik kopyalanmaz |
| Fikir | `kapak.gelistir`: Türkçe fikir + video metni + kare + skill kuralları agy'ye gider, yapılı brief ve `not_tr` döner, `oneri.json`'a yazılır. Fikir boşsa öneri videodan yazılır. Kartlar Stüdyo'da düzenlenir (`POST /oneri`). `--oneri` ile üretilir | Kullanıcının fikri korunur, kapak kurallarına göre güçlendirilir |
| Brief | Yapılı alanlar `sahne, ifade, kompozisyon, isik, palet, yazi_alani`. `prompt` elle yazılmışsa öncelikli. Eski yalnız-prompt brief aynen çalışır | Master prompt her platforma bu alanlardan yazılır |
| Model | `--model`: brief, geliştirme ve eleştiriyi yazan agy modeli. `--gorsel-model`: `generate_image`'ı çağıran model. İkisi de AI panelinin listesinden (`/api/ajan/durum`) gelir ve iş kuyruğunda doğrulanır. Görsel modelinin adı ve kota açılışı loglardan okunur (`gorsel.kota`), rozet "agy sabit" der | Kullanıcı model seçer; seçilemeyen şey dürüstçe gösterilir |
| agy çağrısı | `--print-timeout 600s`, `--effort` seçeneği, kota hatası açılış saatiyle Türkçe tek satır. Görsel arama `brain/<id>/` altında özyinelemeli | agy 1.5.x görseli image-generator alt ajanına verir |
| Görsel düzeltme | `kapak.gorsel_duzelt`: istek ve isteğe bağlı kutu (tuval yüzdesi) alır. Kutu varsa zemine kırmızı kutu çizilir ve prompt "yalnız kutunun içini değiştir, kutuyu sil" der. Varsayılan olarak sonuçtan yalnız kutu bölgesi yumuşak kenarla orijinale geri yapıştırılır, kutu dışı piksel değişmez. Sonuç yeni aday olur (`ebeveyn`, `duzeltme`), yazı alanları korunur | Nano Banana'nın maske girişi yok; "düzenle, baştan üretme" kuralı |
| Dış görsel | `kapak.ice_al`: jpg, png ya da webp, en çok 15 MB. Platform oranına ortadan kırpılır ve ölçeklenir. Yazısız görsel zemin olur ve yazı öneriden ya da brief'ten kodla eklenir. Yazılı görsel `yazisiz` kalıplı bitmiş aday olur; yüz katmanı çizilmez | Başka platformda yapılan kapak aynı teslim ve ölçüm hattına girer |
| Master prompt | `kapak_prompt.master` saf fonksiyondur (agy'siz). Hedefler: Nano Banana Pro, Nano Banana 2.1, ChatGPT, Midjourney, Ideogram, Leonardo. Her hedefin yazılı (tırnak içinde tam metin, yazı tipi, renk, Türkçe harf uyarısı) ve boş zemin sürümü var. Ayarlar (oran, çözünürlük, `--ar`, `--oref/--sref`) ve sıralı referans listesi eklenir. `sec` teslimde `<kapak>-master-prompt.md` dosyasını da outputs'a yazar | Kullanıcı isteği; kota kapalıyken de kapak üretilebilir |

## Sonuçlar
- Yeni dosyalar `work/gorsel/kapak/` altında: `kareler/<video>/`, `referans/`, `<platform>/oneri.json`, `<platform>/disari/` ve `duzelt-N-isaret.png`.
- CLI: `vedit kapak <ref>` şu bayrakları kazandı: `--video`, `--model`, `--gorsel-model`, `--gelistir [FIKIR]`, `--oneri`, `--gorsel-duzelt N --istek "..." [--bolge s,u,sa,a] [--tum-gorsel]`, `--ice-al DOSYA [--yazili]`, `--master [N] [--hedef ad]`.
- API, agy'siz ve eşzamanlı uçlar: `POST /api/kapak/{s}/{a}/kare`, `PUT|DELETE .../referans`, `PUT .../ice-al`, `POST .../oneri`, `GET .../master`. `GET /api/kapak/{s}/{a}?video=`.
- Arayüz `studio/web/src/paneller/kapak/` altında parçalara ayrıldı. `Adim` düz fonksiyondur: render içinde tanımlı bir bileşen alt durumu sıfırlardı.
- Kapsam dışı: görsel modelini seçmek (agy'de yok), ücretli API, yeni repo, Shorts kapağı, sürükleyerek yazı konumlama.

## İlgili kod
- `src/vedit/kapak_prompt.py`, `src/vedit/kapak.py`, `src/vedit/gorsel.py` (`agy`, `kota`), `src/vedit/cli.py` (`cmd_kapak`)
- `src/vedit/studio/isler.py` (`kapak_arguman`, `_agy_model`), `src/vedit/studio/app.py`
- `studio/web/src/paneller/kapak/` (`KapakPaneli`, `VideoAdimi`, `FikirAdimi`, `UretAdimi`, `YaziDuzenle`, `GorselDuzelt`, `MasterPrompt`, `AdayIzgarasi`, `yardimci`)
- Testler: `tests/test_kapak_prompt.py`, `tests/test_kapak_v2.py`, `tests/test_kapak.py`, `tests/test_studio_dosya.py`, `tests/test_studio_kurgu_api.py`, `studio/web/src/paneller/kapak/yardimci.test.ts`
