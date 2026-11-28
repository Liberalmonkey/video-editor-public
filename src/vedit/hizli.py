"""Hızlı hat: hazirla, kes, taslak, final, denetim, kaizen, duzen.

WHY: bkz. wiki/decisions/0017-terminal-hizli-hat.md. Düzeltme taslakta yapılır, tam render bir kez alınır;
her komut work/sure.jsonl'a süre yazar, kaizen en yavaş adımı gösterir.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json

import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from . import ff, kurgu, paths

VIDEO = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
MEDYA = VIDEO | {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
GORSEL = {".png", ".jpg", ".jpeg", ".webp"}
PLATFORM = {"instagram": "reels", "ugc": "ugc", "youtube-animasyon": "youtube"}
RC = paths.ROOT / "openmontage" / "remotion-composer"
STUDIO = paths.ROOT / "studio"
REEL_FONTLARI = ("Inter-Variable.ttf", "JetBrainsMono-Variable.ttf", "SpaceGrotesk-Variable.ttf")
KAIZEN = paths.LIBRARY / "kaizen.md"
# WHY: son kodlama vedit teslim'dedir (slow, CRF 16); ara dosyada aynı işi iki kez yapmak süreyi 2 katına çıkarıyordu.
# PNG kalır: JPEG q95 videolu sahnede SSIM'i 0,979'a düşürüyor, veryfast 0,998'de kalıyor.
ARA_KODLAMA = ["--crf=14", "--x264-preset=veryfast"]
# WHY: bkz. wiki/decisions/0060-proxy-master-conform.md. Master ön ayarı: ara render kayıpsız 4:4:4 (x264 CRF 0),
# tek kayıplı nesil teslim kodlamasında kalır.
ARA_KAYIPSIZ = ["--crf=0", "--pixel-format=yuv444p", "--x264-preset=veryfast"]


@dataclass(frozen=True)
class Proje:
    studyo: str
    ad: str

    @property
    def girdi(self) -> Path:
        return paths.INPUTS / self.studyo / self.ad

    @property
    def cikti(self) -> Path:
        return paths.OUTPUTS / self.studyo / self.ad

    @property
    def work(self) -> Path:
        return self.cikti / "work"


def bul(ref: str) -> Proje:
    """`08-claude`, `instagram/08-claude` ya da tam yol. Girdi ya da çıktı klasörü yeter."""
    ref = str(ref).replace("\\", "/").rstrip("/").removesuffix("/work")
    bulunan = set()
    for kok in (paths.INPUTS, paths.OUTPUTS):
        for d in kok.glob("*/*"):
            if d.is_dir() and not d.parent.name.startswith("_") and not d.name.startswith("_") \
                    and (ref in f"{d.parent.name}/{d.name}" or ref.endswith(f"{d.parent.name}/{d.name}")):
                bulunan.add(Proje(d.parent.name, d.name))
    # Tam ad öncelikli: `arvelior`, `arvelior-hiz` varken belirsiz sayılmaz.
    tam = {p for p in bulunan if ref in (p.ad, f"{p.studyo}/{p.ad}") or ref.endswith(f"/{p.studyo}/{p.ad}")}
    if len(tam) == 1:
        return tam.pop()
    if len(bulunan) == 1:
        return bulunan.pop()
    if not bulunan:
        raise SystemExit(f"Proje yok: {ref}. Dosyaları Projeler/inputs/<stüdyo>/<proje>/ altına koy.")
    raise SystemExit("Birden fazla proje eşleşti: " + ", ".join(f"{p.studyo}/{p.ad}" for p in sorted(bulunan, key=str)))


def dogal(ad: str) -> list:
    """Doğal sıralama anahtarı: 2.mp4, 10.mp4'ten önce gelir."""
    return [int(x) if x.isdigit() else x.casefold() for x in re.split(r"(\d+)", ad)]


def sure_yaz(work: Path, komut: str, saniye: float, not_: str = "") -> None:
    work.mkdir(parents=True, exist_ok=True)
    kayit = {"t": dt.datetime.now().isoformat(timespec="seconds"), "komut": komut, "sn": round(saniye, 1), "not": not_}
    with (work / "sure.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")


def work_bul(argv: list[str]) -> Path | None:
    """Komut satırındaki yollardan ya da proje adından work/ klasörünü çıkar; bulunmazsa sessizce None."""
    for tok in argv:
        p = Path(tok)
        try:
            p = p.resolve()
        except OSError:
            continue
        for ata in (p, *p.parents):
            if ata.name == "work":
                return ata
            if ata.parent.parent.parent == paths.OUTPUTS:
                return ata / "work"
    for tok in argv:
        if not tok.startswith("-"):
            try:
                return bul(tok).work
            except SystemExit:
                pass
    return None


def _ozet(dosya: Path) -> str:
    """Önbellek anahtarı: içerik (başı + sonu + boyut), taşınsa da geçerli."""
    h = hashlib.sha1(str(dosya.stat().st_size).encode())
    with dosya.open("rb") as f:
        h.update(f.read(1 << 20))
        f.seek(max(0, dosya.stat().st_size - (1 << 20)))
        h.update(f.read(1 << 20))
    return h.hexdigest()[:12]


def _gorsel_olcu(f: Path) -> str:
    try:
        v = ff.probe(f).get("video") or {}
        return f"{v.get('width')}x{v.get('height')}"
    except Exception:
        return "?"


def yazi(video: Path, work: Path, *, dil: str | None, prompt: str | None) -> dict:
    """Önbellekli transkript; aynı dosya için model yüklenmez. Düzeltme sözlüğü her okumada uygulanır (önbellek ham kalır)."""
    from . import sozluk, transcribe
    onbellek = work / "analysis" / "yazi" / f"{video.stem}-{_ozet(video)}.json"
    if onbellek.exists():
        return sozluk.uygula(json.loads(onbellek.read_text(encoding="utf-8")))
    wav = work / "analysis" / "audio" / f"{video.stem}.wav"
    ff.extract_audio(video, wav)
    t0 = time.time()
    r = transcribe.transcribe_file(wav, language=dil, model_name=transcribe.DEFAULT_MODEL, prompt=prompt or sozluk.ipucu())
    print(f"  {video.name}: transkript {time.time() - t0:.0f} sn")
    onbellek.parent.mkdir(parents=True, exist_ok=True)
    onbellek.write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
    return sozluk.uygula(r)


