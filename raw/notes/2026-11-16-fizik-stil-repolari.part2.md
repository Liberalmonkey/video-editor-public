# 2026-11-16-fizik-stil-repolari (devam 2)

### A. Kütle, Çarpışma ve Kapalı-Form Hareket
1. **Ön Hazırlık (Anticipation) ve Hacim Korunumlu Squash-Stretch:** Zıplayan veya fırlayan nesne kalkıştan `0.10–0.12s` önce çömelir (`sq > 0`), serbest düşüşte $t^2$ ile ivmelenip hız vektörü yönünde uzar, çarpma anında hacmini koruyarak (`genişlik = 1 + 0.6*sq`, `yükseklik = 1 - sq`) ezilir ve sönümlü kosinüsle (`exp(-8a)*cos(20a)`) yaylanır.
2. **Çoklu Duyusal Çarpışma Kilidi ve Hit-Stop:** Çarpışma karesinde fiziksel darbe (impulse), toz/kıvılcım, kamera sarsıntısı ve ses efektinin tepe noktası aynı karede buluşur; yüksek enerjili yıkımlarda simülasyon 3–6 kare (`50–100 ms`) dondurulup (`hit-stop`) ardından parçalar fırlatılır.
3. **Sıralı Okuma (Sequential Reads) ve Ayrık Metin Zamanlaması:** "Sebep" ve "Tepki" asla aynı karede başlamaz (önce sebep okunur, sonra tepki başlar); şekil değiştiren bir kutuda eski metin tamamen çıkmadan yeni metin beliremez.
4. **İkizleme Yasağı (Anti-Twinning) ve İzole Tohumlama (`boilSeed`):** İki kol, iki göz veya kalabalıktaki öğeler aynı fazda hareket edemez. Hareketli bir öğenin tükettiği PRNG sayıları durağan arka planı titretmesin diye her bileşen `seed + hash(elementId)` ile kendi bağımsız rastgelelik akışını alır.
5. **Gecikmeli Takip (Follow-Through / `lagged`):** Tüm parçalar aynı karede durmaz; gözler önden gider, gövde takip eder, aksesuarlar/gölgeler `stateAt(frame - delayFrames)` veya `exp(-k*t)*sin(w*t)` ile 2–4 kare geriden gelerek yerleşir.
6. **Sürtünme, Kaldıraç ve Kaymasız Yuvarlanma:** Yuvarlanan tekerlek/bilyenin açısal hızı katettiği yay uzunluğuna kilitlidir ($\theta(t) = s(t)/r$); devrilen domino taşı ağırlık merkezi taban sınırını geçince ivmelenir ve en fazla $1.5\times$ boyuttaki komşusunu devirebilir.

### B. Araç, Süspansiyon ve Kamera Fiziği
7. **Kapalı-Form İvmelenme ve Hıza Bağlı Drift:** Oyun döngüsü (`vel += acc`) yerine kapalı-form hız eğrisi kullanılır; yüksek hızda sert dönüşte yanal tutunma düşer, araç burnunun baktığı yöne değil momentum vektörü yönüne kayar.
8. **Şasi Yük Transferi ve 2.5D Süspansiyon:** Kararsız `WheelCollider` yerine zemin yükseklik örneklemesi + sönümlü harmonik osilatör kullanılır; araç gazda geriye (`squat`), frende öne (`dive`), virajda dış tekerleklere (`roll`) yatar. Ön tekerlekte gimbal lock'u önlemek için dış grup direksiyonu (`rotY`), iç grup dönüşü (`rotX`) taşır.
9. **Kayma Açısı Eşikli Lastik İzi ve Duman:** Lastik izi ve duman sürekli çıkmaz; yalnız hız vektörü ile tekerlek açısı arasındaki kayma açısı (slip angle) eşiği aştığında üretilir.
10. **Öngörülü Kamera Takibi (`lookAhead`) ve Dinamik FOV:** Kamera hedefin o anki konumuna değil, $\text{pos} + \text{vel} \times \Delta t$ ilerisine yayla bakar; hız/boost arttıkça geriye çekilir (pull-back) ve imleç turlarında imleç kameradan 2f önce kalkıp 6f önce hedefe varır.

