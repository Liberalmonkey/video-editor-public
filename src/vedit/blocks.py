"""blocks/*.block.html ayrıştırıcı + LLM için kompakt blok kataloğu.

Blok dosyası biçimi:
  <!--meta {json} -->   ad, açıklama, props şeması ("string*" = zorunlu), default_dur, sfx ipuçları, tags
  <style>…</style>      .blk-<ad> ile kapsamlı CSS
  <markup>…</markup>    {{prop}} yer tutuculu HTML (HTML-escape edilir)
  <script>…</script>    HF_BLOCKS["<ad>"] = function (tl, el, P, T, S) {…}
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import paths

_META = re.compile(r"<!--meta\s*(\{.*?\})\s*-->", re.S)
_STYLE = re.compile(r"<style>(.*?)</style>", re.S)
_MARKUP = re.compile(r"<markup>(.*?)</markup>", re.S)
_SCRIPT = re.compile(r"<script>(.*?)</script>", re.S)
_VAR = re.compile(r"\{\{\s*([a-zA-Z_][\w]*)\s*\}\}")
BLANK_IMG = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"


@dataclass
class Block:
    name: str
    meta: dict
    style: str
    markup: str
    script: str
    path: Path = field(repr=False, default=Path())

    @property
    def props(self) -> dict[str, str]:
        return self.meta.get("props", {})

    def required(self) -> list[str]:
        return [k for k, v in self.props.items() if str(v).endswith("*")]

    def image_props(self) -> list[str]:
        return [k for k, v in self.props.items() if str(v).rstrip("*") == "image"]

    def enum_default(self, key: str) -> str:
        m = re.match(r"enum\(([^)]*)\)", str(self.props.get(key, "")).rstrip("*"))
        return m.group(1).split("|")[0] if m else ""

    def render_markup(self, props: dict) -> str:
        def sub(m: re.Match) -> str:
            k = m.group(1)
            v = props.get(k)
            if v is None or v == "":
                if k in self.image_props():
                    return BLANK_IMG
                return self.enum_default(k)
            return html.escape(str(v), quote=True)
        return _VAR.sub(sub, self.markup.strip())


def parse(path: Path) -> Block:
    text = path.read_text(encoding="utf-8")
    m = _META.search(text)
    if not m:
        raise ValueError(f"{path.name}: <!--meta {{…}} --> yok")
    meta = json.loads(m.group(1))
    get = lambda rx: (rx.search(text).group(1).strip() if rx.search(text) else "")  # noqa: E731
    return Block(name=meta["name"], meta=meta, style=get(_STYLE), markup=get(_MARKUP), script=get(_SCRIPT), path=path)


def load_all(extra_dirs: list[Path] | None = None) -> dict[str, Block]:
    out: dict[str, Block] = {}
    for d in [paths.BLOCKS, *(extra_dirs or [])]:
        if d.exists():
            for p in sorted(d.glob("*.block.html")):
                b = parse(p)
                out[b.name] = b
    return out


def validate_props(block: Block, props: dict) -> list[str]:
    errs = [f"{block.name}: zorunlu prop eksik '{k}'" for k in block.required() if props.get(k) in (None, "", [])]
    unknown = set(props) - set(block.props)
    if unknown:
        errs.append(f"{block.name}: bilinmeyen prop {sorted(unknown)} (geçerli: {sorted(block.props)})")
    return errs


def catalog(tag: str | None = None) -> str:
    """LLM'in okuyacağı tek satırlık blok listesi (~40 token/blok)."""
    lines = []
    for b in load_all().values():
        if tag and tag not in b.meta.get("tags", []):
            continue
        props = ", ".join(f"{k}:{v}" for k, v in b.props.items())
        lines.append(f"- {b.name} ({b.meta.get('default_dur', 3)}s) — {b.meta['description']} | props: {props}")
    return "\n".join(lines)
