"""vedit — AI Video Editor pipeline CLI (LLM'siz katman).

Her komut kompakt bir özet basar; ajanlar dosyaları değil bu çıktıları okur.
Örnek: vedit new ugc "Kahve makinesi tanıtım" → vedit status → vedit ingest -p kahve …
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import motorlar, paths, project


def _root(args) -> Path:
    return paths.find_project(getattr(args, "project", None))


def _print_json(d) -> None:
    print(json.dumps(d, ensure_ascii=False, indent=1))


def cmd_new(a):
    root = project.create(a.studio, a.title, pipeline=a.pipeline, language=a.lang)
    print(f"Proje oluşturuldu: {paths.rel(root)}")
    print(f"Dosyaları buraya koy: {paths.rel(paths.input_dir(root))}")
    print(project.status_text(root))


def cmd_status(a):
    print(project.status_text(_root(a)))


def cmd_mark(a):
    root = _root(a)
    gate = "approved" if a.approve else ("skipped" if a.skip else None)
    project.mark(root, a.step, gate=gate)
    print(project.status_text(root))


def cmd_ingest(a):
    from . import ingest
    root = _root(a)
    idx = ingest.run(root)
    project.mark(root, "ingest")
    print(ingest.summary(idx))
    print("Kontak sayfaları: analysis/sheets/*.jpg")


def cmd_transcribe(a):
    from . import transcribe
    root = _root(a)
    proj = project.load(root)
    lang = a.lang or proj.language
    res = transcribe.run(root, language=None if lang == "auto" else lang, model_name=a.model,
                         files=a.files, prompt=a.prompt, force=a.force)
    project.mark(root, "transcribe")
    for k, v in res["files"].items():
        n = sum(len(s["words"]) for s in v["segments"])
        print(f"- {k}: {v['language']} · {v['duration']:.1f}s · {len(v['segments'])} segment · {n} kelime")


def cmd_digest(a):
    from . import digest
    root = _root(a)
    out, tokens = digest.run(root)
    project.mark(root, "digest")
    print(f"Digest: {paths.rel(out)} (~{tokens} token)")


def cmd_cut(a):
    from . import cut
    root = _root(a)
    proj = project.load(root)
    res = cut.run(root, fps=proj.format.fps)
    project.mark(root, "cut")
    print(f"A-roll: {res['aroll']} · {res['duration']:.2f}s · {res['segments']} segment · "
          f"zaman eşlemesi edit/timemap.json · kesilmiş transkript build/transcript_cut.json")


def cmd_reframe(a):
    from . import reframe
    root = _root(a)
    proj = project.load(root)
    w, h = (int(x) for x in (a.size or f"{proj.format.width}x{proj.format.height}").split("x"))
    out = reframe.run(root, a.src, w, h)
    d = json.loads(out.read_text(encoding="utf-8"))
    print(f"Reframe yolu: {paths.rel(out)} · {d['faces']}/{d['samples']} örnekte yüz · {len(d['path'])} nokta")
    print(f'timeline.json video klibine ekle: "reframe": "build/{out.name}"')


def cmd_audio(a):
    from . import audio
    root = _root(a)
    proj = project.load(root)
    src = paths.pj(root, a.src or ("input/vo.wav" if proj.pipeline == "animation" else "build/aroll.mp4"))
    out = audio.clean_voice(src, root / "build" / "voice.wav", denoise=a.denoise, eq=not a.no_eq)
    project.mark(root, "audio")
    from . import ff
    print(f"Temiz konuşma: {paths.rel(out)} · ham loudness {ff.loudness(out).get('I', '?')} LUFS (master'da -14'e çekilir)")


def cmd_captions(a):
    from . import captions
    root = _root(a)
    proj = project.load(root)
    cfg = project.studio_for(proj).captions
    res = captions.run(root, pipeline=proj.pipeline, cfg=cfg, style=a.style)
    project.mark(root, "captions")
    print(f"Altyazı: edit/captions.json · {res['pages']} sayfa · stil {res['style']} · SRT {res['srt']}")


def cmd_align(a):
    from . import align
    root = _root(a)
    res = align.align(root)
    project.mark(root, "align")
    print(f"Hizalandı: {res['scenes']} sahne · {res['duration']}s → direction/scenes.aligned.json")
    for w in res["warnings"]:
        print(f"  ! {w}")


def cmd_scenes2timeline(a):
    from . import align
    root = _root(a)
    proj = project.load(root)
    cfg = project.studio_for(proj).captions
    res = align.scenes2timeline(root, proj.format, burn_captions=cfg.burn, caption_style=cfg.style)
    print(f"timeline.json: {res['overlays']} overlay · {res['chapters']} bölüm · {res['duration']}s")
    if res["placeholders"]:
        print(f"  ! editor (hero) yazmalı (edit/custom/<id>.html): {', '.join(res['placeholders'])}")


def cmd_validate(a):
    from . import blocks as blk
    from .schemas import Edl, Scenes, Timeline, load_json
    root = _root(a)
    problems = []
    for rel_, model in (("edit/edl.json", Edl), ("direction/scenes.json", Scenes), ("edit/timeline.json", Timeline)):
        p = root / rel_
        if p.exists():
            try:
                obj = load_json(p, model)
                print(f"✓ {rel_}")
                if model is Timeline:
                    cat = blk.load_all([root / "edit" / "blocks"])
                    for o in obj.overlays:
                        if o.block == "custom":
                            if not o.src or not paths.pj(root, o.src).exists():
                                problems.append(f"{o.id}: custom src yok ({o.src})")
                        elif o.block not in cat:
                            problems.append(f"{o.id}: bilinmeyen blok {o.block}")
                        else:
                            problems += [f"{o.id}: {e}" for e in blk.validate_props(cat[o.block], o.props)]
                    for c in obj.video:
                        if not paths.pj(root, c.src).exists() and not (paths.ROOT / c.src).exists():
                            problems.append(f"{c.id}: dosya yok {c.src}")
            except Exception as e:
                problems.append(f"{rel_}: {str(e)[:600]}")
    for pr in problems:
        print(f"✗ {pr}")
    sys.exit(1 if problems else 0)


def cmd_build(a):
    from . import build
    root = _root(a)
    res = build.run(root)
    project.mark(root, "build")
    lint = res.get("lint", {})
    print(f"Kompozisyon: {res['comp']}/index.html · bölüm: {len(res['chapters'])} · lint: "
          f"{lint.get('errors', '?')} hata / {lint.get('warnings', '?')} uyarı")
    for t in lint.get("top", []):
        print(f"  - {t}")
    for e in res["errors"]:
        print(f"  ! {e}")


def cmd_render(a):
    from . import render
    root = _root(a)
    proj = project.load(root)
    res = render.run(root, mode=a.mode, fps=proj.format.fps, parallel=a.parallel)
    project.mark(root, "preview" if a.mode == "preview" else "final")
    extra = f" · bölüm {res['rendered']} render / {res['reused']} önbellek" if res.get("chapters") else ""
    print(f"Render: {res['out']} · {res['seconds']}s{extra}")


def cmd_qa(a):
    from . import qa
    root = _root(a)
    rep = qa.run(root, video=Path(a.video) if a.video else None)
    project.mark(root, "qa")
    print(qa.summary(rep))


def cmd_export(a):
    from . import export
    root = _root(a)
    res = export.run(root, variants=a.variants)
    project.mark(root, "export")
    _print_json(res)


def cmd_mix(a):
    from . import audio
    root = _root(a)
    res = audio.mix(root, duck_db=a.duck_db)
    project.mark(root, "mix")
    L = res["loudness"]
    print(f"Master: {res['master']} · {res['duration']}s · müzik {res['music']} · SFX {res['sfx']} · "
          f"{L.get('I', '?')} LUFS / {L.get('TP', '?')} dBTP")


def cmd_sfx(a):
    from . import sfx
    if a.action == "index":
        _print_json(sfx.index(rescan=a.rescan))
    elif a.action == "fetch":
        prov = a.args[0] if a.args else "kenney"
        if prov == "kenney":
            print("\n".join(sfx.fetch_kenney(a.args[1:] or None)))
        elif prov == "remotion":
            print("Remotion CC0:", ", ".join(sfx.fetch_remotion()))
        elif prov == "wyzowl":
            print(f"Wyzowl CC0: {len(sfx.fetch_wyzowl())} dosya → library/sfx/raw/wyzowl/")
        elif prov in ("freesound", "openverse"):
            q = " ".join(a.args[1:]) or a.query
            if not q:
                raise SystemExit("Arama ifadesi ver: vedit sfx fetch freesound phone ring")
            got = (sfx.fetch_freesound if prov == "freesound" else sfx.fetch_openverse)(q, a.n)
            print(f"{prov}: {len(got)} dosya → library/sfx/raw/{prov}/")
        else:
            raise SystemExit("Sağlayıcı: kenney | remotion | wyzowl | freesound | openverse")
        print("Şimdi: vedit sfx index")
    elif a.action == "synth":
        print(f"{sfx.synth(variants=a.n or 3, only=a.args or None)} ses üretildi → library/sfx/raw/synth/ (vedit sfx index)")
    elif a.action == "search":
        for e in sfx.search(" ".join(a.args), limit=a.n or 12):
            print(f"- {e.id} · {e.category} · {e.duration_s:.2f}s · peak {e.peak_offset_s:.3f}s · {','.join(e.tags[:6])} · {e.license}")
    elif a.action == "catalog":
        print(sfx.catalog_text())
    elif a.action == "cues":
        root = _root(a)
        print(sfx.auto_cues(root))
    elif a.action == "suggest":
        root = _root(a)
        from . import captions as cap
        proj = project.load(root)
        lines = sfx.suggest(root, cap.source_words(root, proj.pipeline))
        (root / "audio").mkdir(exist_ok=True)
        (root / "audio" / "sfx_suggestions.txt").write_text("\n".join(lines), encoding="utf-8")
        print("\n".join(lines) or "Öneri yok.")
    elif a.action == "resolve":
        root = _root(a)
        res = sfx.resolve(root)
        project.mark(root, "sfx")
        print(f"SFX: {res['resolved']}/{res['cues']} çözüldü → audio/sfx_resolved.json")
        for m in res["missing"]:
            print(f"  ! eşleşme yok: {m}")
    else:
        raise SystemExit("sfx eylemleri: index | fetch | synth | search | catalog | cues | suggest | resolve")


def cmd_olaysesi(a):
    from . import olaysesi
    r = olaysesi.calistir(Path(a.olaylar), a.output, duck_db=a.duck_db, min_aralik=a.min_aralik)
    L = r["loudness"]
    print(f"Sesli video: {r['cikti']} · {r['yerlesen']} ses {r['adet']} · {L.get('I', '?')} LUFS / {L.get('TP', '?')} dBTP")
    for u in r["uyarilar"]:
        print(f"  ! {u}")


def cmd_teslim(a):
    from . import teslim
    r = teslim.kodla(Path(a.video), Path(a.output) if a.output else None, a.platform, kodek=a.kodek, kalite=a.kalite,
                     kapak=Path(a.kapak_kare) if a.kapak_kare else None)
    print(f"Teslim: {r['cikti']} · {r['boyut']} · {r['mbps']} Mbps · girdi {r['once']} → yuv420p/tv/bt709")
    for u in r["uyarilar"]:
        print(f"  ! {u}")


def cmd_loop(a):
    from . import loop
    for f in a.dosyalar:
        f = Path(f)
        if a.action == "kontrol":
            print(f"{f.name}: {loop.olc(f)}")
        elif a.action == "muhur":
            dst = Path(a.output) if a.output and len(a.dosyalar) == 1 else f.with_name(f"{f.stem}.loop.mp4")
            r = loop.muhurle(f, dst, mod=a.mod, capraz=a.capraz, sure=a.sure)
            durum = "temiz" if r["sonra"]["temiz"] else "SARMA GÖRÜNÜR: yeniden üret ya da --mod capraz dene"
            print(f"{dst.name}: {r['mod']} · sarma {r['once']['sarma']} → {r['sonra']['sarma']} (medyan {r['sonra']['medyan']}) · {durum}")
        else:
            raise SystemExit("loop eylemleri: kontrol | muhur")


def cmd_reference(a):
    from . import reference
    if a.project:
        out = _root(a) / "analysis" / "reference"
    elif a.studio:
        paths.studio_dir(a.studio)
        out = paths.REFERENCES / a.studio / "analysis"
    else:
        raise SystemExit("--project ya da --studio ver")
    res = reference.run(out, a.urls, [Path(i) for i in a.images or []], minutes=a.minutes)
    print((out / "digest.md").read_text(encoding="utf-8"))
    if res["errors"]:
        sys.exit(1)


def cmd_blocks(a):
    from . import blocks as blk
    print(blk.catalog(a.tag))


def cmd_pano(a):
    from . import pano
    html, out = Path(a.html), Path(a.out)
    css = Path(a.css) if a.css else None
    if a.tema:
        # WHY: bkz. wiki/decisions/0043-stile-bagli-tema-tokenlari.md. Panolar vendor koddur; iç renkleri yerine
        # .ebs değişkenleri stilin token'ıyla ezilir (giriş katmanı). Ek --css varsa ondan sonra gelir.
        from . import motion, tema_token
        t = tema_token.oku(a.tema) or tema_token.oku(motion.tema_yolu(a.tema))
        if not t:
            raise SystemExit(f"Tema yok: {a.tema}")
        gecici = out.parent / f".{out.stem}.tema.css"
        out.parent.mkdir(parents=True, exist_ok=True)
        gecici.write_text(tema_token.pano_css(t) + (css.read_text(encoding="utf-8") if css else ""), encoding="utf-8")
        css = gecici
    n = pano.render(html, out, sure=a.sure, w=a.w, h=a.h, fps=a.fps, css=css)
    if a.tema:
        css.unlink(missing_ok=True)
    print(f"Pano: {out} · {n} kare · {a.sure}s")


def _motion_ice_al(a):
    # WHY: bkz. wiki/decisions/0046-dis-varlik-ve-lisans.md. Lisans kaydı olmayan varlık reddedilir (çıkış kodu 2).
    from . import motion_ice
    if not a.kimlik:
        raise SystemExit("Dosya ya da klasör gerekli: vedit motion ice-al <yol> --kaynak mixkit")
    yol = Path(a.kimlik[0])
    kaynak = a.kaynak or (yol.name if yol.is_dir() else yol.parent.name)
    dosyalar = sorted(f for f in yol.iterdir() if f.is_file() and not f.name.startswith(".")) if yol.is_dir() else [yol]
    if a.anahtar_dene:
        for f in dosyalar:
            for k in motion_ice.anahtar_dene(f, paths.ROOT / "work" / "motion-ice" / f.stem):
                print(f"  {paths.rel(k)}")
        return
    try:
        lisans = motion_ice.lisans_kur(kaynak, url=a.url, lisans=a.lisans, atif_gerekli=True if a.atif_gerekli else None,
                                       atif_metni=a.atif_metni or "", kisitlar=a.kisit or None)
    except motion_ice.LisansHatasi as e:
        print(f"Reddedildi: {e}")
        raise SystemExit(2)
    tamam, hata = 0, 0
    for f in dosyalar:
        try:
            e = motion_ice.ice_al(f, lisans, ad=a.ad if len(dosyalar) == 1 else None, tur=a.tur, etiketler=a.etiket or [],
                                  ne_zaman=a.ne_zaman or "", yontem=a.yontem, benzerlik=a.benzerlik)
            print(f"  {e['id']}: {e['alfa_yontemi']} · {e['kind']} · {e['license']}" + (" · atıf gerekli" if e["atif_gerekli"] else ""))
            tamam += 1
        except (motion_ice.LisansHatasi, ValueError, subprocess.CalledProcessError) as er:
            print(f"  ! {f.name}: {er}")
            hata += 1
    motion_ice.manifest_yenile()
    print(f"İçe aktarma: {tamam} varlık, {hata} hata · library/motion/manifest.json güncellendi")
    if hata and not tamam:
        raise SystemExit(1)


def cmd_hf_guncelle(a):
    """HyperFrames güncellemesi (ADR 0051): kontrol, aday + duman testi + sabitleme, geri alma."""
    from . import hf_guncel
    if a.geri:
        d = hf_guncel.geri()
    elif a.duman:
        sonuc = hf_guncel.duman()
        for s in sonuc:
            print(f"  {'✓' if s['gecti'] else '✗'} {s['ad']}" + (f"  fark {s['fark']}" if "fark" in s else "")
                  + ("" if s["gecti"] else "  " + "; ".join(s["sorun"])))
        raise SystemExit(0 if all(s["gecti"] for s in sonuc) else 1)
    elif a.kontrol:
        d = hf_guncel.kontrol(zorla=True)
    else:
        # elle: çalışan iş varsa sabitlemez, bildirir; Görev Zamanlayıcı `--bekle` ile iş bitene kadar bekler
        d = hf_guncel.kur(a.surum, skill=not a.skill_yok, bekle=a.bekle * 60)
    print(json.dumps(d, ensure_ascii=False, indent=1))


def cmd_hf(a):
    """HyperFrames grafikleri (ADR 0050): liste ya da tek kompozisyonu saydam webm'e üret."""
    from . import hf_grafik, hizli, kurgu
    p = hizli.bul(a.ref) if a.ref else None
    work = p.work if p else None
    if a.is_ == "liste":
        for ad in hf_grafik.adlar(work):
            print(f"  {ad}  ({paths.rel(hf_grafik.bul(ad, work))})")
        return
    if not a.ad:
        raise SystemExit("kur için --ad ver")
    param = json.loads(a.param) if a.param else None
    tema = kurgu.etkin_tema(p, a.tema) if p else (a.tema or "varsayilan")
    hedef = Path(a.cikti).resolve() if a.cikti else (work / "public" / "motion" if work else paths.ROOT / "work" / "hf")
    f, bilgi = hf_grafik.uret(a.ad, param, tema, work or paths.ROOT / "work", hedef)
    print(f"{paths.rel(f)}  {bilgi['w']}x{bilgi['h']} {bilgi['sure']} sn")


