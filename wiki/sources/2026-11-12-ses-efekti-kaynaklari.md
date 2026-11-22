---
type: source
title: "Ses efekti kaynakları ve profesyonel yerleşim pratiği"
tags: [ses, sfx, arastirma, cc0]
created: 2026-11-12
updated: 2026-11-12
author: Claude (araştırma ajanı)
---

# Ses efekti kaynakları ve profesyonel yerleşim pratiği

## Özet
Kütüphanede 530 ses var: 452 Kenney, 57 synth, 9 earshot, 8 remotion, 3 mixkit, 1 pixabay. Eksik olanlar: gerçek sinema whoosh'u, sub drop/boom, ters şişme ve riser, yumuşak UI tıkı, fare/klavye foley, pop ve baloncuk, deklanşör, kâğıt, oda sesi, tape stop, kasa/bozuk para. Mevcut indirme düzeni: `vedit sfx fetch kenney|remotion|freesound|openverse` (`src/vedit/sfx.py`), ham dosya `library/sfx/raw/<kaynak>/` + `source.json`. Politika (`sound-design` skill): lisansı belirsiz kaynak yok; BBC SFX, CC-BY-NC, AI üretimi yasak; lisanslı ses'i kullanıcı indirir.

Bulgu: programatik ve girişsiz indirilebilen, doğrulanmış CC0 kaynakların en iyisi **Wyzowl SFX Kit** (320 ses, 67 MB, 28 kategori, boşlukların çoğunu kapatır) ama **tamamı kodla sentezlenmiş** (README: "Every sound is synthesised by code ... created with Claude"). "Gerçek kayıt" şartını karşılamaz. Gerçek kayıt CC0 için OpenGameArt paketleri var (klavye, kâğıt/kumaş/UI, darbe), fakat gerçek sinematik riser/sub drop/reverse için doğrulanmış CC0 bulunamadı; bunlar kullanıcı listesine gitti.

## Ana çıkarımlar
- Tek bir 54 MB'lık CC0 depo (Wyzowl) 11 boşluğun 9'unu sentetik de olsa kapatır; ayrıca her sesin `sync.at` (tepe/varış noktası), `under_voiceover_db` (−1…−8) ve `fits_seconds` verisi var. Bu veri `vedit olaysesi` peak hizalamasına doğrudan uyar.
- Gerçek kayıtlı CC0 az ve dağınık (OpenGameArt). Kalite değişken: "impacts.zip" yazarı bile "yüksek kalite değil" diyor.
- Freesound en zengin CC0 kaynağı ama özgün dosya indirme OAuth2 ister; yalnız önizleme (ogg/mp3) API anahtarıyla gelir. Projedeki `fetch freesound` zaten anahtar bekliyor.
- Sonniss GDC, Pixabay, Mixkit "atıfsız, ticari" ama CC0 değil; yeniden dağıtım yasak. Repoya commit etmeden yerel kullanım.
- Google Actions Sound Library: gerçek kayıt, ama koşul "yalnız Actions içinde; ayrı dağıtım ve Google dışı platform yasak". **Kullanma.**
- BBC Sound Effects: sitede "personal/educational projects ... or licence them for use" yazıyor; CC0 değil. Zaten yasak.
- Kenney'de eldeki 6 pakete eklenecek yeni ses paketi yok (doğrulanmadı: site tek tek taranmadı).

## CC0 kaynak tablosu
Hepsi: girişsiz, programatik. Doğrulama: sayfa açıldı, HTTP 200 + boyut `curl -I` ile alındı (2026-11-12).

