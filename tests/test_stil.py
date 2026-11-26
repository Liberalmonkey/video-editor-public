"""Stil paketleri testleri: liste, üretim, doğrulama ve projeye stil seçimi."""

import pytest

from vedit import ajan_cagri, hizli, paths, reference, stil


@pytest.fixture
def ortam(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "STUDIOS", tmp_path / "studios")
    monkeypatch.setattr(paths, "REFERENCES", tmp_path / "refs")
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "inputs")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "outputs")
    s = tmp_path / "studios" / "instagram"
    s.mkdir(parents=True)
    (s / "studio.yaml").write_text("style: varsayilan\n", encoding="utf-8")
    return tmp_path


def test_liste_iki_kaynagi_birlestirir_ve_ozel_adlari_atlar(ortam):
    k = stil.klasor("instagram", "hazir-stil")
    k.mkdir(parents=True)
    (k / "STYLE.md").write_text("# Stil", encoding="utf-8")
    (k / "MOTION.md").write_text("# Hareket", encoding="utf-8")

    r = stil.referans_klasoru("instagram", "aday-stil")
    (r / "analysis").mkdir(parents=True)
    (r / "analysis" / "digest.md").write_text("ozet", encoding="utf-8")
    (r / "ornek.mp4").write_bytes(b"v")
    (r / "kare.png").write_bytes(b"g")

    for atlanan in ("images", "analysis", "gecersiz ad!"):
        (paths.REFERENCES / "instagram" / atlanan).mkdir(parents=True)
        (paths.STUDIOS / "instagram" / "styles" / atlanan).mkdir(parents=True)

    sonuc = stil.liste("instagram")
    assert [x["ad"] for x in sonuc] == ["aday-stil", "hazir-stil"]
    assert sonuc[0] == {
        "ad": "aday-stil",
        "hazir": False,
        "style_md": "",
        "motion_md": "",
        "referanslar": ["kare.png", "ornek.mp4"],
        "kapak": True,
        "palet": {},
    }
    assert sonuc[1]["hazir"] is True
    assert sonuc[1]["kapak"] is False
    assert stil.kapak_yolu("instagram", "aday-stil").name == "kare.png"
    assert sonuc[1]["style_md"] == "# Stil"
    assert sonuc[1]["motion_md"] == "# Hareket"


def test_palet_tokens_renklerinden_gelir(ortam):
    k = stil.klasor("instagram", "renkli")
    k.mkdir(parents=True)
    (k / "tokens.json").write_text(
        '{"colors": {"bg": "#000000", "fg": "#FFFFFF", "accent": "#2CE66D", "surface": "#151B22", "muted": "#8B949E"}}',
        encoding="utf-8",
    )
    assert stil.palet("instagram", "renkli") == {
        "zemin": "#000000", "yazi": "#FFFFFF", "vurgu": "#2CE66D", "ikincil": "#151B22", "soluk": "#8B949E",
    }
    assert stil.palet("instagram", "yok") == {}