def cmd_motion(a):
    from . import motion
    if a.is_ == "ice-al":
        _motion_ice_al(a)
        return
    if a.is_ == "kontak":
        # WHY: bkz. wiki/decisions/0045-native-motion.md. Native bileşen galerisi: dama zemin (alfa) ve gerçek kare (okunurluk).
        from . import native_motion
        dosyalar = native_motion.kontak(a.kimlik or None, Path(a.cikti).resolve(), tema=a.tema, kare=Path(a.kare) if a.kare else None)
        for f in dosyalar:
            print(f"  {paths.rel(f)}")
        return
    if a.is_ == "olc":
        sonuc = motion.olc(a.kimlik or None)
        for k, kusur in sonuc:
            if kusur:
                print(f"  {k}: " + "; ".join(kusur))
        kotu = sum(1 for _, kusur in sonuc if kusur)
        print(f"Motion ölçüm: {len(sonuc) - kotu} temiz, {kotu} kusurlu")
        raise SystemExit(1 if kotu else 0)
    n = motion.kur(a.kimlik or None, yalniz_manifest=a.manifest, manifest=not a.onizle)
    print(f"Motion: {len(n)} kayıt" + ("" if a.onizle else " · library/motion/manifest.json güncellendi"))


def cmd_gorsel(a):
    from . import gorsel
    out = gorsel.uret(a.prompt, Path(a.out), oran=a.oran)
    print(f"Görsel: {out}")


