---
type: decision
title: "Sade arayüz: üç çalışma alanı, her iş tek yerde"
status: accepted
tags: [adr, studio, arayuz, ergonomi]
created: 2026-11-12
updated: 2026-11-24
sources: []
---

# ADR: Sade arayüz

> [!note] Güncellendi 2026-11-24: Kapak alanı (Alt+4) kaldırıldı; çalışma alanları yeniden üçtür ([[0056-kapak-kaldirildi]]).

## Bağlam
Kullanıcı Video Stüdyo arayüzünü karışık buldu (2026-11-12): "ses ile ilgili düzenlemeleri yaptığımız bir sayfa varsa ikincisine gerek yok, altyazıyı yalnız bir yerden düzenleyelim". Denetimde 5 çalışma alanı ve 17 panel sayıldı; Kurgu alanında sağ grupta 7 sekme vardı, ses 6 yerde, iş başlatma 7 panelde, aynı kesme işlemi 3 arayüzdeydi, "Stil" adı iki ayrı şeyi anlatıyordu.

## Karar
Kural: bir iş tek yerde yaşar. Bileşenler yeniden yazılmaz, yalnız nereye takıldıkları değişir.

| Çalışma alanı | Paneller |
|---|---|
| Kurgu (Alt+1) | sol: Proje, Medya, Kütüphane · orta: Kaynak, Program, Timeline · sağ tek grup: Klip, Ses, Altyazı, İşler, AI |
| Teslim (Alt+2) | Çıktı ayarları, İşler, Denetim, Program, Çıktılar |
| Kütüphane (Alt+3) | Kütüphane, Video stili |
| Kapak (Alt+4) | Kapak, Program, İşler |

> [!note] Güncellendi 2026-11-15
> Kapak, Teslim alanında Çıktılar'ın arkasında gizli sekmeydi ve kullanıcı bulamadı; dördüncü çalışma alanı oldu ([[0027-kapak-sayfasi]]). Kayıtlı yerleşimde alanın varsayılan panellerinden biri eksikse yerleşim varsayılana döner (`ALANLAR[ad].paneller`, `studio/web/src/main.tsx`); sonradan eklenen panel gizli kalmaz ve yerleşim anahtarını elle sürümlemek gerekmez.

| Konu | Karar |
|---|---|
| Ses | İz düzeyi, sessize alma, solo ve ölçüm yalnız **Ses** panelinde (eski Mikser). Program'daki ikinci metre ve Timeline iz başlığındaki ikinci sessize alma kalktı. "Ses" çalışma alanı kalktı |
| Klip | Seçili klibin her ayarı **Klip** panelinde (eski Efekt Kontrolleri) |
| Altyazı | Tek yer. Öneriler (sessizlik ve dolgu) bölüm olarak içine girdi. "Transkripti hazırla" tek düğme: transkript yoksa `hazirla` işini başlatır, bitince projeye alır. Görünüm bölümünün adı "Altyazı görünümü" |
| İşler | Görünen üç düğme: Hazırla, Taslak, Final. AI Edit, Konuşmacıyı birleştir (kes), Kaizen, Düzen, XML "Diğer" menüsünde |
| Grafik | Kütüphane'de sekme |
| Stil | "Video stili" adıyla Kütüphane alanında ([[0029-stil-paneli]]) |
| Yerleşim | Kayıt anahtarı `studio.alan.v2`; bilinmeyen alan ya da panel varsayılan yerleşime düşer |

## Sonuçlar
- Eski kayıtlı yerleşimler bir kez sıfırlanır.
- Alt+4 ve Alt+5 kısayolları kalktı. Panel kimlikleri (`efekt`, `mikser`, `stil`) kodda aynı kaldı, yalnız başlıklar değişti.
- `studio/e2e` betikleri yeni adlara göre güncellendi; bu turda çalıştırılmadı.
- Doğrulandı 2026-11-12: üç alan tarayıcıda açıldı, konsol hatası yok; `tsc`, vitest (99) ve derleme geçti.
- [[0021-video-studyo-nle]] ve [[0027-kapak-sayfasi]] içindeki alan listeleri bu kararla güncellenir (Kapak artık Teslim alanında).

## İlgili kod
- `studio/web/src/main.tsx` (`ALANLAR`, `alanAnahtari`), `studio/web/src/zaman/kisayol.ts`
- `studio/web/src/paneller/{AltyaziPaneli,OnerilerPaneli,KutuphanePaneli,IslerPaneli,Monitorler,MikserPaneli,EfektPaneli}.tsx`, `studio/web/src/zaman/Timeline.tsx`
