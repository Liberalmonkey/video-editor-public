"""AI motorları tek tabloda: Claude Code, Antigravity, Codex, OpenCode.

WHY: bkz. wiki/decisions/0026-arayuzde-ajan.md. Stüdyo AI paneli, `vedit ai-edit` ve `vedit stil-uret` aynı tabloyu okur;
motorun yolu, model listesi, argümanı ve akış çevirisi burada bir kez yazılır. Her motor terminal CLI'ıdır, argüman
listesiyle ve kabuksuz çalışır; izin atlatma bayrağı (`--dangerously-*`, `--auto`) hiçbir motorda kullanılmaz.

Windows notu: npm `.cmd` shim'i Popen'a verilmez. cmd.exe istemdeki `& | ^ %` karakterlerini yorumlar (kabuk enjeksiyonu)
ve nvm `.shim` boşluklu yolda kırılır. Bu yüzden paketin içindeki gerçek ikili aranır.
"""

from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable

WIN = os.name == "nt"
OTURUM = re.compile(r"[\w\-]{8,80}")


# ---------------------------------------------------------------- ikili bulma

def _node_kokleri(ad: str) -> list[Path]:
    """Global npm kökleri: %APPDATA%/npm, nvm sürümleri (NVM_HOME ya da shim'in iki üstü) ve `ad` komutunun dizini."""
    kokler: list[Path] = []
    if os.environ.get("APPDATA"):
        kokler.append(Path(os.environ["APPDATA"]) / "npm")
    nvm = [Path(os.environ["NVM_HOME"])] if os.environ.get("NVM_HOME") else []
    for aday in (shutil.which(ad), shutil.which(ad + ".cmd") if WIN else None):
        if aday:
            p = Path(aday).parent
            kokler.append(p)
            if p.name in (".nodejs", ".shim"):
                nvm.append(p.parent)
    for n in nvm:
        kokler += sorted((n / "installs").glob("*")) if (n / "installs").is_dir() else []
    kokler += [Path(p).parent.parent / "lib" for p in (shutil.which(ad),) if p and not WIN]
    gorulen, sonuc = set(), []
    for k in kokler:
        if k not in gorulen and (k / "node_modules").is_dir():
            gorulen.add(k)
            sonuc.append(k)
    return sonuc


def _npm_ikili(ad: str, desenler: list[str]) -> str | None:
    """npm paketinin içindeki yerel ikili. Birden çok kurulum varsa en yenisi (değişme zamanı); baseline yapısı sonra."""
    bulunan = {Path(f) for k in _node_kokleri(ad) for d in desenler for f in glob.glob(str(k / "node_modules" / d))}
    bulunan = [f for f in bulunan if f.is_file()]
    if not bulunan:
        return None
    return str(max(bulunan, key=lambda f: (f.stat().st_mtime, "baseline" not in str(f))))


def _which_exe(ad: str) -> str | None:
    """PATH'teki gerçek ikili; Windows'ta yalnız .exe (shim .cmd/.ps1 değil)."""
    p = shutil.which(ad)
    if not p:
        return None
    if WIN and Path(p).suffix.lower() != ".exe":
        return None
    return p


def _claude_bul() -> list[str] | None:
    p = _which_exe("claude")
    return [p] if p else None


def _agy_bul() -> list[str] | None:
    from . import gorsel
    try:
        return [gorsel.agy_yolu()]
    except SystemExit:
        return None


def _codex_bul() -> list[str] | None:
    ikili = _npm_ikili("codex", ["@openai/codex/node_modules/@openai/codex-*/vendor/*/bin/codex.exe",
                                 "@openai/codex/node_modules/@openai/codex-*/vendor/*/bin/codex",
                                 "@openai/codex-*/vendor/*/bin/codex.exe"])
    if ikili:
        return [ikili]
    js, node = _npm_ikili("codex", ["@openai/codex/bin/codex.js"]), shutil.which("node")
    if js and node:
        return [node, js]
    p = _which_exe("codex")
    return [p] if p else None


