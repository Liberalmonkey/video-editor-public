"""Ekip motoru v3 (ADR 0053): ayar ve göç, zaman bölüşü, bulgu şeması ve seviyeli, kapılı uçtan uca akış.

Ajanlar, hazirla, taslak ve izleme taklit edilir; gerçek motor çağrılmaz. Kural deposu geçici klasördedir.
"""
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from vedit import aiedit, ekip, ekip_v3, ff, hizli, kural, kurgu, paths
from vedit.ekip_sema import SEVIYE, EkipAyar, Slot


@pytest.fixture
def proje(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "inputs")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "outputs")
    monkeypatch.setattr(paths, "STUDIOS", tmp_path / "studios")
    p = hizli.Proje("instagram", "deneme")
    p.girdi.mkdir(parents=True)
    (p.girdi / "1.mp4").write_bytes(b"video")
    monkeypatch.setattr(ff, "probe", lambda f: {"file": Path(f).name, "duration": 9.0, "video": {"width": 1080, "height": 1920, "fps": 30},
                                                "audio": {"codec": "aac", "sample_rate": 48000, "channels": 2}})

    def sahte_hazirla(prj, **k):
        for d in ("analysis", "edit", "renders", "qa", "public"):
            (prj.work / d).mkdir(parents=True, exist_ok=True)
        kel = [{"w": w, "s": s, "e": e} for w, s, e in (("Bir", 0.0, 0.8), ("iki", 1.0, 2.6), ("üç", 3.4, 4.2), ("dört", 4.5, 5.6),
                                                         ("beş", 6.2, 7.0), ("altı", 7.2, 8.6))]
        tr = {"files": {"1": {"segments": [{"start": 0.0, "end": 8.6, "text": "Bir iki üç dört beş altı", "words": kel}]}}}
        (prj.work / "analysis" / "transcript.json").write_text(json.dumps(tr), encoding="utf-8")
        (prj.work / "analysis" / "digest.txt").write_text("# 1.mp4\n[0.00-8.60] Bir iki üç dört beş altı\n", encoding="utf-8")

    def sahte_taslak(prj, **k):
        f = prj.work / "renders" / "taslak.mp4"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b"taslak")
        return f

    monkeypatch.setattr(hizli, "hazirla", sahte_hazirla)
    monkeypatch.setattr(hizli, "taslak", sahte_taslak)

    def sahte_izle(prj, video, kok):
        (kok / "izle").mkdir(parents=True, exist_ok=True)
        (kok / "izle" / "kare_0003.0.jpg").write_bytes(b"jpg")
        return {"_kok": kok, "taslak video": video}

    monkeypatch.setattr(ekip, "izle", sahte_izle)
    return p


def _ayar(**ek):
    sl = Slot(motor="claude", model="m", yedek_motor="antigravity", yedek_model="y")
    return EkipAyar(gruplar={"orkestrator": sl, "editor": sl, "kk": sl}, **ek)


def _hazir(proje):
    hizli.hazirla(proje)
    return aiedit._kurgu_hazirla(proje)


def test_zaman_bolusu_kelime_arasina_duser(proje):
    k = _hazir(proje)
    araliklar = ekip.zaman_araliklari(k)
    assert len(araliklar) == 3 and araliklar[0][0] == 0 and araliklar[-1][1] == pytest.approx(9.0)
    kel = [(w["s"], w["e"]) for w in kurgu.izdusum(k)]
    for _, b in araliklar[:-1]:
        assert not any(s < b < e for s, e in kel), f"{b} bir kelimenin ortasında"


def test_json_cikar_ve_bulgu_dogrulama(tmp_path):
    kare = tmp_path / "k.jpg"
    kare.write_bytes(b"x")
    metin = ("Açıklama\n```json\n" + json.dumps({"bulgular": [
        {"id": "K2-001", "hedef": "E2", "onem": "P1", "zaman": [1, 2], "katman": "V2", "kategori": "stil", "kanit": str(kare), "sorun": "s", "beklenen": "b"},
        {"id": "K2-002", "hedef": "E2", "onem": "P0", "zaman": [3, 4], "katman": "V2", "kategori": "stil", "kanit": "yok.jpg", "sorun": "s", "beklenen": "b"}],
        "brif": "# Brif"}) + "\n```")
    o = ekip.json_cikar(metin)
    c, dus = ekip.bulgu_dogrula(o, "K2")
    assert [b.id for b in c.bulgular] == ["K2-001"] and dus and c.brif == "# Brif"
    assert ekip.bulgu_dogrula({"bulgular": [{"id": "X"}]}, "K2")[0] is None