### C. Sıvı, Gaz ve Esnek UI Elemanları
11. **Asimetrik Yay (Tırtıl Uzaması):** Hareket eden sıvı damlası veya sekme göstergesinde (tab indicator) öncü kenar hızlı yayla önden uzar, artçı kenar daha yavaş yayla arkadan yetişir.
12. **Elastik Sınır Gerilmesi (Rubber-Banding):** Maksimum sınırın ötesine çekilen kaydırıcı veya sıvı sütunu logaritmik dirençle esner, bırakıldığında kapalı-form yayla yerine oturur.
13. **Isıl Boyun Kopması (Necking) ve Kıyı Köpüğü:** Isınan sıvı/lav yükselirken ortadan incelerek (necking) kopup küreselleşir; suyun katı cisimle kesiştiği sınırda beyaz köpük hattı ve dikey hız eşiği aşıldığında damlacık sıçraması oluşur.

### D. Işık, Gölge, Cam ve CSS Render Kuralları
14. **Mesafeye Bağlı Temas Gölgesi (Contact Shadow):** Nesne zeminden yükseldikçe (`dy` veya `translateZ`) gölgesi yerinde kalır ama küçülür/genişler, bulanıklaşır (`blur` artar) ve opaklığı azalır; değdiği anda keskin ve koyudur.
15. **Pigment vs. Toplamsal Işık (Additive Glow):** Parlayan nesneler boya gibi karıştırılmaz; ayrı `light` tamponunda veya `blendMode(ADD)` ile toplamsal ışık olarak uygulanır.
16. **Fresnel Yansıması ve Alçak Güneş Gölgesi:** Cam ve su dik bakışta şeffaftır, yatay (grazing) açıda ayna gibi yansıtır; alçak ışıkta (golden hour) zemindeki en küçük derz/oyuk bile ters yöne uzun gölge düşürür.
17. **Dinamik Çevre Işığı (1px Rim Light):** Karanlık sahnede parlak bir kaynak yandığında, yakınındaki karakterin o yöne bakan dış konturunda 1–2 piksellik tamamlayıcı kenar ışığı aynı karede parlar.
18. **`preserve-3d` Düzleşme Yasağı:** 3D dönen (`preserve-3d`) bir kartın doğrudan kendisine `opacity` veya `filter` verilmez (3D uzayı düzleştirir); solma işlemi her zaman dış sarmalayıcıya (wrapper) uygulanır.
19. **Ölçeklenen Öğede `will-change` Yasağı ve Çizgi Kalınlığı Dengesi:** Kameranın yakınlaştığı metin/vektör katmanına `will-change: transform` verilmez (bitmap bulanıklığı yapar); kamera `zoom` yaptıkça dünya koordinatındaki `stroke-width` lekeye dönüşmemesi için zoom ile ters orantılı inceltilir.

