"""Adım 2/4/5/6 etki ekseni, öz denetim, ilke temelli istemler ve kural yükü testleri (ADR 0064)."""

import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from vedit import ekip, ekip_v3, ff, hizli, kural, kurgu, paths, suru, yaratici
from vedit.ekip_sema import SEVIYE, Bulgu, EkipAyar, Gorev, KkGorev, KontrolCikti, Slot, Yama
from vedit.schemas import Kurgu

BRIF = {
    "tez": "Tek komutla kurguyu dakikalar içinde bitir.",
    "metafor": "Dağınık kâğıtların tek çizgiye dizilmesi",
    "iplik": "İnce turuncu odak çizgisi",
    "enerji": [{"aralik": [0, 3], "seviye": 5, "neden": "hook"}, {"aralik": [3, 9], "seviye": 2, "neden": "nefes"}],
    "imza_anlari": [{"t": 4.5, "soz": "dört", "ne": "tek vuruş ve sessizlik"}],
    "ses": "Kısa sessizlik ardından tek vuruş",
    "riskler": ["Orta bölümü sakin tut"],
    "yasak": ["her kesimde whoosh"],
}


def _kurgu():
    kel = [{"w": f"k{i}", "s": i * 0.5, "e": i * 0.5 + 0.4} for i in range(18)]
    return Kurgu.model_validate({
        "sekans": {"w": 1080, "h": 1920, "fps": 30},
        "kaynaklar": {"a": {"yol": "inputs:a.mp4", "sure": 9}},
        "kelimeler": {"a": kel},
        "izler": [{"id": "V2", "tur": "video"}, {"id": "V1", "tur": "video"}, {"id": "A1", "tur": "ses"}, {"id": "A2", "tur": "ses"}],
        "klipler": [{"id": "v", "iz": "V1", "tur": "video", "bas": 0, "sure": 9, "kaynak": "a"}],
    })


def _proje_mock(tmp_path: Path):
    work = tmp_path / "work"
    (work / "edit").mkdir(parents=True, exist_ok=True)
    return SimpleNamespace(work=work, studyo="instagram", ad="deneme")


def test_bulgu_etki_kategorisi_ve_kontrol_cikti_uretim_puani(tmp_path):
    kare = tmp_path / "kare.jpg"
    kare.write_bytes(b"jpg")
    b = Bulgu.model_validate({
        "id": "K1-001", "hedef": "E2", "onem": "P1", "zaman": [4.0, 5.0], "katman": "V2",
        "kategori": "etki", "kanit": str(kare), "sorun": "imza anı teslim edilmemiş",
        "beklenen": "4.5 sn imza anı tek vuruşla ve sessizlik sonrası kurulur",
    })
    assert b.kategori == "etki"

    # Değerler 1-5 aralığına kırpılır, bilinmeyen anahtar korunur.
    c = KontrolCikti.model_validate({
        "bulgular": [b.model_dump()],
        "brif": "düzelt",
        "uretim_puani": {"hook": 8, "imza_ani": 0, "ozel_eksen": 3.6, "bozuk": "yok", "bayrak": True},
    })
    assert c.uretim_puani == {"hook": 5, "imza_ani": 1, "ozel_eksen": 4}
    assert len(c.bulgular) == 1

    # Bozuk uretim_puani çıktıyı düşürmez, None olur.
    c_bozuk = KontrolCikti.model_validate({"bulgular": [b.model_dump()], "brif": "b", "uretim_puani": "gecersiz"})
    assert c_bozuk.uretim_puani is None and len(c_bozuk.bulgular) == 1
    c_bos = KontrolCikti.model_validate({"bulgular": [], "uretim_puani": {"hook": "abc"}})
    assert c_bos.uretim_puani is None


def test_yama_oz_denetim_ve_yama_ozeti():
    y = Yama.model_validate({"oz_denetim": "a" * 700})
    assert len(y.oz_denetim) == 600
    assert Yama().oz_denetim == ""
    assert '"oz_denetim":' in ekip_v3.SABIT

    oz = "\n".join(ekip_v3._yama_ozeti(Yama(oz_denetim="İmza anı kuruldu. " + "x" * 260)))
    satir = next(s for s in oz.splitlines() if s.startswith("- Öz denetim:"))
    assert len(satir.removeprefix("- Öz denetim: ")) == 200
    assert "Öz denetim:" not in "\n".join(ekip_v3._yama_ozeti(Yama()))


