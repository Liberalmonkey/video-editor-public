# Piksel 8-bit

Oyun konsolu dili: düşük çözünürlüklü piksel, 14 renk palet, HUD kalbi, soru bloğundan çıkan altın.

Kaynak: huashu-art-motion 风格配方/14_8bit.md; library/motion/tema/piksel-16bit.css (MIT). Hazır stil kataloğundan eklendi (ADR 0042); kural ölçülmüş referans değil, kaynağın tarifidir.

## Ne zaman
Oyun kültürü, retro teknoloji, algoritma, eğlenceli eğitim.

## Görsel dil
- 240x135 piksel ızgara, 1 px siyah kenar
- Sınırlı palet
- HUD: can, puan, seviye

## Palet
- vurgu: `#F8B800`
- ikincil: `#3CBCFC`
- zemin: `#000000`
- yazi: `#FCFCFC`
- soluk: `#BCBCBC`
- Motion teması: `piksel-8bit` (grafikler bu renklerle gelir)

## Tipografi
- Başlık: Pixelify Sans 700
- Gövde: Pixelify Sans
- Kod: VT323
- Altyazı stilin token'larını alır (ADR 0043): okunan kelime stilin vurgusu, gövde beyaz, koyu kontur; kutu, pop ve solma yok.

## Kurgu
- Tempo hızlı; ortalama çekim 1.2-2.5 sn.
- Geçiş aileleri: `piksel-cozunme`, `panjur`.
- Hazır efektler: `punch`, `nabiz`, `sarsinti`.

## Kaçın
- Bulanıklık ve yumuşak gölge
- Serif
- Fotoğraf gerçekçiliği

## Üretilen görsel
Sahne görseli gerektiğinde (gorsel-uret) bu stil soneki kullanılır, yazı görsele gömülmez:

`8-bit pixel art scene, 240x135 low resolution grid, limited 14 color palette, 1px dark outlines, retro game HUD vibe, crisp pixels, no text`
