"""Ekip v3 deterministik çekirdeği (ADR 0048, 0053): atama ve dilim sahipliği, plan doğrulama, paralel yamaların birleşmesi,
çapa eşleme, çakışma, QC yönlendirme, kural kapısı."""

import pytest

from vedit import ekip_v3
from vedit.ekip_sema import Gorev, KkGorev, Plan, Yama
from vedit.schemas import Kurgu


def _k():
    kel = [{"w": f"k{i}", "s": i * 0.5, "e": i * 0.5 + 0.4} for i in range(20)]
    return Kurgu.model_validate({
        "sekans": {"w": 1080, "h": 1920, "fps": 30},
        "kaynaklar": {"a": {"yol": "inputs:a.mp4", "sure": 10}},
        "kelimeler": {"a": kel},
        "izler": [{"id": "V2", "tur": "video"}, {"id": "V1", "tur": "video"}, {"id": "A1", "tur": "ses"}, {"id": "A2", "tur": "ses"}],
        "klipler": [{"id": "v", "iz": "V1", "tur": "video", "bas": 0, "sure": 10, "kaynak": "a"}],
        "altyazi": {"acik": True, "iz": "V1"},
    })


def test_baska_editorun_nesnesi_reddedilir():
    k = _k()
    with pytest.raises(SystemExit, match="başka editörün"):
        ekip_v3.yama_uygula(k, "E2", Yama(guncelle=[{"id": "v", "sure": 5}]))
    with pytest.raises(SystemExit, match="eklenemez"):
        ekip_v3.yama_uygula(k, "E3", Yama(ekle=[{"id": "x", "iz": "V2", "tur": "metin", "bas": 1, "sure": 1, "metin": "a"}]))
    # yabancı skaler alan yamayı düşürmez, yalnız o alan düşer
    dusen = []
    k2 = ekip_v3.yama_uygula(k, "E2", Yama(altyazi={"acik": False}), dusen)
    assert k2.altyazi.acik is True and dusen == ["E2:altyazi"]


def test_paralel_yamalar_cakismasiz_birlesir_ve_capalar_esler():
    k = _k()
    yamalar = {
        # E2 ve E3 tabana (tek parça kesim) göre yazdı: grafik 3.0 sn kelimesinde (k6), ses 7.0 sn kelimesinde (k14); çapa yok.
        "E2": Yama(ekle=[{"id": "g", "iz": "V2", "tur": "metin", "bas": 2.9, "sure": 1, "metin": "x"}]),
        "E3": Yama(ekle=[{"id": "s", "iz": "A2", "tur": "ses", "bas": 6.9, "sure": 0.4, "olay": {"tur": "vurgu"}}]),
        # E1 aynı anda ilk 1 sn'yi kesti.
        "E1": Yama(guncelle=[{"id": "v", "giris": 1, "sure": 9}]),
    }
    yeni, r = ekip_v3.birlestir(k, yamalar)
    assert set(r["uygulanan"]) == {"E1", "E2", "E3"} and not r["red"]
    assert r["capalanan"] == 2
    g = next(c for c in yeni.klipler if c.id == "g")
    s = next(c for c in yeni.klipler if c.id == "s")
    assert abs(g.bas - 1.9) < 1e-6 and abs(s.bas - 5.9) < 1e-6, "E1 kesimi 1 sn kaydırdı: olaylar kelimeleriyle geldi"
    # Hiçbir nesne iki editörce düzenlenmedi: her klibin tek sahibi
    assert {ekip_v3.sahip(yeni, c.iz) for c in yeni.klipler if c.id in ("g",)} == {"E2"}


def test_cakisma_geciste_grafik_itilir_iki_hero_bulgu():
    k = Kurgu.model_validate({
        "kaynaklar": {"a": {"yol": "inputs:a.mp4", "sure": 10}},
        "izler": [{"id": "V2", "tur": "video"}, {"id": "V1", "tur": "video"}],
        "klipler": [{"id": "v1", "iz": "V1", "tur": "video", "bas": 0, "sure": 4, "kaynak": "a"},
                    {"id": "v2", "iz": "V1", "tur": "video", "bas": 4, "sure": 4, "kaynak": "a", "gecis_giris": {"tur": "sil", "sure": 0.4}},
                    {"id": "g1", "iz": "V2", "tur": "sahne", "bas": 3.9, "sure": 2, "sahne": {"kind": "hook"}},
                    {"id": "g2", "iz": "V2", "tur": "sahne", "bas": 4.5, "sure": 2, "sahne": {"kind": "cta"}}],
    })
    itilen, bulgu = ekip_v3.cakisma_coz(k)
    g1 = next(c for c in k.klipler if c.id == "g1")
    assert "g1" in itilen and abs(g1.bas - 4.2) < 1e-6, "geçiş ortasındaki grafik geçiş bitince girer"
    assert any(b["klip"] == "g2" and "iki ana grafik" in b["sorun"] for b in bulgu), "1,7 sn itilemez: sahibine bulgu"


