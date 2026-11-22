---
type: decision
title: "Yerel web arayüzü (Video Stüdyo): Claude Code CLI üzerinden, yalnız 127.0.0.1"
status: superseded
tags: [adr, arayuz, claude-code, guvenlik, yerel]
created: 2026-11-01
updated: 2026-11-01
sources: []
supersedes:
superseded_by: "[[0017-terminal-hizli-hat]]"
---

# 0011 — Yerel web arayüzü (Video Stüdyo)

## Bağlam
Proje yalnız terminaldeki Claude Code sohbetiyle kullanılıyordu. Kullanıcı tek tıkla açılan, kullanıcı dostu bir arayüz istedi. Üç koşul koydu: Claude Code aboneliği kullanılacak (API anahtarı yok), arayüzde yapılan değişiklikler yalnız bu bilgisayarda kalacak, arayüz zamanla değiştirildiğinde sistem bozulmayacak.

## Seçenekler
1. Claude Agent SDK ile ayrı bir uygulama: ek paket ve sürüm takibi gerektirir.
2. React/Vite gibi build adımı olan bir ön yüz: her değişiklikte derleme, bağımlılık güncellemelerinde kırılma riski.
3. Bağımlılıksız Node sunucusu + düz HTML/JS; sunucu kurulu `claude` CLI'yi `-p --output-format stream-json` ile çalıştırır.

## Karar
Seçenek 3. `ui/server.mjs` yalnız Node yerleşik modüllerini kullanır, ön yüz derlenmez. Claude oturumu kullanıcının girişli CLI'si üzerinden açılır, böylece abonelik kullanılır ve `--resume` ile terminaldeki oturumlarla aynı geçmiş paylaşılır.

Yerellik ve güvenlik:
- Sunucu yalnız `127.0.0.1` dinler; `Host` ve `Origin` başlıkları denetlenir (DNS rebinding ve başka sitelerden istek koruması).
- Her açılışta rastgele token üretilir, `HttpOnly; SameSite=Strict` çerezine çevrilir.
- Dosya okuma repo köküne kilitlidir. Yükleme yalnız `ui/config.json` → `uploadDirs` hedeflerine yapılır ve var olan dosyanın üzerine yazmaz (`raw/` değişmezliği korunur).
- İzin modu `acceptEdits` + `allowedTools` beyaz listesi; `git push` listede yoktur. Arayüzdeki "Tam yetki" anahtarı tek mesajlık `bypassPermissions` verir.
- Harici CDN, font ya da telemetri yoktur. Sohbet metni doğal olarak modele gider; dosya ve medya bilgisayarda kalır.

Windows notu: NVM'nin `.nodejs\claude.exe` shim'i güven kontrolüyle çalışmayı reddedebiliyor (NVM4306). Sunucu bu yüzden `node_modules/@anthropic-ai/claude-code/bin/claude.exe` gerçek ikilisini tercih eder.

## Sonuçlar
- Davranış (izinler, modeller, butonlar, yükleme klasörleri) JSON dosyalarındadır; kod değiştirmeden ayarlanır.
- Bilinmeyen stream-json olayları yok sayılır, CLI sürümü değişse de arayüz çalışmaya devam eder.
- `node ui/test.mjs` sahte bir `claude` ile güvenlik ve akış sözleşmesini doğrular; arayüz değişikliğinden sonra çalıştırılır.
- Aynı anda tek Claude çalışması vardır (tek kullanıcı).

## İlgili kod
`ui/server.mjs`, `ui/public/app.js`, `ui/config.json`, `ui/actions.json`, `ui/test.mjs`, `ui/baslat.vbs`, `ui/kur.ps1`, `ui/README.md`.

> [!note] Güncellendi 2026-11-04
> Arayüz kaldırıldı; karar [[0017-terminal-hizli-hat]] ile yerine geçti.
