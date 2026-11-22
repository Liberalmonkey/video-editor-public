---
disable-model-invocation: true
name: decide
description: Mimari veya teknoloji kararı için ADR (Architecture Decision Record) oluştur ya da güncelle — wiki'deki kaynakları topla, seçenekleri karşılaştır, kararı wiki/decisions/'a yaz. Kullanıcı "/decide", "karar verelim", "X mi Y mi" dediğinde kullan.
argument-hint: <karar konusu>
---

# /decide

Konu: $ARGUMENTS

Önce `.claude/wiki-kurallari.md`'yi oku.

1. `wiki/index.md` → ilgili concept/entity/source sayfalarını oku; kod varsa `graphify query` ile etkilenecek modülleri bul.
2. Mevcut ADR'leri kontrol et: bu konu daha önce karara bağlanmış mı? Öyleyse yeni ADR eskisini `supersedes` eder; eskisinin `status: superseded` ve `superseded_by:` alanlarını güncelle.
3. Seçenekleri trade-off tablosuyla sun (performans, lisans, maliyet, karmaşıklık, yerel/bulut, ekosistem). Bilgi eksikse eksikliği belirt ve araştırma öner.
4. Kararı kullanıcıyla netleştir. Kullanıcı onaylamadan `status: accepted` yapma; aksi hâlde `proposed`.
5. Sıradaki numarayla `wiki/decisions/NNNN-kisa-baslik.md` yaz (`templates/decision.md`). İlgili spec/concept sayfalarından link ver, overview'u güncelle.
6. index + `log.md` (`decision`) güncelle, `python scripts/wiki_lint.py` çalıştır.
