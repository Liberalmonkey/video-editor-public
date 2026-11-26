"""Yayın metni paneli (ADR 0055): video listesi, motor/model seçimi, Üret isteği, düzenle, kaydet, yayin.md. Ajan çağırmaz.
argv: çıktı klasörü. Sonuç: TAMAM/HATA satırları, çıkış kodu."""
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import uvicorn
from playwright.sync_api import expect, sync_playwright

from vedit import hizli, kurgu, paths, yayin
from vedit.studio import app as sunucu

cikti = Path(sys.argv[1]).resolve()
cikti.mkdir(parents=True, exist_ok=True)
paths.INPUTS, paths.OUTPUTS = cikti / "in", cikti / "out"
PROJE = "yayin"
PORT = 8794
sonuc = []


def adim(ad, kosul=True, ek=""):
    sonuc.append((ad, bool(kosul)))
    print(("TAMAM " if kosul else "HATA  ") + ad + (f"  [{ek}]" if ek else ""), flush=True)


p = hizli.Proje("instagram", PROJE)
p.girdi.mkdir(parents=True, exist_ok=True)
kurgu.yaz(p.work, kurgu.bos("instagram"))
p.cikti.mkdir(parents=True, exist_ok=True)
for ad in ("2.mp4", "10.mp4"):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=360x640:r=30:d=2", "-c:v", "libx264", "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p", str(p.cikti / ad)], check=True)
(p.cikti / "2.srt").write_text("1\n00:00:00,000 --> 00:00:02,000\nMerhaba\n", encoding="utf-8")
hazir = {"video": "2.mp4", "dil": "tr", "platformlar": {"reels": {
    "baslik": "Claude ile 3 dakikada kurgu", "aciklama": "Videoyu nasıl hızlandırdığımı anlatıyorum.",
    "hashtagler": ["#kurgu", "#claude", "#yapayzeka"], "etiketler": [], "bolumler": [], "notlar": ""}}}
yayin._yaz(p, p.cikti / "2.mp4", hazir, {"motor": "claude", "model": "claude-opus-5-5", "zaman": "2026-11-23T10:00:00"})

token = "e2e"
app = sunucu.create_app(token, izinli_hostlar={f"127.0.0.1:{PORT}"})
threading.Thread(target=lambda: uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning"), daemon=True).start()
time.sleep(1.5)

with sync_playwright() as pw:
    tar = pw.chromium.launch(channel="chrome", headless=True)
    s = tar.new_page(viewport={"width": 1600, "height": 950})
    konsol = []
    s.on("pageerror", lambda e: konsol.append("pageerror: " + str(e)))
    s.on("console", lambda m: konsol.append(m.text) if m.type == "error" else None)
    istekler = []

    def yakala(rota):  # ajan çalışmasın: isteği kaydet, boş yanıt ver
        if rota.request.method == "POST":
            istekler.append(json.loads(rota.request.post_data))
            return rota.fulfill(status=200, content_type="application/json", body="{}")
        rota.continue_()

    s.route("**/api/isler", yakala)
    s.goto(f"http://127.0.0.1:{PORT}/?token={token}")
    s.locator(".satir[aria-pressed]", has_text=PROJE).click()
    expect(s.locator("canvas[data-timeline]")).to_be_visible(timeout=15000)
    s.keyboard.press("Alt+2")
    s.locator(".dv-tab", has_text="Yayın metni").first.click()
    liste = s.get_by_label("Teslim videoları")
    expect(liste).to_be_visible(timeout=10000)
    satirlar = [x.strip() for x in liste.locator("li").all_inner_texts()]
    adim("videolar doğal sırada", len(satirlar) == 2 and satirlar[0].startswith("2.mp4") and satirlar[1].startswith("10.mp4"), str(satirlar))
    adim("paket durumu: 2 hazır, 10 yok", "hazır" in satirlar[0] and "yok" in satirlar[1] and "SRT yok" in satirlar[1])
    try:  # motor taraması (agy ağ, opencode yüzlerce model) bitince seçici dolar
        expect(s.get_by_label("Yayın metni motoru")).to_have_value("claude", timeout=90000)
    except AssertionError:
        pass
    adim("varsayılan motor ve model", s.get_by_label("Yayın metni motoru").input_value() == "claude"
         and s.get_by_label("Yayın metni modeli").input_value() == "claude-opus-5-5",
         f'{s.get_by_label("Yayın metni motoru").input_value()!r} {s.get_by_label("Yayın metni modeli").input_value()}')

    liste.locator("li").nth(1).get_by_role("button", name="Üret").click()
    s.wait_for_timeout(400)
    i = istekler[-1] if istekler else {}
    adim("Üret isteği video, motor, model ve platformu gönderir", {k: i.get(k) for k in ("komut", "video", "motor", "model", "platformlar")} ==
         {"komut": "yayin", "video": "10.mp4", "motor": "claude", "model": "claude-opus-5-5", "platformlar": ["reels"]}, json.dumps(i, ensure_ascii=False))

    s.locator(".dv-tab", has_text="Yayın metni").first.click()
    liste.locator("li").first.get_by_role("button", name="2.mp4").click()
    baslik = s.locator("section[aria-label='2.mp4 yayın metni'] input").first
    expect(baslik).to_have_value("Claude ile 3 dakikada kurgu", timeout=8000)
    baslik.fill("Claude Code ile kurguyu 3 dakikaya indirdim")
    s.get_by_role("button", name="Kaydet").click()
    s.wait_for_timeout(800)
    md = (p.cikti / "yayin.md").read_text(encoding="utf-8")
    adim("Kaydet yayin.md bloğunu günceller", "Claude Code ile kurguyu 3 dakikaya indirdim" in md and md.count("<!-- yayin:2 -->") == 1)
    adim("elle düzenleme işaretlenir", (yayin.paket_oku(p, "2") or {}).get("_uretim", {}).get("duzenlendi"))

    s.locator("section[aria-label='2.mp4 yayın metni'] input").nth(1).fill("#a " * 7)
    s.get_by_role("button", name="Kaydet").click()
    s.wait_for_timeout(800)
    adim("sınır aşan hashtag kaydedilmez", "Claude Code ile kurguyu" in (p.cikti / "yayin.md").read_text(encoding="utf-8")
         and len((yayin.paket_oku(p, "2") or {})["platformlar"]["reels"]["hashtagler"]) == 3)
    s.screenshot(path=str(cikti / "yayin-paneli.png"))
    konsol = [k for k in konsol if "422" not in k]  # beklenen doğrulama yanıtı
    adim("konsol temiz", not konsol, " | ".join(konsol[:3]))
    tar.close()

hatali = [a for a, k in sonuc if not k]
print(f"\n{len(sonuc) - len(hatali)}/{len(sonuc)} geçti")
sys.exit(1 if hatali else 0)
