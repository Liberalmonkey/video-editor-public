"""vedit ai-edit: ajan, hazirla, taslak ve ff.probe taklit edilir; doğrulama, geri yükleme ve geçmiş sınanır."""

import json

import pytest

from vedit import aiedit, ajan_cagri, ff, hizli, kurgu, paths


@pytest.fixture
def proje(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "inputs")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "outputs")
    p = hizli.Proje("instagram", "deneme")
    p.girdi.mkdir(parents=True)
    (p.girdi / "1.mp4").write_bytes(b"video")

    monkeypatch.setattr(ff, "probe", lambda f: {
        "file": f.name, "duration": 10.0,
        "video": {"width": 1080, "height": 1920, "fps": 30},
        "audio": {"codec": "aac", "sample_rate": 48000, "channels": 2},
    })

    def sahte_hazirla(prj, **k):
        for d in ("analysis", "edit", "renders", "qa", "public"):
            (prj.work / d).mkdir(parents=True, exist_ok=True)
        tr = {"files": {"1": {"segments": [{"start": 0.0, "end": 4.0, "text": "Merhaba dünya", "words": [
            {"w": "Merhaba", "s": 0.0, "e": 1.5}, {"w": "dünya", "s": 2.0, "e": 4.0},
        ]}]}}}
        (prj.work / "analysis" / "transcript.json").write_text(json.dumps(tr), encoding="utf-8")
        (prj.work / "analysis" / "digest.txt").write_text("# 1.mp4\n[0.00-4.00] Merhaba dünya\n", encoding="utf-8")

    monkeypatch.setattr(hizli, "hazirla", sahte_hazirla)
    monkeypatch.setattr(hizli, "taslak", lambda prj, **k: prj.work / "renders" / "taslak.mp4")
    return p


def test_kurgu_degismezse_durur(proje, monkeypatch):
    monkeypatch.setattr(ajan_cagri, "calistir", lambda istek, **k: ("ok", "oturum-1"))
    with pytest.raises(SystemExit, match="AI edit yapmadı"):
        aiedit.calistir(proje)


def test_iki_turda_bozuk_json_eski_kurguyu_geri_yukler(proje, monkeypatch):
    oturumlar = []

    def bozuk_ajan(istek, **k):
        oturumlar.append(k.get("oturum"))
        kurgu.yol(proje.work).write_text("{bozuk json", encoding="utf-8")
        return "bozuk", "oturum-2"

    monkeypatch.setattr(ajan_cagri, "calistir", bozuk_ajan)
    with pytest.raises(SystemExit, match="AI edit geçersiz kurgu yazdı, eski kurgu geri yüklendi"):
        aiedit.calistir(proje)

    assert oturumlar == [None, "oturum-2"]
    geri = kurgu.oku(proje.work)
    assert geri.rev == 0
    assert len(geri.klipler) == 1 and geri.klipler[0].sure == 10.0


def test_gecerli_degisiklik_rev_gecmis_ve_taslak(proje, monkeypatch):
    taslaklar, finaller = [], []
    monkeypatch.setattr(hizli, "taslak", lambda prj, **k: taslaklar.append(prj))
    monkeypatch.setattr(hizli, "final", lambda prj, **k: finaller.append((prj, k)))

    def duzenleyen_ajan(istek, **k):
        mevcut = kurgu.oku(proje.work)
        mevcut.klipler[0].sure = 4.0
        mevcut.klipler[0].konusmaci = True
        kurgu.yol(proje.work).write_text(mevcut.model_dump_json(indent=1), encoding="utf-8")
        (proje.work / "edit" / "ai-edit.rapor.md").write_text("- 04:00-10:00 sessizlik kırpıldı\n", encoding="utf-8")
        return "tamam", "oturum-3"

    monkeypatch.setattr(ajan_cagri, "calistir", duzenleyen_ajan)
    aiedit.calistir(proje, notu="Sıkı kurgu yap", final=True, final_ek={"yenile": True})

    yeni = kurgu.oku(proje.work)
    assert yeni.rev == 1
    assert yeni.klipler[0].sure == 4.0 and yeni.klipler[0].konusmaci is True
    assert len(yeni.kelimeler["inputs_1_mp4"]) == 2
    gecmis = proje.work / "edit" / "kurgu-gecmis" / "000000.json"
    assert gecmis.exists()
    assert json.loads(gecmis.read_text(encoding="utf-8"))["klipler"][0]["sure"] == 10.0
    assert taslaklar == [proje]
    assert finaller == [(proje, {"yenile": True})]


