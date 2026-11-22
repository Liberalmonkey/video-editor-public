"""vedit kapak: agy ve Playwright taklit edilir; aday numarası, kota, brief, şablon ve seçim doğrulanır."""
import json
import os

import pytest

from vedit import gorsel, hizli, kapak, pano, paths

CIZILEN = []  # sahte render'a giden (html, ölçü)
URETILEN = []  # sahte gorsel.uret'e giden (prompt, refler)


@pytest.fixture
def proje(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "inputs")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "outputs")
    p = hizli.Proje("instagram", "deneme")
    p.girdi.mkdir(parents=True)
    (p.girdi / "senaryo.md").write_text("Claude Code ile video kurgusu", encoding="utf-8")
    CIZILEN.clear()
    URETILEN.clear()

    kare_dir = p.work / "gorsel" / "kapak" / "kareler"
    kare_dir.mkdir(parents=True)
    sahte_kareler = []
    for i in (1, 2):
        kf = kare_dir / f"kare-{i}.jpg"
        kf.write_bytes(f"kare{i}".encode())
        sahte_kareler.append(kf)

    def sahte_uret(prompt, out, oran, log=None, refler=(), **k):
        URETILEN.append((prompt, list(refler)))
        if "KOTA" in prompt:
            raise SystemExit("agy başarısız: QUOTA")
        f = out.with_suffix(".jpg")
        f.write_bytes(b"zemin")
        return f

    def sahte_render(html, out, **k):
        CIZILEN.append((html.read_text(encoding="utf-8"), k))
        out.write_bytes(b"kapak")
        return 1

    monkeypatch.setattr(kapak, "kareler", lambda _p, n=6, video=None: sahte_kareler)
    monkeypatch.setattr(gorsel, "uret", sahte_uret)
    monkeypatch.setattr(pano, "render", sahte_render)
    return p


def test_adaylar_eklenir_ustune_yazmaz(proje):
    a = kapak.uret(proje, None, 3, metin="Kurgu|ARTIK bedava", prompt="desk")
    b = kapak.uret(proje, None, 2, metin="x|y", prompt="desk")
    assert [f.name for f in a + b] == [f"kapak-{n}.jpg" for n in range(1, 6)]
    html, olcu = CIZILEN[0]
    assert {a: olcu[a] for a in ("sure", "w", "h")} == {"sure": 0, "w": 1080, "h": 1920}
    assert '<div class="baslik">Kurgu<br><em>ARTIK bedava</em></div>' in html and 'url("zemin-1.jpg")' in html


@pytest.mark.parametrize("adet", [0, 6])
def test_adet_siniri(proje, adet):
    with pytest.raises(SystemExit, match="1 ile 5"):
        kapak.uret(proje, None, adet, prompt="x")


def test_ugc_platform_ister(proje):
    with pytest.raises(SystemExit, match="zorunlu"):
        kapak.platform_sec(hizli.Proje("ugc", "x"), None)


def test_kota_dolunca_uretilen_kalir(proje, monkeypatch):
    monkeypatch.setattr(kapak, "kareler", lambda _p, n=6, video=None: [])
    (kapak.klasor(proje, "instagram")).mkdir(parents=True)
    brief = [{"prompt": "a", "satir1": "A", "satir2": "B"}, {"prompt": "KOTA"}, {"prompt": "c"}]
    (kapak.klasor(proje, "instagram") / "brief.json").write_text(json.dumps(brief), encoding="utf-8")
    assert [f.name for f in kapak.uret(proje, None, 3)] == ["kapak-1.jpg"]


def test_brief_agy_ile_ve_vurgu(proje, monkeypatch):
    yanit = 'İşte:\n```json\n[{"prompt": "p1", "satir1": "Claude", "satir2": "artık KURGU yapıyor", "vurgu": "KURGU", "aci": "sonuç", "kare": 2}]\n```'
    monkeypatch.setattr(gorsel, "agy", lambda istek, ekler=(), **k: {"response": yanit})
    kapak.uret(proje, None, 1)
    assert "artık <em>KURGU</em> yapıyor" in CIZILEN[0][0]
    assert kapak.durum(proje, None)["adaylar"][0]["aci"] == "sonuç"
    assert json.loads((kapak.klasor(proje, "instagram") / "brief.json").read_text(encoding="utf-8"))[0]["prompt"] == "p1"


