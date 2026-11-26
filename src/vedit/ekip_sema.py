"""Ekip motoru şemaları: seviye tablosu, ayar, görev kartları, orkestratör çıktıları, editör yaması, kalite kontrol bulgusu.

WHY: bkz. wiki/decisions/0053-seviyeli-ekip-orkestrator.md. Ajan çıktısı veridir: her yama, plan ve bulgu şemadan geçer,
geçmeyen birleşmez. Seviye editör ve kalite kontrol sayısını sabitler; işi orkestratör dağıtır (geçersiz planda sabit tablo).
"""

from __future__ import annotations

import math
import re
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator, model_validator

# ---------------------------------------------------------------- seviye ve roller

SEVIYE: dict[str, tuple[int, int]] = {"low": (2, 1), "medium": (4, 2), "high": (6, 3), "xhigh": (8, 4), "max": (10, 5)}
SeviyeAd = Literal["low", "medium", "high", "xhigh", "max"]
# Swarm (ADR 0059): seviye artık ajan tavanıdır (editör + kalite kontrol); dağılımı ve modeli orkestratör seçer.
EN_COK: dict[str, int] = {"low": 3, "medium": 6, "high": 9, "xhigh": 12, "max": 15}
EDITOR_EN_COK, KK_EN_COK = 10, 5

KATMANLAR = ("kurgu", "grafik", "sfx", "muzik", "stil")
Katman = Literal["kurgu", "grafik", "sfx", "muzik", "stil"]
KATMAN_ADI = {"kurgu": "Kurgu", "grafik": "Grafik", "sfx": "Ses efekti", "muzik": "Müzik", "stil": "Altyazı ve tema"}
KATMAN_TANIM = {
    "kurgu": "kesim, sıra, hook, V1 ve A1, punch/zoom, hazır efekt, geçiş, işaretler",
    "grafik": "motion, metin grafiği, tam ekran sahne, grafik ve tablo (V1 dışındaki görüntü izleri)",
    "sfx": "ses efekti rol olayları (A1 dışındaki ses izleri, müzik hariç)",
    "muzik": "müzik, ducking, kazanç zarfı",
    "stil": "altyazı ayarı ve motion teması",
}
# Zaman dilimine bölünemeyen katmanlar: kurgu bütün zaman çizelgesini, stil skaler alanları taşır.
BOLUNMEZ = ("kurgu", "stil")
EDITOR_ROL_DOSYASI = {"kurgu": "editor-kurgu", "grafik": "editor-grafik", "sfx": "editor-ses-stil", "muzik": "editor-ses-stil",
                      "stil": "editor-ses-stil"}
# Kural deposunun hedef_rol alanı rol sınıfıdır (ADR 0047): E1 kurgu, E2 grafik, E3 ses ve stil.
KURAL_ROLU = {"kurgu": "E1", "grafik": "E2", "sfx": "E3", "muzik": "E3", "stil": "E3"}

KK_ROLLERI = ("genel", "kurgu", "gorsel", "ses", "kurgu-ses", "kural", "izleyici")
KkRol = Literal["genel", "kurgu", "gorsel", "ses", "kurgu-ses", "kural", "izleyici"]
KK_ROL_ADI = {"genel": "Genel denetim", "kurgu": "Kurgu ve ritim", "gorsel": "Görsel ve stil", "ses": "Ses, altyazı, okunurluk",
              "kurgu-ses": "Kurgu, ritim ve ses", "kural": "Kural uyumu", "izleyici": "İzleyici gözü (hook, tutma)"}
KK_ROL_DOSYASI = {"genel": ["kk-genel"], "kurgu": ["kk-kurgu"], "gorsel": ["kk-gorsel"], "ses": ["kk-ses"],
                  "kurgu-ses": ["kk-kurgu", "kk-ses"], "kural": ["kk-kural"], "izleyici": ["kk-izleyici"]}
# Denetim alanları: kalite kontrol kartları birlikte üçünü de kapsamalı.
KK_ALAN = {"genel": {"kurgu", "gorsel", "ses"}, "kurgu": {"kurgu"}, "gorsel": {"gorsel"}, "ses": {"ses"},
           "kurgu-ses": {"kurgu", "ses"}, "kural": set(), "izleyici": set()}
KK_KURAL_ROLU = {"kurgu": ["E1"], "gorsel": ["E2"], "ses": ["E3"], "kurgu-ses": ["E1", "E3"]}  # diğerleri: hepsi

ORKESTRATOR = "O"
GRUPLAR = ("orkestrator", "editor", "kk")
SLOT_DESEN = re.compile(r"^(O|E(10|[1-9])|K[1-5])$")


def editorler(seviye: str) -> list[str]:
    return [f"E{i}" for i in range(1, SEVIYE[seviye][0] + 1)]


