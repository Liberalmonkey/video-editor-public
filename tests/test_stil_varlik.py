"""Stile özel varlık deposu, tam stil izolasyonu, stil: kaynak kökü, native dışa aktarma ve .zip stil paketi testleri."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from vedit import aiedit, cli, ekip_v2, hizli, karakter, kurgu, kurgu_kalite, motion_ice, native_motion, paths, stil, stil_varlik
from vedit.schemas import Kurgu


@pytest.fixture
def ortam(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "STUDIOS", tmp_path / "studios")
    monkeypatch.setattr(paths, "REFERENCES", tmp_path / "refs")
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "inputs")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "outputs")
    for s in ("instagram", "ugc", "youtube-animasyon"):
        d = tmp_path / "studios" / s
        d.mkdir(parents=True, exist_ok=True)
        (d / "studio.yaml").write_text("style: varsayilan\n", encoding="utf-8")
        stil.kaydet(s, "stil-a", "# Stil A\n")
        stil.kaydet(s, "stil-b", "# Stil B\n")
    return tmp_path


def test_depo_sema_oku_yaz_ve_stil_listesi(ortam):
    depo = stil_varlik.oku("instagram", "stil-a")
    assert depo.surum == 1 and depo.yuklenenler == [] and depo.yalniz_bunlar is False

    with pytest.raises(ValueError):
        stil_varlik.StilVarlik.model_validate({
            "id": "x", "ad": "X", "tur": "motion", "dosya": "a", "orijinal": "b", "eklenme": "2026-11-21", "fazla": 1,
        })

    stiller = {s["ad"]: s for s in stil.liste("instagram")}
    assert stiller["stil-a"]["varlik_sayisi"] == 0
    assert stiller["stil-a"]["varliklar_ozet"]["toplam"] == 0


def test_yukle_tum_turler_benzersiz_kimlik_ve_sil(ortam, tmp_path):
    # 1) motion (alfa webm + lottie json + svg + siyah mp4)
    w1 = tmp_path / "Parlama Efekti.webm"
    w1.write_bytes(b"webm-icerik")
    v1 = stil_varlik.yukle("instagram", "stil-a", w1, tur="motion", baslik="Parlama", ne_zaman="Hook girişinde", etiketler=["ışık", "hook"], yontem="alfa")
    assert v1.id == "parlama" and v1.tur == "motion" and v1.yontem == "alfa"
    assert v1.dosya == "varliklar/motion/parlama/parlama.webm"

    # Aynı başlıkla ikinci yükleme otomatik -2 alır
    v2 = stil_varlik.yukle("instagram", "stil-a", w1, tur="motion", baslik="Parlama", yontem="alfa")
    assert v2.id == "parlama-2"

    # Lottie JSON ve .lottie zip
    lot = tmp_path / "ok.json"
    lot.write_text(json.dumps({"v": "5.7", "fr": 30, "ip": 0, "op": 60, "w": 400, "h": 400, "layers": []}), encoding="utf-8")
    v_lot = stil_varlik.yukle("instagram", "stil-a", lot, tur="animasyon", baslik="Çizim Ok")
    assert v_lot.yontem == "lottie" and v_lot.sure == 2.0 and v_lot.w == 400 and v_lot.h == 400

    dot_lot = tmp_path / "anim.lottie"
    with zipfile.ZipFile(dot_lot, "w") as z:
        z.writestr("animations/main.json", json.dumps({"fr": 25, "ip": 0, "op": 50, "layers": []}))
    v_dot = stil_varlik.yukle("instagram", "stil-a", dot_lot, tur="motion")
    assert v_dot.yontem == "lottie" and v_dot.sure == 2.0

    # Bozuk Lottie reddedilir
    bozuk_lot = tmp_path / "bozuk.json"
    bozuk_lot.write_text(json.dumps({"merhaba": 1}), encoding="utf-8")
    with pytest.raises(ValueError, match="Lottie"):
        stil_varlik.yukle("instagram", "stil-a", bozuk_lot, tur="motion")

    # 2) karakter (.json + görsel)
    kar_f = tmp_path / "maskot.json"
    kar_f.write_text(json.dumps({"title": "Stil Maskotu", "ne_zaman": "Açıklama anında", "renkler": {"govde": "vurgu"}}), encoding="utf-8")
    v_kar = stil_varlik.yukle("instagram", "stil-a", kar_f, tur="karakter", baslik="Maskot")
    assert v_kar.id == "maskot" and v_kar.yontem == "karakter_json" and v_kar.dosya.endswith("karakter.json")

    # 3) gorsel ve ses
    svg_f = tmp_path / "ikon.svg"
    svg_f.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"></svg>', encoding="utf-8")
    v_gorsel = stil_varlik.yukle("instagram", "stil-a", svg_f, tur="gorsel")
    assert v_gorsel.yontem == "svg"

    ses_f = tmp_path / "alkis.wav"
    ses_f.write_bytes(b"RIFF0000WAVE")
    v_ses = stil_varlik.yukle("instagram", "stil-a", ses_f, tur="ses")
    assert v_ses.tur == "ses" and v_ses.yontem == "ham"

    # Desteklenmeyen uzantı veya tür reddedilir
    with pytest.raises(ValueError, match="desteklenmeyen uzantı"):
        stil_varlik.yukle("instagram", "stil-a", ses_f, tur="gorsel")
    with pytest.raises(ValueError, match="Geçersiz varlık türü"):
        stil_varlik.yukle("instagram", "stil-a", ses_f, tur="bilinmeyen")

    # Dosya erişimi ve silme
    norm_yol, kayit = stil_varlik.varlik_dosyasi("instagram", "stil-a", "parlama", bicim="normalize")
    orij_yol, _ = stil_varlik.varlik_dosyasi("instagram", "stil-a", "parlama", bicim="orijinal")
    assert norm_yol.is_file() and orij_yol.is_file() and kayit.id == "parlama"

    silinen = stil_varlik.sil("instagram", "stil-a", "parlama-2")
    assert silinen.id == "parlama-2" and not (stil.klasor("instagram", "stil-a") / "varliklar" / "motion" / "parlama-2").exists()
    with pytest.raises((KeyError, ValueError)):
        stil_varlik.sil("instagram", "stil-a", "olmayan-varlik")


def test_tam_stil_izolasyonu_ve_karakter_entegrasyonu(ortam, tmp_path):
    kar_a = tmp_path / "k_a.json"
    kar_a.write_text(json.dumps({"title": "A Karakteri", "ne_zaman": "A stili"}), encoding="utf-8")
    stil_varlik.yukle("instagram", "stil-a", kar_a, tur="karakter", baslik="ozel-kedi")

    # stil-b'nin deposuna veya karakter listesine ASLA sızmaz
    assert stil_varlik.oku("instagram", "stil-b").yuklenenler == []
    assert "ozel-kedi" in karakter.karakterler(stil.klasor("instagram", "stil-a"))
    assert "ozel-kedi" not in karakter.karakterler(stil.klasor("instagram", "stil-b"))
    assert "ozel-kedi" not in karakter.karakterler(None)

    p = hizli.Proje("instagram", "proje1")
    k = Kurgu.model_validate({
        "izler": [{"id": "V1", "tur": "video"}],
        "klipler": [{"id": "c1", "iz": "V1", "tur": "sahne", "bas": 0, "sure": 3, "sahne": {"kind": "karakter", "layout": "full", "karakter": "ozel-kedi"}}],
    })
    stil.sec(p, "stil-a")
    assert kurgu.denetle(p, k) == []

    stil.sec(p, "stil-b")
    hatalar = kurgu.denetle(p, k)
    assert any("bilinmeyen karakter 'ozel-kedi'" in h for h in hatalar)


def test_kurgu_stil_koku_hazirla_screen_ve_uyumsuzluk_uyarisi(ortam, tmp_path, monkeypatch):
    from vedit import ff
    monkeypatch.setattr(ff, "probe", lambda f: {"duration": 2.0, "video": {"width": 1080, "height": 1920}})
    p = hizli.Proje("instagram", "p1")
    stil.sec(p, "stil-a")

    siyah_f = tmp_path / "isik.mp4"
    siyah_f.write_bytes(b"mp4")
    v_siyah = stil_varlik.yukle("instagram", "stil-a", siyah_f, tur="motion", baslik="isik-sizintisi", yontem="siyah", atif="Işık: Özel")

    lot_f = tmp_path / "rozet.json"
    lot_f.write_text(json.dumps({"v": "5.7", "fr": 30, "ip": 0, "op": 45, "layers": []}), encoding="utf-8")
    v_lot = stil_varlik.yukle("instagram", "stil-a", lot_f, tur="animasyon", baslik="rozet")

    baska_f = tmp_path / "baska.webm"
    baska_f.write_bytes(b"webm")
    v_baska = stil_varlik.yukle("instagram", "stil-b", baska_f, tur="motion", baslik="yabanci", yontem="alfa")

    yol_siyah = stil_varlik.kurgu_yolu("instagram", "stil-a", v_siyah.dosya)
    yol_lot = stil_varlik.kurgu_yolu("instagram", "stil-a", v_lot.dosya)
    yol_baska = stil_varlik.kurgu_yolu("instagram", "stil-b", v_baska.dosya)

    assert kurgu.dosya(p, yol_siyah).is_file()
    with pytest.raises(ValueError):
        kurgu.dosya(p, "stil:instagram/stil-a/../../gizli.txt")
    with pytest.raises(ValueError):
        kurgu.dosya(p, "stil:instagram/stil-a")

    k = Kurgu.model_validate({
        "kaynaklar": {
            "K1": {"yol": yol_siyah, "sure": 2.0, "ses": False},
            "K2": {"yol": yol_baska, "sure": 2.0, "ses": False},
        },
        "izler": [{"id": "V3", "tur": "video"}, {"id": "V2", "tur": "video"}, {"id": "V1", "tur": "video"}],
        "klipler": [
            {"id": "c1", "iz": "V1", "tur": "motion", "kaynak": "K1", "bas": 0, "sure": 2},
            {"id": "c2", "iz": "V2", "tur": "motion", "bas": 0, "sure": 2, "bilesen": {"ad": "dis/lottie", "param": {"dosya": yol_lot}}},
            {"id": "c3", "iz": "V3", "tur": "motion", "kaynak": "K2", "bas": 2.5, "sure": 1.5},
        ],
    })
    assert motion_ice.karisim_haritasi(k) == {"K1": "screen"}
    assert motion_ice.atif_satirlari(k) == ["Işık: Özel"]

    # Aktif stil stil-a iken stil-b varlığı STIL_VARLIK_UYUMSUZ uyarısı verir
    uyarilar = kurgu_kalite.uyarilar(k, p=p)
    uyumsuz = [u for u in uyarilar if u["kod"] == "STIL_VARLIK_UYUMSUZ"]
    assert len(uyumsuz) == 1 and "stil-b" in uyumsuz[0]["kanit"]

    # hazirla() stil: kaynaklarını _k/ ve dis/ altına bağlar
    kurgu.yaz(p.work, k)
    render_f = kurgu.hazirla(p)
    render = json.loads(render_f.read_text(encoding="utf-8"))
    assert (p.work / "public" / "_k" / "K1.mp4").is_file()
    lottie_klip = next(c for c in render["klipler"] if c["id"] == "c2")
    assert lottie_klip["bilesen"]["param"]["dosya"].startswith("public:dis/")
    assert (p.work / "public" / "dis" / "rozet.json").is_file()


def test_secki_yalniz_bunlar_aiedit_ve_ekip_v2(ortam, tmp_path):
    tum_native = sorted(native_motion.kayitlar())
    assert len(tum_native) >= 2
    secilen = [tum_native[0]]

    with pytest.raises(ValueError, match="Bilinmeyen native"):
        stil_varlik.secki_guncelle("instagram", "stil-a", secili_native=["olmayan/bilesen"])

    depo = stil_varlik.secki_guncelle("instagram", "stil-a", secili_native=secilen, secili_kutuphane=["kutup-1"], yalniz_bunlar=True)
    assert depo.secili_native == secilen and depo.yalniz_bunlar is True

    w = tmp_path / "ozel.webm"
    w.write_bytes(b"webm")
    stil_varlik.yukle("instagram", "stil-a", w, tur="motion", baslik="Özel Vurgu", ne_zaman="Zirve anında", yontem="alfa")

    baglam = stil_varlik.baglam_metni("instagram", "stil-a")
    assert "yalniz_bunlar: true" in baglam and "stil:instagram/stil-a/" in baglam and secilen[0] in baglam

    p = hizli.Proje("instagram", "p2")
    stil.sec(p, "stil-a")
    k = kurgu.bos("instagram")

    # ekip_v2 E2 paketi yalnız seçili native bileşeni içerir, diğerlerini içermez
    paket_metni = ekip_v2.paket(p, k, "E2", {"surum": 2}, p.work / "edit" / "ekip")
    assert f"`{secilen[0]}`" in paket_metni
    assert f"`{tum_native[1]}`" not in paket_metni
    assert "Seçili Stilin Özel Varlıkları" in paket_metni

    # aiedit istek dosyası da özel varlığı ve kısıtlı native kataloğu içerir
    istek_f = aiedit._istek_yaz(p, k, stil_adi="stil-a", notu=None)
    istek_metni = istek_f.read_text(encoding="utf-8")
    assert "Seçili Stilin Özel Varlıkları" in istek_metni
    assert f"`{secilen[0]}`" in istek_metni
    assert f"`{tum_native[1]}`" not in istek_metni


def test_native_disa_aktar_onbellek_ve_param_dogrulama(ortam, monkeypatch):
    bilesen = sorted(native_motion.kayitlar())[0]
    with pytest.raises(ValueError):
        stil_varlik.native_disa_aktar("instagram", "stil-a", "olmayan/bilesen")
    with pytest.raises(ValueError):
        stil_varlik.native_disa_aktar("instagram", "stil-a", bilesen, en_boy="4:3")  # type: ignore[arg-type]

    cagrilar = []

    def sahte_run(cmd, **kw):
        cagrilar.append(cmd)
        assert "MotionTekil" in cmd and "--codec=vp9" in cmd and "--pixel-format=yuva420p" in cmd
        props_arg = next(a for a in cmd if a.startswith("--props=")).removeprefix("--props=")
        props = json.loads(Path(props_arg).read_text(encoding="utf-8"))
        assert props["ad"] == bilesen and props["en_boy"] == "9:16" and props["tema"]["dosyalar"]
        cikti_yolu = Path(cmd[4])
        cikti_yolu.write_bytes(b"WEBM-ALPHA")

    monkeypatch.setattr(stil_varlik.subprocess, "run", sahte_run)
    f1 = stil_varlik.native_disa_aktar("instagram", "stil-a", bilesen, en_boy="9:16", sure=1.5)
    assert f1.is_file() and f1.read_bytes() == b"WEBM-ALPHA" and len(cagrilar) == 1

    # İkinci çağrı önbellekten anında döner
    f2 = stil_varlik.native_disa_aktar("instagram", "stil-a", bilesen, en_boy="9:16", sure=1.5)
    assert f2 == f1 and len(cagrilar) == 1


def test_paket_zip_disa_ice_ve_zip_slip_korumasi(ortam, tmp_path):
    w = tmp_path / "parlama.webm"
    w.write_bytes(b"webm-veri")
    stil_varlik.yukle("instagram", "stil-a", w, tur="motion", baslik="Parlama", yontem="alfa")

    # .disa önbelleği zip'e girmemeli
    disa_k = stil.klasor("instagram", "stil-a") / ".disa"
    disa_k.mkdir(parents=True)
    (disa_k / "onbellek.webm").write_bytes(b"cache")

    ref_k = stil.referans_klasoru("instagram", "stil-a")
    ref_k.mkdir(parents=True)
    (ref_k / "ref1.jpg").write_bytes(b"jpg")

    zip_yolu = tmp_path / "stil-a.stil.zip"
    stil_varlik.paket_zip_uret("instagram", "stil-a", zip_yolu)
    assert zip_yolu.is_file()

    with zipfile.ZipFile(zip_yolu, "r") as z:
        isimler = set(z.namelist())
        assert "STYLE.md" in isimler and "varliklar.json" in isimler and "referanslar/ref1.jpg" in isimler
        assert not any(".disa" in n for n in isimler)

    # Başka bir stüdyoya yeni adla içe aktar
    sonuc = stil_varlik.paket_zip_ice_al("ugc", zip_yolu, yeni_ad="alinan-stil")
    assert sonuc["ad"] == "alinan-stil" and sonuc["varlik_sayisi"] == 1
    assert (stil.klasor("ugc", "alinan-stil") / "varliklar" / "motion" / "parlama" / "parlama.webm").is_file()

    # uzerine_yaz=False iken var olan stili ezmez
    with pytest.raises(ValueError, match="zaten var"):
        stil_varlik.paket_zip_ice_al("ugc", zip_yolu, yeni_ad="alinan-stil", uzerine_yaz=False)
    stil_varlik.paket_zip_ice_al("ugc", zip_yolu, yeni_ad="alinan-stil", uzerine_yaz=True)

    # Zip-slip saldırısı engellenir
    kotu_zip = tmp_path / "kotu.zip"
    with zipfile.ZipFile(kotu_zip, "w") as z:
        z.writestr("STYLE.md", "# Stil")
        z.writestr("../../gizli.txt", "saldiri")
    with pytest.raises(ValueError, match="zip-slip"):
        stil_varlik.paket_zip_ice_al("ugc", kotu_zip, yeni_ad="kotu-stil")
    assert not (ortam / "gizli.txt").exists()


def test_cli_stil_varlik_ve_stil_paket(ortam, tmp_path, capsys):
    svg = tmp_path / "etiket.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding="utf-8")

    cli.main(["stil-varlik", "ekle", "instagram", "stil-a", str(svg), "--tur", "gorsel", "--baslik", "Etiket"])
    assert "Eklendi: etiket" in capsys.readouterr().out

    cli.main(["stil-varlik", "liste", "instagram", "stil-a", "--json"])
    liste_json = json.loads(capsys.readouterr().out)
    assert len(liste_json["yuklenenler"]) == 1 and liste_json["yuklenenler"][0]["id"] == "etiket"

    zip_f = tmp_path / "paket.zip"
    cli.main(["stil-paket", "disa", "instagram", "stil-a", "-o", str(zip_f)])
    assert zip_f.is_file()
    capsys.readouterr()

    cli.main(["stil-paket", "ice", "ugc", str(zip_f), "--ad", "cli-stil"])
    assert "ugc/cli-stil (1 varlık)" in capsys.readouterr().out

    cli.main(["stil-varlik", "sil", "instagram", "stil-a", "etiket"])
    assert "Silindi: etiket" in capsys.readouterr().out
