---
type: decision
title: "Swarm edit: ajan tavanı, orkestratörün model seçimi, plana paralel kurgu editörü, birleştirme sağlamlığı"
status: accepted
tags: [adr, ai-edit, ajan, ekip, orkestrator, swarm, studio]
created: 2026-11-25
updated: 2026-11-25
sources: ["[[0053-seviyeli-ekip-orkestrator]]", "[[0054-hizli-edit]]", "[[0058-hizli-ve-kaliteli-edit]]", "[[0026-arayuzde-ajan]]"]
---

# ADR 0059: Swarm edit

## Bağlam
Kullanıcı sabit ekip seviyelerinin (ADR 0053: low 2+1 … max 10+5) yerine dinamik bir swarm istedi (2026-11-24). Orkestratör, alt ajan modelini kaliteye göre serbestçe seçecekti (Claude, agy, codex, opencode). Kapılı akış, kural güvencesi ve deterministik birleştirme korunacaktı. Eski `--ekip --seviye` çağrıları çalışmaya devam edecekti.

## Seçenekler
- **Yeni modül, yeni akış (`suru.py` içinde baştan).** Planın ilk hâli buydu. Testler `ekip_v3` modülüne monkeypatch uyguluyor; 300 satırlık akışı taşımak davranış değiştirmeden test kırar.
- **Akış yerinde genelleşir, swarm kararları `suru.py`'de.** Seçildi.

## Karar
- **Ajan tavanı:** `EkipAyar.en_cok` (2-15, editör + kalite kontrol). Seviye artık tavanın kısaltmasıdır (`ekip_sema.EN_COK`: low 3, medium 6, high 9, xhigh 12, max 15). Orkestratör sayıyı tavan içinde seçer: editör en çok 10, QC en çok 5.
- **Kart başına model:** `Gorev` ve `KkGorev` isteğe bağlı `motor`, `model`, `seviye` alanları taşır. `suru.ezme` bunları slot ezmesine çevirir. Motor yazılmamışsa modelin bulunduğu motor alınır, yedek grup ayarından gelir. Kullanıcının açık slot ezmesi kazanır.
- **Model listesi:** `suru.model_listesi` kurulu motorların modellerini plan istemine koyar. Tarama 11 sn sürdüğü için sonuç `%LOCALAPPDATA%/vedit/motor-durum.json`'da 6 saat tutulur; opencode'dan yalnız ücretsiz ilk 12 model girer. İstemde ölçüme dayalı model notu da vardır (`suru.MODEL_NOTU`).
- **Plan doğrulaması** (`suru.plan_dogrula`):
  - E1 yalnız kurgu katmanını taşır, aralığı null'dır.
  - Slotlar ardışıktır; toplam tavanı aşmaz.
  - Katman × zaman kapsamı eksiksizdir (`ekip_v3.kapsam_hatalari`, seviye doğrulamasıyla ortak).
  - Motor kurulu, model listede olmalıdır.
  - Geçersiz planda video süresine göre varsayılan boya düşülür (`suru.varsayilan_boy`: 45 sn altı low, 150 sn altı medium, 420 sn altı high, üstü xhigh; tavanı aşarsa bir alt seviye).
- **E1 plana paralel:** kurgu katmanı bölünmez ve plandan bağımsızdır, bu yüzden E1 orkestratörün plan çağrısıyla aynı anda başlar. Hook'u E1 seçer, orkestratör artık hook yazmaz.
- **Durum:** plan belli olunca seviye tablosundan açılmış boş kartlar silinir (`ekip.Durum.daralt`); her kart motoru ve modeli taşır. `durum.json` `en_cok` alanını yazar. Klasör `work/edit/ekip/` kalır; Stüdyo uçları ve ölçüm betikleri bu yolu kullanıyor.
- **CLI:** `vedit ai-edit <proje> --suru [--orkestrator MOTOR[:MODEL]] [--en-cok N]`. `--ekip` aynıdır; `--seviye` tavanı verir, `--en-cok` kazanır. `--hizli` değişmez: plan çağrısı yok, 2 editör, dilim başına QC ([[0058-hizli-ve-kaliteli-edit]]).
- **Orkestratör rolü:** `ekip-orkestrator` swarm'a göre güncellendi (tavan hedef değildir, E1 aynen yazılır, model seçimi ölçüme dayanır). Kod rolü bu adla çağırdığı için ayrı `suru-orkestrator` açılmadı.
- **Stüdyo:** AI paneli "Tek ajan | Swarm" seçimi sunar.
  - `SuruSecici.tsx`: Hızlı anahtarı, orkestratörün motor ve modeli, en çok ajan (3/6/9/12/15 kısayolu ve sayı).
  - `SeviyeSecici.tsx` kaldırıldı.
  - Ajan kartları modeli gösterir; özet satırı ajan sayısını ve tavanı yazar.
  - Hazır olma denetimi slot listesi yerine gereken motorlara bakar (`seviye.gerekenMotorlar`).
  - Motor taraması bitmeden "kurulu değil" denmez; düğme "Motorlar taranıyor" der (Playwright görüntüsünde yanlış alarmdı).
  - Doğrulama: Playwright ile proje açıldı, Swarm seçildi; g4d'nin 7 kartı (O, E1-E4, K1-K2) rol, model, süre ve token ile göründü, tavan kutusuna 12 yazıldı, konsol hatası yok (`work/olcum/g4-panel/`).
