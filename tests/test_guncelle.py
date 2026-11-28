"""Uygulama güncelleme testleri (ADR 0065)."""

from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path

import pytest

from vedit import guncelle, hf_guncel, paths


@pytest.fixture(autouse=True)
def _mesgul_onbellegi_kapali(monkeypatch):
    """Testler süreç taramasını yamaladığı için önbellek testler arasında taşınmasın."""
    from vedit import guncelle as _g
    monkeypatch.setattr(_g, "_MESGUL_OMUR", 0.0)


def _git(cwd: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return r.stdout.strip()


def _commit_dosya(repo: Path, rel: str, icerik: str, mesaj: str) -> str:
    f = repo / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(icerik, encoding="utf-8")
    _git(repo, "add", rel)
    _git(repo, "commit", "-m", mesaj)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def ortam(tmp_path, monkeypatch):
    """Bare origin, ikinci geliştirici klonu (uzak) ve kullanıcı klonu kurar."""
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True, capture_output=True)

    uzak = tmp_path / "uzak"
    subprocess.run(["git", "clone", str(bare), str(uzak)], check=True, capture_output=True)
    _git(uzak, "config", "user.name", "Test")
    _git(uzak, "config", "user.email", "test@example.com")
    _git(uzak, "checkout", "-B", "main")
    (uzak / ".gitignore").write_text("/Projeler/\n", encoding="utf-8")
    (uzak / "src" / "vedit").mkdir(parents=True, exist_ok=True)
    (uzak / "src" / "vedit" / "kod.py").write_text("SURUM = 1\n", encoding="utf-8")
    (uzak / "library" / "kurallar").mkdir(parents=True, exist_ok=True)
    (uzak / "library" / "kurallar" / "kurallar.json").write_text('{"kurallar": ["k1"]}\n', encoding="utf-8")
    _git(uzak, "add", ".")
    _git(uzak, "commit", "-m", "ilk commit")
    _git(uzak, "push", "-u", "origin", "main")
    subprocess.run(["git", "--git-dir", str(bare), "symbolic-ref", "HEAD", "refs/heads/main"], check=True)

    klon = tmp_path / "klon"
    subprocess.run(["git", "clone", str(bare), str(klon)], check=True, capture_output=True)
    _git(klon, "config", "user.name", "Kullanici")
    _git(klon, "config", "user.email", "kullanici@example.com")

    monkeypatch.setattr(paths, "ROOT", klon)
    monkeypatch.setattr(hf_guncel, "mesgul", lambda: [])
    monkeypatch.setattr(hf_guncel, "KILIT", tmp_path / "hf.kilit")
    monkeypatch.setattr(guncelle, "_pip_kur", lambda kok: subprocess.CompletedProcess([], 0, "", ""))
    monkeypatch.setattr(guncelle, "_npm_calistir", lambda args, cwd: subprocess.CompletedProcess([], 0, "", ""))

    return {"bare": bare, "uzak": uzak, "klon": klon}


def test_git_olmayan_kokte_destek_false(tmp_path, monkeypatch):
    bos = tmp_path / "bos"
    bos.mkdir()
    monkeypatch.setattr(paths, "ROOT", bos)
    monkeypatch.setattr(hf_guncel, "mesgul", lambda: [])
    d = guncelle.kontrol()
    assert d["destek"] is False
    assert d["geride"] == 0
    with pytest.raises(RuntimeError):
        guncelle.uygula()


def test_a_temiz_fast_forward(ortam):
    uzak, klon = ortam["uzak"], ortam["klon"]
    hedef_sha = _commit_dosya(uzak, "src/vedit/kod.py", "SURUM = 2\n", "feat: surum 2")
    _git(uzak, "push", "origin", "main")

    d = guncelle.kontrol()
    assert d["destek"] is True
    assert d["dal"] == "main"
    assert d["hedef"] == "origin/main"
    assert d["geride"] == 1
    assert d["ileride"] == 0
    assert d["yeni"][0]["baslik"] == "feat: surum 2"

    sonuc = guncelle.uygula()
    assert _git(klon, "rev-parse", "HEAD") == hedef_sha
    assert (klon / "src" / "vedit" / "kod.py").read_text(encoding="utf-8") == "SURUM = 2\n"
    assert sonuc["geride"] == 0
    assert sonuc["son_sonuc"]["durum"] == "basarili"
    assert sonuc["son_sonuc"]["yeniden_baslat"] is True
    assert (klon / sonuc["son_sonuc"]["rapor"]).is_file()


