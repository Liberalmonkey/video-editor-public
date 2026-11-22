"""Olay tabanlı kurgu sesi: zoom, kesme, geçiş ve ekran olaylarını kare doğruluğunda sese çevirir.

# WHY: bkz. wiki/decisions/0013-uretim-akisi-ve-olay-sesi.md — OpenMontage/Remotion kurgusunda SFX katmanı
# yoktu, kütüphane yalnız eski vedit hattına bağlıydı. Girdi motordan bağımsız olaylar.json, çıktı sesli mp4.

Rol olayı sözleşmesi (kurgu.json, değişmez; hazır efektler de bu biçimi üretir):
    {"tur": "ses", "iz": "A2", "bas": <olay anı sn>, "sure": <timeline'da işaret boyu, ör. 0.3>,
     "olay": {"tur": <ROLLER ya da KOMBOLAR anahtarı>, "guc": "yumusak|orta|sert", "sure": <hareket süresi sn, ops.>, "not": "<kısa neden>"}}
    # "kaynak" YOK
- Klibin `bas`ı görünen olayın anıdır (kesme karesi, grafiğin girişi, zoom başlangıcı); sesin başladığı an değil. Dosyayı,
  tepe çapasını (sesin en güçlü anı olaya oturur), süre uydurmayı, yönü ve ±%3 perdeyi `planla` seçer.
- `olay.sure` hareketli rollerde (zoom, geçiş, yükseliş) hareketin süresidir; yoksa 0. Klibin `sure`ı yalnız görsel işarettir.
- `olay.guc` yoksa rolün varsayılanı; klibin `ses.gain_db` 0 değilse seviye tablosuna eklenir (dB farkı).
"""

from __future__ import annotations

import json
import zlib
from pathlib import Path


from .tembel import Tembel

# WHY: Stüdyo açılışında yüklenmesin (ADR 0050)
np = Tembel("numpy")
sf = Tembel("soundfile")

from . import audio, ff, paths
from .sfx import load_manifest

SR = audio.SR
GUC_DB = {"soft": -9.0, "medium": -5.0, "hard": -1.5}
GUC_SIRA = {"soft": 0, "medium": 1, "hard": 2}
# Sözleşme Türkçe güç adı yazar; içte İngilizce ad kalır, eski olaylar.json dosyaları da çalışır.
GUC_ADI = {"yumusak": "soft", "orta": "medium", "sert": "hard"}
# WHY: bkz. wiki/decisions/0032-ses-katmani.md. Vuruştan önce müzik çekilir ("pre-hit dip"), vuruşta açılır: (önce sn, dB).
DIP = {"medium": (0.15, -3.0), "hard": (0.25, -6.0)}
FADE_IN, FADE_OUT = 0.01, 0.04  # kesik baş ve kuyruk tıklamasın

# son: tepe hareketin varışına oturur · orta: tepe geçişin ortasındaki kesme karesine · bas: tepe olay anına.
# yon: yukselen ses izleyiciye yaklaşır (zoom in), dusen uzaklaşır (zoom out); örnek ters yöndeyse çevrilir.
ROLLER = {
    "zoom_in": {"kat": ["whoosh", "riser-short", "swoosh"], "etiket": ["zoom", "in"], "db": -6, "capa": "son", "yon": "yukselen", "uydur": True},
    "zoom_out": {"kat": ["whoosh", "swoosh"], "etiket": ["zoom", "out"], "db": -9, "capa": "bas", "yon": "dusen", "uydur": True},
    "punch_in": {"kat": ["impact"], "etiket": ["light"], "db": -12, "capa": "bas", "sessiz": True},
    "kesme": {"kat": ["tick", "click"], "db": -14, "capa": "bas", "sessiz": True},
    "gecis": {"kat": ["whoosh", "swoosh"], "etiket": ["transition"], "db": -3, "capa": "orta", "uydur": True, "guc": "medium"},
    "hizli_gecis": {"kat": ["whip", "whoosh"], "db": -3, "capa": "orta", "uydur": True, "guc": "medium"},
    "slayt": {"kat": ["swoosh", "page_turn"], "db": -6, "capa": "orta", "uydur": True},
    "bolum": {"kat": ["whoosh"], "db": 0, "capa": "orta", "uydur": True, "guc": "medium"},
    "riser": {"kat": ["riser", "riser-short"], "db": -3, "capa": "bas"},
    "vurgu": {"kat": ["impact"], "db": -3, "capa": "bas", "guc": "medium"},
    "tik": {"kat": ["click"], "db": -3, "capa": "bas", "kit": "mouse_click"},
    "klavye": {"kat": ["typing"], "db": -3, "capa": "ilk", "kit": "keyboard", "doldur": True},
    "pop": {"kat": ["pop"], "db": -3, "capa": "bas"},
    "bildirim": {"kat": ["notification", "ding"], "db": -3, "capa": "bas"},
    "basari": {"kat": ["success", "ding"], "db": -3, "capa": "bas"},
    "hata": {"kat": ["error"], "db": -3, "capa": "bas"},
    "para": {"kat": ["cash"], "db": -3, "capa": "bas"},
    "sayac": {"kat": ["tick"], "db": -6, "capa": "bas"},
    "deklansor": {"kat": ["camera_shutter"], "db": -3, "capa": "bas"},
    "sayfa": {"kat": ["page_turn"], "db": -3, "capa": "orta", "uydur": True},
}

