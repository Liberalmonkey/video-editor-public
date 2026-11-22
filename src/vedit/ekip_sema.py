"""Ekip motoru şemaları: ayar (6 slot), editör parça dosyası, kalite kontrol bulgusu.

WHY: bkz. wiki/decisions/0044-ekip-motoru.md. Ajan çıktısı veridir: her parça ve bulgu şemadan geçer, geçmeyen birleşmez.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

EDITORLER = ("E1", "E2", "E3")
KONTROLLER = ("K1", "K2", "K3")
SLOTLAR = EDITORLER + KONTROLLER
HEDEF = {"K1": "E1", "K2": "E2", "K3": "E3"}  # her kontrolcü kendi editörüne brif yazar
ROL_ADI = {"E1": "editor-kurgu", "E2": "editor-grafik", "E3": "editor-ses-stil",
           "K1": "kk-kurgu", "K2": "kk-gorsel", "K3": "kk-ses"}
ROL_TANIM = {"E1": "Kurgu: kesim, sıra, hook, V1, punch/zoom, hazır efekt, geçiş",
             "E2": "Grafik: motion, metin grafiği, sahne, grafik/tablo (V2/V3)",
             "E3": "Ses ve stil: ses efekti rolleri, müzik, ducking, altyazı, tema tutarlılığı (A2/A3)",
             "K1": "Kurgu ve ritim denetimi", "K2": "Görsel ve stil denetimi", "K3": "Ses, altyazı ve okunurluk denetimi"}


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Slot(_M):
    motor: Literal["claude", "antigravity", "codex", "opencode"]
    model: str | None = None
    seviye: str | None = None
    yedek_motor: Literal["claude", "antigravity", "codex", "opencode"] | None = None
    yedek_model: str | None = None
    yedek_seviye: str | None = None


def _vars_slotlar() -> dict[str, Slot]:
    return {"E1": Slot(motor="claude", model="claude-opus-5-5", seviye="high", yedek_motor="antigravity", yedek_model="gemini-4-argon-high"),
            "E2": Slot(motor="claude", model="claude-sonnet-5-5", seviye="medium", yedek_motor="antigravity", yedek_model="gemini-4-neon-high"),
            "E3": Slot(motor="claude", model="claude-sonnet-5-5", seviye="medium", yedek_motor="antigravity", yedek_model="gemini-4-neon-high"),
            "K1": Slot(motor="antigravity", model="gemini-4-argon-high", yedek_motor="claude", yedek_model="claude-sonnet-5-5"),
            "K2": Slot(motor="antigravity", model="gemini-4-neon-high", yedek_motor="claude", yedek_model="claude-sonnet-5-5"),
            "K3": Slot(motor="antigravity", model="gemini-4-neon-xhigh", yedek_motor="claude", yedek_model="claude-sonnet-5-5")}


class EkipAyar(_M):
    ad: str = "varsayilan"
    slotlar: dict[str, Slot] = Field(default_factory=_vars_slotlar)
    bolus: Literal["rol", "zaman"] = "rol"
    tur: int = Field(default=3, ge=1, le=6)
    motion: Literal["az", "orta", "yogun"] = "yogun"
    stil: str | None = None
    eszamanlilik: int = Field(default=6, ge=1, le=6)  # ADR 0048: E1+E2+E3 ve K1+K2+K3 aynı anda

    @field_validator("slotlar")
    @classmethod
    def _alti_slot(cls, v):
        eksik = [s for s in SLOTLAR if s not in v]
        fazla = [s for s in v if s not in SLOTLAR]
        if eksik or fazla:
            raise ValueError(f"slotlar {', '.join(SLOTLAR)} olmalı (eksik {eksik}, fazla {fazla})")
        return v


class Parca(_M):
    """Editörün tek çıktısı: sahip olduğu izlerin klipleri (tam liste) ve izin verilen alanlar."""
    klipler: list[dict[str, Any]] = []
    kaynaklar: dict[str, dict[str, Any]] = {}  # yalnız yeni kaynak eklenir
    isaretler: list[dict[str, Any]] | None = None  # E1
    altyazi: dict[str, Any] | None = None  # E3
    motion_tema: str | None = None  # E3
    rapor: str = ""  # ne yaptı, en çok 15 satır


class Bulgu(_M):
    id: str = Field(pattern=r"^K[123]-\d{3}$")
    hedef: Literal["E1", "E2", "E3"]
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


class Yama(_M):
    """Ekip v2 editör çıktısı (ADR 0048): yalnız kendi katmanına ekle, güncelle, sil. Tam liste değil, fark."""
    ekle: list[dict[str, Any]] = []
    guncelle: list[dict[str, Any]] = []   # her öğe {"id": ..., <değişen alanlar>}
    sil: list[str] = []
    kaynaklar: dict[str, dict[str, Any]] = {}  # yalnız yeni kaynak
    isaretler: list[dict[str, Any]] | None = None  # E1
    altyazi: dict[str, Any] | None = None  # E3
    motion_tema: str | None = None  # E3
    hook: dict[str, Any] | None = None  # E1 sözleşme çağrısı: {"bas", "son", "neden"}
    # E2: bu videoya özgü HyperFrames kompozisyonu {ad: index.html içeriği}; dosyayı vedit yazar (ADR 0050)
    hf: dict[str, str] = {}
    pano: list[Mesaj] = []
    rapor: str = Field(default="", max_length=1500)


class KontrolCikti(_M):
    bulgular: list[Bulgu] = []
    brif: str = ""  # editöre profesyonel düzeltme brifi (markdown)