def test_paket_sablon_listesi_yok_ilke_arac_kutusu_ve_brif(tmp_path, monkeypatch):
    p = _proje_mock(tmp_path)
    k = _kurgu()
    kok = tmp_path / "ekip"
    kok.mkdir()
    monkeypatch.setattr(ekip_v3.kural, "yukle", lambda: kural.Depo())
    monkeypatch.setattr(ekip_v3.aiedit, "_hf_katalogu", lambda w, *a: "### HyperFrames grafikleri\n- (katalog)")
    monkeypatch.setattr(ekip_v3.aiedit, "_kasa_bolumu", lambda: "")
    monkeypatch.setattr(ekip_v3.aiedit, "_hazir_katalogu", lambda: "### Hazır efektler\n- (hazır)")
    monkeypatch.setattr(ekip_v3.native_motion, "katalog_ozeti", lambda izinli=None: ["- (native)"])
    monkeypatch.setattr(ekip_v3.yuz_bolge, "model_var", lambda: False)
    monkeypatch.setattr(ekip_v3.kurgu, "etkin_tema", lambda prj, t: "varsayilan")
    monkeypatch.setattr(ekip_v3, "_muzik_katalogu", lambda: "- (müzik)")
    soz = ekip_v3.sozlesme(p, k, None, None)

    # Brif yokken eski motion brifi davranışı sürer; sabit anlatı hiyerarşisi listesi yoktur.
    atama = ekip_v3.Atama.uc()
    m_grafik_yok = ekip_v3.paket(p, k, "E2", soz, kok, atama)
    assert "## Anlatı hiyerarşisi" not in m_grafik_yok
    assert "## Grafik ilkeleri" in m_grafik_yok
    assert "## Yaratıcı brif" not in m_grafik_yok
    assert "Brif beş bölüm (ADR 0063)" in m_grafik_yok
    for yasak_sablon in ("akis-ajan-agi", "arayuz-imlec-odak", "tipografi-bolum-kapsul", "tipografi/kinetik-baslik",
                         "tipografi/bolum-baslik", "tipografi/durum-rozeti", "tipografi/vurgu-soz", "kart/cta-karti"):
        assert yasak_sablon not in m_grafik_yok

    # Brif varken paket ## Yaratıcı brif taşır ve _motion_brif_ozeti brifin iplik/metaforunu yazar (istek farklı olsa bile oku() ile).
    yaratici.yaz(p.work, BRIF, "başka istek")
    mb = ekip_v3._motion_brif_ozeti(p, None)
    assert BRIF["iplik"] in mb and BRIF["metafor"] in mb and "Brif beş bölüm (ADR 0063)" not in mb
    m_grafik_var = ekip_v3.paket(p, k, "E2", soz, kok, atama, istek="başka istek")
    assert "## Yaratıcı brif" in m_grafik_var and BRIF["tez"] in m_grafik_var

    # Kurgu ve ses-stil blokları araç kutusudur; format örnekleri korunur.
    m_kurgu = ekip_v3.paket(p, k, "E1", soz, kok, atama, istek="başka istek")
    assert "4,5 saniye" in m_kurgu and "Yaratıcı yetki" in m_kurgu and "odak_karart" in m_kurgu
    assert "Her konuşan kafada" not in m_kurgu

    m_ses = ekip_v3.paket(p, k, "E3", soz, kok, atama, istek="başka istek")
    assert "sessizlik de bilinçli bir seçimdir" in m_ses
    assert '"gain_db": -12' in m_ses and '"olay": {"muzik": true}' in m_ses


