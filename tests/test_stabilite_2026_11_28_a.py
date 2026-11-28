"""2026-11-28 stabilite ve güvenlik düzeltmeleri için regresyon testleri (Bulgu 1, 2, 4, 5, 6, 9, 10, 12)."""

from __future__ import annotations

import errno
import json
import subprocess
import threading
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi import HTTPException
from fastapi.testclient import TestClient

from vedit import ekip as ekip_mod
from vedit import ff, hizli, kurgu, motorlar, paths, teslim
from vedit.ekip_sema import EkipAyar
from vedit.schemas import Kurgu
from vedit.studio import ekip as ekip_api
from vedit.studio import gorsel, isler, ortak
from vedit.studio.app import create_app

HOST = "127.0.0.1:8765"
ORIGIN = {"origin": f"http://{HOST}"}


@pytest.fixture
def istemci(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    monkeypatch.setattr(paths, "STUDIOS", tmp_path / "studios")
    monkeypatch.setattr(paths, "LIBRARY", tmp_path / "lib")
    monkeypatch.setattr(paths, "FONTS_DIR", tmp_path / "lib" / "fonts")
    (tmp_path / "lib" / "fonts").mkdir(parents=True)
    (tmp_path / "in" / "instagram" / "x").mkdir(parents=True)
    (tmp_path / "out" / "instagram" / "x" / "work").mkdir(parents=True)
    monkeypatch.setattr(ortak, "send2trash", lambda y: Path(y).unlink() if Path(y).is_file() else None)
    c = TestClient(create_app("t0k", izinli_hostlar={HOST}), base_url=f"http://{HOST}", follow_redirects=False)
    c.get("/?token=t0k")
    return c, tmp_path


@pytest.mark.parametrize("yol", [
    "Work/edit/kurgu.json",
    "./work/edit/kurgu.json",
    "work\\edit\\kurgu.json",
    "a/../work/edit/kurgu.json",
])
def test_bulgu1_dosya_sil_work_baypasini_reddeder(istemci, yol):
    c, t = istemci
    kurgu_f = t / "out" / "instagram" / "x" / "work" / "edit" / "kurgu.json"
    kurgu_f.parent.mkdir(parents=True, exist_ok=True)
    kurgu_f.write_text("{}", encoding="utf-8")
    (t / "out" / "instagram" / "x" / "a").mkdir(exist_ok=True)
    r = c.delete("/api/dosya/instagram/x/outputs", params={"yol": yol}, headers=ORIGIN)
    assert r.status_code == 403
    assert kurgu_f.exists()


def test_bulgu4_stil_koku_gecersiz_yolda_404_verir_gecerli_yollar_calisir(istemci):
    c, t = istemci
    st = t / "studios"
    (st / "instagram" / "styles" / "stil-a").mkdir(parents=True)
    (st / "instagram" / "studio.yaml").write_text("style: varsayilan\n", encoding="utf-8")
    (st / "gizli.txt").write_text("kok-gizli", encoding="utf-8")
    (st / "instagram" / "styles" / "stil-gizli.txt").write_text("styles-gizli", encoding="utf-8")
    (st / "instagram" / "styles" / "stil-a" / "logo.png").write_bytes(b"PNG")

    assert c.get("/dosya/instagram/x/stil/instagram/stil-a/logo.png").status_code == 200
    assert c.get("/dosya/instagram/x/stil/instagram/styles/stil-a/logo.png").status_code == 200

    for kotu in (
        "/dosya/instagram/x/stil/instagram/studio.yaml",
        "/dosya/instagram/x/stil/gizli.txt",
        "/dosya/instagram/x/stil/instagram/styles/stil-gizli.txt",
        "/dosya/instagram/x/stil/instagram/stil-a/..%2F..%2Fstudio.yaml",
    ):
        r = c.get(kotu)
        assert r.status_code == 404, kotu


def test_bulgu5_hizli_denetim_sessiz_videoda_cokmez(tmp_path, monkeypatch, capsys):
    from vedit import slop

    v = tmp_path / "sessiz.mp4"
    v.write_bytes(b"v")
    monkeypatch.setattr(ff, "probe", lambda p: {"duration": 2.0, "video": {"width": 1080, "height": 1920, "fps": 30.0}})
    monkeypatch.setattr(ff, "loudness", lambda p: {})
    monkeypatch.setattr(ff, "contact_sheet", lambda *a, **kw: tmp_path / "sheet.jpg")
    monkeypatch.setattr(slop, "calistir", lambda *a, **kw: {"bulgular": []})

    sonuc = hizli.denetim(v, work=tmp_path)
    assert sonuc["loudness"] == {}
    qa_json = json.loads((tmp_path / "qa" / "denetim.json").read_text(encoding="utf-8"))
    assert qa_json["ses_tamam"] is None
    assert "| Ses | ses akışı yok |" in capsys.readouterr().out


def test_bulgu9_public_hazirla_hardlink_hatasi_ve_fileexists(tmp_path, monkeypatch):
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    (fonts / "A.ttf").write_bytes(b"font-a")
    (fonts / "B.ttf").write_bytes(b"font-b")
    monkeypatch.setattr(paths, "FONTS_DIR", fonts)
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    p = hizli.Proje("instagram", "x")

    # OSError (ör. EXDEV) -> shutil.copy2 yedeklemesi
    monkeypatch.setattr(Path, "hardlink_to", lambda self, src: (_ for _ in ()).throw(OSError(errno.EXDEV, "cross-device")))
    hizli._public_hazirla(p)
    assert (p.work / "public" / "fonts" / "A.ttf").read_bytes() == b"font-a"
    assert (p.work / "public" / "fonts" / "B.ttf").read_bytes() == b"font-b"

    # FileExistsError yarışında yutulmalı
    (p.work / "public" / "fonts" / "B.ttf").unlink()
    monkeypatch.setattr(Path, "hardlink_to", lambda self, src: (_ for _ in ()).throw(FileExistsError("var")))
    hizli._public_hazirla(p)


def test_bulgu10_teslim_bozuk_kurgu_gecersiz_kaynak_ve_kucuk_resim_yok(istemci, monkeypatch):
    c, t = istemci
    # (a) Bozuk/0-bayt teslim dosyası Teslim panelini 500 yapmamalı
    (t / "out" / "instagram" / "x" / "bozuk.mp4").write_bytes(b"")
    monkeypatch.setattr(teslim, "_akislar", lambda p: (_ for _ in ()).throw(ValueError("Video akışı yok")))
    r_teslim = c.get("/api/teslim/instagram/x")
    assert r_teslim.status_code == 200 and r_teslim.json()["son"] is None

    # (b) kurgu_oku içindeki geçersiz kaynak yolu 422 dönmeli
    k = Kurgu.model_validate({
        "kaynaklar": {"K1": {"yol": "inputs:../../kac.mp4", "sure": 1.0, "ses": False}},
        "izler": [{"id": "V1", "tur": "video"}],
        "klipler": [],
    })
    kurgu.yaz(t / "out" / "instagram" / "x" / "work", k)
    r_kurgu = c.get("/api/kurgu/instagram/x")
    assert r_kurgu.status_code == 422

    # (c) ff.still çıktı üretmezse kucuk() 415 dönmeli (500 değil)
    (t / "in" / "instagram" / "x" / "v.mp4").write_bytes(b"v")
    monkeypatch.setattr(ff, "still", lambda *a, **kw: a[1])
    r_kucuk = c.get("/api/kucuk/instagram/x/inputs", params={"yol": "v.mp4"})
    assert r_kucuk.status_code == 415


def test_bulgu2_isler_tekil_kilit_iptal_yarisi_ve_stdout_kapanisi(monkeypatch):
    eski_k, eski_a = isler.kuyruk, isler.ajan
    try:
        isler.kuyruk = None
        isler.ajan = None
        olusan: list[object] = []

        class SahteKuyruk:
            def __init__(self):
                olusan.append(self)

        with monkeypatch.context() as m:
            m.setattr(isler, "Kuyruk", SahteKuyruk)
            bariyer = threading.Barrier(6)
            sonuclar = []

            def cagir(fn):
                bariyer.wait()
                sonuclar.append(fn())

            th = [threading.Thread(target=cagir, args=(isler._k,)) for _ in range(3)] + [
                threading.Thread(target=cagir, args=(isler.ajan_kuyrugu,)) for _ in range(3)
            ]
            for t_ in th:
                t_.start()
            for t_ in th:
                t_.join(timeout=5)
            assert len(olusan) == 2
            assert len({id(x) for x in sonuclar}) == 2
    finally:
        isler.kuyruk, isler.ajan = eski_k, eski_a

    # İptal edilmiş iş Popen başlatmamalı ve hata durumunda s.stdout kapatılmalı
    k = object.__new__(isler.Kuyruk)
    k.exe = Path("python")
    k.isler = []
    k._kilit = threading.Lock()

    popen_cagrildi = []
    monkeypatch.setattr(isler.subprocess, "Popen", lambda *a, **kw: popen_cagrildi.append(1))
    iptal_is = isler.Is(id=99, komut="taslak", baslik="t", args=[], iptal=True, durum="calisiyor")
    k._calistir(iptal_is)
    assert popen_cagrildi == []
    assert iptal_is.durum == "iptal"

    class BozukStdout:
        def __init__(self):
            self.kapandi = False

        def __iter__(self):
            raise RuntimeError("okuma hatası")

        def close(self):
            self.kapandi = True

    sahte_stdout = BozukStdout()

    class SahteSurec:
        stdout = sahte_stdout
        pid = 1234

        def poll(self):
            return 0

        def wait(self):
            return 0

    monkeypatch.setattr(isler.subprocess, "Popen", lambda *a, **kw: SahteSurec())
    hata_is = isler.Is(id=100, komut="taslak", baslik="t", args=[])
    with pytest.raises(RuntimeError, match="okuma hatası"):
        k._calistir(hata_is)
    assert sahte_stdout.kapandi is True


def test_bulgu12_ekip_atomik_kilitli_yazim_ve_bozuk_meta(tmp_path, monkeypatch):
    durum = {
        "claude": {"ad": "Claude Code", "kurulu": True, "modeller": [{"id": "claude-opus-5-5"}, {"id": "claude-sonnet-5-5"}]},
        "antigravity": {"ad": "Antigravity", "kurulu": True, "modeller": [{"id": "gemini-4-neon-high"}, {"id": "gemini-4-argon-high"},
                                                                          {"id": "gemini-4-neon-xhigh"}]},
        "codex": {"ad": "Codex", "kurulu": False, "modeller": []},
        "opencode": {"ad": "OpenCode", "kurulu": False, "modeller": []},
    }
    monkeypatch.setattr(motorlar, "durum", lambda: durum)
    monkeypatch.setattr(ekip_mod, "GLOBAL", tmp_path / "ekip.json")
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    (tmp_path / "in" / "instagram" / "p").mkdir(parents=True)

    ayar = EkipAyar().model_dump()
    bariyer = threading.Barrier(4)
    hatalar = []

    def yaz(i: int):
        try:
            bariyer.wait()
            ekip_api.onayar_yaz(f"ayar-{i}", ayar)
        except Exception as e:  # noqa: BLE001
            hatalar.append(e)

    th = [threading.Thread(target=yaz, args=(i,)) for i in range(4)]
    for t_ in th:
        t_.start()
    for t_ in th:
        t_.join(timeout=5)
    assert hatalar == []
    kayit = json.loads((tmp_path / "ekip.json").read_text(encoding="utf-8"))
    assert sorted(kayit["onayarlar"]) == ["ayar-0", "ayar-1", "ayar-2", "ayar-3"]

    kok = tmp_path / "out" / "instagram" / "p" / "work" / "edit" / "ekip" / "plan"
    kok.mkdir(parents=True)
    (kok / "O.cikti.txt").write_text("merhaba\n", encoding="utf-8")
    (kok / "O.meta.json").write_text("{bozuk", encoding="utf-8")
    yanit = ekip_api.cikti("instagram", "p", "O")
    assert yanit["satirlar"] == ["merhaba"] and yanit["meta"] is None


def test_bulgu6_gorsel_benzersiz_gecici_temizlik_ve_timeout(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    p = hizli.Proje("instagram", "x")
    p.girdi.mkdir(parents=True)
    medya_f = p.girdi / "v.mp4"
    medya_f.write_bytes(b"video")

    timeout_degerleri = []

    def sahte_run(cmd, **kw):
        timeout_degerleri.append(kw.get("timeout"))
        raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))

    monkeypatch.setattr(gorsel.subprocess, "run", sahte_run)
    with pytest.raises(HTTPException) as exc:
        gorsel.peak(p, medya_f)
    assert exc.value.status_code == 415
    assert timeout_degerleri == [300]

    # os.replace başarısız olursa benzersiz geçici dosya finally'de temizlenmeli
    monkeypatch.setattr(
        gorsel.subprocess,
        "run",
        lambda *a, **kw: type("R", (), {"returncode": 0, "stdout": b""})(),
    )
    monkeypatch.setattr(gorsel.os, "replace", lambda src, dst: (_ for _ in ()).throw(OSError("replace hatası")))
    with pytest.raises(OSError):
        gorsel.peak(p, medya_f)
    assert list((p.work / "gorsel").glob("*.tmp")) == []

    # serit: ff.ffmpeg hata atarsa 415 dönmeli ve geçici .tmp.jpg bırakmamalı
    monkeypatch.setattr(ff, "probe_ob", lambda f: {"duration": 3.0})

    def sahte_ffmpeg(*a, **kw):
        Path(a[-1]).write_bytes(b"yarim")
        raise RuntimeError("ffmpeg çöktü")

    monkeypatch.setattr(ff, "ffmpeg", sahte_ffmpeg)
    with pytest.raises(HTTPException) as exc2:
        gorsel.serit(p, medya_f)
    assert exc2.value.status_code == 415
    assert list((p.work / "proxy").glob("*.tmp.jpg")) == []