def test_qc_birlestirici_tekillestirir_ve_sahibe_yollar():
    k = _k()
    listeler = {
        "K1": [{"id": "K1-001", "hedef": "E1", "onem": "P1", "zaman": [2.0, 3.0], "katman": "V2", "kategori": "okunurluk", "sorun": "grafik okunmuyor", "beklenen": ""}],
        "K2": [{"id": "K2-001", "hedef": "E2", "onem": "P0", "zaman": [2.2, 2.8], "katman": "V2", "kategori": "okunurluk", "sorun": "yazı küçük", "beklenen": ""}],
        "K3": [{"id": "K3-001", "hedef": "E3", "onem": "P2", "zaman": [5, 6], "katman": "A2", "kategori": "ses", "sorun": "sfx yüksek", "beklenen": ""}],
    }
    b, kisit = ekip_v3.bulgu_birlestir(k, listeler)
    assert [x["id"] for x in b] == ["K2-001", "K3-001"], "aynı katman, kategori ve zaman: en ağır olan kalır"
    l = {"K1": [{**listeler["K1"][0], "kategori": "ritim"}]}
    b, kisit = ekip_v3.bulgu_birlestir(k, l)
    assert b[0]["hedef"] == "E2" and kisit["E1"], "V2 bulgusu E2'ye gider, E1 kısıt olarak görür"


def test_token_ozeti_tahmin_isaretler():
    assert ekip_v3.token_ozeti({"token": {"input_tokens": 10, "output_tokens": 5}}, "x", "y") == {"token": 15, "tahmini": False}
    o = ekip_v3.token_ozeti({"token": None}, "a" * 400, "b" * 400, gorsel=2)
    assert o == {"token": 200 + 3000, "tahmini": True}


def test_kalip_kaynak_bicimi_semadan_gecer():
    # instagram/1 koşusunda E3 kaynağı "dosya" alanıyla yazdı, 17 şema hatasıyla tüm ses katmanı düştü.
    assert '"yol": "library:music/' in ekip_v3.SABIT
    k = ekip_v3.yama_uygula(_k(), "E3", Yama(kaynaklar={"m1": {"yol": "library:music/pixabay/m1.mp3", "sure": 30}},
                                              ekle=[{"id": "mz", "iz": "A2", "tur": "ses", "bas": 0, "sure": 10, "kaynak": "m1"}]))
    assert k.kaynaklar["m1"].yol.startswith("library:")


def test_capali_klipte_bas_yoksa_capadan_hesaplanir():
    # instagram/1 piksel-8bit koşusunda E2 çapalı grafikleri `bas` olmadan yazdı; bütün katman düşüyordu.
    k = ekip_v3.yama_uygula(_k(), "E2", Yama(ekle=[{"id": "g", "iz": "V2", "tur": "metin", "sure": 1, "metin": "x",
                                                     "capa": {"kaynak": "a", "kelime": 6, "once_kare": 3}}]))
    g = next(c for c in k.klipler if c.id == "g")
    assert g.bas == pytest.approx(3.0 - 3 / 30, abs=0.01)


def test_bozuk_oge_duser_gerisi_birlesir():
    dusen = []
    y = Yama(ekle=[{"id": "iyi", "iz": "V2", "tur": "metin", "bas": 1, "sure": 1, "metin": "x"},
                   {"id": "kotu", "iz": "V2", "tur": "metin", "sure": 1, "metin": "y"}],
             kaynaklar={"m": {"dosya": "library/music/m.mp3"}})
    k = ekip_v3.yama_uygula(_k(), "E2", y, dusen)
    ids = {c.id for c in k.klipler}
    assert "iyi" in ids and "kotu" not in ids and "m" not in k.kaynaklar
    assert set(dusen) == {"E2:kotu", "E2:m"}


