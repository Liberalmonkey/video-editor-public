"""timeline.json → HyperFrames kompozisyonu (comp/index.html) + bölüm kompozisyonları.

# WHY: bkz. wiki/decisions/0005-timeline-json-tek-dogruluk-kaynagi.md — LLM HTML yazmaz;
# bu modül şemalı JSON'dan deterministik HTML üretir. comp/ her build'de yeniden yazılır;
# kalıcı özel sahneler edit/custom/ altında tutulur ve buraya kopyalanır.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from . import blocks as blk
from . import ff, hf, paths, project
from .schemas import Format, Timeline, load_json

FONT_REG = json.loads((paths.FONTS_DIR / "fonts.json").read_text(encoding="utf-8"))
BROWSER_SAFE = {"h264", "vp9", "vp8", "av1"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}


# ---------------------------------------------------------------- stil

def load_tokens(root: Path, style: str) -> dict:
    proj = project.load(root)
    for cand in (paths.studio_dir(proj.studio) / "styles" / style / "tokens.json",
                 paths.LIBRARY / "styles" / style / "tokens.json",
                 paths.LIBRARY / "styles" / "default" / "tokens.json"):
        if cand.exists():
            base = json.loads((paths.LIBRARY / "styles" / "default" / "tokens.json").read_text(encoding="utf-8"))
            tok = json.loads(cand.read_text(encoding="utf-8"))
            for k, v in tok.items():
                if isinstance(v, dict) and isinstance(base.get(k), dict):
                    base[k] = {**base[k], **v}
                else:
                    base[k] = v
            return base
    raise SystemExit("Stil bulunamadı (library/styles/default/tokens.json eksik)")


# ---------------------------------------------------------------- varlıklar

class Assets:
    """Proje dosyalarını comp/assets/ altına hard-link (yoksa kopya) ile koyar."""

    def __init__(self, root: Path, comp: Path):
        self.root, self.dir = root, comp / "assets"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.map: dict[str, str] = {}

    def add(self, src: str | Path) -> str:
        p = Path(src)
        if not p.is_absolute():
            p = paths.pj(self.root, p) if paths.pj(self.root, p).exists() else (paths.ROOT / p)
        p = p.resolve()
        if not p.exists():
            raise SystemExit(f"Varlık bulunamadı: {src}")
        key = str(p)
        if key in self.map:
            return self.map[key]
        p = self._browser_safe(p)
        h = hashlib.sha1(key.encode()).hexdigest()[:6]
        name = f"{p.stem}-{h}{p.suffix.lower()}"
        dst = self.dir / name
        if not dst.exists() or dst.stat().st_size != p.stat().st_size:
            dst.unlink(missing_ok=True)
            try:
                dst.hardlink_to(p)
            except OSError:
                shutil.copy2(p, dst)
        self.map[key] = f"assets/{name}"
        return self.map[key]

    def _browser_safe(self, p: Path) -> Path:
        """Chrome'un çözemeyeceği video kodeklerini (HEVC/ProRes) H.264'e çevir (önbellekli)."""
        if p.suffix.lower() not in {".mp4", ".mov", ".mkv", ".m4v", ".avi", ".webm"}:
            return p
        info = ff.probe(p)
        v = info.get("video")
        if not v or (v["codec"] in BROWSER_SAFE and v["rotation"] == 0):
            return p
        out = self.root / "build" / "media" / f"{p.stem}.h264.mp4"
        if not out.exists() or out.stat().st_mtime < p.stat().st_mtime:
            out.parent.mkdir(parents=True, exist_ok=True)
            print(f"  transcode: {p.name} ({v['codec']}) → H.264")
            ff.ffmpeg("-i", str(p), "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p",
                      "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out))
        return out

    def font_faces(self, families: list[str]) -> str:
        css = []
        for fam in dict.fromkeys(families):
            reg = FONT_REG.get(fam)
            if not reg:
                continue
            rel_ = self.add(paths.FONTS_DIR / reg["file"])
            css.append(f'@font-face {{ font-family: "{fam}"; src: url("{rel_}") format("truetype"); '
                       f'font-weight: {reg["weight"]}; font-display: block; }}')
        return "\n".join(css)


# ---------------------------------------------------------------- pencere (bölüm) kırpma

@dataclass
class Window:
    t0: float
    t1: float

    def clip(self, start: float, dur: float) -> tuple[float, float, float] | None:
        """(yeni_start, yeni_dur, baştan_kesilen) ya da pencere dışındaysa None."""
        s, e = max(start, self.t0), min(start + dur, self.t1)
        if e - s < 1e-3:
            return None
        return round(s - self.t0, 3), round(e - s, 3), round(s - start, 3)


def _f(x: float) -> str:
    return f"{x:.3f}".rstrip("0").rstrip(".") if "." in f"{x:.3f}" else str(x)


def _js(obj) -> str:
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


# ---------------------------------------------------------------- HTML üretimi

def compose(root: Path, tl: Timeline, *, window: Window, fmt: Format, comp: Path, include_audio: bool,
            tokens: dict, studio_cfg, lang: str) -> tuple[str, list[str]]:
    W, H, fps = fmt.width, fmt.height, fmt.fps
    u0 = min(W, H) / 100
    # Blok ölçeği: 1080p yatayda gövde metni ~48–64 px, dikeyde (telefon tam ekran) ~%18 büyük.
    # Altyazılar ham ölçekte (--u0) kalır.
    u = u0 * (1.18 if H > W else 1.3)
    sa = studio_cfg.safe_area
    assets = Assets(root, comp)
    all_blocks = blk.load_all([root / "edit" / "blocks"])
    errors: list[str] = []
    dom: list[str] = []
    js: list[str] = []
    used_blocks: list[str] = []
    dur = round(window.t1 - window.t0, 3)

    # --- video katmanları
    for c in sorted(tl.video, key=lambda c: c.z):
        cut = window.clip(c.start, c.dur)
        if not cut:
            continue
        st, d, lead = cut
        src = assets.add(c.src)
        is_img = c.role == "image" or Path(c.src).suffix.lower() in IMG_EXT
        layout = c.layout
        wrap_id, in_id = f"w-{c.id}", f"in-{c.id}"
        css = []
        if c.crop_x is not None:
            css.append(f"object-position: {c.crop_x * 100:.1f}% 50%")
        if c.view:
            t_, r_, b_, l_ = c.view
            css.append(f"object-view-box: inset({t_}% {r_}% {b_}% {l_}%)")
        if c.blur or c.dim:
            css.append(f"filter: blur({c.blur * H / 1080:.1f}px) brightness({1 - c.dim:.2f})")
        style = f' style="{"; ".join(css)}"' if css else ""
        if is_img:
            media = (f'<img id="{c.id}" class="clip vimg" src="{src}" data-start="{_f(st)}" '
                     f'data-duration="{_f(d)}" alt=""{style} />')
        else:
            media_in = c.in_ + lead * c.rate
            rate = f' data-playback-rate="{_f(c.rate)}"' if c.rate != 1 else ""
            media = (f'<video id="{c.id}" class="clip" src="{src}" data-start="{_f(st)}" data-duration="{_f(d)}" '
                     f'data-media-start="{_f(media_in)}"{rate} muted playsinline{style}></video>')
        dom.append(f'<div class="vwrap layout-{layout} fit-{c.fit}" id="{wrap_id}" style="z-index:{1 + c.z}">'
                   f'<div class="inner" id="{in_id}">{media}</div></div>')
        if layout != "full":
            js.append(f'tl.set("#{wrap_id}", {{opacity: 0}}, 0);')
            js.append(f'tl.fromTo("#{wrap_id}", {{opacity: 0, scale: 0.92}}, {{opacity: 1, scale: 1, duration: 0.35, '
                      f'ease: S.ease.ui}}, {_f(st)});')
            js.append(f'tl.set("#{wrap_id}", {{opacity: 0}}, {_f(st + d)});')
        elif c.fade_in or c.fade_out:
            if c.fade_in:
                js.append(f'tl.fromTo("#{in_id}", {{opacity: 0}}, {{opacity: 1, duration: {_f(c.fade_in)}, ease: "none"}}, {_f(st)});')
            if c.fade_out:
                js.append(f'tl.to("#{in_id}", {{opacity: 0, duration: {_f(c.fade_out)}, ease: "none"}}, {_f(st + d - c.fade_out)});')
        # Kamera anahtarları (punch-in / zoom / pan): klip yerel zamanı → pencere zamanı
        for k in sorted(c.keys, key=lambda k: k.t):
            at = st + k.t - lead
            props = f"scale: {_f(k.scale)}, xPercent: {_f(k.x)}, yPercent: {_f(k.y)}"
            if at < st:
                js.append(f'tl.set("#{in_id}", {{{props}}}, {_f(st)});')
            elif at <= st + d:
                if k.dur <= 0:
                    js.append(f'tl.set("#{in_id}", {{{props}}}, {_f(at)});')
                else:
                    js.append(f'tl.to("#{in_id}", {{{props}, duration: {_f(k.dur)}, ease: "{k.ease}"}}, {_f(at)});')
        # 9:16 yeniden kadraj yolu (yüz takibi): object-position x yüzdesi
        if c.reframe and not is_img:
            rf = json.loads((root / c.reframe).read_text(encoding="utf-8"))
            pts = [p for p in rf.get("path", []) if c.in_ + lead <= p["t"] <= c.in_ + lead + d * c.rate]
            prev = None
            for p in pts:
                at = st + (p["t"] - c.in_ - lead) / c.rate
                pos = f'"{p["pos"]:.1f}% 50%"'
                if prev is None:
                    js.append(f'tl.set("#{c.id}", {{objectPosition: {pos}}}, {_f(st)});')
                else:
                    js.append(f'tl.to("#{c.id}", {{objectPosition: {pos}, duration: {_f(max(at - prev, 0.04))}, '
                              f'ease: "sine.inOut"}}, {_f(prev)});')
                prev = at

    # --- overlay blokları
    for o in sorted(tl.overlays, key=lambda o: (o.z, o.start)):
        cut = window.clip(o.start, o.dur)
        if not cut:
            continue
        st, d, lead = cut
        if lead > 0.05:
            errors.append(f"uyarı: {o.id} pencere başında kırpıldı ({lead:.2f}s) — bölüm sınırını sahne sınırına koy")
        if o.block == "custom":
            if not o.src:
                errors.append(f"{o.id}: custom blok 'src' ister")
                continue
            src_file = paths.pj(root, o.src)
            if not src_file.exists():
                errors.append(f"{o.id}: custom sahne yok: {o.src}")
                continue
            dst = comp / "scenes" / src_file.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            # Sahnenin kendi klasörüne göreli varlıkları ("../assets/x.jpg" → edit/assets/x.jpg) comp/assets/'e
            # alınır ve comp/scenes/'e göre yeniden yazılır (HyperFrames "../" yolunu kompozisyon köküne taşır).
            def _asset(m, _base=src_file.parent):
                p = (_base / m.group(2)).resolve()
                return m.group(1) + "../" + assets.add(p) if p.is_file() else m.group(0)
            scene_txt = re.sub(r'((?:src=|href=|url\()["\']?)(\.\./[^"\'\)\s>]+)', _asset,
                               src_file.read_text(encoding="utf-8"))
            dst.write_text(scene_txt, encoding="utf-8")
            dom.append(f'<div id="{o.id}" data-composition-id="{o.id}" data-composition-src="scenes/{src_file.name}" '
                       f'data-start="{_f(st)}" data-duration="{_f(d)}" style="position:absolute;inset:0;z-index:{o.z}"></div>')
            continue
        b = all_blocks.get(o.block)
        if not b:
            errors.append(f"{o.id}: bilinmeyen blok '{o.block}' (vedit blocks ile listele)")
            continue
        errors += [f"{o.id}: {e}" for e in blk.validate_props(b, o.props)]
        props = dict(o.props)
        for k in b.image_props():
            if props.get(k):
                props[k] = assets.add(props[k])
        if o.block not in used_blocks:
            used_blocks.append(o.block)
        dom.append(f'<div id="{o.id}" class="clip blk-wrap" data-start="{_f(st)}" data-duration="{_f(d)}" '
                   f'style="z-index:{o.z}">{b.render_markup(props)}</div>')
        is_last = abs((o.start + o.dur) - tl.duration) < 0.05
        T = {"start": st, "dur": d, "id": o.id, "isLast": is_last}
        js.append(f'HF_BLOCKS[{_js(o.block)}](tl, document.querySelector("#{o.id} > .blk"), {_js(props)}, {_js(T)}, S);')

    # --- altyazılar
    cap_style = None
    if tl.captions and tl.captions.enabled and (root / tl.captions.src).exists():
        cap = json.loads((root / tl.captions.src).read_text(encoding="utf-8"))
        cap_style = tl.captions.style or cap.get("style") or studio_cfg.captions.style
        upper = ' style="text-transform: uppercase"' if studio_cfg.captions.uppercase else ""
        pages_html = []
        for i, pg in enumerate(cap["pages"]):
            cut = window.clip(pg["start"], pg["end"] - pg["start"])
            if not cut:
                continue
            st, d, _ = cut
            off = window.t0
            pid = f"cp{i}"
            if cap_style == "clean-sub":
                words = " ".join(html.escape(w["w"]) for w in pg["words"])
                pages_html.append(f'<div class="clip cap-page" id="{pid}" data-start="{_f(st)}" data-duration="{_f(d)}">'
                                  f'<span class="line-box">{words}</span></div>')
                continue
            spans = []
            for j, w in enumerate(pg["words"]):
                wid = f"{pid}w{j}"
                spans.append(f'<span class="cw" id="{wid}">{html.escape(w["w"])}</span>')
                ws, we = max(w["s"] - off, st), min(w["e"] - off, st + d)
                if cap_style in ("bold-pop", "odak"):  # odak: pop yok, yalnız okunan kelime turuncu
                    js.append(f'tl.set("#{wid}", {{attr: {{"data-on": "1"}}}}, {_f(ws)});')
                    if cap_style == "bold-pop":
                        js.append(f'tl.fromTo("#{wid}", {{scale: 0.82}}, {{scale: 1, duration: 0.12, ease: "back.out(2)"}}, {_f(ws)});')
                    nxt = pg["words"][j + 1]["s"] - off if j + 1 < len(pg["words"]) else st + d
                    js.append(f'tl.set("#{wid}", {{attr: {{"data-on": "0"}}}}, {_f(min(max(nxt, we), st + d))});')
                elif cap_style == "underline":  # söylenen kelime kalıcı olarak yanar + alt çizgi
                    js.append(f'tl.set("#{wid}", {{attr: {{"data-on": "1"}}}}, {_f(ws)});')
                else:  # karaoke
                    js.append(f'tl.set("#{wid}", {{attr: {{"data-on": "1", "data-cur": "1"}}}}, {_f(ws)});')
                    js.append(f'tl.set("#{wid}", {{attr: {{"data-cur": "0"}}}}, {_f(max(we, ws + 0.05))});')
            pages_html.append(f'<div class="clip cap-page" id="{pid}" data-start="{_f(st)}" data-duration="{_f(d)}"{upper}>'
                              + "".join(spans) + "</div>")
        if pages_html:
            dom.append(f'<div class="captions cap-{cap_style}" id="captions">' + "".join(pages_html) + "</div>")

    # --- ses: tek master parça (bölüm render'larında yok; sonradan mux)
    master = root / "build" / "master.wav"
    if include_audio and master.exists():
        src = assets.add(master)
        dom.append(f'<audio id="master" src="{src}" data-start="0" data-duration="{_f(dur)}" '
                   f'data-media-start="{_f(window.t0)}" data-volume="1"></audio>')

    # --- stil ve kök
    c = tokens["colors"]
    fonts = tokens["fonts"]
    cap_bottom = (max(sa.bottom * H + 4 * u, 0.27 * H) if H > W else sa.bottom * H + 7 * u)
    root_vars = {
        "--u": f"{u:.3f}px", "--u0": f"{u0:.3f}px", "--W": f"{W}px", "--H": f"{H}px",
        "--safe-t": f"{sa.top * H:.1f}px", "--safe-b": f"{sa.bottom * H:.1f}px",
        "--safe-l": f"{sa.left * W:.1f}px", "--safe-r": f"{sa.right * W:.1f}px",
        "--c-bg": tl.background if tl.background != "#0b0b0c" else c["bg"],
        "--c-surface": c["surface"], "--c-fg": c["fg"], "--c-muted": c["muted"], "--c-accent": c["accent"],
        "--c-on-accent": c.get("on_accent", "#000"), "--c-cap-fg": c["cap_fg"], "--c-cap-hl": c["cap_hl"],
        "--c-cap-stroke": c["cap_stroke"],
        "--f-display": f'"{fonts["display"]}", ui-sans-serif, system-ui, sans-serif',
        "--f-body": f'"{fonts["body"]}", ui-sans-serif, system-ui, sans-serif',
        "--f-mono": f'"{fonts.get("mono", "JetBrains Mono")}", ui-monospace, monospace',
        "--w-display": str(tokens.get("weights", {}).get("display", 800)),
        "--radius": f"{tokens.get('radius_u', 2) * u:.1f}px", "--grain": str(tokens.get("grain", 0)),
        "--cap-bottom": f"{cap_bottom:.1f}px",
        # portrait konuşmacı kartının yarı genişliği — glass-* blokları buna göre hizalanır
        "--portrait-ar": _f(next((c.aspect for c in tl.video if c.layout == "portrait" and c.aspect), 9 / 16)),
        "--card-half": "calc(var(--H) * 0.44 * var(--portrait-ar))",
    }
    # Stil paketine özel ek renkler (glass, glow, hud…) → --c-<ad>
    for k, v in c.items():
        root_vars.setdefault(f"--c-{k.replace('_', '-')}", v)
    root_css = ":root { " + " ".join(f"{k}: {v};" for k, v in root_vars.items()) + " }"
    font_css = assets.font_faces([fonts["display"], fonts["body"], fonts.get("mono", "JetBrains Mono")]
                                 + (["Montserrat"] if cap_style == "odak" else []))
    gsap = assets.add(paths.LIBRARY / "vendor" / "gsap.min.js")
    base_css = (paths.BLOCKS / "_base.css").read_text(encoding="utf-8")
    block_css = "\n".join(all_blocks[n].style for n in used_blocks)
    block_js = "\n".join(all_blocks[n].script for n in used_blocks)
    runtime = (paths.BLOCKS / "_runtime.js").read_text(encoding="utf-8")
    S = {"ease": tokens["ease"], "durations": tokens["durations"], "grain": tokens.get("grain", 0),
         "colors": c, "fps": fps}

    doc = f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" />
<!-- vedit build tarafından üretildi — ELLE DÜZENLEME; edit/timeline.json'u değiştir ve yeniden build et -->
<script src="{gsap}"></script>
<style>
{font_css}
{root_css}
html, body {{ width: {W}px; height: {H}px; }}
{base_css}
{block_css}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{_f(dur)}" data-width="{W}" data-height="{H}" data-fps="{fps}">
{chr(10).join(dom)}
</div>
<script>
{runtime}
{block_js}
const S = {_js(S)};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["main"] = tl;
</script>
</body>
</html>
"""
    return doc, errors