def test_bozuk_brief_durur():
    with pytest.raises(SystemExit, match="JSON"):
        kapak.json_dizisi("kota doldu")


def test_sec_ustune_yazmaz_ve_durum(proje):
    kapak.uret(proje, None, 2, metin="a|b", prompt="x")
    assert kapak.sec(proje, None, 2).name == "kapak-reels.jpg"
    assert kapak.sec(proje, None, 1).name == "kapak-reels-v2.jpg"
    d = kapak.durum(proje, None)
    assert d["secim"] == {"n": 1, "dosya": "kapak-reels-v2.jpg", "eski": False}
    assert d["adaylar"][0]["yol"] == "work/gorsel/kapak/instagram/kapak-1.jpg"
    assert d["adaylar"][0]["aci"] is None
    with pytest.raises(SystemExit, match="Aday yok"):
        kapak.sec(proje, None, 9)


def test_zemin_ve_metin_agy_cagirmaz(proje, tmp_path, monkeypatch):
    monkeypatch.setattr(gorsel, "agy", lambda *a, **k: pytest.fail("agy çağrıldı"))
    monkeypatch.setattr(gorsel, "uret", lambda *a, **k: pytest.fail("agy görseli istendi"))
    z = tmp_path / "kare.jpg"
    z.write_bytes(b"k")
    assert [f.name for f in kapak.uret(proje, None, 2, metin="a|b", zemin=z)] == ["kapak-1.jpg", "kapak-2.jpg"]


def test_kare_varsa_gorsel_uret_refler_alir(proje):
    (proje.girdi / "karakter-ana.png").write_bytes(b"kar")
    kapak.uret(proje, None, 1, prompt="studio")
    prompt_giden, refler_giden = URETILEN[0]
    assert "Use the reference frame:" in prompt_giden
    assert [r.name for r in refler_giden] == ["kare-1.jpg", "karakter-ana.png"]
    meta = json.loads((kapak.klasor(proje, "instagram") / "kapak-1.json").read_text(encoding="utf-8"))
    assert meta["kare"] == 1 and meta["zemin_kaynagi"] == "agy"


def test_agy_hata_verince_kare_zemin_olur(proje, capsys):
    cikti = kapak.uret(proje, None, 1, metin="A|B", prompt="KOTA")
    assert [f.name for f in cikti] == ["kapak-1.jpg"]
    assert "agy üretmedi, videodaki kare zemin yapıldı" in capsys.readouterr().out
    assert 'url("../kareler/kare-1.jpg")' in CIZILEN[0][0]
    meta = json.loads((kapak.klasor(proje, "instagram") / "kapak-1.json").read_text(encoding="utf-8"))
    assert meta["kare"] == 1 and meta["zemin_kaynagi"] == "kare"


def test_kare_parametresi_brief_secimini_ezer(proje):
    (kapak.klasor(proje, "instagram")).mkdir(parents=True)
    brief = [{"prompt": "p1", "satir1": "A", "satir2": "B", "kare": 1}]
    (kapak.klasor(proje, "instagram") / "brief.json").write_text(json.dumps(brief), encoding="utf-8")
    kapak.uret(proje, None, 1, kare=2)
    assert [r.name for r in URETILEN[0][1]] == ["kare-2.jpg"]
    meta = json.loads((kapak.klasor(proje, "instagram") / "kapak-1.json").read_text(encoding="utf-8"))
    assert meta["kare"] == 2


