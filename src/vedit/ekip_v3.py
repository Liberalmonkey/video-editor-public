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
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pydantic import BaseModel, ValidationError

from . import aiedit, capa, ekip, ff, hizli, kural, kurgu, kurgu_kalite, native_motion, tema_token, yuz_bolge
from .ekip_sema import (BOLUNMEZ, EDITOR_ROL_DOSYASI, KATMAN_ADI, KATMAN_TANIM, KATMANLAR, KK_ALAN, KK_KURAL_ROLU, KK_ROL_ADI,
                        KK_ROL_DOSYASI, KURAL_ROLU, ORKESTRATOR, SEVIYE, EkipAyar, Gorev, KapiCikti, KkGorev, Mesaj, Plan,
                        Triyaj, Yama, editorler, kontroller)
from .schemas import Kurgu

ROL_KLASORU = ekip.ROL_KLASORU
KAPILAR = [("G0", "Plan"), ("G1", "Düzen"), ("G2", "Kural kapısı"), ("G3", "Birleştir"), ("G4", "QC"), ("G5", "Triyaj ve kural"),
           ("G6", "Düzeltme"), ("G7", "Son")]
ZORUNLU_EN_COK = 12  # karta atanan kural sayısı üst sınırı (P0'lar her zaman girer)


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
    return h


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
    ekle = [c for c in copy.deepcopy(list(y.ekle)) if c.get("id") not in disari]
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
    gun = {g["id"]: g for g in copy.deepcopy(list(y.guncelle))}
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
    fazla = [er["loc"] for er in hata.errors() if er.get("type") == "extra_forbidden" and len(er.get("loc", ())) >= 3
             and er["loc"][0] == "klipler" and isinstance(er["loc"][1], int) and er["loc"][1] < len(d["klipler"])]
    if fazla:
        ek_id = {c.get("id") for c in ekle}
        for loc in fazla:
            c = d["klipler"][loc[1]]
            hedef = next((x for x in ekle if x.get("id") == c["id"]), None) if c["id"] in ek_id else gun.get(c["id"])
            if hedef is None:
                continue
            for anahtar in loc[2:-1]:
                hedef = hedef.get(anahtar) if isinstance(hedef, dict) else None
            if isinstance(hedef, dict) and hedef.pop(loc[-1], None) is not None and dusen is not None:
                dusen.append(f"{rol}:{c['id']}." + ".".join(str(x) for x in loc[2:]))
        d = _kurgu_dict(k, y, ekle, gun, kaynaklar)
        try:
            return Kurgu.model_validate(d)
        except ValidationError as e:
            hata = e
    kotu_klip, kotu_kay = set(), set()
    for er in hata.errors():
        loc = er.get("loc", ())
        if len(loc) >= 2 and loc[0] == "klipler" and isinstance(loc[1], int):
            kotu_klip.add(d["klipler"][loc[1]]["id"] if loc[1] < len(d["klipler"]) else None)
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
    return k, rapor


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


def plan_dogrula(plan: Plan, seviye: str, son: float) -> list[str]:
    """Seviye sayıları, tek kurgu sahibi, her katman × zamanın tam bir editörde olması, QC alanlarının kapsanması."""
    h = []
    e, kk = editorler(seviye), kontroller(seviye)
    if sorted(g.slot for g in plan.gorevler) != sorted(e):
        h.append(f"editör slotları {', '.join(e)} olmalı")
    if sorted(g.slot for g in plan.kk_gorevler) != sorted(kk):
        h.append(f"kalite kontrol slotları {', '.join(kk)} olmalı")
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


def pano_ekle(kok: Path, rol: str, mesajlar: list[Mesaj]) -> None:
    f = kok / "pano.json"
    eski = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    eski += [{**m.model_dump(), "kimden": rol} for m in mesajlar]
    f.write_text(json.dumps(eski, ensure_ascii=False, indent=1), encoding="utf-8")


