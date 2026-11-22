---
type: source
title: "Kapak araştırması v2: Nano Banana prompt kuralları, bölgesel düzeltme, açık kaynak kapak araçları"
tags: [kapak, thumbnail, nano-banana, antigravity, arastirma]
created: 2026-11-22
updated: 2026-11-22
sources: []
url: "https://dev.to/googleai/nano-banana-pro-prompting-guide-strategies-1h9n"
---

# Kapak araştırması v2

## Özet
[[0052-kapak-is-akisi-v2]] için yapılan web ve GitHub araştırması (2026-11-22). Üç soru vardı:
- Antigravity'de görsel modeli seçilebilir mi?
- Profesyonel kapak prompt'u nasıl yazılır?
- Hazır açık kaynak araç var mı?

## Ana çıkarımlar
- **agy görsel modeli.** agy 1.5.14 görseli yerleşik `image-generator` alt ajanıyla üretir. Model loglarda `gemini-3.1-flash-image` olarak görünür (kota hatası satırı, `quotaResetTimeStamp`). `agy --help`'te görsel modeli bayrağı yok; `--model` yalnız yönlendiren modeli seçer (23 model). Resmi bir görsel modeli seçme yolu bulunamadı.
- **Topluluk çözümleri.** `nano-banana-antigravity` adlı skill (openclaw/skills), Antigravity OAuth jetonlarını başka bir araçla kullanıyor ve hız sınırında hesaplar arasında dönüyor. Bu bir ToS riski; alınmadı. Medium'daki bir yazı kendi MCP sunucusuyla `GEMINI_MODEL_NAME` ortam değişkeni kullanıyor; bu yol API anahtarı ister.
- **Google'ın Nano Banana Pro rehberi** (dev.to/googleai):
  - Etiket yığını değil, yaratıcı yönetmen gibi cümle yazılır.
  - Hedef kitle ve bağlam verilir.
  - Referanslı kişide kimlik kilitlenir: yüz hatları Image 1 ile aynı kalır, yalnız ifade değişir.
  - Yazı tırnak içinde tam metinle verilir.
  - Oran açıkça yazılır.
  - Neredeyse doğru görsel baştan üretilmez; yalnız değişecek şey söylenir.
  - Rehberin "Viral Thumbnail" şablonu şunları içerir: kimlik, eylem, ikinci nesne, bağlayıcı grafik, büyük yazı, parlak doygun zemin.
- **Nano Banana 2.1 ve Pro.** Kaynaklar üçüncü taraf: fuser.studio, nanoprompts.net, glbgpt.com, omniakey.com.
  - 2.1 varsayılan model önerilir. Kısa ve net prompt'u ödüllendirir, daha az fazladan nesne ekler.
  - Pro yoğun marka ve tipografi işi içindir.
  - Referans sınırları: Pro 14 (6 nesne, 5 karakter, 3 stil); 2.1 14 (10 nesne, 4 karakter).
- **Kapak prompt'u pratikleri** (vidpros, miraflow, morphed, crossroadmedia):
  - Oran prompt'un başında yazılır ("YouTube thumbnail, 16:9").
  - Tek kahraman nesne; bir ana palet ve bir vurgu rengi.
  - Yazı için boş alan açıkça tarif edilir (ör. sağ üçte birde yüz, sol üçte bir yazıya boş).
  - Başlık 2-4 kelimedir.
  - A/B varyantlarında iskelet sabit tutulur.
- **Bölgesel düzeltme (kırmızı kutu tekniği).** Kaynaklar: nanoprompts.org, fotiecodes, Hacker News, RunDiffusion.
  - Nano Banana'nın maske ya da kutu girişi yoktur.
  - Görsele kırmızı kutu çizilir. Prompt "kutunun içinde X'i değiştir, kutuyu ve işaretleri sil" der.
  - Sonuçtan yalnız kutu bölgesini orijinale geri yapıştırmak, dışarıda hiçbir şeyin değişmemesini garanti eder.
- **Açık kaynak araçlar.**
  - jordicor/youtube_thumbnail_generator_with_AIs (MIT): sahne, yüz kümeleme ve transkriptle fikir ve görsel modelini ayırır, yüzü videodan seçer. Redis, InsightFace (ticari kullanıma kapalı modeller) ve ücretli API ister.
  - ohvignas/ThumbGen (MIT): düğüm tuvali, prompt geliştirme, A/B/C varyant; OpenRouter ücretli.
  - srvjha/ThumbAI, Rd6rd8/thumbforge: ücretli API ister.
  - brendanjowett/yt-thumbnail-generator: gpt-image ister.
  - Hiçbiri kurulmadı. Alınan fikirler: fikir modeli ile görsel modelini ayırmak, stil referansı, prompt geliştirme, varyant.
- **Midjourney.** Yazıyı güvenilir çizmez. Kişi referansı sürüme göre `--oref` (Omni) ya da `--cref`, stil referansı `--sref`.

## Projeye etkisi
- [[0052-kapak-is-akisi-v2]]: model seçici (yönlendiren model) ve "görsel modeli agy sabit" rozeti eklendi.
- Brief yapılı alanlara geçti.
- `kapak_prompt.master` altı hedef için yazılı ve boş zemin sürümü üretiyor.
- Görsel düzeltmede kırmızı kutu ve geri yapıştırma kullanılıyor.
- Dış görsel içe alma eklendi.

## Çelişkiler ve açık sorular
> [!question] Çıkarım
> agy'nin görsel modeli Google tarafında değişebilir. Rozet adı loglardan okur ve yalnız kota hatasında güncellenir.

- Leonardo'nun model adları (Lucid Origin, Phoenix, Lucid Realism) ve Midjourney'nin referans parametreleri sürüme göre değişebilir. Master prompt bunları not olarak verir.

## Bağlantılar
- [[0027-kapak-sayfasi]], [[2026-11-15-kapak-kalip-analizi]], [[2026-11-09-kapak-arastirmasi]], [[0025-gorsel-uretimi-google]]
- https://dev.to/googleai/nano-banana-pro-prompting-guide-strategies-1h9n
- https://github.com/jordicor/youtube_thumbnail_generator_with_AIs
- https://github.com/ohvignas/ThumbGen
- https://nanoprompts.org/advanced-techniques/precise-local-editing
- https://fuser.studio/articles/nano-banana-prompt-guide
- https://www.glbgpt.com/hub/nano-banana-2-1-vs-pro/
