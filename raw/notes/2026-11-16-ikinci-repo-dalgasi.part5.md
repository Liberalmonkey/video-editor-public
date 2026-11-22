# 2026-11-16-ikinci-repo-dalgasi (devam 5)

#### 6. `snapcn` (shadcn-labs / Sri Nath — MIT)
- **(1) Ne Yapar & Motor:** Shadcn UI tasarım dilini Remotion video dünyasına taşıyan, React tabanlı, 21 adet kopyala-yapıştır video bileşeni sunan açık kaynak kütüphanedir.
  - **Motor:** Remotion, React, Tailwind CSS v4, Lucide React, Shaders/WebGL.
  - **React / Remotion Sürümü:** **Remotion 4.0.542**, **React 19.2.4**. (Bizim Stüdyomuz Remotion 4.0.484, React 18.3.1 kullanmaktadır; Remotion API'si %100 örtüşmektedir).
- **(2) Bileşen ve Sahne Listesi (registry/snap-cn):**
  1. `answer-stream`: Buton tıklamasından ChatGPT tarzı kelime kelime sıcak akan AI yanıt akışı.
  2. `answer-highlight`: Yapay zeka yanıtı içinde imlecin cümlenin altını çizip kilit kelimeyi seçmesi.
  3. `agent-steps`: Yapay zeka ajanının adım adım görev günlüğü (dönen küre → yeşil tik, yukarı kayan aktif satır).
  4. `announce-title`: 4 çekimli kinetik tipografi ürün lansman introsu.
  5. `text-reveal`: 14 klasik hazır ayarlı harf/kelime maskeli metin girişi.
  6. `text-highlight`: Cümle içinde fosforlu kalem, alt çizgi, üstünü çizme veya ışıltı.
  7. `text-rewrite`: Daktilo ile yazılan metnin son kısmını silip yenisini yazma.
  8. `text-select`: Yazılan cümlenin üzerine seçim şeridi çekilmesi.
  9. `text-swap`: İki satırın eksenel dönüşle yer değiştirmesi (shared-axis).
  10. `text-swell`: Harflerin dalga halinde baseline'dan sıçrayarak şişmesi.
  11. `text-build`: Kelimeler eklendikçe merkeze doğru fiziksel olarak yeniden dizilen metin.
  12. `word-flip`: Cümledeki tek bir kelimenin 3D flip ile takla atarak değişmesi.
  13. `word-captions`: MrBeast / Hormozi stili dış konturlu kelime kelime zıplayan altyazı.
  14. `karaoke-captions`: Konuşuldukça dolan karaoke altyazı.
  15. `logo-drift`: Başlığın arkasında kameradan geriye doğru süzülen entegrasyon logo bulutu.
  16. `logo-assemble`: Dönen kartların merkeze çökerek logoyu doğurması.
  17. `logo-flicker`: Hızlı resim flaşlarının yavaşlayarak logoya oturması.
  18. `block-wordmark`: Renkli blokların harflere dönüşerek marka adını kurması.
  19. `phone-frame`: iPhone Dynamic Island'lı 3D eğimli telefon maketi.
  20. `laptop-frame`: Kapağı açılan ve kameranın ekrana daldığı MacBook maketi.
  21. `terminal-simulator`: Komut yazan, çıktı basan, adımlı kayan CLI terminal simülatörü.
  22. `screen-recording`: Ham ekran kaydını kenarlardan kırpıp ilgi noktasına otomatik zoom yapan kamera.
  23. `count-grid`: Kartlar çoğaldıkça sayacın fırladığı "ölçeklenme" istatistik sahnesi.
  24. `roster-grant`: Butona tıklandığında ekip avatarlarının sırayla aktifleştiği erişim onay sahnesi.
  25. `wordmark-cut`: Devasa marka adından sığ alan derinlikli yakın çekime sert kesim.
  26. `cursor-track`: Herhangi bir UI üzerinde yürüyen ve tıklama dalgası yayan macOS imleci.
  27. `pulsing-border`: Ekran kenarlarında yapay zekanın düşündüğünü gösteren nabız gibi atan ışıltılı kenarlık.
  28. `follower-rush`: Takipçi sayısının patlayıp avatarların dalgalandığı sosyal kanıt bildirimi.
- **(3) Bizim 102 Kaydımızda ve Hazır Efektlerde Karşılığı Olmayanlar:**
  - `ajan-gorev-adimlari` (agent-steps: spinner dönen, yeşil tike dönüp yukarı kayan AI agent terminal günlüğü).
  - `yapay-zeka-yanit-akisi` (answer-stream: sıcak kelimelerle akan AI cevap akışı ve seçim bandı).
  - `terminal-kod-simulasyonu` (terminal-simulator: komut, çıktı, kaydırma ve imleçli gerçekçi CLI).
  - `3b-kelime-taklasi` (word-flip: satır bozulmadan tek kelimenin 3D eksende takla atıp değişmesi).
  - `sosyal-kanit-takipci` (follower-rush: patlayan sayı sayacı ve dalgalanan avatar yığını).
  - `dizustu-dalis-cercevesi` (laptop-frame: kapağı açılıp ekrana doğru dalış yapan MacBook).
  - `logo-entegrasyon-bulutu` (logo-drift: geriye çekilen kamera ile sonsuz entegrasyon kutucukları).
  - `parlayan-ai-kenarlik` (pulsing-border: ekran kenarlarında parıldayan hesaplama ışığı).
- **(4) Bizimkinden İyi Kurallar (Dosya:Satır):**
  - `README.md:98-101`: **Metin Titremesi (Judder) Önleme:** Büyüyen/küçülen tipografide merkez yerine **baseline pivotu** kullanılması ve CSS'te `text-rendering: geometricPrecision` verilmesi. Sub-pixel rasterizasyonun her karede font köklerini yeniden hizalamasını engelleyerek titremeyi 0.284px'ten 0.014px'e düşürür.
  - `registry/snap-cn/registry.json:430`: **Headless WebGL Güvenliği:** Chromium headless ortamında shader'ların siyah kare vermemesi için `--gl=angle` / `Config.setChromiumOpenGlRenderer("angle")` parametresinin zorunlu tutulması.
  - `registry/snap-cn/registry.json:382`: **Roster Grant Asimetrisi:** Liste onaylanırken avatarların 7 karede bir rastgele satır sırasıyla (üst, orta, alt, üst...) aktifleşmesi; yapay simetriyi kırıp gerçek sistem onayı hissi yaratması.

---

### 2. Bizim Sözleşmeye Çevrilebilir En Değerli 12 Aday

Sözleşme şartlarımız: `library/motion/custom/<id>/` altında `<id>.html` + `meta.json`, saydam webm (`alpha: true`), `window.PARAM`, CSS değişkenleri (`--tema-vurgu`, `--tema-zemin`, vb.) ve sanal saat `window.seek(t)`.

1. **`ajan-adimlari`** (Kaynak: `snapcn/agent-steps`)
   - **Tür:** `lower-third` / `overlay`
   - **Tarif:** Yapay zekanın işlem yaptığı anlarda beliren; dönen mini küre indikatörle aktif adımı gösteren, tamamlanınca yeşil tike dönüştürüp tüm sütunu bir satır yukarı kaydıran minimalist görev akış kartı.
   - **Parametreler:** `{"adim1": "İçerik taranıyor...", "adim2": "Model çalıştırılıyor...", "sonuc": "Kurgu hazırlandı"}`

2. **`odometre-sayac`** (Kaynak: `product-launch-motion/references/technique.md:63-69`)
   - **Tür:** `overlay` / `lower-third`
   - **Tarif:** Rakamların basamak basamak mekanik bir sayaç gibi dikey yarıklarda yuvarlanarak aktığı, font sıçraması yapmayan pürüzsüz sayı sayacı.
   - **Parametreler:** `{"baslangic": 0, "hedef": 125000, "para_birimi": "₺", "etiket": "Görüntülenme"}`

3. **`terminal-kod-akisi`** (Kaynak: `snapcn/terminal-simulator`)
   - **Tür:** `overlay`
   - **Tarif:** macOS/Linux tarzı şeffaf pencerede komutun daktilo gibi yazıldığı, çıktının adım adım aktığı ve imlecin yanıp söndüğü gerçekçi komut satırı terminali.
   - **Parametreler:** `{"komut": "vedit final --hizli", "cikti": "Render tamamlandı: 60 fps", "baslik": "bash"}`

4. **`isik-demeti-baglanti`** (Kaynak: `claude-motion-design/skill/motion-design/SKILL.md:39`)
   - **Tür:** `overlay`
   - **Tarif:** İki arayüz kartı veya koordinat arasında SVG bezier eğrisi üzerinden akan parıltılı enerji/veri ışık çizgisi.
   - **Parametreler:** `{"kalinlik": 3, "renk": "vurgu", "yon": "ileri"}`

5. **`kart-kenar-isiltisi`** (Kaynak: `claude-motion-design/skill/motion-design/SKILL.md:39`)
   - **Tür:** `overlay`
   - **Tarif:** Bir kartın veya ekran görüntüsünün kenar çizgisi boyunca döngüsel olarak dolaşan ve köşeleri dönen parlak ışık huzmesi.
   - **Parametreler:** `{"sure": 2.0, "uzunluk_px": 90, "renk": "vurgu"}`

6. **`komut-arama-paleti`** (Kaynak: `product-launch-motion/references/technique.md:50-53`)
   - **Tür:** `overlay`
   - **Tarif:** ⌘K ile açılan modern arama kutusu; metin yazılır, sonuçlar elenerek aktif satır seçilir ve onaylanır.
   - **Parametreler:** `{"arama": "video dışa aktar", "sonuc1": "4K MP4", "sonuc2": "Instagram Reels 9:16"}`

7. **`3b-kelime-taklasi`** (Kaynak: `snapcn/word-flip`)
   - **Tür:** `lower-third`
   - **Tarif:** Cümlenin hizasını bozmadan, içindeki tek bir kilit kelimenin 3D eksende takla atarak zıt/yeni kelimeye dönüşmesi.
   - **Parametreler:** `{"onceki": "ZOR", "sonraki": "KOLAY", "cumle_basi": "Video kurgulamak artık ", "cumle_sonu": "."}`

8. **`metin-secim-seridi`** (Kaynak: `snapcn/answer-highlight`)
   - **Tür:** `overlay`
   - **Tarif:** Ekranda beliren bir cümlenin en önemli kısmının üzerinden fareyle taranırcasına renkli bir seçim bandının çekilmesi ve kelimenin vurgulanması.
   - **Parametreler:** `{"metin": "Yapay zeka tüm süreci otomatikleştirir.", "secilen": "tüm süreci otomatikleştirir"}`

9. **`lastikli-ayar-cubugu`** (Kaynak: `motion-graphics/skills/motion-broll/reference/engine-api.md:81`)
   - **Tür:** `lower-third` / `overlay`
   - **Tarif:** İmlecin tutup sağa çektiği, uç sınıra vurunca hafif gerilip esneyerek yerine oturan ve üzerindeki değeri güncelleyen lastik bantlı kaydırıcı.
   - **Parametreler:** `{"etiket": "Kalite", "deger": "%100", "min": 0, "max": 100}`

10. **`kart-yelpaze-acilis`** (Kaynak: `motion-video-kit/business-motion-film/references/motion-grammar.md:34`)
    - **Tür:** `overlay`
    - **Tarif:** Tek bir kartın arkasından 3 adet kartın yelpaze gibi dışa doğru açılarak seçenekleri veya özellikleri sergilemesi, ardından tekrar tek karta toplanması.
    - **Parametreler:** `{"kart1": "Hız", "kart2": "Kalite", "kart3": "Sıfır Maliyet"}`

11. **`parildayan-ai-kenarlik`** (Kaynak: `snapcn/pulsing-border`)
    - **Tür:** `overlay`
    - **Tarif:** Ekranın 4 kenarında yapay zekanın veri işlediğini ya da dinlediğini hissettiren, yumuşakça nefes alan gradyan ışık çerçevesi.
    - **Parametreler:** `{"hiz": 1.5, "kalinlik": 6, "renk": "vurgu"}`

12. **`sosyal-kanit-sayac-dalgasi`** (Kaynak: `snapcn/follower-rush`)
    - **Tür:** `lower-third` / `overlay`
    - **Tarif:** Takipçi, abone veya indirme sayısının hızla fırladığı ve yanındaki avatar dairelerinin dalgalanarak üst üste bindiği sosyal kanıt rozeti.
    - **Parametreler:** `{"sayi": "50.000+", "etiket": "Yeni Kullanıcı"}`

---