def test_duzenle_agy_cagirmaz_yerinde_ve_kopya(proje, monkeypatch):
    kapak.uret(proje, None, 1, metin="Eski|YAZI burada", prompt="desk")
    monkeypatch.setattr(gorsel, "agy", lambda *a, **k: pytest.fail("agy çağrıldı"))
    monkeypatch.setattr(gorsel, "uret", lambda *a, **k: pytest.fail("agy görseli istendi"))
    k = kapak.klasor(proje, "instagram")
    assert kapak.duzenle(proje, None, 1, metin="Yeni|SATIR burada", vurgu="SATIR", yerlesim="alt", kutu=True).name == "kapak-1.jpg"
    html, olcu = CIZILEN[-1]
    assert {a: olcu[a] for a in ("sure", "w", "h")} == {"sure": 0, "w": 1080, "h": 1920}
    assert '<div class="baslik">Yeni<br><em>SATIR</em> burada</div>' in html and 'url("zemin-1.jpg")' in html
    assert '<body data-kalip="klasik" data-yerlesim="alt" class="kutu" style="--olcek: 1">' in html
    meta = json.loads((k / "kapak-1.json").read_text(encoding="utf-8"))
    assert (meta["satir1"], meta["vurgu"], meta["yerlesim"], meta["zemin"], meta["zemin_kaynagi"]) == ("Yeni", "SATIR", "alt", "zemin-1.jpg", "agy")
    # yalnız ölçek değişir: yazı ve yerleşim korunur; kopya yeni aday açar, eskisi durur
    assert kapak.duzenle(proje, None, 1, olcek=1.2, kopya=True).name == "kapak-2.jpg"
    assert 'style="--olcek: 1.2"' in CIZILEN[-1][0] and "<em>SATIR</em>" in CIZILEN[-1][0]
    a1, a2 = kapak.durum(proje, None)["adaylar"]
    assert (a1["olcek"], a2["olcek"], a2["yerlesim"], a2["kutu"], a2["satir2"]) == (1.0, 1.2, "alt", True, "SATIR burada")
    assert "yazı" in (proje.work / "gorsel" / "log.md").read_text(encoding="utf-8")


def test_eski_aday_zemini_htmlden_bulunur(proje):
    k = kapak.klasor(proje, "instagram")
    k.mkdir(parents=True)
    (k / "zemin-1.png").write_bytes(b"z")
    (k / "kapak-1.jpg").write_bytes(b"k")
    (k / "kapak-1.html").write_text(':root { --zemin: url("zemin-1.png"); }', encoding="utf-8")
    (k / "kapak-1.json").write_text('{"satir1": "A", "satir2": "B", "aci": "sonuç"}', encoding="utf-8")
    kapak.duzenle(proje, None, 1, metin="C|D")
    assert 'url("zemin-1.png")' in CIZILEN[-1][0] and "C<br><em>D</em>" in CIZILEN[-1][0]
    assert json.loads((k / "kapak-1.json").read_text(encoding="utf-8"))["aci"] == "sonuç"
    (k / "zemin-1.png").unlink()
    with pytest.raises(SystemExit, match="zemini bulunamadı"):
        kapak.duzenle(proje, None, 1, metin="E|F")
    with pytest.raises(SystemExit, match="Aday yok"):
        kapak.duzenle(proje, None, 9, metin="E|F")


def test_stil_dogrulanir_agy_harcanmaz(proje):
    for kotu, hata in ((dict(yerlesim="sol"), "yerleşimi"), (dict(olcek=2), "Ölçek"), (dict(olcek="x"), "Ölçek")):
        with pytest.raises(SystemExit, match=hata):  # sol yalnız YouTube'da var
            kapak.uret(proje, None, 1, prompt="x", **kotu)
    assert URETILEN == []
    kapak.uret(proje, None, 1, metin="a|b c", prompt="x", vurgu="c", karart=True)
    assert "a<br>b <em>c</em>" in CIZILEN[0][0] and 'data-yerlesim="ust" class="karart"' in CIZILEN[0][0]


def test_dis_zemin_aday_klasorune_kopyalanir(proje, tmp_path):
    z = tmp_path / "dışarıda kare.JPG"
    z.write_bytes(b"k")
    kapak.uret(proje, None, 1, metin="a|b", zemin=z)
    k = kapak.klasor(proje, "instagram")
    assert (k / "zemin-1.jpg").read_bytes() == b"k" and 'url("zemin-1.jpg")' in CIZILEN[0][0]
    with pytest.raises(SystemExit, match="Zemin yok"):
        kapak.uret(proje, None, 1, metin="a|b", zemin=tmp_path / "yok.jpg")


