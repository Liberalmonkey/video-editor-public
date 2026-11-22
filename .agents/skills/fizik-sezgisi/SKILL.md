---
name: fizik-sezgisi
description: Kurguda ve animasyonda söylenmeden uygulanacak fizik, ışık, ses ve senkron kuralları — düşen, yuvarlanan, çarpan, hızlanan nesne; ışık yönü ve gölge; çarpma sesi ve kamera sarsıntısının aynı karede olması; karakter konuşurken ağız ve ses uyumu. Senaryoda ya da görüntüde hareket, çarpma, hız, ışık, karanlık, parlama, karakter konuşması geçtiğinde, fizik sahnesi (`sahne.kind: "fizik"`) seçerken, "gerçekçi değil", "ses kaymış", "dudak oynamıyor", "havada duruyor" dendiğinde kullan. usta-editor ve sound-design ile birlikte çalışır.
---

# Fizik sezgisi

İzleyici fiziği hesaplamaz ama yanlışını hemen hisseder. Düşen top yavaşlıyorsa, çarpma sesi bir kare geç geliyorsa, gölge ışığın tersine düşüyorsa video "yapay" görünür ve izleyici nedenini söyleyemeden gider. Bu skill kullanıcı istemeden uygulanır. Kaynaklar ve gerekçe: `wiki/decisions/0039-fizik-ritim-galeri.md`.

## Önce ölç, sonra yerleştir
| Ölçüm | Nereden | Ne için |
|---|---|---|
| Ses vurgu anları, beat, tempo | `work/edit/ritim.json` (`vedit ritim`) | Kesim, punch, grafik girişi ve olay sesi bu anlara oturur |
| Ses ile görüntü kayması | `vedit senkron <proje>` | Flow/Veo klibinde ses birkaç kare kayıksa önce düzeltilir (`--uygula`) |
| Fizik teması | Fizik sahnesinin bake dosyası | Çarpma sesi kendiliğinden gelir; elle olay yazılmaz |
| Ağız şekli | `work/edit/viseme.json` (`vedit viseme`) | Kodla çizilen karakter konuşurken ağız sesle açılır |

Ölçülmemiş ana "yaklaşık" ses ya da grafik konmaz. Bir kare 30 fps'de 33 ms'dir; göz 2 karelik kaymayı fark eder.

## Fizik sahnesi ne zaman
Anlatıda gerçek bir fiziksel olay varsa (düşme, sekme, yuvarlanma, ivme, sarkaç, atış, zincirleme devrilme, çöküş) elle animasyon yerine fizik sahnesi kullanılır: `sahne.kind: "fizik"`, preset kataloğu `studio/remotion/fizik/presetler.json`. Simülasyon gerçek yerçekimiyle koşar; hız, sekme ve temas anı kendiliğinden doğrudur. Mecaz da sayılır: "domino etkisi" domino, "her şey çöktü" kule çöküşü, "gaza bastık" araba ivmesi.
- Sahne anlattığı cümleyle başlar; olayın en güçlü anı (ilk çarpma, en yüksek hız) cümlenin vurgulu kelimesine denk gelir. Gerekirse `param` (yükseklik, ivme) ile zamanı oynat; sahneyi kesip zorla hizalama.
- `param.etiket` kısa kalır: kavram ya da formül ("v = a·t"). Ölçüm göstergesi (`olcum: true`) bilgi videosunda açık, duygusal anlatıda kapalı.
- Işık presetini içeriğe göre seç (`presetler.json` > `isik`): bilgi için `studyo` ya da `laboratuvar`, açık hava ve araç için `gun-isigi`, dram için `sinematik`, teknoloji için `neon`, kapanış için `gun-batimi`. Bir videoda en çok iki ışık dili.

## Değişmez kurallar (kısa)
1. **Yerçekimi hızlandırır.** Düşen nesne ease-in ile iner (t² ile), yavaşlayarak değil. Yukarı atılan yavaşlayarak çıkar, tepede bir an durur.
2. **Sekme enerji kaybeder.** Her sekme bir öncekinden alçak ve kısadır; ses de her sekmede kısılır.
3. **Yuvarlanan dönme yola kilitlidir.** Dönme açısı = gidilen yol / yarıçap. Kayan tekerlek ya da yerinde dönen top yanlıştır.
4. **Hızlanma ritimle anlatılır.** İvmelenen sahnede kesimler sıklaşır, hız izi (motion blur) artar, kamera hedefin biraz gerisinden gelir.
5. **Temas tek karede buluşur.** Görüntüde temas, ses efektinin tepesi, kamera sarsıntısı ve varsa parçacık aynı karede başlar. Ses görüntüden önce gelmez.
6. **Önce sebep, sonra tepki.** Sebep ile tepki aynı karede başlamaz; tepki 2-4 kare sonra gelir (follow-through).
7. **Işığın tek yönü vardır.** Bir sahnedeki bütün gölgeler aynı yöne düşer. Parlayan nesne çevresine ışık verir; karanlık sahnede yanan ışık yakındaki kenarı aydınlatır.
8. **Gölge mesafeyi söyler.** Yükselen nesnenin gölgesi yerinde kalır, büyür, solar; değdiği anda keskin ve koyudur.
9. **Uzaklık sesi kısar.** Kameradan uzak olay daha alçak ve daha yumuşak duyulur. Yüzlerce küçük çarpışma tek tek değil, tek doku olarak duyulur.
10. **Havada sessizlik.** Büyük düşüşte ya da sert çarpmadan hemen önce müzik bir an çekilir, temas karesinde geri girer.
11. **Konuşan ağız açıktır.** Karakter konuşurken ağız sesin enerjisiyle açılıp kapanır; sessizlikte kapanır. Ağız sesten önce açılabilir (1-2 kare), sonra açılmaz.
12. **İkizleme yok.** İki göz, iki kol, kalabalıktaki öğeler aynı fazda hareket etmez.

Uzun liste, sayılar ve kaynakları: `references/kurallar.md`. Karakter ve dudak senkronu: `references/karakter.md`.

## Denetim
Taslaktan sonra `video-izle` ile temas karelerine bak: çarpma karesinde ses tepesi var mı (`earshot`), gölge yönü sahne boyunca aynı mı, yuvarlanan nesne kayıyor mu. Kusur zaman damgasıyla `denetim` skill'inin slop listesine yazılır; onaysız düzeltilmez.
