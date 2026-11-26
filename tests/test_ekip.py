"""Ekip motoru v3 (ADR 0053): ayar ve göç, zaman bölüşü, bulgu şeması ve seviyeli, kapılı uçtan uca akış.

Ajanlar, hazirla, taslak ve izleme taklit edilir; gerçek motor çağrılmaz. Kural deposu geçici klasördedir.
"""
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from vedit import aiedit, ekip, ekip_v3, ff, hizli, kural, kurgu, paths, suru, yaratici
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
    monkeypatch.setattr(hizli, "qc_taslak", sahte_taslak)

    def sahte_izle(prj, video, kok):
        (kok / "izle").mkdir(parents=True, exist_ok=True)
        (kok / "izle" / "kare_0003.0.jpg").write_bytes(b"jpg")
        return {"_kok": kok, "taslak video": video}

    monkeypatch.setattr(ekip, "izle", sahte_izle)
    # Swarm (ADR 0059): gerçek motor taraması (11 sn, disk önbelleği) testte çalışmaz.
    monkeypatch.setattr(suru, "model_listesi", lambda **k: dict(MODELLER))
    return p


MODELLER = {"claude": ["m", "y", "claude-sonnet-5-5"], "antigravity": ["y", "gemini-4-neon-high"]}


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
    c, dus = ekip.bulgu_dogrula({"bulgular": [{"id": "X"}]}, "K2")
    assert c.bulgular == [] and dus, "bozuk bulgu tek başına düşer"
    assert ekip.bulgu_dogrula({"bulgular": "yok"}, "K2")[0] is None
    # Bir bozuk bulgu ötekileri düşürmez; ek alan atılır, kalıba uymayan isteğe bağlı alan boşalır, kimlik slota göre numaralanır.
    iyi = {"onem": "P1", "zaman": [1, 2], "katman": "V2", "kategori": "stil", "kanit": str(kare), "sorun": "s", "beklenen": "b"}
    c, dus = ekip.bulgu_dogrula({"bulgular": [{**iyi, "id": "K1-001", "klip": "c3", "hedef": "E11", "kural_adayi": "YAP:\n kısa ama  geçerli emir"},
                                              {**iyi, "id": "K2-001", "kategori": "kurgu"}, {**iyi, "id": "K2-001"}]}, "K2")
    assert [b.id for b in c.bulgular] == ["K2-001", "K2-003"] and len(dus) == 1
    assert c.bulgular[0].hedef is None and c.bulgular[0].kural_adayi == "YAP: kısa ama geçerli emir"


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
ADAY_SES = "YAP: altyazı kelimesini sesteki kelimeyle aynı karede göster."


def _kural_deposu(tmp_path, monkeypatch):
    monkeypatch.setattr(kural, "paths", SimpleNamespace(LIBRARY=tmp_path / "lib", ROOT=paths.ROOT, rel=paths.rel))
    d = kural.Depo()
    kural.ekle(d, KURAL_METNI, hedef_rol="E2", onem="P0", kategori="grafik")
    kural.kaydet(d)
    return d.kurallar[0].id


