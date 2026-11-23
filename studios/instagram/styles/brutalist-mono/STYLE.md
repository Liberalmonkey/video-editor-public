# Brutalist mono

Siyah-beyaz, keskin köşe, dev yazı, tek sarı vurgu; iddialı fikir ve manifesto videoları için.

Kaynak: bang-motion (brutalist mono); library/motion/tema/brutalist-mono.css (MIT). Hazır stil kataloğundan eklendi (ADR 0042); kural ölçülmüş referans değil, kaynağın tarifidir.

## Ne zaman
Görüş, manifesto, iş dünyası tavsiyesi, sert hook.

## Görsel dil
- Ekranı dolduran dev yazı
- Sıfır köşe yuvarlama, kalın çizgi
- Tek sarı vurgu

## Palet
- vurgu: `#FFE600`
- ikincil: `#FFFFFF`
- zemin: `#000000`
- yazi: `#FFFFFF`
- soluk: `#9A9A9A`
- Motion teması: `brutalist-mono` (grafikler bu renklerle gelir)

## Tipografi
- Başlık: Montserrat 900
- Gövde: Inter
- Altyazı stilin token'larını alır (ADR 0043): okunan kelime stilin vurgusu, gövde beyaz, koyu kontur; kutu, pop ve solma yok.

## Kurgu
- Tempo hızlı; ortalama çekim 1-2 sn.
- Geçiş aileleri: `sil`, `panjur`, `bozulma`, `piksel`, `zoom_kirbac`, `kirbac`.
- Hazır efektler: `punch`, `carp_zoom`, `giris_carp`.

## Kaçın
- Yumuşak gradyan
- Pastel ve yuvarlak köşe
- Uzun çapraz geçiş

## Üretilen görsel
Sahne görseli gerektiğinde (gorsel-uret) bu stil soneki kullanılır, yazı görsele gömülmez:

`brutalist black and white poster composition, massive bold type blocks, hard edges, single yellow accent, high contrast, no text`
