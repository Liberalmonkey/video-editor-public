"""SFX kütüphanesi: index · fetch (kenney/remotion/wyzowl/freesound/openverse) · synth · search · cues · resolve.

# WHY: bkz. wiki/decisions/0004-ses-efekti-stratejisi.md — lisanssız ses kullanılmaz (manifest'te
# license zorunlu); yerleştirme kural tabanlı, LLM yalnızca anlamsal ipucu ekler.

Klasörler:
  library/sfx/raw/<kaynak>/<paket>/…   ham dosyalar + source.json (lisans kaydı)   [git dışı]
  library/sfx/processed/<id>.wav       kırpılmış, normalize, 48 kHz stereo         [git dışı]
  library/sfx/manifest.json            tek doğruluk kaynağı                         [git'te]
"""

from __future__ import annotations

import io
import json
import os
import re
import time
import zipfile
import zlib
from pathlib import Path

from .tembel import Tembel

# WHY: Stüdyo açılışında yüklenmesin (ADR 0050)
np = Tembel("numpy")
requests = Tembel("requests")
sf = Tembel("soundfile")

from . import ff, paths
from .schemas import SfxEntry, SfxManifest, Timeline, load_json, save_json

RAW = paths.SFX_DIR / "raw"
PROC = paths.SFX_DIR / "processed"
MANIFEST = paths.SFX_DIR / "manifest.json"
AUDIO_EXT = {".wav", ".ogg", ".mp3", ".flac", ".aiff", ".aif", ".m4a"}
UA = {"User-Agent": "vedit/0.1 (kisisel video kurgu araci)"}

KENNEY_PACKS = ["interface-sounds", "ui-audio", "impact-sounds", "digital-audio", "casino-audio", "rpg-audio"]
# Yalnızca CC0 olduğu belgelenen Remotion sesleri (meme sesleri bilinçli olarak hariç)
REMOTION_CC0 = {"whoosh": "whoosh.wav", "whip": "whip.wav", "page_turn": "page-turn.wav", "switch": "switch.wav",
                "click": "mouse-click.wav", "camera_shutter": "shutter-modern.wav",
                "camera_shutter_old": "shutter-old.wav", "ding": "ding.wav"}

# Dosya adı anahtar kelimesi → kategori (sıra önemli: ilk eşleşen kazanır)
CATEGORY_RULES = [
    (r"whoosh|swoosh|whip|swish|woosh", "whoosh"), (r"riser|rise|build", "riser"),
    (r"impact|hit|thud|punch|boom", "impact"), (r"shutter|camera", "camera_shutter"),
    (r"page|bookflip|book_flip", "page_turn"), (r"coin|chip|cash|register|money", "cash"),
    (r"ring|phone", "phone_ring"), (r"notif|message|chime", "notification"),
    (r"type|typing|keyboard|keypress", "typing"), (r"ding|bell|glass", "ding"),
    (r"confirm|success|powerup|highup|complete", "success"), (r"error|wrong|lowdown|fail", "error"),
    (r"switch|toggle", "switch"), (r"click|select|tap|press|metalclick|button", "click"),
    (r"drop|pluck|bong|pop|bubble", "pop"), (r"scroll|scratch|tick", "tick"),
    (r"laser|zap|phaser|glitch", "glitch"), (r"maximize|open|minimize|close|back", "swoosh"),
    (r"footstep|door|cloth|knife|chop|creak", "foley"),
    (r"ambience|ambiance|room.?tone|atmos", "ambience"),  # sonda: önceki eşleşmeleri değiştirmez
]


def load_manifest() -> SfxManifest:
    return load_json(MANIFEST, SfxManifest) if MANIFEST.exists() else SfxManifest()


def _slug(s: str) -> str:
    s = re.sub(r"([a-z])([A-Z])", r"\1-\2", s)
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def categorize(stem: str, pack: str) -> tuple[str, list[str]]:
    low = stem.lower()
    cat = next((c for rx, c in CATEGORY_RULES if re.search(rx, low)), None)
    tags = [t for t in _slug(stem).split("-") if t and not t.isdigit()]
    tags += [t for t in _slug(pack).split("-") if t not in ("kenney", "audio", "sounds")]
    for level in ("light", "medium", "heavy", "soft", "hard"):
        if level in low:
            tags.append(level)
    return cat or (_slug(pack).split("-")[0] or "misc"), sorted(set(tags))


