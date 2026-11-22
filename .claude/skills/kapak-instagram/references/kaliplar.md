# Instagram Reels kapak kalıpları

Kaynak: `wiki/sources/2026-11-15-kapak-kalip-analizi.md` (24 referans kapak, Antigravity analizi). `vedit kapak` brief isteğine bu dosyayı ekler; brief her aday için `kalip`, `ek` ve `stil` seçer. Yalnız kalıp alınır: kişi yüzü, logo ve tasarım kopyalanmaz.

## Kalıp seçimi
| `kalip` | Ne zaman | `satir1` / `satir2` | `ek` | Zemin |
|---|---|---|---|---|
| `seri` | Varsayılan seri şablonu: 24 referansın 22'si | Altta iki satır, toplam 4-6 kelime, satır başına en çok 16 karakter (taşan satır bölünür); ikinci satırın tamamı renkli kutuda | Üstte tek marka ya da konu sözü ("Claude"); başın arkasında durur | Özne ortada baş ve omuz, kameraya bakıyor, koyu sade zemin, başın iki yanı boş |
| `klasik` | Tek nesne ya da ekran; yüz yok | İki satır, en çok 6 kelime | yok | Ana nesne ortadaki 3:4 alanda |
| `yazisiz` | Görsel tek başına anlatıyorsa | çizilmez | yok | Özne ortadaki 3:4 alanda |

`seri` kalıbında iki yandaki simge kartları kullanıcının girdi klasörüne koyduğu `logo1.png` ve `logo2.png` dosyalarıdır (üretilmez, başkasının logosu kopyalanmaz). Dosya yoksa kartlar çizilmez.

## Ölçülü kurallar (referanslardan)
- Toplam (marka sözü + iki satır) en çok 7 kelime; referans ortalaması 6.
- Yazı ve yüz ortadaki 1080×1440 alanda (ızgara 3:4); üstten ve alttan 240 px'e hiçbir şey girmez.
- İfade sakin: hafif gülümseme ya da ciddi bakış; referansların hiçbirinde abartılı şok yok.
- Izgarada bütün kapaklar tek seri gibi görünür: aynı kalıp, aynı stil, yalnız söz ve zemin değişir.

## Yazı stili (`stil`)
`kirmizi-kutu` referans serinin stilidir (beyaz yazı, ikinci satır kırmızı kutuda). Diğerleri: `turuncu` (proje varsayılanı), `mavi-kutu`, `sari-vurgu`, `beyaz-kontur`, `acik-siyah` (yalnız açık zemin), `serif-karisik`. Stüdyo `studios/instagram/kapak.json` (`{"stil": "..."}`) ile stilini sabitlerse brief'in önerisi ezilir.
