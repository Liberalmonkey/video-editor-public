"""HyperFrames sürekli güncelleme: kontrol, aday kurulumu, duman testi, sabitleme, geri alma.

WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Kullanıcı HyperFrames güncellemelerinin repodan sürekli
alınmasını istedi; kararı "otomatik + duman testi + geri alma". Yeni sürüm önce `work/hf-aday/<sürüm>/` altında kurulur
ve `tests/hf_duman/` ile denenir; yalnız geçerse repo kökündeki sabit sürüm değişir. Kalırsa eski sürüm kalır.

Durum dosyası `work/hf-aday/durum.json`: mevcut, en yeni, son kontrol, son deneme ve sonucu. Stüdyo `/api/hf/durum` ile
okur.

Zamanlama: haftada bir, Cuma 13:00 (yerel saat). Stüdyo açıkken her 10 dakikada pencerenin gelip gelmediğine bakar;
pencere kaçırıldıysa (Stüdyo kapalıydı) ilk boş anda çalışır. Çalışan bir edit/render varken (Stüdyo kuyruğu ya da
terminalden `vedit`, ffmpeg, HyperFrames/Remotion) güncelleme ertelenir; kök sürüm değişirken `kuruluyor.kilit` yazılır,
Stüdyo kuyruğu kilit kalkana kadar yeni iş başlatmaz. WHY: 2026-11-23'te günlük güncelleme, ekip edit'inin taslak
render'ı sürerken node_modules'u değiştirdi ve işi düşürdü.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

from . import ff, hf, hf_grafik, paths

ADAY = paths.ROOT / "work" / "hf-aday"
DURUM = ADAY / "durum.json"
ONCEKI = ADAY / "onceki.json"
DUMAN = paths.ROOT / "tests" / "hf_duman"
PAKET = paths.ROOT / "package.json"
SKILLER = ("hyperframes", "hyperframes-cli", "hyperframes-registry", "remotion-to-hyperframes")
HAFTA_GUNU, SAAT, DAKIKA = 4, 13, 0  # Cuma 13:00 (Pazartesi = 0)
YOKLAMA = 600  # Stüdyo zamanlayıcısının bakma aralığı, saniye
BEKLE_SINIR = 4 * 3600  # sabitlemeden önce boş anı en çok bu kadar bekler
KILIT = ADAY / "kuruluyor.kilit"  # kök sürüm değişirken: Stüdyo kuyruğu yeni iş başlatmaz
DENEME = ADAY / "deneme.kilit"  # bir aday denemesi sürerken: ikinci deneme başlamaz
FARK_ESIGI = 8.0  # 0-255 ortalama mutlak piksel farkı; yazı tipi yumuşatması 2-3 civarı oynar
SESSIZ = {"HYPERFRAMES_NO_TELEMETRY": "1", "DO_NOT_TRACK": "1", "HYPERFRAMES_SKIP_SKILLS": "1",
          "HYPERFRAMES_NO_UPDATE_CHECK": "1", "DISABLE_TELEMETRY": "1"}


def _npm() -> str:
    return shutil.which("npm") or "npm"


def _npx() -> str:
    return shutil.which("npx") or "npx"


def _calis(komut: list[str], cwd: Path, zaman: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run(komut, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=zaman, env={**os.environ, **SESSIZ}, shell=os.name == "nt")


def _surum_anahtari(v: str) -> tuple:
    return tuple(int(x) if x.isdigit() else x for x in v.replace("-", ".").split("."))


def durum_oku() -> dict:
    try:
        return json.loads(DURUM.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _durum_yaz(**alan) -> dict:
    d = {**durum_oku(), **alan, "mevcut": hf.surum()}
    if d.get("en_yeni"):  # sabitleme ya da geri almadan sonra bayat kalmasın
        d["yeni_var"] = _surum_anahtari(d["en_yeni"]) > _surum_anahtari(d["mevcut"])
    ADAY.mkdir(parents=True, exist_ok=True)
    DURUM.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


def en_yeni() -> str:
    r = _calis([_npm(), "view", "hyperframes", "version"], paths.ROOT, zaman=60)
    v = r.stdout.strip().splitlines()[-1].strip() if r.returncode == 0 and r.stdout.strip() else ""
    if not v:
        raise RuntimeError(f"npm view başarısız: {(r.stderr or r.stdout)[-300:]}")
    return v


def son_pencere(simdi: datetime | None = None) -> datetime:
    """`simdi`den önceki (ya da ona eşit) en son Cuma 13:00."""
    simdi = simdi or datetime.now()
    p = simdi.replace(hour=SAAT, minute=DAKIKA, second=0, microsecond=0) - timedelta(days=(simdi.weekday() - HAFTA_GUNU) % 7)
    return p if p <= simdi else p - timedelta(days=7)


def sonraki_pencere(simdi: datetime | None = None) -> datetime:
    return son_pencere(simdi) + timedelta(days=7)


def vakti_geldi(d: dict | None = None, simdi: datetime | None = None) -> bool:
    """Son kontrol en son Cuma 13:00 penceresinden önceyse sıra gelmiştir."""
    d = durum_oku() if d is None else d
    return d.get("son_kontrol_ts", 0) < son_pencere(simdi).timestamp()


def _surecler() -> list[tuple[int, str, str]]:
    """(pid, ad, komut satırı) listesi. Windows'ta CIM, diğerinde ps."""
    if os.name == "nt":
        ps = ("Get-CimInstance Win32_Process -Filter \"Name='python.exe' or Name='vedit.exe' or Name='node.exe' "
              "or Name='ffmpeg.exe'\" | ForEach-Object { \"$($_.ProcessId)`t$($_.Name)`t$($_.CommandLine)\" }")
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
        satirlar = r.stdout.splitlines()
    else:
        r = subprocess.run(["ps", "-eo", "pid=,comm=,args="], capture_output=True, text=True, timeout=60)
        satirlar = ["\t".join(x.strip().split(None, 2)) for x in r.stdout.splitlines() if x.strip()]
    out = []
    for x in satirlar:
        parca = x.split("\t", 2)
        if len(parca) == 3 and parca[0].strip().isdigit():
            out.append((int(parca[0]), parca[1].strip().lower(), parca[2]))
    return out