- **Eski ön ayarlar:** `en_cok` alanı olmayan ön ayar tavanı seviyeden okur; göç gerekmez.

## Ölçüm koşularının ortaya çıkardığı sağlamlık düzeltmeleri
Swarm koşuları üç eski açığı gösterdi. Üçü de koşuyu G2 ya da G3'te durduruyordu:
- **id'siz yama öğesi** (g4, ses-stil editörü Haiku): `_dogrula` `KeyError: 'id'` ile çöküyordu. Öğe artık düşer, `dusen`'e yazılır, kapı sahibine düzeltme yollar. Editör kartındaki Haiku seçimi grup modeline döner (`suru.EDITOR_YASAK`); QC'de serbesttir.
- **Render'ı bozan tek grafik** (g4b, `seviye: 'yuksek'`): G3 bütün edit'i durduruyordu. `ekip_v3.render_kurtar` hatanın adını verdiği V1 dışı klibi düşürür ve kurgu temizse sürdürür. Düşen klip sahibine P1 bulgusu olarak gider. V1 hatası ya da klip adı geçmeyen hata eskisi gibi durdurur.
- **Geçiş kısa yazımı** (g4c, `gecis_giris: "sil"`): şema reddedince bütün klip güncellemesi düşüyor, eski klip V1'i çakıştırıyordu. `schemas.Klip._gecis_kisa` metni `{"tur": ...}` yapar; bilinmeyen ad yine reddedilir.

## Sonuçlar
Ölçüm (instagram/arvelior-swarm, 53 sn, aynı istek, varsayılan ön ayar `karisik`, tavan 6):

| Koşu | Süre | Uyarı | Slop | Ekip | Kapılar (sn) |
|---|---|---|---|---|---|
| temel ekip medium (agy QC, sabit 4+2) | 778 sn | 2 | 0 | 4E + 2K | G0 34, G1 98, G2 144, G3 124, G4 279, G6 75 |
| g4 swarm | durdu, 96 sn | — | — | 4E + 2K | G2'de `KeyError: 'id'` (ses-stil editörü Haiku) |
| g4b swarm | durdu, 205 sn | — | — | 4E + 2K | G3: tek rozetin parametre tipi |
| g4c swarm | durdu, 228 sn | — | — | 4E + 2K | G3: `gecis_giris: "sil"` V1'i çakıştırdı |
| g4d swarm | **692 sn** | 2 | 0 | 4E (E2, E3 Opus) + 2K (Sonnet) | G0 35, G1 111, G2 155, G3 66, G4 105, G5 23, G6 198 |

- g4d kalitesi temelle eşit: iki uyarı, slop 0, denetim ölçümleri aynı (-15,4 LUFS taslak miksi). Uyarıların ikisi de dilim sınırında, E2 ile E3 arasında "aynı grafik art arda" (MOTION_ART_ARDA).
- Swarm QC (iki Claude Sonnet) temelin agy QC'sinden daha sert çıktı: 22 bulgu, orkestratör 5'ini reddetti (temel: P0 0, P1 5).
- 4 dk hedefi swarm'da tutmadı. En uzun kapılar G6 (198 sn, tam yamayı yeniden yazan düzeltme) ve G2 (155 sn, orkestratörün yeniden çapalama brifi). Hızlı yol 419 sn ([[0058-hizli-ve-kaliteli-edit]]).
- g4d, agy (Gemini 4 Neon High) kod incelemesinin 12 bulgusu uygulanmadan önce koştu; bu düzeltmeler testli (aşağıda).

