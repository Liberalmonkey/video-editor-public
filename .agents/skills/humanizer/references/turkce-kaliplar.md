# Türkçe AI-yazı kalıpları ve video senaryosu modu

> Bu ek, blader/humanizer (MIT) için proje uzantısıdır. SKILL.md "kalıp her dilde aynıdır, eşdeğer yapıya aynı muameleyi yap" der. Aşağıdakiler Türkçe eşdeğerlerdir.

## Senaryo modu (seslendirme metni)
- **D grubu (biçim, §19–21) KAPALI.** Senaryo okunmak için değil, söylenmek için yazılır. Kalın, başlık ve emoji zaten seslendirmeye girmez.
- **A, B, C, E grupları AÇIK.**
- **Ek kural, kulak testi:** her cümle tek nefeste rahat söylenebilmeli. Yaklaşık 18 kelimeyi geçen cümleyi böl.
- **Ek kural, konuşma dili:** "-mektedir / -maktadır" yazı dilidir, seslendirmede "-iyor" kullanılır. "Bu durum…" yerine somut özne yazılır.
- Sayılar seslendirmede nasıl okunacaksa öyle yazılır ("%40" → "yüzde kırk", "2026" → "iki bin yirmi altı"), ama ekran metni (blok props) rakamla kalır.
- Rakip, iddia, istatistik gibi gerçekler değiştirilmez. Eksik bilgi uydurulmaz; `[KAYNAK?]` işaretiyle bırakılır.

## Türkçe kalıplar (görünce düzelt)

### A — Söylemek yerine sahnelemek
| Kalıp | Örnek | Düzeltme yönü |
|---|---|---|
| "X değil, Y" karşıtlığı (sadece ağırlık katmak için) | "Bu bir ürün değil, bir yaşam tarzı." | Doğrudan Y'yi somutla: "Sabah kahveni 10 saniyede öğütüyor." |
| "Sadece X değil, aynı zamanda Y" | "Sadece hızlı değil, aynı zamanda sessiz." | "Hızlı ve sessiz: 10 saniye, 50 dB." |
| Tek satırlık dramatik kapanış | "Ve her şey değişti." / "İşte fark bu." | Değişen şeyi söyle ya da cümleyi sil. |
| Sahnelenmiş giriş | "Şimdi size bir sır vereceğim." / "İşin aslı şu:" / "Peki ya size … desem?" | Sırrı direkt söyle. |
| Derin görünen özdeyiş | "Çünkü bazen en büyük adım, en küçük olanıdır." | Sil. |
| Hayali karşı tarafla tartışma | "Biliyorum, şimdi 'ama…' diyorsunuz." | Gerçek itirazsa veriyle cevapla, değilse sil. |

### B — Kuralla ritim
- Zorlama üçlüler: "hızlı, kolay ve etkili". Gerçekten üç şey yoksa ikiye ya da bire indir.
- Her cümlenin aynı kalıpla başlaması: "Bu…, Bu…, Bu…" ya da "Peki…, Peki…".
- Uzun tire (—) yağmuru: Türkçede doğal değil. Virgül, nokta ya da iki nokta kullan.
- Yığılmış niteleyiciler: "gerçekten inanılmaz derecede etkileyici".

### C — Şişirme
- **Kalıp AI kelimeleri (TR):** eşsiz, büyüleyici, devrim niteliğinde, oyunun kurallarını değiştiren, bir sonraki seviyeye taşımak, yolculuk (mecaz), derinlemesine dalmak, keşfetmek (her şeyi), kilidini açmak, sorunsuz, kusursuz, vazgeçilmez, mihenk taşı, harika bir şekilde, tam anlamıyla.
- **Şişirilmiş önem:** "hayatınızı tamamen değiştirecek", "tarihî bir an".
- **Ödünç otorite:** "uzmanlar diyor ki", "araştırmalar gösteriyor ki" (kaynak yoksa).
- **Satış dili (UGC'de dahi):** "kaçırmayın!", "muhteşem fırsat". UGC samimi tavsiye gibi duyulmalı, reklam metni gibi değil. Tek CTA yeterli.
- "-dır/-dir" ile biten resmî tanımlar ("Bu cihaz, … sağlayan bir çözümdür.").

### E — Sohbet artıkları
- "Harika bir soru!", "Umarım faydalı olmuştur.", "Gelin birlikte bakalım", "Hadi başlayalım!" (hook'tan önce), "Bu videoda size … anlatacağım" (hook yerine).
- "Şunu unutmayın:" / "Özetle," / "Kısacası," / "Sonuç olarak,": gerekmiyorsa sil.

## Kendi sesine uyum
Kullanıcı 2–3 paragraf kendi metnini ya da eski bir video transkriptini verirse, `script/voice-sample.md` dosyasına koy. Polisher, cümle uzunluğu, hitap (sen/siz), argo ve espri dozu için bu örneğe göre ayar yapar.
