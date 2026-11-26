---
name: gorsel-uret
description: Sunum ya da açıklama grafiği, videoda kullanılacak durağan görsel ve loop-flow başlangıç karesi üretir. Önce eldeki malzeme, sonra ücretsiz Google araçları (Antigravity CLI görseli, Google Flow / Nano Banana, Gemini uygulaması); yazı her zaman kodla eklenir. "görsel üret", "resim oluştur", "sunum görseli", "B-roll görseli" dendiğinde kullan.
---

# Görsel üretimi

Genel araç bilgisi ikinci beyindedir: `<AI klasörü>/ikinci-beyin/.agents/skills/google-araclari/SKILL.md` (hangi araç, ücretsiz sınır, Flow'u Chrome ile sürme, prompt kuralları). Bu skill o bilginin bu projedeki uygulamasıdır. Karar: `wiki/decisions/0025-gorsel-uretimi-google.md`.

## Ne zaman kullanılır
- Sunum ya da açıklama grafiğinin zemini veya illüstrasyonu.
- Videoda gerçek çekimin ya da kodla çizilmiş grafiğin olmadığı yerde durağan B-roll görseli.
- `loop-flow` için başlangıç karesi (klibi Flow üretir, görseli bu skill hazırlar).

## Motor sırası
Bir adım işi görüyorsa sonrakine geçme.
1. **Eldeki malzeme.** Videodan kare (`vedit still`), avatar ya da konuşmacı karesi, `library/` varlıkları, `library/boards/katalog.md` panoları, HyperFrames sahnesi.
2. **Antigravity CLI.** `.venv/Scripts/vedit gorsel "<prompt>" -o work/gorsel/<ad> --oran 16:9` (9:16, 1:1, 4:5 de olur). agy'yi çağırır, görseli agy'nin klasöründen alıp hedefe kopyalar, `work/gorsel/log.md`'ye satır yazar. Ücretsiz, kota dar (5 saatte birkaç görsel); kota hatasında Flow'a geç. Ölçüldü (2026-11-08, agy 1.5.3): 77-98 sn, 16:9 çıktı 1376×768, 9:16 çıktı 768×1376 JPEG. Elle çağrı gerekirse: agy headless modda dosya taşıyamaz, görsel agy'nin `brain/<conversation_id>` klasörüne iner.
3. **Google Flow (Nano Banana 2).** Kullanıcının Chrome oturumunda, `google-araclari` skill'indeki adımlarla. Çok aday, referans görsel ve karakter tutarlılığı gerektiğinde ilk tercih budur.
4. **Gemini uygulaması.** Yalnız yedek.

Ücretli Gemini API (`gemini-api-cli`, Nano Banana API, Imagen) bütçe 0 USD kuralı nedeniyle kullanılmaz; kullanıcı açıkça isterse ADR'yi güncelle.

## Denge kuralları
- Varsayılan 1 aday. Beğenilmezse prompt'u düzelt, toptan yeniden üretme.
- B-roll görseli: yalnız gerçek ya da kodla üretilmiş görselin olmadığı yerde, dakikada en çok bir tane. Aynı videoda üretilmiş görseller tek stil paragrafını paylaşır.
- Sunum grafiğinde veri, sayı, şema ve metin kodla çizilir (`vedit pano`, HTML/SVG). Üretilen görsel yalnız zemin ya da illüstrasyondur.
- Görsele yazı gömülmez; Türkçe harfler modelde bozulur. Yazı görsel şablonunda (`library/gorsel/sablon.html`) kodla eklenir.
- Gerçek kişinin yüzünü, marka logosunu ya da telifli karakteri taklit eden görsel üretilmez. Kullanıcının kendi yüzü ya da Flow avatarı gerçek kareden alınır.
- Her üretim `work/gorsel/log.md` dosyasına tek satır yazılır: tarih, motor, oran, prompt'un ilk 80 karakteri, sonuç. `vedit gorsel` bunu kendisi yazar; Flow ve Gemini uygulaması üretimleri elle eklenir, seçim kararı (seçildi, atıldı, neden) sonradan satıra işlenir.

## Görsele yazı
Kapak özelliği kaldırıldı (`wiki/decisions/0056-kapak-kaldirildi.md`). Durağan görsele yazı gerekiyorsa:
1. `library/gorsel/sablon.html` dosyasını `work/gorsel/gorsel.html` olarak kopyala, yanına `zemin.png` (ve varsa `yuz.png`) koy, iki satırı yaz; vurgulanacak kelime `<em>` içinde.
2. Render: `.venv/Scripts/vedit pano work/gorsel/gorsel.html -o work/gorsel/gorsel-1.jpg --sure 0 --w 1280 --h 720` (dikey: `--w 1080 --h 1920`). `-o` .png ya da .jpg olunca `vedit pano` tek kare çeker.

## Videoda kullanılan görsel
- Dosya `work/gorsel/` altında üretilir, kurguya kütüphane varlığı gibi girer. Hareket gerekiyorsa `kurgu.json` dönüşüm keyframe'iyle yavaş itme verilir ya da `loop-flow` ile canlandırılır.
- Yeniden kullanılabilir çıkan görsel `library/` altına taşınır ve kilitlenmesi önerilir; kullanıcı onaylamadan kilitlenmez.
- `denetim` skill'i üretilmiş görseli AI slop açısından da değerlendirir: yapay parlaklık, bozuk el, anlamsız yazı, şablon kompozisyon.
