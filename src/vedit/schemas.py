"""Veri sözleşmeleri: studio.yaml, project.yaml, edl.json, timeline.json, scenes.json, SFX manifest.

# WHY: bkz. wiki/decisions/0005-timeline-json-tek-dogruluk-kaynagi.md — LLM bu şemalara
# parametre yazar; build/cut/mix deterministik olarak bunlardan üretilir. Şema hatası
# render'dan önce, ucuza yakalanır.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------- stüdyo / proje

class Format(_M):
    width: int = 1920
    height: int = 1080
    fps: int = 30


class Variant(_M):
    name: str
    width: int
    height: int


class Loudness(_M):
    integrated: float = -14.0
    true_peak: float = -1.0
    lra: float = 11.0


class SafeArea(_M):
    top: float = 0.0
    bottom: float = 0.0
    left: float = 0.0
    right: float = 0.0


class CaptionCfg(_M):
    style: str = "odak"
    max_chars: int = 32
    max_words: int = 7
    lines: int = 2
    uppercase: bool = False
    burn: bool = True             # videoya göm; False ise yalnızca SRT


class StudioConfig(_M):
    studio: str
    label: str
    pipeline: Literal["footage", "animation", "mixed"]
    language: str = "tr"
    format: Format = Format()
    variants: list[Variant] = []
    loudness: Loudness = Loudness()
    safe_area: SafeArea = SafeArea()
    captions: CaptionCfg = CaptionCfg()
    target_duration: tuple[float, float] = (30, 60)
    style: str = "default"
    words_per_minute: dict[str, int] = {"tr": 140, "en": 150}


class ProjectState(_M):
    step: str = "brief"
    done: list[str] = []
    gates: dict[str, Literal["pending", "approved", "skipped"]] = {}
    notes: list[str] = []


class Project(_M):
    id: str
    studio: str
    title: str
    pipeline: Literal["footage", "animation", "mixed"]
    language: str = "tr"
    created: str
    format: Format
    style: str = "default"
    auto_approve: bool = False  # kullanıcı "toplu" dediyse onay kapıları atlanır
    studio_overrides: dict = {}  # stüdyo ayarlarını bu proje için ez (ör. UGC ama 16:9 web: safe_area, captions, variants)
    state: ProjectState = ProjectState()


# ---------------------------------------------------------------- EDL (çekim kesimi)

class EdlSegment(_M):
    src: str                 # sources anahtarı
    in_: float = Field(alias="in")
    out: float
    note: str = ""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @model_validator(mode="after")
    def _order(self):
        if self.out <= self.in_:
            raise ValueError(f"segment out ({self.out}) in'den ({self.in_}) büyük olmalı")
        return self


class Edl(_M):
    version: int = 1
    sources: dict[str, str]          # {"A": "input/take1.mp4"}
    segments: list[EdlSegment]
    audio_xfade_ms: int = 12


# ---------------------------------------------------------------- timeline

class Key(_M):
    """Kamera anahtar karesi (punch-in, zoom, pan) — klibe göre yerel saniye."""
    t: float
    scale: float = 1.0
    x: float = 0.0            # yüzde (xPercent)
    y: float = 0.0
    dur: float = 0.0          # 0 = anlık (jump-cut punch); >0 = yumuşak geçiş
    ease: str = "power2.inOut"


class VideoClip(_M):
    id: str
    src: str
    start: float
    dur: float
    in_: float = Field(0.0, alias="in")
    role: Literal["aroll", "broll", "screen", "image", "bg"] = "broll"
    fit: Literal["cover", "contain"] = "cover"
    layout: Literal["full", "pip-br", "pip-bl", "top-half", "bottom-half", "card", "portrait", "screen"] = "full"
    rate: float = 1.0
    keys: list[Key] = []
    crop_x: float | None = None   # 9:16 reframe için 0–1 yatay merkez (sabit); reframe yolu ayrı dosyada
    reframe: str | None = None    # reframe JSON yolu (proje göreli)
    view: list[float] | None = None  # kaynaktan kırpma [üst, sağ, alt, sol] yüzde (object-view-box inset) — ör. tarayıcı arayüzünü atmak
    blur: float = 0.0             # px (1080p ölçeğinde); dikey kaynağın arka plan dolgusu için
    dim: float = 0.0              # 0–1 karartma
    aspect: float | None = None   # portrait kartın en/boy oranı (view ile kırpılmış kaynak için; varsayılan 9/16)
    fade_in: float = 0.0
    fade_out: float = 0.0
    z: int = 0

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Overlay(_M):
    id: str
    block: str                    # blocks/<ad> ya da "custom"
    start: float
    dur: float
    props: dict[str, Any] = {}
    src: str | None = None        # custom blok için alt kompozisyon HTML yolu
    z: int = 10


class CaptionTrack(_M):
    src: str = "edit/captions.json"
    style: str | None = None      # None → studio varsayılanı
    enabled: bool = True


class AudioClip(_M):
    id: str
    src: str
    start: float = 0.0
    in_: float = Field(0.0, alias="in")
    dur: float | None = None
    gain_db: float = 0.0
    fade_in: float = 0.0
    fade_out: float = 0.0
    duck: bool = False            # müzik: konuşma altında ez

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SfxCue(_M):
    id: str
    t: float                      # olayın (peak'in) gerçekleştiği an
    type: str                     # manifest kategorisi/etiketi: whoosh, pop, click, phone_ring…
    intensity: Literal["soft", "medium", "hard"] = "medium"
    file: str | None = None       # resolver doldurur
    gain_db: float | None = None  # None → yoğunluğa göre varsayılan
    auto: bool = False            # kural tabanlı üretildi mi
    reason: str = ""


class AudioTracks(_M):
    voice: list[AudioClip] = []
    music: list[AudioClip] = []
    sfx: list[SfxCue] = []


class Chapter(_M):
    id: str
    title: str = ""
    start: float
    end: float


class Timeline(_M):
    version: int = 1
    format: Format
    duration: float
    style: str = "default"
    background: str = "#0b0b0c"
    chapters: list[Chapter] = []
    video: list[VideoClip] = []
    overlays: list[Overlay] = []
    captions: CaptionTrack | None = None
    audio: AudioTracks = AudioTracks()

    @model_validator(mode="after")
    def _check(self):
        ids = [c.id for c in self.video] + [o.id for o in self.overlays] + [s.id for s in self.audio.sfx]
        ids += [a.id for a in self.audio.voice + self.audio.music]
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            raise ValueError(f"tekrarlanan id: {sorted(dup)}")
        for item in [*self.video, *self.overlays]:
            if item.start < 0 or item.start + item.dur > self.duration + 0.05:
                raise ValueError(f"{item.id}: [{item.start}, {item.start + item.dur}] süre dışında (0–{self.duration})")
        return self


# ---------------------------------------------------------------- sahne listesi (yönetmen)

class Scene(_M):
    id: str
    chapter: str = "ch01"
    start: float | None = None     # seslendirmeye hizalandıktan sonra dolar
    dur: float | None = None
    vo_from: str | None = None     # bu sahneyi başlatan senaryo cümlesi/segment id'si
    intent: str                    # sahnenin tek işi (izleyici ne anlamalı)
    visual: str                    # ne görünüyor
    blocks: list[dict[str, Any]] = []   # [{block, props, at, dur}]
    transition_in: str = "cut"     # aile adı: cut | match | push | mask | dissolve
    complexity: Literal["block", "custom", "hero"] = "block"
    sfx: list[str] = []
    notes: str = ""


class Scenes(_M):
    version: int = 1
    style: str = "default"
    motion_language: dict[str, str] = {}
    transition_families: list[str] = ["cut", "match", "push"]
    scenes: list[Scene]


# ---------------------------------------------------------------- SFX manifest

class SfxEntry(_M):
    id: str
    file: str
    category: str
    tags: list[str] = []
    duration_s: float
    peak_offset_s: float = 0.0
    lufs: float | None = None
    license: str
    source: str
    source_url: str = ""
    raw: str = ""                 # ham dosya yolu (tekrar indekslemeyi önler)
    attribution: str | None = None
    # WHY: ADR 0040 (brag sfx-analysis fikri). 4 kHz üstü enerji payı × parlak kalma süresi, 0-1. Tekrarlanan seste
    # yüksek değer kulağı yorar (cızırtılı tık, cam gibi çınlama); olaysesi tekrarlı rollerde eşiğin üstünü eler.
    parlak: float | None = None


class SfxManifest(_M):
    version: int = 1
    entries: list[SfxEntry] = []


# ---------------------------------------------------------------- yardımcılar

def load_yaml(path: Path, model: type[BaseModel]):
    return model.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def save_yaml(path: Path, obj: BaseModel) -> None:
    data = obj.model_dump(mode="json", by_alias=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def load_json(path: Path, model: type[BaseModel]):
    return model.model_validate_json(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj: BaseModel | dict | list) -> None:
    data = obj.model_dump(mode="json", by_alias=True, exclude_none=False) if isinstance(obj, BaseModel) else obj
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- kurgu.json (Video Stüdyo)
# WHY: bkz. wiki/decisions/0021-video-studyo-nle.md. Çok izli kurgunun tek doğruluk kaynağı.

class KF(_M):
    t: float = Field(ge=0)  # klibin başından saniye
    v: float
    # geri: hedefi biraz aşıp döner · expo: hızlı çıkış, uzun yavaşlama · yay: yay gibi sönerek oturur (ADR 0033)
    ease: Literal["dogrusal", "yumusak", "giris", "cikis", "tut", "geri", "expo", "yay"] = "dogrusal"


class Sekans(_M):
    w: int = 1080
    h: int = 1920
    fps: int = 30


class KurguKaynak(_M):
    yol: str  # public:speaker.mp4 | inputs:01-1.mp4 | library:sfx/x.wav
    sure: float = 0.0
    w: int | None = None
    h: int | None = None
    ses: bool = True


class Kelime(_M):
    w: str
    s: float
    e: float


class KurguIz(_M):
    id: str
    tur: Literal["video", "ses"]
    ad: str = ""
    kilit: bool = False
    sessiz: bool = False
    gizli: bool = False
    gain_db: float = 0.0


class Nokta(_M):
    x: float = Field(default=0.5, ge=0, le=1)
    y: float = Field(default=0.5, ge=0, le=1)


class Donus(_M):
    x: list[KF] = []
    y: list[KF] = []
    olcek: list[KF] = []
    opaklik: list[KF] = []
    aci: list[KF] = []           # derece, saat yönü
    capa: Nokta | None = None    # ölçek ve dönüşün merkezi, klip kutusunun 0..1 oranı; yoksa orta
    anim: list[Literal["x", "y", "olcek", "opaklik", "aci"]] = []  # kapalıysa tek değer sabittir


class Efekt(_M):
    parlaklik: float = 1.0
    kontrast: float = 1.0
    doygunluk: float = 1.0
    bulanik: float = 0.0
    bulanik_kf: list[KF] = []    # px; doluysa sabit `bulanik` yerine geçer
    parlaklik_kf: list[KF] = []  # çarpan; doluysa sabit `parlaklik` yerine geçer (odak_karart hazır efekti)
    kirp: dict[str, float] | None = None


class Punch(_M):
    """Konuşmacı vurgusu, nesne biçimi: her punch başka ölçek, süre ve odakla (sayı biçimi eskisi gibi +%10)."""
    t: float                                        # kaynak zamanı
    olcek: float = Field(default=1.1, ge=1, le=2)   # hedef çarpan
    sure: float = Field(default=1.0, gt=0)          # tutma süresi, sn
    x: float | None = Field(default=None, ge=0, le=1)  # odak; yoksa bugünkü merkez (dikeyde üst orta)
    y: float | None = Field(default=None, ge=0, le=1)


class KlipSes(_M):
    gain_db: float = 0.0
    fade_in: float = 0.012
    fade_out: float = 0.012
    duck: bool = False
    temizle: bool = False   # render'da konuşma gürültü temizliği (ffmpeg afftdn), yalnız konuşma klibinde
    kf: list[KF] = []       # kazanç keyframe'leri, dB, klip başından; boşsa gain_db sabittir


# WHY: bkz. wiki/decisions/0031-motion-grafik.md. Alanlar açık uçlu sözlükte kalır (eski kurgu.json aynen yüklenir);
# tür adları kurgu.denetle'de sınanır, Kurgu.tsx ile aynı liste.
SAHNE_TURLERI = ("shot", "stat", "text", "chips", "timeline", "steps", "hook", "cta", "fizik", "karakter")  # fizik, karakter: ADR 0039
SAHNE_ZEMINLERI = ("dark", "light", "saydam")
METIN_TIPLERI = ("anahtar", "altbant", "etiket", "cagri", "daktilo", "sayac", "ilerleme", "bolum", "vurgu")
VURGU_BICIMLERI = ("kutu", "daire", "alt_cizgi")


class Gecis(_M):
    # zoom, it, savur, bulanik: ADR 0033; çıkan klibin kuyruğu da hareket eder
    # sil, kay, saat, iris, kirbac, isik, piksel: ADR 0045; orta noktası kesimde, sonraki çekim her karede görünür
    # zoom_kirbac, film_yanigi, bolunme, bozulma, yirtma: aynı sözleşme (gecisler.tsx, tests/test_gecis_olcum.py)
    tur: Literal["capraz", "kararma", "kaydir", "zoom", "it", "savur", "bulanik",
                 "sil", "kay", "saat", "iris", "kirbac", "isik", "piksel",
                 "zoom_kirbac", "film_yanigi", "bolunme", "bozulma", "yirtma"] = "capraz"
    sure: float = Field(default=0.3, gt=0)
    yon: Literal["sol", "sag", "yukari", "asagi"] = "sol"  # it ve savur: görüntünün gittiği yön


class Bilesen(_M):
    ad: str                                   # studio/remotion/motion/kayit.ts anahtarı, ör. "ikon/tik"
    param: dict[str, Any] = {}
    # Yerleşim ipucu; yoksa bileşenin meta.json'undaki tercih sırası. Kesin kutu 0..1 oranıdır.
    yer: Literal["oto", "ust", "orta", "alt", "sol", "sag", "hedef", "tam"] = "oto"
    hedef: dict[str, float] | None = None     # {x, y} 0..1: call-out ve çizim için işaret edilen nokta
    hero: bool | None = None                  # meta varsayılanını ezer
    # Kutunun arkasında yumuşak radyal karartma (Katman.tsx). Bileşen parametresi değildir: param.odakKarart buraya taşınır,
    # çünkü param sema.json ile katı doğrulanır.
    odak_karart: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def _odak_karart_tasi(cls, v):
        if isinstance(v, dict) and isinstance(v.get("param"), dict) and "odakKarart" in v["param"]:
            param = dict(v["param"])
            deger = param.pop("odakKarart")
            v = {**v, "param": param}
            if v.get("odak_karart") is None:
                v["odak_karart"] = bool(deger)
        return v


class Capa(_M):
    kaynak: str                               # kurgu.kaynaklar anahtarı (konuşma klibinin kaynağı)
    kelime: int | None = Field(default=None, ge=0)  # kurgu.kelimeler[kaynak] dizini
    t: float | None = Field(default=None, ge=0)     # kaynak zamanı (sn); kelime yoksa
    once_kare: int = Field(default=3, ge=0, le=12)  # giriş kelimeden bu kadar kare önce


class Klip(_M):
    id: str
    iz: str
    bas: float = Field(ge=0)
    sure: float = Field(gt=0)
    tur: Literal["video", "gorsel", "metin", "sahne", "motion", "ses"]
    kaynak: str | None = None
    giris: float = Field(default=0.0, ge=0)
    hiz: float = Field(default=1.0, gt=0)
    bag: str | None = None
    ses_kapali: bool = False      # ses ayrı klipte (olay.konusma); görüntü sessiz render edilir
    konusmaci: bool = False       # SplitReel Speaker davranışı
    zoom: float = 1.0             # konuşmacı taban zoom
    punches: list[float | Punch] = []  # konuşmacı vurguları, kaynak zamanı
    donus: Donus = Field(default_factory=Donus)
    # WHY: bkz. wiki/decisions/0033-hazir-efektler.md. [{ad, t, sure, ...}] ham kalır; açılım Kurgu.tsx'te (hazirEfekt.ts), denetim hazir_efekt.py
    hazir: list[dict[str, Any]] = []
    efekt: Efekt = Field(default_factory=Efekt)
    ses: KlipSes = Field(default_factory=KlipSes)
    gecis_giris: Gecis | None = None
    gecis_cikis: Gecis | None = None
    sahne: dict[str, Any] | None = None  # SplitReel sahne alanları; kind başına açık uçlu (SAHNE_TURLERI)
    metin: str | None = None
    # boyut, renk, font; motion grafikte tip (METIN_TIPLERI), konum {x,y}, vurgu, arka, hedef, kutu, bicim, deger... (ADR 0031)
    metin_stil: dict[str, Any] | None = None
    olay: dict[str, Any] | None = None   # olaysesi alanları: tur, sure, not, muzik, konusma
    # WHY: bkz. wiki/decisions/0036-motion-kutuphanesi-ve-ajanlar.md. Motion şablonu {ad, param, tema}; webm'i kurgu.motion_bagla üretir
    sablon: dict[str, Any] | None = None
    # WHY: bkz. wiki/decisions/0050-hyperframes-birincil-motor.md. HyperFrames kompozisyonu {ad, param, tema}; ad
    # work/edit/hf/<ad>/ ya da library/motion/hf/<ad>/ klasörüdür, saydam webm'i kurgu.motion_bagla üretir.
    hf: dict[str, Any] | None = None

    @field_validator("hf")
    @classmethod
    def _hf_bicimi(cls, v):
        """{ad: str, param: dict, tema: str|None}; başka alan ya da tip 422 olur, denetimde 500 olmaz (ADR 0050)."""
        if v is None:
            return v
        if set(v) - {"ad", "param", "tema"}:
            raise ValueError(f"hf yalnız ad, param, tema alır: {sorted(set(v) - {'ad', 'param', 'tema'})}")
        if not isinstance(v.get("ad"), str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", v["ad"]):
            raise ValueError("hf.ad harf, rakam, - ve _ olmalı")
        if v.get("param") is not None and not isinstance(v["param"], dict):
            raise ValueError("hf.param bir nesne olmalı")
        if v.get("tema") is not None and not isinstance(v["tema"], str):
            raise ValueError("hf.tema metin olmalı")
        return v
    # WHY: bkz. wiki/decisions/0045-native-motion.md. Native Remotion bileşeni {ad, param}; param bileşenin Zod
    # şemasından üretilen library/motion/native/sema.json ile doğrulanır (kurgu.denetle). Kaynak dosya gerekmez.
    bilesen: Bilesen | None = None
    # Kelimeye çapa: olay kaynak kelimesine bağlıdır; E1 kesimi değişince vedit sekans zamanını yeniden eşler (ADR 0048).
    capa: Capa | None = None


class AltyaziStil(_M):
    font: str = "Montserrat"
    boyut: int = 72
    renk: str = "#FFFFFF"
    aktif_renk: str = "#FF7A00"
    kontur: int = 12
    kontur_renk: str = "#000000"
    kip: Literal["kelime", "tam"] = "kelime"
    en_kelime: int = Field(default=3, ge=1, le=12)
    en_karakter: int = Field(default=18, ge=4, le=80)
    konum: float | None = Field(default=None, ge=0, le=1)  # None: reel düzenini izler
    dosya: str | None = None  # library/fonts içindeki dosya


class Altyazi(_M):
    acik: bool = True
    iz: str = "V1"
    stil: AltyaziStil | None = None  # None: ADR 0014


class Isaret(_M):
    t: float = Field(ge=0)
    ad: str = ""


class Kurgu(_M):
    surum: Literal[1] = 1
    rev: int = 0
    sekans: Sekans = Field(default_factory=Sekans)
    kaynaklar: dict[str, KurguKaynak] = {}
    kelimeler: dict[str, list[Kelime]] = {}
    izler: list[KurguIz]
    klipler: list[Klip] = []
    altyazi: Altyazi = Field(default_factory=Altyazi)
    isaretler: list[Isaret] = []
    motion_tema: str = "varsayilan"  # library/motion/tema/<ad>.css; klipteki sablon.tema bunu ezer (ADR 0036)
    # WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. oto: HyperFrames yapabiliyorsa HyperFrames, değilse Remotion.
    motor: Literal["oto", "hf", "remotion"] = "oto"

    @model_validator(mode="after")
    def _baglar(self):
        izler = {i.id for i in self.izler}
        if len(izler) != len(self.izler):
            raise ValueError("iz id'leri benzersiz olmalı")
        idler = [k.id for k in self.klipler]
        if len(set(idler)) != len(idler):
            raise ValueError("klip id'leri benzersiz olmalı")
        for k in self.klipler:
            if k.iz not in izler:
                raise ValueError(f"{k.id}: iz yok: {k.iz}")
            if k.kaynak and k.kaynak not in self.kaynaklar:
                raise ValueError(f"{k.id}: kaynak yok: {k.kaynak}")
        return self
