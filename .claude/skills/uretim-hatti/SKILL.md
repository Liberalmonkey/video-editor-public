---
name: uretim-hatti
description: Video üretiminin tek giriş noktası, terminalden — konu ya da hazır senaryo, malzeme listesi, hızlı edit, denetim ve teslim. "yeni video", "videoyu editle", "reels yap", "senaryo yaz", "malzeme listesi", "sıradaki adım", "düzeltme yap" dendiğinde kullan.
---

# Üretim hattı

Hedef: en az render ve en az okuma ile yayına hazır video. Sıra: senaryo, malzeme, edit, denetim, teslim, kaizen.

## Düzen

Kullanıcı her şeyi girdi klasörüne koyar, videoyu çıktı klasöründen alır. Görsel kurgu isteğe bağlı: `vedit studio` (ADR 0021). `work/edit/kurgu.json` olan projede düzeltme yalnız ona yazılır; `sahne.mjs` çalışmaz, `olaylar.json` ondan üretilir. Eski projeyi almak: `vedit kurgu-al <proje>`. `kurgu.json` yazdıktan sonra `vedit kurgu-denetle <proje>` çalıştır; Stüdyo açıksa değişikliği anında alır, kullanıcının kaydedilmemiş düzenlemesi varsa ona sorar. Ses düzeltmesinde görüntü render etmeden `vedit miks <proje>` ölç. Eski projelerdeki `brief.md` tercih kaynağıdır, sabitleri ezmez.

```
Projeler/inputs/<stüdyo>/<proje>/        ham çekim, ekran görüntüsü, senaryo, ISTEK.md
Projeler/outputs/<stüdyo>/<proje>/       teslim mp4, srt, kapak, yayın metni, NOTLAR.md
Projeler/outputs/<stüdyo>/<proje>/work/  analysis, edit, renders, qa, public, sure.jsonl
```

Video ve ses yalnız burada durur; ses efekti, müzik ve motion `library/`'dedir. Stil referansları `Projeler/inputs/_referanslar/<stüdyo>/`. Stüdyolar: `instagram`, `ugc`, `youtube-animasyon`. Senaryo ve teslim dosyaları tam düzyazıdır.

## Hız kuralları

1. Düzeltme döngüsü `vedit taslak` ile yapılır. `vedit final` bir kez çalışır; final sonrası düzeltme varsa önce yine taslak. Yalnız ses düzeltmesinde final motor render'ını atlar.
2. Tek sahne değiştiyse `--aralik BAS BIT`, tüm videoyu render etme.
3. Ham medya ve büyük JSON okuma: `vedit hazirla` çıktısı, `digest.txt` ve kontak sayfası yeter.
4. Edit ana oturumda yapılır. Ajan yalnız taze göz (`director`) ve uzun ölçüm çıktısı (`render-qc`) içindir.
5. Editten önce `library/checks.md` ve `library/kit.json`. Kullanıcı düzeltmesi tek satırla `checks.md`'ye.

## 1. Senaryo

**Konu verildiyse:** olguları kaynaklı topla (`writer` ajanı ya da `konu-arastirma`), `hikaye-matematigi` ile 8 adımı kur, ayna çiftlerini kontrol et, `scriptwriting` ile süre bütçesini dağıt. `yt-script` ile 5 hook yaz, `hookscore.py` ile puanla, en iyi ikisini göster. İlk 15 sn tıklamayı doğrular, kapanmayan soruyu açar, ödülün varlığını kanıtlar. Her 30–60 sn değişim, her paragrafa `[EKRAN: …]`, `humanizer`, teleprompter. Uydurma sayı yok; eksik veri `[KAYNAK?]`. `studios/<s>/references/voice.md` varsa ona uy, yoksa kullanıcıya söyle.

**Senaryo verildiyse:** metin kullanıcınındır, `girdi.md` asla ezilmez. `senaryo.md` aynı metin + `[EKRAN: …]` notlarıdır. Story Circle, hook puanı, tutma ve doğruluk önerileri `oneriler.md`'ye gider. Onay gelmeden metin değişmez. Finans konusunda `konu-arastirma` dürüstlük kuralları geçerlidir.

Açıklama videosunda onaydan sonra `explainer-board-brief` ile görsel isteyen satırı belirle. Animasyonlu işte `sanat-yonetimi` stil kartını `work/edit/stil-karti.md`'ye yaz; aynı serideki önceki karttan en az üç eksende ayrış. Kullanıcı okuyacaksa `teleprompter` skill'ini öner. Onay almadan malzeme istemeye geçme. Hook ve kapanış önerisi için format reçetesi `viral-kurgu`.

## 2. Malzeme

Önce sahip olunanı kullan: `library/kit.json`, `library/{sfx,music,motion}/manifest.json`. Yalnız eksiği `Projeler/inputs/<s>/<p>/ISTEK.md`'ye yaz, sahne sırasına göre, kullanıcının çekim sırasında okuyacağı sade Türkçeyle. Her kalem: kimlik, tür (`ses`, `ekran-kaydi`, `ekran-goruntusu`, `broll`, `loop`, `muzik-sfx`), açıklama, süre, sahne, kaynak/ayar.