def _sahte_ekip(proje, kayit: list):
    """Kapı klasöründen ve istemden rolü bulan sahte ajan.
    Plan: varsayılan dağıtımı aynen döndürür. Kapıda grafik editörünü bir kez düzeltmeye yollar. QC bir P1 ve kural adayı yazar."""
    def ajan(slot, istem, mod, yol, *, yedek=False, **_):
        f = Path(re.search(r"Read the file (.+?\.istem\.md)", istem).group(1))
        rol, asama = f.name.split(".")[0], f.parent.name
        metin = f.read_text(encoding="utf-8")
        kayit.append((asama, rol))
        meta = {"motor": slot.motor, "sure": 0.1, "token": {"input_tokens": 10}}
        if rol == "O" and asama == "plan":
            # Swarm (ADR 0059): bütçenin izin verdiği en büyük seviye tablosunu seçer (varsayılan boydan büyük olabilir).
            tavan = int(re.search(r"En çok (\d+) ajan", metin).group(1))
            sev = max((s for s, (e, q) in SEVIYE.items() if e + q <= tavan), key=lambda s: sum(SEVIYE[s]))
            v = json.loads(ekip_v3.varsayilan_dagitim(sev, kurgu.oku(proje.work)).model_dump_json(include={"gorevler", "kk_gorevler"}))
            return True, json.dumps({**v, "gerekce": "istek dengeli"}), meta
        if rol == "O" and asama == "brif":  # ADR 0064: hızlı modda brif tek kısa çağrıdır
            return True, json.dumps({"tez": "Altı kelimede tek fikir.", "enerji": [{"aralik": [0, 3], "seviye": 5}],
                                     "imza_anlari": [{"t": 4.5, "soz": "dört", "ne": "tek vuruş"}]}), meta
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
        # İkinci bulgu ses-stil slotuna gider (medium'da E4): kural deposuna rol sınıfı (E3) olarak yazılmalı.
        return True, "```json\n" + json.dumps({"bulgular": [{"id": f"{rol}-001", "onem": "P1", "zaman": [1, 2], "katman": "V2",
                                                            "kategori": "okunurluk", "kanit": str(kare), "sorun": "altyazıyla çakışıyor",
                                                            "beklenen": "bant dışında", "kural_adayi": ADAY},
                                                           {"id": f"{rol}-002", "onem": "P2", "zaman": [3, 4], "katman": "altyazi",
                                                            "kategori": "ses", "kanit": str(kare), "sorun": "altyazı geç düşüyor",
                                                            "beklenen": "kelimeyle aynı kare", "kural_adayi": ADAY_SES}], "brif": "b"}) + "\n```", meta
    return ajan


@pytest.mark.parametrize("seviye", ["low", "medium", "high", "max"])
def test_seviyeli_kapili_akis(proje, tmp_path, monkeypatch, seviye):
    k0 = _kural_deposu(tmp_path, monkeypatch)
    kayit: list = []
    monkeypatch.setattr(ekip, "ajan", _sahte_ekip(proje, kayit))
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
    ses = kural.bul_benzer(kural.yukle(), ADAY_SES)
    assert ses is not None and ses.hedef_rol == "E3", "ses-stil slotunun adayı depoya rol sınıfıyla (E3) yazılır, slotla değil"
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

    def ajan(slot, istem, mod, yol, *, yedek=False, **_):
        if Path(re.search(r"Read the file (.+?\.istem\.md)", istem).group(1)).parent.name == "plan":
            iki_kurgu = [{"slot": "E1", "katmanlar": ["kurgu"]}, {"slot": "E2", "katmanlar": ["kurgu", "grafik", "sfx", "muzik", "stil"]}]
            return True, json.dumps({"gorevler": iki_kurgu, "kk_gorevler": [{"slot": "K1", "rol": "genel"}]}), {"sure": 1}
        return sahte(slot, istem, mod, yol, yedek=yedek)

    monkeypatch.setattr(ekip, "ajan", ajan)
    o = ekip_v3.calistir(proje, _ayar(ekip_seviye="low"))
    assert o["dagitim"] == "varsayilan" and any("kurgu bölünmez" in h for h in o["plan_hata"])


def test_slot_kural_rolu_ve_qc_isle(tmp_path, monkeypatch):
    """G5 hatası (reel-video, medium): QC hedefi slot (E4) idi, depo rol sınıfı (E1-E3) bekler; ValidationError triyajı düşürürdü."""
    from vedit.ekip_sema import Gorev
    a = ekip_v3.Atama([Gorev(slot="E1", katmanlar=["kurgu"]), Gorev(slot="E2", katmanlar=["grafik"]),
                       Gorev(slot="E3", katmanlar=["grafik"]), Gorev(slot="E4", katmanlar=["sfx", "muzik", "stil"]),
                       Gorev(slot="E5", katmanlar=["kurgu", "grafik"])])
    assert [a.kural_rolu(s) for s in ("E1", "E2", "E3", "E4", "E5", None, "E9")] == ["E1", "E2", "E2", "E3", "hepsi", "hepsi", "hepsi"]
    assert a.kural_rolu("E5", "grafik") == "E2" and a.kural_rolu("E5", "stil") == "hepsi", "karışık slotta bulgu katmanı seçer, slotta olmayan sınıf seçmez"
    _kural_deposu(tmp_path, monkeypatch)
    s = kural.qc_isle([{"id": "K1-001", "hedef": "E4", "onem": "P1", "kategori": "ses", "sorun": "x", "kural_adayi": ADAY_SES},
                       {"id": "K1-002", "hedef": None, "onem": "P2", "kategori": "stil", "sorun": "y", "kural_adayi": ADAY}], proje="i/p")
    d = kural.yukle()
    assert len(s["yeni"]) == 2 and all(kural._ara(d, i).hedef_rol == "hepsi" for i in s["yeni"]), "geçersiz hedef çökertmez, hepsi olur"


