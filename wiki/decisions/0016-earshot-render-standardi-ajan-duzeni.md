---
type: decision
title: "earshot ile ses ölçümü, teslim render standardı ve ajan düzeni"
status: accepted
tags: [adr, ses, render, kalite, ajan, maliyet]
created: 2026-11-03
updated: 2026-11-25
sources: []
supersedes:
superseded_by:
---

# 0016 — earshot, render standardı, ajan düzeni

> [!note] Güncellendi 2026-11-15
> Teslim artık çözünürlük, kalite, kodek ve kare hızı seçer: `vedit final --cozunurluk --kalite --kodek --fps`; varsayılan yine sekans boyutu, H.264, CRF 16. `--scale=1.33334` Remotion 4.0.484'te tek sayı hatası verdiği için bırakıldı ([[0035-teslim-ayarlari]]).

> [!note] Güncellendi 2026-11-04
> Ara render hızlandı, son kodlama değişmedi: bkz. [[0019-arayuz-ve-efekt-motoru-birlesimi]] Hız ölçümü.

## Bağlam
Kullanıcı iki repo verdi ([earshot](https://github.com/Leonxlnx/earshot), [claude-video-edit](https://github.com/YildizDikme/claude-video-edit)), kaliteli render ve token tasarruflu ajan düzeni istedi.

Ölçümler (ffprobe, 2026-11-03):
- php2shell Reels teslimi ve ham Remotion çıktısı: `yuvj420p`, tam aralık, `bt470bg`, 4,3 Mbps.
- ornek-marka UGC teslimi (vedit, HyperFrames): `yuv420p`, `tv`, `bt709`, 5,4 Mbps.
- `video_compose.py` varsayılanı CRF 23 idi; Remotion ayar dosyası yoktu.

## Seçenekler
1. **earshot:** MCP sunucusu ya da CLI. Az çağrıda CLI, toplu işte tek Python betiği yeterli; sürekli sunucu eklenmedi.
2. **claude-video-edit:** Skill olarak kurmak ya da kuralları almak. `vedit`, `usta-editor` ve `kesimqa` ile çakıştığı için yalnız kural alındı.
3. **Renk düzeltmesi:** Her motoru ayrı yamalamak ya da tek son adım. Son adım eski dosyaları da düzeltir, ama kaynaktaki hatayı gizlememesi için Remotion ayarı da düzeltildi.

## Karar
1. Her iki repo skill kütüphanesine eklendi. Projeye yalnız `earshot` skill'i kuruldu; `real-sound` ve `video-edit` kütüphanede kaldı.
2. earshot kendi ortamında çalışır: `Skills/repos/Leonxlnx__earshot/.venv`. `llm` komutu kullanılmaz, çünkü sesi dışarı yükler.
3. Son adım `vedit teslim`: sınırlı aralık BT.709, `libx264 -preset slow -crf 16`, AAC 320k ya da yeterli AAC'yi kopyalama. Renk etiketi yanlışsa hata verir, düşük bitrate yalnız uyarıdır.
4. Remotion final ayarı `remotion.config.ts`: PNG kare, BT.709, CRF 16, x264 `slow`. OpenMontage FFmpeg varsayılanları CRF 16. vedit ara dosyaları `medium/14`.
5. YouTube uzun videoda kod sahnesi gerçek 1440p render edilir (`--scale=1.33334` 2560x1440 verdi). Gerçek çekim büyütülmez. NVENC yalnız önizlemede.
6. Ajanlar beş oldu: `sound` (sonnet) ve `render-qc` (haiku) eklendi. Çağrı başına model kuralı [[0003-model-yonlendirme]] kararını genişletir:
   - writer: outline, script, polish opus; research sonnet; teleprompter haiku.
   - director: reference, critique opus; shoot-plan, treatment, scenes, slop sonnet.
   - editor: hero opus; edl, timeline sonnet; assets haiku.
7. earshot sesleri `aday` kategorisiyle kütüphaneye girer ve otomatik seçilmez. Kullanıcı dinleyip seçince `kit.json` rolüne kimliğiyle yazılır.

## Sonuçlar
- `critique` kapı değildir: profili 7 lansman filminden gelir, konuşan kafa videosunda yanıltır. Kuvvetli miksteki etiketler ipucudur; zaman ve seviye ölçümleri esas alınır.
- Pilot: basit bir Remotion sahnesinde 10 saniyelik 1440p render 64 sn sürdü (12 çekirdek). 15 dakikalık video kabaca 1,5 saat ve üstü sürer; ağır sahnede daha uzun.
- `openmontage/` ayrı git deposudur ve `.gitignore`'dadır. Yamaları orada kalır; üst sürümden güncelleme bunları ezebilir.
- Yüksek kaliteli `PNG` ve `slow` taslakta da geçerlidir; taslakta bayrakla düşürülür: `--image-format=jpeg --x264-preset=veryfast --crf=23 --scale=0.5`.
- `clean_voice` varsayılanı değişmedi. claude-video-edit uyarlanabilir gürültü azaltmanın sesi boğabileceğini söylüyor; değiştirmek her videonun sesini değiştireceği için ayrı karar ister.

> [!question] Çıkarım
> Remotion çıktısında `color_primaries` ve `color_trc` boş kalıyor, aralık ve matris doğru. Bu yüzden `vedit teslim` son adım olarak zorunlu kalır.

## İlgili kod
`src/vedit/teslim.py`, `tests/test_teslim.py`, `openmontage/remotion-composer/remotion.config.ts`, `.claude/agents/sound.md`, `.claude/agents/render-qc.md`, `.claude/skills/sound-design/`, `library/sfx/raw/earshot/source.json`

> [!note] Güncellendi 2026-11-04
> `editor` ve `sound` ajanları kaldırıldı, standart aynı: [[0017-terminal-hizli-hat]].

## Güncelleme (2026-11-25)
Teslim kapısı 10-bit (`yuv420p10le`, yalnız Master H.265) kabul eder ve SSIM/PSNR sadakat ölçümü yazar; renk dönüşümü zscale ile dither'lı. Ayrıntı [[0060-proxy-master-conform]].
