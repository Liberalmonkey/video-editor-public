"""Uygulama hız ölçümü (ADR 0057): CLI içe aktarma, Stüdyo açılışı, ilk boyama, timeline kaydırma, önizleme, taslak render.

Kullanım: .venv/Scripts/python scripts/hiz_olc.py <etiket> [--proje instagram/arvelior-swarm] [--tekrar 5] [--render]
Sonuç: work/olcum/hiz-<etiket>.json. İki etiketi karşılaştırma: --karsilastir once sonra (Markdown tablo basar).
Her metrik birkaç koşunun medyanıdır; ölçüm sırasında makinede başka ağır iş çalışmamalı.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
PY = KOK / ".venv" / "Scripts" / "python.exe"
VEDIT = KOK / ".venv" / "Scripts" / "vedit.exe"
OLCUM = KOK / "work" / "olcum"


def medyan(f, n: int) -> float:
    return round(statistics.median(f() for _ in range(n)), 3)


def cli_import() -> float:
    """`import vedit.cli` toplam süresi (sn), -X importtime'ın kümülatif sütunundan."""
    r = subprocess.run([str(PY), "-X", "importtime", "-c", "import vedit.cli"], capture_output=True, text=True, cwd=KOK)
    satir = [x for x in r.stderr.splitlines() if x.rstrip().endswith("| vedit.cli")]
    return int(satir[-1].split("|")[1]) / 1e6


def cli_help() -> float:
    t = time.perf_counter()
    subprocess.run([str(VEDIT), "--help"], capture_output=True, cwd=KOK, check=True)
    return time.perf_counter() - t


