---
type: entity
kind: tool
title: "Graphify"
tags: [arac, bilgi-grafigi, wiki, kod]
created: 2026-11-15
updated: 2026-11-15
url: https://github.com/Graphify-Labs/graphify
sources: []
---

# Graphify

## Ne olduğu
Kodu, belgeleri ve ham kaynakları kalıcı bir bilgi grafiğine çeviren komut satırı aracı ve skill. Çıktı `graphify-out/`: `graph.json`, `graph.html`, `GRAPH_REPORT.md`.

## Yetenekler
- `graphify update .`: kod dosyalarını yeniden çıkarır; LLM gerekmez, ücretsizdir.
- `graphify query "<soru>"`, `graphify explain "<düğüm>"`, `graphify path "A" "B"`: grafiğe soru.
- `graphify hook install`: commit, checkout, merge ve rewrite sonrası grafiği kendiliğinden günceller; `graph.json` için birleştirme sürücüsü kaydeder.
- `/graphify .`: kod, wiki ve `raw/` için anlamsal çıkarım; token harcar.
- `graphify export obsidian --dir graphify-out/obsidian`: Obsidian'da görsel grafik.

## Lisans / maliyet
Açık kaynak, yerel çalışır. Kod grafiği ücretsiz; anlamsal çıkarım ajanın token'ını harcar.

## Entegrasyon notları
- Sürüm 0.9.102, `uv tool` ile kurulu. Proje skill'i `.claude/skills/graphify/` Windows (PowerShell) uyarlamasıdır ve 150 satır kuralı için bölünmüştür.
- Hariç tutulanlar `.graphifyignore` içinde: medya, `Projeler/`, `library/`, `openmontage/`, `node_modules/`.
- Git hook'ları 2026-11-15'te kuruldu.

## Projedeki rolü
Wiki neden ve neyi, graf nerede ve nasıl bağlı olduğunu söyler. `/ask` sırası: wiki, graf, ham kaynak, kod. `/lint` ADR'de yazan komut ve dosyanın kodda var olup olmadığına grafla bakar. 2026-11-15'te graft kaldırıldı; kod haritası işini yalnız graphify görür ([[0037-antigravity-orkestra]]).

## Kaynaklar
- `.claude/wiki-kurallari.md`, Graphify bölümü.