def test_max_dayaniklilik(tmp_path):
    """Max seviye: uzun ajan metni kırpılır, paralel grafik editörlerinin kompozisyon adı çakışmaz,
    pano paralel yazımda mesaj kaybetmez, ajan eşzamanlılığı boş belleğe sığar."""
    from concurrent.futures import ThreadPoolExecutor

    from vedit.ekip_sema import Gorev, Mesaj, Yama
    y = Yama.model_validate({"pano": [{"tip": "done", "aralik": [0, 1], "metin": "x" * 318}], "rapor": "r" * 2000})
    assert len(y.pano[0].metin) == 240 and len(y.rapor) == 1500, "uzun not yamayı düşürmez (reel-video E3)"

    at = ekip_v3.Atama([Gorev(slot="E1", katmanlar=["kurgu"]),
                        *[Gorev(slot=f"E{i}", katmanlar=["grafik"], aralik=[i - 2.0, i - 1.0]) for i in range(2, 7)]])
    html = '<div data-composition-id="x"></div>'
    y = Yama(ekle=[{"id": "g1", "iz": "V2", "tur": "motion", "hf": {"ad": "baslik"}}], hf={"baslik": html, "kart-e3": html})
    y = ekip_v3.hf_ad_ayir("E3", y, at)
    assert set(y.hf) == {"baslik-e3", "kart-e3"} and y.ekle[0]["hf"]["ad"] == "baslik-e3"
    tek = ekip_v3.Atama([Gorev(slot="E1", katmanlar=["kurgu"]), Gorev(slot="E2", katmanlar=["grafik"])])
    assert set(ekip_v3.hf_ad_ayir("E2", Yama(hf={"baslik": html}), tek).hf) == {"baslik"}, "tek grafik editöründe ad değişmez"

    def yaz(i):
        ekip_v3.pano_ekle(tmp_path, f"E{i % 10 + 1}", [Mesaj(tip="claim", aralik=[0, 1], metin=f"m{i}")])
        return ekip_v3.pano_oku(tmp_path, "E0")
    with ThreadPoolExecutor(10) as h:
        list(h.map(yaz, range(60)))
    assert len(json.loads((tmp_path / "pano.json").read_text(encoding="utf-8"))) == 60, "paralel pano yazımı mesaj kaybetmez"

    ay = EkipAyar(ekip_seviye="max")
    assert ekip_v3.ajan_eszamanlilik(ay, bos=20.0) == 10
    assert ekip_v3.ajan_eszamanlilik(ay, bos=5.0) == 3 and ekip_v3.ajan_eszamanlilik(ay, bos=1.0) == 2
    assert ekip_v3.ajan_eszamanlilik(EkipAyar(ekip_seviye="max", eszamanlilik=8), bos=1.0) == 8, "açık ayar kazanır"


def test_triyaj_cozumlenemezse_aday_islenmez(proje, tmp_path, monkeypatch):
    _kural_deposu(tmp_path, monkeypatch)
    kayit: list = []
    asil = _sahte_ekip(proje, kayit)

    def ajan(slot, istem, mod, yol, *, yedek=False, **_):
        ok, yanit, meta = asil(slot, istem, mod, yol, yedek=yedek)
        return (ok, "anlaşılmaz yanıt", meta) if kayit[-1] == ("triyaj", "O") else (ok, yanit, meta)
    monkeypatch.setattr(ekip, "ajan", ajan)
    o = ekip_v3.calistir(proje, _ayar(ekip_seviye="max"), notu="hızlı tempo")
    assert kural.bul_benzer(kural.yukle(), ADAY) is None, "orkestratör onaylamadan aday depoya girmez"
    assert "triyaj çözümlenemedi" in o["kapilar"]["G5"]


