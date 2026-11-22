---
type: decision
title: "Avenox kurgu dersleri: pano haritası sorusu, transkript sözlüğü, emoji uyarısı, kapı kuralı"
status: accepted
tags: [adr, kurgu, transkript, kalite, ai-edit]
created: 2026-11-17
updated: 2026-11-20
sources: ["[[2026-11-17-avenox-kurgu-notlari]]", "[[2026-11-03-sirio-berati-repolari]]"]
---

# ADR: Avenox kurgu dersleri

> [!note] Güncellendi 2026-11-20: kurallar artık `library/kurallar/kurallar.json` deposundadır, checks.md ondan üretilir; tekrar >= 2 ve ölçülebilir kural kapı önerisi olur ([[0047-kural-deposu]]).

## Bağlam
Kullanıcı iki repo verdi (2026-11-17): Avenox'un ajanla kurgu notları ve Sirio Berati'nin YouTube-AI-Video-Editing-System'i. Sirio reposu 2026-11-03'te aynı commit'te alınmıştı ([[0014-altyazi-standardi-ve-repo-entegrasyonu]]); yeni bir şey yok. Avenox'un derslerinin çoğunun projede karşılığı var: yoğunluk hedefi `kurgu.YOGUNLUK`, ses-görüntü kapısı `vedit senkron` ([[0039-fizik-ritim-galeri]]), kapak kodla ([[0027-kapak-sayfasi]]), düzeltme defteri `library/checks.md`.

## Seçenekler
| Seçenek | Artı | Eksi |
|---|---|---|
| Avenox skill'ini olduğu gibi kur | Hızlı | Projedeki hatla (uretim-hatti, ai-edit) çakışır; ikinci hat kurar |
| Yalnız eksik dersleri koda ve kurala çevir | Tek hat kalır, ölçülür | Elle seçim ister |

## Karar
| Ders | Projede | Neden |
|---|---|---|
| Pano haritası: "yalnız dinleyen anlar mı?" | ai-edit `MOTION_KURALLARI` | Yoğunluk hedefi grafik sayısını artırıyor; bu soru grafiğin konuşmayı tekrar etmesini önler |
| Logo ve kaynak kuralı | ai-edit `MOTION_KURALLARI` | checks.md "uydurma" diyordu; resmi logo ve birebir alıntı açık yazıldı |
| Transkript düzeltme sözlüğü | `library/sozluk.json`, `src/vedit/sozluk.py`, `hizli.yazi` | Altyazı, kesim ve grafik zamanı transkriptten çıkar; ad hatası her videoda geri gelir |
| Ekran yazısında emoji | `kurgu_kalite` `YAZI_EMOJI` (P2 uyarı) | Yasak listesinin ölçülebilen kalemi; palet ve parlama `slop` ölçümünde |
| Aynı düzeltme iki kez: koda yaz | `library/checks.md` kapı kuralı, CLAUDE.md | Not modelin hatırlamasına bağlı, kod değil |

Sözlük ayrıntısı: `isimler` Whisper'a `initial_prompt` olur (`--prompt` verilirse o kazanır). `duzelt` çok kelimeli olabilir; birleşen kelimeler ilkinin başından sonuncunun sonuna uzanır, güven en düşüğü alır. Ham transkript önbellekte değişmez; sözlük her okumada uygulanır, güncellenince yeniden transkript gerekmez. Tek başına gerçek kelime olan anahtar (yalnız "cloud") konmaz; test bunu denetler.

## Sonuçlar
- Alınmayanlar: ücretli görsel/video üretimi ve model kıyası (bütçe 0 USD), kısa form kesit hattı ve paylaşım takvimi (ayrı özellik), Sirio'nun çok çekimli kesim ve kamera kayma araçları (kullanıcı çekim yapmıyor). Ayrıntı ham kayıtta.
- Emoji aralığı tipografik işaretleri (✓, oklar) saymaz.

## İlgili kod
- `src/vedit/sozluk.py`, `library/sozluk.json`, `src/vedit/hizli.py` (`yazi`)
- `src/vedit/kurgu_kalite.py`, `src/vedit/aiedit.py` (`MOTION_KURALLARI`)
- `tests/test_sozluk.py`, `tests/test_kalite.py`
