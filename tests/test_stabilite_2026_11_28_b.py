"""Stabilite denetimi regresyon testleri (2026-11-28, grup B: bulgular 3, 7, 9, 11, 13, 14)."""

from __future__ import annotations

import errno
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from vedit import ajan_cagri, ekip, ff, hf, hf_guncel, hf_motion, kurgu, motion, motorlar, pano, paths, render, slop, vekil
from vedit.ekip_sema import Slot
from vedit.hizli import Proje


# ---------------------------------------------------------------- Bulgu 3: hf_guncel.duman ve hf.run/kok


def test_bulgu3_duman_os_environ_degistirmez_ve_aday_koku_iletir(tmp_path, monkeypatch):
    monkeypatch.delenv("VEDIT_HF_KOK", raising=False)
    duman_dir = tmp_path / "hf_duman"
    (duman_dir / "kart").mkdir(parents=True)
    (duman_dir / "kart" / "index.html").write_text(
        '<html><div data-composition-id="main" data-width="1080" data-height="1920" data-duration="1"></div></html>',
        encoding="utf-8",
    )
    aday = tmp_path / "aday"
    bin_dir = aday / "node_modules" / ".bin"
    bin_dir.mkdir(parents=True)
    aday_exe = bin_dir / ("hyperframes.cmd" if os.name == "nt" else "hyperframes")
    aday_exe.write_text("echo ok", encoding="utf-8")

    monkeypatch.setattr(hf_guncel, "DUMAN", duman_dir)
    monkeypatch.setattr(hf_guncel.hf_grafik, "_hazirla", lambda src, dst, tema: dst.mkdir(parents=True, exist_ok=True))
    monkeypatch.setattr(hf_guncel.hf_grafik, "olcu", lambda d: {"w": 1080, "h": 1920, "sure": 1.0})
    monkeypatch.setattr(hf_guncel, "_kare", lambda v, t, hedef: hedef.write_bytes(b"png"))
    monkeypatch.setattr(ff, "probe", lambda v: {"duration": 1.0, "video": {"width": 1080, "height": 1920}})

    gozlenen_env: list[str | None] = []
    gorulen_cmd: list[list[str]] = []

    def sahte_run(cmd, **kw):
        gozlenen_env.append(os.environ.get("VEDIT_HF_KOK"))
        gorulen_cmd.append(cmd)
        assert kw["env"].get("VEDIT_HF_KOK") == str(aday)
        if "lint" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout='{"errorCount": 0}', stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(hf.subprocess, "run", sahte_run)
    # Diğer işler aynı anda hf._bin() çağırdığında sabit kurulumu görmeli
    assert hf._bin() != [str(aday_exe)]
    sonuc = hf_guncel.duman(aday, cikti=tmp_path / "cikti")
    assert sonuc[0]["gecti"] is True
    assert "VEDIT_HF_KOK" not in os.environ
    assert gozlenen_env == [None, None]
    assert gorulen_cmd[0][0] == str(aday_exe)
    assert gorulen_cmd[1][0] == str(aday_exe)


# ---------------------------------------------------------------- Bulgu 9: kurgu hardlink_to fallback


def test_bulgu9_kurgu_bagla_oserror_kopyalar_ve_fileexists_yutar(tmp_path, monkeypatch):
    kaynak = tmp_path / "kaynak.txt"
    kaynak.write_text("veri", encoding="utf-8")
    hedef = tmp_path / "hedef.txt"

    def sahte_hardlink_oserror(self, target):
        raise OSError(errno.EXDEV, "Cross-device link")

    monkeypatch.setattr(Path, "hardlink_to", sahte_hardlink_oserror)
    kurgu._bagla(hedef, kaynak)
    assert hedef.read_text(encoding="utf-8") == "veri"

    hedef2 = tmp_path / "hedef2.txt"
    hedef2.write_text("eski", encoding="utf-8")

    def sahte_hardlink_exists(self, target):
        raise FileExistsError(errno.EEXIST, "File exists")

    monkeypatch.setattr(Path, "hardlink_to", sahte_hardlink_exists)
    kurgu._bagla(hedef2, kaynak)
    assert hedef2.read_text(encoding="utf-8") == "eski"