- Orkestratör kısa videoda tavanı doldurdu (4 editör + 2 QC). Grafiği iki Opus dilimine, ses ve stili tek editöre, QC'yi iki Claude Sonnet'e verdi; agy QC'nin yavaşlığını gerekçesine yazdı.
- Bilinen sınır: grafik ve ses editörleri taban zaman çizelgesine yazar (ADR 0053). E1 çizelgeyi çok değiştirirse (ör. sıra düzeltip 70 sn'yi 53 sn'ye indirirse) çapasız öğeler eski zamanda kalır; orkestratör G2'de yeniden çapalatır. Bu tasarımın parçasıdır; E1'in paralel başlamasıyla ortaya çıkmadı.

## agy kod incelemesi (Gemini 4 Neon High, 2026-11-25)
12 bulgunun hepsi doğrulandı ve uygulandı (`work/agy/2026-11-25-suru-inceleme/inceleme.md`):
- E1 plana paralel çalışırken `ayar`, `atama`, `zorunlu` yeniden bağlanıyordu; E1 başladığı andaki görüntüyle çalışır (`editor(anlik=)`).
- `render_kurtar` klip kimliğini serbest metinden değil satır başından ve çakışma satırından alır (`_hata_klipleri`); kurgu katmanı (V1, A1) düşmez.
- Kart seviyesi motorun seviye listesinde doğrulanır; geçersiz seviye ezmede düşer.
- Tavan en az 3'tür (E1 + bir editör + bir QC); `--en-cok 2` hiçbir planla karşılanamıyordu.
- Model listesi yoksa kart seçimi uygulanmaz; E1 kartı ezilmez; seçilen motor grubun yedeğiyle aynıysa yedek grubun birincili olur.
- `ayar_yukle`: seviye veren ama tavan vermeyen katman alttaki `en_cok`'u taşımaz.
- Havuz hata yolunda kapanır (`cancel_futures`); E1 G0'da düştüyse öteki editörler başlamaz.
- `--orkestrator` ve paneldeki orkestratör seçicisi `ezme["O"]`'yu temizler.
- Panel: tavan sayısı yazılırken sıkıştırılmaz (odak kaybında), çalışırken bütün swarm seçicileri kilitlidir, tavan dışındaki eski ezmeler görünür kalır, hazırlık denetimi yedek motoru da sayar; sunucu hızlıda orkestratörü denetlemez.
- id'siz `ekle`/`guncelle` öğesi `yama_hatalari`'nda yamayı düşürmez.
- Görüntüsüz kurgu (2026-11-27, ornek-proje): `_kurgu_hazirla` girdisi olmayan var olan kurguyu da tohumlar; `girdi_denetimi` ajan çağrısından önce girdideki videonun kurguya alındığını doğrular. `yama_uygula` içindeki `_v1_onar` `baslangic`/`start`/`t` takma adını `bas`'a çevirir, girdi kökünü (`"1"`) kaynak kimliğine eşler, `bas`sız V1 kliplerini ardışık dizer. G2 sonrası birleşme görüntüsüz kalırsa kurgu editörü şemalı brifle (`bos_goruntu_brifi`) bir kez düzeltir; yine boşsa düşen öğelerle durur. Boş V1'de E1 paketi aynı brifi taşır.

## İlgili kod
- `src/vedit/suru.py`: `model_listesi`, `varsayilan_boy`, `plan_dogrula`, `ezme`, `plan_bolumu`, `orkestrator_ayristir`
- `src/vedit/ekip_v3.py`: `_akis` (G0/G1), `kapsam_hatalari`, `plan_paketi(suru_bolumu=)`, `render_kurtar`, `yama_uygula`, `rapor_yaz`
- `src/vedit/ekip_sema.py`: `EN_COK`, `EkipAyar.en_cok`, `tavan()`, `Gorev`/`KkGorev` motor alanları
- `src/vedit/schemas.py`: `Klip._gecis_kisa`; `src/vedit/ekip.py`: `Durum.daralt`; `src/vedit/cli.py`: `cmd_ai_edit`
- `src/vedit/studio/ekip.py`, `studio/isler.py`; `studio/web/src/paneller/ai/SuruSecici.tsx`, `EditSekmesi.tsx`, `EkipIlerleme.tsx`, `EkipAyarlari.tsx`, `seviye.ts`
- Testler: `tests/test_ekip.py` (`test_suru_*`, `test_cli_suru_bayraklari_ve_eski_cagri`), `tests/test_ekip_v3.py` (`test_idsiz_oge_duser_cokertmez`, `test_bassiz_v1_klipleri_ardisik_dizilir_ve_kaynak_eslenir`, `test_render_kurtar_*`, `test_gecis_kisa_yazimi_kabul_edilir`), `seviye.test.ts`