def _sidecar(path: Path) -> dict | None:
    for d in [path.parent, *path.parents]:
        sc = d / "source.json"
        if sc.exists():
            return json.loads(sc.read_text(encoding="utf-8"))
        if d == RAW:
            break
    return None


def _lufs(x: np.ndarray, sr: int, tmp: Path) -> float | None:
    """Karşılaştırılabilir loudness. 1 sn'den kısa ses sessizlikle 1 sn'ye uzatılır: ölçülen değer en yüksek 400 ms pencerenin
    enerjisidir (momentary), kısa tık ile uzun whoosh aynı ölçekte durur."""
    # WHY: bkz. wiki/decisions/0032-ses-katmani.md. Eskiden 0,45 sn altı `null` kalıyordu; kategori içi seviye eşlenemiyordu.
    n = max(len(x), sr)
    sf.write(tmp, np.pad(x, ((0, n - len(x)), (0, 0))), sr, subtype="FLOAT")
    try:
        lufs = ff.loudness(tmp).get("I")
    finally:
        tmp.unlink(missing_ok=True)
    return round(lufs, 1) if lufs and lufs > -70 else None


def _process(src: Path, dst: Path) -> tuple[float, float, float | None, float]:
    """Baş sessizliği kırp, normalize et; (süre, peak_offset, lufs, kırpılan baş sn) döndür."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp.wav")
    ff.ffmpeg("-i", str(src), "-af", "aresample=48000", "-ac", "2", "-c:a", "pcm_f32le", str(tmp))
    x, sr = sf.read(tmp, dtype="float32", always_2d=True)
    tmp.unlink(missing_ok=True)
    # Baş sessizliği burada kırpılır ki kırpılan süre bilinsin (sidecar tepe anı ham dosyaya göredir).
    ses = np.flatnonzero(np.abs(x).max(axis=1) > 10 ** (-50 / 20))
    if len(ses) == 0:
        raise ValueError("boş ses")
    bas = max(0, int(ses[0]) - int(0.004 * sr))
    x = x[bas:]
    dur = len(x) / sr
    # Kısa transient: tepe -4 dBFS; uzun: RMS tabanlı yaklaşık -20 LUFS
    if dur < 1.0:
        x = x / (np.abs(x).max() + 1e-9) * 10 ** (-4 / 20)
    else:
        rms = np.sqrt((x ** 2).mean() + 1e-12)
        x = x * min(10 ** (-21 / 20) / rms, 10 ** (-1 / 20) / (np.abs(x).max() + 1e-9))
    mono = np.abs(x).mean(axis=1)
    win = max(1, int(0.005 * sr))
    peak = float(np.argmax(np.convolve(mono, np.ones(win) / win, mode="same")) / sr)
    sf.write(dst, x, sr, subtype="PCM_24")
    return round(dur, 3), round(peak, 4), _lufs(x, sr, tmp), bas / sr


PARLAK_ESIK = 0.25  # üstü "yüksek frekans riski": tekrarlı rolde seçilmez (olaysesi)


def parlaklik(x: np.ndarray, sr: int) -> float:
    """4 kHz üstü enerji payı, parlak bandın -40 dBFS üstünde kaldığı süreyle ağırlıklı (0,3 sn'de doyar)."""
    m = x.mean(axis=1) if x.ndim > 1 else x
    if len(m) < 64:
        return 0.0
    n = 1024
    hop = n // 2
    if len(m) < n:  # çok kısa tık: tek pencere, sıfırla doldurulur
        m = np.pad(m, (0, n - len(m)))
    kare = [m[i:i + n] * np.hanning(n) for i in range(0, len(m) - n + 1, hop)]
    spek = np.abs(np.fft.rfft(np.asarray(kare), axis=1)) ** 2
    frek = np.fft.rfftfreq(n, 1 / sr)
    yuksek, toplam = spek[:, frek >= 4000].sum(axis=1), spek.sum(axis=1) + 1e-12
    oran = float(yuksek.sum() / toplam.sum())
    rms_yuksek = np.sqrt(yuksek / n)
    aktif = float((rms_yuksek > 10 ** (-40 / 20) * np.sqrt(n) * 0.5).sum() * hop / sr)
    return round(min(1.0, oran * min(1.0, aktif / 0.3) * 2), 3)


def _olc_eksik(man: SfxManifest) -> int:
    """Eski kayıtlarda eksik loudness ve süreyi aşan tepe anını yeniden ölç; kimlik ve dosya değişmez."""
    n = 0
    for e in man.entries:
        f = paths.ROOT / e.file
        if (e.lufs is not None and e.peak_offset_s <= e.duration_s and e.parlak is not None) or not f.exists():
            continue
        x, sr = sf.read(f, dtype="float32", always_2d=True)
        if e.parlak is None:
            e.parlak = parlaklik(x, sr)
        if e.lufs is None:
            e.lufs = _lufs(x, sr, f.with_suffix(".tmp.wav"))
        if e.peak_offset_s > e.duration_s:
            # Sidecar tepesi ham dosyaya göreydi; kırpılan baş = ham süre - işlenmiş süre.
            ham = paths.ROOT / e.raw
            kirp = ff.probe(ham)["duration"] - e.duration_s if ham.exists() else 0.0
            e.peak_offset_s = round(min(max(e.peak_offset_s - kirp, 0.0), e.duration_s), 4)
        n += 1
    return n


def index(rescan: bool = False) -> dict:
    man = load_manifest()
    if rescan:
        man.entries = []
    known = {e.raw for e in man.entries}
    by_raw = {e.id: e for e in man.entries}
    added, skipped = 0, []
    for f in sorted(p for p in RAW.rglob("*") if p.suffix.lower() in AUDIO_EXT):
        rel_raw = f.relative_to(paths.ROOT).as_posix()
        if rel_raw in known:
            continue
        sc = _sidecar(f)
        if not sc or not sc.get("license"):
            skipped.append(f"{rel_raw} (source.json/lisans yok)")
            continue
        pack = f.parent.name
        per_file = (sc.get("files") or {}).get(f.name, {})
        cat, tags = categorize(f.stem, pack)
        cat = per_file.get("category", cat)
        tags = sorted(set(tags + per_file.get("tags", [])))
        eid = f"{cat}-{sc.get('source', 'x')}-{_slug(f.stem)}"[:64]
        if eid in by_raw:
            eid = f"{eid}-{zlib.crc32(rel_raw.encode()) % 999:03d}"
        dst = PROC / f"{eid}.wav"
        try:
            dur, peak, lufs, kirp = _process(f, dst)
        except Exception as e:  # bozuk dosya kütüphaneyi durdurmasın
            skipped.append(f"{rel_raw} ({e})")
            continue
        if "peak_offset_s" in per_file:
            peak = round(min(max(per_file["peak_offset_s"] - kirp, 0.0), dur), 4)
        entry = SfxEntry(id=eid, file=dst.relative_to(paths.ROOT).as_posix(), category=cat, tags=tags,
                         duration_s=dur, peak_offset_s=peak, lufs=lufs, license=sc["license"],
                         source=sc.get("source", "user"), source_url=per_file.get("url") or sc.get("source_url", ""),
                         raw=rel_raw,
                         attribution=sc.get("attribution"))
        man.entries.append(entry)
        by_raw[eid] = entry
        added += 1
    olculen = _olc_eksik(man)
    man.entries.sort(key=lambda e: (e.category, e.id))
    save_json(MANIFEST, man)
    cats: dict[str, int] = {}
    for e in man.entries:
        cats[e.category] = cats.get(e.category, 0) + 1
    return {"added": added, "remeasured": olculen, "total": len(man.entries), "categories": cats, "skipped": skipped[:20]}


# ---------------------------------------------------------------- fetch

def _get(url: str, *, tries: int = 3, **kw) -> requests.Response:
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=60, **kw)
            if r.status_code < 500:
                r.raise_for_status()
                return r
            last = RuntimeError(f"HTTP {r.status_code}")
        except requests.RequestException as e:
            last = e
        time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{url}: {last}")


