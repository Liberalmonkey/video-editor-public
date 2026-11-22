---
type: decision
title: "Platform sinyallerine göre kurgu: viral-kurgu skill'i"
status: accepted
tags: [adr, algoritma, kurgu, retention]
created: 2026-11-04
updated: 2026-11-04
sources: ["[[2026-11-04-platform-algoritmalari]]"]
---

# ADR: viral-kurgu skill'i

## Bağlam
Kullanıcı YouTube, Instagram ve LinkedIn algoritmalarının ve Nick Saraev'in kurgusunun araştırılıp videoların izlenmesi için gereken kurgunun projeye net biçimde girmesini istedi (2026-11-04). Mevcut `usta-editor` zanaatı anlatır; platformun neyi ölçtüğünü ve format başına reçeteyi anlatmaz.

## Seçenekler
| Seçenek | Artıları | Eksileri |
|---|---|---|
| Otomatik açılan skill | Her planda bağlama girer, kod gerektirmez | Skill listesini bir satır uzatır |
| Yeni ajan | Taze bağlam | ADR 0017 ajan sınırı 3; edit ana oturumda |
| `usta-editor` içine yazmak | Yeni dosya yok | Zanaat ile platform kuralı karışır, dosya şişer |
| `vedit` içinde yeni ölçüm | Otomatik uyarı | `vedit denetim` zaten ritim ölçüyor; eşikler kanıtlı değil |

## Karar
- **Skill.** `.claude/skills/viral-kurgu/SKILL.md`: platform sinyalleri, Reels/Shorts, YouTube, kurs ve LinkedIn reçeteleri, Saraev'den alınan ve alınmayanlar, taslak kapısı, yayın sonrası ölçüm.
- **Bağlantı.** `uretim-hatti` senaryo ve edit adımında çağırır, `denetim` sonrasında taslak kapısı çalışır.
- **Eşikler başlangıç değeridir.** Kesim hızının nedensel etkisi kanıtlanmadı, sayılar kanalın kendi verisi gelince değişir.
- **Kod yok.** Kapı, kontak sayfası ve mevcut `vedit denetim` çıktısıyla çalışır.

## Sonuçlar
- ADR 0014 altyazısı ve `checks.md` önceliklidir. Saraev'in tek kelimelik altyazısı ve repo adı formatı alınmaz.
- LinkedIn için stüdyo ya da render profili açılmadı; önce `--platform reels` çıktısı denenir.
- Skill viral garanti vermez. İzlenme tahmini yazılmaz.
- Kanal verisi olmadan reçete doğrulanamaz; ilk yayınlardan sonra güncellenmelidir.

## İlgili kod
`.claude/skills/viral-kurgu/SKILL.md`, `.claude/skills/uretim-hatti/SKILL.md`, `.claude/skills/denetim/SKILL.md`