def test_suresiz_ogeye_varsayilan_sure():
    # instagram/1 temiz-kurumsal koşusunda E2/E3 öğeleri `bas` ve `sure` yazmadı; hepsi düştü.
    from vedit import native_motion
    ad = sorted(native_motion.kayitlar())[0]
    k = ekip_v3.yama_uygula(_k(), "E2", Yama(ekle=[{"id": "g", "iz": "V2", "tur": "motion", "bilesen": {"ad": ad, "param": {}},
                                                     "capa": {"kaynak": "a", "kelime": 4}}]))
    assert next(c for c in k.klipler if c.id == "g").sure > 0
    k = ekip_v3.yama_uygula(_k(), "E3", Yama(ekle=[{"id": "s", "iz": "A2", "tur": "ses", "olay": {"tur": "vurgu"},
                                                     "capa": {"kaynak": "a", "kelime": 4}}]))
    assert next(c for c in k.klipler if c.id == "s").sure == 0.3


def test_sekans_v1_sonunda_biter():
    k = ekip_v3.yama_uygula(_k(), "E3", Yama(kaynaklar={"m": {"yol": "library:music/m.mp3", "sure": 60}},
                                              ekle=[{"id": "mz", "iz": "A2", "tur": "ses", "bas": 0, "sure": 14, "kaynak": "m"},
                                                    {"id": "geç", "iz": "A2", "tur": "ses", "bas": 11, "sure": 0.3, "olay": {"tur": "vurgu"}}]))
    assert sorted(ekip_v3.sona_kirp(k)) == ["geç", "mz"]
    mz = next(c for c in k.klipler if c.id == "mz")
    assert mz.sure == 10 and mz.ses.fade_out >= 1.0 and all(c.id != "geç" for c in k.klipler)


def test_bilinmeyen_alt_alan_atilir_oge_kalir():
    # instagram/1: E3 müziği `ses.seviye` yazdı (şemada yok), müzik düşüyordu.
    dusen = []
    y = Yama(kaynaklar={"m": {"yol": "library:music/m.mp3", "sure": 60}},
             ekle=[{"id": "mz", "iz": "A2", "tur": "ses", "bas": 0, "sure": 9, "kaynak": "m", "ses": {"duck": True, "seviye": 0.3}}])
    k = ekip_v3.yama_uygula(_k(), "E3", y, dusen)
    assert next(c for c in k.klipler if c.id == "mz").ses.duck is True
    assert dusen == ["E3:mz.ses.seviye"] and y.ekle[0]["ses"]["seviye"] == 0.3


def test_bozuk_ic_alan_atilir_oge_kalir():
    # arvelior-hiz (ADR 0054): E4 müziğin kazanç zarfını [t, v] çifti yazdı; müzik klibi bütünüyle düşüyordu.
    dusen = []
    y = Yama(kaynaklar={"m": {"yol": "library:music/m.mp3", "sure": 60}},
             ekle=[{"id": "mz", "iz": "A2", "tur": "ses", "bas": 0, "sure": 9, "kaynak": "m",
                    "ses": {"duck": True, "kf": [[0.0, 1.0], [8.0, 0.0]]}}])
    k = ekip_v3.yama_uygula(_k(), "E3", y, dusen)
    mz = next(c for c in k.klipler if c.id == "mz")
    assert mz.ses.duck is True and mz.ses.kf == []
    assert dusen == ["E3:mz.ses.kf"]


def test_sozlesme_kelime_dizinleri(monkeypatch):
    monkeypatch.setattr(ekip_v3.yuz_bolge, "model_var", lambda: False)
    monkeypatch.setattr(ekip_v3.kurgu, "etkin_tema", lambda p, t: "varsayilan")
    soz = ekip_v3.sozlesme(None, _k(), None, None)
    assert soz["kelimeler"]["a"].startswith("0:k0@0.00 1:k1@0.50")


