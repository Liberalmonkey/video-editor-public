---
type: decision
title: "Seviyeli ekip ve orkestratör: 2-10 editör, 1-5 kalite kontrol, kapılı paralel akış, kural güvencesi"
status: accepted
tags: [adr, ai-edit, ajan, ekip, orkestrator, kural, studio]
created: 2026-11-22
updated: 2026-11-22
sources: ["[[0048-ekip-motoru-v2]]", "[[0047-kural-deposu]]", "[[0044-ekip-motoru]]"]
---

# ADR 0053: Seviyeli ekip ve orkestratör

> [!note] [[0048-ekip-motoru-v2]]'nin yerini alır. Sabit 3+3 ekip, eski turlu motor ([[0044-ekip-motoru]], `--ekip-v1`), Bölüş ve Tur seçenekleri kaldırıldı.

## Bağlam
- Ekip v2 her işte sabit 3 editör ve 3 kalite kontrol çalıştırıyordu. Küçük iş için fazla, büyük iş için azdı.
- Kural uyumunu kimse denetlemiyordu. Kurallar istemdeki bir bloktu; editörün uyup uymadığı ölçülmüyordu. QC'nin kural adayının depoya girdiği de doğrulanmıyordu.
- v2'de kullanıcının isteği (`--not`) editörlere hiç ulaşmıyordu (`calistir` parametreyi kullanmıyordu).
- Stüdyo AI paneli sohbeti, tek ajan editi ve 6 slotluk ekip tablosunu tek sütunda üst üste diziyordu. Kullanıcı daha sade ve profesyonel bir sayfa istedi (2026-11-22).

## Seçenekler
- **Rol dağıtımı:** sabit tablo ya da orkestratör. Kullanıcı orkestratörü seçti; geçersiz planda sabit tabloya düşülür.
- **Eski akışlar:** bayrakla tutmak ya da kaldırmak. Kullanıcı kaldırmayı seçti; eski ön ayarlar kendiliğinden göçer.
- **Panel:** Edit/Sohbet sekmeli ya da tek sütun. Kullanıcı sekmeliyi seçti.

## Karar

### Seviye
Seviye yalnız ajan sayısını belirler. Her seviyede ayrıca bir orkestratör (O) çalışır.

| Seviye | Editör | Kalite kontrol |
|---|---|---|
| low | 2 | 1 |
| medium | 4 | 2 |
| high | 6 | 3 |
| xhigh | 8 | 4 |
| max | 10 | 5 |

- Ayar alanı `ekip_seviye`dir. `Slot.seviye` akıl yürütme seviyesidir (effort); ikisi karışmasın diye ad ayrıdır.
- Motor ve model üç grupta seçilir: orkestratör, editör, kalite kontrol. `ezme` tek bir slota (ör. yalnız E1) ayrı motor verir.
- Eşzamanlılık varsayılan olarak editör sayısıdır.

### Katmanlar ve sahiplik
- Katman sınıfları:
  - `kurgu`: V1, A1, hook, işaretler.
  - `grafik`: V1 dışındaki görüntü izleri.
  - `sfx`: A1 dışındaki ses izleri, müzik hariç.
  - `muzik`: adında "Müzik" geçen iz ya da `olay.muzik`.
  - `stil`: altyazı ve motion teması.
- `kurgu` ve `stil` bölünmez. `grafik`, `sfx` ve `muzik` zaman dilimlerine bölünebilir.
- Görev kartı şunları taşır: katmanlar, aralık (taban zaman çizelgesinde), odak, zorunlu kurallar.
- Sahibi katman sınıfı ve klibin taban zaman çizelgesindeki başlangıcı belirler.
- Başka katmana yazan yama düşer. Aralık dışına eklenen öğe ise tek başına düşer.
- Kural deposundaki `hedef_rol` rol sınıfı olarak kalır: E1 kurgu, E2 grafik, E3 ses ve stil.

Varsayılan dağıtım (orkestratörün planı geçersizse):