def _write_project_files(comp: Path, name: str) -> None:
    (comp / "hyperframes.json").write_text(json.dumps({
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
        "media": {"autoProxy": True}}, indent=2), encoding="utf-8")
    (comp / "meta.json").write_text(json.dumps({"id": name, "name": name}, indent=2), encoding="utf-8")


def chapter_hash(html_text: str, comp: Path) -> str:
    """Bölüm HTML'i + başvurduğu varlıkların boyut/mtime'ı → içerik özeti (render önbelleği)."""
    h = hashlib.sha1(html_text.encode())
    for ref in sorted(set(re.findall(r'(?:src|url\()="?(assets/[^"\)]+)', html_text))):
        p = comp / ref
        if p.exists():
            st = p.stat()
            h.update(f"{ref}:{st.st_size}:{int(st.st_mtime)}".encode())
    return h.hexdigest()[:12]


def run(root: Path, *, fmt_override: Format | None = None, out_name: str = "comp", lint: bool = True) -> dict:
    proj = project.load(root)
    studio_cfg = project.studio_for(proj)
    tl = load_json(root / "edit" / "timeline.json", Timeline)
    fmt = fmt_override or tl.format
    tokens = load_tokens(root, tl.style or proj.style)
    comp = root / out_name
    # comp/ üretilmiş alandır: eski HTML'leri temizle (assets hard-link'leri kalabilir)
    for old in [comp / "index.html", *comp.glob("chapters/*/index.html")]:
        old.unlink(missing_ok=True)
    comp.mkdir(parents=True, exist_ok=True)
    _write_project_files(comp, proj.id)
    doc, errors = compose(root, tl, window=Window(0, tl.duration), fmt=fmt, comp=comp, include_audio=True,
                          tokens=tokens, studio_cfg=studio_cfg, lang=proj.language)
    (comp / "index.html").write_text(doc, encoding="utf-8")
    result = {"comp": paths.rel(comp), "errors": errors, "chapters": []}
    if len(tl.chapters) > 1:
        for ch in tl.chapters:
            cdir = comp / "chapters" / ch.id
            cdir.mkdir(parents=True, exist_ok=True)
            _write_project_files(cdir, f"{proj.id}-{ch.id}")
            cdoc, cerr = compose(root, tl, window=Window(ch.start, ch.end), fmt=fmt, comp=cdir, include_audio=False,
                                 tokens=tokens, studio_cfg=studio_cfg, lang=proj.language)
            (cdir / "index.html").write_text(cdoc, encoding="utf-8")
            result["chapters"].append({"id": ch.id, "dir": paths.rel(cdir), "hash": chapter_hash(cdoc, cdir),
                                       "start": ch.start, "end": ch.end})
            errors += [f"[{ch.id}] {e}" for e in cerr if not e.startswith("uyarı")]
    if lint:
        result["lint"] = summarize_lint(hf.lint(comp))
    (root / "build").mkdir(exist_ok=True)
    (root / "build" / f"{out_name}_manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=1),
                                                              encoding="utf-8")
    return result


def summarize_lint(rep: dict) -> dict:
    if "raw" in rep:
        return {"error": rep["raw"][-600:]}
    findings = rep.get("findings") or rep.get("results") or []
    errs = [f for f in findings if f.get("severity") == "error"]
    warns = [f for f in findings if f.get("severity") == "warning"]
    short = lambda f: f"{f.get('code') or f.get('rule')}: {str(f.get('message', ''))[:140]}"  # noqa: E731
    return {"errors": len(errs), "warnings": len(warns), "top": [short(f) for f in (errs + warns)[:8]]}