def test_ikon_cekim_sinirini_asmaz():
    from vedit import native_motion
    ad = next(a for a, v in native_motion.kayitlar().items() if v["meta"].get("tur") == "ikon")
    alt = native_motion.kayitlar()[ad]["meta"]["sure"]["min"]
    k = _k()
    k = ekip_v3.yama_uygula(k, "E1", Yama(guncelle=[{"id": "v", "sure": 5}],
                                          ekle=[{"id": "v2", "iz": "V1", "tur": "video", "bas": 5, "sure": 5, "kaynak": "a", "giris": 5}]))
    k = ekip_v3.yama_uygula(k, "E2", Yama(ekle=[
        {"id": "uzun", "iz": "V2", "tur": "motion", "bas": 5 - alt - 0.2, "sure": alt + 0.6, "bilesen": {"ad": ad, "param": {}}},
        {"id": "gec", "iz": "V2", "tur": "motion", "bas": 5 - alt / 2, "sure": alt, "bilesen": {"ad": ad, "param": {}}}]))
    assert sorted(ekip_v3.cekime_sigdir(k)) == ["gec", "uzun"]
    for c in k.klipler:
        if c.iz == "V2":
            assert c.bas + c.sure <= 5 + 1e-3 and c.sure >= alt - 1e-3


# ---------------------------------------------------------------- v3: atama, plan, kapı

def _atama5():
    """max seviyesindeki gibi: kurgu, 0-10 sn'yi beşe bölen grafik dilimleri, ses ve stil."""
    g = [Gorev(slot="E1", katmanlar=["kurgu"])]
    g += [Gorev(slot=f"E{i + 2}", katmanlar=["grafik"], aralik=[i * 2.0, i * 2.0 + 2.0]) for i in range(5)]
    g += [Gorev(slot="E7", katmanlar=["sfx", "muzik"]), Gorev(slot="E8", katmanlar=["stil"])]
    return ekip_v3.Atama(g)


def test_bes_grafik_dilimi_paralel_birlesir_ve_dilim_disi_oge_duser():
    k, a = _k(), _atama5()
    yamalar = {f"E{i + 2}": Yama(ekle=[{"id": f"g{i}", "iz": "V2", "tur": "metin", "bas": i * 2.0 + 0.5, "sure": 1, "metin": "x"}])
               for i in range(5)}
    yamalar["E3"] = Yama(ekle=[{"id": "g1", "iz": "V2", "tur": "metin", "bas": 2.5, "sure": 1, "metin": "x"},
                               {"id": "kacak", "iz": "V2", "tur": "metin", "bas": 7.0, "sure": 1, "metin": "y"}])
    yamalar["E8"] = Yama(motion_tema="varsayilan")
    yeni, r = ekip_v3.birlestir(k, yamalar, a)
    ids = {c.id for c in yeni.klipler}
    assert {f"g{i}" for i in range(5)} <= ids and "kacak" not in ids, "E3'ün 7 sn'deki öğesi E5'in diliminde: tek başına düşer"
    assert "E3:kacak(aralık dışı)" in r["dusen"] and not r["red"]
    assert yeni.motion_tema == "varsayilan"
    assert {a.sahip(yeni, c) for c in yeni.klipler if c.id == "g3"} == {"E5"}


def test_baska_katmana_yazan_yama_duser_skaler_alan_sahibine():
    k, a = _k(), _atama5()
    with pytest.raises(SystemExit, match="eklenemez"):
        ekip_v3.yama_uygula(k, "E2", Yama(ekle=[{"id": "s", "iz": "A2", "tur": "ses", "bas": 1, "sure": 0.3, "olay": {"tur": "vurgu"}}]), atama=a)
    dusen = []
    k2 = ekip_v3.yama_uygula(k, "E7", Yama(altyazi={"acik": False}), dusen, atama=a)
    assert k2.altyazi.acik is True and dusen == ["E7:altyazi"], "altyazı yalnız stil kartının"
    with pytest.raises(SystemExit, match="hf alanı"):
        ekip_v3.yama_uygula(k, "E7", Yama(hf={"x": "<div data-composition-id='x'></div>"}), atama=a)


def test_bulgu_katman_ve_zamandan_dilim_sahibine_gider():
    k, a = _k(), _atama5()
    l = {"K1": [{"id": "K1-001", "hedef": "E1", "onem": "P1", "zaman": [6.2, 6.8], "katman": "V2", "kategori": "okunurluk", "sorun": "s", "beklenen": ""}],
         "K2": [{"id": "K2-001", "onem": "P2", "zaman": [1, 2], "katman": "altyazi", "kategori": "okunurluk", "sorun": "s", "beklenen": ""}]}
    b, kisit = ekip_v3.bulgu_birlestir(k, l, a)
    assert {x["id"]: x["hedef"] for x in b} == {"K1-001": "E5", "K2-001": "E8"}
    assert kisit["E1"], "QC'nin yazdığı E1 kısıt olarak görür"