def _opencode_bul() -> list[str] | None:
    ikili = _npm_ikili("opencode", ["@opencode/cli/bin/opencode.exe", "@opencode/cli/bin/opencode",
                                    "opencode-ai/node_modules/opencode-windows-*/bin/opencode.exe",
                                    "opencode-ai/node_modules/opencode-*/bin/opencode"])
    if ikili:
        return [ikili]
    p = _which_exe("opencode")
    if p and WIN and Path(p).stat().st_size < 5_000_000:
        return None  # WHY: nvm .shim (≈0,5 MB) boşluklu yolda cmd.exe'ye düşer; gerçek ikili ≈200 MB
    return [p] if p else None


# ---------------------------------------------------------------- model listeleri

def _model(id_: str, ad: str, grup: str, **ek) -> dict:
    return {"id": id_, "ad": ad, "grup": grup, **ek}


CLAUDE_MODELLER = [
    _model("sonnet", "Sonnet (en güncel)", "Takma ad"), _model("opus", "Opus (en güncel)", "Takma ad"),
    _model("haiku", "Haiku (en güncel)", "Takma ad"), _model("fable", "Fable (en güncel)", "Takma ad"),
    _model("claude-fable-5-2", "Claude Fable 5.2", "Sürüm"), _model("claude-opus-5-5", "Claude Opus 5.5", "Sürüm"),
    _model("claude-sonnet-5-5", "Claude Sonnet 5.5", "Sürüm"), _model("claude-haiku-5-5", "Claude Haiku 5.5", "Sürüm"),
]


def _calistir(bas: list[str], *args: str, timeout: int = 60) -> str:
    r = subprocess.run([*bas, *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                       stdin=subprocess.DEVNULL, env={**os.environ, "NO_COLOR": "1"})
    return r.stdout


def _claude_modeller(bas: list[str]) -> tuple[list[dict], str | None]:
    return list(CLAUDE_MODELLER), "sonnet"


AGY_GRUP = (("gemini", "Gemini"), ("claude", "Claude"), ("gpt", "GPT"))


def agy_ayristir(metin: str) -> list[dict]:
    """`agy models`: `kimlik<TAB>ad` satırları; sekmesiz satır (ör. "Fetching…") atlanır."""
    sonuc = []
    for satir in metin.splitlines():
        a, sekme, b = satir.partition("\t")
        if sekme and a.strip() and b.strip():
            grup = next((g for on, g in AGY_GRUP if a.startswith(on)), "Diğer")
            sonuc.append(_model(a.strip(), b.strip(), grup))
    return sonuc


def _agy_modeller(bas: list[str]) -> tuple[list[dict], str | None]:
    m = agy_ayristir(_calistir(bas, "models"))
    return m, (m[0]["id"] if m else None)


def _codex_ev() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def codex_ayristir(katalog: dict) -> list[dict]:
    """`codex debug models` kataloğu → görünür modeller öncelik sırasıyla."""
    ham = [m for m in katalog.get("models", []) if isinstance(m, dict) and m.get("slug") and m.get("visibility", "list") == "list"]
    ham.sort(key=lambda m: m.get("priority", 99))
    return [_model(m["slug"], m.get("display_name") or m["slug"], "OpenAI", aciklama=m.get("description", "")) for m in ham]


def _codex_varsayilan() -> str | None:
    try:
        metin = (_codex_ev() / "config.toml").read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r'^model\s*=\s*"([^"]+)"', metin, re.M)  # WHY: tomllib 3.11+; üst düzey tek anahtar yeter
    return m.group(1) if m else None


