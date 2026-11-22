---
disable-model-invocation: true
name: lint
description: LLM Wiki sağlık kontrolü — kırık link, öksüz sayfa, eksik frontmatter, çelişkiler, eskimiş iddialar, eksik kavram sayfaları ve wiki↔kod tutarsızlıkları. Kullanıcı "/lint", "wiki'yi kontrol et" dediğinde kullan.
---

# /lint

Wiki'yi denetler, düzeltmez. Bulguları kullanıcı ayıklar; düzeltme onaydan sonra gelir. Ölçütler `.claude/wiki-kurallari.md`'dedir, önce onu oku.

## Akış
1. **Mekanik.** `python scripts/wiki_lint.py`: kırık link, eksik frontmatter, index dışı sayfa.
2. **Anlamsal.** `wiki/index.md`'den başlayarak sayfaları oku, şu sırayla ara:
   1. **Çelişki:** iki sayfa aynı varlık, karar ya da durum için bağdaşmayan iddia taşıyor. İkisini de alıntıyla göster.
   2. **Eskimiş iddia:** daha yeni kaynak ya da ADR ile geçersiz kalmış; `superseded` olması gerekirken `accepted` duran karar, `draft` kalmış spec.
   3. **Öksüz sayfa:** index'te yok ve hiçbir sayfadan link almıyor.
   4. **Kavram boşluğu:** üç ya da daha çok sayfada geçen ama kendi sayfası olmayan terim.
   5. **Kırık link.**
   6. **Zayıf kaynak:** önemli iddia kaynaksız ya da yalnız wiki'nin kendisine dönüyor.
   7. **Index ve log kayması.**
3. **Wiki ile kod.** `graphify-out/graph.json` varsa `graphify query` ve `graphify explain` ile ADR ya da spec'te yazan komut, dosya ve bayrağın kodda var olup olmadığına bak.
4. **Büyük wiki'de dağıt.** Sayfa sayısı fazlaysa denetimi `wiki-bakici` ajanına ver (Antigravity: `python -I ~/.claude/skills/antigravity/scripts/agy_gorev.py gorev "<kapsam>" --ajan wiki-bakici --out work/agy/<tarih>-wiki-lint.md`). Yanıtı örnekleyerek doğrula.
5. **Rapor.** İlk satır sayı: `kritik N, orta N, düşük N`. Her bulgu tek satır: sayfa, 1-2 satır kanıt, öneri, sonraki işlem (`/ingest`, `/wiki-index`, `/decide`, elle inceleme).
   - **kritik:** çelişki, etkin sayfaya kırık link, uydurma kaynak.
   - **orta:** eskimiş iddia, zayıf kaynak, büyük kavram boşluğu, wiki-kod tutarsızlığı.
   - **düşük:** öksüz sayfa, index ve log kayması.
   Ciddiyetten emin değilsen orta yaz, "doğrula" notu düş.
6. **Kayıt.** `wiki/log.md` sonuna `## [YYYY-MM-DD] lint | N bulgu, M kritik` ve sayılar. Bulgu yoksa da yaz; denetimin yapıldığı görünsün.
7. **Düzeltme.** Yalnız kullanıcı onayıyla; sonra lint'i yeniden çalıştır.

## Bitiş denetimi
- [ ] Bulgular ciddiyete göre gruplu; her birinde sayfa, kanıt ve öneri var.
- [ ] Onay gelmeden `wiki/log.md` dışında hiçbir wiki sayfası değişmedi; `raw/` hiç değişmedi.
