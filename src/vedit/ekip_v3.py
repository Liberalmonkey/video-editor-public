"""Ekip motoru v3: seviyeli ekip, orkestratör, kapılı paralel akış (ADR 0053).

WHY: v2 (ADR 0048) sabit 3 editör + 3 kalite kontrol çalıştırıyordu ve kural uyumunu kimse denetlemiyordu. v3'te seviye
ajan sayısını sabitler (low 2E+1K … max 10E+5K); işi orkestratör (O) dağıtır, kuralları atar ve kapılarda denetler.
Her kapı bir bariyerdir, paralel işler orada buluşur:
  G0 plan        : O tek çağrı: hook, görev kartları (katman × zaman dilimi), karta zorunlu kurallar. Geçersiz plan: sabit tablo
  G1 düzen       : N editör aynı anda; her biri yalnız kendi kartının katmanına ve aralığına fark yaması yazar
  G2 kural kapısı: deterministik (sahiplik, şema, kural_uyum, deneme birleştirmesinde denetim) + O tek çağrı: kabul ya da düzelt;
                   düzelt alan editör bir kez, paralel düzeltir
  G3 birleştir   : deterministik birleştirme (ADR 0048 kuralları), tek render
  G4 QC          : M kalite kontrol aynı anda, ortak kare/ölçüm paketiyle
  G5 triyaj      : O yanlış pozitifi atar, kural adaylarını onaylar; vedit kural deposuna işler ve depoda olduğunu doğrular
  G6 düzeltme    : yalnız P0/P1 sahibi, bulgu farkı + yeni kurallarla, bir kez; etkilenen aralık yeniden render edilir
  G7 son         : deterministik denetim; ikinci QC yalnız P0 kalırsa ya da istenirse
"""

from __future__ import annotations

import copy
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pydantic import BaseModel, ValidationError

from . import (aiedit, capa, ekip, hizli, kural, kurgu, kurgu_kalite, muzik_once, native_motion, paths, suru, tema_denetim, tema_token,
               yaratici, yuz_bolge)
from .ekip_sema import (BOLUNMEZ, EDITOR_ROL_DOSYASI, KATMAN_ADI, KATMAN_TANIM, KATMANLAR, KK_ALAN, KK_KURAL_ROLU, KK_ROL_ADI,
                        KK_ROL_DOSYASI, KURAL_ROLU, ORKESTRATOR, SEVIYE, EkipAyar, Gorev, KapiCikti, KkGorev, KontrolCikti, Mesaj, Plan,
                        Triyaj, Yama, editorler, kontroller)
from .schemas import Kurgu

ROL_KLASORU = ekip.ROL_KLASORU
KAPILAR = [("G0", "Plan"), ("G1", "Düzen"), ("G2", "Kural kapısı"), ("G3", "Birleştir"), ("G4", "QC"), ("G5", "Triyaj ve kural"),
           ("G6", "Düzeltme"), ("G7", "Son")]
O_ROL = ("ekip-orkestrator",)
QC_TEK_KARE = 6  # QC'nin paftadan sonra açacağı en çok tek kare (ADR 0054)
ZORUNLU_EN_COK = 8  # karta atanan kural sayısı üst sınırı (P0'lar her zaman girer; WHY: bkz. wiki/decisions/0064-yaratici-yon.md)


def _no(slot: str) -> int:
    return int(slot[1:]) if slot[1:].isdigit() else 0


# ---------------------------------------------------------------- katman ve atama

def _al(c, ad: str):
    return c.get(ad) if isinstance(c, dict) else getattr(c, ad, None)


def _muzik_izi(k: Kurgu, iz: str) -> bool:
    i = next((x for x in k.izler if x.id == iz), None)
    if i is None or i.tur != "ses":
        return False
    if "muzik" in (i.ad or "").lower().replace("ü", "u"):
        return True
    return any((c.olay or {}).get("muzik") for c in k.klipler if c.iz == iz)


def katman_sinifi(k: Kurgu, iz: str, klip=None) -> str | None:
    """İz ve klipten katman sınıfı: kurgu (V1, A1), grafik (diğer görüntü), muzik, sfx. Bilinmeyen iz: None."""
    if iz in ("V1", "A1"):
        return "kurgu"
    tur = next((i.tur for i in k.izler if i.id == iz), None)
    if tur is None:
        return None
    if tur == "video":
        return "grafik"
    if (_al(klip, "olay") or {}).get("muzik") or _muzik_izi(k, iz):
        return "muzik"
    return "sfx"


class Atama:
    """Görev kartlarından sahiplik: katman sınıfı + klibin taban zaman çizelgesindeki başlangıcı → editör slotu."""

    def __init__(self, gorevler: list[Gorev]):
        self.gorevler: dict[str, Gorev] = {g.slot: g for g in sorted(gorevler, key=lambda g: _no(g.slot))}
        self.klip: dict[str, str] = {}

    @classmethod
    def uc(cls) -> Atama:
        """Klasik üçlü (ADR 0048): E1 kurgu, E2 grafik, E3 ses ve stil."""
        return cls([Gorev(slot="E1", katmanlar=["kurgu"]), Gorev(slot="E2", katmanlar=["grafik"]),
                    Gorev(slot="E3", katmanlar=["sfx", "muzik", "stil"])])

    def kurgu_sahibi(self) -> str:
        return next(s for s, g in self.gorevler.items() if "kurgu" in g.katmanlar)

    def katmanlar(self, slot: str) -> list[str]:
        g = self.gorevler.get(slot)
        return list(g.katmanlar) if g else []

    def katman_sahibi(self, sinif: str | None, t: float | None = None) -> str | None:
        adaylar = sorted((g for g in self.gorevler.values() if sinif in g.katmanlar), key=lambda g: (g.aralik or [0, 0])[0])
        if not adaylar:
            return None
        if len(adaylar) == 1 or t is None:
            return adaylar[0].slot
        for g in adaylar:
            if g.aralik is None or g.aralik[0] - 1e-6 <= t < g.aralik[1]:
                return g.slot
        return adaylar[-1].slot if t >= (adaylar[-1].aralik or [0, 0])[0] else adaylar[0].slot

    def bagla(self, k: Kurgu) -> None:
        """Mevcut kliplerin sahibi taban zaman çizelgesinde bir kez belirlenir; birleştirme sırasında kaymaz."""
        self.klip = {c.id: s for c in k.klipler if (s := self.katman_sahibi(katman_sinifi(k, c.iz, c), c.bas))}

    def sahip(self, k: Kurgu, c) -> str | None:
        return self.klip.get(_al(c, "id")) or self.katman_sahibi(katman_sinifi(k, _al(c, "iz") or "", c), _al(c, "bas"))

    def kural_rolu(self, slot: str | None, katman: str | None = None) -> str:
        """Editör slotu (E1..E10) → kural deposunun rol sınıfı (E1 kurgu, E2 grafik, E3 ses ve stil, ya da hepsi).

        Slot seviyeye göre değişir (medium'da ses-stil E4); depo yalnız rol sınıfını tanır. Slot birden çok sınıf
        taşıyorsa (low'da E2 grafik + ses) bulgunun katman sınıfı seçer; yine belirsizse ya da slot bilinmiyorsa: hepsi."""
        # WHY: bkz. wiki/decisions/0053-seviyeli-ekip-orkestrator.md — slot ve rol sınıfı ayrı kavramlar.
        sinif = {KURAL_ROLU[x] for x in self.katmanlar(slot)} if slot else set()
        if len(sinif) == 1:
            return sinif.pop()
        return KURAL_ROLU[katman] if katman in KURAL_ROLU and KURAL_ROLU[katman] in sinif else "hepsi"

    def alanlar(self, slot: str) -> set[str]:
        ks = self.katmanlar(slot)
        return ({"isaretler", "hook"} if "kurgu" in ks else set()) | ({"altyazi", "motion_tema"} if "stil" in ks else set())

    def etiket(self, slot: str) -> str:
        g = self.gorevler[slot]
        ar = f" · {g.aralik[0]:.1f}–{g.aralik[1]:.1f} sn" if g.aralik else ""
        return f"{slot} · {', '.join(KATMAN_ADI[x] for x in g.katmanlar)}{ar}"

    def tablo(self) -> list[str]:
        return [f"- {self.etiket(s)}" for s in self.gorevler]


def sahip(k: Kurgu, iz: str, atama: Atama | None = None) -> str | None:
    """Uyum: izin klasik sahibi (aralıksız)."""
    return (atama or Atama.uc()).katman_sahibi(katman_sinifi(k, iz))


# ---------------------------------------------------------------- yama denetimi ve uygulama

HF_EN_BUYUK = 200_000  # bayt; tek kompozisyon HTML'i


def hf_hatalari(rol: str, y: Yama, atama: Atama | None = None) -> list[str]:
    """`hf` alanı yalnız grafik katmanının sahibinindir; ad kök dışına çıkamaz, içerik HTML kompozisyonudur (ADR 0050)."""
    h = []
    if y.hf and "grafik" not in (atama or Atama.uc()).katmanlar(rol):
        h.append(f"{rol}: hf alanı bu editörün değil")
    for ad, html in y.hf.items():
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", ad):
            h.append(f"{rol}: geçersiz kompozisyon adı '{ad}'")
        elif len(html.encode("utf-8")) > HF_EN_BUYUK or "data-composition-id" not in html:
            h.append(f"{rol}: {ad} geçerli bir HyperFrames kompozisyonu değil (data-composition-id yok ya da çok büyük)")
        elif v := tema_denetim.ihlaller(html, kaynak=ad):
            # WHY: bkz. wiki/decisions/0058-hizli-ve-kaliteli-edit.md. Ajanın kendi kompozisyonu stilin token'ını okur (ADR 0043).
            h.append(f"{rol}: {tema_denetim.mesaj(v)}")
        elif det := [m for d, m in kurgu_kalite._YASAK_DETERMINIZM if d.search(html)]:
            h.append(f"{rol}: {ad} determinizm ihlali: {'; '.join(det[:3])}")
    for c in [*y.ekle, *y.guncelle]:
        for alan in ("hf", "sablon"):
            if isinstance(c, dict) and isinstance(c.get(alan), dict) and (v := tema_denetim.param_ihlalleri(c[alan].get("param"), kaynak=str(c.get("id")))):
                h.append(f"{rol}: {tema_denetim.mesaj(v)}")
    return h


def hf_ad_ayir(rol: str, y: Yama, atama: Atama) -> Yama:
    """Birden çok grafik editörü varken yeni kompozisyon adına slot eki koyar (`baslik` → `baslik-e3`), klip başvurularını da.

    WHY: grafik editörleri aynı anda yazar (max'ta beş); ikisi aynı adı seçince `work/edit/hf/<ad>/` son yazanınki olur ve
    öteki editörün klibi yanlış kompozisyonla render edilir. Ek zaten varsa ad değişmez (düzeltme turunda aynı ad korunur)."""
    if not y.hf or sum("grafik" in g.katmanlar for g in atama.gorevler.values()) < 2:
        return y
    ek = f"-{rol.lower()}"
    harita = {ad: ad if ad.endswith(ek) else ad[:48 - len(ek)] + ek for ad in y.hf}
    if all(a == b for a, b in harita.items()):
        return y
    y.hf = {harita[ad]: html for ad, html in y.hf.items()}
    for c in [*y.ekle, *y.guncelle]:
        hf = c.get("hf") if isinstance(c, dict) else None
        if isinstance(hf, dict) and hf.get("ad") in harita:
            hf["ad"] = harita[hf["ad"]]
    return y


def hf_yaz(p, rol: str, y: Yama, atama: Atama | None = None) -> list[str]:
    """Grafik editörünün döndürdüğü kompozisyonları `work/edit/hf/<ad>/index.html` olarak yazar; yazılan adları döner."""
    from . import hf_grafik
    yazilan = []
    if hf_hatalari(rol, y, atama):
        return yazilan
    for ad, html in y.hf.items():
        f = hf_grafik.proje_kok(p.work) / ad / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html, encoding="utf-8")
        yazilan.append(ad)
    return yazilan


def _capa_bas(k: Kurgu, c: dict) -> float | None:
    """`bas` yazılmamış çapalı klibin sekans zamanı (çapa kelimesinden, `once_kare` önce)."""
    ca = c.get("capa") or {}
    kel = k.kelimeler.get(ca.get("kaynak") or "") or []
    i = ca.get("kelime")
    t = kel[i].s if isinstance(i, int) and 0 <= i < len(kel) else ca.get("t")
    if t is None or not ca.get("kaynak"):
        return None
    s = capa.sekans_zamani(k, ca["kaynak"], t)
    return None if s is None else round(max(0.0, s - (ca.get("once_kare") or 0) / k.sekans.fps), 3)


def yama_hatalari(k: Kurgu, rol: str, y: Yama, atama: Atama | None = None) -> tuple[list[str], list[str]]:
    """(yamayı düşüren hatalar, aralık dışına eklenen öğeler). Başka katmana yazmak yamayı düşürür; aralık dışı öğe tek başına düşer."""
    atama = atama or Atama.uc()
    var = {c.id: c for c in k.klipler}
    benim = set(atama.katmanlar(rol))
    h, disari = [], []
    for c in y.ekle:
        if not isinstance(c, dict) or not c.get("id"):
            continue  # id'siz öğe yamayı düşürmez; yama_uygula öğeyi düşürür (ADR 0059)
        if c.get("id") in var:
            h.append(f"{rol}: {c.get('id')} zaten var (ekle değil guncelle)")
        sinif = katman_sinifi(k, c.get("iz", ""), c)
        if sinif is None:
            continue  # bilinmeyen iz: şema öğeyi düşürür
        if sinif not in benim:
            h.append(f"{rol}: {c.get('id')} {c.get('iz')} izine eklenemez (sahibi {atama.katman_sahibi(sinif)})")
            continue
        t = c.get("bas") if isinstance(c.get("bas"), (int, float)) else (_capa_bas(k, c) if c.get("capa") else None)
        if t is not None and atama.katman_sahibi(sinif, t) != rol:
            disari.append(c.get("id"))
    for g in y.guncelle:
        if not isinstance(g, dict) or not g.get("id"):
            continue
        c = var.get(g.get("id"))
        if c is None:
            h.append(f"{rol}: güncellenecek {g.get('id')} yok")
        elif atama.sahip(k, c) != rol or ("iz" in g and katman_sinifi(k, g["iz"], {**c.model_dump(), **g}) not in benim):
            h.append(f"{rol}: {c.id} başka editörün nesnesi ({c.iz})")
    for kid in y.sil:
        c = var.get(kid)
        if c is not None and atama.sahip(k, c) != rol:
            h.append(f"{rol}: {kid} başka editörün nesnesi, silinemez")
    for alan in ("isaretler", "altyazi", "motion_tema", "hook"):
        if getattr(y, alan) is not None and alan not in atama.alanlar(rol):
            h.append(f"{rol}: {alan} alanı bu editörün değil")
    h += hf_hatalari(rol, y, atama)
    for kid, kay in y.kaynaklar.items():
        if kid in k.kaynaklar and k.kaynaklar[kid].model_dump() != {**k.kaynaklar[kid].model_dump(), **kay}:
            h.append(f"{rol}: mevcut kaynak değiştirilemez: {kid}")
    return h, disari


def _kurgu_dict(k: Kurgu, y: Yama, ekle: list[dict], gun: dict[str, dict], kaynaklar: dict) -> dict:
    d = k.model_dump()
    sil = set(y.sil)
    d["klipler"] = [{**c, **gun.get(c["id"], {})} for c in d["klipler"] if c["id"] not in sil] + ekle
    for kid, kay in kaynaklar.items():
        d["kaynaklar"].setdefault(kid, kay)
    for alan in ("isaretler", "altyazi", "motion_tema"):
        if getattr(y, alan) is not None:
            d[alan] = getattr(y, alan)
    return d


def yama_uygula(k: Kurgu, rol: str, y: Yama, dusen: list[str] | None = None, atama: Atama | None = None) -> Kurgu:
    """Sahiplik denetimli uygulama; sahiplik hatası SystemExit (yama birleşmez).
    Şema hatasında ya da aralık dışında yalnız o öğeler düşer, gerisi birleşir; düşenler `dusen` listesine yazılır."""
    # WHY: instagram/1 v2 koşularında tek bozuk öğe (kaynakta `dosya`, çapalı klipte `bas` yok) bütün E2/E3 katmanını düşürdü.
    # Başka editörün skaler alanı (ör. grafik editörünün motion_tema'sı) yamayı düşürmez; yalnız o alan düşer.
    atama = atama or Atama.uc()
    yabanci = [a for a in ("isaretler", "altyazi", "motion_tema", "hook") if getattr(y, a) is not None and a not in atama.alanlar(rol)]
    if yabanci:
        y = y.model_copy(update={a: None for a in yabanci})
    h, disari = yama_hatalari(k, rol, y, atama)
    if h:
        raise SystemExit("; ".join(h))
    # WHY: bkz. wiki/decisions/0059-swarm-edit.md. id'siz öğe (g4 koşusu, E4: `baslangic` alanlı ses olayları) birleştirmeyi
    # KeyError ile çökertiyordu; öğe düşer, kapı sahibine düzeltme yollar.
    idsiz = [c for c in y.ekle if not isinstance(c, dict) or not c.get("id")]
    ekle = [c for c in copy.deepcopy(list(y.ekle)) if isinstance(c, dict) and c.get("id") and c.get("id") not in disari]
    idsiz += [g for g in y.guncelle if not isinstance(g, dict) or not g.get("id")]
    if idsiz and dusen is not None:
        dusen += [f"{rol}:id'siz öğe ({str(c.get('tur') if isinstance(c, dict) else c)[:20]})" for c in idsiz]
    for c in ekle:
        if "bas" not in c and c.get("capa"):
            if (b := _capa_bas(k, c)) is not None:
                c["bas"] = b
        if "sure" not in c:
            if c.get("tur") == "motion" and isinstance(c.get("bilesen"), dict):
                m = (native_motion.kayitlar().get(c["bilesen"].get("ad")) or {}).get("meta", {})
                c["sure"] = (m.get("sure") or {}).get("varsayilan") or 1.5
            elif c.get("tur") == "motion" and isinstance(c.get("hf"), dict):
                from . import hf_grafik  # süre kompozisyonun kökünden: önce bu yamadaki, sonra kütüphanedeki
                ad = c["hf"].get("ad") or ""
                try:
                    if ad in y.hf:
                        c["sure"] = hf_grafik.olcu_metin(y.hf[ad], ad)["sure"]
                    elif d := hf_grafik.bul(ad):
                        c["sure"] = hf_grafik.olcu(d)["sure"]
                except ValueError:
                    pass
                c.setdefault("sure", 2.0)
            elif c.get("olay"):
                c["sure"] = 0.3  # olaysesi: klip süresi yalnız görsel işarettir
    gun = {g["id"]: g for g in copy.deepcopy(list(y.guncelle)) if isinstance(g, dict) and g.get("id")}
    kaynaklar = dict(y.kaynaklar)
    if dusen is not None:
        dusen += [f"{rol}:{a}" for a in yabanci] + [f"{rol}:{a}(aralık dışı)" for a in disari]
    sonuc = _dogrula(k, rol, y, ekle, gun, kaynaklar, dusen)
    ids = {c.id for c in sonuc.klipler}
    atama.klip.update({c["id"]: rol for c in ekle if c.get("id") in ids})
    return sonuc


