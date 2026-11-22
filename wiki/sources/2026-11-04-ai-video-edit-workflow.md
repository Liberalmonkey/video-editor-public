---
type: source
title: "omergocmen/ai-video-edit-workflow"
tags: [remotion, efekt, arayuz, kurulum]
created: 2026-11-04
updated: 2026-11-04
url: https://github.com/omergocmen/ai-video-edit-workflow
author: Omer Gocmen
sources: []
---

# ai-video-edit-workflow

> [!note] Güncellendi 2026-11-05
> Bu kaynaktan alınan kod kullanıcı isteğiyle silindi: [[0020-panel-kaldirildi]]. Sayfa geçmiş kaydıdır.

MIT lisanslı, 48 dosya. İncelenen commit `0cd495b` (2026-11-04). Birleşim kaydı: [[0019-arayuz-ve-efekt-motoru-birlesimi]].

## Özet
- Form, video ve materyalleri alır, `brief.md` yazar, terminalde yapay zeka aracını başlatır.
- Remotion ile 25 efektlik şeffaf katman, yatay kaydı 9:16 kırpıp takip eden `Dikey`, kaynak görüntüsü olmayan sesli anlatım modu.
- `scripts/kontrol.mjs` render öncesi plan kapısı ve render sonrası ölçüm yapar.
- `baslat.bat` eksik araçları proje içine kurar, kalıcı PATH'e yazmaz. Mac başlatıcısı var. Claude, Codex, Gemini seçilebilir.

## Ana çıkarımlar
- Efektler için güçlü, açık bir JSON sözleşmesi var; ajan kod yazmadan çalışıyor.
- Ekran kaydını dikeye çevirme, projede eksik bir yetenekti.
- Altyazı `textShadow` ve tema rengi kullanıyordu; ADR 0014 ile çelişir.
- Render ayarında renk uzayı belirtilmiyor, ölçümü süre, ses, siyah alan ve donuk görüntüyle sınırlı. Loudness, BT.709 ve slop denetimi yok.
- Kütüphane, kaizen ve düzeltme defteri yok.

## Projeye etkisi
`motor/`, `ui/public/brif.html`, başlatıcılar ve `efekt-katmani` skill'i buradan uyarlandı. Lisans `motor/LICENSE`.

## Çelişkiler ve açık sorular
> [!warning] Çelişki
> Repo ajana "soru sorma, varsayımla devam et" diyor; proje onay kapıları kullanıyor. Proje kuralı alındı.

**Açık:** Depoda 4 yıldız var, uzun vadeli bakımı bilinmiyor. Birleşim kopyadır, upstream takip edilmez.

## Bağlantılar
[[0019-arayuz-ve-efekt-motoru-birlesimi]] · [[0014-altyazi-standardi-ve-repo-entegrasyonu]] · [[0017-terminal-hizli-hat]]
