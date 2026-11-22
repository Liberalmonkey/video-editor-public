---
type: decision
title: "Yapım ekibi: Claude mimar ve entegratör, agy Gemini 4 Neon sözleşmeye karşı kod ve inceleme yazar"
status: accepted
tags: [adr, ajan, antigravity, yapim]
created: 2026-11-20
updated: 2026-11-20
sources: []
---

# ADR 0049: Yapım ekibi

> [!note] [[0003-model-yonlendirme]] ve [[0037-antigravity-orkestra]]'yı günceller: kod artık yalnız Claude'da değildir.

## Bağlam
Native motion kütüphanesi onlarca bileşen ve 31 stilin hareket token'ı demekti. Kullanıcı sınırlı işleri agy (Gemini 4 Neon) ajanlarına, Claude'un çalışmasıyla paralel vermek istedi (2026-11-19).

## Karar
- **Claude:** mimari ve sözleşmeler, çekirdek (Kurgu.tsx, alfa, geçiş, yerleşim, birleştirici, çapa, kurallar, Stüdyo), entegrasyon, ADR ve son inceleme.
- **agy:** araştırma (lisans, zanaat), bileşen aileleri, tema token taslakları, galeri kontaklarının multimodal incelemesi.
  - Model `gemini-4-neon-high` (kod) ve `gemini-4-neon-medium` (araştırma, inceleme).
  - Rol dosyaları: `motion-gelistirici`, `tema-gelistirici`, `test-yazari`, `lisans-arastirmaci`, `motion-gozden-gecirici`.
- **Protokol:**
  1. Önce sözleşme gelir (`studio/remotion/motion/SOZLESME.md`, örnek bileşen). agy yalnız ona karşı yazar.
  2. Görev kartı `work/agy/<tarih>-<konu>/asama-*.json`. Her kartın sahip olduğu dosyalar ayrıdır; iki kart aynı dosyaya yazmaz.
  3. Aynı anda en çok 3 agy görevi çalışır.
  4. Her karttan sonra `git status` farkıyla kapsam denetlenir; kapılar (tsc, şema, vitest, yasak kalıp, sabit renk) ve galeri kontağı açılır.
  5. Başarısız kart bir düzeltme kartı alır. İkinci başarısızlıkta işi Claude alır.
  6. Günlük `work/agy/ozet.md`.
- **Yalıtım:** worktree kurulmadı; commit edilmemiş çalışma ağacını commit etmeyi gerektiriyordu. Kartlar ayrık klasörlerde çalıştı; bu ADR'nin ölçülen sapmasıdır.

## Sonuçlar
- agy headless modda güvenilen klasörde dosya yazabildi; bypass bayrağı kullanılmadı.
- agy araştırma kartları adres uydurdu (13 LottieFiles, 2 GitHub). Adres içeren her çıktı Claude tarafında HTTP ile doğrulanır.
- İki kez gelen kod kusurları (elle anticipation, küçük yazı) gözden geçirici bulgusundan koda kapı oldu.

## İlgili kod
`.claude/agents/{motion-gelistirici,tema-gelistirici,test-yazari,lisans-arastirmaci,motion-gozden-gecirici}.md`, `scripts/ajan_esitle.py`, `work/agy/ozet.md`
