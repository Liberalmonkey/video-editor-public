---
type: decision
title: "Video Stüdyo içinde AI paneli: Claude Code, Antigravity, Codex ya da OpenCode; model seçimi arayüzde"
status: accepted
tags: [adr, studio, ajan, claude-code, antigravity, codex, opencode, model]
created: 2026-11-08
updated: 2026-11-17
sources: []
---

# ADR: Arayüzde AI paneli

## Bağlam
Proje yerelde çalışıyor ve Claude ile Antigravity abonelikleriyle kullanılıyor. Kullanıcı `vedit studio` içinden hangi AI motorunun çalıştığını görmek, motoru ve modeli kendisi seçmek istedi (2026-11-08). [[0021-video-studyo-nle]] "AI terminalde kalır" demişti; gerekçe [[0017-terminal-hizli-hat]]'teki yavaşlıktı: eski arayüz agent'ı kendi içinde yürütüyor, bağlam ve render yükünü taşıyordu.

## Seçenekler
| Seçenek | Artı | Eksi |
|---|---|---|
| Arayüz yalnız durumu gösterir, istek terminalden | Hiç kod riski yok | Kullanıcı model seçemez, iki pencere arasında gider gelir |
| Arayüz CLI'ı başlatır, izler, durdurur | Seçim ve görünürlük arayüzde, ajan yine terminal CLI'ı | Uzun işte arayüz beklemez ama günlük kalabalıklaşır |
| Arayüze SDK ile gömülü ajan | Zengin etkileşim | API anahtarı ister, abonelik kullanılamaz, 0017'deki yük geri gelir |

## Karar
| Konu | Karar | Neden |
|---|---|---|
| Çalıştırma | `claude -p` ya da `agy -p`, proje kökünde ayrı süreç, `stream-json` | Abonelik oturumu kullanılır; CLAUDE.md ve AGENTS.md aynen yüklenir |
| Kuyruk | `isler.Kuyruk`'un ikinci örneği; iş kimliği ortak sayaçtan | Ajan ağ işidir, render kuyruğunu bekletmemeli; İşler paneli ve bildirim aynen çalışır |
| Model | Claude için sabit takma ad ve tam ad listesi; Antigravity için `agy models` çıktısı | Kullanıcı seçer; liste dışı model 400 |
| İzin | Yalnız `Düzenle` (`acceptEdits`, `accept-edits`) ve `Yalnız plan`; izin atlatma bayrağı yok | Başsız modda soru sorulamaz; onaysız komut CLI tarafından reddedilir |
| Sohbet | Son ajan işinin oturum kimliğiyle `--resume` / `--conversation`; "Yeni sohbet" sıfırlar | Bağlam sürer, istenince temizlenir |
| Görünürlük | Üst çubukta rozet: motor, model, Hazır / Çalışıyor / Kurulu değil | Kullanıcının ana isteği |

## Sonuçlar
- Gerçek model `init` olayından günlüğe yazılır. Doğrulama sırasında `claude --model haiku` isteği `claude-sonnet-5-5` ile döndü; rozet seçileni, günlük çalışanı gösterir.
- Ajan `kurgu.json`'a yazarsa iş bitince arayüz kurguyu yeniden yükler (mevcut SSE yolu).
- Oturum ve abonelik girişi denetlenmez; giriş yoksa CLI hatası günlükte görünür.
- Logo değişti: koyu zemin, kesik turuncu oynat üçgeni, AI kıvılcımı (`studio/web/public/logo.svg`), favicon ve üst çubuk.

> [!note] Güncellendi 2026-11-15
> Panel iki iş görür: "Gönder" serbest sohbet (bu karar), "AI ile editle" aynı isteği `vedit ai-edit` işine not olarak verir ([[0028-ai-edit]]). AI edit işleri de panel günlüğünde akar; bitince önce/sonra özeti ve "Geri al" görünür.

> [!note] Güncellendi 2026-11-17: dört motor
> Kullanıcı bilgisayarında kurulu Codex ve OpenCode'un da panele girmesini istedi. Motorlar artık tek tabloda: `src/vedit/motorlar.py` (yol, model listesi, argüman, akış çevirisi). Stüdyo paneli, `vedit ai-edit` ve `vedit stil-uret` aynı tabloyu okur.
>
> | Motor | Komut | Düzenle / Yalnız plan | Devam | Model listesi |
> |---|---|---|---|---|
> | Claude Code | `claude -p … --output-format stream-json` | `acceptEdits` / `plan` | `--resume` | Sabit takma ad + sürüm listesi |
> | Antigravity | `agy -p … --output-format stream-json` | `accept-edits` / `plan` | `--conversation` | `agy models` |
> | Codex | `codex exec --json -c sandbox_mode=…` | `workspace-write` / `read-only` sandbox | `codex exec resume <id>` | `~/.codex/models_cache.json` (`visibility: list`), varsayılan `config.toml` |
> | OpenCode | `opencode run --format json --agent …` | `build` / `plan` ajanı | `-s <oturum>` | `opencode models`, sağlayıcıya göre gruplu |
>
> - `codex exec resume` `-s` almaz; sandbox iki durumda da `-c sandbox_mode="…"` ile verilir.
> - Windows'ta npm `.cmd` shim'i çalıştırılmaz: cmd.exe istemdeki `& | ^ %` karakterlerini yorumlar ve bu kabuk enjeksiyonu demektir. nvm `.shim` de boşluklu yolda ("Author Software") kırıldı. Bu yüzden paketin içindeki gerçek ikili aranır (`@openai/codex-win32-x64/vendor/*/bin/codex.exe`, `@opencode/cli/bin/opencode.exe`). Birden çok kurulum varsa en yenisi seçilir; npm'deki eski OpenCode 1.19.5 başsız modda yanıt vermeden asılı kaldı.
> - `--auto` (OpenCode) ve `--dangerously-*` (Codex) kullanılmaz; ilke aynı kalır.
> - Dört motor paralel taranır (yaklaşık 5 sn). OpenCode yüzlerce model listelediği için panelde model seçici gruplu (`optgroup`), 20'den çok modelde aranabilir; ücretsiz ve varsayılan modeller etiketlidir. Rozet model kimliği yerine okunur adı gösterir.
> - Akış biçimleri 2026-11-17'de gerçek çağrıyla ölçüldü (codex-cli 0.154.0, opencode 2.3.0); örnek satırlar `tests/test_studio_ajan.py` içindedir.

## İlgili kod
- `src/vedit/motorlar.py`, `src/vedit/studio/ajan.py`, `src/vedit/studio/isler.py`, `src/vedit/ajan_cagri.py`
- `studio/web/src/paneller/AjanPaneli.tsx`, `studio/web/src/depo.ts`, `studio/web/src/main.tsx`
- `tests/test_studio_ajan.py`