def _is_sureci_mi(ad: str, komut: str) -> bool:
    k = komut.lower().replace("\\", "/")
    if "ffmpeg" in ad:
        return True
    if "node" in ad:
        return "hyperframes" in k or "remotion" in k
    if "vedit" not in k:
        return False
    # Stüdyo sunucusunun kendisi ve güncelleme komutu iş sayılmaz
    return not any(x in k for x in ("vedit.studio", "vedit studio", "vedit.exe studio", "vedit.exe\" studio", "hf-guncelle"))


def mesgul() -> list[str]:
    """Çalışan edit/render işleri (kısa açıklama). Boş liste: güncelleme güvenli."""
    neden = []
    try:
        from .studio import isler  # WHY: Stüdyo içinden çağrıldığında kuyruktaki iş de sayılır
        for q in (isler.kuyruk, isler.ajan):
            neden += [f"Stüdyo işi: {i.baslik}" for i in (q.isler if q else []) if i.durum in ("sirada", "calisiyor")]
    except Exception:
        pass
    try:
        ben = os.getpid()
        neden += [f"{ad} {pid}" for pid, ad, komut in _surecler() if pid != ben and _is_sureci_mi(ad, komut)]
    except (OSError, subprocess.SubprocessError):
        pass
    return neden


def _bosta_bekle(sinir: float) -> list[str]:
    """Çalışan iş bitene kadar bekler. Dönüş: süre dolduysa hâlâ çalışanlar, boşsa []."""
    son = time.time() + sinir
    while True:
        m = mesgul()
        if not m or time.time() >= son:
            return m
        _durum_yaz(bekliyor=f"çalışan iş bitince: {', '.join(m[:3])}")
        time.sleep(60)


def kontrol(*, zorla: bool = False) -> dict:
    """Yeni sürüm var mı. Ağ ister; `zorla` yoksa haftada bir (Cuma 13:00 penceresi) sorar."""
    d = durum_oku()
    if not zorla and not vakti_geldi(d):
        return _durum_yaz(sonraki=sonraki_pencere().isoformat(timespec="minutes"))
    try:
        v = en_yeni()
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as e:
        return _durum_yaz(son_kontrol_ts=time.time(), hata=str(e)[:300])
    return _durum_yaz(en_yeni=v, son_kontrol_ts=time.time(), son_kontrol=datetime.now().isoformat(timespec="seconds"),
                      sonraki=sonraki_pencere().isoformat(timespec="minutes"), bekliyor=None,
                      yeni_var=_surum_anahtari(v) > _surum_anahtari(hf.surum()), hata=None)


