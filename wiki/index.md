---
type: overview
title: Wiki İndeksi
tags: [meta]
created: 2026-10-20
updated: 2026-10-20
---

# Wiki İndeksi

Wiki'deki her sayfanın kataloğu. LLM her ingest'te günceller; sorgularda ilk okunan dosyadır.
Format: `- [[sayfa]] — tek satır özet`

## Genel
- [[overview]] — Projenin güncel büyük resmi ve sentezi
- [[log]] — Kronolojik işlem günlüğü

## Specs (özellikler)
- [[hf-canli-gomme-ve-dikey-duzen]] — HyperFrames canlı gömmede kök sorgusu hatası (42 şablon) ve 9:16 dikey düzen; agy aile ajanlarıyla (done, 2026-11-26)
- [[video-studyo]] — Video Stüdyo: paneller, veri modeli, render köprüsü, kabul kriterleri (done)
- [[ugc-studyosu]] — Ürün tanıtımı/satış odaklı çekim kurgusu, 3 en-boy varyantı (active, 2026-10-20)
- [[instagram-studyosu]] — Reels: 9:16, güvenli alan, kapak karesi, loop (active, 2026-10-20)
- [[youtube-animasyon-studyosu]] — 10–15 dk eğitici/eğlenceli animasyon, bölüm render (active, 2026-10-20)
- [[sfx-kutuphanesi]] — library/sfx manifest, index/fetch/synth/resolve (active, 2026-10-20)

