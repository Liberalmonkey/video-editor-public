"""Native motion bileşenlerinin HyperFrames karşılığını Remotion aslıyla kare kare karşılaştırır (ADR 0051).

Kullanım:
    .venv/Scripts/python -X utf8 scripts/hf_native_karsilastir.py ikon/begeni ikon/tik
    .venv/Scripts/python -X utf8 scripts/hf_native_karsilastir.py --aile ikon
    .venv/Scripts/python -X utf8 scripts/hf_native_karsilastir.py --hepsi
    .venv/Scripts/python -X utf8 scripts/hf_native_karsilastir.py --eksik     # ölçülmemiş, geçmemiş ya da değişmiş olanlar

Sentetik bir kurgu kurar: seçilen bileşenler art arda, varsayılan süre ve parametreyle, `instagram/1` projesinin
teması ve public klasörüyle. İki motorda yarım ölçekte render eder; klip başına fark ve
`work/hf-native/<ad>.png` kontak sayfası (öğeye kırpılmış; sol Remotion, sağ HyperFrames) yazar. Ölçü: öğenin sınır
kutusunda piksel farkı (0-255), ortalama ve %99 dilimi.
WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Taşınan her bileşen kare açılıp bakılmadan bitti sayılmaz.
"""
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from vedit import hf_kurgu, hizli  # noqa: E402

CIKTI = KOK / "work" / "hf-native"
SEMA = KOK / "library" / "motion" / "native" / "sema.json"
HF = KOK / "library" / "motion" / "hf"
BOSLUK = 0.3


def tasinmis() -> set[str]:
    return {d.name.replace("-", "/", 1) for d in HF.iterdir() if (d / "sahne.html").exists()}


def props_kur(p, adlar: list[str], sema: dict) -> tuple[Path, list[tuple[str, float, float]]]:
    kaynak = json.loads((p.work / "edit" / "kurgu.render.json").read_text(encoding="utf-8"))
    sablon = next(k for k in kaynak["klipler"] if k["tur"] == "motion" and k.get("bilesen"))
    klipler, araliklar, t = [], [], 0.0
    for i, ad in enumerate(adlar):
        sure = float(sema[ad]["meta"]["sure"]["varsayilan"])
        k = copy.deepcopy(sablon)
        k.update(id=f"nt{i:02d}", iz="V1", bas=round(t, 3), sure=sure, kaynak=None, hazir=[], gecis_giris=None, gecis_cikis=None,
                 bilesen={"ad": ad, "param": {}, "yer": "oto"})
        klipler.append(k)
        araliklar.append((ad, t, sure))
        t = round(t + sure + BOSLUK, 3)
    yeni = {**kaynak, "klipler": klipler, "izler": [{"id": "V1", "tur": "video", "sessiz": True, "gizli": False, "gain_db": 0.0}],
            "altyazi": {**kaynak["altyazi"], "acik": False}, "words": [], "bitis": t, "bolgeler": None}
    yol = p.work / "edit" / "kurgu.render.nativetest.json"
    yol.write_text(json.dumps(yeni, ensure_ascii=False), encoding="utf-8")
    return yol, araliklar


W, H = 540, 960
FPS = 30