# Katmanlı olay: bir olay birden çok rol katmanına açılır; yoğunluk süzgecinde tek olay sayılır.
# Katmanda `rol` dışındaki alanlar: db (rolün seviyesine eklenir), kayma (sn, tepeye eklenir), en_uzun (sn, katman bu
# boydan uzunsa tepesi korunarak kırpılır), hedef (sn, aday süresi), capa/etiket/yon (rolünkini ezer).
# WHY: alt katman kısa ve üstü boğmayacak kadar alçak (wiki/sources/2026-11-12-ses-efekti-kaynaklari.md, Profesyonel pratik).
KOMBOLAR = {
    # whoosh kesme karesine biraz erken iner, kesme karesinde kısa ve alçak sub darbe gövde verir
    "gecis_guclu": {"capa": "orta", "guc": "medium", "katman": [
        {"rol": "gecis", "kayma": -0.03},
        {"rol": "vurgu", "capa": "orta", "etiket": ["sub"], "db": -8, "hedef": 0.6, "en_uzun": 0.5}]},
    # kısa ters whoosh ya da riser tepesi olay anında, darbe aynı anda
    "vurgu_guclu": {"capa": "bas", "guc": "medium", "katman": [
        {"rol": "vurgu"},
        {"rol": "riser", "etiket": ["reverse"], "yon": "yukselen", "db": -6, "hedef": 0.7, "en_uzun": 0.9}]},
    # açılış ya da büyük reveal: riser 1-2 sn önceden kurar, kısa sub darbe iner
    "acilis": {"capa": "bas", "guc": "medium", "katman": [
        {"rol": "riser", "yon": "yukselen", "hedef": 1.5, "en_uzun": 2.0},
        {"rol": "vurgu", "etiket": ["sub"], "db": -6, "hedef": 0.6, "en_uzun": 0.8}]},
}


def guc_adi(g: str | None) -> str | None:
    return GUC_ADI.get(g, g)


def olay_ani(o: dict, fps: float) -> float:
    return float(o["kare"]) / fps if "kare" in o else float(o["t"])


def tepe_ani(o: dict, rol: dict, fps: float) -> float:
    """Sesin en güçlü noktasının videoda oturacağı an."""
    t, d = olay_ani(o, fps), float(o.get("sure") or 0)
    if o.get("kesin"):  # zaman sesin başlangıcıdır, çapa uygulanmaz
        return t
    return {"son": t + d * 0.9, "orta": t + d / 2}.get(rol["capa"], t)


TEKRARLI_KAT = {"click", "tick", "typing", "keypress", "tap", "switch"}
PARLAK_ESIK = 0.25  # sfx.PARLAK_ESIK ile aynı; olaysesi sfx'i (requests) içe almasın diye burada


