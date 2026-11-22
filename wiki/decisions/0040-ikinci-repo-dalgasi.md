---
type: decision
title: "İkinci repo dalgası: on beş repodan yalnız projeyi geliştiren parçalar"
status: accepted
tags: [adr, hyperframes, motion, sablon, ses, hdr, teslim, kalite, ritim, antigravity, lisans]
created: 2026-11-16
updated: 2026-11-16
sources: ["[[2026-11-16-ikinci-repo-dalgasi]]", "[[2026-11-16-fizik-stil-repolari]]"]
---

# ADR: İkinci repo dalgası

## Bağlam
Kullanıcı 2026-11-16'da on beş repo verdi ve aynı süreci istedi: kurulu olanı yeniden kurma, bizde daha iyisi olanı alma, yalnız projeyi gerçekten geliştiren yönleri al. Repolar: hyperframes, ffmpeg-skill, snapcn, hyperframes-community-skills, saas-motion-kit, open-edit, rea-video, herk-edit-kit, onetake, claude-motion-design, product-launch-motion, motion-video-kit, motion-graphics, opus-video-skills, brag.

## Süreç
Mevcut sistemin envanteri ve kabul ölçütü yazıldı (`work/agy/2026-11-16-repolar2/sistem.md`). Antigravity'de dört paralel karşılaştırma (hyperframes, hat, motion, beceri) koştu. İkisi kredi sınırına takıldı, flash modeliyle ikinci denemede geçti. Birleştirme aşaması çalışmadı; kararları Claude birleştirip kaynak satırlarından doğruladı. Üretim: 12 şablon üç paralel agy görevinde. Kod ve kurallar ana oturumda yazıldı.

## Karar
| Repo | Alınan | Alınmayan ve neden |
|---|---|---|
| hyperframes (Apache-2.0) | npm 0.8.181 → 0.9.56. Kırıcı değişiklikler dağıtık bulut render, inspector ve studio-server'da; bizim `lint --json` ve `render -o -q -w --quiet` çağrılarımız gerçek render'la sınandı. `hyperframes-cli` skill'ine 0.9.x komutları (`snapshot --range`, `timeline … --plan`, `render --start/--end`, `data-motion-blur`, yerel `media-treatment`, `remove-background`) | Upstream skill'lerin tamamı: HeyGen hesabı ya da kredisi, TTS, telemetri, `uretim-hatti` ile çakışma. `style-sampling` ücretli abonelik ister; `slideshow` video üretmez; `figma` jeton ister |
| hyperframes-community-skills (Apache-2.0) | `vox-explainer`'ın vektör yasası, yedi kesim tekniği ve süreklilik kuralları (`motion-design/references/kesim-surekliligi.md`) | `p5-paint-animation`: ayrı Puppeteer ve 500 MB Chromium, ikinci render hattı, p5 LGPL. `camera-3d-captions`: CDN'den GSAP, bash betikleri; 3D three.js ile zaten var. `prod-by-claude` AGPL bağımlılığı. `duo`, `x-posting-license`, `day-in-my-life`, `session-story`: tek amaçlı, marka görseli ya da macOS |
| ffmpeg-skill (MIT) | HDR (HLG, PQ) → BT.709 SDR ton eşleme zinciri, düzeltilmiş beyaz noktasıyla (`ff.sdr_zinciri`, `ff.sdr_cevir`); render bağlamasında ve önizleme proxy'sinde kendiliğinden | Skill'in kendisi ([[0038-video-izleme-ve-google-baglantilari\|ADR 0038]] kararı sürer) |
| snapcn (MIT) | Dört şablon fikri (ajan adımları, terminal, kelime taklası, seçim şeridi, AI kenarlık, sosyal kanıt); ölçeklenen yazıda taban çizgisi dayanağı kuralı | Next.js belge altyapısı |
| product-launch-motion, claude-motion-design, motion-video-kit, motion-graphics (MIT) | Şablon fikirleri: odometre sayaç, komut paleti, ayar çubuğu, ışık demeti, kenar ışıltısı, kart yelpazesi. B-roll yeri kuralı (tam kare / saydam panel / hiçbiri); uydurma rakam yok | Tam film şablonları ve ses indirme betikleri (ikinci hat), marka görselleri, `object-separation` |
| saas-motion-kit (MIT) | Çeşitlilik denetimi fikri: art arda üç aynı geçiş, efekt ya da grafik uyarısı (`kurgu_kalite.py`) | HyperFrames tam film şablonları; 101 tema (20 temamız var, ihtiyaç kadar) |
| open-edit (Apache-2.0) | Yazı okuma süresi formülü (kelime başına 0,2 sn + taban; kapanış kartı 2 sn taban) → `YAZI_KISA`; 3 sn ölü hava → `slop` `SES_OLU_HAVA` | VEED bağımlı CLI |
| rea-video (Apache-2.0) | Katmanlı çözümleme raporu kuralı (`video-izle`) | Kod ve model bağımlılıkları |
| opus-video-skills (MIT) | Geçişte whoosh yorgunluğu kuralı (`sound-design`); alt ajana dağıtmadan önce bir sahneyi bitirme ve kesim kontak sayfası protokolü (`sahne-motoru`) | `painted-animation` ve `kinetic-reel` tam skill'leri (ikinci hat, bash), kodla müzik sentezi |
| brag (MIT) | Vurgu yoğunluğu formülü (0,45 onset + 0,25 yerel kontrast + 0,20 RMS + 0,10 bas) `ritim.py`'de; SFX parlaklık ölçüsü (`parlak`) ve tekrarlı rollerde süzme; teslimde 0. kareye kapak (`vedit teslim --kapak-kare`) | Ses dosyaları: 260 sesin hepsi bizde (Kenney ve OpenGameArt keypress setleri). Kokoro TTS (TTS yok kuralı), ayrı `brag-output` hattı |
| onetake (PolyForm Noncommercial) | Yalnız fikir: taşıyıcı öğe ve kadans farkı (`kesim-surekliligi.md`) | Kod ve metin: ticari kullanım yasak |
| herk-edit-kit (lisans yok) | Hiçbir şey | Lisanssız; klon yarıda kaldı, iddialar doğrulanamadı |