def _plan(gorevler, kk=None):
    return Plan(gorevler=[Gorev(**g) for g in gorevler], kk_gorevler=[KkGorev(**x) for x in (kk or [{"slot": "K1", "rol": "genel"}])])


def test_plan_dogrulama():
    iyi = [{"slot": "E1", "katmanlar": ["kurgu", "stil"]}, {"slot": "E2", "katmanlar": ["grafik", "sfx", "muzik"]}]
    assert ekip_v3.plan_dogrula(_plan(iyi), "low", 10) == []
    assert any("editör slotları" in h for h in ekip_v3.plan_dogrula(_plan(iyi[:1]), "low", 10))
    iki_kurgu = [{"slot": "E1", "katmanlar": ["kurgu"]}, {"slot": "E2", "katmanlar": ["kurgu", "grafik", "sfx", "muzik", "stil"]}]
    assert any("kurgu bölünmez" in h for h in ekip_v3.plan_dogrula(_plan(iki_kurgu), "low", 10))
    bosluklu = [{"slot": "E1", "katmanlar": ["kurgu"]}, {"slot": "E2", "katmanlar": ["grafik"], "aralik": [0, 4]},
                {"slot": "E3", "katmanlar": ["grafik"], "aralik": [5, 10]}, {"slot": "E4", "katmanlar": ["sfx", "muzik", "stil"]}]
    kk = [{"slot": "K1", "rol": "kurgu-ses"}, {"slot": "K2", "rol": "gorsel"}]
    assert any("boşluksuz" in h for h in ekip_v3.plan_dogrula(_plan(bosluklu, kk), "medium", 10))
    bosluklu[2]["aralik"] = [4, 10]
    assert ekip_v3.plan_dogrula(_plan(bosluklu, kk), "medium", 10) == []
    assert any("kapsamalı" in h for h in ekip_v3.plan_dogrula(_plan(bosluklu, [{"slot": "K1", "rol": "kural"}, {"slot": "K2", "rol": "gorsel"}]), "medium", 10))


@pytest.mark.parametrize("seviye", ["low", "medium", "high", "xhigh", "max"])
def test_varsayilan_dagitim_her_seviyede_gecerli(seviye):
    from vedit.ekip_sema import SEVIYE
    k = _k()
    p = ekip_v3.varsayilan_dagitim(seviye, k)
    assert (len(p.gorevler), len(p.kk_gorevler)) == SEVIYE[seviye]
    assert ekip_v3.plan_dogrula(p, seviye, ekip_v3._bitis(k)) == []


def test_kural_kapisi_eksik_uyumu_ve_reddi_sahibine_yazar(monkeypatch):
    monkeypatch.setattr(ekip_v3.kurgu, "denetle", lambda p, k: ["V2 g9: renk stilde yok"])
    monkeypatch.setattr(ekip_v3.kurgu_kalite, "uyarilar", lambda *a, **kw: [])
    monkeypatch.setattr(ekip_v3.kurgu, "etkin_tema", lambda p, t: "varsayilan")
    k, a = _k(), _atama5()
    yamalar = {"E2": Yama(ekle=[{"id": "g9", "iz": "V2", "tur": "metin", "bas": 0.5, "sure": 1, "metin": "x"}]),
               "E3": Yama(guncelle=[{"id": "v", "sure": 5}], kural_uyum=[{"id": "K0001", "nasil": "x"}])}
    ihlal, genel = ekip_v3.kural_denetimi(None, k, yamalar, a, {"E2": ["K0001"], "E3": ["K0001"]})
    assert any(x.startswith("kural_uyum eksik: K0001") for x in ihlal["E2"])
    assert any("renk stilde yok" in x for x in ihlal["E2"]), "denetim mesajındaki klip kimliği sahibine gider"
    assert any(x.startswith("yama reddedildi") for x in ihlal["E3"]) and not genel