def pano_oku(kok: Path, rol: str, aralik: tuple[float, float] | None = None) -> list[dict]:
    f = kok / "pano.json"
    if not f.exists():
        return []
    m = [x for x in json.loads(f.read_text(encoding="utf-8")) if x["kimden"] != rol]
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
 "rapor": "<ne yaptın, zaman damgalı, en çok 10 satır>"}
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
    dosyalar = [f"`{(ROL_KLASORU / (ad + '.md')).resolve()}`" for ad in dict.fromkeys(EDITOR_ROL_DOSYASI[x] for x in katmanlar)]
    aralik = (f"{g.aralik[0]:.2f}–{g.aralik[1]:.2f} sn (taban zaman çizelgesi; yalnız başlangıcı bu aralıkta olan klipleri ekle ve güncelle)"
              if g.aralik else "bütün video")
    sabit = [f"# Ekip editörü {rol}: " + "; ".join(f"{KATMAN_ADI[x]} ({KATMAN_TANIM[x]})" for x in katmanlar),
             f"Rol dosyaların: {', '.join(dosyalar)} (bir kez oku). Katman adları rol dosyasındaki izlerle eşleşir.",
             SABIT, "## Etkin kurallar", kurallar or "- (yok)"]
    if ozel_varlik:
        sabit.append(ozel_varlik)
    gecis_listesi = ", ".join(kurgu.ORTA_GECIS)
    if "grafik" in katmanlar:
        izinli_native = set(depo.secili_native) if (depo and depo.yalniz_bunlar) else None
        katalog_satirlari = native_motion.katalog_ozeti(izinli=izinli_native)
        sabit += [
            aiedit._hf_katalogu(p.work),  # birincil motor (ADR 0050)
            "## Native grafik kataloğu (HyperFrames karşılığı yoksa; yalnız bunlar)", *(katalog_satirlari or ["- (yalniz_bunlar aktif, seçili native bileşen yok)"]),
            "## Anlatı hiyerarşisi (rastgele ikon serpme YASAK)",
            "- Hook (0–3 sn): `tipografi/kinetik-baslik` (vurgu kelimesi patlar)\n"
            "- Bölüm / örnek ayrımları: `tipografi/bolum-baslik` (üst kapsül: `01 · KLASİK REKLAM`)\n"
            "- Değerlendirme / sonuç / metrik anları: `tipografi/durum-rozeti` veya `veri/*`\n"
            "- Zirve fikir / tezat anı: `tipografi/vurgu-soz` (~~eski~~ → **yeni**, gerekirse `odak_karart: true`) veya `veri/karsilastirma`\n"
            "- Kısa vurucu kelime: `tipografi/kayan-kelime`\n"
            "- Kapanış çağrısı: `kart/cta-karti`\n"
            "- İkonlar (`ikon/*`) yalnız 1–1.3 sn'lik seyrek destekçidir: grafik kliplerinin en çok %30'u ikon olabilir; konuşmacının yüzünü ve odak nesnesini/ürünü kapatma.",
            "## Kesim geçişleri (kurgu editörünün; yalnız bilgi)", gecis_listesi,
        ]
    if any(x in katmanlar for x in ("sfx", "muzik", "stil")):
        from . import olaysesi
        sabit += [
            "## Ses rolleri (dosya seçme, rol yaz; olaysesi seçer)", ", ".join(sorted({*olaysesi.ROLLER, *olaysesi.KOMBOLAR})),
            "## Yönetmenlik kuralları (ses ve stil)",
            "- Her bölüm açılışında (`acilis`, `vurgu_guclu`), geçişte ve önemli grafik girişinde katmanlı, kulağı yormayan gerçek SFX rol olayı kullan (sentetik yok; orta noktalı V1 geçişinin ve sesli hazır efektin sesi kendiliğinden gelir, aynı yere ikinci geçiş sesi koyma).\n"
            "- Hikâye ve duygu anlarında müzikte dinamik nefes/ducking (`ses.duck: true`, gerekirse `ses.kf`) kur.",
        ]
    if "kurgu" in katmanlar:
        sabit += [
            "## Geçiş türleri (orta noktası kesimde, sesi kendiliğinden)", gecis_listesi,
            "## Yönetmenlik kuralları (kurgu)",
            "- 0.4 sn üstü ölü boşlukları, dolgu ve tekrarları kelime sınırında kırp.\n"
            "- Konuşan kafada durağanlığı kırmak için `el_kamerasi` + `hizli_zoom` / `punch` çeşitliliği kur.\n"
            "- Bölüm geçişlerinde seçili stile uygun `zoom_kirbac`, `film_yanigi`, `bolunme`, `yirtma`, `bozulma` (veya stilin `gecis` listesi) kullan.\n"
            "- Büyük tipografi zirvelerinde arka planı sakinleştirmek için `odak_karart` hazır efektini kullan.",
        ]
    kendi = [c.model_dump(exclude_defaults=True) for c in k.klipler if atama.sahip(k, c) == rol]
    degisken = ["## Kullanıcı isteği", _istek_metni(istek),
                "## Görev kartın (orkestratör)", f"- Katmanlar: {', '.join(KATMAN_ADI[x] for x in katmanlar)}", f"- Aralık: {aralik}",
                *([f"- Odak: {g.odak}"] if g.odak else []),
                "## Zorunlu kurallar (her biri için kural_uyum yaz)", *(_kural_metinleri(zorunlu or [], d) or ["- (yok)"]),
                "## Ekip kartları", *atama.tablo(),
                "## Sözleşme", "```json", json.dumps(soz, ensure_ascii=False)[:6000], "```",
                f"## Transkript özeti: `{(p.work / 'analysis' / 'digest.txt').resolve()}`",
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
            f"Rol dosyan: `{(ROL_KLASORU / 'ekip-orkestrator.md').resolve()}` (bir kez oku). Hiçbir dosyayı değiştirme. Yanıtın tamamı tek JSON nesnesi."]


