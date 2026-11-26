"""Yayın metni (ADR 0055): doğrulama, yayin.md blokları, iş kuyruğu beyaz listesi, API."""

import json

import pytest

from vedit import hizli, paths, yayin


@pytest.fixture
def proje(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    monkeypatch.setattr(yayin, "_sure", lambda yol, mtime: 42.0)  # ffprobe gerekmesin
    p = hizli.Proje("instagram", "x")
    p.cikti.mkdir(parents=True)
    (p.girdi).mkdir(parents=True)
    for ad in ("10.mp4", "2.mp4"):
        (p.cikti / ad).write_bytes(b"\0")
    (p.cikti / "2.srt").write_text("1\n00:00:00,000 --> 00:00:02,000\nMerhaba dünya\n\n2\n00:01:05,000 --> 00:01:07,000\nİkinci\n",
                                    encoding="utf-8")
    return p


def paket(**ek):
    d = {"baslik": "Claude ile 3 dakikada kurgu", "aciklama": "Videoyu nasıl hızlandırdığımı anlatıyorum.",
         "hashtagler": ["#kurgu", "claude", "#yapayzeka"], "notlar": ""}
    return {**d, **ek}


def test_dogrula_temizler_ve_kabul_eder():
    temiz, hata, _ = yayin.dogrula({"video": "a.mp4", "platformlar": {"reels": paket(), "fazla": paket()}}, ["reels"])
    assert not hata
    assert list(temiz["platformlar"]) == ["reels"]  # istenmeyen platform atılır
    assert temiz["platformlar"]["reels"]["hashtagler"] == ["#kurgu", "#claude", "#yapayzeka"]


@pytest.mark.parametrize("bozuk, parca", [
    (paket(hashtagler=["#a", "#b", "#c", "#d", "#e", "#f"]), "6 hashtag"),
    (paket(hashtagler=["#a", "#A", "#b"]), "tekrar"),
    (paket(hashtagler=["#iki kelime", "#b", "#c"]), "geçersiz hashtag"),
    (paket(baslik="x" * 101), "sınır 100"),
    (paket(aciklama="x" * 2190), "sınır 2200"),
])
def test_dogrula_sinirlar(bozuk, parca):
    temiz, hata, _ = yayin.dogrula({"video": "a.mp4", "platformlar": {"reels": bozuk}}, ["reels"])
    assert temiz is None and any(parca in h for h in hata), hata


def test_dogrula_eksik_platform_ve_youtube_kurallari():
    _, hata, _ = yayin.dogrula({"video": "a.mp4", "platformlar": {"reels": paket()}}, ["reels", "youtube"])
    assert "youtube: platform eksik" in hata
    yt = paket(baslik="a < b", bolumler=[{"t": "0:00", "baslik": "Giriş"}, {"t": "0:05", "baslik": "x"}, {"t": "1:00", "baslik": "y"}])
    _, hata, _ = yayin.dogrula({"video": "a.mp4", "platformlar": {"youtube": yt}}, ["youtube"])
    assert any("'<'" in h for h in hata) and any("bölümler" in h for h in hata)
    yt = paket(etiketler=["claude code"] * 50)
    _, hata, _ = yayin.dogrula({"video": "a.mp4", "platformlar": {"youtube": yt}}, ["youtube"])
    assert any("etiketler" in h for h in hata)


def test_kapali_alanlar_bosaltilir():
    temiz, _, _ = yayin.dogrula({"video": "a.mp4", "platformlar": {"reels": paket(etiketler=["x"], bolumler=[{"t": "0:00", "baslik": "a"}])}},
                                ["reels"])
    assert temiz["platformlar"]["reels"]["etiketler"] == [] and temiz["platformlar"]["reels"]["bolumler"] == []


def test_etiket_uzunlugu_youtube_sayimi():
    assert yayin.etiket_uzunlugu(["ab", "c d"]) == 2 + 3 + 2 + 1


def test_kopya_metni():
    pk = {"aciklama": "Metin", "bolumler": [{"t": "0:00", "baslik": "Giriş"}], "hashtagler": ["#a", "#b"]}
    assert yayin.kopya_metni("youtube", pk) == "Metin\n\n0:00 Giriş\n\n#a #b"


def test_md_bloklari_dogal_sira_ve_atif_korunur(proje):
    f = proje.cikti / "yayin.md"
    f.write_text("# Elle yazılmış not\n\n" + hizli.ATIF_BASLIK + "\n- Lottie: X, CC BY\n", encoding="utf-8")
    v = {"platformlar": {"reels": paket(hashtagler=["#a", "#b", "#c"])}}
    yayin.md_yaz(proje, "10", "10.mp4", v)
    yayin.md_yaz(proje, "2", "2.mp4", v)
    yayin.md_yaz(proje, "10", "10.mp4", {"platformlar": {"reels": paket(baslik="Yeni başlık", hashtagler=["#a", "#b", "#c"])}})
    m = f.read_text(encoding="utf-8")
    assert m.startswith("# Elle yazılmış not")
    assert m.index("<!-- yayin:2 -->") < m.index("<!-- yayin:10 -->") < m.index(hizli.ATIF_BASLIK)
    assert m.count("<!-- yayin:10 -->") == 1 and "Yeni başlık" in m and "- Lottie: X, CC BY" in m
    assert "#a #b #c" in m


def test_atif_yaz_bloklari_bozmaz(proje, monkeypatch):
    from vedit import kurgu, motion_ice
    yayin.md_yaz(proje, "2", "2.mp4", {"platformlar": {"reels": paket()}})
    k = proje.work / "kurgu.json"
    k.parent.mkdir(parents=True, exist_ok=True)
    k.write_text("{}")
    monkeypatch.setattr(kurgu, "yol", lambda w: k)
    monkeypatch.setattr(kurgu, "oku", lambda w: None)
    monkeypatch.setattr(motion_ice, "atif_satirlari", lambda _k: ["Lottie: X, CC BY"])
    hizli.atif_yaz(proje)
    yayin.md_yaz(proje, "10", "10.mp4", {"platformlar": {"reels": paket()}})  # atıftan sonra yeni blok
    m = (proje.cikti / "yayin.md").read_text(encoding="utf-8")
    assert m.index("<!-- /yayin:2 -->") < m.index("<!-- /yayin:10 -->") < m.index(hizli.ATIF_BASLIK)
    assert m.rstrip().endswith("- Lottie: X, CC BY")


def test_videolar_dogal_sira_ve_srt(proje):
    v = yayin.videolar(proje)
    assert [x["ad"] for x in v] == ["2.mp4", "10.mp4"]
    assert v[0]["srt"] and not v[1]["srt"] and v[0]["paket"] is None


def test_istek_srt_metnini_ve_semayi_icerir(proje):
    f = yayin.istek_yaz(proje, proje.cikti / "2.mp4", ["reels", "youtube"], "tr")
    m = f.read_text(encoding="utf-8")
    assert "[0:00] Merhaba dünya" in m and "[1:05] İkinci" in m
    assert str(yayin.paket_yolu(proje, "2").resolve()) in m and "`youtube`" in m


def test_metin_yoksa_durur(proje):
    with pytest.raises(SystemExit):
        yayin.metin_kaynagi(proje, proje.cikti / "10.mp4")


def test_video_bul_disariyi_reddeder(proje):
    for kotu in ("../x.mp4", "work/a.mp4", "yok.mp4", "2.srt"):
        with pytest.raises(SystemExit):
            yayin.video_bul(proje, kotu)


def test_uret_dogrular_ve_duzeltme_turu(proje, monkeypatch):
    from vedit import ajan_cagri
    cagri = []

    def sahte_calistir(istem, **ek):
        ilk = not ek.get("oturum")
        cagri.append(("ilk" if ilk else "duzelt", ek, istem))
        pk = paket(hashtagler=["#a"] * 2) if ilk else paket()
        yayin.paket_yolu(proje, "2").write_text(json.dumps({"video": "2.mp4", "platformlar": {"reels": pk}}), encoding="utf-8")
        return "", "oturum-1"

    monkeypatch.setattr(ajan_cagri, "calistir", sahte_calistir)
    v = yayin.uret(proje, "2.mp4", ["reels"])
    assert [c[0] for c in cagri] == ["ilk", "duzelt"]
    assert cagri[0][1]["model"] == "claude-opus-5-5" and cagri[1][1]["oturum"] == "oturum-1"
    assert "Get-Content" in cagri[0][2] and "istek-2.md" in cagri[0][2]  # Codex kabukla okuyabilsin
    assert v["_uretim"]["motor"] == "claude" and "<!-- yayin:2 -->" in (proje.cikti / "yayin.md").read_text(encoding="utf-8")


def test_yanittan_json():
    v = {"video": "a.mp4", "platformlar": {"reels": paket()}}
    assert yayin.yanittan_json("Yazamadım.\n```json\n" + json.dumps(v) + "\n```\nBitti") == v
    assert yayin.yanittan_json("önce " + json.dumps(v) + " sonra") == v
    assert yayin.yanittan_json("```json\n{\"x\": 1}\n```") is None


def test_uret_dosya_yazilamazsa_yanittan_alir(proje, monkeypatch):
    from vedit import ajan_cagri
    v = {"video": "2.mp4", "platformlar": {"reels": paket()}}
    monkeypatch.setattr(ajan_cagri, "calistir", lambda istem, **ek: ("İzin yok.\n```json\n" + json.dumps(v) + "\n```", "o"))
    assert yayin.uret(proje, "2.mp4", ["reels"])["platformlar"]["reels"]["baslik"] == paket()["baslik"]


def test_uret_iki_kez_hatali_onceki_paketi_korur(proje, monkeypatch):
    from vedit import ajan_cagri
    yayin.paket_yolu(proje, "2").parent.mkdir(parents=True, exist_ok=True)
    yayin.paket_yolu(proje, "2").write_text('{"eski": true}', encoding="utf-8")

    def bozuk(*a, **ek):
        yayin.paket_yolu(proje, "2").write_text("bozuk", encoding="utf-8")
        return "", None

    monkeypatch.setattr(ajan_cagri, "calistir", bozuk)
    with pytest.raises(SystemExit):
        yayin.uret(proje, "2.mp4", ["reels"], motor="codex")
    assert yayin.paket_oku(proje, "2") == {"eski": True}
    assert yayin.paket_yolu(proje, "2").with_suffix(".hatali.json").exists()


def test_kaydet_dogrular(proje):
    v, _ = yayin.kaydet(proje, "2.mp4", {"platformlar": {"reels": paket()}})
    assert v["_uretim"]["duzenlendi"]
    with pytest.raises(SystemExit):
        yayin.kaydet(proje, "2.mp4", {"platformlar": {"reels": paket(baslik="")}})


def test_platform_listesi(proje):
    assert yayin.platform_listesi(None, "youtube-animasyon") == ["youtube"]
    assert yayin.platform_listesi("reels, tiktok,reels", "instagram") == ["reels", "tiktok"]
    with pytest.raises(SystemExit):
        yayin.platform_listesi("myspace", "instagram")


def test_is_arguman_beyaz_liste(proje):
    fastapi = pytest.importorskip("fastapi")
    from vedit.studio import isler
    a = isler.arguman(isler.Istek(komut="yayin", studyo="instagram", ad="x", video="2.mp4", platformlar=["reels", "linkedin"]))
    assert a == ["yayin", "instagram/x", "--video=2.mp4", "--platform=reels,linkedin"]
    assert isler.arguman(isler.Istek(komut="yayin", studyo="instagram", ad="x", hepsi=True))[2] == "--hepsi"
    for kotu in ({"video": "../2.mp4"}, {"video": "2.mp4", "platformlar": ["myspace"]}, {}):
        with pytest.raises(fastapi.HTTPException):
            isler.arguman(isler.Istek(komut="yayin", studyo="instagram", ad="x", **kotu))