def test_ayar_katmanlari_ve_eski_on_ayar_gocu(proje, tmp_path, monkeypatch):
    g = tmp_path / "ekip.json"
    eski = {s: {"motor": "claude", "model": f"m-{s}"} for s in ("E1", "E2", "E3", "K1", "K2", "K3")}
    g.write_text(json.dumps({"varsayilan": "a", "onayarlar": {"a": {"slotlar": eski, "bolus": "zaman", "tur": 2, "eszamanlilik": 6}}}),
                 encoding="utf-8")
    monkeypatch.setattr(ekip, "GLOBAL", g)
    a = ekip.ayar_yukle(proje)
    assert (a.gruplar["orkestrator"].model, a.gruplar["editor"].model, a.gruplar["kk"].model) == ("m-E1", "m-E2", "m-K1"), "6 slot gruplara göçer"
    (proje.work / "edit").mkdir(parents=True, exist_ok=True)
    (proje.work / "edit" / "ekip.json").write_text(json.dumps({"ekip_seviye": "high"}), encoding="utf-8")
    assert ekip.ayar_yukle(proje).ekip_seviye == "high"
    a = ekip.ayar_yukle(proje, ekip_seviye="max", eszamanlilik=None)
    assert a.ekip_seviye == "max" and a.slotlar() == ["O", *[f"E{i}" for i in range(1, 11)], *[f"K{i}" for i in range(1, 6)]]
    assert a.es() == 6, "eski ön ayarın eşzamanlılığı korunur"
    with pytest.raises(Exception):
        EkipAyar(gruplar={"editor": Slot(motor="claude")})
    with pytest.raises(Exception):
        EkipAyar(ezme={"E11": Slot(motor="claude")})
    assert EkipAyar(ezme={"E3": Slot(motor="codex")}).slot("E3").motor == "codex"


KURAL_METNI = "YAPMA: grafiği konuşmacının yüzünün üstüne koyma."
ADAY = "YAPMA: grafiği altyazı bandının üstüne koyma, bandın dışında tut."


def _kural_deposu(tmp_path, monkeypatch):
    monkeypatch.setattr(kural, "paths", SimpleNamespace(LIBRARY=tmp_path / "lib", ROOT=paths.ROOT, rel=paths.rel))
    d = kural.Depo()
    kural.ekle(d, KURAL_METNI, hedef_rol="E2", onem="P0", kategori="grafik")
    kural.kaydet(d)
    return d.kurallar[0].id


def _sahte_ekip(proje, kayit: list):
    """Kapı klasöründen ve istemden rolü bulan sahte ajan.
    Plan: varsayılan dağıtımı aynen döndürür. Kapıda grafik editörünü bir kez düzeltmeye yollar. QC bir P1 ve kural adayı yazar."""
    def ajan(slot, istem, mod, yol, *, yedek=False):
        f = Path(re.search(r"Read the file (.+?\.istem\.md)", istem).group(1))
        rol, asama = f.name.split(".")[0], f.parent.name
        metin = f.read_text(encoding="utf-8")
        kayit.append((asama, rol))
        meta = {"motor": slot.motor, "sure": 0.1, "token": {"input_tokens": 10}}
        if rol == "O" and asama == "plan":
            v = json.loads(re.search(r"Varsayılan dağıtım.*?```json\n(.+?)\n```", metin, re.S).group(1))
            return True, json.dumps({"hook": {"bas": 0, "son": 2, "neden": "soru"}, **v, "gerekce": "istek dengeli"}), meta
        if rol == "O" and asama == "kapi":
            grafik = sorted(set(re.findall(r"### (E\d+) · [^\n]*Grafik", metin)), key=lambda s: int(s[1:]))
            return True, json.dumps({"kararlar": [{"slot": grafik[0], "karar": "duzelt", "brif": "kural_uyum yaz"}]}), meta
        if rol == "O" and asama == "triyaj":
            ids = re.findall(r'"id": "(K\d-\d{3})"', metin)
            return True, json.dumps({"kabul": ids, "red": [], "kural_onay": ids}), meta
        if rol.startswith("E"):
            zorunlu = re.findall(r"^- \[(K\d{4}) P\d\]", metin.split("## Zorunlu kurallar")[1].split("##")[0], re.M)
            ar = re.search(r"- Aralık: ([\d.]+)–([\d.]+) sn", metin)
            grafik = re.search(r"- Katmanlar: [^\n]*Grafik", metin) is not None
            ilk_dilim = ar is None or float(ar.group(1)) <= 1.0 < float(ar.group(2))
            y = {"ekle": [], "rapor": "tamam"}
            # Kapıdan önce grafik editörleri uyumu unutur; kapı düzeltmesinde yazar.
            if not (grafik and asama == "duzen"):
                y["kural_uyum"] = [{"id": i, "nasil": "yüzden uzak"} for i in zorunlu]
            if grafik and asama in ("duzen", "kapi") and ilk_dilim:
                y["ekle"] = [{"id": "g1", "iz": "V2", "tur": "metin", "bas": 1.0, "sure": 1.5, "metin": "Merhaba"}]
            if asama == "duzelt":
                y = {"guncelle": [{"id": "g1", "bas": 1.2}], "kural_uyum": [{"id": i, "nasil": "x"} for i in zorunlu]}
            return True, json.dumps(y), meta
        kare = next((f.parent / "izle").glob("*.jpg"))
        return True, "```json\n" + json.dumps({"bulgular": [{"id": f"{rol}-001", "onem": "P1", "zaman": [1, 2], "katman": "V2",
                                                            "kategori": "okunurluk", "kanit": str(kare), "sorun": "altyazıyla çakışıyor",
                                                            "beklenen": "bant dışında", "kural_adayi": ADAY}], "brif": "b"}) + "\n```", meta
    return ajan


