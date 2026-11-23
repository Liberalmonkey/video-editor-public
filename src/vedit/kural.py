"""Kural deposu: kullanıcı düzeltmeleri ve kalite kontrol bulgularından genelleşmiş YAP/YAPMA kuralları (ADR 0047).

WHY: library/checks.md elle büyüyen bir listeydi; kim neyi okuyacak, hangi kural kaç kez tekrarlandı, kullanıcı hangisini
sildi bilinmiyordu. Tek kaynak `library/kurallar/kurallar.json`; checks.md ondan üretilir (okuyan skill'ler değişmez).
Silinen kural mezar taşı olarak kalır: QC aynı kuralı yeniden önermez (kullanıcı yeniden açmadıkça).
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import unicodedata
from datetime import date
from pathlib import Path
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import paths

Kapsam = Literal["global", "studyo", "stil", "proje"]
Rol = Literal["E1", "E2", "E3", "hepsi"]
Onem = Literal["P0", "P1", "P2"]
Durum = Literal["aktif", "oneri", "pasif", "silinen"]
KATEGORILER = ("altyazi", "kadraj", "kesim", "grafik", "renk", "hareket", "gecis", "ses", "icerik", "slop", "yayin", "teknik", "genel")
ONEM_SIRA = {"P0": 0, "P1": 1, "P2": 2}
BENZERLIK = 0.6  # token Jaccard; üstündeyse aynı kural sayılır


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Kanit(_M):
    proje: str | None = None
    zaman: float | None = None    # sn
    kare: str | None = None       # kök göreli kare yolu
    not_: str | None = Field(default=None, alias="not")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("kare")
    @classmethod
    def _goreli(cls, v: str | None) -> str | None:
        # WHY: QC kanıtı mutlak yolla geliyordu; depo makineye özgü ve kişisel yol taşıyordu (yayın kopyası taraması yakaladı).
        return paths.rel(Path(v)) if v and Path(v).is_absolute() else v


class Kural(_M):
    id: str
    metin: str
    neden: str = ""
    kapsam: Kapsam = "global"
    kapsam_deger: str | None = None   # stüdyo, stil ya da proje adı
    hedef_rol: Rol = "hepsi"
    kategori: str = "genel"
    onem: Onem = "P1"
    kaynak: str = "kullanici"         # kullanici | kk:<ajan>
    kanit: list[Kanit] = []
    durum: Durum = "aktif"
    tekrar: int = Field(default=1, ge=1)
    olcut: str | None = None          # makine denetimi: kapı kodu ya da test (ör. "kurgu-denetle STIL_DISI_RENK")
    olusturma: str = Field(default_factory=lambda: date.today().isoformat())
    guncelleme: str = Field(default_factory=lambda: date.today().isoformat())

    @field_validator("metin")
    @classmethod
    def _yap_yapma(cls, v: str) -> str:
        v = " ".join(v.split())
        if not re.match(r"^(YAP|YAPMA): \S", v):
            raise ValueError("kural 'YAP: ' ya da 'YAPMA: ' ile başlayan tek emir satırıdır")
        return v

    @field_validator("kategori")
    @classmethod
    def _kategori(cls, v: str) -> str:
        if v not in KATEGORILER:
            raise ValueError(f"kategori {', '.join(KATEGORILER)} olmalı")
        return v


class Depo(_M):
    surum: int = 1
    kurallar: list[Kural] = []


class Ayar(_M):
    onay_bekle: bool = False   # True: yeni kural 'oneri' olarak kullanıcı onayını bekler
    butce_token: int = Field(default=1200, ge=200)


def klasor() -> Path:
    return paths.LIBRARY / "kurallar"


def _yol() -> Path:
    return klasor() / "kurallar.json"


def _atomik(f: Path, metin: str) -> None:
    f.parent.mkdir(parents=True, exist_ok=True)
    fd, gecici = tempfile.mkstemp(dir=f.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as h:
        h.write(metin)
    os.replace(gecici, f)


def yukle() -> Depo:
    f = _yol()
    return Depo.model_validate_json(f.read_text(encoding="utf-8")) if f.exists() else Depo()


def ayar() -> Ayar:
    f = klasor() / "ayar.json"
    return Ayar.model_validate_json(f.read_text(encoding="utf-8")) if f.exists() else Ayar()


def ayar_yaz(a: Ayar) -> None:
    _atomik(klasor() / "ayar.json", a.model_dump_json(indent=1) + "\n")


def kaydet(d: Depo) -> None:
    """Depoyu ve ondan üretilen checks.md'yi yazar."""
    _atomik(_yol(), d.model_dump_json(indent=1, by_alias=True, exclude_none=True) + "\n")
    _atomik(paths.LIBRARY / "checks.md", checks_md(d))
    _atomik(klasor() / "kurallar.schema.json", json.dumps(Depo.model_json_schema(by_alias=True), ensure_ascii=False, indent=1) + "\n")


