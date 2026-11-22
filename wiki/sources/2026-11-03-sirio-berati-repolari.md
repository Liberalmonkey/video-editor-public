---
type: source
title: "Sirio Berati açık kaynak video repoları"
tags: [motion, pano, kurgu, teleprompter]
created: 2026-11-03
updated: 2026-11-03
url: https://github.com/sirioberati
author: Sirio Berati (TEIN AI)
raw: "[[raw/repos/2026-11-03-sirio-berati-repolari]]"
sources: []
---

# Sirio Berati repoları

Dört repo da MIT. İncelenen commit'ler ham kayıtta.

## Özet
- **YouTube-AI-Motion-Graphics:** 74 HTML pano, üç skill (`explainer-board-brief`, `explainer-board-system`, `board-sync`), `checks.md` yöntemi, sanal saatli `export.py`.
- **YouTube-AI-Video-Editing-System:** Eyeline teleprompter, Eyeline Edit, 267 pano, kesim QA araçları. Yedi skill'i kasıtlı olarak boş yer tutucu.
- **Genjustsu:** Seedance (Enhancor) ile video özne değiştirme. Ücretli API, Windows'ta WSL2.
- **Emotion-Control:** videodan kil yüz maskesi. FLAME/SPECTRE lisansı ticari olmayan kullanımla sınırlı.

## Ana çıkarımlar
- Bir pano, sese kilitlenince değer kazanır: öğe kendi kelimesinde girer.
- Düzeltmeler bir dosyada birikirse aynı hata tekrar etmez (`checks.md`).
- Render ekran kaydı olmamalı; her kare zamana konumlanırsa geri sarmada aynı görüntü çıkar.
- Kesim, klip etiketine göre değil dışa aktarılan sesin yeniden yazıya dökülmesiyle denetlenir.

## Projeye etkisi
Bkz. [[0014-altyazi-standardi-ve-repo-entegrasyonu]]. Üretilen: `library/boards/`, `library/checks.md`, `vedit pano`, `vedit kesimqa`, teleprompter.

## Çelişkiler/açık sorular
`board-sync` zoom ve SFX'i yasaklar, [[0013-uretim-akisi-ve-olay-sesi]] ister. Karar: proje kuralı geçerli.

## Bağlantılar
[[0014-altyazi-standardi-ve-repo-entegrasyonu]]
