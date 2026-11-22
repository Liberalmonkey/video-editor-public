---
name: gorsel-uret
description: Kapak (YouTube thumbnail, Instagram/Reels kapağı), sunum ya da açıklama grafiği, videoda kullanılacak durağan görsel ve loop-flow başlangıç karesi üretir. Önce eldeki malzeme, sonra ücretsiz Google araçları (Antigravity CLI görseli, Google Flow / Nano Banana, Gemini uygulaması); yazı her zaman kodla eklenir. "kapak yap", "thumbnail", "görsel üret", "resim oluştur", "sunum görseli", "B-roll görseli" dendiğinde kullan.
---

# Görsel üretimi

Genel araç bilgisi ikinci beyindedir: `<AI klasörü>/ikinci-beyin/.agents/skills/google-araclari/SKILL.md` (hangi araç, ücretsiz sınır, Flow'u Chrome ile sürme, prompt kuralları). Bu skill o bilginin bu projedeki uygulamasıdır. Karar: `wiki/decisions/0025-gorsel-uretimi-google.md`.

## Ne zaman kullanılır
- YouTube kapağı (16:9, 1280×720) ve Instagram/Reels kapağı (9:16, 1080×1920).
- Sunum ya da açıklama grafiğinin zemini veya illüstrasyonu.
- Videoda gerçek çekimin ya da kodla çizilmiş grafiğin olmadığı yerde durağan B-roll görseli.
- `loop-flow` için başlangıç karesi (klibi Flow üretir, görseli bu skill hazırlar).

## Motor sırası
Bir adım işi görüyorsa sonrakine geçme.
1. **Eldeki malzeme.** `vedit` teslimde kapak kareleri çıkarır (`renders/covers/cover*.jpg`, `src/vedit/export.py` `covers`). Avatar ya da konuşmacı karesi, `library/` varlıkları, `library/boards/katalog.md` panoları, HyperFrames sahnesi.
2. **Antigravity CLI.** `.venv/Scripts/vedit gorsel "<prompt>" -o work/gorsel/<ad> --oran 16:9` (9:16, 1:1, 4:5 de olur). agy'yi çağırır, görseli agy'nin klasöründen alıp hedefe kopyalar, `work/gorsel/log.md`'ye satır yazar. Ücretsiz, kota dar (5 saatte birkaç görsel); kota hatasında Flow'a geç. Ölçüldü (2026-11-08, agy 1.5.3): 77-98 sn, 16:9 çıktı 1376×768, 9:16 çıktı 768×1376 JPEG. Elle çağrı gerekirse: agy headless modda dosya taşıyamaz, görsel agy'nin `brain/<conversation_id>` klasörüne iner.
3. **Google Flow (Nano Banana 2).** Kullanıcının Chrome oturumunda, `google-araclari` skill'indeki adımlarla. Çok aday, referans görsel ve karakter tutarlılığı gerektiğinde ilk tercih budur.
4. **Gemini uygulaması.** Yalnız yedek.

Ücretli Gemini API (`gemini-api-cli`, Nano Banana API, Imagen) bütçe 0 USD kuralı nedeniyle kullanılmaz; kullanıcı açıkça isterse ADR'yi güncelle.

## Denge kuralları
- Kapak: varsayılan 1 aday, kullanıcı isterse en çok 5 (`vedit kapak --adet`). Beğenilmezse prompt'u düzelt, toptan yeniden üretme.
- B-roll görseli: yalnız gerçek ya da kodla üretilmiş görselin olmadığı yerde, dakikada en çok bir tane. Aynı videoda üretilmiş görseller tek stil paragrafını paylaşır.
- Sunum grafiğinde veri, sayı, şema ve metin kodla çizilir (`vedit pano`, HTML/SVG). Üretilen görsel yalnız zemin ya da illüstrasyondur.
- Görsele yazı gömülmez; Türkçe harfler modelde bozulur. Yazı kapak şablonunda Montserrat 800 ile eklenir.
- Gerçek kişinin yüzünü, marka logosunu ya da telifli karakteri taklit eden görsel üretilmez. Kullanıcının kendi yüzü ya da Flow avatarı gerçek kareden alınır.
- Her üretim `work/gorsel/log.md` dosyasına tek satır yazılır: tarih, motor, oran, prompt'un ilk 80 karakteri, sonuç. `vedit gorsel` bunu kendisi yazar; Flow ve Gemini uygulaması üretimleri elle eklenir, seçim kararı (seçildi, atıldı, neden) sonradan satıra işlenir.

## Kapak akışı
YouTube ve Instagram kapağı artık `vedit kapak` ile üretilir (Video Stüdyo'da Kapak sekmesi); içerik kuralları `kapak-youtube` ve `kapak-instagram` skill'lerinde, karar `wiki/decisions/0027-kapak-sayfasi.md`. Varsayılan 1 aday, kullanıcı isterse en çok 5. İş akışı v2 (ADR 0052): video ve an seçimi, fikri geliştirme (`--gelistir`), agy modeli seçimi, bölgesel görsel düzeltme (`--gorsel-duzelt`). agy kotası kapalıysa ya da başka model istenirse `vedit kapak <ref> --master` Nano Banana Pro/2.1, ChatGPT, Midjourney, Ideogram ve Leonardo için yazılı ve boş zemin prompt'u verir; dış görsel `--ice-al` ile aday olur, boş zeminde yazı kodla eklenir. Aşağıdaki elle akış yalnız komutun karşılamadığı özel kapakta kullanılır.

1. Metin önce gelir: YouTube'da `/yt-package` başlık + kapak metni (en çok 3 kelime, başlığı tekrar etmez), Reels'te `viral-kurgu` madde 9. Seri şablonu: yüz ya da avatar, iki satır başlık.
2. Zemin: önce gerçek kare ya da `cover*.jpg`; işe yaramazsa motor sırasıyla üretilir. Prompt yüz ve yazı için boş alan ister ("empty space on the left third for text"), tek ana nesne, yüksek kontrast, sade arka plan.
3. Yüz ya da avatar kesiti şeffaf PNG olarak hazırlanır (gerçek kareden).
4. `library/kapak/sablon.html` dosyasını `work/gorsel/kapak.html` olarak kopyala, yanına `zemin.png` ve `yuz.png` koy, iki satırı yaz; vurgulanacak kelime `<em>` içinde (varsayılan turuncu `#FF7A00`; kalıp ve stil paketi için `kapak-youtube` ve `kapak-instagram`).
5. Render: `.venv/Scripts/vedit pano work/gorsel/kapak.html -o work/gorsel/kapak-1.jpg --sure 0 --w 1280 --h 720` (Reels: `--w 1080 --h 1920`). `-o` .png ya da .jpg olunca `vedit pano` tek kare çeker.
6. Adayları kullanıcıya göster. Seçilen `Projeler/outputs/<stüdyo>/<proje>/kapak.jpg` olur ve `yayin.md` kapak bölümüne yazılır.

## Videoda kullanılan görsel
- Dosya `work/gorsel/` altında üretilir, kurguya kütüphane varlığı gibi girer. Hareket gerekiyorsa `kurgu.json` dönüşüm keyframe'iyle yavaş itme verilir ya da `loop-flow` ile canlandırılır.
- Yeniden kullanılabilir çıkan görsel `library/` altına taşınır ve kilitlenmesi önerilir; kullanıcı onaylamadan kilitlenmez.
- `denetim` skill'i üretilmiş görseli AI slop açısından da değerlendirir: yapay parlaklık, bozuk el, anlamsız yazı, şablon kompozisyon.
