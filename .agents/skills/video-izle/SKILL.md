---
name: video-izle
description: Bir videoyu gerçekten izler — sahne değişimi kareleri, kare üstü yazı (OCR), zaman damgalı transkript ve zaman çizelgesi çıkarır, kareleri açıp bakar, sesi ölçer. Taslak ya da final render'ı gözle denetlerken, referans videoyu incelerken, "videoyu izle", "videoda ne oluyor", "şu saniyede ne var", "altyazı taşıyor mu", "izleyip söyle" dendiğinde kullan.
argument-hint: "<video yolu ya da URL> [soru]"
license: MIT
metadata:
  kaynak: https://github.com/guimatheus92/mcp-video-analyzer (0.11.0, MIT)
---

# Video izle

Ajan videoyu göremez; bu skill ona göz ve kulak verir. Kareleri ve transkripti çıkarır, sonra kareler `Read` ile açılıp bakılır. Görmeden yorum yapılmaz: bir kusuru yazmadan önce o saniyenin karesi açılmış olmalı.

## 1. Çıkar
Sürüm sabittir; `@latest` kullanma.

```bash
OPENAI_API_KEY= TWELVELABS_API_KEY= npx -y mcp-video-analyzer@0.11.0 analyze "<video>" --out work/izle/<ad> --max-frames 40 --ocr-language tur+eng --language tr > work/izle/<ad>/analiz.json
```

- `OPENAI_API_KEY=` ve `TWELVELABS_API_KEY=` boş verilir: araç yerel Whisper bulamazsa sesi OpenAI'a, anahtar varsa video adresini TwelveLabs'e gönderir. Bu projede yalnız yerel ve ücretsiz yol kullanılır; transkript boş gelirse `work/edit/digest.txt` ya da `vedit hazirla` kullan.
- `--out` her zaman verilir; yoksa kareler `%LOCALAPPDATA%\mcp-video-analyzer\` altında birikir. OCR dil dosyaları da ilk çalıştırmada oraya iner.
- Çıktı tek JSON: `metadata`, `transcript` (zaman damgalı), `ocrResults` (kare üstü yazı), `timeline`, `warnings`, `frames` (`time`, `filePath`).
- 76 saniyelik Reels için yaklaşık 95 saniye sürer (ölçüm 2026-11-15). İlk çalıştırma paketi indirir.
- `--max-frames` en çok 60. Kareler sahne değişimine göre seçilir ve videonun başına yığılabilir: uzun videoda belirli aralığı görmek için 2. adımdaki tek kare yolunu kullan.
- Yalnız konuşma gerekiyorsa `--detail brief` (kare çıkarmaz, hızlıdır).
- Küçük yazılı ekran kaydında `--max-width 0` kaynağın çözünürlüğünü korur.
- URL (YouTube, Instagram, TikTok) için `yt-dlp` gerekir; projede `.venv/Scripts/yt-dlp` vardır.

Bu projenin kendi araçları aynı işin bir parçasını zaten yapar; önce onlar:
- Tüm videonun tek bakışta özeti: `vedit sheet <video>` (kontak sayfası).
- Proje videosunun kelime zamanları: `work/edit/digest.txt`.

## 2. Bak
1. `analiz.json` içinden `frames[].filePath` karelerini `Read` ile aç (birkaçını aynı anda).
2. Belirli bir saniye gerekiyorsa tek kare al:
   ```bash
   ffmpeg -v error -ss <saniye> -i "<video>" -frames:v 1 -q:v 3 work/izle/<ad>/t<saniye>.jpg
   ```
3. Her gözlemi zaman damgasıyla yaz (`0:12`). Transkript, OCR ve kare birbirini doğrulamalı: altyazıda yazan kelime o anda söyleniyor mu, yazı güvenli alanda mı, kesme karesinde yüz yarım mı kalmış.

## 3. Dinle
Ses için tahmin yürütme, ölç:
- Loudness ve tepe: `vedit teslim` çıktısındaki LUFS ve dBTP, ya da `ffmpeg -i "<video>" -af ebur128=peak=true -f null -`.
- Olay sesi, senkron, müzik altında konuşma: `earshot` skill'i.
- Sessizlik ve dolgu adayı: `vedit oneri`.

## 4. Raporla
Uzun video ya da referans çözümlemesinde katmanlı yaz (ADR 0040, rea-video VIDEO.md fikri): birkaç yüz tokenlik özet kartı, sonra plan başına tek satırlık zaman çizelgesi, ayrıntı yalnız sorulan plan için. Ekranda görüleni araçların çıkardığından ayır. Sonraki soruda önce kart okunur, ham veri değil.
Kusurları `denetim` skill'inin biçiminde ver: zaman damgası, ne görüldü, öneri. Onaysız düzeltme yapılmaz.

## Sınırlar
- Kare örneklemedir, akış değildir: iki kare arasındaki tek karelik kusur kaçabilir. Şüpheli aralıkta kareleri sıklaştır.
- OCR Türkçe büyük harflerde ve stilize yazıda hata yapar (güven değeri 50-65); yazıyı kareden kendin oku.
- Çıktılar `work/izle/` altında kalır, git'e girmez. Ham videoyu ve büyük JSON'u bağlama alma; `analiz.json`'dan gereken alanı süz.
