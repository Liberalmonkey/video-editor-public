"""İş kuyruğu: beyaz listeli vedit alt komutları, tek seferde bir iş, canlı günlük, iptal.

WHY: bkz. wiki/decisions/0021-video-studyo-nle.md. Komut yalnız argüman listesiyle kurulur; istekten kabuk dizgesi çıkmaz.
Render makineyi doldurur, iki render yan yana hepsini yavaşlatır; bu yüzden tek işçi.
"""

from __future__ import annotations

import asyncio
import itertools
import json
import os
import queue
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .. import ayristir, kurgu, paths, teslim
from ..ekip_sema import EN_COK
from . import ortak

VEDIT = paths.ROOT / ".venv" / "Scripts" / ("vedit.exe" if os.name == "nt" else "vedit")
# ayristir ve ses-cikar ayrı dalda: yol ve seçenek alırlar (ses_arguman)
PROJELI = {"hazirla", "kes", "taslak", "final", "kaizen", "kurgu-al", "miks", "ai-edit"}
STIL_AD = re.compile(r"[\w\-]{1,40}")
PLATFORM = {"youtube", "reels", "ugc"}
router = APIRouter()
_sayac = itertools.count(1)  # iki kuyruk ortak: iş kimliği tek


class Istek(BaseModel):
    komut: str
    studyo: str | None = None
    ad: str | None = None
    aralik: tuple[float, float] | None = None
    platform: str | None = None
    cikti_adi: str | None = None
    yenile: bool = False
    cozunurluk: int | None = None  # final: kısa kenar
    kalite: str | None = None
    kodek: str | None = None
    fps: int | None = None
    kaynaga: bool | None = None  # final: kaynağa eşle (ADR 0060); None ön ayarın varsayılanı
    vmaf: bool = False
    dil: str | None = None
    video: str | None = None  # denetim: outputs içinde göreli yol
    motor: str | None = None  # ai-edit, stil-uret
    model: str | None = None
    stil: str | None = None
    notu: str | None = None  # ai-edit
    motion: str | None = None  # ai-edit: az | orta | yogun
    final: bool = False  # ai-edit: taslaktan sonra final
    yol: str | None = None  # ayristir, ses-cikar: "inputs:1.mp4" ya da "public:..."
    stem: int | None = None  # ayristir: 2 ya da 4
    bicim: str | None = None  # ses-cikar
    hepsi: bool = False  # ayristir, ses-cikar: girdi klasörünün tamamı
    ekip: bool = False  # ai-edit: orkestratör + seviyeli ekip (ADR 0053)
    ekip_ayar: dict | None = None  # seviye, gruplar, ezme; doğrulanıp work/edit/ekip/istek-ayar.json'a yazılır
    platformlar: list[str] | None = None  # yayin: reels, youtube, shorts, tiktok, linkedin (ADR 0055)
    seviye: str | None = None  # yayin: akıl yürütme seviyesi (motorlar.SEVIYELER)