def fetch_kenney(packs: list[str] | None = None) -> list[str]:
    done = []
    for pack in packs or KENNEY_PACKS:
        dest = RAW / "kenney" / pack
        if dest.exists() and any(dest.rglob("*.ogg")):
            done.append(f"{pack}: zaten var")
            continue
        page = _get(f"https://kenney.nl/assets/{pack}").text
        m = re.search(r'https://kenney\.nl/media/pages/assets/[^"]+\.zip', page)
        if not m:
            done.append(f"{pack}: zip linki bulunamadı")
            continue
        z = zipfile.ZipFile(io.BytesIO(_get(m.group(0)).content))
        dest.mkdir(parents=True, exist_ok=True)
        for name in z.namelist():
            if Path(name).suffix.lower() in AUDIO_EXT:
                (dest / Path(name).name).write_bytes(z.read(name))
        (dest / "source.json").write_text(json.dumps({"license": "CC0", "source": "kenney",
                                                      "source_url": f"https://kenney.nl/assets/{pack}"}, indent=1),
                                          encoding="utf-8")
        done.append(f"{pack}: {len(list(dest.glob('*.*'))) - 1} dosya")
    return done


def fetch_remotion() -> list[str]:
    dest = RAW / "remotion" / "cc0"
    dest.mkdir(parents=True, exist_ok=True)
    files = {}
    for cat, fname in REMOTION_CC0.items():
        p = dest / fname
        if not p.exists():
            p.write_bytes(_get(f"https://remotion.media/{fname}").content)
        files[fname] = {"category": cat.replace("_old", ""), "url": f"https://remotion.media/{fname}"}
    (dest / "source.json").write_text(json.dumps({"license": "CC0", "source": "remotion",
                                                  "source_url": "https://www.remotion.dev/docs/sfx",
                                                  "files": files}, indent=1), encoding="utf-8")
    return list(files)