| Kaynak | Lisans (alıntı) | Boyut | Gerçek mi | Doldurduğu boşluk | Örnek dosya |
|---|---|---|---|---|---|
| Wyzowl SFX Kit, github.com/wyzowl/sfx-kit | "CC0 1.0 Universal: no rights reserved." | 67 MB wav (depo 54 MB) | Hayır, kodla sentez | whoosh, reverse whoosh, riser/faller, sub drop/boom/808, pop/bubble, UI tık, klavye, mekanik/deklanşör, foley, para, glitch, bildirim | `whoosh-fast-soft`, `reverse-whoosh-medium-soft`, `riser-2s-soft`, `bass-sub-drop-medium`, `boom-hit-soft`, `pop-medium-bubble`, `click-mouse-soft`, `mechanical-shutter-light`, `props-page-turn`, `money-register`, `digital-glitch-subtle` |
| OGA Owlish Media Sound Effects | "CC0" (sayfada) | 142.4 MB zip | Evet (yazar kaydı) | kâğıt, kumaş, UI, metal/seramik darbe, oda/ambiyans, su | zip içi dosya adları görülmedi (doğrulanmadı) |
| OGA Keyboard Soundpack #1 (unicaegames) | "CC0" | 8.5 MB | 10 insan yazımı + 32 tek tuş gerçek; 7 üretilmiş | klavye foley | zip içi adlar doğrulanmadı |
| OGA UI Sound Effects (Button Clicks, User Feedback, Notifications) | "CC0" | wav 1.4 MB / ogg 231 KB | Doğrulanmadı | yumuşak tık, bildirim | `ui_wav.zip` |
| OGA Impacts/Gun/sfx | "CC0" | 12.5 MB | Evet (yazarın kaydı, bas boost) | alçak darbe, slam | "yüksek kalite değil" notu var |
| OGA Swishes Sound Pack | "CC0" | 385 KB, 13 wav | Doğrulanmadı (Summoning Wars için) | kısa whoosh/swish (oyun tonu riski) | `swishes.zip` |
| OGA Air Woosh Move | "CC0" | 127 KB | Doğrulanmadı | tek hava whoosh | `air_move.wav` |
| OGA typing soundeffect | "CC0" | 167 KB | Doğrulanmadı | klavye yazımı | `typing_0.ogg` |
| Freesound (CC0 filtreli) | sound nesnesinde `license` alanı | değişken | Evet | her şey: riser, sub drop, tape stop, oda sesi | API anahtarı şart; özgün indirme OAuth2; önizleme anahtarla gelir |
| romainsimon/uisfx | "procedurally generated audio library is dedicated to the public domain under CC0 1.0" | MP3+OGG 936 dosya | Hayır, prosedürel | UI tık (12 stil) | npm paketi `uisfx`; doğrudan zip yok; ihtiyaç düşük |

