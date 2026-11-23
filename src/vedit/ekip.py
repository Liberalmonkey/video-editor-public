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
from .ekip_sema import Bulgu, EkipAyar, KontrolCikti, Slot
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
                    # Kapı süresi (ADR 0054): sonraki hızlandırma ölçüme dayansın; rapor ve kaizen en yavaş kapıyı yazar.
                    if durum == "acik":
                        self.d["asama"] = k["ad"]
                        k["bas"] = round(time.time(), 1)
                    elif durum in ("gecti", "kaldi") and k.get("bas"):
                        k["sure"] = round(time.time() - k["bas"], 1)
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


def ajan(slot: Slot, istem: str, mod: str, kayit: Path, *, yedek: bool = False, metin: str | None = None,
         sistem: str | None = None, araclar: str = "", dizinler: tuple = ()) -> tuple[bool, str, dict]:
    """Tek çağrı. Ham akış `<kayit>.cikti.jsonl`, okunur günlük `<kayit>.cikti.txt`. (başarılı, yanıt metni, meta).

    `metin` verilirse ve motor Claude ise yalın çağrı yapılır (ADR 0054): `metin` stdin'den, `sistem` (rol) sistem istemine,
    araç yalnız `araclar`. Öteki motorlar `istem`deki "dosyayı oku" yönergesiyle çalışır."""
    motor = slot.yedek_motor if yedek else slot.motor
    model = slot.yedek_model if yedek else slot.model
    seviye = slot.yedek_seviye if yedek else slot.seviye
    yalin = metin is not None and motor == "claude"
    meta = {"motor": motor, "model": model, "seviye": seviye, "mod": mod, "yedek": yedek, "yalin": yalin, "baslangic": time.time()}
    try:
        if yalin:
            komut = motorlar.yalin_komut(model, seviye, sistem=sistem, araclar=araclar, dizinler=dizinler)
            motorlar.YALIN_KOK.mkdir(parents=True, exist_ok=True)
        else:
            komut = motorlar.komut(motor, istem, model, mod, None, seviye)  # bypass bayrağı yok (motorlar kuralı)
    except SystemExit as e:
        meta.update(hata=str(e), sure=0)
        return False, "", meta
    is_ = SimpleNamespace(oturum=None, model=model or "varsayılan")
    cevir, ham, okunur = motorlar.cevirici(), [], []
    with open(f"{kayit}.cikti.jsonl", "w", encoding="utf-8") as fj, open(f"{kayit}.cikti.txt", "w", encoding="utf-8") as ft:
        # Yalın çağrı repo dışında başlar: proje CLAUDE.md'si kendiliğinden yüklenmesin.
        s = subprocess.Popen(komut, cwd=motorlar.YALIN_KOK if yalin else paths.ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             stdin=subprocess.PIPE if yalin else subprocess.DEVNULL,
                             text=True, encoding="utf-8", errors="replace", env={**os.environ, "NO_COLOR": "1"})
        if yalin:
            def besle():
                try:
                    s.stdin.write(metin)
                    s.stdin.close()
                except OSError:
                    pass
            threading.Thread(target=besle, daemon=True).start()  # büyük istemde stdout borusu dolarken kilitlenmesin
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

KARE_ARALIK = 1.5   # sn; sabit kare aralığı (uzun videoda en çok KARE_EN_COK kare)
KARE_EN_COK = 160
PAFTA_KARE = 12     # pafta başına kare (4 sütun × 3 satır)


def _ocr_analiz(video: Path, izd: Path) -> dict[float, str]:
    """mcp-video-analyzer: sahne kareleri + OCR. Hata ya da eksik araç denetimi düşürmez."""
    ocr: dict[float, str] = {}
    try:
        # WHY: video-izle skill'i (ADR 0038); anahtarlar boş: yalnız yerel ve ücretsiz yol.
        r = subprocess.run(["npx", "-y", "mcp-video-analyzer@0.11.0", "analyze", str(video), "--out", str(izd), "--max-frames", "40",
                            "--ocr-language", "tur+eng", "--language", "tr"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=900, env={**os.environ, "OPENAI_API_KEY": "", "TWELVELABS_API_KEY": ""}, shell=os.name == "nt")
        if r.returncode == 0 and r.stdout.strip().startswith("{"):
            (izd / "analiz.json").write_text(r.stdout, encoding="utf-8")
            for o in json.loads(r.stdout).get("ocrResults") or []:
                if o.get("text"):
                    ocr[round(float(o.get("time", 0)), 1)] = " ".join(str(o["text"]).split())[:160]
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return ocr


def sabit_kareler(video: Path, izd: Path, sure: float, *, es: int = 4) -> list[tuple[float, Path]]:
    """Her KARE_ARALIK sn'de bir kare; kesin seek (fps filtresi kareyi 1-2 sn kaydırır), paralel. Zaman dosya adındadır."""
    from concurrent.futures import ThreadPoolExecutor
    adim = max(KARE_ARALIK, sure / KARE_EN_COK)
    zamanlar = [round(x * adim, 1) for x in range(int(sure / adim) + 1)]

    def bir(t: float) -> tuple[float, Path]:
        hedef = izd / f"kare_{t:06.1f}.jpg"
        if not hedef.exists():
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(video), "-frames:v", "1", "-vf", "scale=540:-2",
                            str(hedef)], check=False)
        return t, hedef

    with ThreadPoolExecutor(es) as h:
        return [(t, f) for t, f in h.map(bir, zamanlar) if f.exists()]