def _uc_klip(proje):
    """Üç ardışık klipli kurgu: aralık düzeltmesi ortadakine (3-6 sn) uygulanır."""
    aiedit._kurgu_hazirla(proje)
    k = kurgu.oku(proje.work)
    ilk = k.klipler[0]
    k.klipler = [ilk.model_copy(update={"id": ad, "bas": b, "giris": b, "sure": 3.0}) for ad, b in (("a", 0.0), ("b", 3.0), ("c", 6.0))]
    kurgu.yol(proje.work).write_text(k.model_dump_json(indent=1), encoding="utf-8")


def _ajan(proje, degistir):
    def ajan(istek, **k):
        mevcut = kurgu.oku(proje.work)
        degistir({c.id: c for c in mevcut.klipler})
        kurgu.yol(proje.work).write_text(mevcut.model_dump_json(indent=1), encoding="utf-8")
        return "tamam", "oturum"
    return ajan


def test_aralik_disina_dokunan_edit_geri_alinir(proje, monkeypatch):
    hizli.hazirla(proje)
    _uc_klip(proje)
    monkeypatch.setattr(ajan_cagri, "calistir", _ajan(proje, lambda c: setattr(c["a"], "zoom", 1.1)))
    with pytest.raises(SystemExit, match="aralık dışındaki klip değişmiş"):
        aiedit.calistir(proje, aralik=(3.0, 6.0))
    assert kurgu.oku(proje.work).klipler[0].zoom == 1.0


def test_aralik_ici_kisalir_sonrasi_kayar_ve_ozet_yazilir(proje, monkeypatch):
    hizli.hazirla(proje)
    _uc_klip(proje)

    def kisalt(c):
        c["b"].sure = 2.0
        c["c"].bas = 5.0

    monkeypatch.setattr(ajan_cagri, "calistir", _ajan(proje, kisalt))
    aiedit.calistir(proje, aralik=(3.0, 6.0))
    assert [(c.id, c.bas, c.sure) for c in kurgu.oku(proje.work).klipler] == [("a", 0.0, 3.0), ("b", 3.0, 2.0), ("c", 5.0, 3.0)]
    ozet = json.loads((proje.work / "edit" / "ai-edit.ozet.json").read_text(encoding="utf-8"))
    assert ozet["klip"] == [3, 3] and ozet["sure"] == [9.0, 8.0] and ozet["rev"] == ozet["once_rev"] + 1
    assert (proje.work / "edit" / "kurgu-gecmis" / f"{ozet['once_rev']:06}.json").exists()
    assert "yalnız 3.00-6.00 sn" in (proje.work / "edit" / "ai-edit.istek.md").read_text(encoding="utf-8")


