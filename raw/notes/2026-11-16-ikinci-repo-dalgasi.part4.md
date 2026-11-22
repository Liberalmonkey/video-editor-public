# 2026-11-16-ikinci-repo-dalgasi (devam 4)

#### 3. `motion-video-kit` (echris6 — MIT)
- **(1) Ne Yapar & Motor:** 28 profesyonel SaaS lansman filminden damıtılmış hareket grameri (16 mekanizma), bağımsız eleştirmen döngüsü (Gauntlet) ve Three.js destekli donanım/yazılım reklam üretim çerçevesidir.
  - **Motor:** HTML, GSAP, Three.js (opsiyonel), HyperFrames veya Playwright render.
  - **React / Remotion Sürümü:** Bağımsız (Pure HTML/JS veya HyperFrames).
- **(2) Bileşen ve Sahne Listesi:**
  - 16 Mekanizma (Mechanism Catalog):
    1. `Foreground fly-through`: Ön plan tipografisinin kamerayı delip geçerek alt sahneyi açması.
    2. `Logo-as-portal`: Marka logosunun büyüyüp içindeki boşluğun sonraki sahneye dönüşmesi.
    3. `Selection → expansion`: Seçilen kartın tüm çalışma alanına genişlemesi.
    4. `Materializing result`: Önce iskeletin belirmesi, ardından iç bölgelerin sırayla dolması.
    5. `Persistent rails`: Metin değişirken iki durumu bağlayan sabit hatlar/raylar.
    6. `Continuous canvas`: Kameranın geniş bir düzlemde kayması, odak dışındakilerin bulanıklaşması.
    7. `Artifact ring`: Merkezi sabit cümlenin etrafında dönen küçük kartlar halkası.
    8. `Card stack / fan`: Kart destesinin yelpaze gibi açılıp tek karta toplanması.
    9. `Perspective fold`: Panelin ışıklı bir çizgiye katlanması, sonraki panelin oradan yükselmesi.
    10. `Exploded layers`: Ürünün 3D fiziksel katmanlarına ayrılıp birleşmesi.
    11. `Registered decomposition`: Ana varlık sabitken bölgelerinin kategorilere ayrılması.
    12. `Wall → one actor`: Bilgi karmaşası/kart duvarının tek bir net nesneye çökmesi.
    13. `Carousel emphasis`: Dönen listede aktif öğenin parlaması, komşuların kararması.
    14. `Colour-field takeover`: Yumuşak gradyan bulutunun ekranı kaplayarak marka aktarımı yapması.
    15. `Tile wipe`: Bölüm ayracı olarak ızgara karo silmesi.
    16. `Request → picker → confirmation`: Mesaj balonu sabitken alttan sayfa yükselmesi, seçim ve onay.
  - `projected-overlays.js`: 3D Three.js koordinatlarını 2D ekran etiketlerine izdüşüren şablon.
