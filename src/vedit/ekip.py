"""Ekip motoru: 3 editör + 3 kalite kontrol ajanı, turlu düzeltme döngüsü.

WHY: bkz. wiki/decisions/0044-ekip-motoru.md. Tek ajan tek geçişte kurgu yazıyor, kimse sonucu izlemiyordu. Ekipte:
1. Hazırlık (deterministik): digest, transkript, ritim, stil token'ı, katalog özetleri (`aiedit._istek_yaz` bağlamı).
2. Editörler yalnız kendi parça dosyasını yazar (`work/edit/ekip/tur-N/E*.json`). E1 (kesim) önce çalışır, çünkü zaman
   çizelgesini o belirler; E2 (grafik) ve E3 (ses, altyazı, tema) sonra paralel çalışır (kullanıcı kararı, 2026-11-19).
3. Birleştirme deterministik: sahiplik dışı yazım reddedilir, şema, çakışma ve stil denetimi, sonra taslak render.
4. K1-K3 paralel ve salt okunur (plan modu): kare, kontak, OCR, ölçüm ve kurgu-denetle ile bulgu + editöre brif.
5. P0/P1 kalmayınca ya da `--tur` dolunca durur; kalan bulgular rapora, teslim kararı kullanıcıda (ADR 0015).
Bozuk parça birleşmez: bir kez yeniden denenir, sonra slotun yedek motoru; o da olmazsa önceki turun parçası kalır.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

from pydantic import ValidationError

from . import aiedit, ff, fizik, hizli, karakter, kural, kurgu, kurgu_kalite, motorlar, paths, stil, tema_token
from .ekip_sema import EDITORLER, HEDEF, KONTROLLER, ROL_ADI, ROL_TANIM, EkipAyar, KontrolCikti, Parca, Slot
from .schemas import Kurgu

AJAN_SURE = 1800  # sn; tek ajanın üst sınırı
GLOBAL = paths.LIBRARY / "ekip.json"
ROL_KLASORU = paths.ROOT / ".claude" / "agents"


# ---------------------------------------------------------------- ayar

def ayar_yukle(p, dosya: Path | None = None, **ezme) -> EkipAyar:
    """Sıra: library/ekip.json varsayılan ön ayarı < work/edit/ekip.json < --ekip-dosyasi < CLI bayrakları."""
    d: dict = {}
    if GLOBAL.is_file():
        g = json.loads(GLOBAL.read_text(encoding="utf-8"))
        d = dict((g.get("onayarlar") or {}).get(g.get("varsayilan") or "", {}))
    for f in (p.work / "edit" / "ekip.json", dosya):
        if f and Path(f).is_file():
            d.update(json.loads(Path(f).read_text(encoding="utf-8")))
    d.update({k: v for k, v in ezme.items() if v is not None})
    return EkipAyar.model_validate(d)


# ---------------------------------------------------------------- durum (Stüdyo canlı okur)

class Durum:
    def __init__(self, kok: Path, ayar: EkipAyar):
        self.kok, self.kilit = kok, threading.Lock()
        self.d = {"tur": 0, "tur_sinir": ayar.tur, "asama": "hazirlik", "bitti": False, "hata": None,
                  "acik": {"P0": 0, "P1": 0, "P2": 0}, "kapanan": 0, "baslangic": time.time(),
                  "slotlar": {s: {"durum": "bekliyor", "motor": ayar.slotlar[s].motor, "model": ayar.slotlar[s].model,
                                  "seviye": ayar.slotlar[s].seviye, "sure": None, "cikti": None} for s in ayar.slotlar}}
        self.yaz()

    def ayarla(self, **kv):
        with self.kilit:
            self.d.update(kv)
            self.yaz()

    def slot(self, s: str, **kv):
        with self.kilit:
            self.d["slotlar"][s].update(kv)
            self.yaz()

    def yaz(self):
        self.kok.mkdir(parents=True, exist_ok=True)
        kurgu._atomik(self.kok / "durum.json", json.dumps(self.d, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- ajan çağrısı

def _metin_ve_kullanim(satirlar: list[str]) -> tuple[str, dict]:
    """Ham akıştan son yanıt metni ve token kullanımı (motorların ortak alanlarından)."""
    son, kul = "", {}
    for s in satirlar:
        try:
            o = json.loads(s)
        except ValueError:
            continue
        if not isinstance(o, dict):
            continue
        for anahtar in ("result", "response"):
            if isinstance(o.get(anahtar), str) and o[anahtar].strip():
                son = o[anahtar]
        u = o.get("usage") or (o.get("part") or {}).get("tokens") or {}
        if isinstance(u, dict):
            for k, v in u.items():
                if isinstance(v, (int, float)) and "token" in k:
                    kul[k] = kul.get(k, 0) + v
    return son, kul


def ajan(slot: Slot, istem: str, mod: str, kayit: Path, *, yedek: bool = False) -> tuple[bool, str, dict]:
    """Tek çağrı. Ham akış `<kayit>.cikti.jsonl`, okunur günlük `<kayit>.cikti.txt`. (başarılı, yanıt metni, meta)."""
    motor = slot.yedek_motor if yedek else slot.motor
    model = slot.yedek_model if yedek else slot.model
    seviye = slot.yedek_seviye if yedek else slot.seviye
    meta = {"motor": motor, "model": model, "seviye": seviye, "mod": mod, "yedek": yedek, "baslangic": time.time()}
    try:
        komut = motorlar.komut(motor, istem, model, mod, None, seviye)  # bypass bayrağı yok (motorlar kuralı)
    except SystemExit as e:
        meta.update(hata=str(e), sure=0)
        return False, "", meta
    is_ = SimpleNamespace(oturum=None, model=model or "varsayılan")
    cevir, ham, okunur = motorlar.cevirici(), [], []
    with open(f"{kayit}.cikti.jsonl", "w", encoding="utf-8") as fj, open(f"{kayit}.cikti.txt", "w", encoding="utf-8") as ft:
        s = subprocess.Popen(komut, cwd=paths.ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                             text=True, encoding="utf-8", errors="replace", env={**os.environ, "NO_COLOR": "1"})
        zaman = threading.Timer(AJAN_SURE, s.kill)
        zaman.start()
        try:
            for satir in s.stdout:
                satir = satir.rstrip()
                ham.append(satir)
                fj.write(satir + "\n")
                for x in cevir(is_, satir):
                    okunur.append(x)
                    ft.write(x + "\n")
                    ft.flush()
            kod = s.wait()
        finally:
            zaman.cancel()
    son, kul = _metin_ve_kullanim(ham)
    hata = next((x for x in okunur if x.startswith("Hata:")), None)
    meta.update(sure=round(time.time() - meta["baslangic"], 1), kod=kod, token=kul or None, oturum=is_.oturum, hata=hata)
    return kod == 0 and not hata, son or "\n".join(okunur), meta


# ---------------------------------------------------------------- sahiplik ve birleştirme

def kapsamlar(k: Kurgu, ayar: EkipAyar, araliklar: list[tuple[float, float]] | None) -> dict[str, dict]:
    """Rol bölüşü: E1 V1 (+A1), E2 diğer görüntü izleri, E3 diğer ses izleri + altyazı, tema.
    Zaman bölüşü: her editör bir aralığın bütün izlerinin sahibidir; genel alanlar değişmez."""
    video = [i.id for i in k.izler if i.tur == "video"]
    ses = [i.id for i in k.izler if i.tur == "ses"]
    if ayar.bolus == "zaman":
        return {e: {"izler": set(video + ses), "aralik": araliklar[i], "alanlar": {"isaretler"}} for i, e in enumerate(EDITORLER)}
    return {"E1": {"izler": {"V1", *(["A1"] if "A1" in ses else [])}, "aralik": None, "alanlar": {"isaretler"}},
            "E2": {"izler": {i for i in video if i != "V1"}, "aralik": None, "alanlar": set()},
            "E3": {"izler": {i for i in ses if i != "A1"}, "aralik": None, "alanlar": {"altyazi", "motion_tema"}}}


def _sahip(c: dict, kap: dict) -> bool:
    if c.get("iz") not in kap["izler"]:
        return False
    if kap["aralik"]:
        a, b = kap["aralik"]
        return a - 1e-3 <= float(c.get("bas", 0)) < b - 1e-3
    return True


def sahiplik_hatalari(rol: str, parca: Parca, kap: dict) -> list[str]:
    h = [f"{rol}: {c.get('id')} ({c.get('iz')}, {c.get('bas')} sn) sahipliğin dışında" for c in parca.klipler if not _sahip(c, kap)]
    if kap["aralik"]:
        a, b = kap["aralik"]
        h += [f"{rol}: {c.get('id')} aralığı ({b:.2f} sn) aşıyor" for c in parca.klipler
              if float(c.get("bas", 0)) + float(c.get("sure", 0)) > b + 0.05]
    for alan in ("isaretler", "altyazi", "motion_tema"):
        if getattr(parca, alan) is not None and alan not in kap["alanlar"]:
            h.append(f"{rol}: {alan} alanı bu editörün değil")
    return h


def birlestir(taban: Kurgu, parcalar: dict[str, Parca], kap: dict[str, dict]) -> Kurgu:
    """Parçaları tabanın üstüne uygular. Hata SystemExit (birleşmez)."""
    d = taban.model_dump()
    hatalar: list[str] = []
    for rol, pr in parcalar.items():
        hatalar += sahiplik_hatalari(rol, pr, kap[rol])
        d["klipler"] = [c for c in d["klipler"] if not _sahip(c, kap[rol])] + list(pr.klipler)
        for kid, kay in pr.kaynaklar.items():
            if kid in d["kaynaklar"] and d["kaynaklar"][kid] != {**d["kaynaklar"][kid], **kay}:
                hatalar.append(f"{rol}: mevcut kaynak değiştirilemez: {kid}")
            d["kaynaklar"].setdefault(kid, kay)
        if pr.isaretler is not None:
            if kap[rol]["aralik"]:
                a, b = kap[rol]["aralik"]
                d["isaretler"] = [x for x in d["isaretler"] if not a <= x["t"] < b] + [x for x in pr.isaretler if a <= x.get("t", -1) < b]
            else:
                d["isaretler"] = pr.isaretler
        if pr.altyazi is not None:
            d["altyazi"] = pr.altyazi
        if pr.motion_tema is not None:
            d["motion_tema"] = pr.motion_tema
    idler = [c.get("id") for c in d["klipler"]]
    if tekrar := sorted({i for i in idler if idler.count(i) > 1}):
        hatalar.append(f"aynı klip kimliği birden çok yerde: {', '.join(map(str, tekrar[:5]))}")
    if hatalar:
        raise SystemExit("; ".join(hatalar))
    try:
        return Kurgu.model_validate(d)
    except ValidationError as e:
        raise SystemExit(f"şema: {str(e)[:600]}") from e


def zaman_araliklari(k: Kurgu, n: int = 3) -> list[tuple[float, float]]:
    """Süreyi kelime sınırında n parçaya böler: hedef noktaya en yakın kelime arası boşluğun ortası."""
    bitis = max((c.bas + c.sure for c in k.klipler), default=0.0)
    kel = sorted((w["s"], w["e"]) for w in kurgu.izdusum(k)) if k.kelimeler else []
    sinir = [0.0]
    for i in range(1, n):
        hedef = bitis * i / n
        bosluk = [((a[1] + b[0]) / 2, b[0] - a[1]) for a, b in zip(kel, kel[1:]) if abs((a[1] + b[0]) / 2 - hedef) < 2.5]
        sinir.append(round(max(bosluk, key=lambda x: (x[1], -abs(x[0] - hedef)))[0] if bosluk else hedef, 3))
    sinir.append(round(bitis, 3))
    return list(zip(sinir, sinir[1:]))


# ---------------------------------------------------------------- istemler

PARCA_SEMASI = """```json
{"klipler": [ <sahip olduğun izlerdeki BÜTÜN klipler, kurgu.json klip şemasıyla; değişmeyenler de dahil, kimlikleri korunur> ],
 "kaynaklar": { <yalnız YENİ kaynaklar; var olana dokunma> },
 "isaretler": [ ... ] | null, "altyazi": { ... } | null, "motion_tema": "<tema>" | null,
 "rapor": "<ne yaptın, neden; zaman damgalı, en çok 15 satır>"}
```"""


def editor_istemi(p, rol: str, tur: int, kap: dict, baglam: Path, cikti: Path, brif: Path | None, notlar: list[str]) -> Path:
    izler = ", ".join(sorted(kap["izler"])) or "(yok)"
    satir = [
        f"# Ekip editörü {rol}: {ROL_TANIM[rol]} · tur {tur}",
        f"Önce rol dosyanı oku: `{(ROL_KLASORU / (ROL_ADI[rol] + '.md')).resolve()}`.",
        f"Bağlam (kurallar, kataloglar, ritim, stil, platform): `{baglam.resolve()}`. Oradaki “yalnız iki dosya yaz” kuralı ekipte geçersizdir.",
        f"Güncel kurgu (yalnız oku): `{kurgu.yol(p.work).resolve()}`.",
        "## Sahipliğin",
        f"- İzler: {izler}" + (f"; yalnız {kap['aralik'][0]:.2f}-{kap['aralik'][1]:.2f} sn aralığında başlayan klipler. "
                                 "Aralığın süresi sabittir: aralık dışına taşma, sonraki aralığı kaydırma." if kap["aralik"] else "."),
        f"- Ek alanlar: {', '.join(sorted(kap['alanlar'])) or 'yok'}. Başka alan yazarsan parça reddedilir ve birleşmez.",
        "- Başka izlerin kliplerine, `kelimeler`e ve var olan `kaynaklar`a dokunma.",
        "## Çıktı",
        f"Yalnız şu dosyayı yaz (geçerli JSON, UTF-8): `{cikti.resolve()}`\n{PARCA_SEMASI}",
        "Kabuk komutu çalıştırma. Başka dosya yazma.",
    ]
    if brif and brif.exists():
        satir += ["## Düzeltme brifi (yalnız bunu uygula, istenmeyene dokunma)", f"`{brif.resolve()}`"]
    if notlar:
        satir += ["## Notlar"] + [f"- {n}" for n in notlar]
    f = cikti.with_suffix(".istem.md")
    f.write_text("\n\n".join(satir) + "\n", encoding="utf-8")
    return f


def kontrol_istemi(p, rol: str, tur: int, girdi: dict, onceki: list[dict], ayar: EkipAyar, araliklar) -> Path:
    satir = [
        f"# Kalite kontrol {rol}: {ROL_TANIM[rol]} · tur {tur}",
        f"Önce rol dosyanı oku: `{(ROL_KLASORU / (ROL_ADI[rol] + '.md')).resolve()}`. Hiçbir dosyayı değiştirme.",
        "## Girdiler",
        *[f"- {ad}: `{Path(y).resolve()}`" for ad, y in girdi.items()],
        "## Kural",
        "- Bir kusuru yazmadan önce o saniyenin karesini aç. `kanit` açtığın kare dosyasının tam yoludur; dosya yoksa bulgu düşer.",
        "- Her bulgu ölçülebilir `beklenen` taşır (ör. “yazı 1080p'de en az 28 px”, “ses tepesi -1 dBTP altında”, “0,4 sn'de en çok bir ses”).",
        f"- `id` `{rol}-001` biçiminde; `hedef` düzeltecek editör (E1 kesim/ritim, E2 grafik/stil, E3 ses/altyazı). Senin editörün {HEDEF[rol]}.",
        "- P0 yayına giremez, P1 düzeltilmeli, P2 küçük iyileştirme.",
        # WHY: bkz. wiki/decisions/0047-kural-deposu.md
        "- Bulgu etkin bir kuralı ihlal ediyorsa `kural_id` yaz (ör. `K0012`). Bulgu tek seferlik değil, başka videoda da "
        "geçerli bir dersse `kural_adayi` yaz: projeye özgü ad, saniye ve metin içermeyen, `YAP: ` ya da `YAPMA: ` ile başlayan "
        "tek emir satırı (ör. `YAPMA: ikonu yüzün ya da altyazı bandının üstüne koyma.`).",
        "## Etkin kurallar (bunlara göre denetle)",
        kural.paket(kural.yukle(), rol=HEDEF[rol], studyo=p.studyo, proje=f"{p.studyo}/{p.ad}") or "- (yok)",
    ]
    if ayar.bolus == "zaman" and rol == "K2":
        satir.append("- Video üç zaman aralığında ayrı editörlerce yapıldı ("
                     + ", ".join(f"{a:.1f}-{b:.1f} sn" for a, b in araliklar)
                     + "). Aralık sınırlarında stil sürekliliğini (renk, font, grafik dili, geçiş) ayrıca denetle.")
    if onceki:
        satir += ["## Önceki turun açık bulguları (kapandı mı bak; kapanmadıysa yeniden yaz)", "```json",
                  json.dumps(onceki, ensure_ascii=False, indent=1), "```"]
    satir += ["## Yanıt", "Yanıtın sonunda tek bir ```json bloğu ver, başka JSON verme:",
              '```json\n{"bulgular": [{"id": "K1-001", "hedef": "E1", "onem": "P1", "zaman": [12.4, 13.1], "katman": "V1", '
              '"kategori": "stil|okunurluk|ritim|ses|teknik|tutarlilik", "kanit": "<kare yolu>", "sorun": "", "beklenen": "", '
              '"kural_id": "K0012 | null", "kural_adayi": "YAPMA: ... | null"}],\n'
              f' "brif": "<{HEDEF[rol]} için profesyonel düzeltme brifi, markdown: bağlam, P0→P2 maddeler, her maddede zaman damgası ve '
              'ölçülebilir kabul ölçütü, dokunulmayacaklar>"}\n```']
    f = girdi["_kok"] / f"{rol}.istem.md"
    f.write_text("\n\n".join(x for x in satir if x) + "\n", encoding="utf-8")
    return f


def json_cikar(metin: str) -> dict | None:
    """Metindeki `bulgular` anahtarlı son JSON nesnesi."""
    bloklar = re.findall(r"```json\s*(\{.*?\})\s*```", metin, flags=re.S)
    for b in reversed(bloklar):
        try:
            o = json.loads(b)
            if isinstance(o, dict) and "bulgular" in o:
                return o
        except ValueError:
            pass
    dec = json.JSONDecoder()
    for i in reversed([m.start() for m in re.finditer(r"\{", metin)]):
        try:
            o, _ = dec.raw_decode(metin[i:])
        except ValueError:
            continue
        if isinstance(o, dict) and "bulgular" in o:
            return o
    return None


# ---------------------------------------------------------------- QC girdisi

def izle(p, video: Path, kok: Path) -> dict:
    """K ajanlarının ortak girdisi: kareler (+OCR), kontak sayfası, ölçüm, kurgu-denetle. Deterministik."""
    kok.mkdir(parents=True, exist_ok=True)
    sure = float(ff.probe(video)["duration"])
    kontak = kok / "kontak.jpg"
    ff.contact_sheet(video, kontak, duration=sure, cols=6, rows=4, width=270)
    izd = kok / "izle"
    izd.mkdir(exist_ok=True)
    analiz = izd / "analiz.json"
    ocr: dict[float, str] = {}
    try:
        # WHY: video-izle skill'i (ADR 0038); anahtarlar boş: yalnız yerel ve ücretsiz yol.
        r = subprocess.run(["npx", "-y", "mcp-video-analyzer@0.11.0", "analyze", str(video), "--out", str(izd), "--max-frames", "40",
                            "--ocr-language", "tur+eng", "--language", "tr"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=900, env={**os.environ, "OPENAI_API_KEY": "", "TWELVELABS_API_KEY": ""}, shell=os.name == "nt")
        if r.returncode == 0 and r.stdout.strip().startswith("{"):
            analiz.write_text(r.stdout, encoding="utf-8")
            for o in json.loads(r.stdout).get("ocrResults") or []:
                if o.get("text"):
                    ocr[round(float(o.get("time", 0)), 1)] = " ".join(str(o["text"]).split())[:160]
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    # Sahne kareleri başa yığılabilir: her 1,5 sn'de bir sabit kare de çıkarılır, zaman damgası dosya adındadır.
    for t in [round(x * 1.5, 1) for x in range(int(sure / 1.5) + 1)]:
        hedef = izd / f"kare_{t:06.1f}.jpg"
        if not hedef.exists():
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(video), "-frames:v", "1", "-vf", "scale=540:-2", str(hedef)],
                           check=False)
    kareler = sorted(izd.glob("*.jpg"))
    liste = kok / "kareler.md"
    liste.write_text("# Kareler (zaman · dosya · OCR)\n\n" + "\n".join(
        f"- {f.stem.removeprefix('kare_')} · `{f.resolve()}`" + (f" · OCR: {ocr[float(f.stem[5:])]}"
                                                                  if f.stem.startswith("kare_") and float(f.stem[5:]) in ocr else "")
        for f in kareler) + "\n", encoding="utf-8")
    olaylar = p.work / "edit" / "olaylar.json"
    try:
        ol = hizli.denetim(video, olaylar=olaylar if olaylar.exists() else None, work=kok)
        (kok / "olcum.json").write_text(json.dumps(ol, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    except (SystemExit, Exception) as e:  # noqa: BLE001 - ölçüm eksik olsa da denetim sürer
        (kok / "olcum.json").write_text(json.dumps({"hata": str(e)[:400]}, ensure_ascii=False), encoding="utf-8")
    k = kurgu.oku(p.work)
    t = tema_token.oku(kurgu.etkin_tema(p, k.motion_tema))
    dn = [f"! {h}" for h in kurgu.denetle(p, k)] + [f"~ {u['bas']:.2f} sn {u['kod']}: {u['kanit']}. {u['oneri']}"
                                                    for u in kurgu_kalite.uyarilar(k, t)]
    (kok / "kurgu-denetle.txt").write_text("\n".join(dn) or "Kurgu temiz.", encoding="utf-8")
    if t:
        (kok / "stil-token.json").write_text(t.model_dump_json(indent=1), encoding="utf-8")
    return {"_kok": kok, "taslak video": video, "kontak sayfası": kontak, "kare listesi (zaman, yol, OCR)": liste,
            "ölçüm (format, loudness, slop)": kok / "olcum.json", "kurgu-denetle": kok / "kurgu-denetle.txt",
            "kurgu": kurgu.yol(p.work), **({"stil token": kok / "stil-token.json"} if t else {})}


# ---------------------------------------------------------------- bulgu takibi

def _ayni(a: dict, b: dict) -> bool:
    return a["hedef"] == b["hedef"] and a["kategori"] == b["kategori"] and a["zaman"][0] <= b["zaman"][1] + 0.5 and b["zaman"][0] <= a["zaman"][1] + 0.5


def bulgu_dogrula(o: dict, rol: str) -> tuple[KontrolCikti | None, list[str]]:
    try:
        c = KontrolCikti.model_validate(o)
    except ValidationError as e:
        return None, [f"{rol}: şema: {str(e)[:300]}"]
    tut, dus = [], []
    for b in c.bulgular:
        if Path(b.kanit).is_file() or (paths.ROOT / b.kanit).is_file():
            tut.append(b)
        else:
            dus.append(f"{b.id}: kanıt karesi yok ({b.kanit}), bulgu düştü")
    c.bulgular = tut
    return c, dus


# ---------------------------------------------------------------- akış

def calistir(p, ayar: EkipAyar, *, notu: str | None = None, final: bool = False, final_ek: dict | None = None) -> dict:
    ekip = p.work / "edit" / "ekip"
    ekip.mkdir(parents=True, exist_ok=True)
    durum = Durum(ekip, ayar)
    if not aiedit._hazir_mi(p):
        hizli.hazirla(p)
    if ayar.stil:
        _stil_sec(p, ayar.stil)
    k = aiedit._kurgu_hazirla(p)
    once = k
    baglam_kaynak = aiedit._istek_yaz(p, k, stil_adi=ayar.stil, notu=notu, motion_seviye=ayar.motion)
    baglam = ekip / "baglam.md"
    baglam.write_text(baglam_kaynak.read_text(encoding="utf-8"), encoding="utf-8")
    araliklar = zaman_araliklari(k) if ayar.bolus == "zaman" else None
    havuz = ThreadPoolExecutor(max_workers=ayar.eszamanlilik)
    turlar: list[dict] = []
    acik: list[dict] = []
    kapanan: list[dict] = []
    son_parca: dict[str, Parca] = {}

    def editor(rol: str, tur: int, tdir: Path, brifler: dict[str, Path], notlar: list[str]) -> tuple[str, Parca | None, list[str]]:
        taban = kurgu.oku(p.work)
        kap = kapsamlar(taban, ayar, araliklar)[rol]
        cikti = tdir / f"{rol}.json"
        istem_f = editor_istemi(p, rol, tur, kap, baglam, cikti, brifler.get(rol), notlar)
        istem = (f"Read the file {istem_f.resolve()} completely and do exactly what it says. "
                 "Do not run shell commands; only read files and write the single output file it names.")
        hatalar: list[str] = []
        for deneme, yedek in ((1, False), (2, False), (3, True)):
            sl = ayar.slotlar[rol]
            if yedek and not sl.yedek_motor:
                break
            durum.slot(rol, durum="yedek" if yedek else "calisiyor", cikti=str(tdir / f"{rol}.cikti.txt"),
                       motor=sl.yedek_motor if yedek else sl.motor, model=sl.yedek_model if yedek else sl.model)
            cikti.unlink(missing_ok=True)
            ek = "" if not hatalar else "\nPrevious attempt was rejected: " + "; ".join(hatalar)[:1500]
            ok, _, meta = ajan(sl, istem + ek, "duzenle", tdir / rol, yedek=yedek)
            meta["deneme"] = deneme
            (tdir / f"{rol}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
            hatalar = [] if ok else [meta.get("hata") or f"ajan kodu {meta.get('kod')}"]
            if ok:
                try:
                    pr = Parca.model_validate_json(cikti.read_text(encoding="utf-8"))
                    hatalar = sahiplik_hatalari(rol, pr, kap)
                    if not hatalar:
                        yeni = birlestir(taban, {rol: pr}, {rol: kap})
                        hatalar = kurgu.denetle(p, yeni)
                except FileNotFoundError:
                    hatalar = [f"parça dosyası yazılmadı: {cikti.name}"]
                except (ValidationError, ValueError, SystemExit) as e:
                    hatalar = [f"parça geçersiz: {str(e)[:500]}"]
            if not hatalar:
                durum.slot(rol, durum="bitti", sure=meta.get("sure"))
                return rol, pr, []
        durum.slot(rol, durum="hata")
        return rol, None, hatalar

    def uygula(sonuclar: list[tuple[str, Parca | None, list[str]]], tur_kayit: dict):
        taban = kurgu.oku(p.work)
        kap = kapsamlar(taban, ayar, araliklar)
        parcalar = {}
        for rol, pr, h in sonuclar:
            if pr is None:
                tur_kayit["notlar"].append(f"{rol} birleşmedi ({'; '.join(h)[:300]}); önceki tur korunuyor")
                if rol in son_parca:  # önceki turun parçası geri yüklenir (taban zaten onu içeriyor)
                    tur_kayit["geri"].append(rol)
                continue
            parcalar[rol] = pr
            son_parca[rol] = pr
        if parcalar:
            yeni = birlestir(taban, parcalar, kap)
            kurgu.yaz(p.work, yeni)

    for tur in range(1, ayar.tur + 1):
        tdir = ekip / f"tur-{tur}"
        tdir.mkdir(parents=True, exist_ok=True)
        tur_kayit = {"tur": tur, "baslangic": time.time(), "calisan": [], "notlar": [], "geri": [], "bulgu": {}}
        durum.ayarla(tur=tur, kayit=str(tdir))
        for s in ayar.slotlar:
            durum.slot(s, durum="bekliyor", sure=None)
        brifler = {}
        if tur > 1:
            for kk in KONTROLLER:
                if (b := ekip / f"tur-{tur - 1}" / f"{kk}.brif.md").exists():
                    brifler[HEDEF[kk]] = b
            gerek = {b["hedef"] for b in acik if b["onem"] in ("P0", "P1")}
            hedefler = {e: tdir / f"{e}.bulgular.json" for e in gerek}
            for e, f in hedefler.items():
                f.write_text(json.dumps([b for b in acik if b["hedef"] == e], ensure_ascii=False, indent=1), encoding="utf-8")
        else:
            gerek = set(EDITORLER)
            hedefler = {}

        def notlar(e: str) -> list[str]:
            n = [f"Senin için açık bulgular: `{hedefler[e].resolve()}`"] if e in hedefler else []
            return n

        if ayar.bolus == "zaman":
            durum.ayarla(asama="E1+E2+E3")
            sonuc = list(havuz.map(lambda e: editor(e, tur, tdir, brifler, notlar(e)), [e for e in EDITORLER if e in gerek]))
            uygula(sonuc, tur_kayit)
            tur_kayit["calisan"] = [r for r, _, _ in sonuc]
        else:
            v1_once = [(c.bas, c.sure) for c in kurgu.oku(p.work).klipler if c.iz == "V1"]
            if "E1" in gerek:
                durum.ayarla(asama="E1")
                sonuc = [editor("E1", tur, tdir, brifler, notlar("E1"))]
                uygula(sonuc, tur_kayit)
                tur_kayit["calisan"].append("E1")
            v1_sonra = [(c.bas, c.sure) for c in kurgu.oku(p.work).klipler if c.iz == "V1"]
            ikinci = [e for e in ("E2", "E3") if e in gerek or (tur > 1 and v1_once != v1_sonra)]
            ek_not = ["E1 bu turda zaman çizelgesini değiştirdi: kliplerini yeni kesim zamanlarına göre güncelle."] if tur > 1 and v1_once != v1_sonra else []
            if ikinci:
                durum.ayarla(asama="+".join(ikinci))
                sonuc = list(havuz.map(lambda e: editor(e, tur, tdir, brifler, notlar(e) + ek_not), ikinci))
                uygula(sonuc, tur_kayit)
                tur_kayit["calisan"] += ikinci
        # render
        durum.ayarla(asama="render")
        yeni = kurgu.oku(p.work)
        kurgu.motion_bagla(p, yeni)
        fizik.bagla(p, yeni)
        karakter.bagla(p, yeni)
        kurgu.yaz(p.work, yeni)
        video = hizli.taslak(p)
        kopya = tdir / "taslak.mp4"
        kopya.unlink(missing_ok=True)
        os.link(video, kopya) if os.name == "nt" else kopya.symlink_to(video)
        # QC
        durum.ayarla(asama="izle")
        girdi = izle(p, kopya, tdir)
        durum.ayarla(asama="K1+K2+K3")
        onceki = acik

        def kontrol(kk: str):
            f = kontrol_istemi(p, kk, tur, girdi, [b for b in onceki if b["hedef"] == HEDEF[kk] or b["id"].startswith(kk)], ayar, araliklar)
            istem = (f"Read the file {f.resolve()} completely and do exactly what it says. Do not modify any file.")
            for deneme, yedek in ((1, False), (2, False), (3, True)):
                sl = ayar.slotlar[kk]
                if yedek and not sl.yedek_motor:
                    break
                durum.slot(kk, durum="yedek" if yedek else "calisiyor", cikti=str(tdir / f"{kk}.cikti.txt"))
                ok, metin, meta = ajan(sl, istem, "plan", tdir / kk, yedek=yedek)
                meta["deneme"] = deneme
                o = json_cikar(metin) if ok else None
                if o is None and ok:
                    # yanıt metni çeviride bölünmüş olabilir: okunur günlükten de ara
                    o = json_cikar((tdir / f"{kk}.cikti.txt").read_text(encoding="utf-8", errors="replace"))
                c, dus = bulgu_dogrula(o, kk) if o is not None else (None, ["JSON bloğu yok"])
                meta["dusen"] = dus
                (tdir / f"{kk}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
                if c is not None:
                    (tdir / f"{kk}.bulgu.json").write_text(json.dumps([b.model_dump() for b in c.bulgular], ensure_ascii=False, indent=1), encoding="utf-8")
                    (tdir / f"{kk}.brif.md").write_text(c.brif or "(brif yok)\n", encoding="utf-8")
                    durum.slot(kk, durum="bitti", sure=meta.get("sure"))
                    return kk, [b.model_dump() for b in c.bulgular]
            durum.slot(kk, durum="hata")
            return kk, None

        sonuclar = list(havuz.map(kontrol, KONTROLLER))
        yeni_bulgu = [b for _, bl in sonuclar for b in (bl or [])]
        # Yanıt vermeyen denetçinin önceki bulguları denetlenmedi: kapanmış sayılmaz, açık kalır.
        for kk, bl in sonuclar:
            if bl is None:
                yeni_bulgu += [{**b, "denetlenmedi": True} for b in onceki if b["id"].startswith(kk)]
        if ayar.bolus == "zaman":  # hedef zaman aralığının sahibidir
            for b in yeni_bulgu:
                b["hedef"] = next((e for e, (a, z) in zip(EDITORLER, araliklar) if a <= b["zaman"][0] < z), "E3")
        # WHY: bkz. wiki/decisions/0047-kural-deposu.md. Genelleşmiş bulgu kural adayı olur; silinen kural yeniden önerilmez.
        tur_kayit["kurallar"] = kural.qc_isle([b for b in yeni_bulgu if not b.get("denetlenmedi")], proje=f"{p.studyo}/{p.ad}")
        kapanan += [b for b in onceki if b["onem"] in ("P0", "P1") and not any(_ayni(b, y) for y in yeni_bulgu)]
        acik = yeni_bulgu
        sayi = {o: sum(1 for b in acik if b["onem"] == o) for o in ("P0", "P1", "P2")}
        tur_kayit.update(bulgu=sayi, sure=round(time.time() - tur_kayit["baslangic"], 1),
                         basarisiz_kk=[kk for kk, bl in sonuclar if bl is None])
        turlar.append(tur_kayit)
        durum.ayarla(acik=sayi, kapanan=len(kapanan))
        (tdir / "ozet.json").write_text(json.dumps(tur_kayit, ensure_ascii=False, indent=1), encoding="utf-8")
        if not sayi["P0"] and not sayi["P1"] and not tur_kayit["basarisiz_kk"]:
            break
    havuz.shutdown()
    son = kurgu.oku(p.work)
    rapor_yaz(p, ayar, once, son, turlar, acik, kapanan)
    durum.ayarla(asama="bitti", bitti=True)
    if final:
        if any(b["onem"] == "P0" for b in acik):
            print("  ! Açık P0 bulgusu var: teslim kullanıcı kararı (ADR 0015). --final atlandı.")
        else:
            hizli.final(p, **(final_ek or {}))
    return {"turlar": turlar, "acik": acik, "kapanan": kapanan}


def _stil_sec(p, ad: str) -> None:
    """Stil projede seçilir; katalog stiliyse ve stüdyoda yoksa önce eklenir (temalar ADR 0043)."""
    from . import stil_katalog
    if not (stil.klasor(p.studyo, ad) / "STYLE.md").exists():
        stil_katalog.ekle(p.studyo, ad, p)
    else:
        stil.sec(p, ad)


def rapor_yaz(p, ayar: EkipAyar, once: Kurgu, son: Kurgu, turlar: list[dict], acik: list[dict], kapanan: list[dict]) -> Path:
    bit = lambda k: max((c.bas + c.sure for c in k.klipler), default=0.0)  # noqa: E731
    sat = [f"# AI Edit Raporu (ekip) · {p.studyo}/{p.ad}", "",
           f"{time.strftime('%d.%m.%Y %H:%M')} · rev {once.rev} → {son.rev} · süre **{bit(son):.2f} s** · bölüş `{ayar.bolus}` · "
           f"stil **{stil.secili_adi(p) or 'yok'}** · motion `{ayar.motion}`", "",
           "## Ekip", "| Slot | Rol | Motor | Model | Seviye | Yedek |", "|---|---|---|---|---|---|"]
    for s, sl in ayar.slotlar.items():
        sat.append(f"| {s} | {ROL_TANIM[s]} | {sl.motor} | {sl.model or 'varsayılan'} | {sl.seviye or '-'} | "
                   f"{(sl.yedek_motor or '-') + (' / ' + sl.yedek_model if sl.yedek_model else '')} |")
    sat += ["", "## Turlar", "| Tur | Çalışan editör | Süre | Açık P0 / P1 / P2 | Not |", "|---|---|---|---|---|"]
    for t in turlar:
        b = t["bulgu"]
        sat.append(f"| {t['tur']} | {', '.join(t['calisan']) or '-'} | {t.get('sure', 0):.0f} sn | {b.get('P0', 0)} / {b.get('P1', 0)} / {b.get('P2', 0)} | "
                   + "; ".join(t["notlar"] + [f"{k} yanıt vermedi" for k in t.get("basarisiz_kk", [])])[:300] + " |")
    sat += ["", f"## Kapanan bulgular ({len(kapanan)})"] + [f"- {b['id']} {b['onem']} {b['zaman'][0]:.1f}-{b['zaman'][1]:.1f} sn {b['katman']}: {b['sorun']}" for b in kapanan]
    sat += ["", f"## Açık bulgular ({len(acik)})"] + [f"- **{b['onem']}** {b['id']} → {b['hedef']} · {b['zaman'][0]:.1f}-{b['zaman'][1]:.1f} sn "
                                                     f"{b['katman']} ({b['kategori']}): {b['sorun']} Beklenen: {b['beklenen']}" for b in acik]
    if any(b["onem"] == "P0" for b in acik):
        sat += ["", "> P0 açık: teslim kararı kullanıcıda (ADR 0015)."]
    eksik = sorted({k for t in turlar[-1:] for k in t.get("basarisiz_kk", [])})
    if eksik:
        sat += ["", f"> Son turda {', '.join(eksik)} yanıt vermedi: o alanlar denetlenmedi, sonuç temiz sayılmaz."]
    sat += ["", f"Kayıtlar: `{paths.rel(p.work / 'edit' / 'ekip')}` (tur-N: istemler, ajan çıktıları, süre, model, token, bulgular, brifler)."]
    f = p.work / "edit" / "ai-edit.rapor.md"
    f.write_text("\n".join(sat) + "\n", encoding="utf-8")
    (p.work / "edit" / "ai-edit.ozet.json").write_text(json.dumps({
        "once_rev": once.rev, "rev": son.rev, "klip": [len(once.klipler), len(son.klipler)],
        "sure": [round(bit(once), 2), round(bit(son), 2)], "aralik": None, "ekip": True,
        "acik": {o: sum(1 for b in acik if b["onem"] == o) for o in ("P0", "P1", "P2")}, "kapanan": len(kapanan)}), encoding="utf-8")
    print(f"Rapor: {paths.rel(f)}")
    return f
