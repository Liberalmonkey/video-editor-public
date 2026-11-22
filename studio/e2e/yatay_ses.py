"""A/V ayırma, canlı metre, +dB önizleme, 16:9 sekans. Kendi geçici Projeler kökünde çalışır, kullanıcı projesine dokunmaz.
argv: çıktı klasörü. Sonuç: TAMAM/HATA satırları, çıkış kodu."""
import subprocess
import sys
import threading
import time
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
PROJE = "yatay"
PORT = 8791
SR = 48000
sonuc = []


def adim(ad, kosul=True, ek=""):
    sonuc.append((ad, bool(kosul)))
    print(("TAMAM " if kosul else "HATA  ") + ad + (f"  [{ek}]" if ek else ""), flush=True)


def kaynak_yap(ad, w, h, sure=14):
    """Bilinen seviyede ses: 440 Hz -12 dBFS. 7. saniyede tek tık ile senkron ölçülür."""
    yol = paths.INPUTS / "instagram" / PROJE / ad
    yol.parent.mkdir(parents=True, exist_ok=True)
    wav = cikti / f"{ad}.wav"
    n = int(sure * SR)
    x = 10 ** (-12 / 20) * np.sin(2 * np.pi * 440 * np.arange(n) / SR)
    sf.write(wav, np.stack([x, x], axis=1).astype(np.float32), SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=s={w}x{h}:r=30:d={sure}", "-i", str(wav),
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", str(yol)], check=True)
    return yol


kaynak_yap("yatay.mp4", 1280, 720)
kaynak_yap("dikey.mp4", 720, 1280)
p = hizli.Proje("instagram", PROJE)
kurgu.yaz(p.work, kurgu.bos("instagram"))

token = "e2e"
app = sunucu.create_app(token, izinli_hostlar={f"127.0.0.1:{PORT}"})
threading.Thread(target=lambda: uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning"), daemon=True).start()
time.sleep(1.5)
url = f"http://127.0.0.1:{PORT}/?token={token}"


def db_oku(s, ad):
    v = s.locator(f"canvas[data-metre='{ad}']").first.get_attribute("data-db") or "-inf"
    return [float(x.replace("-inf", "-999")) for x in v.split()]


def olc(s, ad, sure=1.5):
    """Oynatırken en yüksek okuma."""
    en = -999.0
    bit = time.time() + sure
    while time.time() < bit:
        en = max(en, max(db_oku(s, ad)))
        s.wait_for_timeout(60)
    return en


with sync_playwright() as pw:
    tar = pw.chromium.launch(channel="chrome", headless=True, args=["--autoplay-policy=no-user-gesture-required"])
    s = tar.new_page(viewport={"width": 1600, "height": 950})
    konsol = []
    s.on("pageerror", lambda e: konsol.append("pageerror: " + str(e)))
    s.on("console", lambda m: konsol.append(m.text) if m.type == "error" else None)
    s.goto(url)
    s.locator(".satir[aria-pressed]", has_text=PROJE).click()
    expect(s.locator("canvas[data-timeline]")).to_be_visible(timeout=15000)
    s.wait_for_function("window.__studio && window.__studio.player")
    K = lambda: s.evaluate("() => window.__studio.depo.getState().kurgu")
    ekle = lambda yol, tur="video", t=0: s.evaluate("""async ([yol, tur, t]) => { await window.__studio.depo.getState().kaynaktanEkle({ yol, ad: yol, tur }, t, null, false); }""", [yol, tur, t])
    kayit = lambda: s.locator("[data-kayit='kayitli']").wait_for(timeout=8000)
    sekme = lambda ad: s.locator(".dv-tab", has_text=ad).first.click()

    # Sekans videoya uyar
    adim("boş proje dikey açılır", K()["sekans"]["h"] == 1920)
    ekle("inputs:yatay.mp4")
    s.wait_for_timeout(300)
    adim("ilk yatay video sekansı 16:9 yapar", K()["sekans"]["w"] == 1920 and K()["sekans"]["h"] == 1080)
    sira = s.get_by_label("Sekans oranı")
    expect(sira).to_have_value("16:9")
    s.wait_for_function("() => Object.values(window.__studio.depo.getState().medya).every((u) => u.includes('/proxy/'))", timeout=60000)
    s.wait_for_timeout(600)

    # Metre
    sekme("Ses")
    expect(s.locator("canvas[data-metre='V1']")).to_be_visible()
    oynat = lambda t=1.0: (s.evaluate("(t) => window.__studio.player.seekTo(Math.round(t * 30))", t), s.evaluate("() => window.__studio.player.play()"))
    durdur = lambda: s.evaluate("() => window.__studio.player.pause()")
    oynat()
    s.wait_for_timeout(700)
    v0, m0 = olc(s, "V1"), olc(s, "master")
    adim("kanal metresi -12 dB'yi okur", abs(v0 + 12) < 3, f"{v0:.1f} dB")
    adim("master metresi gerçek çıkışı okur", abs(m0 + 12) < 3, f"{m0:.1f} dB")

    # 0 dB üstü önizlemede duyulur: eski hata
    s.evaluate("""() => window.__studio.depo.getState().duzenle("t", (d) => { d.izler.find((i) => i.id === "V1").gain_db = 6; })""")
    s.wait_for_timeout(900)
    v1, m1 = olc(s, "V1"), olc(s, "master")
    adim("+6 dB fader kanal metresini 6 dB artırır", abs(v1 - v0 - 6) < 1.5, f"{v0:.1f} > {v1:.1f}")
    adim("+6 dB fader gerçek çıkışı 6 dB artırır (eski hata)", abs(m1 - m0 - 6) < 1.5, f"{m0:.1f} > {m1:.1f}")

    # Oynatma akıcılığı
    akis = s.evaluate("""() => new Promise((ok) => { const p = window.__studio.player; let n = 0; const f = () => n++; p.addEventListener("frameupdate", f); setTimeout(() => { p.removeEventListener("frameupdate", f); ok(n); }, 5000); })""")
    durdur()
    adim("metre açıkken oynatma akıcı", akis >= 140, f"{akis}/150 kare")

    s.evaluate("""() => window.__studio.depo.getState().duzenle("t", (d) => { const i = d.izler.find((i) => i.id === "V1"); i.gain_db = 0; i.sessiz = true; })""")
    oynat()
    s.wait_for_timeout(2500)
    adim("sustur kanalı sıfırlar", olc(s, "V1", 0.5) < -50)
    durdur()
    s.evaluate("""() => window.__studio.depo.getState().duzenle("t", (d) => { d.izler.find((i) => i.id === "V1").sessiz = false; })""")

    # Ayırma
    s.locator("canvas[data-timeline]").click(position={"x": 200, "y": 26 + 54 + 25})
    s.wait_for_timeout(200)
    s.keyboard.press("Shift+A")
    s.wait_for_timeout(500)
    k = K()
    ses = [c for c in k["klipler"] if c["tur"] == "ses"]
    vid = [c for c in k["klipler"] if c["tur"] == "video"][0]
    adim("Shift+A sesi ayırır", len(ses) == 1 and vid["ses_kapali"] and ses[0]["iz"] == "A1", f"izler {[i['id'] for i in k['izler']]}")
    s.screenshot(path=str(cikti / "1-ayrik-timeline.png"))
    oynat()
    s.wait_for_timeout(900)
    a, v, m = olc(s, "A1"), olc(s, "V1"), olc(s, "master")
    durdur()
    adim("ayrık ses A1'de okunur, video kanalı susar", abs(a + 12) < 3 and v < -50, f"A1 {a:.1f}, V1 {v:.1f}")
    adim("ayrık ses gerçekten çalar", abs(m + 12) < 3, f"master {m:.1f} dB")

    # Bağlı bölme
    s.keyboard.press("Home")
    s.evaluate("() => window.__studio.player.seekTo(150)")
    s.wait_for_timeout(300)
    s.evaluate("() => { const d = window.__studio.depo.getState(); d.sec([]); }")
    s.keyboard.press("Control+k")
    s.wait_for_timeout(200)
    k = K()
    sag = sorted(k["klipler"], key=lambda c: (c["bas"], c["tur"]))
    baglar = {c["bas"]: c["bag"] for c in sag if c["tur"] == "video"}
    adim("kesim çifti birlikte böler, bağ korunur", len(sag) == 4 and all(any(x["bag"] == c["bag"] and x["tur"] == "ses" for x in sag) for c in sag if c["tur"] == "video"), str(baglar))
    s.keyboard.press("Control+z")

    # Ses çizgisi
    sekme("Klip")
    tl = s.locator("canvas[data-timeline]")
    izler = K()["izler"]
    y = 26
    for i in izler:
        if i["id"] == "A1":
            break
        y += 54 if i["tur"] == "video" else 42
    # 0 dB çizgisi: -24..+12 aralığında üstten 1/3
    cy = y + 1 + 40 * (12 / 36)
    tl.hover(position={"x": 300, "y": cy})
    s.mouse.down()
    s.mouse.move(*(lambda b: (b["x"] + 300, b["y"] + y + 1 + 40 * (18 / 36)))(tl.bounding_box()), steps=4)
    s.screenshot(path=str(cikti / "2-ses-cizgisi.png"))
    s.mouse.up()
    s.wait_for_timeout(200)
    g = [c for c in K()["klipler"] if c["tur"] == "ses"][0]["ses"]["gain_db"]
    adim("ses çizgisi sürüklenince kazanç iner", abs(g + 6) < 1, f"{g} dB")
    tl.dblclick(position={"x": 300, "y": y + 1 + 40 * (18 / 36)})
    s.wait_for_timeout(200)
    adim("çift tık 0 dB", [c for c in K()["klipler"] if c["tur"] == "ses"][0]["ses"]["gain_db"] == 0)
    s.keyboard.press("Alt+ArrowUp")
    s.wait_for_timeout(150)
    adim("Alt+Yukarı 1 dB açar", [c for c in K()["klipler"] if c["tur"] == "ses"][0]["ses"]["gain_db"] == 1)
    s.keyboard.press("Alt+ArrowDown")

    # Efekt paneli bağlı grupta çalışır
    s.wait_for_timeout(200)
    adim("Efekt paneli bağlı çiftte kilitli değil", s.get_by_label("Kazanç").count() >= 1)

    # Yatay sahne önizleme
    sekme("Kütüphane"); s.get_by_role("tab", name="Grafik").click()
    s.evaluate("() => { const d = window.__studio.depo.getState(); d.ayarla({ zaman: 2 }); }")
    s.wait_for_timeout(200)
    s.evaluate("""() => window.__studio.depo.getState().duzenle("sahne", (d) => {
      d.klipler.push({ id: "sah", iz: "V2", bas: 2, sure: 3, tur: "sahne", kaynak: null, giris: 0, hiz: 1, bag: null, ses_kapali: false, konusmaci: false, zoom: 1, punches: [],
        donus: { x: [], y: [], olcek: [], opaklik: [], anim: [] }, efekt: { parlaklik: 1, kontrast: 1, doygunluk: 1, bulanik: 0, kirp: null }, ses: { gain_db: 0, fade_in: 0, fade_out: 0, duck: false },
        gecis_giris: null, gecis_cikis: null, sahne: { layout: "split", bg: "dark", kind: "stat", value: 100, decimals: 0, prefix: "", unit: "%", label: "Etiket yaz" }, metin: null, metin_stil: null, olay: null });
      d.klipler.find((c) => c.tur === "video").konusmaci = true;
    })""")
    s.evaluate("() => window.__studio.player.seekTo(100)")
    s.wait_for_timeout(1200)
    s.screenshot(path=str(cikti / "3-yatay-sahne-onizleme.png"))
    sira.select_option("9:16")
    s.wait_for_timeout(1200)
    adim("sekans elle değişir", K()["sekans"]["w"] == 1080)
    s.screenshot(path=str(cikti / "4-dikeye-gecis.png"))
    s.keyboard.press("Control+z")
    s.wait_for_timeout(300)
    adim("sekans değişimi geri alınır", K()["sekans"]["w"] == 1920)

    kayit()
    adim("konsol temiz", not konsol, " | ".join(konsol[:3]))
    tar.close()

hatali = [a for a, k in sonuc if not k]
print(f"\n{len(sonuc) - len(hatali)}/{len(sonuc)} geçti")
sys.exit(1 if hatali else 0)