## Yeni ve değişen
| Konu | Ne |
|---|---|
| Motion | 12 parametrik şablon: `ajan-adimlari`, `odometre-sayac`, `terminal-akisi`, `kelime-taklasi`, `isik-demeti`, `kenar-isiltisi`, `komut-paleti`, `secim-seridi`, `ayar-cubugu`, `kart-yelpaze`, `ai-kenarlik`, `sosyal-kanit`. Kütüphane 102 → 114. `vedit motion olc` 12/12 temiz, kontak sayfaları gözle denetlendi, kural taraması temiz |
| HDR | `kurgu._public_bagla`: HDR kaynak render'a bağlantıyla değil `work/sdr/` altındaki SDR kopyayla girer; kurgu, kaynak yolu ve uzantı değişmez. Stüdyo proxy'si de ton eşlenir. HLG %100 beyaz sınırlı aralıkta Y > 215 (test) |
| Kalite | `kurgu_kalite.uyarilar`: `YAZI_KISA`, `GECIS_TEKRAR`, `EFEKT_TEKRAR`, `GRAFIK_TEKRAR`; `vedit kurgu-denetle` basar, ai-edit ek turda düzelttirir, render'ı durdurmaz. `slop`: `SES_OLU_HAVA` |
| Ses | `SfxEntry.parlak`; 871 kaydın hepsi ölçüldü (143 yüksek). `olaysesi` tık, klavye, kesme ve benzeri kategorilerde 0,25 üstünü seçmez |
| Ritim | Vurgu gücü bileşik formülle; önbellek anahtarı `v2` |
| Teslim | `--kapak-kare`: kapak yalnız 0. kareye gömülür; süre ve ses değişmez |
| HyperFrames | `hf.run` her çağrıda `HYPERFRAMES_SKIP_SKILLS`, `HYPERFRAMES_NO_TELEMETRY`, `DO_NOT_TRACK`, `HYPERFRAMES_NO_UPDATE_CHECK` verir |

## Sonuçlar
- Olay: deneme için CLI doğrudan çalıştırılınca `hyperframes init` altı skill'i genel `~/.claude/skills` ve `~/.agents/skills` altına kurdu. Hemen geri alındı (yedek `work/agy/2026-11-16-repolar2/hf-genel-skill-yedek/`); `hyperframes-cli` skill'ine uyarı yazıldı.
- Kapak 0. karede bir kare görünür; varsayılan kapalı, yalnız X, Discord, Slack gibi ilk kareyi önizleyen yerler için.
- HDR dönüşümü ilk render'da kaynak başına bir kez sürer (CRF 14 ara kalite); son kalite kodlaması teslimdedir.
- agy kredi sınırı: uzun orkestrada pro model düşebilir; flash modeli yedektir.

## İlgili kod
- `package.json`, `src/vedit/hf.py`, `src/vedit/ff.py` (`hdr_mi`, `sdr_zinciri`, `sdr_cevir`), `src/vedit/kurgu.py` (`_public_bagla`), `src/vedit/studio/app.py` (`_proxy_uret`), `src/vedit/kurgu_kalite.py`, `src/vedit/slop.py`, `src/vedit/sfx.py` (`parlaklik`), `src/vedit/olaysesi.py` (`TEKRARLI_KAT`), `src/vedit/schemas.py` (`SfxEntry.parlak`), `src/vedit/ritim.py` (`_yogunluk`), `src/vedit/teslim.py` (`kapak`), `src/vedit/cli.py`, `src/vedit/aiedit.py`
- `library/motion/custom/{ajan-adimlari,…,sosyal-kanit}/`, `library/sfx/manifest.json`
- `.claude/skills/{hyperframes-cli,motion-design,sound-design,footage-editing,sahne-motoru,video-izle}/`
- `tests/test_hdr.py`, `tests/test_kalite.py`, `tests/test_senkron.py`