def plan_paketi(p, k: Kurgu, ayar: EkipAyar, istek: str | None, varsayilan: Plan) -> str:
    ne, nk = SEVIYE[ayar.ekip_seviye]
    son = _bitis(k)
    d = kural.yukle()
    etkin = kural.secim(d, rol="hepsi", **_kapsam(p))
    v1 = [c for c in k.klipler if c.iz == "V1"]
    return "\n\n".join([
        *_o_basi("plan (G0)"),
        "## Kullanıcı isteği", _istek_metni(istek),
        "## Seviye", f"`{ayar.ekip_seviye}`: {ne} editör ({', '.join(editorler(ayar.ekip_seviye))}), {nk} kalite kontrol "
        f"({', '.join(kontroller(ayar.ekip_seviye))}). Sayılar sabittir; işi sen dağıtırsın.",
        "## Katmanlar", *[f"- `{x}`: {KATMAN_TANIM[x]}" + (" (bölünmez: tek editör, aralık null)" if x in BOLUNMEZ else " (zaman dilimlerine bölünebilir)")
                          for x in KATMANLAR],
        "## Kalite kontrol rolleri", *[f"- `{r}`: {KK_ROL_ADI[r]}" for r in KK_ROL_ADI],
        "## Video", f"- Süre {son:.2f} sn, V1'de {len(v1)} çekim, sekans {k.sekans.w}x{k.sekans.h}, motion sıklığı `{ayar.motion}`",
        f"- Transkript özeti: `{(p.work / 'analysis' / 'digest.txt').resolve()}` (hook için oku)",
        "## Etkin kurallar (id, önem, rol)", *([f"- [{x.id} {x.onem} {x.hedef_rol}] {x.metin}" for x in etkin] or ["- (yok)"]),
        "## Varsayılan dağıtım (istek özel bir ağırlık istemiyorsa bunu temel al)", "```json",
        varsayilan.model_dump_json(include={"gorevler", "kk_gorevler"}), "```",
        "## Çıktı", "```json\n"
        '{"hook": {"bas": <sn>, "son": <sn>, "neden": "<tek satır>"},\n'
        ' "gorevler": [{"slot": "E1", "katmanlar": ["kurgu"], "aralik": null, "odak": "<en çok 3 satır: isteğe göre ne yapacak>", "kurallar": ["K0003"]}],\n'
        ' "kk_gorevler": [{"slot": "K1", "rol": "kurgu|gorsel|ses|kurgu-ses|genel|kural|izleyici", "aralik": null, "odak": ""}],\n'
        ' "gerekce": "<dağıtımın nedeni, en çok 5 satır>"}\n```',
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
        "- Kural adayı genelleşmiş, projeye özgü olmayan, tek emir satırıysa onaylanır; onaylanan aday kural deposuna işlenir ve "
        "düzeltmede editörlere zorunlu kural olarak gider.",
    ]) + "\n"