- **(3) Bizim 102 Kaydımızda ve Hazır Efektlerde Karşılığı Olmayanlar:**
  - `kart-yelpaze-deste` (Card stack / fan: kartların desteden yelpaze gibi açılıp tek karta kapanması).
  - `katman-patlatma` (Exploded layers: ürün veya UI'ın 3D katmanlarına ayrılıp geri oturması).
  - `perspektif-katlanma` (Perspective fold: panelin parlayan 1px çizgiye katlanıp yeni panel açması).
  - `halka-yuruyen-kartlar` (Artifact ring: merkez metin etrafında yörüngede dönen mini kartlar).
  - `iskelet-dolus` (Materializing result / skeleton loader: kabuk çizilip iç blokların kademeli dolması).
  - `portal-gecis` (Logo-as-portal: logonun içi kamerayı yutarak sonraki sahneyi başlatır).
- **(4) Bizimkinden İyi Kurallar (Dosya:Satır):**
  - `business-motion-film/references/motion-grammar.md:16`: **Kadro Doluluk Oranı:** Ana nesne özellik anlarında ekranın **%60–85'ini** doldurmalıdır; boş alan izleyiciye ucuz görünür.
  - `business-motion-film/references/motion-grammar.md:46-48`: **Tempo ve Açılış:** Kare 0 kesinlikle bitmiş bir kompozisyonla açılmalıdır (yarım girmiş kelime yasak); durağanlık 0.6 sn'yi aşamaz; metin okuma anında bile %3–5 mikro kamera itişi sahneyi canlı tutmalıdır.
  - `business-motion-film/references/motion-grammar.md:20-21`: **Nesne Devir Teslimi (Hand-off):** Sahne geçişinde taşınan nesne hedef sahnedeki tam piksel koordinatlarına teslim edilmelidir; çıkan başlık silmeden önce kaybolmalı, giren başlık silmeden sonra belirmelidir.
  - `business-motion-film/references/gauntlet.md`: **"Builder ≠ Judge" Ayrımı:** Kurguyu kodlayan ajan ile görsel denetimi yapan ajanın ayrılması, render edilmiş kontak sayfası üzerinden kör okuma yapılması.

---

#### 4. `motion-graphics` (Barty-Bart — MIT)
- **(1) Ne Yapar & Motor:** Konuşan kafa (talking-head) videoları için transkript kelimelerine tam kilitli B-roll hareketli grafikler, şeffaf yan paneller ve dinamik ürün demoları üreten araç kitidir.
  - **Motor:** Saf HTML5 / CSS, `motion.js` motoru (`M.scene`, `M.track`, `M.vis`, kapalı form yaylar), Playwright ve ffmpeg.
  - **React / Remotion Sürümü:** Yok (Saf JS).
- **(2) Bileşen ve Sahne Listesi:**
  - `primary action`: Etiket hapı + tıklama (pill + click).
  - `progress`: Dolum çubuğu, şeritler (loader, bars, lanes).
  - `confirmation`: Onay tiki, toast bildirimi.
  - `live status`: Dynamic island / canlı durum hapı.
  - `detail card with a drag`: Sürüklenen detay kartı.
  - `slider with rubber band`: Lastik bant dirençli kaydırıcı.
  - `toggle`: Açma/kapama anahtarı.
  - `tabs`: Sekme çubuğu.
  - `chart with tooltip`: Gezinen araç ipuçlu çizgi/çubuk grafik.
  - `search and filter list`: Arama ve süzülen sonuç listesi.
  - `file -> drag -> drop target`: Dosya sürükle-bırak hedefi.
  - `terminal typing`: Komut satırı yazımı ve imleç.
  - `side-by-side comparison`: Yan yana karşılaştırma kartları.
  - `chapter card`: Bölüm başlığı kartı.
  - `liquid indicator`: İki kenarı bağımsız akan sıvımsı çubuk.
  - `transparent panel`: `bg: null` ile konuşmacının yanındaki boşluğa oturan saydam panel.
- **(3) Bizim 102 Kaydımızda ve Hazır Efektlerde Karşılığı Olmayanlar:**
  - `surukle-birak-hedef` (File drag & drop target: dosyanın sürüklenip bırakılması ve onaylanması).
  - `arama-filtre-listesi` (Search & filter list: arama kutusuna yazıldıkça elenen liste satırları).
  - `grafige-arac-ipucu` (Chart with animated tooltip: grafikte gezinen nokta ve açılan veri kartı).
  - `karsilastirma-kartlari` (Side-by-side comparison: eski/yeni veya A/B karşılaştırma paneli).
  - `lastikli-kaydirici` (Slider with rubber-band: sınırda gerilip bırakan elastik sürükleme çubuğu).
  - `canli-durum-adasi` (Live status island: hapın genişleyip bildirim gösterip büzülmesi).
- **(4) Bizimkinden İyi Kurallar (Dosya:Satır):**
  - `skills/motion-broll/SKILL.md:66-77`: **Kadraj Paylaşım Disiplini:** Konuşan kafada 3 net muamele:
    1. Tam ekran cutaway (3–10 sn, duygusal anda veya ilk 1 sn'de asla kesilmez, iki cutaway arasında en az 2 sn yüz kalır).
    2. Saydam boşluk paneli (`bg:null`, konuşmacı kutusuna değmeyen alanda 15 sn+ kesintisiz morfoloji).
    3. Hiçbir şey (kişisel/fikir anlarında grafik sokulmaz).
  - `skills/motion-broll/reference/engine-api.md:40`: **Dünya-Ekran Koordinat Ayrımı:** Şekil dünya (0,0)'da durur, kamera `center + cam * (world - focus)` ile çizer; kartlar için `cam: 1.2-1.6`, haplar için `cam: 1.8-2.2` seçilerek nesnenin çerçeveyi otomatik doldurması sağlanır.
  - `skills/motion-broll/SKILL.md:82`: **Konuşma Ritmi:** Müzik yerine konuşma ritmine kilitlenme: Spoken beat başına 0.4–1.2 sn aralıkla tek bir değişiklik; kelimeden önce değil kelimeyle tam senkron.

---

#### 5. `saas-motion-kit` (tugrawork-creator — MIT)
- **(1) Ne Yapar & Motor:** HyperFrames ve Claude Code ile yazılım ürünleri için 101 görsel tema, 24 anlatısal geçiş atlası ve tekrarları önleyen çeşitlilik denetimi (variety audit) içeren komple promo stüdyosudur.
  - **Motor:** HyperFrames (HTML + GSAP + Three.js), CSS, Playwright.
  - **React / Remotion Sürümü:** Remotion yok; HyperFrames 0.8.x uyumlu.
- **(2) Bileşen ve Sahne Listesi:**
  - 101 Görsel Tema (11 Aile: Product UI, Tipografi, 3D/Malzeme, Işık/Doku, Metafor, Veri Hikayeciliği, Maskot, Sanat Akımları, Kamera/Kurgu, Donanım Reklamı vb.).
  - 24 Anlatısal Geçiş Atlası: Match cuts, Carries (kelime taşıma), Camera moves (whip, dolly), Mask wipes (harf/çizgi maskesi), Material transitions (cam/döküm), Time shifts.
  - Bileşenler:
    - `Metric stave` (Nota çizgisi üzerinde vuruşla yükselen metrikler).
    - `Rollback rolling pin` (Oklava gibi yuvarlanarak eski sürüme dönen UI).
    - `Fineliner seismograph` (Çizim yapan sismograf iğnesi).
    - `Bento grid` (Theme 055: modüler bento kutusu hücrelerinin sırayla canlanması).
    - `Noise cancelling wave` (Theme 101: 38 çizgi dalganın tek bir sinyale susması / sessizlik anı).
    - `Over-the-shoulder dive` (Kullanıcının omzundan ekrana ve 3D arayüze dalış).
    - `Turntable 3D booth` (3D stant üzerinde dönen ürün kartları).
- **(3) Bizim 102 Kaydımızda ve Hazır Efektlerde Karşılığı Olmayanlar:**
  - `bento-kutu-akisi` (Bento grid: modern bento kartlarının kademeli uyanışı).
  - `kelime-tasima-gecisi` (Word-carry transition: bir cümledeki kilit kelimenin sonraki sahneye başlık olarak uçması).
  - `ses-dalgasi-susturma` (Noise cancelling waveform: gürültülü dalgaların ürünle düz çizgiye/sessizliğe inmesi).
  - `metrik-porte-notalari` (Metric stave: nota portesi üzerinde veri noktalarının vuruşla yükselmesi).
  - `harf-maskeli-silme` (Letter-mask wipe: dev bir harfin içi açılarak sonraki sahneyi ortaya çıkarması).
- **(4) Bizimkinden İyi Kurallar (Dosya:Satır):**
  - `README.md:159`: **4K Render, Küçülterek Teslim (Super-sampling):** `landscape-4k` render alıp Lanczos ile 1080p'ye küçültmek; 1080p native render'a kıyasla metin kenarlarını ve ince 1px çizgileri jaggies olmadan jilet gibi yapar.
  - `README.md:162-163`: **Türkçe Büyük Harf Kuralı:** CSS `text-transform: uppercase` Türkçede "i" harfini hatalı dönüştürebilir; bu yüzden metin doğrudan büyük harf yazılmalı ve her kelimeye `lang="tr"` verilmelidir.
  - `README.md:164`: **Ses Tınısı:** Saf sinüs bip sesleri ince ve tekinsiz durur; aynı tonda akortlanmış sıcak tınılar (marimba, ahşap blok, kısa oda yankısı) kullanılmalıdır (`warm_sfx.py`).
  - `creative/variety-rules.md`: **Çeşitlilik Denetimi (Variety Audit):** Bir storyboard'da aynı geçişin, aynı easing'in veya aynı giriş yönünün 3 kez üst üste tekrarlanmasını engelleyen kural motoru.

---

