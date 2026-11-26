"""Kurgu kalite uyarıları, ölü hava ve SFX parlaklık süzgeci (ADR 0040)."""

import numpy as np

from vedit import kurgu_kalite, olaysesi, slop
from vedit.schemas import Kurgu, SfxEntry


def kur(klipler):
    return Kurgu.model_validate({"izler": [{"id": "V2", "tur": "video"}, {"id": "V1", "tur": "video"}], "klipler": klipler})


def test_kisa_yazi_ve_kapanis_tabani():
    k = kur([
        {"id": "a", "iz": "V2", "tur": "metin", "bas": 0, "sure": 1.0, "metin": "Bu cümle ekranda okunamayacak kadar kısa kalıyor"},
        {"id": "b", "iz": "V2", "tur": "metin", "bas": 2, "sure": 2.0, "metin": "Yeterli süre"},
        {"id": "c", "iz": "V1", "tur": "metin", "bas": 4, "sure": 2.5, "metin": "Abone ol ve bildirimleri aç"},
    ])
    u = {x["kanit"].split(":")[0]: x for x in kurgu_kalite.uyarilar(k)}
    assert "a" in u and "b" not in u
    assert "c" in u and "kapanış" in u["c"]["oneri"]  # 5 kelime: 1,0 + 2,0 = 3,0 sn gerek


def test_ekran_yazisinda_emoji():
    k = kur([
        {"id": "a", "iz": "V2", "tur": "metin", "bas": 0, "sure": 3, "metin": "Hemen dene 🚀"},
        {"id": "b", "iz": "V2", "tur": "metin", "bas": 4, "sure": 3, "metin": "Adım ✓ → sonuç"},
        {"id": "c", "iz": "V2", "tur": "metin", "bas": 8, "sure": 3, "metin": "Yeni ✨ özellik"},
    ])
    emoji = {x["kanit"].split(":")[0] for x in kurgu_kalite.uyarilar(k) if x["kod"] == "YAZI_EMOJI"}
    assert emoji == {"a", "c"}, "✓ ve ok tipografidir, emoji değil"


def test_art_arda_ayni_gecis_ve_efekt():
    g = {"tur": "it", "sure": 0.3, "yon": "sol"}
    k = kur([{"id": f"v{i}", "iz": "V1", "tur": "gorsel", "kaynak": None, "bas": i * 2, "sure": 2, "gecis_giris": g,
              "hazir": [{"ad": "punch", "t": 0.5}]} for i in range(4)])
    kodlar = [x["kod"] for x in kurgu_kalite.uyarilar(k)]
    assert kodlar.count("GECIS_TEKRAR") == 1 and kodlar.count("EFEKT_TEKRAR") == 1
    gec = next(x for x in kurgu_kalite.uyarilar(k) if x["kod"] == "GECIS_TEKRAR")
    assert gec["klip"] == "v2" and "(v2)" in gec["kanit"], "ADR 0058: seri üçüncü klibi adlandırır, uyarı sahibine gider"
    k.klipler[1].gecis_giris.yon = "sag"
    assert "GECIS_TEKRAR" not in [x["kod"] for x in kurgu_kalite.uyarilar(k)]


def test_olu_hava():
    zarf = np.full(400, -20.0)
    zarf[100:140] = -70  # 4 sn tam sessizlik
    zarf[200:204] = -70  # 0,4 sn nefes: kusur değil
    b = [x for x in slop.ses_analizi(zarf, None, 40.0) if x["kod"] == "SES_OLU_HAVA"]
    assert len(b) == 1 and b[0]["bas"] == 10.0


def test_tekrarli_rolde_parlak_ses_secilmez():
    def e(i, p):
        return SfxEntry(id=f"tik{i}", file=f"x/{i}.wav", category="click", duration_s=0.05, license="CC0", source="t", parlak=p)
    havuz = [e(0, 0.9), e(1, 0.1), e(2, 0.8)]
    rol = olaysesi.ROLLER["tik"]
    secilen = {olaysesi._aday(havuz, rol, "medium", 0.05, str(i), None).id for i in range(20)}
    assert secilen == {"tik1"}


