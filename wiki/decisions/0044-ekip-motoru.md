---
type: decision
title: "Ekip motoru: 3 editör + 3 kalite kontrol ajanı, turlu düzeltme"
status: superseded
tags: [adr, ai-edit, ajan, studio, denetim]
created: 2026-11-19
updated: 2026-11-20
sources: []
---

# ADR 0044: Ekip motoru

> [!note] Güncellendi 2026-11-20: yerini [[0048-ekip-motoru-v2]] aldı. 2026-11-22: turlu akış ve `--ekip-v1` kaldırıldı ([[0053-seviyeli-ekip-orkestrator]]).

## Bağlam
[[0028-ai-edit|ADR 0028]]'deki `vedit ai-edit` tek ajanla tek geçişte kurgu yazıyordu. Ek turlar yalnız şema hatası ve motion yoğunluğu içindi; kimse taslağı izlemiyordu. `instagram/1` editinde koyu zeminde okunmayan yeşil vurgu, stile aykırı turuncu altyazı ve şablon görünümlü grafikler yayına kadar fark edilmedi. Kullanıcı kesim, grafik ve ses için ayrı editörler, her birinin işini izleyen ayrı kalite kontrol ajanları ve slot başına motor ve model seçimi istedi.

## Seçenekler
- Üç editör aynı anda: E1 zaman çizelgesini değiştirince E2 ve E3'ün eski zamanlara yazdığı grafik ve ses kayar. Reddedildi.
- Kesimi kilitleyip üçünü paralel çalıştırmak: hook'u öne alma gibi kurgu kararları kaybolur. Reddedildi.
- E1 değişikliğinden sonra E2/E3'ü vedit'in yeniden eşlemesi: karmaşık, yanlış eşleme riski. Reddedildi.
- **E1 önce, E2 ve E3 paralel** (seçildi; kullanıcı kararı, 2026-11-19). K1-K3 her zaman paralel.

