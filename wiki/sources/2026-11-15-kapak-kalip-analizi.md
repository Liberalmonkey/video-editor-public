---
type: source
title: "Kapak kalıp analizi: 138 referans kapakta düzen, yazı stili ve izlenme"
tags: [kapak, thumbnail, youtube, instagram, reels, kalip, antigravity]
created: 2026-11-15
updated: 2026-11-15
raw: "[[raw/notes/2026-11-15-kapak-kalip-analizi]]"
author: Antigravity alt ajanları (5 analiz + 1 birleştirme), Claude doğrulaması
sources: ["[[2026-11-09-kapak-arastirmasi]]"]
---

# Kapak kalıp analizi

Kullanıcının topladığı 22 ekran görüntüsündeki 138 kapak (114 YouTube, 24 Instagram) tek tek etiketlendi: kalıp, kapaktaki yazı, kelime sayısı, yazı konumu ve alanı, yazı tipi sınıfı, renk, özne alanı, ifade, ek öğe, görüntüde yazıyorsa izlenme. Ham tablolar [[raw/notes/2026-11-15-kapak-kalip-analizi]] içindedir.

Kanıt düzeyi: **gözlem** (tek kişinin seçtiği referans seti; rastgele örneklem değil). Etiketleme dil modeliyle yapıldı; Claude ilk ekran görüntüsünün altı satırını görüntüyle karşılaştırdı ve tuttu, kalanı örneklenmedi. Yüzde ve alan değerleri tahmindir.

## Özet
- YouTube'da tek bir baskın kalıp yok. En sık görülen `klasik` (özne bir yanda, 2-4 kelime karşı yanda) kapakların dörtte biridir; geri kalanı rozet, yazısız, alt bant, bölünmüş kare, dev yazı ve çoklu kart düzenlerine dağılır.
- Instagram'da 24 kapağın 22'si tek şablondur: üstte marka sözü, yüz ortada, iki yanda eğik simge kartı, altta iki satır başlık, ikinci satır kırmızı kutuda.
- Yazılı YouTube kapaklarında ortalama 3 kelime; Instagram seri kapaklarında 6.
- Yazı stili altı kümeye iner; en sık üçü kırmızı kutu, kalın siyah konturlu beyaz ve açık zeminde siyah yazı + renkli kutudur.

## Ana çıkarımlar

### YouTube kalıp sıklığı (114 kapak)
| Kalıp | Adet | Tipik kelime | Tipik yazı yeri |
|---|---:|---|---|
| klasik | 28 | 2-4 | sol ya da sağ üst |
| ekran-vitrin (özne + ekran kartı) | 17 | 3-5 | sol üst |
| yazısız | 13 | 0 | yok |
| rozet (köşede 1-2 kelime) | 9 | 1-2 | sağ üst |
| alt bant (altta dev söz) | 9 | 3-5 | alt |
| seri (yüz + iki kart) | 8 | 2-4 | üst |
| bölünmüş kare | 6 | 2-6 | üstte iki yanda |
| üst başlık | 6 | 1-3 | üst |
| dev yazı (özne arkasında) | 4 | 2-3 | üst |
| el yazısı not + ok | 2 | 1-3 | sağ üst |
| tekil kalıplar (kolaj, simge denklemi, beyaz tahta vb.) | 12 | 2-6 | değişken |

Alt ajanlar aynı düzeni farklı adlandırdı: bir ajanın `ekran-vitrin` dediği kapakları diğer ikisi `klasik` ya da `alt-bant` saydı. Sayılar bu yüzden kalıp sınırlarında kesin değildir.

### İzlenme (yalnız görüntüde sayı yazan kapaklar)
- Eğlence kanalı grubu (18 kapak, 75-340 milyon): yalnız üç kalıp kullanılmış: rozet (ortalama 165 milyon), bölünmüş kare (168 milyon), yazısız (127 milyon).
- Yapay zekâ ve eğitim grubu (96 kapak, 5 bin - 1,2 milyon): çok tekrar eden kalıplarda ortalama sırası alt bant (134 bin), dev yazı (131 bin), üst başlık (112 bin), seri (95 bin), klasik (68 bin), ekran-vitrin (36 bin).

