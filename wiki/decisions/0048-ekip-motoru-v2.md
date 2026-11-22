---
type: decision
title: "Ekip motoru v2: sözleşme, paralel düzenleme, çapa eşleme, deterministik birleştirme, tek QC"
status: superseded
tags: [adr, ai-edit, ajan, ekip, token]
created: 2026-11-20
updated: 2026-11-22
sources: []
---

# ADR 0048: Ekip motoru v2

> [!note] Güncellendi 2026-11-22
> Yerini [[0053-seviyeli-ekip-orkestrator]] aldı: seviyeli ekip, orkestratör, kapılar. Eski turlu akış (`--ekip-v1`) kaldırıldı. Sözleşme, çapa eşleme ve deterministik birleştirme kuralları v3'te aynen geçerlidir.

> [!note] [[0044-ekip-motoru]]'nün yerini alır.

## Bağlam
v1'de E1 önce çalışıyor, E2 ve E3 sonra geliyor, en çok üç tam tur dönülüyordu. Her editör bütün manifestleri, kurguyu ve kuralları okuyordu.

Ölçülen v1 koşuları (`instagram/1`):
- temiz-kurumsal: yaklaşık 3,38 M token (agy slotları tahmini), 3002 sn duvar saati;
- piksel-8bit: 5,66 M token, 5481 sn duvar saati.

Sonnet K slotlarında 5-8 sn süren, 0 token harcayan çağrılar başarılı sayılıyordu (sessiz başarısızlık). ADR 0044 "E1 değişince vedit yeniden eşlesin" seçeneğini karmaşık diye reddetmişti; kullanıcı bunu istedi (2026-11-19).

## Karar
Akış sabittir, açık uçlu döngü yoktur:
1. **Sözleşme:** tek E1 çağrısı (hook ve sıra) ve vedit `ekip/sozlesme.json`'u yazar: kesim iskeleti, ayrılmış bölgeler, ritim, stil özeti.
2. **Paralel düzen:** E1, E2 ve E3 aynı anda çalışır. Her biri kendi katmanına fark yaması (`Yama`: ekle, guncelle, sil) yazar. Olaylar kaynak kelimesine çapalanır: `capa: {kaynak, kelime | t, once_kare}`. Pano (`ekip/pano.json`) yalnız iki satırlık `claim|constraint|request|done` mesajı taşır.
3. **Birleştirme (deterministik):**
   - E2 ve E3 tabana uygulanır; çapasız olayları vedit çapalar; E1 uygulanır; çapalar yeniden eşlenir.
   - Kesimde düşen kelimenin olayı silinmez, sahibine bulgu olur.
   - Çakışma önceliği: konuşma/kesim > okunurluk > grafik > SFX. Geçiş ortasındaki grafik en çok 0,6 sn itilir; iki hero ya da 0,4 sn'de iki ses olayı sahibine bulgu olur.
   - Başka editörün klibine dokunmak yamayı reddeder. Başka editörün skaler alanı (`motion_tema`, `altyazi` gibi) yalnız o alanı düşürür.
   - Şema hatası yamayı düşürmez: bilinmeyen alt alan atılır, onarılamayan öğe tek başına düşer, kalanı birleşir. Raporda "düşen öğe" sayılır. `bas` yazılmamış çapalı öğenin zamanı çapadan, `sure` yazılmamış native grafiğin süresi meta'daki varsayılandan gelir.
   - Sekans V1 ile biter: taşan müzik ya da grafik V1 sonuna kırpılır, sonra başlayan düşer (`sona_kirp`).
   - Sözleşme, V1 kaynaklarının kelime dizinlerini (`dizin:kelime@sn`) taşır; editörler çapayı tahmin etmez.
   - Yazım rev denetimlidir: kullanıcı Stüdyo'da yazdıysa ezilmez.