def test_yalniz_senaryo_animasyon_modu(proje, monkeypatch):
    (proje.girdi / "1.mp4").unlink()
    (proje.girdi / "senaryo.md").write_text("Bir. İki. Üç.", encoding="utf-8")
    monkeypatch.setattr(hizli, "hazirla", lambda prj, **k: pytest.fail("medya yokken hazirla çağrılmamalı"))

    def sahne_yazan(istek, **k):
        mevcut = kurgu.oku(proje.work)
        mevcut.klipler.append(aiedit.Klip(
            id="s1", iz="V1", bas=0, sure=3, tur="sahne", sahne={"layout": "full", "kind": "text", "bg": "dark", "lines": [{"t": "Bir", "at": 0.1}]}))
        kurgu.yol(proje.work).write_text(mevcut.model_dump_json(indent=1), encoding="utf-8")
        return "tamam", "oturum"

    monkeypatch.setattr(ajan_cagri, "calistir", sahne_yazan)
    aiedit.calistir(proje)
    istek = (proje.work / "edit" / "ai-edit.istek.md").read_text(encoding="utf-8")
    assert "Animasyon Modu" in istek and "senaryo.md" in istek and "Ses yok" in istek
    assert [c.tur for c in kurgu.oku(proje.work).klipler] == ["sahne"]


def test_yalniz_seslendirme_konusma_klibi_olur(proje):
    (proje.girdi / "1.mp4").rename(proje.girdi / "1.wav")
    hizli.hazirla(proje)
    k = aiedit._kurgu_hazirla(proje)
    c = k.klipler[0]
    assert (c.iz, c.tur, c.olay) == ("A1", "ses", {"konusma": True}) and "A1" in [i.id for i in k.izler]
    assert len(k.kelimeler[c.kaynak]) == 2 and aiedit._animasyon(k)


def test_aralik_disina_yeni_klip_eklenemez(proje, monkeypatch):
    hizli.hazirla(proje)
    _uc_klip(proje)

    def ekle(yer):
        def ajan(istek, **k):
            mevcut = kurgu.oku(proje.work)
            if any(c.id == "yeni" for c in mevcut.klipler):  # düzeltme turu: aynı hatalı kurgu kalır
                return "tamam", "oturum"
            mevcut.klipler.append(aiedit.Klip(id="yeni", iz="V2", bas=yer, sure=1.0, tur="metin", metin="x"))
            kurgu.yol(proje.work).write_text(mevcut.model_dump_json(indent=1), encoding="utf-8")
            return "tamam", "oturum"
        return ajan

    monkeypatch.setattr(ajan_cagri, "calistir", ekle(7.0))
    with pytest.raises(SystemExit, match="aralığın dışına yeni klip"):
        aiedit.calistir(proje, aralik=(3.0, 6.0))
    assert len(kurgu.oku(proje.work).klipler) == 3
    monkeypatch.setattr(ajan_cagri, "calistir", ekle(4.0))
    aiedit.calistir(proje, aralik=(3.0, 6.0))
    assert [c.id for c in kurgu.oku(proje.work).klipler][-1] == "yeni"


def test_bos_kurgu_sonradan_gelen_girdiyi_alir(proje):
    # WHY: ornek-proje 2026-11-27. Stüdyo boş kurgu yazmıştı; girdiler sonradan gelince edit görüntüsüz kaldı.
    kurgu.yaz(proje.work, kurgu.bos(proje.studyo))
    hizli.hazirla(proje)
    k = aiedit._kurgu_hazirla(proje)
    v1 = [c for c in k.klipler if c.iz == "V1"]
    assert [c.kaynak for c in v1] == ["inputs_1_mp4"] and v1[0].tur == "video"
    assert len(k.kelimeler["inputs_1_mp4"]) == 2
    assert kurgu.oku(proje.work).rev == k.rev
    aiedit.girdi_denetimi(proje, k)  # sağlıklı kurgu durmaz


def test_girdisi_olan_kurgu_yeniden_tohumlanmaz(proje):
    hizli.hazirla(proje)
    ilk = aiedit._kurgu_hazirla(proje)
    ikinci = aiedit._kurgu_hazirla(proje)
    assert [c.id for c in ikinci.klipler] == [c.id for c in ilk.klipler]


def test_girdi_denetimi_videosuz_kurguda_durur(proje):
    k = kurgu.bos(proje.studyo)
    with pytest.raises(SystemExit, match="kurguya alınamadı"):
        aiedit.girdi_denetimi(proje, k)