## Decisions (ADR)
- [[0001-claude-code-skill-ajan-mimarisi]] — Claude Code skill + 8 alt ajan + vedit CLI, 3 stüdyo klasörü (accepted)
- [[0002-renderer-hyperframes]] — Tek renderer HyperFrames 0.8.181 + FFmpeg ön-geçiş; Remotion reddedildi (accepted)
- [[0003-model-yonlendirme]] — Ana Opus; ajan ve model tablosu (accepted)
- [[0004-ses-efekti-stratejisi]] — Yerel CC0 kütüphane + Freesound/Openverse + sentez (accepted)
- [[0005-timeline-json-tek-dogruluk-kaynagi]] — LLM JSON yazar, HTML üretilir; EDL → FFmpeg A-roll (accepted)
- [[0006-tts-yedegi]] — Chatterbox/Kokoro TTS yedeği (superseded → 0007)
- [[0007-seslendirme-kullanici-harici-arac]] — Seslendirmeyi kullanıcı harici araçta üretir, TTS kaldırıldı (accepted, 2026-10-21)
- [[0008-harici-varlik-kaynaklari]] — Müzik/SFX/motion kullanıcı 6 siteden indirir; atıf credits.txt; teslim Projeler/ (accepted, 2026-10-21)
- [[0009-token-optimizasyonu]] — Caveman plugin (yalnız sohbet, içerik hariç) + CLAUDE.md 14,6→6 KB, wiki kuralları .claude/wiki-kurallari.md (accepted, 2026-10-21)
- [[0011-yerel-arayuz]] — Yerel web arayüzü (superseded, [[0017-terminal-hizli-hat]])
- [[0012-kutuphane-kit]] — Kütüphane kiti: kilitli ve her zaman kullanılan varlıklar, library/kit.json (accepted, 2026-11-01)
- [[0013-uretim-akisi-ve-olay-sesi]] — Arayüzde yapım akışı ve motordan bağımsız olay sesi (accepted, 2026-11-02)
- [[0014-altyazi-standardi-ve-repo-entegrasyonu]] — Sabit altyazı standardı (odak), pano kütüphanesi, kesim denetimi, repo seçimi (accepted, 2026-11-03)
- [[0016-earshot-render-standardi-ajan-duzeni]] — earshot ses ölçümü, vedit teslim render standardı, beş ajan ve çağrı başına model (accepted, 2026-11-03)
- [[0015-ai-slop-denetimi]] — Edit sonrası slop ölçümü, kare incelemesi ve onaylı düzeltme önerisi (accepted, 2026-11-03)
- [[0010-openmontage-edit-motoru]] — OpenMontage varsayılan edit motoru; /video yalnız açık istekte, bütçe cap 0 USD, ortak müzik kütüphanesi (accepted, 2026-10-23)
- [[0017-terminal-hizli-hat]] — Arayüz kalktı; tek girdi/çıktı düzeni, hızlı hat, skill katmanları, kaizen (accepted, 2026-11-04)
- [[0024-oneri-araclari]] — Konuşma temizliği, kesim önerisi, metinden kurgu, Demucs, reframe, ses keyframe, XML (accepted, 2026-11-05)
- [[0025-gorsel-uretimi-google]] — Kapak ve görsel üretimi: ücretsiz Google araçları, kodla yazı katmanı (accepted, 2026-11-08)
- [[0034-ses-araclari]] — Ses araçları: ses çıkarma, 2 ve 4 kanallı ayırma, hepsi Ses panelinde (accepted, 2026-11-12)
- [[0038-video-izleme-ve-google-baglantilari]] — `video-izle` skill'i, kütüphaneye 12 yeni kayıt, Stitch, `gws`, YouTube ve tarayıcı yolları
- [[0040-ikinci-repo-dalgasi]] — on beş repodan yalnız kazanç: HyperFrames 0.9.56, HDR ton eşleme, kalite uyarıları, SFX parlaklığı, 12 şablon, kesim sürekliliği
- [[0041-avenox-kurgu-dersleri]] — pano haritası sorusu, logo/kaynak kuralı, transkript düzeltme sözlüğü, emoji uyarısı, "iki kez olan hata koda" kapı kuralı
- [[0042-stil-katalogu-ve-video-temasi]] — stil silme, 31 hazır stil (anime, çizgi film, editoryal...), motion teması stilden ya da videodan; turuncu yalnız istenirse
- [[0043-stile-bagli-tema-tokenlari]] — tek token şeması (renk, font, şekil, hareket, altyazı); 31 stilin kendi teması, piksel-8bit, sabit renk testi, stilli altyazı
- [[0044-ekip-motoru]] — 3 editör + 3 kalite kontrol ajanı, turlu düzeltme, slot başına motor/model, Stüdyo Ekip modu (yerini 0048 aldı)
- [[0045-native-motion]] — tema token'ına bağlı native Remotion grafikleri, orta noktalı geçişler, yüzden kaçan yerleşim, alfa (proxy) düzeltmesi
- [[0046-dis-varlik-ve-lisans]] — `vedit motion ice-al`: zorunlu lisans kaydı, alfa yöntemi tespiti, Lottie tema boyası, yayin.md atfı
- [[0047-kural-deposu]] — kurallar.json ve Kurallar sayfası; QC kural adayı, mezar taşı, rol başına teslim; checks.md üretilir
- [[0048-ekip-motoru-v2]] — sözleşme, paralel düzen, çapa eşleme, deterministik birleştirme, tek QC, tek düzeltme (yerini 0053 aldı)
- [[0049-yapim-ekibi]] — Claude mimar ve entegratör, agy Gemini 4 Neon sözleşmeye karşı kod ve inceleme yazar
- [[0050-hyperframes-birincil-motor]] — HyperFrames 0.9.77 birincil motor, Remotion ikinci plan; sanat-yonetimi skill'i; Stüdyo hızlı açılış
- [[0051-uctan-uca-hyperframes]] — Tek derleyici (kurgu → HyperFrames), çift motor geçişi, otomatik güncelleme + duman testi
- [[0039-fizik-ritim-galeri]] — fizik ve karakter sahnesi (Rapier bake), ritim, senkron, viseme, `fizik-sezgisi`, 10 tema, 8 geçiş, Stüdyo galerisi
- [[0037-antigravity-orkestra]] — Antigravity 1.5.9: `--ajan`, aşamalı `orkestra`, `elestirmen`, `wiki-bakici`, `orkestrator` ajanları
- [[0036-motion-kutuphanesi-ve-ajanlar]] — Motion kütüphanesi: `vedit motion kur`, parametrik şablon, on tema, yoğunluk hedefi, Stüdyo Motion paneli, üç motion alt ajanı (accepted, 2026-11-13)
- [[0035-teslim-ayarlari]] — Teslim ayarları: HD/FHD/QHD/UHD çözünürlük, CRF kademesi, H.264/H.265, 30/60 fps; Teslim alanında Çıktı ayarları paneli (accepted, 2026-11-13)
- [[0033-hazir-efektler]] — Hazır efektler: zoom, punch, odak zoom, ken burns, giriş ve çıkış; klipte `hazir`, render'da keyframe (accepted, 2026-11-12)
- [[0032-ses-katmani]] — Ses katmanı: rol olayı sözleşmesi, katmanlı kombolar, Türkçe güç adları, vuruş öncesi müzik çekme, Wyzowl kiti (accepted, 2026-11-12)
- [[0031-motion-grafik]] — Motion grafik: metin türleri, tam ekran sahneler, saydam pano, proje yapımı motion kütüphanesi (accepted, 2026-11-12)
- [[0030-sade-arayuz]] — Sade arayüz: üç çalışma alanı (Kurgu, Teslim, Kütüphane), her iş tek yerde (accepted, 2026-11-12)
- [[0029-stil-paneli]] — Stil paneli: referanstan STYLE.md üretimi (`vedit stil-uret`), projeye stil seçimi (accepted, 2026-11-12)
- [[0028-ai-edit]] — AI edit: Final öncesi kurguyu ajan yazar, vedit doğrular ve render eder (`vedit ai-edit`) (accepted, 2026-11-12)
- [[0027-kapak-sayfasi]] — Kapak sayfası: YouTube ve Instagram, Antigravity ile 1-5 aday, iki platform skill'i (superseded, 2026-11-24)
- [[0052-kapak-is-akisi-v2]] — Kapak v2: video seç, fikri geliştir, agy modeli, bölgesel görsel düzeltme, master prompt, dış görsel (superseded, 2026-11-24)
- [[0057-her-makinede-hiz]] — Her makinede hız: tembel Remotion yolu, doğru JS parçaları (ilk yük 2,7 → 0,9 MB), tembel CLI importu, ölü kod ve paket temizliği, `jsonschema` bağımlılığı (accepted, 2026-11-24)
- [[0058-hizli-ve-kaliteli-edit]] — Hızlı ve kaliteli edit: tema kilidi denetimi, görselli tek tur QC, 15 fps önbellekli QC render'ı, dilimli QC, G6 uyarı kapısı; `--hizli` 672 → 419 sn, uyarı 1 → 0 (accepted, 2026-11-25)
- [[0059-swarm-edit]] — Swarm edit: ajan tavanı (`--en-cok`, seviye kısaltması 3-15), orkestratörün kart başına model seçimi, plana paralel kurgu editörü, birleştirme sağlamlığı (id'siz öğe, render kurtarma, geçiş kısa yazımı); medium 778 → 692 sn (accepted, 2026-11-25)
- [[0060-proxy-master-conform]] — proxy (vekil) ile kurgu ve taslak, teslimde orijinale conform kapısı; Master ön ayarı (kayıpsız 4:4:4 ara, H.265 10-bit, kaynağa eşle), zscale renk zinciri, SSIM/PSNR/VMAF sadakat ölçümü (accepted, 2026-11-25)
- [[0061-kasa-ve-kesif]] — hibrit motion kütüphanesi: Kasam (videodan kaydet, niyetiyle), Keşif (şablon + dış), Arşiv; kilidi kaldırıp silme, toplu silme, galeride gizleme; alfa kırpımlı doğru-kare önizleme (accepted, 2026-11-25)
- [[0062-modern-hyperframes-motion-mimarisi]] — canlı `data-composition-src` HF gömme, Tema v2, `+1 kare` ses ipuçları, 4-düzen, sürekli-dünya kamera, 5 optik geçiş, 24 modern HF şablonu, 5 referans stil ve Swarm v4 G0.5 brifi (accepted, 2026-11-25)
- [[0063-gsap-eklentileri-ve-threejs-hf]] — GSAP eklenti paketi (SplitText, DrawSVG, MorphSVG, MotionPath, tema eğrileri), `uc.js` three.js çekirdeği (saydam WebGL, seçici bloom), 22 yeni şablon, hareket kişiliği ve beş bölümlü motion brifi (accepted, 2026-11-25)
- [[0064-yaratici-yon]] — G0.5 yaratıcı brif (tez, enerji eğrisi, imza anları, metafor, iplik, ses, riskler, yasak klişeler); swarm'da plan çağrısında, hızlıda tek kısa çağrıda, tek ajanda kurgudan önce; şablondan özerkliğe sekiz adımlı yükseltmenin ilki (accepted, 2026-11-26)
- [[0056-kapak-kaldirildi]] — Kapak özelliği kaldırıldı: Kapak alanı, `vedit kapak`, `--kapak-kare`, iki kapak skill'i; şablon `library/gorsel/`'e taşındı (accepted, 2026-11-24)
- [[0053-seviyeli-ekip-orkestrator]] — seviyeli ekip (low 2+1 … max 10+5), orkestratör, kapılı paralel akış, kural uyumu ve kural işleme güvencesi, sade AI paneli (superseded → 0059, 2026-11-25)
- [[0054-hizli-edit]] — yalın ajan çağrısı, pafta ile QC, koşullu orkestratör ve render, deterministik ön düzeltme, `--hizli` ön ayarı (superseded → 0059, 2026-11-25)
- [[0055-teslimde-yayin-metni]] — Teslim'de video başına, platforma göre başlık, açıklama ve hashtag (`vedit yayin`, Yayın metni paneli, varsayılan Opus 5.5) (accepted, 2026-11-23)
- [[0026-arayuzde-ajan]] — Video Stüdyo AI paneli: Claude Code ya da Antigravity, model seçimi arayüzde (accepted, 2026-11-08)
- [[0023-coklu-ajan]] — Antigravity CLI ve Codex kopyaları tek kaynaktan üretilir (accepted, 2026-11-05)
- [[0022-av-ayirma-metre-yatay]] — Görüntü ve sesi ayırma, canlı metre, 16:9 sahne şablonları (accepted, 2026-11-05)
- [[0021-video-studyo-nle]] — Yerel çok izli kurgu uygulaması, kurgu.json tek kaynak, AI terminalde (accepted, 2026-11-05)
- [[0020-panel-kaldirildi]] — Panel ve ai-video-edit-workflow kodu silindi, yalnız SplitReel hattı, ölçülmüş hız değişiklikleri (accepted, 2026-11-05)
- [[0019-arayuz-ve-efekt-motoru-birlesimi]] — ai-video-edit-workflow birleşimi: ince panel, motor/, tek hat (superseded, 2026-11-05)
- [[0018-viral-kurgu-skill]] — Platform sinyallerine göre kurgu reçetesi ve taslak kapısı (accepted, 2026-11-04)

## Concepts (kavramlar)
- [[render-sozlesmesi]] — Her kare t'nin saf fonksiyonu; seed'li rastgelelik; tek kare inceleme (2 kaynak)
- [[motion-design-ilkeleri]] — Yasaklar, işe göre easing, süreklilik, ritim, kısa/uzun format kuralları (1 kaynak)
- [[model-yonlendirme]] — İşi kaliteyi düşürmeyen en ucuz modele verme (1 kaynak)
- [[token-ekonomisi]] — Digest, kontak sayfası, JSON, onay kapısı, artımlı render (3 kaynak)
- [[sfx-stratejisi]] — 4 katmanlı ücretsiz SFX: kütüphane, çekme, sentez, deterministik yerleştirme (3 kaynak)
- [[loudness-standartlari]] — -14 LUFS / -1 dBTP; müzik ve SFX göreli seviyeleri (2 kaynak)
- [[timeline-json]] — Projenin şemalı tek doğruluk kaynağı (1 kaynak)

## Entities (araçlar, kütüphaneler, modeller, rakipler)
- [[hyperframes]] — HTML+GSAP → MP4 renderer, Apache-2.0 (library)
- [[remotion]] — React video framework, değerlendirildi/reddedildi (library)
- [[ffmpeg]] — Kesim, ses mastering, QA ölçümleri (tool)
- [[faster-whisper]] — Kelime zaman damgalı transkripsiyon, TR/EN (library)
- [[humanizer]] — AI-yazı izlerini temizleyen skill, MIT (tool)
- [[opus-animasyon-rehberi]] — Motion design metodolojisi ilham kaynağı, lisanssız (tool)
- [[freesound]] — CC0 SFX API'si (service)
- [[kenney-audio]] — CC0 UI/arayüz ses paketleri (service)
- [[yt-dlp]] — Referans video/altyazı indirme (tool)
- [[graphify]] — Kod, wiki ve ham kaynaktan bilgi grafiği; `/ask` ve `/lint` ile kullanılır (tool)

## Sources (kaynak özetleri)
- [[2026-11-13-motion-kutuphane-arastirmasi]] — bang-motion, huashu-art-motion, claude-drawing-skill, vox-explainer-skill ve benzerleri: lisans, maliyet, ne alındı (araştırma)
- [[2026-11-12-motion-grafik-arastirmasi]] — Remotion ekosistemi, MIT topluluk şablonları, lisans tuzakları, öncelikli 10 motion şablonu (araştırma)
- [[2026-11-12-ses-efekti-kaynaklari]] — CC0 ses efekti kaynakları, indirme planı, profesyonel yerleşim sayıları (araştırma)
- [[2026-11-04-ai-video-edit-workflow]] — Form, 25 efekt, dikey kırp-takip, plan kapıları (repo, MIT)
- [[2026-11-09-kapak-arastirmasi]] — MrBeast, Nick Saraev, Iman Gadzhi kapak kalıpları, Test & Compare, Instagram ızgara ölçüleri (araştırma)
- [[2026-11-15-kapak-kalip-analizi]] — 138 referans kapağın kalıp, yazı stili ve izlenme analizi; şablon kalıpları buradan (Antigravity analizi)
- [[2026-11-22-kapak-arastirmasi-v2]] — Nano Banana prompt kuralları, kırmızı kutu düzeltmesi, agy görsel modeli, açık kaynak kapak araçları (araştırma)
- [[2026-11-16-ikinci-repo-dalgasi]] — on beş repo: lisans, tekrarlar, gerçek kazançlar, doğrulanamayanlar
- [[2026-11-17-avenox-kurgu-notlari]] — Avenox ajanla kurgu notları (MIT): tek şef, kapılar, pano haritası, transkript sözlüğü
- [[2026-11-16-fizik-stil-repolari]] — on repo: lisans, sürüm, bake mimarisi, 30 fizik-ışık-ses kuralı, tema ve efekt adayları
- [[2026-11-04-platform-algoritmalari]] — YouTube, Instagram, LinkedIn sinyalleri ve Nick Saraev kurgu ölçümü, kanıt düzeyli (araştırma)
- [[2026-10-20-opus-animasyon-rehberi]] — Opus ile kodla animasyon rehberi (repo)
- [[2026-10-20-hyperframes]] — HyperFrames repo + yerel kurulum testi (repo)
- [[2026-10-20-remotion]] — Remotion repo incelemesi (repo)
- [[2026-10-20-humanizer]] — humanizer skill (repo)
- [[2026-10-25-youtube-agent-skill]] — YouTube yayın paketi: 11 yt-* skill, hook/başlık/retention araçları (repo)
- [[2026-11-02-kalem]] — Sahneye göre motor seçimi, kareye kilitli ses (repo + video)
- [[2026-11-02-loop-slayt]] — Loop slayt yöntemi, Flow'a uyarlandı (repo + video)
- [[2026-11-03-sirio-berati-repolari]] — Pano, kelimeye kilit, teleprompter, kesim denetimi; alınan ve alınmayan repolar
- [[2026-10-20-ffmpeg]] — FFmpeg filtre seçkisi (repo)
- [[2026-10-20-sfx-ve-arac-arastirmasi]] — SFX/müzik/TTS/çekim araçları ve lisanslar (araştırma)
- [[2026-11-25-motion-kaynaklari]] — prompt-motion, gsap-skills, threejs-skills, LottieFiles motion-design, video-shotcraft, pascal editor: ne alındı, ne alınmadı

## Queries (dosyalanmış cevaplar)
- [[2026-11-02-usta-editor-denetimi]] — Sistem 15 yıllık editör seviyesinde mi: güçlü, zayıf yönler ve öneriler