def test_kontrol_istemi_ve_triyaj_etki_uretim_puani(tmp_path, monkeypatch):
    p = _proje_mock(tmp_path)
    qdir = tmp_path / "qc"
    qdir.mkdir()
    monkeypatch.setattr(ekip_v3.kural, "yukle", lambda: kural.Depo())
    atama = ekip_v3.Atama.uc()
    kg = KkGorev(slot="K1", rol="genel")

    # Brif yokken de rubrik ve uretim_puani istenir.
    f_yok = ekip_v3.kontrol_istemi(p, kg, {"_kok": qdir}, atama, "enerjik edit")
    m_yok = f_yok.read_text(encoding="utf-8")
    assert "## Yaratıcı brif" not in m_yok
    assert "## Üretim değeri" in m_yok and "kullanıcı isteğine" in m_yok
    assert '"uretim_puani":' in m_yok and "|etki" in m_yok

    # Brif varken ## Yaratıcı brif ve brif maddeleri eklenir.
    yaratici.yaz(p.work, BRIF, "enerjik edit")
    f_var = ekip_v3.kontrol_istemi(p, kg, {"_kok": qdir}, atama, "enerjik edit")
    m_var = f_var.read_text(encoding="utf-8")
    assert "## Yaratıcı brif" in m_var and BRIF["tez"] in m_var and "yaratıcı brife" in m_var
    assert '"uretim_puani": {"hook": 4, "imza_ani": 2, "brif_uyumu": 3, "ozgunluk": 3, "ritim_enerji": 4}' in m_var

    tri = ekip_v3.triyaj_paketi("enerjik edit", [], atama)
    assert "`etki` bulgusu zaman damgası, kare kanıtı" in tri and "zevk tartışmasıysa reddedilir" in tri


def test_zorunlu_kurallar_en_cok_8_ve_p0_her_zaman_girer(tmp_path, monkeypatch):
    assert ekip_v3.ZORUNLU_EN_COK == 8
    monkeypatch.setattr(kural, "paths", SimpleNamespace(LIBRARY=tmp_path / "lib", ROOT=paths.ROOT, rel=paths.rel))
    d = kural.Depo(kurallar=[
        *[kural.Kural(id=f"K{i + 1:04d}", metin=f"YAP: P1 kuralı {i}", hedef_rol="E1", onem="P1", kategori="kesim") for i in range(10)],
        *[kural.Kural(id=f"K{i + 11:04d}", metin=f"YAPMA: P0 kuralı {i}", hedef_rol="E1", onem="P0", kategori="kesim") for i in range(3)],
    ])
    kural.kaydet(d)

    p = _proje_mock(tmp_path)
    g = Gorev(slot="E1", katmanlar=["kurgu"])
    secilen = ekip_v3.zorunlu_kurallar(p, g, d, doldur=True)
    p0_ids = {kr.id for kr in d.kurallar if kr.onem == "P0"}
    assert len(p0_ids) == 3
    assert len(secilen) == 8 and p0_ids <= set(secilen)

    # P0 sayısı 8'i aşsa bile bütün P0'lar girer.
    d.kurallar += [kural.Kural(id=f"K{i + 20:04d}", metin=f"YAPMA: ekstra P0 {i}", hedef_rol="E1", onem="P0", kategori="kesim")
                   for i in range(7)]
    p0_hepsi = {kr.id for kr in d.kurallar if kr.onem == "P0"}
    assert len(p0_hepsi) == 10
    assert set(ekip_v3.zorunlu_kurallar(p, g, d, doldur=True)) == p0_hepsi