- Dosya adı kimlikle başlarsa kalemi karşılar: `E01-bilanco.mp4`.
- Ekran kaydında ne gösterileceğini tıklama tıklama yaz. Belirsiz istek işe yaramaz çekim getirir.
- Ses kalemi örneği: 48 kHz WAV, sessiz oda, ağız–mikrofon 15 cm. Ekran kaydı: 1080p, 30 fps, tarayıcı yakınlaştırma %125, imleci yavaş götür.
- Loop ve görseller `loop-flow`; prompt kalemin içinde. Müzik/SFX lisansı `sound-design`; site, arama terimi, süre ver. Ses efekti listesi `library/sfx/INDIRME-LISTESI.md`.

Kontrol isteğinde: dosyaları kalemlere eşle, adlarını kimlikle başlat (kullanıcı dosyasını silme), `ffprobe` ile süre ve çözünürlük bak, kaliteyi söyle. Altyazı standardı sabittir, sorulmaz.

## 3. Edit

Tek komut (Stüdyo'da "AI Edit" ve Final diyaloğu): `vedit ai-edit <proje> [--stil <ad>] [--not "…"] [--final]` kurguyu ajana yazdırır (yalnız `kurgu.json` + `ai-edit.rapor.md`), doğrular, taslak alır (ADR 0028). Ana oturumda elle editte aşağıdaki sıra geçerlidir.

Kurallar `usta-editor` ve `viral-kurgu`; kod sahnesi varsa `sahne-motoru` tablosunu göster, onay al. Grafik, animasyon ve motion üretimi önce HyperFrames'tedir (ADR 0050): kompozisyon `work/edit/hf/<ad>/` ya da `library/motion/hf/<ad>/`, klipte `hf: {ad, param}`, sözleşme `library/motion/hf/SOZLESME.md`, tek kompozisyon `vedit hf kur`. Timeline birleştirmesi `kurgu.json`; taslak, final ve Stüdyo önizlemesi HyperFrames'te derlenir (ADR 0051), motor ve nedeni `work/edit/motor.json` ve Stüdyo rozetinde. Reels'te eski yol `SplitReel`, diğerlerinde `openmontage/AGENT_GUIDE.md` (yalnız bu durumda oku).

1. `vedit hazirla <proje>`: ffprobe, önbellekli transkript, digest, kontak sayfası.
2. Ses önce: dolgu, tekrar, sessizlik temizliği (`footage-editing`), birden çok kayıt varsa birleştir, `vedit kesimqa`.
   Kullanıcı sıra verdiyse parçalar yer değiştirmez. Kesilmiş videolarda `kesim.json` yazma: `vedit kes` hepsini doğal ad sırasıyla birleştirir. Sonra `vedit hazirla <proje> --ek work/public/speaker.mp4`.
3. Sahne planı: `work/edit/sahne.mjs` (`remotion-composer/reel_kit.mjs`); yalnız sahne ve altyazı düzeltmesi yazılır. Zamanlar kelimeye kilitlidir.
4. Her zoom, geçiş, kesme ve ekran olayı `work/edit/olaylar.json`.
5. `vedit taslak <proje>` → kontak sayfası → `viral-kurgu` taslak kapısı → düzelt.
6. `vedit final <proje> --platform <youtube|reels|ugc>`: tam render, `olaysesi`, `teslim`, `denetim`.
7. `denetim` skill'i: rubrik + slop raporu. P0 ve P1 düzelir, en çok 2 tur. Slop önerileri onaysız uygulanmaz. Hüküm YAYINLANAMAZ ise dur, kullanıcı kararını al.

## 4. Teslim

Kullanıcı onaylayınca çıktı `Projeler/outputs/<s>/<p>/<ad>.mp4`; eskisinin üzerine yazma, `-v2` ekle. YouTube için elle: `/yt-package`, `/yt-seo`, `/yt-chapters` → `yayin.md`. Her videoda yayın paketi `Projeler/outputs/<s>/<p>/yayin.md` (`viral-kurgu` Yayın paketi): açıklama, hashtag, kapak (`vedit kapak`, `kapak-youtube` / `kapak-instagram`; varsayılan 1, istenirse en çok 5 aday). Paket çıktıyla birlikte verilir, kullanıcı istemeden de. Yayınlama. Yeniden kullanılabilir grafik çıktıysa kütüphaneye al (`library/motion/custom/<id>/`, şeffaf `.webm` + kaynak, manifest), kilit öner.

## 5. Kaizen

Her teslimde: `vedit kaizen <proje>` ve `vedit duzen`. Tek satır sonuç `library/kaizen.md`'ye yazılır. En yavaş adım için tek küçük iyileştirme yap ya da öner. Tekrarlanan el işi `vedit`/`reel_kit`'e, kullanıcı düzeltmesi `checks.md`'ye, hiç kullanılmayan skill elle çağrılan katmana.

## Sık istekler

Sıradaki adım: `vedit hazirla` durumu ve `work/` içeriğine bak, yapılabileni yap, onay gereken yerde dur. Düzeltme: yalnız o alanı değiştir, taslak al. Shorts adayı: `/yt-shorts`. Kütüphaneye kaydet: yukarıdaki kural, sonra rol sor.

Elle çağrılanlar (otomatik açılmaz, gerekirse `.claude/skills/<ad>/SKILL.md` yolundan oku): `hyperframes-*`, `video`, `yt-*`, `board-sync`, `explainer-board-*`, `directing`, `style-pack`, `playwright-cli`.