def test_b_kirli_kurallar_korunur_ve_yeni_kod_gelir(ortam):
    uzak, klon = ortam["uzak"], ortam["klon"]
    kurallar = klon / "library" / "kurallar" / "kurallar.json"
    kurallar.write_text('{"kurallar": ["k1", "kullanici"]}\n', encoding="utf-8")

    _commit_dosya(uzak, "src/vedit/kod.py", "SURUM = 3\n", "feat: kod guncellendi")
    _git(uzak, "push", "origin", "main")

    sonuc = guncelle.uygula()
    assert kurallar.read_text(encoding="utf-8") == '{"kurallar": ["k1", "kullanici"]}\n'
    assert (klon / "src" / "vedit" / "kod.py").read_text(encoding="utf-8") == "SURUM = 3\n"
    assert "library/kurallar/kurallar.json" in sonuc["son_sonuc"]["korunan"]


def test_c_ayni_dosya_cakismasinda_kullanici_kalir_ve_gelen_kaydedilir(ortam):
    uzak, klon = ortam["uzak"], ortam["klon"]
    hedef_yol = "library/kurallar/kurallar.json"
    (klon / hedef_yol).write_text('{"kurallar": ["yerel-ozel"]}\n', encoding="utf-8")

    _commit_dosya(uzak, hedef_yol, '{"kurallar": ["uzak-yeni"]}\n', "chore: uzak kural")
    _git(uzak, "push", "origin", "main")

    sonuc = guncelle.uygula()
    ts = sonuc["son_sonuc"]["ts"]
    assert (klon / hedef_yol).read_text(encoding="utf-8") == '{"kurallar": ["yerel-ozel"]}\n'
    gelen = klon / "work" / "guncelleme" / ts / "gelen" / hedef_yol
    assert gelen.is_file()
    assert gelen.read_text(encoding="utf-8") == '{"kurallar": ["uzak-yeni"]}\n'
    assert hedef_yol in sonuc["son_sonuc"]["korunan"]
    assert sonuc["son_sonuc"]["durum"] == "uyari"
    # Stash düşürülmemiş olmalı
    assert f"cat-cut guncelleme {ts}" in _git(klon, "stash", "list")


def test_d_mesgul_doluysa_reddeder_head_degismez(ortam, monkeypatch):
    uzak, klon = ortam["uzak"], ortam["klon"]
    _commit_dosya(uzak, "src/vedit/kod.py", "SURUM = 9\n", "feat: dokuz")
    _git(uzak, "push", "origin", "main")

    eski_head = _git(klon, "rev-parse", "HEAD")
    monkeypatch.setattr(hf_guncel, "mesgul", lambda: ["ffmpeg.exe 999999"])
    with pytest.raises(RuntimeError):
        guncelle.uygula()
    assert _git(klon, "rev-parse", "HEAD") == eski_head


def test_e_projeler_altindaki_dosyanin_hashi_degismez(ortam):
    uzak, klon = ortam["uzak"], ortam["klon"]
    proje_dosya = klon / "Projeler" / "inputs" / "instagram" / "demo" / "not.txt"
    proje_dosya.parent.mkdir(parents=True, exist_ok=True)
    proje_dosya.write_bytes(b"kullanici verisi 12345\n")
    once_hash = hashlib.sha256(proje_dosya.read_bytes()).hexdigest()

    _commit_dosya(uzak, "src/vedit/kod.py", "SURUM = 4\n", "feat: dort")
    _git(uzak, "push", "origin", "main")

    guncelle.uygula()
    sonra_hash = hashlib.sha256(proje_dosya.read_bytes()).hexdigest()
    assert sonra_hash == once_hash