def cmd_kesimqa(a):
    from . import captions, kesimqa
    video = Path(a.video)
    kesimler = None
    if a.beklenen:
        beklenen, rapor = kesimqa.metinden(Path(a.beklenen)), video.with_suffix(".kesimqa.json")
        dil = a.dil
    else:
        root = _root(a)
        proj = project.load(root)
        beklenen, rapor = captions.source_words(root, proj.pipeline), root / "qa" / "kesimqa.json"
        dil = a.dil or proj.language
        tm = root / "edit" / "timemap.json"
        if tm.exists():
            kesimler = [s["start"] for s in json.loads(tm.read_text(encoding="utf-8"))["segments"]][1:]
    rep = kesimqa.calistir(video, beklenen, dil=dil, kesimler=kesimler)
    kesimqa.yaz(rep, rapor)
    print(f"Benzerlik {rep['benzerlik']} · eksik {len(rep['eksik'])} · fazla {len(rep['fazla'])} · rapor: {rapor}")
    for ad in ("eksik", "fazla"):
        for r in rep[ad][:15]:
            print(f"  {ad}: {r['kelime']}" + (f" @ {r['t']:.2f}s" if r["t"] is not None else "")
                  + (" (kesim kenarı)" if r["kesim_kenari"] else ""))


def cmd_slop(a):
    from . import slop
    video = Path(a.video)
    cikti = Path(a.cikti) if a.cikti else (video.parent.parent / "qa" if video.parent.name == "renders" else video.parent)
    rep = slop.calistir(video, cikti, olaylar=Path(a.olaylar) if a.olaylar else None,
                        metin=Path(a.metin) if a.metin else None, yazisiz=a.yazisiz, dil=a.dil)
    b = rep["bulgular"]
    print(f"Slop ölçümü: {rep['sure']}s · {rep['plan']} plan · {len(b)} şüphe · metin: {rep['metin_kaynagi']}")
    for x in b[:25]:
        zaman = "tümü" if x["bas"] is None else f"{x['bas']:.1f}–{x['bit']:.1f}s"
        print(f"  {x['seviye']} {zaman} {x['kod']}: {x['kanit']}")
    print(f"Rapor: {cikti / 'slop-olcum.json'} · Kareler: {rep['kareler']}")


def cmd_hazirla(a):
    from . import hizli
    hizli.hazirla(hizli.bul(a.ref), dil=a.dil, prompt=a.prompt, ek=a.ek)


def cmd_kes(a):
    from . import hizli
    hizli.kes(hizli.bul(a.ref))


def cmd_taslak(a):
    from . import hizli
    hizli.taslak(hizli.bul(a.ref), aralik=a.aralik)


def _teslim_ayari(a) -> dict:
    return {"cozunurluk": a.cozunurluk, "kalite": a.kalite, "kodek": a.kodek, "fps": a.fps}


def _teslim_bayraklari(sp) -> None:
    from . import teslim
    sp.add_argument("--cozunurluk", type=int, choices=list(teslim.COZUNURLUK), help="kısa kenar: 720 HD, 1080 FHD, 1440 QHD (2K), 2160 UHD (4K); yoksa sekans boyutu")
    sp.add_argument("--kalite", default="yayin", choices=list(teslim.KALITE), help="CRF kademesi (H.264: 14 / 16 / 20)")
    sp.add_argument("--kodek", default="h264", choices=list(teslim.KODEK))
    sp.add_argument("--fps", type=int, choices=list(teslim.FPS), help="yoksa sekans kare hızı")


def cmd_final(a):
    from . import hizli
    hizli.final(hizli.bul(a.ref), platform=a.platform, ad=a.ad, metin=a.metin, yenile=a.yenile, **_teslim_ayari(a))


def cmd_ai_edit(a):
    from . import aiedit, hizli
    if a.ekip:
        # WHY: bkz. wiki/decisions/0053-seviyeli-ekip-orkestrator.md. --ekip yoksa tek ajan akışı aynen çalışır.
        from . import ekip
        p = hizli.bul(a.ref)
        ayar = ekip.ayar_yukle(p, Path(a.ekip_dosyasi) if a.ekip_dosyasi else None, ekip_seviye=a.seviye,
                               motion=a.motion if a.motion != "yogun" else None, stil=a.stil)
        if a.sifirdan:
            from . import kurgu
            f = kurgu.yol(p.work)
            if f.exists():  # güncel sürüm geçmişe kopyalanır; Stüdyo'dan geri alınabilir
                g = p.work / "edit" / "kurgu-gecmis"
                g.mkdir(parents=True, exist_ok=True)
                (g / f"{kurgu.oku(p.work).rev:06d}-sifirdan.json").write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
                f.unlink()
        final_ek = {"platform": a.platform, "ad": a.ad, "yenile": a.yenile, **_teslim_ayari(a)}
        # Kapılı akış: plan, paralel düzen, kural kapısı, birleştirme, QC, triyaj ve kural, düzeltme, son.
        from . import ekip_v3
        o = ekip_v3.calistir(p, ayar, notu=a.notu, tekrar_denetle=a.tekrar_denetle)
        print(f"Ekip v3 ({o['seviye']}): {o['sure_sn']} sn · rapor work/edit/ai-edit.rapor.md")
        if a.final:
            if any(b["onem"] == "P0" for b in o["bulgular"]) or o["son_denetim"]["hata"]:
                print("  ! Açık P0 bulgusu ya da denetim hatası var: teslim kullanıcı kararı (ADR 0015). --final atlandı.")
            else:
                hizli.final(p, **final_ek)
        return
    aiedit.calistir(hizli.bul(a.ref), motor=a.motor, model=a.model, stil=a.stil, notu=a.notu, final=a.final, motion_seviye=a.motion,
                    aralik=tuple(a.aralik) if a.aralik else None,
                    final_ek={"platform": a.platform, "ad": a.ad, "yenile": a.yenile, **_teslim_ayari(a)})


def cmd_stil_uret(a):
    from . import stil
    stil.uret(a.studyo, a.ad, motor=a.motor, model=a.model)


def cmd_stil_katalog(a):
    from . import hizli, stil_katalog
    if a.eylem == "liste":
        for e in stil_katalog.liste():
            print(f"{e['kategori']:<14} {e['id']:<26} {e['ad']}  (tema {e['motion_tema']})")
    elif a.eylem == "kur":
        stil_katalog.kur(a.kimlik or None, onizleme=not a.onizlemesiz)
    elif a.eylem == "kart":
        from . import stil_kart  # WHY: ADR 0043, sabit örnek setle stil kartı ve taşma/kontrast ölçümü
        kotu = [o["stil"] for o in stil_kart.kur(a.kimlik or None) if o["tasma"] or o["kontrast"]]
        if kotu:
            raise SystemExit(f"Kartta sorun: {', '.join(kotu)} (kart.json)")
    else:
        if not a.studyo or len(a.kimlik) != 1:
            raise SystemExit("ekle: --studyo <stüdyo> ve tek stil kimliği gerekir")
        p = hizli.bul(a.proje) if a.proje else None
        print(f"Eklendi: {paths.rel(stil_katalog.ekle(a.studyo, a.kimlik[0], p))}")


def cmd_stil_varlik(a):
    import shutil
    from . import stil_varlik
    if a.eylem == "liste":
        depo = stil_varlik.oku(a.studyo, a.ad)
        if a.json:
            _print_json(depo.model_dump())
            return
        for v in depo.yuklenenler:
            if a.tur and v.tur != a.tur:
                continue
            print(f"{v.id:<22} {v.tur:<11} {v.yontem:<13} {v.dosya} ({v.ad})")
        print(f"Toplam: {len(depo.yuklenenler)} varlık · seçili native {len(depo.secili_native)} · yalnız bunlar: {depo.yalniz_bunlar}")
    elif a.eylem == "ekle":
        if not a.hedef:
            raise SystemExit("Dosya yolu gerekli: vedit stil-varlik ekle <stüdyo> <stil> <dosya> --tur motion")
        v = stil_varlik.yukle(
            a.studyo,
            a.ad,
            Path(a.hedef),
            tur=a.tur or "motion",
            baslik=a.baslik or "",
            ne_zaman=a.ne_zaman or "",
            etiketler=a.etiket or [],
            yontem=a.yontem,
            lisans=a.lisans or "Kendi üretimim",
            kaynak_url=a.url or "",
            atif=a.atif or "",
        )
        print(f"Eklendi: {v.id} ({v.tur}, {v.yontem}) → {stil_varlik.kurgu_yolu(a.studyo, a.ad, v.dosya)}")
    elif a.eylem == "sil":
        if not a.hedef:
            raise SystemExit("Varlık kimliği gerekli: vedit stil-varlik sil <stüdyo> <stil> <id>")
        v = stil_varlik.sil(a.studyo, a.ad, a.hedef)
        print(f"Silindi: {v.id} ({v.dosya})")
    elif a.eylem == "indir":
        if not a.hedef:
            raise SystemExit("Bileşen adı gerekli: vedit stil-varlik indir <stüdyo> <stil> <bileşen>")
        param = json.loads(a.param) if a.param else None
        cikti = stil_varlik.native_disa_aktar(a.studyo, a.ad, a.hedef, param=param, en_boy=a.en_boy, sure=a.sure)
        if a.out:
            hedef = Path(a.out)
            hedef.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cikti, hedef)
            cikti = hedef
        print(f"İndirildi: {paths.rel(cikti) if cikti.is_relative_to(paths.ROOT) else cikti}")


