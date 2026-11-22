"""Ekip motoru şemaları: seviye tablosu, ayar, görev kartları, orkestratör çıktıları, editör yaması, kalite kontrol bulgusu.

WHY: bkz. wiki/decisions/0053-seviyeli-ekip-orkestrator.md. Ajan çıktısı veridir: her yama, plan ve bulgu şemadan geçer,
geçmeyen birleşmez. Seviye editör ve kalite kontrol sayısını sabitler; işi orkestratör dağıtır (geçersiz planda sabit tablo).
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ---------------------------------------------------------------- seviye ve roller

SEVIYE: dict[str, tuple[int, int]] = {"low": (2, 1), "medium": (4, 2), "high": (6, 3), "xhigh": (8, 4), "max": (10, 5)}
SeviyeAd = Literal["low", "medium", "high", "xhigh", "max"]

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

    def es(self) -> int:
        return self.eszamanlilik or len(self.editorler())


# ---------------------------------------------------------------- orkestratör: plan, kapı, triyaj

class Gorev(_M):
    """Editör görev kartı: hangi katmanlar, hangi zaman aralığı (taban zaman çizelgesinde), odak ve zorunlu kurallar."""
    slot: str = Field(pattern=r"^E(10|[1-9])$")
    katmanlar: list[Katman] = Field(min_length=1)
    aralik: list[float] | None = Field(default=None, min_length=2, max_length=2)
    odak: str = Field(default="", max_length=600)
    kurallar: list[str] = []  # kural id (K0012); P0'ları vedit kendisi ekler

    @field_validator("kurallar")
    @classmethod
    def _kural_id(cls, v):
        return [x for x in dict.fromkeys(v) if re.fullmatch(r"K\d{4}", x)]


class KkGorev(_M):
    slot: str = Field(pattern=r"^K[1-5]$")
    rol: KkRol
    aralik: list[float] | None = Field(default=None, min_length=2, max_length=2)
    odak: str = Field(default="", max_length=600)


class Plan(_M):
    hook: dict[str, Any] | None = None  # {"bas", "son", "neden"}
    gorevler: list[Gorev] = []
    kk_gorevler: list[KkGorev] = []
    gerekce: str = Field(default="", max_length=1500)


class KapiKarari(_M):
    slot: str = Field(pattern=r"^E(10|[1-9])$")
    karar: Literal["kabul", "duzelt"]
    brif: str = Field(default="", max_length=1500)


class KapiCikti(_M):
    kararlar: list[KapiKarari] = []
    not_: str = Field(default="", max_length=800, alias="not")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Red(_M):
    id: str
    neden: str = Field(default="", max_length=300)


class Triyaj(_M):
    kabul: list[str] = []      # bulgu id
    red: list[Red] = []        # yanlış pozitif
    kural_onay: list[str] = []  # kural adayı onaylanan bulgu id'leri
    not_: str = Field(default="", max_length=800, alias="not")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ---------------------------------------------------------------- editör ve kalite kontrol çıktıları

class Bulgu(_M):
    id: str = Field(pattern=r"^K[1-9]-\d{3}$")
    hedef: str | None = Field(default=None, pattern=r"^E(10|[1-9])$")  # vedit katman ve zamandan yeniden bulur
    onem: Literal["P0", "P1", "P2"]
    zaman: list[float] = Field(min_length=2, max_length=2)
    katman: str
    kategori: Literal["stil", "okunurluk", "ritim", "ses", "teknik", "tutarlilik"]
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
    metin: str = Field(max_length=240)
    kimden: str = ""  # vedit doldurur


class KuralUyum(_M):
    id: str = Field(pattern=r"^K\d{4}$")
    nasil: str = Field(default="", max_length=300)


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
    rapor: str = Field(default="", max_length=1500)


class KontrolCikti(_M):
    bulgular: list[Bulgu] = []
    brif: str = ""  # editöre profesyonel düzeltme brifi (markdown)