def test_onizleme_html_kacis_ve_adres(proje):
    kapak.uret(proje, None, 1, metin="a|b", prompt="x")
    once = len(CIZILEN)
    s = kapak.onizleme_html(proje, None, 1, metin='<script>x</script>|"B" & c', yerlesim="alt")
    assert len(CIZILEN) == once  # önizleme render etmez, dosya yazmaz
    assert "<script>" not in s and "&lt;script&gt;x&lt;/script&gt;" in s and "&quot;B&quot; &amp; c" in s
    assert 'url("/dosya/instagram/deneme/outputs/work/gorsel/kapak/instagram/zemin-1.jpg")' in s
    assert "/lib/fonts/Montserrat-Variable.ttf" in s and 'data-yerlesim="alt"' in s
    assert json.loads((kapak.klasor(proje, "instagram") / "kapak-1.json").read_text(encoding="utf-8"))["satir1"] == "a"


def test_durum_alanlari_ve_eski_teslim(proje):
    kapak.uret(proje, None, 1, metin="a|b", prompt="x")
    kapak.sec(proje, None, 1)
    d = kapak.durum(proje, None)
    assert (d["w"], d["h"], d["yerlesimler"]) == (1080, 1920, ["ust", "alt"])
    assert [g["ad"] for g in d["guvenli"]] == ["Izgara 3:4", "Akış 4:5"] and d["secim"]["eski"] is False
    kapak.duzenle(proje, None, 1, metin="c|d")
    jpg = kapak.klasor(proje, "instagram") / "kapak-1.jpg"
    os.utime(jpg, (jpg.stat().st_mtime + 5, jpg.stat().st_mtime + 5))
    assert kapak.durum(proje, None)["secim"]["eski"] is True


def test_vurgu_ham_metinde_aranir():
    B = lambda s2, vurgu: kapak.baslik_html({"satir1": "A", "satir2": s2, "vurgu": vurgu})
    # kaçırılmış metinde arama &amp; ve &#x27; varlıklarını bölerdi
    assert B("A & B", "amp") == '<div class="baslik">A<br><em>A &amp; B</em></div>'
    assert B("Türkiye'de İLK", "x") == '<div class="baslik">A<br><em>Türkiye&#x27;de İLK</em></div>'
    assert B("A & B", "& B") == '<div class="baslik">A<br>A <em>&amp; B</em></div>'
    assert B("artık KURGU yapıyor", "kurgu") == '<div class="baslik">A<br>artık <em>KURGU</em> yapıyor</div>'  # yazı büyük harfle çizilir
    assert B("", "x") == '<div class="baslik">A<br></div>'  # boş satır boş turuncu kutu çizmesin


def test_proje_disi_zemin_reddedilir_girdi_zemini_onizlenir(proje, tmp_path):
    k = kapak.klasor(proje, "instagram")
    k.mkdir(parents=True)
    (k / "kapak-1.jpg").write_bytes(b"k")
    (tmp_path / "gizli.png").write_bytes(b"g")
    for yol in ("../../../../../../../gizli.png", str(tmp_path / "gizli.png")):  # elle değiştirilmiş kayıt
        (k / "kapak-1.json").write_text(json.dumps({"zemin": yol}), encoding="utf-8")
        with pytest.raises(SystemExit, match="zemini bulunamadı"):
            kapak.duzenle(proje, None, 1, metin="a|b")
        with pytest.raises(SystemExit, match="zemini bulunamadı"):
            kapak.onizleme_html(proje, None, 1)
    assert CIZILEN == []
    # eski `--zemin inputs/...` adayı: zemin girdi klasöründe, önizleme /dosya inputs kökünden gelir
    (proje.girdi / "kare.jpg").write_bytes(b"z")
    (k / "kapak-1.json").write_text(json.dumps({"zemin": os.path.relpath(proje.girdi / "kare.jpg", k)}), encoding="utf-8")
    assert 'url("/dosya/instagram/deneme/inputs/kare.jpg")' in kapak.onizleme_html(proje, None, 1)
    assert kapak.duzenle(proje, None, 1, metin="a|b").name == "kapak-1.jpg"
    with pytest.raises(SystemExit, match="Ölçek"):
        kapak.duzenle(proje, None, 1, olcek=0)


