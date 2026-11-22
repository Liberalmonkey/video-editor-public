---
type: decision
title: "AI edit: Final öncesi kurguyu ajan yazar, vedit doğrular ve render eder"
status: accepted
tags: [adr, ai-edit, kurgu, studio, ajan, antigravity, claude-code, codex, opencode]
created: 2026-11-12
updated: 2026-11-15
sources: []
---

# ADR: AI edit

## Bağlam
Kullanıcı Video Stüdyo'da projeye malzeme koyup "Final başlat"a bastı; iş bir süre çalıştı ama video editlenmedi (2026-11-12). Neden: Final düğmesi yalnız `vedit final` çalıştırıyordu ve bu komut mevcut `kurgu.json`'ı olduğu gibi render ediyor. Kurguyu yazan adım yalnız terminal oturumunda, ajanın elle yürüttüğü `uretim-hatti` içindeydi; arayüzde karşılığı yoktu. Örnek projede `kurgu.json` yedi ham klibi arka arkaya tutuyordu, `kelimeler` boştu (altyazı çıkmadı), kesim, vurgu ve ses yoktu.

## Seçenekler
- AI panelinden serbest istek ([[0026-arayuzde-ajan]]). Headless ajan kabuk komutu çalıştıramadığı için `hazirla` ve `taslak` adımları eksik kalıyor; kullanıcı ne yazacağını bilmek zorunda.
- Ajanı komut izniyle (`--dangerously-skip-permissions`) çalıştırmak. Arayüzden izin atlatma [[0026-arayuzde-ajan]] ile reddedilmişti.
- Tek komut: ölçüm ve render'ı `vedit` yapar, ajan yalnız `kurgu.json` yazar. Seçilen.

## Karar
| Konu | Karar | Neden |
|---|---|---|
| Komut | `vedit ai-edit <proje> [--motor claude\|antigravity\|codex\|opencode] [--model] [--stil] [--not] [--final]` | Terminal hattı sürer ([[0020-panel-kaldirildi]]); Stüdyo aynı komutu iş kuyruğunda çalıştırır. Motor tablosu `motorlar.py` (2026-11-17, [[0026-arayuzde-ajan]]) |
| İş bölümü | `vedit`: `hazirla`, kelimelerin kurguya yazılması, sessizlik adayları, doğrulama, `taslak`, `final`. Ajan: yalnız `kurgu.json` ve `ai-edit.rapor.md` | Headless ajanda komut izni yok; ölçüm ve render deterministik kalır |
| İstek | `work/edit/ai-edit.istek.md`: `usta-editor`, `viral-kurgu`, `footage-editing`, `sound-design`, `checks.md`, `kit.json`, digest, kontak sayfaları, seçili stil ([[0029-stil-paneli]]), kurgu şeması | Kurallar tek yerde; ajana yalnız dosya yolu gider (komut satırı sınırı) |
| Doğrulama | Şema (`Kurgu`) + `kurgu.denetle`; hata varsa aynı oturumda bir düzeltme turu, yine bozuksa eski kurgu geri yüklenir | Bozuk kurgu render'a girmez |
| Sessiz başarısızlık | Klipler değişmediyse çıkış kodu 1, "AI edit yapmadı" | Bildirilen sorunun tekrarını önler |
| Geri alma | Eski sürüm `kurgu-gecmis/` altına girer, `rev` artar | Stüdyo'nun mevcut geçmiş düzeni ([[0021-video-studyo-nle]]) |
| Arayüz | İşler panelinde "AI Edit" düğmesi; Final diyaloğunda varsayılan açık "Önce AI ile profesyonel edit yap" | Kullanıcı Final'e basınca edit bekliyor |
| Sabitler | Altyazı [[0014-altyazi-standardi-ve-repo-entegrasyonu\|ADR 0014]] (stil `null`), girdilere dokunulmaz, kütüphane dışı kaynak yazılmaz | Proje sabitleri ajan isteğinde tekrar edilir |

## Sonuçlar
- Motor ve model AI panelindeki seçimden gelir; iş kuyruğu beyaz listesi (`ajan_bayraklari`) ikisini de `ajan._durum()` listesiyle doğrular.
- İlk sonuç taslaktır; kullanıcı Stüdyo'da düzeltir, sonra Final'i AI kutusu kapalı çalıştırır. Kutu açık kalırsa AI kurguyu yeniden yazar.
- Edit kalitesi modele bağlıdır; denetim ([[0015-ai-slop-denetimi\|ADR 0015]]) final sonunda yine çalışır.

> [!note] Güncellendi 2026-11-15
> Kullanıcı Kurgu sayfasında isteği yazıp stili adıyla anarak "AI ile editle" demek istedi; AI Edit İşler menüsünde gizliydi ve stil seçtirmiyordu.
>
> | Konu | Karar | Neden |
> |---|---|---|
> | Arayüz | AI panelinde stil, motion yoğunluğu, kapsam ve teslim seçimi ile **AI ile editle** düğmesi; istek `--not` olarak gider. İstekte geçen stil adı seçiciyi kendiliğinden ayarlar. İşler menüsündeki öğe paneli açar, eski diyalog kalktı | Tek yol; serbest sohbet ("Gönder") ayrı kalır ([[0026-arayuzde-ajan]]) |
> | Aralık | `--aralik BAS SON`: ajan yalnız o sekans aralığını düzeltir. `aiedit._aralik_disi` öncesindeki klipleri birebir, sonrasındakileri yalnız tek tip `bas` kaymasıyla aynı ister; değilse bir düzeltme turu, sonra eski kurgu | Tek bölümü düzeltmek bütün kurguyu yeniden yazdırmasın. Yoğunluk turu aralıkta çalışmaz (aralık dışına grafik ekletirdi) |
> | Önce/sonra | `work/edit/ai-edit.ozet.json` (rev, klip, süre); `GET /api/kurgu/{s}/{a}/ai-ozet`, `POST /api/kurgu/{s}/{a}/geri/{rev}` önceki sürümü `kurgu-gecmis/` altından geri yazar | Geçmiş vardı ama arayüzde görünmüyordu |
> | Videosuz proje | Girdi yalnız seslendirmeyse ses `A1` izinde konuşma klibi olur (altyazı ve zamanlama ondan); yalnız `senaryo.md` varsa `hazirla` atlanır. İsteğe "Animasyon Modu" ve `sahne-motoru` kuralı eklenir: `V1`i ajan sahne, görsel ve tam kare şablonla doldurur | youtube-animasyon projesinde konuşmacı videosu yok; önceki akış girdi videosu bekliyordu |
>
> Not sınırı 800'den 2000 karaktere çıktı. Videosuz mod birim testle doğrulandı; gerçek bir animasyon projesinde uçtan uca render denenmedi.

## İlgili kod
- `src/vedit/aiedit.py`, `src/vedit/ajan_cagri.py`, `src/vedit/cli.py` (`cmd_ai_edit`)
- `src/vedit/studio/isler.py` (`ajan_bayraklari`), `src/vedit/studio/app.py` (`ai_ozet`, `kurgu_geri`), `studio/web/src/paneller/AjanPaneli.tsx`
- Testler: `tests/test_aiedit.py`, `tests/test_studio_dosya.py`, `tests/test_studio_kurgu_api.py`, `studio/web/src/paneller/AjanPaneli.test.ts`
