---
type: decision
title: "Dış motion varlığı: zorunlu lisans kaydı, alfa yöntemi tespiti, atıf"
status: accepted
tags: [adr, motion, lisans, kutuphane, lottie]
created: 2026-11-20
updated: 2026-11-20
sources: []
---

# ADR 0046: Dış varlık içe aktarma ve lisans

## Bağlam
Kullanıcı ücretsiz motion varlıklarını elle indirir: CTA, ok, light leak, film yanığı, konfeti, tepki. Kaynaklar Mixkit, Pixabay, LottieFiles, Uppbeat ve GitHub'dır. Kazıma ve API yoktur (kullanıcı kararı, 2026-11-19).

Eski yükleme yalnız lisans adını alıyordu. Yeşil perde ve siyah zeminli dosyalar alfasız kalıyordu; atıf ve kısıt bilgisi AI edit'e ulaşmıyordu.

## Karar
- **Komut:** `vedit motion ice-al <dosya|klasör> --kaynak ... [--url --lisans --atif-metni --kisit --tur --anahtar-dene]`. Stüdyo'da Kütüphane > Motion > "İçe aktar" aynı yolu kullanır.
- **Lisans kaydı zorunlu:** `kaynak`, `url`, `lisans`, `atif_gerekli`, `atif_metni`, `kisitlar`, `indirme_tarihi`.
  - Eksik alan kaynağın doğrulanmış varsayılanından tamamlanır (`motion_ice.VARSAYILAN`, 2026-11-19).
  - Yine eksikse varlık reddedilir (CLI çıkış kodu 2, API 422).
  - Uppbeat Free atıf metni olmadan alınmaz.
- **Alfa yöntemi kendiliğinden bulunur:**
  - alfalı webm/mov olduğu gibi kalır;
  - yeşil perde chromakey + despill ile VP9 alfaya çevrilir (`--anahtar-dene` üç eşikte önizler);
  - siyah zemin kaynakta `screen` karışımıyla çizilir;
  - Lottie ve dotLottie native `dis/lottie` bileşenine gider, doygun renkler temanın vurgu ve ikincil rengine eşlenir;
  - GIF/APNG VP9 alfaya çevrilir; SVG görsel klibi olur.
- **Depo:** `library/motion/dis/<kaynak>/<id>/` altında orijinal, normalize dosya, poster, kontak ve `meta.json` durur. Manifestteki dış kayıtlar bunlardan üretilir (`manifest_yenile`), elle yazılmaz; silme klasörü kaldırır.
- **Atıf:** atıf isteyen varlık kurguda kullanılırsa `vedit final` `yayin.md`'ye "Atıflar" bölümünü yazar.
- **Kısıtlar:** Motion sayfasında rozet olarak görünür ("atıf gerekli", "yalnız kendi kanalın"). AI edit kataloğu kısıtlarla birlikte görür.

## Sonuçlar
- İndirme listesi `library/motion/indirme-listesi.md`'dedir (agy `lisans-arastirmaci`, adresleri Claude doğruladı).
  - 13 uydurma LottieFiles adresi ve 2 olmayan GitHub reposu yakalandı ve değiştirildi.
  - Pixabay otomatik denetimde 403 veriyor; tarayıcıda açılan adresler kullanılır.
- Kod lisansları: SwiftClip, remotion-templates, onda (yalnız kod), pqoqubbw/icons, Lucide, Tabler ve Phosphor kopyalanabilir.
  - remotion-transition-series lisanssız olduğu için kod alınmaz.
  - remotion-bits, remocn ve Curvable/motion için LICENSE dosyası doğrulanmadı; kod kopyalanmaz.

## İlgili kod
`src/vedit/motion_ice.py`, `src/vedit/studio/kutuphane.py`, `studio/web/src/paneller/MotionPaneli.tsx`, `studio/remotion/motion/dis/lottie/`, `src/vedit/hizli.py atif_yaz`, `tests/test_ice_al.py`
