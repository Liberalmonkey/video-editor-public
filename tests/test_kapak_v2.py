"""Kapak iş akışı v2 (ADR 0052): video seçimi, fikir geliştirme, öneriyle üretim, görsel düzeltme, dış görsel, master prompt.
agy ve Playwright taklit edilir; görüntü işlemleri (kırpma, kırmızı kutu, geri yapıştırma) gerçek piksellerle denetlenir."""
import json
import shutil
import subprocess

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from vedit import gorsel, hizli, kapak, pano, paths

GERCEK_KARELER = kapak.kareler
URETILEN = []  # (prompt, refler, k)
AGY = []  # (istek, k)


def _gorsel(f, w, h, renk=(40, 80, 120)):
    g = np.zeros((h, w, 3), np.uint8)
    g[:] = renk
    cv2.circle(g, (w // 3, h // 2), min(w, h) // 5, (200, 200, 200), -1)
    ok, buf = cv2.imencode(f.suffix, g)
    buf.tofile(str(f))
    return f


def _oku(f):
    return cv2.imdecode(np.fromfile(str(f), dtype=np.uint8), cv2.IMREAD_COLOR)


BRIEF = {"sahne": "A creator at a desk", "ifade": "calm focus", "kompozisyon": "subject right", "isik": "soft key",
         "palet": "navy and orange", "yazi_alani": "the upper part of the central area",
         "satir1": "Claude", "satir2": "KURGU yapıyor", "vurgu": "KURGU", "kalip": "klasik", "stil": "turuncu", "kare": 2,
         "not_tr": "Yüzü büyüttüm, yazıyı kısalttım."}


@pytest.fixture
def proje(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "inputs")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "outputs")
    p = hizli.Proje("instagram", "deneme")
    p.girdi.mkdir(parents=True)
    (p.girdi / "senaryo.md").write_text("Claude Code ile video kurgusu", encoding="utf-8")
    URETILEN.clear()
    AGY.clear()
    kare_dir = p.work / "gorsel" / "kapak" / "kareler"
    kare_dir.mkdir(parents=True)
    kr = [_gorsel(kare_dir / f"kare-{i}.jpg", 320, 568) for i in (1, 2)]

    def sahte_uret(prompt, out, oran, log=None, refler=(), **k):
        URETILEN.append((prompt, list(refler), k))
        if "KOTA" in prompt:
            raise SystemExit("agy görsel kotası dolu")
        return _gorsel(out.with_suffix(".png"), 600, 600, (250, 250, 250))  # kare: oran farkı kırpılmalı

    def sahte_agy(istek, ekler=(), **k):
        AGY.append((istek, k))
        return {"response": json.dumps([BRIEF])}

    def sahte_render(html, out, **k):
        out.write_bytes(b"kapak")
        return 1

    monkeypatch.setattr(kapak, "kareler", lambda _p, n=6, video=None: kr)
    monkeypatch.setattr(gorsel, "uret", sahte_uret)
    monkeypatch.setattr(gorsel, "agy", sahte_agy)
    monkeypatch.setattr(pano, "render", sahte_render)
    return p


def test_gelistir_oneri_yazar_ve_uret_kullanir(proje):
    liste = kapak.gelistir(proje, None, "Ben şaşkın bakıyorum, laptop parlıyor", model="gemini-4-argon-medium", kare=2)
    istek, secenek = AGY[0]
    assert "Ben şaşkın bakıyorum, laptop parlıyor" in istek and "not_tr" in istek and secenek == {"model": "gemini-4-argon-medium"}
    assert "2: " in istek and "1: " not in istek.split("pick the best one")[1].split("---")[0]  # yalnız seçili kare
    oneri = json.loads((kapak.klasor(proje, "instagram") / "oneri.json").read_text(encoding="utf-8"))
    assert oneri["fikir"].startswith("Ben şaşkın") and oneri["briefler"][0]["not_tr"] == liste[0]["not_tr"]
    cikti = kapak.uret(proje, None, 2, oneri=True, gorsel_model="gemini-3.8-flash-medium")
    assert [f.name for f in cikti] == ["kapak-1.jpg", "kapak-2.jpg"]
    prompt, refler, k = URETILEN[0]
    assert prompt.startswith("A creator at a desk") and "Expression: calm focus" in prompt
    assert k["model"] == "gemini-3.8-flash-medium" and "Image 1" in k["ref_metni"]
    assert [r.name for r in refler] == ["kare-2.jpg"]
    d = kapak.durum(proje, None)
    assert d["oneri"]["briefler"][0]["govde"].startswith("A creator at a desk")
    assert d["adaylar"][0]["satir2"] == "KURGU yapıyor" and d["adaylar"][0]["zemin_kaynagi"] == "agy"


def test_gelistir_metinsiz_calisir_oneri_yoksa_uret_durur(proje):
    (proje.girdi / "senaryo.md").unlink()
    kapak.gelistir(proje, None, "fikir")
    assert "(none)" in AGY[0][0]
    (proje.girdi / "senaryo.md").write_text("metin", encoding="utf-8")
    (kapak.klasor(proje, "instagram") / "oneri.json").unlink()
    with pytest.raises(SystemExit, match="Öneri yok"):
        kapak.uret(proje, None, 1, oneri=True)
    kapak.gelistir(proje, None, "   ")  # boş fikir: yalnız videodan öneri; metin yoksa durur
    assert "creator's own idea" not in AGY[-1][0]
    (proje.girdi / "senaryo.md").unlink()
    with pytest.raises(SystemExit, match="Brief için metin yok"):
        kapak.gelistir(proje, None, "")


def test_oneri_yaz_temizler(proje):
    v = kapak.oneri_yaz(proje, None, [{**BRIEF, "satir1": "a\nb", "kotu": "x", "kare": "3"}], fikir="yeni fikir")
    b = v["briefler"][0]
    assert b["satir1"] == "a b" and "kotu" not in b and b["kare"] == 3 and v["fikir"] == "yeni fikir"
    with pytest.raises(SystemExit):
        kapak.oneri_yaz(proje, None, [])


def test_referanslar_agy_sirasi(proje):
    ref = proje.work / "gorsel" / "kapak" / "referans"
    ref.mkdir(parents=True)
    for ad in ("stil-a.jpg", "yuz-b.png", "yuz-c.png", "diger-d.png"):
        (ref / ad).write_bytes(b"x")
    (proje.girdi / "karakter-1.png").write_bytes(b"x")
    assert [(r, f.name) for r, f in kapak.referanslar(proje)] == [
        ("stil", "stil-a.jpg"), ("yuz", "yuz-b.png"), ("yuz", "yuz-c.png"), ("yuz", "karakter-1.png")]
    kapak.uret(proje, None, 1, prompt="desk")
    assert [r.name for r in URETILEN[0][1]] == ["kare-1.jpg", "yuz-b.png", "yuz-c.png", "karakter-1.png", "stil-a.jpg"]
    assert "style reference" in URETILEN[0][2]["ref_metni"]
    kapak.referans_sil(proje, "stil-a.jpg")
    with pytest.raises(SystemExit):
        kapak.referans_sil(proje, "../senaryo.md")


def _aday(proje, w=1080, h=1920):
    z = _gorsel(proje.work / "zemin.png", w, h)
    kapak.uret(proje, None, 1, metin="Üst|ALT", zemin=z)
    return kapak.klasor(proje, "instagram")


def test_gorsel_duzelt_bolge_disi_degismez(proje):
    k = _aday(proje)
    jpg = kapak.gorsel_duzelt(proje, None, 1, "arka planı mavi yap", bolge=[60, 10, 20, 40], model="m1")
    assert jpg.name == "kapak-2.jpg"
    prompt, refler, sec = URETILEN[-1]
    assert "inside the red rectangle: arka planı mavi yap" in prompt and sec["model"] == "m1"
    isaret = _oku(refler[0])
    assert refler[0].name == "duzelt-2-isaret.png" and (isaret[:, :, 2] > 200).sum() > 0
    once, sonra = _oku(k / "zemin-1.png"), _oku(k / "zemin-2.png")
    assert sonra.shape == once.shape
    x1, y1, x2, y2 = 216, 192, 648, 768  # 20-60 %, 10-40 %
    pay = 2 * round(1080 * 0.02) + 2
    dis = np.ones(once.shape[:2], bool)
    dis[max(y1 - pay, 0):y2 + pay, max(x1 - pay, 0):x2 + pay] = False
    assert (once[dis] == sonra[dis]).all()  # kutu dışı piksel aynen kalır
    assert sonra[y1 + 20:y2 - 20, x1 + 20:x2 - 20].mean() > 200 > once[y1 + 20:y2 - 20, x1 + 20:x2 - 20].mean()  # içi sonuçtan
    meta = json.loads((k / "kapak-2.json").read_text(encoding="utf-8"))
    assert (meta["ebeveyn"], meta["zemin_kaynagi"], meta["satir2"]) == (1, "duzeltme", "ALT")
    assert kapak.durum(proje, None)["adaylar"][1]["ebeveyn"] == 1


def test_gorsel_duzelt_tum_gorsel_ve_kota(proje):
    k = _aday(proje)
    kapak.gorsel_duzelt(proje, None, 1, "ışığı dramatik yap")
    assert _oku(k / "zemin-2.png").shape[:2] == (1920, 1080)  # kare sonuç ortadan kırpılıp ölçeklenir
    assert "red rectangle" not in URETILEN[-1][0]
    with pytest.raises(SystemExit, match="kota"):
        kapak.gorsel_duzelt(proje, None, 1, "KOTA")
    assert kapak.adaylar(k) == [1, 2]
    with pytest.raises(SystemExit, match="küçük"):
        kapak.gorsel_duzelt(proje, None, 1, "x", bolge=[10, 10, 11, 50])
    with pytest.raises(SystemExit, match="0-100"):
        kapak.gorsel_duzelt(proje, None, 1, "x", bolge=[10, 10, 120, 50])


def test_ice_al_kirpar_yazili_ve_yazisiz(proje, tmp_path, monkeypatch):
    kapak.oneri_yaz(proje, None, [BRIEF])
    dis = _gorsel(tmp_path / "gemini.png", 1600, 900)
    jpg = kapak.ice_al(proje, None, dis)
    k = kapak.klasor(proje, "instagram")
    assert _oku(k / "zemin-1.jpg").shape[:2] == (1920, 1080)
    meta = json.loads((k / "kapak-1.json").read_text(encoding="utf-8"))
    assert (meta["zemin_kaynagi"], meta["satir1"], meta["kalip"]) == ("dis", "Claude", "klasik")
    (k.parent.parent / "yuz.png").write_bytes(b"y")  # dış görselde ikinci yüz çizilmez
    kapak.ice_al(proje, None, dis, yazili=True)
    meta = json.loads((k / "kapak-2.json").read_text(encoding="utf-8"))
    assert meta["kalip"] == "yazisiz" and "yuz.png" not in (k / "kapak-2.html").read_text(encoding="utf-8")
    assert jpg.name == "kapak-1.jpg"
    kotu = tmp_path / "a.gif"
    kotu.write_bytes(b"x")
    with pytest.raises(SystemExit, match="jpg"):
        kapak.ice_al(proje, None, kotu)
    monkeypatch.setattr(kapak, "DIS_SINIR", 10)
    with pytest.raises(SystemExit, match="MB"):
        kapak.ice_al(proje, None, dis)


def test_master_kaynaklari_ve_teslimde_md(proje):
    with pytest.raises(SystemExit, match="önce"):
        kapak.master(proje, None)
    kapak.oneri_yaz(proje, None, [BRIEF])
    m = kapak.master(proje, None, kare=2)
    assert m["kaynak"] == "öneri" and set(m["hedefler"]) == {"nano-banana-pro", "nano-banana-21", "chatgpt", "midjourney",
                                                             "ideogram", "leonardo"}
    assert m["ekler"][0] == {"no": 1, "rol": "kare", "dosya": "kare-2.jpg", "kok": "outputs",
                             "yol": "work/gorsel/kapak/kareler/kare-2.jpg"}
    assert '"KURGU yapıyor"' in m["hedefler"]["chatgpt"]["yazili"]["prompt"]
    _aday(proje)
    assert kapak.master(proje, None, 1)["kaynak"] == "aday 1"
    hedef = kapak.sec(proje, None, 1)
    md = (proje.cikti / f"{hedef.stem}-master-prompt.md").read_text(encoding="utf-8")
    assert "Nano Banana Pro" in md and "Midjourney" in md


def test_kota_logdan(tmp_path, monkeypatch):
    monkeypatch.setattr(gorsel, "_KOTA_ONBELLEK", {})
    assert gorsel.kota(tmp_path) == {"model": None, "kapali": False}
    (tmp_path / "cli-20261118_134701.log").write_text(
        '"model": "gemini-3.1-flash-image",\n "quotaResetTimeStamp": "2099-01-01T00:00:00Z"', encoding="utf-8")
    k = gorsel.kota(tmp_path)
    assert (k["model"], k["acilis"], k["kapali"]) == ("gemini-3.1-flash-image", "2099-01-01T00:00:00Z", True)


def test_agy_model_ve_efor_bayragi(monkeypatch, tmp_path):
    giden = []

    class Sonuc:
        stdout = '{"status": "SUCCESS", "response": "ok"}'
        stderr = ""

    monkeypatch.setattr(gorsel, "agy_yolu", lambda: "agy")
    monkeypatch.setattr(gorsel.subprocess, "run", lambda komut, **k: giden.append(komut) or Sonuc())
    gorsel.agy("merhaba", model="gemini-4-argon-medium", efor="high")
    assert giden[0][:8] == ["agy", "--output-format", "json", "--print-timeout", "600s", "--model", "gemini-4-argon-medium", "--effort"]
    with pytest.raises(SystemExit, match="Efor"):
        gorsel.agy("x", efor="cok")
    Sonuc.stdout = '{"status": "ERROR", "response": "RESOURCE_EXHAUSTED quota"}'
    monkeypatch.setattr(gorsel, "kota", lambda: {"model": "m", "acilis": "2099"})
    with pytest.raises(SystemExit, match="kotası dolu .açılış 2099"):
        gorsel.agy("x")


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg yok")
def test_video_secimi_kareler_ve_elle_kare(proje, monkeypatch):
    monkeypatch.setattr(kapak, "kareler", GERCEK_KARELER)
    for ad, renk in (("1.mp4", "red"), ("2.mp4", "blue")):
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"color=c={renk}:s=160x284:d=2", "-pix_fmt", "yuv420p",
                        str(proje.girdi / ad)], check=True)
    assert [v["yol"] for v in kapak.videolar(proje)] == ["inputs:1.mp4", "inputs:2.mp4"]
    kr = kapak.kareler(proje, n=2, video="inputs:2.mp4")
    assert [f.parent.name for f in kr] == ["inputs-2.mp4"] * 2
    assert _oku(kr[0])[100, 80, 0] > 200  # mavi (BGR)
    el = kapak.kare_ekle(proje, "inputs:2.mp4", 1.25)
    assert el.name == "el-00001250.jpg" and kapak.kareler(proje, n=2, video="inputs:2.mp4")[-1] == el
    assert kapak.kareler(proje, n=2, video="inputs:1.mp4")[-1].name == "kare-2.jpg"  # el karesi videoya özgü
    with pytest.raises(SystemExit, match="dışında"):
        kapak.kare_ekle(proje, "inputs:2.mp4", 9)
    for kotu in ("inputs:../../x.mp4", "inputs:senaryo.md", "c:/x.mp4", "outputs:yok.mp4"):
        with pytest.raises(SystemExit):
            kapak.video_yolu(proje, kotu)
    d = kapak.durum(proje, None, "inputs:2.mp4")
    assert d["video"] == "inputs:2.mp4" and d["kareler"][-1]["el"] is True and len(d["videolar"]) == 2