Atıflı/izinli ama CC0 olmayan, programatik: DailySounds (dailysounds.org) "free for commercial games, credit appreciated"; tek tek MP3 sayfası, girişsiz; tam lisans sayfası (dailysounds.org/license) okunmadı (doğrulanmadı). Oyun odaklı, listeye alma.
Mixkit: önizleme mp3 doğrudan açılıyor (`assets.mixkit.co/active_storage/sfx/1489/1489-preview.mp3`, 200 OK, 72 KB). Lisans modal metni okunamadı ("Sound Effects Free License"); sayfada madde alıntılanamadı (doğrulanmadı).
Pixabay: "Use Content without having to attribute the author"; "You cannot sell or distribute Content ... on a Standalone basis." (Pixabay Content License özeti; SFX'e özel madde sayfada yok). Programatik indirme Cloudflare nedeniyle denenmedi (doğrulanmadı).

## İndirme planı
Sıra önemli: önce geniş ve güvenli, sonra gerçek kayıt. Toplam yaklaşık 165 MB. Hepsi CC0, girişsiz. Her biri `library/sfx/raw/<kaynak>/` altına `source.json` ile (lisans "CC0", `source_url`, dosya başına kategori).

1. `https://github.com/wyzowl/sfx-kit/archive/refs/heads/main.zip` (~54 MB; 302 sonra 200). Hedef klasör `raw/wyzowl/`, yalnız `sounds/**/*.wav`. Önerilen eşleme (manifest kategori adı):
   - whooshes, swishes-and-zips, swipes, bounce-spin-zoom -> `whoosh`, `swoosh`, `whip`
   - reverse-whooshes, risers-and-fallers -> `riser`
   - booms-and-bass, impacts, cinematic-hits -> `impact` (sub drop için `bass-sub-drop-*`, `boom-hit-*`)
   - pops, appear-and-vanish -> `pop`
   - interface, keyboard, writing-and-drawing -> `click`, `tap`, `typing`
   - mechanical (`mechanical-shutter-*`) -> `camera_shutter`; everyday-props (`props-page-turn`, `props-book-close`) -> `page_turn`; foley -> `foley`
   - money -> `cash`; digital (`digital-glitch-*`, `digital-power-down`) -> `glitch` (tape stop yaklaşığı); notifications, tones -> `ding`, `notification`
   - Uyarı: sentez; `earshot rank/describe` ile tek tek ölç, "p_real" düşük çıkarsa kit rolüne kilitleme.
2. `https://opengameart.org/sites/default/files/Owlish%20Media%20Sound%20Effects.zip` (142.4 MB). Gerçek kâğıt, kumaş, UI, darbe, ambiyans, su. -> `page_turn`, `foley`, `ui`, `impact`, ambiyans (yeni kategori `ambience` gerekebilir). Yalnız beğenilenleri tut, geri kalanını sil (disk).
3. `https://opengameart.org/sites/default/files/unicae_games_keyboard_soundpack_1_0.zip` (8.5 MB). -> `typing`, `foley`.
4. `https://opengameart.org/sites/default/files/impacts.zip` (12.5 MB). Alçak darbe adayı; "aday" kategorisinde tut, earshot ile kalite süz. -> `impact`.
5. `https://opengameart.org/sites/default/files/ui_wav.zip` (1.4 MB). -> `ui`, `click`, `notification`. Önce dinle: Kenney'den farkı yoksa atla.
6. `https://opengameart.org/sites/default/files/swishes.zip` (385 KB) ve `https://opengameart.org/sites/default/files/air_move.wav` (127 KB). -> `swoosh`. Oyun tonu riski, `aday`.
7. İsteğe bağlı, anahtarla: `vedit sfx fetch freesound "riser reverse"`, `"sub drop"`, `"tape stop"`, `"room tone"` (yalnız CC0, `FREESOUND_API_KEY` ücretsiz). Önizleme kalitesi (ogg/mp3) yeterli kısa efektlerde.

Gerçek, CC0, sinematik riser/sub drop/reverse için doğrulanmış doğrudan URL bulamadım. Bu boşluk 1. adımın sentezi ya da aşağıdaki kullanıcı listesiyle kapanır.

## Kullanıcının indireceği liste
Proje politikası: lisanslı sesi kullanıcı indirir. Dosyayı `library/sfx/raw/<site>/` içine koy, sonra "kütüphaneye kaydet" de.

| Site | Arama / paket | Lisans | Ne al |
|---|---|---|---|
| Pixabay Sound Effects, pixabay.com/sound-effects | "whoosh", "cinematic whoosh", "reverse", "riser", "sub drop", "impact bass", "tape stop", "camera shutter", "bubble pop", "paper", "mouse click" | Pixabay Content License, atıf gerekmez, tek başına dağıtım yasak; hesap isteyebilir | Her aramadan 3-4 kısa (0,2-1 sn); riser 1-3 sn; sonu temiz |
| Mixkit SFX, mixkit.co/free-sound-effects (kategoriler: Transition, Technology, Lifestyle) | "whoosh", "impact", "typing", "camera", "cash register" | "Mixkit Sound Effects Free License" (metin okunamadı, sayfada kontrol et) | Transition kategorisi, Technology UI |
| Sonniss GDC bundle, sonniss.com/gameaudiogdc | Ör. GDC 2024 (23,5 GB, 9 parça), 2021-23 (38,7 GB), vb. | "royalty free and commercially usable", atıf yok; yalnız medya yapımı; AI/ML eğitimi yasak; tek başına satış yasak; giriş gerekmediği açıkça yazmıyor | Tek bir parçayı seç (zip parçaları var); whoosh, impact, foley, ambiyans, riser klasörlerinden süz. Büyük: yalnız gerektiğinde, tamamını repoya koyma |
| Freesound, freesound.org | Filtre: License = Creative Commons 0; "tape stop", "room tone", "reverse cymbal", "sub drop", "bubble pop" | CC0 (dosya bazında doğrula); giriş şart | Kısa, temiz, tek vuruşlu kayıtlar |
| Wikimedia Commons | Kategori "Sound effects" | PD/CC dosya bazında | Düşük öncelik, kalite düzensiz (doğrulanmadı) |

Kullanma: BBC Sound Effects (sitede kişisel/eğitsel kullanım, ticari için lisans), Google Actions Sound Library (yalnız Actions içinde), ZapSplat (atıf ve ticari kısıt, kayıt gerekir; doğrulanmadı), CC-BY-NC, AI üretimi sesler.

## Profesyonel pratik
Kaynak notu: Aşağıdakilerden "proje" ve "Wyzowl" doğrulandı (bu depodaki `sound-design` skill'i, `github.com/wyzowl/sfx-kit/GUIDE.md`). "Sektör" olanlar yaygın kural, bu oturumda kaynağı açılamadı (doğrulanmadı; web arama sınırı doldu).

- **Katmanlama (sektör).** Vurgulu büyük anlar için üç katman: üst (whoosh, hava, 2-8 kHz), orta (darbe gövdesi), alt (sub, 40-80 Hz). Sub kısa olsun (0,3-0,8 sn), whoosh'u boğmasın. Örnek: whoosh + soft sub drop. Wyzowl kiti `layers well with` verisi veriyor.
- **Ön-lap zamanlaması (Wyzowl + sektör).** Sesi `başlangıç = olay anı − sync.at` ile koy; whoosh'un tepesi hareketin en hızlı noktasına (ease-in-out'ta ortası), riser/ters whoosh'un tepesi kesme karesine ("arrival"), darbe tam kesme karesine. Pratik: whoosh genelde kesmeden 2-6 kare önce başlar; whoosh hareketin bitişinden hemen önce söner ki iniş darbesi temiz çıksın. Aynı kuralı projenin `vedit olaysesi` aracı uygular.
- **Seviye (proje, Wyzowl).** Teslim −14 LUFS / ≤ −1 dBTP. Konuşmaya göre: soft −9 dB (UI, metin, B-roll), medium −5 dB (vurgu, bölüm), hard −1,5 dB (tek büyük an). Konuşma üstünde efekt −4 dB; Wyzowl `under_voiceover_db` −1…−8, bas ağırlıklı sesler daha çok. Sakin eğitici videoda SFX başlangıç tepesi −32…−26 dBFS. Müzik konuşmanın 18-22 dB altında, `gain_db` −12…−16.
- **Yoğunluk (proje).** ≤ 1 ses / 0,4 sn; kısa format ~4-8 / 15 sn (yani dakikada 16-32), uzun format 6-15 / dk. Her ses ekranda görünen ya da söylenen bir olaya bağlı. Aynı whoosh 6 kezden fazla duyulursa kütüphaneyi büyüt.
- **Çeşitleme.** Aynı olay için en az 3-4 varyant, art arda aynı dosya yok; ±1-2 yarım ses perde ve ±1-2 dB seviye oynat (Wyzowl `adapt.rate` ile hız/perde uyarlar). Klavye: bir tuş başına bir örnek, küçük perde ve zaman farkı (proje).
- **Müzik ducking (proje + sektör).** Konuşma varken müzik −12…−16 dB ve `duck: true`; güçlü vuruşta müzik 200 ms −2,5 dB. Sektör: büyük darbeden 100-300 ms önce müzik/atmosferi −3…−6 dB çek ("pre-hit dip"), vuruşta aç; riser'dan sonra 1-2 sn sessizlik ya da darbe. Riser reveal'den 1-2 sn önce başlar (proje).
- **Boşluk.** Kısa boşlukta dijital sıfır yok, o kaydın oda sesi (proje).
- **Yaygın amatör hatalar.** (1) Her kesmeye whoosh; (2) aynı ses tekrar; (3) efekt konuşmayı maskeler, vurgulu heceye binme; (4) tepe olay karesinde değil, geç ya da erken; (5) oyun/cartoon sesi (UGC'de yasak); (6) bas sesi telefon hoparlöründe duyulmaz, sadece sub'a güvenme; (7) tüm sesler aynı seviyede (hiyerarşi yok); (8) limiter'a vuran toplam miks; (9) kuyruk kesik, tıklama (kısa fade: başta 10-30 ms, sonda 20-50 ms; Wyzowl); (10) sessizlik hiç yok (SFX'siz an da tasarımdır).

## Açık sorular
- Wyzowl sentez sesleri kulakta "amatör" duruyor mu? `earshot describe` ve kullanıcı kulağıyla 10 örnek A/B gerekir; gerçek kayıt şartı kesinse yalnız OGA + kullanıcı listesi kalır.
- Owlish ve keyboard zip'lerinin içindeki dosya adları ve kalite ölçülmedi (indirilmedi, kural: projeye ses indirilmedi).
- Mixkit SFX lisans metni, Pixabay SFX özel koşulları, ZapSplat, DailySounds lisansı, Wikimedia içeriği açılamadı (doğrulanmadı).
- Freesound'da CC0 riser/sub drop/tape stop için somut ID listesi çıkarılmadı (arama aracı sınıra takıldı); anahtar gelince `fetch freesound` ile denenmeli.
- Mevcut `fetch` kodu yalnız kenney/remotion/freesound/openverse biliyor; Wyzowl ve OGA için `fetch wyzowl` ve `fetch oga` eklemek (kodlama ayrı iş, bu raporda yapılmadı) gerekecek.
- `ambience` ve `tape_stop` kategorileri manifestte yok; eklenip eklenmeyeceği karar bekliyor.
