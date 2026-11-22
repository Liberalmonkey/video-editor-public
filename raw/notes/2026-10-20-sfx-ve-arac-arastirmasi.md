---
accessed: 2026-10-20
note: LLM araştırma notu (alt ajan, web + GitHub raw). Doğrulanamayan maddeler "doğrulanmadı" işaretli.
---

# Ses efekti, müzik, TTS ve çekim araçları araştırması

## SFX kütüphaneleri (ticari YouTube/Instagram)
| Kaynak | Lisans | API | Not |
|---|---|---|---|
| Freesound | Ses başına CC0 / CC-BY / CC-BY-NC | APIv2 | `filter=license:"Creative Commons 0"`; preview token ile, orijinal OAuth2; loudness LUFS döner. Sadece CC0 al. |
| Kenney audio | CC0 | Yok (zip) | 100 arayüz + 50 UI sesi; normalize edilmiş; UI/dokunma temel kaynağı |
| @remotion/sfx | Paket MIT, ses başına lisans | Düz URL | Sadece CC0 olanlar: whip, whoosh, pageTurn, uiSwitch, mouseClick, shutterModern, shutterOld, ding. Meme sesleri hariç. |
| Openverse | CC0 / CC BY | Hesapsız API | HyperFrames media-use bunu kullanıyor |
| Sonniss GDC paketleri | Telifsiz, atıfsız | Yok | ~7.5 GB/yıl; tek başına SFX olarak yeniden dağıtım ve AI eğitimi yasak; riser/impact/whoosh çok iyi |
| Mixkit | Mixkit SFX Free License | Yok | YouTube kullanımı serbest, atıf gerekmez; öğe başına kontrol |
| Pixabay | Pixabay Content License | Ses API'si yok | Elle indirme; müzikte ara sıra Content ID talebi |
| Zapsplat | Ücretsiz katman atıflı (doğrulanmadı) | Yok | |
| BBC Sound Effects | RemArc, ticari değil (doğrulanmadı) | Yok | Para kazanan kanalda KULLANMA |
| YouTube Audio Library | Standart lisans YouTube'a özel | Yok | Instagram'da kullanma |

## AI üretimi
- ElevenLabs SFX: ücretli plan ticari; "sadece ücretsiz" kararı gereği kapsam dışı
- Stable Audio Open 1.0 / Small: Stability Community License (yıllık gelir < $1M ticari serbest); Small 341M parametre, ~11 sn, İngilizce prompt; 4 GB GPU'da denenebilir (doğrulanmadı)
- MMAudio, AudioCraft (AudioGen/MusicGen) ağırlıkları CC-BY-NC → kullanma; ThinkSound model kartı ticari değil → kullanma

## Önerilen katmanlı strateji
1. Yerel kürate kütüphane (300–600 dosya), ffmpeg ebur128 ile ölçüm, -18 LUFS normalize, baş sessizliği kırpma, peak/onset offset; manifest.json {id, file, category, tags, duration_s, peak_offset_s, lufs, license, source_url, attribution_required}
2. Eşleşme yoksa Freesound (CC0) / Openverse'ten çek, işle, manifest'e ekle
3. Prosedürel sentez / yerel AI yedek

Yerleştirme çoğunlukla EDL'den deterministik: kesim → whoosh (start = kesim − peak_offset), metin girişi → pop, punch-in → impact, liste → click, reveal öncesi → riser. LLM sadece anlamsal ipuçları (ör. "telefonum çaldı" → phone_ring), kompakt etiket listesi (~1–2k token) ile. Kurallar: ~0.4 sn'de en fazla 1 SFX, sesin -8…-14 dB altında, aynı id arka arkaya yok.

## Müzik
Pixabay Music, Mixkit, Free Music Archive CC-BY (atıflı). YouTube Audio Library standart parçalar sadece YouTube.

## Çekim araçları
| Araç | Lisans | Rol |
|---|---|---|
| faster-whisper | MIT | word_timestamps; large-v3(-turbo) Türkçe iyi |
| WhisperX | BSD-2 | wav2vec2 hizalama; Türkçe model mpoyraz/wav2vec2-xls-r-300m-cv7-turkish |
| whisper.cpp | MIT | Bağımlılıksız; HyperFrames transcribe bunu kullanır |
| auto-editor | Unlicense | Sessizlik/hareket kesimi, NLE export |
| PySceneDetect | BSD-3 | Çekim/kesim tespiti |
| DeepFilterNet | MIT/Apache-2.0 | Yüksek kalite konuşma gürültü temizleme |
| MediaPipe | Apache-2.0 | Yüz/poz; 9:16 reframe için kendi takipçimiz |
| Chatterbox Multilingual | MIT | Açık TTS, Türkçe + İngilizce, zero-shot ses klonlama, 0.5B |
| Kokoro | Apache-2.0 | Hızlı, kaliteli; Türkçe YOK |
| F5-TTS, XTTS-v2 | Ağırlıklar ticari değil | Kullanma |
| yt-dlp | Unlicense | Referans video/altyazı indirme (`--skip-download --write-auto-subs`) |
| FFmpeg kontak sayfası | — | `fps=1/5,scale=320:-1,tile=4x4` → 16 an tek görselde (~1.5k token) |

Ticari hatta kaçınılacaklar: MMAudio, ThinkSound, AudioCraft, F5-TTS/XTTS ağırlıkları, BBC SFX, Freesound CC-BY-NC, @remotion/sfx meme sesleri.

## Bu makine (2026-10-20)
GTX 1650 4 GB, 16 GB RAM, i5-11400H 12 çekirdek; kurulu: faster-whisper 1.2.1, yt-dlp 2026.08.19, FFmpeg 9.0.2, Node 24, Python 3.12, Docker (çalışmıyor).
