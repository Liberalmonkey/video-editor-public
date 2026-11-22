"""Transkript düzeltme sözlüğü (ADR 0041)."""
import json

from vedit import hizli, sozluk

S = {"isimler": ["Claude Code", "Antigravity"], "duzelt": {"cloud code": "Claude Code", "anti gravity": "Antigravity",
                                                          "open code": "OpenCode"}}


def W(*ws):
    return [{"w": w, "s": i * 1.0, "e": i * 1.0 + 0.5, "p": 0.9 - i * 0.1} for i, w in enumerate(ws)]


def test_cok_kelimeli_duzeltme_zamani_korur():
    t = {"segments": [{"text": "Bugün Cloud Code, ve anti-gravity ile cloud bilişim.",
                       "words": W("Bugün", "Cloud", "Code,", "ve", "anti", "gravity", "ile", "cloud", "bilişim.")}]}
    r = sozluk.uygula(t, S)
    seg = r["segments"][0]
    assert seg["text"] == "Bugün Claude Code, ve Antigravity ile cloud bilişim."
    assert [w["w"] for w in seg["words"]] == ["Bugün", "Claude Code,", "ve", "Antigravity", "ile", "cloud", "bilişim."]
    cc = seg["words"][1]
    assert (cc["s"], cc["e"], cc["p"]) == (1.0, 2.5, 0.7)  # ilk kelimenin başı, son kelimenin sonu, düşük güven
    assert t["segments"][0]["words"][1]["w"] == "Cloud", "girdi değişmez (önbellek ham kalır)"


def test_bos_sozluk_ve_ipucu():
    t = {"segments": [{"text": "a", "words": W("a")}]}
    assert sozluk.uygula(t, {"isimler": [], "duzelt": {}}) is t
    assert sozluk.ipucu(S) == "Claude Code, Antigravity."
    assert sozluk.ipucu({"isimler": [], "duzelt": {}}) is None


def test_proje_sozlugu_gecerli_ve_tek_kelime_tuzagi_yok():
    d = json.loads(sozluk.DOSYA.read_text(encoding="utf-8"))
    assert d["isimler"] and d["duzelt"]
    gercek = {"cloud", "code", "open", "kod", "gravity"}
    assert not [a for a in d["duzelt"] if a.casefold() in gercek], "tek başına gerçek kelime her geçişte değişirdi"


def test_hazirla_onbellekten_okurken_sozlugu_uygular(tmp_path, monkeypatch):
    video = tmp_path / "a.mp4"
    video.write_bytes(b"x")
    on = tmp_path / "work" / "analysis" / "yazi" / f"a-{hizli._ozet(video)}.json"
    on.parent.mkdir(parents=True)
    on.write_text(json.dumps({"segments": [{"text": "open code", "words": W("open", "code")}]}), encoding="utf-8")
    monkeypatch.setattr(sozluk, "yukle", lambda yol=sozluk.DOSYA: S)
    r = hizli.yazi(video, tmp_path / "work", dil="tr", prompt=None)
    assert r["segments"][0]["text"] == "OpenCode" and [w["w"] for w in r["segments"][0]["words"]] == ["OpenCode"]
    assert "open code" in on.read_text(encoding="utf-8"), "önbellek ham kalır"
