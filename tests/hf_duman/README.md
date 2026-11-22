# HyperFrames duman paketi (ADR 0051)

`vedit hf-guncelle` yeni bir HyperFrames sürümünü sabitlemeden önce bu kompozisyonları aday sürümle render eder:
`lint` hatasız mı, çıktı boyutu ve süresi doğru mu, saydam webm alfa taşıyor mu, 1. saniye karesi `altin.png` ile
ortalama piksel farkı eşiğin altında mı. `altin.png` yoksa ilk geçen sürüm onu yazar. Kompozisyon değişirse
`altin.png` silinir, bir sonraki koşu yenisini üretir.

- `saydam-degisken`: saydam kök, değişken metin, `--format webm`.
- `video-gsap`: zaman aralıklı `<video>` (`data-media-start`) ve GSAP zoom; video koşu sırasında ffmpeg ile üretilir.
- `metin-turkce`: Montserrat ile Türkçe harfler (ğ ş ı İ), tema token'ı.