def _aday(entries: list, rol: dict, guc: str, hedef: float, sira: str, son: str | None):
    """Kategoriye göre aday; etiket eşleşeni öne al, süresi hareketin süresine yakın olanı seç, tekrar etme."""
    for kat in rol["kat"]:
        c = [e for e in entries if e.category == kat]
        # library/checks.md: synth-* "pırt" gibi duyuluyor; gerçek kayıt varsa o seçilir
        c = [e for e in c if "-synth-" not in e.id] or c
        if kat in TEKRARLI_KAT:
            # WHY: ADR 0040. Tık ve klavye sesi videoda onlarca kez çalar; parlak (cızırtılı) olanı yorar.
            c = [e for e in c if (e.parlak or 0) <= PARLAK_ESIK] or c
        if guc == "soft":
            c = [e for e in c if "heavy" not in e.tags] or c
        elif guc == "hard":
            c = [e for e in c if "light" not in e.tags] or c
        tercih = [e for e in c if set(rol.get("etiket", [])) <= set(e.tags)] if rol.get("etiket") else []
        c = tercih or c
        if c:
            c = sorted(c, key=lambda e: (abs(e.duration_s - hedef), e.id))[:4] if hedef else sorted(c, key=lambda e: e.id)
            pick = c[zlib.crc32(sira.encode()) % len(c)]
            if pick.id == son and len(c) > 1:
                pick = c[(c.index(pick) + 1) % len(c)]
            return pick
    return None


def planla(spec: dict, entries: list, kit: dict, *, min_aralik: float = 0.4) -> dict:
    """Olayları sese eşle. Saf işlev: dosya okumaz, miks yapmaz (test edilebilir)."""
    fps = float(spec.get("fps") or 30)
    always = {**(kit.get("always", {}).get("*") or {}), **(kit.get("always", {}).get(spec.get("studyo") or "") or {})}
    by_id = {e.id: e for e in entries}
    bilinmeyen = sorted({o.get("tur") for o in spec.get("olaylar", []) if o.get("tur") not in ROLLER and o.get("tur") not in KOMBOLAR and not o.get("dosya")}, key=str)
    if bilinmeyen:
        raise SystemExit(f"Bilinmeyen olay türü: {bilinmeyen}. Türler: {', '.join(ROLLER)}. Kombolar: {', '.join(KOMBOLAR)}")
    adaylar, sessiz = [], []
    for i, o in enumerate(spec.get("olaylar", [])):
        rol = ROLLER.get(o.get("tur")) or KOMBOLAR.get(o.get("tur")) or {"capa": "bas", "db": -3, "kat": []}
        guc = guc_adi(o.get("guc")) or rol.get("guc", "soft")
        # WHY: görünmez kesme ve punch-in ses istemez; yalnız açıkça vurgulananlar duyulur (usta-editor §Ses).
        if o.get("sessiz") or (rol.get("sessiz") and guc == "soft"):
            sessiz.append({"t": round(olay_ani(o, fps), 3), "tur": o.get("tur"), "neden": "kural: görünmez olay sessiz kalır"})
            continue
        adaylar.append((i, o, rol, guc))
    kabul, dusen = [], []
    for i, o, rol, guc in sorted(adaylar, key=lambda x: (-GUC_SIRA.get(x[3], 0), olay_ani(x[1], fps))):
        tepe = tepe_ani(o, rol, fps)
        # WHY: bkz. wiki/decisions/0021-video-studyo-nle.md. Kullanıcı timeline'a koyduysa ses düşürülmez, kendi yerinde çalar.
        if not o.get("kesin") and any(abs(tepe - k["tepe"]) < min_aralik for k in kabul):
            dusen.append({"t": round(tepe, 3), "tur": o.get("tur"), "neden": f"{min_aralik} sn içinde daha güçlü ses var"})
            continue
        kabul.append({"i": i, "o": o, "rol": rol, "guc": guc, "tepe": tepe})
    kabul.sort(key=lambda k: k["tepe"])
    son: dict = {}
    yerler, eksik = [], []
    tekrar: dict = {}
    for k in kabul:
        o, guc = k["o"], k["guc"]
        tur = o.get("tur")
        sure = float(o.get("sure") or 0)
        if o.get("dosya") or tur not in KOMBOLAR:
            katmanlar = [(tur, k["rol"], 0.0, 0.0, 0.0)]  # (rol adı, rol, ek dB, tepe kayması, en uzun)
        else:
            katmanlar = [(c["rol"], {**ROLLER[c["rol"]], **{a: c[a] for a in ("capa", "etiket", "yon") if a in c}, "_hedef": c.get("hedef", 0)},
                          float(c.get("db", 0)), float(c.get("kayma", 0)), float(c.get("en_uzun", 0))) for c in KOMBOLAR[tur]["katman"]]
        yer_sayisi = len(yerler)
        for j, (ad, rol, ek_db, kayma, en_uzun) in enumerate(katmanlar):
            kombo = len(katmanlar) > 1
            tepe = tepe_ani(o, rol, fps) + kayma if kombo else k["tepe"]
            if o.get("dosya"):
                dosya = o["dosya"]
            else:
                kit_id = None if kombo else always.get(rol.get("kit", ad))
                sec = by_id.get(kit_id) if kit_id else None
                hedef = rol.get("_hedef") or (sure * 1.3 if rol.get("uydur") else 0)
                sec = sec or _aday(entries, rol, guc, hedef, f"{tur}:{k['i']}" + (f":{j}" if kombo else ""), son.get(ad))
                if not sec:
                    eksik.append({"t": round(tepe, 3), "tur": tur, "neden": f"kütüphanede yok: {rol['kat']}"})
                    continue
                son[ad] = sec.id  # aynı rolde art arda aynı dosya yok; kombo katmanı da rolün sırasına girer
                dosya = sec.file
            if o.get("dosya") and o.get("gain_db") is not None:
                gain = o["gain_db"]
            else:
                # Sözleşme: dosyasız olayda gain_db tablo seviyesine eklenen farktır. ±1 dB oynatma olay kimliğinden tohumlu.
                oyna = (zlib.crc32(f"{tur}:{k['i']}:{j}:db".encode()) % 21 - 10) / 10
                gain = round(GUC_DB.get(guc, -9.0) + rol.get("db", 0) + ek_db + float(o.get("gain_db") or 0) + oyna, 2)
            yerler.append({"tur": tur, "tepe": round(tepe, 3), "sure": sure, "guc": guc, "gain_db": gain,
                           "dosya": dosya, "sira": k["i"], "yon": rol.get("yon"), "uydur": bool(rol.get("uydur")),
                           "doldur": bool(rol.get("doldur")), "capa": rol["capa"], "not": o.get("not", ""),
                           **({"katman": j, "rol": ad} if kombo else {}), **({"en_uzun": en_uzun} if en_uzun else {}),
                           **({"kesin": True, "in": float(o.get("in", 0)), "dur": o.get("dur"), "fade_in": float(o.get("fade_in", 0)), "fade_out": float(o.get("fade_out", 0)), "zarf": o.get("zarf")} if o.get("kesin") else {})})
        if len(yerler) > yer_sayisi:
            tekrar[tur] = tekrar.get(tur, 0) + 1  # olay sayılır, katman değil
    return {"yerler": yerler, "dusen": dusen, "sessiz": sessiz, "eksik": eksik, "adet": tekrar}


