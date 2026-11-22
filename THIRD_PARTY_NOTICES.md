# Üçüncü taraf bileşenler

Bu repodaki özgün kod ve belgeler MIT lisanslıdır (`LICENSE`). Aşağıdaki parçalar başkalarının işidir ve kendi lisanslarıyla gelir. Lisans metinleri belirtilen dosyalardadır. Denetim tarihi 2026-11-16.

## Farklı lisanslı parça

| Parça | Kaynak | Lisans | Not |
|---|---|---|---|
| `patches/openmontage.patch` | [OpenMontage](https://github.com/calesthio/OpenMontage) | AGPL-3.0 | OpenMontage üzerindeki değişikliklerdir. OpenMontage repoda yoktur; `kur.bat` onu ayrıca klonlar ve yamayı uygular. Yamayı ya da yamalı OpenMontage'ı dağıtan AGPL-3.0 koşullarına uyar. |

## Kopyalanan ya da uyarlanan skill'ler (`.claude/skills/`, kopyaları `.agents/skills/`)

| Skill | Kaynak | Lisans | Lisans metni |
|---|---|---|---|
| `earshot` | [Leonxlnx/earshot](https://github.com/Leonxlnx/earshot) | MIT | `licenses/earshot.MIT.txt` |
| `hyperframes`, `hyperframes-cli`, `hyperframes-registry`, `remotion-to-hyperframes` | [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | Apache-2.0 | `licenses/hyperframes.Apache-2.0.txt` |
| `yt-audit`, `yt-chapters`, `yt-comment`, `yt-edit`, `yt-package`, `yt-plan`, `yt-retention`, `yt-script`, `yt-seo`, `yt-shorts`, `yt-viral` | [Jakeschincariol/youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill) | MIT | `licenses/youtube-agent-skill.MIT.txt` |
| `playwright-cli` | [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli) | Apache-2.0 | `licenses/playwright-cli.Apache-2.0.txt` |
| `humanizer` | [blader/humanizer](https://github.com/blader/humanizer) | MIT | `licenses/humanizer.MIT.txt` |
| `graphify` | [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | Apache-2.0 | `licenses/graphify.Apache-2.0.txt` |
| `ingest`, `ask`, `lint`, `wiki-index` (uyarlama) | [paperclipai/paperclip](https://github.com/paperclipai/paperclip), `plugin-llm-wiki` | MIT | `licenses/paperclip-llm-wiki.MIT.txt` |
| `video-izle` (uyarlama) | [guimatheus92/mcp-video-analyzer](https://github.com/guimatheus92/mcp-video-analyzer) | MIT | `licenses/mcp-video-analyzer.MIT.txt` |
| `explainer-board-brief`, `explainer-board-system`, `board-sync` | [sirioberati/YouTube-AI-Motion-Graphics](https://github.com/sirioberati/YouTube-AI-Motion-Graphics) | MIT | `library/boards/LICENSE`, `.claude/skills/board-sync/LICENSE` |
| `bang-motion`, `claude-drawing`, `huashu-art-motion` | `library/vendor/` altındaki kaynaklar | MIT | Her klasörün kendi `LICENSE` dosyası |

## Kütüphane (`library/`)

| Parça | Kaynak | Lisans | Lisans metni |
|---|---|---|---|
| `library/boards/` (267 pano, katalog, tema) | [sirioberati/YouTube-AI-Video-Editing-System](https://github.com/sirioberati/YouTube-AI-Video-Editing-System), [YouTube-AI-Motion-Graphics](https://github.com/sirioberati/YouTube-AI-Motion-Graphics) | MIT | `library/boards/LICENSE` |
| `library/stiller/katalog.json` (31 hazır stil kartı, ADR 0042) | huashu-art-motion `风格配方`, bang-motion `references`, OpenMontage `styles/*.yaml` | MIT; AGPL-3.0 (OpenMontage kartlarındaki palet ve tempo değerleri) | Kart başına `kaynak` ve `lisans` alanı; metinler Türkçe yeniden yazıldı, kaynak kod kopyalanmadı |
| `library/vendor/bang-motion/` | Bang Tutorial | MIT | `library/vendor/bang-motion/LICENSE` |
| `library/vendor/claude-drawing-skill/` | cloveric | MIT | `library/vendor/claude-drawing-skill/LICENSE` |
| `library/vendor/eyeline-teleprompter/` | Sirio Berati | MIT | `library/vendor/eyeline-teleprompter/LICENSE` |
| `library/vendor/huashu-art-motion/` | alchaincyf | MIT | `library/vendor/huashu-art-motion/LICENSE` |
| `library/vendor/video-shotcraft/` (yalnız `references/`, `assets/lib`, README) | [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | Apache-2.0 | `library/vendor/video-shotcraft/LICENSE`; müzik ve ses varlıkları kopyalanmadı |
| `library/vendor/ClaudeAnimationBase/` | [JohnHeibel/ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase) | MIT | `library/vendor/ClaudeAnimationBase/LICENSE` |
| `library/vendor/pixelfx/` (yazı tipi hariç) | [patch-gg/pixelfx](https://github.com/patch-gg/pixelfx) | MIT | `library/vendor/pixelfx/LICENSE`, `NOTICE.md`; *Patch Pixel* yazı tipi lisans dışıdır, kopyalanmadı |
| `library/motion/custom/{ajan-adimlari,odometre-sayac,terminal-akisi,kelime-taklasi,isik-demeti,kenar-isiltisi,komut-paleti,secim-seridi,ayar-cubugu,kart-yelpaze,ai-kenarlik,sosyal-kanit}/`, `src/vedit/kurgu_kalite.py`, `src/vedit/ff.py` (`sdr_zinciri`), `.claude/skills/motion-design/references/kesim-surekliligi.md` | Proje yapımı; fikir kaynakları snapcn, product-launch-motion, claude-motion-design, motion-video-kit, motion-graphics, saas-motion-kit, ffmpeg-skill, brag, opus-video-skills (MIT), hyperframes, hyperframes-community-skills, open-edit, rea-video (Apache-2.0), onetake (PolyForm Noncommercial: yalnız fikir). Kod ve metin kopyalanmadı | MIT (bu repo) | ADR 0040 |
| `studio/remotion/fizik/`, `library/motion/tema/`, `library/motion/custom/gecis-{crt-kapanis,firca-darbesi,pencere,piksel-cozunme}-*` | Proje yapımı; fikir kaynağı yukarıdaki üç repo ve [lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) (belgeleri CC BY-NC 4.0: metin ve kod kopyalanmadı) | MIT (bu repo) | ADR 0039 |
| `src/vedit/sozluk.py`, `library/sozluk.json`, `kurgu_kalite.py` emoji uyarısı, `aiedit.py` pano haritası ve logo/kaynak kuralı, `library/checks.md` kapı kuralı | Proje yapımı; fikir kaynağı [avenoxai/avenox-video-kurgu-notlari](https://github.com/avenoxai/avenox-video-kurgu-notlari) (MIT, Copyright (c) 2026 Avenox). Kod ve metin kopyalanmadı | MIT (bu repo) | ADR 0041 |
| `library/vendor/gsap.min.js`, `library/motion/hf/*/gsap.min.js`, `.claude/skills/board-sync/assets/gsap.min.js` | [GSAP](https://gsap.com) 3.14.2, GreenSock | GSAP Standard License | <https://gsap.com/standard-license>; dosya başlığındaki telif bildirimi korunur |
| `library/fonts/*.ttf` (Inter, Montserrat, Space Grotesk, Playfair Display, JetBrains Mono, Outfit, EB Garamond, Fraunces, Pixelify Sans, VT323, Caveat, Bungee) | [google/fonts](https://github.com/google/fonts) | SIL Open Font License 1.1 | `library/fonts/licenses/` |

## Native motion bileşenleri (ADR 0045, 0046; denetim 2026-11-19)

| Parça | Kaynak | Lisans | Not |
|---|---|---|---|
| İkon geometrisi (`studio/remotion/motion/ikon/*`, path verisi) | [Lucide](https://github.com/lucide-icons/lucide) | ISC (Feather kökenli kısımlar MIT) | `licenses/lucide.ISC.txt`. Animasyon kareye bağlı olarak yeniden yazıldı. |
| İkon hareket fikirleri | [pqoqubbw/icons](https://github.com/pqoqubbw/icons) (lucide-animated) | MIT | Kod kopyalanmadı; Framer Motion yerine kare tabanlı yeniden yazım. |
| Kesim geçiş sunumları (`sil`, `kay`, `saat`, `iris`) | [@remotion/transitions](https://www.remotion.dev/docs/transitions) 4.0.484 | Remotion lisansı | Bağımlılık olarak kullanılır. |
| Lottie oynatıcı | @remotion/lottie 4.0.484, lottie-web 5.13.0 | Remotion lisansı, MIT | İçe aktarılmış Lottie dosyaları kendi lisanslarıyla gelir (`library/motion/dis/**/meta.json`). |
| Parametre şemaları | zod 4.3.6 | MIT | |
| Remotion | [remotion.dev/license](https://www.remotion.dev/license) | Remotion License | Bireyler ve en çok 3 çalışanlı şirketler için ücretsizdir; 4 ve üstü çalışanlı kâr amaçlı şirkette Company License gerekir. |

Kodu kopyalanmayan, yalnız incelenen kaynaklar:
- `marcusstenbeck/remotion-transition-series`: LICENSE dosyası yok.
- `av/remotion-bits`, `Remocn/remocn`, `Curvable/motion`: LICENSE metni doğrulanmadı.
- Kaynak: `work/agy/2026-11-19-motion/A/A1-lisans.md`.

## Repoda olmayanlar

- **Müzik, ses efekti ve motion klipleri:** lisans nedeniyle repoda yoktur. `library/music/manifest.json`, `library/sfx/INDIRME-LISTESI.md` ve `library/motion/manifest.json` yalnız liste tutar; dosyaları kullanıcı kaynağından indirir.
- **OpenMontage, node_modules, Python paketleri:** kurulumda indirilir, kendi lisanslarıyla gelir. Fizik ve ritim için: three (MIT), @react-three/fiber (MIT), @react-three/postprocessing ve postprocessing (MIT, Zlib), @remotion/three (Remotion lisansı), @dimforge/rapier3d-compat (Apache-2.0), librosa (ISC).

## Markalar

`library/boards/assets/` altındaki Claude ve OpenAI logoları ilgili şirketlerin markalarıdır. Panolar onları yalnız o ürünlerden söz ederken gösterir; bu repo o şirketlerle bağlantılı değildir.

## Ham notlar

`raw/` altındaki dosyalar kaynakların birebir kopyası değil, inceleme sırasında yazılmış özet notlardır; her notun başında kaynak adresi durur.
