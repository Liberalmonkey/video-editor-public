---
disable-model-invocation: true
name: ask
description: LLM Wiki'ye (ve gerekiyorsa graphify kod grafiğine) karşı soru cevapla, kaynak göster, değerli cevapları wiki/queries/'e dosyala. Kullanıcı "/ask", "wiki'ye göre", "wiki'de ne var" dediğinde kullan.
argument-hint: <soru>
---

# /ask

Soruyu wiki'nin gerçekten içerdiğiyle, kaynak göstererek cevaplar. Soru: $ARGUMENTS

## Sıra: wiki, graf, ham kaynak, kod
1. **`wiki/index.md`** ile başla; aday sayfaları seç ve baştan sona oku. Soru birden çok kavrama yayılıyorsa `[[link]]`leri bir adım izle.
2. **Graf.** `graphify-out/graph.json` varsa ve soru "nerede", "ne neye bağlı", "neyi etkiler" türündeyse:
   - `graphify query "<soru>"`: ilgili düğümler ve bağlantılar.
   - `graphify explain "<düğüm>"`: bir modül, fonksiyon ya da kavramın komşuları.
   - `graphify path "A" "B"`: iki şey arasındaki en kısa bağ (örnek: bir ADR ile onu uygulayan dosya).
   Wiki neden ve neyi, graf nerede ve nasıl bağlı olduğunu söyler; cevapta ikisini birlikte kullan.
3. **Ham kaynak.** Bir wiki iddiası zayıf duruyorsa `raw/` altındaki kaynağa bakıp doğrula.
4. **Kod.** Graf bayatsa (`graphify-out/graph.json` tarihi son kod değişikliğinden eski) ya da ayrıntı gerekiyorsa dosyayı oku.

## Cevap
- Önce doğrudan cevap, 1-4 cümle.
- Sonra destekleyen maddeler; her madde yerinde atıflı: `([[sayfa]])`, `(raw/<dosya>)` ya da `dosya:satır`. Atıf sonda toplu verilmez.
- Wiki'nin özetlemediği bir ham kaynağı okumak zorunda kaldıysan bunu boşluk olarak söyle.
- Biçim soruya göre: metin, karşılaştırma tablosu, Mermaid, Obsidian `.canvas`.

## Wiki cevap veremiyorsa
Açıkça söyle, uydurma. Somut bir sonraki adım öner: işlenecek kaynak (`/ingest`), web araştırması ya da karar (`/decide`).

## Kalıcı cevap
Soru gerçek bir sentez gerektirdiyse (karşılaştırma, ödünleşim, sayfası olmayan bir şeyin tanımı) `wiki/queries/`'e dosyalamayı öner; sessizce yazma. Kullanıcı kabul ederse: önce `.claude/wiki-kurallari.md`, `templates/query.md` ile `wiki/queries/kisa-baslik.md`, ilgili sayfalardan link, `index.md`, `log.md` (`query`), `python scripts/wiki_lint.py`.

## Bitiş denetimi
- [ ] Her iddia bir wiki sayfasına, ham kaynağa ya da `dosya:satır`a bağlı.
- [ ] Wiki yetersizse bu ve sonraki adım yazıldı.
- [ ] `raw/` altında hiçbir dosya değişmedi.