WYZOWL_ZIP = "https://github.com/wyzowl/sfx-kit/archive/refs/heads/main.zip"
# Wyzowl klasörü → kategori; ada göre ince eşleme _wyzowl_kategori'de. Listede olmayan klasör alınmaz.
WYZOWL_DIRS = {"whooshes": "whoosh", "swishes-and-zips": "swoosh", "swipes": "swoosh", "bounce-spin-zoom": "swoosh",
               "reverse-whooshes": "riser", "risers-and-fallers": "riser", "booms-and-bass": "impact",
               "impacts": "impact", "cinematic-hits": "impact", "pops": "pop", "appear-and-vanish": "pop",
               "interface": "click", "keyboard": "typing", "writing-and-drawing": "typing", "mechanical": "foley",
               "everyday-props": "foley", "foley": "foley", "money": "cash", "digital": "glitch",
               "notifications": "notification", "tones": "ding"}


def _wyzowl_kategori(klasor: str, stem: str) -> str | None:
    cat = WYZOWL_DIRS.get(klasor)
    if cat is None:
        return None
    if "whip" in stem:
        return "whip"
    if klasor == "interface" and "tap" in stem:
        return "tap"
    if klasor == "mechanical" and "shutter" in stem:
        return "camera_shutter"
    if klasor == "everyday-props" and "page-turn" in stem:
        return "page_turn"
    return cat


