"""Swarm edit (ADR 0059): ajan bütçesi, orkestratörün model seçimi, plan doğrulaması ve varsayılan boy.

WHY: bkz. wiki/decisions/0059-swarm-edit.md. Sabit seviye tablosu (ADR 0053) yerine orkestratör ajan sayısını (tavan içinde),
dağılımı ve her ajanın motor/modelini seçer. Kapılı akış (`ekip_v3._akis`) ve deterministik parçalar aynen kullanılır;
bu modül yalnız swarm'a özgü kararları tutar.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from .ekip_sema import EDITOR_EN_COK, KK_EN_COK, SEVIYE, EkipAyar, Plan, Slot
from .motorlar import SEVIYELER

# Motor taraması (motorlar.durum) ~11 sn sürer; plan çağrısı onu beklemesin diye diskte tutulur.
ONBELLEK = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "vedit" / "motor-durum.json"
ONBELLEK_SN = 6 * 3600
OPENCODE_EN_COK = 12  # opencode yüzlerce model listeler; plana yalnız ilk ücretsizler girer

# Varsayılan boy: video süresine göre seviye (sn sınırı). Tavan küçükse bir alt seviyeye iner.
BOY = (("low", 45.0), ("medium", 150.0), ("high", 420.0), ("xhigh", float("inf")))

# Ölçüme dayalı model notu (ADR 0058, arvelior-swarm 53 sn): orkestratör seçimini buna göre yapar.
MODEL_NOTU = [
    "Ölçüm (53 sn video): Claude sonnet editör 80-110 sn; Claude sonnet QC paftayla 45-55 sn; agy (Gemini) QC 250-340 sn.",
    "Kurgu (E1) ve grafik en çok yargı ister: güçlü model. Ses ve stil daha mekaniktir: hızlı model yeter.",
    "Seviye `low` E1'de kazanç getirmedi ve biçim hatası yaptı; editörde `medium` altına inme.",
    "Bilinmeyen ya da listede olmayan modeli yazma; emin değilsen motor/model alanını boş bırak (grup ayarı).",
    "Editörde haiku kullanma: 2026-11-25 swarm koşusunda ses-stil yaması şemaya uymadı (id'siz öğe, yanlış alan adı). "
    "vedit editör kartındaki haiku seçimini grup modeline çevirir.",
]
# Editör yaması sıkı şemadır; bu modeller editör kartında grup ayarına döner (QC'de serbest).
EDITOR_YASAK = ("haiku",)


def orkestrator_ayristir(deger: str | None) -> tuple[str, str | None] | None:
    """`MOTOR[:MODEL]` → (motor, model). Boşsa None."""
    if not deger:
        return None
    motor, _, model = deger.partition(":")
    return motor.strip(), (model.strip() or None)


def _tara() -> dict:
    from . import motorlar
    return motorlar.durum()


def model_listesi(*, tazele: bool = False) -> dict[str, list[str]]:
    """Kurulu motorların model kimlikleri. Disk önbelleği ONBELLEK_SN boyunca geçerlidir; okunamazsa yeniden taranır."""
    if not tazele:
        try:
            d = json.loads(ONBELLEK.read_text(encoding="utf-8"))
            if time.time() - d.get("zaman", 0) < ONBELLEK_SN and d.get("modeller"):
                return d["modeller"]
        except (OSError, ValueError):
            pass
    out: dict[str, list[str]] = {}
    for motor, m in _tara().items():
        if not m.get("kurulu"):
            continue
        ids = [x["id"] if isinstance(x, dict) else str(x) for x in m.get("modeller") or []]
        if motor == "opencode":
            ids = [i for i in ids if i.endswith("-free")][:OPENCODE_EN_COK] or ids[:OPENCODE_EN_COK]
        if ids:
            out[motor] = ids
    try:
        ONBELLEK.parent.mkdir(parents=True, exist_ok=True)
        ONBELLEK.write_text(json.dumps({"zaman": time.time(), "modeller": out}, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return out


def varsayilan_boy(son: float, tavan: int) -> str:
    """Video süresine göre seviye; editör + QC toplamı tavanı aşarsa bir alt seviye (en az low)."""
    sira = [s for s, _ in BOY]
    i = next(i for i, (_, sinir) in enumerate(BOY) if son < sinir)
    while i > 0 and sum(SEVIYE[sira[i]]) > tavan:
        i -= 1
    return sira[i]


def plan_dogrula(plan: Plan, tavan: int, son: float, modeller: dict[str, list[str]] | None = None) -> list[str]:
    """Swarm planı: E1 yalnız kurgu (plana paralel çalışıyor), slotlar ardışık, bütçe içinde, katman × zaman tam kapsam,
    QC alanları kapsanır, motor kurulu ve model listede."""
    from . import ekip_v3
    h: list[str] = []
    e = sorted(g.slot for g in plan.gorevler)
    k = sorted(g.slot for g in plan.kk_gorevler)
    ne, nk = len(e), len(k)
    if e != sorted(f"E{i}" for i in range(1, ne + 1)) or not 1 <= ne <= EDITOR_EN_COK:
        h.append(f"editör slotları E1'den ardışık, 1-{EDITOR_EN_COK} olmalı")
    if k != sorted(f"K{i}" for i in range(1, nk + 1)) or not 1 <= nk <= KK_EN_COK:
        h.append(f"kalite kontrol slotları K1'den ardışık, 1-{KK_EN_COK} olmalı")
    if ne + nk > tavan:
        h.append(f"ajan sayısı {ne + nk}, tavan {tavan}")
    e1 = next((g for g in plan.gorevler if g.slot == "E1"), None)
    if e1 is None or e1.katmanlar != ["kurgu"] or e1.aralik is not None:
        h.append("E1 yalnız kurgu katmanı, aralık null olmalı (plana paralel çalışıyor)")
    h += ekip_v3.kapsam_hatalari(plan, son)
    if modeller is not None:
        for g in [*plan.gorevler, *plan.kk_gorevler]:
            if g.motor and g.motor not in modeller:
                h.append(f"{g.slot}: motor kurulu değil: {g.motor}")
            elif g.model:
                mm = g.motor or next((m for m, v in modeller.items() if g.model in v), None)
                if mm is None or g.model not in modeller.get(mm, []):
                    h.append(f"{g.slot}: listede olmayan model: {g.model}")
            if g.seviye and g.motor and g.seviye not in SEVIYELER.get(g.motor, ()):
                h.append(f"{g.slot}: {g.motor} için seviye {', '.join(SEVIYELER.get(g.motor, ())) or 'yok'} olmalı: {g.seviye}")
    return h


def ezme(plan: Plan, ayar: EkipAyar, modeller: dict[str, list[str]] | None = None) -> dict[str, Slot]:
    """Planın kart motor/model seçimi → slot ezmesi. Motor yoksa modelin bulunduğu motor; yedek grup ayarından.
    Kullanıcının açık slot ezmesi kazanır."""
    from .ekip_sema import grup
    out: dict[str, Slot] = {}
    for g in [*plan.gorevler, *plan.kk_gorevler]:
        # E1 plana paralel, grup motoruyla çoktan çalışıyor: kartındaki seçim sonraki kapılarda motoru değiştirmesin.
        if g.slot == "E1" or g.slot in ayar.ezme or not (g.motor or g.model or g.seviye):
            continue
        if g.slot.startswith("E") and g.model and any(x in g.model.lower() for x in EDITOR_YASAK):
            continue  # WHY: bkz. wiki/decisions/0059-swarm-edit.md (haiku editör yaması şemaya uymadı)
        taban = ayar.gruplar[grup(g.slot)]
        motor = g.motor or next((m for m, v in (modeller or {}).items() if g.model in v), None) or taban.motor
        model = g.model if (g.model and (modeller is None or g.model in modeller.get(motor, []))) else (taban.model if motor == taban.motor else None)
        seviye = g.seviye if g.seviye in SEVIYELER.get(motor, ()) else (taban.seviye if motor == taban.motor else None)
        yedek = {}
        if motor == taban.yedek_motor:  # yedek birincille aynı olmasın: grubun birincili yedek olur
            yedek = {"yedek_motor": taban.motor, "yedek_model": taban.model, "yedek_seviye": taban.seviye}
        out[g.slot] = taban.model_copy(update={"motor": motor, "model": model, "seviye": seviye, **yedek})
    return out


def plan_bolumu(ayar: EkipAyar, modeller: dict[str, list[str]], e1: Slot) -> list[str]:
    """Plan paketinin swarm bölümü: bütçe, paralel E1, seçilebilir modeller."""
    t = ayar.tavan()
    return [
        "## Ajan bütçesi",
        f"En çok {t} ajan (editör + kalite kontrol): editör en çok {EDITOR_EN_COK}, kalite kontrol en çok {KK_EN_COK}. "
        "Sayıyı işin büyüklüğüne göre sen seç; az ajan da yeterliyse fazlasını açma.",
        f"E1 (kurgu, aralık null) şu an çalışıyor: motor `{e1.motor}`, model `{e1.model or 'varsayılan'}`. Planında E1'i aynen yaz, "
        "katmanını ve motorunu değiştirme. Hook'u E1 seçer.",
        "## Seçilebilir motor ve modeller (kartta `motor`, `model`, `seviye`; boşsa grup ayarı)",
        *[f"- `{m}`: {', '.join(v)}" for m, v in modeller.items()],
        f"- Grup ayarı: editör `{ayar.gruplar['editor'].motor}` {ayar.gruplar['editor'].model or ''}, "
        f"kalite kontrol `{ayar.gruplar['kk'].motor}` {ayar.gruplar['kk'].model or ''}",
        *[f"- {x}" for x in MODEL_NOTU],
    ]
