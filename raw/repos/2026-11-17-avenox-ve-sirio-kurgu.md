# Avenox kurgu notları ve Sirio kurgu sistemi (2026-11-17)

Kullanıcı iki repo verdi: "faydalı bulduğun kısımları projede kullan".

| Repo | Commit | Lisans | Durum |
|---|---|---|---|
| https://github.com/avenoxai/avenox-video-kurgu-notlari | depth 1 klon, 2026-11-17 | MIT, Copyright (c) 2026 Avenox | Fikirler alındı, metin ve kod kopyalanmadı |
| https://github.com/sirioberati/YouTube-AI-Video-Editing-System | 616028d (2026-10-21) | MIT, Copyright (c) 2026 Sirio Berati | 2026-11-03'te aynı commit alınmıştı; yeni commit yok |

## Avenox: içerik
- `skill/ajanla-video-kurgu/`: SKILL.md, 10 referans (atölye, pano haritası, orkestrasyon, kapılar, marka kilidi, ses ve transkript, üretim, kısa form, pahalı dersler, başlangıç kiti), 6 şablon (beğenmeme defteri, bölüm brief'i, marka, pano haritası, prompt sözleşmesi, teslim formu).
- `notlar/`: YouTube videosunun (BAn-6Cu-cCM) bölüm özeti ve tam transkripti.
- Pano haritası ve kapı fikrini kendisi Sirio'nun sistemine bağlıyor.

## Avenox: projede karşılığı olanlar (alınmadı, zaten var)
- Üç hat ve istasyon sırası: `uretim-hatti` (hazirla, kes, taslak, final).
- Hareket yoğunluğu hedefi (10 sn'de 10-10,5 hareket): `kurgu.YOGUNLUK` ve `motion_yogunlugu`, ai-edit "görsel durum her 2-4 sn değişsin".
- Ses-görüntü kayma kapısı: `vedit senkron` (ADR 0039).
- Ses zinciri (80 Hz, gürültü, kompresör, -14 LUFS): `audio.py`, `vedit miks`, `earshot`.
- Kapak yazısını kod dizer: `vedit kapak` (ADR 0027).
- Beğenmeme defteri: `library/checks.md`.
- Tek şef, dosya sözleşmesi, teslim: ADR 0037 orkestra, çıktı `work/agy/`.
- Render tek sırada: Stüdyo iş kuyruğu tek işçi.
- Kesimden sonra kesime dokunulmaz: ai-edit `--aralik` kuralı.

## Avenox: alınanlar
- Pano haritası sorusu "yalnız dinleyen anlar mı?" ve logo/kaynak kuralı: ai-edit motion kuralları.
- Transkript düzeltme sözlüğü (Whisper "Claude"/"cloud"): `library/sozluk.json`, `src/vedit/sozluk.py`.
- Yasak listesinden ölçülebilen kalem, ekran yazısında emoji: `kurgu_kalite` `YAZI_EMOJI`.
- "Aynı hata iki kez olursa koda yaz": `library/checks.md` kapı kuralı.

## Avenox: alınmayanlar
- Topview, Seedance, GPT Image ve video modeli kıyası: ücretli üretim, proje bütçesi 0 USD.
- Kısa form kesit hattı ve paylaşım takvimi: ayrı özellik, kullanıcı isterse.
- Karakter kilidi ve göz rengi hex satırı: proje karakteri kodla çizer (`library/karakter/`); Flow avatar kullanıcıda.

## Sirio: 2026-11-03'te alınmayan parçalar yeniden değerlendirildi
- `ingest_sync.py` (kamera saati = mikrofon × (1+a) + b), `assemble_cut.py` (çok çekimli aday kesim): kullanıcı çekim yapmıyor, konuşmacı Flow avatarı. Alınmadı.
- `render_boards.py`, `qa_cut.py`, `qa_edges.py`: karşılıkları `vedit pano`, `vedit kesimqa`.