def test_cli_sifir_aday_uretime_dusmez(proje, monkeypatch):
    from vedit import cli
    monkeypatch.setattr(kapak, "uret", lambda *a, **k: pytest.fail("üretim başladı"))
    for bayrak in ("--sec", "--duzenle"):
        with pytest.raises(SystemExit, match="Aday yok"):
            cli.main(["kapak", "instagram/deneme", bayrak, "0"])


SINAMA_YAZISI = {"satir1": "Kapak yazısı", "satir2": "güvenli ALANDA", "vurgu": "ALANDA"}


@pytest.mark.parametrize("platform,yerlesim", [(pl, y) for pl, ys in kapak.YERLESIM.items() for y in ys])
def test_baslik_guvenli_alanda_gercek_render(tmp_path, platform, yerlesim):
    """Şablonu gerçek tarayıcıda açar: başlık kutusu her `ic` alanın içinde, her `dis` alanın dışında kalmalı."""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright
    _, w, h, _, _ = kapak.PLATFORMLAR[platform]
    f = tmp_path / "kapak.html"
    f.write_text(kapak.html_metni(platform, "yok.png", None, {**SINAMA_YAZISI, "yerlesim": yerlesim, "kutu": True}), encoding="utf-8")
    with sync_playwright() as p:
        try:
            b, pg = pano.ac(p, f, w, h, None)
        except Exception as e:
            pytest.skip(f"tarayıcı açılamadı: {e}")
        # pano.render'daki gibi: ölçüm yedek yazı tipiyle değil Montserrat ile yapılsın
        pg.add_style_tag(content='@font-face { font-family: "Montserrat"; font-weight: 100 900; src: url("'
                         + (paths.FONTS_DIR / "Montserrat-Variable.ttf").resolve().as_uri() + '"); }')
        pg.evaluate("document.fonts.load('800 40px Montserrat').then(() => document.fonts.ready)")
        assert pg.evaluate("document.fonts.check('800 40px Montserrat')")
        r = pg.evaluate("(() => { const r = document.querySelector('.baslik').getBoundingClientRect();"
                        " return [r.left / innerWidth, r.top / innerHeight, r.right / innerWidth, r.bottom / innerHeight].map((v) => v * 100); })()")
        b.close()
    sol, ust, sag, alt = r
    assert sag > sol and alt > ust
    for g in kapak.GUVENLI[platform]:
        gs, gu, gsa, ga = g["kutu"]
        if g["tur"] == "ic":
            assert sol >= gs and ust >= gu and sag <= gsa and alt <= ga, (g["ad"], r)
        else:
            assert sag <= gs or alt <= gu or sol >= gsa or ust >= ga, (g["ad"], r)


# --- kalıp, stil paketi, özne kesiti, ölçüm (ADR 0027, 2026-11-15 notu)

def test_kalip_kesit_ve_ek_soz(proje, monkeypatch):
    def sahte_kesit(zemin):
        out = zemin.with_name(f"{zemin.stem}-ozne.png")
        out.write_bytes(b"ozne")
        return out

    monkeypatch.setattr(kapak, "kesit", sahte_kesit)
    kapak.uret(proje, "youtube", 1, metin="SEEDANCE|2.5", prompt="x", kalip="dev-yazi", ek="4K!", stil="kirmizi-kutu")
    html = CIZILEN[-1][0]
    assert 'data-kalip="dev-yazi"' in html and '<div class="ek">4K!</div><div class="baslik">' in html
    assert "--ozne: url(&#x27;zemin-1-ozne.png&#x27;)" in html and "--vurgu: #E52521" in html
    assert 'class="kutu"' in html, "paketin kutu varsayılanı açık seçim yokken uygulanır"
    assert "plain uncluttered backdrop" in URETILEN[-1][0], "kalıp zeminden kompozisyon ister"
    a = kapak.durum(proje, "youtube")["adaylar"][0]
    assert (a["kalip"], a["stil"], a["ek"], a["kutu"]) == ("dev-yazi", "kirmizi-kutu", "4K!", True)
    # önizleme kesiti kullanır; kutu açıkça kapatılabilir
    onizleme = kapak.onizleme_html(proje, "youtube", 1, kutu=False)
    assert "zemin-1-ozne.png" in onizleme and 'class=""' in onizleme and "PlayfairDisplay-Variable.ttf" in onizleme