def _codex_modeller(bas: list[str]) -> tuple[list[dict], str | None]:
    # WHY: `models_cache.json`'u Codex masaüstü uygulaması da yazar; orada CLI'ın desteklemediği model olabilir
    # (2026-11-17: config'teki gpt-6-luna CLI 0.154'te "not supported" döndü). Kaynak CLI'ın kendi kataloğudur.
    try:
        katalog = json.loads(_calistir(bas, "debug", "models", timeout=30) or "{}")
    except (OSError, subprocess.SubprocessError, ValueError):
        katalog = {}
    if not katalog.get("models"):
        try:
            katalog = json.loads((_codex_ev() / "models_cache.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            katalog = {}
    m = codex_ayristir(katalog)
    varsayilan = _codex_varsayilan()
    return m, varsayilan if any(x["id"] == varsayilan for x in m) else (m[0]["id"] if m else None)


OPENCODE_SAGLAYICI = {"opencode": "OpenCode Zen", "openai": "OpenAI", "anthropic": "Anthropic", "openrouter": "OpenRouter",
                      "google": "Google", "cloudflare-workers-ai": "Cloudflare Workers AI", "github-copilot": "GitHub Copilot",
                      "groq": "Groq", "mistral": "Mistral", "deepseek": "DeepSeek", "xai": "xAI"}
OPENCODE_SIRA = ("opencode", "anthropic", "openai", "google", "openrouter")


def opencode_ayristir(metin: str) -> list[dict]:
    """`opencode models`: `sağlayıcı/model` satırları. Grup sağlayıcıdır; ücretsiz Zen önce, sonra büyük sağlayıcılar."""
    sonuc = []
    for satir in metin.splitlines():
        s = satir.strip()
        saglayici, bolu, ad = s.partition("/")
        if not bolu or not ad or " " in s:
            continue
        ucretsiz = saglayici == "opencode" or ad.endswith(("-free", ":free"))
        grup = OPENCODE_SAGLAYICI.get(saglayici) or saglayici.replace("-", " ").title()
        sonuc.append(_model(s, ad, grup, saglayici=saglayici, **({"ucretsiz": True} if ucretsiz else {})))
    sira = {s: i for i, s in enumerate(OPENCODE_SIRA)}
    sonuc.sort(key=lambda m: (sira.get(m["saglayici"], len(sira)), m["saglayici"]))  # kararlı: sağlayıcı içi sıra korunur
    return sonuc


def _opencode_varsayilan() -> str | None:
    ev = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "opencode"
    for ad in ("opencode.json", "opencode.jsonc", "config.json"):
        try:
            m = re.search(r'"model"\s*:\s*"([^"]+/[^"]+)"', (ev / ad).read_text(encoding="utf-8"))
        except OSError:
            continue
        if m:
            return m.group(1)
    return None


def _opencode_modeller(bas: list[str]) -> tuple[list[dict], str | None]:
    m = opencode_ayristir(_calistir(bas, "models", timeout=90))
    ids = {x["id"] for x in m}
    varsayilan = next((v for v in (_opencode_varsayilan(), "opencode/big-pickle") if v in ids), m[0]["id"] if m else None)
    return m, varsayilan


# ---------------------------------------------------------------- argümanlar

def _claude_arg(istem: str, model: str | None, mod: str, oturum: str | None) -> list[str]:
    return ["-p", istem, *(["--model", model] if model else []), "--output-format", "stream-json", "--verbose",
            "--permission-mode", {"duzenle": "acceptEdits", "plan": "plan"}[mod], *(["--resume", oturum] if oturum else [])]


def _agy_arg(istem: str, model: str | None, mod: str, oturum: str | None) -> list[str]:
    return ["-p", istem, *(["--model", model] if model else []), "--output-format", "stream-json",
            "--mode", {"duzenle": "accept-edits", "plan": "plan"}[mod], *(["--conversation", oturum] if oturum else [])]


def _codex_arg(istem: str, model: str | None, mod: str, oturum: str | None) -> list[str]:
    # WHY: `exec resume` -s almaz; sandbox ikisinde de -c ile verilir. Düzenle: çalışma alanına yazar; plan: salt okunur.
    sandbox = {"duzenle": "workspace-write", "plan": "read-only"}[mod]
    return ["exec", *(["resume", oturum] if oturum else []), "--json", "-c", f'sandbox_mode="{sandbox}"',
            *(["-m", model] if model else []), istem]


def _opencode_arg(istem: str, model: str | None, mod: str, oturum: str | None) -> list[str]:
    return ["run", "--format", "json", *(["-m", model] if model else []), "--agent", {"duzenle": "build", "plan": "plan"}[mod],
            *(["-s", oturum] if oturum else []), istem]


# ---------------------------------------------------------------- tablo

@dataclass(frozen=True)
class Motor:
    ad: str
    bul: Callable[[], list[str] | None]
    modeller: Callable[[list[str]], tuple[list[dict], str | None]]
    arguman: Callable[[str, str | None, str, str | None], list[str]]
    kurulum: str
    mod_ipucu: dict


MOTORLAR: dict[str, Motor] = {
    "claude": Motor("Claude Code", _claude_bul, _claude_modeller, _claude_arg,
                    "Claude Code'u kur, terminalde bir kez `claude` ile giriş yap.",
                    {"duzenle": "Dosya düzenler (acceptEdits)", "plan": "Okur ve önerir, dosyaya dokunmaz"}),
    "antigravity": Motor("Antigravity", _agy_bul, _agy_modeller, _agy_arg,
                         "PowerShell: `irm https://antigravity.google/cli/install.ps1 | iex`, sonra `agy` ile giriş.",
                         {"duzenle": "Dosya düzenler (accept-edits)", "plan": "Okur ve önerir, dosyaya dokunmaz"}),
    "codex": Motor("Codex", _codex_bul, _codex_modeller, _codex_arg,
                   "`npm i -g @openai/codex`, sonra terminalde `codex login`.",
                   {"duzenle": "Proje klasörüne yazar (workspace-write sandbox)", "plan": "Salt okunur sandbox, dosyaya dokunmaz"}),
    "opencode": Motor("OpenCode", _opencode_bul, _opencode_modeller, _opencode_arg,
                      "`npm i -g opencode-ai`, sonra `opencode auth login` ile sağlayıcı ekle.",
                      {"duzenle": "build ajanı: dosya düzenler", "plan": "plan ajanı: okur ve önerir"}),
}
MODLAR = ("duzenle", "plan")


def bas(motor: str) -> list[str] | None:
    """Motorun komut başı (ikili ya da node + betik); kurulu değilse None."""
    return MOTORLAR[motor].bul() if motor in MOTORLAR else None


# WHY: bkz. wiki/decisions/0044-ekip-motoru.md. Akıl yürütme seviyesi motor başına farklı bayraktır; OpenCode'da
# seviye model adının `#variant` ekidir ve burada verilmez. Bypass bayrağı hiçbir motorda eklenmez.
SEVIYELER = {"claude": ("low", "medium", "high", "xhigh", "max"), "antigravity": ("low", "medium", "high", "xhigh", "max"),
             "codex": ("minimal", "low", "medium", "high"), "opencode": ()}


def seviye_arg(motor: str, seviye: str | None) -> list[str]:
    if not seviye:
        return []
    if seviye not in SEVIYELER.get(motor, ()):
        raise SystemExit(f"{MOTORLAR[motor].ad} için seviye {', '.join(SEVIYELER[motor]) or 'yok'} olmalı: {seviye}")
    if motor == "codex":
        return ["-c", f'model_reasoning_effort="{seviye}"']
    return ["--effort", seviye]


def komut(motor: str, istem: str, model: str | None, mod: str = "duzenle", oturum: str | None = None,
          seviye: str | None = None) -> list[str]:
    """Tam komut. '-' ile başlayan istem bayrak sanılmasın diye boşlukla başlar."""
    if motor not in MOTORLAR:
        raise SystemExit(f"Motor {', '.join(MOTORLAR)} olmalı: {motor}")
    b = bas(motor)
    if not b:
        raise SystemExit(f"{MOTORLAR[motor].ad} kurulu değil. {MOTORLAR[motor].kurulum}")
    istem = " " + istem if istem.startswith("-") else istem
    if model is None and motor == "codex":
        model = _codex_modeller(b)[1]  # WHY: config'teki model CLI'da desteklenmeyebilir; bkz. _codex_modeller
    arg = MOTORLAR[motor].arguman(istem, model, mod, oturum)
    if seviye:
        # Seviye bayrağı istemden önce: agy ve claude'da `-p <istem>` sonda kalmalı, codex'te istem son konumsal argüman.
        ek = seviye_arg(motor, seviye)
        i = arg.index("-p") if "-p" in arg else len(arg) - 1
        arg = [*arg[:i], *ek, *arg[i:]]
    return [*b, *arg]


def _surum(b: list[str]) -> str:
    try:
        cikti = _calistir(b, "--version", timeout=20).strip().splitlines()
        return cikti[0] if cikti else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _tara(anahtar: str) -> dict:
    m = MOTORLAR[anahtar]
    d = {"ad": m.ad, "kurulu": False, "surum": "", "modeller": [], "varsayilan": None, "kurulum": m.kurulum,
         "mod_ipucu": m.mod_ipucu, "seviyeler": list(SEVIYELER.get(anahtar, ()))}
    try:
        b = m.bul()
        if not b:
            return d
        d["kurulu"] = True
        d["surum"] = _surum(b)
        d["modeller"], d["varsayilan"] = m.modeller(b)
        if not d["modeller"]:
            d["hata"] = "Model listesi boş; giriş yapıldı mı?"
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        d["hata"] = f"Tarama hatası: {e}"[:300]
    return d


@lru_cache(maxsize=1)
def durum() -> dict:
    """Dört motor paralel taranır (agy ağ ister, opencode yüzlerce model listeler). Sunucu ömrü boyunca bir kez."""
    with ThreadPoolExecutor(max_workers=len(MOTORLAR)) as h:
        return dict(zip(MOTORLAR, h.map(_tara, MOTORLAR)))


# ---------------------------------------------------------------- akış çevirisi

_ARAC_ANAHTAR = ("file_path", "filePath", "command", "pattern", "path", "url", "query", "description")
_KOMUT_SARMA = re.compile(r"""-Command\s+(['"])(.*)\1\s*$""", re.S)


def _arac(ad: str, girdi: dict) -> str:
    hedef = next((str(girdi[k]) for k in _ARAC_ANAHTAR if girdi.get(k)), "")
    return f"→ {ad} {hedef[:160]}".rstrip()


def _ic_mesaj(m) -> str:
    """Codex hata mesajı çoğu kez iç içe JSON'dur; en içteki `message` alınır."""
    for _ in range(3):
        if not isinstance(m, str):
            break
        try:
            o = json.loads(m)
        except ValueError:
            break
        if not isinstance(o, dict):
            break
        m = (o.get("error") or {}).get("message") if isinstance(o.get("error"), dict) else o.get("message", m)
    return str(m or "")[:300]


GURULTU = ("Reading additional input from stdin",)


def cevirici():
    """Dört motorun JSON akış satırını okunur günlük satırına çevirir; oturum kimliğini işe yazar. JSON değilse satır aynen.

    Claude `stream-json` (type: system/assistant/result), Antigravity (event: …), Codex `--json` (type: thread.started,
    item.completed, turn.completed …), OpenCode `--format json` (sessionID + type: text/tool_use/step_finish/error).
    """
    tampon: list[str] = []
    durum_ = {"t0": None, "model_yazildi": False}

    def model_satiri(is_) -> list[str]:
        if durum_["model_yazildi"] or not getattr(is_, "model", None):
            return []
        durum_["model_yazildi"] = True
        return [f"Model: {is_.model}"]

    def cevir(is_, satir: str) -> list[str]:
        try:
            o = json.loads(satir)
        except ValueError:
            return [satir] if satir and not satir.startswith(GURULTU) else []
        if not isinstance(o, dict):
            return [satir]
        t = o.get("type")
        # OpenCode: her olayda sessionID vardır (Claude session_id yazar)
        if "sessionID" in o:
            is_.oturum = o.get("sessionID") or is_.oturum
            ts = o.get("timestamp")
            if durum_["t0"] is None and isinstance(ts, (int, float)):
                durum_["t0"] = ts
            p = o.get("part") or {}
            if t == "error":
                e = o.get("error") or {}
                return [f"Hata: {(e.get('message') or (e.get('data') or {}).get('message') or e.get('type') or e)}"[:320]]
            if t == "text" and str(p.get("text", "")).strip():
                return model_satiri(is_) + p["text"].strip().splitlines()
            if t == "tool_use":
                st = p.get("state") or {}
                return model_satiri(is_) + [_arac(p.get("tool", "araç"), st.get("input") or {})]
            if t == "step_finish" and p.get("reason") not in ("tool-calls", "tool_calls"):
                sn = ((ts or 0) - (durum_["t0"] or ts or 0)) / 1000
                return model_satiri(is_) + [f"Bitti · {sn:.0f} sn"]
            return []
        # Codex
        if isinstance(t, str) and (t.startswith(("thread.", "turn.", "item.")) or (t == "error" and "message" in o)):
            if t == "thread.started":
                is_.oturum = o.get("thread_id") or is_.oturum
                durum_["t0"] = time.time()
                return model_satiri(is_)
            if t == "item.completed":
                it = o.get("item") or {}
                tur = it.get("type")
                if tur == "agent_message" and str(it.get("text", "")).strip():
                    return it["text"].strip().splitlines()
                if tur == "command_execution":
                    k = str(it.get("command", ""))
                    m = _KOMUT_SARMA.search(k)
                    return [_arac("Komut", {"command": m.group(2) if m else k})]
                if tur == "file_change":
                    yollar = ", ".join(str(c.get("path", "")) for c in it.get("changes") or [] if isinstance(c, dict))
                    return [_arac("Düzenle", {"path": yollar})]
                if tur == "mcp_tool_call":
                    return [_arac(f"{it.get('server', 'mcp')}.{it.get('tool', 'araç')}", it.get("arguments") or {})]
                if tur == "web_search":
                    return [_arac("Web", {"query": it.get("query", "")})]
                return []  # reasoning, todo_list, error (uyarı) günlüğü kirletmez
            if t == "turn.completed":
                sn = time.time() - (durum_["t0"] or time.time())
                return [f"Bitti · {sn:.0f} sn"]
            if t == "turn.failed":
                return [f"Hata: {_ic_mesaj((o.get('error') or {}).get('message', ''))}"]
            return []  # turn.started, item.started, item.updated; üst düzey error ardından turn.failed gelir
        # Claude Code
        if t == "system":
            if o.get("subtype") == "init":
                is_.oturum = o.get("session_id") or is_.oturum
                return [f"Model: {o.get('model', is_.model)}"]
            return []
        if t == "assistant":
            cikti = []
            for c in o.get("message", {}).get("content", []):
                if c.get("type") == "text" and c.get("text", "").strip():
                    cikti += c["text"].strip().splitlines()
                elif c.get("type") == "tool_use":
                    cikti.append(_arac(c.get("name", "araç"), c.get("input") or {}))
            return cikti
        if t == "result" or ("duration_api_ms" in o and "session_id" in o):
            is_.oturum = o.get("session_id") or is_.oturum
            sn = (o.get("duration_ms") or 0) / 1000
            return [f"Hata: {o.get('result', '')[:300]}"] if o.get("is_error") else [f"Bitti · {sn:.0f} sn"]
        # Antigravity
        e = o.get("event")
        if e == "init":
            is_.oturum = o.get("conversation_id") or is_.oturum
            return [f"Model: {(o.get('init') or {}).get('model', is_.model)}"]
        if e == "step_update":
            s = o.get("step_update") or {}
            if s.get("step_type") == "agent_response":
                tampon.append(s.get("text_delta", ""))
                if s.get("state") != "DONE":
                    return []
                metin, tampon[:] = "".join(tampon).strip(), []
                return metin.splitlines()
            # system_message ve error_message araç değildir; hata metni zaten ayrı satır olarak gelir
            if s.get("state") == "DONE" and s.get("step_type") not in (None, "user_input", "system_message", "error_message"):
                return [_arac(s.get("tool_name") or s["step_type"], s.get("tool_input") or {})]
            return []
        if e == "result":
            r = o.get("result") or {}
            is_.oturum = r.get("conversation_id") or is_.oturum
            if r.get("status") != "SUCCESS":
                return [f"Hata: {r.get('status')} {str(r.get('response', ''))[:300]}".rstrip()]
            return [f"Bitti · {r.get('duration_seconds', 0):.0f} sn"]
        return []

    return cevir


if __name__ == "__main__":  # elle tarama: python -m vedit.motorlar
    json.dump(durum(), sys.stdout, ensure_ascii=False, indent=1, default=str)
