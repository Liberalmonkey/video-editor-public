---
type: decision
title: "Kural deposu ve Kurallar sayfası: QC bulgusundan genelleşmiş kural, mezar taşı, rol başına teslim"
status: accepted
tags: [adr, kurallar, denetim, ai-edit, studio]
created: 2026-11-20
updated: 2026-11-20
sources: []
---

# ADR 0047: Kural deposu

## Bağlam
`library/checks.md` elle büyüyen bir listeydi (ADR 0014, 0041). Bilinmeyenler:
- hangi editörün hangi kurala uyacağı;
- hangi kuralın tekrarlandığı;
- kullanıcının hangisini istemediği.

Kalite kontrol bulguları tek seferlik nottu ve aynı ders her videoda yeniden bulunuyordu.

## Karar
- **Depo:** tek kaynak `library/kurallar/kurallar.json` + `kurallar.schema.json` (Pydantic `src/vedit/kural.py`).
  - Alanlar: `id, metin (YAP:/YAPMA:), neden, kapsam (global|studyo|stil|proje), kapsam_deger, hedef_rol (E1|E2|E3|hepsi), kategori, onem (P0-P2), kaynak (kullanici|kk:<ajan>), kanit[], durum (aktif|oneri|pasif|silinen), tekrar, olcut, tarihler`.
  - `checks.md` depodan üretilir; okuyan skill'ler aynı yolu okur. Göç tek seferliktir (`vedit kural goc`): 25 kural taşındı, yedeği `library/kurallar/checks.goc-oncesi.md`.
- **QC akışı:**
  - Bulgu `kural_id` (ihlal) ve `kural_adayi` (genelleşmiş tek satır) taşır.
  - Aday benzerine eşlenirse `tekrar` artar. Benzerlik ölçüsü: polarite (YAP/YAPMA) aynıyken token Jaccard, ya da en az 3 token üstünde kapsama × 0.9.
  - Yeni kural varsayılan olarak `aktif` olur; "Yeni kurallar onayımı beklesin" ayarı açıksa `oneri` olur.
- **Mezar taşı:** silinen kural `silinen` durumunda kalır. Benzeri aday düşer, QC yeniden önermez; kullanıcı açarsa geri gelir.
- **Teslim:**
  - `kural.paket(rol, stüdyo, stil, proje, bütçe)` P0 → P2 sıralar; P0 asla düşmez, sığmayan P2 tek satır özet olur.
  - Editör isteğine (`ai-edit.istek.md`, ekip paketi) ve QC istemine girer.
- **Kapı:** `tekrar >= 2` ve ölçülebilir kural kapı önerisi olarak listelenir (ADR 0041).
- **Arayüz:**
  - CLI: `vedit kural liste|ekle|sil|ac|kapat|onayla|reddet|disa|ice|goc`.
  - API: `/api/kurallar`.
  - Stüdyo Kütüphane alanında "Kurallar" sayfası.

## Sonuçlar
- İki kez gelen anticipation ve yazı boyu kusurları koda yazıldı (`tests/test_motion_kurallari.py`).
- Kullanıcının elle eklediği kural her zaman aktiftir; aynısı yeniden eklenirse `tekrar` artar.

## İlgili kod
`src/vedit/kural.py`, `src/vedit/studio/kurallar.py`, `studio/web/src/paneller/KurallarPaneli.tsx`, `src/vedit/aiedit.py`, `src/vedit/ekip.py`, `tests/test_studio_kurallar.py`