def test_iz_cakisma_coz_kirpar_ya_da_tasir():
    """Aynı izde üst üste binen grafik: küçük örtüşmede önceki kısalır, büyükte başka ize taşınır; denetim temiz kalır."""
    from vedit.schemas import Klip, Kurgu, KurguIz
    k = Kurgu(izler=[KurguIz(id="V3", tur="video"), KurguIz(id="V1", tur="video"), KurguIz(id="A2", tur="ses")],
              klipler=[Klip(id="a", iz="V3", tur="metin", bas=32.29, sure=2.65), Klip(id="b", iz="V3", tur="metin", bas=34.83, sure=2.3),
                       Klip(id="c", iz="V3", tur="metin", bas=40.0, sure=3.0), Klip(id="d", iz="V3", tur="metin", bas=41.0, sure=2.0)])
    degisen, bulgu = ekip_v3.iz_cakisma_coz(k)
    by = {c.id: c for c in k.klipler}
    assert by["a"].sure == pytest.approx(2.54) and by["a"].iz == "V3"
    assert by["d"].iz not in ("V3", "V1") and by["c"].sure == 3.0
    assert [i.id for i in k.izler][0] == by["d"].iz  # yeni görüntü izi en üstte
    assert {"a", "d"} <= set(degisen) and len(bulgu) == 1
    for iz in k.izler:
        sira = sorted((c for c in k.klipler if c.iz == iz.id), key=lambda c: c.bas)
        assert all(b.bas >= a.bas + a.sure - 1e-3 for a, b in zip(sira, sira[1:]))


def _sayac(proje, monkeypatch):
    """QC render çağrılarını sayar (ADR 0054: render yalnız gerekince; ADR 0058: QC videosu `qc_taslak`)."""
    sayi = {"taslak": 0}
    asil = hizli.qc_taslak

    def taslak(prj, **k):
        sayi["taslak"] += 1
        return asil(prj, **k)
    monkeypatch.setattr(hizli, "qc_taslak", taslak)
    return sayi


def test_hizli_on_ayar_orkestratorsuz(proje, tmp_path, monkeypatch):
    """--hizli: 2E + zaman dilimi başına QC (ADR 0058), orkestratör hiç çağrılmaz, kural adayı onaysız depoya girmez, düzeltmeden sonra render yok."""
    _kural_deposu(tmp_path, monkeypatch)
    kayit: list = []
    monkeypatch.setattr(ekip, "ajan", _sahte_ekip(proje, kayit))
    sayi = _sayac(proje, monkeypatch)
    o = ekip_v3.calistir(proje, _ayar(ekip_seviye="max", hizli=True), notu="hızlı tempo")
    assert o["seviye"] == "low" and o["hizli"] and o["dagitim"] == "hizli"
    # ADR 0064: orkestratör plan, kapı ve triyaj yapmaz; yalnız yaratıcı brifi bir kez yazar (aynı istekte yeniden kullanılır).
    assert [a for a, r in kayit if r == "O"] == ["brif"], kayit
    assert "yaratıcı brif yeni" in o["kapilar"]["G0"] and yaratici.gecerli(proje.work, "hızlı tempo") is not None
    assert sorted({r for a, r in kayit if a == "duzen"}) == ["E1", "E2"] and sorted({r for a, r in kayit if a == "qc"}) == ["K1", "K2"]
    assert kural.bul_benzer(kural.yukle(), ADAY) is None, "onaysız aday depoya girmez"
    assert o["duzeltilen"], "P1 bulgusu yine düzeltilir"
    assert sayi == {"taslak": 1} and o["taslak_eski"], "G6'dan sonra render alınmaz"
    assert "atlandı (hızlı)" in o["kapilar"]["G0"] and "deterministik" in o["kapilar"]["G2"]


def test_temiz_kural_kapisinda_orkestrator_beklenmez(proje, tmp_path, monkeypatch):
    """Editörler kurala uyunca G2'de O çağrılmaz: plan + triyaj = 2 çağrı. --tekrar-denetle düzeltilen videoyu render eder."""
    _kural_deposu(tmp_path, monkeypatch)
    kayit: list = []
    asil = _sahte_ekip(proje, kayit)

    def ajan(slot, istem, mod, yol, *, yedek=False, **_):
        ok, yanit, meta = asil(slot, istem, mod, yol, yedek=yedek)
        f = Path(re.search(r"Read the file (.+?\.istem\.md)", istem).group(1))
        asama, rol = f.parent.name, f.name.split(".")[0]  # E1 plana paralel çalışır (ADR 0059): kayit[-1] başka ajan olabilir
        if rol.startswith("E") and asama == "duzen":  # grafik editörü de ilk seferde uyumu yazar
            y = json.loads(yanit)
            metin = f.read_text(encoding="utf-8")
            z = re.findall(r"^- \[(K\d{4}) P\d\]", metin.split("## Zorunlu kurallar")[1].split("##")[0], re.M)
            y["kural_uyum"] = [{"id": i, "nasil": "x"} for i in z]
            yanit = json.dumps(y)
        return ok, yanit, meta
    monkeypatch.setattr(ekip, "ajan", ajan)
    sayi = _sayac(proje, monkeypatch)
    o = ekip_v3.calistir(proje, _ayar(ekip_seviye="medium"), tekrar_denetle=True)
    assert [a for a, r in kayit if r == "O"] == ["plan", "triyaj"], kayit
    assert "orkestratör çağrılmadı" in o["kapilar"]["G2"]
    assert sayi["taslak"] == 2 and not o["taslak_eski"], "ikinci QC için düzeltilmiş kurgu yeniden çizilir (QC videosu)"


