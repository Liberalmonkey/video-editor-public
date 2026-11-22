"""Ekip motorunun ortak yardımcıları: ayar yükleme, canlı durum, tek ajan çağrısı, zaman bölüşü, QC girdisi, bulgu doğrulama.

WHY: bkz. wiki/decisions/0053-seviyeli-ekip-orkestrator.md. Akış `ekip_v3.py`'dedir; eski turlu motor (ADR 0044) kaldırıldı.
Ayar sırası: library/ekip.json varsayılan ön ayarı < work/edit/ekip.json < --ekip-dosyasi < CLI bayrakları.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path
from types import SimpleNamespace

from pydantic import ValidationError

from . import ff, hizli, kurgu, kurgu_kalite, motorlar, paths, stil, tema_token
from .ekip_sema import EkipAyar, KontrolCikti, Slot
from .schemas import Kurgu

AJAN_SURE = 1800  # sn; tek ajanın üst sınırı
GLOBAL = paths.LIBRARY / "ekip.json"
ROL_KLASORU = paths.ROOT / ".claude" / "agents"


# ---------------------------------------------------------------- ayar

def ayar_yukle(p, dosya: Path | None = None, **ezme) -> EkipAyar:
    """Sıra: library/ekip.json varsayılan ön ayarı < work/edit/ekip.json < --ekip-dosyasi < CLI bayrakları."""
    d: dict = {}
    if GLOBAL.is_file():
        g = json.loads(GLOBAL.read_text(encoding="utf-8"))
        d = dict((g.get("onayarlar") or {}).get(g.get("varsayilan") or "", {}))
    for f in (p.work / "edit" / "ekip.json", dosya):
        if f and Path(f).is_file():
            d.update(json.loads(Path(f).read_text(encoding="utf-8")))
    d.update({k: v for k, v in ezme.items() if v is not None})
    return EkipAyar.model_validate(d)


# ---------------------------------------------------------------- durum (Stüdyo canlı okur)

class Durum:
    """`work/edit/ekip/durum.json`: seviye, kapılar, slot başına durum. Stüdyo canlı okur (ADR 0053)."""

    def __init__(self, kok: Path, ayar: EkipAyar, kapilar: list[tuple[str, str]] | None = None):
        self.kok, self.kilit = kok, threading.Lock()
        self.d = {"seviye": ayar.ekip_seviye, "asama": "hazirlik", "bitti": False, "hata": None,
                  "acik": {"P0": 0, "P1": 0, "P2": 0}, "kapanan": 0, "baslangic": time.time(), "dagitim": None,
                  "kurallar": {"atanan": 0, "uyum_eksik": 0, "yeni": 0, "tekrar": 0, "dogrulanan": 0, "dogrulanamayan": 0},
                  "kapilar": [{"id": i, "ad": ad, "durum": "bekliyor", "not": ""} for i, ad in (kapilar or [])],
                  "slotlar": {s: {"durum": "bekliyor", "rol": "", "aralik": None, "motor": ayar.slot(s).motor, "model": ayar.slot(s).model,
                                  "seviye": ayar.slot(s).seviye, "sure": None, "token": None, "cikti": None} for s in ayar.slotlar()}}
        self.yaz()

    def ayarla(self, **kv):
        with self.kilit:
            self.d.update(kv)
            self.yaz()

    def slot(self, s: str, **kv):
        with self.kilit:
            self.d["slotlar"].setdefault(s, {"durum": "bekliyor"}).update(kv)
            self.yaz()

    def kapi(self, kid: str, durum: str, not_: str = ""):
        """Kapı durumu: bekliyor | acik | gecti | kaldi. Açılan kapı aşama adını da verir."""
        with self.kilit:
            for k in self.d["kapilar"]:
                if k["id"] == kid:
                    k["durum"] = durum
                    if not_:
                        k["not"] = not_[:300]
                    if durum == "acik":
                        self.d["asama"] = k["ad"]
            self.yaz()

    def yaz(self):
        self.kok.mkdir(parents=True, exist_ok=True)
        kurgu._atomik(self.kok / "durum.json", json.dumps(self.d, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- ajan çağrısı

def _metin_ve_kullanim(satirlar: list[str]) -> tuple[str, dict]:
    """Ham akıştan son yanıt metni ve token kullanımı (motorların ortak alanlarından)."""
    son, kul = "", {}
    for s in satirlar:
        try:
            o = json.loads(s)
        except ValueError:
            continue
        if not isinstance(o, dict):
            continue
        for anahtar in ("result", "response"):
            if isinstance(o.get(anahtar), str) and o[anahtar].strip():
                son = o[anahtar]
        u = o.get("usage") or (o.get("part") or {}).get("tokens") or {}
        if isinstance(u, dict):
            for k, v in u.items():
                if isinstance(v, (int, float)) and "token" in k:
                    kul[k] = kul.get(k, 0) + v
    return son, kul


def ajan(slot: Slot, istem: str, mod: str, kayit: Path, *, yedek: bool = False) -> tuple[bool, str, dict]:
    """Tek çağrı. Ham akış `<kayit>.cikti.jsonl`, okunur günlük `<kayit>.cikti.txt`. (başarılı, yanıt metni, meta)."""
    motor = slot.yedek_motor if yedek else slot.motor
    model = slot.yedek_model if yedek else slot.model
    seviye = slot.yedek_seviye if yedek else slot.seviye
    meta = {"motor": motor, "model": model, "seviye": seviye, "mod": mod, "yedek": yedek, "baslangic": time.time()}
    try:
        komut = motorlar.komut(motor, istem, model, mod, None, seviye)  # bypass bayrağı yok (motorlar kuralı)
    except SystemExit as e:
        meta.update(hata=str(e), sure=0)
        return False, "", meta
    is_ = SimpleNamespace(oturum=None, model=model or "varsayılan")
    cevir, ham, okunur = motorlar.cevirici(), [], []
    with open(f"{kayit}.cikti.jsonl", "w", encoding="utf-8") as fj, open(f"{kayit}.cikti.txt", "w", encoding="utf-8") as ft:
        s = subprocess.Popen(komut, cwd=paths.ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                             text=True, encoding="utf-8", errors="replace", env={**os.environ, "NO_COLOR": "1"})
        zaman = threading.Timer(AJAN_SURE, s.kill)
        zaman.start()
        try:
            for satir in s.stdout:
                satir = satir.rstrip()
                ham.append(satir)
                fj.write(satir + "\n")
                for x in cevir(is_, satir):
                    okunur.append(x)
                    ft.write(x + "\n")
                    ft.flush()
            kod = s.wait()
        finally:
            zaman.cancel()
    son, kul = _metin_ve_kullanim(ham)
    hata = next((x for x in okunur if x.startswith("Hata:")), None)
    meta.update(sure=round(time.time() - meta["baslangic"], 1), kod=kod, token=kul or None, oturum=is_.oturum, hata=hata)
    return kod == 0 and not hata, son or "\n".join(okunur), meta


# ---------------------------------------------------------------- zaman bölüşü

def zaman_araliklari(k: Kurgu, n: int = 3) -> list[tuple[float, float]]:
    """Süreyi kelime sınırında n parçaya böler; sınırlar kesin artar, her dilim en az eşit payın yarısıdır.

    Sınır, hedef noktaya yakın kelime arası boşluğun ortasıdır (geniş boşluk hafif öne geçer); uygun boşluk yoksa hedefin kendisi.
    WHY: kısa videoda en geniş boşluğu seçen eski kural iki sınırı aynı boşluğa koyup sıfır uzunlukta dilim üretiyordu (ADR 0053).
    """
    bitis = max((c.bas + c.sure for c in k.klipler), default=0.0)
    if n <= 1 or bitis <= 0:
        return [(0.0, round(bitis, 3))]
    kel = sorted((w["s"], w["e"]) for w in kurgu.izdusum(k)) if k.kelimeler else []
    bosluklar = [((a[1] + b[0]) / 2, b[0] - a[1]) for a, b in zip(kel, kel[1:]) if b[0] > a[1]]
    pay, en_az = bitis / n, bitis / n / 2
    sinir = [0.0]
    for i in range(1, n):
        hedef = bitis * i / n
        uygun = [(m, g) for m, g in bosluklar
                 if m - sinir[-1] >= en_az and bitis - m >= en_az * (n - i) and abs(m - hedef) < pay / 2]
        s = min(uygun, key=lambda x: abs(x[0] - hedef) - 0.5 * x[1])[0] if uygun else hedef
        sinir.append(round(max(s, sinir[-1] + en_az), 3))
    sinir.append(round(bitis, 3))
    return list(zip(sinir, sinir[1:]))


# ---------------------------------------------------------------- QC çıktısı

def json_cikar(metin: str) -> dict | None:
    """Metindeki `bulgular` anahtarlı son JSON nesnesi."""
    bloklar = re.findall(r"```json\s*(\{.*?\})\s*```", metin, flags=re.S)
    for b in reversed(bloklar):
        try:
            o = json.loads(b)
            if isinstance(o, dict) and "bulgular" in o:
                return o
        except ValueError:
            pass
    dec = json.JSONDecoder()
    for i in reversed([m.start() for m in re.finditer(r"\{", metin)]):
        try:
            o, _ = dec.raw_decode(metin[i:])
        except ValueError:
            continue
        if isinstance(o, dict) and "bulgular" in o:
            return o
    return None


# ---------------------------------------------------------------- QC girdisi

def izle(p, video: Path, kok: Path) -> dict:
    """K ajanlarının ortak girdisi: kareler (+OCR), kontak sayfası, ölçüm, kurgu-denetle. Deterministik."""
    kok.mkdir(parents=True, exist_ok=True)
    sure = float(ff.probe(video)["duration"])
    kontak = kok / "kontak.jpg"
    ff.contact_sheet(video, kontak, duration=sure, cols=6, rows=4, width=270)
    izd = kok / "izle"
    izd.mkdir(exist_ok=True)
    analiz = izd / "analiz.json"
    ocr: dict[float, str] = {}
    try:
        # WHY: video-izle skill'i (ADR 0038); anahtarlar boş: yalnız yerel ve ücretsiz yol.
        r = subprocess.run(["npx", "-y", "mcp-video-analyzer@0.11.0", "analyze", str(video), "--out", str(izd), "--max-frames", "40",
                            "--ocr-language", "tur+eng", "--language", "tr"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=900, env={**os.environ, "OPENAI_API_KEY": "", "TWELVELABS_API_KEY": ""}, shell=os.name == "nt")
        if r.returncode == 0 and r.stdout.strip().startswith("{"):
            analiz.write_text(r.stdout, encoding="utf-8")
            for o in json.loads(r.stdout).get("ocrResults") or []:
                if o.get("text"):
                    ocr[round(float(o.get("time", 0)), 1)] = " ".join(str(o["text"]).split())[:160]
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    # Sahne kareleri başa yığılabilir: her 1,5 sn'de bir sabit kare de çıkarılır, zaman damgası dosya adındadır.
    for t in [round(x * 1.5, 1) for x in range(int(sure / 1.5) + 1)]:
        hedef = izd / f"kare_{t:06.1f}.jpg"
        if not hedef.exists():
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(video), "-frames:v", "1", "-vf", "scale=540:-2", str(hedef)],
                           check=False)
    kareler = sorted(izd.glob("*.jpg"))
    liste = kok / "kareler.md"
    liste.write_text("# Kareler (zaman · dosya · OCR)\n\n" + "\n".join(
        f"- {f.stem.removeprefix('kare_')} · `{f.resolve()}`" + (f" · OCR: {ocr[float(f.stem[5:])]}"
                                                                  if f.stem.startswith("kare_") and float(f.stem[5:]) in ocr else "")
        for f in kareler) + "\n", encoding="utf-8")
    olaylar = p.work / "edit" / "olaylar.json"
    try:
        ol = hizli.denetim(video, olaylar=olaylar if olaylar.exists() else None, work=kok)
        (kok / "olcum.json").write_text(json.dumps(ol, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    except (SystemExit, Exception) as e:  # noqa: BLE001 - ölçüm eksik olsa da denetim sürer
        (kok / "olcum.json").write_text(json.dumps({"hata": str(e)[:400]}, ensure_ascii=False), encoding="utf-8")
    k = kurgu.oku(p.work)
    t = tema_token.oku(kurgu.etkin_tema(p, k.motion_tema))
    dn = [f"! {h}" for h in kurgu.denetle(p, k)] + [f"~ {u['bas']:.2f} sn {u['kod']}: {u['kanit']}. {u['oneri']}"
                                                    for u in kurgu_kalite.uyarilar(k, t)]
    (kok / "kurgu-denetle.txt").write_text("\n".join(dn) or "Kurgu temiz.", encoding="utf-8")
    if t:
        (kok / "stil-token.json").write_text(t.model_dump_json(indent=1), encoding="utf-8")
    return {"_kok": kok, "taslak video": video, "kontak sayfası": kontak, "kare listesi (zaman, yol, OCR)": liste,
            "ölçüm (format, loudness, slop)": kok / "olcum.json", "kurgu-denetle": kok / "kurgu-denetle.txt",
            "kurgu": kurgu.yol(p.work), **({"stil token": kok / "stil-token.json"} if t else {})}


# ---------------------------------------------------------------- bulgu takibi

def bulgu_dogrula(o: dict, rol: str) -> tuple[KontrolCikti | None, list[str]]:
    try:
        c = KontrolCikti.model_validate(o)
    except ValidationError as e:
        return None, [f"{rol}: şema: {str(e)[:300]}"]
    tut, dus = [], []
    for b in c.bulgular:
        if Path(b.kanit).is_file() or (paths.ROOT / b.kanit).is_file():
            tut.append(b)
        else:
            dus.append(f"{b.id}: kanıt karesi yok ({b.kanit}), bulgu düştü")
    c.bulgular = tut
    return c, dus


def _stil_sec(p, ad: str) -> None:
    """Stil projede seçilir; katalog stiliyse ve stüdyoda yoksa önce eklenir (temalar ADR 0043)."""
    from . import stil_katalog
    if not (stil.klasor(p.studyo, ad) / "STYLE.md").exists():
        stil_katalog.ekle(p.studyo, ad, p)
    else:
        stil.sec(p, ad)
