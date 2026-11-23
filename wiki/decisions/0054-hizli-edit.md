---
type: decision
title: "Hızlı edit: yalın ajan çağrısı, pafta ile QC, gereksiz render ve seri çağrının kaldırılması, hızlı ön ayar"
status: accepted
tags: [adr, ai-edit, ajan, ekip, hiz, kaizen, qc]
created: 2026-11-23
updated: 2026-11-23
sources: ["[[0053-seviyeli-ekip-orkestrator]]", "[[0017-terminal-hizli-hat]]"]
---

# ADR 0054: Hızlı edit

## Bağlam
Kullanıcı edit süresinin kısalmasını istedi (2026-11-23). Kaizen günlüğüne göre darboğaz artık render değil, `ai-edit`.

Ölçülen temel koşu `instagram/arvelior` oldu (medium: 4 editör, 2 QC, Opus orkestratör, Sonnet editörler, agy QC). Koşu 20,8 dk sürdü. Süre dökümü `work/edit/ekip/*/*.meta.json` dosyalarından çıkarıldı:

| Adım | Süre | Neden |
|---|---|---|
| G0 plan | 75 sn | 8 tur, 402k token: istemi, rol dosyasını ve digest'i araçla okudu |
| G1 düzen | 70 sn | Her editör 3 tur: istemi oku, rol dosyasını oku, yanıtı yaz |
| G2 kapı | 52 + 46 sn | O her koşuda çağrılıyordu, sonra düzeltmeler seri bekliyordu |
| G3 birleştir, taslak, izle | 204 sn | |
| G4 QC | 413 sn | agy 53 kareyi `read_file` ile tek tek okudu; `olcum.json`'daki bulguları yeniden yazdı |
| G6 düzeltme ve render | 114 + 176 sn | Render'ı hiçbir sonraki adım kullanmadı |

Kök nedenler:
- **Şişkin ajan bağlamı.** `ekip.ajan` her ajanı proje kökünde `claude -p` ile başlatıyordu. Her çağrı şunları yükledi:
  - 269 araç
  - 15 MCP sunucusu (claude.ai bağlayıcıları dahil)
  - 151 slash komutu
  - CLAUDE.md
  - plugin hook'ları

  Bu, çağrı başına yaklaşık 45k token taban bağlam demek. İstem "Read the file …" ile dosyadan okutuluyordu, bu da her çağrıya 1-2 tur ekliyordu.
- **QC'nin kare kare okuması.**
- **Boşa render ve seri bekleme.**

## Seçenekler
- **Kapsam:** yalnız kalite kaybetmeyen hızlandırmalar ya da bunlara ek seçilebilir bir hızlı ön ayar. Kullanıcı ikisini birden seçti.
- **QC motoru:** agy'de kalıp kareleri paftada toplamak ya da Claude'a geçmek. Kullanıcı agy + paftayı seçti; ücretsiz kota korunur.
- **Yalın çağrı yolu:** `--bare` ya da tek tek bayraklar. `--bare` yalnız `ANTHROPIC_API_KEY` okur, abonelik girişini (OAuth) okumaz. Bu yüzden bayraklar seçildi.

## Karar