def test_ekip_v3_uretim_puani_ozet_ve_raporda_toplanir(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "inputs")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "outputs")
    monkeypatch.setattr(paths, "STUDIOS", tmp_path / "studios")
    monkeypatch.setattr(kural, "paths", SimpleNamespace(LIBRARY=tmp_path / "lib", ROOT=paths.ROOT, rel=paths.rel))
    kural.kaydet(kural.Depo())

    p = hizli.Proje("instagram", "etki")
    p.girdi.mkdir(parents=True)
    (p.girdi / "1.mp4").write_bytes(b"video")
    monkeypatch.setattr(ff, "probe", lambda f: {"file": Path(f).name, "duration": 9.0, "video": {"width": 1080, "height": 1920, "fps": 30},
                                                "audio": {"codec": "aac", "sample_rate": 48000, "channels": 2}})

    def sahte_hazirla(prj, **k):
        for d in ("analysis", "edit", "renders", "qa", "public"):
            (prj.work / d).mkdir(parents=True, exist_ok=True)
        kel = [{"w": w, "s": s, "e": e} for w, s, e in (("Bir", 0.0, 1.0), ("iki", 1.5, 3.0), ("üç", 4.0, 6.0), ("dört", 6.5, 8.5))]
        (prj.work / "analysis" / "transcript.json").write_text(
            json.dumps({"files": {"1": {"segments": [{"start": 0.0, "end": 8.5, "text": "Bir iki üç dört", "words": kel}]}}}), encoding="utf-8")
        (prj.work / "analysis" / "digest.txt").write_text("# 1.mp4\n[0.00-8.50] Bir iki üç dört\n", encoding="utf-8")

    def sahte_taslak(prj, **k):
        f = prj.work / "renders" / "taslak.mp4"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b"taslak")
        return f

    def sahte_izle(prj, video, kok):
        (kok / "izle").mkdir(parents=True, exist_ok=True)
        (kok / "izle" / "kare_0003.0.jpg").write_bytes(b"jpg")
        return {"_kok": kok, "taslak video": video}

    monkeypatch.setattr(hizli, "hazirla", sahte_hazirla)
    monkeypatch.setattr(hizli, "taslak", sahte_taslak)
    monkeypatch.setattr(hizli, "qc_taslak", sahte_taslak)
    monkeypatch.setattr(ekip, "izle", sahte_izle)
    monkeypatch.setattr(suru, "model_listesi", lambda **k: {"claude": ["m"]})

    def sahte_ajan(slot, istem, mod, yol, *, yedek=False, **_):
        f = Path(re.search(r"Read the file (.+?\.istem\.md)", istem).group(1))
        rol, asama = f.name.split(".")[0], f.parent.name
        meta = {"motor": slot.motor, "sure": 0.1, "token": {"input_tokens": 10}}
        if rol == "O" and asama == "plan":
            v = json.loads(ekip_v3.varsayilan_dagitim("medium", kurgu.oku(p.work)).model_dump_json(include={"gorevler", "kk_gorevler"}))
            return True, json.dumps({**v, "yaratici_brif": BRIF, "gerekce": "dengeli"}), meta
        if rol == "O" and asama == "triyaj":
            ids = re.findall(r'"id": "(K\d-\d{3})"', f.read_text(encoding="utf-8"))
            return True, json.dumps({"kabul": ids, "red": [], "kural_onay": []}), meta
        if rol.startswith("E"):
            return True, json.dumps({"ekle": [], "rapor": "tamam", "oz_denetim": "imza anı tek vuruşla kuruldu"}), meta
        kare = next((f.parent / "izle").glob("*.jpg"))
        puan = {"hook": 4, "imza_ani": 2, "ozgunluk": 3} if rol == "K1" else {"hook": 5, "imza_ani": 4, "ritim_enerji": 9}
        bulgu = ([{"id": f"{rol}-001", "onem": "P2", "zaman": [4.0, 5.0], "katman": "V2", "kategori": "etki",
                   "kanit": str(kare), "sorun": "imza anı zayıf", "beklenen": "4.5 sn tek vuruş"}]
                 if rol == "K1" else [])
        return True, "```json\n" + json.dumps({"bulgular": bulgu, "uretim_puani": puan, "brif": "etki notu"}) + "\n```", meta

    monkeypatch.setattr(ekip, "ajan", sahte_ajan)
    sl = Slot(motor="claude", model="m")
    ayar = EkipAyar(ekip_seviye="medium", gruplar={"orkestrator": sl, "editor": sl, "kk": sl})
    o = ekip_v3.calistir(p, ayar, notu="etkili kurgu")
    assert o["uretim_puani"] == {"hook": 4.5, "imza_ani": 3.0, "ozgunluk": 3.0, "ritim_enerji": 5.0}
    assert o["bulgular"] and o["bulgular"][0]["kategori"] == "etki"
    rapor = (p.work / "edit" / "ai-edit.rapor.md").read_text(encoding="utf-8")
    assert "- Üretim puanı: hook 4.5/5" in rapor