## Karar
| Konu | Karar |
|---|---|
| Komut | `vedit ai-edit <proje> --ekip [--bolus rol\|zaman] [--tur 3] [--ekip-dosyasi …] [--sifirdan]`. `--ekip` yoksa eski tek ajan akışı aynen çalışır |
| Hazırlık | Deterministik: `hazirla`, `_kurgu_hazirla`, `_istek_yaz` bağlamı (kurallar, kataloglar, ritim, stil teması) `work/edit/ekip/baglam.md`'ye |
| Sahiplik (rol) | E1 `V1` (+`A1`) ve `isaretler`; E2 diğer görüntü izleri; E3 diğer ses izleri, `altyazi`, `motion_tema`. Var olan kaynak değiştirilemez, yalnız eklenir |
| Sahiplik (zaman) | Süre kelime sınırında üçe bölünür (hedef noktaya en yakın kelime arası boşluk); her editör bir aralığın bütün izlerine sahiptir, aralığın süresi sabittir. Bulgunun hedefi zamanından bulunur; K2 aralık sınırlarında stil sürekliliğine de bakar |
| Parça | Editör yalnız `tur-N/E*.json` yazar (`ekip_sema.Parca`). Birleştirme deterministik: sahiplik, kimlik tekrarı, şema, `kurgu.denetle`; geçmeyen parça birleşmez |
| Kalite kontrol | K1 kurgu ve ritim (→E1), K2 görsel ve stil (→E2), K3 ses, altyazı ve okunurluk (→E3). Plan modunda (salt okunur) çalışır, yanıtın sonunda tek JSON bloğu verir. Girdi: taslak, kontak sayfası, `video-izle` kareleri ve OCR (+1,5 sn'de bir sabit kare), `vedit denetim` ölçümü (format, loudness, slop), `kurgu-denetle`, stil token'ı |
| Bulgu | `{"id","hedef","onem","zaman","katman","kategori","kanit","sorun","beklenen"}` şeması (`ekip_sema.Bulgu`). Kanıt karesi diskte yoksa bulgu düşer. Her K editörüne brif yazar (bağlam, P0→P2, zaman damgası, ölçülebilir kabul ölçütü, dokunulmayacaklar) |
| Döngü | Düzeltme turunda yalnız P0/P1 bulgusu olan editör çalışır; E1 zaman çizelgesini değiştirdiyse E2 ve E3 de çalışır. P0/P1 kalmayınca ya da `--tur` dolunca durur. Kapanan bulgu: sonraki turda aynı hedef, kategori ve örtüşen zamanda yeniden gelmeyen |
| Hata | Bir yeniden deneme (ret sebebi isteme eklenir), sonra slotun yedek motoru; o da olmazsa önceki turun durumu kalır |
| Güvenlik | Komut yalnız `motorlar.komut` ile kurulur; bypass bayrağı yok. Seviye bayrağı: Claude ve agy `--effort`, Codex `-c model_reasoning_effort` |
| Günlük | `work/edit/ekip/tur-N/`: her slotun istemi, ham akışı (`.cikti.jsonl`), okunur çıktısı, `meta.json` (motor, model, seviye, süre, token, deneme, yedek), bulgu ve brifler; `durum.json` canlı |
| Rapor | `ai-edit.rapor.md`: ekip tablosu, turlar (çalışan editör, süre, açık P0/P1/P2), kapanan ve açık bulgular. P0 açıksa `--final` atlanır, teslim kararı kullanıcıda ([[0015-ai-slop-denetimi]]) |
| Ayar | `library/ekip.json` ön ayarlar ve varsayılan; proje ezmesi `work/edit/ekip.json`; sıra: varsayılan ön ayar < proje < `--ekip-dosyasi` < CLI bayrağı |
| Stüdyo | AI panelinde "Ekip modu": 6 slot (motor, model, seviye, yedek motor ve model), listeler canlı taramadan (`motorlar.durum`, seviye listesi dahil); kurulu olmayan motor soluk ve sebebiyle. Bölüş, tur, eşzamanlılık; ön ayar kaydet, varsayılan yap, projeye kaydet. Slot rozetleri, tur, açık P0/P1/P2, ajan başına çıktı sekmesi, "Hepsini durdur" (iş iptali, süreç ağacı kapanır). API `src/vedit/studio/ekip.py` |
| Rol dosyaları | `.claude/agents/{editor-kurgu,editor-grafik,editor-ses-stil,kk-kurgu,kk-gorsel,kk-ses}.md`; `scripts/ajan_esitle.py` Antigravity kopyasını üretir |

Örnek ön ayar `karisik`: E1 Claude Opus 5.5 (high), E2 ve E3 Claude Sonnet 5.5; K1 agy `gemini-4-argon-high`, K2 agy `gemini-4-neon-high`, K3 agy `gemini-4-neon-xhigh`. Kullanıcının Codex aboneliği olmadığı için K slotlarında Codex yok; Codex kurulu olduğundan panelde seçilebilir görünür, giriş yoksa çağrı hata verir ve yedek motora geçilir.

## Sonuçlar
- Tur süresi E1 + max(E2, E3) + render + izleme + max(K1..K3). Düzeltme turunda bulgusuz editör çalışmaz.
- `earshot` Python modülü proje ortamında kurulu değil; K3 ses ölçümünü `vedit denetim` (ffmpeg loudness, slop olay ölçümü) ve olay sesi listesinden alır.
- Plan modundaki K ajanı dosya yazamaz; bulgu yanıt metnindeki JSON bloğundan okunur, dosyayı vedit yazar.
- Stil ekipte `--stil` ile seçilir; katalog stili stüdyoda yoksa önce eklenir ([[0043-stile-bagli-tema-tokenlari]]).

## İlgili kod
`src/vedit/{ekip,ekip_sema,motorlar,cli}.py`, `src/vedit/studio/{ekip,isler,app}.py`, `studio/web/src/paneller/{EkipPaneli,AjanPaneli}.tsx`, `library/ekip.json`, `.claude/agents/{editor-*,kk-*}.md`, `tests/{test_ekip,test_studio_ekip}.py`.
