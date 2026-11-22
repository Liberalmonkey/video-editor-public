"""Çıktı ayarları paneli (ADR 0035): kademe seçimi, teknik özet, uyarılar, EXPORT isteği, indirme, kurgu engeli. Geçici kökte çalışır, render başlatmaz.
argv: çıktı klasörü. Sonuç: TAMAM/HATA satırları, çıkış kodu."""
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import uvicorn
from playwright.sync_api import expect, sync_playwright

from vedit import hizli, kurgu, paths
from vedit.studio import app as sunucu

cikti = Path(sys.argv[1]).resolve()
cikti.mkdir(parents=True, exist_ok=True)
paths.INPUTS, paths.OUTPUTS = cikti / "in", cikti / "out"
PROJE = "teslim"
PORT = 8793
sonuc = []


def adim(ad, kosul=True, ek=""):
    sonuc.append((ad, bool(kosul)))
    print(("TAMAM " if kosul else "HATA  ") + ad + (f"  [{ek}]" if ek else ""), flush=True)


yol = paths.INPUTS / "instagram" / PROJE / "dikey.mp4"
yol.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=720x1280:r=30:d=4", "-f", "lavfi", "-i", "sine=f=440:d=4",
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(yol)], check=True)
p = hizli.Proje("instagram", PROJE)
kurgu.yaz(p.work, kurgu.bos("instagram"))
p.cikti.mkdir(parents=True, exist_ok=True)
(p.cikti / "teslim.mp4").write_bytes(yol.read_bytes())  # hazır bir "son export": 720x1280 H.264 30 fps

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

    def yakala(rota):  # gerçek render başlamasın: isteği kaydet, boş yanıt ver
        if rota.request.method == "POST":
            istekler.append(json.loads(rota.request.post_data))
            return rota.fulfill(status=200, content_type="application/json", body="{}")
        rota.continue_()

    s.route("**/api/isler", yakala)
    s.goto(f"http://127.0.0.1:{PORT}/?token={token}")
    s.locator(".satir[aria-pressed]", has_text=PROJE).click()
    expect(s.locator("canvas[data-timeline]")).to_be_visible(timeout=15000)

    # Kurgu alanındaki Final düğmesi Teslim alanını ve Çıktı ayarlarını açar
    s.locator(".dv-tab", has_text="İşler").first.click()
    s.get_by_role("button", name="Export", exact=True).click()
    ozet = s.locator("[data-ozet='boyut']")
    expect(ozet).to_be_visible(timeout=8000)
    adim("Export düğmesi Çıktı ayarlarını açar", "1080x1920 · 30 fps" in ozet.inner_text(), ozet.inner_text())
    adim("eski Final diyaloğu yok", s.locator("dialog[open]").count() == 0)

    # İndirme: son export dosyası ek olarak iner, seçili ayarla eşleşme durumu görünür
    esl = s.locator("[data-eslesme]")
    adim("son export sekans ayarıyla eşleşmiyor (720p dosya, 1080p seçim)", esl.get_attribute("data-eslesme") == "false", esl.inner_text())
    s.get_by_label("Çözünürlük").select_option("720")
    adim("720p seçilince eşleşir", esl.get_attribute("data-eslesme") == "true", esl.inner_text())
    with s.expect_download(timeout=15000) as inen:
        s.locator("[data-indir]").click()
    inen.value.save_as(str(cikti / "inen.mp4"))
    adim("İndir dosyayı aynen indirir", inen.value.suggested_filename == "teslim.mp4" and (cikti / "inen.mp4").stat().st_size == yol.stat().st_size,
         f"{inen.value.suggested_filename} {(cikti / 'inen.mp4').stat().st_size} bayt")
    s.locator(".dv-tab", has_text="Çıktılar").first.click()
    with s.expect_download(timeout=15000) as inen2:
        s.get_by_label("teslim.mp4 dosyasını indir").click(force=True)
    adim("Çıktılar satırındaki indir ikonu çalışır", inen2.value.suggested_filename == "teslim.mp4")

    coz = s.get_by_label("Çözünürlük")
    adim("dört kademe teknik adıyla listelenir", [o.strip() for o in coz.locator("option").all_inner_texts()][1:] == [
        "HD 720p · 720x1280", "FHD 1080p · 1080x1920", "QHD 1440p (2K) · 1440x2560", "UHD 2160p (4K) · 2160x3840"], str(coz.locator("option").all_inner_texts()))
    coz.select_option("1440")
    adim("2K seçilince özet 1440x2560 ve motor ölçeği", "1440x2560" in ozet.inner_text() and "×1.333" in ozet.inner_text(), ozet.inner_text())
    notlar = lambda: " | ".join(s.locator("p[role='note']").all_inner_texts())
    adim("büyütme uyarısı kaynak çözünürlüğünü söyler", "%200" in notlar() and "720p" in notlar(), notlar())
    adim("Reels boyut uyarısı", "1080p'ye indirir" in notlar())

    s.get_by_label("Kodek").select_option("h265")
    s.get_by_label("Kalite").select_option("arsiv")
    video = s.locator("dl[aria-label='Çıktı özeti']").inner_text()
    adim("H.265 arşiv CRF 18 ve uyum uyarısı", "H.265 / HEVC, Main · CRF 18" in video and "H.265:" in notlar(), video.replace("\n", " "))
    s.get_by_label("Kare hızı").select_option("60")
    adim("60 fps özeti ve süre uyarısı", "60 fps" in ozet.inner_text() and "2 kat" in notlar(), notlar())
    s.screenshot(path=str(cikti / "1-cikti-ayarlari.png"))

    # Eski sürümden kalmış "AI ile edit" tercihi export'u ajana yönlendirmemeli
    s.evaluate("""() => { const k = "studio.teslim.instagram/teslim"; localStorage.setItem(k, JSON.stringify({ ...JSON.parse(localStorage.getItem(k) || "{}"), aiEdit: true })); }""")
    adim("export panelinde AI kutusu yok", s.get_by_text("AI ile edit").count() == 0 and "Yapay zekâ kullanılmaz" in s.locator(".alt").last.inner_text())
    s.get_by_role("button", name="EXPORT", exact=True).click()
    s.wait_for_timeout(500)
    i = istekler[-1] if istekler else {}
    adim("EXPORT seçilen ayarı gönderir", {k: i.get(k) for k in ("komut", "cozunurluk", "kalite", "kodek", "fps")} ==
         {"komut": "final", "cozunurluk": 1440, "kalite": "arsiv", "kodek": "h265", "fps": 60}, json.dumps(i, ensure_ascii=False))

    adim("başlatınca İşler öne gelir", s.locator(".dv-tab.dv-active-tab, .dv-tab.active-tab", has_text="İşler").count() > 0 or s.get_by_role("button", name="Taslak").is_visible())
    s.reload()
    s.locator(".dv-tab", has_text="Çıktı ayarları").first.click()
    expect(ozet).to_be_visible(timeout=15000)
    adim("ayarlar proje için hatırlanır", "1440x2560 · 60 fps" in ozet.inner_text(), ozet.inner_text())
    # Kurgu engeli: bölünmüş sahnede saydam zemin export'u durdurur, panel bunu söyler
    s.evaluate("""() => window.__studio.depo.getState().duzenle("sahne", (d) => {
      d.klipler.push({ id: "sah", iz: "V2", bas: 0, sure: 2, tur: "sahne", kaynak: null, giris: 0, hiz: 1, bag: null, ses_kapali: false, konusmaci: false, zoom: 1, punches: [],
        donus: { x: [], y: [], olcek: [], opaklik: [], anim: [] }, efekt: { parlaklik: 1, kontrast: 1, doygunluk: 1, bulanik: 0, kirp: null }, ses: { gain_db: 0, fade_in: 0, fade_out: 0, duck: false },
        gecis_giris: null, gecis_cikis: null, sahne: { layout: "split", bg: "saydam", kind: "text", lines: [{ t: "Deneme" }] }, metin: null, metin_stil: null, olay: null });
    })""")
    engel = s.locator("[data-engel]")
    expect(engel).to_be_visible(timeout=10000)
    adim("geçersiz kurguda engel bloğu çıkar ve EXPORT kapanır", "saydam zemin" in engel.inner_text() and s.get_by_role("button", name="EXPORT", exact=True).is_disabled(), " ".join(engel.inner_text().split())[:120])
    # Sahne formu: bölünmüşte Saydam seçeneği yok; tam ekrana alınca gelir, geri dönünce zemin koyuya düşer
    s.keyboard.press("Alt+1")
    s.evaluate("() => window.__studio.depo.setState({ secim: ['sah'] })")
    s.locator(".dv-tab", has_text="Klip").first.click()
    zemin = s.get_by_label("Zemin", exact=True)
    expect(zemin).to_be_visible(timeout=8000)
    adim("bölünmüş sahnede Saydam seçeneği sunulmaz", "Saydam" not in " ".join(zemin.locator("option").all_inner_texts()), str(zemin.locator("option").all_inner_texts()))
    s.get_by_label("Yerleşim", exact=True).select_option("full")
    adim("tam ekranda Saydam seçilebilir", "Saydam" in " ".join(zemin.locator("option").all_inner_texts()))
    zemin.select_option("saydam")
    s.get_by_label("Yerleşim", exact=True).select_option("split")
    s.wait_for_timeout(300)
    sah = s.evaluate("() => window.__studio.depo.getState().kurgu.klipler.find((c) => c.id === 'sah').sahne")
    adim("bölünmüşe dönünce zemin koyuya düşer", sah["bg"] == "dark" and sah["layout"] == "split", json.dumps(sah, ensure_ascii=False))
    s.keyboard.press("Alt+2")
    s.locator(".dv-tab", has_text="Çıktı ayarları").first.click()
    exp = s.get_by_role("button", name="EXPORT", exact=True)
    expect(exp).to_be_visible(timeout=10000)
    try:
        expect(exp).to_be_enabled(timeout=10000)
    except AssertionError:
        pass
    adim("düzeltilince engel kalkar ve EXPORT açılır", exp.is_enabled() and engel.count() == 0)
    adim("konsol temiz", not konsol, " | ".join(konsol[:3]))
    tar.close()

hatali = [a for a, k in sonuc if not k]
print(f"\n{len(sonuc) - len(hatali)}/{len(sonuc)} geçti")
sys.exit(1 if hatali else 0)
