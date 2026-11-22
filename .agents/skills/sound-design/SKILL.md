---
name: sound-design
description: Ses tasarımı ve miks — SFX seçimi/yerleştirme, müzik seçimi ve ducking, loudness, kullanıcıya indirme listesi (Pixabay, Mixkit, Bensound, NCS, Uppbeat, Audio Library) ve CC0 kütüphane. SFX ipuçları eklerken, müzik seçerken, ses kütüphanesini büyütürken ya da miks sorunlarında kullan.
---

# Ses tasarımı

Strateji: `wiki/decisions/0004-ses-efekti-stratejisi.md`, `wiki/concepts/sfx-stratejisi.md`, `wiki/concepts/loudness-standartlari.md`.

## Akış
1. `vedit sfx cues`: kural tabanlı ipuçları (başlık → whoosh, kinetic-text/product-card → pop, cta → pop + click, madde → tick/click/pop, B-roll → swoosh, bölüm → whoosh). `auto: false` olanlar korunur.
2. `vedit sfx suggest`: transkriptteki ses olayları ("telefonum çaldı" → phone_ring, "tıkla" → click, "yazıyorum" → typing, "satış" → cash).
3. **Ana oturum:** yalnız `audio/sfx_suggestions.txt`, `vedit sfx catalog` ve `audio.sfx` okunur; anlamsal ipucu ekle, gereksiz otomatikleri sil, müzik seç.
4. `vedit sfx resolve`: dosya seçer, tekrarlamaz, peak'i hizalar, yoksa sentezler.
5. `vedit mix` → `vedit qa` loudness.

## SFX kuralları
- Her ses ekranda görünen ya da söylenen bir olaya bağlı; boşluk doldurmak için ses yok.
- Yoğunluk ≤ 1 / 0.4 sn; kısa format ~4–8 / 15 sn, uzun format 6–15 / dk.
- Seviye: soft −9 dB (UI, metin, B-roll) · medium −5 dB (vurgu, bölüm) · hard −1.5 dB (tek büyük an). Konuşmayı asla bastırmaz.
- Riser reveal'den 1–2 sn önce başlar, `t` = reveal; ardından impact ya da sessizlik.
- Aynı whoosh 6 kezden fazla duyulursa kütüphaneyi büyüt.
- **Geçişte whoosh yorgunluğu (ADR 0040, opus-video-skills):** kesimlerin yaklaşık yarısı sessiz kalır; onları vuruş ve gelen planın kendi giriş sesi taşır. Aynı ipucu art arda iki kez çalmaz. Gürültü kuyruklu sert darbe videoda yaklaşık beş yapısal ana ayrılır, diğerleri yumuşak darbe.
- **Parlaklık (ADR 0040):** `library/sfx/manifest.json` her seste `parlak` (0-1, 4 kHz üstü enerji × süre) taşır. Tık, klavye, kesme gibi tekrarlanan roller 0,25 üstünü seçmez (`olaysesi`); cızırtılı ses tekrarlandıkça kulağı yorar. Tek seferlik vurguda parlak ses serbest.
- UGC'de "cartoon" SFX yok; eğlenceli YouTube/Reels'te dozunda.

İpucu: `{"id": "s-ring", "t": 12.40, "type": "phone_ring", "intensity": "medium", "reason": "'telefonum çaldı' (12.4s)"}`
Türler: whoosh, swoosh, pop, click, tap, tick, impact, riser, riser-short, ding, notification, success, error, phone_ring, vibrate, typing, camera_shutter, cash, glitch, page_turn, switch, foley (+ casino, digital, rpg paketleri).

## Çalışma biçimi (eski `sound` ajanı)
Sesi duyamaz, ölçersin: nasıl duyulduğunu ölçümsüz söyleme, rakamı yaz, son kararı kullanıcının kulağına bırak. Dolu `kit.json` rolünü değiştirme, `locked` varlığa dokunma; ham ses ve büyük JSON okuma, `python -c` ile süz.
- **Olay:** `olaylar.json` → `vedit olaysesi`; düşen ve eksik sesleri bildir.
- **Seçim:** adaylar arasından `earshot rank`, `find`, `ab`; z ve hüküm değerini yaz.
- **Denetim:** son videoda `earshot measure`, `timeline --cues`, gerekirse `sheet`. Kaçan vuruşu zaman damgasıyla listele, onaysız düzeltme.
- **Kütüphane:** `vedit sfx fetch …` ya da `earshot sfx render` → `library/sfx/raw/<kaynak>/` + `source.json` → `vedit sfx index`. Lisansı belirsiz kaynak ve `source.json`'suz dosya ekleme. SFX yoğunluğu ≤ 1/0.4 sn, `auto: false` ve `reason` dolu.
- **Rapor:** seçilen sesler (zaman · id · neden), LUFS / dBTP / LRA, kaçan vuruşlar, kulakla dinlenecek zaman damgaları, ölçülemeyenler.