# ------------------------------------------------------------------ benzerlik

_DOLGU = set("ve ile ya da de da bir bu şu o için gibi en çok yalnız her ama olarak olan kendi daha".split())


def _tokenler(metin: str) -> set[str]:
    s = unicodedata.normalize("NFKC", metin).lower()
    s = re.sub(r"^(yap|yapma):", "", s)
    s = re.sub(r"\([^)]*\)", " ", s)  # kanıt parantezi
    return {w[:6] for w in re.findall(r"\w+", s) if len(w) > 2 and w not in _DOLGU}


def benzerlik(a: str, b: str) -> float:
    if a.split(":")[0] != b.split(":")[0]:  # YAP ile YAPMA aynı kural değildir
        return 0.0
    x, y = _tokenler(a), _tokenler(b)
    if not x or not y:
        return 0.0
    jaccard = len(x & y) / len(x | y)
    # Biri ötekinin genişletilmiş hali (QC aynı kuralı ek ayrıntıyla yazar): kısa olanın tamamı içerideyse aynı kural.
    kapsama = len(x & y) / min(len(x), len(y)) if min(len(x), len(y)) >= 3 else 0.0
    return max(jaccard, 0.9 * kapsama)


def bul_benzer(d: Depo, metin: str, *, durumlar: tuple[str, ...] = ("aktif", "oneri", "pasif", "silinen")) -> Kural | None:
    aday = max((k for k in d.kurallar if k.durum in durumlar), key=lambda k: benzerlik(k.metin, metin), default=None)
    return aday if aday and benzerlik(aday.metin, metin) >= BENZERLIK else None


def _yeni_id(d: Depo) -> str:
    n = max((int(k.id[1:]) for k in d.kurallar if re.fullmatch(r"K\d+", k.id)), default=0)
    return f"K{n + 1:04d}"


def _ara(d: Depo, kid: str) -> Kural:
    for k in d.kurallar:
        if k.id == kid:
            return k
    raise KeyError(f"kural yok: {kid}")


# ------------------------------------------------------------------ işlemler

def ekle(d: Depo, metin: str, **alan) -> Kural:
    """Kullanıcının elle eklediği kural: her zaman aktif. Aynısı varsa tekrar artar ve o döner."""
    if (var := bul_benzer(d, metin)) is not None:
        var.tekrar += 1
        var.guncelleme = date.today().isoformat()
        if var.durum in ("silinen", "pasif", "oneri"):
            var.durum = "aktif"  # kullanıcı açıkça yeniden istedi
        return var
    k = Kural(id=_yeni_id(d), metin=metin, **alan)
    d.kurallar.append(k)
    return k


def aday_ekle(d: Depo, metin: str, *, kaynak: str, kanit: Kanit | None = None, **alan) -> tuple[Kural | None, str]:
    """QC'nin kural adayı. Döner: (kural, 'yeni' | 'tekrar' | 'mezar').

    'mezar': kullanıcı benzerini silmiş; aday düşer, yeniden önerilmez.
    """
    var = bul_benzer(d, metin)
    if var is not None and var.durum == "silinen":
        return None, "mezar"
    if var is not None:
        var.tekrar += 1
        var.guncelleme = date.today().isoformat()
        if kanit:
            var.kanit = [*var.kanit, kanit][-5:]
        return var, "tekrar"
    k = Kural(id=_yeni_id(d), metin=metin, kaynak=kaynak, kanit=[kanit] if kanit else [],
              durum="oneri" if ayar().onay_bekle else "aktif", **alan)
    d.kurallar.append(k)
    return k, "yeni"


def durum_degistir(d: Depo, kid: str, durum: Durum) -> Kural:
    k = _ara(d, kid)
    k.durum = durum
    k.guncelleme = date.today().isoformat()
    return k


def guncelle(d: Depo, kid: str, **alan) -> Kural:
    k = _ara(d, kid)
    yeni = Kural.model_validate({**k.model_dump(by_alias=True), **alan, "guncelleme": date.today().isoformat()})
    d.kurallar[d.kurallar.index(k)] = yeni
    return yeni


def kapi_onerileri(d: Depo) -> list[Kural]:
    """ADR 0041: tekrar >= 2 ve ölçülebilir kural koda kapı olarak yazılmalı."""
    return [k for k in d.kurallar if k.durum == "aktif" and k.tekrar >= 2 and k.olcut and "kapı:" not in k.olcut]