| Seviye | Editörler | Kalite kontrol |
|---|---|---|
| low | kurgu · {grafik, sfx, müzik, stil} | genel |
| medium | kurgu · grafik ×2 · {sfx, müzik, stil} | kurgu-ses, görsel |
| high | kurgu · grafik ×3 · sfx · {müzik, stil} | kurgu, görsel, ses |
| xhigh | kurgu · grafik ×4 · sfx ×2 · {müzik, stil} | + kural |
| max | kurgu · grafik ×5 · sfx ×2 · müzik · stil | + izleyici |

- Dilim sınırları kelime arasına düşer. Sınırlar kesin artar ve her dilim en az eşit payın yarısıdır.
- Eski bölme kuralı, kısa videoda iki sınırı aynı boşluğa koyup sıfır uzunlukta dilim üretiyordu.

### Kapılar
Her kapı bir bariyerdir: paralel işler orada buluşur. Durum `work/edit/ekip/durum.json` içindeki `kapilar` listesine yazılır.

| Kapı | İş |
|---|---|
| G0 Plan | O hook'u, görev kartlarını ve karta zorunlu kuralları yazar. `plan_dogrula` kontrol eder: sayılar, tek kurgu sahibi, her katman × zamanın tam bir editörde olması, QC alanlarının kapsanması. Geçersizse varsayılan dağıtım kullanılır. |
| G1 Düzen | N editör aynı anda kendi kartına fark yaması yazar. Kullanıcı isteği her editöre gider. |
| G2 Kural kapısı | Deterministik: `kural_uyum` kapsamı, deneme birleştirmesinde red, düşen öğe, çakışma ve `kurgu-denetle`. Mesajdaki klip kimliği sahibine yazılır. Sonra O her editöre kabul ya da düzelt der. Eksik uyum ve reddedilen yama O'nun kararından bağımsız olarak düzeltmeye gider. Düzeltme bir kez ve paralel yapılır. |
| G3 Birleştir | ADR 0048'in deterministik birleştirmesi, tek render. |
| G4 QC | M kalite kontrol aynı anda, ortak kare ve ölçüm paketiyle çalışır. Bulgu katman ve zamandan sahibine gider. |
| G5 Triyaj ve kural | O yanlış pozitifi reddeder ve kural adaylarını onaylar. `kural.qc_isle` adayları depoya işler, `kural_dogrula` depoyu yeniden okuyup her onaylı adayı arar. Bulunamayan aday kapıyı düşürür ve raporun başına yazılır. |
| G6 Düzeltme | Yalnız P0/P1 sahibi düzeltir. Kısıtları etkin kurallar ve bu koşunun yeni kurallarıdır. Uyum yeniden ölçülür. |
| G7 Son | Deterministik denetim. İkinci QC yalnız P0 kalırsa ya da `--tekrar-denetle` verilirse çalışır. |

- Orkestratör en çok üç çağrı yapar: plan, kapı, triyaj. Bulgu yoksa triyaj çağrılmaz.
- v2'deki E1 hook çağrısının yerini O alır. Böylece seri çağrı sayısı yalnız bir artar.

### Arayüz
- AI paneli iki sekmedir.
- **Edit sekmesi:**
  - İstek kutusu.
  - Tek satır ayar: stil, motion, kapsam, teslim.
  - Tek ajan ya da ekip seçimi.
  - Ekipte seviye segmenti (low…max ve ekip sayısı).
  - Katlanır "Ekip ayarları": üç grup, slot ezmesi, eşzamanlılık, ön ayar.
  - Tek birincil düğme.
  - Çalışırken kapı adımları ve ajan kartları. Karta tıklayınca o ajanın günlüğü açılır.
  - Altta son edit özeti ve geri al.
- **Sohbet sekmesi:** motor, model, mod, günlük ve mesaj kutusu.

## Sonuçlar
- CLI: `vedit ai-edit <proje> --ekip [--seviye low|medium|high|xhigh|max] [--tekrar-denetle]`. `--ekip-v1`, `--bolus` ve `--tur` kaldırıldı.
- Rol dosyaları:
  - Yeni: `ekip-orkestrator`, `kk-genel`, `kk-kural`, `kk-izleyici`.
  - Görev kartı ve `kural_uyum` için güncellenen: `editor-*`, `kk-*`.
