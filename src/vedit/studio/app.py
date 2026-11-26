"""Video Stüdyo sunucusu: yerel, token'lı, kök içi dosya erişimi.

WHY: bkz. wiki/decisions/0021-video-studyo-nle.md. Yerel sunucuya ziyaret edilen web siteleri de istek atabilir;
Host + Origin + çerez token bu yüzden her istekte denetlenir.
"""

from __future__ import annotations

import asyncio
import functools
import json
import re
import secrets
import threading
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel

from .. import ayristir, ff, hizli, kurgu, motion, paths, teslim, vekil
from ..schemas import Kurgu
from . import ajan, gorsel, isler, kutuphane, medya
from . import ekip as ekip_api
from . import galeri as galeri_api
from . import kurallar as kurallar_api
from . import stil as stil_api
from .ortak import kok_ici, proje

DIST = paths.ROOT / "studio" / "web" / "dist"
# WHY: kullanıcı dosyası aynı kökten HTML olarak çalışıp API'ye ulaşamasın.
GUVENLI = {"X-Content-Type-Options": "nosniff", "Content-Security-Policy": "sandbox"}


def _proxy_yolu(p: hizli.Proje, kaynak: Path) -> Path:
    return vekil.yol(p.work, kaynak, "onizleme")


def _proxy_uret(p: hizli.Proje, kaynak: Path) -> None:
    # WHY: bkz. wiki/decisions/0060-proxy-master-conform.md. Önizleme ve taslak proxy'si tek modülde (vekil);
    # ağır kaynakta (4K, HEVC, 10-bit, HDR, VFR) taslak katmanı da arka planda hazırlanır.
    vekil.sessiz_uret(p.work, kaynak, "onizleme")
    if kaynak.suffix.lower() in vekil.BAGLANABILIR and vekil.gerekli(ff.probe_ob(kaynak)):
        vekil.sessiz_uret(p.work, kaynak, "taslak")


@functools.lru_cache(maxsize=512)
def _alfali(yol: str, _mtime: int, _boyut: int) -> bool:
    try:
        return bool((ff.probe(Path(yol)).get("video") or {}).get("alfa"))
    except Exception:  # WHY: okunamayan dosyada karar eski davranışa düşer
        return False


def _video_bilgi(f: Path) -> dict | None:
    """ffprobe video akışı, önbellekli. WHY: Teslim paneli her açılışta her girdiyi yoklamasın (ADR 0050)."""
    try:
        return ff.probe_ob(f).get("video")
    except Exception:  # WHY: okunamayan girdi özet ekranını düşürmesin
        return None


def alfali(f: Path) -> bool:
    """Dosya alfa kanalı taşıyor mu. Sonuç mtime ve boyutla önbellekte: her GET'te ffprobe çalışmasın."""
    if f.suffix.lower() not in (".webm", ".mov", ".mkv"):
        return False
    st = f.stat()
    return _alfali(str(f), st.st_mtime_ns, st.st_size)


def medya_eslemesi(p: hizli.Proje, k: Kurgu, *, proxy_baslat: bool = True) -> dict[str, str]:
    """Kaynak id → önizleme adresi. Proxy hazır değilse özgün dosya, üretim arka planda."""
    es: dict[str, str] = {}
    motion_kaynak = {c.kaynak for c in k.klipler if c.tur == "motion" and c.kaynak}
    for ad, kay in k.kaynaklar.items():
        f = kurgu.dosya(p, kay.yol)
        if not f.exists():
            continue
        kok, _, ic = kay.yol.partition(":")
        url = f"/dosya/{p.studyo}/{p.ad}/{kok}/{quote(ic)}"
        # WHY: proxy libx264 yuv420p yazar ve alfayı atar; motion klibi Player'da siyah kutu olur
        # (instagram/1, 2026-11-19). Motion kaynağı ve alfalı her dosya özgün haliyle oynar.
        if f.suffix.lower() in hizli.VIDEO and kok not in ("library", "stil") and ad not in motion_kaynak and not alfali(f):
            px = _proxy_yolu(p, f)
            if px.exists():
                url = f"/dosya/{p.studyo}/{p.ad}/proxy/{quote(px.name)}"
            elif proxy_baslat:
                threading.Thread(target=_proxy_uret, args=(p, f), daemon=True).start()
        es[ad] = url
    return es