def _dogrula(k: Kurgu, rol: str, y: Yama, ekle: list[dict], gun: dict, kaynaklar: dict, dusen: list[str] | None) -> Kurgu:
    d = _kurgu_dict(k, y, ekle, gun, kaynaklar)
    try:
        return Kurgu.model_validate(d)
    except ValidationError as e:
        hata = e
    # Bilinmeyen alt alan (ör. ses.seviye) öğeyi düşürmez: alan atılır, bir kez yeniden denenir.
    # WHY: ADR 0054. Bozuk iç içe alan da (ör. ses.kf [t, v] çifti yazılmış) öğeyi düşürmez: o alt alan atılır.
    # arvelior-hiz koşusunda müzik klibi yalnız kf biçimi yüzünden bütünüyle düşmüştü.
    fazla = [er["loc"] if er.get("type") == "extra_forbidden" else er["loc"][:4] for er in hata.errors()
             if (er.get("type") == "extra_forbidden" and len(er.get("loc", ())) >= 3
                 or len(er.get("loc", ())) >= 5 and isinstance(er["loc"][2], str) and isinstance(er["loc"][3], str))
             and er["loc"][0] == "klipler" and isinstance(er["loc"][1], int) and er["loc"][1] < len(d["klipler"])]
    fazla = list(dict.fromkeys(tuple(x) for x in fazla))
    if fazla:
        ek_id = {c.get("id") for c in ekle}
        for loc in fazla:
            c = d["klipler"][loc[1]]
            hedef = next((x for x in ekle if x.get("id") == c.get("id")), None) if c.get("id") in ek_id else gun.get(c.get("id"))
            if hedef is None:
                continue
            for anahtar in loc[2:-1]:
                hedef = hedef.get(anahtar) if isinstance(hedef, dict) else None
            if isinstance(hedef, dict) and hedef.pop(loc[-1], None) is not None and dusen is not None:
                dusen.append(f"{rol}:{c.get('id')}." + ".".join(str(x) for x in loc[2:]))
        d = _kurgu_dict(k, y, ekle, gun, kaynaklar)
        try:
            return Kurgu.model_validate(d)
        except ValidationError as e:
            hata = e
    kotu_klip, kotu_kay = set(), set()
    for er in hata.errors():
        loc = er.get("loc", ())
        if len(loc) >= 2 and loc[0] == "klipler" and isinstance(loc[1], int):
            kotu_klip.add(d["klipler"][loc[1]].get("id") if loc[1] < len(d["klipler"]) else None)
        elif len(loc) >= 2 and loc[0] == "kaynaklar" and loc[1] in kaynaklar:
            kotu_kay.add(loc[1])
    if not kotu_klip and not kotu_kay:
        raise SystemExit(f"{rol}: şema: {str(hata)[:500]}") from hata
    kaynaklar = {kid: v for kid, v in kaynaklar.items() if kid not in kotu_kay}
    yeni_ekle = [c for c in ekle if c.get("id") not in kotu_klip and c.get("kaynak") not in kotu_kay]
    gun = {kid: g for kid, g in gun.items() if kid not in kotu_klip}
    atilan = [c.get("id") for c in ekle if c not in yeni_ekle] + sorted(x for x in kotu_klip if x in {g.get("id") for g in y.guncelle}) + sorted(kotu_kay)
    try:
        sonuc = Kurgu.model_validate(_kurgu_dict(k, y, yeni_ekle, gun, kaynaklar))
    except ValidationError as e:
        raise SystemExit(f"{rol}: şema: {str(e)[:500]}") from e
    if dusen is not None:
        dusen += [f"{rol}:{a}" for a in atilan]
    return sonuc


# ---------------------------------------------------------------- birleştirme

def _konusma_kaynagi(k: Kurgu, t: float) -> str | None:
    """t anında V1'de görünen konuşma kaynağı (çapalama için)."""
    for c in k.klipler:
        if c.iz == "V1" and c.tur == "video" and c.kaynak and c.bas <= t < c.bas + c.sure and k.kelimeler.get(c.kaynak):
            return c.kaynak
    return None


def birlestir(taban: Kurgu, yamalar: dict[str, Yama], atama: Atama | None = None) -> tuple[Kurgu, dict]:
    """Kurgu dışı yamalar tabana (kurgu kesiminden önceki zaman çizelgesine) uygulanır; çapasız olayları vedit çapalar;
    sonra kurgu yaması; çapalar yeniden eşlenir."""
    atama = atama or Atama.uc()
    atama.bagla(taban)
    rapor: dict = {"uygulanan": [], "red": {}, "dusen": [], "capalanan": 0, "tasinan": [], "capa_bulgu": [], "itilen": [], "cakisma_bulgu": []}
    k = taban
    ks = atama.kurgu_sahibi()
    for rol in sorted(yamalar, key=_no):
        if rol == ks:
            continue
        try:
            k = yama_uygula(k, rol, yamalar[rol], rapor["dusen"], atama)
            rapor["uygulanan"].append(rol)
        except SystemExit as e:
            rapor["red"][rol] = str(e)
    for c in k.klipler:
        if c.capa is None and katman_sinifi(k, c.iz, c) != "kurgu" and (kay := _konusma_kaynagi(k, c.bas + 0.1)):
            capa.capala(k, c, kay)
            rapor["capalanan"] += c.capa is not None
    if ks in yamalar:
        try:
            k = yama_uygula(k, ks, yamalar[ks], rapor["dusen"], atama)
            rapor["uygulanan"].append(ks)
        except SystemExit as e:
            rapor["red"][ks] = str(e)
    rapor["tasinan"], rapor["capa_bulgu"] = capa.esle(k)
    for b in rapor["capa_bulgu"]:
        c = next((x for x in k.klipler if x.id == b.get("klip")), None)
        b["hedef"] = atama.sahip(k, c) if c is not None else None
    rapor["itilen"], rapor["cakisma_bulgu"] = cakisma_coz(k, atama=atama)
    rapor["sigdirilan"] = cekime_sigdir(k)
    rapor["kirpilan"] = sona_kirp(k)
    rapor["iz_cozulen"], iz_bulgu = iz_cakisma_coz(k, atama=atama)
    rapor["cakisma_bulgu"] += iz_bulgu
    return k, rapor


def oto_duzelt(k: Kurgu) -> list[str]:
    """Kodla bulunabilen, güvenli kusurları render'dan önce düzeltir; her değişiklik tek satır döner.

    WHY: bkz. wiki/decisions/0054-hizli-edit.md. arvelior koşusunda QC'nin P1 bulgularının yarısı (zoom yoğunluğu, okunamayacak
    kadar kısa native grafik) koddan bulunabilen şeylerdi ve bir düzeltme turu + render'a mal oluyordu. Eşikler ölçen
    modüllerden okunur: slop.OLAY_YOGUN_DAKIKA, native_motion.sure_siniri."""
    from . import hazir_efekt, native_motion, slop
    out: list[str] = []
    gizli = {i.id for i in k.izler if i.gizli}
    bitis = _bitis(k)

    # 1) Native grafik süresi bileşen sınırına: kısa olan aynı izdeki sonraki klibe ve sekans sonuna taşmadan uzar, uzun olan kısalır.
    for c in k.klipler:
        if c.tur != "motion" or not c.bilesen or c.iz in gizli:
            continue
        alt, ust = native_motion.sure_siniri(c)
        if alt is not None and c.sure < alt - 1e-3:
            sonraki = min((x.bas for x in k.klipler if x.iz == c.iz and x.id != c.id and x.bas > c.bas + 1e-3), default=bitis)
            yeni = round(min(alt, sonraki - c.bas, bitis - c.bas), 3)
            if yeni > c.sure + 1e-3:
                out.append(f"{c.id}: {c.bilesen.ad} {c.sure:.2f} → {yeni:.2f} sn (okunurluk sınırı {alt} sn)")
                c.sure = yeni
        elif ust is not None and c.sure > ust + 1e-3:
            out.append(f"{c.id}: {c.bilesen.ad} {c.sure:.2f} → {ust:.2f} sn (en çok {ust} sn)")
            c.sure = float(ust)

    # 2) Zoom/punch olay yoğunluğu: sınırı aşınca en sık kümelenen hazır efekt silinir (slop OLAY_YOGUN önerisi: gerisini sil).
    kat = hazir_efekt.katalog()
    sure = bitis
    sinir = int(slop.OLAY_YOGUN_DAKIKA * sure / 60) if sure > 0 else 0
    olaylar: list[tuple[float, object, dict | None]] = []
    for c in k.klipler:
        if c.iz in gizli:
            continue
        if c.tur in hazir_efekt.GORUNTU:
            for e in c.hazir:
                tn = kat.get(e.get("ad"))
                if tn and tn["ses"] and e.get("ses") is not False and tn["rol"] in slop.ZOOM_ROLLERI:
                    olaylar.append((c.bas + hazir_efekt.cozumle(c, e)[0], c, e))
        elif c.tur == "ses" and str((c.olay or {}).get("tur")) in slop.ZOOM_ROLLERI:
            olaylar.append((c.bas, c, None))
    if sure > 0 and len(olaylar) > max(sinir, 0):
        once = len(olaylar)
        olaylar.sort(key=lambda x: x[0])
        while len(olaylar) > sinir and olaylar:
            # En yakın komşusuna en yakın olay (kümelenme) gider; hook (ilk 3 sn) son çare.
            def aralik(i):
                t = olaylar[i][0]
                g = min([abs(t - olaylar[j][0]) for j in (i - 1, i + 1) if 0 <= j < len(olaylar)] or [1e9])
                return (t < 3.0, g)
            i = min(range(len(olaylar)), key=aralik)
            t, c, e = olaylar.pop(i)
            if e is not None:
                c.hazir = [x for x in c.hazir if x is not e]
            else:
                k.klipler = [x for x in k.klipler if x is not c]
        out.append(f"zoom/punch olayı {once} → {len(olaylar)} (dakikada en çok {slop.OLAY_YOGUN_DAKIKA}; kümelenenler silindi)")

    # 3) Art arda üçüncü aynı geçiş (kurgu_kalite GECIS_TEKRAR): uyarının önerisi uygulanır, yön çevrilir; geçiş yumuşak kalır.
    # WHY: bkz. wiki/decisions/0058-hizli-ve-kaliteli-edit.md. Düzeltme turları seriyi editörler arasında bölüyor, uyarı
    # kimsede kalmıyordu (hizlic: 1 → 4 uyarı). Efekt tekrarı (EFEKT_TEKRAR) kodla silinmez: hangi vurgunun gideceği
    # kurgu kararıdır; uyarı klip id'siyle sahibine gider.
    gorunur = sorted((c for c in k.klipler if c.iz not in gizli), key=lambda c: c.bas)
    ters = {"sol": "sag", "sag": "sol", "yukari": "asagi", "asagi": "yukari"}
    seri, onceki = 0, None
    for c in gorunur:
        if not c.gecis_giris:
            continue
        ad = (c.gecis_giris.tur, c.gecis_giris.yon)
        seri = seri + 1 if ad == onceki else 1
        if seri == kurgu_kalite.ART_ARDA:
            c.gecis_giris.yon = ters[c.gecis_giris.yon]
            out.append(f"{c.id}: art arda {seri}. {ad[0]}/{ad[1]} geçişi → {ad[0]}/{c.gecis_giris.yon}")
            ad, seri = (c.gecis_giris.tur, c.gecis_giris.yon), 1
        onceki = ad
    return out


def _en_kisa(c) -> float:
    """Klibin kısaltılabileceği en kısa süre: native bileşende meta `min`, ses olayında 0,1 sn, gerisinde 0,5 sn."""
    if c.tur == "ses":
        return 0.1
    if c.tur == "motion" and c.bilesen:
        m = (native_motion.kayitlar().get(c.bilesen.ad) or {}).get("meta", {})
        return (m.get("sure") or {}).get("min") or native_motion.SURE_SINIRI.get(m.get("tur"), (0.5, None))[0]
    return 0.5


def _bos_iz(k: Kurgu, iz, c) -> str | None:
    """c'yi alabilecek, aynı tür ve katman sınıfında, o aralıkta boş, kilitsiz başka iz."""
    sinif = katman_sinifi(k, iz.id, c)
    for d in k.izler:
        if d.id == iz.id or d.id in ("V1", "A1") or d.tur != iz.tur or d.kilit or katman_sinifi(k, d.id, c) != sinif:
            continue
        if all(x.bas + x.sure <= c.bas + 1e-3 or x.bas >= c.bas + c.sure - 1e-3 for x in k.klipler if x.iz == d.id):
            return d.id
    return None


def _yeni_iz(k: Kurgu, iz) -> str:
    from .schemas import KurguIz
    on = "V" if iz.tur == "video" else "A"
    kullanilan = {d.id for d in k.izler}
    no = next(n for n in range(2, 100) if f"{on}{n}" not in kullanilan)
    yeni = KurguIz(id=f"{on}{no}", tur=iz.tur, ad=iz.ad)
    # Görüntü izleri listede baştan sona üstten alta çizilir: yeni iz çakıştığı izin hemen üstüne girer.
    k.izler.insert(k.izler.index(iz), yeni) if iz.tur == "video" else k.izler.insert(k.izler.index(iz) + 1, yeni)
    return yeni.id


def iz_cakisma_coz(k: Kurgu, *, en_cok_kirpma: float = 0.6, atama: Atama | None = None) -> tuple[list[str], list[dict]]:
    """Aynı izde üst üste binen klipleri ayırır; yoksa `kurgu.denetle` render'ı durdurur.

    Küçük örtüşmede (≤ 0,6 sn, kurgu izinde ≤ 0,1 sn) önceki klip kısalır; büyükte sonraki aynı sınıftan boş bir ize,
    yoksa yeni ize taşınır ve sahibine bulgu yazılır. Kurgu izinde (V1, A1) büyük örtüşmeye dokunulmaz."""
    # WHY: reel-video 2026-11-23: editörler kesim öncesi zamanda yazar; E1'in kesimi sonrası çapalar yeniden eşlenince
    # E3'ün iki grafiği V3'te 0,11 sn üst üste bindi, G3 taslağı "çakışıyor" diye düştü ve bozuk kurgu diske yazıldı.
    atama = atama or Atama.uc()
    degisen, bulgu = [], []
    for iz in list(k.izler):
        kurgu_izi = iz.id in ("V1", "A1")
        for _ in range(500):
            sira = sorted((c for c in k.klipler if c.iz == iz.id), key=lambda c: (c.bas, c.id))
            cift = next(((a, b) for a, b in zip(sira, sira[1:]) if b.bas < a.bas + a.sure - 1e-3), None)
            if cift is None:
                break
            a, b = cift
            ortusme, kalan = a.bas + a.sure - b.bas, b.bas - a.bas
            if ortusme <= (0.1 if kurgu_izi else en_cok_kirpma) and kalan >= (0.04 if kurgu_izi else _en_kisa(a)):
                a.sure = round(kalan, 3)
                degisen.append(a.id)
                continue
            if kurgu_izi:
                break  # kurgu kararı: denetle raporlar, editör düzeltir
            hedef = _bos_iz(k, iz, b) or _yeni_iz(k, iz)
            b.iz = hedef
            degisen.append(b.id)
            bulgu.append({"hedef": atama.sahip(k, b), "klip": b.id, "iz": hedef, "zaman": [b.bas, b.bas + b.sure],
                          "sorun": f"{a.id} ile aynı izde {ortusme:.2f} sn üst üste biniyordu; {hedef} izine taşındı"})
    return degisen, bulgu


CEKIME_BAGLI = {"ikon", "kart", "cizim", "cta", "parcacik"}


def cekime_sigdir(k: Kurgu) -> list[str]:
    """Çekime bağlı native grafik başladığı V1 çekiminin sonunu aşmaz: önce kısalır (meta `min` altına inmez), yetmezse öne kayar."""
    # WHY: instagram/1 v2 koşularında ikonlar kesimden sonra 0,3-0,6 sn sonraki çekime taştı (piksel-8bit'te QC P0, temiz-kurumsal'da kaçtı).
    v1 = sorted((c for c in k.klipler if c.iz == "V1"), key=lambda c: c.bas)
    degisen = []
    for c in k.klipler:
        if c.tur != "motion" or not c.bilesen:
            continue
        m = (native_motion.kayitlar().get(c.bilesen.ad) or {}).get("meta", {})
        if m.get("tur") not in CEKIME_BAGLI:
            continue
        cek = next((v for v in v1 if v.bas - 1e-3 <= c.bas < v.bas + v.sure), None)
        if cek is None:
            continue
        son = cek.bas + cek.sure
        if c.bas + c.sure <= son + 1e-3:
            continue
        alt = (m.get("sure") or {}).get("min") or native_motion.SURE_SINIRI.get(m.get("tur"), (0.5, None))[0]
        if son - c.bas >= alt:
            c.sure = round(son - c.bas, 3)
        elif son - alt >= cek.bas:
            c.bas, c.sure = round(son - alt, 3), alt
        else:
            continue  # çekim grafikten kısa: dokunulmaz, QC görür
        degisen.append(c.id)
    return degisen


def sona_kirp(k: Kurgu) -> list[str]:
    """Sekans V1 ile biter: kurgu kesimi kısalttıysa taşan müzik/grafik kırpılır, sonra başlayan düşer (yerinde)."""
    # WHY: instagram/1 piksel-8bit v2 koşusunda A3 müziği V1 sonundan 4,3 sn taştı; taslağın sonu siyah kaldı.
    v1 = [c for c in k.klipler if c.iz == "V1"]
    if not v1:
        return []
    son = max(c.bas + c.sure for c in v1)
    degisen, kalan = [], []
    for c in k.klipler:
        if c.iz != "V1" and c.bas >= son - 0.05:
            degisen.append(c.id)
            continue
        if c.iz != "V1" and c.bas + c.sure > son + 1e-3:
            c.sure = round(son - c.bas, 3)
            if c.ses is not None and c.tur == "ses":
                c.ses.fade_out = max(c.ses.fade_out, min(1.0, c.sure / 4))
            degisen.append(c.id)
        kalan.append(c)
    k.klipler[:] = kalan
    return degisen


def _hero(c) -> bool:
    if not c.bilesen:
        return c.tur == "sahne" or (c.metin_stil or {}).get("tip") in ("anahtar", "cagri", "bolum")
    m = (native_motion.kayitlar().get(c.bilesen.ad) or {}).get("meta", {})
    return c.bilesen.hero if c.bilesen.hero is not None else bool(m.get("hero"))


