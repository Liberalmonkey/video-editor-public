---
disable-model-invocation: true
name: ingest
description: Yeni bir kaynağı (dosya, URL, video, not) LLM Wiki'ye işle — raw/'a kaydet, özetle, ilgili concept/entity/decision/spec sayfalarını güncelle, index ve log'u güncelle. Kullanıcı "ingest", "wiki'ye ekle", "bu kaynağı işle" dediğinde kullan.
argument-hint: <dosya yolu | URL | "raw/ içindeki yeniler">
---

# /ingest

Tek bir kaynağı kalıcı, birbirine bağlı wiki bilgisine çevirir. Argüman: $ARGUMENTS

## Önce bağlam
1. `.claude/wiki-kurallari.md` (dosya adı, frontmatter, link ve yazım kuralları).
2. `wiki/index.md`: ne var.
3. Son 20 log girdisi: `grep "^## \[" wiki/log.md | tail -20`. Aynı kaynağı ikinci kez işleme, başkasının çözdüğü çelişkiyi yeniden açma.

## Akış
1. **Kaynağı yerleştir.** `raw/` değişmezdir.
   - `raw/` içindeyse olduğu gibi kullan.
   - URL (makale): markdown'a çevir, `raw/articles/YYYY-MM-DD-kisa-baslik.md`; başına `source_url:` ve erişim tarihi.
   - YouTube ya da podcast: `graphify add <url>` ile transkript al ya da transkripti `raw/transcripts/`'e koy.
   - PDF: `raw/papers/`.
   - Argüman "yeniler" ise: `raw/` altında olup `wiki/sources/*.md` içindeki `raw:` alanlarında geçmeyen dosyaları bul, sırayla işle.
2. **Baştan sona oku.** Göz gezdirme. Yapıyı, iddiaları, tarihleri ve var olan sayfalarla çelişen yerleri not et. Görsel varsa önce metin, sonra ilgili görseller.
3. **Planla, kullanıcı varsa sor.** 3-5 ana çıkarımı ve projeye etkisini kısaca söyle; toplu ingest istenmediyse neyin vurgulanacağını sor.
4. **Kaynak sayfası.** `templates/source.md` iskeletiyle `wiki/sources/YYYY-MM-DD-kisa-baslik.md`. Yansız dil; ağırlık taşıyan iddia alıntıyla. Bu sayfa, bu ingest'in yazdığı her şeyin atıf hedefidir.
5. **Yay.** Etkilenen `concepts/`, `entities/`, `decisions/`, `specs/` sayfalarını güncelle ya da aç. Tipik ingest 5-15 sayfaya dokunur. Yalnız bir kez geçen fikir için sayfa açma.
6. **Bağla.** Kaynaktan gelen her iddia `([[kaynak-sayfasi]])` ile atıflanır. İki ya da daha çok sayfada adı geçen kavram ve varlık kendi sayfasına link alır. `updated:` ve `sources:` alanlarını güncelle.
7. **Çelişkiyi işaretle, üstüne yazma.** Eski sayfaya `> [!warning] Çelişki` kutusu, iki görüş ve iki kaynakla. Log'a da yaz.
8. **Sentez.** Büyük resmi değiştiriyorsa `wiki/overview.md`.
9. **Kayıt.** Yeni sayfalar `wiki/index.md`'ye tek satır özetle girer. `wiki/log.md` sonuna:
   ```
   ## [YYYY-MM-DD] ingest | <kaynak başlığı>
   - kaynak: raw/<dosya>
   - yeni: [[...]], [[...]]
   - güncellenen: [[...]], [[...]]
   - not: <tek satır sentez ya da açık soru>
   ```
10. **Graf.** Kod da değiştiyse `graphify update .`. Beş ya da daha çok kaynaklık dalgadan sonra kullanıcıya tam grafik için `/graphify .` öner (token harcar, kendiliğinden çalıştırma).

## Bitiş denetimi
- [ ] Kaynak sayfası geçerli frontmatter ile var, `raw:` ham dosyayı gösteriyor.
- [ ] Yeni ya da güncellenen her sayfa kaynak sayfasına ya da ona bağlanan bir sayfaya link veriyor.
- [ ] `wiki/index.md` her yeni sayfayı doğru başlık altında listeliyor.
- [ ] Log girdisi başlık biçimine uyuyor.
- [ ] Çelişkiler işaretli, sessizce silinmedi.
- [ ] `raw/` altında hiçbir dosya değişmedi.
- [ ] `python scripts/wiki_lint.py` hatasız.

Kullanıcıya dokunulan sayfaların listesini ver.
