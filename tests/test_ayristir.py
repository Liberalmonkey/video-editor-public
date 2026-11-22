import shutil
from types import SimpleNamespace
import subprocess
import time
from pathlib import Path

import pytest

from vedit import ayristir, cli, ff


def _kaynak(tmp_path: Path, sn: float = 5.0) -> Path:
    """440 Hz 'müzik' + 3 Hz genlik modülasyonlu 220 Hz 'konuşma' karışımı."""
    f = tmp_path / "klip.wav"
    ff.ffmpeg("-f", "lavfi", "-i", f"sine=f=440:d={sn}", "-f", "lavfi",
              "-i", f"aevalsrc='0.5*sin(2*PI*220*t)*(0.5+0.5*sin(2*PI*3*t))':d={sn}",
              "-filter_complex", "amix=inputs=2", "-ar", "44100", str(f))
    return f


def _sahte_demucs(args, **_):
    """Demucs yerine girdi wav'ını iki kanal adına kopyalar."""
    cikti = Path(args[args.index("-o") + 1]) / "htdemucs"
    cikti.mkdir(parents=True, exist_ok=True)
    for ad in (("vocals", "drums", "bass", "other") if "--two-stems" not in args else ("vocals", "no_vocals")):
        shutil.copy(args[-1], cikti / f"{ad}.wav")
    return subprocess.CompletedProcess(args, 0, "", "")


def test_yollar_ve_onbellek(tmp_path, monkeypatch):
    kaynak, hedef = _kaynak(tmp_path), tmp_path / "ayrik"
    monkeypatch.setattr(ayristir, "hazir", lambda: True)
    cagri, gercek = [], subprocess.run

    def run(a, **k):  # yalnız Demucs çağrısı sahte; ffmpeg gerçek
        if "demucs.separate" not in a:
            return gercek(a, **k)
        cagri.append(a)
        return _sahte_demucs(a)
    monkeypatch.setattr(subprocess, "run", run)
    r = ayristir.ayir(kaynak, hedef)
    assert r["vokal"] == hedef / "klip.vokal.wav" and r["muzik"] == hedef / "klip.muzik.wav"
    assert not r["onbellek"] and len(cagri) == 1
    assert "--two-stems" in cagri[0] and "htdemucs" in cagri[0]
    info = ff.probe(r["vokal"])["audio"]
    assert (info["sample_rate"], info["channels"]) == (48000, 2)
    assert not list(hedef.glob("_ayristir_*"))
    r2 = ayristir.ayir(kaynak, hedef)
    assert r2["onbellek"] and len(cagri) == 1


def _demucs_sahte(monkeypatch):
    cagri, gercek = [], subprocess.run

    def run(a, **k):
        if "demucs.separate" not in a:
            return gercek(a, **k)
        cagri.append(a)
        return _sahte_demucs(a)
    monkeypatch.setattr(ayristir, "hazir", lambda: True)
    monkeypatch.setattr(subprocess, "run", run)
    return cagri


def test_dort_kanal_yollar_ve_onbellek(tmp_path, monkeypatch):
    kaynak, hedef = _kaynak(tmp_path), tmp_path / "ayrik"
    cagri = _demucs_sahte(monkeypatch)
    r = ayristir.ayir(kaynak, hedef, stem=4)
    assert {k for k in r} == {"vokal", "davul", "bas", "diger", "muzik", "sure", "onbellek"}
    assert r["vokal"] == hedef / "klip.s4.vokal.wav" and "--two-stems" not in cagri[0]
    for k in ("vokal", "davul", "bas", "diger", "muzik"):
        assert abs(ff.probe(r[k])["duration"] - 5.0) <= 0.1
    assert ayristir.ayir(kaynak, hedef, stem=4)["onbellek"] and len(cagri) == 1
    assert not ayristir.ayir(kaynak, hedef)["onbellek"] and len(cagri) == 2, "iki kipin önbelleği ayrı"
    assert ayristir.onbellekte(kaynak, hedef, 2) and ayristir.onbellekte(kaynak, hedef, 4)
    with pytest.raises(ValueError):
        ayristir.ayir(kaynak, hedef, stem=3)


def _proje(tmp_path, monkeypatch):
    p = SimpleNamespace(girdi=tmp_path / "in", cikti=tmp_path / "out", work=tmp_path / "out" / "work", studyo="s", ad="p")
    p.girdi.mkdir()
    klip = _kaynak(p.girdi, 1)
    for ad in ("10.wav", "2.wav"):
        shutil.copy(klip, p.girdi / ad)
    (p.girdi / "not.txt").write_text("x")
    monkeypatch.setattr("vedit.hizli.bul", lambda ref: p)
    return p


def test_hepsi_dogal_sirada_ayirir(tmp_path, monkeypatch, capsys):
    p = _proje(tmp_path, monkeypatch)
    cagri = _demucs_sahte(monkeypatch)
    cli.cmd_ayristir(SimpleNamespace(ref="s/p", yol=None, hepsi=True, stem=4))
    cikti = capsys.readouterr().out
    assert len(cagri) == 3
    assert cikti.index("2.wav:") < cikti.index("10.wav:") < cikti.index("klip.wav:") and "davul:" in cikti and "txt" not in cikti


def test_ses_cikar_bicimler_ve_uzerine_yazmaz(tmp_path, monkeypatch, capsys):
    p = _proje(tmp_path, monkeypatch)
    cli.cmd_ses_cikar(SimpleNamespace(ref="s/p", yol="2.wav", hepsi=False, bicim="mp3"))
    cli.cmd_ses_cikar(SimpleNamespace(ref="s/p", yol="2.wav", hepsi=False, bicim="mp3"))
    cli.cmd_ses_cikar(SimpleNamespace(ref="s/p", yol="2.wav", hepsi=False, bicim="m4a"))
    assert sorted(f.name for f in (p.cikti / "ses").iterdir()) == ["2-2.mp3", "2.m4a", "2.mp3"]
    i = ff.probe(p.cikti / "ses" / "2.mp3")["audio"]
    assert (i["sample_rate"], i["channels"]) == (48000, 2)
    with pytest.raises(ValueError):
        ayristir.ses_cikar(p.girdi / "2.wav", p.cikti / "ses", "ogg")
    sessiz = tmp_path / "v.mp4"
    ff.ffmpeg("-f", "lavfi", "-i", "color=c=black:s=64x64:d=1", str(sessiz))
    with pytest.raises(RuntimeError, match="ses yok"):
        ayristir.ses_cikar(sessiz, p.cikti / "ses")


def test_kurulu_degilse_hata(tmp_path, monkeypatch):
    monkeypatch.setattr(ayristir, "hazir", lambda: False)
    with pytest.raises(RuntimeError, match="kurulu değil"):
        ayristir.ayir(_kaynak(tmp_path, 1), tmp_path / "ayrik")


@pytest.mark.skipif(not ayristir.hazir(), reason=".venv-ayristir kurulu değil")
def test_gercek_demucs(tmp_path):
    kaynak = _kaynak(tmp_path)
    t0 = time.time()
    r = ayristir.ayir(kaynak, tmp_path / "ayrik")
    print(f"\nDemucs 5 sn ayırma: {time.time() - t0:.1f} sn")
    for k in ("vokal", "muzik"):
        assert abs(ff.probe(r[k])["duration"] - 5.0) <= 0.05