def arguman(i: Istek) -> list[str]:
    """Beyaz liste. Bilinmeyen komut ya da biçimsiz değer burada durur."""
    if i.komut == "duzen":
        return ["duzen"]
    if i.komut == "stil-uret":
        if i.studyo not in paths.STUDIO_NAMES:
            raise HTTPException(400, "Bilinmeyen stüdyo")
        return ["stil-uret", i.studyo, _stil(i.stil), *ajan_bayraklari(i)]
    if i.studyo is None or i.ad is None:
        raise HTTPException(400, "Proje gerekli")
    p = ortak.proje(i.studyo, i.ad)
    ref = f"{p.studyo}/{p.ad}"
    if i.komut == "denetim":
        if not i.video:
            raise HTTPException(400, "Video gerekli")
        return ["denetim", str(ortak.kok_ici(p.cikti, i.video))]
    if i.komut in ("ayristir", "ses-cikar"):
        return ses_arguman(i, p, ref)
    if i.komut == "yayin":
        return yayin_arguman(i, p, ref)
    if i.komut not in PROJELI:
        raise HTTPException(400, f"İzinli olmayan komut: {i.komut}")
    a = [i.komut, ref]
    if i.komut == "hazirla" and i.dil:
        if i.dil not in ("tr", "en"):
            raise HTTPException(400, "Dil tr ya da en")
        a += ["--dil", i.dil]
    if i.komut in ("taslak", "ai-edit") and i.aralik:
        a += ["--aralik", f"{float(i.aralik[0]):.3f}", f"{float(i.aralik[1]):.3f}"]
    if i.komut == "ai-edit" and i.ekip:
        # WHY: bkz. wiki/decisions/0053-seviyeli-ekip-orkestrator.md. Grup ve ezme motor/modeli canlı listede doğrulanır.
        from . import ekip as ekip_api
        ayar = ekip_api.dogrula({**(i.ekip_ayar or {}), **({"stil": i.stil} if i.stil else {}), **({"motion": i.motion} if i.motion else {})})
        f = p.work / "edit" / "ekip" / "istek-ayar.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(ayar.model_dump_json(indent=1), encoding="utf-8")
        a += ["--ekip", "--ekip-dosyasi", str(f)]
    elif i.komut == "ai-edit":
        a += ajan_bayraklari(i)
    if i.komut == "ai-edit":
        if i.stil:
            a += ["--stil", _stil(i.stil)]
        if i.notu and (notu := " ".join(i.notu.split())):
            if len(notu) > 2000:  # AI panelindeki istek buradan geçer
                raise HTTPException(400, "Not en çok 2000 karakter")
            a.append(f"--not={notu}")  # WHY: '-' ile başlayan not bayrak sanılmasın
        if i.motion:
            if i.motion not in ("az", "orta", "yogun"):
                raise HTTPException(400, "Motion yoğunluğu az, orta ya da yogun")
            a += ["--motion", i.motion]
        if i.final:
            a.append("--final")
    if i.komut == "final" or (i.komut == "ai-edit" and i.final):
        if i.platform:
            if i.platform not in PLATFORM:
                raise HTTPException(400, "Bilinmeyen platform")
            a += ["--platform", i.platform]
        if i.cikti_adi:
            if not re.fullmatch(r"[\w\-]{1,80}", i.cikti_adi):
                raise HTTPException(400, "Çıktı adı yalnız harf, rakam, tire")
            a += ["--ad", i.cikti_adi]
        if i.yenile:
            a.append("--yenile")
        for bayrak, deger, izinli in (("--cozunurluk", i.cozunurluk, teslim.COZUNURLUK), ("--kalite", i.kalite, teslim.KALITE),
                                      ("--kodek", i.kodek, teslim.KODEK), ("--fps", i.fps, teslim.FPS)):
            if deger is not None:
                if deger not in izinli:
                    raise HTTPException(400, f"Bilinmeyen değer: {bayrak[2:]}")
                a += [bayrak, str(deger)]
        if i.kaynaga is not None:
            a.append("--kaynaga-esle" if i.kaynaga else "--no-kaynaga-esle")
        if i.vmaf:
            a.append("--vmaf")
    return a


def _stil(ad: str | None) -> str:
    if not ad or not STIL_AD.fullmatch(ad):
        raise HTTPException(400, "Stil adı yalnız harf, rakam, tire; en çok 40 karakter")
    return ad


def ajan_bayraklari(i: Istek) -> list[str]:
    """Motor ve model AI panelindeki listeden; listede olmayan değer komuta girmez."""
    from . import ajan  # döngüsel içe aktarma: ajan bu modülü kullanır
    if not i.motor:
        if i.model:
            raise HTTPException(400, "Model için motor gerekli")
        return []
    d = ajan._durum().get(i.motor)
    if not d or not d["kurulu"]:
        raise HTTPException(400, f"Motor yok ya da kurulu değil: {i.motor}")
    if i.model and i.model not in [m["id"] for m in d["modeller"]]:
        raise HTTPException(400, f"Bu motorda olmayan model: {i.model}")
    return ["--motor", i.motor, *(["--model", i.model] if i.model else [])]


def yayin_arguman(i: Istek, p, ref: str) -> list[str]:
    """WHY: bkz. wiki/decisions/0055-teslimde-yayin-metni.md. Video teslim kökünde, platform reçetede, motor/model canlı listede."""
    from .. import motorlar, yayin
    a = ["yayin", ref]
    if i.hepsi:
        a.append("--hepsi")
    elif i.video:
        try:
            a.append(f"--video={yayin.video_bul(p, i.video).name}")
        except SystemExit as e:
            raise HTTPException(400, str(e)) from e
    else:
        raise HTTPException(400, "Video ya da hepsi gerekli")
    if i.platformlar:
        try:
            a.append("--platform=" + ",".join(yayin.platform_listesi(i.platformlar, p.studyo)))
        except SystemExit as e:
            raise HTTPException(400, str(e)) from e
    a += ajan_bayraklari(i)
    if i.seviye:
        if not i.motor or i.seviye not in motorlar.SEVIYELER.get(i.motor, ()):
            raise HTTPException(400, f"Bu motorda olmayan seviye: {i.seviye}")
        a += ["--seviye", i.seviye]
    if i.dil:
        if i.dil not in ("tr", "en"):
            raise HTTPException(400, "Dil tr ya da en")
        a += ["--dil", i.dil]
    return a