# ---------------------------------------------------------------- duman testi

def _ornek_video(hedef: Path) -> None:
    ff.ffmpeg("-f", "lavfi", "-i", "testsrc2=size=960x540:rate=30:duration=4", "-c:v", "libx264", "-pix_fmt", "yuv420p",
              "-g", "30", str(hedef))


def _kare(video: Path, t: float, hedef: Path) -> None:
    kod = ["-c:v", "libvpx-vp9"] if video.suffix == ".webm" else []
    ff.ffmpeg(*kod, "-ss", f"{t}", "-i", str(video), "-frames:v", "1", str(hedef))


def _fark(a: Path, b: Path) -> float:
    from PIL import Image, ImageChops, ImageStat
    x, y = Image.open(a).convert("RGBA"), Image.open(b).convert("RGBA")
    if x.size != y.size:
        return 255.0
    return sum(ImageStat.Stat(ImageChops.difference(x, y)).mean) / 4


def duman(kok: Path | None = None, *, cikti: Path | None = None) -> list[dict]:
    """Duman paketini `kok` altındaki HyperFrames ile koşar (None: sabit kurulum). Her kompozisyon için sonuç."""
    cikti = cikti or ADAY / "duman"
    sonuclar = []
    # WHY: aday kökü os.environ yerine yalnız duman alt çağrılarına iletilir; eşzamanlı Stüdyo işleri sabit kurulumu korur.
    for d in sorted(p for p in DUMAN.iterdir() if (p / "index.html").is_file()):
        s = {"ad": d.name, "gecti": False, "sorun": []}
        kopya = cikti / d.name
        try:
            hf_grafik._hazirla(d, kopya, "varsayilan")
            if d.name == "video-gsap":
                _ornek_video(kopya / "klip.mp4")
            lint = hf.lint(kopya, kok=kok)
            if lint.get("errorCount") or lint.get("errors"):
                s["sorun"].append(f"lint: {lint.get('errorCount') or lint.get('errors')} hata")
            olcu = hf_grafik.olcu(d)
            saydam = "background: none" in (d / "index.html").read_text(encoding="utf-8")
            video = cikti / f"{d.name}.{'webm' if saydam else 'mp4'}"
            if saydam:
                hf.render_saydam(kopya, video, degiskenler={"baslik": "Duman"}, kok=kok)
            else:
                hf.render(kopya, video, quality="draft", kok=kok)
            b = ff.probe(video)
            v = b.get("video") or {}
            if (v.get("width"), v.get("height")) != (olcu["w"], olcu["h"]):
                s["sorun"].append(f"boyut {v.get('width')}x{v.get('height')}, beklenen {olcu['w']}x{olcu['h']}")
            if abs(b["duration"] - olcu["sure"]) > 0.15:
                s["sorun"].append(f"süre {b['duration']}, beklenen {olcu['sure']}")
            kare, altin = cikti / f"{d.name}.png", d / "altin.png"
            _kare(video, 1.0, kare)
            if altin.exists():
                s["fark"] = round(_fark(kare, altin), 2)
                if s["fark"] > FARK_ESIGI:
                    s["sorun"].append(f"altın kareden fark {s['fark']} > {FARK_ESIGI}")
            elif not s["sorun"]:
                shutil.copy2(kare, altin)  # ilk geçen sürüm altını yazar
                s["altin_yazildi"] = True
        except Exception as e:  # WHY: bir kompozisyonun çökmesi raporda görünsün, paket sürsün
            s["sorun"].append(f"{type(e).__name__}: {str(e)[-300:]}")
        s["gecti"] = not s["sorun"]
        sonuclar.append(s)
    return sonuclar


# ---------------------------------------------------------------- kurulum

def _aday_kur(v: str) -> Path:
    kok = ADAY / v
    kok.mkdir(parents=True, exist_ok=True)
    (kok / "package.json").write_text(json.dumps({"name": "hf-aday", "private": True}), encoding="utf-8")
    r = _calis([_npm(), "install", f"hyperframes@{v}", "--no-audit", "--no-fund", "--save-exact"], kok)
    if r.returncode:
        raise RuntimeError(f"aday npm install başarısız:\n{(r.stderr or r.stdout)[-800:]}")
    return kok