def test_kesit_yoksa_klasige_duser(proje, monkeypatch, capsys):
    monkeypatch.setattr(kapak, "kesit", lambda zemin: None)
    kapak.uret(proje, "instagram", 1, metin="a|b", prompt="x", kalip="seri", ek="Claude")
    assert 'data-kalip="klasik"' in CIZILEN[-1][0] and '<div class="ek">' not in CIZILEN[-1][0]
    assert "klasik kalıpla çizildi" in capsys.readouterr().out
    assert kapak.durum(proje, "instagram")["adaylar"][0]["kalip"] == "klasik"


def test_bolunmus_ve_yazisiz_yazilari():
    b = {"satir1": "ÖNCE", "satir2": "SONRA <1>", "kalip": "bolunmus"}
    html = kapak.html_metni("youtube", "z.png", None, b)
    assert '<div class="etiket sol">ÖNCE</div><div class="etiket sag">SONRA &lt;1&gt;</div>' in html and 'class="baslik"' not in html
    assert "<div class=" not in kapak.yazilar_html({"satir1": "a", "kalip": "yazisiz"})
    assert '<div class="ek">' not in kapak.html_metni("youtube", "z.png", None, {"satir1": "a", "ek": "x"}), "klasikte ek söz çizilmez"


def test_gecersiz_kalip_ve_stil(proje):
    for kotu in (dict(kalip="seri"), dict(kalip="yok"), dict(stil="yok")):  # seri yalnız Instagram'da
        with pytest.raises(SystemExit):
            kapak.uret(proje, "youtube", 1, metin="a|b", prompt="x", **kotu)
    assert not URETILEN, "geçersiz seçim agy kotası harcamadan durur"
    assert kapak.stiller()["turuncu"]["css"] == {} and kapak.stiller()["acik-siyah"]["kutu"] is True


def test_briefin_gecersiz_kalibi_adayi_yakmaz(proje, monkeypatch):
    brief = [{"prompt": "desk", "satir1": "a", "satir2": "b", "kalip": "uydurma", "stil": "uydurma", "ek": "x"}]
    monkeypatch.setattr(gorsel, "agy", lambda istek, **k: {"response": json.dumps(brief)})
    assert len(kapak.uret(proje, "youtube", 1)) == 1
    a = kapak.durum(proje, "youtube")["adaylar"][0]
    assert (a["kalip"], a["stil"]) == ("klasik", "turuncu")


def test_olcum_kelime_guvenli_alan_ve_harf(tmp_path):
    jpg = tmp_path / "yok.jpg"
    temiz = kapak.olc("youtube", {"satir1": "İKİ", "satir2": "SÖZ"}, jpg, [{"sinif": "baslik", "arka": False, "punto": 94, "kutu": [5, 30, 60, 70]}])
    assert temiz["gecti"] and temiz["kelime"] == 2 and temiz["harf"] == 9.4
    kotu = kapak.olc("youtube", {"satir1": "bu kapakta çok fazla", "satir2": "kelime var"}, jpg,
                     [{"sinif": "baslik", "arka": False, "punto": 40, "kutu": [5, 70, 90, 96]},
                      {"sinif": "ek", "arka": True, "punto": 300, "kutu": [-10, 0, 110, 60]}])
    assert not kotu["gecti"] and len(kotu["notlar"]) == 3, kotu["notlar"]  # kelime, güvenli alan, harf; arkadaki dev söz sayılmaz
    assert "Süre rozeti" in " ".join(kotu["notlar"])
    assert kapak.olc("youtube", {"kalip": "yazisiz", "satir1": "a b c d e f g"}, jpg, None)["kelime"] == 0