### 1. Yalın ajan çağrısı (`motorlar.yalin_komut`, `ekip.ajan(metin=…)`)
Ekip Claude'u şu bayraklarla çağırır:
- `-p` (istem stdin'den)
- `--tools ""` (QC'nin Claude yedeğinde `Read`)
- `--strict-mcp-config --mcp-config {"mcpServers":{}}`
- `--disable-slash-commands`
- `--setting-sources ""` (plugin hook'ları da kapanır)
- `--no-session-persistence`
- `--append-system-prompt <rol tanımı>`

Süreç repo dışında, `%LOCALAPPDATA%/vedit/ajan` klasöründe başlar. Böylece proje CLAUDE.md'si kendiliğinden yüklenmez.

İstem içeriği de değişti:
- Rol dosyasının metni (`ekip_v3.rol_metni`, frontmatter'sız) sistem istemine gider.
- `digest.txt` istemin içine gömülür.
- Kurgu editörü hazır efekt kataloğunu, müzik editörü lisanslı müzik listesini istemde alır.

Dosya okuyan motorlar (agy) için rol metni istem dosyasının sonuna eklenir. İstem stdin'den gittiği için Windows'un 32k karakterlik komut satırı sınırı sorun olmaz.

Tek ajan `ai-edit` (`ajan_cagri.komut`) araçları ve `--resume`'u kullandığı için yalnız MCP ve slash kısıtını alır.

Ölçülen fark (aynı E4 istemi, Sonnet medium):

| | Eski | Yalın |
|---|---|---|
| Tur | 4 | 1 |
| Önbelleğe yazılan giriş | 45k | 11,5k |
| Toplam giriş | ~156k | ~12k |

Ayar kaynaklarını kapatmak (`--setting-sources ""`) tabanı 3,7k token'a indirir ve OAuth girişi çalışmaya devam eder.

### 2. QC paftası (`ekip.izle`, `ekip.pafta_yap`)
- Sabit kareler kesin seek ile ve paralel çıkarılır. Uzun videoda en çok 160 kare alınır.
- Kareler 12'lik paftalarda toplanır (`qc/pafta-N.jpg`, 4×3, köşede saniye).
- OCR (`npx mcp-video-analyzer`) ve kontak sayfası arka planda çalışır.
- QC önce paftaları açar, en çok 6 tek kareye bakar. `kanit` yine kare dosyasının yoludur, bu yüzden "dosya yoksa bulgu düşer" kuralı değişmez.

vedit'in ölçtükleri QC istemine "tekrar yazma" listesi olarak girer (`vedit_bulgulari`):
- slop
- loudness (taslakta yalnız bilgi; teslim miksi -14 LUFS / -1 dBTP'ye kendisi eşler)
- kurgu-denetle

Slop'un P0 ve P1 bulguları K9 yoluyla doğrudan sahibine gider (`slop_bulgulari`).

### 3. Seri bekleme ve boşa render
- **G2:** O yalnız şu durumlardan biri varsa çağrılır:
  - deterministik ihlal,
  - sahipsiz uyarı,
  - yanıtsız editör.

  Temiz kapı deterministik geçer. Sert ihlal kuralı aynen kalır.
- **G6:** Düzeltmeden sonra render alınmaz. Videoyu yalnız ikinci QC kullanır. Render G7'de yalnız `p0` doluysa ya da `--tekrar-denetle` verildiyse alınır.
  - Alınmadığında `ozet.taslak_eski` true olur ve kapı notu "`vedit taslak` yeniler" der.
  - Stüdyo önizlemesi kurgu.json'dan canlı çizer.
  - `--final` zaten tam render alır.

### 4. Deterministik ön düzeltme (`ekip_v3.oto_duzelt`, G3 render'ından önce)
- Native grafik süresi bileşen sınırına çekilir (`native_motion.sure_siniri`). Uzatma aynı izdeki sonraki klibe ve sekans sonuna taşmaz.
- Zoom/punch olayı dakikada `slop.OLAY_YOGUN_DAKIKA` (6) sınırını aşarsa en sık kümelenen hazır efekt silinir. Hook'taki (ilk 3 sn) efekt son çaredir. Sessiz efekt (el kamerası) dokunulmaz.

Bu, "ikinci kez gelen düzeltme koda yazılır" kuralının uygulamasıdır ([[0047-kural-deposu]]). Değişiklikler raporda "vedit'in düzelttikleri" bölümüne yazılır.

### 5. Hızlı ön ayar (`--hizli`, `EkipAyar.hizli`, Stüdyo "Hızlı" anahtarı)
- Seviye low'a sabitlenir (2 editör, 1 QC).
- G0'da O çağrılmaz. Varsayılan dağıtım kullanılır ve P0/P1 kuralları karta doldurulur.
- G2 deterministiktir.
- G5'te triyaj yoktur: bulgular kabul edilir. Kural adayı onaysız olduğu için depoya girmez ([[0053-seviyeli-ekip-orkestrator]]). Aday raporda "onaysız kural adayları" bölümünde kalır.
- `--hizli` `--ekip`'i de açar.

### 6. Ölçüm
- Her kapının başlangıcı ve süresi `durum.json`'a (`kapilar[].bas`, `sure`) ve `ozet.json` `kapi_sure` alanına yazılır.
- Rapor en yavaş üç kapıyı yazar.
- `vedit kaizen` satırı ekip koşusunun en yavaş kapısını ekler.

## Ölçüm (2026-11-23, aynı istek, kopya proje `instagram/arvelior-hiz`)

| Kapı | Eski medium | Yeni medium | Hızlı (low) |
|---|---|---|---|
| G0 plan | 75 sn | 40 sn | 0 sn |
| G1 düzen | 70 sn | 73 sn | 182 sn |
| G2 kapı | 98 sn | 90 sn | 105 sn |
| G3 birleştir + taslak | 204 sn | 114 sn | 136 sn |
| G4 QC | 413 sn | 347 sn | 307 sn |
| G5 triyaj | 35 sn | 20 sn | 0 sn |
| G6 düzeltme + render | 290 sn | 81 sn | 187 sn |
| Toplam | 20,8 dk | 13,4 dk | 15,3 dk |

- Low seviyede ikinci editör bütün grafik, ses ve stil katmanını tek başına yazar. Bu yüzden G1 ve G6 uzar ve hızlı ön ayar bu 53 sn'lik videoda medium'dan yavaş kaldı.
- Daha çok ajan da hızlandırmaz: kapı en yavaş ajanı bekler, render ve QC seri kalır. Kısa videoda dengeli nokta medium'dur.
- QC metin girdilerinin isteme gömülmesi bu ölçümden sonra eklendi.

## Sonuçlar
- CLI: `vedit ai-edit <proje> --ekip [--seviye …] [--hizli] [--tekrar-denetle] [--final]`. `--final` artık ekip akışına da iletilir.
- Orkestratör çağrı sayısı:

  | Durum | Çağrı |
  |---|---|
  | Kural kapısı temiz | 2 (plan, triyaj) |
  | İhlal var | 3 |
  | Hızlı | 0 |

- QC rol dosyaları (`kk-*.md`) pafta okumaya göre güncellendi.
- Testler:
  - `tests/test_ekip.py`: `test_hizli_on_ayar_orkestratorsuz`, `test_temiz_kural_kapisinda_orkestrator_beklenmez`, `test_yalin_claude_komutu_ve_stdin`, `test_pafta_kareleri_toplar`
  - `tests/test_ekip_v3.py`: `test_oto_duzelt_zoom_yogunlugu_ve_kisa_grafik`, `test_slop_bulgulari_k9_bicimi`, `test_rol_metni_frontmatter_atar_ve_paketler_dosya_okutmaz`
  - `studio/web/src/paneller/ai/seviye.test.ts`

## İlgili kod
- `src/vedit/motorlar.py`: `yalin_komut`, `YALIN_KOK`
- `src/vedit/ekip.py`: `ajan`, `izle`, `sabit_kareler`, `pafta_yap`, `vedit_bulgulari`, `Durum.kapi`
- `src/vedit/ekip_v3.py`: `rol_metni`, `_digest`, `_muzik_katalogu`, `_cagir`, `oto_duzelt`, `slop_bulgulari`, `_akis`
- `src/vedit/ajan_cagri.py`: `komut`
- `src/vedit/hizli.py`: `kaizen`
- `studio/web/src/paneller/ai/SeviyeSecici.tsx`, `EditSekmesi.tsx`, `EkipIlerleme.tsx`