def cmd_stil_paket(a):
    from . import stil_varlik
    if a.eylem == "disa":
        cikti = Path(a.out) if a.out else (paths.ROOT / "work" / f"{a.studyo}-{a.hedef}.stil.zip")
        z = stil_varlik.paket_zip_uret(a.studyo, a.hedef, cikti)
        print(f"Stil paketi: {paths.rel(z) if z.is_relative_to(paths.ROOT) else z}")
    elif a.eylem == "ice":
        sonuc = stil_varlik.paket_zip_ice_al(a.studyo, Path(a.hedef), yeni_ad=a.yeni_ad, uzerine_yaz=a.uzerine_yaz)
        print(f"İçe aktarıldı: {sonuc['studyo']}/{sonuc['ad']} ({sonuc['varlik_sayisi']} varlık)")


def cmd_tema_cikar(a):
    from . import hizli, tema
    tema.cikar(hizli.bul(a.ref))


def cmd_denetim(a):
    from . import hizli
    hizli.denetim(Path(a.video), olaylar=Path(a.olaylar) if a.olaylar else None, metin=Path(a.metin) if a.metin else None, dil=a.dil)


def cmd_kaizen(a):
    from . import hizli
    hizli.kaizen(hizli.bul(a.ref))


def cmd_duzen(a):
    from . import hizli
    if hizli.duzen():
        sys.exit(1)


def cmd_sheet(a):
    from . import ff
    src = Path(a.video)
    info = ff.probe(src)
    start = a.start or 0.0
    dur = (a.dur or (info["duration"] - start)) + start
    out = Path(a.out) if a.out else src.with_name(f"{src.stem}.sheet_{int(start)}.jpg")
    cols, rows = (int(x) for x in a.grid.split("x"))
    ff.contact_sheet(src, out, duration=dur, start=start, cols=cols, rows=rows, width=a.width)
    print(f"Kontak sayfası: {out}")


def cmd_still(a):
    from . import ff
    src = Path(a.video)
    out = Path(a.out) if a.out else src.with_name(f"{src.stem}.t{a.t:.2f}.jpg")
    ff.still(src, out, a.t, width=a.width)
    print(f"Kare: {out}")


def cmd_kurgu_al(a):
    from . import hizli, kurgu
    p = hizli.bul(a.ref)
    if kurgu.yol(p.work).exists() and not a.zorla:
        raise SystemExit("kurgu.json zaten var. Üzerine yazmak için --zorla.")
    k = kurgu.yaz(p.work, kurgu.eski_projeden(p))
    print(f"Kurgu: {paths.rel(kurgu.yol(p.work))} · {len(k.klipler)} klip · {len(k.izler)} iz")


def cmd_kurgu_denetle(a):
    from . import hizli, kurgu
    p = hizli.bul(a.ref)
    k = kurgu.oku(p.work)
    hatalar = kurgu.denetle(p, k)
    for h in hatalar:
        print(f"  ! {h}")
    from . import kurgu_kalite
    from . import tema_token
    tema = tema_token.oku(kurgu.etkin_tema(p, k.motion_tema))
    for u in kurgu_kalite.uyarilar(k, tema, p=p):  # ADR 0040: uyarı, render'ı durdurmaz; ADR 0043: stil dışı renk
        print(f"  ~ {u['bas']:7.2f} sn {u['kod']}: {u['kanit']}. {u['oneri']}")
    if hatalar:
        raise SystemExit(f"{len(hatalar)} sorun: render edilemez.")
    print("Kurgu temiz.")


def cmd_miks(a):
    from . import hizli
    hizli.miks(hizli.bul(a.ref))


def cmd_oneri(a):
    from . import hizli, kurgu, sessizlik
    p = hizli.bul(a.ref)
    o = sessizlik.oneriler(p, kurgu.oku(p.work), min_sessizlik=a.min)
    for x in o:
        print(f"  {x['bas']:8.2f}-{x['bit']:8.2f} sn  {x['tur']:9} {x['neden']}")
    print(f"{len(o)} aday, toplam {sum(x['bit'] - x['bas'] for x in o):.1f} sn. Kurguya yazılmaz; Video Stüdyo > Öneriler'den seçerek uygula.")


def cmd_ritim(a):
    from . import hizli, kurgu, ritim
    p = hizli.bul(a.ref)
    f = ritim.yaz(p, kurgu.oku(p.work))
    import json
    r = json.loads(f.read_text(encoding="utf-8"))
    print(ritim.ozet(r, en_cok=12))
    print(f"{len(r['onsets'])} onset, {len(r['beats'])} beat, {len(r['vurgular'])} vurgu → {paths.rel(f)}")


def cmd_galeri(a):
    from . import galeri
    if a.islem == "kur":
        yapilan = galeri.kur(a.tur.split(",") if a.tur else None, yenile=a.yenile)
        print(f"{len(yapilan)} önizleme üretildi" + (": " + ", ".join(yapilan) if yapilan else " (hepsi hazır; --yenile zorlar)"))
        return
    from collections import Counter
    og = galeri.ogeler()
    eksik = [f"{o['tur']}/{o['id']}" for o in og if o["tur"] in ("tema", "fizik", "isik", "karakter") and not o.get("poster_url")]
    print(", ".join(f"{t}: {n}" for t, n in Counter(o["tur"] for o in og).items()))
    if eksik:
        print(f"Önizlemesi eksik {len(eksik)}: {', '.join(eksik[:12])}{' ...' if len(eksik) > 12 else ''} (vedit galeri kur)")


def cmd_viseme(a):
    from . import hizli, kurgu, viseme
    p = hizli.bul(a.ref)
    f = viseme.yaz(p, kurgu.oku(p.work))
    import json
    s = json.loads(f.read_text(encoding="utf-8"))["kareler"]
    print(f"{len(s)} kare, ağız açık %{viseme.acik_oran(s) * 100:.0f} → {paths.rel(f)}")


def cmd_senkron(a):
    from . import hizli, kurgu, senkron
    p = hizli.bul(a.ref)
    k = kurgu.oku(p.work)
    hedef = a.klip or [c.id for c in k.klipler if c.tur == "video" and c.kaynak and k.kaynaklar[c.kaynak].ses]
    olcumler = [senkron.olc(p, k, kid, en_cok=a.en_cok) for kid in hedef]
    for o in olcumler:
        print("  " + o.metin())
    if not a.uygula:
        return
    uyg = [o for o in olcumler if o.kayma_kare and not o.belirsiz and not o.dogal]
    for o in uyg:
        print("  " + senkron.uygula(k, o))
    if uyg:
        kurgu.yaz(p.work, k)
        print(f"{len(uyg)} klip düzeltildi; kurgu.json yazıldı.")
    else:
        print("Uygulanacak kesin kayma yok.")


def cmd_disa(a):
    from . import disa, hizli, kurgu
    p = hizli.bul(a.ref)
    k = kurgu.oku(p.work)
    for f in disa.yaz(p, k, p.cikti):
        print(f"Dışa aktarıldı: {paths.rel(f)}")
    for y in disa.yer_tutucular(k):
        print(f"  ! {y}")


def cmd_kurgu_reframe(a):
    from . import hizli, kurgu, kurgu_reframe
    p = hizli.bul(a.ref)
    k = kurgu.oku(p.work)
    s = kurgu_reframe.donus_hesapla(p, k, a.klip)
    kurgu.yaz(p.work, kurgu_reframe.uygula(k, a.klip, s))
    print(f"Reframe: {a.klip} · ölçek {s['olcek'][0]['v']:.3f} · {len(s['x'])} keyframe · yüz bulunan kare %{s['yuz_orani'] * 100:.0f}")


def cmd_kural(a):
    # WHY: bkz. wiki/decisions/0047-kural-deposu.md. Tek kaynak library/kurallar/kurallar.json; checks.md ondan üretilir.
    from . import kural
    if a.is_ == "goc":
        hedef = kural.klasor() / "kurallar.json"
        if hedef.exists() and not a.zorla:
            raise SystemExit(f"Depo zaten var: {paths.rel(hedef)} (yeniden göç için --zorla)")
        eski = paths.LIBRARY / "checks.md"
        yedek = kural.klasor() / "checks.goc-oncesi.md"
        yedek.parent.mkdir(parents=True, exist_ok=True)
        yedek.write_text(eski.read_text(encoding="utf-8"), encoding="utf-8")
        d = kural.goc(eski)
        kural.kaydet(d)
        print(f"Göç: {len(d.kurallar)} kural · yedek {paths.rel(yedek)} · checks.md artık üretiliyor")
        return
    d = kural.yukle()
    if a.is_ == "liste":
        for k in d.kurallar:
            if a.durum and k.durum != a.durum:
                continue
            if a.ara and a.ara.lower() not in k.metin.lower():
                continue
            print(f"{k.id} {k.onem} {k.durum:<7} {k.hedef_rol:<5} {k.kategori:<8} ×{k.tekrar} {k.metin}")
        if a.is_ == "liste" and (kapi := kural.kapi_onerileri(d)):
            print(f"\nKapı önerisi (tekrar >= 2, ölçülebilir): {', '.join(k.id for k in kapi)}")
        return
    if a.is_ == "ekle":
        if not a.metin:
            raise SystemExit('Kural metni gerekli: vedit kural ekle "YAP: ..."')
        k = kural.ekle(d, " ".join(a.metin), kategori=a.kategori, onem=a.onem, hedef_rol=a.rol, kapsam=a.kapsam,
                       kapsam_deger=a.deger, neden=a.neden or "", kaynak="kullanici")
        kural.kaydet(d)
        print(f"{k.id} {k.durum} ×{k.tekrar}: {k.metin}")
        return
    if a.is_ == "disa":
        print(d.model_dump_json(indent=1, by_alias=True, exclude_none=True))
        return
    if a.is_ == "ice":
        gelen = kural.Depo.model_validate_json(Path(a.metin[0]).read_text(encoding="utf-8"))
        n = 0
        for k in gelen.kurallar:
            if kural.bul_benzer(d, k.metin) is None:
                d.kurallar.append(k.model_copy(update={"id": kural._yeni_id(d)}))
                n += 1
        kural.kaydet(d)
        print(f"İçe aktarıldı: {n} yeni kural ({len(gelen.kurallar) - n} benzeri vardı)")
        return
    durum = {"sil": "silinen", "ac": "aktif", "kapat": "pasif", "onayla": "aktif", "reddet": "silinen"}[a.is_]
    for kid in a.metin:
        k = kural.durum_degistir(d, kid, durum)
        print(f"{k.id} → {k.durum}")
    kural.kaydet(d)