def _json(f: Path) -> dict | None:
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def ses_ozeti(p: hizli.Proje) -> dict:
    f = p.work / "edit" / "olaylar.rapor.json"
    r = _json(f)
    if not r:
        return {"olcum": None}
    k = kurgu.yol(p.work)
    sesli = p.work / "renders" / "sesli.mp4"
    return {
        "olcum": r.get("loudness"), "yerlesen": r.get("yerlesen"), "uyarilar": r.get("uyarilar", []), "dusen": r.get("dusen", []),
        # WHY: kurgu sonradan değiştiyse eski sayı güncel gibi görünmesin.
        "eski": k.exists() and k.stat().st_mtime > f.stat().st_mtime,
        "dinle": f"/dosya/{p.studyo}/{p.ad}/outputs/work/renders/sesli.mp4?v={int(sesli.stat().st_mtime)}" if sesli.exists() else None,
    }


def hukum_ver(bulgular: list[dict], ses_tamam: bool | None) -> str:
    """Ölçüme dayalı hüküm: P0 ya da eşik dışı ses yayınlanamaz. Görsel rubrik `denetim` skill'indedir."""
    if any(b.get("seviye") == "P0" for b in bulgular) or ses_tamam is False:
        return "YAYINLANAMAZ"
    return "YAYINLANABILIR"


def denetim_ozeti(p: hizli.Proje) -> dict:
    qa = p.work / "qa"
    d, s, o = _json(qa / "denetim.json"), _json(qa / "slop-olcum.json"), _json(qa / "onay.json")
    if not d:
        return {"video": None}
    bulgular = (s or {}).get("bulgular", [])
    sira = {"P0": 0, "P1": 1, "P2": 2}
    bulgular = sorted(bulgular, key=lambda b: (sira.get(b.get("seviye"), 9), b.get("bas", 0)))
    k = kurgu.yol(p.work)
    onay = o if o and o.get("video") == d["video"] else None
    sheet = qa / f"{Path(d['video']).stem}.jpg"
    return {**d, "bulgular": bulgular, "hukum": hukum_ver(bulgular, d.get("ses_tamam")), "onay": onay,
            "eski": k.exists() and k.stat().st_mtime > (qa / "denetim.json").stat().st_mtime,
            "kareler": f"/dosya/{p.studyo}/{p.ad}/outputs/work/qa/{quote(sheet.name)}" if sheet.exists() else None}


def kurgu_al(p: hizli.Proje):
    """Kurguyu okur; yoksa 404, bozuksa 422. WHY: terminalden elle yazılan kurgu bozuk olabilir, sunucu 500 vermemeli."""
    try:
        return kurgu.oku(p.work)
    except FileNotFoundError as e:
        raise HTTPException(404, "Kurgu yok") from e
    except ValueError as e:
        raise HTTPException(422, f"kurgu.json geçersiz: {e}") from e