def uydur_aralik(tepe: int, n: int, sure: float) -> tuple[int, int]:
    """`uydur` rolünde sesin kalan parçası [a, b): hareket süresine göre, tepesi korunur."""
    hedef = int(max(sure, 0.2) * 1.5 * SR)
    if n <= hedef:
        return 0, n
    if tepe / n >= 0.5:  # yükselen: sonu koru
        a = max(0, tepe + int(0.15 * SR) - hedef)
        return a, a + hedef
    return 0, hedef


def _sekillendir(data: np.ndarray, y: dict) -> tuple[np.ndarray, int]:
    """Yön, süre ve küçük perde değişimi uygula; (ses, tepe örneği) döndür."""
    tepe = int(np.argmax(np.abs(data).mean(axis=1)))
    oran = tepe / max(len(data) - 1, 1)
    if (y["yon"] == "yukselen" and oran < 0.5) or (y["yon"] == "dusen" and oran > 0.5):
        data, tepe = data[::-1].copy(), len(data) - 1 - tepe
    a, b = uydur_aralik(tepe, len(data), y["sure"]) if y["uydur"] else (0, len(data))
    if y.get("en_uzun"):  # kombo alt katmanı kısa kalır; tepe korunur
        a2, b2 = uydur_aralik(tepe - a, b - a, y["en_uzun"] / 1.5)
        a, b = a + a2, a + b2
    if (a, b) != (0, len(data)):
        data, tepe = data[a:b].copy(), tepe - a
        k = min(int(0.03 * SR), len(data))
        data[:k] *= np.linspace(0, 1, k, dtype=np.float32)[:, None]
        data[len(data) - k:] *= np.linspace(1, 0, k, dtype=np.float32)[:, None]
    # WHY: aynı örnek birebir tekrar edince kulak yakalar ("makineli tüfek"); ±%3 perde bunu örter.
    r = 0.97 + (zlib.crc32(f"{y['tur']}{y['sira']}{y.get('katman', '')}".encode()) % 7) * 0.01
    if r != 1.0 and len(data) > 8:
        x = np.arange(0, len(data) - 1, r)
        data = np.stack([np.interp(x, np.arange(len(data)), data[:, c]) for c in range(2)], axis=1).astype(np.float32)
        tepe = int(tepe / r)
    return data, tepe


