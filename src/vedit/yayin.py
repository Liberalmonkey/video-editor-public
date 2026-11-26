"""Teslim edilen her video için platforma göre başlık, açıklama ve hashtag (yayın metni). WHY: bkz. wiki/decisions/0055-teslimde-yayin-metni.md

Ajan (Claude Code, Antigravity, Codex, OpenCode) istek dosyasını okur ve yalnız `work/yayin/<video>.json` yazar. vedit JSON'u
platform reçetesine (`library/yayin/platformlar.json`) göre doğrular; hata varsa ajan aynı oturumda bir kez düzeltir. Geçen
paket `yayin.md`'de video başına işaretli bloğa yazılır; elle yazılmış metin ve atıf bölümü korunur.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ValidationError

from . import ff, hizli, paths

RECETE = paths.LIBRARY / "yayin" / "platformlar.json"
VARSAYILAN_MOTOR = "claude"
VARSAYILAN_MODEL = "claude-opus-5-5"
METIN_SINIRI = 60_000  # ajana giden transkript; 15 dk konuşma ≈ 15k karakter
BLOK = re.compile(r"<!-- yayin:(?P<stem>[^>]+?) -->\n(?P<govde>.*?)<!-- /yayin:(?P=stem) -->\n?", re.S)
HASHTAG = re.compile(r"#[^\s#]+")
ZAMAN = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{2})$")


# ---------------------------------------------------------------- reçete

@lru_cache(maxsize=1)
def _recete_ham(mtime: float) -> dict:
    return json.loads(RECETE.read_text(encoding="utf-8"))


def recete() -> dict:
    return _recete_ham(RECETE.stat().st_mtime)


def platformlar() -> dict[str, dict]:
    return recete()["platformlar"]


def varsayilan_platformlar(studyo: str) -> list[str]:
    return list(recete()["studyo_varsayilan"].get(studyo, ["reels"]))


def platform_listesi(deger: str | list[str] | None, studyo: str) -> list[str]:
    """'reels,youtube' ya da liste → sıralı, tekrarsız; boşsa stüdyo varsayılanı. Bilinmeyen platform SystemExit."""
    if not deger:
        return varsayilan_platformlar(studyo)
    ham = deger.split(",") if isinstance(deger, str) else list(deger)
    sonuc = list(dict.fromkeys(x.strip() for x in ham if x and x.strip()))
    bilinmeyen = [x for x in sonuc if x not in platformlar()]
    if bilinmeyen:
        raise SystemExit(f"Bilinmeyen platform: {', '.join(bilinmeyen)}. Geçerli: {', '.join(platformlar())}")
    return sonuc or varsayilan_platformlar(studyo)


# ---------------------------------------------------------------- videolar

def _klasor(p: hizli.Proje) -> Path:
    return p.work / "yayin"


def paket_yolu(p: hizli.Proje, stem: str) -> Path:
    return _klasor(p) / f"{stem}.json"


@lru_cache(maxsize=256)
def _sure(yol: str, mtime: float) -> float | None:
    try:
        return round(float(ff.probe(Path(yol))["duration"]), 2)
    except Exception:  # ffprobe yok ya da bozuk dosya: süre bilinmiyor, liste yine döner
        return None


def video_bul(p: hizli.Proje, ad: str) -> Path:
    """Teslim klasöründeki mp4; alt klasör, work ve kök dışı reddedilir."""
    f = (p.cikti / Path(str(ad)).name).resolve()
    if Path(str(ad)).name != str(ad) or f.suffix.lower() != ".mp4" or not f.is_file() or not f.is_relative_to(p.cikti.resolve()):
        raise SystemExit(f"Teslim videosu yok: {ad}")
    return f


def paket_oku(p: hizli.Proje, stem: str) -> dict | None:
    f = paket_yolu(p, stem)
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else None
    except ValueError:
        return None


def videolar(p: hizli.Proje) -> list[dict]:
    """Teslim videoları doğal sırayla; her biri için süre, SRT, paket ve paket videodan eski mi."""
    if not p.cikti.exists():
        return []
    sonuc = []
    for f in sorted((f for f in p.cikti.glob("*.mp4") if f.is_file()), key=lambda f: hizli.dogal(f.name)):
        paket = paket_oku(p, f.stem)
        uretim = (paket or {}).get("_uretim") or {}
        sonuc.append({
            "ad": f.name, "stem": f.stem, "sure": _sure(str(f), f.stat().st_mtime), "srt": f.with_suffix(".srt").is_file(),
            "paket": paket, "eski": bool(paket) and abs(uretim.get("video_mtime", 0) - f.stat().st_mtime) > 1,
        })
    return sonuc


# ---------------------------------------------------------------- bağlam

def _srt_metni(f: Path) -> str:
    """SRT → '[m:ss] metin' satırları; bölüm zamanları için başlangıç korunur."""
    satirlar = []
    for blok in re.split(r"\n\s*\n", f.read_text(encoding="utf-8-sig").replace("\r", "")):
        parca = [x for x in blok.strip().split("\n") if x.strip()]
        zaman = next((x for x in parca if "-->" in x), None)
        if not zaman:
            continue
        m = re.match(r"(\d+):(\d+):(\d+)", zaman.strip())
        metin = " ".join(parca[parca.index(zaman) + 1:]).strip()
        if m and metin:
            sn = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3])
            satirlar.append(f"[{sn // 60}:{sn % 60:02d}] {metin}")
    return "\n".join(satirlar)


def metin_kaynagi(p: hizli.Proje, video: Path) -> tuple[str, str]:
    """(kaynak adı, metin): teslimin SRT'si, yoksa hazirla digest'i, yoksa senaryo.md."""
    srt = video.with_suffix(".srt")
    if srt.is_file() and (m := _srt_metni(srt)):
        return srt.name, m[:METIN_SINIRI]
    for f in (p.work / "analysis" / "digest.txt", p.girdi / "senaryo.md"):
        if f.is_file() and (m := f.read_text(encoding="utf-8").strip()):
            return paths.rel(f), m[:METIN_SINIRI]
    raise SystemExit(f"{video.name} için metin yok: yanında .srt, work/analysis/digest.txt ya da girdide senaryo.md gerekli.")


def dil_bul(p: hizli.Proje) -> str:
    """Transkript önbelleğindeki dil (hazirla); yoksa tr."""
    sayac: dict[str, int] = {}
    for f in (p.work / "analysis" / "yazi").glob("*.json") if (p.work / "analysis" / "yazi").exists() else []:
        try:
            d = json.loads(f.read_text(encoding="utf-8")).get("language")
        except (ValueError, OSError):
            continue
        if d in ("tr", "en"):
            sayac[d] = sayac.get(d, 0) + 1
    return max(sayac, key=sayac.get) if sayac else "tr"


def _kurallar_metni() -> str:
    """Kullanıcının düzeltme defterinden yayın metniyle ilgili satırlar (checks.md kural deposundan üretilir)."""
    f = paths.LIBRARY / "checks.md"
    if not f.is_file():
        return ""
    anahtar = ("yayın", "yayin", "açıklama", "hashtag", "başlık", "caption", "cta", "çağrı", "emoji")
    return "\n".join(x for x in f.read_text(encoding="utf-8").splitlines()
                     if x.lstrip().startswith(("-", "*")) and any(k in x.casefold() for k in anahtar))[:4000]


def _sure_metni(sn: float | None) -> str:
    return "bilinmiyor" if sn is None else f"{int(sn) // 60}:{int(sn) % 60:02d} ({sn:.0f} sn)"


def istek_yaz(p: hizli.Proje, video: Path, secili: list[str], dil: str) -> Path:
    """Ajanın okuyacağı istek dosyası: kanıt paketi, platform reçeteleri, çıktı şeması."""
    from . import stil
    kaynak, metin = metin_kaynagi(p, video)
    sure = _sure(str(video), video.stat().st_mtime)
    hedef = paket_yolu(p, video.stem).resolve()
    dil_ad = {"tr": "Türkçe", "en": "English"}.get(dil, dil)
    rec = platformlar()
    bolum = []
    for k in secili:
        r = rec[k]
        sinir = (f"{r['baslik_ad']}: en çok {r['baslik_max']} karakter (hedef ≤ {r['baslik_oneri']}). "
                 f"Açıklama + hashtag satırı birlikte en çok {r['aciklama_max']} karakter. "
                 f"Hashtag: {r['hashtag_min']}-{r['hashtag_max']} adet.")
        if r["etiket_max"]:
            sinir += f" Etiketler (tags) virgülle birleşince en çok {r['etiket_max']} karakter, 8-15 etiket."
        sinir += " Bölümler: " + ("video 8 dakikayı geçiyorsa zorunlu, değilse boş liste." if r["bolumler"] else "boş liste.")
        bolum.append(f"### `{k}` · {r['ad']}{'' if r['arastirildi'] else ' (genel kurallar)'}\n{sinir}\n"
                     + "\n".join(f"- {x}" for x in r["kural"]))
    ornek = {"video": video.name, "dil": dil, "platformlar": {k: {
        "baslik": "...", "aciklama": "...", "hashtagler": ["#ornek"], "etiketler": [], "bolumler": [], "notlar": "..."} for k in secili}}
    if any(rec[k]["bolumler"] for k in secili):
        ornek["platformlar"][next(k for k in secili if rec[k]["bolumler"])]["bolumler"] = [{"t": "0:00", "baslik": "..."}]
    kurallar = _kurallar_metni()
    govde = f"""# Yayın metni görevi