def cakisma_coz(k: Kurgu, *, en_cok_itme: float = 0.6, atama: Atama | None = None) -> tuple[list[str], list[dict]]:
    """Öncelik: konuşma/kesim > okunurluk > grafik > SFX. Çakışan grafik güvenli payda itilir, olmuyorsa sahibine bulgu."""
    atama = atama or Atama.uc()
    itilen, bulgu = [], []
    grafik = sorted((c for c in k.klipler if katman_sinifi(k, c.iz, c) == "grafik" and c.tur in ("motion", "metin", "sahne", "gorsel")),
                    key=lambda c: c.bas)
    # 1) Kesim geçişinin üstüne binen grafik: geçiş bitene kadar it (geçiş okunurluğu bozar).
    gecisler = [(c.bas - c.gecis_giris.sure / 2, c.bas + c.gecis_giris.sure / 2) for c in k.klipler
                if c.iz == "V1" and c.gecis_giris and c.gecis_giris.tur not in ("kararma",)]
    for c in grafik:
        for a, b in gecisler:
            if a - 1e-3 < c.bas < b:
                ek = b - c.bas
                if ek <= en_cok_itme:
                    c.bas = round(b, 3)
                    itilen.append(c.id)
                else:
                    bulgu.append({"hedef": atama.sahip(k, c), "klip": c.id, "iz": c.iz, "zaman": [a, b], "sorun": "grafik kesim geçişinin üstünde"})
    # 2) Aynı anda iki hero: sonraki öncekinin bitişine itilir.
    son = None
    for c in sorted(grafik, key=lambda c: c.bas):
        if not _hero(c):
            continue
        if son and c.bas < son.bas + son.sure - 1e-3:
            ek = son.bas + son.sure - c.bas
            if ek <= en_cok_itme:
                c.bas = round(son.bas + son.sure, 3)
                itilen.append(c.id)
            else:
                bulgu.append({"hedef": atama.sahip(k, c), "klip": c.id, "iz": c.iz, "zaman": [c.bas, c.bas + c.sure],
                              "sorun": f"{son.id} ile aynı anda iki ana grafik"})
                continue
        son = c
    # 3) SFX yoğunluğu: 0,4 sn'de birden çok rol olayı (konuşmayı örter) → sahibine bulgu.
    sfx = sorted((c for c in k.klipler if c.tur == "ses" and (c.olay or {}).get("tur") and not (c.olay or {}).get("muzik")
                  and not (c.olay or {}).get("konusma")), key=lambda c: c.bas)
    for a, b in zip(sfx, sfx[1:]):
        if b.bas - a.bas < 0.4:
            bulgu.append({"hedef": atama.sahip(k, b), "klip": b.id, "iz": b.iz, "zaman": [a.bas, b.bas], "sorun": "0,4 sn içinde iki ses olayı"})
    return itilen, bulgu


# ---------------------------------------------------------------- plan: doğrulama ve varsayılan dağıtım

# Varsayılan dağıtım: (katmanlar, dilim sayısı) grupları. Sayıların toplamı seviyenin editör sayısıdır.
VARSAYILAN = {
    "low": [(["kurgu"], 1), (["grafik", "sfx", "muzik", "stil"], 1)],
    "medium": [(["kurgu"], 1), (["grafik"], 2), (["sfx", "muzik", "stil"], 1)],
    "high": [(["kurgu"], 1), (["grafik"], 3), (["sfx"], 1), (["muzik", "stil"], 1)],
    "xhigh": [(["kurgu"], 1), (["grafik"], 4), (["sfx"], 2), (["muzik", "stil"], 1)],
    "max": [(["kurgu"], 1), (["grafik"], 5), (["sfx"], 2), (["muzik"], 1), (["stil"], 1)],
}
VARSAYILAN_KK = {"low": ["genel"], "medium": ["kurgu-ses", "gorsel"], "high": ["kurgu", "gorsel", "ses"],
                 "xhigh": ["kurgu", "gorsel", "ses", "kural"], "max": ["kurgu", "gorsel", "ses", "kural", "izleyici"]}


def _bitis(k: Kurgu) -> float:
    return max((c.bas + c.sure for c in k.klipler if c.iz == "V1"), default=0.0) or max((c.bas + c.sure for c in k.klipler), default=0.0)


def varsayilan_dagitim(seviye: str, k: Kurgu) -> Plan:
    gorevler, n = [], 1
    for katmanlar, dilim in VARSAYILAN[seviye]:
        araliklar = ekip.zaman_araliklari(k, dilim) if dilim > 1 else [None]
        for ar in araliklar:
            gorevler.append(Gorev(slot=f"E{n}", katmanlar=katmanlar, aralik=list(ar) if ar else None))
            n += 1
    kk = [KkGorev(slot=f"K{i + 1}", rol=r) for i, r in enumerate(VARSAYILAN_KK[seviye])]
    return Plan(gorevler=gorevler, kk_gorevler=kk, gerekce="varsayılan dağıtım")


HIZLI_QC_UZUN = 90.0  # sn; hızlı modda bu süreden kısa video iki, uzun video üç QC dilimine bölünür (ADR 0058)


def hizli_kk(k: Kurgu) -> list[KkGorev]:
    """Hızlı mod QC kartları: tek genel QC yerine zaman dilimi başına bir genel QC, paralel.

    WHY: bkz. wiki/decisions/0058-hizli-ve-kaliteli-edit.md. Tek QC bütün paftaları okuyup 12-18k token düşünüyordu (G4'ün
    134 sn'si); dilim başına ajan daha az görsel okur, aynı anda biter. Dilim sınırı kelime arasıdır (zaman_araliklari)."""
    n = 2 if _bitis(k) < HIZLI_QC_UZUN else 3
    return [KkGorev(slot=f"K{i + 1}", rol="genel", aralik=[round(a, 2), round(b, 2)])
            for i, (a, b) in enumerate(ekip.zaman_araliklari(k, n))]


def pafta_sec(girdi: dict, aralik: list[float] | None, pay: float = 1.5) -> list:
    """Aralığa değen paftalar (sınırdaki geçişi iki taraf da görsün diye bir kare payıyla). Zaman yoksa hepsi."""
    paftalar, zaman = girdi.get("_paftalar") or [], girdi.get("_pafta_zaman")
    if not aralik or not zaman or len(zaman) != len(paftalar):
        return list(paftalar)
    return [f for f, (a, b) in zip(paftalar, zaman) if b >= aralik[0] - pay and a <= aralik[1] + pay]


def plan_dogrula(plan: Plan, seviye: str, son: float) -> list[str]:
    """Seviye sayıları, tek kurgu sahibi, her katman × zamanın tam bir editörde olması, QC alanlarının kapsanması."""
    h = []
    e, kk = editorler(seviye), kontroller(seviye)
    if sorted(g.slot for g in plan.gorevler) != sorted(e):
        h.append(f"editör slotları {', '.join(e)} olmalı")
    if sorted(g.slot for g in plan.kk_gorevler) != sorted(kk):
        h.append(f"kalite kontrol slotları {', '.join(kk)} olmalı")
    return h + kapsam_hatalari(plan, son)


def kapsam_hatalari(plan: Plan, son: float) -> list[str]:
    """Tek kurgu sahibi, her katman × zamanın tam bir editörde olması, QC alanlarının kapsanması (seviye ve swarm ortak)."""
    h: list[str] = []
    pay = 0.06
    for katman in KATMANLAR:
        kartlar = sorted((g for g in plan.gorevler if katman in g.katmanlar), key=lambda g: (g.aralik or [0, 0])[0])
        if not kartlar:
            h.append(f"{katman} katmanının sahibi yok")
            continue
        if katman in BOLUNMEZ:
            if len(kartlar) != 1 or kartlar[0].aralik is not None:
                h.append(f"{katman} bölünmez: tek editör, aralık null")
            continue
        if len(kartlar) == 1 and kartlar[0].aralik is None:
            continue
        if any(g.aralik is None for g in kartlar):
            h.append(f"{katman}: bölünmüşse her kartın aralığı olmalı")
            continue
        ar = [g.aralik for g in kartlar]
        if ar[0][0] > pay or ar[-1][1] < son - pay:
            h.append(f"{katman}: aralıklar 0–{son:.1f} sn'yi kapsamıyor")
        if any(a[1] <= a[0] for a in ar) or any(abs(a[1] - b[0]) > pay for a, b in zip(ar, ar[1:])):
            h.append(f"{katman}: aralıklar boşluksuz ve örtüşmesiz olmalı")
    alan = set().union(*(KK_ALAN[g.rol] for g in plan.kk_gorevler)) if plan.kk_gorevler else set()
    if not {"kurgu", "gorsel", "ses"} <= alan:
        h.append("kalite kontrol kartları kurgu, görsel ve ses alanlarını birlikte kapsamalı")
    return h


def _kapsam(p) -> dict:
    from . import stil as stil_mod
    try:
        stil_ad = stil_mod.secili_adi(p)
    except Exception:  # noqa: BLE001 - stil yoksa kapsam yalnız stüdyo ve proje
        stil_ad = None
    return {"studyo": getattr(p, "studyo", None), "stil": stil_ad, "proje": f"{getattr(p, 'studyo', '')}/{getattr(p, 'ad', '')}"}


def zorunlu_kurallar(p, g: Gorev, d: kural.Depo | None = None, *, doldur: bool = False) -> list[str]:
    """Kartın zorunlu kuralları: katmanına uyan bütün etkin P0'lar + orkestratörün atadıkları (etkin olanlar).
    `doldur`: orkestratör atamadıysa (varsayılan dağıtım) P1'ler de eklenir, en çok ZORUNLU_EN_COK."""
    d = d or kural.yukle()
    kap = _kapsam(p)
    sec = list({kr.id: kr for r in sorted({KURAL_ROLU[x] for x in g.katmanlar}) for kr in kural.secim(d, rol=r, **kap)}.values())
    etkin = {kr.id for kr in kural.secim(d, rol="hepsi", **kap)}
    p0 = [kr.id for kr in sec if kr.onem == "P0"]
    atanan = [i for i in g.kurallar if i in etkin]
    sonuc = list(dict.fromkeys(p0 + atanan))
    if doldur and not atanan:
        sonuc += [kr.id for kr in sec if kr.onem == "P1" and kr.id not in sonuc]
    return sonuc[:max(ZORUNLU_EN_COK, len(p0))]


# ---------------------------------------------------------------- sözleşme, pano, bağlam paketi

def sozlesme(p, k: Kurgu, hook: dict | None, ritim: dict | None) -> dict:
    t = tema_token.oku(kurgu.etkin_tema(p, k.motion_tema)) or tema_token.oku("varsayilan")
    W, H = k.sekans.w, k.sekans.h
    yuz = yuz_bolge.hesapla(p, k) if yuz_bolge.model_var() else []
    return {
        "surum": 3, "rev": k.rev, "sekans": k.sekans.model_dump(), "hook": hook,
        "kesim": [{"id": c.id, "bas": c.bas, "sure": c.sure, "kaynak": c.kaynak, "giris": c.giris, "hiz": c.hiz,
                   **({"gecis": c.gecis_giris.tur} if c.gecis_giris else {})} for c in sorted(k.klipler, key=lambda c: c.bas) if c.iz == "V1"],
        "ayrilmis": {"altyazi_bandi_y": [round(0.66 * H), round(0.80 * H)] if H > W else [round(0.82 * H), round(0.94 * H)],
                     "platform": "9:16 üst %10, alt %20, sağ sütun %14 (y %42-80)" if H > W else "yok",
                     "yuz_araliklari": len(yuz), "not": "Native grafik yerleşimi yüz ve altyazıdan kendiliğinden kaçar; bölge yazma."},
        # WHY: dizinler pakette yoktu; E2/E3 çapa dizinini tahmin ediyor ya da hiç çapalamıyordu (instagram/1 v2 koşusu).
        "kelimeler": {kay: " ".join(f"{i}:{w.w}@{w.s:.2f}" for i, w in enumerate(k.kelimeler.get(kay) or []))
                      for kay in dict.fromkeys(c.kaynak for c in sorted(k.klipler, key=lambda c: c.bas) if c.iz == "V1" and c.kaynak)
                      if k.kelimeler.get(kay)},
        "ritim": {"bpm": (ritim or {}).get("bpm"), "vurus": [round(x, 2) for x in ((ritim or {}).get("beats") or [])[:200]]},
        "stil": {"tema": t.ad, "vurgu": t.renk.vurgu, "ikincil": t.renk.ikincil, "baslik": t.font.baslik,
                 "egri": (t.hareket.egri.model_dump() if t.hareket.egri else t.hareket.easing)},
    }


# WHY: editörler paralel thread'lerde pano'ya yazar; kilitsiz oku-ekle-yaz mesaj kaybettiriyor, yarım dosya okuyan thread
# JSONDecodeError ile bütün akışı düşürebiliyordu (max'ta on editör).
_PANO_KILIT = threading.Lock()


def _pano_yukle(f: Path) -> list[dict]:
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    except ValueError:
        return []


def pano_ekle(kok: Path, rol: str, mesajlar: list[Mesaj]) -> None:
    f = kok / "pano.json"
    with _PANO_KILIT:
        eski = _pano_yukle(f) + [{**m.model_dump(), "kimden": rol} for m in mesajlar]
        kurgu._atomik(f, json.dumps(eski, ensure_ascii=False, indent=1))


def pano_oku(kok: Path, rol: str, aralik: tuple[float, float] | None = None) -> list[dict]:
    with _PANO_KILIT:
        m = [x for x in _pano_yukle(kok / "pano.json") if x.get("kimden") != rol]
    if aralik:
        m = [x for x in m if x["aralik"][0] <= aralik[1] and aralik[0] <= x["aralik"][1]]
    return m[-40:]


def _katman_ozeti(k: Kurgu, rol: str, atama: Atama) -> list[str]:
    """Başka editörlerin katmanından birer satır: ne var, nerede yoğun."""
    sat = []
    for r in atama.gorevler:
        if r == rol:
            continue
        ks = [c for c in k.klipler if atama.sahip(k, c) == r]
        if ks:
            sat.append(f"- {atama.etiket(r)}: {len(ks)} klip, {min(c.bas for c in ks):.1f}-{max(c.bas + c.sure for c in ks):.1f} sn; "
                       + ", ".join(sorted({c.tur for c in ks})))
    return sat


SABIT = """## Çıktı (yalnız bu JSON, başka metin yok)
```json
{"ekle": [<yeni klipler, kurgu.json klip şeması>], "guncelle": [{"id": "<klip>", <yalnız değişen alanlar>}], "sil": ["<klip id>"],
 "kaynaklar": {"<yeni kaynak id>": {"yol": "library:music/<klasör>/<dosya>.mp3", "sure": <sn>}}, "isaretler": null, "altyazi": null, "motion_tema": null, "hook": null, "hf": {},
 "pano": [{"tip": "claim|constraint|request|done", "aralik": [a, b], "metin": "<en çok 2 satır>"}],
 "kural_uyum": [{"id": "K0012", "nasil": "<bu kurala nasıl uydun, tek satır>"}],
 "rapor": "<ne yaptın, zaman damgalı, en çok 10 satır>",
 "oz_denetim": "<imza anı nasıl teslim edildi, en zayıf an ve neden, taşınan brif maddesi; en çok 4 satır>"}
```
Kurallar:
- Yalnız kartındaki katmana ve aralığa yaz. Başka katmandaki klibe dokunursan yaman birleşmez; aralığın dışına eklediğin öğe düşer.
- Zorunlu kuralların her biri için `kural_uyum`'a bir satır yaz. Eksik ya da ihlal edilen kural, kural kapısında yamanı düzeltmeye geri yollar.
- Grafik ve ses olayını sekans saniyesine değil kaynak kelimesine çapala: `"capa": {"kaynak": "<id>", "kelime": <dizin>}`; dizinler sözleşmenin `kelimeler` alanında (`dizin:kelime@kaynak sn`); giriş kelimeden 2-4 kare önce (`once_kare`). Kesim değişirse vedit taşır.
- Grafik önce HyperFrames: `{"tur": "motion", "hf": {"ad": "<kompozisyon>", "param": {...}}}` (ADR 0050); webm'i vedit üretir. Katalogda uygun kompozisyon yoksa (yalnız grafik katmanı) yeni kompozisyonu dosya yazmadan çıktının `"hf": {"<ad>": "<index.html içeriği>"}` alanına koy; sözleşme `library/motion/hf/SOZLESME.md`, vedit `work/edit/hf/<ad>/` altına yazar.
- Native grafik için `{"tur": "motion", "bilesen": {"ad": "<katalog adı>", "param": {...}}}`; konum yazma, yerleşim yüz ve altyazıdan kendiliğinden kaçar.
- Kaynak alanları yalnız `yol`, `sure`, `w`, `h`, `ses`; `yol` önekli yazılır (`library:`, `inputs:`, `public:`, `stil:`). Başka alan yamayı düşürür.
- Yanıtın tamamı tek JSON nesnesi olsun.
"""


def _kural_metinleri(ids: list[str], d: kural.Depo | None = None) -> list[str]:
    d = d or kural.yukle()
    m = {k.id: k for k in d.kurallar}
    return [f"- [{i} {m[i].onem}] {m[i].metin}" for i in ids if i in m]


_ROL_ONBELLEK: dict[str, str] = {}


def rol_metni(adlar) -> str:
    """Rol dosyalarının (`.claude/agents/<ad>.md`) frontmatter'sız metni; yalın çağrıda sistem istemine gider (ADR 0054)."""
    parca = []
    for ad in dict.fromkeys(adlar):
        if ad not in _ROL_ONBELLEK:
            f = ROL_KLASORU / f"{ad}.md"
            m = f.read_text(encoding="utf-8") if f.is_file() else ""
            _ROL_ONBELLEK[ad] = re.sub(r"\A---\n.*?\n---\n\s*", "", m, flags=re.S).strip()
        if _ROL_ONBELLEK[ad]:
            parca.append(_ROL_ONBELLEK[ad])
    return "\n\n".join(parca)


def editor_rolleri(atama: Atama, rol: str) -> list[str]:
    return list(dict.fromkeys(EDITOR_ROL_DOSYASI[x] for x in atama.gorevler[rol].katmanlar))


DIGEST_EN_COK = 8000  # karakter; uzun videoda istem şişmesin


def _digest(p) -> str:
    """Transkript özeti istemin içinde: ajan dosya okumak için ayrı tur dönmesin (ADR 0054)."""
    f = p.work / "analysis" / "digest.txt"
    t = f.read_text(encoding="utf-8").strip() if f.is_file() else ""
    if len(t) > DIGEST_EN_COK:
        t = t[:DIGEST_EN_COK] + "\n… (kırpıldı)"
    return t or "(transkript yok)"


