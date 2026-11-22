from pathlib import Path

import pytest

from vedit import hizli, paths


@pytest.fixture
def kok(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "Projeler/inputs")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "Projeler/outputs")
    monkeypatch.setattr(hizli, "KAIZEN", tmp_path / "kaizen.md")
    (tmp_path / "Projeler/inputs/instagram/08-demo").mkdir(parents=True)
    (tmp_path / "Projeler/inputs/ugc/09-baska").mkdir(parents=True)
    return tmp_path


def test_dogal_sira():
    assert sorted(["10.mp4", "2.mp4", "B-1.mp4", "a-1.mp4"], key=hizli.dogal) == ["2.mp4", "10.mp4", "a-1.mp4", "B-1.mp4"]


def test_ham_imzasi_goruntuye_bagli_sese_bagli_degil(kok, monkeypatch):
    monkeypatch.setattr(hizli, "RC", kok / "rc")
    (kok / "rc/src").mkdir(parents=True)
    p = hizli.bul("08-demo")
    (p.work / "edit").mkdir(parents=True)
    (p.work / "public").mkdir()
    (p.work / "edit/props.json").write_text('{"scenes": []}', encoding="utf-8")
    ilk = hizli.ham_imzasi(p)
    (p.work / "edit/olaylar.json").write_text("{}", encoding="utf-8")
    assert hizli.ham_imzasi(p) == ilk
    (p.work / "edit/props.json").write_text('{"scenes": [1]}', encoding="utf-8")
    ikinci = hizli.ham_imzasi(p)
    assert ikinci != ilk
    (kok / "rc/src/SplitReel.tsx").write_text("x", encoding="utf-8")
    ucuncu = hizli.ham_imzasi(p)
    assert ucuncu != ikinci
    (p.girdi / "logo.png").write_bytes(b"x")
    assert hizli.ham_imzasi(p) != ucuncu


def test_hiz_parcalari():
    p = [{"k": "A", "in": 0, "out": 10}]
    assert hizli.hiz_parcalari(p, {}, 1.25) == [{"k": "A", "in": 0, "out": 10, "hiz": 1.25}]
    w = [{"s": 0.0, "e": 1.0}, {"s": 1.2, "e": 2.0}, {"s": 5.0, "e": 6.0}]
    r = hizli.hiz_parcalari(p, {"A": w}, 1.0, 3.0)
    assert [(x["in"], x["out"], x["hiz"]) for x in r] == [(0, 2.0, 1.0), (2.0, 5.0, 3.0), (5.0, 6.0, 1.0), (6.0, 10, 3.0)]


def test_kesim_olustur_sirayi_korur(monkeypatch, tmp_path):
    monkeypatch.setattr(hizli.ff, "probe", lambda f: {"duration": 2.5 if f.name.startswith("10") else 1.0})
    k = hizli.kesim_olustur(tmp_path, ["02-a.mp4", "10-b.mp4"])
    assert k["kaynak"] == {"V01": "02-a.mp4", "V02": "10-b.mp4"}
    assert [(s["k"], s["out"]) for s in k["parcalar"]] == [("V01", 1.0), ("V02", 2.5)]


def test_kesim_filtresi_boyut_ve_sessiz():
    v = lambda w, h: {"width": w, "height": h}
    p = [{"k": "A", "in": 0, "out": 2, "hiz": 1}, {"k": "B", "in": 0, "out": 1, "hiz": 1}]
    ayni, n = hizli.kesim_filtresi(["A", "B"], p, {"A": {"video": v(1920, 1080), "audio": {}}, "B": {"video": v(1920, 1080), "audio": {}}}, 0.01, 30)
    assert n == 2 and "scale=" not in ayni and "anullsrc" not in ayni
    fark, _ = hizli.kesim_filtresi(["A", "B"], p, {"A": {"video": v(1920, 1080), "audio": {}}, "B": {"video": v(640, 360)}}, 0.01, 30)
    assert "scale=1920:1080" in fark and "pad=1920:1080" in fark
    assert "anullsrc=r=48000:cl=stereo,atrim=0:1.000" in fark and "[1:a]" not in fark


def test_bul_girdi_ve_cikti_ayni_projeye_gider(kok):
    p = hizli.bul("08-demo")
    assert (p.studyo, p.ad) == ("instagram", "08-demo")
    assert p.work == kok / "Projeler/outputs/instagram/08-demo/work"


def test_bul_belirsiz_ve_yok(kok):
    (kok / "Projeler/inputs/instagram/08-ikinci").mkdir()
    with pytest.raises(SystemExit):
        hizli.bul("08-")
    with pytest.raises(SystemExit):
        hizli.bul("yok")


def test_pj_input_girdiye_gerisi_worke(kok):
    root = kok / "Projeler/outputs/ugc/x/work"
    assert paths.pj(root, "input/a.mp4") == kok / "Projeler/inputs/ugc/x/a.mp4"
    assert paths.pj(root, "build/a.mp4") == root / "build/a.mp4"