def test_elestiri_adaya_yazilir(proje, monkeypatch):
    kapak.uret(proje, None, 2, metin="a|b", prompt="x")
    yanit = '```json\n[{"n": 2, "puan": 14, "not": "Yazı küçük; büyüt."}, {"n": 9, "puan": 5, "not": "yok"}]\n```'
    monkeypatch.setattr(gorsel, "agy", lambda istek, **k: {"response": yanit})
    kapak.elestir(proje, None)
    a1, a2 = kapak.durum(proje, None)["adaylar"]
    assert (a1["puan"], a2["puan"], a2["elestiri"]) == (None, 10, "Yazı küçük; büyüt.")


@pytest.mark.parametrize("platform,kalip", [(pl, k) for pl, ks in kapak.KALIP.items() for k in ks if k != "klasik"])
def test_kalip_yazilari_guvenli_alanda_gercek_render(tmp_path, platform, kalip):
    """Her kalıbın öndeki yazıları gerçek tarayıcıda güvenli alanın içinde kalır (render'ın kullandığı ölçüm betiğiyle)."""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright
    _, w, h, _, _ = kapak.PLATFORMLAR[platform]
    b = {"satir1": "ÖNCE", "satir2": "SONRA", "vurgu": "SONRA", "ek": "4K!", "kalip": kalip}
    f = tmp_path / "kapak.html"
    f.write_text(kapak.html_metni(platform, "yok.png", None, b), encoding="utf-8")
    with sync_playwright() as p:
        try:
            tarayici, pg = pano.ac(p, f, w, h, None)
        except Exception as e:
            pytest.skip(f"tarayıcı açılamadı: {e}")
        pg.add_style_tag(content='@font-face { font-family: "Montserrat"; font-weight: 100 900; src: url("'
                         + (paths.FONTS_DIR / "Montserrat-Variable.ttf").resolve().as_uri() + '"); }')
        pg.evaluate("document.fonts.load('800 40px Montserrat').then(() => document.fonts.ready)")
        kutular = pg.evaluate(kapak.OLC_JS)
        tarayici.close()
    siniflar = sorted(ku["sinif"] for ku in kutular)
    beklenen = {"yazisiz": [], "bolunmus": ["etiket", "etiket"], "rozet": ["baslik"]}.get(kalip, ["baslik", "ek"])
    assert siniflar == beklenen, kutular
    assert [ku["arka"] for ku in kutular if ku["sinif"] == "ek"] == ([True] if kalip in kapak.KESITLI else [False] if "ek" in beklenen else [])
    olcum = kapak.olc(platform, b, tmp_path / "yok.jpg", kutular)
    assert olcum["gecti"], olcum["notlar"]


def test_kontursuz_yazi_zemine_karisirsa_uyarir(tmp_path):
    cv2, np = pytest.importorskip("cv2"), pytest.importorskip("numpy")
    kutu = [{"sinif": "baslik", "arka": False, "punto": 94, "kutu": [5, 30, 60, 70]}]
    b = {"satir1": "İKİ", "satir2": "SÖZ", "stil": "acik-siyah"}  # siyah yazı, kontursuz
    for ton, gecer in ((250, True), (10, False)):
        jpg = tmp_path / f"zemin-{ton}.jpg"
        cv2.imencode(".jpg", np.full((720, 1280, 3), ton, np.uint8))[1].tofile(str(jpg))
        olcum = kapak.olc("youtube", b, jpg, kutu)
        assert olcum["gecti"] is gecer and (olcum["kontrast"] >= 3) is gecer, olcum
    koyu = tmp_path / "zemin-10.jpg"
    assert kapak.olc("youtube", {**b, "karart": True}, koyu, kutu)["kontrast"] is None, "karartma açıkken zemin ölçülmez"
    assert kapak.olc("youtube", {**b, "stil": "turuncu"}, koyu, kutu)["gecti"], "konturlu yazı zemine bağlı değildir"
