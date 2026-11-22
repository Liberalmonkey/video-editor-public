---
type: decision
title: "Edit sonrası zorunlu AI slop denetimi"
status: accepted
tags: [adr, kalite, kurgu, skill]
created: 2026-11-03
updated: 2026-11-03
sources: []
supersedes:
superseded_by:
---

# 0015 — AI slop denetimi

## Bağlam
Kullanıcı videoların AI slop gibi görünmemesini, edit bittikten sonra sistemin kontrol edip slop olan yerler için düzeltme önermesini istedi. `render-qa` teknik ve genel kalite odaklıdır, slop için kısa bir madde taşır; klişe testi yalnız 6 kareye bakar.

## Seçenekler
- Yalnız skill metni: maliyetsiz, ama ritim ve palet gibi ölçülebilir kalıplar göze bırakılır.
- Yalnız ölçüm aracı: ucuz ve tekrarlanabilir, ama bozuk el ya da bağlam kopukluğunu göremez.
- İkisi birlikte, otomatik düzeltmesiz.

## Karar
1. `vedit slop` motordan bağımsız olarak bitmiş videoyu ölçer ve zaman damgalı şüphe listesi çıkarır.
2. `ai-slop-denetimi` skill'i şüpheleri karelerle doğrular, üretken kusur ve bağlam kopukluğunu gözle arar, `qa/slop-raporu.md` yazar.
3. Skill düzeltmeyi önerir, kullanıcı onayı olmadan uygulamaz. P0 varken teslim için kullanıcı kararı gerekir.
4. Altyazı standardı (ADR 0014), kilitli kit varlıkları ve gerekçeli stil kartı seçimleri bulgu sayılmaz.

## Sonuçlar
- Yapım akışında edit ile teslim arasına denetim girdi; arayüzde ayrı düğmesi var.
- Eşikler sınırlı örnekle ayarlandı: bir sentetik slop video ve iki gerçek teslim. Yanlış pozitif beklenir, bu yüzden ölçüm hüküm değil şüphedir.
- Yumuşak geçişler kesim sayılmaz; müzik karakteri ölçülmez, kulak testi kullanıcıdadır.

## İlgili kod
`src/vedit/slop.py`, `tests/test_slop.py`, `.claude/skills/ai-slop-denetimi/`, `ui/uretim.json`, `ui/public/app.js`.

> [!note] Güncellendi 2026-11-04
> Skill `denetim` altında birleşti (`references/slop.md`); kural değişmedi: [[0017-terminal-hizli-hat]].
