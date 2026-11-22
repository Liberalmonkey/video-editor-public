# Pano kataloğu

267 HTML pano `boards/` altında. Kaynak: YouTube-AI-Video-Editing-System ve YouTube-AI-Motion-Graphics (MIT, `LICENSE`). Aşağıdaki 74 pano "şunu derken" etiketiyle eşlenmiştir: transkriptteki cümleye en yakın etiketi bul. Kalan 193 pano `catalog.json` başlıklarıyla aranır.

Kullanım: `vedit pano library/boards/boards/D44Line.html --sure 8 -o <çıktı>.mp4`. Görünüm `theme.css` ya da `--css` ile stüdyo stiline çekilir; hareket korunur. Oynatıcı: `python -m http.server 5331 --directory library/boards`.

## Diyagramlar

| Pano | Ne | Şunu derken |
|---|---|---|
| D43Bars | Çubuk grafik | miktar karşılaştırırken, "bu çok daha büyük" |
| D44Line | Çizgi grafik | "yükseldi", "zamanla", büyüme |
| D45Numbers | Pay ve büyük sayı | "yüzde X", tek büyük sayı |
| D46Pyramid | Piramit | "hepsi bunun üstüne kurulu", temel |
| D47Cycle | Döngü | "döngü", "tekrar tekrar", geri bildirim |
| D48Funnel | Huni | "bunların içinden yalnız", daralma |
| D49Timeline | Zaman çizelgesi | "önce… sonra… 2024'te", tarihçe |
| D50Venn | Venn | "kesiştiği yer", "ikisi de" |
| D51Matrix | 2×2 matris | "ödünleşim", "hızlı ama pahalı" |
| D52Tree | Ağaç | "şunlardan oluşuyor", "şuna ayrılıyor" |
| D53Steps | Numaralı adımlar | "birinci adım, ikinci adım", nasıl yapılır |
| D54Terminal | Terminal | "şu komutu çalıştır", "şunu yaz" |
| D56Chapter | Bölüm ayracı | büyük bölümler arası 2–3 sn |
| D57Quote | Kinetik alıntı | akılda kalması gereken tek cümle |
| Y165Devices | Cihaz bağlantıları | "şuna bağlı", "şununla konuşuyor" |

## Grafikler

| Pano | Ne | Şunu derken |
|---|---|---|
| C108Waterfall | Şelale | "toplamı şu ediyor", "maliyet nereye gidiyor" |
| C109Stacked | Yığılmış çubuk | "toplam şunlardan oluşuyor" |
| C110Grouped | Gruplu çubuk | "fiyat, hız ve kalitede karşılaştırınca" |
| C111Slope | Eğim grafiği | "önce ve sonra", "X'ten Y'ye çıktı" |
| C112Scatter | Nokta grafiği | "ucuz ama yavaş", iki özellik birden |
| C113KPI | KPI satırı | "rakamlar", yıldız, izlenme, üye; hepsi önemliyse |
| C114Ranking | Sıralama tablosu | "en iyisi şu", araç sıralaması |
| C115Gauge | Gösterge | "ne kadar riskli", ölçekte puan |
| C116Heatmap | Isı haritası | "her gün", zaman içinde etkinlik |
| Y163Share | Pay bölüşümü | "ne kadarı X, ne kadarı Y" |

## Bileşen hareketi

| Pano | Ne | Şunu derken |
|---|---|---|
| C239PriceCard | Fiyat kartı | "şu kadar tutuyor", fiyat |
| C240TableFocus | Tablo + satır odağı | "cevap da bu satır" |
| C241ChartFocus | Grafik + çubuk odağı | "şu çubuğa bakın" |
| C242AppFocus | Uygulama + alan odağı | "uygulamada buraya tıkla" |
| C243CodeFocus | Kod + satır odağı | "bu satır şunu yapıyor" |
| C244Receipt | Fiş çıkışı | "fatura", "ödediğin" |
| C245NodeGraph | Düğüm ağı, akış | "veri buradan akıyor" |
| C246Phone | Telefon + bildirim | "telefonunda", bildirim |
| C247ChipFilter | Etiket süzme | "bunca seçenek içinden" |
| C248KPIFocus | KPI + odak | "önemli olan sayı bu" |
| C249VersusCards | Karşılaştırma + kazanan | "X mi Y mi, kazanan şu" |
| C251FolderTree | Klasör açılışı | "şu klasörü aç" |
| C252Lens | Büyüteç | "yakından bakınca", tek değer |
| C254DealPull | Desteden çekme | "yığının içinden birini seç" |