def test_yalin_claude_komutu_ve_stdin(tmp_path, monkeypatch):
    """ADR 0054: ekip Claude'u araçsız, MCP'siz, ayar kaynaksız çalıştırır; istem stdin'den, rol sistem isteminden."""
    from vedit import motorlar
    monkeypatch.setattr(motorlar, "bas", lambda m: ["claude.exe"])
    k = motorlar.yalin_komut("m", "medium", sistem="ROL", araclar="", dizinler=(tmp_path,))
    for bayrak in ("--strict-mcp-config", "--disable-slash-commands", "--no-session-persistence", "--append-system-prompt"):
        assert bayrak in k
    assert k[k.index("--tools") + 1] == "" and k[k.index("--setting-sources") + 1] == "" and k[k.index("--effort") + 1] == "medium"
    assert "--add-dir" in k and k[1] == "-p" and "--bare" not in k

    # Sahte "claude": stdin'i okur, stream-json sonuç satırı basar.
    betik = tmp_path / "sahte.py"
    betik.write_text("import sys,json\nt=sys.stdin.buffer.read().decode('utf-8')\nprint(json.dumps({'type':'result','result':'ALDIM:'+str(len(t)),"
                     "'usage':{'input_tokens':3}}))\n", encoding="utf-8")
    import sys
    monkeypatch.setattr(motorlar, "yalin_komut", lambda *a, **kw: [sys.executable, str(betik)])
    monkeypatch.setattr(motorlar, "YALIN_KOK", tmp_path / "kok")
    sl = Slot(motor="claude", model="m")
    metin = "ğüşİ " * 20000  # Windows komut satırı sınırını (32k) aşan istem
    ok, yanit, meta = ekip.ajan(sl, "Read the file x", "plan", tmp_path / "O", metin=metin, sistem="ROL")
    assert ok and yanit == f"ALDIM:{len(metin)}" and meta["yalin"]


def test_pafta_kareleri_toplar(tmp_path):
    from PIL import Image
    kareler = []
    for i in range(14):
        f = tmp_path / f"kare_{i * 1.5:06.1f}.jpg"
        Image.new("RGB", (540, 960), (i * 15, 40, 90)).save(f)
        kareler.append((i * 1.5, f))
    (tmp_path / "pafta-9.jpg").write_bytes(b"eski")
    paftalar = ekip.pafta_yap(kareler, tmp_path)
    assert [f.name for f in paftalar] == ["pafta-1.jpg", "pafta-2.jpg"] and not (tmp_path / "pafta-9.jpg").exists()
    with Image.open(paftalar[0]) as im:
        assert im.size == (4 * 270, 3 * 480)
    with Image.open(paftalar[1]) as im:
        assert im.size == (4 * 270, 480), "2 kare tek satır"