def test_uret_referans_yok_basarili_ve_bozuk_tokens(ortam, monkeypatch):
    with pytest.raises(SystemExit, match="Referans yok"):
        stil.uret("instagram", "yeni")

    r = stil.referans_klasoru("instagram", "yeni")
    r.mkdir(parents=True)
    (r / "clip.mp4").write_bytes(b"v")
    (r / "ref.jpg").write_bytes(b"g")

    analiz_cagrilari = []

    def sahte_run(out_dir, urls, images, *, minutes=5.0, videos=()):
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "digest.md").write_text("# Digest", encoding="utf-8")
        analiz_cagrilari.append((urls, [p.name for p in images], [p.name for p in videos]))
        return {"videos": [], "images": None, "errors": []}

    monkeypatch.setattr(reference, "run", sahte_run)

    def sahte_dosyadan(istek_dosyasi, **ek):
        metin = istek_dosyasi.read_text(encoding="utf-8")
        assert "ADR 0043" in metin and "digest.md" in metin
        hedef = stil.klasor("instagram", "yeni")
        (hedef / "STYLE.md").write_text("# STYLE", encoding="utf-8")
        (hedef / "MOTION.md").write_text("# MOTION", encoding="utf-8")
        (hedef / "tokens.json").write_text('{"name": "yeni", "colors": {"accent": "#3366FF", "bg": "#101418", "fg": "#FFFFFF"}}', encoding="utf-8")
        return "tamam", "oturum-1"

    # Paket kendi paletinden tema üretir (ADR 0043); gerçek kütüphaneye yazmasın.
    import shutil
    from vedit import motion, paths
    shutil.copytree(paths.MOTION_DIR / "tema", ortam / "motion" / "tema")
    monkeypatch.setattr(paths, "MOTION_DIR", ortam / "motion")
    monkeypatch.setattr(ajan_cagri, "dosyadan", sahte_dosyadan)
    hedef = stil.uret("instagram", "yeni", motor="claude", model="sonnet")
    assert hedef == stil.klasor("instagram", "yeni")
    assert stil.motion_temasi(hedef) == "paket-instagram-yeni" and motion.tema_yolu("paket-instagram-yeni")
    assert analiz_cagrilari == [([], ["ref.jpg"], ["clip.mp4"])]

    def bozuk_tokens(istek_dosyasi, **ek):
        (stil.klasor("instagram", "yeni") / "tokens.json").write_text("{bozuk", encoding="utf-8")
        return "tamam", None

    monkeypatch.setattr(ajan_cagri, "dosyadan", bozuk_tokens)
    with pytest.raises(SystemExit, match="tokens.json"):
        stil.uret("instagram", "yeni")

    def eksik_dosya(istek_dosyasi, **ek):
        (stil.klasor("instagram", "yeni") / "MOTION.md").unlink()
        return "tamam", None

    monkeypatch.setattr(ajan_cagri, "dosyadan", eksik_dosya)
    with pytest.raises(SystemExit, match="eksik"):
        stil.uret("instagram", "yeni")


def test_sec_secili_adi_ve_secili(ortam):
    p = hizli.Proje("instagram", "deneme")
    assert stil.secili_adi(p) == "varsayilan"
    assert stil.secili(p) is None  # varsayılan stil paketi hazır değilse sessizce None

    with pytest.raises(SystemExit, match="Stil hazır değil"):
        stil.sec(p, "olmayan")

    with pytest.raises(SystemExit, match="Stil yok"):
        stil.secili(p, "olmayan")

    stil.kaydet("instagram", "ozel", "# Özel Stil")
    stil.sec(p, "ozel")
    assert stil.secili_adi(p) == "ozel"
    assert stil.secili(p) == stil.klasor("instagram", "ozel")

    # Seçilmiş stil sonradan silinirse açık seçim olduğu için SystemExit verir
    (stil.klasor("instagram", "ozel") / "STYLE.md").unlink()
    with pytest.raises(SystemExit, match="Stil yok"):
        stil.secili(p)


def test_sil_paket_referans_ve_proje_secimini_kaldirir(ortam):
    p = hizli.Proje("instagram", "deneme")
    stil.kaydet("instagram", "eski", "# Eski")
    ref = stil.referans_klasoru("instagram", "eski")
    ref.mkdir(parents=True)
    (ref / "a.jpg").write_bytes(b"x")
    stil.sec(p, "eski")
    baska = hizli.Proje("instagram", "diger")
    (baska.work / "edit").mkdir(parents=True)
    (baska.work / "edit" / "stil.txt").write_text("baska", encoding="utf-8")

    silinen = stil.sil("instagram", "eski")
    assert len(silinen) == 3
    assert not stil.klasor("instagram", "eski").exists() and not ref.exists()
    assert not (p.work / "edit" / "stil.txt").exists()
    assert (baska.work / "edit" / "stil.txt").exists()  # başka stili seçen projeye dokunmaz
    assert all(s["ad"] != "eski" for s in stil.liste("instagram"))

    with pytest.raises(SystemExit, match="Stil yok"):
        stil.sil("instagram", "eski")
    with pytest.raises(SystemExit, match="Stil adı"):
        stil.sil("instagram", "../studios")
