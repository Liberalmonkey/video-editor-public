---
disable-model-invocation: true
name: directing
description: Yönetmenlik — referanslardan stil grameri, sahne listesi (scenes.json), çekim kurgusu tretmanı, çekim öncesi plan (ışık, ses, kamera, kadraj, ekran kaydı, B-roll). Çekim planı, sahne listesi, stil grameri ya da kadraj/ışık/ses tavsiyesi gerektiğinde kullan.
---

# Yönetmenlik

Çıktılar: `studios/<s>/references/style-grammar.md` (bir kez, tekrar kullanılır) · `direction/scenes.json` (animasyon) ya da `direction/treatment.md` (çekim) · `direction/shoot-plan.md` (çekimden önce).

## 1. Stil grameri
Girdi: `vedit reference` çıktısı (`digest.md`, `sheet.jpg`, `hook.jpg`, görsel ızgarası); ham video izlenmez. Her bölüm 2–5 ölçülebilir madde:
- **Tempo:** kesim/dk, ortalama çekim süresi, ilk 30 sn kesim sayısı (digest'ten aynen).
- **Kadraj:** yakın/orta/geniş oranı, konuşmacı konumu, B-roll oranı.
- **Metin:** miktar, parça uzunluğu, harf durumu, konum.
- **Renk/ışık:** sıcak/soğuk, kontrast, palet (hex), grain.
- **Hareket:** zoom/punch sıklığı, geçiş türleri, easing karakteri.
- **Ses:** müzik tipi/BPM hissi, SFX yoğunluğu.
- **Alınacak / alınmayacak:** gramer alınır, içerik kopyalanmaz.

Sonra `style-pack` → `styles/<ad>/tokens.json` + STYLE.md + MOTION.md.

## 2. Sahne listesi — `direction/scenes.json`
Şema: `video/references/timeline.md`; katalog: `vedit blocks --tag animation`.
- Her sahne: tek iş (`intent`), görsel fikir (`visual`), `vo_from` (senaryodan birebir 4–7 kelime), bloklar, giriş geçişi, karmaşıklık (block/custom/hero).
- Eğitici 4–8 sn/sahne; hero %10–20 (maliyet); uzun formatta her bölüm `chapter-card` ile açılır.
- `motion_language` ve 2–3 `transition_families` tüm videoda sabit.
- Her 30–60 sn pattern interrupt (stat, compare, flow, image, hero).
- Önce kullanıcıya bölüm başına 2–3 satır özet, onay; sonra align.

## 3. Çekim tretmanı — `direction/treatment.md`
edl onayından sonra: overlay listesi (zaman, blok, metin), B-roll/ekran kaydı yerleşimi, punch-in ritmi, renk notu. Editor timeline'a çevirir; kısa projede doğrudan timeline yazılabilir.

## 4. Çekim planı — `direction/shoot-plan.md`
Tek kişi, telefon/kamera varsayımıyla pratik yaz.
- **Işık:** pencere/softbox yüze 30–45°, göz hizasının biraz üstü; arka/pratik ışıkla ayrışma; tavan ışığı kapalı; renk sıcaklığı karışmaz; pozlama yüze kilitli (AE/AF).
- **Ses (en kritik):** yaka mikrofonu ağızdan 15–20 cm ya da telefon ≤ 50 cm; yumuşak eşyalı oda; klima/buzdolabı/fan kapalı; her çekim öncesi 3 sn oda sesi.
- **Kamera:** göz hizası; 9:16'da göğüsten yukarı, gözler üst üçte birde; 4K/1080p 30 fps; temiz lens, tripod.
- **Performans:** hatada cümleyi baştan tekrar (tekrarları sistem atar); hook'u 3 şekilde çek; enerji normalin %20 üstü.
- **B-roll:** ürün close-up (kutu açma, kullanım, detay, sonuç), el hareketi, ortam; 3–5 sn, sabit ya da yavaş.
- **Ekran kaydı:** 1080p+ 60 fps, bildirimler kapalı, büyük imleç, temiz masaüstü, tarayıcı zoom %125, tıklamadan önce 1 sn bekle.
- **Dosya adları:** `hook-1.mp4`, `demo-ekran.mp4`, `broll-urun-01.mp4` (`vedit ingest` ekran kaydını adından tanır).

## Kontrol
- [ ] Gramer ölçülebilir, içerik kopyası yok
- [ ] Her sahnenin tek işi var, `vo_from` birebir, hero oranı makul
- [ ] Çekim planı brief'teki ekipmana uygun