def kontroller(seviye: str) -> list[str]:
    return [f"K{i}" for i in range(1, SEVIYE[seviye][1] + 1)]


def Kirp(n: int):
    """En çok n karakterlik serbest metin; uzunsa kırpılır, reddedilmez.

    WHY: reel-video (2026-11-23) G2'de E3'ün düzeltme yaması tek pano mesajı 318 karakter olduğu için bütünüyle reddedildi;
    düzeltme sessizce kayboldu. Ajan metni veridir; fazla uzun not yamanın, planın ya da triyajın tamamını düşürmemeli."""
    return Annotated[str, BeforeValidator(lambda v: v[:n] if isinstance(v, str) else v), Field(max_length=n)]


def grup(slot: str) -> str:
    return "orkestrator" if slot == ORKESTRATOR else "editor" if slot.startswith("E") else "kk"


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------- ayar

Motor = Literal["claude", "antigravity", "codex", "opencode"]


class Slot(_M):
    motor: Motor
    model: str | None = None
    seviye: str | None = None  # akıl yürütme seviyesi (motorlar.SEVIYELER)
    yedek_motor: Motor | None = None
    yedek_model: str | None = None
    yedek_seviye: str | None = None


def _vars_gruplar() -> dict[str, Slot]:
    return {"orkestrator": Slot(motor="claude", model="claude-opus-5-5", seviye="high", yedek_motor="antigravity", yedek_model="gemini-4-argon-high"),
            "editor": Slot(motor="claude", model="claude-sonnet-5-5", seviye="medium", yedek_motor="antigravity", yedek_model="gemini-4-neon-high"),
            "kk": Slot(motor="antigravity", model="gemini-4-neon-high", yedek_motor="claude", yedek_model="claude-sonnet-5-5")}


class EkipAyar(_M):
    ad: str = "varsayilan"
    ekip_seviye: SeviyeAd = "medium"
    gruplar: dict[str, Slot] = Field(default_factory=_vars_gruplar)
    ezme: dict[str, Slot] = {}  # slot bazında (ör. "E1": Opus); yoksa grup ayarı
    eszamanlilik: int | None = Field(default=None, ge=1, le=15)  # None: editör sayısı
    motion: Literal["az", "orta", "yogun"] = "yogun"
    stil: str | None = None
    # ADR 0054: low seviye, orkestratör çağrısı yok (varsayılan dağıtım, deterministik kural kapısı, triyajsız), render yalnız gerekince
    hizli: bool = False
    # ADR 0059: swarm ajan tavanı (editör + kalite kontrol); yoksa seviyeden (EN_COK)
    # En küçük geçerli ekip 3'tür: E1 (yalnız kurgu) + kalan katmanlar için bir editör + bir QC.
    en_cok: int | None = Field(default=None, ge=3, le=EDITOR_EN_COK + KK_EN_COK)

    @model_validator(mode="before")
    @classmethod
    def _goc(cls, v: Any) -> Any:
        """Eski 6 slotlu ayar (ADR 0044/0048): E1 orkestratöre, E2 editörlere, K1 kalite kontrole taşınır."""
        if not isinstance(v, dict) or "slotlar" not in v:
            return v
        v = dict(v)
        eski = v.pop("slotlar") or {}
        for alan in ("bolus", "tur"):
            v.pop(alan, None)
        if "gruplar" not in v and eski:
            g = {}
            for ad, kaynak in (("orkestrator", "E1"), ("editor", "E2"), ("kk", "K1")):
                if kaynak in eski:
                    g[ad] = eski[kaynak]
            v["gruplar"] = {**{k: s.model_dump() for k, s in _vars_gruplar().items()}, **g}
        if v.get("eszamanlilik") and v["eszamanlilik"] > 15:
            v["eszamanlilik"] = 15
        return v

    @field_validator("gruplar")
    @classmethod
    def _uc_grup(cls, v):
        eksik = [g for g in GRUPLAR if g not in v]
        fazla = [g for g in v if g not in GRUPLAR]
        if eksik or fazla:
            raise ValueError(f"gruplar {', '.join(GRUPLAR)} olmalı (eksik {eksik}, fazla {fazla})")
        return v

    @field_validator("ezme")
    @classmethod
    def _ezme_slot(cls, v):
        kotu = [s for s in v if not SLOT_DESEN.match(s)]
        if kotu:
            raise ValueError(f"geçersiz slot: {kotu} (O, E1-E10, K1-K5)")
        return v

    def editorler(self) -> list[str]:
        return editorler(self.ekip_seviye)

    def kontroller(self) -> list[str]:
        return kontroller(self.ekip_seviye)

    def slotlar(self) -> list[str]:
        return [ORKESTRATOR, *self.editorler(), *self.kontroller()]

    def slot(self, s: str) -> Slot:
        return self.ezme.get(s) or self.gruplar[grup(s)]

    def tavan(self) -> int:
        return self.en_cok or EN_COK[self.ekip_seviye]

    def es(self) -> int:
        # Swarm'da editör sayısını plan belirler; havuz tavana göre açılır, bellek sınırı ajan_eszamanlilik'te.
        return self.eszamanlilik or (len(self.editorler()) if self.hizli else min(EDITOR_EN_COK, self.tavan()))


