---
type: source
title: "Avenox: ajanla video kurgu notları"
tags: [kurgu, ajan, kapi, transkript, motion]
created: 2026-11-17
updated: 2026-11-17
url: https://github.com/avenoxai/avenox-video-kurgu-notlari
author: Avenox
raw: "[[raw/repos/2026-11-17-avenox-ve-sirio-kurgu]]"
sources: []
---

# Avenox kurgu notları

MIT. Bir YouTube videosunun skill'e çevrilmiş dersleri: kodlama ajanıyla uzun videoyu "slop" çıkarmadan editlemenin düzeni.

## Özet
- Hız ajan sayısından değil, ajanların etrafındaki düzenden gelir: tek şef, dosya sözleşmesi, her istasyonun çıkışında kapı.
- Kesimden sonra, grafikten önce pano haritası: her pasaj için "yalnız dinleyen anlar mı?" sorusu.
- Aynı hata iki kez olursa nota değil koda yazılır; kod geçmezse video çıkmaz.
- Eşikler sayıyla verilir (10 sn'de 10-10,5 hareket), yasaklar açık yazılır (neon, mor gradyan, parlama, emoji).
- Whisper adları karıştırır ("Claude" ile "cloud"); düzeltme sözlüğü tutulur.

## Ana çıkarımlar
- Dinleyen anlıyorsa ekran sesi tekrar etmez; anlamıyorsa somut olan gösterilir (rakam, logo, kaynak, arayüz).
- Ürün adı geçiyorsa resmi logo; alıntı birebir ve doğrulanabilir olur.
- Görsel duyguyu çizer, kod bilgiyi yazar: rakam, yazı ve logo modele çizdirilmez.

## Projeye etkisi
Bkz. [[0041-avenox-kurgu-dersleri]]. Çoğu ders projede zaten vardı (yoğunluk hedefi, senkron kapısı, kapak kodla, checks.md); dördü eklendi.

## Çelişkiler/açık sorular
- Avenox "kesimden sonra kesime dokunulmaz" der; projede ai-edit kesimi de yazar. Proje kuralı geçerli: `--aralik` dışı değişmez ([[0028-ai-edit]]).

## Bağlantılar
[[2026-11-03-sirio-berati-repolari]] (pano haritası ve kapı fikrinin kaynağı)