def cmd_kurgu_gecis(a):
    # WHY: bkz. wiki/decisions/0045-native-motion.md. Eski opak gecis-* bindirmesi → V1 kesim geçişi.
    from . import gecis_donustur, hizli, kurgu
    p = hizli.bul(a.ref)
    k = kurgu.oku(p.work)
    rapor = gecis_donustur.donustur(k)
    for s in rapor:
        print(f"  {s}")
    if not rapor:
        print("Eski geçiş bindirmesi yok.")
    elif a.uygula:
        kurgu.yaz(p.work, k)
        print(f"Kurgu yazıldı: {len(rapor)} bindirme dönüştürüldü.")
    else:
        print("Önizleme; yazmak için --uygula.")


def _ses_kaynaklari(p, yol: str | None, hepsi: bool) -> list:
    """Yol verilmezse ya da --hepsi ile girdi klasörünün tüm video/ses dosyaları, doğal sırayla. Çıplak ad `inputs:` sayılır."""
    from . import hizli, kurgu
    if yol and not hepsi:
        return [kurgu.dosya(p, yol if ":" in yol else f"inputs:{yol}")]
    d = sorted((f for f in p.girdi.iterdir() if f.is_file() and f.suffix.lower() in hizli.MEDYA), key=lambda f: hizli.dogal(f.name))
    if not d:
        raise SystemExit(f"Girdi klasöründe video ya da ses yok: {paths.rel(p.girdi)}")
    return d


def cmd_ayristir(a):
    from . import ayristir, hizli
    p = hizli.bul(a.ref)
    if not ayristir.hazir():
        raise SystemExit(ayristir.kurulum_komutu())
    for f in _ses_kaynaklari(p, a.yol, a.hepsi):
        r = ayristir.ayir(f, p.work / "public" / "ayrisan", stem=a.stem)
        print(f"{f.name}: {r['sure']:.0f} sn{' (önbellek)' if r['onbellek'] else ''}")
        for ad in ayristir.KIPLER[a.stem]:
            print(f"  {ad}: {paths.rel(r[ad])}")


def cmd_ses_cikar(a):
    from . import ayristir, hizli
    p = hizli.bul(a.ref)
    for f in _ses_kaynaklari(p, a.yol, a.hepsi):
        print(f"Ses: {paths.rel(ayristir.ses_cikar(f, p.cikti / 'ses', a.bicim))}")


def cmd_kapak(a):
    from . import hizli, kapak
    p = hizli.bul(a.ref)
    if a.sec is not None:  # 0 da geçersiz adaydır; üretime düşüp agy kotası harcamasın
        print(f"Seçildi: {paths.rel(kapak.sec(p, a.platform, a.sec))}")
        return
    if a.master is not None:  # 0: aday yok, ilk öneri ya da brief
        m = kapak.master(p, a.platform, a.master or None, kare=a.kare, video=a.video)
        if a.hedef:
            for tur in ("yazili", "bos"):
                h = m["hedefler"][a.hedef][tur]
                print(f"## {h['ad']} · {'yazılı' if tur == 'yazili' else 'boş zemin'}\n{h['prompt']}\n")
        else:
            print(m["md"])
        return
    if a.gelistir is not None:
        kapak.gelistir(p, a.platform, a.gelistir, max(a.adet, 1), model=a.model, video=a.video, kare=a.kare)
        print(f"Öneri yazıldı. Üretim: vedit kapak {p.studyo}/{p.ad} --oneri --adet N")
        return
    if a.gorsel_duzelt is not None:
        bolge = [float(v) for v in a.bolge.split(",")] if a.bolge else None
        print(f"Düzeltildi: {paths.rel(kapak.gorsel_duzelt(p, a.platform, a.gorsel_duzelt, a.istek or '', bolge=bolge, yalniz_bolge=not a.tum_gorsel, model=a.gorsel_model))}")
        return
    if a.ice_al:
        print(f"İçe alındı: {paths.rel(kapak.ice_al(p, a.platform, Path(a.ice_al), yazili=a.yazili, metin=a.metin))}")
        return
    stil = dict(vurgu=a.vurgu, yerlesim=a.yerlesim, olcek=a.olcek, karart=a.karart, kutu=a.kutu, kalip=a.kalip, stil=a.stil, ek=a.ek)
    if a.duzenle is not None:
        print(f"Yazı çizildi: {paths.rel(kapak.duzenle(p, a.platform, a.duzenle, kopya=a.kopya, metin=a.metin, **stil))}")
        return
    if a.elestir and a.adet == 0:  # yalnız eleştiri: yeni aday üretmez
        kapak.elestir(p, a.platform)
        return
    yeni = kapak.uret(p, a.platform, a.adet, metin=a.metin, prompt=a.prompt, zemin=Path(a.zemin) if a.zemin else None,
                      yeni_brief=a.yeni_brief, kare=a.kare, video=a.video, oneri=a.oneri, model=a.model,
                      gorsel_model=a.gorsel_model, **stil)
    print(f"{len(yeni)}/{a.adet} aday. Seçim: vedit kapak {p.studyo}/{p.ad} --sec <n>")
    if a.elestir and yeni:
        kapak.elestir(p, a.platform)