_QC_KATEGORI = {"stil": "renk", "okunurluk": "grafik", "ritim": "kesim", "ses": "ses", "teknik": "teknik", "tutarlilik": "genel"}


def _rol(v) -> str:
    """QC hedefi rol sınıfı değilse (ör. seviyeli ekipte E4 slotu ya da boş) hepsi: tek aday bütün triyajı düşürmesin."""
    return v if v in get_args(Rol) else "hepsi"


def qc_isle(bulgular: list[dict], *, proje: str, kaynak_kok: str = "") -> dict:
    """QC bulgularını kural deposuna işler: aday → yeni ya da tekrar (mezar taşı düşer); kural_id → ihlal sayımı.

    Döner: {"yeni": [id], "tekrar": [id], "mezar": [metin], "ihlal": {id: sayı}}. Depo değiştiyse yazılır.
    """
    d = yukle()
    sonuc: dict = {"yeni": [], "tekrar": [], "mezar": [], "ihlal": {}}
    for b in bulgular:
        if b.get("kural_id"):
            sonuc["ihlal"][b["kural_id"]] = sonuc["ihlal"].get(b["kural_id"], 0) + 1
        aday = b.get("kural_adayi")
        if not aday:
            continue
        kanit = Kanit(proje=proje, zaman=(b.get("zaman") or [None])[0], kare=b.get("kanit"), **{"not": b.get("sorun")})
        k, ne = aday_ekle(d, aday, kaynak=f"kk:{b['id'][:2]}", kanit=kanit, kategori=_QC_KATEGORI.get(b.get("kategori"), "genel"),
                          hedef_rol=_rol(b.get("hedef")), onem=b.get("onem", "P1"), neden=b.get("sorun", "")[:200])
        if ne == "mezar":
            sonuc["mezar"].append(aday)
        else:
            sonuc[ne].append(k.id)
    for kid in sonuc["ihlal"]:
        try:
            k = _ara(d, kid)
            k.tekrar += 1  # ADR 0041: tekrar eden ihlal kapı önerisini tetikler
        except KeyError:
            pass
    if sonuc["yeni"] or sonuc["tekrar"] or sonuc["ihlal"]:
        kaydet(d)
    return sonuc


# ------------------------------------------------------------------ teslim

def _kapsamda(k: Kural, studyo: str | None, stil: str | None, proje: str | None) -> bool:
    return k.kapsam == "global" or {"studyo": studyo, "stil": stil, "proje": proje}.get(k.kapsam) == k.kapsam_deger


def secim(d: Depo, *, rol: str = "hepsi", studyo: str | None = None, stil: str | None = None, proje: str | None = None) -> list[Kural]:
    sec = [k for k in d.kurallar if k.durum == "aktif" and _kapsamda(k, studyo, stil, proje)
           and (rol == "hepsi" or k.hedef_rol in (rol, "hepsi"))]
    return sorted(sec, key=lambda k: (ONEM_SIRA[k.onem], -k.tekrar, k.id))


def paket(d: Depo, *, rol: str = "hepsi", studyo: str | None = None, stil: str | None = None, proje: str | None = None,
          butce_token: int | None = None) -> str:
    """Editöre giden kural bloğu: P0 → P2, bütçe içinde. P0 asla düşmez; sığmayan P2'ler tek satır özet olur."""
    butce = (butce_token or ayar().butce_token) * 4  # karakter
    sat, kalan, dusen = [], butce, []
    for k in secim(d, rol=rol, studyo=studyo, stil=stil, proje=proje):
        s = f"- [{k.id} {k.onem}] {k.metin}"
        if k.onem != "P0" and len(s) > kalan:
            dusen.append(k)
            continue
        sat.append(s)
        kalan -= len(s) + 1
    if dusen:
        kat = sorted({k.kategori for k in dusen})
        sat.append(f"- (+{len(dusen)} düşük öncelikli kural sığmadı: {', '.join(kat)}; ayrıntı library/checks.md)")
    return "\n".join(sat)


# ------------------------------------------------------------------ checks.md

BASLIK = {"altyazi": "Altyazı", "kadraj": "Kadraj", "kesim": "Kesim", "grafik": "Grafik", "renk": "Renk", "hareket": "Hareket",
          "gecis": "Geçiş", "ses": "Ses", "icerik": "İçerik", "slop": "AI slop", "yayin": "Yayın", "teknik": "Teknik", "genel": "Genel"}