def studio_ac(port: int) -> tuple[subprocess.Popen, str, float]:
    """Sunucuyu pencere açmadan başlatır; ilk 200 yanıtına kadar geçen süre."""
    t = time.perf_counter()
    s = subprocess.Popen([str(VEDIT), "studio", "--acma", "--port", str(port)], cwd=KOK, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    url = None
    while url is None:
        satir = s.stdout.readline()
        if not satir:
            raise SystemExit("Stüdyo başlamadı")
        m = re.search(r"(http://127\.0\.0\.1:\d+/\?token=\S+)", satir)
        url = m.group(1) if m else None
    import threading
    threading.Thread(target=lambda: [None for _ in s.stdout], daemon=True).start()  # boru dolup sunucu kilitlenmesin
    saglik = url.split("/?")[0] + "/api/projeler"
    while True:
        try:
            with urllib.request.urlopen(saglik, timeout=2):
                break
        except urllib.error.HTTPError:  # sunucu yanıt verdi (yetki/404 da olsa): ayakta
            break
        except OSError:
            if time.perf_counter() - t > 120:
                s.kill()
                raise SystemExit("Stüdyo 120 sn içinde yanıt vermedi")
            time.sleep(0.02)
    return s, url, time.perf_counter() - t


def tarayici(url: str, proje: str | None) -> dict:
    from playwright.sync_api import sync_playwright
    sonuc: dict = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True, args=["--autoplay-policy=no-user-gesture-required"])
        s = b.new_page(viewport={"width": 1600, "height": 950})
        s.add_init_script("""window.__lcp = 0; new PerformanceObserver((l) => { for (const e of l.getEntries()) window.__lcp = e.startTime; })
          .observe({type: 'largest-contentful-paint', buffered: true});
          const _ce = document.createElement.bind(document);
          document.createElement = (ad, ...r) => { const el = _ce(ad, ...r);
            if (String(ad).toLowerCase() === 'hyperframes-player') el.addEventListener('ready', () => { window.__hfHazir = performance.now(); });
            return el; };""")
        s.goto(url, wait_until="load")
        s.wait_for_timeout(1500)
        sonuc.update(s.evaluate("""() => {
          const p = Object.fromEntries(performance.getEntriesByType('paint').map(e => [e.name, e.startTime]));
          const r = performance.getEntriesByType('resource');
          const js = r.filter(e => e.name.endsWith('.js') || e.initiatorType === 'script');
          const nav = performance.getEntriesByType('navigation')[0];
          return {fcp_ms: p['first-contentful-paint'] ?? null, lcp_ms: window.__lcp || null, istek: r.length,
                  js_kb: Math.round(js.reduce((a, e) => a + (e.encodedBodySize || 0), 0) / 1024),
                  dom_ms: nav ? nav.domContentLoadedEventEnd : null};
        }"""))
        if proje:
            studyo, ad = proje.split("/")
            s.keyboard.press("Alt+1")
            s.wait_for_timeout(500)
            t0 = s.evaluate("performance.now()")
            s.locator(".satir[aria-pressed]", has_text=ad).first.click()
            s.locator("canvas[data-timeline]").wait_for(state="visible", timeout=30000)
            sonuc["proje_ac_ms"] = round(s.evaluate("performance.now()") - t0)
            # Önizleme: <hyperframes-player> 'ready' olayına kadar (proje tıklamasından)
            s.wait_for_function("window.__hfHazir", timeout=60000)
            sonuc["onizleme_ms"] = round(s.evaluate("window.__hfHazir") - t0)
            s.wait_for_timeout(1000)
            # Timeline kaydırma: cetvel üstünde 60 adımlık sürükleme; kare süreleri rAF ile.
            r = s.locator("canvas[data-timeline]").bounding_box()
            s.evaluate("""() => { window.__kare = []; let son = performance.now();
              const d = (t) => { window.__kare.push(t - son); son = t; if (window.__kare.length < 400) requestAnimationFrame(d); };
              requestAnimationFrame(d); }""")
            y = r["y"] + 10
            s.mouse.move(r["x"] + 40, y)
            s.mouse.down()
            for i in range(60):
                s.mouse.move(r["x"] + 40 + (r["width"] - 80) * i / 59, y)
                s.wait_for_timeout(16)
            s.mouse.up()
            k = sorted(s.evaluate("window.__kare.slice(2)"))
            if k:
                sonuc["scrub_p50_ms"] = round(k[len(k) // 2], 1)
                sonuc["scrub_p95_ms"] = round(k[int(len(k) * 0.95)], 1)
        b.close()
    return sonuc


def render(proje: str) -> float:
    t = time.perf_counter()
    subprocess.run([str(VEDIT), "taslak", proje], cwd=KOK, check=True, capture_output=True)
    return time.perf_counter() - t


def olc(etiket: str, proje: str | None, tekrar: int, render_al: bool) -> dict:
    d: dict = {"etiket": etiket, "zaman": time.strftime("%Y-%m-%d %H:%M"), "makine": os.environ.get("COMPUTERNAME", "?")}
    d["cli_import_sn"] = medyan(cli_import, tekrar)
    d["cli_help_sn"] = medyan(cli_help, tekrar)
    acilis, sayfa = [], []
    for i in range(3):
        s, url, sure = studio_ac(8790 + i)
        acilis.append(sure)
        try:
            sayfa.append(tarayici(url, proje if i == 2 else None))
        finally:
            s.kill()
            s.wait()
    d["studio_sunucu_sn"] = round(statistics.median(acilis), 3)
    for anahtar in ("fcp_ms", "lcp_ms", "dom_ms", "js_kb", "istek"):
        v = [x[anahtar] for x in sayfa if x.get(anahtar) is not None]
        d[anahtar] = round(statistics.median(v), 1) if v else None
    for anahtar in ("proje_ac_ms", "onizleme_ms", "scrub_p50_ms", "scrub_p95_ms"):
        d[anahtar] = sayfa[-1].get(anahtar)
    dist = KOK / "studio" / "web" / "dist"
    d["dist_kb"] = round(sum(f.stat().st_size for f in dist.rglob("*") if f.is_file()) / 1024) if dist.exists() else None
    if render_al and proje:
        d["taslak_sn"] = round(render(proje), 1)
    OLCUM.mkdir(parents=True, exist_ok=True)
    (OLCUM / f"hiz-{etiket}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(d, ensure_ascii=False, indent=1))
    return d


AD = {"cli_import_sn": "CLI içe aktarma (sn)", "cli_help_sn": "`vedit --help` (sn)", "studio_sunucu_sn": "Stüdyo sunucu ilk yanıt (sn)",
      "fcp_ms": "İlk boyama FCP (ms)", "lcp_ms": "LCP (ms)", "dom_ms": "DOMContentLoaded (ms)", "js_kb": "İlk yükte JS (KB)",
      "istek": "İlk yükte istek", "proje_ac_ms": "Proje açma (ms)", "onizleme_ms": "Önizleme hazır (ms)",
      "scrub_p50_ms": "Kaydırma kare süresi p50 (ms)", "scrub_p95_ms": "Kaydırma kare süresi p95 (ms)", "dist_kb": "Derleme boyutu (KB)",
      "taslak_sn": "Taslak render 53 sn video (sn)"}


def karsilastir(a: str, b: str) -> None:
    x = json.loads((OLCUM / f"hiz-{a}.json").read_text(encoding="utf-8"))
    y = json.loads((OLCUM / f"hiz-{b}.json").read_text(encoding="utf-8"))
    print(f"| Metrik | {a} | {b} | Fark |\n|---|---|---|---|")
    for k, ad in AD.items():
        if x.get(k) is None and y.get(k) is None:
            continue
        fark = f"{(y[k] - x[k]) / x[k] * 100:+.0f}%" if x.get(k) and y.get(k) is not None else ""
        print(f"| {ad} | {x.get(k)} | {y.get(k)} | {fark} |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("etiket", nargs="?")
    ap.add_argument("--proje", default="instagram/arvelior-swarm")
    ap.add_argument("--tekrar", type=int, default=5)
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--karsilastir", nargs=2)
    a = ap.parse_args()
    if a.karsilastir:
        karsilastir(*a.karsilastir)
    else:
        olc(a.etiket or "olcum", a.proje, a.tekrar, a.render)
    sys.exit(0)
