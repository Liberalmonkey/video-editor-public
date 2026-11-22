"""Kurgu kalite uyarıları, ölü hava ve SFX parlaklık süzgeci (ADR 0040)."""
from pathlib import Path

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


def test_teslim_kapak_yalniz_ilk_karede(tmp_path):
    import subprocess

    from vedit import ff, teslim
    v, k = tmp_path / "v.mp4", tmp_path / "k.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=640x360:d=2:r=30", "-f", "lavfi",
                    "-i", "sine=f=440:d=2", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(v)], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=1280x720:d=1", "-frames:v", "1", str(k)], check=True)
    r = teslim.kodla(v, tmp_path / "o.mp4", kapak=k)

    def kare(n):
        ham = subprocess.run(["ffmpeg", "-v", "error", "-i", r["cikti"], "-vf", f"select=eq(n\,{n})", "-frames:v", "1",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        return np.frombuffer(ham, np.uint8).reshape(-1, 3).mean(axis=0)
    assert kare(0)[0] > 180 and kare(0)[1] < 80      # kırmızı kapak
    assert abs(kare(1)[0] - kare(1)[1]) < 10           # gri özgün kare
    o = ff.probe(Path(r["cikti"]))
    assert abs(o["duration"] - 2.0) < 0.1 and o.get("audio")
