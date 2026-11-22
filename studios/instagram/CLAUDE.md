# Stüdyo: Instagram Reels

Genel akış `uretim-hatti`. Spec: `wiki/specs/instagram-studyosu.md`.

## Format
1080x1920, 30 fps, 15–90 sn, −14 LUFS. Güvenli alan: üst %12, alt %22, sağ %12; altyazı alt-orta (≈ %27 yükseklik).

## Kurallar
- Stil paketi zorunlu (`style-pack`); yoksa önce referans iste.
- İlk kare kapak: okunur başlık ya da güçlü görüntü; hareket ilk 0.5 sn'de başlar.
- Sessiz izlenebilir: önemli bilgi ekranda da metin (standart altyazı + kinetic-text).
- Her 1–2 sn anlamlı görsel değişim; büyük andan önce 300–600 ms durgunluk.
- Metin yüksekliği ≥ genişliğin %7'si (≈ 75 px); ekranda tek fikir.
- Mümkünse loop: son kare ilk kareye bağlanır.
- Trend ses Instagram içinde eklenir; render'da lisanslı/CC müzik ya da yalnız SFX. Audio Library standart parçaları kullanılmaz.
- Referans Reels görselleri `Projeler/inputs/_referanslar/instagram/images/`; stil grameri bir kez çıkarılır.
