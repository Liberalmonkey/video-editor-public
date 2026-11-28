---
type: decision
title: "0065 · Uygulama güncellemesi: Stüdyo'dan GitHub'a güvenli güncelleme"
tags: [studio, cat-cut, git, guncelleme, kurulum]
status: accepted
created: 2026-11-28
updated: 2026-11-28
sources: []
---

# ADR 0065: Uygulama güncellemesi

## Bağlam
cat-cut, GitHub'daki `Liberalmonkey/video-editor` deposunun klonu olarak kurulur (`kur.bat`). Yeni sürüm çıktığında kullanıcı bunu fark etmiyor, güncellemek için terminalden `git pull` yazması gerekiyordu. Kullanıcı başlıkta bir "Güncelle" düğmesi istedi: GitHub'da yeni sürüm varsa yanıp sönsün, tıklanınca güncel kod insin ve üzerinde çalışılan projelere zarar gelmesin.

Ölçülen veri dağılımı: `Projeler/` git'te değil, `git` işlemleri ona dokunmaz. `library/` (kurallar, kaizen, manifest'ler) ve `studios/` (stil paketleri) git'tedir; kullanıcı bunları her gün değiştirir. Düz `git pull` bu dosyalarda çakışıp güncellemeyi yarıda bırakabilir ya da kullanıcı değişikliğini ezebilir.

## Seçenekler
- **Sürüm zip'i indirip üzerine açmak:** git geçmişini ve kullanıcının yerel değişikliğini ayırt edemez, silinen dosyaları temizleyemez.
- **`git pull` (düz):** kirli ağaçta durur, çakışmada yarım birleştirme bırakır.
- **Yedekli, kapılı git akışı:** etiket + yedek kopya, stash, birleştirme, stash'i geri koyma, çakışmada kullanıcı sürümünü koruma. Seçilen budur.

## Karar
- **Modül:** `src/vedit/guncelle.py`; CLI `vedit guncelle [--kontrol|--uygula|--geri-al TS]`; Stüdyo rotaları `/api/guncelleme/{durum,kontrol,uygula,geri-al,yeniden-baslat}`; düğme `studio/web/src/paneller/GuncellemeDugmesi.tsx` (başlıkta HF rozetinin solunda).
- **Kontrol:** Stüdyo açıkken 30 dakikada bir `git fetch origin`; `HEAD` ile `origin/HEAD`'in gösterdiği varsayılan dal karşılaştırılır. Geride kalınmışsa düğme yanıp söner ve diyalog yeni commit başlıklarını gösterir. Ağ yoksa sessizce geçer.
- **Kapılar:** çalışan edit/render varsa (`hf_guncel.mesgul()`), HyperFrames kurulum kilidi varsa ya da başka bir güncelleme sürüyorsa reddedilir. Arayüz kaydedilmemiş kurguda düğmeyi kapatır.
- **Güvenlik sırası:** `cat-cut-oncesi-<ts>` etiketi; kirli ve izlenmeyen dosyaların kopyası `work/guncelleme/<ts>/yedek/`; `git stash push -u`; `merge --ff-only`, olmazsa `merge --no-edit`, çakışmada `merge --abort` ve kod eski haliyle kalır; `stash pop`; çakışan dosyada kullanıcının sürümü kalır, gelen sürüm `work/guncelleme/<ts>/gelen/` altına konur ve raporda listelenir.
- **Yasak komutlar:** `git clean`, `git reset --hard`, `git checkout -- .`. Geri alma yalnız açık istekle ve `git reset --keep` ile yapılır; yerel değişiklik çakışırsa durur.
- **Bağımlılık:** değişen dosyaya göre `pip install -e .`, `npm ci`, arayüz derlemesi. Başarısız adım uyarı olur, rapor `work/guncelleme/<ts>/rapor.md`.
- **Yeniden başlatma:** kullanıcı "Yeniden başlat" deyince sunucu `studio.vbs`'i ayrık başlatıp kapanır; derleme ya da kurulum gerekirse `baslat.hazirlik()` zaten `studio.bat` yoluna gider.

## Sonuçlar
- Güncelleme tek tıktır ve geri alınabilir; kullanıcı verisi kaybolmaz, en kötü durumda iki sürüm yan yana kalır.
- Yerel commit'i olan geliştirici dalında birleştirme commit'i oluşur; çakışırsa düğme "elle birleştirme gerekli" der.
- Testler `tests/test_guncelle.py` geçici bir "origin" ve klonla ff, kirli kural dosyası, çakışma, meşgul reddi, `Projeler/` dokunulmazlığı, geri alma ve birleştirme commit'ini dener.
