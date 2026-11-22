# Cam ve ışık (yapay zekâ)

Yapay zekâ anlatımının modern dili: koyu uzay, kırılan cam yüzey, parlayan çekirdek, ince ışık halesi.

Kaynak: bang-motion techniques.md §6, §7e (kaca / bola bercahaya) (MIT). Hazır stil kataloğundan eklendi (ADR 0042); kural ölçülmüş referans değil, kaynağın tarifidir.

## Ne zaman
Yapay zekâ, teknoloji haberi, gelecek ve bilim anlatımı.

## Görsel dil
- Buzlu cam kart (backdrop blur), ince açık kenar
- Parlayan küre ya da çekirdek, küçük bloom
- Mor-camgöbeği çift vurgu, koyu zemin

## Palet
- vurgu: `#8B5CF6`
- ikincil: `#22D3EE`
- zemin: `#070712`
- yazi: `#F5F3FF`
- soluk: `#8A87A8`
- Motion teması: `cam-ve-isik` (grafikler bu renklerle gelir)

## Tipografi
- Başlık: Space Grotesk 700
- Gövde: Inter
- Altyazı stilin token'larını alır (ADR 0043): okunan kelime stilin vurgusu, gövde beyaz, koyu kontur; kutu, pop ve solma yok.

## Kurgu
- Tempo orta; ortalama çekim 2-3.5 sn.
- Geçiş aileleri: `isik-sizintisi`, `piksel-cozunme`, `zoom_kirbac`, `bolunme`, `isik`, `kirbac`.
- Hazır efektler: `bulanik_gir`, `odak_zoom`, `zoom_in`.

## Kaçın
- Turuncu vurgu
- Kâğıt ve kolaj
- Çizgi film karakteri

## Üretilen görsel
Sahne görseli gerektiğinde (gorsel-uret) bu stil soneki kullanılır, yazı görsele gömülmez:

`dark space background with a glowing glass orb core, frosted translucent glass panels, refraction, subtle bloom, violet and cyan light, futuristic AI aesthetic, no text`