def teslim_ozeti(p: hizli.Proje) -> dict:
    """Çıktı ayarı seçenekleri, sekans, kaynak klip çözünürlüğü ve son teslimin ölçülen değerleri (tahmin yok)."""
    tam = kurgu_al(p) if kurgu.yol(p.work).exists() else None
    k = tam.sekans if tam else None
    kisa = [min(v["width"], v["height"]) for f in sorted(p.girdi.glob("*.mp4")) if (v := _video_bilgi(f))]
    son = max(p.cikti.glob("*.mp4"), key=lambda f: f.stat().st_mtime, default=None) if p.cikti.exists() else None
    olcum = None
    if son:
        v, s = teslim._akislar(son)
        olcum = {"dosya": son.name, "w": int(v["width"]), "h": int(v["height"]), "kodek": v.get("codec_name"), "profil": v.get("profile"),
                 "fps": f"{teslim.eval_kesir(v.get('avg_frame_rate')):g}", "mbps": round(int(v.get("bit_rate") or v["_toplam_bit"]) / 1e6, 1),
                 "pix_fmt": v.get("pix_fmt"), "renk": f"{v.get('color_space')} / {v.get('color_range')}",
                 "ses": f"{s.get('codec_name')} {round(int(s.get('bit_rate') or 0) / 1000)} kbps {s.get('sample_rate')} Hz" if s else None,
                 "mb": round(son.stat().st_size / 1e6, 1)}
    # WHY: bkz. wiki/decisions/0060-proxy-master-conform.md. Proxy durumu ve son teslimin sadakat/conform raporu.
    vekiller = []
    for f in sorted(x for x in p.girdi.iterdir() if x.is_file() and x.suffix.lower() in hizli.VIDEO) if p.girdi.exists() else []:
        try:
            n = vekil.neden(ff.probe_ob(f))
        except Exception:  # WHY: okunamayan girdi özet ekranını düşürmesin
            continue
        vekiller.append({"dosya": f.name, "neden": n, "hazir": [kt for kt in vekil.KATMAN if vekil.hazir(p.work, f, kt)]})
    rapor = hizli._json_oku(p.work / "renders" / "kalite.json")
    if rapor and (not son or rapor.get("dosya") != son.name):
        rapor = None  # son teslimle eşleşmeyen rapor gösterilmez
    k_coz, k_fps = hizli.kaynaga_esle(p) if tam else (None, None)
    return {"secenekler": teslim.secenekler(), "sekans": {"w": k.w, "h": k.h, "fps": k.fps} if k else None,
            "vekil": vekiller, "rapor": rapor, "kaynak_esle": {"cozunurluk": k_coz, "fps": k_fps},
            "kaynak_kisa": max(kisa) if kisa else None, "platform": hizli.PLATFORM.get(p.studyo), "son": olcum,
            # Export'u durduracak kurgu hataları: final'in kurgu.hazirla içinde çalıştırdığı aynı denetim
            "hatalar": kurgu.denetle(p, tam) if tam else []}


class KaynakIstek(BaseModel):
    yol: str


class KlipIstek(BaseModel):
    klip: str


class AyristirIstek(BaseModel):
    yol: str
    stem: int = 2


class PanoIstek(BaseModel):
    dosya: str
    sure: float = 8.0


class SablonIstek(BaseModel):
    ad: str
    param: dict = {}
    tema: str | None = None
    w: int = 1080
    h: int = 1920


def _kaynak(p: hizli.Proje, yol: str) -> Path:
    try:
        f = kurgu.dosya(p, yol)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    if not f.is_file():
        raise HTTPException(404, "Dosya yok")
    return f


def _onizleme_temasi(p: hizli.Proje, k: Kurgu) -> None:
    """HyperFrames önizlemesinin tema.css'i (work/public/hf/tema.css, /pub/ altından); render hf_kurgu.hazirla ile aynı."""
    from .. import hf_kurgu
    f = p.work / "public" / "hf" / "tema.css"
    try:
        css = hf_kurgu.tema_css(kurgu.etkin_tema(p, k.motion_tema))
        if not f.exists() or f.read_text(encoding="utf-8") != css:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(css, encoding="utf-8")
    except Exception as e:  # noqa: BLE001  WHY: tema yazılamazsa önizleme varsayılan renklerle sürer, kurgu açılmalı
        print(f"önizleme teması yazılamadı: {e}", flush=True)