def dip_egrisi(n: int, i: int, guc: str) -> tuple[int, np.ndarray]:
    """Müzik kazanç eğrisi (başlangıç örneği, eğri): vuruştan `once` sn önce 40 ms'de iner, vuruşta 50 ms'de açılır."""
    once, db = DIP[guc]
    a, b = max(0, i - int((once + 0.04) * SR)), min(n, i + int(0.05 * SR))
    x = np.arange(a, b) - i
    return a, np.interp(x, [-(once + 0.04) * SR, -once * SR, 0, 0.05 * SR], [1, audio._db(db), audio._db(db), 1]).astype(np.float32)


def _bul(src: str, taban: Path) -> Path:
    p = Path(src)
    # olaylar.json genelde <proje>/edit/ altındadır; yollar proje köküne de göreli olabilir
    for aday in ([p] if p.is_absolute() else [taban / p, taban.parent / p, paths.ROOT / p]):
        if aday.exists():
            return aday
    raise SystemExit(f"Dosya yok: {src}")


def _kesme_denetimi(ses: np.ndarray, spec: dict, fps: float) -> list[str]:
    """Kesme anında örnek sıçraması (tık sesi) ara."""
    uyari = []
    mono = ses.mean(axis=1)
    for o in spec.get("olaylar", []):
        if o.get("tur") not in ("kesme", "punch_in"):
            continue
        i = int(olay_ani(o, fps) * SR)
        ort = mono[max(0, i - int(0.1 * SR)): i + int(0.1 * SR)]
        if len(ort) < 100:
            continue
        fark = np.abs(np.diff(ort))
        if fark.max() > 0.05 and fark.max() > 25 * (np.median(fark) + 1e-5):
            uyari.append(f"{olay_ani(o, fps):.2f} sn: kesmede tık riski; kesimi sıfır geçişe al ya da 10–20 ms çapraz geçiş ver")
    return uyari