def _muzik_katalogu() -> str:
    """Lisanslı müzik kayıtları, kısa: müzik editörü manifest'i okumak için tur dönmesin."""
    f = paths.LIBRARY / "music" / "manifest.json"
    try:
        kayit = json.loads(f.read_text(encoding="utf-8")).get("entries") or []
    except (OSError, ValueError):
        return "- (müzik kaydı yok)"
    sat = []
    for e in kayit:
        if not e.get("license") or not e.get("file"):
            continue
        yol = str(e["file"]).replace("\\", "/").removeprefix("library/music/")
        sat.append(f"- `library:music/{yol}` · {e.get('genre') or ''} · {', '.join(e.get('mood') or [])} · enerji {e.get('energy') or '?'}"
                   f" · {e.get('bpm') or '?'} bpm · {e.get('duration_s') or '?'} sn" + (f" · yapı: {e['structure']}" if e.get("structure") else ""))
    return "\n".join(sat) or "- (lisanslı müzik kaydı yok)"


def _motion_brif_ozeti(p, stil_ad: str | None) -> str:
    """G0.5 Yönetmen Motion Brifi (ADR 0062): work/edit/motion-brief.json varsa o, yoksa stil kartından otomatik sentez."""
    brif_f = p.work / "edit" / "motion-brief.json"
    if brif_f.is_file():
        try:
            veri = json.loads(brif_f.read_text(encoding="utf-8"))
            return "## G0.5 Yönetmen Motion Brifi (work/edit/motion-brief.json)\n```json\n" + json.dumps(veri, ensure_ascii=False)[:2400] + "\n```"
        except (OSError, ValueError):
            pass
    ybrif = yaratici.oku(p.work)  # WHY: bkz. wiki/decisions/0064-yaratici-yon.md
    if ybrif and (ybrif.iplik or ybrif.metafor):
        parca = []
        if ybrif.metafor:
            parca.append(f"görsel metafor: {ybrif.metafor}")
        if ybrif.iplik:
            parca.append(f"iplik öğe: {ybrif.iplik}")
        yon_satir = "- Brif yönü (ADR 0064): " + "; ".join(parca) + ". Her hareket ekranda zaten olan bir öğeden doğar."
    else:
        yon_satir = (
            "- Brif beş bölüm (ADR 0063): girdi, yön (tek **iplik öğe** tüm grafikleri bağlar + yasak listesi), yapı (beat başına görsel değişim), "
            "kurulum (kare yalnız t'den, ölçülen vuruşa kilit), tuzaklar. Her hareket ekranda zaten olan bir öğeden doğar."
        )
    satir = [
        "## G0.5 Sanat Yönetimi & Motion Brifi (ADR 0062)",
        "- 4-Düzen disiplini (yüzün üstüne ağır kart basma): `konusmaci` ↔ `diyagram-pip` ↔ `ekran-pip` ↔ `tam-kanit`.",
        "- Anti-Slop yasakları: her öğeye aynı `power2.out`, iniş sonrası boşta sallanan başlık, rastgele ikon serpme, sabit renk/font.",
        "- Giriş 0.35-0.6 sn (`expo.out`/`power4.out`), çıkış girişten %40-50 kısa (`power2.in`); her metin ≥ 0.5 sn + 0.3 sn/kelime.",
        yon_satir,
        "- Eğri adları her kompozisyonda hazır: `giris`, `cikis`, `vurgu`, `oturma` (stil token'ından). GSAP eklentileri: SplitText, drawSVG, morphSVG, motionPath, physics2D.",
        "- 3D (`uc-*`, three.js): videoda en çok 2, art arda değil; yalnız açılış, kapanış, ürün ya da açıklayan simülasyon anında.",
    ]
    if stil_ad:
        from . import stil_katalog
        try:
            kart = stil_katalog.bul(stil_ad)
            if kart.get("gorsel"):
                satir.append(f"- Stil ({kart['ad']}) görsel dili: " + "; ".join(kart["gorsel"][:3]))
            if kart.get("hareket"):
                satir.append("- Stil hareket dili: " + "; ".join(kart["hareket"][:3]))
            if kart.get("motion_kisilik"):
                satir.append(f"- Hareket kişiliği: `{kart['motion_kisilik']}` (motion-design references/yonetmen-katmani.md §2)")
            if kart.get("motion"):
                satir.append("- Öncelikli motion şablonları: " + ", ".join(f"`{m}`" for m in kart["motion"][:8]))
            if kart.get("kacin"):
                satir.append("- Bu stilde kaçın: " + "; ".join(kart["kacin"][:4]))
        except SystemExit:
            pass
    return "\n".join(satir)


def _stil_ozeti(p) -> str:
    """Hızlı moddaki brif çağrısı için seçili stilin kısa görsel ve hareket dili (ADR 0064)."""
    from . import stil as stil_mod
    try:
        ad = stil_mod.secili_adi(p)
    except SystemExit:
        ad = None
    if not ad:
        return ""
    sat = [f"- Seçili stil `{ad}` (renk, font ve eğri token'dan gelir; brif onları değiştirmez)"]
    try:
        from . import stil_katalog
        kart = stil_katalog.bul(ad)
    except SystemExit:
        return sat[0]
    for alan, baslik in (("gorsel", "Görsel dil"), ("hareket", "Hareket dili"), ("kacin", "Kaçın")):
        if kart.get(alan):
            sat.append(f"- {baslik}: " + "; ".join(kart[alan][:3]))
    if kart.get("motion_kisilik"):
        sat.append(f"- Hareket kişiliği: `{kart['motion_kisilik']}`")
    return "\n".join(sat)


def _komsu_grafikler(k: Kurgu, aralik: tuple[float, float] | None) -> str:
    """Komşu zaman dilimlerindeki sınır grafikleri: dilim sınırında MOTION_ART_ARDA tekrarını önler."""
    if not aralik:
        return ""
    a, b = aralik
    gr = []
    for c in sorted(k.klipler, key=lambda x: x.bas):
        if c.tur != "motion":
            continue
        ad = (c.bilesen.ad if c.bilesen else None) or (f"hf:{c.hf['ad']}" if c.hf else None) or (c.sablon or {}).get("ad")
        if ad:
            gr.append((c.bas, ad, c.id))
    once = [x for x in gr if x[0] < a][-2:]
    sonra = [x for x in gr if x[0] >= b][:2]
    if not once and not sonra:
        return ""
    sat = ["## Komşu dilim sınır grafikleri (aynı bileşeni art arda koyma)"]
    if once:
        sat.append("- Önceki dilim sonu: " + ", ".join(f"{t:.1f}s `{ad}` ({cid})" for t, ad, cid in once))
    if sonra:
        sat.append("- Sonraki dilim başı: " + ", ".join(f"{t:.1f}s `{ad}` ({cid})" for t, ad, cid in sonra))
    return "\n".join(sat)


_HF_TOKEN_OZETI = (
    "## HyperFrames sözleşme & tema.css v2 token özeti (özel y.hf yazarken zorunlu)\n"
    "- Kök: `background:none`, `<link rel=\"stylesheet\" href=\"tema.css\">`, `data-composition-variables`, tek paused `gsap.timeline({paused:true})` -> `window.__timelines[\"main\"] = tl`.\n"
    "- Sabit renk/font YASAK; yalnız token kullan: `--vurgu`, `--ikincil`, `--zemin`, `--yazi`, `--soluk`, `--olumlu`, `--olumsuz`, "
    "`--vurgu-rgb`, `--zemin-rgb`, `--yazi-rgb`, `--yuzey-cam`, `--kenar-ince`, `--yukselti-golge`, `--izgara-desen`, "
    "`--ease-enter`, `--ease-exit`, `--ease-emphasis`, `--ease-settle`, `--font`, `--font-govde`, `--font-mono`, `--font-rakam`, `--kose`.\n"
    "- Yasak: `Math.random`, `Date.now`, `requestAnimationFrame`, `setTimeout`, CSS `@keyframes`/`transition`, `repeat:-1`."
)


def _istek_metni(istek: str | None) -> str:
    return " ".join((istek or "").split()) or "(özel istek yok: seçili stile ve videoya göre en iyi edit)"


def paket(p, k: Kurgu, rol: str, soz: dict, kok: Path, atama: Atama | None = None, *, istek: str | None = None,
          zorunlu: list[str] | None = None, bulgular: list[dict] | None = None, kisitlar: list[str] | None = None,
          onceki: Yama | None = None) -> str:
    """Kart başına kompakt bağlam: sabit kısım önce (önbellek), değişken sonra. Ham medya, manifest ve tam kurgu yok."""
    from . import stil as stil_mod
    from . import stil_varlik

    atama = atama or Atama.uc()
    g = atama.gorevler[rol]
    katmanlar = list(g.katmanlar)
    try:
        stil_k = stil_mod.secili(p)
    except SystemExit:
        stil_k = None
    stil_ad = stil_k.name if stil_k else stil_mod.secili_adi(p)
    depo = stil_varlik.oku(p.studyo, stil_ad) if stil_ad else None
    ozel_varlik = stil_varlik.baglam_metni(p.studyo, stil_ad) if stil_ad else ""
    d = kural.yukle()
    satirlar = []
    for r in sorted({KURAL_ROLU[x] for x in katmanlar}):
        satirlar += kural.paket(d, rol=r, studyo=p.studyo, stil=stil_ad, proje=f"{p.studyo}/{p.ad}").splitlines()
    kurallar = "\n".join(dict.fromkeys(satirlar))
    aralik = (f"{g.aralik[0]:.2f}–{g.aralik[1]:.2f} sn (taban zaman çizelgesi; yalnız başlangıcı bu aralıkta olan klipleri ekle ve güncelle)"
              if g.aralik else "bütün video")
    sabit = [f"# Ekip editörü {rol}: " + "; ".join(f"{KATMAN_ADI[x]} ({KATMAN_TANIM[x]})" for x in katmanlar),
             "Rol tanımın sistem isteminde (ya da bu metnin sonunda). Katman adları rol tanımındaki izlerle eşleşir. Dosya okuma ve yazma yok: bütün bağlam bu metinde.",
             SABIT, "## Etkin kurallar", kurallar or "- (yok)"]
    if ozel_varlik:
        sabit.append(ozel_varlik)
    gecis_listesi = ", ".join(kurgu.ORTA_GECIS)
    if "grafik" in katmanlar:
        izinli_native = set(depo.secili_native) if (depo and depo.yalniz_bunlar) else None
        katalog_satirlari = native_motion.katalog_ozeti(izinli=izinli_native)
        kasa_metin = aiedit._kasa_bolumu() if izinli_native is None else ""
        komsu_metin = _komsu_grafikler(k, tuple(g.aralik) if g.aralik else None)
        sabit += [
            _motion_brif_ozeti(p, stil_ad),
            *([kasa_metin] if kasa_metin else []),
            aiedit._hf_katalogu(p.work, (k.sekans.w, k.sekans.h)),  # birincil motor (ADR 0050, 0062 — canlı gömme)
            _HF_TOKEN_OZETI,
            "## Native grafik kataloğu (HyperFrames karşılığı yoksa; yalnız bunlar)", *(katalog_satirlari or ["- (yalniz_bunlar aktif, seçili native bileşen yok)"]),
            *([komsu_metin] if komsu_metin else []),
            # WHY: bkz. wiki/decisions/0064-yaratici-yon.md
            "## Grafik ilkeleri",
            "- Bileşeni katalogdaki \"Ne zaman\" satırına, yaratıcı brifin görsel metaforuna, iplik öğesine ve enerji eğrisine göre seç; "
            "ezber şablonla doldurma.\n"
            "- Aralığına düşen imza anını kendi bileşen ya da özel kompozisyon seçiminle teslim et; sakin enerji dilimlerini bilinçli olarak boş bırakabilirsin.\n"
            "- İkonlar (`ikon/*`) yalnız seyrek destekçidir ve grafik kliplerinin en çok %30'u olabilir.\n"
            "- Tam-yüz konuşmacının üstüne ağır kart koyma; dört düzen arasında dolaş (`konusmaci` / `diyagram-pip` / `ekran-pip` / `tam-kanit`).\n"
            "- Bileşen ve kompozisyon seçimini raporda gerekçelendir.",
            "## Kesim geçişleri (kurgu editörünün; yalnız bilgi)", gecis_listesi,
        ]
    if any(x in katmanlar for x in ("sfx", "muzik", "stil")):
        from . import olaysesi
        sabit += [
            "## Ses rolleri (dosya seçme, rol yaz; olaysesi seçer)", ", ".join(sorted({*olaysesi.ROLLER, *olaysesi.KOMBOLAR})),
            # WHY: bkz. wiki/decisions/0064-yaratici-yon.md
            "## Yönetmenlik kuralları (ses ve stil)",
            "- Ses efekti bölüm açılışı (`acilis`, `vurgu_guclu`), geçiş ve önemli grafik girişi için birer adaydır ve enerji eğrisini izler; "
            "sessizlik de bilinçli bir seçimdir (sentetik yok; orta noktalı V1 geçişinin ve sesli hazır efektin sesi kendiliğinden gelir, aynı yere ikinci geçiş sesi koyma).\n"
            "- Hikâye ve duygu anlarında müzikte dinamik nefes ve ducking (`ses.duck: true`, gerekirse `ses.kf`) kur; doruk öncesi nefes boşaltmak güçlü kontrast üretir.\n"
            "- Biçim: `\"ses\": {\"gain_db\": -12, \"duck\": true, \"kf\": [{\"t\": 0.0, \"v\": -12}, {\"t\": 48.9, \"v\": -30, \"ease\": \"yumusak\"}]}`; "
            "`kf.t` klibin başından sn, `kf.v` dB. Müzik klibi `{\"tur\": \"ses\", \"iz\": \"A3\", \"kaynak\": \"<id>\", \"olay\": {\"muzik\": true}}`.",
        ]
    if "muzik" in katmanlar:
        sabit += ["## Müzik kütüphanesi (yalnız bunlar; `kaynaklar`a bu yolla ekle)", _muzik_katalogu()]
    if "kurgu" in katmanlar:
        stil_kurgu_ek = ""
        if stil_ad:
            from . import stil_katalog
            try:
                sk = stil_katalog.bul(stil_ad)
                par = []
                if sk.get("gecis"):
                    par.append("izinli geçişler (`gecis`): " + ", ".join(f"`{x}`" for x in sk["gecis"]))
                if sk.get("kacin"):
                    par.append("kaçın (`kacin`): " + "; ".join(sk["kacin"][:4]))
                if par:
                    stil_kurgu_ek = f"\n- Seçili stil (`{stil_ad}`) bağlayıcıdır — " + " | ".join(par) + "."
            except SystemExit:
                pass
        sabit += [
            "## Geçiş türleri (orta noktası kesimde, sesi kendiliğinden)", gecis_listesi,
            # WHY: bkz. wiki/decisions/0064-yaratici-yon.md
            "## Yönetmenlik kuralları (kurgu)",
            "- 0,4 saniye üstü ölü boşlukları, dolgu ve tekrarları kelime sınırında kırp (bilinçli dramatik sessizlik anları hariç).\n"
            "- Konuşan kafada yalnız durağanlık 4,5 saniyeyi geçerse `punch`, `el_kamerasi` veya `hizli_zoom` araçlarını değerlendir; her konuşan klibe otomatik koyma.\n"
            "- `odak_karart` aracını yalnız tipografi ekranda tek başına durmalıysa ve arka planı sakinleştirmek gerekiyorsa kullan.\n"
            "- Geçiş anlam değişimini söyler; kesimlerin %90'ı düz kesim kalır, videoda en çok 2–3 geçiş ailesi seçilir ve seçili stilin `gecis` listesi ile `kacin` listesi bağlayıcıdır."
            + stil_kurgu_ek
            + "\n- Yaratıcı yetki: match cut, hız rampası (`hiz`), J/L cut, pattern interrupt ve sessizlik sonrası vuruş araçlarını içerik ve brif gerektirdikçe kullan; zaman dilimin başına en az bir bilinçli yaratıcı karar ver ve bunu raporda ve `oz_denetim` içinde gerekçelendir.",
            aiedit._hazir_katalogu(),
        ]
    kendi = [c.model_dump(exclude_defaults=True) for c in k.klipler if atama.sahip(k, c) == rol]
    degisken = ["## Kullanıcı isteği", _istek_metni(istek),
                *yaratici.ekip_bolumu(yaratici.gecerli(p.work, istek)),  # ADR 0064: G0.5 brif bütün editörlere
                *([m] if (m := muzik_once.metin(soz.get("muzik_once"))) else []),  # ADR 0064 adım 8: müzik öncülü
                "## Görev kartın (orkestratör)", f"- Katmanlar: {', '.join(KATMAN_ADI[x] for x in katmanlar)}", f"- Aralık: {aralik}",
                *([f"- Odak: {g.odak}"] if g.odak else []),
                "## Zorunlu kurallar (her biri için kural_uyum yaz)", *(_kural_metinleri(zorunlu or [], d) or ["- (yok)"]),
                "## Ekip kartları", *atama.tablo(),
                "## Sözleşme", "```json", json.dumps(soz, ensure_ascii=False)[:6000], "```",
                "## Transkript özeti", _digest(p),
                "## Senin katmanın (şu anki klipler)", "```json", json.dumps(kendi, ensure_ascii=False)[:8000], "```",
                "## Diğer katmanlar (özet)", *(_katman_ozeti(k, rol, atama) or ["- (boş)"])]
    if pano := pano_oku(kok, rol, tuple(g.aralik) if g.aralik else None):
        degisken += ["## Pano (diğer editörlerin notları)"] + [f"- [{m['kimden']} {m['tip']} {m['aralik'][0]:.1f}-{m['aralik'][1]:.1f}] {m['metin']}" for m in pano]
    if onceki is not None:
        degisken += ["## Önceki yaman (düzeltilmiş TAM yamayı döndür; bu yamanın yerine geçer)", "```json",
                     onceki.model_dump_json(exclude_defaults=True)[:8000], "```"]
    if bulgular:
        degisken += ["## Düzelt (yalnız bunlar; başka şeye dokunma)", "```json", json.dumps(bulgular, ensure_ascii=False), "```"]
    if kisitlar:
        degisken += ["## Kısıtlar (orkestratör ve başka editörlerin bulguları)"] + [f"- {x}" for x in kisitlar]
    return "\n\n".join(sabit) + "\n\n" + "\n\n".join(degisken) + "\n"


# ---------------------------------------------------------------- orkestratör paketleri

def _o_basi(baslik: str) -> list[str]:
    return [f"# Ekip orkestratörü · {baslik}",
            "Rol tanımın sistem isteminde (ya da bu metnin sonunda). Dosya okuma, komut ve dosya yazma yok: bütün bağlam bu metinde. "
            "Yanıtın tamamı tek JSON nesnesi."]


