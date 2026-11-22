# Wiki kuralları

Wiki'ye yazan her işlem (ingest, ask, lint, decide, elle düzenleme) önce bunu okur.

## Dizinler
- `raw/` değişmez ham kaynak (LLM yalnız okur): `articles/` (web), `papers/`, `repos/`, `transcripts/`, `notes/` (kullanıcı notları), `assets/` (görseller).
- `wiki/`: `index.md` (katalog), `log.md` (yalnız ekleme), `overview.md` (büyük resim), `sources/`, `concepts/`, `entities/` (araç, kütüphane, model), `decisions/` (ADR), `specs/`, `queries/`.
- `templates/`: sayfa şablonları.

## Dosya adı ve link
- `kebab-case`, ASCII, Türkçe karakter yok. Kararlar `decisions/NNNN-kisa-baslik.md`; kaynaklar `sources/YYYY-MM-DD-kisa-baslik.md`.
- Wiki içinde Obsidian wikilink: `[[ffmpeg]]`, `[[scene-detection|sahne tespiti]]`; ham kaynak `[[raw/articles/dosya]]`.
- İki sayfada anılan ama sayfası olmayan kavram/varlık → sayfasını aç. Yeni sayfa en az bir yerden link alır ve `index.md`'ye girer.

## Frontmatter (zorunlu)
```yaml
---
type: source | concept | entity | decision | spec | query | overview
title: İnsan-okur başlık
tags: [video, ai]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: ["[[2026-10-20-ornek-kaynak]]"]
status: ...   # decision: proposed|accepted|superseded|rejected · spec: draft|active|done|dropped
---
```
Ek: entity `kind: tool|library|model|service|competitor|format`; source `raw:`, `url:`, `author:`.

## Sayfa iskeletleri (`templates/`)
- **source:** Özet · Ana çıkarımlar · Projeye etkisi · Çelişkiler/açık sorular · Bağlantılar
- **concept:** Tanım · Nasıl çalışır · Projede kullanımı · Alternatifler · Kaynaklar
- **entity:** Ne · Yetenekler · Lisans/maliyet · Entegrasyon · Projedeki rolü · Kaynaklar
- **decision:** Bağlam · Seçenekler · Karar · Sonuçlar · İlgili kod
- **spec:** Problem · Kullanıcı hikâyeleri · Kapsam · Tasarım · Kabul kriterleri · Açık sorular
- **query:** Soru · Cevap (alıntılı) · Kullanılan sayfalar · Takip soruları

## Yazım
- İddia kaynağa bağlanır: `([[kaynak-sayfasi]])`.
- Çelişki silinmez: `> [!warning] Çelişki` ile iki görüş + kaynak.
- Eskiyen bilgi: `> [!note] Güncellendi YYYY-MM-DD`; eskisi gerekçeyle üstü çizili ya da `superseded`.
- LLM çıkarımı: `> [!question] Çıkarım`.
- Sayfa kısa ve odaklı; ~400 satırı aşarsa böl.

## index.md ve log.md
- **index:** kategori başlıkları altında `- [[sayfa]] — tek satır özet`. Her ingest'te güncellenir; sorguda ilk okunan.
- **log bölünmesi:** `log.md` 150 satırı aşınca en eski girdiler `log.partN.md` olarak arşivlenir; içerik eksilmez, arşiv değiştirilmez. Tüm girdiler: `grep -h "^## \[" wiki/log.part*.md wiki/log.md`.
- **log:** yalnız sona ekle. Başlık `## [YYYY-MM-DD] <işlem> | <başlık>` (`ingest|query|lint|decision|spec|code|setup|refactor`), altında 1–5 madde + dokunulan sayfalar. Son girdiler: `grep "^## \[" wiki/log.md | tail -5`.

## Graphify
- Kod grafiği (yerel, ücretsiz): git hook'u kurulu (`graphify hook install`), her commit'ten sonra kendiliğinden güncellenir; elle `graphify update .`.
- Sorgu: `graphify query "<soru>"`, `graphify explain "<düğüm>"`, `graphify path "A" "B"`. `/ask` sırası wiki, graf, ham kaynak, kod; `/lint` wiki-kod tutarlılığına grafla bakar.
- Tam grafik (kod + wiki + raw, token harcar): `/graphify .` yalnız büyük ingest dalgalarından sonra ya da istek üzerine.
- Görsel: `graphify export obsidian --dir graphify-out/obsidian`. Hariçler `.graphifyignore`'da.
- Wiki = neden/ne; graf = nerede/nasıl bağlı. Cevapta ikisini birlikte kullan.