def test_oto_duzelt_zoom_yogunlugu_ve_kisa_grafik():
    """ADR 0054: render'dan önce kodla düzeltilen kusurlar. Eşik slop'tan gelir: dakikada en çok 6 zoom/punch olayı."""
    from vedit import native_motion, slop
    klipler = [{"id": f"v{i}", "iz": "V1", "tur": "video", "bas": i * 3.0, "sure": 3.0, "kaynak": "a",
                "hazir": [{"ad": "punch", "t": 0.5}, {"ad": "el_kamerasi"}]} for i in range(10)]
    ad = next(a for a, r in native_motion.kayitlar().items() if (r["meta"].get("sure") or {}).get("min", 0) >= 1.0)
    alt = native_motion.kayitlar()[ad]["meta"]["sure"]["min"]
    klipler += [{"id": "g1", "iz": "V2", "tur": "motion", "bas": 4.0, "sure": 0.4, "bilesen": {"ad": ad, "param": {}}},
                {"id": "g2", "iz": "V2", "tur": "motion", "bas": 20.0, "sure": 0.4, "bilesen": {"ad": ad, "param": {}}},
                {"id": "g3", "iz": "V2", "tur": "motion", "bas": 20.6, "sure": 1.0, "bilesen": {"ad": ad, "param": {}}}]
    k = Kurgu.model_validate({"sekans": {"w": 1080, "h": 1920, "fps": 30}, "kaynaklar": {"a": {"yol": "inputs:a.mp4", "sure": 30}},
                              "izler": [{"id": "V2", "tur": "video"}, {"id": "V1", "tur": "video"}], "klipler": klipler})
    out = ekip_v3.oto_duzelt(k)
    by = {c.id: c for c in k.klipler}
    punch = [c.id for c in k.klipler if any(e.get("ad") == "punch" for e in c.hazir)]
    assert len(punch) == int(slop.OLAY_YOGUN_DAKIKA * 30 / 60), out
    assert all(any(e.get("ad") == "el_kamerasi" for e in by[f"v{i}"].hazir) for i in range(10)), "sessiz efekt dokunulmaz"
    assert by["g1"].sure == pytest.approx(alt), "kısa grafik sınırına uzar"
    assert by["g2"].sure == pytest.approx(0.6), "sonraki klibe taşmadan uzar"
    assert any("zoom/punch" in x for x in out)


def test_slop_bulgulari_k9_bicimi(tmp_path):
    import json
    (tmp_path / "olcum.json").write_text(json.dumps({"slop": {"bulgular": [
        {"kod": "OLAY_YOGUN", "seviye": "P1", "bas": None, "bit": None, "kanit": "dakikada 19 zoom"},
        {"kod": "SES_OLU_HAVA", "seviye": "P1", "bas": 3.0, "bit": 4.5, "kanit": "1.5 sn sessizlik"},
        {"kod": "PALET", "seviye": "P2", "bas": 0, "bit": 1, "kanit": "x"}]}}), encoding="utf-8")
    b = ekip_v3.slop_bulgulari(tmp_path, 30.0)
    assert [x["kategori"] for x in b] == ["ritim", "ses"] and b[0]["zaman"] == [0.0, 30.0] and b[1]["zaman"] == [3.0, 4.5]
    assert all(x["katman"] == "V1" and x["onem"] == "P1" for x in b), "P2 girmez, bulgu kurgu sahibine gider"


def test_rol_metni_frontmatter_atar_ve_paketler_dosya_okutmaz(monkeypatch):
    m = ekip_v3.rol_metni(["editor-kurgu", "editor-kurgu", "yok-boyle-rol"])
    assert m and not m.startswith("---") and "tools:" not in m.split("\n")[0]
    assert "\n\n" not in m[:3]
    from vedit.ekip_sema import EkipAyar
    k = _k()
    p = type("P", (), {"work": __import__("pathlib").Path("yok"), "studyo": "instagram", "ad": "x"})()
    monkeypatch.setattr(ekip_v3.kural, "yukle", lambda: ekip_v3.kural.Depo())
    metin = ekip_v3.plan_paketi(p, k, EkipAyar(), None, ekip_v3.varsayilan_dagitim("medium", k))
    assert "oku" not in metin.split("## Kullanıcı isteği")[0].replace("okuma", ""), "orkestratör rol dosyası okumaya yollanmaz"
    assert "(transkript yok)" in metin, "digest istemin içinde"
