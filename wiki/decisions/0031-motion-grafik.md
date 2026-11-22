---
type: decision
title: "Motion grafik: metin türleri, tam ekran sahneler, saydam pano ve proje yapımı motion kütüphanesi"
status: accepted
tags: [adr, motion, remotion, kurgu, ai-edit]
created: 2026-11-12
updated: 2026-11-20
sources: ["[[2026-11-12-motion-grafik-arastirmasi]]"]
---

# ADR: Motion grafik

> [!note] Güncellendi 2026-11-20: yeni grafikler native Remotion bileşenidir (`bilesen: {ad, param}`); metin grafik türleri çalışmaya devam eder ([[0045-native-motion]]).

## Bağlam
Kullanıcı editlerde motion grafik kullanılmasını ve bunun GitHub gibi kaynaklardan nasıl yapılacağının araştırılmasını istedi (2026-11-12). AI edit yalnız düz görsel koyabiliyordu: `library/motion/manifest.json` boştu, `shot` sahnesinin görselini yalnız Stüdyo API'si bağlıyordu, tam ekran sahnelerden yalnız `hook` ve `cta` çiziliyordu, `metin` klibi düz yazıydı, `vedit pano` saydam çıktı veremiyordu ve ajan isteği sahne alanlarını anlatmıyordu.

## Seçenekler
- Topluluk şablonlarını paket olarak almak (`reactvideoeditor/remotion-templates`, `av/remotion-bits`). Araştırma: lisansları MIT ama İngilizce ve ASCII varsayıyor, görünüş tutarsız olur, bağımlılık getirir.
- Remotion'u yükseltip `rough-notation`, `mac-cursors`, `effects` paketlerini kullanmak. Kurulu sürüm 4.0.484; yükseltme ayrı bir test işi.
- Fikri ve matematiği alıp mevcut motorun diliyle (`Reveal`, `ez`, `OUT4`) yeniden yazmak. Seçilen.

## Karar
| Konu | Karar | Neden |
|---|---|---|
| Metin türleri | `metin_stil.tip`: `anahtar`, `altbant`, `etiket`, `cagri`, `daktilo`, `sayac`, `ilerleme`, `bolum`, `vurgu`; tip yoksa eski düz metin | Geriye uyum; her tür giriş ve çıkışını klip süresinden hesaplar |
| Vurgu çizimi | `tip: "vurgu"` + `kutu{x,y,w,h}` + `bicim: kutu\|daire\|alt_cizgi`; `gorsel` klibinde koordinat görselin çizildiği alana göre | Ekran görüntüsünde anlatılan öğeyi işaretlemek |
| Tam ekran sahne | `layout: "full"` ile `text`, `stat`, `chips`, `steps`, `timeline`, `shot`; zemin `dark\|light\|saydam` | SplitReel bileşenleri yeniden kullanılır |
| Shot görseli | `img: "inputs:5.png"`, kaynak kimliği ya da `shot/<ad>`; `kurgu.shot_bagla` hem `hazirla`'da hem Stüdyo API'sinde | Ajan kabuk komutu çalıştıramaz; bağlantıyı `vedit` kurar |
| Saydam pano | `vedit pano -o x.webm`: saydam sayfa, VP9 + alfa | Yer paylaşımlı grafik videonun üstüne biner |
| Kütüphane | `library/motion/custom/<id>/` altında proje yapımı 9 kayıt (ok, daire, alt çizgi, üstünü çiz, vurgu patlaması, konfeti, onay, iki silme geçişi); kaynak HTML git'te, webm üretilir | Katalogdaki panolar 16:9 tanıtım panosu, saydam zeminde kullanılamadı |
| Ajan isteği | `MOTION_OZETI`: her sahne ve metin türü alanlarıyla, motion kataloğu manifest'ten her çalışmada üretilir, "hangi anda hangi grafik" kuralları | İstek koddan sapmasın |
| Güvenli alan | Grafik çapası dikeyde 0,14–0,68, yatayda 0,09–0,74; altyazı bandına ve yüze inmez | Altyazı standardı ([[0014-altyazi-standardi-ve-repo-entegrasyonu\|ADR 0014]]) değişmez |
| Lisans | Yeni paket yok, dış kod kopyalanmadı; Remotion 4.0.484'te kalır | Remotion lisansı 3 kişiye kadar ücretsiz; React Bits (Commons Clause) ve Cap (AGPL) kullanılmaz |

## Sonuçlar
- `kit.json` motion yuvaları doldurulmadı; kilit kararı kullanıcıda. Adaylar: `gecis` için `gecis-sil-dikey` / `gecis-sil-yatay`.
- `openmontage/remotion-composer/src/SplitReel.tsx` iki satır değişti (`bg: "saydam"`); `patches/openmontage.patch` buna göre yenilenir.
- Tam ekran sahneler SplitReel temasını kullanır, vurgu rengi orada sarıdır; metin türleri turuncu `#FF7A00` kullanır.
- Yazı sığdırma harf genişliği tahminiyle yapılır; çok geniş harfli uzun başlıkta taşma olabilir.
- `motion-design` skill'i ve `library/boards/katalog.md` ajan isteğine eklenmedi: ilki eski HyperFrames hattını anlatır, ikincisi kabuk komutu ister.
- Doğrulandı 2026-11-12: her tür için Remotion kare render'ı (dikey ve yatay), saydam webm `alpha_mode=1`; pytest 130, vitest 104.

## İlgili kod
- `studio/remotion/Kurgu.tsx` (`TamSahne`), `studio/remotion/MotionMetin.tsx`, `studio/remotion/metinOlcu.ts`, `studio/remotion/tipler.ts`
- `src/vedit/kurgu.py` (`shot_bagla`, `hazirla`, `denetle`), `src/vedit/pano.py` (`kodlayici`), `src/vedit/aiedit.py` (`MOTION_OZETI`, `_motion_katalogu`), `src/vedit/schemas.py`
- `studio/web/src/paneller/{EfektPaneli,GrafikPaneli,SahneFormu}.tsx`, `sablonlar.ts`, `library/motion/`