def hazirla(p: Proje, *, dil: str | None = "tr", prompt: str | None = None, ek: list[str] | None = None) -> None:
    if not p.girdi.exists():
        raise SystemExit(f"Girdi yok: {paths.rel(p.girdi)}")
    for d in ("analysis", "edit", "renders", "qa", "public"):
        (p.work / d).mkdir(parents=True, exist_ok=True)
    dosyalar = sorted((f for f in p.girdi.iterdir() if f.is_file() and f.suffix.lower() in MEDYA), key=lambda f: dogal(f.name)) + [Path(e) for e in ek or []]
    # WHY: bkz. wiki/decisions/0060-proxy-master-conform.md. Ağır kaynağın proxy'si transkriptle paralel hazırlanır.
    from . import vekil
    vekil_isleri = vekil.arka_planda(p.work, dosyalar)
    if vekil_isleri:
        print(f"Proxy: {len(vekil_isleri)} iş başladı (4K/HEVC/10-bit/HDR/VFR kaynak; final yine orijinali kullanır)", flush=True)
    sonuc, digest = {"files": {}}, []
    for f in dosyalar:
        v = ff.probe(f).get("video")
        print(f"- {f.name}: {ff.probe(f)['duration']:.1f}s" + (f" {v['width']}x{v['height']}@{v['fps']:g}" if v else " ses"))
        t = yazi(f, p.work, dil=dil, prompt=prompt)
        sonuc["files"][f.stem] = t
        digest.append(f"# {f.name}")
        digest += [f"[{s['start']:.2f}-{s['end']:.2f}] {s['text']}" for s in t["segments"]]
        if v:
            sheet = p.work / "analysis" / "sheets" / f"{f.stem}.jpg"
            if not sheet.exists() or sheet.stat().st_mtime < f.stat().st_mtime:
                ff.contact_sheet(f, sheet, duration=ff.probe(f)["duration"])
    for f in sorted(x for x in p.girdi.rglob("*") if x.is_file() and x.suffix.lower() in GORSEL):
        print(f"- {f.relative_to(p.girdi).as_posix()}: {_gorsel_olcu(f)}")
    (p.work / "analysis" / "transcript.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    (p.work / "analysis" / "digest.txt").write_text("\n".join(digest) + "\n", encoding="utf-8")
    print(f"Digest: {paths.rel(p.work / 'analysis' / 'digest.txt')}")
    for t in vekil_isleri:
        t.join()
    if vekil_isleri:
        print(f"Proxy hazır: {paths.rel(vekil.klasor(p.work))}")


def hiz_parcalari(parcalar: list[dict], kelimeler: dict[str, list[dict]], hiz: float = 1.0, sessiz_hiz: float = 1.0,
                  esik: float = 1.2) -> list[dict]:
    """Parçalara `hiz` ekler. `sessiz_hiz` varsa `esik` saniyeden uzun konuşmasız aralıklar ayrı parça olup hızlanır.

    kelimeler: kaynak anahtarı -> kaynak zamanında kelimeler. WHY: bkz. wiki/decisions/0019-arayuz-ve-efekt-motoru-birlesimi.md
    """
    sonuc = []
    for s in parcalar:
        sinirlar, imlec = [], s["in"]  # (bas, bit, carpan)
        if sessiz_hiz > 1:
            icerde = [w for w in kelimeler.get(s["k"], []) if w["e"] > s["in"] and w["s"] < s["out"]]
            for w in sorted(icerde, key=lambda w: w["s"]):
                if w["s"] - imlec >= esik:
                    sinirlar.append((imlec, w["s"], sessiz_hiz))
                    imlec = w["s"]
                bit = max(imlec, min(w["e"], s["out"]))
                if bit > imlec:
                    sinirlar.append((imlec, bit, 1.0))
                    imlec = bit
            if s["out"] - imlec >= esik:
                sinirlar.append((imlec, s["out"], sessiz_hiz))
                imlec = s["out"]
        if imlec < s["out"]:
            sinirlar.append((imlec, s["out"], 1.0))
        birlesik: list[list[float]] = []
        for a, b, k in sinirlar:  # kelimeler arası kısa boşluk konuşmaya katılır, kesim sayısı artmaz
            if birlesik and birlesik[-1][2] == k:
                birlesik[-1][1] = b
            else:
                birlesik.append([a, b, k])
        sonuc += [{**s, "in": a, "out": b, "hiz": round(hiz * k, 4)} for a, b, k in birlesik]
    return sonuc


def kesim_olustur(girdi: Path, duzen: list[str]) -> dict:
    """Kesilmiş parçalar: hepsi baştan sona, sırayla."""
    kaynak = {f"V{i + 1:02d}": ad for i, ad in enumerate(duzen)}
    return {"kaynak": kaynak, "parcalar": [{"k": k, "in": 0, "out": ff.probe(girdi / ad)["duration"]} for k, ad in kaynak.items()]}


def kesim_filtresi(anahtarlar: list[str], parcalar: list[dict], bilgi: dict[str, dict], fade: float, v_fps: float) -> tuple[str, int]:
    """filter_complex metni. Boyutlar farklıysa ilk kaynağa sığdırır, sesi olmayan kaynağa sessizlik koyar."""
    boyut = {(bilgi[k]["video"]["width"], bilgi[k]["video"]["height"]) for k in anahtarlar}
    W, H = bilgi[anahtarlar[0]]["video"]["width"], bilgi[anahtarlar[0]]["video"]["height"]
    sigdir = f",scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1" if len(boyut) > 1 else ""
    filt, ciftler = [], []
    for i, s in enumerate(parcalar):
        n = anahtarlar.index(s["k"])
        h = s["hiz"]
        d = (s["out"] - s["in"]) / h
        g = s.get("gain_db", 0)
        filt.append(f"[{n}:v]trim={s['in']}:{s['out']},setpts=(PTS-STARTPTS)/{h},fps={v_fps}{sigdir}[v{i}]")
        ses = (f"[{n}:a]atrim={s['in']}:{s['out']},asetpts=PTS-STARTPTS,{f'atempo={h},' if h != 1 else ''}"
               if "audio" in bilgi[s["k"]] else f"anullsrc=r=48000:cl=stereo,atrim=0:{d:.3f},")
        filt.append(f"{ses}volume={g}dB,afade=t=in:d={fade},afade=t=out:st={max(0, d - fade):.3f}:d={fade}[a{i}]")
        ciftler.append(f"[v{i}][a{i}]")
    filt.append("".join(ciftler) + f"concat=n={len(ciftler)}:v=1:a=1[v][a]")
    return ";".join(filt), len(ciftler)


def kes(p: Proje) -> Path:
    """work/edit/kesim.json → work/public/speaker.mp4.

    {"kaynak": {"A": "ana.mp4"}, "parcalar": [{"k": "A", "in": 0, "out": 12.3}]}
    İsteğe bağlı: "hiz": 1.25 (tüm video), "sessiz_hiz": 3 (konuşmasız aralıklar; önce vedit hazirla gerekir).
    kesim.json yoksa girdideki videolar doğal ad sırasıyla uç uca alınır.
    """
    kesim = p.work / "edit" / "kesim.json"
    if not kesim.exists():
        videolar = sorted((f.name for f in p.girdi.iterdir() if f.is_file() and f.suffix.lower() in VIDEO), key=dogal)
        if not videolar:
            raise SystemExit(f"Video yok: {paths.rel(p.girdi)}")
        kesim.parent.mkdir(parents=True, exist_ok=True)
        kesim.write_text(json.dumps(kesim_olustur(p.girdi, videolar), ensure_ascii=False, indent=1), encoding="utf-8")
    spec = json.loads(kesim.read_text(encoding="utf-8"))
    kaynak = {k: p.girdi / v for k, v in spec["kaynak"].items()}
    sira = list(kaynak)
    args: list[str] = []
    for k in sira:
        args += ["-i", str(kaynak[k])]
    fade = spec.get("fade", 0.012)  # WHY: kesim tıkını önler (usta-editor: 10-20 ms)
    v_fps = spec.get("fps", 30)
    hiz, sessiz_hiz = float(spec.get("hiz", 1)), float(spec.get("sessiz_hiz", 1))
    for i, s in enumerate(spec["parcalar"]):
        if s["out"] <= s["in"]:
            raise SystemExit(f"Parça {i}: out <= in")
    kelimeler: dict[str, list[dict]] = {}
    if sessiz_hiz > 1:
        yol = p.work / "analysis" / "transcript.json"
        dosyalar = json.loads(yol.read_text(encoding="utf-8"))["files"] if yol.exists() else {}
        for k in sira:
            if kaynak[k].stem not in dosyalar:
                raise SystemExit(f"{kaynak[k].name} için transkript yok. sessiz_hiz için önce: vedit hazirla")
            kelimeler[k] = [w for g in dosyalar[kaynak[k].stem]["segments"] for w in g["words"]]
    bilgi = {k: ff.probe(kaynak[k]) for k in sira}
    filtre, adet = kesim_filtresi(sira, hiz_parcalari(spec["parcalar"], kelimeler, hiz, sessiz_hiz), bilgi, fade, v_fps)
    out = p.work / "public" / "speaker.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    ff.ffmpeg(*args, "-filter_complex", filtre, "-map", "[v]", "-map", "[a]", "-c:v", "libx264",
              "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", str(out))
    print(f"Kesim: {paths.rel(out)} · {ff.probe(out)['duration']:.2f}s · {adet} parça")
    return out


