---
type: decision
title: "Ses katmanı: Türkçe güç adları, katmanlı kombolar, çeşitleme, vuruş öncesi müzik çekme ve kütüphane ölçümü"
status: accepted
tags: [adr, ses, sfx, olaysesi, kutuphane]
created: 2026-11-12
updated: 2026-11-12
sources: ["[[2026-11-12-ses-efekti-kaynaklari]]"]
---

# ADR: Ses katmanı

## Bağlam
Kullanıcı ses efektlerini "acemi ve vasat" buldu (2026-11-12). İnceleme iki tür sorun gösterdi. Birincisi kütüphaneydi: whoosh, riser ve darbe aileleri zayıftı, kısa seslerin ses yüksekliği yanlış ölçülüyordu. İkincisi `src/vedit/olaysesi.py` idi: modülün başındaki rol olayı sözleşmesi Türkçe güç adlarını (`yumusak`, `orta`, `sert`) ve `KOMBOLAR` anahtarlarını kabul ettiğini yazıyordu, ama kod yalnız İngilizce güç adlarını tanıyordu ve kombo yoktu. Her olay tek ses çalıyordu; profesyonel pratikte büyük anlar katmanlanır, vuruştan önce müzik çekilir, aynı örnek aynı seviyede tekrar etmez ve kesik kuyruk tıklar ([[2026-11-12-ses-efekti-kaynaklari]], Profesyonel pratik). Dosyası olmayan rol olayında `gain_db` sözleşmede tablo seviyesine eklenen farktı, kod ise onu mutlak seviye sayıyordu.

## Seçenekler
- Kütüphaneyi büyütüp planlayıcıyı olduğu gibi bırakmak. Tek katmanlı, sabit seviyeli yerleşim amatör duyulmaya devam eder.
- Katman, perde ve müzik çekmeyi kurgu tarafında (`kurgu.json`) ayrı klipler olarak üretmek. Kurgu şişer, ajan her olay için üç klip yazmak zorunda kalır.
- Planlayıcıda bir olayı rol katmanlarına açmak, çeşitleme ve müzik çekmeyi aynı yerde yapmak. Seçilen.

## Karar
| Konu | Karar | Neden |
|---|---|---|
| Güç adı | `olay.guc` `yumusak\|orta\|sert` kabul eder; içte `soft\|medium\|hard` kalır, eski adlar da çalışır | Sözleşme Türkçe; eski `olaylar.json` dosyaları bozulmaz |
| Olay türü | `olay.tur` `ROLLER` ya da `KOMBOLAR` anahtarı; bilinmeyen tür hatası iki listeyi de yazar | Ajan doğru adı hata mesajından bulur |
| Kombo | `gecis_guclu`: whoosh tepesi kesme karesinden 30 ms önce, kesme karesinde kısa sub darbe −8 dB, en çok 0,5 sn. `vurgu_guclu`: darbe olay anında, kısa ters whoosh ya da riser tepesi aynı anda −6 dB, en çok 0,9 sn. `acilis`: riser tepesi reveal anında (1,5 sn hedef, en çok 2 sn), kısa sub darbe −6 dB, en çok 0,8 sn | Üst katman havayı, alt katman gövdeyi verir; alt katman kısa ve alçak kalır ki üstü boğmasın |
| Yoğunluk | Kombo katmanları `min_aralik` süzgecinde tek olay sayılır, `adet` olayı sayar | Bir olayın katmanları birbirini düşürmez |
| Seçim | Aynı rolde art arda aynı dosya seçilmez; kombo katmanı da rolün sırasına girer. `sert` olay `light` etiketli darbeyi, `yumusak` olay `heavy` etiketliyi geri plana atar. `aday` kategorisi hiçbir rolde yoktur, otomatik seçilmez | Tekrar ve güç uyumsuzluğu amatörlüğün en sık iki nedeni |
| Çeşitleme | Perde ±%3, seviye ±1 dB; ikisi de olay sırası ve katman numarasından tohumlu | Makineli tüfek etkisi kalkar; aynı girdi aynı çıktıyı verir |
| Seviye | Dosyasız olayda `gain_db` tablo seviyesine eklenen farktır; dosyalı olayda mutlak seviye olarak kalır | Sözleşmeye uyum; kurgu klibinin kazancı rol olayını kısar ya da açar |
| Müzik çekme | `orta` vuruştan 150 ms önce müzik −3 dB, `sert` vuruştan 250 ms önce −6 dB iner (40 ms rampa), vuruşta 50 ms'de geri açılır. Eski "200 ms −2,5 dB" kodunun yerini aldı, kombo bir kez çeker | Sektördeki "pre-hit dip": vuruş boşluğa düşer, müzik boğmaz |
| Fade | Planlayıcının yerleştirdiği her seste başta 10 ms, sonda 40 ms fade; kurgu klibinde fade 0 ise aynı değerler eklenir | Kırpılan baş ve kuyruk tıklamasın |

Aynı turda başka adımlarda yapılanlar:
- `sfx._lufs` kısa seslerde 400 ms momentary loudness ölçer; `_olc_eksik` eski kayıtları yeniden ölçer; tepe anı kırpılan baş sessizliğine göre düzeltilir.
- `vedit sfx fetch wyzowl` eklendi: CC0, kodla sentezlenmiş kit, 261 ses. earshot ölçümüyle 40 kayıt `aday` kategorisine alındı.
- OGA owlish ve keyboard paketleri indekslendi.
- `kit.json` `zoom_in`, `zoom_out`, `gecis` yuvaları doldurulmadı; karar kullanıcıda.
- Gerçek kayıt sinematik riser ve sub drop için doğrulanmış CC0 kaynak bulunamadı; kullanıcının indireceği liste `library/sfx/INDIRME-LISTESI.md`.

## Sonuçlar
- Kombolar yalnız terminal `olaylar.json` ile ya da `olay.tur` alanı doğrudan olaysesi'ne geçen yerlerde çalışır. `kurgu.olaylar_uret` `olay.guc` alanını aktarır; hazır efektin ses olayı da aynı yoldan gelir ([[0033-hazir-efektler]]).
- Dosyasız rol olayında `gain_db` artık fark olduğundan, elle mutlak seviye yazılmış eski `olaylar.json` dosyaları daha alçak çalar.
- Kütüphane kombo katmanları için hâlâ sentez ağırlıklıdır (wyzowl, vedit sentezi); gerçek kayıt riser ve sub drop gelince seçim kendiliğinden onlara da açılır.
- 10 ms baş fade, tepesi ilk örnekte olan darbenin atağını biraz yumuşatır; kulakla denenmedi.
- Doğrulandı 2026-11-12: pytest 147 (8 yeni test), `scripts/test_olaysesi.py` birim bölümü. `avatar-reel` olaylarının rol karşılığıyla `planla` çıktısı önce ve sonra karşılaştırıldı. Render alınmadı, kulakla dinlenmedi; ilk gerçek videoda kullanıcı onayı gerekir.

## İlgili kod
- `src/vedit/olaysesi.py` (`GUC_ADI`, `KOMBOLAR`, `DIP`, `dip_egrisi`, `planla`, `_aday`, `_sekillendir`, `calistir`)
- `tests/test_olaysesi_katman.py`, `scripts/test_olaysesi.py`
- `src/vedit/sfx.py` (`_lufs`, `_olc_eksik`, `fetch wyzowl`), `library/sfx/INDIRME-LISTESI.md`
- `.claude/skills/sound-design/SKILL.md`