def _skilleri_guncelle(v: str) -> list[str]:
    """Skill'leri geçici klasöre kurar, sonra projeye kopyalar; skills-lock.json girdileri taşınır."""
    gecici = ADAY / v / "skiller"
    shutil.rmtree(gecici, ignore_errors=True)
    gecici.mkdir(parents=True)
    komut = [_npx(), "--yes", "skills", "add", "heygen-com/hyperframes", *sum((["-s", s] for s in SKILLER), []),
             "-a", "claude-code", "--copy", "-y"]
    r = _calis(komut, gecici)
    if r.returncode:
        raise RuntimeError(f"skills add başarısız:\n{(r.stderr or r.stdout)[-800:]}")
    kurulan = []
    for ad in SKILLER:
        kaynak = gecici / ".claude" / "skills" / ad
        if kaynak.is_dir():
            hedef = paths.ROOT / ".claude" / "skills" / ad
            shutil.rmtree(hedef, ignore_errors=True)
            shutil.copytree(kaynak, hedef)
            kurulan.append(ad)
    try:
        yeni = json.loads((gecici / "skills-lock.json").read_text(encoding="utf-8"))["skills"]
        kilit_f = paths.ROOT / "skills-lock.json"
        kilit = json.loads(kilit_f.read_text(encoding="utf-8"))
        kilit["skills"].update({a: yeni[a] for a in SKILLER if a in yeni})
        kilit_f.write_text(json.dumps(kilit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError):
        pass
    subprocess.run([str(paths.ROOT / ".venv" / "Scripts" / "python.exe") if os.name == "nt" else "python",
                    str(paths.ROOT / "scripts" / "ajan_esitle.py")], cwd=paths.ROOT, capture_output=True)
    return kurulan


def _sabitle(v: str) -> None:
    """Repo kökünü `v`'ye geçirir: package.json + node_modules. Öncekini geri alma için saklar."""
    onceki = hf.surum()
    paket = json.loads(PAKET.read_text(encoding="utf-8"))
    paket.setdefault("devDependencies", {})["hyperframes"] = v
    PAKET.write_text(json.dumps(paket, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    r = _calis([_npm(), "install", "--no-audit", "--no-fund"], paths.ROOT)
    if r.returncode:
        paket["devDependencies"]["hyperframes"] = onceki
        PAKET.write_text(json.dumps(paket, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        _calis([_npm(), "install", "--no-audit", "--no-fund"], paths.ROOT)
        raise RuntimeError(f"kök npm install başarısız, {onceki} korundu:\n{(r.stderr or r.stdout)[-800:]}")
    ONCEKI.write_text(json.dumps({"surum": onceki, "ts": datetime.now().isoformat(timespec="seconds")}), encoding="utf-8")


def _log(satir: str) -> None:
    f = paths.ROOT / "wiki" / "log.md"
    try:
        f.write_text(f.read_text(encoding="utf-8").rstrip("\n") + "\n\n" + satir + "\n", encoding="utf-8")
    except OSError:
        pass


def kur(surum: str | None = None, *, skill: bool = True, bekle: float = BEKLE_SINIR) -> dict:
    """Aday sürümü kurar, duman testinden geçirir, geçerse sabitler. Rapor `work/hf-aday/<sürüm>/rapor.md`.

    Sabitlemeden önce çalışan iş bitene kadar en çok `bekle` saniye bekler; süre dolarsa sabitlemez ve son_deneme
    yazmaz, böylece sonraki yoklama yeniden dener."""
    # WHY: Stüdyo zamanlayıcısı ile Görev Zamanlayıcı aynı anda kurmasın (ikisi de Cuma 13:00)
    try:
        if time.time() - DENEME.stat().st_mtime < 6 * 3600:
            return _durum_yaz(bekliyor="başka bir güncelleme denemesi sürüyor")
    except OSError:
        pass
    DENEME.parent.mkdir(parents=True, exist_ok=True)
    DENEME.write_text(str(os.getpid()), encoding="utf-8")
    try:
        return _kur(surum, skill=skill, bekle=bekle)
    finally:
        DENEME.unlink(missing_ok=True)


def _kur(surum: str | None, *, skill: bool, bekle: float) -> dict:
    v = surum or kontrol(zorla=True).get("en_yeni")
    if not v:
        return _durum_yaz(son_deneme={"hata": "en yeni sürüm okunamadı"})
    if v == hf.surum() and not surum:
        return _durum_yaz(son_deneme={"surum": v, "gecti": True, "not": "zaten güncel"})
    rapor = ADAY / v / "rapor.md"
    try:
        kok = _aday_kur(v)
        sonuc = duman(kok, cikti=ADAY / v / "duman")
    except Exception as e:
        sonuc = [{"ad": "kurulum", "gecti": False, "sorun": [str(e)[-600:]]}]
    gecti = all(s["gecti"] for s in sonuc)
    satirlar = [f"# HyperFrames {v} aday denemesi ({datetime.now():%Y-%m-%d %H:%M})", "",
                f"Mevcut: {hf.surum()}. Sonuç: {'GEÇTİ' if gecti else 'KALDI'}.", ""]
    satirlar += [f"- {s['ad']}: {'tamam' if s['gecti'] else '; '.join(s['sorun'])}" + (f" (fark {s['fark']})" if "fark" in s else "")
                 for s in sonuc]
    kurulan = []
    if gecti:
        kalan = _bosta_bekle(bekle)
        if kalan:
            rapor.parent.mkdir(parents=True, exist_ok=True)
            rapor.write_text("\n".join(satirlar + ["", f"Ertelendi, çalışan iş: {', '.join(kalan[:3])}."]) + "\n", encoding="utf-8")
            return _durum_yaz(bekliyor=f"{v} duman testini geçti; çalışan iş bitince sabitlenecek: {', '.join(kalan[:3])}")
        try:
            KILIT.parent.mkdir(parents=True, exist_ok=True)
            KILIT.write_text(datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
            try:
                _sabitle(v)
                kurulan = _skilleri_guncelle(v) if skill else []
            finally:
                KILIT.unlink(missing_ok=True)
            satirlar += ["", f"Sabitlendi: {v}. Skill'ler: {', '.join(kurulan) or 'değişmedi'}."]
            _log(f"## [{datetime.now():%Y-%m-%d}] setup | HyperFrames {v}\n- `vedit hf-guncelle`: duman testi geçti, "
                 f"{ONCEKI.exists() and json.loads(ONCEKI.read_text(encoding='utf-8'))['surum']} → {v}. Rapor `work/hf-aday/{v}/rapor.md`.")
        except Exception as e:
            gecti = False
            satirlar += ["", f"Sabitleme başarısız: {e}"]
    rapor.parent.mkdir(parents=True, exist_ok=True)
    rapor.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    return _durum_yaz(bekliyor=None, son_deneme={"surum": v, "gecti": gecti, "rapor": paths.rel(rapor), "skiller": kurulan,
                                                 "zaman": datetime.now().isoformat(timespec="seconds")})


def geri() -> dict:
    """Bir önceki sabit sürüme döner (skill'ler aynı kalır; gerekirse `kur(surum=...)`)."""
    if not ONCEKI.exists():
        raise SystemExit("Önceki sürüm kaydı yok.")
    v = json.loads(ONCEKI.read_text(encoding="utf-8"))["surum"]
    _sabitle(v)
    return _durum_yaz(son_deneme={"surum": v, "gecti": True, "not": "geri alındı"})


def kilitli() -> bool:
    """Kök sürüm değişiyor mu. Bayat kilit (1 saatten eski, süreç çöktü) yok sayılır."""
    try:
        return time.time() - KILIT.stat().st_mtime < 3600
    except OSError:
        return False


def bir_tur() -> dict:
    """Zamanlayıcının bir yoklaması: pencere geldiyse ve iş yoksa kontrol; yeni sürüm denenmediyse aday denemesi."""
    d = durum_oku()
    if vakti_geldi(d):
        m = mesgul()
        if m:
            return _durum_yaz(bekliyor=f"haftalık kontrol, çalışan iş bitince: {', '.join(m[:3])}")
        d = kontrol(zorla=True)
    if d.get("yeni_var") and (d.get("son_deneme") or {}).get("surum") != d.get("en_yeni"):
        if mesgul():
            return d
        return kur()
    return d


def arka_plan() -> None:
    """Stüdyo açıkken döner: her `YOKLAMA` saniyede bir tur (haftada bir Cuma 13:00; iş varken ertelenir)."""
    while True:
        try:
            bir_tur()
        except Exception as e:  # WHY: zamanlayıcı ölmesin; hata durum dosyasında görünsün
            try:
                _durum_yaz(hata=str(e)[:300])
            except OSError:
                pass
        time.sleep(YOKLAMA)
