---
type: decision
title: "Kapak özelliği kaldırıldı: Kapak alanı, vedit kapak, teslimde kapak karesi ve iki kapak skill'i"
status: accepted
tags: [adr, kapak, temizlik, studio, teslim]
created: 2026-11-24
updated: 2026-11-24
sources: ["[[0027-kapak-sayfasi]]", "[[0052-kapak-is-akisi-v2]]", "[[0025-gorsel-uretimi-google]]"]
---

# ADR 0056: Kapak özelliği kaldırıldı

## Bağlam
Kullanıcı kapak (thumbnail) özelliğinin tamamen kaldırılmasını istedi (2026-11-24). Kapak işi uygulamada ayrı bir alan, 11 API ucu, 1074 satırlık bir modül, iki skill ve beş test dosyası taşıyordu. Hızlandırma ve swarm edit işlerinden önce yük azaltılır.

Şart: çalışan başka hiçbir özellik bozulmaz. Kapak dosyasını kullanan başka bir özellik varsa dosya taşınır, silinmez.

## Seçenekler
- Kapağı gizlemek (arayüzden kaldırıp kodu bırakmak): ölü kod kalır, testler ve bağımlılık (`rembg`) yük olmaya devam eder.
- Tamamen kaldırmak: seçildi.

## Karar
Repo `kapak|thumbnail|cover` için tarandı; her eşleşme sil, düzenle ya da tut olarak sınıflandı.

**Silinenler**
- `src/vedit/kapak.py`, `src/vedit/kapak_prompt.py`, `vedit kapak` komutu.
- `vedit teslim --kapak-kare` ve `teslim.kodla(kapak=)`: kapağı 0. kareye gömme ([[0040-ikinci-repo-dalgasi]]).
- Stüdyo: Kapak çalışma alanı (Alt+4), `paneller/kapak/` (12 dosya), kapak CSS'i, `/api/kapak/*` uçları, iş kuyruğundaki `kapak` komutu ve yalnız onun kullandığı `_agy_model`, `_tek_satir`.
- Eski `/video` hattındaki `export.covers()` (`renders/covers/cover*.jpg`).
- `kapak-youtube` ve `kapak-instagram` skill'leri ve ajan kopyaları.
- `library/kapak/stiller/`, `pyproject.toml` `kapak` extra'sı (`rembg`).
- Testler: `test_kapak.py`, `test_kapak_v2.py`, `test_kapak_prompt.py` ve diğer dosyalardaki kapak testleri. Yerine kaldırmayı doğrulayan iki test geldi: `kapak` iş komutu 400, `/api/kapak/...` 404.

**Taşınanlar**
- `library/kapak/sablon.html` → `library/gorsel/sablon.html`. `gorsel-uret` skill'i durağan görsele kodla yazı eklerken bunu kullanır ([[0025-gorsel-uretimi-google]]).
- Font tablosu `kapak.FONTLAR` → `pano.FONTLAR`. `vedit pano -o x.jpg` tek kare render'ı bunu kullanır. Renk beyaz listesindeki girdi `pano.py`'ye geçti.

**Düzenlenenler**
- `vedit yayin` istemi artık kapak yazısı satırı taşımaz ([[0055-teslimde-yayin-metni]]).
- `gorsel-uret`, `uretim-hatti`, `viral-kurgu`, `yt-package`, `video` skill'leri ve CLAUDE.md.

**Kalanlar**
- `stil.kapak_yolu` ve `GET /api/stil/{stüdyo}/{ad}/kapak`: stil kartının önizleme görselidir, kapak özelliği değildir ([[0029-stil-paneli]]).
- "İlk kare kapak gibi okunur" kurgu ilkesi (stüdyo CLAUDE.md, [[instagram-studyosu]]) ve `library/yayin/platformlar.json` içindeki Reels kapak yazısı bilgisi: platform bilgisidir.
- Kaynak sayfaları ve geçmiş log girdileri tarih kaydıdır.

## Sonuçlar
- Stüdyo sunucusu bilinmeyen `/api/`, `/dosya/`, `/pub/` yolunda artık 404 döner; eskiden SPA'ya düşüp 200 `index.html` veriyordu.
- Stüdyo üç çalışma alanına döndü: Kurgu, Teslim, Kütüphane (Alt+1..3). Kayıtlı `studio.alan = kapak` açılışta Kurgu'ya düşer.
- Kapak görseli bu projede üretilmez. `yt-package` kapak metnini yalnız metin olarak önerir.
- [[0027-kapak-sayfasi]] ve [[0052-kapak-is-akisi-v2]] `superseded`.

## İlgili kod
`src/vedit/pano.py`, `src/vedit/teslim.py`, `src/vedit/export.py`, `src/vedit/yayin.py`, `src/vedit/cli.py`, `src/vedit/studio/app.py`, `src/vedit/studio/isler.py`, `studio/web/src/main.tsx`, `studio/web/src/zaman/kisayol.ts`, `library/gorsel/sablon.html`, `tests/test_studio_dosya.py`, `tests/test_studio_kurgu_api.py`.
