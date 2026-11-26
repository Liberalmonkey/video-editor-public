"""Kurgu düzeyinde kalite uyarıları: okunamayacak kadar kısa yazı, ekran yazısında emoji, art arda aynı geçiş, efekt ya da grafik.

WHY: bkz. wiki/decisions/0040-ikinci-repo-dalgasi.md. ai-edit isteğinde "aynı türü art arda 3 kez kullanma" kuralı vardı
ama ölçülmüyordu (saas-motion-kit variety_audit fikri). Yazı süresi open-edit'in (Apache-2.0) okuma süresi formülünden:
kelime başına 0,2 sn + taban; kapanış kartında taban daha uzun. Uyarıdır, render'ı durdurmaz (denetle hata verir).
"""
from __future__ import annotations

import re
from . import native_motion

# Ekran yazısında emoji: Avenox yasak listesinden (neon, mor gradyan, parlama, emoji işi ucuz gösterir). Ölçülebilen tek
# kalem emoji; palet ve parlama bitmiş videoda `slop` ölçümündedir. WHY: bkz. wiki/decisions/0041-avenox-kurgu-dersleri.md
# ✓ ve oklar gibi tipografik işaretler emoji sayılmaz; yalnız resimli emoji blokları ve tek tek emoji dingbat'ları.
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-⛿✅❌✨❓❗⭐]")

KELIME_SN = 0.2
TABAN_SN = 1.0          # ara yazı: göz yazıyı bulur ve okur
KAPANIS_TABAN_SN = 2.0  # son kart (CTA, kapanış): okunur ve üstünde bir an durulur
ART_ARDA = 3


def _kelime(metin: str) -> int:
    return len(re.findall(r"\w+", metin or "", flags=re.UNICODE))


def _yazi(c) -> str:
    """Klibin ekranda okunan yazısı: metin klibi ya da şablon parametrelerindeki metinler."""
    if c.tur == "metin":
        m = c.metin_stil or {}
        return " ".join(str(x) for x in (c.metin, m.get("baslik"), m.get("alt")) if x)
    if c.tur == "motion" and (c.sablon or c.hf):
        return " ".join(str(v) for v in ((c.sablon or c.hf).get("param") or {}).values() if isinstance(v, str))
    return ""


HEX = re.compile(r"#[0-9A-Fa-f]{6}")
STIL_DISI_DE = 14.0  # ΔE76; bunun üstü göze "başka renk" gelir


def _lab(h: str) -> tuple[float, float, float]:
    def d(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (d(int(h[i:i + 2], 16)) for i in (1, 3, 5))
    x, y, z = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047, 0.2126 * r + 0.7152 * g + 0.0722 * b, (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = [t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116 for t in (x, y, z)]
    return 116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])


def stil_disi(renk: str, palet: list[str]) -> float:
    """Rengin paletteki en yakın renge ΔE76 uzaklığı."""
    a = _lab(renk)
    return min(sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5 for b in map(_lab, palet))


def palet(t) -> list[str]:
    r, a = t.renk, t.altyazi
    return [r.vurgu, r.ikincil, r.ikincil_yazi, r.zemin, r.yazi, r.soluk, r.olumlu, r.olumsuz, a.renk, a.aktif_renk, a.kontur_renk,
            "#FFFFFF", "#000000"]


def _stil_ayristir(yol: str) -> tuple[str, str] | None:
    if not isinstance(yol, str) or not yol.startswith("stil:"):
        return None
    parcalar = [x for x in yol.removeprefix("stil:").replace("\\", "/").split("/") if x]
    return (parcalar[0], parcalar[1]) if len(parcalar) >= 2 else None


def _klip_stil_yollari(k, c) -> list[str]:
    yollar: list[str] = []
    if c.kaynak and c.kaynak in k.kaynaklar:
        yollar.append(k.kaynaklar[c.kaynak].yol)
    if c.bilesen and isinstance(c.bilesen.param, dict):
        d = c.bilesen.param.get("dosya")
        if isinstance(d, str):
            yollar.append(d)
    if c.tur == "sahne" and isinstance(c.sahne, dict):
        for s in (c.sahne, c.sahne.get("shot")):
            if isinstance(s, dict) and isinstance(s.get("img"), str):
                img = s["img"]
                yollar.append(k.kaynaklar[img].yol if img in k.kaynaklar else img)
    return [y for y in yollar if isinstance(y, str) and y.startswith("stil:")]