def cmd_kontrol(a):
    """Değişiklikten sonra tek komutla doğrulama: testler, tip denetimi, ajan kopyaları, wiki. Dosya değiştirmez."""
    import shutil
    import subprocess
    import time

    kok = paths.ROOT
    py, npm = sys.executable, shutil.which("npm")
    adimlar = [("pytest", [py, "-m", "pytest", "tests", "-q"], kok),
               ("ajan kopyaları", [py, "scripts/ajan_esitle.py", "--denetle"], kok),
               ("wiki lint", [py, "scripts/wiki_lint.py"], kok),
               ("wiki log boyu", [py, "scripts/wiki_log_bol.py", "--denetle"], kok)]
    if npm and (kok / "studio" / "node_modules").is_dir():
        adimlar += [("arayüz tip", [npm, "run", "tip"], kok / "studio"), ("arayüz test", [npm, "test"], kok / "studio")]
    else:
        print("  ! npm ya da studio/node_modules yok: arayüz adımları atlandı")
    kalan = 0
    for ad, komut, cwd in adimlar:
        t0 = time.time()
        r = subprocess.run(komut, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(f"{'TAMAM' if r.returncode == 0 else 'HATA '}  {ad:<16} {time.time() - t0:5.1f} sn")
        if r.returncode:
            kalan += 1
            print("\n".join("    " + s for s in (r.stdout + r.stderr).strip().splitlines()[-12:]))
    if kalan:
        raise SystemExit(f"{kalan} adım hatalı.")
    print("Hepsi geçti.")


def cmd_studio(a):
    from .studio import baslat  # WHY: pencere ağır importtan önce açılır (ADR 0050)
    baslat.calistir(port=a.port, ac=not a.acma)


def main(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="vedit", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def P(name, fn, help_, project_arg=True):
        sp = sub.add_parser(name, help=help_)
        if project_arg:
            sp.add_argument("-p", "--project", help="proje slug'ı ya da yolu (varsayılan: içinde bulunulan klasör)")
        sp.set_defaults(fn=fn)
        return sp

    sp = P("new", cmd_new, "yeni proje", project_arg=False)
    sp.add_argument("studio", choices=paths.STUDIO_NAMES)
    sp.add_argument("title")
    sp.add_argument("--pipeline", choices=["footage", "animation"])
    sp.add_argument("--lang", choices=["tr", "en"])
    P("status", cmd_status, "proje durumu ve sıradaki adım")
    sp = P("mark", cmd_mark, "adımı tamamlandı say / onay kapısını işaretle")
    sp.add_argument("step")
    g = sp.add_mutually_exclusive_group()
    g.add_argument("--approve", action="store_true")
    g.add_argument("--skip", action="store_true")
    P("ingest", cmd_ingest, "input/ envanteri + kontak sayfaları")
    sp = P("transcribe", cmd_transcribe, "kelime zamanlı transkripsiyon")
    sp.add_argument("--model", default=None)
    sp.add_argument("--lang", help="tr | en | auto")
    sp.add_argument("--prompt", help="özel isimler/marka (doğruluğu artırır)")
    sp.add_argument("--files", nargs="*")
    sp.add_argument("--force", action="store_true")
    P("digest", cmd_digest, "LLM için kompakt transkript")
    P("cut", cmd_cut, "EDL → A-roll")
    sp = P("reframe", cmd_reframe, "yüz takipli dikey kadraj yolu")
    sp.add_argument("--src", default="build/aroll.mp4")
    sp.add_argument("--size", help="ör. 1080x1920 (varsayılan proje formatı)")
    sp = P("audio", cmd_audio, "konuşma temizleme")
    sp.add_argument("--src")
    sp.add_argument("--denoise", default="light", choices=["off", "light", "medium", "strong"])
    sp.add_argument("--no-eq", action="store_true")
    sp = P("captions", cmd_captions, "altyazı sayfaları + SRT")
    sp.add_argument("--style", choices=["odak", "bold-pop", "clean-sub", "karaoke", "underline"])
    P("align", cmd_align, "sahneleri seslendirmeye hizala (animasyon)")
    P("scenes2timeline", cmd_scenes2timeline, "hizalı sahneler → timeline.json (animasyon)")
    P("validate", cmd_validate, "edl/scenes/timeline şema + blok prop kontrolü")
    P("build", cmd_build, "timeline → HyperFrames kompozisyonu")
    sp = P("render", cmd_render, "preview | final")
    sp.add_argument("mode", choices=["preview", "final"])
    sp.add_argument("--parallel", type=int, default=2)
    sp = P("qa", cmd_qa, "otomatik kalite kontrol")
    sp.add_argument("--video")
    sp = P("export", cmd_export, "varyantlar, SRT, bölümler, kapaklar")
    sp.add_argument("--variants", nargs="*")
    sp = P("mix", cmd_mix, "master ses (konuşma + müzik + SFX)")
    sp.add_argument("--duck-db", type=float, default=-11.0)
    sp = P("sfx", cmd_sfx, "SFX kütüphanesi")
    sp.add_argument("action")
    sp.add_argument("args", nargs="*")
    sp.add_argument("--query")
    sp.add_argument("--n", type=int, default=0)
    sp.add_argument("--rescan", action="store_true")
    sp = P("olaysesi", cmd_olaysesi, "olaylar.json'dan zoom/kesme/geçiş sesi + miks + mp4", project_arg=False)
    sp.add_argument("olaylar")
    sp.add_argument("-o", "--output")
    sp.add_argument("--duck-db", type=float, default=-11.0)
    sp.add_argument("--min-aralik", type=float, default=0.4)
    sp = P("loop", cmd_loop, "loop mührü ve sarma ölçümü (kontrol | muhur)", project_arg=False)
    sp.add_argument("action")
    sp.add_argument("dosyalar", nargs="+")
    sp.add_argument("-o", "--output")
    sp.add_argument("--mod", default="otomatik")
    sp.add_argument("--capraz", type=float, default=0.5)
    sp.add_argument("--sure", type=float, default=0.0)
    sp = P("reference", cmd_reference, "referans video/görsel analizi", project_arg=False)
    sp.add_argument("urls", nargs="*")
    sp.add_argument("--images", nargs="*")
    sp.add_argument("-p", "--project")
    sp.add_argument("--studio", choices=paths.STUDIO_NAMES)
    sp.add_argument("--minutes", type=float, default=5.0)
    sp = P("blocks", cmd_blocks, "blok kataloğu (LLM için kompakt)", project_arg=False)
    sp.add_argument("--tag")
    sp = P("hf-guncelle", cmd_hf_guncelle, "HyperFrames'i repodan güncelle: aday kurulum + duman testi, geçerse sabitle (ADR 0051)", project_arg=False)
    sp.add_argument("--kontrol", action="store_true", help="yalnız yeni sürüm var mı bak")
    sp.add_argument("--duman", action="store_true", help="duman paketini mevcut sürümle koş")
    sp.add_argument("--geri", action="store_true", help="bir önceki sabit sürüme dön")
    sp.add_argument("--surum", help="belirli sürümü dene (boşsa en yeni)")
    sp.add_argument("--skill-yok", action="store_true", help="skill'leri güncelleme")
    sp.add_argument("--bekle", type=float, default=0, metavar="DAKIKA",
                    help="çalışan edit/render varsa sabitlemeden önce en çok bu kadar bekle (varsayılan 0: bekleme, ertele)")
    sp = P("hf", cmd_hf, "HyperFrames grafikleri (ADR 0050): liste, kur = kompozisyonu saydam webm'e üret", project_arg=False)
    sp.add_argument("is_", metavar="liste|kur", choices=["liste", "kur"])
    sp.add_argument("ref", nargs="?", help="proje: <stüdyo>/<proje> (boşsa yalnız kütüphane)")
    sp.add_argument("--ad", help="kompozisyon adı (work/edit/hf/<ad>/ ya da library/motion/hf/<ad>/)")
    sp.add_argument("--param", help="""değişkenler JSON, ör. '{"baslik": "Merhaba"}'""")
    sp.add_argument("--tema", help="motion teması (boşsa varsayilan ya da projenin teması)")
    sp.add_argument("--cikti", help="çıktı klasörü (boşsa work/hf)")
    sp = P("motion", cmd_motion, "motion kütüphanesi: kur = kaynaktan (html + meta.json) webm, poster, kontak ve manifest üret; olc = alfa, boyut, son kare, geçiş ortası ölçümü", project_arg=False)
    sp.add_argument("is_", metavar="kur|olc|kontak|ice-al", choices=["kur", "olc", "kontak", "ice-al"])
    sp.add_argument("--kaynak", help="ice-al: mixkit, pixabay, lottiefiles, uppbeat, github (boşsa klasör adı)")
    sp.add_argument("--url", help="ice-al: varlığın sayfası (boşsa kaynağın lisans sayfası)")
    sp.add_argument("--lisans", help="ice-al: lisans adı (boşsa kaynağın varsayılanı)")
    sp.add_argument("--atif-gerekli", action="store_true", help="ice-al: atıf zorunlu (Uppbeat Free'de kendiliğinden)")
    sp.add_argument("--atif-metni", help="ice-al: yayin.md'ye yazılacak atıf satırı")
    sp.add_argument("--kisit", action="append", help="ice-al: kısıt (birden çok kez), ör. yalniz-kendi-kanalin")
    sp.add_argument("--tur", default="overlay", help="ice-al: overlay, icon, transition, lower-third, background, broll, cta, reaction, light-leak, texture")
    sp.add_argument("--ad", help="ice-al: tek dosyada görünen ad")
    sp.add_argument("--etiket", action="append", help="ice-al: etiket (birden çok kez)")
    sp.add_argument("--ne-zaman", help="ice-al: AI edit için tek cümle")
    sp.add_argument("--yontem", choices=["alfa", "yesil", "siyah", "lottie", "gif", "svg"], help="ice-al: alfa yöntemi (boşsa bulunur)")
    sp.add_argument("--benzerlik", type=float, default=0.18, help="ice-al: yeşil perde anahtar eşiği")
    sp.add_argument("--anahtar-dene", action="store_true", help="ice-al: yeşil perde için 3 eşikte dama zeminli önizleme yaz, içe aktarma")
    sp.add_argument("kimlik", nargs="*", help="yalnız bu kayıtlar; boşsa hepsi (kontak: native bileşen adları, ör. ikon/tik)")
    sp.add_argument("--tema", help="kontak: stil teması (library/motion/tema/<ad>)")
    sp.add_argument("--kare", help="kontak: gerçek kare zemini (görsel dosyası)")
    sp.add_argument("--cikti", default="work/motion-galeri", help="kontak: çıktı klasörü")
    sp.add_argument("--manifest", action="store_true", help="render etme, yalnız manifesti meta.json'lardan yenile")
    sp.add_argument("--onizle", action="store_true", help="manifesti yazma: webm, poster ve kontak üret (paralel ajanlar için)")
    sp = P("pano", cmd_pano, "HTML panoyu kare kare mp4'e çevir; -o .webm saydam VP9 (motion), .png/.jpg ise --sure anındaki tek kare (kapak)", project_arg=False)
    sp.add_argument("html")
    sp.add_argument("--sure", type=float, default=8.0)
    sp.add_argument("-o", "--out", required=True)
    sp.add_argument("--w", type=int, default=1920)
    sp.add_argument("--h", type=int, default=1080)
    sp.add_argument("--fps", type=int, default=30)
    sp.add_argument("--css", help="stüdyo stiline çeken ek CSS")
    sp.add_argument("--tema", help="stil teması (library/motion/tema/<ad>): pano renk ve fontu stilden gelir (ADR 0043)")
    sp = P("gorsel", cmd_gorsel, "agy (Antigravity) ile ücretsiz görsel üret, work/gorsel/log.md'ye yaz", project_arg=False)
    sp.add_argument("prompt")
    sp.add_argument("-o", "--out", required=True, help="hedef dosya; uzantısız verilirse agy'nin biçimi")
    sp.add_argument("--oran", default="16:9", choices=["16:9", "9:16", "1:1", "4:5", "4:3", "3:4"])
    sp = P("kapak", cmd_kapak, "YouTube/Instagram kapak adayları (Antigravity zemini + şablon yazısı); --sec ile teslim", project_arg=False)
    sp.add_argument("ref")
    sp.add_argument("--platform", choices=["youtube", "instagram"], help="varsayılan stüdyodan; ugc'de zorunlu")
    sp.add_argument("--adet", type=int, default=1, help="1-5 yeni aday")
    sp.add_argument("--metin", help='kapak yazısı "satır1|satır2"; yoksa brief')
    sp.add_argument("--prompt", help="görsel prompt'u; yoksa brief.json ya da agy brief'i")
    sp.add_argument("--zemin", help="agy yerine bu kareyi zemin yap (eldeki malzeme)")
    sp.add_argument("--kare", type=int, help="videodan çıkarılan karelerden referans (work/gorsel/kapak/kareler); yoksa brief seçer")
    sp.add_argument("--yeni-brief", action="store_true", help="brief.json'u agy ile yeniden yaz")
    sp.add_argument("--sec", type=int, help="bu adayı outputs'a teslim et")
    sp.add_argument("--duzenle", type=int, help="bu adayın yazısını zemini yeniden üretmeden yeniden çiz (agy'siz)")
    sp.add_argument("--kopya", action="store_true", help="--duzenle ile: adayın üzerine yazma, yeni aday aç (varyasyon)")
    sp.add_argument("--vurgu", help="ikinci satırda turuncu olacak kelime; yoksa tüm ikinci satır")
    sp.add_argument("--yerlesim", choices=["sol", "sag", "ust", "alt"], help="başlık yeri; YouTube sol|sag|ust|alt, Instagram ust|alt")
    sp.add_argument("--olcek", type=float, help="yazı boyutu çarpanı 0.6-1.4")
    sp.add_argument("--karart", action=argparse.BooleanOptionalAction, help="yazı arkasına yönlü gradyan")
    sp.add_argument("--kutu", action=argparse.BooleanOptionalAction, help="vurguyu renkli kutuda yaz; yoksa stil paketinin varsayılanı")
    sp.add_argument("--kalip", help="YouTube klasik|dev-yazi|alt-bant|bolunmus|rozet|not|yazisiz, Instagram klasik|seri|yazisiz")
    sp.add_argument("--stil", help="yazı stil paketi (library/kapak/stiller/); yoksa stüdyonun kapak.json'u, brief ya da turuncu")
    sp.add_argument("--ek", help="kalıbın ek sözü: dev-yazi'da arkadaki dev söz, alt-bant'ta üst satır, not'ta el yazısı, seri'de marka")
    sp.add_argument("--elestir", action="store_true", help="adayları agy'ye puanlat (1-10 ve tek düzeltme); --adet 0 ile yalnız eleştiri")
    sp.add_argument("--video", help='kareler yalnız bu videodan: "inputs:1.mp4" ya da "outputs:work/renders/ham.mp4"')
    sp.add_argument("--model", help="brief, geliştirme ve eleştiriyi yazan agy modeli (`agy models`)")
    sp.add_argument("--gorsel-model", help="generate_image'ı çağıran agy modeli; görsel modelinin kendisi agy'de sabittir")
    sp.add_argument("--gelistir", metavar="FIKIR", nargs="?", const="",
                    help="fikrini skill kurallarıyla yapılı brief'e çevir (oneri.json); fikir boşsa videodan öner; görsel üretmez")
    sp.add_argument("--oneri", action="store_true", help="brief olarak oneri.json'u kullan (--gelistir sonrası)")
    sp.add_argument("--gorsel-duzelt", type=int, metavar="N", help="adayın görselini düzelt (--istek); sonuç yeni aday")
    sp.add_argument("--istek", help='görsel düzeltme isteği, ör. "arka planı koyu mavi yap"')
    sp.add_argument("--bolge", help="düzeltilecek kutu, tuval yüzdesi: sol,üst,sağ,alt (ör. 50,10,95,60)")
    sp.add_argument("--tum-gorsel", action="store_true", help="--bolge ile: sonucun tamamını al (varsayılan yalnız kutu değişir)")
    sp.add_argument("--ice-al", metavar="DOSYA", help="başka platformda üretilen görseli aday yap (oran kırpılır)")
    sp.add_argument("--yazili", action="store_true", help="--ice-al ile: görselde yazı var, yazı eklenmez")
    sp.add_argument("--master", type=int, nargs="?", const=0, metavar="N",
                    help="dış platformlar için master prompt (Nano Banana Pro/2.1, ChatGPT, Midjourney, Ideogram, Leonardo); N aday")
    sp.add_argument("--hedef", choices=["nano-banana-pro", "nano-banana-21", "chatgpt", "midjourney", "ideogram", "leonardo"],
                    help="--master ile yalnız bu platform")
    sp = P("teslim", cmd_teslim, "son kodlama: BT.709, yüksek kalite, ölçümle kapı", project_arg=False)
    sp.add_argument("video")
    sp.add_argument("-o", "--output")
    sp.add_argument("--platform", choices=["youtube", "reels", "ugc"])
    sp.add_argument("--kalite", choices=["arsiv", "yayin", "hafif"], default="yayin")
    sp.add_argument("--kodek", choices=["h264", "h265"], default="h264")
    sp.add_argument("--kapak-kare", help="kapak görselini yalnız 0. kareye göm (X, Discord, Slack önizlemesi; oynatmada 1 kare)")
    sp = P("kesimqa", cmd_kesimqa, "dışa aktarılan sesi beklenen metinle karşılaştır", project_arg=False)
    sp.add_argument("video")
    sp.add_argument("--beklenen", help="düz metin dosyası (yoksa projenin transkripti)")
    sp.add_argument("--dil", choices=["tr", "en"])
    sp.add_argument("-p", "--project")
    sp = P("slop", cmd_slop, "bitmiş videoda AI slop şüphelerini ölç", project_arg=False)
    sp.add_argument("video")
    sp.add_argument("--olaylar", help="edit/olaylar.json")
    sp.add_argument("--metin", help="transkript yerine düz metin")
    sp.add_argument("--yazisiz", action="store_true", help="metin taramasını atla")
    sp.add_argument("--dil", choices=["tr", "en"])
    sp.add_argument("--cikti", help="rapor klasörü (varsayılan: proje qa/)")
    sp = P("hazirla", cmd_hazirla, "girdi ölçümü, önbellekli transkript, digest, kontak sayfası", project_arg=False)
    sp.add_argument("ref", help="proje adı (Projeler/inputs/<stüdyo>/<proje>)")
    sp.add_argument("--dil", default="tr")
    sp.add_argument("--prompt", help="özel isimler (doğruluğu artırır)")
    sp.add_argument("--ek", nargs="*", help="girdi dışından ek dosya, ör. work/public/speaker.mp4")
    sp = P("kes", cmd_kes, "work/edit/kesim.json → work/public/speaker.mp4", project_arg=False)
    sp.add_argument("ref")
    sp = P("taslak", cmd_taslak, "hızlı önizleme + kontak sayfası (düzeltme döngüsü)", project_arg=False)
    sp.add_argument("ref")
    sp.add_argument("--aralik", nargs=2, type=float, metavar=("BAS", "BIT"), help="yalnız bu saniye aralığı")
    sp = P("final", cmd_final, "tam render → olaysesi → teslim → denetim", project_arg=False)
    sp.add_argument("ref")
    sp.add_argument("--platform", choices=["youtube", "reels", "ugc"])
    sp.add_argument("--ad", help="teslim dosyası adı; varsa -v2 eklenir")
    sp.add_argument("--metin", help="beklenen metin dosyası")
    sp.add_argument("--yenile", action="store_true", help="görüntü girdileri aynı olsa da motoru yeniden çalıştır")
    _teslim_bayraklari(sp)
    sp = P("ai-edit", cmd_ai_edit, "AI kurguyu yazar (kurgu.json), doğrular, taslak alır; --final ile teslim eder", project_arg=False)
    sp.add_argument("ref")
    sp.add_argument("--motor", default="claude", choices=list(motorlar.MOTORLAR))
    sp.add_argument("--model", help="motorun model kimliği; yoksa motorun varsayılanı")
    sp.add_argument("--stil", help="stil paketi adı; yoksa work/edit/stil.txt ya da stüdyo varsayılanı")
    sp.add_argument("--not", dest="notu", help="editöre not")
    sp.add_argument("--motion", default="yogun", choices=["az", "orta", "yogun"], help="motion grafik yoğunluğu (ADR 0036)")
    sp.add_argument("--aralik", nargs=2, type=float, metavar=("BAS", "SON"), help="yalnız bu sekans aralığını (sn) düzelt; dışı değişmez")
    sp.add_argument("--final", action="store_true", help="taslaktan sonra final render")
    sp.add_argument("--ekip", action="store_true", help="orkestratör + seviyeli editör ve kalite kontrol ekibi (ADR 0053, kapılı paralel akış)")
    sp.add_argument("--seviye", choices=["low", "medium", "high", "xhigh", "max"],
                    help="ekip seviyesi: low 2E+1K, medium 4E+2K, high 6E+3K, xhigh 8E+4K, max 10E+5K (yoksa ön ayar)")
    sp.add_argument("--tekrar-denetle", action="store_true", help="ekip: düzeltmeden sonra ikinci QC paketi (yalnız istenirse)")
    sp.add_argument("--ekip-dosyasi", help="ekip ayarı JSON; yoksa work/edit/ekip.json, sonra library/ekip.json")
    sp.add_argument("--sifirdan", action="store_true", help="ekip: mevcut kurguyu geçmişe bırakıp girdiden yeniden kur")
    sp.add_argument("--platform", choices=["youtube", "reels", "ugc"])
    sp.add_argument("--ad", help="teslim dosyası adı (--final)")
    sp.add_argument("--yenile", action="store_true")
    _teslim_bayraklari(sp)
    sp = P("stil-uret", cmd_stil_uret, "referanslardan STYLE.md, MOTION.md, tokens.json (Projeler/inputs/_referanslar/<stüdyo>/<ad>/)", project_arg=False)
    sp.add_argument("studyo", choices=list(paths.STUDIO_NAMES))
    sp.add_argument("ad")
    sp.add_argument("--motor", default="claude", choices=list(motorlar.MOTORLAR))
    sp.add_argument("--model")
    sp = P("stil-katalog", cmd_stil_katalog, "hazır stil kataloğu: liste, kur (tema + önizleme), ekle (stüdyoya paket), kart (örnek set + ölçüm)", project_arg=False)
    sp.add_argument("eylem", choices=["liste", "kur", "ekle", "kart"])
    sp.add_argument("kimlik", nargs="*")
    sp.add_argument("--studyo", choices=list(paths.STUDIO_NAMES))
    sp.add_argument("--proje", help="ekle: stili bu projede seç")
    sp.add_argument("--onizlemesiz", action="store_true", help="kur: yalnız tema CSS'leri")
    sp = P("stil-varlik", cmd_stil_varlik, "stile özel varlık deposu: liste, ekle, sil, indir (temalı native .webm)", project_arg=False)
    sp.add_argument("eylem", choices=["liste", "ekle", "sil", "indir"])
    sp.add_argument("studyo", choices=list(paths.STUDIO_NAMES))
    sp.add_argument("ad", help="stil paketi adı")
    sp.add_argument("hedef", nargs="?", help="ekle: dosya yolu; sil: varlık kimliği; indir: native bileşen adı")
    sp.add_argument("--tur", choices=["motion", "animasyon", "karakter", "gorsel", "ses"], help="varlık türü (ekle varsayılanı: motion)")
    sp.add_argument("--baslik", help="ekle: görünen ad")
    sp.add_argument("--ne-zaman", help="ekle: AI edit kullanım zamanı notu")
    sp.add_argument("--etiket", action="append", help="ekle: etiket (birden çok kez)")
    sp.add_argument("--yontem", choices=["alfa", "yesil", "siyah", "lottie", "gif", "svg", "karakter_json", "ham"], help="ekle: alfa/dönüşüm yöntemi")
    sp.add_argument("--lisans", default="Kendi üretimim", help="ekle: lisans açıklaması")
    sp.add_argument("--url", help="ekle: kaynak URL")
    sp.add_argument("--atif", help="ekle: atıf metni")
    sp.add_argument("--en-boy", default="1:1", choices=["9:16", "16:9", "1:1"], help="indir: en-boy oranı")
    sp.add_argument("--sure", type=float, help="indir: süre (sn)")
    sp.add_argument("--param", help="indir: bileşen parametreleri JSON metni")
    sp.add_argument("-o", "--out", "--cikti", dest="out", help="indir: hedef .webm yolu")
    sp.add_argument("--json", action="store_true", help="liste: JSON çıktı")
    sp = P("stil-paket", cmd_stil_paket, "stil paketini tüm özel varlıklarıyla .zip olarak dışa/içe aktar", project_arg=False)
    sp.add_argument("eylem", choices=["disa", "ice"])
    sp.add_argument("studyo", choices=list(paths.STUDIO_NAMES))
    sp.add_argument("hedef", help="disa: stil adı; ice: .zip dosya yolu")
    sp.add_argument("-o", "--out", "--cikti", dest="out", help="disa: hedef .zip yolu")
    sp.add_argument("--ad", "--yeni-ad", dest="yeni_ad", help="ice: stil adını değiştir")
    sp.add_argument("--uzerine-yaz", "--zorla", dest="uzerine_yaz", action="store_true", help="ice: var olan stilin üzerine yaz")
    sp = P("tema-cikar", cmd_tema_cikar, "girdinin baskın renklerinden proje motion teması (work/edit/motion_tema.css)", project_arg=False)
    sp.add_argument("ref")
    sp = P("denetim", cmd_denetim, "format, loudness, kesim ve slop ölçümü tek tablo", project_arg=False)
    sp.add_argument("video")
    sp.add_argument("--olaylar")
    sp.add_argument("--metin")
    sp.add_argument("--dil", default="tr")
    sp = P("kaizen", cmd_kaizen, "süre tablosu + library/kaizen.md satırı", project_arg=False)
    sp.add_argument("ref")
    P("duzen", cmd_duzen, "Projeler dışında medya, emekli bağ, uzun SKILL.md kontrolü", project_arg=False)
    sp = P("kurgu-al", cmd_kurgu_al, "props.json + olaylar.json → work/edit/kurgu.json", project_arg=False)
    sp.add_argument("ref")
    sp.add_argument("--zorla", action="store_true")
    sp = P("kurgu-denetle", cmd_kurgu_denetle, "kurgu.json şema, çakışma, eksik dosya denetimi", project_arg=False)
    sp.add_argument("ref")
    sp = P("oneri", cmd_oneri, "sessizlik ve dolgu kesim adayları (kurguya yazmaz)", project_arg=False)
    sp.add_argument("ref")
    sp.add_argument("--min", type=float, default=0.6, help="en kısa sessizlik, sn")
    sp = P("ritim", cmd_ritim, "konuşma ve müzikte onset, beat ve vurgu anları (work/edit/ritim.json)", project_arg=False)
    sp.add_argument("ref")
    sp = P("galeri", cmd_galeri, "stil ve motion galerisi: liste ya da önizleme üret (library/galeri/)", project_arg=False)
    sp.add_argument("islem", choices=["liste", "kur"])
    sp.add_argument("--tur", help="virgülle: tema,fizik,isik,karakter (varsayılan hepsi)")
    sp.add_argument("--yenile", action="store_true", help="var olan önizlemeleri de yeniden üret")
    sp = P("viseme", cmd_viseme, "konuşmadan kare başına ağız şekli (work/edit/viseme.json; konuşan karakter için)", project_arg=False)
    sp.add_argument("ref")
    sp = P("senkron", cmd_senkron, "video kliplerinde ses-görüntü kaymasını kare cinsinden ölç (--uygula ayrık sesi kaydırır)", project_arg=False)
    sp.add_argument("ref")
    sp.add_argument("klip", nargs="*", help="klip kimlikleri; yoksa sesli tüm video klipleri")
    sp.add_argument("--en-cok", type=int, default=12, help="aranan en büyük kayma, kare")
    sp.add_argument("--uygula", action="store_true", help="kesin kaymayı aynı bağdaki ayrık ses klibine uygula")
    sp = P("disa", cmd_disa, "kurgu.json → FCPXML (Resolve, Final Cut) ve XML (Premiere)", project_arg=False)
    sp.add_argument("ref")
    sp = P("kurgu-reframe", cmd_kurgu_reframe, "klibi yüz takibiyle kareyi dolduracak şekilde kadrajla", project_arg=False)
    sp.add_argument("ref")
    sp.add_argument("klip")
    sp = P("kural", cmd_kural, "kural deposu (library/kurallar): liste, ekle, sil, ac, kapat, onayla, reddet, disa, ice, goc; checks.md ondan üretilir", project_arg=False)
    sp.add_argument("is_", metavar="liste|ekle|sil|ac|kapat|onayla|reddet|disa|ice|goc",
                    choices=["liste", "ekle", "sil", "ac", "kapat", "onayla", "reddet", "disa", "ice", "goc"])
    sp.add_argument("metin", nargs="*", help="ekle: kural metni; sil/ac/kapat/onayla/reddet: kimlikler; ice: JSON dosyası")
    sp.add_argument("--kategori", default="genel")
    sp.add_argument("--onem", default="P1", choices=["P0", "P1", "P2"])
    sp.add_argument("--rol", default="hepsi", choices=["E1", "E2", "E3", "hepsi"])
    sp.add_argument("--kapsam", default="global", choices=["global", "studyo", "stil", "proje"])
    sp.add_argument("--deger", help="kapsam değeri: stüdyo, stil ya da proje adı")
    sp.add_argument("--neden")
    sp.add_argument("--durum", choices=["aktif", "oneri", "pasif", "silinen"], help="liste: süz")
    sp.add_argument("--ara", help="liste: metinde ara")
    sp.add_argument("--zorla", action="store_true", help="goc: var olan depoyu ez")
    sp = P("kurgu-gecis", cmd_kurgu_gecis, "eski opak gecis-* bindirmelerini V1 kesim geçişine çevir (sonraki çekim görünür)", project_arg=False)
    sp.add_argument("ref")
    sp.add_argument("--uygula", action="store_true", help="kurgu.json'a yaz; yoksa yalnız önizleme")
    sp = P("ayristir", cmd_ayristir, "Demucs ile konuşmayı müzikten (--stem 4: davul, bas, diğer) ayır (work/public/ayrisan/)", project_arg=False)
    sp.add_argument("ref")
    sp.add_argument("yol", nargs="?", help="kaynak, örn. 01.mp4 ya da inputs:01.mp4; yoksa girdi klasörünün hepsi")
    sp.add_argument("--stem", type=int, choices=[2, 4], default=2, help="2: konuşma+müzik, 4: konuşma+davul+bas+diğer (+müzik toplamı)")
    sp.add_argument("--hepsi", action="store_true", help="girdi klasöründeki tüm video/ses dosyaları")
    sp = P("ses-cikar", cmd_ses_cikar, "videonun sesini dosyaya çıkar (outputs/<stüdyo>/<proje>/ses/)", project_arg=False)
    sp.add_argument("ref")
    sp.add_argument("yol", nargs="?", help="kaynak, örn. 01.mp4; yoksa girdi klasörünün hepsi")
    sp.add_argument("--bicim", choices=["wav", "mp3", "m4a"], default="wav")
    sp.add_argument("--hepsi", action="store_true", help="girdi klasöründeki tüm video/ses dosyaları")
    sp = P("miks", cmd_miks, "görüntü render etmeden güncel ses miksi ve loudness ölçümü", project_arg=False)
    sp.add_argument("ref")
    P("kontrol", cmd_kontrol, "tek komutla doğrulama: pytest, arayüz tip ve test, ajan kopyaları, wiki", project_arg=False)
    sp = P("studio", cmd_studio, "Video Stüdyo: yerel kurgu uygulaması", project_arg=False)
    sp.add_argument("--port", type=int, default=8765)
    sp.add_argument("--acma", action="store_true", help="pencere açma")
    sp = P("sheet", cmd_sheet, "herhangi bir videodan kontak sayfası", project_arg=False)
    sp.add_argument("video")
    sp.add_argument("--start", type=float)
    sp.add_argument("--dur", type=float)
    sp.add_argument("--grid", default="4x4")
    sp.add_argument("--width", type=int, default=320)
    sp.add_argument("--out")
    sp = P("still", cmd_still, "tek kare", project_arg=False)
    sp.add_argument("video")
    sp.add_argument("t", type=float)
    sp.add_argument("--width", type=int)
    sp.add_argument("--out")

    args = ap.parse_args(argv)
    if getattr(args, "cmd", None) == "transcribe" and args.model is None:
        from .transcribe import DEFAULT_MODEL
        args.model = DEFAULT_MODEL
    import time
    t0 = time.time()
    args.fn(args)
    from . import hizli
    # WHY: kaizen için ham veri (ADR 0017); kayıt hatası işi bozmamalı, proje bulunamazsa sessiz geç.
    try:
        w = hizli.work_bul(argv if argv is not None else sys.argv[1:])
        if w is not None and w.parent.exists():
            hizli.sure_yaz(w, args.cmd, time.time() - t0)
    except OSError:
        pass


if __name__ == "__main__":
    main()