## Zoom, kesme ve geçiş sesi (`vedit olaysesi`)
Varsayılan edit hattı OpenMontage dahil her motorun çıktısına ses ekler. Karar kuralları `usta-editor`.
```json
{ "video": "renders/ham.mp4", "fps": 30, "studyo": "youtube-animasyon",
  "ses": [{ "src": "malzeme/ses/S01.wav", "start": 0 }],
  "muzik": [{ "src": "library/music/pixabay/M1-tech-upbeat.mp3", "gain_db": -14, "duck": true }],
  "olaylar": [
    { "t": 12.4, "tur": "zoom_in", "sure": 0.5 },
    { "kare": 402, "tur": "zoom_out", "sure": 0.4 },
    { "t": 31.0, "tur": "gecis", "sure": 0.5, "guc": "medium" },
    { "t": 40.2, "tur": "kesme" },
    { "t": 58.0, "tur": "vurgu", "guc": "hard", "not": "büyük sayı" }
  ] }
```
- Zaman: `t` saniye ya da `kare`. `sure` hareketin uzunluğudur; ses buna göre seçilir ve kırpılır.
- Türler: zoom_in, zoom_out, punch_in, kesme, gecis, hizli_gecis, slayt, bolum, riser, vurgu, tik, klavye, pop, bildirim, basari, hata, para, sayac, deklansor, sayfa. Özel ses: `"dosya"`. Susturma: `"sessiz": true`.
- `kesme` ve `punch_in` varsayılan sessizdir; `guc: medium` ile duyulur.
- Yerleşim: zoom_in tepesi varışta, zoom_out başta, geçiş kesme karesinde. Yön gerekirse örnek ters çevrilir. Çakışmada güçlü olan kalır (`--min-aralik`, varsayılan 0.4 sn).
- `ses` yoksa videonun kendi sesi konuşma kabul edilir. Konuşma üstünde efekt −4 dB. Vuruş öncesi müzik çekilir: `orta` 150 ms önce −3 dB, `sert` 250 ms önce −6 dB, vuruşta açılır.
- Güç: `yumusak`, `orta`, `sert` (eski `soft`, `medium`, `hard` de geçer). Perde ±%3 ve seviye ±1 dB olaydan tohumlu oynar; her seste kısa baş ve kuyruk fade'i var.
- Kombolar (ADR 0032), tek olay sayılır: `gecis_guclu` (whoosh + kesme karesinde kısa sub, bölüm ya da sahne değişimi), `vurgu_guclu` (darbe + kısa ters whoosh, büyük sayı ya da punchline), `acilis` (riser + sub, açılış ya da tek büyük reveal). Videoda birkaç kez kullan; sıradan kesme ve UI için tek rol yeter.
- Rol sabitleme: `library/kit.json` içinde `zoom_in`, `zoom_out`, `gecis` rollerine ata; rol doluysa o ses kullanılır.
- Çıktı: `-o` mp4, `<olaylar>.master.wav`, `<olaylar>.rapor.json` (yerleşen, düşen, sessiz, uyarılar). −14 LUFS / −1 dBTP.
- Eksik ses türleri ve arama terimleri: `library/sfx/INDIRME-LISTESI.md`.

## Müzik
- Kullanıcı indirir; eksikler `direction/assets-request.md` (format: `video/references/asset-request.md`).
- Pixabay, Mixkit: atıfsız, UGC/reklam için ilk tercih. Bensound, NCS, Uppbeat, Audio Library: atıf zorunlu (metin birebir → manifest `attribution` → `credits.txt`); ücretli reklamda kullanılmaz.
- Kayıt: `library/music/<site>/<ID>-<ad>.mp3` + `manifest.json` (id, file, title, mood, genre, bpm, energy, vocals, duration_s, license, source_url, attribution). Lisansı boş müzik kullanılmaz.
- Seçim: UGC hafif/pozitif 95–120 BPM vokalsiz · eğitici YouTube sakin, ritmik · Reels enerjik. Konuşma varsa `duck: true`, `gain_db` −12…−16.
- Beat senkronu: `node_modules/.bin/hyperframes beats <dosya>`; geçişler downbeat'e yakın.