def plan_paketi(p, k: Kurgu, ayar: EkipAyar, istek: str | None, varsayilan: Plan, *, suru_bolumu: list[str] | None = None,
                brif_iste: bool = False) -> str:
    """Orkestratörün plan istemi. `suru_bolumu` (ADR 0059): sabit seviye sayıları yerine ajan bütçesi ve seçilebilir modeller;
    hook'u E1 seçtiği için çıktıda hook yok, kartlarda motor/model/seviye var."""
    ne, nk = SEVIYE[ayar.ekip_seviye]
    son = _bitis(k)
    d = kural.yukle()
    etkin = kural.secim(d, rol="hepsi", **_kapsam(p))
    v1 = [c for c in k.klipler if c.iz == "V1"]
    if suru_bolumu:
        cikti = ('{"gorevler": [{"slot": "E1", "katmanlar": ["kurgu"], "aralik": null, "odak": "", "kurallar": ["K0003"]},\n'
                 '              {"slot": "E2", "katmanlar": ["grafik"], "aralik": [0, 20.5], "odak": "<en çok 3 satır>", "kurallar": [], '
                 '"motor": "claude|antigravity|codex|opencode|null", "model": "<listeden ya da null>", "seviye": "medium|null"}],\n'
                 ' "kk_gorevler": [{"slot": "K1", "rol": "kurgu|gorsel|ses|kurgu-ses|genel|kural|izleyici", "aralik": null, "odak": "", '
                 '"motor": null, "model": null}],\n')
    else:
        cikti = ('{"hook": {"bas": <sn>, "son": <sn>, "neden": "<tek satır>"},\n'
                 ' "gorevler": [{"slot": "E1", "katmanlar": ["kurgu"], "aralik": null, "odak": "<en çok 3 satır: isteğe göre ne yapacak>", "kurallar": ["K0003"]}],\n'
                 ' "kk_gorevler": [{"slot": "K1", "rol": "kurgu|gorsel|ses|kurgu-ses|genel|kural|izleyici", "aralik": null, "odak": ""}],\n')
    return "\n\n".join([
        *_o_basi("plan (G0)"),
        "## Kullanıcı isteği", _istek_metni(istek),
        *(suru_bolumu or ["## Seviye", f"`{ayar.ekip_seviye}`: {ne} editör ({', '.join(editorler(ayar.ekip_seviye))}), {nk} kalite kontrol "
                          f"({', '.join(kontroller(ayar.ekip_seviye))}). Sayılar sabittir; işi sen dağıtırsın."]),
        "## Katmanlar", *[f"- `{x}`: {KATMAN_TANIM[x]}" + (" (bölünmez: tek editör, aralık null)" if x in BOLUNMEZ else " (zaman dilimlerine bölünebilir)")
                          for x in KATMANLAR],
        "## Kalite kontrol rolleri", *[f"- `{r}`: {KK_ROL_ADI[r]}" for r in KK_ROL_ADI],
        "## Video", f"- Süre {son:.2f} sn, V1'de {len(v1)} çekim, sekans {k.sekans.w}x{k.sekans.h}, motion sıklığı `{ayar.motion}`",
        "## Transkript özeti (hook için)", _digest(p),
        "## Etkin kurallar (id, önem, rol)", *([f"- [{x.id} {x.onem} {x.hedef_rol}] {x.metin}" for x in etkin] or ["- (yok)"]),
        "## Varsayılan dağıtım (istek özel bir ağırlık istemiyorsa bunu temel al)", "```json",
        varsayilan.model_dump_json(include={"gorevler", "kk_gorevler"}), "```",
        # ADR 0064: brif yoksa (ya da istek değiştiyse) orkestratör yaratıcı yönü aynı yanıtta yazar; ek çağrı yok.
        *(yaratici.plan_bolumu() if brif_iste else []),
        "## Çıktı", "```json\n" + cikti
        + (' "yaratici_brif": ' + yaratici.CIKTI_ORNEGI.replace("\n", "\n  ") + ",\n" if brif_iste else "")
        + ' "gerekce": "<dağıtımın (ve model seçiminin) nedeni, en çok 5 satır>"}\n```',
        "Kurallar:\n"
        f"- Her katman × zaman tam bir editörde olur. Bölünen katmanda aralıklar 0–{son:.2f} sn'yi boşluksuz ve örtüşmesiz kapsar; "
        "kartın aralığı kartın bütün katmanlarına uygulanır. Kurgu ve stil bölünmez.\n"
        "- Ağırlığı isteğe göre ver: ses ağırlıklı istekte ses editörü, grafik ağırlıklı istekte grafik dilimi artar.\n"
        "- Her karta katmanına uyan P0/P1 kuralları ata (`kurallar`); P0'ları vedit ayrıca ekler.\n"
        "- Kalite kontrol kartları kurgu, görsel ve ses alanlarını birlikte kapsar.",
    ]) + "\n"


def _yama_ozeti(y: Yama) -> list[str]:
    sat = [f"- Yama: ekle {len(y.ekle)}, güncelle {len(y.guncelle)}, sil {len(y.sil)}, yeni kaynak {len(y.kaynaklar)}"
           + (f", hf {', '.join(y.hf)}" if y.hf else "")]
    for c in y.ekle[:20]:
        ne = ((c.get("bilesen") or {}).get("ad") or (c.get("hf") or {}).get("ad") or (c.get("olay") or {}).get("tur")
              or (c.get("metin") or "")[:30] or c.get("tur"))
        sat.append(f"  - + {c.get('id')} {c.get('iz')} {c.get('tur')} @{c.get('bas', 'çapa')} {ne}")
    # WHY: bkz. wiki/decisions/0064-yaratici-yon.md
    if y.oz_denetim and y.oz_denetim.strip():
        sat.append("- Öz denetim: " + " ".join(y.oz_denetim.split())[:200])
    return sat


def kapi_paketi(istek: str | None, atama: Atama, yamalar: dict[str, Yama], zorunlu: dict[str, list[str]],
                ihlal: dict[str, list[str]], genel: list[str]) -> str:
    d = kural.yukle()
    sat = [*_o_basi("kural kapısı (G2)"), "## Kullanıcı isteği", _istek_metni(istek), "## Editörler"]
    for s in atama.gorevler:
        y = yamalar.get(s)
        sat += [f"### {atama.etiket(s)}", "- Zorunlu kurallar:", *(_kural_metinleri(zorunlu.get(s, []), d) or ["  (yok)"])]
        if y is None:
            sat.append("- Yanıt yok ya da çözümlenemedi (düzeltmeye gönderilir).")
            continue
        sat += ["- Uyum:", *([f"  - {u.id}: {u.nasil}" for u in y.kural_uyum] or ["  (boş)"]), *_yama_ozeti(y),
                "- Rapor: " + " ".join(y.rapor.split())[:800],
                "- Deterministik ihlal: " + ("; ".join(ihlal.get(s, [])) or "yok")]
    sat += ["## Sahipsiz denetim uyarıları", *([f"- {x}" for x in genel[:20]] or ["- yok"]),
            "## Çıktı", '```json\n{"kararlar": [{"slot": "E2", "karar": "kabul|duzelt", "brif": "<duzelt ise: ne, nerede, ölçülebilir kabul ölçütü>"}], "not": ""}\n```',
            "Ölçüt: zorunlu kural eksik ya da ihlal edilmişse, yama reddedildiyse, kullanıcı isteğine aykırıysa `duzelt`; aksi `kabul`. "
            "Her editör için tam bir karar yaz."]
    return "\n\n".join(sat) + "\n"


def triyaj_paketi(istek: str | None, bulgular: list[dict], atama: Atama) -> str:
    alan = ("id", "hedef", "onem", "zaman", "katman", "kategori", "sorun", "beklenen", "kural_id", "kural_adayi", "kanit")
    return "\n\n".join([
        *_o_basi("triyaj ve kural (G5)"), "## Kullanıcı isteği", _istek_metni(istek), "## Ekip kartları", *atama.tablo(),
        "## Bulgular (tekilleştirilmiş)", "```json", json.dumps([{a: b.get(a) for a in alan} for b in bulgular], ensure_ascii=False), "```",
        "## Çıktı", '```json\n{"kabul": ["K1-001"], "red": [{"id": "K2-003", "neden": "<neden yanlış pozitif>"}], '
        '"kural_onay": ["<kural_adayi onaylanan bulgu id>"], "not": ""}\n```',
        "Ölçüt:\n- Kanıtı ve ölçülebilir beklentisi olan bulgu kabul edilir; isteğe aykırı ya da kanıtsız bulgu reddedilir.\n"
        # WHY: bkz. wiki/decisions/0064-yaratici-yon.md
        "- `etki` bulgusu zaman damgası, kare kanıtı ve brif maddesine (ya da kullanıcı isteğine) bağlı somut beklenti taşıyorsa kabul edilir; "
        "yalnız zevk tartışmasıysa reddedilir.\n"
        "- Kural adayı genelleşmiş, projeye özgü olmayan, tek emir satırıysa onaylanır; onaylanan aday kural deposuna işlenir ve "
        "düzeltmede editörlere zorunlu kural olarak gider.",
    ]) + "\n"


KURGU_OZET_EN_COK = 14000  # karakter
QC_METIN_GIRDI = ("kare listesi (zaman, yol, OCR)", "ölçüm (format, loudness, slop)", "kurgu-denetle", "stil token")


def kurgu_ozeti(k: Kurgu) -> str:
    """Klip başına tek satır: QC 47 KB'lık kurgu.json'u parça parça okumak için tur dönmesin (ADR 0054)."""
    sat = []
    for c in sorted(k.klipler, key=lambda c: (c.bas, c.iz)):
        ek = []
        if c.kaynak:
            ek.append(f"kaynak {c.kaynak}" + (f" @{c.giris:.2f}" if getattr(c, "giris", None) else ""))
        if c.metin:
            ek.append(f"“{' '.join(str(c.metin).split())[:60]}”")
        if c.bilesen:
            ek.append(f"bilesen {c.bilesen.ad} {json.dumps(c.bilesen.param, ensure_ascii=False)[:90]}")
        if c.hf:
            ek.append(f"hf {c.hf.get('ad')} {json.dumps(c.hf.get('param') or {}, ensure_ascii=False)[:90]}")
        if c.sablon:
            ek.append(f"sablon {c.sablon.get('ad')}")
        if c.olay and c.olay.get("tur"):
            ek.append(f"olay {c.olay.get('tur')}{'/' + str(c.olay['guc']) if c.olay.get('guc') else ''}")
        elif c.olay and c.olay.get("muzik"):
            ek.append("müzik")
        if c.hazir:
            ek.append("hazir " + ",".join(f"{e.get('ad')}@{e.get('t', 0)}" for e in c.hazir))
        if c.gecis_giris:
            ek.append(f"gecis {c.gecis_giris.tur}")
        sat.append(f"- {c.id} {c.iz} {c.tur} {c.bas:.2f}–{c.bas + c.sure:.2f}" + (f" · {' · '.join(ek)}" if ek else ""))
    t = "\n".join(sat)
    return t if len(t) <= KURGU_OZET_EN_COK else t[:KURGU_OZET_EN_COK] + "\n… (kırpıldı; tam kurgu dosyada)"


def _metin_girdi(ad: str, y) -> str:
    try:
        t = Path(y).read_text(encoding="utf-8")
    except OSError:
        return ""
    if Path(y).suffix == ".json":
        try:
            t = json.dumps(json.loads(t), ensure_ascii=False, separators=(",", ":"))
        except ValueError:
            pass
    return f"### {ad}\n{t[:9000]}"


def kontrol_istemi(p, kg: KkGorev, girdi: dict, atama: Atama, istek: str | None) -> Path:
    """Kalite kontrol kartından istem: rol dosyaları, aralık, odak, ekip kartları, rolün kural paketi."""
    kap = _kapsam(p)
    d = kural.yukle()
    if kg.rol == "kural":
        kurallar = "\n".join(f"- [{x.id} {x.onem} {x.hedef_rol}] {x.metin}" + (f" (ölçüt: {x.olcut})" if x.olcut else "")
                             for x in kural.secim(d, rol="hepsi", **kap))
    else:
        sat = []
        for r in KK_KURAL_ROLU.get(kg.rol, ["hepsi"]):
            sat += kural.paket(d, rol=r, **kap).splitlines()
        kurallar = "\n".join(dict.fromkeys(sat))
    ybrif = yaratici.oku(p.work)  # WHY: bkz. wiki/decisions/0064-yaratici-yon.md
    if ybrif is not None:
        olcut_kaynagi = "yaratıcı brife"
        olcut_detay = ("imza anı teslim edildi mi, enerji eğrisi (sakin ve doruk bölümler) hissediliyor mu, "
                       "brifteki yasak klişelerden biri kullanılmış mı, ")
    else:
        olcut_kaynagi = "kullanıcı isteğine"
        olcut_detay = ("ana fikir ya da doruk anı teslim edildi mi, enerji ve ritim değişimi hissediliyor mu, "
                       "tekrarlayan şablon klişeleri var mı, ")
    satir = [
        f"# Kalite kontrol {kg.slot}: {KK_ROL_ADI[kg.rol]}",
        "Rol tanımın sistem isteminde (ya da bu metnin sonunda). Hiçbir dosyayı değiştirme.",
        "## Kullanıcı isteği", _istek_metni(istek),
        *(["## Yaratıcı brif", yaratici.metin(ybrif)] if ybrif is not None else []),
        "## Üretim değeri",
        f"Taslağı yalnız kusur için değil, {olcut_kaynagi} karşı da oku: {olcut_detay}"
        "hook ilk saniyelerde kaydırmayı durduruyor mu? Kendine \"bu video şablon gibi mi, yoksa bu içeriğe özgü bir iş mi?\" sorusunu sor.\n"
        "- Sıradanlık, eksik imza anı, düz enerji, yasak klişe ya da zayıf hook görürsen `etki` kategorisinde bulgu yaz; "
        "`kanit` yine paftadaki karenin tam yolu, `beklenen` brif maddesine (brif yoksa kullanıcı isteğine) bağlı somut ölçüt olsun.\n"
        "- Yanıt JSON'una 1–5 arası `uretim_puani` ekle (`hook`, `imza_ani`, `brif_uyumu`, `ozgunluk`, `ritim_enerji`).",
        *(["## Bakacağın aralık", f"Yalnız {kg.aralik[0]:.1f}–{kg.aralik[1]:.1f} sn."] if kg.aralik else []),
        *(["## Orkestratörün odağı", kg.odak] if kg.odak else []),
        # Claude'da paftalar mesaja görsel olarak eklidir (ADR 0058); öteki motorlar yoldan açar.
        *(["## Önce paftalara bak (her biri 12 kare, köşede saniye; mesajda görsel olarak ekliyse ondan, değilse bu yollardan aç)",
           *[f"- `{Path(f).resolve()}`" for f in girdi["_paftalar"]],
           f"Tek kareyi yalnız ayrıntı gerektiğinde aç, en çok {QC_TEK_KARE}. Kareleri tek tek gezme; pafta yeter."]
          if girdi.get("_paftalar") else []),
        *(["## vedit'in ölçtükleri (zaten bulgu; tekrar yazma, yalnız gözle görülen kusura bak)", *[f"- {x}" for x in girdi["_vedit"]]]
          if girdi.get("_vedit") else []),
        # WHY: ADR 0054. Metin girdileri istemde: agy her dosya için ayrı model turu dönüyordu (arvelior-hiz K1: 13 metin okuması).
        "## Metin girdileri (burada; dosyayı ayrıca okuma)",
        *[m for ad in QC_METIN_GIRDI if ad in girdi and (m := _metin_girdi(ad, girdi[ad]))],
        *([f"### kurgu özeti (klip başına satır; tam kurgu yalnız gerekirse: `{Path(girdi['kurgu']).resolve()}`)",
           kurgu_ozeti(kurgu.oku(p.work))] if "kurgu" in girdi else []),
        "## Dosya girdileri",
        *[f"- {ad}: `{Path(y).resolve()}`" for ad, y in girdi.items() if not ad.startswith("_") and ad not in QC_METIN_GIRDI and ad != "kurgu"],
        "## Ekip kartları (katman ve zaman sahibi)", *atama.tablo(),
        "## Kural",
        "- Kusuru paftada (gerekirse tek karede) gör. `kanit` o saniyenin kare dosyasının tam yoludur (kare listesinden); dosya yoksa bulgu düşer.",
        "- Her bulgu ölçülebilir `beklenen` taşır (ör. “yazı 1080p'de en az 28 px”, “ses tepesi -1 dBTP altında”, “0,4 sn'de en çok bir ses”).",
        f"- `id` `{kg.slot}-001` biçiminde. `katman` iz kimliğidir (V1, V2, A2…) ya da `altyazi`; düzeltecek editörü vedit katman ve zamandan bulur, "
        "`hedef` yazarsan ekip kartlarından seç.",
        "- P0 yayına giremez, P1 düzeltilmeli, P2 küçük iyileştirme.",
        # WHY: bkz. wiki/decisions/0047-kural-deposu.md
        "- Bulgu etkin bir kuralı ihlal ediyorsa `kural_id` yaz (ör. `K0012`). Bulgu tek seferlik değil, başka videoda da "
        "geçerli bir dersse `kural_adayi` yaz: projeye özgü ad, saniye ve metin içermeyen, `YAP: ` ya da `YAPMA: ` ile başlayan "
        "tek emir satırı (ör. `YAPMA: ikonu yüzün ya da altyazı bandının üstüne koyma.`).",
        "## Etkin kurallar (bunlara göre denetle)", kurallar or "- (yok)",
        "## Yanıt", "Yanıtın sonunda tek bir ```json bloğu ver, başka JSON verme:",
        '```json\n{"bulgular": [{"id": "' + kg.slot + '-001", "hedef": "E1", "onem": "P1", "zaman": [12.4, 13.1], "katman": "V1", '
        '"kategori": "stil|okunurluk|ritim|ses|teknik|tutarlilik|etki", "kanit": "<kare yolu>", "sorun": "", "beklenen": "", '
        '"kural_id": "K0012 | null", "kural_adayi": "YAPMA: ... | null"}],\n'
        ' "uretim_puani": {"hook": 4, "imza_ani": 2, "brif_uyumu": 3, "ozgunluk": 3, "ritim_enerji": 4},\n'
        ' "brif": "<düzeltme brifi, markdown: bağlam, P0→P2 maddeler, her maddede zaman damgası ve ölçülebilir kabul ölçütü, dokunulmayacaklar>"}\n```',
    ]
    f = girdi["_kok"] / f"{kg.slot}.istem.md"
    f.write_text("\n\n".join(x for x in satir if x) + "\n", encoding="utf-8")
    return f


# ---------------------------------------------------------------- kural kapısı (deterministik kısım)

def _klip_sahipleri(metin: str, sahipler: dict[str, str]) -> list[str]:
    return sorted({s for kid, s in sahipler.items() if re.search(rf"(?<![\w-]){re.escape(kid)}(?![\w-])", metin)})