### E. Karakter, Konuşma ve Ses/Kurgu Senkronu
20. **Kaymasız Adım (Stance & Swing) ve Rölanti Nefesi:** Yürüyen karakterin yere basan ayağı (stance) zemine tam kilitlenir, asla kaymaz; dururken bile göğüs kafesi `PROJECT.bpm` nabzıyla (`pulse(t)`) hafifçe nefes alır.
21. **Kısık Göz Altında Duygu Geçişi:** Yüz ifadesi iki kare arasında aniden (snap) değişmez; değişimden `0.10s` önce gözler kısılır (`squint`), ifade kısık göz altında değişir ve `0.14s` içinde `take()` sıçramasıyla açılır.
22. **Frekans Merkezli Kare-Bazlı Viseme (`librosa`):** `hop_length = int(sr / fps)` ile her video karesi için `rms < 0.08` ise `kapalı`, `spectral_centroid < 1100 Hz` ise `O`, `> 2200 Hz` ise `E`, arası (`1100–2200 Hz`) ise `A` ağız şekli atanır.
23. **Konuşma-B-Roll Kilidi ve Dairesel PiP:** Görsel örnekler söylenen kavrama kilitlenir; tam ekran grafiğe geçildiğinde konuşmacı sağ altta altyazıyı kapatmayan dairesel pencereye (PiP) küçülür.
24. **Zamandan Türetilen Daktilo İmleci:** Eşzamanlı yazılan metinlerde harf sayısı $\lfloor \text{ilerleme} \times \text{uzunluk} \rfloor$ ile zamandan türetilir; imleç (caret) yazım sürerken sabit yanar, yalnız durduğunda yanıp söner.
25. **Dosya Başı Değil, Tepe Noktası (Transient Peak) Hizalaması:** Ses efektleri 0. saniyesinden değil, dalga formunun ölçülen gerçek tepe noktasından olayın gerçekleştiği kareye oturtulur.
26. **Uzaklık ve Yoğunluk Miksi:** Kamera uzaklaştıkça SFX seviyesi düşer; yüzlerce küçük çarpışma (bilye/karo yağmuru) tek tek üst üste bindirilip patlatılmaz, tek bir hışırtı/yağmur dokusuna yuvarlanır.
27. **Havada Boşluk (Drop Silence):** Nesne havadayken veya sert tema geçişinden hemen önce bas/davul bir anlığına kesilir, yere/başlığa çarptığı karede tüm gücüyle geri girer.
28. **Marka Kişiliğine Göre Easing ve Overshoot:** Fintech/Güven işlerinde overshoot `1.0` (`~21f`, sekmez); Lüks işlerde `≤1.02` (`~48f`); Enerjik/Oyun işlerinde overshoot `1.12` + squash `0.25` (`~18f`) uygulanır.
29. **Kusursuz Döngü Mührü (Loop Seam):** Loop videolarda ilk ve son kare arasında yalnız konum değil, hız vektörü (`velocity`), kamera açısı ve parçacık fazı da birebir aynı olmalıdır ($f(0) = f(T)$).
30. **Üç Seviyeli Görsel Denetim (`sheet` + `strip` + `crop`):** Kod sahnesi denetlenirken yalnız genel kontak sayfasına (`sheet`) bakılmaz; hızlı geçişler için ardışık kare şeridi (`strip`) ve el/ayak teması için dünya koordinatlı bölge kırpması (`--crop-at`) kontrol edilir.

---

## (8) Riskler ve İşaretlenen Çelişkiler