def test_bulgu9_shot_bagla_oserror_dusebilir(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    monkeypatch.setattr(ff, "probe", lambda f: {"video": {"width": 320, "height": 240}})
    p = Proje("instagram", "hlink")
    gorsel = tmp_path / "kare.png"
    gorsel.write_bytes(b"png")

    monkeypatch.setattr(Path, "hardlink_to", lambda self, t: (_ for _ in ()).throw(OSError(errno.EXDEV, "EXDEV")))
    bilgi = kurgu.shot_bagla(p, gorsel)
    assert bilgi["img"] == "shot/kare.png"
    assert (p.work / "public" / "shot" / "kare.png").read_bytes() == b"png"


# ---------------------------------------------------------------- Bulgu 11: encoding utf-8 ve motion.olc kontrolleri


def test_bulgu11_motion_ve_hf_motion_utf8_ve_olc_hatalari(tmp_path, monkeypatch):
    m_dir = tmp_path / "motion"
    (m_dir / "custom" / "a").mkdir(parents=True)
    (m_dir / "custom" / "a" / "a.html").write_text("<html></html>", encoding="utf-8")
    (m_dir / "custom" / "a" / "meta.json").write_text(
        json.dumps({"title": "A", "kind": "overlay", "sure": 1.0, "w": 100, "h": 100}), encoding="utf-8"
    )
    (m_dir / "custom" / "a" / "a.webm").write_bytes(b"webm")
    monkeypatch.setattr(paths, "MOTION_DIR", m_dir)

    cagrilar: list[dict] = []

    def sahte_run_ok(cmd, **kw):
        cagrilar.append(kw)
        if cmd[0] == "ffprobe":
            return subprocess.CompletedProcess(cmd, 0, stdout='{"streams": []}', stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(motion.subprocess, "run", sahte_run_ok)
    with pytest.raises(RuntimeError, match="Video akışı bulunamadı"):
        motion.olc(["a"])
    assert cagrilar[0]["encoding"] == "utf-8" and cagrilar[0]["errors"] == "replace"

    monkeypatch.setattr(
        motion.subprocess,
        "run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, stdout="", stderr="bozuk dosya"),
    )
    with pytest.raises(RuntimeError, match="ffprobe başarısız"):
        motion.olc(["a"])

    # _ff ve hf_motion._pikselle çağrılarında da utf-8 + errors='replace' verilmeli
    ff_kw: list[dict] = []
    monkeypatch.setattr(
        motion.subprocess,
        "run",
        lambda cmd, **kw: ff_kw.append(kw) or subprocess.CompletedProcess(cmd, 0, stdout="", stderr=""),
    )
    motion._ff("-version")
    assert ff_kw[0]["encoding"] == "utf-8" and ff_kw[0]["errors"] == "replace"

    hf_kw: list[dict] = []
    sahte_webm = tmp_path / "x.webm"
    sahte_webm.write_bytes(b"x")

    def sahte_piksel(cmd, **kw):
        hf_kw.append(kw)
        Path(cmd[-1]).write_bytes(b"y")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(hf_motion.subprocess, "run", sahte_piksel)
    hf_motion._pikselle(sahte_webm, 2)
    assert hf_kw[0]["encoding"] == "utf-8" and hf_kw[0]["errors"] == "replace"


# ---------------------------------------------------------------- Bulgu 7: zaman aşımında süreç ağacı ve stdout kapanışı


def _alt_surec_betik(dosya: Path) -> Path:
    # Torun süreç stdout tutamacını miras alır ve 30 sn uyur; yalnız ana süreç öldürülürse stdout takılırdı.
    dosya.write_text(
        "import subprocess, sys, time\n"
        "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        "time.sleep(30)\n",
        encoding="utf-8",
    )
    return dosya


def test_bulgu7_ajan_cagri_varsayilan_sure_ve_zaman_asimi_agaci_sonlandirir(tmp_path, monkeypatch):
    assert ajan_cagri.AJAN_SURE == 3600 and ekip.AJAN_SURE == 1800
    betik = _alt_surec_betik(tmp_path / "takil.py")
    monkeypatch.setattr(ajan_cagri, "komut", lambda *a, **kw: [sys.executable, str(betik)])

    t0 = time.monotonic()
    with pytest.raises(SystemExit, match="zaman aşımı"):
        ajan_cagri.calistir("x", sure=0.25)
    assert time.monotonic() - t0 < 5.0


def test_bulgu7_ekip_ajan_zaman_asimi_agaci_sonlandirir_ve_stdout_kapatir(tmp_path, monkeypatch):
    betik = _alt_surec_betik(tmp_path / "takil_ekip.py")
    monkeypatch.setattr(motorlar, "komut", lambda *a, **kw: [sys.executable, str(betik)])
    monkeypatch.setattr(ekip, "AJAN_SURE", 0.25)

    acilmis: list = []
    gercek_popen = ekip.subprocess.Popen

    def izle_popen(*a, **kw):
        p = gercek_popen(*a, **kw)
        acilmis.append(p)
        return p

    monkeypatch.setattr(ekip.subprocess, "Popen", izle_popen)
    t0 = time.monotonic()
    ok, _, meta = ekip.ajan(Slot(motor="codex", model="m"), "x", "duzenle", tmp_path / "kayit")
    assert time.monotonic() - t0 < 5.0
    assert ok is False and "Zaman aşımı" in (meta.get("hata") or "")
    assert acilmis and acilmis[0].stdout.closed


# ---------------------------------------------------------------- Bulgu 13: pano.render ve slop.kareleri_oku finally


def test_bulgu13_pano_render_hatada_pipe_kapatir_ve_sureci_sonlandirir(tmp_path, monkeypatch):
    olaylar: list[str] = []

    class SahteStdin:
        closed = False

        def write(self, data):
            pass

        def close(self):
            self.closed = True
            olaylar.append("close")

    class SahteProc:
        def __init__(self):
            self.stdin = SahteStdin()
            self._alive = True

        def poll(self):
            return None if self._alive else 0

        def terminate(self):
            olaylar.append("terminate")
            self._alive = False

        def wait(self, timeout=None):
            olaylar.append(f"wait:{timeout}")
            self._alive = False
            return 0

    monkeypatch.setattr(pano.subprocess, "Popen", lambda *a, **kw: SahteProc())
    html = tmp_path / "a.html"
    html.write_text("<html></html>", encoding="utf-8")

    # sync_playwright hata fırlatsa da stdin kapanmalı ve süreç terminate + wait(timeout=10) görmeli
    import playwright.sync_api as pw

    class BozukPW:
        def __enter__(self):
            raise RuntimeError("playwright çöktü")

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(pw, "sync_playwright", lambda: BozukPW())
    with pytest.raises(RuntimeError, match="playwright çöktü"):
        pano.render(html, tmp_path / "out.webm", sure=1.0, w=320, h=240)
    assert olaylar == ["close", "terminate", "wait:10"]


def test_bulgu13_slop_kareleri_oku_hatada_pipe_kapatir_ve_sureci_sonlandirir(tmp_path, monkeypatch):
    olaylar: list[str] = []

    class SahteStdout:
        closed = False

        def read(self, n):
            raise OSError("okuma koptu")

        def close(self):
            self.closed = True
            olaylar.append("close")

    class SahteProc:
        def __init__(self):
            self.stdout = SahteStdout()
            self._alive = True

        def poll(self):
            return None if self._alive else 0

        def terminate(self):
            olaylar.append("terminate")
            self._alive = False

        def wait(self, timeout=None):
            olaylar.append(f"wait:{timeout}")
            self._alive = False
            return 0

    monkeypatch.setattr(slop.subprocess, "Popen", lambda *a, **kw: SahteProc())
    with pytest.raises(OSError, match="okuma koptu"):
        slop.kareleri_oku(tmp_path / "v.mp4")
    assert olaylar == ["close", "terminate", "wait:10"]


# ---------------------------------------------------------------- Bulgu 14: vekil.uret ve render._render_one tmp temizliği


def test_bulgu14_vekil_uret_hatada_tmp_mp4_temizler(tmp_path, monkeypatch):
    work = tmp_path / "work"
    kaynak = tmp_path / "a.mp4"
    kaynak.write_bytes(b"video")
    monkeypatch.setattr(ff, "probe", lambda f: {"duration": 2.0, "video": {"width": 3840, "height": 2160, "fps": 30}})

    def sahte_ffmpeg(*a, **kw):
        Path(a[-1]).write_bytes(b"yarim-tmp")
        raise RuntimeError("ffmpeg çöktü")

    monkeypatch.setattr(ff, "ffmpeg", sahte_ffmpeg)
    with pytest.raises(RuntimeError, match="ffmpeg çöktü"):
        vekil.uret(work, kaynak, "taslak")
    assert list((work / "proxy").glob("*.tmp.mp4")) == []


def test_bulgu14_render_one_hatada_tmp_mp4_temizler(tmp_path, monkeypatch):
    out = tmp_path / "renders" / "bolum.mp4"

    def sahte_hf_render(comp_dir, tmp_out, **kw):
        Path(tmp_out).write_bytes(b"yarim-render")
        raise RuntimeError("render çöktü")

    monkeypatch.setattr(hf, "render", sahte_hf_render)
    with pytest.raises(RuntimeError, match="render çöktü"):
        render._render_one(tmp_path / "comp", out, "draft", 30)
    assert not out.with_suffix(".tmp.mp4").exists()
    assert not out.exists()
