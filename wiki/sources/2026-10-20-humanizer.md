---
type: source
title: "humanizer skill (blader)"
tags: [senaryo, yazim, skill]
created: 2026-10-20
updated: 2026-10-20
raw: raw/repos/2026-10-20-humanizer.md
url: https://github.com/blader/humanizer
author: Siqi Chen
sources: []
---

# humanizer skill

## Özet
Metni söylediğini değiştirmeden "AI yazmış gibi" okunmaktan çıkaran, 26 desenli bir Agent Skill (MIT) ([[raw/repos/2026-10-20-humanizer]]).

## Ana çıkarımlar
- Desenler altı grupta toplanıyor:
  - A: söylemek yerine sahnelemek
  - B: kuralla ritim
  - C: şişirme
  - D: kuralla biçim
  - E: sohbet artıkları
  - F: yanlış okur
- Akış: işaretle → yeniden yaz → eleştir → son hâl. Asla gerçek uydurmaz.
- Kurallar dilden bağımsız; Türkçe eşdeğer kalıplar ayrıca tanımlanmalı.

## Projeye etkisi
`.claude/skills/humanizer/` altına kopyalanacak. Senaryo modunda D grubu kapalı olacak. `references/turkce-kaliplar.md` ile Türkçe genişletilecek. `script-polisher` ajanı (Sonnet) kullanacak ([[0003-model-yonlendirme]]).

## Çelişkiler / açık sorular
- Konuşma dili için ek kural gerekiyor: kısa cümle, nefes noktaları, sesli okunabilirlik. Bunlar `scriptwriting` skill'ine yazılacak.

## Bağlantılı sayfalar
- [[humanizer]] · [[youtube-animasyon-studyosu]]
