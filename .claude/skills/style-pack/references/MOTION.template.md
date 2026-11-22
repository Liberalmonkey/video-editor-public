# MOTION — <paket adı>

> Kaynak: <referans videolar + zaman damgaları, references/style-grammar.md> · Onay: <tarih>
> Hareket kişiliği tek cümle: "<ör. kağıt kesik gibi kısa kaymalar, yumuşak duruş, ara sıra el yapımı titreşim>"

## 1. Ritim (referanstan ölçülen)
- Ortalama sahne süresi: <sn> · kesme/dk: <N> · pattern interrupt aralığı: <sn>
- Duraklama: önemli bilgiden sonra <sn> nefes; bölüm sonu <sn>

## 2. Anlam haritası (hareket = anlam)
| Anlam | Hareket | Süre | Easing (tokens.ease) |
|---|---|---|---|
| yeni bilgi girer | <ör. alttan 24px kayarak + opaklık> | 0.45 | text |
| vurgu | <ör. accent alt çizgi soldan çizilir> | 0.35 | ui |
| karşılaştırma | <ör. ekran ikiye bölünür> | 0.6 | camera |
| sayı / veri | <ör. sayaç, çubuk büyür> | 0.8–1.2 | ui |
| çıkış | <ör. hızlı solma, giriş süresinin yarısı> | 0.25 | exit |
| neden-sonuç | <ör. ok çizilir, kamera takip eder> | | |

## 3. Easing tablosu
- ui / text / camera / exit / logo / overshoot → tokens.json'daki değerler ve neden seçildikleri
- Asla: linear (yalnızca sürekli dönen/kayan arka plan), bounce (marka eğlenceli değilse)

## 4. Geçiş aileleri (videoda en fazla 2–3)
1. <ör. sert kesme — varsayılan>
2. <ör. kağıt yırtılma / wipe — bölüm geçişi>
3. <ör. kamera zoom-through — kavramdan detaya>

## 5. Kamera dili
- Ken Burns / punch-in oranı: <ör. %4–8, 3–6 sn>; hareket yönü kuralı
- Paralaks katman sayısı ve hız farkı

## 6. Kinetik tipografi
- Kelime / satır / harf bazlı giriş; stagger: <tokens.durations.stagger>
- Vurgu kelimesi davranışı (renk, ölçek, alt çizgi)

## 7. Ses-hareket senkronu
- Hangi hareket hangi SFX ile eşleşir (whoosh = büyük kayma, pop = öğe belirmesi, tick = madde)
- Müzik vuruşuna kilitlenen anlar: <bölüm geçişleri, reveal>

## Dersler
- <YYYY-MM-DD> <…>