def _public_hazirla(p: Proje) -> None:
    fontlar = p.work / "public" / "fonts"
    fontlar.mkdir(parents=True, exist_ok=True)
    # WHY: bkz. wiki/decisions/0043-stile-bagli-tema-tokenlari.md. Stilin fontu (piksel, el yazısı...) render'da da bulunsun.
    for f in paths.FONTS_DIR.glob("*.ttf"):
        hedef = fontlar / f.name
        if not hedef.exists():
            # WHY: farklı sürücüde hardlink EXDEV verir, eşzamanlı isteklerde ise FileExistsError oluşur.
            try:
                hedef.hardlink_to(f)
            except FileExistsError:
                pass
            except OSError:
                shutil.copy2(f, hedef)


def _props(p: Proje, mod: str = "final") -> Path:
    # WHY: bkz. wiki/decisions/0021-video-studyo-nle.md. kurgu.json varsa tek kaynak odur, sahne.mjs çalışmaz.
    # mod (ADR 0060): "taslak" ağır kaynakta proxy bağlar; "final"/"master" orijinali bağlar ve conform kapısını çalıştırır.
    if kurgu.yol(p.work).exists():
        return kurgu.hazirla(p, mod=mod)
    sahne = p.work / "edit" / "sahne.mjs"
    if sahne.exists():
        subprocess.run(["node", str(sahne)], check=True, cwd=sahne.parent)
    props = p.work / "edit" / "props.json"
    if not props.exists():
        raise SystemExit(f"Props yok: {paths.rel(props)}. Önce work/edit/sahne.mjs yaz.")
    # WHY: bkz. wiki/decisions/0043-stile-bagli-tema-tokenlari.md. Eski SplitReel yolu da seçili stilin token'ını alır.
    d = json.loads(props.read_text(encoding="utf-8"))
    d["tema"] = kurgu.tema_tokeni(p, kurgu.bos(p.studyo))
    props.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return props


