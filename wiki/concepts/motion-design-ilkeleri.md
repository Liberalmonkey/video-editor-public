---
type: concept
title: "Motion design ilkeleri (sistemin zevk katmanı)"
tags: [motion-design, tipografi, easing, gecis]
created: 2026-10-20
updated: 2026-10-20
sources: ["[[2026-10-20-opus-animasyon-rehberi]]"]
---

# Motion design ilkeleri

## Tanım
Bu sistemde üretilen her videonun uyduğu görsel ve hareket kuralları. Çekirdek kurallar [[2026-10-20-opus-animasyon-rehberi]] kaynağından fikir olarak alındı. Gerçek çekim, uzun video ve platform kuralları bizim eklememiz.

## Nasıl çalışır
**Yasaklar ("AI şablonu" görünümü):**
- Ortalanmış başlık ile mor/mavi gradyan kombinasyonu
- Anlamsız parçacık, lens flare, neon parlama, RGB kayması, sürekli sarsıntı
- Her şeye uygulanan elastik easing

**Easing işe göre seçilir:**
- UI öğeleri: sıkı yay
- Kamera: yumuşak gir-çık
- Taşma (overshoot): yalnızca etkileşimde ve küçük
- Logo: kontrollü yavaşlama

**Hiyerarşi:**
- En fazla 2 yazı tipi ve tek vurgu rengi
- Her sahnenin tek bir işi olur
- Metin en az ~1.2 sn ekranda kalır

**Süreklilik:**
- Geçiş, önceki sahnede görünen bir nesneden doğar
- 2–3 geçiş ailesi seçilir ve tüm videoda yalnızca bunlar kullanılır

**Ritim:**
- Büyük andan önce 300–600 ms durgunluk bırakılır
- Kısa formatta her 1–2 sn'de anlamlı bir değişim olur
- Ölü zaman en fazla 0.5 sn

**Hareket dili (anlam haritası):**
- Sağa hareket = ilerleme
- Büyüme = önem
- Dönme = durum değişikliği

**Eğitici videolar:**
- Önce göster, sonra adlandır
- En fazla 5 kavram
- Ekranda aynı anda tek cümle

**Kısa dikey video:**
- Sessiz izlendiğinde de anlaşılır olmalı
- İlk kare kapak işlevi görmeli
- Üst %12 ve alt %20 güvenli alanın dışında kalır
- Metin yüksekliği ekran genişliğinin en az %7'si olmalı

> [!question] Çıkarım
> **Gerçek çekim için eklemelerimiz** (kaynakta yok, sektör pratiği):
> - Jump cut'ı gizlemek için %100 ve %115 punch-in dönüşümlü kullanılır.
> - Kesimler kelime sınırında ve nefeste yapılır.
> - J/L cut kullanılır.
> - B-roll kısa formatta 2–4 sn'de, uzun formatta 5–10 sn'de bir gelir.

## Projede kullanımı
`.claude/skills/motion-design/` (kurallar), `render-qa` (rubrik) ve `director` ajanı (critique). Stil paketleri (`studios/*/styles/`) bu ilkeleri marka düzeyinde somutlaştırır.

## Alternatifler / trade-off'lar
Kural seti zevki daraltabilir. Bu yüzden stil paketleri, gerekçe yazılmak şartıyla bir kuralı esnetebilir.

## Kaynaklar
- [[2026-10-20-opus-animasyon-rehberi]] · [[render-sozlesmesi]]
