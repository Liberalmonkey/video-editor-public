"""Stüdyo ekip modu (ADR 0044): slot doğrulama canlı motor listesine karşı, iş argümanı, ön ayar ve durum uçları."""
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
    assert ekip_api.dogrula(a).slotlar["E1"].model == "claude-opus-5-5"
    a["slotlar"]["K1"] = {"motor": "codex", "model": "gpt-5.6-terra"}
    with pytest.raises(HTTPException, match="kurulu değil"):
        ekip_api.dogrula(a)
    a["slotlar"]["K1"] = {"motor": "antigravity", "model": "uydurma"}
    with pytest.raises(HTTPException, match="olmayan model"):
        ekip_api.dogrula(a)
    a["slotlar"]["K1"] = {"motor": "claude", "seviye": "ultra"}
    with pytest.raises(HTTPException, match="seviye"):
        ekip_api.dogrula(a)


def test_ekip_isi_dosyaya_yazilir_ve_ekip_bayragiyla_baslar(ortam):
    args = isler.arguman(isler.Istek(komut="ai-edit", studyo="instagram", ad="p", ekip=True, ekip_ayar=EkipAyar().model_dump(),
                                     notu="hızlı", motion="orta"))
    assert args[:2] == ["ai-edit", "instagram/p"] and "--ekip" in args and "--motor" not in args
    f = args[args.index("--ekip-dosyasi") + 1]
    assert json.loads(open(f, encoding="utf-8").read())["motion"] == "orta"
    assert "--not=hızlı" in args and args[args.index("--motion") + 1] == "orta"


def test_onayar_kaydet_varsayilan_ve_durum(ortam):
    r = ekip_api.onayar_yaz("hizli", EkipAyar(tur=2).model_dump(), varsayilan=True)
    assert r["varsayilan"] == "hizli"
    g = json.loads((ortam / "ekip.json").read_text(encoding="utf-8"))
    assert g["onayarlar"]["hizli"]["tur"] == 2
    with pytest.raises(HTTPException):
        ekip_api.onayar_yaz("Kötü Ad", EkipAyar().model_dump())
    assert ekip_api.durum("instagram", "p") == {"yok": True}
    assert ekip_api.proje_oku("instagram", "p")["etkin"]["tur"] == 2