Sen kıdemli bir sosyal medya editörüsün. Aşağıdaki teslim videosu için her platforma ayrı, yayına hazır başlık, açıklama ve
hashtag yaz. Metin profesyonel, akıcı ve insan yazmış gibi olsun; videoda söylenmeyen hiçbir şeyi vaat etme, sayı ve iddia
uydurma. Viral ya da keşfet garantisi verme. Gereken her şey bu dosyada; başka dosya okuma ya da arama.

## Yazım kuralları (hepsi)
- Dil: {dil_ad}. Konuşma dili, kısa cümle, somut fiil. Kurumsal dolgu yok.
- Yapay zekâ kokan kalıpları kullanma: "X değil, Y" karşıtlığı, zorlama üçlüler, abartı sıfatlar ("devrim", "oyun değiştirici",
  "inanılmaz"), satış ağzı, gereksiz tire ve kalın etiketler, tek satırlık süslü kapanış cümlesi.
- Emoji yalnız platform alışkanlığına uyuyorsa ve en çok 2 tane; LinkedIn ve YouTube başlığında emoji yok.
- Hashtag'ler konuya özgü, `#` ile başlar, boşluk içermez, tekrar etmez; genel popüler etiket (#viral, #fyp, #keşfet) yok.
- Hashtag'leri açıklama metnine yazma; yalnız `hashtagler` listesine koy (vedit kopyalanacak metne kendisi ekler).
- `notlar`: kullanıcıya tek iki cümle (ör. riskli çağrı, AI avatar etiketi hatırlatması, araştırılmamış platform uyarısı).

