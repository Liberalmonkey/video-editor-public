"""kapak_prompt: agy zemin prompt'u ve dış platform master prompt'u (ADR 0052). Saf fonksiyonlar, agy'siz."""
import pytest

from vedit import kapak_prompt as kp

BRIEF = {"sahne": "A creator at a desk holding a glowing laptop", "ifade": "confident half smile",
         "kompozisyon": "subject on the right third, chest-up", "isik": "warm key light, cool rim light",
         "palet": "deep navy with one orange accent", "yazi_alani": "the left third",
         "satir1": "Claude Code", "satir2": "artık KURGU yapıyor", "vurgu": "KURGU", "kalip": "klasik", "stil": "turuncu"}
REFS = [("kare", "kare-3.jpg"), ("yuz", "yuz-ben.png"), ("stil", "stil-ornek.jpg")]


@pytest.mark.parametrize("platform", ["youtube", "instagram"])
@pytest.mark.parametrize("hedef", list(kp.HEDEFLER))
def test_her_hedef_yazili_ve_bos(hedef, platform):
    yazili = kp.master(BRIEF, platform, hedef, True, REFS)
    bos = kp.master(BRIEF, platform, hedef, False, REFS)
    assert '"Claude Code"' in yazili["prompt"] and '"artık KURGU yapıyor"' in yazili["prompt"]
    assert "Claude Code" not in bos["prompt"]
    assert ("--no text" if hedef == "midjourney" else "No text") in bos["prompt"]
    assert ["Oran", kp.ORAN[platform]] in yazili["ayar"]
    if hedef == "midjourney":
        assert f"--ar {kp.ORAN[platform]}" in yazili["prompt"] and any("güvenilir" in n for n in yazili["notlar"])
    else:
        assert "Turkish letters" in yazili["prompt"]


def test_referans_sirasi_kimlik_ve_stil():
    m = kp.master(BRIEF, "youtube", "nano-banana-pro", False, REFS)
    assert [(e["no"], e["rol"], e["dosya"]) for e in m["ekler"]] == [(1, "kare", "kare-3.jpg"), (2, "yuz", "yuz-ben.png"),
                                                                     (3, "stil", "stil-ornek.jpg")]
    assert "Image 1 and Image 2 exactly the same" in m["prompt"]
    assert "Use Image 3 only as a style reference" in m["prompt"]
    assert "bottom-right corner" in m["prompt"]  # YouTube süre rozeti
    assert "bottom-right" not in kp.master(BRIEF, "instagram", "nano-banana-pro", False, REFS)["prompt"]


def test_ref_siniri_ve_midjourney_referansi():
    cok = [("yuz", f"y{i}.png") for i in range(6)]
    assert len(kp.master(BRIEF, "youtube", "midjourney", False, cok)["ekler"]) == kp.HEDEFLER["midjourney"]["ref_sinir"]
    mj = kp.master(BRIEF, "youtube", "midjourney", False, REFS)["prompt"]
    assert "--oref" in mj and "--sref" in mj
    assert "--oref" not in kp.master(BRIEF, "youtube", "midjourney", False, [])["prompt"]


def test_vurgu_kutu_ve_renk():
    css = {"--vurgu": "#E52521", "--kontur-k": "0.35vh"}
    m = kp.master(BRIEF, "youtube", "ideogram", True, [], css, kutu=True)["prompt"]
    assert 'The word "KURGU" sits inside a solid #E52521 box' in m and "thick black outline" in m
    duz = kp.master(BRIEF, "youtube", "ideogram", True, [], {"--kontur-k": "0"}, kutu=False)["prompt"]
    assert 'The word "KURGU" is coloured bright orange' in duz and "no outline" in duz


def test_yazisiz_kalip_ve_bolunmus():
    yazisiz = {**BRIEF, "kalip": "yazisiz"}
    assert "No text anywhere" in kp.master(yazisiz, "youtube", "chatgpt", True)["prompt"]
    bolunmus = {**BRIEF, "kalip": "bolunmus", "satir1": "ÖNCE", "satir2": "SONRA"}
    p = kp.master(bolunmus, "youtube", "nano-banana-21", True)["prompt"]
    assert '"ÖNCE" over the left half and "SONRA" over the right half' in p


def test_eski_brief_prompt_aynen_ve_agy_prompt():
    eski = {"prompt": "dark desk, laptop glow"}
    assert kp.govde(eski, "youtube") == "dark desk, laptop glow"
    assert kp.agy_prompt(eski, "instagram", "rozet").startswith("dark desk, laptop glow The scene tells")
    yeni = kp.agy_prompt(BRIEF, "youtube", "klasik", REFS)
    assert yeni.startswith("A creator at a desk") and "Keep the left third clean and empty" in yeni
    assert kp.REF_KURALI.strip() in yeni and kp.STIL_KURALI.strip() in yeni
    assert "Use the reference frame" not in kp.agy_prompt(BRIEF, "youtube", "klasik", [])
    # elle yazılan prompt yapılı alanları ezer
    assert kp.agy_prompt({**BRIEF, "prompt": "ELLE"}, "youtube").startswith("ELLE")


def test_yazi_alani_yerlesimden():
    b = {"sahne": "x", "yerlesim": "sag"}
    assert kp.yazi_alani(b, "youtube") == "the right third"
    assert kp.yazi_alani({"sahne": "x"}, "instagram") == "the upper part of the central area"


def test_master_md_tum_hedefler_ve_ref_metni():
    md = kp.master_md(BRIEF, "youtube", REFS, baslik="deneme")
    for h in kp.HEDEFLER.values():
        assert md.count(f"## {h['ad']} ·") == 2
    assert "1. `kare-3.jpg`" in md
    assert kp.ref_metni([("kare", "/a/k.jpg"), ("stil", "/a/s.jpg")]).startswith("Image 1 (/a/k.jpg) is a frame")
    with pytest.raises(ValueError):
        kp.master(BRIEF, "youtube", "yok", True)