def ses_yolu(p, yol: str | None) -> str:
    """Yalnız projenin girdisi ya da work/public altındaki var olan dosya; kök dışına çıkan yol reddedilir."""
    kok = (yol or "").partition(":")[0]
    if kok not in ("inputs", "public"):
        raise HTTPException(400, "Yol inputs: ya da public: ile başlamalı")
    try:
        f = kurgu.dosya(p, yol)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    if not f.is_file():
        raise HTTPException(404, "Dosya yok")
    return yol


def ses_arguman(i: Istek, p, ref: str) -> list[str]:
    # WHY: bkz. wiki/decisions/0034-ses-araclari.md. Biçim ve stem kapalı kümeden; yol proje köküne kilitli.
    a = [i.komut, ref]
    if i.hepsi:
        a.append("--hepsi")
    else:
        a.append(ses_yolu(p, i.yol))
    if i.komut == "ayristir":
        if i.stem not in (None, 2, 4):
            raise HTTPException(400, "Stem 2 ya da 4")
        a += ["--stem", str(i.stem or 2)]
    else:
        if i.bicim not in (None, *ayristir.BICIMLER):
            raise HTTPException(400, f"Biçim {', '.join(ayristir.BICIMLER)} olmalı")
        a += ["--bicim", i.bicim or "wav"]
    return a


@dataclass
class Is:
    id: int
    komut: str
    baslik: str
    args: list[str]
    durum: str = "sirada"  # sirada | calisiyor | bitti | hata | iptal
    satirlar: list[str] = field(default_factory=list)
    baslangic: float | None = None
    bitis: float | None = None
    kod: int | None = None
    surec: subprocess.Popen | None = None
    iptal: bool = False
    exe: str | None = None  # ajan işi: claude ya da agy
    motor: str | None = None
    model: str | None = None
    oturum: str | None = None
    cevir: Callable[["Is", str], list[str]] | None = None

    def ozet(self) -> dict:
        return {"id": self.id, "komut": self.komut, "baslik": self.baslik, "durum": self.durum, "baslangic": self.baslangic,
                "bitis": self.bitis, "kod": self.kod, "satir": len(self.satirlar), "motor": self.motor, "model": self.model,
                "oturum": self.oturum}