> [!question] Çıkarım
> İzlenme farkı kalıbın etkisi olarak okunamaz: kanal büyüklüğü, konu ve yayın tarihi denetlenmedi, gruplar birkaç kanaldan oluşuyor. Bu veri "hangi kalıplar başarılı kanallarda kullanılıyor" sorusunu yanıtlar, "hangi kalıp izlenmeyi artırır" sorusunu yanıtlamaz.

### Yazı stili kümeleri (125 yazılı kapak)
| Stil | Adet |
|---|---:|
| Koyu zemin, beyaz yazı, kırmızı kutu ya da kırmızı söz | 31 |
| Gerçek sahne üstünde tek renk beyaz, kalın siyah kontur | 29 |
| Açık zemin, siyah yazı, renkli kutu ya da alt çizgi | 26 |
| Koyu zemin, beyaz yazı, sarı ya da turuncu vurgu | 21 |
| Beyaz yazı, son söz mavi ya da yeşil kutuda | 11 |
| El yazısı ya da serif not | 7 |

### İfade ve özne
- İfade çoğunlukla sakin, ciddi ya da hafif gülümseme; Instagram setinde abartılı şok ifadesi hiç yok.
- Özne karenin yaklaşık üçte biri ile yarısı arasında; rozet ve yazısız kalıpta %50-85.

### Web araştırması (alt ajan bildirimi)
Web ajanının verdiği bağlantıların çoğu arama yönlendirme adresidir ve açılıp doğrulanmadı; yalnız vidIQ'nun 500 videoluk çalışması doğrudan adres taşır ([vidIQ](https://vidiq.com/blog/post/youtube-thumbnail-study/)). O çalışmaya atfedilen bulgular: kapakların %72'si yazılı, en başarılı dilimde 0-3 kelime; abartılı şok ifadesi %5; özne karenin yaklaşık üçte biri, yazı karşı yanda. Bu maddeler referans setindeki gözlemle aynı yöndedir ama Claude kaynağı açıp okumadı.

## Projeye etkisi
- Şablona yedi yeni kalıp ve yedi yazı stili paketi eklendi; kapak yazısı altyazı standardından ayrıldı ([[0027-kapak-sayfasi]], 2026-11-15 notu).
- `ekran-vitrin` ve çoklu kart kalıpları alınmadı: ikinci bir görsel ister ve bu sette en düşük izlenme ortalamasını verdi.
- Ölçüm eşikleri buradan: YouTube'da en çok 5, Instagram'da en çok 7 kelime; harf yüksekliği karenin en az %8'i.
- Kişi yüzü, logo ve tasarım kopyalanmaz; yalnız düzen alınır ([[2026-11-09-kapak-arastirmasi]]).

## Çelişkiler/açık sorular
> [!warning] Çelişki
> Sadelik: web kaynakları görsel kalabalığın ve birden çok okun tıklamayı düşürdüğünü söyler; referans setinde 6-16 simgeli ve çift oklu kapaklar kendi kanallarında yüksek izlenme almış. İkisi de denetimsiz gözlemdir.

> [!warning] Çelişki
> Yazısız kapak: eğlence grubunda kapakların dörtte birinden fazlası yazısız; yapay zekâ ve eğitim grubunda neredeyse hiç yok. Kalıp seçimi nişe bağlıdır.

- Instagram setinde izlenme sayısı görünmüyor; seri şablonunun etkisi ölçülemedi.
- Projenin kendi kapaklarında hangi kalıbın çalıştığı ancak YouTube Test & Compare sonuçlarıyla öğrenilir; bu veri henüz toplanmıyor.

## Bağlantılar
- [[2026-11-09-kapak-arastirmasi]], [[0027-kapak-sayfasi]], [[0014-altyazi-standardi-ve-repo-entegrasyonu]]