## İleri hareket

| Pano | Ne | Şunu derken |
|---|---|---|
| P36Focus | Odak kaydırma | "önce bu, sonra bu", liste gezme |
| P37Keyframes | Anahtar kare | "buradan şuraya gidiyor" |
| P196Kinetic | Kinetik yazı | sayılı vurucu cümle |
| P197MaskReveal | Maskeli satır | iddia başlığı |
| P198Odometer | Sayaç | sonuç sayısı |
| P199Scramble | Karışıp çözülme | isim beliriyor: skill, dosya, komut |
| P200LineDraw | Çizgi çizme | "buradan oraya" |
| P209Flip | Kart çevirme | "önce / sonra", soru ve cevap |
| P211Fan | Deste açılması | "bunlardan N tane var", sürümler |
| P217Cable | Canlı kablo | "bağlı", hareket ederken bağlı kalır |
| P218Loader | Yükleme → bitti | "çalışıyor… ve bitti" |
| P219Chat | Sohbet | "ona sordum", ajanla konuşma |
| P220LetterWave | Harf dalgası | vurgulanan tek kelime |
| P221Confetti | Konfeti | "işe yaradı", kazanım |
| P226LiquidFill | Sıvı dolumu | "doluyor", ilerleme, kapasite |
| P227ScribbleFill | Karalama dolgu | "boyayalım" |
| P228CrossOut | Üstünü çiz, yeniden yaz | "bu değil, şu", eski yol → yeni yol |
| P230WordSlot | Dönen kelime | "X yapıyor, Y yapıyor, Z yapıyor" |
| P236Checklist | Kontrol listesi | "tamam, tamam, sıradaki" |
| P237Highlighter | Fosforlu kalem | önemli iki ifade |

## İş akışı ve kod

| Pano | Ne | Şunu derken |
|---|---|---|
| W69Nodes | Düğüm ağı, adım çıktıları | "iş akışı", sistem olarak hat |
| Y175Render | Render hattı | "kod videoya nasıl dönüşüyor" |
| Y182SystemMap | Raydaki adımlar | "tüm süreç N adımda" |
| A136FileAnatomy | Dosya anatomisi | "skill dosyası", "prompt dosyası" |
| A137FolderTree | Klasör haritası | "nerede bulurum" |
| A138Diff | Fark görünümü | "şunu buna çevir" |
| A139ErrorFix | Hata → çözüm | "bozuldu, çözümü şu" |
| A141Decision | Karar akışı | "hangisini seçeyim" |
| B134Request | İstek → yanıt | "API nedir", istek ve yanıt |

## Hikâye ve karşılaştırma

| Pano | Ne | Şunu derken |
|---|---|---|
| H143Agenda | Gündem | "neler konuşacağız", bölümler |
| H144MythFact | Efsane / gerçek | "herkes sanıyor ki… ama" |
| H145Recap | Akılda kalacak 3 şey | "aklınızda üç şey kalsın" |
| Y164Versus | Karşılaştırma defteri | "birçok açıdan X ve Y" |
| K123Scorecard | Karne | "hangisini kullanmalıyım", üç ve üstü seçenek |
| X41EndLayout | Bitiş ekranı | kapanış |

Aynı işi yapanlar: tek sayı önemliyse `C248KPIFocus`, hepsi önemliyse `C113KPI`. Veri akıyorsa `C245NodeGraph`, her adımın çıktısı varsa `W69Nodes`. Tek klasör açılıyorsa `C251FolderTree`, tüm harita için `A137FolderTree`. İki seçenek + kazanan `C249VersusCards`, iki seçenek + çok ölçüt `Y164Versus`.

Kurallar: pano başına tek iddia; okunur yazı 1080p'de en az 28 px; uydurma sayı yok, eksik varlık kesik çizgili "bekliyor" kartı; `library/checks.md` her render öncesi okunur.
