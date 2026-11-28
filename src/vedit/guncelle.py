"""Uygulama güncelleme: origin kontrolü, güvenli birleştirme, yedekleme ve geri alma.

WHY: bkz. wiki/decisions/0065-uygulama-guncelleme.md. Stüdyo içinden GitHub (origin) üzerindeki yeni commitleri
bildirir ve kullanıcının yerel verilerini (Projeler/, library/ değişiklikleri, studios/) ezmeden günceller.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from . import hf_guncel, paths

YOKLAMA = 1800  # arka plan kontrol aralığı: 30 dakika
FETCH_ZAMAN_ASIMI = 20  # git fetch zaman aşımı, saniye
_DURUM_BOS_YENI_SINIR = 20
# WHY: bkz. wiki/decisions/0065-uygulama-guncelleme.md. Sunucu modülü açılışta yükler; bu andan önce biten bir
# güncelleme yeni kodla zaten çalışıyordur, "Yeniden başlat" yeniden açılıştan sonra kalıcı görünmesin.
_SUREC_BASLANGIC = datetime.now().strftime("%Y%m%d-%H%M%S")


def _kok() -> Path:
    """Repo kökü; testlerde paths.ROOT yamalanabildiği için her çağrıda okunur."""
    return paths.ROOT


def _calisma() -> Path:
    return _kok() / "work" / "guncelleme"


def _durum_yolu() -> Path:
    return _calisma() / "durum.json"


def _kilit_yolu() -> Path:
    return _calisma() / "kilit"


def _git_var_mi() -> bool:
    return bool(shutil.which("git"))


def _git(args: list[str], *, zaman: int = 60, check: bool = False) -> subprocess.CompletedProcess:
    cmd = ["git", "-c", "core.quotepath=false", *args]
    return subprocess.run(
        cmd,
        cwd=_kok(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=zaman,
        check=check,
    )


def _git_bytes(args: list[str], *, zaman: int = 60) -> subprocess.CompletedProcess:
    cmd = ["git", "-c", "core.quotepath=false", *args]
    return subprocess.run(
        cmd,
        cwd=_kok(),
        capture_output=True,
        timeout=zaman,
    )


def _git_cikti(args: list[str], *, zaman: int = 30) -> str:
    r = _git(args, zaman=zaman)
    return r.stdout.strip() if r.returncode == 0 else ""


def _destek_var_mi() -> bool:
    if not _git_var_mi():
        return False
    kok = _kok()
    if not (kok / ".git").exists():
        return False
    r = _git(["rev-parse", "--is-inside-work-tree"], zaman=10)
    return r.returncode == 0 and r.stdout.strip().lower() == "true"


def _kilitli() -> bool:
    return _kilit_yolu().exists()


_MESGUL_ONBELLEK: tuple[float, list[str]] = (0.0, [])
_MESGUL_OMUR = 20.0  # sn; durum yoklaması her seferinde PowerShell süreç taraması açmasın


def _mesgul(taze: bool = False) -> list[str]:
    """Çalışan işleri döndürür; kendi sürecini, ebeveynini ve 'guncelle' komutlu vedit süreçlerini hariç tutar.

    Okuma yolları (durum yoklaması) 20 sn önbellek kullanır; kapılar `taze=True` ile her zaman yeniden tarar.
    """
    # WHY: bkz. wiki/decisions/0065-uygulama-guncelleme.md. Windows'ta süreç taraması PowerShell CIM'dir (1-2 sn);
    # arayüz güncelleme sürerken 3 sn'de bir yokladığı için tarama önbelleğe alınır.
    global _MESGUL_ONBELLEK
    zaman, deger = _MESGUL_ONBELLEK
    if not taze and time.monotonic() - zaman < _MESGUL_OMUR:
        return list(deger)
    sonuc = _mesgul_tara()
    _MESGUL_ONBELLEK = (time.monotonic(), sonuc)
    return list(sonuc)


def _mesgul_tara() -> list[str]:
    # WHY: bkz. wiki/decisions/0065-uygulama-guncelleme.md. hf_guncel._is_sureci_mi() değiştirilmeden burada süzgeçlenir.
    ham = list(hf_guncel.mesgul())
    if not ham:
        return []
    haric_pid = {os.getpid(), os.getppid()}
    surec_var = any(not x.startswith("Stüdyo işi:") and x.rsplit(" ", 1)[-1].isdigit() for x in ham)
    if surec_var:
        try:
            for pid, _ad, komut in hf_guncel._surecler():
                k = komut.lower().replace("\\", "/")
                if "vedit" in k and re.search(r"(?:^|\s|\"|')guncelle(?:\s|$)", k):
                    haric_pid.add(pid)
        except Exception:
            pass
    sonuc: list[str] = []
    for oge in ham:
        if not oge.startswith("Stüdyo işi:"):
            son = oge.rsplit(" ", 1)[-1]
            if son.isdigit() and int(son) in haric_pid:
                continue
        sonuc.append(oge)
    return sonuc


def _hedef_bul(dal: str) -> str:
    ref = _git_cikti(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"])
    if ref:
        return ref
    if dal and dal != "HEAD" and _git(["rev-parse", "--verify", "--quiet", f"origin/{dal}"]).returncode == 0:
        return f"origin/{dal}"
    for aday in ("origin/main", "origin/master"):
        if _git(["rev-parse", "--verify", "--quiet", aday]).returncode == 0:
            return aday
    return ""


def _kirli_dosyalar() -> list[str]:
    """Git status --porcelain -z -uall çıktısından work/guncelleme/ hariç yol listesi."""
    r = _git(["status", "--porcelain", "-z", "-uall"])
    if r.returncode != 0:
        return []
    parcalar = r.stdout.split("\0")
    yollar: list[str] = []
    i = 0
    while i < len(parcalar):
        kayit = parcalar[i]
        i += 1
        if not kayit or len(kayit) < 4:
            continue
        xy = kayit[:2]
        yol = kayit[3:]
        if xy[0] in ("R", "C"):
            i += 1  # rename/copy eski yol token'ını atla
        yol_norm = yol.replace("\\", "/").lstrip("./")
        if yol_norm == "work/guncelleme" or yol_norm.startswith("work/guncelleme/"):
            continue
        yollar.append(yol_norm)
    return yollar


def _yeni_commitler(hedef: str) -> list[dict]:
    if not hedef:
        return []
    r = _git(["log", f"-n{_DURUM_BOS_YENI_SINIR}", "--date=short", "--format=%h%x09%s%x09%ad", f"HEAD..{hedef}"])
    if r.returncode != 0:
        return []
    out: list[dict] = []
    for satir in r.stdout.splitlines():
        if not satir.strip():
            continue
        parca = satir.split("\t", 2)
        if len(parca) == 3:
            out.append({"kisa": parca[0], "baslik": parca[1], "tarih": parca[2]})
    return out


def _onbellek_oku() -> dict:
    try:
        veri = json.loads(_durum_yolu().read_text(encoding="utf-8"))
        return veri if isinstance(veri, dict) else {}
    except (OSError, ValueError):
        return {}


def _durum_yaz(veri: dict) -> dict:
    calisma = _calisma()
    calisma.mkdir(parents=True, exist_ok=True)
    _durum_yolu().write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    return veri


def _bos_durum(*, destek: bool, hata: str | None = None, onbellek: dict | None = None) -> dict:
    ob = onbellek or {}
    return {
        "destek": destek,
        "dal": "",
        "hedef": "",
        "mevcut": "",
        "uzak": "",
        "geride": 0,
        "ileride": 0,
        "yeni": [],
        "kirli": [],
        "mesgul": _mesgul(),
        "son_kontrol": ob.get("son_kontrol"),
        "hata": hata,
        "calisiyor": _kilitli(),
        "son_sonuc": ob.get("son_sonuc"),
    }


def _yerel_durum(*, son_kontrol: str | None, hata: str | None, son_sonuc: dict | None) -> dict:
    if not _destek_var_mi():
        return _bos_durum(destek=False, hata=hata, onbellek={"son_kontrol": son_kontrol, "son_sonuc": son_sonuc})
    dal = _git_cikti(["rev-parse", "--abbrev-ref", "HEAD"])
    hedef = _hedef_bul(dal)
    mevcut = _git_cikti(["rev-parse", "--short", "HEAD"])
    uzak = _git_cikti(["rev-parse", "--short", hedef]) if hedef else ""
    geride, ileride = 0, 0
    if hedef:
        sayim = _git_cikti(["rev-list", "--left-right", "--count", f"HEAD...{hedef}"])
        parca = sayim.split()
        if len(parca) == 2 and parca[0].isdigit() and parca[1].isdigit():
            ileride, geride = int(parca[0]), int(parca[1])
    return {
        "destek": True,
        "dal": dal,
        "hedef": hedef,
        "mevcut": mevcut,
        "uzak": uzak,
        "geride": geride,
        "ileride": ileride,
        "yeni": _yeni_commitler(hedef),
        "kirli": _kirli_dosyalar(),
        "mesgul": _mesgul(),
        "son_kontrol": son_kontrol,
        "hata": hata,
        "calisiyor": _kilitli(),
        "son_sonuc": son_sonuc,
    }


def _yeniden_baslatildi_mi(d: dict) -> dict:
    """Güncelleme bu süreç başlamadan önce bittiyse yeniden başlatma isteğini düşürür."""
    son = d.get("son_sonuc")
    if isinstance(son, dict) and son.get("yeniden_baslat") and str(son.get("ts", "")) < _SUREC_BASLANGIC:
        d = {**d, "son_sonuc": {**son, "yeniden_baslat": False}}
    return d


def durum_oku() -> dict:
    """Önbellek work/guncelleme/durum.json dosyasını okur (fetch yapmaz); canlı kilit ve meşgul alanlarını günceller."""
    ob = _onbellek_oku()
    if ob:
        return _yeniden_baslatildi_mi({
            **_bos_durum(destek=bool(ob.get("destek", False)), hata=ob.get("hata"), onbellek=ob),
            **ob,
            "mesgul": _mesgul(),
            "calisiyor": _kilitli(),
        })
    return _yerel_durum(son_kontrol=None, hata=None, son_sonuc=None)


def kontrol() -> dict:
    """git fetch --quiet origin (20 sn zaman aşımı) çalıştırır, sonucu durum.json'a yazar ve döner."""
    ob = _onbellek_oku()
    simdi = datetime.now().isoformat(timespec="seconds")
    if not _destek_var_mi():
        return _durum_yaz(_bos_durum(destek=False, hata=None, onbellek={**ob, "son_kontrol": simdi}))
    hata: str | None = None
    try:
        r = _git(["fetch", "--quiet", "origin"], zaman=FETCH_ZAMAN_ASIMI)
        if r.returncode != 0:
            hata = (r.stderr or r.stdout or "git fetch başarısız").strip()[:400]
    except subprocess.TimeoutExpired:
        hata = f"git fetch {FETCH_ZAMAN_ASIMI} sn zaman aşımına uğradı"
    except OSError as e:
        hata = str(e)[:400]
    durum = _yerel_durum(son_kontrol=simdi, hata=hata, son_sonuc=ob.get("son_sonuc"))
    return _yeniden_baslatildi_mi(_durum_yaz(durum))