def pencere(v: Path, a0: int, n: int):
    """[a0, a0 + n) kare penceresi (n, H, W, 3) uint8, kare numarasıyla. Tüm videoyu belleğe almaz.

    WHY: saniyeyle arama (-ss) iki videonun farklı zaman tabanında (HyperFrames 1/15360, Remotion 1/90000) farklı kareye
    düşüyordu; zil ve konumda hayali bir kare kayması ölçüldü. Kare numarasıyla seçim kesindir.
    """
    import numpy as np
    ham = subprocess.run(["ffmpeg", "-v", "error", "-i", str(v), "-vf", f"select=between(n\\,{max(0, a0)}\\,{max(0, a0) + n - 1}),scale={W}:{H}",
                          "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(ham, np.uint8).reshape(-1, H, W, 3)


def olc(rm: Path, hfv: Path, ad: str, bas: float, sure: float):
    """Klip penceresinde öğenin sınır kutusu içinde fark, iki motorun kutu örtüşmesi ve kırpılmış kontak.

    WHY: tam karede koyu zemin baskın; küçük öğenin hatası SSIM'de görünmüyordu (kart/cip 0,999). Kutu örtüşmesi
    farklı boyda çizilen öğeyi yakalar (altbant-blok paneli tam boya uzuyordu, ortalama fark bunu seyreltti).
    """
    import numpy as np
    from PIL import Image
    a0 = int(round(bas * FPS)) - 3  # 3 kare önce: zemin karesi
    n = int(round(sure * FPS)) + 3
    r, h = pencere(rm, a0, n), pencere(hfv, a0, n)
    n = min(len(r), len(h))
    if n < 4:
        return 0.0, 0.0, 0.0, None
    zemin = r[0].astype(np.int16)
    fark_say = lambda v, i: np.abs(v[i].astype(np.int16) - zemin).max(axis=2) > 10
    mr = np.zeros((H, W), bool); mh = np.zeros((H, W), bool)
    for i in range(3, n):
        mr |= fark_say(r, i); mh |= fark_say(h, i)
    maske = mr | mh
    ys, xs = np.nonzero(maske)
    if not len(ys):
        return 0.0, 0.0, 1.0, None

    def kutu(m):
        y, x = np.nonzero(m)
        return (x.min(), y.min(), x.max() + 1, y.max() + 1) if len(y) else (0, 0, 0, 0)
    ka, kb = kutu(mr), kutu(mh)
    # Kenar kayması / uzun kenar: ince uzun öğede (fosforlu) parıltının birkaç pikseli kesişim oranını 0,83'e düşürüyordu.
    uzun = max(ka[2] - ka[0], ka[3] - ka[1], kb[2] - kb[0], kb[3] - kb[1], 1)
    iou = max(abs(x - y) for x, y in zip(ka, kb)) / uzun
    pad = 12
    y0, y1 = max(0, ys.min() - pad), min(H, ys.max() + pad)
    x0, x1 = max(0, xs.min() - pad), min(W, xs.max() + pad)
    toplam, ornek = 0.0, []
    for i in range(3, n):
        f = np.abs(r[i, y0:y1, x0:x1].astype(np.int16) - h[i, y0:y1, x0:x1].astype(np.int16)).max(axis=2)
        toplam += float(f.mean())
        ornek.append(f[::2, ::2].ravel())  # %99 dilimi için seyreltilmiş örnek
    ort = toplam / (n - 3)
    p99 = float(np.percentile(np.concatenate(ornek), 99))
    m = n - 3
    secim = sorted({3 + min(m - 1, int(k * m)) for k in (0.12, 0.25, 0.5, 0.92)})
    yuk = min(4, max(1, int(220 / max(1, y1 - y0))))
    img = Image.fromarray(np.concatenate([np.concatenate([r[i, y0:y1, x0:x1], h[i, y0:y1, x0:x1]], axis=1) for i in secim], axis=0))
    if yuk > 1:
        img = img.resize((img.width * yuk, img.height * yuk), Image.NEAREST)
    yol = CIKTI / f"{ad.replace('/', '-')}.png"
    img.save(yol)
    return ort, p99, iou, yol


SONUC = CIKTI / "sonuc.json"


def ozet(ad: str) -> str:
    import hashlib
    return hashlib.sha1((HF / ad.replace("/", "-", 1) / "sahne.html").read_bytes()).hexdigest()[:12]


def grup_olc(p, adlar: list[str], sema: dict) -> dict[str, dict]:
    props, araliklar = props_kur(p, adlar, sema)
    rm, hfv = CIKTI / "remotion.mp4", CIKTI / "hf.mp4"
    try:
        # Bellek: iki işçi (otomatik 4 işçi ve Remotion varsayılanı, 6+ bileşende sistemi sıkıştırdı).
        hf_kurgu.render(p, props, hfv, kalite="draft", olcek=0.5, isci=2)
        hizli._remotion(props, p.work / "public", rm, "--scale=0.5", "--concurrency=2")
    finally:
        props.unlink(missing_ok=True)
    cikti = {}
    for ad, bas, sure in araliklar:
        ort, p99, iou, yol = olc(rm, hfv, ad, bas, sure)
        # Eşik (ölçüldü 2026-11-22, ikon/begeni ve kart/cip gözle birebir): parıltı, yumuşatma ve kodlama gürültüsü ort 6,
        # %99 33-61; metnin alt piksel kayması (tipografi) 100-140. Yanlış yer ya da renk %99 200+; yanlış boy kutu kayması > 0,05.
        iyi = yol is not None and ort < 10 and p99 < 150 and iou < 0.05
        cikti[ad] = {"ort": round(ort, 2), "p99": round(p99, 1), "kayma": round(iou, 3), "sonuc": "TAMAM" if iyi else "FARK",
                     "kontak": str(yol.relative_to(KOK)) if yol else None, "ozet": ozet(ad)}
        print(f"{ad:32} {ort:9.2f} {p99:9.1f} {iou:5.2f}  {cikti[ad]['sonuc']:5} {cikti[ad]['kontak'] or 'öğe görünmüyor'}", flush=True)
    return cikti


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("adlar", nargs="*")
    ap.add_argument("--aile")
    ap.add_argument("--hepsi", action="store_true")
    ap.add_argument("--eksik", action="store_true", help="yalnız ölçülmemiş, geçmemiş ya da sahnesi değişmiş bileşenler")
    ap.add_argument("--proje", default="instagram/1")
    ap.add_argument("--grup", type=int, default=6, help="bir render'daki en çok bileşen (bellek)")
    ap.add_argument("--en-cok", type=int, default=0, help="bu çağrıda ölçülecek en çok bileşen (0: hepsi)")
    ap.add_argument("--onayla", nargs="+", metavar="AD", help="kontak gözle incelendi, fark kabul edilebilir (gerekçe zorunlu)")
    ap.add_argument("--gerekce", default="")
    a = ap.parse_args()
    sema = json.loads(SEMA.read_text(encoding="utf-8"))["bilesenler"]
    var = tasinmis()
    CIKTI.mkdir(parents=True, exist_ok=True)
    kayit = json.loads(SONUC.read_text(encoding="utf-8")) if SONUC.exists() else {}
    if a.onayla:
        # Gözle onay: ölçü eşiği aşan ama kontakta aynı görünen bileşen (ör. metnin alt piksel kayması). Sahne değişirse düşer.
        if not a.gerekce:
            print("--gerekce zorunlu")
            return 2
        for ad in a.onayla:
            kayit[ad] = {**kayit.get(ad, {}), "sonuc": "TAMAM", "gozle": a.gerekce, "ozet": ozet(ad)}
        SONUC.write_text(json.dumps(kayit, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"onaylandı: {a.onayla}")
        return 0
    if a.eksik:
        adlar = sorted(x for x in var if kayit.get(x, {}).get("sonuc") != "TAMAM" or kayit[x].get("ozet") != ozet(x))
    else:
        adlar = sorted(var) if a.hepsi else sorted(x for x in var if x.startswith(f"{a.aile}/")) if a.aile else a.adlar
    if a.en_cok:
        adlar = adlar[:a.en_cok]
    eksik = [x for x in adlar if x not in var]
    if eksik or not adlar:
        print(f"Ölçülecek yok: {eksik or 'seçim boş'}")
        return 2 if eksik else 0
    p = hizli.bul(a.proje)
    print(f"{len(adlar)} bileşen, {a.grup}'lık gruplar halinde sıralı")
    print(f"\n{'bileşen':32} {'ort fark':>9} {'%99 fark':>9} {'kayma':>5}  kontak (her satır: sol Remotion, sağ HyperFrames)")
    for i in range(0, len(adlar), a.grup):
        kayit.update(grup_olc(p, adlar[i:i + a.grup], sema))
        SONUC.write_text(json.dumps(kayit, ensure_ascii=False, indent=1), encoding="utf-8")  # her gruptan sonra: yarıda kalırsa kaybolmaz
    tamam = sum(1 for x in var if kayit.get(x, {}).get("sonuc") == "TAMAM" and kayit[x].get("ozet") == ozet(x))
    print(f"\nToplam: {tamam}/{len(var)} TAMAM ({SONUC.relative_to(KOK)})")
    return 0 if all(kayit[x]["sonuc"] == "TAMAM" for x in adlar) else 1


if __name__ == "__main__":
    raise SystemExit(main())