def _wyzowl_ac(veri: bytes, dest: Path) -> list[str]:
    """Güvenilmeyen zip'i bellekte okur; yalnız sounds/<klasör>/*.wav ve sounds.json'u dest'e düz yazar."""
    z = zipfile.ZipFile(io.BytesIO(veri))
    meta, wavs = {}, []
    for name in z.namelist():
        parts = name.split("/")
        if ".." in parts or name.startswith("/") or ":" in name:
            raise ValueError(f"zip yol kaçışı: {name}")
        if name.endswith("/sounds.json") and len(parts) == 2:
            for m in json.loads(z.read(name)).get("sounds", []):
                meta[Path(m.get("file", "")).name] = m
        elif len(parts) == 4 and parts[1] == "sounds" and name.lower().endswith(".wav"):
            wavs.append((name, parts[2]))
    dest.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, klasor in wavs:
        fname = Path(name).name
        cat = _wyzowl_kategori(klasor, Path(fname).stem)
        if not cat:
            continue
        (dest / fname).write_bytes(z.read(name))
        m = meta.get(fname, {})
        f = {"category": cat, "tags": [t.lower() for t in m.get("tags", [])][:8] + [klasor]}
        if (m.get("sync") or {}).get("at") is not None:
            f["peak_offset_s"] = m["sync"]["at"]
        files[fname] = f
    (dest / "source.json").write_text(json.dumps({"license": "CC0", "source": "wyzowl",
                                                  "source_url": "https://github.com/wyzowl/sfx-kit", "files": files},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    return sorted(files)


def fetch_wyzowl() -> list[str]:
    # Kod ile sentezlenmiş CC0 kit: ham ses gerçek kayıt değildir, earshot ile ölç, kit rolüne körlemesine kilitleme.
    return _wyzowl_ac(_get(WYZOWL_ZIP).content, RAW / "wyzowl")


def fetch_freesound(query: str, n: int = 5, max_dur: float = 6.0) -> list[str]:
    key = os.environ.get("FREESOUND_API_KEY")
    if not key:
        raise SystemExit("FREESOUND_API_KEY yok. Ücretsiz anahtar: https://freesound.org/apiv2/apply — sonra "
                         "ortam değişkeni olarak ayarla.")
    r = _get("https://freesound.org/apiv2/search/text/", params={
        "query": query, "filter": f'license:"Creative Commons 0" duration:[0 TO {max_dur}]',
        "fields": "id,name,tags,duration,previews,license,url,username", "page_size": n, "token": key})
    dest = RAW / "freesound" / _slug(query)
    dest.mkdir(parents=True, exist_ok=True)
    files, out = {}, []
    for s in r.json().get("results", []):
        fname = f"{s['id']}-{_slug(s['name'])[:40]}.mp3"
        (dest / fname).write_bytes(_get(s["previews"]["preview-hq-mp3"]).content)
        files[fname] = {"url": s["url"], "tags": [t.lower() for t in s.get("tags", [])][:8],
                        "author": s.get("username")}
        out.append(fname)
    (dest / "source.json").write_text(json.dumps({"license": "CC0", "source": "freesound",
                                                  "source_url": "https://freesound.org", "files": files},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def fetch_openverse(query: str, n: int = 5) -> list[str]:
    try:
        r = _get("https://api.openverse.org/v1/audio/", params={"q": query, "license": "cc0", "page_size": n,
                                                                  "category": "sound_effect"})
    except RuntimeError as e:
        raise SystemExit(f"Openverse şu an yanıt vermiyor ({e}). Freesound ya da synth kullan.")
    dest = RAW / "openverse" / _slug(query)
    dest.mkdir(parents=True, exist_ok=True)
    files, out = {}, []
    for s in r.json().get("results", []):
        if s.get("license") != "cc0" or (s.get("duration") or 0) > 15000:
            continue
        ext = Path(s["url"].split("?")[0]).suffix or ".mp3"
        fname = f"{_slug(s['title'])[:40]}-{s['id'][:6]}{ext}"
        try:
            (dest / fname).write_bytes(_get(s["url"]).content)
        except RuntimeError:
            continue
        files[fname] = {"url": s.get("foreign_landing_url") or s["url"], "tags": [t["name"] for t in s.get("tags", [])][:8]}
        out.append(fname)
    (dest / "source.json").write_text(json.dumps({"license": "CC0", "source": "openverse",
                                                  "source_url": "https://openverse.org", "files": files},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def synth(variants: int = 3, only: list[str] | None = None) -> int:
    from . import synth as syn
    return len(syn.generate(RAW / "synth" / "vedit", variants=variants, only=only))


# ---------------------------------------------------------------- arama / çözümleme

def search(query: str, limit: int = 12) -> list[SfxEntry]:
    q = [t for t in _slug(query).split("-") if t]
    scored = []
    for e in load_manifest().entries:
        s = 0
        for t in q:
            s += 4 if t == e.category or t == e.category.replace("_", "") else 0
            s += 2 if t in e.tags else 0
            s += 1 if t in e.id else 0
        if s:
            scored.append((s, e))
    scored.sort(key=lambda x: (-x[0], x[1].id))
    return [e for _, e in scored[:limit]]


def catalog_text() -> str:
    """ana oturum için kompakt kategori listesi (kategori: adet, örnek etiketler)."""
    cats: dict[str, list[SfxEntry]] = {}
    for e in load_manifest().entries:
        cats.setdefault(e.category, []).append(e)
    lines = []
    for c, es in sorted(cats.items()):
        tags = sorted({t for e in es for t in e.tags})[:10]
        lines.append(f"- {c} ({len(es)}): {', '.join(tags)}")
    return "\n".join(lines)


def _candidates(entries: list[SfxEntry], typ: str, intensity: str) -> list[SfxEntry]:
    c = [e for e in entries if e.category == typ] or [e for e in entries if typ in e.tags]
    if intensity == "soft":
        c = [e for e in c if "heavy" not in e.tags] or c
    elif intensity == "hard":
        c = [e for e in c if "light" not in e.tags] or c
    return c


def resolve(root: Path) -> dict:
    tl = load_json(root / "edit" / "timeline.json", Timeline)
    man = load_manifest()
    entries = man.entries
    out, missing, last_by_type = [], [], {}
    synth_cats = None
    for cue in sorted(tl.audio.sfx, key=lambda c: c.t):
        if cue.file:
            path = cue.file
            e = next((x for x in entries if x.file == cue.file), None)
            peak = e.peak_offset_s if e else 0.0
        else:
            cands = _candidates(entries, cue.type, cue.intensity)
            if not cands:
                if synth_cats is None:
                    from .synth import RECIPES
                    synth_cats = set(RECIPES)
                if cue.type in synth_cats:  # kütüphanede yok → sentezle, indexle, tekrar dene
                    synth(only=[cue.type])
                    index()
                    entries = load_manifest().entries
                    cands = _candidates(entries, cue.type, cue.intensity)
            if not cands:
                missing.append(f"{cue.id}: '{cue.type}'")
                out.append({**cue.model_dump(), "file": None})
                continue
            start = zlib.crc32(cue.id.encode()) % len(cands)
            pick = cands[start]
            if len(cands) > 1 and last_by_type.get(cue.type) == pick.id:
                pick = cands[(start + 1) % len(cands)]
            last_by_type[cue.type] = pick.id
            path, peak = pick.file, pick.peak_offset_s
        out.append({**cue.model_dump(), "file": path, "peak_offset_s": peak})
    save_json(root / "audio" / "sfx_resolved.json", {"cues": out, "missing": missing})
    return {"cues": len(out), "resolved": sum(1 for c in out if c["file"]), "missing": missing}


# ---------------------------------------------------------------- otomatik ipuçları

def auto_cues(root: Path, *, min_gap: float = 0.4) -> dict:
    """Timeline olaylarından kural tabanlı SFX ipuçları üret; elle eklenenleri (auto=False) koru."""
    from . import blocks as blk
    from .schemas import SfxCue

    tl_path = root / "edit" / "timeline.json"
    tl = load_json(tl_path, Timeline)
    catalog = blk.load_all([root / "edit" / "blocks"])
    cues: list[tuple[float, str, str, str]] = []  # (t, type, intensity, reason)
    for o in tl.overlays:
        b = catalog.get(o.block)
        meta = (b.meta.get("sfx") if b else {}) or {}
        if meta.get("in"):
            cues.append((o.start, meta["in"], "soft", f"{o.id} giriş"))
        for ex in meta.get("extra", []):
            at = ex["at"]
            if at == "count_end":
                at = o.props.get("count_dur") or min(1.4, o.dur * 0.5)
            cues.append((o.start + float(at), ex["type"], ex.get("intensity", "soft"), f"{o.id} vurgu"))
        if meta.get("per_item"):
            for t in _item_times(o):
                cues.append((t, meta["per_item"], "soft", f"{o.id} madde"))
    prev_role = "aroll"
    for c in sorted(tl.video, key=lambda c: c.start):
        if c.role in ("broll", "screen", "image") and c.start > 0.2 and c.layout != "full":
            cues.append((c.start, "swoosh", "soft", f"{c.id} giriş"))
        elif c.role in ("broll", "screen") and prev_role == "aroll" and c.start > 0.2:
            cues.append((c.start, "swoosh", "soft", f"{c.id} kesme"))
        prev_role = c.role
    for ch in tl.chapters[1:]:
        cues.append((ch.start, "whoosh", "medium", f"bölüm {ch.id}"))
    manual = [c for c in tl.audio.sfx if not c.auto]
    taken = sorted(c.t for c in manual)
    new: list[SfxCue] = []
    for i, (t, typ, inten, why) in enumerate(sorted(cues)):
        if any(abs(t - x) < min_gap for x in taken):
            continue
        taken.append(t)
        new.append(SfxCue(id=f"auto{i:03d}", t=round(t, 3), type=typ, intensity=inten, auto=True, reason=why))
    tl.audio.sfx = sorted(manual + new, key=lambda c: c.t)
    save_json(tl_path, tl)
    return {"auto": len(new), "manual": len(manual)}


def _item_times(o) -> list[float]:
    """bullet-list / flow / bar-chart madde zamanları — blok JS'indeki formülün aynısı."""
    P, T0, D = o.props, o.start, o.dur
    if o.block == "bullet-list":
        items = P.get("items", [])
        t0 = T0 + (0.45 if P.get("title") else 0)
        step = P.get("interval") or max(0.5, (D - (t0 - T0) - 0.8) / max(len(items), 1))
        return [T0 + float(P["at"][i]) if P.get("at") and i < len(P["at"]) else t0 + i * step for i in range(len(items))]
    if o.block == "flow":
        n = len(P.get("nodes", []))
        step = max(0.45, (D - 1.0) / max(n, 1))
        return [T0 + float(P["at"][i]) if P.get("at") and i < len(P["at"]) else T0 + i * step for i in range(n)]
    if o.block == "bar-chart":
        t0 = T0 + (0.4 if P.get("title") else 0)
        return [t0 + i * 0.22 for i in range(len(P.get("items", [])))]
    return []


# Konuşmada geçen ses olayları → öneri (ajan onaylar; otomatik eklenmez)
KEYWORDS = {
    "phone_ring": r"\b(zil|çal(dı|ıyor|ınca)|aradı|arıyor|ring(s|ing)?|call(ed|ing)?)\b",
    "notification": r"\b(bildirim|mesaj (geldi|attı)|notification|message|dm)\b",
    "typing": r"\b(yaz(ıyorum|dım|alım)|klavye|typing|type|keyboard)\b",
    "click": r"\b(tıkla|tık|bas(ın|ıyorum)|click|tap|press)\b",
    "cash": r"\b(satış|para|kazan(dım|ç)|ödeme|indirim|sale|money|paid|discount)\b",
    "camera_shutter": r"\b(fotoğraf|çek(tim|elim)|photo|snap|picture)\b",
    "ding": r"\b(doğru|tamam|bitti|hazır|done|ready|correct)\b",
}


def suggest(root: Path, words: list[dict]) -> list[str]:
    text_words = [(w["w"].lower(), w["s"]) for w in words]
    out = []
    for typ, rx in KEYWORDS.items():
        r = re.compile(rx, re.I)
        for i, (w, s) in enumerate(text_words):
            ctx = " ".join(x for x, _ in text_words[max(0, i - 3): i + 4])
            if r.search(w) or (i + 1 < len(text_words) and r.search(f"{w} {text_words[i + 1][0]}")):
                out.append(f"{s:7.2f}s {typ:<15} «{ctx}»")
    return sorted(set(out))