def calistir(spec_yol: Path, cikti: Path | None = None, *, duck_db: float = -11.0, min_aralik: float = 0.4) -> dict:
    spec = json.loads(Path(spec_yol).read_text(encoding="utf-8"))
    taban = Path(spec_yol).resolve().parent
    fps = float(spec.get("fps") or 30)
    video = _bul(spec["video"], taban)
    info = ff.probe(video)
    total = int(np.ceil(float(spec.get("sure") or info["duration"]) * SR))
    kit_yol = paths.ROOT / "library" / "kit.json"
    kit = json.loads(kit_yol.read_text(encoding="utf-8")) if kit_yol.exists() else {}
    plan = planla(spec, load_manifest().entries, kit, min_aralik=min_aralik)

    cache = taban / ".ses-onbellek"
    voice = np.zeros((total, 2), dtype=np.float32)
    sesler = spec.get("ses") or ([{"src": str(video)}] if info.get("audio") else [])
    for v in sesler:
        data = audio._decode(_bul(v["src"], taban), cache)[int(float(v.get("in", 0)) * SR):]
        if v.get("dur"):  # ayrık ses klibi: timeline kırpımı
            data = data[:int(float(v["dur"]) * SR)]
        audio._place(voice, audio.zarf(data, v.get("zarf")), float(v.get("start", 0)), audio._db(float(v.get("gain_db", 0))), float(v.get("fade_in", 0)), float(v.get("fade_out", 0)))
    if spec.get("temizle"):
        voice = audio.temizle(voice, spec["temizle"])
    env = audio.voice_envelope(voice) if voice.any() else np.zeros(total, dtype=np.float32)
    env = np.pad(env, (0, max(0, total - len(env))))[:total]

    music = np.zeros((total, 2), dtype=np.float32)
    for m in spec.get("muzik", []):
        data = audio._decode(_bul(m["src"], taban), cache)[int(float(m.get("in", 0)) * SR):]
        bas = float(m.get("start", 0))
        uzun = int((float(m.get("dur") or (total / SR - bas))) * SR)
        if 0 < len(data) < uzun:
            data = np.tile(data, (int(np.ceil(uzun / len(data))), 1))
        seg = np.zeros((total, 2), dtype=np.float32)
        audio._place(seg, audio.zarf(data[:uzun], m.get("zarf")), bas, audio._db(float(m.get("gain_db", -14))), float(m.get("fade_in", 1.0)), float(m.get("fade_out", 2.0)))
        if m.get("duck", True):
            seg *= (1 - env * (1 - audio._db(duck_db)))[:, None]
        music += seg

    sfx = np.zeros((total, 2), dtype=np.float32)
    for y in plan["yerler"]:
        data = audio._decode(_bul(y["dosya"], taban), cache)
        i = min(int(y["tepe"] * SR), total - 1)
        if y.get("kesin"):
            # Yer, kırpma ve fade timeline'daki gibi; perde oynatılmaz. Konuşma öncelik kuralı aşağıda aynen geçerli.
            a = int(y["in"] * SR)
            parca = audio.zarf(data[a:a + int(float(y["dur"]) * SR)] if y.get("dur") else data[a:], y.get("zarf"))
            gain = y["gain_db"] - (4 if env[i] > 0.5 else 0)
            audio._place(sfx, parca, y["tepe"], audio._db(gain), y["fade_in"] or FADE_IN, y["fade_out"] or FADE_OUT)
            y.update(gain_db=round(gain, 1), konusma_ustu=bool(env[i] > 0.5), baslangic=round(y["tepe"], 3))
            continue
        if y["doldur"] and y["sure"]:
            uzun = int(y["sure"] * SR)
            if len(data) < uzun:
                data = np.tile(data, (int(np.ceil(uzun / len(data))), 1))
            data = data[:uzun]
        data, tepe = _sekillendir(data, y)
        # WHY: konuşma üstünde efekt 4 dB geri çekilir; konuşma her zaman önde (wiki/concepts/loudness-standartlari).
        konusma = env[i] > 0.5
        gain = y["gain_db"] - (4 if konusma else 0)
        bas = y["tepe"] if y["capa"] == "ilk" else y["tepe"] - tepe / SR
        audio._place(sfx, data, bas, audio._db(gain), FADE_IN, FADE_OUT)
        y.update(gain_db=round(gain, 1), konusma_ustu=bool(konusma), baslangic=round(bas, 3))
        if y["guc"] in DIP and not y.get("katman") and music.any():
            # orta/sert vuruştan önce müzik iner, vuruşta 50 ms'de geri açılır; kombo bir kez çeker
            a, egri = dip_egrisi(total, i, y["guc"])
            music[a:a + len(egri)] *= egri[:, None]

    uyarilar = _kesme_denetimi(voice, spec, fps)
    dakika = max(total / SR / 60, 1 / 6)
    for tur, n in plan["adet"].items():
        if tur in ("zoom_in", "zoom_out", "gecis") and n / dakika > 6:
            uyarilar.append(f"{tur}: dakikada {n / dakika:.1f} ses; kulak yorar, güçsüz olanları sessiz yap")
    uyarilar += [f"{e['t']:.2f} sn {e['tur']}: {e['neden']}" for e in plan["eksik"]]

    stem = Path(spec_yol).stem
    ham, master = taban / f"{stem}.ham.wav", taban / f"{stem}.master.wav"
    sf.write(ham, np.clip(voice + music + sfx, -4, 4), SR, subtype="FLOAT")
    audio.loudnorm_2pass(ham, master, I=-14, TP=-1, LRA=11)
    ham.unlink(missing_ok=True)
    cikti = Path(cikti) if cikti else video.with_name(f"{video.stem}.sesli.mp4")
    ff.ffmpeg("-i", str(video), "-i", str(master), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
              "-shortest", "-movflags", "+faststart", str(cikti))
    rapor = {"cikti": str(cikti), "yerlesen": len(plan["yerler"]), "adet": plan["adet"], "uyarilar": uyarilar,
             "loudness": ff.loudness(master), "yerler": plan["yerler"], "dusen": plan["dusen"], "sessiz": plan["sessiz"]}
    (taban / f"{stem}.rapor.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    return rapor
