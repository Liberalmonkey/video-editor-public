---
type: decision
title: "Hızlı ve kaliteli edit: tema kilidi denetimi, görselli tek tur QC, 15 fps önbellekli QC render'ı, dilimli QC, uyarı kapısı"
status: accepted
tags: [adr, ai-edit, ekip, hiz, qc, kalite, tema]
created: 2026-11-25
updated: 2026-11-25
sources: ["[[0054-hizli-edit]]", "[[0053-seviyeli-ekip-orkestrator]]", "[[0043-stile-bagli-tema-tokenlari]]", "[[0057-her-makinede-hiz]]"]
---

# ADR 0058: Hızlı ve kaliteli edit

## Bağlam
Hedef: 60 sn'lik videonun editi kaliteden ödün vermeden 4 dk'nın altına insin (kullanıcı isteği, 2026-11-24). Kalite önce gelir: `kurgu-denetle` uyarısı, slop ve `denetim` sonucu temel koşudan kötü olamaz.

Ölçüm projesi `instagram/arvelior-swarm` (53 sn, `sert-isik-gercekcilik`, motion orta), istek her koşuda aynı. Betik `work/olcum/temel_olc.sh`, sonuçlar `work/olcum/<etiket>/`. `hizlic` modu `--ekip --hizli` ile Claude QC'yi kullanır (`work/olcum/ekip-claude.json`).

Temel ölçümde süreyi en çok QC (agy, 336 sn) ve taslak render'ı (~120 sn) alıyordu. G1'de editörler 60-107 sn sürüyordu, G2 düzeltmeleri de sırayla çalışıyordu.

## Karar
- **Tema kilidi denetimi** (`src/vedit/tema_denetim.py`): ajanın yazdığı HyperFrames kompozisyonu ve `hf`/`sablon` parametreleri sabit renk ve font için taranır. Nötr siyah/beyaz serbesttir, token'dan türeyen JS de serbesttir. İhlal yamayı sahibine düzeltmeye yollar (`ekip_v3.hf_hatalari`, tek ajan yolunda `aiedit.tema_hatalari`). `tests/test_sabit_renk.py` aynı deseni kullanır. Kütüphanedeki 175 HTML'de yanlış alarm yok.
- **Görseller tek turda:** Claude'a QC paftaları ve kontak sayfası stream-json ile mesaja ekli gider (`motorlar.yalin_komut(akis_girdi=)`, `ekip.akis_mesaji`). Ajan dosyaları tek tek açmaz.
- **QC render'ı:** `hizli.qc_taslak` → `renders/qc.mp4`, 15 fps, ölçek 0,5. `hf_kurgu.render(onbellek=True)` derleme özeti aynıysa render'ı atlar. 30 fps 100 sn, 15 fps 75 sn sürüyor; 4 işçi CPU sınırında 2 işçiden yavaş. Teslim render'ı değişmez ([[0016-earshot-render-standardi-ajan-duzeni]]).
- **OCR en çok 5 sn beklenir** (`ekip.OCR_BEKLE`). OCR 48 sn sürüyor, öteki girdiler 8 sn; QC yazıyı paftadan okur.
- **Motion ön üretimi** (`ekip_v3.OnUretim`): editörün yaması gelince webm'ler arka planda üretilir, G3 bekler.
- **G2'de sert ihlal paralel düzeltilir:** eksik `kural_uyum`, reddedilen yama ve yanıtsız editör, orkestratörün kapı kararı beklenmeden düzeltmeye başlar.
- **Dilimli QC** (`ekip_v3.hizli_kk`, `pafta_sec`): hızlı modda tek genel QC yerine zaman dilimi başına bir genel QC çalışır (90 sn altı 2, üstü 3). Sınır kelime arasıdır; her ajan yalnız kendi diliminin paftalarını görür, sınırda bir kare payı vardır. G4 154 sn'den 69 sn'ye indi.
- **Uyarılar sahibine gider:** `kurgu_kalite` tekrar uyarıları (`GECIS_TEKRAR`, `EFEKT_TEKRAR`, `GRAFIK_TEKRAR`) ve `MOTION_ART_ARDA` artık klip id'si taşır (`klip` alanı). Eskiden sahipsiz kalıyor, kimse düzeltmiyordu.
- **Geçiş tekrarı kodla düzelir** (`oto_duzelt` 3. adım): üçüncü aynı geçişin yönü çevrilir, geçiş yumuşak kalır. Efekt tekrarı kodla silinmez; hangi vurgunun gideceği kurgu kararıdır.
- **G6 uyarı kapısı** (`ekip_v3.yeni_uyarilar`): G3'te kalan uyarılar G6 editörüne kısıt olarak gider (ek çağrı yok). Düzeltme yeni uyarı doğurursa sahibine bir kez kısa tur gider. P0/P1 düzeltmesi P2 uyarısı için geri alınmaz; ikinci tur yalnız uyarıyı azaltıyorsa kabul edilir. Sonuç `ozet.json` `uyari_kapisi` alanında.
- Alt süreler `ozet.alt_sure`'de (bağlama, render, ön üretim, izle).

