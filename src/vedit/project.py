"""Proje iskeleti ve durum makinesi.

`project.yaml` her adımın bitip bitmediğini tutar; `/video next` yalnızca `vedit status`
çıktısını okuyarak ne yapılacağını bilir (tüm dosyaları taramaya gerek kalmaz).
"""

from __future__ import annotations

import datetime as dt
import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from . import paths
from .schemas import Project, ProjectState, StudioConfig, load_yaml, save_yaml


@dataclass(frozen=True)
class Step:
    name: str
    kind: str          # script | agent | user | gate
    who: str           # komut ya da ajan adı
    output: str        # tamamlandığını gösteren dosya (proje göreli) — boşsa durumdan okunur
    hint: str
    optional: bool = False


FOOTAGE_STEPS = [
    Step("brief", "gate", "ana oturum", "brief.md", "Kullanıcıyla brief.md yaz (amaç, hedef kitle, hook fikri, CTA, süre, referans) ve onay al."),
    Step("plan_shoot", "agent", "director", "direction/shoot-plan.md", "Çekim öncesi: ışık/ses/açı/plan listesi. Çekim zaten yapıldıysa atla.", optional=True),
    Step("ingest", "script", "vedit ingest", "analysis/media_index.json", "input/ içine dosyaları koy, sonra çalıştır."),
    Step("transcribe", "script", "vedit transcribe", "analysis/transcript.json", "Konuşmalı kliplerin kelime zamanları."),
    Step("digest", "script", "vedit digest", "analysis/digest.txt", "LLM için kompakt transkript + sessizlik/tekrar işaretleri."),
    Step("edit_plan", "gate", "ana oturum", "edit/edl.json", "Ana oturum digest'ten edl.json yazar; kullanıcıya kurgu planını özetle ve onay al."),
    Step("cut", "script", "vedit cut", "build/aroll.mp4", "EDL → A-roll + zaman eşlemesi."),
    Step("audio", "script", "vedit audio", "build/voice.wav", "Konuşma temizleme zinciri."),
    Step("captions", "script", "vedit captions", "edit/captions.json", "Eşlenmiş transkriptten altyazı sayfaları + SRT."),
    Step("design", "agent", "director → editor", "edit/timeline.json", "Overlay/B-roll/punch-in/altyazı stili ile timeline.json."),
    Step("assets", "user", "kullanıcı indirir", "", "direction/assets-request.md'deki müzik/SFX/motion listesini kullanıcı indirip belirtilen klasörlere koyar; sonra vedit sfx index + vedit mark assets."),
    Step("sfx", "script", "vedit sfx cues + editor", "audio/sfx_resolved.json", "Kural tabanlı ipuçları + anlamsal ipuçları → resolve."),
    Step("mix", "script", "vedit mix", "build/master.wav", "Konuşma + müzik (ducking) + SFX → -14 LUFS master."),
    Step("build", "script", "vedit build", "comp/index.html", "timeline.json → HyperFrames kompozisyonu (+ lint)."),
    Step("preview", "script", "vedit render preview", "renders/preview.mp4", "Taslak render."),
    Step("qa", "script", "vedit qa", "qa/report.json", "Otomatik ölçümler + kontak sayfası."),
    Step("critique", "gate", "director", "qa/critique.md", "director (critique) rubrikle puanlar; P0/P1 düzelt (en fazla 2 tur); kullanıcı onayı."),
    Step("final", "script", "vedit render final", "renders/final.mp4", "Yüksek kalite render."),
    Step("export", "script", "vedit export", "renders/export.json", "Platform varyantları, SRT, kapak önerileri."),
]

ANIMATION_STEPS = [
    Step("brief", "gate", "ana oturum", "brief.md", "Konu, hedef kitle, ton (eğitici/eğlenceli), süre, referans linkler/görseller; onay al."),
    Step("reference", "agent", "vedit reference → director", "analysis/style-grammar.md", "Referansları analiz et (stüdyoda style-grammar.md varsa yeniden kullan)."),
    Step("outline", "gate", "writer", "script/outline.md", "Bölümler, hook, açık döngüler; onay al."),
    Step("script", "gate", "writer", "script/script.md", "Tam senaryo + humanizer geçişi; onay al."),
    Step("voiceover", "user", "kullanıcı (harici ses aracı)", "input/vo.wav", "Kullanıcıya script/teleprompter.md verilir; kendi klon sesiyle seslendirip input/vo.wav olarak geri verir."),
    Step("transcribe", "script", "vedit transcribe", "analysis/transcript.json", "Seslendirmenin kelime zamanları."),
    Step("audio", "script", "vedit audio", "build/voice.wav", "Seslendirme temizleme zinciri."),
    Step("scenes", "gate", "director", "direction/scenes.json", "Sahne listesi (blok/hero), hareket dili, geçiş aileleri; onay al."),
    Step("align", "script", "vedit align", "direction/scenes.aligned.json", "Sahne sürelerini seslendirmeye hizala."),
    Step("design", "agent", "vedit scenes2timeline → editor", "edit/timeline.json", "Blok sahneler otomatik; hero/custom sahneleri editor yazar."),
    Step("captions", "script", "vedit captions", "edit/captions.json", "Altyazı (YouTube'da opsiyonel, SRT her zaman)."),
    Step("assets", "user", "kullanıcı indirir", "", "direction/assets-request.md'deki müzik/SFX/motion listesini kullanıcı indirip belirtilen klasörlere koyar; sonra vedit sfx index + vedit mark assets."),
    Step("sfx", "script", "vedit sfx cues + editor", "audio/sfx_resolved.json", "Ses tasarımı."),
    Step("mix", "script", "vedit mix", "build/master.wav", "Master ses."),
    Step("build", "script", "vedit build", "comp/index.html", "Kompozisyon (+ bölümler)."),
    Step("preview", "script", "vedit render preview", "renders/preview.mp4", "Bölüm bazlı taslak render."),
    Step("qa", "script", "vedit qa", "qa/report.json", "Otomatik ölçümler."),
    Step("critique", "gate", "director", "qa/critique.md", "Bölüm bölüm eleştiri, düzeltme, onay."),
    Step("final", "script", "vedit render final", "renders/final.mp4", "Final render (değişmeyen bölümler cache'ten)."),
    Step("export", "script", "vedit export", "renders/export.json", "SRT, YouTube bölüm listesi, kapak önerileri."),
]


