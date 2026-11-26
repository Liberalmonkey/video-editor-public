---
type: decision
title: "Teslimde yayın metni: video başına, platforma göre başlık, açıklama ve hashtag"
status: accepted
tags: [adr, teslim, yayin, studyo, ajan, viral-kurgu]
created: 2026-11-23
updated: 2026-11-24
sources: ["[[0035-teslim-ayarlari]]", "[[0026-arayuzde-ajan]]", "[[0028-ai-edit]]", "[[0046-dis-varlik-ve-lisans]]"]
---

# ADR 0055: Teslimde yayın metni

> [!note] Güncellendi 2026-11-24: istem artık kapak yazısı taşımaz; kapak özelliği kaldırıldı ([[0056-kapak-kaldirildi]]).

## Bağlam
Kullanıcı, Stüdyo'nun Teslim sayfasında her video için yayınlanacağı platforma uygun, profesyonel başlık, açıklama ve hashtag istedi (2026-11-23). Varsayılan model Claude Opus 5.5 olmalı. Codex, Antigravity ve OpenCode da seçilebilmeli ve kullanıcı istediği modeli seçebilmeli.

Önceki durum:
- `yayin.md` yalnız terminal hattında yazılıyordu: `viral-kurgu` skill'ini okuyan ajan dosyayı elle düzenliyordu.
- Proje başına tek dosya vardı; birden çok teslim videosunda bölümler karışıyordu.
- Sınırlar (karakter, hashtag sayısı) denetlenmiyordu.

## Karar
1. **Yeni komut `vedit yayin <proje> [--video ad.mp4 | --hepsi] [--platform …] [--motor …] [--model …] [--seviye …] [--dil tr|en]`.** Varsayılan motor `claude`, model `claude-opus-5-5`. Motor ve model listesi `motorlar.py` tablosudur; AI paneliyle aynıdır.
2. **Kanıt paketi istek dosyasıdır** (`work/yayin/istek-<video>.md`). İçeriği:
   - Teslimin yanındaki SRT. Yoksa `digest.txt`, o da yoksa `senaryo.md`.
   - Süre, stüdyo, stil ve varsa kapak yazısı.
   - `checks.md`'deki yayınla ilgili kurallar.
   - Platform reçeteleri ve çıktı şeması.
   
   Ajan `ajan_cagri.calistir` ile çalışır ve yalnız `work/yayin/<video>.json` yazar. `dosyadan` kullanılmaz: o kabuk komutunu yasaklar ve Codex'in tek dosya aracı kabuktur. 2026-11-23 denemesinde Codex istek dosyasını bu yüzden okuyamadı. Bu istemde yalnız dosya basan okuma komutlarına (`Get-Content`, `cat`) izin verilir; yazma tek hedef dosyadır.
   
   Dosyayı yazamayan motor (izin ya da sandbox) JSON'u yanıtında tek bir ```json bloğu olarak verir; vedit oradan alır (`yanittan_json`).
   
   Gerçek koşu (`instagram/arvelior`):
   - Claude Opus 5.5 (reels + linkedin): 51 sn.
   - Codex (reels + tiktok): 60 sn.
   - Antigravity (reels): 88 sn.
   
   Üçü de ilk turda doğrulamadan geçti.
3. **Doğrulama vedit'tedir.** Pydantic şeması ve reçete sınırları denetlenir:
   - başlık ve açıklama karakteri;
   - hashtag sayısı, biçimi ve tekrarı;
   - YouTube etiket toplamı ve `<` `>` yasağı;
   - bölüm zamanları.
   
   Hata varsa ajan aynı oturumda bir kez düzeltir. İkinci hata işi durdurur. Önceki geçerli paket geri konur, hatalı çıktı `.hatali.json` olarak saklanır.
4. **Platform reçetesi tek dosyadır: `library/yayin/platformlar.json`.** Platformlar `reels`, `youtube`, `shorts`, `tiktok` ve `linkedin`. Sınırlar 2026-11-23'te doğrulandı:
   - Instagram: 2.200 karakter, en çok 5 hashtag (Aralık 2025'ten beri).
   - YouTube: başlık 100, açıklama 5.000, etiket toplamı 500 karakter.
   - TikTok: uygulama içi açıklama 4.000 karakter, en çok 5 hashtag.
   - LinkedIn: 3.000 karakter.
   
   Kurallar `viral-kurgu`'nun Yayın paketi bölümünün özetidir. TikTok kuralları araştırılmadı (`arastirildi: false`); metin genel kurallarla yazılır ve panel bunu rozetle gösterir. Stüdyo varsayılanları: `instagram` → reels, `youtube-animasyon` → youtube, `ugc` → reels.
5. **`yayin.md` video başına işaretli bloktur:** `<!-- yayin:<video> -->` … `<!-- /yayin:<video> -->`.
   - Bloklar doğal dosya adı sırasıyla dizilir.
   - Blok dışındaki elle yazılmış metin başta kalır.
   - ADR 0046'nın atıf bölümü sonda kalır; `atif_yaz` blokları bozmaz.
   - Kopyalanacak metin açıklama, (YouTube'da) bölümler ve hashtag satırından oluşur. Python `yayin.kopya_metni` ile arayüz `kopyaMetni` aynı biçimi üretir.
6. **Stüdyo: Teslim alanında "Yayın metni" paneli** (Çıktı ayarlarının yanında sekme; yerleşim anahtarı `v4`). Panelde şunlar var:
   - Motor, model, akıl yürütme seviyesi ve dil seçimi, `localStorage` `studio.yayin.motor` anahtarında saklanır.
   - Platform onay kutuları; stüdyo varsayılanı işaretli gelir.
   - Video listesi: süre, SRT ve paket durumu (yok, hazır, eski). Her satırda "Üret" düğmesi, altta "Hepsini üret".
   - Platform sekmelerinde düzenlenebilir alanlar, sınır sayaçları, kopyala düğmeleri ve "Kaydet" (`PUT /api/yayin/...`, ajan çağrılmaz, aynı doğrulama).
   
   Üretim iş kuyruğunda `vedit yayin` olarak çalışır. Motor, model ve seviye canlı listeden doğrulanır (`isler.yayin_arguman`).
7. **Yalnız düğmeyle.** Export ajan çağırmaz kuralı (ADR 0035) korunur. Yayın metni token harcar, kullanıcı ne zaman üretileceğini seçer.

## Sonuçlar
- Her teslim videosu, kendi platform bölümleriyle `yayin.md`'de ayrı ve kopyalanmaya hazır durur. Ham veri `work/yayin/<video>.json`'dadır.
- Paket videodan eskiyse (video yeniden export edildiyse) panel "eski" rozeti gösterir.
- Yeni platform eklemek için önce kuralları araştırılır, sonra reçeteye satır eklenir. Kod değişmez.
- Test: `tests/test_yayin.py`, `studio/web/src/paneller/YayinPaneli.test.ts`.
