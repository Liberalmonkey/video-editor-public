---
name: denetim
description: Video kalite denetiminin tek yeri — vedit denetim ölçümleri, 12 maddelik rubrik (özgünlük ve brif uyumu dahil), P0/P1/P2 düzeltme listesi, QC etki ekseni ve AI slop denetimi (zaman damgası + öneri, kullanıcı onayı olmadan değiştirmez). Taslak ya da final render sonrası ve teslimden önce her zaman kullan; "AI slop", "yapay duruyor", "AI yapmış gibi", "şablon gibi", "ucuz görünüyor", "ruhsuz", "render QA", "kontrol et" dendiğinde kullan.
---

# Denetim

Tek komut: `.venv/Scripts/vedit denetim <video> --olaylar work/edit/olaylar.json --metin <senaryo>`. `kesimqa`, `slop`, ses ölçümü ve kontak sayfasını çalıştırır, tek tablo basar, dosyaları videonun `work/qa/` klasörüne yazar. Sonra: rubrik (aşağıda), ardından `references/slop.md` adımları. Taslakta yalnız kontak sayfası ve rubrik yeter; tüm denetim final render'da bir kez çalışır.

# Render QA ve eleştiri

Sıra: `vedit qa` (otomatik) → hatalar düzelir → director (critique).

## 1. Otomatik rapor (`qa/report.json`)
| Kontrol | Eşik | Düzeltme |
|---|---|---|
| loudness / true peak | −14 ±1 LUFS, ≤ −1 dBTP | `vedit mix` |
| siyah kare | yok | timeline start/dur |
| donuk görüntü ≥ 3.5 sn (uyarı) | — | punch-in, B-roll, overlay |
| sessizlik ≥ 1.5 sn (uyarı) | — | EDL'de kes ya da müzik |
| SFX yoğunluğu (uyarı) | ≥ 0.4 sn aralık | ipucu sil |
| altyazı hızı (clean-sub) | ≤ 22 kr/sn | sayfa böl |
| TR glif | eksik yok | font değiştir |
| hyperframes lint | 0 hata | build/blok |

OpenMontage / olay sesli çıktıda ek olarak `<olaylar>.rapor.json` oku: `uyarilar` (tık riski, dakikada 6'dan fazla zoom/geçiş sesi, eksik ses), `dusen` (çakıştığı için atılan olaylar), loudness. Son aşamada `usta-editor` üç geçişli denetim ve videoyu görmemiş taze denetçi.

## 2. Girdi (token disiplini)
Ölçüm temiz olsa da videoyu izle: `video-izle` skill'i sahne karelerini, kare üstü yazıyı ve transkripti çıkarır; kusur yazmadan önce o saniyenin karesi açılır. `qa/sheet.jpg`, `qa/report.json` özeti, `brief.md`, stüdyo `CLAUDE.md`, timeline'ın yalnız overlay listesi. Şüpheli aralık: `vedit sheet renders/preview.mp4 --start 6 --dur 4 --grid 4x2` ya da `vedit still renders/preview.mp4 7.2 --width 720`. Videoyu kare kare okuma.

## 3. Rubrik (1–10, tek satır gerekçe)
1. Hikâye netliği (hedef anlaşılıyor, hook ilk 3 sn)
2. Ritim (ölü zaman yok, değişim sıklığı formata uygun, büyük andan önce nefes)
3. Easing ve hareket (işe göre, elastik yok, çıkış kısa)
4. Tipografi (boyut, ağırlık, ≤ 2 font, TR glif)
5. Hiyerarşi (tek fikir, vurgu doğru kelimede)
6. Kompozisyon (güvenli alan, yüz/ürün açık, denge)
7. Geçiş sürekliliği (aileler tutarlı)
8. Renk (palet, tek accent, kontrast, çekimler arası tutarlılık)
9. Okunabilirlik (≥ 1.2 sn, sessizde anlaşılır)
10. Ses (konuşma net, müzik altta, SFX olaya bağlı)
11. Özgünlük ve akılda kalan an (imza anı teslim edildi mi, şablon gibi mi)
12. Brif uyumu (tez, enerji eğrisi, yasak klişe; yaratıcı brif yoksa bu madde atlanır)

Ayrıca zaman damgalı: "AI şablonu" anları, aceleye gelen anlar, ölü zaman (> 0.5 sn). Ortalama ve aşağıdaki "hâlâ < 8" kuralı 12 madde üzerinden çalışır (brif yoksa 11 madde).

## 4. Düzeltme listesi (`qa/critique.md`)
```
Tur 1 · Ortalama 7.4 · En düşük: Ritim 6, Tipografi 6
P0  00:02.1  hook metni yüze biniyor → overlays[hook].props.position = "top"
P1  00:06.8  zoom geç → video[scr1].keys[1].t 0.6 → 0.3
P1  00:11.0–12.4 ölü zaman → product-card start 10.3 → 11.2
```
- P0 yayınlanamaz (okunmuyor, yanlış bilgi, ses) · P1 profesyonellik farkı · P2 zevk.
- Her madde tek alanlık değişiklik (yol + eski → yeni); N kare = N/fps sn.
- P0+P1 uygula → `validate` → `build` → `render preview` → `qa` → tur 2. En fazla 2 tur; hâlâ < 8 varsa kararı kullanıcıya bırak.

## 5. Ders kaydı
Aynı hata iki projede tekrarlanırsa kalıcı çöz (blok varsayılanı, stil token'ı ya da skill kuralı) ve `wiki/log.md`'ye `code` kaydı düş.


## 6. Düzeltme defteri ve klişe testi (ADR 0014)
- Kontrol kareleri `library/checks.md` kurallarına göre denetlenir.
- Animasyon ve motion işlerinde `sanat-yonetimi` klişe testi uygulanır: 0., 1., 3., 6., 10. saniye ve son kare, `sanat-yonetimi/references/klise-listesi.md`. Puanı `qa/critique.md`'ye yaz.
- Altyazı karesinde okunan kelime turuncu, gerisi beyaz, kontur siyah mı bak. `vedit qa` stil dışını uyarır.

## 7. AI slop ve etki ekseni (ADR 0015, 0064)
Bu denetim temizlendikten sonra slop adımı çalışır: `references/slop.md`. "AI şablonu" anları ayrıntısıyla orada aranır; burada yalnız rubrik puanı verilir.

Kalite kontrol çıktısında "doğru ama sıradan" kurguyu yakalamak için `etki` bulgu kategorisi ve `uretim_puani` alanı kullanılır:
- **`etki` kategorisi:** sıradanlık, imza anının teslim edilmemesi, enerji eğrisinin hissedilmemesi, yasak klişe kullanımı ya da zayıf hook durumlarında açılır. Her `etki` bulgusu zaman damgası, kare kanıtı ve brif maddesine bağlı somut bir `beklenen` ölçütü taşır; kanıtsız zevk tartışması triyajda reddedilir.
- **`uretim_puani`:** `{"hook": 1-5, "imza_ani": 1-5, "brif_uyumu": 1-5, "ozgunluk": 1-5, "ritim_enerji": 1-5}` biçiminde isteğe bağlı üretim puanı verir (eksik anahtar serbesttir).

## 8. Teslim kodlaması ve ölçüm (ADR 0016)
Onaydan sonra son adım `vedit teslim <video> --platform <youtube|reels|ugc> -o <çıktı>`. Renk ya da piksel biçimi hatası teslimi durdurur; düşük bitrate uyarısında karede detay kaybına bak. Ölçüm çıktısı uzunsa `render-qc` ajanına ver. Ses denetimi `sound-design` skill'indeki earshot bölümündedir.
