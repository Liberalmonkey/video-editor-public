---
source_url: https://github.com/blader/humanizer
accessed: 2026-10-20
license: MIT (Copyright (c) 2025 Siqi Chen)
version_checked: SKILL.md v3.1.0
note: LLM inceleme notu.
---

# humanizer — inceleme notu

Bir Agent Skill (kütüphane değil). Metni, söylediğini değiştirmeden "AI yazmış gibi" okunmaktan çıkarır. Wikipedia "Signs of AI writing" rehberine dayanır. AI dedektörünü atlatmak amaç değil.

Dosyalar: SKILL.md (397 satır), README.md, AGENTS.md, CHANGELOG.md, LICENSE, .claude-plugin/, .cursor-plugin/, agents/openai.yaml, scripts/validate-package.py.

Kurulum: `/plugin marketplace add blader/humanizer` + `/plugin install humanizer@humanizer` veya `npx skills add blader/humanizer`.

## 26 desen (güçlüden zayıfa)
- A. Söylemek yerine sahnelemek (1–5): "X değil Y", tek satırlık kapanış/dramatik parça, derin görünen özdeyiş, sahnelenmiş giriş ("İşte mesele şu"), kimseyle tartışmak
- B. Kuralla ritim (6–11): zorlama üçlüler, tekrarlanan cümle başları, her yerde tire, yığılmış niteleyiciler, tireli ikililer, edilgen çatı
- C. Şişirme (12–18): kalıp AI kelimeleri (delve, testament), şişirilmiş önem, belirsiz ilişki, sığ "-ing" ekleri, satış dili, ödünç otorite ("uzmanlar diyor ki"), "is" yerine "serves as"
- D. Kuralla biçim (19–21): süs kalın, süs başlık/emoji, kıvrık tırnak
- E. Sohbet artıkları (22–25): chatbot sarmalayıcıları, bilgi sınırı uyarıları, başlığı ilk cümlede tekrarlamak, konudan değil belgeden bahsetmek
- F. Yanlış okur (26): okurun bildiğini yeniden açıklamak

1–5 tek görülmede düzeltme gerektirir; "weak alone" olanlar ancak birden fazla iz bir aradaysa sayılır.

Akış: izleri işaretle → yeniden yaz → eleştir → son hâl. Asla gerçek uydurmaz; eksik detayı sorar. Kullanıcının 2–3 paragraf yazısıyla sesine uyum sağlayabilir. SKILL.md: "The formula appears in every language; treat the equivalent construction the same way."

## Projeye uyarlama
Senaryo için D grubu kapalı, A/B/C/E açık. Türkçe eşdeğer kalıplar eki gerekli ("sadece X değil, aynı zamanda Y", "Peki ya…?", "Gelin birlikte bakalım", "Şunu unutmayın:", "kısacası", "eşsiz", "büyüleyici", "devrim niteliğinde").