_KARE = re.compile(r"Rendered (\d+)/(\d+)(?:, time remaining: (.+))?")


def ilerleme_satiri(satir: str, son: int, adim: int = 5) -> tuple[int, str | None]:
    """Remotion'ın 'Rendered 120/2274, time remaining: 3m 10s' satırından her %`adim`'de bir özet. (yeni son, satır | None)"""
    m = _KARE.search(satir)
    if not m or not int(m[2]):
        return son, None
    yuzde = int(m[1]) * 100 // int(m[2])
    kova = yuzde // adim * adim
    if kova <= son:
        return son, None
    return kova, f"  %{yuzde} · {m[1]}/{m[2]} kare" + (f" · kalan {m[3].strip()}" if m[3] and yuzde < 100 else "")


def _remotion(props: Path, public: Path, cikti: Path, *ek: str, ilerleme: bool = False) -> None:
    kok, giris, kompozisyon = (STUDIO, "remotion/index.tsx", "Kurgu") if props.name.startswith("kurgu.render") else (RC, "src/index.tsx", "SplitReel")
    exe = kok / "node_modules" / ".bin" / ("remotion.cmd" if os.name == "nt" else "remotion")
    cikti, props, public = cikti.resolve(), props.resolve(), public.resolve()  # Remotion studio/ içinde çalışır; göreli yol oraya düşerdi
    cikti.parent.mkdir(parents=True, exist_ok=True)
    # WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Fizik sahnesi WebGL ister; headless Chrome'un varsayılan GL'i
    # Windows'ta three.js'i çizmeyebilir. Bayrak yalnız fizik varken eklenir, 2B kurguların render'ı değişmez.
    gl = ["--gl=angle"] if '"kind": "fizik"' in props.read_text(encoding="utf-8", errors="ignore") else []
    komut = [str(exe), "render", giris, kompozisyon, str(cikti), f"--props={props}", f"--public-dir={public}", *gl, *ek]
    if not ilerleme:
        subprocess.run([*komut, "--log=error"], check=True, cwd=kok, shell=os.name == "nt")
        return
    # WHY: bkz. wiki/decisions/0035-teslim-ayarlari.md. Export dakikalarca sessiz kalınca ne çalıştığı anlaşılmıyordu.
    s = subprocess.Popen(komut, cwd=kok, shell=os.name == "nt", stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace")
    son, kuyruk = -1, []
    for satir in s.stdout:
        son, ozet = ilerleme_satiri(satir, son)
        if ozet:
            print(ozet, flush=True)
        elif not _KARE.search(satir):
            kuyruk = [*kuyruk, satir.rstrip()][-15:]  # hata olursa motorun son sözleri
    if s.wait():
        raise SystemExit("Görüntü render'ı durdu:\n" + "\n".join(kuyruk))


def _goruntu(p: Proje, props: Path, cikti: Path, ek: list[str], *, kalite: str, aralik: tuple[float, float] | None = None,
             ilerleme: bool = False) -> str:
    """Görüntü render'ı: HyperFrames yapabiliyorsa HyperFrames, değilse Remotion (son çare). Kullanılan motoru döner.

    WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Seçim ve nedeni work/edit/motor.json'da; Stüdyo rozeti okur.
    """
    from . import hf_kurgu
    motor, neden = hf_kurgu.motor_sec(p, props, olcek=any(e.startswith("--scale=") and float(e.split("=", 1)[1]) > 1 for e in ek))
    print(f"  Motor: {'HyperFrames' if motor == 'hf' else 'Remotion'} ({neden})", flush=True)
    if motor == "hf":
        olcek = next((float(e.split("=", 1)[1]) for e in ek if e.startswith("--scale=")), 1.0)
        crf = next((int(e.split("=", 1)[1]) for e in ek if e.startswith("--crf=")), None)
        chroma = "444" if "--pixel-format=yuv444p" in ek else None
        hf_kurgu.render(p, props, cikti, kalite=kalite, aralik=aralik, olcek=olcek, crf=crf, chroma=chroma)
    else:
        # Remotion H.264'te CRF 0'ı reddeder (iOS uyumu); master ara render orada CRF 1 4:4:4, görsel olarak kayıpsız.
        ek = ["--crf=1" if e == "--crf=0" else e for e in ek]
        if aralik and not any(e.startswith("--frames=") for e in ek):
            fps = json.loads(props.read_text(encoding="utf-8")).get("sekans", {}).get("fps", 30)
            ek = [*ek, f"--frames={int(aralik[0] * fps)}-{int(aralik[1] * fps)}"]
        _remotion(props, p.work / "public", cikti, *ek, ilerleme=ilerleme)
    return motor


def taslak(p: Proje, *, aralik: list[float] | None = None) -> Path:
    bas = aralik[0] if aralik else 0.0
    out = p.work / "renders" / "taslak.mp4"
    props = _props(p, "taslak")
    _public_hazirla(p)
    ek = ["--image-format=jpeg", "--x264-preset=veryfast", "--crf=23", "--scale=0.5"]
    if aralik:
        fps = kurgu.oku(p.work).sekans.fps if kurgu.yol(p.work).exists() else 30
        ek.append(f"--frames={int(aralik[0] * fps)}-{int(aralik[1] * fps)}")
    _goruntu(p, props, out, ek, aralik=tuple(aralik) if aralik else None, kalite="draft")
    sure = ff.probe(out)["duration"]
    sheet = p.work / "renders" / "taslak.jpg"
    ff.contact_sheet(out, sheet, duration=sure, cols=6, rows=4, width=270)
    print(f"Taslak: {paths.rel(out)} · {sure:.1f}s · Kareler: {paths.rel(sheet)}" + (f" · {bas:g}. sn'den" if aralik else ""))
    return out


QC_FPS = 15  # QC videosu: slop 4 fps ölçer, paftalar seçilmiş sabit kareler; kesim tespiti 30 fps ile aynı (ADR 0058)


def qc_taslak(p: Proje) -> Path:
    """Kalite kontrolün videosu: yarım çözünürlük, 15 fps, `renders/qc.mp4`. Kurgu görüntüsü değişmediyse yeniden çizilmez.

    WHY: bkz. wiki/decisions/0058-hizli-ve-kaliteli-edit.md. QC karelere, 4 fps'lik slop ölçümüne ve sese bakar; 30 fps
    taslak aynı bulguyu ~%25 daha uzun sürede verir (arvelior: 100 → 75 sn). Kullanıcıya giden taslak ve final değişmez.
    HyperFrames yapamadığında (Remotion yolu) tam taslak alınır."""
    from . import hf_kurgu
    props = _props(p, "taslak")
    _public_hazirla(p)
    motor, neden = hf_kurgu.motor_sec(p, props, olcek=False)
    if motor != "hf":
        return taslak(p)
    out = p.work / "renders" / "qc.mp4"
    print(f"  Motor: HyperFrames ({neden}) · QC videosu {QC_FPS} fps", flush=True)
    hf_kurgu.render(p, props, out, kalite="draft", olcek=0.5, fps=QC_FPS, crf=23, onbellek=True)
    return out


def miks(p: Proje) -> dict:
    """Görüntü render etmeden ses: son ham.mp4 + güncel kurgu sesleri. Mikser ölçümü buradan gelir."""
    from . import olaysesi
    t0 = time.time()
    ham = p.work / "renders" / "ham.mp4"
    if not ham.exists():
        raise SystemExit("ham.mp4 yok: önce bir kez final al. Konuşma sesi oradan gelir.")
    _props(p)
    olaylar = p.work / "edit" / "olaylar.json"
    if not olaylar.exists():
        raise SystemExit("olaylar.json yok.")
    imza = p.work / "renders" / "ham.imza"
    ayar = p.work / "renders" / "ham.ayar"
    if not imza.exists() or imza.read_text(encoding="utf-8") != ham_imzasi(p, ayar.read_text(encoding="utf-8") if ayar.exists() else ""):
        print("  ! Görüntü ya da konuşma kesimi son finalden sonra değişti: ölçüm eski kesimin konuşmasıyla.")
    spec = json.loads(olaylar.read_text(encoding="utf-8"))
    spec["video"] = "../renders/ham.mp4"
    olaylar.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    r = olaysesi.calistir(olaylar, p.work / "renders" / "sesli.mp4")
    L = r["loudness"]
    print(f"Miks: {L['I']:.1f} LUFS / {L['TP']:.1f} dBTP / LRA {L['LRA']:.1f} · {r['yerlesen']} olay · {time.time() - t0:.0f} sn")
    for u in r["uyarilar"]:
        print(f"  ! {u}")
    return r


def _srt_zaman(t: float) -> str:
    ms = round(t * 1000)
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def sayfala(kelimeler: list[dict], *, en_kelime: int = 3, en_karakter: int = 18) -> list[list[dict]]:
    """Varsayılan ≤3 kelime, ≤18 karakter, cümle sonunda yeni sayfa (SplitReel.tsx buildPages ile aynı)."""
    toks: list[dict] = []
    for w in kelimeler:
        m = w["w"].strip()
        if toks and m[:1] in "'’,":
            toks[-1] = {"w": toks[-1]["w"].rstrip(".,") + m, "s": toks[-1]["s"], "e": w["e"]}
        else:
            toks.append({"w": m, "s": w["s"], "e": w["e"]})
    sayfalar, cur = [], []
    for t in toks:
        if cur and (len(cur) >= en_kelime or len(" ".join(x["w"] for x in cur + [t])) > en_karakter):
            sayfalar.append(cur)
            cur = []
        cur.append(t)
        if t["w"][-1:] in ".!?":
            sayfalar.append(cur)
            cur = []
    if cur:
        sayfalar.append(cur)
    return sayfalar


def srt_yaz(kelimeler: list[dict], stil: dict | None = None) -> str:
    """Props kelimelerinden SRT. Özel altyazı stilinde sayfalar ekrandakiyle aynı kalır."""
    sayfalar = sayfala(kelimeler, en_kelime=stil["en_kelime"], en_karakter=stil["en_karakter"]) if stil else sayfala(kelimeler)
    return "\n".join(f"{i}\n{_srt_zaman(s[0]['s'])} --> {_srt_zaman(s[-1]['e'])}\n{' '.join(x['w'] for x in s)}\n"
                     for i, s in enumerate(sayfalar, 1))


def _json_oku(f: Path) -> dict | None:
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _bos_ad(cikti: Path, ad: str) -> Path:
    """Eski teslimin üzerine yazmaz: ad.mp4, ad-v2.mp4, ad-v3.mp4 …"""
    f, n = cikti / f"{ad}.mp4", 2
    while f.exists():
        f, n = cikti / f"{ad}-v{n}.mp4", n + 1
    return f


def ham_imzasi(p: Proje, ayar: str = "") -> str:
    """Ham render'ı belirleyen her şeyin özeti. Olay sesi dahil değil: ses düzeltmesi görüntüyü yeniden render ettirmez.

    WHY: bkz. wiki/decisions/0020-panel-kaldirildi.md. Klasörlerde boyut + zaman, props'ta içerik.
    """
    h = hashlib.sha1(" ".join(ARA_KODLAMA).encode())
    h.update(ayar.encode())  # ölçek ve fps (ham.ayar); boşsa eski imzalar geçerli kalır
    k = p.work / "edit" / "kurgu.render.json" if kurgu.yol(p.work).exists() else None
    props = k or p.work / "edit" / "props.json"
    h.update(props.read_bytes() if props.exists() else b"-")
    for d in (RC / "src", *([STUDIO / "remotion"] if k else []), p.work / "public", p.girdi):
        for f in sorted(x for x in d.rglob("*") if x.is_file()):
            s = f.stat()
            h.update(f"{f.relative_to(d).as_posix()}|{s.st_size}|{s.st_mtime_ns}".encode())
    return h.hexdigest()


def _render_ayari(props: Path, cozunurluk: int | None, fps: int | None) -> tuple[Path, list[str], str, tuple[int, int]]:
    """(props, motor bayrakları, ham.ayar metni, çıktı boyutu). WHY: bkz. wiki/decisions/0035-teslim-ayarlari.md."""
    from . import teslim
    veri = json.loads(props.read_text(encoding="utf-8"))
    sekans = veri.get("sekans") or {"w": 1080, "h": 1920, "fps": 30}
    w, h = int(sekans["w"]), int(sekans["h"])
    boyut = teslim.hedef_boyut(w, h, cozunurluk)
    ek, ayar = [], []
    if boyut != (w, h):
        # Tam hassasiyet: motor w*ölçek ve h*ölçek tam sayı değilse durur (1.33334 → 2560.0128 reddedildi)
        olcek = cozunurluk / min(w, h)
        if not ((w * olcek).is_integer() and (h * olcek).is_integer()):
            raise SystemExit(f"{w}x{h} sekans {cozunurluk}p'ye tam piksel ölçeklenmiyor. Sekansı 1080x1920 ya da 1920x1080 yap.")
        ek.append(f"--scale={olcek!r}")
        ayar.append(f"olcek={olcek!r}")
    if fps and fps != int(sekans.get("fps") or 30):
        if not props.name.startswith("kurgu.render"):
            raise SystemExit("Kare hızı yalnız kurgu.json projelerinde değişir. Önce `vedit kurgu-al` ile kurguya geç.")
        veri["sekans"] = {**sekans, "fps": fps}
        props = props.with_name("kurgu.render.fps.json")
        props.write_text(json.dumps(veri, ensure_ascii=False), encoding="utf-8")
        ayar.append(f"fps={fps}")
    return props, ek, " ".join(ayar), boyut


def _buyutme_uyarisi(p: Proje, boyut: tuple[int, int]) -> str | None:
    """Kaynak klipler hedeften küçükse görüntü büyütülür; yazı ve grafik gerçek çözünürlükte çizilir."""
    kisa = [min(v["width"], v["height"]) for f in sorted(p.girdi.glob("*.mp4")) if (v := ff.probe(f).get("video"))]
    if kisa and max(kisa) < min(boyut):
        return f"klip görüntüsü %{round(min(boyut) / max(kisa) * 100)} büyütülüyor (kaynak {max(kisa)}p); yazı ve grafik gerçek çözünürlükte"
    return None


def kaynaga_esle(p: Proje) -> tuple[int | None, int | None]:
    """(çözünürlük kademesi, fps): kurgudaki en büyük video kaynağına göre. WHY: ADR 0060 "Kaynağa eşle".

    Kademe kaynağın kısa kenarını aşmaz (büyütme yok); fps yalnız kaynak 50+ ise 60 olur, değilse sekansınki kalır.
    """
    from . import teslim
    if not kurgu.yol(p.work).exists():
        return None, None
    k = kurgu.oku(p.work)
    kisa, hiz = 0, 0.0
    for kay in k.kaynaklar.values():
        try:
            f = kurgu.dosya(p, kay.yol)
        except ValueError:
            continue
        if f.suffix.lower() not in VIDEO or not f.is_file():
            continue
        v = (ff.probe_ob(f).get("video") or {})
        if v and not v.get("alfa"):
            kisa, hiz = max(kisa, min(v["width"], v["height"])), max(hiz, float(v.get("fps") or 0))
    kademe = max((c for c in teslim.COZUNURLUK if c <= kisa), default=None)
    return kademe, (60 if hiz >= 50 else None)


def final(p: Proje, *, platform: str | None = None, ad: str | None = None, metin: str | None = None,
          yenile: bool = False, cozunurluk: int | None = None, kalite: str = "yayin", kodek: str = "h264",
          fps: int | None = None, kaynaga: bool | None = None, vmaf: bool = False) -> Path:
    from . import olaysesi, teslim
    t0 = time.time()
    ham = p.work / "renders" / "ham.mp4"
    imza = p.work / "renders" / "ham.imza"
    ayar_dosya = p.work / "renders" / "ham.ayar"
    # WHY: bkz. wiki/decisions/0060-proxy-master-conform.md. Master: kayıpsız ara render, kaynağa eşle varsayılan.
    master = teslim.KALITE[kalite].get("ara") == "kayipsiz"
    if kaynaga if kaynaga is not None else master:
        k_coz, k_fps = kaynaga_esle(p)
        cozunurluk, fps = cozunurluk or k_coz, fps or k_fps
        print(f"  Kaynağa eşle: {f'{k_coz}p' if k_coz else 'sekans boyutu'}" + (f" · {k_fps} fps" if k_fps else ""), flush=True)
    props = _props(p, "master" if master else "final")
    _public_hazirla(p)
    motor_props, ek, ayar, boyut = _render_ayari(props, cozunurluk, fps)
    ara = ARA_KAYIPSIZ if master else ARA_KODLAMA
    if master:
        ayar = (ayar + " ara=kayipsiz").strip()
    rev = f" rev {kurgu.oku(p.work).rev}" if kurgu.yol(p.work).exists() else ""
    print(f"Export: yapay zekâ kullanılmıyor, kurgu{rev} olduğu gibi render ediliyor.", flush=True)
    if (u := _buyutme_uyarisi(p, boyut)):
        print(f"  ! {u}")
    print(f"1/4 Görüntü render · {boyut[0]}x{boyut[1]}", flush=True)
    if not yenile and ham.exists() and imza.exists() and imza.read_text(encoding="utf-8") == ham_imzasi(p, ayar):
        print("Motor atlandı: görüntü girdileri değişmedi (zorlamak için --yenile).")
    else:
        imza.unlink(missing_ok=True)  # WHY: yarım kalan render geçerli sayılmasın
        _goruntu(p, motor_props, ham, [*ara, *ek], kalite="looks", ilerleme=True)
        ayar_dosya.write_text(ayar, encoding="utf-8")
        imza.write_text(ham_imzasi(p, ayar), encoding="utf-8")
    sure_yaz(p.work, "final:motor", time.time() - t0)
    t0 = time.time()
    print("2/4 Ses miksi", flush=True)
    props_veri = json.loads(props.read_text(encoding="utf-8"))
    kelimeler = props_veri["words"]
    olaylar = p.work / "edit" / "olaylar.json"
    sesli = ham
    if olaylar.exists():
        spec = json.loads(olaylar.read_text(encoding="utf-8"))
        spec["video"] = "../renders/ham.mp4"
        olaylar.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
        sesli = p.work / "renders" / "sesli.mp4"
        r = olaysesi.calistir(olaylar, sesli)
        print(f"Ses: {r['yerlesen']} olay yerleşti")
        for u in r["uyarilar"]:
            print(f"  ! {u}")
    else:
        print("  ! olaylar.json yok: kurgu sesi eklenmedi.")
    sure_yaz(p.work, "final:ses", time.time() - t0)
    t0 = time.time()
    hedef = _bos_ad(p.cikti, ad or p.ad)
    print("3/4 Teslim kodlaması (ffmpeg)", flush=True)
    t = teslim.kodla(sesli, hedef, platform or PLATFORM.get(p.studyo), kodek=kodek, kalite=kalite, beklenen=boyut, vmaf=vmaf)
    sure_yaz(p.work, "final:teslim", time.time() - t0)
    t0 = time.time()
    conform = _json_oku(p.work / "edit" / "conform.json")
    (p.work / "renders" / "kalite.json").write_text(json.dumps(
        {"dosya": hedef.name, "kalite": kalite, "kodek": kodek, "bit": t["bit"], "boyut": t["boyut"], "mbps": t["mbps"],
         "crf": t["crf"], "fps": t["fps"], "ara": "kayipsiz" if master else "hizli", "sadakat": t["sadakat"],
         "conform": conform, "zaman": dt.datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    sd = t["sadakat"]
    print(f"Teslim: {paths.rel(hedef)} · {t['boyut']} · {t['kodek']} · CRF {t['crf']} · {t['bit']}-bit · {t['fps']:g} fps · {t['mbps']} Mbps"
          + (f" · SSIM {sd['ssim']}" if sd.get("ssim") is not None else "") + (f" · VMAF {sd['vmaf']}" if sd.get("vmaf") is not None else ""))
    if conform:
        print(f"  Master conform: {conform.get('master', 0)}/{conform.get('klip', 0)} klip orijinal kaynaktan")
    if master and ham.exists():
        print(f"  Kayıpsız ara render {ham.stat().st_size / 1e9:.2f} GB: work/renders/ham.mp4 (yeniden teslim için önbellek)")
    for u in t["uyarilar"]:
        print(f"  ! {u}")
    if kelimeler:
        hedef.with_suffix(".srt").write_text(srt_yaz(kelimeler, (props_veri.get("altyazi") or {}).get("stil")), encoding="utf-8")
    ff.still(hedef, hedef.with_suffix(".jpg"), 1.0)
    atif_yaz(p)
    print("4/4 Denetim (ölçüm)", flush=True)
    denetim(hedef, olaylar=olaylar if olaylar.exists() else None, metin=Path(metin) if metin else p.girdi / "senaryo.md" if (p.girdi / "senaryo.md").exists() else None,
            work=p.work)
    sure_yaz(p.work, "final:denetim", time.time() - t0)
    return hedef


ATIF_BASLIK = "## Atıflar (kullanılan varlıkların lisansı gereği)"


def atif_yaz(p: Proje) -> list[str]:
    """Atıf isteyen dış varlık kullanıldıysa yayin.md'ye atıf bölümünü yazar ya da günceller (ADR 0046)."""
    from . import motion_ice
    if not kurgu.yol(p.work).exists():
        return []
    satir = motion_ice.atif_satirlari(kurgu.oku(p.work))
    f = p.cikti / "yayin.md"
    eski = f.read_text(encoding="utf-8") if f.exists() else ""
    govde = eski.split(ATIF_BASLIK)[0].rstrip()
    if not satir:
        if ATIF_BASLIK in eski:
            f.write_text(govde + "\n", encoding="utf-8")
        return []
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text((govde + "\n\n" if govde else "") + ATIF_BASLIK + "\n" + "\n".join(f"- {s}" for s in satir) + "\n", encoding="utf-8")
    print(f"  yayin.md: {len(satir)} atıf satırı (lisans gereği açıklamaya ekle)")
    return satir


def denetim(video: Path, *, olaylar: Path | None = None, metin: Path | None = None, work: Path | None = None,
            dil: str = "tr") -> dict:
    """Tek tablo: format, loudness, kesimqa, slop. Yorum yok; hüküm `denetim` skill'inde."""
    from . import kesimqa, slop
    work = work or work_bul([str(video)]) or video.parent
    qa = work / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    info, L = ff.probe(video), ff.loudness(video)
    v = info["video"]
    sheet = qa / f"{video.stem}.jpg"
    ff.contact_sheet(video, sheet, duration=info["duration"], cols=6, rows=4, width=270)
    s = slop.calistir(video, qa, olaylar=olaylar, metin=metin, yazisiz=metin is None, dil=dil, lra=L.get("LRA"))
    k = None
    if metin:
        k = kesimqa.calistir(video, kesimqa.metinden(metin), dil=dil)
        kesimqa.yaz(k, qa / "kesimqa.json")
    # WHY: ses akışı olmayan videolarda ff.loudness {} döner; KeyError ile denetim çökmesin.
    yuk = (-15.0 <= L["I"] <= -13.0 and L["TP"] <= -1.0) if "I" in L and "TP" in L else None
    (qa / "denetim.json").write_text(json.dumps({
        "video": video.name, "format": {"w": v["width"], "h": v["height"], "fps": v["fps"], "sure": info["duration"]},
        "loudness": L, "ses_tamam": yuk, "kesim": {"benzerlik": k["benzerlik"], "eksik": len(k["eksik"]), "fazla": len(k["fazla"])} if k else None,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"| Format | {v['width']}x{v['height']}@{v['fps']:g} · {info['duration']:.1f}s |")
    ses_satiri = f"{L['I']:.1f} LUFS / {L['TP']:.1f} dBTP / LRA {L.get('LRA', 0.0):.1f} · {'tamam' if yuk else 'EŞİK DIŞI'}" if yuk is not None else "ses akışı yok"
    print(f"| Ses | {ses_satiri} |")
    if k:
        print(f"| Kesim | benzerlik {k['benzerlik']} · eksik {len(k['eksik'])} · fazla {len(k['fazla'])} |")
    print(f"| Slop | {len(s['bulgular'])} şüphe: " + ", ".join(sorted({f"{b['seviye']} {b['kod']}" for b in s['bulgular']})) + " |")
    print(f"| Dosyalar | {paths.rel(sheet)} · {paths.rel(qa / 'slop-olcum.json')} |")
    return {"format": v, "loudness": L, "kesim": k, "slop": s}


def kaizen(p: Proje, *, yaz: bool = True) -> str:
    f = p.work / "sure.jsonl"
    if not f.exists():
        raise SystemExit("Süre kaydı yok: önce vedit komutları çalışmalı.")
    kayit = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]
    top: dict[str, list[float]] = {}
    alt: dict[str, float] = {}
    for k in kayit:
        if ":" in k["komut"]:  # final:motor gibi alt adımlar `final` toplamının içindedir, iki kez sayılmaz
            alt[k["komut"]] = alt.get(k["komut"], 0) + k["sn"]
        else:
            top.setdefault(k["komut"], []).append(k["sn"])
    sira =sorted(top.items(), key=lambda kv: -sum(kv[1]))
    toplam = sum(sum(v) for v in top.values()) / 60
    enyavas = " · ".join(f"{k} {sum(v) / 60:.1f} dk" for k, v in sira[:3])
    satir = (f"- {dt.date.today().isoformat()} · {p.ad} · araç {toplam:.1f} dk · taslak {len(top.get('taslak', []))} · "
             f"final {len(top.get('final', []))} · en yavaş: {enyavas}")
    # Ekip koşusu varsa en yavaş kapısı (ADR 0054): ai-edit'in içindeki darboğaz görünsün.
    oz = p.work / "edit" / "ekip" / "ozet.json"
    if oz.exists():
        try:
            ks = {k: v for k, v in (json.loads(oz.read_text(encoding="utf-8")).get("kapi_sure") or {}).items() if v}
        except ValueError:
            ks = {}
        if ks:
            k = max(ks, key=ks.get)
            satir += f" · ekip en yavaş kapı: {k} {ks[k] / 60:.1f} dk"
    for k, v in sira:
        print(f"{k:12} {len(v):3}x  {sum(v) / 60:6.1f} dk")
    for k, sn in sorted(alt.items(), key=lambda kv: -kv[1]):
        print(f"  {k:14}  {sn / 60:6.1f} dk")
    print(satir)
    if not (p.cikti / "yayin.md").exists():
        print(f"! yayin.md yok: teslimden önce `vedit yayin {p.studyo}/{p.ad} --hepsi` ya da Stüdyo Teslim > Yayın metni (ADR 0055).")
    if yaz and (not KAIZEN.exists() or satir not in KAIZEN.read_text(encoding="utf-8")):
        with KAIZEN.open("a", encoding="utf-8") as h:
            h.write(satir + "\n")
    return satir


def duzen() -> list[str]:
    """6S kontrolü: Projeler/ dışında proje medyası, emekli skill bağı, uzun SKILL.md."""
    sorun, uyari = [], []
    atla = {".git", ".venv", "node_modules", "library", "Projeler", "graphify-out", "raw", "openmontage", "__pycache__"}
    tara = [d for d in paths.ROOT.iterdir() if d.is_dir() and d.name not in atla]
    for yer in ("openmontage/projects", "openmontage/remotion-composer/public"):
        tara.append(paths.ROOT / yer)
    for d in tara:
        for kok, altlar, adlar in os.walk(d):
            altlar[:] = [a for a in altlar if a not in ("node_modules", ".venv", "__pycache__")]  # WHY: rglob on binlerce dosyayı boşuna geziyordu
            sorun += [f"yanlış yerde: {paths.rel(Path(kok) / ad)}" for ad in adlar if Path(ad).suffix.lower() in MEDYA]
    for f in (paths.ROOT / "openmontage/remotion-composer/public").rglob("*") if (paths.ROOT / "openmontage/remotion-composer/public").exists() else []:
        if f.is_file() and f.suffix.lower() in GORSEL and "demo-props" not in f.parts:
            sorun.append(f"yanlış yerde: {paths.rel(f)}")
    for f in (paths.ROOT / ".claude").rglob("*.md"):
        t = f.read_text(encoding="utf-8", errors="ignore")
        for ad in ("render-qa", "ai-slop-denetimi", "uretim.json", "server.mjs", "sunucu.mjs", "baslat.bat", "efekt-katmani", "katman.json",
                   "hyperframes-core", "hyperframes-animation", "hyperframes-keyframes", "hyperframes-creative"):
            if ad in t:
                sorun.append(f"emekli bağ `{ad}`: {paths.rel(f)}")
        if f.name == "SKILL.md" and t.count("\n") > 150:
            uyari.append(f"uzun ({t.count(chr(10))} satır): {paths.rel(f)}")
    for s in sorun:
        print("✗", s)
    for u in uyari:
        print("!", u)
    print("Düzen temiz." if not sorun else f"{len(sorun)} sorun.")
    return sorun
