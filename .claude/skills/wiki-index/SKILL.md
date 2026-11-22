---
disable-model-invocation: true
name: wiki-index
description: LLM Wiki index'ini ağaçtan yeniden kurar — wiki/index.md ile diskteki sayfaları eşitler, eksik sayfayı ekler, silinmiş sayfanın satırını çıkarır, sayıları log'a yazar; sayfa gövdesine dokunmaz. Kullanıcı "/wiki-index", "index'i tazele", "index bozuk" dediğinde kullan.
---

# /wiki-index

`wiki/index.md`'yi doğru ve taranabilir tutar. Index her sorgunun ilk durağıdır; kalitesi sonraki her işlemin maliyetini belirler. Önce `.claude/wiki-kurallari.md`.

## Akış
1. `wiki/index.md`'yi şu anki hâliyle oku.
2. `wiki/` ağacını kategori kategori gez: `sources/`, `concepts/`, `entities/`, `decisions/`, `specs/`, `queries/` ve sonradan eklenmiş kategoriler. `index.md`, `log.md` ve `log.partN.md` atlanır.
3. Son 50 log girdisine bak (`grep "^## \[" wiki/log.md | tail -50`): açılıp index'e girmemiş sayfa var mı?
4. Her kategori için sıralı satır üret: `- [[sayfa]] — tek cümle özet`. Özet sayfanın başlığından ya da ilk paragrafından alınır. Index'e durum ve tarih yazılmaz; onlar sayfanın kendisinde ve log'dadır.
5. Sayfası kalmamış satırı çıkar, diskte olup index'te olmayan sayfayı ekle.
6. Özel kategori başlıklarını koru; varsayılan kategorilere indirme.
7. `wiki/log.md` sonuna, sayılar sıfır olsa da:
   ```
   ## [YYYY-MM-DD] lint | index tazelendi: eklenen N, çıkarılan M
   - eklenen: [[...]]
   - çıkarılan: [[...]] (sayfa silinmiş)
   ```
8. `python scripts/wiki_lint.py`.

## Bu skill ne yapmaz
- Sayfa gövdesini değiştirmez.
- Çelişki çözmez, kırık link onarmaz, kavram boşluğu doldurmaz; bunlar `/lint`'e gider.
- Sayfanın desteklemediği özet yazmaz. İlk paragrafı özetlenemeyen sayfayı `/lint` için not eder.

## Bitiş denetimi
- [ ] `wiki/index.md`, `wiki/` içeriğiyle birebir: eksik sayfa yok, boşa çıkan satır yok.
- [ ] Her satır `- [[sayfa]] — özet` biçiminde.
- [ ] Log girdisi sayılarla yazıldı.
- [ ] Sayfa gövdeleri ve `raw/` değişmedi.
