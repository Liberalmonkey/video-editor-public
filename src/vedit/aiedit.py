"""AI Edit: headless ajan ile profesyonel kurgu.json yazımı, doğrulama ve taslak render.

WHY: bkz. wiki/decisions/0028-ai-edit.md. Stüdyo'da ya da terminalde kurgu.json'ı
usta-editor, viral-kurgu, footage-editing ve sound-design kurallarına göre ajan yazar;
vedit şema/dosya/çakışma denetimi yapar, bozuksa ikinci turda düzelttirir ya da eskiyi geri yükler.
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from . import (ajan_cagri, ff, fizik, hazir_efekt, karakter, hizli, kural, kurgu, motion, muzik_once, olaysesi, paths, ritim, sessizlik,
               stil, yaratici)
from .schemas import Kelime, Klip, Kurgu, KurguIz, KurguKaynak

KURALLAR = (
    ".claude/skills/usta-editor/SKILL.md",
    ".claude/skills/viral-kurgu/SKILL.md",
    ".claude/skills/footage-editing/SKILL.md",
    ".claude/skills/sound-design/SKILL.md",
    ".claude/skills/fizik-sezgisi/SKILL.md",  # ADR 0039: fizik, ışık, ses kuralları söylenmeden uygulanır
    ".claude/skills/yaratici-yon/SKILL.md",  # WHY: bkz. wiki/decisions/0064-yaratici-yon.md
    "library/kit.json",
    "library/sfx/manifest.json",
    "library/music/manifest.json",
    "library/motion/manifest.json",
)

SAHNE_KURALI = ".claude/skills/sahne-motoru/SKILL.md"

SEMA_OZETI = """## kurgu.json Şema Özeti (src/vedit/schemas.py ve studio/remotion/Kurgu.tsx)

Üst alanlar (`Kurgu`):
- `surum`: `1` (sabit)
- `rev`: tam sayı (sürüm numarası)
- `sekans`: `{"w": int, "h": int, "fps": 30}`
- `kaynaklar`: `dict[str, KurguKaynak]` — anahtar kaynak kimliğidir (ör. `"inputs_1_mp4"`, `"sfx_whoosh"`).
  Değer: `{"yol": "inputs:<ad>" | "library:<alt_yol>" | "public:<ad>", "sure": float, "w": int | null, "h": int | null, "ses": bool}`.
- `kelimeler`: `dict[str, list[Kelime]]` — kaynak kimliği -> `[{"w": str, "s": float, "e": float}]` (kaynak zamanında saniye).
- `izler`: `[{"id": "V2", "tur": "video", "ad": "Üst", "kilit": false, "sessiz": false, "gizli": false, "gain_db": 0.0}, ...]`
  (`V2` üst görüntü, `V1` ana görüntü, `A2` SFX, `A3` müzik; çizim alttan üste yapılır).
- `klipler`: `list[Klip]`
- `altyazi`: `{"acik": true, "iz": "V1", "stil": null}`
- `isaretler`: `[{"t": float, "ad": str}]` (sekans zamanında bölüm işaretleri)

`Klip` alanları:
- `id`: benzersiz 10 karakter kimlik (ör. `"cmwcfqz8b0"`).
- `iz`: `"V1" | "V2" | "A2" | "A3"` (izler listesindeki bir `id`). Aynı izdeki klipler çakışamaz (`b.bas >= a.bas + a.sure`).
- `bas`: sekans başlangıç zamanı (sn, `>= 0`).
- `sure`: sekans süresi (sn, `> 0`). Kaynakta `[giris, giris + sure * hiz]` aralığını okur.
- `tur`: `"video" | "gorsel" | "metin" | "sahne" | "motion" | "ses"`.
  - `"video"`, `"gorsel"`, `"motion"` kliplerinde `kaynak` zorunludur ve diskte var olan bir kaynağa işaret etmelidir.
    İstisna: `hf`, `sablon` ya da `bilesen` taşıyan motion klibi kaynaksız yazılır; kaynağı vedit bağlar.
  - `"metin"` klibinde `metin` (str) ve `metin_stil` kullanılır; `metin_stil.tip` yoksa düz metindir. Motion türleri aşağıda.
  - `"sahne"` klibinde `sahne` nesnesi kullanılır (alanlar aşağıda, "Sahne türleri").
  - `"ses"` klibinde (`A2`/`A3`) `kaynak` (`library:sfx/...` veya `library:music/...`), `ses` ve `olay`
    (`{"tur": <rol>, "guc": "yumusak" | "orta" | "sert", "sure": float, "not": str}`; roller "Ses Tasarımı" maddesinde, başka ad yazma. Müzikte `{"muzik": true}`,
    ayrık konuşmada `{"konusma": true}`) kullanılır.
- `giris`: kaynaktaki başlangıç saniyesi (`>= 0`, varsayılan `0.0`).
- `hiz`: oynatma hızı (`> 0`, varsayılan `1.0`).
- `bag`: bağlı klip kimliği veya `null`.
- `ses_kapali`: `bool` (varsayılan `false`).
- `konusmaci`: `bool` (`true` ise `Konusmaci` bileşeni: bölünmüş sahnede panel iner, `zoom` ve `punches` uygulanır).
- `zoom`: `float` (konuşmacı taban zoom, ör. `1.0`–`1.12`).
- `punches`: `list[float]` (konuşmacı klibinde kaynak zamanında saniye olarak vurgu zoom anları).
- `donus`: `{"x": list[KF], "y": list[KF], "olcek": list[KF], "opaklik": list[KF], "anim": list["x"|"y"|"olcek"|"opaklik"]}`.
  `KF`: `{"t": float, "v": float, "ease": "dogrusal"|"yumusak"|"giris"|"cikis"|"tut"}` (`t` klibin başından sn).
- `efekt`: `{"parlaklik": 1.0, "kontrast": 1.0, "doygunluk": 1.0, "bulanik": 0.0, "kirp": {"ust": float, "sag": float, "alt": float, "sol": float} | null}`.
- `ses`: `{"gain_db": 0.0, "fade_in": 0.012, "fade_out": 0.012, "duck": false, "temizle": false, "kf": list[KF]}`
  (müzikte `duck: true` konuşma varken müziği kısar; konuşmada `temizle: true` gürültü temizler).
- `gecis_giris`, `gecis_cikis`: `{"tur": "sil" | "kay" | "saat" | "iris" | "kirbac" | "isik" | "piksel" | "zoom_kirbac" | "film_yanigi" | "bolunme" | "bozulma" | "yirtma" | "capraz" | "kararma" | "kaydir" | "zoom" | "it" | "savur" | "bulanik", "sure": float, "yon": "sol" | "sag" | "yukari" | "asagi"} | null`
  (Önerilen orta noktalı geçişler: `sil` wipe, `kay` iki çekim birlikte kayar, `saat` saat yönünde açılır, `iris` daire açılır, `kirbac` hızlı bulanık whip,
  `isik` ışık sızıntılı süpürme, `piksel` blok çözülme, `zoom_kirbac` hızlı yakınlaşıp ışıkla oturan whip-zoom, `film_yanigi` organik sıcak film yanığı ve diyagonal açılış,
  `bolunme` ortadan iki kanatlı açılış, `bozulma` dijital RGB/şerit kayması, `yirtma` dalgalı kâğıt yırtığı. Bunların orta noktası kesimdedir, geçiş sesi kendiliğinden kesime gelir.
  Reels'te `sure` 0.2-0.4 sn. Geçiş yalnız V1 kesiminde; V2'ye `gecis-*` motion klibi koyma, kareyi düz renkle örter.)
  (`gecis_cikis` yalnız kararma uygular; geçiş sonraki klibin `gecis_giris` alanındadır)."""

# WHY: bkz. wiki/decisions/0031-motion-grafik.md. Alanlar Kurgu.tsx, MotionMetin.tsx ve SplitReel.tsx'in okuduklarıyla birebir;
# kurgu.denetle bilinmeyen türü reddeder.
MOTION_OZETI = """## Motion Grafik Alanları (studio/remotion/Kurgu.tsx, MotionMetin.tsx, SplitReel.tsx)