def _kapi_kontrol() -> None:
    if not _destek_var_mi():
        raise RuntimeError("Git deposu değil veya git bulunamadı.")
    if _kilitli():
        raise RuntimeError("Uygulama güncellemesi zaten sürüyor.")
    if hf_guncel.KILIT.exists():
        raise RuntimeError("HyperFrames güncellemesi sürerken uygulama güncellenemez.")
    m = _mesgul(taze=True)
    if m:
        raise RuntimeError(f"Çalışan iş var, güncelleme erteleniyor: {', '.join(m[:3])}")


def _yedekle(ts: str, kirli: list[str]) -> list[str]:
    """Kirli ve izlenmeyen dosyaları work/guncelleme/<ts>/yedek/ altına kopyalar."""
    kok = _kok()
    yedek_kok = _calisma() / ts / "yedek"
    yedeklenen: list[str] = []
    for rel in kirli:
        kaynak = kok / rel
        if not kaynak.exists():
            continue
        hedef = yedek_kok / rel
        hedef.parent.mkdir(parents=True, exist_ok=True)
        if kaynak.is_dir():
            shutil.copytree(kaynak, hedef, dirs_exist_ok=True)
        elif kaynak.is_file():
            shutil.copy2(kaynak, hedef)
        yedeklenen.append(rel)
    return yedeklenen


