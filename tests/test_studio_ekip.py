"""Stüdyo ekip modu (ADR 0053): grup ve ezme doğrulaması canlı motor listesine karşı, iş argümanı, ön ayar, durum ve çıktı uçları."""
import json

import pytest

pytest.importorskip("fastapi")

from fastapi import HTTPException

from vedit import ekip, motorlar, paths
from vedit.ekip_sema import EkipAyar
from vedit.studio import ekip as ekip_api
from vedit.studio import isler

DURUM = {"claude": {"ad": "Claude Code", "kurulu": True, "modeller": [{"id": "claude-opus-5-5"}, {"id": "claude-sonnet-5-5"}]},
         "antigravity": {"ad": "Antigravity", "kurulu": True, "modeller": [{"id": "gemini-4-neon-high"}, {"id": "gemini-4-argon-high"},
                                                                            {"id": "gemini-4-neon-xhigh"}]},
         "codex": {"ad": "Codex", "kurulu": False, "modeller": []}, "opencode": {"ad": "OpenCode", "kurulu": False, "modeller": []}}


@pytest.fixture
def ortam(tmp_path, monkeypatch):
    monkeypatch.setattr(motorlar, "durum", lambda: DURUM)
    monkeypatch.setattr(ekip, "GLOBAL", tmp_path / "ekip.json")
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "inputs")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "outputs")
    (tmp_path / "inputs" / "instagram" / "p").mkdir(parents=True)
    return tmp_path


def test_kurulu_olmayan_motor_ve_listede_olmayan_model_reddedilir(ortam):
    a = EkipAyar().model_dump()
    assert ekip_api.dogrula(a).gruplar["orkestrator"].model == "claude-opus-5-5"
    a["gruplar"]["kk"] = {"motor": "codex", "model": "gpt-5.6-terra"}
    with pytest.raises(HTTPException, match="kurulu değil"):
        ekip_api.dogrula(a)
    a["gruplar"]["kk"] = {"motor": "antigravity", "model": "uydurma"}
    with pytest.raises(HTTPException, match="olmayan model"):
        ekip_api.dogrula(a)
    a["gruplar"]["kk"] = {"motor": "claude", "seviye": "ultra"}
    with pytest.raises(HTTPException, match="seviye"):
        ekip_api.dogrula(a)
    a = EkipAyar().model_dump()
    a["ezme"] = {"E3": {"motor": "codex"}}
    with pytest.raises(HTTPException, match="E3: motor kurulu değil"):
        ekip_api.dogrula(a)
    with pytest.raises(HTTPException):
        ekip_api.dogrula({**EkipAyar().model_dump(), "ekip_seviye": "ultra"})


def test_ekip_isi_dosyaya_yazilir_ve_ekip_bayragiyla_baslar(ortam):
    args = isler.arguman(isler.Istek(komut="ai-edit", studyo="instagram", ad="p", ekip=True,
                                     ekip_ayar={**EkipAyar().model_dump(), "ekip_seviye": "xhigh"}, notu="hızlı", motion="orta"))
    assert args[:2] == ["ai-edit", "instagram/p"] and "--ekip" in args and "--motor" not in args
    f = args[args.index("--ekip-dosyasi") + 1]
    yazilan = json.loads(open(f, encoding="utf-8").read())
    assert yazilan["motion"] == "orta" and yazilan["ekip_seviye"] == "xhigh"
    assert "--not=hızlı" in args and args[args.index("--motion") + 1] == "orta"


def test_onayar_kaydet_varsayilan_durum_ve_cikti(ortam):
    r = ekip_api.onayar_yaz("hizli", EkipAyar(ekip_seviye="low").model_dump(), varsayilan=True)
    assert r["varsayilan"] == "hizli"
    g = json.loads((ortam / "ekip.json").read_text(encoding="utf-8"))
    assert g["onayarlar"]["hizli"]["ekip_seviye"] == "low"
    with pytest.raises(HTTPException):
        ekip_api.onayar_yaz("Kötü Ad", EkipAyar().model_dump())
    assert ekip_api.durum("instagram", "p") == {"yok": True}
    assert ekip_api.proje_oku("instagram", "p")["etkin"]["ekip_seviye"] == "low"
    assert ekip_api.ekip_oku()["seviyeler"]["max"] == {"editor": 10, "kk": 5, "en_cok": 15}
    # Orkestratör birden çok kapıda yazar: en yeni çıktı döner.
    import os
    import time
    kok = ortam / "outputs" / "instagram" / "p" / "work" / "edit" / "ekip"
    for i, asama in enumerate(("plan", "kapi")):
        (kok / asama).mkdir(parents=True)
        f = kok / asama / "O.cikti.txt"
        f.write_text(f"{asama} satırı", encoding="utf-8")
        os.utime(f, (time.time() + i, time.time() + i))
    c = ekip_api.cikti("instagram", "p", "O")
    assert c["asama"] == "kapi" and c["satirlar"] == ["kapi satırı"]
    assert ekip_api.cikti("instagram", "p", "E10")["satirlar"] == []
    with pytest.raises(HTTPException):
        ekip_api.cikti("instagram", "p", "E11")