# ---------------------------------------------------------------- orkestratör: plan, kapı, triyaj

class Gorev(_M):
    """Editör görev kartı: hangi katmanlar, hangi zaman aralığı (taban zaman çizelgesinde), odak ve zorunlu kurallar.
    Swarm (ADR 0059): orkestratör kartın motorunu, modelini ve seviyesini seçebilir; boşsa grup ayarı."""
    slot: str = Field(pattern=r"^E(10|[1-9])$")
    katmanlar: list[Katman] = Field(min_length=1)
    aralik: list[float] | None = Field(default=None, min_length=2, max_length=2)
    odak: Kirp(600) = ""
    kurallar: list[str] = []  # kural id (K0012); P0'ları vedit kendisi ekler
    motor: Motor | None = None
    model: str | None = None
    seviye: str | None = None

    @field_validator("kurallar")
    @classmethod
    def _kural_id(cls, v):
        return [x for x in dict.fromkeys(v) if re.fullmatch(r"K\d{4}", x)]


class KkGorev(_M):
    slot: str = Field(pattern=r"^K[1-5]$")
    rol: KkRol
    aralik: list[float] | None = Field(default=None, min_length=2, max_length=2)
    odak: Kirp(600) = ""
    motor: Motor | None = None
    model: str | None = None
    seviye: str | None = None


class Plan(_M):
    hook: dict[str, Any] | None = None  # {"bas", "son", "neden"}
    gorevler: list[Gorev] = []
    kk_gorevler: list[KkGorev] = []
    gerekce: Kirp(1500) = ""
    # ADR 0064: G0.5 yaratıcı brif plan çağrısıyla gelir. Sözlük kalır, `YaraticiBrif` ayrıca doğrular: bozuk brif planı düşürmez.
    yaratici_brif: dict[str, Any] | None = None


# ---------------------------------------------------------------- G0.5 yaratıcı brif (ADR 0064)

def _ilk(n: int):
    """Liste en çok n öğe; fazlası kırpılır, reddedilmez (Kirp ile aynı gerekçe)."""
    return BeforeValidator(lambda v: v[:n] if isinstance(v, list) else v)


class EnerjiDilimi(BaseModel):
    model_config = ConfigDict(extra="ignore")
    aralik: list[float] = Field(min_length=2, max_length=2)
    seviye: int = Field(ge=1, le=5)
    neden: Kirp(200) = ""

    @field_validator("aralik")
    @classmethod
    def _sira(cls, v):
        if v[0] < 0 or v[1] <= v[0]:
            raise ValueError("aralik [bas, son], 0 <= bas < son")
        return v


class ImzaAni(BaseModel):
    model_config = ConfigDict(extra="ignore")
    t: float | None = Field(default=None, ge=0)  # sekans saniyesi, yaklaşık; çapa söz
    soz: Kirp(160) = ""
    ne: Kirp(300)


class YaraticiBrif(BaseModel):
    """Videoya özgü yaratıcı yön (`work/edit/yaratici-brif.json`). Bütün editörler ve QC bu brife göre karar verir.

    WHY: bkz. wiki/decisions/0064-yaratici-yon.md. Ajan metni veridir ama brif yaratıcı bir taslaktır: bilinmeyen alan ve
    fazla öğe brifi düşürmez; yalnız tez boşsa ya da enerji seviyesi aralık dışındaysa brif geçersizdir."""
    model_config = ConfigDict(extra="ignore")
    tez: Kirp(300) = Field(min_length=3)
    metafor: Kirp(300) = ""
    iplik: Kirp(200) = ""
    enerji: Annotated[list[EnerjiDilimi], _ilk(8)] = []
    imza_anlari: Annotated[list[ImzaAni], _ilk(3)] = []
    ses: Kirp(400) = ""
    riskler: Annotated[list[Kirp(200)], _ilk(3)] = []
    yasak: Annotated[list[Kirp(200)], _ilk(5)] = []
    istek: str | None = None  # vedit: brifin yazıldığı kullanıcı isteği; istek değişince brif yenilenir
    kilit: bool = False       # kullanıcı elle yazdıysa vedit üzerine yazmaz