def test_suru_plan_dogrulama_butce_e1_ve_model():
    """ADR 0059: swarm planı tavan içinde, E1 yalnız kurgu, slotlar ardışık, model listede."""
    from vedit.ekip_sema import Plan
    kk = [{"slot": "K1", "rol": "genel"}]
    iyi = Plan.model_validate({"gorevler": [{"slot": "E1", "katmanlar": ["kurgu"]},
                                            {"slot": "E2", "katmanlar": ["grafik", "sfx", "muzik", "stil"], "motor": "antigravity",
                                             "model": "gemini-4-neon-high"}], "kk_gorevler": kk})
    assert suru.plan_dogrula(iyi, 3, 10, MODELLER) == []
    assert any("tavan 2" in h for h in suru.plan_dogrula(iyi, 2, 10, MODELLER))
    kotu_e1 = iyi.model_copy(deep=True)
    kotu_e1.gorevler[0].katmanlar = ["kurgu", "stil"]
    kotu_e1.gorevler[1].katmanlar = ["grafik", "sfx", "muzik"]
    assert any("E1 yalnız kurgu" in h for h in suru.plan_dogrula(kotu_e1, 6, 10, MODELLER))
    kotu_model = iyi.model_copy(deep=True)
    kotu_model.gorevler[1].model = "yok-model"
    assert any("listede olmayan model" in h for h in suru.plan_dogrula(kotu_model, 6, 10, MODELLER))
    atlamali = iyi.model_copy(deep=True)
    atlamali.gorevler[1].slot = "E3"
    assert any("ardışık" in h for h in suru.plan_dogrula(atlamali, 6, 10, MODELLER))


def test_suru_ezme_ve_boy():
    from vedit.ekip_sema import Plan
    a = _ayar(ezme={"E3": Slot(motor="claude", model="m")})
    plan = Plan.model_validate({"gorevler": [{"slot": "E1", "katmanlar": ["kurgu"]},
                                             {"slot": "E2", "katmanlar": ["grafik"], "model": "gemini-4-neon-high"},
                                             {"slot": "E3", "katmanlar": ["sfx", "muzik", "stil"], "motor": "antigravity"}],
                                "kk_gorevler": [{"slot": "K1", "rol": "genel", "motor": "claude", "model": "claude-sonnet-5-5"}]})
    ez = suru.ezme(plan, a, MODELLER)
    assert ez["E2"].motor == "antigravity" and ez["E2"].model == "gemini-4-neon-high", "motor modelden bulunur"
    assert "E3" not in ez, "kullanıcının açık ezmesi kazanır"
    assert ez["K1"].model == "claude-sonnet-5-5" and ez["K1"].yedek_motor == "antigravity", "yedek grup ayarından"
    assert "E1" not in ez
    plan.gorevler[2].motor, plan.gorevler[2].model = "claude", "claude-haiku-5-5"
    assert "E3" not in suru.ezme(plan, _ayar(), {**MODELLER, "claude": [*MODELLER["claude"], "claude-haiku-5-5"]}),         "editörde haiku grup modeline döner (g4: şemaya uymadı)"
    assert suru.varsayilan_boy(30, 15) == "low" and suru.varsayilan_boy(53, 15) == "medium"
    assert suru.varsayilan_boy(600, 15) == "xhigh" and suru.varsayilan_boy(600, 6) == "medium", "tavan boyu sınırlar"
    assert suru.orkestrator_ayristir("claude:claude-opus-5-5") == ("claude", "claude-opus-5-5")
    assert suru.orkestrator_ayristir("codex") == ("codex", None)
    # agy incelemesi: E1 kartı ezilmez (plana paralel çalışıyor), geçersiz seviye düşer, yedek birincille aynı olmaz.
    p2 = Plan.model_validate({"gorevler": [{"slot": "E1", "katmanlar": ["kurgu"], "motor": "antigravity"},
                                           {"slot": "E2", "katmanlar": ["grafik", "sfx", "muzik", "stil"], "motor": "antigravity",
                                            "model": "gemini-4-neon-high", "seviye": "olmayan"}],
                              "kk_gorevler": [{"slot": "K1", "rol": "genel"}]})
    ez2 = suru.ezme(p2, _ayar(), MODELLER)
    assert "E1" not in ez2 and ez2["E2"].seviye is None
    assert ez2["E2"].yedek_motor == "claude" and ez2["E2"].yedek_model == "m", "yedek grubun birincili olur"
    assert any("seviye" in h for h in suru.plan_dogrula(p2, 6, 10, MODELLER))