def test_ozet_icerige_bagli_tasinca_degismez(tmp_path):
    a = tmp_path / "a.bin"
    a.write_bytes(b"x" * 100)
    h = hizli._ozet(a)
    b = tmp_path / "alt"
    b.mkdir()
    assert hizli._ozet(a.rename(b / "a.bin")) == h
    (b / "a.bin").write_bytes(b"y" * 100)
    assert hizli._ozet(b / "a.bin") != h


def test_eski_teslimin_uzerine_yazmaz(tmp_path):
    assert hizli._bos_ad(tmp_path, "r").name == "r.mp4"
    (tmp_path / "r.mp4").touch()
    assert hizli._bos_ad(tmp_path, "r").name == "r-v2.mp4"
    (tmp_path / "r-v2.mp4").touch()
    assert hizli._bos_ad(tmp_path, "r").name == "r-v3.mp4"


def test_kaizen_toplar_ve_iki_kez_yazmaz(kok):
    p = hizli.bul("08-demo")
    hizli.sure_yaz(p.work, "taslak", 60)
    hizli.sure_yaz(p.work, "taslak", 60)
    hizli.sure_yaz(p.work, "final", 300)
    hizli.sure_yaz(p.work, "final:motor", 200)
    s = hizli.kaizen(p)
    assert "araç 7.0 dk" in s and "final:motor" not in s
    hizli.kaizen(p)
    assert "taslak 2" in s and "final 1" in s and "final 5.0 dk" in s
    assert hizli.KAIZEN.read_text(encoding="utf-8").count("\n") == 1


def test_srt_ek_birlestirir_cumlede_keser():
    w = [{"w": "Claude", "s": 0.0, "e": 0.4}, {"w": "'a", "s": 0.4, "e": 0.5}, {"w": "yaz.", "s": 0.5, "e": 1.0},
         {"w": "bir", "s": 1.0, "e": 1.2}]
    s = hizli.srt_yaz(w)
    assert "Claude'a yaz." in s and "00:00:00,000 --> 00:00:01,000" in s
    assert "2\n00:00:01,000 --> 00:00:01,200\nbir" in s


def test_work_bul_yoldan_ve_addan(kok):
    p = hizli.bul("08-demo")
    assert hizli.work_bul([str(p.work / "renders/a.mp4")]) == p.work
    assert hizli.work_bul(["08-demo", "--x"]) == p.work
    assert hizli.work_bul(["--x"]) is None


def test_render_ayari_olcek_fps_ve_imza(kok, monkeypatch, tmp_path):
    monkeypatch.setattr(hizli, "RC", kok / "rc")
    monkeypatch.setattr(hizli, "STUDIO", kok / "studio")
    (kok / "rc/src").mkdir(parents=True)
    (kok / "studio/remotion").mkdir(parents=True)
    props = tmp_path / "kurgu.render.json"
    props.write_text('{"sekans": {"w": 1080, "h": 1920, "fps": 30}}', encoding="utf-8")
    assert hizli._render_ayari(props, None, None) == (props, [], "", (1080, 1920))
    assert hizli._render_ayari(props, 1080, 30)[1:] == ([], "", (1080, 1920))  # sekansla aynı: imza değişmez
    _, ek, ayar, boyut = hizli._render_ayari(props, 1440, None)
    assert boyut == (1440, 2560) and float(ek[0].split("=")[1]) * 1920 == 2560.0 and ayar.startswith("olcek=")
    p60, _, ayar60, _ = hizli._render_ayari(props, None, 60)
    assert p60.name == "kurgu.render.fps.json" and '"fps": 60' in p60.read_text(encoding="utf-8") and ayar60 == "fps=60"
    eski = tmp_path / "props.json"
    eski.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        hizli._render_ayari(eski, None, 60)
    p = hizli.bul("08-demo")
    (p.work / "edit").mkdir(parents=True)
    (p.work / "public").mkdir()
    (p.work / "edit/props.json").write_text("{}", encoding="utf-8")
    assert hizli.ham_imzasi(p) == hizli.ham_imzasi(p, "") != hizli.ham_imzasi(p, ayar)


def test_ilerleme_satiri_yuzde_adimlariyla():
    son, cikan = -1, []
    for n in range(0, 201):
        son, ozet = hizli.ilerleme_satiri(f"Rendered {n}/200, time remaining: 1m 5s", son)
        if ozet:
            cikan.append(ozet)
    assert len(cikan) == 21 and cikan[0].startswith("  %0 ") and "kalan 1m 5s" in cikan[1] and cikan[-1] == "  %100 · 200/200 kare"
    assert hizli.ilerleme_satiri("Bundling 6%", 10) == (10, None)
    assert hizli.ilerleme_satiri("Rendered 0/0", -1) == (-1, None)