def create_app(token: str, *, izinli_hostlar: set[str] | None = None) -> FastAPI:
    app = FastAPI(title="Video Stüdyo", docs_url=None, redoc_url=None, openapi_url=None)
    hostlar = izinli_hostlar or set()

    @app.middleware("http")
    async def guvenlik(request: Request, cagri):
        host = request.headers.get("host", "")
        if hostlar and host not in hostlar:
            return JSONResponse({"detail": "Host reddedildi"}, 403)
        origin = request.headers.get("origin")
        if origin and origin not in {f"http://{h}" for h in hostlar}:
            return JSONResponse({"detail": "Origin reddedildi"}, 403)
        yol = request.url.path
        if yol == "/" and secrets.compare_digest(request.query_params.get("token", ""), token):
            r = RedirectResponse("/", 303)
            r.set_cookie("studio", token, httponly=True, samesite="strict")
            return r
        if not secrets.compare_digest(request.cookies.get("studio", ""), token):
            return JSONResponse({"detail": "Yetkisiz"}, 401)
        if request.method not in ("GET", "HEAD") and not origin:
            return JSONResponse({"detail": "Origin gerekli"}, 403)
        return await cagri(request)

    app.include_router(medya.router)
    app.include_router(kutuphane.router)
    app.include_router(isler.router)
    app.include_router(ajan.router)
    app.include_router(stil_api.router)
    app.include_router(galeri_api.router)
    app.include_router(ekip_api.router)
    app.include_router(kurallar_api.router)

    @app.get("/api/hf/onizleme")
    def hf_onizleme():
        """Önizleme derleyicisinin girdisi (ADR 0051, 0062): native bileşenler, canlı HF grafikleri ve hız kapısı."""
        from .. import hf_grafik, hf_kurgu
        return {"native": hf_kurgu.native_harita(), "grafikler": hf_grafik.grafik_harita(),
                "oto_hf": bool(hf_kurgu.ayar().get("oto_hf"))}

    @app.get("/hfs/{dizin}/{kok}/{boyut}.html")
    def hf_sahne(dizin: str, kok: str, boyut: str):
        """Native sahnenin bir bağlama kopyası; önizleme alt kompozisyonu buradan yükler (render'da cli.ts hf/n/ yazar)."""
        from .. import hf_kurgu
        m = re.fullmatch(r"(\d{2,5})x(\d{2,5})", boyut)
        if not m or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", kok) or not re.fullmatch(r"[a-z0-9-]{1,80}", dizin):
            raise HTTPException(400, "Geçersiz sahne adresi")
        html = hf_kurgu.sahne_kopyasi(dizin, kok, int(m[1]), int(m[2]))
        if html is None:
            raise HTTPException(404, "Sahne yok")
        return HTMLResponse(html, headers={"Cache-Control": "no-store"})

    @app.get("/hfg/{studyo}/{proje_ad}/{ad}/{kok}/{boyut}.html")
    def hf_grafik_sahne(studyo: str, proje_ad: str, ad: str, kok: str, boyut: str):
        """Canlı HF grafik kompozisyonunun bağlama kopyası (ADR 0062); Stüdyo WebM'siz önizler."""
        from .. import hf_grafik
        m = re.fullmatch(r"(\d{2,5})x(\d{2,5})", boyut)
        if not m or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", kok) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", ad):
            raise HTTPException(400, "Geçersiz grafik adresi")
        p = proje(studyo, proje_ad)
        html = hf_grafik.grafik_kopyasi(ad, kok, int(m[1]), int(m[2]), p.work)
        if html is None:
            raise HTTPException(404, "Grafik yok")
        return HTMLResponse(html, headers={"Cache-Control": "no-store"})

    @app.get("/api/hf/durum")
    def hf_durum():
        """HyperFrames sürümü ve son güncelleme denemesi (ADR 0051); Stüdyo rozeti okur."""
        from .. import hf_guncel
        return hf_guncel.durum_oku() | {"mevcut": hf_guncel.hf.surum()}

    @app.get("/api/kurgu/{studyo}/{ad}")
    def kurgu_oku(studyo: str, ad: str):
        p = proje(studyo, ad)
        if not kurgu.yol(p.work).exists():
            raise HTTPException(404, "Kurgu yok")
        try:
            k = kurgu.oku(p.work)
        except ValueError as e:  # WHY: terminalden elle yazılan kurgu bozuk olabilir, sunucu düşmemeli
            raise HTTPException(422, f"kurgu.json geçersiz: {e}") from e
        hizli._public_hazirla(p)
        _onizleme_temasi(p, k)
        return {"kurgu": k.model_dump(), "medya": medya_eslemesi(p, k), "etag": kurgu.etag(p.work), "tema": kurgu.tema_tokeni(p, k),
                "bolgeler": kurgu.yuz_bolgeleri(p, k)}

    @app.put("/api/kurgu/{studyo}/{ad}")
    async def kurgu_yaz(studyo: str, ad: str, request: Request):
        p = proje(studyo, ad)
        try:
            k = Kurgu.model_validate_json(await request.body())
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
        # WHY: terminal agent dosyayı rev artırmadan yazabilir; içerik özeti bu yazımı da yakalar.
        if request.headers.get("if-match") != kurgu.etag(p.work):
            raise HTTPException(409, "kurgu.json başka bir yerden değişti")
        k = kurgu.yaz(p.work, k)
        return {"rev": k.rev, "etag": kurgu.etag(p.work)}

    # WHY: bkz. wiki/decisions/0028-ai-edit.md. AI edit'in önce/sonra kartı ve geri alma; önceki sürüm kurgu-gecmis/ altındadır.
    @app.get("/api/kurgu/{studyo}/{ad}/ai-ozet")
    def ai_ozet(studyo: str, ad: str):
        p = proje(studyo, ad)
        f, rapor = p.work / "edit" / "ai-edit.ozet.json", p.work / "edit" / "ai-edit.rapor.md"
        if not f.exists():
            return None
        try:
            o = json.loads(f.read_text(encoding="utf-8"))
            int(o["once_rev"])
        except (ValueError, KeyError, TypeError):  # elle bozulmuş özet: kart görünmez, panel çalışır
            return None
        o["rapor"] = rapor.read_text(encoding="utf-8", errors="replace").splitlines()[:40] if rapor.exists() else []
        o["geri_alinabilir"] = (p.work / "edit" / "kurgu-gecmis" / f"{int(o['once_rev']):06}.json").exists()
        return o

    @app.post("/api/kurgu/{studyo}/{ad}/geri/{rev}")
    def kurgu_geri(studyo: str, ad: str, rev: int):
        p = proje(studyo, ad)
        f = p.work / "edit" / "kurgu-gecmis" / f"{rev:06}.json"
        if not f.exists():
            raise HTTPException(404, "Bu sürüm geçmişte yok")
        try:
            k = kurgu.yaz(p.work, Kurgu.model_validate_json(f.read_text(encoding="utf-8")))  # şimdiki sürüm de geçmişe girer
        except ValueError as e:
            raise HTTPException(422, f"Geçmiş sürüm geçersiz: {e}") from e
        return {"rev": k.rev, "etag": kurgu.etag(p.work)}

    @app.get("/api/kurgu/{studyo}/{ad}/izle")
    async def kurgu_izle(studyo: str, ad: str):
        p = proje(studyo, ad)

        async def uret():
            son = kurgu.etag(p.work)
            while True:
                await asyncio.sleep(0.7)
                simdi = kurgu.etag(p.work)
                if simdi != son:
                    son = simdi
                    yield f"data: {simdi}\n\n"
                else:
                    yield ": canli\n\n"
        return StreamingResponse(uret(), media_type="text/event-stream", headers={"Cache-Control": "no-store"})

    @app.post("/api/kaynak/{studyo}/{ad}")
    def kaynak_bilgi(studyo: str, ad: str, g: KaynakIstek):
        """Timeline'a eklenecek kaynak: ölçü, varsa transkript, önizleme adresi."""
        p = proje(studyo, ad)
        try:
            f = kurgu.dosya(p, g.yol)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        if not f.is_file():
            raise HTTPException(404, "Dosya yok")
        gorsel = f.suffix.lower() in hizli.GORSEL
        i = ff.probe(f)
        v = i.get("video") or {}
        kok, _, ic = g.yol.partition(":")
        return {"sure": 0 if gorsel else i.get("duration") or 0, "w": v.get("width"), "h": v.get("height"), "ses": bool(i.get("audio")),
                "kelimeler": kurgu.kaynak_kelimeleri(p, f), "url": f"/dosya/{p.studyo}/{p.ad}/{kok}/{quote(ic)}"}

    # WHY: bkz. wiki/decisions/0024-oneri-araclari.md. Öneri ve reframe kaydedilmiş kurgudan hesaplanır, kurguya yazmaz;
    # uygulama arayüzde geri alınabilir düzenlemedir.
    @app.get("/api/oneri/{studyo}/{ad}")
    def oneri(studyo: str, ad: str):
        from .. import sessizlik
        p = proje(studyo, ad)
        return {"oneriler": sessizlik.oneriler(p, kurgu_al(p))}

    @app.post("/api/reframe/{studyo}/{ad}")
    def reframe(studyo: str, ad: str, g: KlipIstek):
        from .. import kurgu_reframe
        p = proje(studyo, ad)
        try:
            return kurgu_reframe.donus_hesapla(p, kurgu_al(p), g.klip)
        except (ValueError, KeyError) as e:
            raise HTTPException(400, str(e)) from e

    # WHY: bkz. wiki/decisions/0034-ses-araclari.md. Ayırma uzun sürer (CPU'da sesin ~2,5 katı): önbellekte yoksa iş kuyruğuna girer.
    def _stemler(p, yol: str, stem: int) -> dict | None:
        f = kurgu.dosya(p, isler.ses_yolu(p, yol))
        yollar = ayristir.onbellekte(f, p.work / "public" / "ayrisan", stem)
        if not yollar:
            return None
        out = {}
        for ad, y in yollar.items():
            ic = y.relative_to(p.work / "public").as_posix()
            out[ad] = {"id": f"{f.stem}_{ad}", "yol": f"public:{ic}", "sure": ff.probe(y)["duration"], "url": f"/dosya/{p.studyo}/{p.ad}/public/{quote(ic)}"}
        return out

    @app.get("/api/ayristir/{studyo}/{ad}")
    def ayristir_durum(studyo: str, ad: str, yol: str, stem: int = 2):
        if stem not in ayristir.KIPLER:
            raise HTTPException(400, "Stem 2 ya da 4")
        s = _stemler(proje(studyo, ad), yol, stem)
        return {"hazir": True, "stemler": s} if s else {"hazir": False}

    @app.post("/api/ayristir/{studyo}/{ad}")
    def ayristir_(studyo: str, ad: str, g: AyristirIstek):
        p = proje(studyo, ad)
        if g.stem not in ayristir.KIPLER:
            raise HTTPException(400, "Stem 2 ya da 4")
        if (s := _stemler(p, g.yol, g.stem)):
            return {"hazir": True, "stemler": s}
        if not ayristir.hazir():
            raise HTTPException(503, ayristir.kurulum_komutu())
        i = isler.Istek(komut="ayristir", studyo=studyo, ad=ad, yol=g.yol, stem=g.stem)
        return {"hazir": False, "is": isler._k().ekle("ayristir", f"ayristir · {studyo}/{ad} · {g.yol}", isler.arguman(i)).id}

    @app.post("/api/disa/{studyo}/{ad}")
    def disa_aktar(studyo: str, ad: str):
        from .. import disa
        p = proje(studyo, ad)
        k = kurgu_al(p)
        return {"dosyalar": [paths.rel(f) for f in disa.yaz(p, k, p.cikti)], "uyarilar": disa.yer_tutucular(k)}

    @app.get("/api/ses/{studyo}/{ad}")
    def ses_durumu(studyo: str, ad: str):
        """Son ölçülmüş miks. Tahmin yok (ADR 0016): ölçüm yoksa boş, kurgudan eskiyse işaretli."""
        p = proje(studyo, ad)
        return ses_ozeti(p)

    @app.get("/api/teslim/{studyo}/{ad}")
    def teslim_durumu(studyo: str, ad: str):
        return teslim_ozeti(proje(studyo, ad))

    @app.get("/api/yayin/{studyo}/{ad}")
    def yayin_durumu(studyo: str, ad: str):
        """Yayın metni paneli (ADR 0055): reçete sınırları, stüdyo varsayılanı, teslim videoları ve paketleri."""
        from .. import yayin
        return yayin.ozet(proje(studyo, ad))

    @app.put("/api/yayin/{studyo}/{ad}/{video}")
    def yayin_kaydet(studyo: str, ad: str, video: str, g: dict = Body(...)):
        """Elle düzenlenen paket: doğrulanır, JSON ve yayin.md'ye yazılır. Ajan çağrılmaz."""
        from .. import yayin
        try:
            veri, uyarilar = yayin.kaydet(proje(studyo, ad), video, g)
        except SystemExit as e:
            raise HTTPException(422, str(e)) from e
        return {"paket": veri, "uyarilar": uyarilar}

    @app.get("/api/indir/{studyo}/{ad}")
    def indir(studyo: str, ad: str, yol: str):
        """Teslim dosyasını ek olarak verir (Content-Disposition: attachment). Yalnız çıktılar kökü, work hariç."""
        p = proje(studyo, ad)
        f = kok_ici(p.cikti, yol)
        if not f.is_file() or (p.work in f.parents):
            raise HTTPException(404, "Dosya yok")
        return FileResponse(f, filename=f.name, headers={"X-Content-Type-Options": "nosniff"})

    @app.get("/api/denetim/{studyo}/{ad}")
    def denetim_durumu(studyo: str, ad: str):
        return denetim_ozeti(proje(studyo, ad))

    @app.post("/api/denetim/{studyo}/{ad}/onay")
    def denetim_onay(studyo: str, ad: str):
        """YAYINLANAMAZ hükmüne rağmen teslim: kullanıcı kararı kayda geçer."""
        p = proje(studyo, ad)
        o = denetim_ozeti(p)
        if not o["video"]:
            raise HTTPException(404, "Denetlenmiş video yok")
        (p.work / "qa" / "onay.json").write_text(json.dumps({"video": o["video"], "hukum": o["hukum"], "zaman": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False), encoding="utf-8")
        return denetim_ozeti(p)

    @app.post("/api/public-bagla/{studyo}/{ad}")
    def public_bagla(studyo: str, ad: str, g: KaynakIstek):
        """Sahne görseli: girdi görselini work/public/shot altına bağlar; sahne staticFile ile okur."""
        p = proje(studyo, ad)
        f = _kaynak(p, g.yol)
        if f.suffix.lower() not in hizli.GORSEL:
            raise HTTPException(415, "Yalnız görsel")
        return kurgu.shot_bagla(p, f)

    @app.post("/api/motion-sablon/{studyo}/{ad}")
    def motion_sablon(studyo: str, ad: str, g: SablonIstek):
        """Motion şablonunu parametreyle üretir (özetle önbellekte); timeline'a kaynak olarak eklenir. ADR 0036."""
        p = proje(studyo, ad)
        sablonlar = motion.sablonlar()
        if g.ad not in sablonlar:
            raise HTTPException(404, "Böyle bir motion şablonu yok")
        if hatalar := motion.param_hatalari(sablonlar[g.ad], g.param):
            raise HTTPException(422, "; ".join(hatalar))
        if g.tema and g.tema != kurgu.PROJE_TEMASI and not motion.tema_yolu(g.tema):
            raise HTTPException(422, "Bilinmeyen tema")
        if not (240 <= g.w <= 3840 and 240 <= g.h <= 3840):
            raise HTTPException(422, "Sekans boyutu geçersiz")
        # "varsayilan" ya da boş tema otomatiktir: seçili stilin ya da projenin teması (ADR 0042)
        f, bilgi = motion.sablon_uret(g.ad, g.param, kurgu.etkin_tema(p, g.tema), p.work / "public" / "motion", sekans=(g.w, g.h))
        return {"yol": f"public:motion/{f.name}", **bilgi}

    @app.post("/api/pano/{studyo}/{ad}")
    def pano(studyo: str, ad: str, g: PanoIstek):
        """Panoyu mp4'e çevirir; aynı pano ve süre önbellekten gelir. Pano 1920x1080 sabit tasarlandı."""
        p = proje(studyo, ad)
        html = kok_ici(paths.LIBRARY / "boards" / "boards", g.dosya)
        sure = round(float(g.sure), 2)
        if not 0.5 <= sure <= 120:
            raise HTTPException(422, "Süre 0,5 ile 120 sn arasında olmalı")
        ic = f"pano/{html.stem}-{sure:g}s.mp4"
        hedef = p.work / "public" / ic
        if hedef.exists():
            return {"hazir": True, "yol": f"public:{ic}"}
        hedef.parent.mkdir(parents=True, exist_ok=True)
        is_ = isler._k().ekle("pano", f"pano · {html.stem}", ["pano", str(html), "--sure", f"{sure:g}", "-o", str(hedef)])
        return {"hazir": False, "yol": f"public:{ic}", "is": is_.id}

    @app.get("/api/peak/{studyo}/{ad}")
    def peak(studyo: str, ad: str, yol: str):
        p = proje(studyo, ad)
        return FileResponse(gorsel.peak(p, _kaynak(p, yol)), media_type="application/json", headers={"Cache-Control": "no-store"})

    @app.get("/api/serit/{studyo}/{ad}")
    def serit(studyo: str, ad: str, yol: str):
        p = proje(studyo, ad)
        return gorsel.serit(p, _kaynak(p, yol))

    @app.post("/api/kurgu/{studyo}/{ad}/icerial")
    def icerial(studyo: str, ad: str):
        p = proje(studyo, ad)
        if kurgu.yol(p.work).exists():
            raise HTTPException(409, "Kurgu zaten var")
        try:
            kurgu.yaz(p.work, kurgu.eski_projeden(p) if (p.work / "edit" / "props.json").exists() else kurgu.bos(p.studyo))
        except SystemExit as e:  # WHY: hat hataları SystemExit atar; sunucuyu düşürmemeli
            raise HTTPException(422, str(e)) from e
        return {"tamam": True}

    @app.get("/dosya/{studyo}/{ad}/{kok}/{ic:path}")
    def dosya(studyo: str, ad: str, kok: str, ic: str):
        p = proje(studyo, ad)
        koks = {
            "public": p.work / "public",
            "inputs": p.girdi,
            "outputs": p.cikti,
            "library": paths.LIBRARY,
            "proxy": p.work / "proxy",
            "stil": paths.STUDIOS,
        }
        if kok not in koks:
            raise HTTPException(404, "Kök yok")
        if kok == "stil":
            if ".." in Path(ic.replace("\\", "/")).parts:
                raise HTTPException(404, "Dosya yok")
            try:
                hedef = kurgu.dosya(p, f"stil:{ic}")
                if hedef.is_file():
                    rel = hedef.relative_to(paths.STUDIOS.resolve()).as_posix()
                    return FileResponse(kok_ici(koks[kok], rel), headers=GUVENLI)
            except ValueError:
                pass
        return FileResponse(kok_ici(koks[kok], ic), headers=GUVENLI)

    # Remotion staticFile: window.remotion_staticBase = /pub/<stüdyo>/<ad>
    @app.get("/pub/{studyo}/{ad}/{ic:path}")
    def pub(studyo: str, ad: str, ic: str):
        return FileResponse(kok_ici(proje(studyo, ad).work / "public", ic), headers=GUVENLI)

    @app.get("/{yol:path}")
    def web(yol: str):
        if not DIST.exists():
            raise HTTPException(503, "Arayüz derlenmemiş: cd studio && npm run build")
        f = (DIST / yol).resolve()
        if yol and f.is_relative_to(DIST.resolve()) and f.is_file():
            # WHY: assets/ adları içerik özetli; değişen dosya yeni ad alır, tarayıcı eskisini yeniden istemez (ADR 0050).
            ust = {"Cache-Control": "public, max-age=31536000, immutable"} if yol.startswith("assets/") else None
            return FileResponse(f, headers=ust)
        if yol.startswith("assets/"):
            # WHY: yeniden derleme sonrası eski parça istenirse index.html (200, text/html) dönmesin; tembel panel 404 görür
            raise HTTPException(404, "Arayüz güncellendi, sayfayı yenile")
        if yol.startswith(("api/", "dosya/", "pub/")):
            # WHY: kaldırılan ya da yanlış yazılan uç (ör. /api/kapak, ADR 0056) HTML ile 200 dönüp JSON ayrıştırmasını bozmasın
            raise HTTPException(404, "Böyle bir uç yok")
        return FileResponse(DIST / "index.html", headers={"Cache-Control": "no-store"})

    return app


def calistir(*, port: int = 8765, ac: bool = True) -> None:
    """Eski giriş noktası; başlatıcı pencereyi importtan önce açar (ADR 0050)."""
    from .baslat import calistir as _calistir
    _calistir(port=port, ac=ac)
