"""Öneriler (sessizlik kesimi), metinden kurgu, kazanç keyframe'i, reframe, XML dışa aktarma. Geçici kökte çalışır.
argv: çıktı klasörü."""
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import soundfile as sf
import uvicorn
from playwright.sync_api import expect, sync_playwright

from vedit import hizli, kurgu, paths
from vedit.studio import app as sunucu

cikti = Path(sys.argv[1]).resolve()
cikti.mkdir(parents=True, exist_ok=True)
paths.INPUTS, paths.OUTPUTS = cikti / "in", cikti / "out"
PROJE, PORT, SR = "oneri", 8792, 48000
sonuc = []


def adim(ad, kosul=True, ek=""):
    sonuc.append((ad, bool(kosul)))
    print(("TAMAM " if kosul else "HATA  ") + ad + (f"  [{ek}]" if ek else ""), flush=True)


# 10 sn: konuşma benzeri ton, 4-5,5 sn arası tam sessizlik.
yol = paths.INPUTS / "instagram" / PROJE / "yatay.mp4"
yol.parent.mkdir(parents=True, exist_ok=True)
t = np.arange(10 * SR) / SR
x = 0.2 * np.sin(2 * np.pi * 220 * t) * ((t < 4) | (t >= 5.5))
wav = cikti / "s.wav"
sf.write(wav, np.stack([x, x], 1).astype(np.float32), SR)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=10", "-i", str(wav),
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(yol)], check=True)
p = hizli.Proje("instagram", PROJE)
kurgu.yaz(p.work, kurgu.bos("instagram"))

app = sunucu.create_app("e2e", izinli_hostlar={f"127.0.0.1:{PORT}"})
threading.Thread(target=lambda: uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning"), daemon=True).start()
time.sleep(1.5)

with sync_playwright() as pw:
    tar = pw.chromium.launch(channel="chrome", headless=True)
    s = tar.new_page(viewport={"width": 1600, "height": 950})
    konsol = []
    s.on("pageerror", lambda e: konsol.append("pageerror: " + str(e)))
    s.on("console", lambda m: konsol.append(m.text) if m.type == "error" else None)
    s.goto(f"http://127.0.0.1:{PORT}/?token=e2e")
    s.locator(".satir[aria-pressed]", has_text=PROJE).click()
    expect(s.locator("canvas[data-timeline]")).to_be_visible(timeout=15000)
    s.wait_for_function("window.__studio && window.__studio.player")
    K = lambda: s.evaluate("() => window.__studio.depo.getState().kurgu")
    sekme = lambda ad: s.locator(".dv-tab", has_text=ad).first.click()
    # Yatay klibi dikey sekansa koymak için önce dikey kalsın: boş kurgu otomatik sekansı aşmak için sekans sonra geri alınır.
    s.evaluate("""async () => { const d = window.__studio.depo.getState(); await d.kaynaktanEkle({ yol: "inputs:yatay.mp4", ad: "yatay.mp4", tur: "video" }, 0, null, false); }""")
    s.wait_for_timeout(300)
    adim("Öneriler ayrı sekme değil, Altyazı içinde", s.locator(".dv-tab", has_text="Öneriler").count() == 0)

    sekme("Altyazı")
    s.get_by_text("Sessizlik ve dolgu", exact=True).click()
    s.get_by_role("button", name="Sessizlik ve dolgu bul").click()
    s.locator("text=Seçilenleri kes").wait_for(timeout=20000)
    adaylar = s.locator(".panel .satir input[type=checkbox]").count()
    adim("sessizlik adayı bulundu, kurgu değişmedi", adaylar >= 1 and len(K()["klipler"]) == 1, f"{adaylar} aday")
    s.screenshot(path=str(cikti / "1-oneriler.png"))
    s.get_by_role("button", name="Seçilenleri kes").click()
    s.wait_for_timeout(300)
    k = K()
    toplam = sum(c["sure"] for c in k["klipler"])
    adim("seçilen sessizlik ripple ile kesildi", 8.3 < toplam < 9.1 and len(k["klipler"]) == 2, f"toplam {toplam:.2f} sn")
    s.keyboard.press("Control+z")
    s.wait_for_timeout(200)
    adim("tek Ctrl+Z geri alır", len(K()["klipler"]) == 1)

    # Kazanç keyframe'i Efekt panelinden
    s.locator("canvas[data-timeline]").click(position={"x": 120, "y": 26 + 54 + 20})
    sekme("Klip")
    s.get_by_role("button", name="Kazanç animasyonu aç").click()
    s.evaluate("() => window.__studio.player.seekTo(90)")
    s.wait_for_timeout(300)
    s.get_by_label("Kazanç", exact=True).fill("-12")
    s.get_by_label("Kazanç", exact=True).press("Enter")
    s.wait_for_timeout(300)
    kf = K()["klipler"][0]["ses"]["kf"]
    adim("Efekt panelinden kazanç keyframe'i", len(kf) == 2 and kf[1]["v"] == -12, str(kf))
    s.screenshot(path=str(cikti / "2-kazanc-kf.png"))

    # Temizle (Ses paneli)
    sekme("Ses")
    s.get_by_label("Konuşmayı temizle").check()
    adim("konuşma temizliği işaretlendi", K()["klipler"][0]["ses"]["temizle"] is True)

    # Reframe: sekansı dikeye al, klip yatay kalır
    s.get_by_label("Sekans oranı").select_option("9:16")
    s.wait_for_timeout(300)
    s.locator("canvas[data-timeline]").click(position={"x": 120, "y": 26 + 54 + 20})
    sekme("Klip")  # sade arayüzde Klip ve Ses aynı grupta, düğme Klip panelinde
    b = s.get_by_role("button", name="Yüzü takip et, kareyi doldur")
    b.click()
    s.wait_for_function("() => window.__studio.depo.getState().kurgu.klipler[0].donus.olcek.length > 0", timeout=60000)
    o = K()["klipler"][0]["donus"]["olcek"][0]["v"]
    adim("reframe kareyi doldurur", abs(o - 1920 / 607.5) < 0.01, f"ölçek {o:.4f}")
    s.screenshot(path=str(cikti / "3-reframe.png"))

    # XML
    sekme("İşler")
    s.get_by_role("button", name="Diğer").click()
    s.get_by_role("button", name="XML").click()
    s.wait_for_timeout(2500)
    fx, xm = p.cikti / f"{PROJE}.fcpxml", p.cikti / f"{PROJE}.xml"
    ok = fx.exists() and xm.exists()
    if ok:
        ET.parse(fx); ET.parse(xm)
    adim("XML dışa aktarma iki dosya yazar, ikisi de geçerli", ok)

    s.locator("[data-kayit='kayitli']").wait_for(timeout=8000)
    adim("konsol temiz", not konsol, " | ".join(konsol[:3]))
    tar.close()

hatali = [a for a, k in sonuc if not k]
print(f"\n{len(sonuc) - len(hatali)}/{len(sonuc)} geçti")
sys.exit(1 if hatali else 0)
