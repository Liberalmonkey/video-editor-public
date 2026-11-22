"""vedit gorsel: agy çağrısı taklit edilir, brain klasöründen kopya ve log doğrulanır."""
import json
import os
import subprocess
import time

import pytest

from vedit import gorsel


def test_uret_kopyalar_ve_loglar(tmp_path, monkeypatch):
    brain = tmp_path / "brain"
    (brain / "abc").mkdir(parents=True)
    eski = brain / "abc" / "eski.png"
    eski.write_bytes(b"eski")
    os.utime(eski, (time.time() - 100, time.time() - 100))
    (brain / "abc" / "kedi_1.jpg").write_bytes(b"yeni")
    monkeypatch.setattr(gorsel, "BRAIN", brain)
    monkeypatch.setattr(gorsel, "agy_yolu", lambda: "agy")
    yanit = {"conversation_id": "abc", "status": "SUCCESS", "duration_seconds": 97.9}
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, "log\n" + json.dumps(yanit), ""))

    out = gorsel.uret("kedi | pencere", tmp_path / "work" / "gorsel" / "kedi")

    assert out.name == "kedi.jpg" and out.read_bytes() == b"yeni"
    log = (tmp_path / "work" / "gorsel" / "log.md").read_text(encoding="utf-8")
    assert "| agy | 16:9 | kedi / pencere | kedi.jpg, 98 sn |" in log


def test_gorsel_yoksa_durur(tmp_path):
    with pytest.raises(SystemExit, match="kota"):
        gorsel.son_gorsel(tmp_path / "yok")


def test_uret_referans_ve_klasor_bayragi_ekler(tmp_path, monkeypatch):
    brain = tmp_path / "brain"
    (brain / "abc").mkdir(parents=True)
    (brain / "abc" / "out.jpg").write_bytes(b"img")
    ref = tmp_path / "kareler" / "kare-1.jpg"
    ref.parent.mkdir(parents=True)
    ref.write_bytes(b"ref")
    monkeypatch.setattr(gorsel, "BRAIN", brain)
    monkeypatch.setattr(gorsel, "agy_yolu", lambda: "agy")
    komutlar = []
    yanit = {"conversation_id": "abc", "status": "SUCCESS", "duration_seconds": 12.0}

    def sahte_run(cmd, *a, **k):
        komutlar.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, json.dumps(yanit), "")

    monkeypatch.setattr(subprocess, "run", sahte_run)
    out = gorsel.uret("stüdyo portresi", tmp_path / "work" / "zemin-1", refler=[ref])
    assert out.exists()
    cmd = komutlar[0]
    assert "--add-dir" in cmd and str(ref.resolve().parent) in cmd
    assert cmd[-2] == "-p"
    assert str(ref.resolve()) in cmd[-1] and "reference image file(s)" in cmd[-1]
    log = (tmp_path / "work" / "log.md").read_text(encoding="utf-8")
    assert "kare-1.jpg" in log