def kural_denetimi(p, taban: Kurgu, yamalar: dict[str, Yama], atama: Atama, zorunlu: dict[str, list[str]]) -> tuple[dict[str, list[str]], list[str]]:
    """G2'nin deterministik kısmı: kural_uyum kapsamı, deneme birleştirmesinde red/düşen öğe/çakışma ve kurgu denetimi.
    (slot başına ihlal, sahipsiz uyarılar)."""
    ihlal: dict[str, list[str]] = {s: [] for s in atama.gorevler}
    genel: list[str] = []
    for s in atama.gorevler:
        y = yamalar.get(s)
        if y is None:
            continue
        eksik = [i for i in zorunlu.get(s, []) if i not in {u.id for u in y.kural_uyum}]
        if eksik:
            ihlal[s].append(f"kural_uyum eksik: {', '.join(eksik)}")
    deneme_atama = Atama(list(atama.gorevler.values()))
    deneme, br = birlestir(taban.model_copy(deep=True), yamalar, deneme_atama)
    for s, m in br["red"].items():
        ihlal.setdefault(s, []).append(f"yama reddedildi: {m[:300]}")
    for x in br["dusen"]:
        ihlal.setdefault(x.split(":")[0], []).append(f"düşen öğe: {x.split(':', 1)[1]}")
    for b in br["cakisma_bulgu"] + br["capa_bulgu"]:
        (ihlal.setdefault(b["hedef"], []) if b.get("hedef") else genel).append(f"{b.get('klip')}: {b['sorun']}")
    sahipler = {c.id: s for c in deneme.klipler if (s := deneme_atama.sahip(deneme, c))}
    try:
        hatalar = [f"! {h}" for h in kurgu.denetle(p, deneme)]
        t = tema_token.oku(kurgu.etkin_tema(p, deneme.motion_tema))
        hatalar += [f"~ {u['bas']:.2f} sn {u['kod']}: {u['kanit']}" for u in kurgu_kalite.uyarilar(deneme, t, p=p)]
    except Exception as e:  # noqa: BLE001 - denetim eksik olsa da kapı karar verir
        hatalar = [f"! denetim çalışmadı: {str(e)[:200]}"]
    for h in hatalar:
        kim = _klip_sahipleri(h, sahipler)
        for s in kim:
            ihlal.setdefault(s, []).append(h[:300])
        if not kim:
            genel.append(h[:300])
    return {s: v for s, v in ihlal.items() if v}, genel


def _uyari_anahtari(u: dict) -> tuple[str, str]:
    return u["kod"], u.get("klip") or u["kanit"]


def yeni_uyarilar(p, once: Kurgu | None, sonra: Kurgu, atama: Atama, adaylar) -> dict[str, list[str]]:
    """`sonra`da olup `once`de olmayan kurgu_kalite uyarıları, slot başına metin olarak (`once` None: hepsi).

    Sahip adaylar (bu turda yama yazanlar) içinden klip id'siyle bulunur; bulunamazsa bütün adaylara gider: uyarıyı
    bu turun yamalarından biri doğurdu. WHY: bkz. wiki/decisions/0058-hizli-ve-kaliteli-edit.md (G6 uyarı kapısı)."""
    adaylar = sorted(set(adaylar), key=_no)
    if not adaylar:
        return {}
    t = tema_token.oku(kurgu.etkin_tema(p, sonra.motion_tema))
    eski = {_uyari_anahtari(u) for u in kurgu_kalite.uyarilar(once, t, p=p)} if once is not None else set()
    sahipler = {c.id: s for c in sonra.klipler if (s := atama.sahip(sonra, c))}
    out: dict[str, list[str]] = {}
    for u in kurgu_kalite.uyarilar(sonra, t, p=p):
        if _uyari_anahtari(u) in eski:
            continue
        kim = [s for s in _klip_sahipleri(u["kanit"], sahipler) if s in adaylar] or adaylar
        for s in kim:
            out.setdefault(s, []).append(f"Uyarı kapısı ({u['bas']:.2f} sn {u['kod']}): {u['kanit']}. {u['oneri']}. "
                                         + ("Bu uyarıyı senin düzeltmen doğurdu; bulgu düzeltmesini koru, uyarıyı gider." if once is not None
                                            else "Senin klibin; bulgularla birlikte bunu da gider."))
    return out


def _hata_klipleri(h: str, ids) -> list[str]:
    """Denetim satırının yapısal klip kimlikleri: `<id>: ...` başı ya da `<iz>: <a> ile <b> çakışıyor`. Serbest metin taranmaz:
    geçerli değer listeleri (ör. `hook`, `vurgu`) aynı adlı sağlıklı klibi düşürmesin."""
    if m := re.match(r"^\S+: (\S+) ile (\S+) çakışıyor", h):
        return [x for x in m.groups() if x in ids]
    m = re.match(r"^([^:\s]+):", h)
    return [m.group(1)] if m and m.group(1) in ids else []


def render_kurtar(p, k: Kurgu, hatalar: list[str], atama: Atama, br: dict) -> list[str]:
    """Render'ı bozan hata yalnız belli kurgu dışı kliplerdeyse o klipler düşer, kalan hata döner (boşsa kurgu temiz).

    WHY: bkz. wiki/decisions/0059-swarm-edit.md. g4b koşusunda tek rozetin parametre tipi (`seviye: 'yuksek'`) G3'te bütün
    edit'i durdurdu. Kurgu katmanı (V1, konuşma sesi) düşürülmez: hata orada ya da klipsizse eski davranış (durdur) sürer.
    Düşen klip sahibine P1 bulgusu olarak gider (G4 birleştirici, K9), G6'da doğru biçimde yeniden eklenebilir."""
    ids = {c.id: c for c in k.klipler}
    esle = {h: _hata_klipleri(h, ids) for h in hatalar}
    kotu = {x for v in esle.values() for x in v}
    if not kotu or not all(esle.values()) or any(katman_sinifi(k, ids[x].iz, ids[x]) == "kurgu" for x in kotu):
        return hatalar
    sahip = {x: atama.sahip(k, ids[x]) for x in kotu}
    k.klipler = [c for c in k.klipler if c.id not in kotu]
    if kurgu.denetle(p, k):
        k.klipler = sorted([*k.klipler, *(ids[x] for x in kotu)], key=lambda c: c.bas)
        return hatalar
    for x in sorted(kotu):
        c, neden = ids[x], next(h for h, v in esle.items() if x in v)
        br["dusen"].append(f"{sahip[x]}:{x}(render hatası)")
        br.setdefault("render_bulgu", []).append({"hedef": sahip[x], "klip": x, "iz": c.iz, "zaman": [round(c.bas, 2), round(c.bas + c.sure, 2)],
                                                  "sorun": f"render hatası yüzünden düştü: {neden[:200]}"})
    return []


# ---------------------------------------------------------------- QC birleştirici