class Kuyruk:
    def __init__(self, exe: Path = VEDIT):
        self.exe = exe
        self.isler: list[Is] = []
        self._q: queue.Queue[Is] = queue.Queue()
        self._kilit = threading.Lock()
        threading.Thread(target=self._dongu, daemon=True).start()

    def ekle(self, komut: str, baslik: str, args: list[str], **ek) -> Is:
        is_ = Is(next(_sayac), komut, baslik, args, **ek)
        with self._kilit:
            self.isler.append(is_)
            self.isler[:] = self.isler[-50:]
        self._q.put(is_)
        return is_

    def bul(self, iid: int) -> Is:
        with self._kilit:
            isler_kopya = list(self.isler)
        for i in isler_kopya:
            if i.id == iid:
                return i
        raise HTTPException(404, "İş yok")

    def iptal(self, is_: Is) -> None:
        with self._kilit:
            is_.iptal = True
            if is_.durum == "sirada":
                is_.durum = "iptal"
                return
            surec = is_.surec
        if surec and surec.poll() is None:
            # WHY: Remotion ve ffmpeg alt süreç açar; yalnız kökü öldürmek Chrome ve ffmpeg'i arkada bırakır.
            if os.name == "nt":
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(surec.pid)], capture_output=True)
            else:
                surec.kill()

    def _dongu(self) -> None:
        while True:
            is_ = self._q.get()
            with self._kilit:
                if is_.durum == "iptal" or is_.iptal:
                    is_.durum = "iptal"
                    continue
            from .. import hf_guncel
            while hf_guncel.kilitli() and not is_.iptal:  # WHY: HyperFrames kökü değişirken render başlamasın (ADR 0051)
                time.sleep(2)
            with self._kilit:
                # WHY: iptal ile _dongu arasındaki 'sirada'->'calisiyor' geçişi kilitsizdi; iptal edilmiş iş Popen başlatmasın.
                if is_.iptal or is_.durum == "iptal":
                    is_.durum = "iptal"
                    continue
                is_.durum, is_.baslangic = "calisiyor", time.time()
            try:
                self._calistir(is_)
            except Exception as e:  # WHY: tek işin hatası kuyruğu öldürmemeli
                is_.satirlar.append(f"Hata: {e}")
                with self._kilit:
                    is_.durum = "hata"
            is_.bitis = time.time()

    def _calistir(self, is_: Is) -> None:
        ortam = {**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8", "NO_COLOR": "1"}
        with self._kilit:
            # WHY: calisiyor geçişi ile Popen arasındaki küçük aralıkta iptal geldiyse alt süreç açılmasın.
            if is_.iptal:
                is_.durum = "iptal"
                return
            s = subprocess.Popen([is_.exe or str(self.exe), *is_.args], cwd=paths.ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, env=ortam, text=True, encoding="utf-8", errors="replace")
            is_.surec = s
        try:
            for satir in s.stdout:
                satir = satir.rstrip()
                is_.satirlar.extend(x[:2000] for x in (is_.cevir(is_, satir) if is_.cevir else [satir]))
            is_.kod = s.wait()
        finally:
            # WHY: okuma kırılırsa stdout pipe tanıtıcısı açık kalıp süreç kaynağını sızdırmasın.
            if s.stdout is not None and hasattr(s.stdout, "close"):
                s.stdout.close()
        with self._kilit:
            is_.durum = "iptal" if is_.iptal else "bitti" if is_.kod == 0 else "hata"


_baslat_kilit = threading.Lock()
kuyruk: Kuyruk | None = None
ajan: Kuyruk | None = None


def _k() -> Kuyruk:
    global kuyruk
    # WHY: eşzamanlı ilk istekte iki Kuyruk ve iki işçi thread'i oluşmasın.
    with _baslat_kilit:
        if kuyruk is None:
            kuyruk = Kuyruk()
        return kuyruk


def ajan_kuyrugu() -> Kuyruk:
    """Ajan işleri ayrı işçide: ağ işidir, render kuyruğunu bekletmez. WHY: bkz. wiki/decisions/0026-arayuzde-ajan.md"""
    global ajan
    # WHY: eşzamanlı ilk ajan isteğinde iki ajan kuyruğu oluşmasın.
    with _baslat_kilit:
        if ajan is None:
            ajan = Kuyruk()
        return ajan


def _hepsi() -> list[Is]:
    return sorted([*_k().isler, *(ajan.isler if ajan else [])], key=lambda x: x.id)


def _bul(iid: int) -> Is:
    for i in _hepsi():
        if i.id == iid:
            return i
    raise HTTPException(404, "İş yok")


@router.post("/api/isler")
def is_ekle(i: Istek):
    args = arguman(i)
    baslik = f"stil-uret · {i.studyo}/{i.stil}" if i.komut == "stil-uret" else f"{i.komut} · {i.studyo}/{i.ad}" if i.ad and i.komut != "duzen" else i.komut
    # WHY: rozet çalışan işin motorunu gösterir; ekip işinde motor yoktu, rozet tek ajan seçimini (claude) gösteriyordu.
    # Swarm'da "ekip" + tavan yazılır (ADR 0059); rozet çalışan slotları ekip durumundan okur.
    if i.komut == "ai-edit" and i.ekip:
        ea = i.ekip_ayar or {}
        ek = {"motor": "ekip", "model": "hızlı" if ea.get("hizli") else f"en çok {ea.get('en_cok') or EN_COK.get(ea.get('ekip_seviye') or 'medium', 6)}"}
    elif i.komut in ("ai-edit", "stil-uret", "yayin") and i.motor:
        ek = {"motor": i.motor, "model": i.model}
    else:
        ek = {}
    return _k().ekle(i.komut, baslik, args, **ek).ozet()


@router.get("/api/isler")
def is_liste():
    return [x.ozet() for x in _hepsi()]


@router.get("/api/isler/{iid}/gunluk")
def gunluk(iid: int):
    return _bul(iid).satirlar


@router.post("/api/isler/{iid}/iptal")
def iptal(iid: int):
    is_ = _bul(iid)
    (ajan if ajan and is_ in ajan.isler else _k()).iptal(is_)
    return is_.ozet()


@router.get("/api/isler/akis")
async def akis():
    """SSE: durum değişimi ve yeni satırlar. Yeni bağlanan yalnız son 200 satırı alır."""
    async def uret():
        gorulen: dict[int, tuple[str, int]] = {}
        while True:
            for x in _hepsi():
                durum, sira = gorulen.get(x.id, ("", max(0, len(x.satirlar) - 200)))
                yeni = x.satirlar[sira:]
                if x.durum != durum or yeni:
                    yield f"data: {json.dumps({**x.ozet(), 'yeni': yeni}, ensure_ascii=False)}\n\n"
                    gorulen[x.id] = (x.durum, sira + len(yeni))
            yield ": canli\n\n"
            await asyncio.sleep(0.4)
    return StreamingResponse(uret(), media_type="text/event-stream", headers={"Cache-Control": "no-store"})