4. **QC (bir kez, paralel):** K1-K3 ortak kare ve ölçüm paketiyle çalışır. Birleştirici tekilleştirir (aynı katman, kategori ve örtüşen zamanda en ağır bulgu kalır), katman sahibine yollar, öteki editöre kısıt üretir ve kural adayı yazar (ADR 0047).
5. **Düzeltme (bir kez):** yalnız P0/P1 bulgusu olan editör çalışır, yalnız bulgu farkı ve kısıtlarla. E1 değişmediyse yalnız etkilenen aralıklar paralel render edilip eklenir.
6. **Son:** deterministik denetim yapılır. İkinci QC yalnız P0 kapısı düşerse ya da `--tekrar-denetle` verilirse çalışır.

Token disiplini:
- Bağlam paketi rol başınadır: sabit kısım (rol, şema, kurallar, rolün kataloğu) önce, değişken kısım (sözleşme, kendi katmanı, diğer katmanların 3 satırlık özeti, pano) sonra.
- Manifest, ham medya ve tam kurgu verilmez.
- Çıktı yalnız JSON olur. Boş yanıt başarısızdır.
- Motor token vermezse `(istem + çıktı) / 4 + görsel × 1500` ile tahmin edilir ve "tahmini" diye işaretlenir (kullanıcı kararı).
- Eşzamanlılık varsayılanı 6'dır; AI sayfası slot başına süre ve token gösterir.

## Sonuçlar
- Raporda v1 kıyası `ai-edit.rapor.md`'ye yazılır. Hedef: en az %50 daha az token ve daha kısa duvar saati.
- Kapılar: `tests/test_capa.py`, `tests/test_ekip_v2.py`.

## Ölçüm (2026-11-20, `instagram/1`, ön ayar `karisik`)
Tablo, iki stilin yalnız native setle ve aynı ön ayarla (`karisik`) yapılmış son koşusunu, aynı stilin v1 koşusuyla kıyaslar.

| Stil | v1 token | v2 token | Fark | v1 duvar | v2 duvar | v2 ajan çağrısı | QC P0/P1 |
|---|---|---|---|---|---|---|---|
| `temiz-kurumsal` | 3,39 M | 1,69 M | %50 | 7836 sn | 1108 sn | 8 | 0 / 3 |
| `piksel-8bit` | 5,67 M | 1,70 M | %70 | 5481 sn | 849 sn | 9 | 2 / 5 (düzeltildi) |

İki hedef de tuttu. Token en az %50 azaldı. Duvar saati yaklaşık 7 kat kısaldı. agy denetçilerinin (K1-K3) token'ı tahminidir.

Ölçüm koşuları dört birleştirme kusuru buldu. Hepsi kodla kapatıldı ve kapıları `tests/test_ekip_v2.py` içindedir:
- E3 kaynağı `yol` yerine `dosya` alanıyla yazdı. Tek öğe yüzünden bütün ses katmanı düştü.
- E2 çapalı grafiklerde `bas` ve `sure` yazmadı. Bütün grafik katmanı düştü.
- E1 kesimi kısalttı ama müzik kırpılmadı. Taslağın sonunda 4,3 sn siyah kaldı.
- İkonlar kesimden sonra 0,3-0,6 sn sonraki çekime taştı.

Ölçüm iki ek açık bulgu da bıraktı:
- Paket kelime dizinlerini vermiyordu, editörler çapayı tahmin ediyordu. Artık sözleşmede.
- Native yerleşim yalnız klibin ilk karesindeki yüzlere bakıyordu. Artık klip boyunca görünen yüzlere bakıyor (`Katman.tsx`). Yine de yakın planda büyük parçacık grafiğine (konfeti) temiz yer kalmıyor. Bu bulgu açık.

Ara koşuların çıktıları `work/edit/ekip-v2-*-{e3red,e2red,sureyok,dizinsiz}/` altındadır. Son koşular `ekip-v2-temiz-kurumsal/` ve `ekip-v2-piksel-8bit/` altında. Yan yana görsel `work/edit/karsilastirma-v2-piksel-vs-temiz.jpg`.

## İlgili kod
`src/vedit/ekip_v2.py`, `src/vedit/capa.py`, `src/vedit/ekip_sema.py` (`Yama`, `Mesaj`), `src/vedit/ekip.py` (ortak ajan çağrısı, izle), `src/vedit/cli.py`