def pafta_yap(kareler: list[tuple[float, Path]], kok: Path, *, n: int = PAFTA_KARE, sutun: int = 4, genislik: int = 270) -> list[Path]:
    """Kareleri n'lik paftalarda toplar, her karenin köşesine saniyesi yazılır.

    WHY: bkz. wiki/decisions/0054-hizli-edit.md. QC ajanı (agy) 53 kareyi tek tek okuyunca 7 dk sürüyordu; paftayla birkaç
    görsel okur. Kanıt yine tek karenin yoludur (kareler.md), pafta yalnız bakmak içindir."""
    from PIL import Image, ImageDraw, ImageFont
    for eski in kok.glob("pafta-*.jpg"):
        eski.unlink()
    try:
        font = ImageFont.load_default(size=22)
    except TypeError:  # eski Pillow
        font = ImageFont.load_default()
    cikti = []
    for i in range(0, len(kareler), n):
        grup = kareler[i:i + n]
        resimler = []
        for t, f in grup:
            with Image.open(f) as im:
                im = im.convert("RGB")
                resimler.append((t, im.resize((genislik, max(1, round(im.height * genislik / im.width))))))
        h = max(im.height for _, im in resimler)
        satir = -(-len(resimler) // sutun)
        pafta = Image.new("RGB", (sutun * genislik, satir * h), "black")
        ciz = ImageDraw.Draw(pafta)
        for j, (t, im) in enumerate(resimler):
            x, y = (j % sutun) * genislik, (j // sutun) * h
            pafta.paste(im, (x, y))
            etiket = f"{t:.1f} sn"
            kutu = ciz.textbbox((x + 6, y + 6), etiket, font=font)
            ciz.rectangle((kutu[0] - 4, kutu[1] - 3, kutu[2] + 4, kutu[3] + 3), fill="black")
            ciz.text((x + 6, y + 6), etiket, fill="white", font=font)
        hedef = kok / f"pafta-{i // n + 1}.jpg"
        pafta.save(hedef, quality=85)
        cikti.append(hedef)
    return cikti


def izle(p, video: Path, kok: Path) -> dict:
    """K ajanlarının ortak girdisi: kareler (+OCR), paftalar, kontak sayfası, ölçüm, kurgu-denetle. Deterministik.

    OCR (npx, yavaş) arka planda koşarken sabit kareler, paftalar, kontak ve ölçüm çıkarılır (ADR 0054)."""
    from concurrent.futures import ThreadPoolExecutor
    kok.mkdir(parents=True, exist_ok=True)
    sure = float(ff.probe(video)["duration"])
    kontak = kok / "kontak.jpg"
    izd = kok / "izle"
    izd.mkdir(exist_ok=True)
    arka = ThreadPoolExecutor(2)
    ocr_is = arka.submit(_ocr_analiz, video, izd)
    kontak_is = arka.submit(ff.contact_sheet, video, kontak, duration=sure, cols=6, rows=4, width=270)
    sabit = sabit_kareler(video, izd, sure)
    paftalar = pafta_yap(sabit, kok) if sabit else []
    olaylar = p.work / "edit" / "olaylar.json"
    try:
        ol = hizli.denetim(video, olaylar=olaylar if olaylar.exists() else None, work=kok)
        (kok / "olcum.json").write_text(json.dumps(ol, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    except (SystemExit, Exception) as e:  # noqa: BLE001 - ölçüm eksik olsa da denetim sürer
        (kok / "olcum.json").write_text(json.dumps({"hata": str(e)[:400]}, ensure_ascii=False), encoding="utf-8")
    ocr = ocr_is.result()
    kontak_is.result()
    arka.shutdown()
    kareler = sorted(izd.glob("*.jpg"))
    liste = kok / "kareler.md"
    liste.write_text("# Kareler (zaman · dosya · OCR)\n\n" + "\n".join(
        f"- {f.stem.removeprefix('kare_')} · `{f.resolve()}`" + (f" · OCR: {ocr[float(f.stem[5:])]}"
                                                                  if f.stem.startswith("kare_") and float(f.stem[5:]) in ocr else "")
        for f in kareler) + "\n", encoding="utf-8")
    k = kurgu.oku(p.work)
    t = tema_token.oku(kurgu.etkin_tema(p, k.motion_tema))
    dn = [f"! {h}" for h in kurgu.denetle(p, k)] + [f"~ {u['bas']:.2f} sn {u['kod']}: {u['kanit']}. {u['oneri']}"
                                                    for u in kurgu_kalite.uyarilar(k, t)]
    (kok / "kurgu-denetle.txt").write_text("\n".join(dn) or "Kurgu temiz.", encoding="utf-8")
    if t:
        (kok / "stil-token.json").write_text(t.model_dump_json(indent=1), encoding="utf-8")
    return {"_kok": kok, "_paftalar": paftalar, "_vedit": vedit_bulgulari(kok), "taslak video": video, "kontak sayfası": kontak,
            "kare listesi (zaman, yol, OCR)": liste, "ölçüm (format, loudness, slop)": kok / "olcum.json",
            "kurgu-denetle": kok / "kurgu-denetle.txt", "kurgu": kurgu.yol(p.work),
            **({"stil token": kok / "stil-token.json"} if t else {})}


def vedit_bulgulari(kok: Path) -> list[str]:
    """vedit'in ölçtüğü kusurlar (slop, loudness, kurgu-denetle) tek satır: QC bunları yeniden yazmaz (ADR 0054).

    Taslak loudness'i bilgi içindir: teslim miksi -14 LUFS / -1 dBTP'ye kendisi eşler."""
    sat = []
    try:
        ol = json.loads((kok / "olcum.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        ol = {}
    for b in ((ol.get("slop") or {}).get("bulgular") or []):
        yer = f" {b['bas']:.1f}-{b['bit']:.1f} sn" if b.get("bas") is not None and b.get("bit") is not None else ""
        sat.append(f"[{b.get('seviye')} {b.get('kod')}]{yer} {b.get('kanit', '')}")
    if lu := ol.get("loudness"):
        sat.append(f"[bilgi] taslak loudness I {lu.get('I')} LUFS, TP {lu.get('TP')} dBTP (teslim miksi kendisi eşler; bulgu yazma)")
    f = kok / "kurgu-denetle.txt"
    if f.is_file():
        sat += [x for x in f.read_text(encoding="utf-8").splitlines() if x.startswith(("!", "~"))]
    return sat


# ---------------------------------------------------------------- bulgu takibi

_BULGU_DESEN = {"hedef": r"E(10|[1-9])", "kural_id": r"K\d{4}", "kural_adayi": r"(YAP|YAPMA): \S.{8,}"}


def _bulgu_temizle(b: dict) -> dict:
    """Bilinmeyen alanı atar; isteğe bağlı alan (hedef, kural_id, kural_adayi) kalıba uymuyorsa boşaltır.
    Zorunlu alanlar olduğu gibi kalır: onlar bozuksa bulgu şemada düşer."""
    b = {k: v for k, v in b.items() if k in Bulgu.model_fields}
    if isinstance(b.get("kural_adayi"), str):
        b["kural_adayi"] = " ".join(b["kural_adayi"].split())
    for alan, desen in _BULGU_DESEN.items():
        if b.get(alan) is not None and not (isinstance(b[alan], str) and re.fullmatch(desen, b[alan])):
            b[alan] = None
    return b


def bulgu_dogrula(o: dict, rol: str) -> tuple[KontrolCikti | None, list[str]]:
    """Kalite kontrol çıktısını bulgu bulgu doğrular: bozuk bulgu tek başına düşer, ötekiler kalır.

    WHY: tek bir şemaya uymayan bulgu (ek alan, yanlış kategori) eskiden o kalite kontrolün bütün bulgularını düşürüyordu;
    max seviyede beş kalite kontrolle kayıp büyür (ADR 0053). Kimlik `<rol>-NNN` değilse ya da tekrar ediyorsa yeniden numaralanır:
    iki kalite kontrol aynı kimliği yazınca triyajın reddi ikisini birden siliyordu."""
    if not isinstance(o, dict) or not isinstance(o.get("bulgular", []), list):
        return None, [f"{rol}: şema: bulgular listesi yok"]
    tut, dus, gorulen = [], [], set()
    for i, ham in enumerate(o.get("bulgular") or [], 1):
        if not isinstance(ham, dict):
            dus.append(f"{rol}: {i}. bulgu nesne değil, düştü")
            continue
        b = _bulgu_temizle(ham)
        bid = b.get("id")
        if not (isinstance(bid, str) and re.fullmatch(rf"{re.escape(rol)}-\d{{3}}", bid)) or bid in gorulen:
            b["id"] = next(f"{rol}-{n:03d}" for n in range(i, 1000) if f"{rol}-{n:03d}" not in gorulen)
        try:
            bulgu = Bulgu.model_validate(b)
        except ValidationError as e:
            dus.append(f"{rol}: {i}. bulgu şemaya uymuyor, düştü: {str(e)[:200]}")
            continue
        if not (Path(bulgu.kanit).is_file() or (paths.ROOT / bulgu.kanit).is_file()):
            dus.append(f"{bulgu.id}: kanıt karesi yok ({bulgu.kanit}), bulgu düştü")
            continue
        gorulen.add(bulgu.id)
        tut.append(bulgu)
    return KontrolCikti(bulgular=tut, brif=str(o.get("brif") or "")), dus


def _stil_sec(p, ad: str) -> None:
    """Stil projede seçilir; katalog stiliyse ve stüdyoda yoksa önce eklenir (temalar ADR 0043)."""
    from . import stil_katalog
    if not (stil.klasor(p.studyo, ad) / "STYLE.md").exists():
        stil_katalog.ekle(p.studyo, ad, p)
    else:
        stil.sec(p, ad)