## Sonuçlar
| Koşu | Süre | Uyarı | Slop | QC P0/P1 | G1 | G3 | G4 | G6 |
|---|---|---|---|---|---|---|---|---|
| temel hizli (agy QC) | 672 sn | 1 | 0 | 2/5 | 107 | 129 | 336 | 60 |
| g3 hizlic | 450 sn | 4 | 0 | 2/8 | 121 | 82 | 154 | 61 |
| g3b (+ id'li uyarı, uyarı kapısı) | 492 sn | 1 | 0 | 2/8 | 83 | 90 | 177 | 100 |
| g3c (+ dilimli QC, G3 uyarısı kısıt) | **419 sn** | **0** | 0 | 0/5 | 111 | 57 | 69 | 150 |

- Süre 672 → 419 sn (%38). Uyarı temelden iyi (1 → 0), slop 0, `denetim` ölçümleri temel koşuyla aynı (-15,4 LUFS taslak miksi).
- **240 sn hedefi tutmadı; kalite seçildi.** Kalan süre: G1 ~110 sn (grafik, ses ve stil tek editörde, E2), G6 ~150 sn (tam yamayı yeniden yazan düzeltme + uyarı turu), QC render 57-90 sn, G4 ~70 sn.
- E1'i `low` seviyede çalıştırmak (`work/olcum/g3c/hizlicl`) kazanç getirmedi. G1'i E2 bekliyor; kalite de düştü (P0 1, uyarı 1). Rol başına seviye uygulanmadı.
- Hızlı modda QC motorunun varsayılanı (Claude mu agy mi) burada değişmedi. Ayar şeması üç gruba kilitli; seçim swarm orkestratörüne geçiyor ([[0059-swarm-edit]]).
- Ölçüm sırasında boş bellek 2,6 GB'a düştü. Ek editör (hızlı modda 3 editör) bu makinede bellek riski taşıyor.

## İlgili kod
- `src/vedit/tema_denetim.py`, `tests/test_tema_denetim.py`, `tests/test_sabit_renk.py`
- `src/vedit/ekip_v3.py`: `hf_hatalari`, `oto_duzelt`, `yeni_uyarilar`, `hizli_kk`, `pafta_sec`, `OnUretim`, `_akis`
- `src/vedit/ekip.py`: `izle` (`OCR_BEKLE`, `_pafta_zaman`), `akis_mesaji`
- `src/vedit/kurgu_kalite.py`: `uyarilar` (`klip` alanı)
- `src/vedit/hizli.py`: `qc_taslak`; `src/vedit/hf_kurgu.py`: `render(onbellek=)`; `src/vedit/motorlar.py`: `yalin_komut(akis_girdi=)`
- Testler: `tests/test_ekip_v3.py` (`test_oto_duzelt_art_arda_gecis_yonu`, `test_yeni_uyarilar_g6_sahibine_gider`, `test_hizli_qc_dilimleri_ve_pafta_secimi`), `tests/test_ekip.py::test_hizli_on_ayar_orkestratorsuz`, `tests/test_kalite.py::test_art_arda_ayni_gecis_ve_efekt`