Grafik izleri: sahneleri `V2`'ye, metin/motion grafiklerini üstteki ayrı bir ize koy (gerekirse `izler` listesinin başına
`{"id": "V3", "tur": "video", "ad": "Grafik"}` ekle). Süreler saniye; `at` alanları sahnenin başından saniyedir.

### Sahne türleri (`tur: "sahne"`, `sahne` nesnesi)
Ortak: `layout: "split" | "full"`, `kind`, `bg: "dark" | "light" | "saydam"` (`saydam` yalnız `full`: alttaki video karartılıp üstüne
çizilir), `kicker: [{"at": 0, "text": "ÜST YAZI"}]` (yalnız split), `source: "kaynak adı"` (yalnız split).
- Düzen kuralı: `split` sahnede `konusmaci: true` olan V1 klibi alt panele (yatayda sağa) iner. Düzen bir sonraki sahne klibine kadar
  böyle kalır; konuşmacıya tam ekran dönmek için `kind`'sız `{"layout": "full"}` sahne klibi koy.
- `full` + `hook`/`cta`: konuşmacı üstünde büyük başlık kutusu. `title`, `size` (varsayılan 150; uzun başlıkta 100-120), `subtitle`.
- `full` + diğer türler: sahne içeriği tam ekran (`dark`/`light` opak, `saydam` video üstü).
- `shot`: ekran görüntüsü kartı. `img`: `"inputs:5.png"` (girdi görseli) ya da bir `kaynaklar` kimliği; vedit görseli bağlar,
  `iw`/`ih`'yi kendisi doldurur. `focus: {"x", "y", "w"}` görsel pikselinde görünen alan (yoksa tüm genişlik), `focus2` aynı biçimde
  bitiş odağı (kayarak yakınlaşır), `highlights: [{"x", "y", "w", "h", "at"}]` görsel pikselinde vurgu kutusu, `cardH` (560), `cardTop` (330).
- `stat`: `value` (sayı, sayarak büyür), `decimals`, `prefix`, `unit`, `label`; istersen `shot: {img, focus, ...}` altında görsel.
- `text`: `lines: [{"t": "satır", "size": 96, "accent": true|false, "at": 0.1}]` (en çok 3-4 kısa satır).
- `chips`: `items: [{"t": "madde", "at": 0.1, "done": 0.6}]` (2-3 madde) ve `banner: {"at": 1.4, "text": "sonuç"}` (zorunlu).
- `steps`: `items: [{"n": "1", "t": "adım", "at": 0.1}]` (en çok 3 adım).
- `timeline`: `nodes` tam iki öğe `[{"date": "2024", "text": "...", "at": 0.1, "y": 340}, {"date": "2026", "text": "...", "at": 0.8, "y": 720}]`,
  `line: {"at": 0.5, "text": "2 yıl"}`.

