---
type: decision
title: "Token optimizasyonu: Caveman plugin'i (yalnız sohbet) ve inceltilmiş CLAUDE.md"
status: accepted
tags: [adr, token, maliyet, caveman, claude-code]
created: 2026-10-21
updated: 2026-10-21
sources: []
supersedes:
superseded_by:
---

# ADR: Token optimizasyonu

## Bağlam
Proje büyüdükçe oturumlar çok token harcamaya başladı. Kullanıcı 2026-10-21'de [Caveman](https://github.com/JuliusBrussee/caveman)'ı (Apache-2.0, v4.0.1) kurmak ve başka tasarruf önerileri almak istedi. Ölçüm: CLAUDE.md her mesajla yüklenen 14,6 KB'lik bir metindi ve yarısından fazlası yalnız wiki işlemlerinde gereken ayrıntıydı.

Caveman'ın parçaları:
- Yanıtları kısaltan kural seti (oturum başına ~1.160 token ek yük).
- Log/JSON sıkıştıran proxy CLI.
- Auto: modeli bulutta seçer, prompt'ları Caveman Cloud'a gönderir.
- Telemetri varsayılan açıktır.

## Seçenekler
| Seçenek | Artıları | Eksileri |
|---|---|---|
| **Yalnız Claude Code plugin'i** | Hook'lar yerel, ağ çağrısı yok; `/caveman-stats`, `/caveman-compress` | Okunan girdiyi sıkıştırmaz |
| Tam CLI (`npx @caveman-ai/cli`) | Girdi sıkıştırma proxy'si, statusline | Telemetri ve ek süreç; Auto açılırsa prompt'lar buluta gider |
| Caveman yok, yalnız CLAUDE.md inceltme | Sıfır bağımlılık | Çıktı tasarrufu yok |

## Karar
- **Plugin** kuruldu (`claude plugin install caveman@caveman`, kullanıcı kapsamı). Proxy, Auto ve telemetri kullanılmıyor.
- **Mod varsayılan açık.** SessionStart hook'u oturumu, SubagentStart hook'u alt ajanları otomatik açar. Kural seti kullanıcının dilini korur. Sohbet dışında kalıcı olan her şeyi (kod, commit, doküman) düz yazıyla yazdırır.
- **Kapsam (CLAUDE.md §4):** yalnız sohbet yanıtları kısalır. Wiki, senaryo, altyazı, STYLE/MOTION, brief ve alt ajan teslim dosyaları tam düzyazı kalır. Her `.claude/agents/*.md` sonuna aynı kuralın tek satırı eklendi.
- **CLAUDE.md inceltildi:** 14,6 KB'den 6,0 KB'ye indi. Wiki ayrıntıları (dizin ağacı, adlandırma, frontmatter, iskeletler, yazım ilkeleri, index/log, graphify ayrıntıları) `.claude/wiki-kurallari.md`'ye taşındı. `ingest`, `ask`, `lint` ve `decide` skill'leri önce bu dosyayı okur.
- `/caveman-compress` CLAUDE.md'ye uygulanmadı. Türkçe anayasa metni elle sadeleştirildi.

## Sonuçlar
- Her mesajda ~2–2,5k token daha az sabit bağlam yüklenir (CLAUDE.md farkı). Caveman kuralları bunun ~1,2k'sını geri alır, ama yanıt çıktısı kısalır.
- Wiki işlemlerinde bir dosya fazladan okunur (~1,5k token); bu yük yalnız wiki işi yapılırken gelir.
- Kapatmak: `stop caveman` ya da `normal mode` (oturumluk), `claude plugin disable caveman@caveman` (kalıcı).

> [!question] Çıkarım
> En büyük ek kazanç, video projesiyle ilgisi olmayan claude.ai connector'ları ve plugin'lerinin (satış, pazarlama, small-business, Vercel, Supabase…) kapatılmasıdır. Bunların araç adları ve skill satırları her oturumun bağlamına giriyor. Bu bir hesap ayarı olduğu için karar kullanıcıya bırakıldı.

## İlgili
- [[0003-model-yonlendirme]]: model/effort yönlendirmesi de token maliyetini belirler.
- Kod: `.claude/wiki-kurallari.md`, `CLAUDE.md` §4, `.claude/agents/*.md`.