def test_f_geri_al_eski_heade_doner(ortam):
    uzak, klon = ortam["uzak"], ortam["klon"]
    eski_head = _git(klon, "rev-parse", "HEAD")

    _commit_dosya(uzak, "src/vedit/kod.py", "SURUM = 5\n", "feat: bes")
    _git(uzak, "push", "origin", "main")

    sonuc = guncelle.uygula()
    ts = sonuc["son_sonuc"]["ts"]
    assert _git(klon, "rev-parse", "HEAD") != eski_head

    geri_sonuc = guncelle.geri_al(ts)
    assert _git(klon, "rev-parse", "HEAD") == eski_head
    assert (klon / "src" / "vedit" / "kod.py").read_text(encoding="utf-8") == "SURUM = 1\n"
    assert geri_sonuc["son_sonuc"]["geri_alinabilir"] is False


def test_g_yerel_commit_ve_uzak_commit_merge_yapar(ortam):
    uzak, klon = ortam["uzak"], ortam["klon"]
    _commit_dosya(klon, "yerel.txt", "yerel commit\n", "feat: yerel")
    _commit_dosya(uzak, "uzak.txt", "uzak commit\n", "feat: uzak")
    _git(uzak, "push", "origin", "main")

    d = guncelle.kontrol()
    assert d["geride"] == 1 and d["ileride"] == 1

    sonuc = guncelle.uygula()
    assert sonuc["son_sonuc"]["durum"] == "basarili"
    assert (klon / "yerel.txt").read_text(encoding="utf-8") == "yerel commit\n"
    assert (klon / "uzak.txt").read_text(encoding="utf-8") == "uzak commit\n"
    # Merge commit'in 2 ebeveyni olmalı
    ebeveynler = _git(klon, "rev-list", "--parents", "-n", "1", "HEAD").split()
    assert len(ebeveynler) == 3


def test_bagimlilik_adimlari_ve_pip_kilit_uyarisi(ortam, monkeypatch):
    uzak = ortam["uzak"]
    _commit_dosya(uzak, "pyproject.toml", "[project]\nname='x'\n", "build: pyproject")
    _commit_dosya(uzak, "package-lock.json", "{}\n", "build: root lock")
    _commit_dosya(uzak, "studio/package-lock.json", "{}\n", "build: studio lock")
    _commit_dosya(uzak, "studio/web/src/App.tsx", "export {}\n", "feat: web")
    _git(uzak, "push", "origin", "main")

    cagrilar: list[tuple[str, Path]] = []

    def fake_pip(kok: Path):
        cagrilar.append(("pip", kok))
        return subprocess.CompletedProcess([], 1, "", "ERROR: Could not install packages: vedit.exe [WinError 32]")

    def fake_npm(args: list[str], cwd: Path):
        cagrilar.append((" ".join(["npm", *args]), cwd))
        return subprocess.CompletedProcess([], 0, "", "")

    monkeypatch.setattr(guncelle, "_pip_kur", fake_pip)
    monkeypatch.setattr(guncelle, "_npm_calistir", fake_npm)

    sonuc = guncelle.uygula()
    klon = ortam["klon"]
    assert ("pip", klon) in cagrilar
    assert ("npm ci", klon) in cagrilar
    assert ("npm ci", klon / "studio") in cagrilar
    assert ("npm run build", klon / "studio") in cagrilar
    assert sonuc["son_sonuc"]["durum"] == "uyari"
    rapor_metin = (klon / sonuc["son_sonuc"]["rapor"]).read_text(encoding="utf-8")
    assert "Stüdyo'yu kapatıp kur.bat çalıştır" in rapor_metin


def test_mesgul_suzgeci_kendi_ve_guncelle_surecini_elenir(monkeypatch):
    pid = os.getpid()
    ppid = os.getppid()
    monkeypatch.setattr(
        hf_guncel,
        "mesgul",
        lambda: [
            "Stüdyo işi: AI edit",
            f"python.exe {pid}",
            f"vedit.exe {ppid}",
            "vedit.exe 44444",
            "ffmpeg.exe 55555",
        ],
    )
    monkeypatch.setattr(
        hf_guncel,
        "_surecler",
        lambda: [
            (44444, "vedit.exe", r'"C:\x\vedit.exe" guncelle --uygula'),
            (55555, "ffmpeg.exe", "ffmpeg -i a.mp4"),
        ],
    )
    assert guncelle._mesgul(taze=True) == ["Stüdyo işi: AI edit", "ffmpeg.exe 55555"]