@pytest.mark.parametrize("seviye", ["low", "high", "max"])
def test_seviyeli_kapili_akis(proje, tmp_path, monkeypatch, seviye):
    k0 = _kural_deposu(tmp_path, monkeypatch)
    kayit: list = []
    monkeypatch.setattr(ekip, "ajan", _sahte_ekip(proje, kayit))
    monkeypatch.setattr(ekip_v3, "parcali_render", lambda p, a: p.work / "renders" / "taslak.mp4")
    o = ekip_v3.calistir(proje, _ayar(ekip_seviye=seviye), notu="hızlı tempo")
    ne, nk = SEVIYE[seviye]
    assert [r for a, r in kayit if r == "O"] == ["O"] * 3, "orkestratör her seviyede tam üç kez: plan, kapı, triyaj"
    assert sorted({r for a, r in kayit if a == "duzen"}) == sorted(f"E{i}" for i in range(1, ne + 1)), "seviyenin bütün editörleri"
    assert sorted({r for a, r in kayit if a == "qc"}) == sorted(f"K{i}" for i in range(1, nk + 1)), "seviyenin bütün kalite kontrolleri"
    assert o["dagitim"] == "orkestrator" and not o["plan_hata"]
    grafikciler = [g["slot"] for g in o["plan"]["gorevler"] if "grafik" in g["katmanlar"]]
    assert {r for a, r in kayit if a == "kapi" and r != "O"} == set(grafikciler), "uyumu eksik her editör kapıda düzeltmeye gider"
    assert all(k0 in o["zorunlu"][s] for s in grafikciler), "P0 kural grafik kartlarına zorunlu atanır"
    assert not o["kural_ihlal"], f"düzeltmeden sonra kural kapısı temiz: {o['kural_ihlal']}"
    assert o["kural_dogrulama"]["dogrulanan"] and not o["kural_dogrulama"]["dogrulanamayan"], "QC kuralı depoya işlendi ve doğrulandı"
    assert kural.bul_benzer(kural.yukle(), ADAY) is not None
    assert o["duzeltilen"] == [grafikciler[0]], "V2 1-2 sn bulgusu o dilimin grafik editörüne gider"
    d = json.loads((proje.work / "edit" / "ekip" / "durum.json").read_text(encoding="utf-8"))
    assert [x["id"] for x in d["kapilar"]] == [f"G{i}" for i in range(8)]
    assert all(x["durum"] == "gecti" for x in d["kapilar"]), d["kapilar"]
    assert d["bitti"] and d["kurallar"]["dogrulanan"] >= 1
    assert "ekip v3" in (proje.work / "edit" / "ai-edit.rapor.md").read_text(encoding="utf-8")


def test_gecersiz_plan_varsayilan_dagitima_duser(proje, tmp_path, monkeypatch):
    _kural_deposu(tmp_path, monkeypatch)
    kayit: list = []
    sahte = _sahte_ekip(proje, kayit)

    def ajan(slot, istem, mod, yol, *, yedek=False):
        if Path(re.search(r"Read the file (.+?\.istem\.md)", istem).group(1)).parent.name == "plan":
            iki_kurgu = [{"slot": "E1", "katmanlar": ["kurgu"]}, {"slot": "E2", "katmanlar": ["kurgu", "grafik", "sfx", "muzik", "stil"]}]
            return True, json.dumps({"gorevler": iki_kurgu, "kk_gorevler": [{"slot": "K1", "rol": "genel"}]}), {"sure": 1}
        return sahte(slot, istem, mod, yol, yedek=yedek)

    monkeypatch.setattr(ekip, "ajan", ajan)
    monkeypatch.setattr(ekip_v3, "parcali_render", lambda p, a: p.work / "renders" / "taslak.mp4")
    o = ekip_v3.calistir(proje, _ayar(ekip_seviye="low"))
    assert o["dagitim"] == "varsayilan" and any("kurgu bölünmez" in h for h in o["plan_hata"])