class KapiKarari(_M):
    slot: str = Field(pattern=r"^E(10|[1-9])$")
    karar: Literal["kabul", "duzelt"]
    brif: Kirp(1500) = ""


class KapiCikti(_M):
    kararlar: list[KapiKarari] = []
    not_: Kirp(800) = Field(default="", alias="not")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Red(_M):
    id: str
    neden: Kirp(300) = ""


class Triyaj(_M):
    kabul: list[str] = []      # bulgu id
    red: list[Red] = []        # yanlış pozitif
    kural_onay: list[str] = []  # kural adayı onaylanan bulgu id'leri
    not_: Kirp(800) = Field(default="", alias="not")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ---------------------------------------------------------------- editör ve kalite kontrol çıktıları

class Bulgu(_M):
    id: str = Field(pattern=r"^K[1-9]-\d{3}$")
    hedef: str | None = Field(default=None, pattern=r"^E(10|[1-9])$")  # vedit katman ve zamandan yeniden bulur
    onem: Literal["P0", "P1", "P2"]
    zaman: list[float] = Field(min_length=2, max_length=2)
    katman: str
    kategori: Literal["stil", "okunurluk", "ritim", "ses", "teknik", "tutarlilik", "etki"]  # WHY: bkz. wiki/decisions/0064-yaratici-yon.md
    kanit: str  # açılmış kare dosyası; dosya yoksa bulgu düşer
    sorun: str
    beklenen: str  # ölçülebilir kabul ölçütü
    # ADR 0047: ihlal edilen etkin kuralın kimliği ve bu projeye özgü olmayan, genelleşmiş tek satır kural adayı.
    kural_id: str | None = Field(default=None, pattern=r"^K\d{4}$")
    kural_adayi: str | None = Field(default=None, pattern=r"^(YAP|YAPMA): \S.{8,}$")

    @field_validator("zaman")
    @classmethod
    def _sira(cls, v):
        if v[0] < 0 or v[1] < v[0]:
            raise ValueError("zaman [baş, son] ve baş <= son olmalı")
        return v


class Mesaj(_M):
    """Pano mesajı (ADR 0048): en çok iki satır; ajan yalnız kendi aralığına değen mesajları görür."""
    tip: Literal["claim", "constraint", "request", "done"]
    aralik: list[float] = Field(min_length=2, max_length=2)
    metin: Kirp(240)
    kimden: str = ""  # vedit doldurur


class KuralUyum(_M):
    id: str = Field(pattern=r"^K\d{4}$")
    nasil: Kirp(300) = ""


class Yama(_M):
    """Editör çıktısı (ADR 0048, 0053): yalnız kendi katmanına ekle, güncelle, sil. Tam liste değil, fark."""
    ekle: list[dict[str, Any]] = []
    guncelle: list[dict[str, Any]] = []   # her öğe {"id": ..., <değişen alanlar>}
    sil: list[str] = []
    kaynaklar: dict[str, dict[str, Any]] = {}  # yalnız yeni kaynak
    isaretler: list[dict[str, Any]] | None = None  # kurgu
    altyazi: dict[str, Any] | None = None  # stil
    motion_tema: str | None = None  # stil
    hook: dict[str, Any] | None = None  # kurgu
    # grafik: bu videoya özgü HyperFrames kompozisyonu {ad: index.html içeriği}; dosyayı vedit yazar (ADR 0050)
    hf: dict[str, str] = {}
    pano: list[Mesaj] = []
    kural_uyum: list[KuralUyum] = []  # ADR 0053: kartın zorunlu kurallarına nasıl uyduğu
    rapor: Kirp(1500) = ""
    oz_denetim: Kirp(600) = ""  # WHY: bkz. wiki/decisions/0064-yaratici-yon.md


def _uretim_puani_temizle(v: Any) -> dict[str, int] | None:
    """Üretim puanını 1-5 tam sayılarına kırpar; bilinmeyen anahtar kalır, bozuk değer ya da sözlük dışı girdi None olur.

    WHY: bkz. wiki/decisions/0064-yaratici-yon.md."""
    if not isinstance(v, dict):
        return None
    temiz: dict[str, int] = {}
    for k, val in v.items():
        if not isinstance(k, str) or isinstance(val, bool):
            continue
        try:
            f = float(val)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(f):
            continue
        temiz[k] = max(1, min(5, int(round(f))))
    return temiz or None


class KontrolCikti(_M):
    bulgular: list[Bulgu] = []
    brif: str = ""  # editöre profesyonel düzeltme brifi (markdown)
    uretim_puani: Annotated[dict[str, int] | None, BeforeValidator(_uretim_puani_temizle)] = None  # WHY: bkz. wiki/decisions/0064-yaratici-yon.md