def uyarilar(k, tema=None, *, p=None, aktif_stil: str | None = None, stil: str | None = None, studyo: str | None = None) -> list[dict]:
    """tema: etkin stilin token'ı (tema_token.Tokens); verilirse klip renkleri stile göre denetlenir (ADR 0043)."""
    if tema is not None and hasattr(tema, "studyo") and hasattr(tema, "work"):
        p, tema = tema, None
    elif isinstance(tema, str):
        aktif_stil, tema = aktif_stil or tema, None

    etkin_studyo = studyo or (getattr(p, "studyo", None) if p is not None else None)
    etkin_stil = aktif_stil or stil
    if etkin_stil and "/" in etkin_stil:
        etkin_studyo, etkin_stil = etkin_stil.split("/", 1)
    elif not etkin_stil and p is not None:
        from . import stil as stil_mod

        try:
            etkin_stil = stil_mod.secili_adi(p)
        except Exception:
            etkin_stil = None
    elif not etkin_stil and tema is not None and getattr(tema, "ad", None):
        tad = tema.ad
        if tad.startswith("paket-") and tad.count("-") >= 2:
            _, etkin_studyo, etkin_stil = tad.split("-", 2)
        elif tad not in ("varsayilan", "proje"):
            etkin_stil = tad

    gizli = {i.id for i in k.izler if i.gizli}
    klipler = sorted((c for c in k.klipler if c.iz not in gizli), key=lambda c: c.bas)
    bitis = max((c.bas + c.sure for c in klipler), default=0.0)
    out: list[dict] = []

    def ekle(kod, bas, kanit, oneri, klip=None):
        out.append({"kod": kod, "seviye": "P2", "bas": round(bas, 2), "kanit": kanit, "oneri": oneri, **({"klip": klip} if klip else {})})

    kullanilan_kaynaklar = {c.kaynak for c in klipler if c.kaynak}
    stil_kayitlari: list[tuple[str, float, str]] = []
    for c in klipler:
        for y in _klip_stil_yollari(k, c):
            stil_kayitlari.append((c.id, c.bas, y))
    for kid, kay in k.kaynaklar.items():
        if kid not in kullanilan_kaynaklar and kay.yol.startswith("stil:"):
            stil_kayitlari.append((kid, 0.0, kay.yol))

    ilk_stil: tuple[str, str] | None = None
    for nesne_id, bas, y in stil_kayitlari:
        ay = _stil_ayristir(y)
        if not ay:
            continue
        s2, ad2 = ay
        if etkin_stil:
            if ad2 != etkin_stil or (etkin_studyo and s2 != etkin_studyo):
                ekle(
                    "STIL_VARLIK_UYUMSUZ",
                    bas,
                    f"{nesne_id}: '{y}' kaynağı aktif stil '{etkin_stil}' yerine '{s2}/{ad2}' stiline ait",
                    f"Başka stilin varlığını kullanma; yalnız aktif stilin ('{etkin_stil}') varlıklarını seç",
                )
        else:
            if ilk_stil is None:
                ilk_stil = (s2, ad2)
            elif (s2, ad2) != ilk_stil:
                ekle(
                    "STIL_VARLIK_UYUMSUZ",
                    bas,
                    f"{nesne_id}: '{y}' kaynağı '{ilk_stil[0]}/{ilk_stil[1]}' yerine '{s2}/{ad2}' stiline ait",
                    "Tek kurguda farklı stillerin özel varlıklarını karıştırma",
                )

    for c in klipler:
        yazi = _yazi(c)
        if e := EMOJI.findall(yazi):
            ekle("YAZI_EMOJI", c.bas, f"{c.id}: ekran yazısında emoji ({''.join(dict.fromkeys(e))})",
                 "Emojiyi sil; vurgu gerekiyorsa ikon ya da motion klip kullan (Avenox yasak listesi)")
        n = _kelime(yazi)
        if not n:
            continue
        kapanis = c.bas + c.sure >= bitis - 0.05
        gerek = n * KELIME_SN + (KAPANIS_TABAN_SN if kapanis else TABAN_SN)
        if c.sure + 1e-3 < gerek:
            ekle("YAZI_KISA", c.bas, f"{c.id}: {n} kelime {c.sure:.1f} sn ekranda; okumak için en az {gerek:.1f} sn",
                 "Yazıyı kısalt ya da klibi uzat" + ("; kapanış kartı sonunda bir an durmalı" if kapanis else ""))

    if tema is not None:
        # WHY: bkz. wiki/decisions/0043-stile-bagli-tema-tokenlari.md. Klip başına renk istisnadır; stilin paletinden
        # uzak renk (ör. koyu zeminde okunmayan yeşil) seçili stille çatışır.
        pal = palet(tema)
        for c in klipler:
            kaynaklar = (list((c.metin_stil or {}).items()) + list(((c.sablon or {}).get("param") or {}).items())
                         + list(((c.hf or {}).get("param") or {}).items()))
            for ad, v in kaynaklar:
                if isinstance(v, str) and HEX.fullmatch(v) and (de := stil_disi(v, pal)) > STIL_DISI_DE:
                    ekle("STIL_DISI_RENK", c.bas, f"{c.id}: {ad} {v} stilin paletinde yok (ΔE {de:.0f})",
                         f"Alanı sil, stilin rengi gelsin ({tema.ad}: vurgu {tema.renk.vurgu}, ikincil {tema.renk.ikincil})")

    def tekrar(adlar: list[tuple[float, str, str]], kod: str, ne: str, oneri: str):
        # WHY: bkz. wiki/decisions/0058-hizli-ve-kaliteli-edit.md. Kanıt serinin üçüncü klibini adlandırır; ekip kapısı
        # uyarıyı klip sahibine yollayabilsin (eskiden sahipsiz kalıyor, kimse düzeltmiyordu).
        seri, onceki = 0, None
        for bas, ad, kid in adlar:
            seri = seri + 1 if ad == onceki else 1
            onceki = ad
            if seri == ART_ARDA:
                ekle(kod, bas, f"{ART_ARDA} kez art arda aynı {ne}: {ad} ({kid})", oneri, klip=kid)

    tekrar([(c.bas, f"{c.gecis_giris.tur}/{getattr(c.gecis_giris, 'yon', '')}", c.id) for c in klipler if c.gecis_giris],
           "GECIS_TEKRAR", "geçiş", "Birini düz kesime ya da başka yöne çevir; özel geçiş yalnız konu değişiminde")
    tekrar(sorted(((c.bas + (e.get("t") or 0), e.get("ad", ""), c.id) for c in klipler for e in c.hazir), key=lambda x: x[0]),
           "EFEKT_TEKRAR", "hazır efekt", "Aynı efekti üçüncü kez kullanma; vurguyu başka araçla ver ya da sil")
    grafik = []
    for c in klipler:
        if c.tur == "motion":
            grafik.append((c.bas, (c.bilesen.ad if c.bilesen else None) or (f"hf:{c.hf['ad']}" if c.hf else None)
                           or (c.sablon or {}).get("ad") or c.kaynak or "motion", c.id))
        elif c.tur == "sahne" and (c.sahne or {}).get("kind"):
            grafik.append((c.bas, f"sahne:{c.sahne['kind']}", c.id))
        elif (c.metin_stil or {}).get("tip"):
            grafik.append((c.bas, f"metin:{c.metin_stil['tip']}", c.id))
    tekrar(grafik, "GRAFIK_TEKRAR", "grafik", "Arka arkaya üç aynı grafik şablon gibi durur; birini başka türle değiştir")

    # WHY: bkz. wiki/decisions/0045-native-motion.md ve ADR 0062. Native + HF grafik zanaat kapıları.
    from . import gecis_donustur
    for c in klipler:
        if ad := gecis_donustur.eski_gecis_adi(k, c):
            ekle("ESKI_GECIS", c.bas, f"{c.id}: gecis-{ad} bindirmesi kareyi düz renkle örtüyor, sonraki çekim görünmüyor",
                 "V1 kesim geçişine çevir: vedit kurgu-gecis <proje> --uygula (sil, kay, saat, iris, kirbac, isik, piksel, zoom_kirbac, film_yanigi, bolunme, bozulma, yirtma, tikla_iris, buton_zoom, kart_dunyaya, bulanik_takas, dip_kesim)")
    native = [c for c in klipler if c.tur == "motion" and c.bilesen]
    hf_klipler = [c for c in klipler if c.tur == "motion" and c.hf]
    kayit = native_motion.kayitlar()
    for c in native:
        if u := native_motion.sure_uyarisi(c):
            ekle("MOTION_SURE", c.bas, u, "Süreyi bileşenin sınırına çek: ikon 1-1.6 sn, alt bant 2.5-4 sn, kart en çok 3 sn, tipografi 0.8-5 sn")
    for a, b in zip(native, native[1:]):
        if a.bilesen.ad == b.bilesen.ad:
            ekle("MOTION_ART_ARDA", b.bas, f"{a.id} ve {b.id}: aynı grafik art arda ({b.bilesen.ad})",
                 "İkinciyi başka bir grafikle değiştir ya da sil", klip=b.id)
    for a, b in zip(hf_klipler, hf_klipler[1:]):
        if a.hf.get("ad") == b.hf.get("ad"):
            ekle("MOTION_ART_ARDA", b.bas, f"{a.id} ve {b.id}: aynı HyperFrames grafiği art arda ({b.hf.get('ad')})",
                 "İkinciyi başka bir HyperFrames şablonuyla değiştir ya da sil", klip=b.id)
    # WHY: bkz. wiki/specs/hf-canli-gomme-ve-dikey-duzen.md. Dikeyde anlamsız olduğu işaretlenen sahne 9:16 kurguda uyarılır.
    if k.sekans.h > k.sekans.w:
        from . import hf_grafik
        for c in hf_klipler:
            d = hf_grafik.bul(str(c.hf.get("ad") or ""), getattr(p, "work", None) if p is not None else None)
            if d and hf_grafik.meta_bilgi(d).get("yalniz_yatay"):
                ekle("HF_YALNIZ_YATAY", c.bas, f"{c.id}: `{c.hf.get('ad')}` yalnız yatay için tasarlandı, 9:16'da okunmaz",
                     "Dikey düzeni olan bir kompozisyon ya da native bileşen seç", klip=c.id)

    # ADR 0063: three.js sahnesi pahalı ve göz yorar; videoda en çok 2, art arda değil.
    uc_klipler = [c for c in hf_klipler if str(c.hf.get("ad", "")).startswith("uc-")]
    if len(uc_klipler) > UC_TAVAN:
        fazla = uc_klipler[UC_TAVAN]
        ekle("UC_FAZLA", fazla.bas, f"{len(uc_klipler)} three.js 3D sahnesi var (tavan {UC_TAVAN}): "
             + ", ".join(c.id for c in uc_klipler), "3D'yi açılış, kapanış ya da ürün anına bırak; kalanları 2D şablona çevir", klip=fazla.id)
    for a, b in zip(uc_klipler, uc_klipler[1:]):
        if b.bas - (a.bas + a.sure) < UC_ARA_SN:
            ekle("UC_ART_ARDA", b.bas, f"{a.id} ve {b.id}: iki 3D sahne {UC_ARA_SN:g} sn içinde",
                 "Aralarına 2D grafik ya da sade konuşma koy, ya da birini 2D şablona çevir", klip=b.id)

    def hero(c) -> bool:
        return c.bilesen.hero if c.bilesen.hero is not None else bool((kayit.get(c.bilesen.ad) or {}).get("meta", {}).get("hero"))

    herolar = [c for c in native if hero(c)]
    for a in herolar:
        for b in herolar:
            if a.bas < b.bas < a.bas + a.sure - 1e-3:
                ekle("HERO_CAKISMA", b.bas, f"{a.id} ile {b.id}: aynı anda iki ana grafik",
                     "Biri bitmeden öbürü girmesin; ekranda tek hero")

    # 4-Düzen yüz hijyeni (ADR 0062): tam-yüz konuşmacı üstüne 6 sn içinde 3+ tam/orta kart yığılması.
    konusmaci_aralik = [(c.bas, c.bas + c.sure) for c in klipler if c.konusmaci and c.tur == "video"]
    pip_aralik = [(c.bas, c.bas + c.sure) for c in klipler if c.tur == "sahne"
                  and ((c.sahne or {}).get("layout") == "split" or (c.sahne or {}).get("duzen") in ("diyagram-pip", "ekran-pip"))]
    if konusmaci_aralik:
        kartlar = [c for c in klipler if c.tur == "motion" and (c.hf or (c.bilesen and (c.bilesen.yer in ("orta", "tam"))))
                   and any(a <= c.bas < b for a, b in konusmaci_aralik)
                   and not any(a <= c.bas < b for a, b in pip_aralik)]
        for i in range(len(kartlar) - 2):
            if kartlar[i + 2].bas - kartlar[i].bas <= 6.0:
                ekle("YUZ_USTU_KART", kartlar[i + 2].bas,
                     f"{kartlar[i].id}, {kartlar[i + 1].id}, {kartlar[i + 2].id}: 6 sn içinde tam-yüz konuşmacı üstüne 3 kart yığıldı",
                     "4-düzen rotasyonuna geç: diyagram-pip veya ekran-pip ile konuşmacıyı köşeye çek (Nick Saraev kuralı)",
                     klip=kartlar[i + 2].id)
                break
    return sorted(out, key=lambda b: b["bas"])