- Stüdyo `/cikti/{slot}` ucu artık `ekip/<kapı>/<slot>.cikti.txt` dosyalarının en yenisini okur. v2'de eski `tur-*` düzenini aradığı için boş dönüyordu.
- `library/ekip.json` v3 biçimine göçtü. Eski 6 slotlu dosya okunurken de göçer: E1 orkestratör olur, E2 editör, K1 kalite kontrol.
- Kapılar `tests/test_ekip.py`, `tests/test_ekip_v3.py`, `tests/test_studio_ekip.py` ve `studio/web/src/paneller/ai/seviye.test.ts` içindedir.
- Uçtan uca test sahte ajanla low, high ve max seviyelerini koşar. Doğrulanan kurallar:
  - O tam 3 çağrı yapar.
  - Bütün editörler ve kalite kontroller çalışır.
  - Uyumu eksik editör kapıda düzeltilir.
  - QC kuralı depoya işlenir ve doğrulanır.
  - Bulgu dilim sahibine gider.
  - Sekiz kapının hepsi geçer.

> [!question] Çıkarım
> Kurgu kesimi değiştikten sonra dilim sınırları yeniden eşlenmez. G6'da sahiplik güncel zaman çizelgesinden hesaplanır, kartın aralık metni ise tabanı gösterir. Gerçek koşuda sorun çıkarsa sınırlar `capa.sekans_zamani` ile taşınmalı.

## Ölçüm
`instagram/1`, seviye `low`, ön ayar `karisik`, istek "hızlı tempolu, sade grafik", 2026-11-22:

| Duvar | Ajan çağrısı | Token | QC P0/P1 | Kural (atanan / yeni / doğrulanan) | Son denetim |
|---|---|---|---|---|---|
| 629 sn | 9 | 1,30 M (K1 tahmini) | 0 / 4 (düzeltildi) | 24 / 2 / 2 | 0 hata, 1 uyarı |

- Sekiz kapının hepsi geçti. Orkestratör varsayılan tabloyu kullanmadı, işi kendi dağıttı: E1 kurgu ve ses efekti aldı, E2 grafik, müzik, altyazı ve tema aldı.
- G2'de E2 bir kez düzeltildi, kapı temiz kapandı. QC'nin iki kural adayı depoya işlendi ve depoda doğrulandı.
- v2 `piksel-8bit` ile karşılaştırma: 1,70 M token, 849 sn. v3 `low` %23 daha az token harcadı ve %26 daha kısa sürdü.
- Orkestratörün üç çağrısı toplam 537 bin token tuttu, çoğu sabit bağlamdır.
- İlk deneme G3 taslak render'ında makine belleği dolduğu için Claude Code tarafından durduruldu. Çözüm iki adımlı:
  - Koşu Claude Code'un arka plan kabuğu dışında, ayrı bir pencerede çalıştırıldı.
  - `hf_kurgu.isci_sec` render işçisini boş belleğe göre seçiyor.
  - Bu koşuda boş bellek 7,7 GB'tı; render otomatik işçiyle 85 sn sürdü.

## İlgili kod
- `src/vedit/ekip_v3.py`: atama, plan, kapılar, orkestratör paketleri, akış.
- `src/vedit/ekip_sema.py`: seviye, `EkipAyar`, `Gorev`, `Plan`, `KapiCikti`, `Triyaj`, `Yama.kural_uyum`.
- `src/vedit/ekip.py`: ayar ve göç, `Durum.kapi`, ajan çağrısı, zaman bölüşü, QC girdisi.
- `src/vedit/studio/ekip.py`, `src/vedit/cli.py`.
- `studio/web/src/paneller/AjanPaneli.tsx`, `studio/web/src/paneller/ai/`.
- `.claude/agents/ekip-orkestrator.md`, `kk-genel.md`, `kk-kural.md`, `kk-izleyici.md`.