### Metin grafik türleri (`tur: "metin"`, `metin_stil.tip`)
Ortak `metin_stil` alanları: `konum: {"x": 0..1, "y": 0..1}` çapa (x < 0,34 sola, > 0,66 sağa yaslanır; y güvenli alana kısılır:
dikeyde 0,14-0,68, yatayda 0,09-0,74; yoksa türün varsayılanı yüzün altındadır), `boyut` (px), `buyuk` (büyük harf; anahtar ve
bolum'de varsayılan açık). Renk, yazı tipi, köşe, gölge ve hareket seçili stilin token'ından gelir (ADR 0043): `renk`, `vurgu` ve `arka`
YAZMA. Klip başına renk yalnız istisnadır ve stilin paletinden uzaksa `kurgu-denetle` STIL_DISI_RENK uyarır. Metinde `*kelime*` stilin
vurgu rengiyle çizilir; uzun kelime kendiliğinden küçülür; giriş ve çıkış animasyonu klibin süresinden hesaplanır.
- `anahtar`: 1-3 kelimelik vurucu söz, zıplayarak büyür. Örnek `metin: "Bu *çok* önemli"`. 1-1,5 sn.
- `altbant`: `metin: "Ad Soyad\\nUnvan"` (iki satır), vurgu şeridi + stilin paneli, soldan kayar. 3-4 sn.
- `etiket`: yuvarlak kutulu kısa konu etiketi (varsayılan sol üst). 2-3 sn.
- `cagri`: etiket + hedefe çizgi ve nokta. `hedef: {"x": 0..1, "y": 0..1}` karedeki nokta (gösterilen öğe). 2-3 sn.
- `daktilo`: harf harf yazılan metin, `hiz` (harf/sn, 22). 2-4 sn.
- `sayac`: `deger` (sayı, zorunlu), `baslangic` (0), `ondalik` (0), `onek` (ör. "₺"), `sonek` (ör. "%"); `metin` alt etiket. tr-TR biçimi.
- `ilerleme`: `adim` ve `toplam` (tam sayı, 1 <= adim <= toplam), `metin` adım adı; parçalı çubuk (varsayılan üstte). 2-3 sn.
- `bolum`: `numara` ("02"), `metin` başlık; silerek gelir, silerek gider. 2-2,5 sn.
- `vurgu`: el çizimi iz. `kutu: {"x", "y", "w", "h"}` 0..1 oranı, `bicim: "kutu" | "daire" | "alt_cizgi"`, `renk`, `kalinlik` (10).
  Metin klibinde kareye göredir; `tur: "gorsel"` klibinde `metin_stil: {"tip": "vurgu", ...}` görselin kendisine göredir (ekran görüntüsünde
  anlatılan düğme ya da alan).

### Motion klipleri (`tur: "motion"`)
Saydam webm; `kaynaklar`'a `{"yol": "library:motion/custom/<id>/<id>.webm", "sure": <süre>, "w": <g>, "h": <y>, "ses": false}` ekle,
klibi üst ize koy. Kare ortasına çizilir; `donus.x`/`donus.y` (px) ve `donus.olcek` ile hedefin üstüne taşı. Geçiş klibinin ortası kesime gelir.
"""

# WHY: bkz. wiki/decisions/0064-yaratici-yon.md. Sabit bileşen eşlemesi kaldırıldı; seçim işlev, brif ve katalog ilkelerine bağlandı.
MOTION_KURALLARI = """## Motion Grafik Kuralları ve Seçim İlkeleri
- Her grafiğin bir işi vardır (göster, karşılaştır, kanıtla, vurgula, geçiş, kapat); süs için grafik koyma.
- **Şablon yerine bilinçli seçim:** Bileşeni katalogdaki "Ne zaman" satırına, brifin metaforuna, iplik öğesine ve enerji eğrisine göre SEN seç. Aynı işlevi her videoda aynı bileşenle karşılama; seçimini rapora bir satırla yaz.
- **Rastgele ikon serpme yasağı:** Videoya yalnızca küçük ikonlar serpiştirmek ucuz şablon hissi verir. İkonlar (`ikon/*`) yalnız 1–1.3 sn'lik seyrek destekçidir; videodaki V2/V3 grafik kliplerinin **en çok %30'u ikon** olabilir.
- Grafiğe geçmeden her pasajda sor: bunu yalnız dinleyen izleyici anlar mı? Anlıyorsa konuşulanı ekrana tekrar yazma
  (altyazı zaten var); görsel durumu kesim, zoom ya da hareketle değiştir. Anlamıyorsa somut olanı göster: rakam,
  karşılaştırma, adım, arayüz, kaynak.
- Ürün adı geçiyorsa yalnız girdi klasöründeki resmi logo kullanılır; logo çizme, uydurma. Alıntı birebir olur; kaynağı
  açılıp doğrulanamayan söz alıntı kartına girmez.
- Görsel durum her 2-4 sn değişsin (kesim, zoom, grafik ya da sahne).
- Konuşmacının yüzünü, kadrajdaki odak nesnesini/ürünü ve altyazı bandını kapatma: `konum`u varsayılan bırak ya da güvenli alanda tut; tam ekran içerik kısa kalsın.
- Aynı anda en çok bir hero grafik. Aynı türü art arda 3 kez kullanma: tipografi, veri, kart, sahne ve hazır efekt
  arasında dolaş. Aynı kütüphane klibini videoda en çok iki kez kullan.
- Kütüphanedeki motion kliplerini ve şablonları "Ne zaman" satırı tutan anda kullan; konfeti videoda en çok bir kez.
- Sayı, oran, karşılaştırma, alıntı, liste ve çağrı için düz metin yerine uygun native bileşeni veya şablonu seç.
- Zoom ve vurgu için el keyframe'i (`donus`) yazma, `hazir` kullan (`el_kamerasi`, `hizli_zoom`, `punch`, `odak_zoom`, `odak_karart`); `donus` yalnız konum ve yerleşim içindir."""


def _hf_katalogu(work: Path, sekans: tuple[int, int] | None = None) -> str:
    """HyperFrames kompozisyonları (ADR 0050, 0062): canlı gömülen modern motion kataloğu.

    Dikey sekansta `yalniz_yatay` işaretli kompozisyon listelenmez (spec hf-canli-gomme-ve-dikey-duzen)."""
    from . import hf_grafik
    # WHY: bkz. wiki/decisions/0064-yaratici-yon.md. Tür/aile başlığıyla gruplama ajanın şablon yerine işleve göre seçmesini sağlar.
    gruplar: dict[str, list[str]] = {}
    for ad in hf_grafik.adlar(work):
        d = hf_grafik.bul(ad, work)
        try:
            o = hf_grafik.olcu(d)
        except ValueError:
            continue
        meta = hf_grafik.meta_bilgi(d)
        if sekans and sekans[1] > sekans[0] and meta.get("yalniz_yatay"):
            continue
        degisken = ", ".join(sorted(hf_grafik.degisken_adlari(d) or ())) or "yok"
        yer = "proje" if d.parent == hf_grafik.proje_kok(work) else "kütüphane"
        tur = f", {meta['tur']}" if meta.get("tur") else ""
        nz = f" Ne zaman: {meta['ne_zaman']}" if meta.get("ne_zaman") else ""
        ses = " [sesli]" if hf_grafik.ses_ipuclari(d) else ""
        uc = " [3D]" if meta.get("aile") == "uc" else ""
        kart = meta.get("kart") if isinstance(meta.get("kart"), dict) else {}
        yasak = f" Yapma: {kart['yasak']}" if kart.get("yasak") else ""
        grup = str(meta.get("tur") or meta.get("aile") or "diğer")
        gruplar.setdefault(grup, []).append(f"- `{ad}` ({yer}{tur}, {o['sure']:g} sn){ses}{uc}: param: {degisken}.{nz}{yasak}")
    govde = ("\n\n".join(f"**{g}**\n" + "\n".join(gruplar[g]) for g in sorted(gruplar, key=lambda x: (x == "diğer", x)))
             if gruplar else "- (henüz kompozisyon yok)")
    return ("### HyperFrames grafikleri (birincil motor, ADR 0050/0062; `tur: \"motion\"`, `hf: {\"ad\", \"param\"}`)\n"
            "Canlı alt-kompozisyon olarak doğrudan gömülür (WebM beklemesi yok, `[sesli]` olanlar +1 kare senkron SFX üretir). "
            "Yeni motion grafik, düğüm akışı, Bento ızgara, imleç odaklama, kod farkı, metin grafiği, alt bant ve 3B/izometrik sahne için "
            "önce bu listeye bak. Uygun kompozisyon yoksa ve dosya yazma iznin varsa `work/edit/hf/<ad>/index.html` yaz "
            "(sözleşme `library/motion/hf/SOZLESME.md`: saydam kök, `tema.css` v2 token'ı, `data-composition-variables`, paused GSAP timeline). "
            "Native bileşenler (`bilesen`) de HyperFrames sahnesidir (ADR 0051). Eski `sablon` yalnız ikisi de yoksa. "
            "`[3D]` olanlar three.js sahnesidir (ADR 0063): bir kez WebM'e render edilir, videoda en çok 2 ve art arda değil.\n"
            + govde)


MOTION_TURLERI = {"overlay": "İşaret ve vurgu", "icon": "İkon ve tepki", "transition": "Geçiş", "lower-third": "Alt bant",
                  "background": "Arka plan döngüsü", "broll": "Ara görüntü"}


def _param_ozeti(t: dict) -> str:
    v = t["vars"]
    if t.get("secenek"):
        ne = " | ".join(t["secenek"])
    elif isinstance(v, str):
        ne = f"en çok {t['max']} karakter" if t.get("max") else "metin"
    else:
        ne = f"{t.get('min', '')}-{t.get('max', '')}"
    return f"{ne}, varsayılan {json.dumps(v, ensure_ascii=False)}"


def _motion_katalogu(sekans: tuple[int, int] | None = None, *, izinli: set[str] | None = None) -> str:
    """library/motion/manifest.json'dan kullanılabilir motion kimlikleri; elle yazılmaz ki kütüphaneyle hep aynı kalsın."""
    f = paths.LIBRARY / "motion" / "manifest.json"
    try:
        girdiler = json.loads(f.read_text(encoding="utf-8")).get("entries", [])
    except (OSError, ValueError):
        girdiler = []
    girdiler = [e for e in girdiler if e.get("license") and (paths.ROOT / e["file"]).exists()]
    # WHY: bkz. wiki/decisions/0045-native-motion.md. Native karşılığı onaylanan eski kayıt seçilmez (kullanıcı onayı 2026-11-20).
    girdiler = [e for e in girdiler if not e.get("arsiv")]
    if izinli is not None:
        girdiler = [e for e in girdiler if e.get("id") in izinli]
    if sekans:  # tam kare geçiş yalnız kendi oranında işe yarar; öteki oranı listelemek isteği boşuna uzatır
        yatay = sekans[0] > sekans[1]
        girdiler = [e for e in girdiler if e.get("kind") != "transition" or (e.get("width", 0) > e.get("height", 0)) == yatay]
    kasa_bolum = _kasa_bolumu() if izinli is None else ""
    if not girdiler:
        return "\n\n".join(x for x in (kasa_bolum, "### Kütüphanedeki motion klipleri\n- Kütüphanede kullanılabilir motion klibi yok.") if x)

    def satir(e: dict) -> str:
        nz = f" Ne zaman: {e['ne_zaman']}" if e.get("ne_zaman") else ""
        yol = e["file"].removeprefix("library/")
        yer = "" if yol == f"motion/custom/{e['id']}/{e['id']}.webm" else f" `library:{yol}` —"
        return (f"- `{e['id']}` ({e.get('kind', '?')}, {e.get('duration_s', '?')} sn, {e.get('width')}x{e.get('height')}"
                f"{', saydam' if e.get('alpha') else ''}{', döngü' if e.get('loop') else ''}):{yer} {e.get('title', '')}.{nz}")

    def sablon(e: dict) -> str:
        pr = ", ".join(f"`{a}` ({_param_ozeti(t)})" for a, t in e["param"].items())
        return (f"- `{e['id']}` ({e.get('duration_s')} sn{', tam kare' if e.get('tam') else ''}): {e.get('title', '')}. "
                f"Ne zaman: {e.get('ne_zaman', '')} Parametreler: {pr}")

    # WHY: bkz. wiki/decisions/0036-motion-kutuphanesi-ve-ajanlar.md. Tür başlığı ajanın "bu ana ne uyar" aramasını kısaltır.
    bolum = ["### Kütüphanedeki motion klipleri (sabit; `kaynaklar` + `kaynak` ile)\n"
             "Yolu yazılmamış kaydın dosyası `library:motion/custom/<kimlik>/<kimlik>.webm`."]
    sabit = [e for e in girdiler if not e.get("param")]
    for tur, ad in [*MOTION_TURLERI.items(), (None, "Diğer")]:
        grup = [e for e in sabit if (e.get("kind") == tur if tur else e.get("kind") not in MOTION_TURLERI)]
        if grup:
            bolum.append(f"**{ad}**\n" + "\n".join(satir(e) for e in grup))
    sablonlar = [e for e in girdiler if e.get("param")]
    if sablonlar:
        temalar = ", ".join(f"`{t}`" for t in motion.temalar())
        bolum.append(
            "### Motion şablonları (yazısı ve değeri değişir; `sablon` ile)\n"
            'Klip: `{"tur": "motion", "iz": "V3", "bas": 4.2, "sure": <şablon süresi>, "sablon": {"ad": "<kimlik>", "param": {...}}}`. '
            "`kaynak` ve `kaynaklar` yazma; dosyayı vedit üretir. `sure` şablon süresini aşmaz. Yazılmayan parametre varsayılanı alır. "
            f"Tema kurgunun en üstündeki `motion_tema` alanıdır (videonun tamamında tek tema; sabit kütüphane klipleri de bu temayla "
            f"yeniden renklenir): {temalar}, `proje` (videodan çıkarılan). Hangisini yazacağın Stil bölümündedir. "
            "Tam kare şablon kendini yerleştirir, `donus` yazma.\n" + "\n".join(sablon(e) for e in sablonlar))
    return "\n\n".join(([kasa_bolum] if kasa_bolum else []) + bolum)


def _kasa_bolumu() -> str:
    """Kullanıcının videodan kaydettiği varlıklar; ajan önce bunlara bakar (ADR 0061: Kasam → Keşif → üret)."""
    from . import kasa
    kayitlar = [e for e in kasa.oku() if e.get("tur") != "sfx" and (e.get("bilesen") or (e.get("file") and (paths.ROOT / e["file"]).exists()))]
    if not kayitlar:
        return ""

    def satir(e: dict) -> str:
        if e.get("bilesen"):
            nasil = f'`"bilesen": {json.dumps(e["bilesen"], ensure_ascii=False)}`'
        else:
            nasil = f'`kaynaklar` yolu `library:{e["file"].removeprefix("library/")}`'
            if e.get("sablon"):
                nasil += f', `"sablon": {json.dumps(e["sablon"], ensure_ascii=False)}` (param değişebilir)'
            if e.get("hf"):
                nasil += f', `"hf": {json.dumps(e["hf"], ensure_ascii=False)}` (param değişebilir)'
        return f"- `{e['id']}` ({e.get('tur')}, {e.get('sure')} sn): {e.get('title', '')}. Kullanım: {nasil}"

    return ("### Kasam: kullanıcının onayladığı varlıklar (önce bunlar)\n"
            "Sıra: uygun anda önce Kasam, sonra aşağıdaki kütüphane ve native bileşenler; hiçbiri uymuyorsa seçili stilin "
            "token'ıyla HyperFrames kompozisyonu üret (`work/edit/hf/<ad>/`).\n" + "\n".join(satir(e) for e in kayitlar))


def _tema_bolumu(p, stil_k) -> str:
    """Motion teması talimatı. WHY: bkz. wiki/decisions/0042-stil-katalogu-ve-video-temasi.md; grafik her videoda turuncu gelmesin."""
    if stil_k and (t := stil.motion_temasi(stil_k)) and motion.tema_yolu(t):
        return (f"### Motion teması\nSeçili stilin teması `{t}`. Kurgunun en üstüne `\"motion_tema\": \"{t}\"` yaz; "
                "klip bazında `sablon.tema` yazma.")
    css = p.work / "edit" / "motion_tema.css"
    if not css.is_file():
        try:
            from . import tema
            tema.cikar(p)
        except (SystemExit, OSError, ValueError) as e:
            print(f"  ! tema-cikar atlandı: {e}")
    if css.is_file():
        renk = dict(re.findall(r"--(vurgu|ikincil|zemin)\s*:\s*(#[0-9A-Fa-f]{6})", css.read_text(encoding="utf-8")))
        return ("### Motion teması\nStil teması yok. Videonun kendi renklerinden proje teması çıkarıldı ("
                + ", ".join(f"{a} {v}" for a, v in renk.items()) + "). Varsayılan olarak `\"motion_tema\": \"proje\"` yaz. "
                "Konu açıkça başka bir dil istiyorsa (ör. finans için `altin-fintech`, teknik çizim için `xray-sema`) "
                "kütüphane temalarından birini seç. `varsayilan` ve `turuncu` yazma; turuncu yalnız kullanıcı isterse.")
    return ("### Motion teması\nStil teması yok. Konuya en uygun kütüphane temasını seç ve `motion_tema` alanına yaz. "
            "`varsayilan` ve `turuncu` yazma; turuncu yalnız kullanıcı isterse.")


def _hazir_katalogu() -> str:
    """studio/remotion/hazirEfekt.json'dan hazır efekt kataloğu; elle yazılmaz ki Kurgu.tsx ile hep aynı kalsın (ADR 0033)."""
    def aralik(a: str, pr: dict) -> str:
        if "secenek" in pr:
            return f"`{a}` ({' | '.join(pr['secenek'])}, varsayılan {pr['vars']})"
        if isinstance(pr["vars"], bool):
            return f"`{a}` (true/false, varsayılan {str(pr['vars']).lower()})"
        vars_ = "0, klibin sonuna kadar" if a == "sure" and pr["vars"] == 0 else pr["vars"]
        return f"`{a}` ({pr.get('min')}-{pr.get('max')}, varsayılan {vars_})"
    satirlar = [f"- `{ad}`{' (sesli)' if tn['ses'] else ''}: {tn['amac']} Ne zaman: {tn['ne_zaman']} Parametreler: "
                + ", ".join(aralik(a, pr) for a, pr in tn["param"].items())
                for ad, tn in hazir_efekt.katalog().items()]
    return ("### Hazır efektler (`hazir`, görüntü kliplerinde)\n"
            "Klipte `hazir: [{\"ad\": \"punch\", \"t\": 1.2, \"sure\": 0.6, \"s\": 1.14}]`; `t` klibin başından sn (yoksa 0, çıkış efektinde klip sonu), "
            "`sure` 0 ise klibin sonuna kadar. Yazılmayan parametre varsayılan ya da art arda kliplerde değişen değer alır. "
            "Sesli efektin sesi kendiliğinden eklenir, A2'ye ayrıca ses klibi koyma; istemezsen `\"ses\": false`.\n" + "\n".join(satirlar))


def _ses_rolleri() -> str:
    """Rol ve kombo adları koddan: istek olaysesi'nden sapmasın."""
    return ", ".join(f"`{a}`" for a in [*olaysesi.ROLLER, *getattr(olaysesi, "KOMBOLAR", {})])


def _hazir_mi(p: hizli.Proje) -> bool:
    f = p.work / "analysis" / "transcript.json"
    if not p.girdi.exists():
        return False
    if not _medya(p):  # yalnız senaryo: ölçülecek ses ve görüntü yok, hazirla atlanır
        return True
    if not f.exists():
        return False
    try:
        mevcut = set(json.loads(f.read_text(encoding="utf-8")).get("files", {}))
    except Exception:
        return False
    return {x.stem for x in _medya(p)} <= mevcut


def _medya(p: hizli.Proje) -> list[Path]:
    return sorted((x for x in p.girdi.iterdir() if x.is_file() and x.suffix.lower() in hizli.MEDYA),
                  key=lambda x: hizli.dogal(x.name)) if p.girdi.exists() else []


def _animasyon(k: Kurgu) -> bool:
    """Kurguda video klibi yok: görüntü sahne, motion ve görsel klipleriyle sıfırdan kurulur."""
    return not any(c.tur == "video" for c in k.klipler)


def girdi_kimligi(ad: str) -> str:
    """Girdi dosyasının kurgudaki kaynak kimliği (ör. `1.mp4` → `inputs_1_mp4`)."""
    return re.sub(r"\W", "_", "inputs:" + ad)


def _girdisiz(k: Kurgu) -> bool:
    """Kurguda girdiden gelen görüntü ya da konuşma klibi yok (yeni ya da Stüdyo'da boş açılmış kurgu)."""
    return not any(c.tur == "video" or (c.olay or {}).get("konusma") for c in k.klipler) \
        and not any(kay.yol.startswith("inputs:") for kay in k.kaynaklar.values())


def _girdileri_tohumla(p: hizli.Proje, k: Kurgu) -> bool:
    """Girdi medyasını kaynak ve ardışık klip olarak kurguya ekler. Bir şey eklendiyse True."""
    medya = _medya(p)
    videolar = [x for x in medya if x.suffix.lower() in hizli.VIDEO]
    # Video yoksa seslendirme konuşma klibi olur: altyazı ve zamanlama ondan gelir, görüntüyü ajan kurar.
    sesler = [] if videolar else medya
    if not medya:
        return False
    hedef_iz = "A1" if sesler else "V1"
    if not any(i.id == hedef_iz for i in k.izler):
        k.izler.append(KurguIz(id="A1", tur="ses", ad="Konuşma") if sesler else KurguIz(id="V1", tur="video", ad="Ana"))
    imlec = 0.0
    for v_dosya in videolar or sesler:
        kid = girdi_kimligi(v_dosya.name)
        info = ff.probe(v_dosya)
        v = info.get("video") or {}
        sure = float(info.get("duration") or 0.0)
        k.kaynaklar[kid] = KurguKaynak(
            yol=f"inputs:{v_dosya.name}", sure=sure, w=v.get("width"), h=v.get("height"), ses=bool(info.get("audio"))
        )
        if sure > 0:
            k.klipler.append(Klip(
                id=uuid.uuid4().hex[:10], bas=round(imlec, 3), sure=sure, kaynak=kid,
                **({"iz": "A1", "tur": "ses", "olay": {"konusma": True}} if sesler else {"iz": "V1", "tur": "video"})
            ))
            imlec += sure
    return True


def girdi_denetimi(p: hizli.Proje, k: Kurgu) -> None:
    """Ajan çağrısından önce: girdideki video kurguda kaynak değilse token harcamadan dur; kelimesiz kaynağı uyar."""
    videolar = [x for x in _medya(p) if x.suffix.lower() in hizli.VIDEO]
    alinan = {kay.yol.removeprefix("inputs:") for kay in k.kaynaklar.values() if kay.yol.startswith("inputs:")}
    if videolar and not alinan:
        raise SystemExit("Girdideki videolar kurguya alınamadı (kurguda inputs: kaynağı yok). "
                         f"{paths.rel(kurgu.yol(p.work))} dosyasını kontrol edin ya da silip yeniden deneyin.")
    if (p.work / "analysis" / "transcript.json").exists():
        eksik = [kid for kid, kay in k.kaynaklar.items() if kay.yol.startswith("inputs:") and kay.ses and not k.kelimeler.get(kid)]
        if eksik:
            print(f"  Uyarı: kelimesi olmayan girdi kaynağı: {', '.join(eksik)} (altyazı ve çapa bu kaynakta çalışmaz).", flush=True)


def _kurgu_hazirla(p: hizli.Proje) -> Kurgu:
    f = kurgu.yol(p.work)
    vardi = f.exists()
    k = kurgu.oku(p.work) if vardi else kurgu.bos(p.studyo)
    # WHY: ornek-proje 2026-11-27. Stüdyo kurguyu girdiler gelmeden boş yazmıştı; tohumlama yalnız dosya yokken
    # çalıştığı için videolar hiç alınmadı ve swarm 4 dakika sonra G3'te "görüntü klibi yok" ile düştü.
    tohum = p.girdi.exists() and _girdisiz(k) and _girdileri_tohumla(p, k)
    if tohum and vardi:
        print("  Kurguda girdi yoktu: girdi medyası kurguya alındı.", flush=True)
    degisti = False
    for kid, kay in k.kaynaklar.items():
        if not k.kelimeler.get(kid):
            kel = kurgu.kaynak_kelimeleri(p, kurgu.dosya(p, kay.yol))
            if kel:
                k.kelimeler[kid] = [Kelime.model_validate(w) for w in kel]
                degisti = True
    if not vardi or tohum:
        return kurgu.yaz(p.work, k)
    from .ekip_v3 import iz_cakisma_coz  # döngüsel içe aktarma: ekip_v3 bu modülü kullanır
    if iz_cakisma_coz(k)[0]:
        # WHY: önceki bir koşunun bıraktığı iz çakışması her yeni editi aynı denetim hatasıyla düşürüyordu (reel-video 2026-11-23).
        print("  Kurguda üst üste binen klipler ayrıldı.", flush=True)
        return kurgu.yaz(p.work, k)
    if degisti:
        # WHY: mevcut kurguda yalnız eksik kelimeler tamamlandıysa ajan öncesi fazladan rev/geçmiş oluşmasın.
        kurgu._atomik(f, k.model_dump_json(indent=1, exclude_defaults=False))
    return k


def _yogunluk_hedefi(p: hizli.Proje, seviye: str) -> float | None:
    h = kurgu.YOGUNLUK.get(seviye)
    return h[1 if p.studyo.startswith("youtube") else 0] if h else None


def _yogunluk_kurali(p: hizli.Proje, seviye: str) -> str:
    h = _yogunluk_hedefi(p, seviye)
    if not h:
        return ""
    # WHY: bkz. wiki/decisions/0064-yaratici-yon.md. Yoğunluk sabit kota değil, brifin enerji eğrisini izler.
    return (f"\n- **Yoğunluk hedefi:** taban ortalama {h:g} saniyede bir grafik olayı (sahne, motion metin, motion klibi, şablon ya da "
            f"hazır efekt); grafiksiz aralık tabanı {h * 2:g} saniyedir. Yoğunluk hedefi enerji eğrisini izler; sakin bölüm boş kalabilir, "
            "yüksek enerjili bölümler sıklaşır. Hedefi doldurmak için dolgu grafik koyma: o anda söylenen söze bağlanan grafiği bul.")


def _enerji_dilimleri(work: Path, notu: str | None) -> list[tuple[float, float, int]] | None:
    """Geçerli yaratıcı brifin enerji eğrisi dilimleri; brif yoksa None."""
    # WHY: bkz. wiki/decisions/0064-yaratici-yon.md. Enerji eğrisi motion_yogunlugu eşiklerini ölçekler.
    b = yaratici.gecerli(work, notu)
    return [(e.aralik[0], e.aralik[1], e.seviye) for e in b.enerji] if b and b.enerji else None


def _ritim_bolumu(p: hizli.Proje, k: Kurgu) -> str:
    """Ölçülmüş ses anları: ajan sesi duyamaz, kesim ve olay sesini bu sayılara oturtur (ADR 0039)."""
    try:
        r = json.loads(ritim.yaz(p, k).read_text(encoding="utf-8"))
    except Exception as e:  # WHY: ölçüm kurgu yazımını durdurmasın; ajan ölçümsüz de çalışır
        return f"## Ritim ve Senkron\n- Ritim ölçülemedi ({type(e).__name__}); kesimleri kelime sınırına koy."
    kare = 1 / k.sekans.fps
    return ("## Ritim ve Senkron (ölçüldü: `work/edit/ritim.json`)\n" + ritim.ozet(r) + "\n"
            f"- Ses efekti olayının `bas`ı görünen olayın ilk karesindedir; ölçülmüş vurgu anından en çok {kare:.3f} sn (1 kare) sapar.\n"
            "- Müzik varsa sahne ve grafik girişleri beat'e oturur (en yakın beat, en çok 2 kare); her beat'e kesme koyma, "
            "4 ya da 8 beatlik öbekler kur.\n"
            "- Konuşma vurgusunda punch ya da grafik vurgulu hecenin başında başlar, hecenin üstüne ses efekti bindirme.\n"
            "- Hareketli bir olay (çarpma, düşme, kapı kapanması, el çırpma) görüntüde ve seste aynı karede olur; ses görüntüden önce gelmez.")


def _istek_yaz(p: hizli.Proje, k: Kurgu, *, stil_adi: str | None, notu: str | None, motion_seviye: str = "yogun",
               aralik: tuple[float, float] | None = None, rol: str = "hepsi") -> Path:
    animasyon = _animasyon(k)
    kurallar = [str((paths.ROOT / y).resolve()) for y in (*KURALLAR, *([SAHNE_KURALI] if animasyon else []))
                if (paths.ROOT / y).exists()]
    sheets_k = p.work / "analysis" / "sheets"
    sheets = [str(x.resolve()) for x in sorted(sheets_k.glob("*.jpg"))] if sheets_k.exists() else []
    gorseller = sorted(
        (x for x in p.girdi.rglob("*") if x.is_file() and x.suffix.lower() in hizli.GORSEL),
        key=lambda x: hizli.dogal(x.name),
    ) if p.girdi.exists() else []
    try:
        adaylar = sessizlik.oneriler(p, k)
    except Exception:
        adaylar = []
    from . import native_motion, stil_varlik
    stil_k = stil.secili(p, stil_adi)
    etkin_stil_ad = stil_k.name if stil_k else (stil_adi or stil.secili_adi(p))
    depo = stil_varlik.oku(p.studyo, etkin_stil_ad) if etkin_stil_ad else None
    ozel_varlik = stil_varlik.baglam_metni(p.studyo, etkin_stil_ad) if etkin_stil_ad else ""
    if stil_k:
        stil_metin = f"Bu stile uy:\n- STYLE.md: `{(stil_k / 'STYLE.md').resolve()}`"
        if (stil_k / "MOTION.md").exists():
            stil_metin += f"\n- MOTION.md: `{(stil_k / 'MOTION.md').resolve()}`"
    else:
        stil_metin = "Stil seçilmedi."
    if ozel_varlik:
        stil_metin += "\n\n" + ozel_varlik
    stil_metin += "\n\n" + _tema_bolumu(p, stil_k)
    platform = hizli.PLATFORM.get(p.studyo, p.studyo)
    rapor_yol = (p.work / "edit" / "ai-edit.rapor.md").resolve()
    kurgu_yol = kurgu.yol(p.work).resolve()
    digest_yol = (p.work / "analysis" / "digest.txt").resolve()
    senaryo = p.girdi / "senaryo.md"

    bolumler = [
        "# AI Edit Kurgu Görevi\n\n"
        "Sen 15 yıllık kıdemli bir video kurgu editörüsün. Görevin bu projenin ham çekimlerini, "
        "kelime zamanlarını ve görsellerini inceleyip doğrudan profesyonel bir `kurgu.json` yazmaktır.",
        "## Önce Okunacak Kurallar ve Kütüphane\n" + "\n".join(f"- `{y}`" for y in kurallar),
        # WHY: bkz. wiki/decisions/0047-kural-deposu.md. Rol, stüdyo, stil ve projeye göre süzülmüş etkin kurallar; P0 asla düşmez.
        "## Etkin Kurallar (kural deposu; her biri bağlayıcı, ihlal kimliğiyle raporlanır)\n"
        + (kural.paket(kural.yukle(), rol=rol, studyo=p.studyo, stil=stil_k.name if stil_k else None, proje=f"{p.studyo}/{p.ad}")
           or "- (etkin kural yok)"),
        "## Proje Girdileri\n"
        f"- Stüdyo / Platform: `{p.studyo}` (`{platform}`)\n"
        f"- Sekans ölçüsü: `{k.sekans.w}x{k.sekans.h} @ {k.sekans.fps} fps`\n"
        f"- Kurgu dosyası (okunacak ve üzerine yazılacak): `{kurgu_yol}`\n"
        f"- Rapor dosyası (yazılacak): `{rapor_yol}`\n"
        + (f"- Transkript özeti (digest): `{digest_yol}`\n" if digest_yol.exists() else "- Transkript yok.\n")
        + (f"- Senaryo: `{senaryo.resolve()}`\n" if senaryo.exists() else "")
        + ("- Kontak sayfaları (kareleri incele):\n" + "\n".join(f"  - `{s}`" for s in sheets)
           if sheets else "- Kontak sayfası yok.")
        + ("\n- Girdi klasöründeki görseller / ekran görüntüleri:\n"
           + "\n".join(f"  - `inputs:{g.relative_to(p.girdi).as_posix()}` -> `{g.resolve()}`" for g in gorseller)
           if gorseller else "\n- Girdi klasöründe ek görsel yok."),
        "## Sessizlik ve Dolgu Adayları (sekans zamanında)\n```json\n"
        + json.dumps(adaylar, ensure_ascii=False, indent=1) + "\n```",
        f"## Stil\n{stil_metin}",
    ]
    if notu and notu.strip():
        bolumler.append(f"## Kullanıcı Notu\n{notu.strip()}")
    # WHY: bkz. wiki/decisions/0064-yaratici-yon.md. Önce videoya özgü fikir, sonra kurgu. Aralık düzeltmesinde yeni brif yazılmaz.
    if brif_bolumu := yaratici.tek_ajan_bolumu(p.work, notu, yazabilir=not aralik):
        bolumler.append(brif_bolumu)
    if animasyon:
        sesli = any((c.olay or {}).get("konusma") for c in k.klipler)
        bolumler.append(
            "## Animasyon Modu (video çekimi yok)\n"
            "Bu projede konuşmacı videosu yok; görüntünün tamamını sen kurarsın.\n"
            "- `V1` izini baştan sona boşluksuz doldur: `full` düzenli `sahne` klipleri (`bg: \"dark\"` ya da `\"light\"`), "
            "girdi görselleri (`tur: \"gorsel\"`) ve tam kare motion şablonları. `konusmaci`, `zoom`, `punches` ve `split` düzen kullanma.\n"
            "- Metin grafikleri ve saydam motion klipleri üst ize; aynı anda en çok bir grafik kuralı sürer.\n"
            + ("- Zamanlama `A1` izindeki seslendirmenin kelime zamanlarından gelir: her sahne anlattığı cümleyle başlar ve biter. "
               "`A1` klibine dokunma; kırpma (a) ve hook (b) adımlarını atla.\n" if sesli else
               "- Ses yok: süreyi senaryodan hesapla (saniyede yaklaşık 2,5 kelime), her sahne anlattığı cümle kadar sürer. "
               "`altyazi.acik` `false` olur. Kırpma (a) ve hook (b) adımlarını atla; hook'u ilk sahne taşır.\n")
            + "- Her sahnenin türünü ve görsel dilini `sahne-motoru` kuralına göre seç; art arda iki sahne aynı türde olmasın.")
    if aralik:
        bolumler.append(
            f"## Kapsam: yalnız {aralik[0]:.2f}-{aralik[1]:.2f} sn aralığı\n"
            "Kullanıcı kurgunun yalnız bu aralığını düzelttiriyor. Aralığın dışındaki hiçbir klibi değiştirme, silme, yeniden adlandırma: "
            "`id` dahil bütün alanları aynı kalır. Aralıkta süre kısalır ya da uzarsa sonraki bütün klipleri (her izde) aynı miktarda "
            "kaydır; yalnız `bas` değişir. Aralığın içinde serbestsin. Aşağıdaki geçiş listesini yalnız bu aralığa uygula.")
    izinli_native = set(depo.secili_native) if (depo and depo.yalniz_bunlar) else None
    izinli_kutup = set(depo.secili_kutuphane) if (depo and depo.yalniz_bunlar) else None
    native_satirlar = native_motion.katalog_ozeti(izinli=izinli_native)
    native_bolumu = "### Native motion bileşenleri (`tur: \"motion\"`, `bilesen: {\"ad\", \"param\"}`)\n" + (
        "\n".join(native_satirlar) if native_satirlar else "- (yalniz_bunlar aktif, seçili native bileşen yok)"
    )
    etkin_stil_k = stil_k or (stil.klasor(p.studyo, etkin_stil_ad) if etkin_stil_ad else None)
    bolumler += [
        SEMA_OZETI,
        MOTION_OZETI + "\n" + _hf_katalogu(p.work, (k.sekans.w, k.sekans.h)) + "\n\n" + native_bolumu + "\n\n" + _motion_katalogu((k.sekans.w, k.sekans.h), izinli=izinli_kutup),
        MOTION_KURALLARI + _yogunluk_kurali(p, motion_seviye),
        _hazir_katalogu(),
        "\n\n".join(x for x in (fizik.katalog_metni(), karakter.katalog_metni(etkin_stil_k)) if x),
        _ritim_bolumu(p, k),
        # WHY: bkz. wiki/decisions/0064-yaratici-yon.md (adım 8). Aralık düzeltmesinde müzik yeniden seçilmez.
        "" if aralik else muzik_once.metin(muzik_once.hazirla(
            p, yaratici.gecerli(p.work, notu), notu, max((c.bas + c.sure for c in k.klipler), default=0.0))),
        # WHY: bkz. wiki/decisions/0064-yaratici-yon.md. Zorunlu şablon tarifleri yerine yaratıcı yetki ve araç kutusu.
        "## Yapılacak Kurgu Geçişleri (Sırayla)\n"
        "- **Yaratıcı yetki:** Videoya özgün bir yaklaşım kur: match cut, speed ramp, J/L cut, pattern interrupt, sessizlik + vuruş gibi "
        "en az bir bilinçli yaratıcı karar uygula; brifteki imza anlarını teslim et ve neyi neden seçtiğini rapora yaz.\n"
        "- **(a) Kırpma:** 0.4 sn üstü ölü boşlukları, dolgu seslerini ve tekrarları kelime sınırında kırp "
        "(klibi böl: `giris`, `sure`, `bas` değerlerini güncelle; aynı izde klipler çakışmaz ve V1'de boşluk kalmaz).\n"
        "- **(b) Hook:** En güçlü ve merak uyandıran cümle ilk 3 saniyeye gelir; nasıl güçlendireceğine brif karar verir "
        "(söz, kesim, ses ya da uygun grafik). Anlatı ya da kullanıcı sırası bozulacaksa yalnız baştaki boşluğu ve zayıf girişi kırp.\n"
        "- **(c) Konuşmacı ve Kamera Dinamiği:** Konuşmacı kliplerinde `konusmaci: true`, uygun `zoom` ve önemli "
        "kelimelerde kaynak zamanlı `punches` kullanabilirsin. `el_kamerasi`, `hizli_zoom`, `punch` ve `odak_karart` durağanlık "
        "4,5 saniyeyi geçerse kullanılabilecek araçlardır; her klibe değil, enerji eğrisine göre seç. Jump cut noktalarını zoom veya üst katmanla gizle.\n"
        "- **(d) B-Roll ve Ekran Görüntüleri:** Girdi klasöründeki ekran görüntülerini ilgili kelimenin "
        "söylendiği anda `kaynaklar`a ekleyip `V2` izine (`tur: \"gorsel\"` ya da `shot` sahnesi, `img: \"inputs:<ad>\"`) yerleştir. "
        "Üst katmandaki görsel ya da metin konuşmacının yüzünü, kadrajdaki odak nesnesini/ürünü ve altyazı bandını kapatmaz: `donus.y` ile yüzün üstüne ya da "
        "altına taşı, sığmıyorsa görseli kısa süre tam ekran göster.\n"
        "- **(e) Geçişler:** Geçiş anlam değişimini söyler; videonun %90'ı düz kesim kalır, tek videoda en çok 2-3 geçiş ailesi kullanılır. "
        "Bölüm ve konu değişimlerinde seçili stilin karakterine uygun orta noktalı geçişleri "
        "(`zoom_kirbac`, `film_yanigi`, `bolunme`, `yirtma`, `bozulma`, `isik`, `kirbac`, `kay`, `sil`, `iris`, `saat`, `piksel`) ölçülü seç.\n"
        "- **(f) Ses Tasarımı:** Ses efekti için dosya seçme; `A2` izine kaynaksız rol olayı yaz: "
        "`{\"tur\": \"ses\", \"iz\": \"A2\", \"bas\": <görünen olayın anı>, \"sure\": 0.3, "
        "\"olay\": {\"tur\": <rol>, \"guc\": \"yumusak|orta|sert\", \"sure\": <hareket süresi>, \"not\": <neden>}}`. "
        f"Roller: {_ses_rolleri()}. Dosyayı, tepe hizasını ve seviyeyi `vedit` seçer. Hazır efektin ve orta noktalı V1 geçişinin sesi kendiliğinden gelir, "
        "onlara ayrıca olay yazma. Bölüm açılışı, geçiş ve önemli grafik girişi SFX için adaydır; sessizlik de seçimdir. Kullanacağın "
        "anlarda katmanlı, kulağı yormayan gerçek SFX rol olayı seç (sentetik ses yok; her kesmeye whoosh koyma; en çok 0,4 saniyede bir ses, "
        "15 saniyede 4-8 ses; `sert` videoda bir iki büyük an için; vurgulu hecenin üstüne ses bindirme; sessiz an da tasarımdır). Müzik `A3` izinde "
        "kütüphanedeki parçayla: hikâye/duygu anlarında dinamik nefes ve ducking (`ses.duck: true`, `olay: {\"muzik\": true}`, gerekirse `ses.kf`).\n"
        "- **(g) Bölüm İşaretleri:** `isaretler` listesine kurgunun ana bölümlerini (`t`, `ad`) ekle.",
        "## Sabit Kurallar ve Sınırlar\n"
        "- `altyazi.stil` `null` kalır, `altyazi.acik` `true` olur (ADR 0014; sessiz animasyon modu hariç).\n"
        "- Mevcut `kaynaklar` ve `kelimeler` içeriği silinmez (yeni görsel/ses kaynağı eklenebilir).\n"
        "- Girdi dosyalarına dokunma.\n"
        f"- Yalnız iki dosya yaz: `{kurgu_yol}` (geçerli JSON, şemaya uygun, UTF-8) ve `{rapor_yol}` "
        "(ne kesildi, neden, zaman damgalı, en çok 40 satır). İstisnalar: bu videoya özgü HyperFrames grafiği için "
        f"`{(p.work / 'edit' / 'hf').resolve()}/<ad>/index.html` (ADR 0050, sözleşme `library/motion/hf/SOZLESME.md`) ve "
        f"Yaratıcı Yön bölümü istiyorsa `{yaratici.yol(p.work).resolve()}` (ADR 0064).\n"
        "- Kabuk komutu çalıştırma.\n"
        "- Kütüphanede veya girdi klasöründe gerçekten var olmayan hiçbir dosyaya kaynak yazma.",
    ]
    hedef = p.work / "edit" / "ai-edit.istek.md"
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text("\n\n".join(b for b in bolumler if b) + "\n", encoding="utf-8")
    return hedef


def _aralik_disi(eski: Kurgu, yeni: Kurgu, bas: float, son: float) -> list[str]:
    """Aralık düzeltmesinde dokunulmaması gereken klipler: öncekiler birebir, sonrakiler yalnız tek tip kaymayla aynı."""
    yeniler = {c.id: c for c in yeni.klipler}
    hatalar, kaymalar = [], set()
    for c in eski.klipler:
        once, sonra = c.bas + c.sure <= bas + 1e-3, c.bas >= son - 1e-3
        if not (once or sonra):
            continue
        y = yeniler.get(c.id)
        if y is None:
            hatalar.append(f"{c.id}: aralık dışındaki klip silinmiş ya da kimliği değişmiş ({c.bas:.2f} sn)")
        elif y.model_dump(exclude={"bas"}) != c.model_dump(exclude={"bas"}) or (once and abs(y.bas - c.bas) > 1e-3):
            hatalar.append(f"{c.id}: aralık dışındaki klip değişmiş ({c.bas:.2f} sn)")
        elif sonra:
            kaymalar.add(round(y.bas - c.bas, 2))
    if len(kaymalar) > 1:
        hatalar.append(f"Aralıktan sonraki klipler farklı miktarlarda kaymış ({sorted(kaymalar)}); hepsi aynı miktarda kaymalı")
    # Yeni klip yalnız aralığın içine konur; aralığın yeni bitişi sonraki kliplerin kayması kadar oynar (sonrası boşsa serbest).
    yeni_son = son + next(iter(kaymalar)) if len(kaymalar) == 1 else float("inf") if not kaymalar else son
    eskiler = {c.id for c in eski.klipler}
    for c in yeni.klipler:
        if c.id not in eskiler and (c.bas < bas - 1e-3 or c.bas + c.sure > yeni_son + 1e-3):
            hatalar.append(f"{c.id}: aralığın dışına yeni klip eklenmiş ({c.bas:.2f}-{c.bas + c.sure:.2f} sn)")
    return hatalar


def _hatalar(p: hizli.Proje, eski: Kurgu | None = None, aralik: tuple[float, float] | None = None) -> list[str]:
    try:
        k = kurgu.oku(p.work)
    except (OSError, ValueError) as e:
        return [str(e)]
    return kurgu.denetle(p, k) + tema_hatalari(p, k) + (_aralik_disi(eski, k, *aralik) if aralik and eski else [])


def tema_hatalari(p: hizli.Proje, k: Kurgu) -> list[str]:
    """Ajanın kurguda kullandığı kendi kompozisyonu ve parametreleri tema kilidini delmesin (ADR 0043, 0058).

    Yalnız proje kompozisyonları (`work/edit/hf/`) taranır; kütüphane kayıtları kendi denetiminden geçmiştir."""
    from . import hf_grafik, tema_denetim
    out: list[str] = []
    kok = hf_grafik.proje_kok(p.work)
    for c in k.klipler:
        for alan in ("hf", "sablon"):
            d = getattr(c, alan, None)
            if not isinstance(d, dict):
                continue
            out += tema_denetim.param_ihlalleri(d.get("param"), kaynak=c.id)
            if alan == "hf" and (f := kok / str(d.get("ad") or "") / "index.html").is_file():
                out += tema_denetim.ihlaller(f.read_text(encoding="utf-8", errors="replace"), kaynak=f"work/edit/hf/{d.get('ad')}")
    v = list(dict.fromkeys(out))
    return [tema_denetim.mesaj(v)] if v else []


def calistir(
    p: hizli.Proje,
    *,
    motor: str = "claude",
    model: str | None = None,
    stil: str | None = None,
    notu: str | None = None,
    final: bool = False,
    final_ek: dict | None = None,
    motion_seviye: str = "yogun",
    aralik: tuple[float, float] | None = None,
) -> None:
    if aralik and not 0 <= aralik[0] < aralik[1]:
        raise SystemExit("Aralık: başlangıç sıfırdan küçük olamaz ve bitişten küçük olmalı")
    if not _hazir_mi(p):
        hizli.hazirla(p)
    k = _kurgu_hazirla(p)
    girdi_denetimi(p, k)
    istek = _istek_yaz(p, k, stil_adi=stil, notu=notu, motion_seviye=motion_seviye, aralik=aralik)
    kurgu_dosya = kurgu.yol(p.work)
    once = kurgu_dosya.read_text(encoding="utf-8")
    eski = Kurgu.model_validate_json(once)
    _, oturum = ajan_cagri.dosyadan(istek, motor=motor, model=model)
    if not aralik:
        # ADR 0064: ajanın yazdığı brif doğrulanır ve isteğe damgalanır; geçersiz brif edit'i durdurmaz.
        print("  Yaratıcı brif: " + ("yazıldı" if yaratici.damgala(p.work, notu) else "yok ya da geçersiz"), flush=True)

    hatalar = _hatalar(p, eski, aralik)
    # WHY: bkz. wiki/decisions/0036-motion-kutuphanesi-ve-ajanlar.md. Yoğunluk hata değil uyarıdır: bir ek tur ister, kurguyu geri aldırmaz.
    hedef_sn = None if aralik else _yogunluk_hedefi(p, motion_seviye)  # yoğunluk turu aralığın dışına grafik ekletirdi
    enerji = None if aralik else _enerji_dilimleri(p.work, notu)
    seyrek = [] if hatalar or not hedef_sn else kurgu.motion_yogunlugu(kurgu.oku(p.work), hedef_sn, enerji=enerji)
    if not hatalar and not aralik:
        # WHY: ADR 0040. Okunamayan kısa yazı ve art arda aynı geçiş/efekt/grafik aynı ek turda düzeltilir.
        from . import kurgu_kalite
        from . import tema_token
        kk = kurgu.oku(p.work)
        seyrek += [f"{u['bas']:.2f} sn {u['kod']}: {u['kanit']}. {u['oneri']}"
                   for u in kurgu_kalite.uyarilar(kk, tema_token.oku(kurgu.etkin_tema(p, kk.motion_tema)), p=p)]
    if seyrek:
        # WHY: bkz. wiki/decisions/0064-yaratici-yon.md. Seyreklikte dolgu grafik istenmez; sakin bölüm raporda gerekçelenir.
        ajan_cagri.calistir(
            f"{kurgu_dosya.resolve()} geçerli, ama şunlar düzelmeli (motion yoğunluğu ve kalite):\n" + "\n".join(f"- {u}" for u in seyrek)
            + "\nBu aralıklara söze bağlı grafik ekle YA DA aralık brifte sakin bölümse raporda gerekçelendir; dolgu grafik koyma "
              "(motion metin, sahne, kütüphane klibi, şablon ya da hazır efekt). Kesimlere ve mevcut kliplere dokunma. "
              "Dosyayı kaydet. Kabuk komutu çalıştırma.",
            motor=motor, model=model, oturum=oturum)
        hatalar = _hatalar(p, eski, aralik)
    if hatalar:
        duzelt = (
            f"{kurgu_dosya.resolve()} dosyasında şu hatalar bulundu:\n"
            + "\n".join(f"- {h}" for h in hatalar)
            + "\nDosyayı şemaya ve kurallara uygun biçimde düzeltip kaydet. Kabuk komutu çalıştırma."
        )
        ajan_cagri.calistir(duzelt, motor=motor, model=model, oturum=oturum)
        hatalar = _hatalar(p, eski, aralik)
    if hatalar:
        kurgu._atomik(kurgu_dosya, once)
        raise SystemExit("AI edit geçersiz kurgu yazdı, eski kurgu geri yüklendi: " + "; ".join(hatalar))

    yeni = kurgu.oku(p.work)
    if [c.model_dump() for c in yeni.klipler] == [c.model_dump() for c in eski.klipler]:
        kurgu._atomik(kurgu_dosya, once)
        raise SystemExit("AI edit yapmadı: kurgu.json değişmedi. İsteği veya girdi videolarını kontrol et.")

    kurgu._atomik(kurgu_dosya, once)
    kurgu.motion_bagla(p, yeni)  # şablon webm'leri üretilir, kaynakları kurguya yazılır: Stüdyo önizlemesi de görür
    fizik.bagla(p, yeni)  # fizik sahneleri bake edilir, Stüdyo önizlemesi aynı JSON'u okur (ADR 0039)
    karakter.bagla(p, yeni)
    yeni = kurgu.yaz(p.work, yeni)
    for u in (kurgu.motion_yogunlugu(yeni, hedef_sn, enerji=enerji) if hedef_sn else []):
        print(f"  ! {u}")

    eski_sure = max((c.bas + c.sure for c in eski.klipler), default=0.0)
    yeni_sure = max((c.bas + c.sure for c in yeni.klipler), default=0.0)
    print(f"AI Edit: {len(eski.klipler)} -> {len(yeni.klipler)} klip · {eski_sure:.1f}s -> {yeni_sure:.1f}s · rev {yeni.rev}")
    rapor = p.work / "edit" / "ai-edit.rapor.md"
    # Stüdyo AI paneli önce/sonra kartını ve "Geri al"ı bundan kurar; önceki sürüm kurgu-gecmis/<rev>.json'dadır.
    (p.work / "edit" / "ai-edit.ozet.json").write_text(json.dumps({
        "once_rev": eski.rev, "rev": yeni.rev, "klip": [len(eski.klipler), len(yeni.klipler)],
        "sure": [round(eski_sure, 2), round(yeni_sure, 2)], "aralik": aralik,
    }), encoding="utf-8")
    if rapor.exists():
        print(f"Rapor: {paths.rel(rapor)}")
        for satir in rapor.read_text(encoding="utf-8", errors="replace").splitlines()[:30]:
            print(f"  {satir}")

    hizli.taslak(p)
    if final:
        hizli.final(p, **(final_ek or {}))
