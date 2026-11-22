---
type: concept
title: "Token ekonomisi"
tags: [maliyet, mimari]
created: 2026-10-20
updated: 2026-10-20
sources: ["[[2026-10-20-opus-animasyon-rehberi]]", "[[2026-10-20-hyperframes]]", "[[2026-10-20-ffmpeg]]"]
---

# Token ekonomisi

## Tanım
Profesyonel kaliteden ödün vermeden LLM token harcamasını en aza indiren tasarım ilkeleri.

## Nasıl çalışır
1. **Ölçme script'te, karar LLM'de.** ffprobe, whisper, sessizlik, sahne, loudness ve beat ölçümlerini script'ler yapar. LLM yalnızca bunların kompakt özetlerini (digest) görür ([[2026-10-20-ffmpeg]]).
2. **Kontak sayfası.** 16 kare tek görselde birleştirilir, yaklaşık 1.5k token tutar. Ham video asla LLM'e gitmez.
3. **Kod değil veri.** LLM [[timeline-json]] dosyasına parametre yazar, HTML'i üretici script yazar.
4. **HTML okumadan inceleme.** `hyperframes timeline --json` HTML okumadan zaman çizelgesini verir ([[2026-10-20-hyperframes]]).
5. **Onay kapıları.** Kod ve render öncesinde senaryo ile sahne listesi onaylanır ([[2026-10-20-opus-animasyon-rehberi]]).
6. **Hedefli düzeltme.** Düzeltmeler kare cinsinden ve JSON yaması olarak verilir; yeniden üretim yapılmaz.
7. **Önce otomatik QA.** Görsel eleştiriden önce otomatik kontroller çalışır. Cilalama en fazla 2 tur.
8. **Artımlı render.** Bölüm hash'i değişmediyse bölüm yeniden render edilmez.
9. **Kademeli skill yükleme.** SKILL.md kısa tutulur, detay `references/` altında ve gerektiğinde okunur. Stüdyo kuralları yalnızca o klasörde yüklenen `CLAUDE.md` dosyalarında.
10. **Tek seferlik stil grameri.** Referanslar bir kez analiz edilir ve sonuç tekrar kullanılır.
11. **Alt ajan izolasyonu.** Alt ajanlar dar girdi alır ve kısa özet döner; ana Opus bağlamı şişmez.

## Projede kullanımı
Tüm `vedit` komutları ve skill'ler bu ilkelere göre yazılır ([[0001-claude-code-skill-ajan-mimarisi]], [[model-yonlendirme]]).

## Alternatifler / trade-off'lar
Daha az görsel inceleme bazı hataların gözden kaçmasına yol açabilir. Bunu otomatik QA'nın kapsamı (siyah/donuk kare, loudness, güvenli alan, TR glif) dengeler.

## Kaynaklar
- [[model-yonlendirme]] · [[timeline-json]]