def test_studio_api_rotalari(ortam, monkeypatch):
    fastapi = pytest.importorskip("fastapi")
    assert fastapi
    from fastapi.testclient import TestClient

    from vedit.studio import isler
    from vedit.studio.app import create_app

    host = "127.0.0.1:8765"
    c = TestClient(create_app("t0k", izinli_hostlar={host}), base_url=f"http://{host}", follow_redirects=False)
    assert c.get("/?token=t0k").status_code == 303

    # Durum okuma (fetch yapmaz)
    rd = c.get("/api/guncelleme/durum")
    assert rd.status_code == 200 and rd.json()["destek"] is True

    # Geride 0 iken uygula 409 döner
    r0 = c.post("/api/guncelleme/uygula", headers={"origin": f"http://{host}"})
    assert r0.status_code == 409

    # Yeni commit gelince kontrol görür ve uygula kuyruğa ekler
    _commit_dosya(ortam["uzak"], "src/vedit/kod.py", "SURUM = 8\n", "feat: sekiz")
    _git(ortam["uzak"], "push", "origin", "main")
    rk = c.post("/api/guncelleme/kontrol", headers={"origin": f"http://{host}"})
    assert rk.status_code == 200 and rk.json()["geride"] == 1

    class SahteIs:
        id = 77

    eklenen = []
    monkeypatch.setattr(isler, "_k", lambda: type("K", (), {"ekle": lambda self, *a: eklenen.append(a) or SahteIs()})())
    ru = c.post("/api/guncelleme/uygula", headers={"origin": f"http://{host}"})
    assert ru.status_code == 200 and ru.json() == {"is": 77}
    assert eklenen[0] == ("guncelle", "Uygulama güncellemesi", ["guncelle", "--uygula"])

    # Geçersiz geri-al etiketi 409 döner
    rg = c.post("/api/guncelleme/geri-al", json={"ts": "20260101-000000"}, headers={"origin": f"http://{host}"})
    assert rg.status_code == 409


def test_cli_guncelle(ortam, capsys, monkeypatch):
    from vedit import cli

    _commit_dosya(ortam["uzak"], "src/vedit/kod.py", "SURUM = 10\n", "feat: on")
    _git(ortam["uzak"], "push", "origin", "main")

    cli.main(["guncelle", "--kontrol"])
    assert "1 commit geride" in capsys.readouterr().out

    cli.main(["guncelle", "--uygula"])
    cikti = capsys.readouterr().out
    assert "1 commit alındı" in cikti
    ts = guncelle.durum_oku()["son_sonuc"]["ts"]

    cli.main(["guncelle", "--geri-al", ts])
    assert "Geri alındı" in capsys.readouterr().out

    # Meşgulken hata çıkış kodu 1
    monkeypatch.setattr(hf_guncel, "mesgul", lambda: ["ffmpeg.exe 999999"])
    with pytest.raises(SystemExit) as ex:
        cli.main(["guncelle", "--uygula"])
    assert ex.value.code == 1


def test_yeniden_baslat_istegi_acilistan_sonra_duser(monkeypatch):
    """Sunucu güncellemeden sonra açıldıysa düğme "Yeniden başlat"ta takılı kalmaz."""
    son = {"ts": "20261128-100000", "durum": "basarili", "ozet": "x", "yeniden_baslat": True}
    monkeypatch.setattr(guncelle, "_SUREC_BASLANGIC", "20261128-110000")
    assert guncelle._yeniden_baslatildi_mi({"son_sonuc": son})["son_sonuc"]["yeniden_baslat"] is False
    monkeypatch.setattr(guncelle, "_SUREC_BASLANGIC", "20261128-090000")
    assert guncelle._yeniden_baslatildi_mi({"son_sonuc": son})["son_sonuc"]["yeniden_baslat"] is True