def steps_for(pipeline: str) -> list[Step]:
    return ANIMATION_STEPS if pipeline == "animation" else FOOTAGE_STEPS


def slugify(text: str) -> str:
    table = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    text = unicodedata.normalize("NFKD", text.translate(table)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "proje"


def load_studio(name: str) -> StudioConfig:
    return load_yaml(paths.studio_dir(name) / "studio.yaml", StudioConfig)


def studio_for(proj: Project) -> StudioConfig:
    """Stüdyo ayarları + projenin `studio_overrides` alanı (sözlükler alan bazında birleşir)."""
    base = load_studio(proj.studio)
    if not proj.studio_overrides:
        return base
    data = base.model_dump()
    for k, v in proj.studio_overrides.items():
        data[k] = {**data[k], **v} if isinstance(v, dict) and isinstance(data.get(k), dict) else v
    return StudioConfig.model_validate(data)


def create(studio: str, title: str, *, pipeline: str | None = None, language: str | None = None) -> Path:
    cfg = load_studio(studio)
    today = dt.date.today().isoformat()
    pid = f"{today}-{slugify(title)}"
    paths.studio_dir(studio)  # stüdyo adını doğrular
    root = paths.OUTPUTS / studio / pid / "work"
    if root.exists():
        raise SystemExit(f"Proje zaten var: {paths.rel(root)}")
    pipe = pipeline or ("footage" if cfg.pipeline == "mixed" else cfg.pipeline)
    for d in paths.PROJECT_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
    paths.input_dir(root).mkdir(parents=True, exist_ok=True)
    proj = Project(id=pid, studio=studio, title=title, pipeline=pipe, language=language or cfg.language,
                   created=today, format=cfg.format, style=cfg.style, state=ProjectState(step="brief"))
    save_yaml(root / "project.yaml", proj)
    tpl = paths.ROOT / "templates" / "video-brief.md"
    if tpl.exists():
        text = tpl.read_text(encoding="utf-8").replace("{{title}}", title).replace("{{studio}}", cfg.label)
        (root / "brief.md").write_text(text.replace("{{pipeline}}", pipe), encoding="utf-8")
    return root


def load(root: Path) -> Project:
    return load_yaml(root / "project.yaml", Project)


def save(root: Path, proj: Project) -> None:
    save_yaml(root / "project.yaml", proj)


def mark(root: Path, step: str, *, gate: str | None = None) -> None:
    """Adımı tamamlandı say; gate verilirse onay durumunu yaz."""
    proj = load(root)
    if step not in proj.state.done:
        proj.state.done.append(step)
    if gate:
        proj.state.gates[step] = gate  # type: ignore[assignment]
    nxt = next_step(root, proj)
    proj.state.step = nxt.name if nxt else "done"
    save(root, proj)


def is_done(root: Path, proj: Project, st: Step) -> bool:
    if st.kind == "gate":
        if proj.auto_approve and paths.pj(root, st.output).exists():
            return True
        return proj.state.gates.get(st.name) in ("approved", "skipped")
    if st.name in proj.state.done:
        return True
    return bool(st.output) and paths.pj(root, st.output).exists()


def next_step(root: Path, proj: Project) -> Step | None:
    """İlk tamamlanmamış zorunlu adım. Opsiyonel adımlar akışı asla bloklamaz."""
    for st in steps_for(proj.pipeline):
        if not st.optional and not is_done(root, proj, st):
            return st
    return None


def status_text(root: Path) -> str:
    proj = load(root)
    lines = [f"Proje: {proj.title} [{proj.studio} · {proj.pipeline} · {proj.language} · "
             f"{proj.format.width}x{proj.format.height}@{proj.format.fps}]",
             f"Klasör: {paths.rel(root)}"]
    nxt = next_step(root, proj)
    for st in steps_for(proj.pipeline):
        mark_ = "✓" if is_done(root, proj, st) else ("·" if st.optional else " ")
        flag = " ← SIRADAKİ" if nxt and st.name == nxt.name else ""
        gate = f" [onay: {proj.state.gates.get(st.name, 'bekliyor')}]" if st.kind == "gate" else ""
        lines.append(f" [{mark_}] {st.name:<11} {st.kind:<6} {st.who}{gate}{flag}")
    if nxt:
        lines.append(f"Sıradaki: {nxt.name} — {nxt.hint}")
    else:
        lines.append("Tüm adımlar tamam.")
    return "\n".join(lines)


def copy_into(root: Path, files: list[Path]) -> list[Path]:
    out = []
    for f in files:
        dst = paths.input_dir(root) / f.name
        if not dst.exists():
            try:
                dst.hardlink_to(f)
            except OSError:
                shutil.copy2(f, dst)
        out.append(dst)
    return out
