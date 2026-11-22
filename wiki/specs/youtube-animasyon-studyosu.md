---
type: spec
title: "YouTube animasyon stüdyosu — 10–15 dk eğitici/eğlenceli"
status: active
tags: [spec, youtube, animasyon, uzun-video]
created: 2026-10-20
updated: 2026-10-20
sources: ["[[2026-10-20-opus-animasyon-rehberi]]", "[[2026-10-20-hyperframes]]", "[[2026-10-20-humanizer]]"]
decisions: ["[[0002-renderer-hyperframes]]", "[[0003-model-yonlendirme]]", "[[0007-seslendirme-kullanici-harici-arac]]", "[[0008-harici-varlik-kaynaklari]]"]
---

# YouTube animasyon stüdyosu

## Problem
Referans görseller ve YouTube linkleri verildiğinde, 10–15 dk'lık eğitici veya eğlenceli animasyon videoları üretilmeli. Senaryodan render'a kadar profesyonel kalite beklentisi var.

## Kullanıcı hikâyeleri
- Bir YouTuber olarak konu + referans linkler + görseller verip önce outline ve senaryo onaylamak, sonra seslendirip tam animasyonlu bir video almak istiyorum.
- Kanalımın stilini bir kez tanımlayıp her videoda tutarlı kullanmak istiyorum.
- Bir bölümde düzeltme istediğimde sadece o bölümün yeniden render edilmesini istiyorum.

## Kapsam
### Dahil
- **Referans analizi:** [[yt-dlp]] ile altyazı ve düşük çözünürlüklü video → tempo istatistikleri, kontak sayfası, stil grameri
- **Senaryo:** outline → senaryo → humanizer ([[2026-10-20-humanizer]]); retention yapısı, açık döngüler, bölümler
- **Seslendirme:** kullanıcı harici araçta üretip verir ([[0007-seslendirme-kullanici-harici-arac]]); müzik/SFX/motion talebi: [[0008-harici-varlik-kaynaklari]]
- **Senkron:** kelime zaman damgalarından sahne süreleri ([[2026-10-20-opus-animasyon-rehberi]])
- **Kurgu:** yönetmenin sahne listesi, blok tabanlı sahneler + hero sahneler (Canvas/Three.js)
- **Render:** bölüm bazlı render + cache, master ses, SRT, YouTube bölüm listesi

### Hariç
- Gerçekçi insan/yüz animasyonu (video modellerinin işi)

## Tasarım
`studios/youtube-animasyon/`:
- `CLAUDE.md`: eğitici ve eğlenceli kurallar
- `studio.yaml`: 1920x1080, 30 fps

**Akış:**
1. `reference` → `style-grammar.md` (bir kez)
2. `writer` (opus) outline → onay → senaryo + humanizer → onay
3. Seslendirme → `transcribe`
4. `director` (opus) → `scenes.json` → onay
5. Bölüm başına paralel `editor` (hero, opus)
6. Bölüm önizleme → QA → `director` (critique)
7. Final

## Kabul kriterleri
- [ ] 2–3 dk pilot uçtan uca çalışıyor
- [ ] 10 dk video: tek bölüm değişince yalnızca o bölüm render ediliyor
- [ ] Birleştirmede ses kayması yok (≤ 1 kare)
- [ ] Senaryo humanizer'dan geçmiş, Türkçe AI kalıpları temizlenmiş
- [ ] Critic puanları ≥ 8

> [!note] Güncellendi 2026-10-25
> Yayın paketi (başlık/thumbnail, SEO, bölümler, retention, Shorts) `yt-*` skill'leriyle hazırlanır: [[2026-10-25-youtube-agent-skill]].

## Açık sorular
- 12 dk render süresi ölçülecek (tahmin: basit sahnelerde yaklaşık 20–40 dk).