### İşaretlenen Çelişkiler (`[ÇELİŞKİ]`)
1. **`[ÇELİŞKİ]` Klonlanan Repo Sürümleri (React 19) vs. Proje Kilidi (React 18.3.1):**
   * `teknik` notunda incelenen yerel klonlar (`@react-three/postprocessing@3.2.2` ve `@react-three/rapier@2.2.0`) `peerDependencies` içinde **React 19** ve **`@react-three/fiber` v9** istemektedir. Oysa [studio/package.json](studio/package.json#L13-L21) `react: "18.3.1"` ve `remotion: "4.0.484"` kullanmaktadır. Klonların `HEAD` sürümleri doğrudan kurulamaz; `@react-three/fiber@8.18.0`, `@react-three/postprocessing@2.16.3` ve `@react-three/rapier@1.5.0` kurulmalıdır.
2. **`[ÇELİŞKİ]` `@dimforge/rapier3d-compat` İç Sürüm Uyuşmazlığı (`0.19.2` vs `0.12.0`/`0.14.0`):**
   * `teknik` notu doğrudan Node bake işlemi için `@dimforge/rapier3d-compat@0.19.2` önerirken, React 18 uyumlu `@react-three/rapier@1.5.0` paketi kendi içinde `0.12.0` / `0.14.0` sürümüne bağımlıdır. Çözüm: Fizik zaten Node/bake aşamasında koşturulacağı için `<Physics>` bileşenli `@react-three/rapier` hiç kurulmamalı, yalnızca `@dimforge/rapier3d-compat@0.19.2` doğrudan kullanılmalıdır.
3. **`[ÇELİŞKİ]` Fizik Motoru (Rapier WASM) vs. Durumsuz Kapalı-Form (`f(t)`) Yaklaşımı:**
   * `teknik` notu fizik için Rapier WASM simülasyonunu önerirken, `dil` (`ClaudeAnimationBase`) ve `stil` (`lemo-opuscar`) notları fizik motoru çarpıştırıcılarını ("ağır ve kararsız `WheelCollider`") reddedip tüm hareketlerin `t` zamanının kapalı-form fonksiyonu olarak yazılmasını şart koşar. Çözüm: Çoklu katı cisim çarpışmalarında (domino, bilye, yıkım) Rapier Bake; karakter, arayüz ve araç süspansiyonunda kapalı-form `f(t)` kullanılmalıdır.
4. **`[ÇELİŞKİ]` Hareket Bulanıklığı (Motion Blur) Yöntemleri:**
   * `teknik` notu `@remotion/motion-blur` (`<Trail>`), `dil` notu (`video-shotcraft`) CSS bulanıklığı / 3 katmanlı hayalet izi (`f-1.6, f-3.2, f-4.8`), `stil` notu (`lemo-opuscar`) ise CSS filtrelerini reddedip 240 Hz alt-kare (subframe) render + FFmpeg `tmix=frames=4` önermektedir. Alt-kare (`tmix`) yöntemi render süresini 4–8 kat uzatacağından hızlı taslak hattımızla (ADR 0019) çelişir; yalnız kısa 3D hero sahnelerde opsiyonel tutulmalıdır.
5. **`[ÇELİŞKİ]` CSS `zoom` vs. `transform: scale()` ve 2D vs. 3D Dönüş:**
   * `dil` notunda [PageCam.tsx](work/agy/2026-11-16-repolar/kaynak/video-shotcraft/assets/lib/PageCam.tsx#L42-L148) bulanıklığı önlemek için `transform: scale()` yerine CSS `zoom` şart koşarken, aynı repodaki 3D kamera reçeteleri `transform: scale()` + `perspective` kullanır. Benzer şekilde `ClaudeAnimationBase` "3D kutu döndürmek yasaktır, 5 anahtar çizim (`turn()`) kullanılır" derken, `video-shotcraft` ve `stil` notları yoğun 3D (`rotateX/Y/Z`) kullanır (El çizimi 2D karakterlerde `turn()`, UI/ürün kartlarında 2.5D `perspective` uygulanmalıdır).
6. **`[ÇELİŞKİ]` Dijital Glitch Efektleri vs. `motion-design` Klişe Yasakları:**
   * `pixelfx` kataloğundaki `scifi/glitch` (RGB split) ve `glitch-wipe` efektleri, projemizin `motion-design` kurallarındaki "ucuz dijital RGB kayması/AI şablonu" yasağıyla çelişir. Editoryal işlerde bunun yerine `baski_kayma` (Riso misregistration) tercih edilmelidir.
7. **`[ÇELİŞKİ]` `awesome-opus5-5-videos` ve `lemo-opuscar` Lisans Durumu:**
   * `awesome-opus5-5-videos` kök dizinde MIT lisanslı olsa da `README.md` tekil eserlerin telifini yazarlarına bırakmaktadır; `lemo-opuscar` ise uzakta MIT olmasına karşın yerel klonda bozuk/boş (`refs/heads/.invalid`) olduğundan yerel `LICENSE` dosyası mevcut değildir.

### Teknik ve Operasyonel Riskler
* **Headless Chromium Siyah Kare Riski:** `@remotion/three` içinde `<ThreeCanvas gl={{ preserveDrawingBuffer: true, alpha: true }}>` unutulursa veya `EffectComposer` ilk karede `useEffect` gecikmesiyle `renderPriority = 1` üzerinden boş tampon çizerse render siyah çıkar.
* **Paralel Render Titreme (Flicker) Riski:** `Noise` (`effectPass.time` sabitlenmezse), `ToneMapping` (`adaptive={true}` bırakılırsa) ve `DepthOfField` (`target` autoFocus kullanılırsa) paralel Remotion işçilerinde kareler arası parlaklık/doku sıçraması üretir.
* **WASM Bellek Sızıntısı (OOM):** `bakePhysics` sonunda `eventQueue.free()` ve `world.free()` çağrılmazsa her sahne yeniden hesaplandığında WASM doğrusal belleği şişer.
* **Windows `numba` / `llvmlite` Derleme ve Ses Kodek Riski:** Çok yeni Python sürümlerinde prebuilt `.whl` yoksa `pip` MSVC derleme hatası verir (`--only-binary=:all:` ve Python 3.11/3.12 kullanılmalı); `.m4a`/`.aac` girdilerinde `soundfile` yerine devreye giren `audioread` için `ffmpeg.exe`'nin `PATH` üzerinde bulunması şarttır.
* **Varlık Lisansı Sızıntısı Riski:** `pixelfx` içindeki `gallery/fonts` (*Patch Pixel*) veya `video-shotcraft` içindeki üçüncü parti ses dosyaları yanlışlıkla `library/` altına kopyalanırsa lisans ihlali oluşur.
