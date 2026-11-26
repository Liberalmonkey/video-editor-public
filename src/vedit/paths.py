"""Proje kökü, stüdyolar, kütüphane ve proje klasörü çözümleme."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDIOS = ROOT / "studios"
LIBRARY = ROOT / "library"
BLOCKS = ROOT / "blocks"
SFX_DIR = LIBRARY / "sfx"
MUSIC_DIR = LIBRARY / "music"
MOTION_DIR = LIBRARY / "motion"
FONTS_DIR = LIBRARY / "fonts"
# WHY: bkz. wiki/decisions/0017-terminal-hizli-hat.md. Video girdisi ve çıktısı yalnız burada durur.
INPUTS = ROOT / "Projeler" / "inputs"    # <stüdyo>/<proje>/: ham çekim, görsel, senaryo
OUTPUTS = ROOT / "Projeler" / "outputs"  # <stüdyo>/<proje>/: teslim; work/: tüm ara dosyalar
REFERENCES = INPUTS / "_referanslar"

STUDIO_NAMES = ("youtube-animasyon", "ugc", "instagram")

# Her projede oluşturulan alt klasörler
PROJECT_DIRS = (
    "analysis", "script", "direction", "edit", "audio",
    "build", "comp", "renders", "qa",
)


def studio_dir(name: str) -> Path:
    if name not in STUDIO_NAMES:
        raise SystemExit(f"Bilinmeyen stüdyo '{name}'. Seçenekler: {', '.join(STUDIO_NAMES)}")
    return STUDIOS / name


def find_project(ref: str | Path | None) -> Path:
    """Proje klasörünü bul: yol, slug ya da (boşsa) içinde bulunulan klasör."""
    if ref is None:
        cur = Path.cwd().resolve()
        for p in (cur, *cur.parents):
            if (p / "project.yaml").exists():
                return p
        raise SystemExit("Proje bulunamadı: proje klasöründe çalış ya da proje adını ver.")
    p = Path(ref)
    if (p / "project.yaml").exists():
        return p.resolve()
    matches = [d for d in OUTPUTS.glob(f"*/*{ref}*/work") if (d / "project.yaml").exists()]
    if len(matches) == 1:
        return matches[0]
    # Tam ad öncelikli: `arvelior`, `arvelior-hiz` varken belirsiz sayılmaz.
    s = str(ref).replace("\\", "/").rstrip("/")
    tam = [m for m in matches if s in (m.parent.name, f"{m.parent.parent.name}/{m.parent.name}")]
    if len(tam) == 1:
        return tam[0]
    if not matches:
        raise SystemExit(f"Proje bulunamadı: {ref}")
    raise SystemExit("Birden fazla proje eşleşti: " + ", ".join(str(m.relative_to(ROOT)) for m in matches))


def input_dir(root: Path) -> Path:
    """Proje kökünün (…/outputs/<stüdyo>/<proje>/work) girdi klasörü."""
    return INPUTS / root.resolve().parent.parent.name / root.resolve().parent.name


def pj(root: Path, rel_path: str | Path) -> Path:
    """Proje göreli yol: `input/…` girdi klasörüne, gerisi work/ altına çözülür."""
    s = Path(rel_path).as_posix()
    return input_dir(root) / s[6:] if s.startswith("input/") else root / rel_path


def rel(p: Path) -> str:
    """Kök dizine göreli, eğik çizgili yol (çıktılarda kısa görünmesi için)."""
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()