def test_suru_e1_plana_paralel_ve_model_secimi(proje, tmp_path, monkeypatch):
    """ADR 0059: E1 orkestratörün planı bitmeden başlar; plan kartının motor/model seçimi slota uygulanır, durumda görünür."""
    import threading
    _kural_deposu(tmp_path, monkeypatch)
    kayit: list = []
    sahte = _sahte_ekip(proje, kayit)
    e1_basladi = threading.Event()
    motorlar_: dict[str, str] = {}

    def ajan(slot, istem, mod, yol, *, yedek=False, **kw):
        f = Path(re.search(r"Read the file (.+?\.istem\.md)", istem).group(1))
        rol, asama = f.name.split(".")[0], f.parent.name
        motorlar_[f"{asama}/{rol}"] = slot.motor
        if rol == "E1" and asama == "duzen":
            e1_basladi.set()
        if rol == "O" and asama == "plan":
            assert e1_basladi.wait(5), "E1 plan çağrısıyla aynı anda başlamalı"
            v = json.loads(ekip_v3.varsayilan_dagitim("low", kurgu.oku(proje.work)).model_dump_json(include={"gorevler", "kk_gorevler"}))
            v["gorevler"][1].update(motor="antigravity", model="gemini-4-neon-high")
            v["kk_gorevler"].append({"slot": "K2", "rol": "gorsel"})
            kayit.append((asama, rol))
            return True, json.dumps({**v, "gerekce": "grafik agy"}), {"sure": 0.1}
        return sahte(slot, istem, mod, yol, yedek=yedek)

    monkeypatch.setattr(ekip, "ajan", ajan)
    o = ekip_v3.calistir(proje, _ayar(ekip_seviye="medium"))
    assert o["dagitim"] == "orkestrator", o["plan_hata"]
    assert motorlar_["duzen/E2"] == "antigravity" and motorlar_["duzen/E1"] == "claude"
    assert sorted({r for a, r in kayit if a == "qc"}) == ["K1", "K2"], "orkestratör QC sayısını seçer"
    d = json.loads((proje.work / "edit" / "ekip" / "durum.json").read_text(encoding="utf-8"))
    assert sorted(d["slotlar"]) == ["E1", "E2", "K1", "K2", "O"], "plan dışı seviye kartları silinir"
    assert d["slotlar"]["E2"]["model"] == "gemini-4-neon-high" and d["en_cok"] == 6


@pytest.mark.parametrize("argv, tavan, o_motor", [
    (["--ekip", "--seviye", "medium"], 6, "claude"),
    (["--suru", "--en-cok", "4", "--orkestrator", "codex:gpt-x"], 4, "codex"),
    (["--suru", "--seviye", "max", "--en-cok", "5"], 5, "claude"),
])
def test_cli_suru_bayraklari_ve_eski_cagri(proje, monkeypatch, argv, tavan, o_motor):
    """ADR 0059: --ekip = --suru; --seviye tavanı verir (--en-cok kazanır); --orkestrator MOTOR[:MODEL] grubu değiştirir."""
    from vedit import cli
    alinan = {}

    def sahte(p, ayar, **kw):
        alinan["ayar"] = ayar
        return {"sure_sn": 1, "seviye": ayar.ekip_seviye, "en_cok": ayar.tavan(), "editor": 2, "kk": 1, "bulgular": [],
                "son_denetim": {"hata": []}}

    monkeypatch.setattr(ekip_v3, "calistir", sahte)
    monkeypatch.setattr(ekip, "GLOBAL", proje.work / "yok.json")
    cli.main(["ai-edit", f"{proje.studyo}/{proje.ad}", *argv])
    a = alinan["ayar"]
    assert a.tavan() == tavan and a.gruplar["orkestrator"].motor == o_motor
    if o_motor == "codex":
        assert a.gruplar["orkestrator"].model == "gpt-x"


def test_ayar_katmani_seviye_verirse_alttaki_tavan_tasinmaz(proje, monkeypatch, tmp_path):
    """agy incelemesi (ADR 0059): ön ayarda en_cok 9, projede eski biçim {ekip_seviye: low} → tavan 3, 9 değil."""
    g = tmp_path / "ekip.json"
    g.write_text(json.dumps({"varsayilan": "x", "onayarlar": {"x": {"ad": "x", "ekip_seviye": "high", "en_cok": 9}}}), encoding="utf-8")
    monkeypatch.setattr(ekip, "GLOBAL", g)
    assert ekip.ayar_yukle(proje).tavan() == 9
    (proje.work / "edit").mkdir(parents=True, exist_ok=True)
    (proje.work / "edit" / "ekip.json").write_text(json.dumps({"ekip_seviye": "low"}), encoding="utf-8")
    assert ekip.ayar_yukle(proje).tavan() == 3
    with pytest.raises(Exception):
        EkipAyar(en_cok=2)