## Kütüphane
- Büyütme: `vedit sfx fetch kenney|remotion`, `fetch freesound <q>` (FREESOUND_API_KEY, yalnız CC0), `fetch openverse <q>`, `vedit sfx synth` → `vedit sfx index`.
- Kullanıcı sesleri: `library/sfx/raw/<site>/` (`source.json` hazır; dosya bazlı `"files": {"S3-klavye.wav": {"category": "typing", "tags": ["mekanik"]}}`). Kendi kaydı: `raw/user/<paket>/` + `source.json`.
- Önce `vedit sfx search`; yalnız eksikleri iste.
- Yasak: BBC SFX, CC-BY-NC, @remotion/sfx meme sesleri, MMAudio/AudioGen çıktıları.

## Miks
- Teslim −14 LUFS, ≤ −1 dBTP (`vedit mix`: 2 geçişli loudnorm + limiter).
- Konuşma zinciri (`vedit audio`): highpass 80 Hz → afftdn → EQ (−2.5 dB @250 Hz, +2 dB @4.2 kHz) → kompresör 3:1. Gürültü fazlaysa `--denoise medium|strong`; ses robotikleşirse bir kademe düşür.

## earshot: ölçerek dinleme (ADR 0016)
Ayrıntı `earshot` skill'inde. Komut: `"<SKILL_LIB>/repos/Leonxlnx__earshot/.venv/Scripts/python.exe" -m earshot <komut>`. Ses dışarı çıkmaz; `llm` komutunu kullanma.
- Model istemez: `measure`, `sfx list`, `sfx render`. Diğerleri her çağrıda modeli yükler (20-60 sn); çok çağrıda tek betik yaz: `from earshot import api`.
- Aday seçimi: `rank "tarif" <klasör>`, sonra `find`, sonra `ab`. Değeri yaz: "strong, z +3.9".
- Teslim öncesi: `measure <video>`, sonra `timeline <video> --video <video> --cues cues.json`. `cues.json` biçimi `{"fps":30,"events":[{"t":1.2,"kind":"zoom_in"}]}`; zamanları `edit/olaylar.json`'dan üret. Gerekirse `sheet <video> -o sheet.png`.
- Güvenilir: LUFS, true peak, LRA, zamanlama sapması. İpucu: miks içindeki etiketler (`?` işaretli olanlar). "Cut without a hit" listesi yumuşak whoosh'u kaçırabilir; ses eklemeden `sheet`'e bak.
- `critique` kapı değildir: profili lansman filmleri, konuşan kafada yanıltır. Tat, duygu ve "güzel mi" ölçülmez; son karar kullanıcının kulağı.
- Yeni ses: `sfx render <id> -o library/sfx/raw/earshot/<ad>.wav`, `source.json` (`license: MIT`, dosya başına kategori), `vedit sfx index`. Kullanıcı seçene kadar kategori `aday` kalır; `aday` otomatik seçilmez. Seçilen ses `kit.json` rolüne kimliğiyle yazılır, kilit için onay istenir.
- Fit bankası CC0 kayıtlardan türetilir, lisansını koru.

## Seviye ve miks kuralları (claude-video-edit, ADR 0016)
- Müzik, konuşma sürerken ölçümde konuşmanın 18-22 dB altında olsun; `gain_db` −12…−16 başlangıçtır, ölçerek doğrula.
- Sakin eğitici videoda SFX başlangıcı tek başına tepe −32…−26 dBFS. `vedit olaysesi` varsayılanı bundan yüksektir; kullanıcı "fazla" derse buraya in. İlk tepkiyi videonun geri kalanına uygula.
- Vurguyu konuşmadaki vurgulu heceye bindirme; kelimeyi maskeleme.
- Klavye sesi yazı animasyonunu izlesin: görünen karakter grubu başına bir tuş, küçük perde ve zaman farkı. Hazır döngü koyma.
- Kısa boşlukta dijital sıfır yerine o kaydın oda sesini kullan.
- Kullanıcı "boğuk" ya da "cızırtılı" derse önce son ses işlemini geri al, üstüne filtre ekleme. Konuşmaya yeni işlem için A/B dosyası ver.