def _gelen_kaydet(ts: str, rel: str) -> None:
    """Çakışan dosyanın HEAD (gelen) sürümünü work/guncelleme/<ts>/gelen/<yol> altına kaydeder."""
    r = _git_bytes(["show", f"HEAD:{rel}"])
    if r.returncode == 0:
        hedef = _calisma() / ts / "gelen" / rel
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_bytes(r.stdout)


def _pip_kur(kok: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        cwd=kok,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )


def _npm_calistir(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    npm = shutil.which("npm") or "npm"
    return subprocess.run(
        [npm, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        shell=os.name == "nt" and not shutil.which("npm"),
    )


def _bagimlilik_adimlari(degisen: list[str]) -> list[str]:
    """Değişen dosyalara göre pip/npm/build adımlarını çalıştırır; hatalar uyarı listesi döner."""
    kok = _kok()
    uyarilar: list[str] = []
    degisen_set = set(degisen)

    if "pyproject.toml" in degisen_set:
        try:
            r = _pip_kur(kok)
            if r.returncode != 0:
                metin = (r.stderr or r.stdout or "").lower()
                if "vedit.exe" in metin or "winerror 32" in metin or "winerror 5" in metin or "used by another process" in metin:
                    uyarilar.append("Stüdyo'yu kapatıp kur.bat çalıştır")
                else:
                    uyarilar.append(f"pip install uyarısı: {(r.stderr or r.stdout).strip()[-250:]}")
        except Exception as e:
            uyarilar.append(f"pip install çalıştırılamadı: {e}")

    if "package-lock.json" in degisen_set:
        try:
            r = _npm_calistir(["ci"], kok)
            if r.returncode != 0:
                uyarilar.append(f"Kök npm ci başarısız: {(r.stderr or r.stdout).strip()[-250:]}")
        except Exception as e:
            uyarilar.append(f"Kök npm ci çalıştırılamadı: {e}")

    if "studio/package-lock.json" in degisen_set:
        try:
            r = _npm_calistir(["ci"], kok / "studio")
            if r.returncode != 0:
                uyarilar.append(f"studio npm ci başarısız: {(r.stderr or r.stdout).strip()[-250:]}")
        except Exception as e:
            uyarilar.append(f"studio npm ci çalıştırılamadı: {e}")

    if any(y.startswith(("studio/web/", "studio/hf/")) or y in ("studio/web", "studio/hf") for y in degisen):
        try:
            r = _npm_calistir(["run", "build"], kok / "studio")
            if r.returncode != 0:
                uyarilar.append(f"studio build başarısız: {(r.stderr or r.stdout).strip()[-250:]}")
        except Exception as e:
            uyarilar.append(f"studio build çalıştırılamadı: {e}")

    return uyarilar


def _rapor_yaz(
    ts: str,
    *,
    eski_kisa: str,
    yeni_kisa: str,
    commitler: list[str],
    korunan: list[str],
    uyarilar: list[str],
    stash_ref: str | None,
    hata: str | None = None,
) -> Path:
    rapor_yolu = _calisma() / ts / "rapor.md"
    rapor_yolu.parent.mkdir(parents=True, exist_ok=True)
    satirlar = [
        f"# Uygulama Güncelleme Raporu ({ts})",
        "",
        f"- Önceki sürüm: `{eski_kisa}`",
        f"- Güncel sürüm: `{yeni_kisa}`",
        "",
        "## Alınan Commitler",
    ]
    if commitler:
        satirlar += [f"- {c}" for c in commitler]
    else:
        satirlar.append("- Alınan yeni commit yok.")
    satirlar += ["", "## Korunan Dosyalar"]
    if korunan:
        satirlar += [f"- `{k}`" for k in korunan]
    else:
        satirlar.append("- Yok.")
    if stash_ref:
        satirlar += ["", f"Çakışma nedeniyle stash korunmuştur: `{stash_ref}` (gelen sürümler `work/guncelleme/{ts}/gelen/` altında)."]
    if uyarilar:
        satirlar += ["", "## Uyarılar"] + [f"- {u}" for u in uyarilar]
    if hata:
        satirlar += ["", "## Hata", f"- {hata}"]
    satirlar += [
        "",
        "## Geri Alma",
        f"Bu güncellemeyi geri almak için: `vedit guncelle --geri-al {ts}`",
        "",
    ]
    rapor_yolu.write_text("\n".join(satirlar), encoding="utf-8")
    return rapor_yolu


def _stash_ref_bul(ts: str) -> str | None:
    r = _git(["stash", "list", "-n", "5", "--format=%gd %s"])
    if r.returncode != 0:
        return None
    aranan = f"cat-cut guncelleme {ts}"
    for satir in r.stdout.splitlines():
        if aranan in satir:
            return satir.split(" ", 1)[0]
    return None


def uygula() -> dict:
    """Güvenli uygulama güncellemesi uygular: kilit, etiket+yedek, stash, merge, pop, bağımlılık, rapor."""
    _kapi_kontrol()
    kilit = _kilit_yolu()
    kilit.parent.mkdir(parents=True, exist_ok=True)
    kilit.write_text(f"{os.getpid()}\n", encoding="utf-8")

    try:
        # En güncel origin bilgisini almaya çalış (ağ yoksa mevcut origin ref'i ile devam edilir)
        _git(["fetch", "--quiet", "origin"], zaman=FETCH_ZAMAN_ASIMI)

        ob = _onbellek_oku()
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        eski_sha = _git_cikti(["rev-parse", "HEAD"])
        eski_kisa = _git_cikti(["rev-parse", "--short", "HEAD"])
        dal = _git_cikti(["rev-parse", "--abbrev-ref", "HEAD"])
        hedef = _hedef_bul(dal)
        if not hedef:
            raise RuntimeError("Uzak hedef dal (origin) bulunamadı.")

        # (3) Yedek: tag + kirli/izlenmeyen dosyalar
        tag_r = _git(["tag", f"cat-cut-oncesi-{ts}"])
        if tag_r.returncode != 0:
            raise RuntimeError(f"Yedek etiketi oluşturulamadı: {(tag_r.stderr or tag_r.stdout).strip()}")

        kirli = _kirli_dosyalar()
        yedeklenen = _yedekle(ts, kirli)

        # (4) Kirliyse stash (work/guncelleme hariç tutularak kilit ve yedek korunur)
        stash_var = False
        if kirli:
            sr = _git(["stash", "push", "-u", "-m", f"cat-cut guncelleme {ts}", "--", ".", ":(exclude)work/guncelleme"])
            if sr.returncode != 0:
                raise RuntimeError(f"Yerel değişiklikler stash edilemedi: {(sr.stderr or sr.stdout).strip()}")
            stash_var = _stash_ref_bul(ts) is not None

        # (5) Merge: önce ff-only, olmazsa --no-edit
        mr = _git(["merge", "--ff-only", hedef])
        if mr.returncode != 0:
            mr = _git(["merge", "--no-edit", hedef])
            if mr.returncode != 0:
                _git(["merge", "--abort"])
                if stash_var:
                    _git(["stash", "pop"])
                rapor_yolu = _rapor_yaz(
                    ts,
                    eski_kisa=eski_kisa,
                    yeni_kisa=eski_kisa,
                    commitler=[],
                    korunan=yedeklenen,
                    uyarilar=[],
                    stash_ref=None,
                    hata="elle birleştirme gerekli",
                )
                son = {
                    "ts": ts,
                    "durum": "hata",
                    "ozet": "elle birleştirme gerekli",
                    "korunan": yedeklenen,
                    "rapor": f"work/guncelleme/{ts}/rapor.md",
                    "geri_alinabilir": True,
                    "yeniden_baslat": False,
                }
                _durum_yaz(_yerel_durum(son_kontrol=ob.get("son_kontrol"), hata="elle birleştirme gerekli", son_sonuc=son))
                raise RuntimeError("elle birleştirme gerekli")

        yeni_sha = _git_cikti(["rev-parse", "HEAD"])
        yeni_kisa = _git_cikti(["rev-parse", "--short", "HEAD"])

        # (6) Stash pop ve çakışmada kullanıcı sürümünü koruma
        korunan: list[str] = list(yedeklenen)
        stash_ref_rapor: str | None = None
        uyarilar: list[str] = []

        if stash_var:
            pr = _git(["stash", "pop"])
            if pr.returncode != 0:
                stash_ref_rapor = _stash_ref_bul(ts) or "stash@{0}"
                c_r = _git(["diff", "--name-only", "--diff-filter=U", "-z"])
                cakisanlar = [x.replace("\\", "/") for x in c_r.stdout.split("\0") if x]
                for rel in cakisanlar:
                    _gelen_kaydet(ts, rel)
                    co_r = _git(["checkout", "--theirs", "--", rel])
                    if co_r.returncode != 0:
                        # Örn. untracked/silinmiş kenar durumu: yedekten geri yükle
                        yedek_f = _calisma() / ts / "yedek" / rel
                        if yedek_f.is_file():
                            hedef_f = _kok() / rel
                            hedef_f.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(yedek_f, hedef_f)
                    _git(["reset", "-q", "--", rel])
                    if rel not in korunan:
                        korunan.append(rel)
                if not cakisanlar:
                    # Stash pop untracked dosya yüzünden düştüyse yedeklerden koru
                    for rel in yedeklenen:
                        if _git(["ls-files", "--error-unmatch", rel]).returncode == 0:
                            _gelen_kaydet(ts, rel)
                        yedek_f = _calisma() / ts / "yedek" / rel
                        if yedek_f.is_file():
                            hedef_f = _kok() / rel
                            hedef_f.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(yedek_f, hedef_f)
                uyarilar.append(f"Yerel değişiklikler korundu; gelen sürümler work/guncelleme/{ts}/gelen/ altında, stash ({stash_ref_rapor}) saklandı.")

        # (7) Değişen dosyalara göre kurulum/derleme
        degisen = [
            x.replace("\\", "/")
            for x in _git_cikti(["diff", "--name-only", f"{eski_sha}..HEAD"]).splitlines()
            if x.strip()
        ]
        uyarilar.extend(_bagimlilik_adimlari(degisen))

        # (8) Rapor + durum.json
        log_r = _git(["log", "--oneline", f"{eski_sha}..HEAD"])
        commit_satirlari = [s for s in log_r.stdout.splitlines() if s.strip()] if log_r.returncode == 0 else []
        _rapor_yaz(
            ts,
            eski_kisa=eski_kisa,
            yeni_kisa=yeni_kisa,
            commitler=commit_satirlari,
            korunan=korunan,
            uyarilar=uyarilar,
            stash_ref=stash_ref_rapor,
        )

        durum_kodu = "uyari" if uyarilar else "basarili"
        n_commit = len(commit_satirlari)
        ozet = f"{n_commit} commit alındı ({eski_kisa} → {yeni_kisa})" if n_commit else "Zaten güncel"
        son = {
            "ts": ts,
            "durum": durum_kodu,
            "ozet": ozet,
            "korunan": korunan,
            "rapor": f"work/guncelleme/{ts}/rapor.md",
            "geri_alinabilir": True,
            "yeniden_baslat": yeni_sha != eski_sha,
        }
        return _durum_yaz(_yerel_durum(son_kontrol=ob.get("son_kontrol"), hata=None, son_sonuc=son))
    finally:
        kilit.unlink(missing_ok=True)


def geri_al(ts: str) -> dict:
    """Belirtilen güncelleme öncesindeki cat-cut-oncesi-<ts> etiketine güvenli şekilde geri döner."""
    _kapi_kontrol()
    if not re.fullmatch(r"\d{8}-\d{6}", ts or ""):
        raise RuntimeError(f"Geçersiz zaman damgası: {ts}")
    etiket = f"cat-cut-oncesi-{ts}"
    if _git(["rev-parse", "--verify", "--quiet", f"refs/tags/{etiket}"]).returncode != 0:
        raise RuntimeError(f"Geri alma etiketi bulunamadı: {etiket}")

    kilit = _kilit_yolu()
    kilit.parent.mkdir(parents=True, exist_ok=True)
    kilit.write_text(f"{os.getpid()}\n", encoding="utf-8")
    try:
        rr = _git(["reset", "--keep", etiket])
        if rr.returncode != 0:
            raise RuntimeError(f"Geri alma yerel değişikliklerle çakışıyor: {(rr.stderr or rr.stdout).strip()}")

        kok = _kok()
        yedek_kok = _calisma() / ts / "yedek"
        if yedek_kok.is_dir():
            for f in yedek_kok.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(yedek_kok)
                    if rel.parts and rel.parts[0] == "Projeler":
                        continue
                    hedef = kok / rel
                    hedef.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, hedef)

        ob = _onbellek_oku()
        son = {
            "ts": ts,
            "durum": "basarili",
            "ozet": f"{ts} öncesi sürüme geri alındı",
            "korunan": [],
            "rapor": f"work/guncelleme/{ts}/rapor.md",
            "geri_alinabilir": False,
            "yeniden_baslat": True,
        }
        return _durum_yaz(_yerel_durum(son_kontrol=ob.get("son_kontrol"), hata=None, son_sonuc=son))
    finally:
        kilit.unlink(missing_ok=True)


def arka_plan() -> None:
    """Stüdyo açıkken her 30 dakikada bir origin kontrolü yapar; istisnaları durum dosyasına yazar."""
    while True:
        try:
            kontrol()
        except Exception as e:  # WHY: arka plan döngüsü ölmemeli; hata durum dosyasında görünür
            try:
                ob = _onbellek_oku()
                _durum_yaz(_bos_durum(destek=_destek_var_mi(), hata=str(e)[:300], onbellek=ob))
            except OSError:
                pass
        time.sleep(YOKLAMA)