def checks_md(d: Depo) -> str:
    sat = ["# checks.md", "",
           "<!-- ÜRETİLMİŞ DOSYA: elle düzenleme. Tek kaynak library/kurallar/kurallar.json (ADR 0047). "
           "Kural eklemek için: vedit kural ekle \"YAP: ...\" ya da Stüdyo > Kurallar. -->", "",
           "Kullanıcının her düzeltmesi ve kalite kontrolün genelleşmiş bulgusu burada tek satırlık YAP ya da YAPMA kuralıdır. "
           "Ajan editten önce okur; `denetim` her kontrol karesini buna göre denetler. Aynı düzeltme ikinci kez gelirse kural "
           "koda kapı olarak yazılır (ADR 0041). Köşeli parantez: kimlik, önem, tekrar.", ""]
    for kat in KATEGORILER:
        ks = [k for k in d.kurallar if k.kategori == kat and k.durum == "aktif"]
        if not ks:
            continue
        sat += [f"## {BASLIK[kat]}"]
        for k in sorted(ks, key=lambda k: (ONEM_SIRA[k.onem], k.id)):
            ek = [k.kapsam if k.kapsam == "global" else f"{k.kapsam}: {k.kapsam_deger}"]
            if k.olcut:
                ek.append(f"kapı: {k.olcut}")
            if k.kanit and k.kanit[-1].proje:
                ek.append(k.kanit[-1].proje)
            sat.append(f"- {k.metin} [{k.id} {k.onem}{f' ×{k.tekrar}' if k.tekrar > 1 else ''}] ({'; '.join(ek)})")
        sat.append("")
    oneriler = [k for k in d.kurallar if k.durum == "oneri"]
    if oneriler:
        sat += ["## Onay bekleyen öneriler (etkin değil)"] + [f"- {k.metin} [{k.id}, {k.kaynak}]" for k in oneriler] + [""]
    return "\n".join(sat)


# ------------------------------------------------------------------ göç

_BOLUM = {"Altyazı": "altyazi", "Kadraj": "kadraj", "İçerik": "icerik", "Hareket": "hareket", "AI slop": "slop"}
_ANAHTAR = [("icerik", r"senaryo|reels'?in|repo adı"), ("ses", r"\bses(i|inde)?\b|sfx|müzik|synth|olay_"), ("yayin", r"yayin|açıklama|hashtag"),
            ("renk", r"renk|tema|turuncu|palet"), ("grafik", r"ikon|motion|rozet|grafik|pano"), ("teknik", r"proxy|alpha_mode")]
_ROL = {"altyazi": "E3", "ses": "E3", "grafik": "E2", "renk": "E2", "hareket": "E2", "gecis": "E1", "kesim": "E1", "kadraj": "E2"}


def goc(md: Path) -> Depo:
    """Eski elle yazılmış checks.md → depo (tek seferlik). Bölüm başlığı kategori, parantez içi kanıt olur."""
    d, bolum = Depo(), "genel"
    for satir in md.read_text(encoding="utf-8").splitlines():
        if satir.startswith("## "):
            bolum = _BOLUM.get(satir[3:].strip(), "duzeltme")
            continue
        m = re.match(r"^- (YAP|YAPMA): (.+)$", satir.strip())
        if not m:
            continue
        govde = m.group(2)
        kanit = re.search(r"\(([^()]*\d{4}-\d{2}-\d{2}[^()]*)\)\s*$", govde)
        kapi = re.search(r"[Kk]apı: ([^()]+?)(?=\s*\(|$)", govde)
        temiz = govde[:kanit.start()].strip() if kanit else govde
        if kapi:
            temiz = temiz.replace(f"Kapı: {kapi.group(1)}", "").replace(f"kapı: {kapi.group(1)}", "").strip().rstrip(".") + "."
        kat = bolum if bolum != "duzeltme" else next((k for k, d_ in _ANAHTAR if re.search(d_, govde, re.I)), "genel")
        proje = kanit.group(1).split(",")[0].strip() if kanit else None
        tarih = re.search(r"\d{4}-\d{2}-\d{2}", kanit.group(1)).group(0) if kanit else date.today().isoformat()
        d.kurallar.append(Kural(
            id=_yeni_id(d), metin=f"{m.group(1)}: {temiz}", kategori=kat, hedef_rol=_ROL.get(kat, "hepsi"),
            onem="P0" if kat == "altyazi" or kapi else "P1", olcut=kapi.group(1).strip() if kapi else None,
            kanit=[Kanit(proje=proje)] if proje and proje != "kullanıcı isteği" else [], olusturma=tarih, guncelleme=tarih,
            neden="checks.md göçü"))
    return d