def kontrol_istemi(p, kg: KkGorev, girdi: dict, atama: Atama, istek: str | None) -> Path:
    """Kalite kontrol kartından istem: rol dosyaları, aralık, odak, ekip kartları, rolün kural paketi."""
    dosyalar = [f"`{(ROL_KLASORU / (ad + '.md')).resolve()}`" for ad in KK_ROL_DOSYASI[kg.rol]]
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
    satir = [
        f"# Kalite kontrol {kg.slot}: {KK_ROL_ADI[kg.rol]}",
        f"Önce rol dosyalarını oku: {', '.join(dosyalar)}. Hiçbir dosyayı değiştirme.",
        "## Kullanıcı isteği", _istek_metni(istek),
        *(["## Bakacağın aralık", f"Yalnız {kg.aralik[0]:.1f}–{kg.aralik[1]:.1f} sn."] if kg.aralik else []),
        *(["## Orkestratörün odağı", kg.odak] if kg.odak else []),
        "## Girdiler",
        *[f"- {ad}: `{Path(y).resolve()}`" for ad, y in girdi.items() if not ad.startswith("_")],
        "## Ekip kartları (katman ve zaman sahibi)", *atama.tablo(),
        "## Kural",
        "- Bir kusuru yazmadan önce o saniyenin karesini aç. `kanit` açtığın kare dosyasının tam yoludur; dosya yoksa bulgu düşer.",
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
        '"kategori": "stil|okunurluk|ritim|ses|teknik|tutarlilik", "kanit": "<kare yolu>", "sorun": "", "beklenen": "", '
        '"kural_id": "K0012 | null", "kural_adayi": "YAPMA: ... | null"}],\n'
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


# ---------------------------------------------------------------- QC birleştirici

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
    izler = {i.id for i in k.izler}
    for b in kalan:
        orta = (b["zaman"][0] + b["zaman"][1]) / 2
        if b.get("katman") in izler:
            sahibi = atama.katman_sahibi(katman_sinifi(k, b["katman"]), orta)
        elif b.get("katman") in ("altyazi", "motion_tema", "stil", "tema"):
            sahibi = atama.katman_sahibi("stil")
        else:
            sahibi = None
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

def parcali_render(p, araliklar: list[tuple[float, float]], *, es: int = 2) -> Path:
    """Etkilenen aralıkları paralel render eder ve mevcut taslağa ekler (taslak çözünürlüğü, veryfast)."""
    taslak = p.work / "renders" / "taslak.mp4"
    if not taslak.exists() or not araliklar:
        return hizli.taslak(p)
    props = hizli._props(p)
    hizli._public_hazirla(p)
    fps = kurgu.oku(p.work).sekans.fps
    kok = p.work / "renders" / "parca"
    kok.mkdir(parents=True, exist_ok=True)

    from . import hf_kurgu
    motor, neden = hf_kurgu.motor_sec(p, props)  # WHY: ADR 0051; motor bir kez seçilir, proje bir kez derlenir
    print(f"  Motor: {'HyperFrames' if motor == 'hf' else 'Remotion'} ({neden})", flush=True)

    def bir(i_ab):
        i, (a, b) = i_ab
        out = kok / f"p{i}.mp4"
        if motor == "hf":
            hf_kurgu.render(p, props, out, kalite="draft", aralik=(a, b), olcek=0.5)
        else:
            hizli._remotion(props, p.work / "public", out, "--image-format=jpeg", "--x264-preset=veryfast", "--crf=23", "--scale=0.5",
                            f"--frames={int(a * fps)}-{int(b * fps) - 1}")
        return out

    # HyperFrames parçaları sırayla: her parça work/public'e kendi pencereli derlemesini yazar (ADR 0051).
    with ThreadPoolExecutor(max_workers=1 if motor == "hf" else es) as h:
        parcalar = list(h.map(bir, enumerate(sorted(araliklar))))
    # Eski taslağın aralık dışı bölümleri + yeni parçalar; sınırda yeniden kodlama (taslak kalitesi yeter).
    tv = ff.probe(taslak).get("video") or {}
    tw, th = tv.get("width", 540), tv.get("height", 960)
    girdiler, filtre, n = ["-i", str(taslak)], [], 0
    sinir = [0.0] + [x for ab in sorted(araliklar) for x in ab] + [float(ff.probe(taslak)["duration"])]
    for j, (a, b) in enumerate(zip(sinir[::2], sinir[1::2])):
        if b - a > 1 / fps:
            filtre.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{n}];[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{n}]")
            n += 1
        if j < len(parcalar):
            girdiler += ["-i", str(parcalar[j])]
            # Parça başka motordan ya da ölçekten gelebilir: taslağın boyutuna eşitlenir (ADR 0051).
            filtre.append(f"[{len(girdiler) // 2 - 1}:v]scale={tw}:{th},setsar=1,setpts=PTS-STARTPTS[v{n}];[{len(girdiler) // 2 - 1}:a]asetpts=PTS-STARTPTS[a{n}]")
            n += 1
    zincir = ";".join(filtre) + ";" + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
    yeni = p.work / "renders" / "taslak.yeni.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *girdiler, "-filter_complex", zincir, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", str(yeni)], check=True)
    os.replace(yeni, taslak)
    return taslak


# ---------------------------------------------------------------- ajan çağrısı ve çıktı çözümleme

def _cagir(p, ayar: EkipAyar, rol: str, metin: str, kok: Path, mod: str, durum) -> tuple[str, dict]:
    """Tek ajan çağrısı: istem dosyası + yanıt; bir yeniden deneme, sonra yedek motor. (yanıt, ölçüm)."""
    kok.mkdir(parents=True, exist_ok=True)
    f = kok / f"{rol}.istem.md"
    f.write_text(metin, encoding="utf-8")
    istem = (f"Read the file {f.resolve()} completely and do exactly what it says. "
             + ("Do not modify any file." if mod == "plan" else "Do not run shell commands and do not write files: return only the JSON."))
    meta: dict = {}
    for deneme, yedek in ((1, False), (2, True)):
        sl = ayar.slot(rol)
        if yedek and not sl.yedek_motor:
            break
        durum.slot(rol, durum="yedek" if yedek else "calisiyor", cikti=str(kok / f"{rol}.cikti.txt"))
        ok, yanit, meta = ekip.ajan(sl, istem, mod, kok / rol, yedek=yedek)
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