def slop_bulgulari(qdir: Path, sure: float) -> list[dict]:
    """Ölçümün (olcum.json slop) P0/P1 bulguları ekip bulgusu olarak; QC bunları tekrar yazmaz (ADR 0054). id çağıranda verilir."""
    try:
        ol = json.loads((qdir / "olcum.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    from . import slop
    out = []
    for b in ((ol.get("slop") or {}).get("bulgular") or []):
        if b.get("seviye") not in ("P0", "P1"):
            continue
        kod = str(b.get("kod") or "")
        bas = float(b["bas"]) if b.get("bas") is not None else 0.0
        bit = float(b["bit"]) if b.get("bit") is not None else max(sure, bas + 0.1)
        out.append({"hedef": None, "onem": b["seviye"], "zaman": [round(bas, 2), round(max(bit, bas + 0.1), 2)], "katman": "V1",
                    "kategori": "ses" if kod.startswith("SES") else "ritim" if kod.startswith(("OLAY", "RITIM")) else "teknik",
                    "kanit": "", "sorun": f"{kod}: {b.get('kanit', '')}",
                    "beklenen": slop.ONERI.get(kod) or f"ölçümde {kod} çıkmaz"})
    return out


def bulgu_sinifi(k: Kurgu, b: dict) -> str | None:
    """Bulgunun katman sınıfı: iz kimliğinden (V2, A3) ya da stil alanından (altyazi, tema). Bilinmeyen: None."""
    if b.get("katman") in {i.id for i in k.izler}:
        return katman_sinifi(k, b["katman"])
    return "stil" if b.get("katman") in ("altyazi", "motion_tema", "stil", "tema") else None


def bulgu_birlestir(k: Kurgu, listeler: dict[str, list[dict]], atama: Atama | None = None) -> tuple[list[dict], dict[str, list[str]]]:
    """Tekilleştir (aynı katman, kategori ve örtüşen zaman: en ağır kalır), katman ve zamandan sahibe yolla,
    QC'nin yazdığı öteki editöre kısıt üret."""
    atama = atama or Atama.uc()
    hepsi = [b for kk in sorted(listeler, key=_no) for b in (listeler.get(kk) or [])]
    sira = {"P0": 0, "P1": 1, "P2": 2}
    kalan: list[dict] = []
    for b in sorted(hepsi, key=lambda b: sira[b["onem"]]):
        if any(x["kategori"] == b["kategori"] and x.get("katman") == b.get("katman") and x["zaman"][0] <= b["zaman"][1] + 0.3
               and b["zaman"][0] <= x["zaman"][1] + 0.3 for x in kalan):
            continue
        kalan.append(dict(b))
    kisit: dict[str, list[str]] = {e: [] for e in atama.gorevler}
    for b in kalan:
        orta = (b["zaman"][0] + b["zaman"][1]) / 2
        sinif = bulgu_sinifi(k, b)
        sahibi = atama.katman_sahibi(sinif, orta if sinif != "stil" else None) if sinif else None
        onceki = b.get("hedef")
        if sahibi is None:
            sahibi = onceki if onceki in atama.gorevler else atama.kurgu_sahibi()
        if onceki in atama.gorevler and onceki != sahibi:
            kisit[onceki].append(f"{b['zaman'][0]:.1f}-{b['zaman'][1]:.1f} sn: {b['sorun'][:160]} ({sahibi} düzeltiyor; sen bu aralıkta buna uy)")
        b["hedef"] = sahibi
    return kalan, kisit


def kural_dogrula(kabul: list[dict], sonuc: dict) -> dict:
    """G5: onaylanan her kural adayı depoda aktif ya da öneri olarak var mı (yeniden okunarak)."""
    d = kural.yukle()
    dogru, yok = [], []
    for b in kabul:
        aday = b.get("kural_adayi")
        if not aday or aday in sonuc.get("mezar", []):
            continue
        k = kural.bul_benzer(d, aday, durumlar=("aktif", "oneri"))
        (dogru if k else yok).append(k.id if k else aday)
    return {"dogrulanan": sorted(set(dogru)), "dogrulanamayan": yok}


# ---------------------------------------------------------------- ölçüm

def token_ozeti(meta: dict, istem_metni: str, cikti_metni: str, gorsel: int = 0) -> dict:
    """Motor token verdiyse o; vermediyse tahmin: (istem + çıktı) / 4 + görsel başına 1500 ('tahmini')."""
    t = meta.get("token") or {}
    toplam = sum(v for kk, v in t.items() if isinstance(v, (int, float)))
    if toplam:
        return {"token": int(toplam), "tahmini": False}
    return {"token": int((len(istem_metni) + len(cikti_metni)) / 4 + gorsel * 1500), "tahmini": True}


# ---------------------------------------------------------------- render

# ---------------------------------------------------------------- ajan çağrısı ve çıktı çözümleme

def _cagir(p, ayar: EkipAyar, rol: str, metin: str, kok: Path, mod: str, durum, *, roller=(), araclar: str = "",
           dizinler: tuple = (), gorseller: list[Path] | None = None) -> tuple[str, dict]:
    """Tek ajan çağrısı: istem dosyası + yanıt; bir yeniden deneme, sonra yedek motor. (yanıt, ölçüm).

    Claude yalın çağrılır (ADR 0054): metin stdin'den, rol tanımı sistem isteminden. Dosyayı okuyan motorlar (agy) için
    rol tanımı istem dosyasının sonuna eklenir; böylece hiçbir motor rol dosyası okumak için tur dönmez."""
    kok.mkdir(parents=True, exist_ok=True)
    f = kok / f"{rol}.istem.md"
    sistem = rol_metni(roller) if roller else ""
    f.write_text(metin + (f"\n\n## Rol tanımın\n\n{sistem}\n" if sistem else ""), encoding="utf-8")
    istem = (f"Read the file {f.resolve()} completely and do exactly what it says. "
             + ("Do not modify any file." if mod == "plan" else "Do not run shell commands and do not write files: return only the JSON."))
    meta: dict = {}
    for deneme, yedek in ((1, False), (2, True)):
        sl = ayar.slot(rol)
        if yedek and not sl.yedek_motor:
            break
        # Kart ve üst rozet o an gerçekten çalışan motoru göstersin (yedekte yedek motor).
        durum.slot(rol, durum="yedek" if yedek else "calisiyor", cikti=str(kok / f"{rol}.cikti.txt"),
                   motor=sl.yedek_motor if yedek else sl.motor, model=sl.yedek_model if yedek else sl.model)
        ok, yanit, meta = ekip.ajan(sl, istem, mod, kok / rol, yedek=yedek, metin=metin, sistem=sistem or None,
                                    araclar=araclar, dizinler=dizinler, gorseller=gorseller)
        gorsel = 30 if rol.startswith("K") else 0
        meta.update(deneme=deneme, **token_ozeti(meta, metin, yanit, gorsel))
        # WHY: v1 ölçümünde 5-8 sn ve 0 token biten Claude slotları başarılı sayılıyordu (sessiz başarısızlık).
        if ok and not yanit.strip():
            ok, meta["hata"] = False, "boş yanıt"
        (kok / f"{rol}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        if ok:
            durum.slot(rol, durum="bitti", sure=meta.get("sure"), token=meta["token"], tahmini=meta["tahmini"])
            return yanit, meta
    durum.slot(rol, durum="hata")
    return "", meta


def _nesne(metin: str, anahtarlar: tuple[str, ...]) -> dict | None:
    """Metindeki, anahtarlardan birini taşıyan son JSON nesnesi (```json bloğu önce)."""
    for b in reversed(re.findall(r"```json\s*(\{.*?\})\s*```", metin or "", flags=re.S)):
        try:
            o = json.loads(b)
        except ValueError:
            continue
        if isinstance(o, dict) and any(a in o for a in anahtarlar):
            return o
    dec = json.JSONDecoder()
    for i in [m for m in range(len(metin or "")) if metin[m] == "{"][:400]:
        try:
            o, _ = dec.raw_decode(metin[i:])
        except ValueError:
            continue
        if isinstance(o, dict) and any(a in o for a in anahtarlar):
            return o
    return None


def _sema(metin: str, sema: type[BaseModel], anahtarlar: tuple[str, ...]):
    o = _nesne(metin, anahtarlar)
    if o is None:
        return None
    try:
        return sema.model_validate(o)
    except ValidationError:
        return None


def _yama_cikar(metin: str) -> Yama | None:
    return _sema(metin, Yama, ("ekle", "guncelle", "sil", "hook", "kural_uyum"))


class OnUretim:
    """Editörün yaması gelir gelmez motion webm'lerini arka planda üretir; G3'teki bağlama önbellekten okur.

    WHY: bkz. wiki/decisions/0058-hizli-ve-kaliteli-edit.md. HyperFrames ve şablon webm'i dosya adındaki özetle önbelleklidir
    (`hf_grafik.uret`, `motion.sablon_uret`); editörler LLM beklerken CPU boştur, render seri yolda G3'e yığılıyordu.
    Hata yutulur: bağlama aynı işi yeniden dener ve kendi hata yolunu (`_bagla`) izler."""

    def __init__(self, p, k: Kurgu, es: int = 2):
        self.p, self.k, self.havuz, self.isler, self.kilit = p, k, ThreadPoolExecutor(max_workers=es), {}, threading.Lock()

    def _uret(self, alan: str, d: dict) -> None:
        from . import hf_grafik, motion
        tema = kurgu.etkin_tema(self.p, d.get("tema") or self.k.motion_tema)
        hedef = self.p.work / "public" / "motion"
        if alan == "hf":
            hf_grafik.uret(d["ad"], d.get("param"), tema, self.p.work, hedef, sekans=(self.k.sekans.w, self.k.sekans.h))
        else:
            motion.sablon_uret(d["ad"], d.get("param"), tema, hedef, sekans=(self.k.sekans.w, self.k.sekans.h))

    def ekle(self, y: Yama) -> None:
        for c in [*y.ekle, *y.guncelle]:
            for alan in ("hf", "sablon"):
                d = c.get(alan) if isinstance(c, dict) else None
                if not isinstance(d, dict) or not d.get("ad"):
                    continue
                anahtar = (alan, json.dumps(d, sort_keys=True, ensure_ascii=False))
                with self.kilit:
                    if anahtar not in self.isler:
                        self.isler[anahtar] = self.havuz.submit(self._uret, alan, dict(d))

    def bekle(self) -> int:
        """Bitenlerin sayısı; hata sayılmaz (bağlama kendisi dener)."""
        n = 0
        for f in list(self.isler.values()):
            try:
                f.result()
                n += 1
            except Exception:  # noqa: BLE001 - ön üretim en iyi çaba
                pass
        self.havuz.shutdown(wait=False)
        return n


def _bagla(p, k: Kurgu) -> None:
    """motion_bagla; render edilemeyen grafik (bilinmeyen hf adı, alfasız çıktı) ekip akışını düşürmez, klip çıkarılır."""
    try:
        kurgu.motion_bagla(p, k)
        return
    except (ValueError, RuntimeError) as e:
        hata = str(e)
    from . import hf_grafik
    kalan = []
    for c in k.klipler:
        if c.tur == "motion" and c.hf and not c.kaynak:
            if not hf_grafik.bul(c.hf.get("ad") or "", p.work):
                print(f"  ! {c.id}: HyperFrames kompozisyonu bulunamadı, klip çıkarıldı ({hata[:120]})")
                continue
        kalan.append(c)
    k.klipler = kalan
    try:
        kurgu.motion_bagla(p, k)
    except (ValueError, RuntimeError) as e:  # ikinci deneme de düşerse bağlanmayan hf klipleri çıkar
        print(f"  ! motion bağlanamadı: {str(e)[:200]}")
        k.klipler = [c for c in k.klipler if not (c.tur == "motion" and c.hf and not c.kaynak)]


# ---------------------------------------------------------------- akış

AJAN_BELLEK_GB = 0.8  # bir ajan CLI sürecinin tepe belleği (claude, agy); ölçüm: reel-video medium koşusu
BELLEK_PAY_GB = 2.0   # sistem ve Stüdyo için ayrılan


def ajan_eszamanlilik(ayar: EkipAyar, bos: float | None = None) -> int:
    """Aynı anda çalışacak ajan sayısı. Açık `eszamanlilik` kazanır; yoksa editör sayısı, boş belleğe sığacak kadar (en az 2).

    WHY: max seviyede varsayılan on ajan süreci aynı anda açılır; 15,8 GB makinede instagram/1 koşusu bellek yüzünden düşmüştü."""
    if ayar.eszamanlilik:
        return ayar.eszamanlilik
    from . import hf_kurgu
    bos = hf_kurgu.bos_bellek_gb() if bos is None else bos
    if bos is None:
        return ayar.es()
    return max(2, min(ayar.es(), int((bos - BELLEK_PAY_GB) / AJAN_BELLEK_GB)))


def _uretim_puani_cikar(o: dict | None) -> dict[str, int] | None:
    """Ham QC JSON sözlüğünden üretim puanını çıkarır ve KontrolCikti ile doğrular (ekip.bulgu_dogrula düşürdüğü için).

    WHY: bkz. wiki/decisions/0064-yaratici-yon.md."""
    if not isinstance(o, dict) or "uretim_puani" not in o:
        return None
    return KontrolCikti.model_validate({"uretim_puani": o.get("uretim_puani")}).uretim_puani


def _uretim_puani_ort(puanlar: list[dict[str, int] | None]) -> dict[str, float] | None:
    """QC kartlarının üretim puanlarından anahtar başına ortalama; geçerli puan yoksa None.

    WHY: bkz. wiki/decisions/0064-yaratici-yon.md."""
    topla: dict[str, list[int]] = {}
    for p in puanlar:
        if not isinstance(p, dict):
            continue
        for k, v in p.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                topla.setdefault(k, []).append(v)
    if not topla:
        return None
    return {k: round(sum(v) / len(v), 2) for k, v in topla.items()}


def calistir(p, ayar: EkipAyar, *, notu: str | None = None, final: bool = False, tekrar_denetle: bool = False) -> dict:
    kok = p.work / "edit" / "ekip"
    kok.mkdir(parents=True, exist_ok=True)
    (kok / "pano.json").unlink(missing_ok=True)
    if ayar.hizli and ayar.ekip_seviye != "low":
        ayar = ayar.model_copy(update={"ekip_seviye": "low"})  # WHY: ADR 0054; hızlı ön ayar 2 editör + 1 QC
    durum = ekip.Durum(kok, ayar, KAPILAR)
    try:
        return _akis(p, ayar, kok, durum, notu=notu, final=final, tekrar_denetle=tekrar_denetle)
    except BaseException as e:
        # WHY: çöken iş panelde açık kapıda asılı kalmasın; hata ve kapı durum dosyasına yazılır (2026-11-23 olayı)
        acik = [k for k in durum.d.get("kapilar", []) if k.get("durum") == "acik"]
        for k in acik:
            k["durum"], k["not"] = "kaldi", f"hata: {type(e).__name__}"
        durum.ayarla(hata=f"{type(e).__name__}: {str(e)[-400:]}", asama=f"Hata ({acik[0]['ad']})" if acik else "Hata",
                     bitti=True, bitis=time.time())
        raise


def _akis(p, ayar: EkipAyar, kok: Path, durum, *, notu: str | None, final: bool, tekrar_denetle: bool) -> dict:
    t0 = time.time()
    if not aiedit._hazir_mi(p):
        hizli.hazirla(p)
    if ayar.stil:
        ekip._stil_sec(p, ayar.stil)
    k = aiedit._kurgu_hazirla(p)
    once = k
    olcum: dict[str, dict] = {}
    kapilar: dict[str, str] = {}
    ritim_f = p.work / "edit" / "ritim.json"
    ritim = json.loads(ritim_f.read_text(encoding="utf-8")) if ritim_f.exists() else None
    es = ajan_eszamanlilik(ayar)
    if es < ayar.es():
        print(f"  Ajan eşzamanlılığı {ayar.es()} → {es} (boş bellek az)", flush=True)
    havuz = ThreadPoolExecutor(max_workers=es)
    on_uretim = OnUretim(p, k)
    try:
        return _akis_govde(p, ayar, kok, durum, notu=notu, final=final, tekrar_denetle=tekrar_denetle, t0=t0, k=k, once=once,
                           olcum=olcum, kapilar=kapilar, ritim=ritim, havuz=havuz, on_uretim=on_uretim)
    finally:
        # WHY: bkz. wiki/decisions/0059-swarm-edit.md. Hata yolunda bekleyen editörler başlamasın; plana paralel E1 ve
        # süren çağrılar arka planda biter ama yeni iş açılmaz.
        havuz.shutdown(wait=False, cancel_futures=True)


def _akis_govde(p, ayar: EkipAyar, kok: Path, durum, *, notu, final, tekrar_denetle, t0, k, once, olcum, kapilar, ritim, havuz,
                on_uretim) -> dict:

    def kapi(kid: str, d: str, not_: str = ""):
        kapilar[kid] = f"{d}{' · ' + not_ if not_ else ''}"
        durum.kapi(kid, d, not_)

    # G0 plan. Swarm (ADR 0059): orkestratör ajan sayısını (tavan içinde), kartları ve her ajanın modelini seçer.
    # Kurgu editörü (E1) plandan bağımsızdır (bölünmez, tam aralık): plan çağrısıyla aynı anda başlar, hook'u o seçer.
    kapi("G0", "acik")
    durum.slot(ORKESTRATOR, rol="Orkestratör")
    son_sn = _bitis(k)
    boy = "low" if ayar.hizli else suru.varsayilan_boy(son_sn, ayar.tavan())
    varsayilan = varsayilan_dagitim(boy, k)
    atama = Atama(varsayilan.gorevler)
    depo = kural.yukle()
    zorunlu = {g.slot: zorunlu_kurallar(p, g, depo, doldur=True) for g in varsayilan.gorevler}
    soz = sozlesme(p, k, None, ritim)
    # WHY: bkz. wiki/decisions/0064-yaratici-yon.md (adım 8). Parça editörlerden önce seçilir; LLM çağrısı yok, analiz önbellekli.
    if muzik := muzik_once.hazirla(p, yaratici.gecerli(p.work, notu), notu, son_sn):
        soz["muzik_once"] = muzik
    (kok / "sozlesme.json").write_text(json.dumps(soz, ensure_ascii=False, indent=1), encoding="utf-8")

    def editor(rol: str, kdir: Path, *, bulgular=None, kisitlar=None, onceki=None, zor=None, taban=None, anlik=None):
        # anlik: (ayar, atama, zorunlu) sabit görüntüsü. E1 plana paralel çalışırken ana iş parçacığı bu adları yeniden
        # bağlar; E1 başladığı andaki görüntüyle biter (ADR 0059).
        ayar_, atama_, zorunlu_ = anlik or (ayar, atama, zorunlu)
        yanit, meta = _cagir(p, ayar_, rol, paket(p, taban or k, rol, soz, kok, atama_, istek=notu, zorunlu=zor or zorunlu_.get(rol),
                                                  bulgular=bulgular, kisitlar=kisitlar, onceki=onceki), kdir, "duzenle", durum,
                             roller=editor_rolleri(atama_, rol))
        olcum[f"{kdir.name}/{rol}"] = meta
        y = _yama_cikar(yanit)
        if y and y.hf:
            y = hf_ad_ayir(rol, y, atama_)
        if y and y.pano:
            pano_ekle(kok, rol, y.pano)
        if y and y.hf:
            hf_yaz(p, rol, y, atama_)  # kompozisyon klipten önce diskte olmalı: birleştirmede denetlenir (ADR 0050)
        if y and not hf_hatalari(rol, y, atama_):
            on_uretim.ekle(y)
        return rol, y

    # G0.5 yaratıcı brif (ADR 0064): aynı istekle yazılmış ya da kilitli brif yeniden kullanılır. E1 plana paralel başladığı
    # için ilk turda yalnız var olan brifi görür; düzeltme turları yeni brifi görür.
    brif = yaratici.gecerli(p.work, notu)
    brif_durum = "var" if brif else "yok"
    e1 = atama.kurgu_sahibi()
    durum.slot(e1, rol=KATMAN_ADI["kurgu"], aralik=None)
    e1_is = havuz.submit(editor, e1, kok / "duzen", anlik=(ayar, atama, dict(zorunlu)))
    modeller: dict[str, list[str]] = {}
    if ayar.hizli:
        # Hızlı: orkestratör plan yapmaz; varsayılan dağıtım (ADR 0054). Brif yoksa E1 çalışırken tek kısa çağrıyla yazılır.
        plan, plan_hata = varsayilan, []
        if brif is None:
            yanit, meta = _cagir(p, ayar, ORKESTRATOR, yaratici.paket(notu, _digest(p), sure=son_sn, studyo=p.studyo,
                                                                       stil=_stil_ozeti(p)),
                                 kok / "brif", "plan", durum, roller=O_ROL)
            olcum["brif/O"] = meta
            brif = yaratici.yaz(p.work, _nesne(yanit, ("tez",)), notu)
            brif_durum = "yeni" if brif else "geçersiz"
        else:
            durum.slot(ORKESTRATOR, durum="atlandi")
    else:
        try:
            modeller = suru.model_listesi()
        except Exception as e:  # noqa: BLE001 - model listesi yoksa orkestratör grup ayarıyla dağıtır
            print(f"  Model listesi alınamadı ({str(e)[:120]}); kartlar grup ayarıyla çalışır", flush=True)
        bolum = suru.plan_bolumu(ayar, modeller, ayar.slot(e1))
        yanit, meta = _cagir(p, ayar, ORKESTRATOR, plan_paketi(p, k, ayar, notu, varsayilan, suru_bolumu=bolum, brif_iste=brif is None),
                             kok / "plan", "plan", durum, roller=O_ROL)
        olcum["plan/O"] = meta
        plan = _sema(yanit, Plan, ("gorevler", "kk_gorevler"))
        if brif is None:
            # Plan geçersiz olsa da brif ayrıca kurtarılır: biri ötekini düşürmez.
            brif = yaratici.yaz(p.work, (_nesne(yanit, ("yaratici_brif",)) or {}).get("yaratici_brif"), notu)
            brif_durum = "yeni" if brif else "geçersiz"
        plan_hata = suru.plan_dogrula(plan, ayar.tavan(), son_sn, modeller or None) if plan else ["plan çözümlenemedi"]
    dagitim = "hizli" if ayar.hizli else "orkestrator" if not plan_hata else "varsayilan"
    if plan_hata:
        plan = varsayilan
    plan = plan.model_copy(update={"hook": None})
    # Model listesi yoksa kart seçimi doğrulanamaz: uygulanmaz, grup ayarı çalışır.
    if dagitim == "orkestrator" and modeller and (ez := suru.ezme(plan, ayar, modeller)):
        ayar = ayar.model_copy(update={"ezme": {**ayar.ezme, **ez}})
    atama = Atama(plan.gorevler)
    zorunlu = {g.slot: (zorunlu[g.slot] if g.slot == e1 else zorunlu_kurallar(p, g, depo, doldur=dagitim != "orkestrator"))
               for g in plan.gorevler}
    gecerli = {ORKESTRATOR, *atama.gorevler, *(g.slot for g in plan.kk_gorevler)}
    durum.daralt(gecerli)
    for g in [*plan.gorevler, *plan.kk_gorevler]:
        sl = ayar.slot(g.slot)
        rol = ", ".join(KATMAN_ADI[x] for x in g.katmanlar) if isinstance(g, Gorev) else KK_ROL_ADI[g.rol]
        durum.slot(g.slot, rol=rol, aralik=g.aralik, **({} if g.slot == e1 else {"motor": sl.motor, "model": sl.model, "seviye": sl.seviye}))
    kk_kart = {g.slot: g for g in plan.kk_gorevler}
    durum.ayarla(dagitim=dagitim, en_cok=None if ayar.hizli else ayar.tavan(),
                 kurallar={**durum.d["kurallar"], "atanan": sum(len(v) for v in zorunlu.values())})
    ne, nk = len(plan.gorevler), len(plan.kk_gorevler)
    kapi("G0", "gecti", (f"orkestratör dağıttı: {ne} editör + {nk} QC (tavan {ayar.tavan()})" if dagitim == "orkestrator"
                         else "atlandı (hızlı): varsayılan dağıtım" if dagitim == "hizli"
                         else f"varsayılan dağıtım {boy} ({'; '.join(plan_hata)[:200]})") + f" · yaratıcı brif {brif_durum}")
    (kok / "plan.json").write_text(plan.model_dump_json(indent=1), encoding="utf-8")

    # G1 düzen: E1 zaten çalışıyor; öteki editörler aynı anda
    kapi("G1", "acik")
    otekiler = [r for r in atama.gorevler if r != e1]
    if e1_is.done() and e1_is.exception():
        raise e1_is.exception()  # E1 G0'da düştüyse öteki editörler boşa çalışmasın
    sonuclar = [*havuz.map(lambda r: editor(r, kok / "duzen"), otekiler), e1_is.result()]
    yamalar = {r: y for r, y in sorted(sonuclar, key=lambda x: _no(x[0])) if y is not None}
    eksik_yanit = [r for r in atama.gorevler if r not in yamalar]
    kapi("G1", "gecti" if not eksik_yanit else "kaldi", f"yanıtsız: {', '.join(eksik_yanit)}" if eksik_yanit else f"{len(yamalar)} yama")

    # G2 kural kapısı: deterministik denetim + orkestratör kararı; düzelt alan editör bir kez, paralel
    kapi("G2", "acik")
    ihlal, genel = kural_denetimi(p, k, yamalar, atama, zorunlu)
    karar = None
    # WHY: ADR 0054. Deterministik kapı temizse O'nun kararı beklenmez (arvelior: her koşuda 52 sn seri bekleme).
    o_kapi = not ayar.hizli and bool(ihlal or genel or eksik_yanit)

    def kapi_duzelt(r, brif: str = ""):
        kis = [*([brif] if brif else []), *ihlal.get(r, [])]
        return editor(r, kok / "kapi", kisitlar=kis, onceki=yamalar.get(r))
    # Sert ihlal (eksik kural_uyum, reddedilen yama, yanıtsız editör) orkestratörün kabulüyle geçmez. WHY: ADR 0058; bu yüzden
    # düzeltmesi O'nun kararı beklenmeden başlar (medium: kapı çağrısı 51 sn, düzeltmeler ardından seri).
    sert = sorted({s for s, v in ihlal.items() if any(x.startswith(("kural_uyum eksik", "yama reddedildi")) for x in v)}
                  | set(eksik_yanit), key=_no)
    erken = {r: havuz.submit(kapi_duzelt, r) for r in sert}
    if o_kapi:
        yanit, meta = _cagir(p, ayar, ORKESTRATOR, kapi_paketi(notu, atama, yamalar, zorunlu, ihlal, genel), kok / "kapi", "plan", durum,
                             roller=O_ROL)
        olcum["kapi/O"] = meta
        karar = _sema(yanit, KapiCikti, ("kararlar",))
    duzelt = {x.slot: x.brif for x in (karar.kararlar if karar else []) if x.karar == "duzelt" and x.slot in atama.gorevler
              and x.slot not in erken}
    if karar is None:  # O yanıt vermediyse (ya da çağrılmadıysa) bütün ihlaller düzeltilir
        duzelt.update({s: "" for s in ihlal if s not in erken})
    gec = {r: havuz.submit(kapi_duzelt, r, duzelt[r]) for r in sorted(duzelt, key=_no)}
    gelen: list[str] = []
    dusen_duzeltme: list[str] = []
    if erken or gec:
        for r, is_ in [*erken.items(), *gec.items()]:
            _, y = is_.result()
            if y is not None:
                yamalar[r] = y
                gelen.append(r)
        # WHY: düzeltmesi çözümlenemeyen editör eskiden "düzeltilen" sayılıyordu (reel-video E3, 2026-11-23).
        dusen_duzeltme = [r for r in sorted([*erken, *gec], key=_no) if r not in gelen]
        gelen = sorted(gelen, key=_no)
        ihlal, genel = kural_denetimi(p, k, yamalar, atama, zorunlu)
    uyum_eksik = sum(1 for v in ihlal.values() for x in v if x.startswith("kural_uyum eksik"))
    durum.ayarla(kurallar={**durum.d["kurallar"], "uyum_eksik": uyum_eksik})
    kapi("G2", "gecti" if not ihlal else "kaldi",
         ("" if o_kapi else "deterministik (orkestratör çağrılmadı); ")
         + (f"düzeltilen: {', '.join(gelen)}; " if gelen else "")
         + (f"düzeltmesi gelmedi (ilk yama kaldı): {', '.join(dusen_duzeltme)}; " if dusen_duzeltme else "")
         + (f"kalan ihlal: {', '.join(sorted(ihlal, key=_no))}" if ihlal else "temiz"))

    # G3 deterministik birleştirme + tek render
    kapi("G3", "acik")
    taban_rev = kurgu.oku(p.work).rev
    yeni, br = birlestir(k, yamalar, atama)
    br["oto"] = oto_duzelt(yeni)
    hatalar = kurgu.denetle(p, yeni)
    if hatalar:
        hatalar = render_kurtar(p, yeni, hatalar, atama, br)
    if hatalar:
        # WHY: bozuk kurgu diske yazılırsa Stüdyo önizlemesi ve sonraki her edit aynı hatayla düşer (reel-video 2026-11-23).
        br["denetle"] = hatalar[:10]
        raise SystemExit("Birleşen kurgu render edilemez; diskteki kurgu korunuyor:\n  " + "\n  ".join(hatalar[:10]))
    kurgu.yaz(p.work, yeni, beklenen_rev=taban_rev)  # WHY: kullanıcı Stüdyo'da yazdıysa ezilmez (RevCakismasi)
    yeni = kurgu.oku(p.work)
    t_bag = time.time()
    hazir_motion = on_uretim.bekle()
    _bagla(p, yeni)
    kurgu.yaz(p.work, yeni)
    t_render = time.time()
    video = hizli.qc_taslak(p)  # WHY: ADR 0058; QC videosu 15 fps, özet aynıysa atlanır
    alt_sure = {"bagla": round(t_render - t_bag, 1), "render": round(time.time() - t_render, 1), "on_uretim": hazir_motion}  # WHY: ADR 0058; QC videosu 15 fps, özet aynıysa atlanır
    kapi("G3", "gecti" if not br["red"] else "kaldi", f"uygulanan {len(br['uygulanan'])}, reddedilen {len(br['red'])}, düşen öğe {len(br['dusen'])}"
         + (f", vedit düzeltti {len(br['oto'])}" if br["oto"] else "")
         + f"; bağlama {alt_sure['bagla']:g} sn (önceden hazır {alt_sure['on_uretim']}), QC render {alt_sure['render']:g} sn")

    # G4 QC: bütün kalite kontrol kartları aynı anda, ortak paket
    kapi("G4", "acik")
    qdir = kok / "qc"
    t_izle = time.time()
    girdi = ekip.izle(p, video, qdir)
    alt_sure["izle"] = round(time.time() - t_izle, 1)

    if ayar.hizli:
        kk_kart = {g.slot: g for g in hizli_kk(yeni)}  # dilimler birleşen kurgunun süresinden
        plan = plan.model_copy(update={"kk_gorevler": list(kk_kart.values())})
        for g in kk_kart.values():
            durum.slot(g.slot, rol=KK_ROL_ADI[g.rol], aralik=g.aralik, motor=ayar.slot(g.slot).motor, model=ayar.slot(g.slot).model)

    def kontrol(kk: str):
        kgirdi = {**girdi, "_paftalar": pafta_sec(girdi, kk_kart[kk].aralik)}
        f = kontrol_istemi(p, kk_kart[kk], kgirdi, atama, notu)
        # QC kareleri görmek zorunda: Claude'a (yedekte) yalnız Read verilir, proje work klasörü okunabilir.
        yanit, meta = _cagir(p, ayar, kk, f.read_text(encoding="utf-8"), qdir, "plan", durum, roller=KK_ROL_DOSYASI[kk_kart[kk].rol],
                             araclar="Read", dizinler=(p.work,), gorseller=[*kgirdi["_paftalar"], *([girdi["kontak sayfası"]] if girdi.get("kontak sayfası") else [])])
        olcum[f"qc/{kk}"] = meta
        o = ekip.json_cikar(yanit) if yanit else None
        c, _ = ekip.bulgu_dogrula(o, kk) if o is not None else (None, [])
        puan = _uretim_puani_cikar(o if o is not None else (_nesne(yanit, ("uretim_puani",)) if yanit else None))
        return kk, [b.model_dump() for b in c.bulgular] if c else [], puan

    qc_sonuc = list(havuz.map(kontrol, sorted(kk_kart, key=_no)))
    listeler = {kk: b for kk, b, _ in qc_sonuc}
    uretim_puani = _uretim_puani_ort([puan for _, _, puan in qc_sonuc])
    for i, b in enumerate(slop_bulgulari(qdir, _bitis(yeni))):  # QC'ye "tekrar yazma" denen ölçüm bulguları sahibine gider
        listeler.setdefault("K9", []).append({**b, "id": f"K9-{800 + i:03d}"})
    for i, b in enumerate(br["capa_bulgu"] + br["cakisma_bulgu"] + br.get("render_bulgu", [])):  # vedit'in kendi bulguları da birleştiriciye girer
        listeler.setdefault("K9", []).append(
            {"id": f"K9-{900 + i:03d}", "hedef": b.get("hedef"), "onem": "P1", "zaman": list(b.get("zaman") or [0, 0.1]),
             "katman": b.get("iz", "V2"), "kategori": "tutarlilik", "kanit": "", "sorun": b["sorun"], "beklenen": "çakışma yok"})
    bulgular, kisit = bulgu_birlestir(yeni, listeler, atama)
    kapi("G4", "gecti", f"{len(bulgular)} bulgu")

    # G5 triyaj + kural işleme: orkestratör ayıklar ve onaylar, vedit depoya işler ve doğrular
    kapi("G5", "acik")
    reddedilen: list[dict] = []
    tri = None
    if bulgular and not ayar.hizli:
        yanit, meta = _cagir(p, ayar, ORKESTRATOR, triyaj_paketi(notu, bulgular, atama), kok / "triyaj", "plan", durum, roller=O_ROL)
        olcum["triyaj/O"] = meta
        tri = _sema(yanit, Triyaj, ("kabul", "red", "kural_onay"))
        if tri is not None:
            red = {r.id: r.neden for r in tri.red}
            reddedilen = [{**b, "red_neden": red[b["id"]]} for b in bulgular if b["id"] in red]
            bulgular = [b for b in bulgular if b["id"] not in red]
            onay = set(tri.kural_onay)
            for b in bulgular:
                if b.get("kural_adayi") and b["id"] not in onay:
                    b["kural_adayi"] = None
    if tri is None:
        # WHY: ADR 0053: aday ancak orkestratör onayıyla depoya girer; triyaj çözümlenemezse ya da hızlı modda atlanırsa
        # (ADR 0054) onaysız aday işlenmez. Aday rapordaki bulguda kalır, kullanıcı `vedit kural ekle` ile ekleyebilir.
        for b in bulgular:
            if b.get("kural_adayi"):
                b["onaysiz_aday"], b["kural_adayi"] = b["kural_adayi"], None
    # Bulgunun hedefi slottur (G6 onu kullanır); depoya giden aday rol sınıfıyla yazılır.
    kurallar = kural.qc_isle([{**b, "hedef": atama.kural_rolu(b.get("hedef"), bulgu_sinifi(yeni, b))} for b in bulgular],
                             proje=f"{p.studyo}/{p.ad}")
    dogrulama = kural_dogrula(bulgular, kurallar)
    durum.ayarla(kurallar={**durum.d["kurallar"], "yeni": len(kurallar["yeni"]), "tekrar": len(kurallar["tekrar"]),
                           "dogrulanan": len(dogrulama["dogrulanan"]), "dogrulanamayan": len(dogrulama["dogrulanamayan"])},
                 acik={x: sum(b["onem"] == x for b in bulgular) for x in ("P0", "P1", "P2")})
    kapi("G5", "gecti" if not dogrulama["dogrulanamayan"] else "kaldi",
         ("atlandı (hızlı): bulgular kabul, kural adayı onaysız işlenmedi; " if bulgular and ayar.hizli
          else "triyaj çözümlenemedi, kural adayı işlenmedi; " if bulgular and tri is None else "")
         + f"kabul {len(bulgular)}, red {len(reddedilen)}, kural yeni {len(kurallar['yeni'])}, tekrar {len(kurallar['tekrar'])}, "
         f"doğrulanan {len(dogrulama['dogrulanan'])}" + (f", DOĞRULANAMAYAN {len(dogrulama['dogrulanamayan'])}" if dogrulama["dogrulanamayan"] else ""))

    # G6 düzeltme: yalnız P0/P1 sahibi, bulgu farkı + bu koşunun yeni kurallarıyla, bir kez
    kapi("G6", "acik")
    gerek = sorted({b["hedef"] for b in bulgular if b["onem"] in ("P0", "P1") and b.get("hedef") in atama.gorevler}, key=_no)
    duzeltilen, br2, uyum2 = [], None, {}
    uyari_kapisi: dict = {}
    bekleyen_render = None
    yeni_ids = list(dict.fromkeys(kurallar["yeni"] + kurallar["tekrar"]))
    if gerek:
        k = kurgu.oku(p.work)
        d = kural.yukle()
        rol_kural = {x.id: x.hedef_rol for x in d.kurallar}

        def ilgili(r):
            sinif = {KURAL_ROLU[x] for x in atama.katmanlar(r)} | {"hepsi"}
            return list(dict.fromkeys(zorunlu.get(r, []) + [i for i in yeni_ids if rol_kural.get(i) in sinif]))

        # G3'te kalan uyarılar (ör. zoom yoğunluğu kırpılınca art arda kalan sessiz zoom) bu turun editörüne kısıt olarak gider;
        # ek çağrı yok. WHY: bkz. wiki/decisions/0058-hizli-ve-kaliteli-edit.md (g3b: kalan tek uyarı bu yoldan doğdu).
        g3_uyari = yeni_uyarilar(p, None, k, atama, gerek)
        sonuc = dict(havuz.map(lambda r: editor(r, kok / "duzelt", bulgular=[b for b in bulgular if b["hedef"] == r],
                                                kisitlar=[*(kisit.get(r) or []), *g3_uyari.get(r, [])] or None, zor=ilgili(r),
                                                taban=k), gerek))
        sonuc = {r: y for r, y in sonuc.items() if y is not None}
        if sonuc:
            yeni2, br2 = birlestir(k, sonuc, atama)
            if h2 := kurgu.denetle(p, yeni2):
                # WHY: düzeltme turu G3'te temiz yazılan kurguyu bozmasın; düzeltme düşer, G3 sürümü kalır.
                br2["denetle"], sonuc = h2[:10], {}
        if sonuc:
            # G6 uyarı kapısı. WHY: bkz. wiki/decisions/0058-hizli-ve-kaliteli-edit.md. hizlic'te G2 temizdi, 4 uyarının
            # hepsi bu düzeltmeden doğdu. Önce kodla düzeltilebilen (oto_duzelt), kalan yeni uyarı sahibine bir kez gider.
            br2["oto"] = oto_duzelt(yeni2)
            if uy := yeni_uyarilar(p, k, yeni2, atama, sonuc):
                durum.ayarla(asama="Düzeltme · uyarı kapısı")
                ek = dict(havuz.map(lambda r: editor(r, kok / "uyari", bulgular=[b for b in bulgular if b["hedef"] == r],
                                                     kisitlar=[*(kisit.get(r) or []), *uy[r]], onceki=sonuc[r], zor=ilgili(r),
                                                     taban=k), [r for r in uy if r in sonuc]))
                aday = {**sonuc, **{r: y for r, y in ek.items() if y is not None}}
                yeni3, br3 = birlestir(k, aday, atama)
                kalan = uy
                if not kurgu.denetle(p, yeni3):
                    br3["oto"] = oto_duzelt(yeni3)
                    kalan = yeni_uyarilar(p, k, yeni3, atama, aday)
                    # Bulgu düzeltmesi (P0/P1) P2 uyarı için geri alınmaz; ikinci tur yalnız uyarıyı azaltıyorsa kabul edilir.
                    if sum(map(len, kalan.values())) < sum(map(len, uy.values())):
                        sonuc, yeni2, br2 = aday, yeni3, br3
                    else:
                        kalan = uy
                uyari_kapisi = {"gelen": {r: len(v) for r, v in uy.items()}, "kalan": {r: len(v) for r, v in kalan.items()},
                                "duzelten": [r for r in ek if ek[r] is not None]}
        uyum2 = {r: [i for i in ilgili(r) if i not in {u.id for u in y.kural_uyum}] for r, y in sonuc.items()}
        uyum2 = {r: v for r, v in uyum2.items() if v}
        if sonuc:
            _bagla(p, yeni2)  # yeni hf/şablon klibinin kaynağı diske de yazılsın; Stüdyo kaynaksız klipte düşer
            kurgu.yaz(p.work, yeni2, beklenen_rev=k.rev)
            duzeltilen = [r for r in br2["uygulanan"] if r in sonuc]
            # WHY: ADR 0054. Render burada alınmaz: videoyu yalnız ikinci QC kullanır (G7). arvelior'da 176 sn'lik bu render'ı
            # hiçbir adım okumadı; Stüdyo önizlemesi kurgu.json'dan canlı çizer, --final zaten tam render alır.
            bekleyen_render = True
    kapi("G6", "gecti" if not uyum2 else "kaldi",
         (f"düzeltilen: {', '.join(duzeltilen)}" if duzeltilen else "düzeltme gerekmedi" if not gerek else "düzeltme birleşmedi")
         + (f"; uyarı kapısı {sum(uyari_kapisi['gelen'].values())} → {sum(uyari_kapisi['kalan'].values())}" if uyari_kapisi else "")
         + (f"; kural_uyum eksik: {', '.join(uyum2)}" if uyum2 else ""))

    # G7 son: deterministik denetim; ikinci QC yalnız P0 kapısı düşerse ya da istenirse
    kapi("G7", "acik")
    son = kurgu.oku(p.work)
    p0 = [h for h in kurgu.denetle(p, son)]
    uyari = kurgu_kalite.uyarilar(son, tema_token.oku(kurgu.etkin_tema(p, son.motion_tema)), p=p)
    taslak_eski = False
    if bekleyen_render and (tekrar_denetle or p0):
        durum.ayarla(asama="Son · render")
        video = hizli.qc_taslak(p)
    elif bekleyen_render:
        taslak_eski = True
    if tekrar_denetle or p0:
        ekip.izle(p, video, kok / "qc2")
    havuz.shutdown()
    kapi("G7", "gecti" if not p0 else "kaldi", f"{len(p0)} hata, {len(uyari)} uyarı"
         + ("; taslak.mp4 düzeltmeden önceki hâl (Stüdyo önizlemesi güncel; `vedit taslak` yeniler)" if taslak_eski and not final else ""))
    durum.ayarla(asama="Bitti", bitti=True, bitis=time.time())
    ozet = {"sure_sn": round(time.time() - t0), "seviye": ayar.ekip_seviye, "en_cok": None if ayar.hizli else ayar.tavan(),
            "editor": len(plan.gorevler), "kk": len(plan.kk_gorevler),
            "ajanlar": {s: f"{ayar.slot(s).motor}:{ayar.slot(s).model or ''}" for s in [ORKESTRATOR, *atama.gorevler, *kk_kart]},
            "dagitim": dagitim, "plan_hata": plan_hata, "yaratici_brif": brif_durum,
            "plan": plan.model_dump(exclude={"yaratici_brif"}), "kapilar": kapilar, "olcum": olcum, "zorunlu": zorunlu, "kural_ihlal": ihlal,
            "birlestirme": br, "duzeltme_birlestirme": br2, "bulgular": bulgular, "reddedilen": reddedilen, "kurallar": kurallar,
            "kural_dogrulama": dogrulama, "duzeltme_uyum_eksik": uyum2, "duzeltilen": duzeltilen, "uyari_kapisi": uyari_kapisi,
            "son_denetim": {"hata": p0, "uyari": len(uyari)}, "uretim_puani": uretim_puani, "taslak_eski": taslak_eski, "hizli": ayar.hizli,
            "kapi_sure": {x["id"]: x.get("sure") for x in durum.d["kapilar"]}, "alt_sure": alt_sure}
    (kok / "ozet.json").write_text(json.dumps(ozet, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    rapor_yaz(p, once, son, ozet, atama)
    return ozet


def rapor_yaz(p, once: Kurgu | None, son: Kurgu | None, o: dict, atama: Atama | None = None) -> Path:
    toplam = sum((m or {}).get("token", 0) for m in o["olcum"].values())
    tahmini = sum(1 for m in o["olcum"].values() if (m or {}).get("tahmini"))
    ne, nk = o.get("editor") or SEVIYE.get(o.get("seviye") or "", (0, 0))[0], o.get("kk") or SEVIYE.get(o.get("seviye") or "", (0, 0))[1]
    sat = [f"# AI edit raporu (ekip v3 swarm, ADR 0059) · {p.studyo}/{p.ad}", ""]
    if (o.get("kural_dogrulama") or {}).get("dogrulanamayan"):
        sat += [f"> [!warning] Kural deposuna işlenemeyen aday: {'; '.join(o['kural_dogrulama']['dogrulanamayan'])}", ""]
    sat += [f"- Ekip: {ne} editör, {nk} kalite kontrol, 1 orkestratör" + (f" (tavan {o['en_cok']})" if o.get("en_cok") else "") + " · dağıtım: "
            + ("orkestratör" if o.get("dagitim") == "orkestrator" else "hızlı (orkestratörsüz, ADR 0054)" if o.get("dagitim") == "hizli"
               else f"varsayılan ({'; '.join(o.get('plan_hata') or [])[:200]})"),
            f"- Duvar saati: {o['sure_sn']} sn · ajan çağrısı: {len(o['olcum'])} · token: {toplam:,}" + (f" ({tahmini} slot tahmini)" if tahmini else ""),
            f"- Birleştirme: uygulanan {', '.join(o['birlestirme']['uygulanan']) or '-'} · reddedilen {', '.join(o['birlestirme']['red']) or '-'} · "
            f"düşen öğe {len(o['birlestirme'].get('dusen', []))} · çekime sığdırılan {len(o['birlestirme'].get('sigdirilan', []))} · "
            f"çapalanan {o['birlestirme']['capalanan']} · yeniden eşlenen {len(o['birlestirme']['tasinan'])} · itilen {len(o['birlestirme']['itilen'])}",
            f"- QC bulgusu: {len(o['bulgular'])} (P0 {sum(b['onem'] == 'P0' for b in o['bulgular'])}, P1 {sum(b['onem'] == 'P1' for b in o['bulgular'])}) · "
            f"orkestratörün reddettiği {len(o.get('reddedilen') or [])} · düzeltilen: {', '.join(o['duzeltilen']) or '-'}",
            *(["- Üretim puanı: " + " · ".join(f"{k} {v:g}/5" for k, v in o["uretim_puani"].items())] if o.get("uretim_puani") else []),
            f"- Kurallar: atanan {sum(len(v) for v in (o.get('zorunlu') or {}).values())}, kapıda kalan ihlal {sum(len(v) for v in (o.get('kural_ihlal') or {}).values())} · "
            f"işlenen yeni {len(o['kurallar']['yeni'])}, tekrar {len(o['kurallar']['tekrar'])}, mezar taşından düşen {len(o['kurallar']['mezar'])}, "
            f"ihlal sayımı {sum(o['kurallar']['ihlal'].values())} · depoda doğrulanan {len((o.get('kural_dogrulama') or {}).get('dogrulanan', []))}",
            f"- Son denetim: {len(o['son_denetim']['hata'])} hata, {o['son_denetim']['uyari']} uyarı", ""]
    if atama is not None:
        ajan = o.get("ajanlar") or {}
        sat += ["## Görev kartları", *[x + (f" · `{ajan[s]}`" if s in ajan else "") for s, x in zip(atama.gorevler, atama.tablo())],
                *[f"- {s} · `{m}`" for s, m in ajan.items() if s.startswith(("K", "O"))], ""]
    if o.get("kapilar"):
        ks = o.get("kapi_sure") or {}
        sat += ["## Kapılar", "| kapı | sn | sonuç |", "|---|---|---|",
                *[f"| {k} | {ks.get(k) if ks.get(k) is not None else ''} | {v} |" for k, v in o["kapilar"].items()], ""]
        if yavas := sorted(((s, k) for k, s in ks.items() if s), reverse=True)[:3]:
            sat += ["En yavaş kapılar: " + " · ".join(f"{k} {s:.0f} sn" for s, k in yavas), ""]
    if oto := (o.get("birlestirme") or {}).get("oto"):
        sat += ["## vedit'in düzelttikleri (render'dan önce)", *[f"- {x}" for x in oto], ""]
    if onaysiz := [b for b in o.get("bulgular") or [] if b.get("onaysiz_aday")]:
        sat += ["## Onaysız kural adayları (depoya işlenmedi; uygunsa `vedit kural ekle`)",
                *[f"- {b['id']}: {b['onaysiz_aday']}" for b in onaysiz], ""]
    if o.get("kural_ihlal"):
        sat += ["## Kural kapısında kalan ihlal", *[f"- {s}: {'; '.join(v)[:400]}" for s, v in o["kural_ihlal"].items()], ""]
    sat += ["## Ajanlar", "| çağrı | motor | model | sn | token | tahmini |", "|---|---|---|---|---|---|"]
    sat += [f"| {s} | {m.get('motor')} | {m.get('model')} | {m.get('sure')} | {m.get('token')} | {'evet' if m.get('tahmini') else ''} |"
            for s, m in o["olcum"].items() if m]
    f = p.work / "edit" / "ai-edit.rapor.md"
    f.write_text("\n".join(sat) + "\n", encoding="utf-8")
    return f