## Video
- Dosya: {video.name}
- Süre: {_sure_metni(sure)}
- Stüdyo: {p.studyo} · Proje: {p.ad} · Stil: {stil.secili_adi(p) or 'yok'}

## Platformlar
{chr(10).join(bolum)}
{f"{chr(10)}## Kullanıcının kalıcı kuralları (uy){chr(10)}{kurallar}{chr(10)}" if kurallar else ""}
## Videonun metni ({kaynak})
```text
{metin}
```

## Çıktı
Yalnız şu dosyayı yaz (UTF-8 JSON; başka dosya yazma, dosya okumak dışında komut çalıştırma):
`{hedef}`

Şema (yalnız bu platform anahtarları: {', '.join(secili)}):
```json
{json.dumps(ornek, ensure_ascii=False, indent=1)}
```
`bolumler` öğesi `{{"t": "m:ss", "baslik": "..."}}`; zamanlar metindeki gerçek konu değişimlerinden alınır, ilk bölüm 0:00.
Dosyayı yazdıktan sonra tek satırla bitir. Dosyayı yazamazsan aynı JSON'u yanıtında tek bir ```json bloğu olarak ver.
"""
    f = _klasor(p) / f"istek-{video.stem}.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(govde, encoding="utf-8")
    return f


# ---------------------------------------------------------------- doğrulama

class Bolum(BaseModel):
    t: str
    baslik: str


class Paket(BaseModel):
    baslik: str
    aciklama: str
    hashtagler: list[str] = []
    etiketler: list[str] = []
    bolumler: list[Bolum] = []
    notlar: str = ""


class Yayin(BaseModel):
    video: str
    dil: str = "tr"
    platformlar: dict[str, Paket]


def _saniye(t: str) -> int | None:
    m = ZAMAN.match(t.strip())
    return None if not m else int(m[1] or 0) * 3600 + int(m[2]) * 60 + int(m[3])


def etiket_uzunlugu(etiketler: list[str]) -> int:
    """YouTube sayımı: virgüller sayılır, boşluklu etiket tırnakla (+2) sayılır."""
    return sum(len(e) + (2 if " " in e else 0) for e in etiketler) + max(0, len(etiketler) - 1)


def kopya_metni(platform: str, paket: dict) -> str:
    """Platforma yapıştırılacak açıklama: metin, (YouTube'da) bölümler, sonra hashtag satırı. Arayüz aynı biçimi kullanır."""
    parca = [paket.get("aciklama", "").strip()]
    if paket.get("bolumler"):
        parca.append("\n".join(f"{b['t']} {b['baslik']}" for b in paket["bolumler"]))
    if paket.get("hashtagler"):
        parca.append(" ".join(paket["hashtagler"]))
    return "\n\n".join(x for x in parca if x)


def _hashtag_temizle(ham: list[str]) -> list[str]:
    return [("#" + h.strip().lstrip("#")) if h.strip() else "" for h in ham]


def dogrula(veri: dict, secili: list[str], *, sure: float | None = None) -> tuple[dict | None, list[str], list[str]]:
    """(temiz paket, hatalar, uyarılar). Hata varsa paket None. İstenmeyen platform atılır, kapalı alan boşaltılır."""
    try:
        y = Yayin.model_validate(veri)
    except ValidationError as e:
        return None, [f"{'.'.join(map(str, h['loc']))}: {h['msg']}" for h in e.errors()], []
    rec, hatalar, uyarilar = platformlar(), [], []
    temiz: dict[str, dict] = {}
    for k in secili:
        if k not in y.platformlar:
            hatalar.append(f"{k}: platform eksik")
            continue
        r, pk = rec[k], y.platformlar[k].model_copy(deep=True)
        pk.baslik, pk.aciklama, pk.notlar = pk.baslik.strip(), pk.aciklama.strip(), pk.notlar.strip()
        pk.hashtagler = _hashtag_temizle(pk.hashtagler)
        if not pk.baslik:
            hatalar.append(f"{k}: başlık boş")
        if not pk.aciklama:
            hatalar.append(f"{k}: açıklama boş")
        if len(pk.baslik) > r["baslik_max"]:
            hatalar.append(f"{k}: başlık {len(pk.baslik)} karakter, sınır {r['baslik_max']}")
        elif len(pk.baslik) > r["baslik_oneri"]:
            uyarilar.append(f"{k}: başlık {len(pk.baslik)} karakter; akışta yaklaşık ilk {r['baslik_oneri']} görünür")
        for h in pk.hashtagler:
            if h == "#" or not HASHTAG.fullmatch(h):
                hatalar.append(f"{k}: geçersiz hashtag {h!r} (boşluk ya da boş)")
        kucuk = [h.casefold() for h in pk.hashtagler]
        if len(set(kucuk)) != len(kucuk):
            hatalar.append(f"{k}: tekrar eden hashtag")
        if not r["hashtag_min"] <= len(pk.hashtagler) <= r["hashtag_max"]:
            hatalar.append(f"{k}: {len(pk.hashtagler)} hashtag, olması gereken {r['hashtag_min']}-{r['hashtag_max']}")
        if HASHTAG.search(pk.aciklama) and pk.hashtagler:
            uyarilar.append(f"{k}: açıklamada da hashtag var; kopyalanan metinde iki kez görünebilir")
        if r["etiket_max"]:
            pk.etiketler = [e.strip() for e in pk.etiketler if e.strip()]
            if (n := etiket_uzunlugu(pk.etiketler)) > r["etiket_max"]:
                hatalar.append(f"{k}: etiketler {n} karakter, sınır {r['etiket_max']}")
        else:
            pk.etiketler = []
        if r["bolumler"] and pk.bolumler:
            zamanlar = [_saniye(b.t) for b in pk.bolumler]
            if None in zamanlar:
                hatalar.append(f"{k}: bölüm zamanı m:ss olmalı")
            elif zamanlar[0] != 0 or len(zamanlar) < 3 or any(b - a < 10 for a, b in zip(zamanlar, zamanlar[1:])):
                hatalar.append(f"{k}: bölümler 0:00 ile başlar, en az 3 tane, aralar en az 10 sn ve artan sırada")
            elif sure and zamanlar[-1] >= sure:
                hatalar.append(f"{k}: son bölüm ({pk.bolumler[-1].t}) videonun süresini aşıyor")
        elif r["bolumler"] and sure and sure > 480:
            uyarilar.append(f"{k}: 8 dakikadan uzun video için bölüm yok")
        if not r["bolumler"]:
            pk.bolumler = []
        if k in ("youtube", "shorts") and any(c in pk.baslik + pk.aciklama for c in "<>"):
            hatalar.append(f"{k}: YouTube başlık ve açıklamada '<' ve '>' kabul etmez")
        d = pk.model_dump()
        if (n := len(kopya_metni(k, d))) > r["aciklama_max"]:
            hatalar.append(f"{k}: açıklama + bölüm + hashtag {n} karakter, sınır {r['aciklama_max']}")
        if not r["arastirildi"]:
            uyarilar.append(f"{k}: platform kuralları araştırılmadı, metin genel kurallarla yazıldı")
        temiz[k] = d
    if hatalar:
        return None, hatalar, uyarilar
    return {"video": y.video, "dil": y.dil, "platformlar": temiz}, [], uyarilar


# ---------------------------------------------------------------- yayin.md

def _blok_md(video_ad: str, veri: dict) -> str:
    rec = platformlar()
    satir = [f"## {video_ad}", ""]
    for k, pk in veri["platformlar"].items():
        r = rec.get(k, {"ad": k, "baslik_ad": "Başlık"})
        satir += [f"### {r['ad']}", "", f"**{r['baslik_ad']}:** {pk['baslik']}", "", "**Açıklama (kopyala):**", "",
                  "```text", kopya_metni(k, pk), "```", ""]
        if pk.get("etiketler"):
            satir += [f"**Etiketler:** {', '.join(pk['etiketler'])}", ""]
        if pk.get("notlar"):
            satir += [f"> Not: {pk['notlar']}", ""]
    u = veri.get("_uretim") or {}
    if u:
        satir += [f"<sub>{u.get('motor', '?')} · {u.get('model') or 'varsayılan'} · {u.get('zaman', '')}"
                  f"{' · elle düzenlendi' if u.get('duzenlendi') else ''}</sub>", ""]
    return "\n".join(satir).rstrip() + "\n"


def md_yaz(p: hizli.Proje, stem: str, video_ad: str, veri: dict) -> Path:
    """`yayin.md`'de bu videonun bloğunu yazar. Bloklar doğal sırada; blok dışı metin başta, atıf bölümü sonda kalır."""
    f = p.cikti / "yayin.md"
    eski = f.read_text(encoding="utf-8") if f.exists() else ""
    govde, atif = (eski.split(hizli.ATIF_BASLIK, 1) + [None])[:2]
    bloklar = {m["stem"]: m["govde"] for m in BLOK.finditer(govde)}
    bas = BLOK.sub("", govde).strip()
    bloklar[stem] = _blok_md(video_ad, veri)
    parca = [bas] if bas else []
    parca += [f"<!-- yayin:{s} -->\n{bloklar[s].rstrip()}\n<!-- /yayin:{s} -->" for s in sorted(bloklar, key=hizli.dogal)]
    metin = "\n\n".join(parca) + "\n"
    if atif is not None:
        metin += "\n" + hizli.ATIF_BASLIK + atif
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(metin, encoding="utf-8")
    return f


# ---------------------------------------------------------------- üret ve kaydet

def _yaz(p: hizli.Proje, video: Path, veri: dict, uretim: dict) -> dict:
    veri = {**veri, "video": video.name, "_uretim": {**uretim, "video_mtime": video.stat().st_mtime}}
    f = paket_yolu(p, video.stem)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    md_yaz(p, video.stem, video.name, veri)
    return veri


def yanittan_json(metin: str) -> dict | None:
    """Ajan dosya yazamadıysa (izin, sandbox) yanıttaki ```json bloğu ya da ilk '{' ile son '}' arası."""
    adaylar = re.findall(r"```(?:json)?\s*\n(.*?)```", metin, re.S)
    if "{" in metin:
        adaylar.append(metin[metin.index("{"):metin.rindex("}") + 1])
    for a in adaylar:
        try:
            v = json.loads(a)
        except ValueError:
            continue
        if isinstance(v, dict) and isinstance(v.get("platformlar"), dict):
            return v
    return None


def _yanittan_yaz(hedef: Path, yanit: str) -> None:
    """Dosya yoksa ya da okunamıyorsa ve yanıtta geçerli JSON varsa onu yazar; bozuk dosya yalnız böyle ezilir."""
    if (not hedef.exists() or not _json_oku(hedef)[0]) and (v := yanittan_json(yanit)):
        print("  Ajan dosyayı yazamadı; JSON yanıttan alındı.", flush=True)
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")


def _json_oku(f: Path) -> tuple[dict | None, list[str]]:
    if not f.is_file():
        return None, [f"Ajan {f.name} dosyasını yazmadı"]
    try:
        v = json.loads(f.read_text(encoding="utf-8-sig"))
    except ValueError as e:
        return None, [f"JSON okunamadı: {e}"]
    return (v, []) if isinstance(v, dict) else (None, ["JSON nesne olmalı"])


# WHY: ajan_cagri.dosyadan kabuk komutunu yasaklar; Codex'in tek dosya aracı kabuktur ve o yasakla istek dosyasını
# okuyamıyordu (2026-11-23 denemesi). Burada yalnız okuma komutuna izin verilir; yazma tek hedef dosyadır, Codex sandbox'ı
# (workspace-write) zaten çalışma alanıyla sınırlar. Yazamayan motor JSON'u yanıtında verir (yanittan_json).
_ERISIM = ("Use your file tools; if your only file tool is a shell, read-only commands that print a file (Get-Content, cat, type) "
           "are allowed. Write exactly one file, {hedef}; do not create, modify or delete anything else and do not run other commands. "
           "If you cannot write the file, reply with the full JSON in one ```json block.")


def uret(p: hizli.Proje, video_ad: str, secili: list[str], *, motor: str = VARSAYILAN_MOTOR, model: str | None = None,
         seviye: str | None = None, dil: str | None = None) -> dict:
    """Ajana yazdırır, doğrular (bir düzeltme turu), JSON ve yayin.md'ye işler."""
    from . import ajan_cagri
    video = video_bul(p, video_ad)
    if model is None and motor == VARSAYILAN_MOTOR:
        model = VARSAYILAN_MODEL
    dil = dil or dil_bul(p)
    istek = istek_yaz(p, video, secili, dil)
    hedef = paket_yolu(p, video.stem)
    yedek = hedef.with_suffix(".onceki.json")
    if hedef.exists():
        hedef.replace(yedek)
    sure = _sure(str(video), video.stat().st_mtime)
    try:
        print(f"{video.name}: {', '.join(secili)} · {motor} {model or 'varsayılan'}", flush=True)
        yanit, oturum = ajan_cagri.calistir(
            f"Read the file {istek.resolve()} completely and do exactly what it says. {_ERISIM.format(hedef=hedef.resolve())}",
            motor=motor, model=model, seviye=seviye)
        _yanittan_yaz(hedef, yanit)
        ham, hatalar = _json_oku(hedef)
        temiz, hatalar2, uyarilar = dogrula(ham, secili, sure=sure) if ham else (None, hatalar, [])
        if not temiz:
            print("  Düzeltme turu: " + "; ".join(hatalar2), flush=True)
            yanit, _ = ajan_cagri.calistir(
                f"The JSON at {hedef.resolve()} failed validation. Fix ONLY these problems and rewrite the same file "
                f"(keep the rest; rules are in {istek.resolve()}). Problems: " + " | ".join(hatalar2)
                + ". " + _ERISIM.format(hedef=hedef.resolve()),
                motor=motor, model=model, oturum=oturum, seviye=seviye)
            _yanittan_yaz(hedef, yanit)
            ham, hatalar = _json_oku(hedef)
            temiz, hatalar2, uyarilar = dogrula(ham, secili, sure=sure) if ham else (None, hatalar, [])
            if not temiz:
                raise SystemExit(f"{video.name}: yayın metni doğrulanamadı: " + "; ".join(hatalar2))
    except BaseException:
        if hedef.exists():
            hedef.replace(hedef.with_suffix(".hatali.json"))  # inceleme için; geçerli paket bozulmasın
        if yedek.exists():
            yedek.replace(hedef)
        raise
    yedek.unlink(missing_ok=True)
    for u in uyarilar:
        print(f"  ! {u}")
    veri = _yaz(p, video, temiz, {"motor": motor, "model": model, "seviye": seviye,
                                   "zaman": dt.datetime.now().isoformat(timespec="seconds")})
    print(f"  yayın metni: {paths.rel(hedef)} · yayin.md", flush=True)
    return veri


def kaydet(p: hizli.Proje, video_ad: str, veri: dict) -> tuple[dict, list[str]]:
    """Arayüzde elle düzenlenen paketi doğrular ve yazar; ajan çağrılmaz. Hata SystemExit (metinle)."""
    video = video_bul(p, video_ad)
    secili = [k for k in (veri.get("platformlar") or {}) if k in platformlar()]
    if not secili:
        raise SystemExit("En az bir bilinen platform gerekli")
    temiz, hatalar, uyarilar = dogrula({**veri, "video": video.name}, secili, sure=_sure(str(video), video.stat().st_mtime))
    if not temiz:
        raise SystemExit("; ".join(hatalar))
    eski = (paket_oku(p, video.stem) or {}).get("_uretim") or {}
    uretim = {**{k: v for k, v in eski.items() if k != "video_mtime"}, "duzenlendi": dt.datetime.now().isoformat(timespec="seconds")}
    return _yaz(p, video, temiz, uretim), uyarilar


def ozet(p: hizli.Proje) -> dict:
    """Stüdyo Yayın metni paneli: reçete (sınırlar), stüdyo varsayılanı, videolar ve paketleri."""
    alanlar = ("ad", "arastirildi", "baslik_ad", "baslik_max", "baslik_oneri", "aciklama_max", "hashtag_min", "hashtag_max",
               "etiket_max", "bolumler")
    return {
        "platformlar": {k: {a: r[a] for a in alanlar} for k, r in platformlar().items()},
        "varsayilan": varsayilan_platformlar(p.studyo),
        "varsayilan_motor": VARSAYILAN_MOTOR, "varsayilan_model": VARSAYILAN_MODEL,
        "dil": dil_bul(p),
        "videolar": videolar(p),
    }
