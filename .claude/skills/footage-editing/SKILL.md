---
name: footage-editing
description: Gerçek çekim kurgusu — konuşan kafa, UGC, ekran kaydı. Take seçimi, dolgu/sessizlik temizliği, hook'u öne alma, kelime sınırında kesim, J/L cut, punch-in ile jump cut gizleme, B-roll/ekran kaydı yerleşimi, tempo. digest.txt'den edl.json yazarken ya da timeline'a B-roll/punch-in eklerken kullan.
---

# Çekim kurgusu

Kesim, ritim, zoom ve geçiş kararlarında üst kural: `usta-editor`. Her zoom/geçiş `edit/olaylar.json`'a yazılır (`sound-design`).

Girdi: `analysis/digest.txt`, `analysis/sheets/*.jpg`, `brief.md`, `studios/<s>/CLAUDE.md`. Çıktı: `edit/edl.json` + `edit/edit-notes.md`. Şema: `video/references/timeline.md`.

İlk geçiş için `yt-edit`: `python -X utf8 .claude/skills/yt-edit/deadair.py analysis/transcript.json` (ölü boşluk, TR/EN dolgu, tekrar take; yalnız öneri).

## Digest okuma
- `S012 00:41.2–00:44.0 metin`: zamanlar kaynak saniyesi.
- `↻ S015 ile %88 benzer`: muhtemel kötü take; genelde son tekrar en iyisi. Akıcı olanı seç, ikisini birden alma.
- `[dolgu: ıı×2]`: segmenti bölerek dolguyu at; cümle başındaysa in'i sonraki kelimeye kaydır (kelime zamanı transcript_cut'tan).
- `~1.3s`: sessizlik; kurguda 0.15–0.3 sn'ye iner (pay otomatik).
- `[düşük güven]`: kontak sayfasına/sese bak, gerekirse at.

## Kesim kuralları
1. Hook ilk 3 sn'de; en güçlü cümle sonda bile olsa başa al (EDL sırası serbest).
2. Kelime sınırında, nefeste kes; `vedit cut` yaslar, sen segment düzeyinde düşün.
3. Boşluk: UGC/Reels 0.1–0.25 sn, YouTube 0.25–0.5 sn; önemli cümleden sonra 0.5–0.8 sn olabilir.
4. Dolgu, tekrar, yanlış başlangıç, meta konuşma ("şimdi şunu söyleyeceğim") atılır.
5. Bir sonucu atıyorsan ona işaret eden önceki cümleyi de at.
6. Hedef `studio.yaml → target_duration`; fazlaysa önce en zayıf kanıt / tekrar eden fayda gider.

## Görsel çeşitlilik (timeline)
- **Jump cut:** aynı açıdan art arda iki segmentte ikincide punch-in (%112–118, `dur: 0`), sonra %100; üç kez üst üste aynı ölçek yok.
- **B-roll:** "bu ürün", "şuna bakın", "sonuç" anında; UGC 2–4 sn, YouTube 4–8 sn; A-roll sesi sürer (L-cut), geçişte swoosh (otomatik).
- **B-roll yeri (ADR 0040, motion-graphics):** her grafik için üç seçenekten biri seçilir ve nedeni yazılır: tam kare ara görüntü (söz tamamen o şeyi anlatıyorsa), konuşmacının yanındaki boşlukta saydam panel (söz sürerken destek), hiçbiri (yüz ve duygu önemliyse). Gerçek rakam verilmediyse grafik uydurmaz: göreli boy ve iskelet çizgi.
- **Ekran kaydı:** anlatılan öğeye 0.5–0.7 sn zoom + `callout`; tıklamada click/tap SFX; 2 sn'den uzun statik ekran yok.
- **Dikey:** yatay kaynakta `vedit reframe`; ekran kaydı `layout: top-half` (konuşmacı altta) ya da `card`.
- **Renk:** kaynaklar arası belirgin fark notlara; ton eşleme manuel (HyperFrames `media-treatment` / LUT).

## J/L cut
- **L-cut:** görüntü B-roll'a geçer, konuşma sürer (B-roll üst katmanda). En doğal geçiş.
- **J-cut:** sonraki sesin önce başlaması; EDL'de önceki out'u uzat, görüntüyü B-roll ile kapat.

## edit-notes.md (≤ 25 satır)
```
Süre: 41.8s (hedef 30–45) · Atılan: S001–S003 (kötü take), S011 (tekrar)
Hook: S007 başa alındı — "…"
B-roll: 6.8–10.2 ekran kaydı (zoom: buton) · 12.0 ürün close-up
Overlay: 0.0 kinetic-text "…" · 10.3 product-card · son 3 sn cta
Riskler: S009 ses patlaması (düşük güven) · S004 ışık farklı
```

## Kontrol
- [ ] İlk 3 sn hook, hedef süre içinde, kötü take ve dolgu yok
- [ ] Cümle ortasından kesim yok, anlam bütün
- [ ] Jump cut'lar kapatıldı; kısa formatta 3 sn'den uzun değişimsiz an yok


## Kesim denetimi (ADR 0014)
- Aday kesim, onaylı planın üstüne yazılmaz; ayrı dosyada kalır.
- Dışa aktarımdan sonra `vedit kesimqa <video>` çalıştır: duyulan metin beklenen metinle karşılaştırılır, eksik ve tekrar eden kelimeler kesim kenarı işaretiyle listelenir. OpenMontage işinde `--beklenen senaryo.txt` ver.
- Rapor ipucudur. Kelimenin ilk ve son sesini kesim yerinde dinlemeden onay verme.

## Kesim noktası ve tekrar çekim (claude-video-edit, ADR 0016)
- Whisper kelime sonu 0,1-0,4 sn kayabilir. Elle seçilen kesimi enerji zarfına göre doğrula; kelime sonundaki t, k, p, ç patlamasını kesme.
- Boşluğu 0,2 sn altında olan iki kelimenin arasından kesme; cümleyi doğal sonuna kadar bırak.
- Tekrar çekimleri görmek için kaydı önce sessizlikten böl, parçaları ayrı yazıya dök. Tüm dosyada Whisper tekrarları birleştirir.
- Sessiz ama görünen donma anlarını sesle bulamazsın; kare farkına bak ya da kullanıcıya sor.