def calistir(p, ayar: EkipAyar, *, notu: str | None = None, final: bool = False, tekrar_denetle: bool = False) -> dict:
    kok = p.work / "edit" / "ekip"
    kok.mkdir(parents=True, exist_ok=True)
    (kok / "pano.json").unlink(missing_ok=True)
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
    havuz = ThreadPoolExecutor(max_workers=ayar.es())

    def kapi(kid: str, d: str, not_: str = ""):
        kapilar[kid] = f"{d}{' · ' + not_ if not_ else ''}"
        durum.kapi(kid, d, not_)

    # G0 plan: orkestratör hook, görev kartları ve zorunlu kurallar yazar
    kapi("G0", "acik")
    durum.slot(ORKESTRATOR, rol="Orkestratör")
    varsayilan = varsayilan_dagitim(ayar.ekip_seviye, k)
    yanit, meta = _cagir(p, ayar, ORKESTRATOR, plan_paketi(p, k, ayar, notu, varsayilan), kok / "plan", "plan", durum)
    olcum["plan/O"] = meta
    plan = _sema(yanit, Plan, ("gorevler", "hook"))
    plan_hata = plan_dogrula(plan, ayar.ekip_seviye, _bitis(k)) if plan else ["plan çözümlenemedi"]
    dagitim = "orkestrator" if not plan_hata else "varsayilan"
    if plan_hata:
        hook = plan.hook if plan else None
        plan = varsayilan.model_copy(update={"hook": hook})
    atama = Atama(plan.gorevler)
    depo = kural.yukle()
    zorunlu = {g.slot: zorunlu_kurallar(p, g, depo, doldur=dagitim == "varsayilan") for g in plan.gorevler}
    for g in plan.gorevler:
        durum.slot(g.slot, rol=", ".join(KATMAN_ADI[x] for x in g.katmanlar), aralik=g.aralik)
    kk_kart = {g.slot: g for g in plan.kk_gorevler}
    for g in plan.kk_gorevler:
        durum.slot(g.slot, rol=KK_ROL_ADI[g.rol], aralik=g.aralik)
    durum.ayarla(dagitim=dagitim, kurallar={**durum.d["kurallar"], "atanan": sum(len(v) for v in zorunlu.values())})
    kapi("G0", "gecti", "orkestratör dağıttı" if dagitim == "orkestrator" else f"varsayılan dağıtım ({'; '.join(plan_hata)[:200]})")
    soz = sozlesme(p, k, plan.hook, ritim)
    (kok / "sozlesme.json").write_text(json.dumps(soz, ensure_ascii=False, indent=1), encoding="utf-8")
    (kok / "plan.json").write_text(plan.model_dump_json(indent=1), encoding="utf-8")

    def editor(rol: str, kdir: Path, *, bulgular=None, kisitlar=None, onceki=None, zor=None, taban=None):
        yanit, meta = _cagir(p, ayar, rol, paket(p, taban or k, rol, soz, kok, atama, istek=notu, zorunlu=zor or zorunlu.get(rol),
                                                 bulgular=bulgular, kisitlar=kisitlar, onceki=onceki), kdir, "duzenle", durum)
        olcum[f"{kdir.name}/{rol}"] = meta
        y = _yama_cikar(yanit)
        if y and y.pano:
            pano_ekle(kok, rol, y.pano)
        if y and y.hf:
            hf_yaz(p, rol, y, atama)  # kompozisyon klipten önce diskte olmalı: birleştirmede denetlenir (ADR 0050)
        return rol, y

    # G1 düzen: bütün editörler aynı anda
    kapi("G1", "acik")
    yamalar = {r: y for r, y in havuz.map(lambda r: editor(r, kok / "duzen"), atama.gorevler) if y is not None}
    eksik_yanit = [r for r in atama.gorevler if r not in yamalar]
    kapi("G1", "gecti" if not eksik_yanit else "kaldi", f"yanıtsız: {', '.join(eksik_yanit)}" if eksik_yanit else f"{len(yamalar)} yama")

    # G2 kural kapısı: deterministik denetim + orkestratör kararı; düzelt alan editör bir kez, paralel
    kapi("G2", "acik")
    ihlal, genel = kural_denetimi(p, k, yamalar, atama, zorunlu)
    yanit, meta = _cagir(p, ayar, ORKESTRATOR, kapi_paketi(notu, atama, yamalar, zorunlu, ihlal, genel), kok / "kapi", "plan", durum)
    olcum["kapi/O"] = meta
    karar = _sema(yanit, KapiCikti, ("kararlar",))
    duzelt = {x.slot: x.brif for x in (karar.kararlar if karar else []) if x.karar == "duzelt" and x.slot in atama.gorevler}
    # Sert ihlal (eksik kural_uyum, reddedilen yama, yanıtsız editör) orkestratörün kabulüyle geçmez; yanıt yoksa bütün ihlaller.
    sert = {s for s, v in ihlal.items() if karar is None or any(x.startswith(("kural_uyum eksik", "yama reddedildi")) for x in v)}
    duzelt.update({s: duzelt.get(s, "") for s in [*sert, *eksik_yanit]})
    if duzelt:
        def kapi_duzelt(r):
            kis = [*([duzelt[r]] if duzelt[r] else []), *ihlal.get(r, [])]
            return editor(r, kok / "kapi", kisitlar=kis, onceki=yamalar.get(r))
        for r, y in havuz.map(kapi_duzelt, sorted(duzelt, key=_no)):
            if y is not None:
                yamalar[r] = y
        ihlal, genel = kural_denetimi(p, k, yamalar, atama, zorunlu)
    uyum_eksik = sum(1 for v in ihlal.values() for x in v if x.startswith("kural_uyum eksik"))
    durum.ayarla(kurallar={**durum.d["kurallar"], "uyum_eksik": uyum_eksik})
    kapi("G2", "gecti" if not ihlal else "kaldi",
         (f"düzeltilen: {', '.join(sorted(duzelt, key=_no))}; " if duzelt else "") + (f"kalan ihlal: {', '.join(sorted(ihlal, key=_no))}" if ihlal else "temiz"))

    # G3 deterministik birleştirme + tek render
    kapi("G3", "acik")
    taban_rev = kurgu.oku(p.work).rev
    yeni, br = birlestir(k, yamalar, atama)
    hatalar = kurgu.denetle(p, yeni)
    if hatalar:
        br["denetle"] = hatalar[:10]
    kurgu.yaz(p.work, yeni, beklenen_rev=taban_rev)  # WHY: kullanıcı Stüdyo'da yazdıysa ezilmez (RevCakismasi)
    yeni = kurgu.oku(p.work)
    _bagla(p, yeni)
    kurgu.yaz(p.work, yeni)
    video = hizli.taslak(p)
    kapi("G3", "gecti" if not br["red"] else "kaldi", f"uygulanan {len(br['uygulanan'])}, reddedilen {len(br['red'])}, düşen öğe {len(br['dusen'])}")

    # G4 QC: bütün kalite kontrol kartları aynı anda, ortak paket
    kapi("G4", "acik")
    qdir = kok / "qc"
    girdi = ekip.izle(p, video, qdir)

    def kontrol(kk: str):
        f = kontrol_istemi(p, kk_kart[kk], girdi, atama, notu)
        yanit, meta = _cagir(p, ayar, kk, f.read_text(encoding="utf-8"), qdir, "plan", durum)
        olcum[f"qc/{kk}"] = meta
        o = ekip.json_cikar(yanit) if yanit else None
        c, _ = ekip.bulgu_dogrula(o, kk) if o is not None else (None, [])
        return kk, [b.model_dump() for b in c.bulgular] if c else []

    listeler = dict(havuz.map(kontrol, sorted(kk_kart, key=_no)))
    for i, b in enumerate(br["capa_bulgu"] + br["cakisma_bulgu"]):  # vedit'in kendi bulguları da birleştiriciye girer
        listeler.setdefault("K9", []).append(
            {"id": f"K9-{900 + i:03d}", "hedef": b.get("hedef"), "onem": "P1", "zaman": list(b.get("zaman") or [0, 0.1]),
             "katman": b.get("iz", "V2"), "kategori": "tutarlilik", "kanit": "", "sorun": b["sorun"], "beklenen": "çakışma yok"})
    bulgular, kisit = bulgu_birlestir(yeni, listeler, atama)
    kapi("G4", "gecti", f"{len(bulgular)} bulgu")

    # G5 triyaj + kural işleme: orkestratör ayıklar ve onaylar, vedit depoya işler ve doğrular
    kapi("G5", "acik")
    reddedilen: list[dict] = []
    if bulgular:
        yanit, meta = _cagir(p, ayar, ORKESTRATOR, triyaj_paketi(notu, bulgular, atama), kok / "triyaj", "plan", durum)
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
    kurallar = kural.qc_isle(bulgular, proje=f"{p.studyo}/{p.ad}")
    dogrulama = kural_dogrula(bulgular, kurallar)
    durum.ayarla(kurallar={**durum.d["kurallar"], "yeni": len(kurallar["yeni"]), "tekrar": len(kurallar["tekrar"]),
                           "dogrulanan": len(dogrulama["dogrulanan"]), "dogrulanamayan": len(dogrulama["dogrulanamayan"])},
                 acik={x: sum(b["onem"] == x for b in bulgular) for x in ("P0", "P1", "P2")})
    kapi("G5", "gecti" if not dogrulama["dogrulanamayan"] else "kaldi",
         f"kabul {len(bulgular)}, red {len(reddedilen)}, kural yeni {len(kurallar['yeni'])}, tekrar {len(kurallar['tekrar'])}, "
         f"doğrulanan {len(dogrulama['dogrulanan'])}" + (f", DOĞRULANAMAYAN {len(dogrulama['dogrulanamayan'])}" if dogrulama["dogrulanamayan"] else ""))

    # G6 düzeltme: yalnız P0/P1 sahibi, bulgu farkı + bu koşunun yeni kurallarıyla, bir kez
    kapi("G6", "acik")
    gerek = sorted({b["hedef"] for b in bulgular if b["onem"] in ("P0", "P1") and b.get("hedef") in atama.gorevler}, key=_no)
    duzeltilen, br2, uyum2 = [], None, {}
    yeni_ids = list(dict.fromkeys(kurallar["yeni"] + kurallar["tekrar"]))
    if gerek:
        k = kurgu.oku(p.work)
        d = kural.yukle()
        rol_kural = {x.id: x.hedef_rol for x in d.kurallar}

        def ilgili(r):
            sinif = {KURAL_ROLU[x] for x in atama.katmanlar(r)} | {"hepsi"}
            return list(dict.fromkeys(zorunlu.get(r, []) + [i for i in yeni_ids if rol_kural.get(i) in sinif]))

        sonuc = dict(havuz.map(lambda r: editor(r, kok / "duzelt", bulgular=[b for b in bulgular if b["hedef"] == r],
                                                kisitlar=kisit.get(r), zor=ilgili(r), taban=k), gerek))
        sonuc = {r: y for r, y in sonuc.items() if y is not None}
        uyum2 = {r: [i for i in ilgili(r) if i not in {u.id for u in y.kural_uyum}] for r, y in sonuc.items()}
        uyum2 = {r: v for r, v in uyum2.items() if v}
        if sonuc:
            yeni2, br2 = birlestir(k, sonuc, atama)
            _bagla(p, yeni2)  # yeni hf/şablon klibinin kaynağı diske de yazılsın; Stüdyo kaynaksız klipte düşer
            kurgu.yaz(p.work, yeni2, beklenen_rev=k.rev)
            duzeltilen = [r for r in br2["uygulanan"] if r in sonuc]
            araliklar = sorted({(max(0.0, b["zaman"][0] - 0.5), b["zaman"][1] + 0.5) for b in bulgular if b["hedef"] in sonuc})
            durum.ayarla(asama="Düzeltme · render")
            ks = atama.kurgu_sahibi()
            video = parcali_render(p, araliklar) if ks not in sonuc else hizli.taslak(p)
    kapi("G6", "gecti" if not uyum2 else "kaldi",
         (f"düzeltilen: {', '.join(duzeltilen)}" if duzeltilen else "düzeltme gerekmedi" if not gerek else "düzeltme birleşmedi")
         + (f"; kural_uyum eksik: {', '.join(uyum2)}" if uyum2 else ""))

    # G7 son: deterministik denetim; ikinci QC yalnız P0 kapısı düşerse ya da istenirse
    kapi("G7", "acik")
    son = kurgu.oku(p.work)
    p0 = [h for h in kurgu.denetle(p, son)]
    uyari = kurgu_kalite.uyarilar(son, tema_token.oku(kurgu.etkin_tema(p, son.motion_tema)), p=p)
    if tekrar_denetle or p0:
        ekip.izle(p, video, kok / "qc2")
    havuz.shutdown()
    kapi("G7", "gecti" if not p0 else "kaldi", f"{len(p0)} hata, {len(uyari)} uyarı")
    durum.ayarla(asama="Bitti", bitti=True, bitis=time.time())
    ozet = {"sure_sn": round(time.time() - t0), "seviye": ayar.ekip_seviye, "dagitim": dagitim, "plan_hata": plan_hata,
            "plan": plan.model_dump(), "kapilar": kapilar, "olcum": olcum, "zorunlu": zorunlu, "kural_ihlal": ihlal,
            "birlestirme": br, "duzeltme_birlestirme": br2, "bulgular": bulgular, "reddedilen": reddedilen, "kurallar": kurallar,
            "kural_dogrulama": dogrulama, "duzeltme_uyum_eksik": uyum2, "duzeltilen": duzeltilen,
            "son_denetim": {"hata": p0, "uyari": len(uyari)}}
    (kok / "ozet.json").write_text(json.dumps(ozet, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    rapor_yaz(p, once, son, ozet, atama)
    return ozet


def rapor_yaz(p, once: Kurgu | None, son: Kurgu | None, o: dict, atama: Atama | None = None) -> Path:
    toplam = sum((m or {}).get("token", 0) for m in o["olcum"].values())
    tahmini = sum(1 for m in o["olcum"].values() if (m or {}).get("tahmini"))
    ne, nk = SEVIYE.get(o.get("seviye") or "", (0, 0))
    sat = [f"# AI edit raporu (ekip v3, ADR 0053) · {p.studyo}/{p.ad}", ""]
    if (o.get("kural_dogrulama") or {}).get("dogrulanamayan"):
        sat += [f"> [!warning] Kural deposuna işlenemeyen aday: {'; '.join(o['kural_dogrulama']['dogrulanamayan'])}", ""]
    sat += [f"- Seviye: `{o.get('seviye')}` ({ne} editör, {nk} kalite kontrol, 1 orkestratör) · dağıtım: "
            + ("orkestratör" if o.get("dagitim") == "orkestrator" else f"varsayılan ({'; '.join(o.get('plan_hata') or [])[:200]})"),
            f"- Duvar saati: {o['sure_sn']} sn · ajan çağrısı: {len(o['olcum'])} · token: {toplam:,}" + (f" ({tahmini} slot tahmini)" if tahmini else ""),
            f"- Birleştirme: uygulanan {', '.join(o['birlestirme']['uygulanan']) or '-'} · reddedilen {', '.join(o['birlestirme']['red']) or '-'} · "
            f"düşen öğe {len(o['birlestirme'].get('dusen', []))} · çekime sığdırılan {len(o['birlestirme'].get('sigdirilan', []))} · "
            f"çapalanan {o['birlestirme']['capalanan']} · yeniden eşlenen {len(o['birlestirme']['tasinan'])} · itilen {len(o['birlestirme']['itilen'])}",
            f"- QC bulgusu: {len(o['bulgular'])} (P0 {sum(b['onem'] == 'P0' for b in o['bulgular'])}, P1 {sum(b['onem'] == 'P1' for b in o['bulgular'])}) · "
            f"orkestratörün reddettiği {len(o.get('reddedilen') or [])} · düzeltilen: {', '.join(o['duzeltilen']) or '-'}",
            f"- Kurallar: atanan {sum(len(v) for v in (o.get('zorunlu') or {}).values())}, kapıda kalan ihlal {sum(len(v) for v in (o.get('kural_ihlal') or {}).values())} · "
            f"işlenen yeni {len(o['kurallar']['yeni'])}, tekrar {len(o['kurallar']['tekrar'])}, mezar taşından düşen {len(o['kurallar']['mezar'])}, "
            f"ihlal sayımı {sum(o['kurallar']['ihlal'].values())} · depoda doğrulanan {len((o.get('kural_dogrulama') or {}).get('dogrulanan', []))}",
            f"- Son denetim: {len(o['son_denetim']['hata'])} hata, {o['son_denetim']['uyari']} uyarı", ""]
    if atama is not None:
        sat += ["## Görev kartları", *atama.tablo(), ""]
    if o.get("kapilar"):
        sat += ["## Kapılar", "| kapı | sonuç |", "|---|---|", *[f"| {k} | {v} |" for k, v in o["kapilar"].items()], ""]
    if o.get("kural_ihlal"):
        sat += ["## Kural kapısında kalan ihlal", *[f"- {s}: {'; '.join(v)[:400]}" for s, v in o["kural_ihlal"].items()], ""]
    sat += ["## Ajanlar", "| çağrı | motor | model | sn | token | tahmini |", "|---|---|---|---|---|---|"]
    sat += [f"| {s} | {m.get('motor')} | {m.get('model')} | {m.get('sure')} | {m.get('token')} | {'evet' if m.get('tahmini') else ''} |"
            for s, m in o["olcum"].items() if m]
    f = p.work / "edit" / "ai-edit.rapor.md"
    f.write_text("\n".join(sat) + "\n", encoding="utf-8")
    return f