UC_TAVAN = 2  # ADR 0063
UC_ARA_SN = 8.0

_YASAK_DETERMINIZM = (
    (re.compile(r"\bMath\.random\s*\("), "tohumsuz Math.random() yasak; mulberry32 tohumlu üreteç kullan"),
    (re.compile(r"\bDate\.now\s*\("), "Date.now() yasak; her kare yalnız timeline zamanı t'nin fonksiyonu olmalı"),
    (re.compile(r"\brequestAnimationFrame\s*\("), "requestAnimationFrame() yasak; tek paused GSAP timeline kullan"),
    (re.compile(r"\bset(?:Timeout|Interval)\s*\("), "setTimeout/setInterval yasak; zamanlayıcı determinizmi bozar"),
    (re.compile(r"@keyframes\b"), "CSS @keyframes yasak; tüm hareket GSAP timeline içinde olmalı"),
    (re.compile(r"repeat\s*:\s*-1\b"), "GSAP repeat:-1 yasak; sonlu ve deterministik süre yaz"),
    # three.js (ADR 0063): kare yalnız hf-seek zamanından; saat ve döngü yok.
    (re.compile(r"\bTHREE\.Clock\b|\bnew\s+Clock\s*\("), "THREE.Clock yasak; zamanı hf-seek olayından al (HFUC.sur)"),
    (re.compile(r"\bsetAnimationLoop\s*\("), "renderer.setAnimationLoop yasak; çizim yalnız HFUC.sur içinde"),
    (re.compile(r"\bperformance\.now\s*\("), "performance.now() yasak; kare yalnız zaman t'nin fonksiyonu olmalı"),
    (re.compile(r"\bScrambleText"), "ScrambleText pakette yok (tohumsuz rastgele); tohumlu karıştırma yaz"),
)


def hf_determinizm_hatalari(html: str) -> list[str]:
    """HyperFrames determinizm & Anti-Slop statik kapısı (ADR 0050, 0062)."""
    hatalar = [mesaj for desen, mesaj in _YASAK_DETERMINIZM if desen.search(html)]
    if "HFUC.sur" in html and "window.__timelines" not in html:
        hatalar.append("three.js sahnesi de GSAP timeline'ını window.__timelines'a kaydetmeli (süre ve DOM katmanı)")
    if "window.__timelines" not in html and "HFN.sahne" not in html:
        hatalar.append("window.__timelines kaydı yok (paused GSAP timeline zorunlu)")
    return hatalar
