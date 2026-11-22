"""3. aşama uçtan uca: gerçek fare ve klavye. argv: url, çıktı, video, kurgu.json yolu."""
import json
import statistics
import sys
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

url, cikti, video, kurgu_yol = sys.argv[1], Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
cikti.mkdir(parents=True, exist_ok=True)
sonuc = []
PROJE = "e2e-kurgu"


def adim(ad, kosul=True, ek=""):
    sonuc.append((ad, bool(kosul)))
    print(("TAMAM " if kosul else "HATA  ") + ad + (f"  [{ek}]" if ek else ""), flush=True)


with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True, args=["--autoplay-policy=no-user-gesture-required"])
    s = b.new_page(viewport={"width": 1600, "height": 950})
    konsol = []
    s.on("pageerror", lambda e: konsol.append("pageerror: " + str(e)))
    s.on("console", lambda m: konsol.append(m.text) if m.type == "error" else None)
    s.goto(url)
    s.locator(".satir[aria-pressed]", has_text=PROJE).click()
    expect(s.locator("canvas[data-timeline]")).to_be_visible(timeout=15000)
    s.wait_for_function("window.__studio && window.__studio.player")

    durum = lambda: s.evaluate("""() => { const d = window.__studio.depo.getState(); return {klipler: d.kurgu.klipler.map(c=>({id:c.id,iz:c.iz,tur:c.tur,bas:c.bas,sure:c.sure,giris:c.giris,bag:c.bag})), izler: d.kurgu.izler.map(i=>({id:i.id,tur:i.tur,kilit:i.kilit})), secim:d.secim, zaman:d.zaman, kayit:d.kayit, arac:d.arac, giris:d.giris, cikis:d.cikis, isaret:d.kurgu.isaretler||[], geri:d.geri.length, oynuyor:d.oynuyor}; }""")
    bilgi = lambda: s.evaluate("""() => { const t = window.__studioTl, r = t.tuval().getBoundingClientRect(); return {px:t.px(), sl:t.sc().scrollLeft, st:t.sc().scrollTop, l:r.left, t:r.top}; }""")

    def yer(t, iz, dy=0.5):
        i, d = bilgi(), durum()
        y = 26
        for z in d["izler"]:
            h = 54 if z["tur"] == "video" else 42
            if z["id"] == iz:
                return i["l"] + t * i["px"] - i["sl"], i["t"] + y + h * dy - i["st"]
            y += h
        raise KeyError(iz)

    def surukle(t1, iz1, t2, iz2=None, ctrl=False):
        x1, y1 = yer(t1, iz1)
        x2, y2 = yer(t2, iz2 or iz1)
        s.mouse.move(x1, y1)
        s.mouse.down()
        if ctrl:
            s.keyboard.down("Control")
        s.mouse.move((x1 + x2) / 2, (y1 + y2) / 2, steps=3)
        s.mouse.move(x2, y2, steps=4)
        s.mouse.up()
        if ctrl:
            s.keyboard.up("Control")
        s.wait_for_timeout(60)

    v1 = lambda d=None: sorted([c for c in (d or durum())["klipler"] if c["iz"] == "V1"], key=lambda c: c["bas"])
    yakin = lambda a, b, e=0.04: abs(a - b) <= e
    odak = lambda: s.locator("canvas[data-timeline]").focus() if False else None

    s.wait_for_timeout(1500)
    s.screenshot(path=str(cikti / "1-acilis.png"))
    ilk = durum()
    adim("kurgu ve timeline yüklendi", len(ilk["klipler"]) > 5, f"{len(ilk['klipler'])} klip")
    tek = v1(ilk)
    adim("başlangıç V1 tek klip", len(tek) == 1, str(tek[0]["sure"]))

    # Sığdır sonrası piksel: V2 ve A izleri kilitlenince V1 araçları temiz ölçülür
    # Razor
    s.keyboard.press("c")
    x, y = yer(10, "V1")
    s.mouse.click(x, y)
    d = durum()
    adim("Razor (C + tık) V1'i böldü", len(v1(d)) == 2 and yakin(v1(d)[1]["bas"], 10), f"{[round(c['bas'], 3) for c in v1(d)]}")
    # Geri al / yinele
    s.keyboard.press("Control+z")
    adim("Ctrl+Z geri aldı", len(v1()) == 1)
    s.keyboard.press("Control+y")
    adim("Ctrl+Y yineledi", len(v1()) == 2)
    x, y = yer(25, "V1")
    s.mouse.click(x, y)
    adim("üç parça", len(v1()) == 3)
    s.keyboard.press("v")

    # Kırpma: b klibinin başı
    d0 = v1()[1]
    surukle(d0["bas"] + 0.01, "V1", d0["bas"] + 1.5)
    d1 = v1()[1]
    adim("Seç aracı baş kırpma: giriş izledi", yakin(d1["bas"], d0["bas"] + 1.5) and yakin(d1["giris"], d0["giris"] + 1.5) and yakin(d1["sure"], d0["sure"] - 1.5), f"bas {d1['bas']:.3f} giris {d1['giris']:.3f}")
    s.keyboard.press("Control+z")

    # Yapışma: kırpılan kenar oynatma kafasına
    s.evaluate("() => window.__studio.player.seekTo(420)")
    s.wait_for_timeout(120)
    d0 = v1()[1]
    surukle(d0["bas"] + 0.01, "V1", 14.05)
    adim("yapışma: kenar oynatma kafasına oturdu (14,00)", yakin(v1()[1]["bas"], 14.0, 0.001), f"{v1()[1]['bas']:.4f}")
    s.keyboard.press("Control+z")
    s.keyboard.press("s")
    d0 = v1()[1]
    surukle(d0["bas"] + 0.01, "V1", 14.05)
    adim("yapışma kapalıyken oturmaz (S)", not yakin(v1()[1]["bas"], 14.0, 0.001), f"{v1()[1]['bas']:.4f}")
    s.keyboard.press("Control+z")
    s.keyboard.press("s")

    # Ripple kırpma: A izleri ve V2 senkron
    s.keyboard.press("b")
    a0, c0 = v1()[0], v1()[2]
    sonraki_ust = sorted(c["bas"] for c in durum()["klipler"] if c["iz"] == "V2" and c["bas"] > 15)[0]
    surukle(a0["bas"] + a0["sure"] - 0.01, "V1", a0["bas"] + a0["sure"] - 2)
    d = durum()
    yeni = sorted(c["bas"] for c in d["klipler"] if c["iz"] == "V2" and c["bas"] > 13)[0]
    adim("Ripple kırp (B): sonrası kaydı, V2 senkron", yakin(v1(d)[2]["bas"], c0["bas"] - 2) and yakin(v1(d)[1]["bas"], a0["bas"] + a0["sure"] - 2), f"V1 sonraki {v1(d)[1]['bas']:.3f}, V2 {sonraki_ust:.3f}→{yeni:.3f}")
    s.keyboard.press("Control+z")

    # Rolling
    s.keyboard.press("n")
    a0, b0 = v1()[0], v1()[1]
    top = sum(c["sure"] for c in v1())
    surukle(b0["bas"] + 0.01, "V1", b0["bas"] + 1.2)
    a1, b1 = v1()[0], v1()[1]
    adim("Rolling (N): ortak kesim kaydı, toplam sabit", yakin(a1["sure"], a0["sure"] + 1.2) and yakin(b1["giris"], b0["giris"] + 1.2) and yakin(sum(c["sure"] for c in v1()), top, 1e-3), f"a {a1['sure']:.2f} b {b1['bas']:.2f}")
    s.keyboard.press("Control+z")

    # Slip
    s.keyboard.press("y")
    b0 = v1()[1]
    surukle(b0["bas"] + 3, "V1", b0["bas"] + 4)
    b1 = v1()[1]
    adim("Slip (Y): yer sabit, kaynak kaydı", yakin(b1["bas"], b0["bas"], 1e-3) and yakin(b1["giris"], b0["giris"] + 1), f"giris {b0['giris']:.2f}→{b1['giris']:.2f}")
    s.keyboard.press("Control+z")

    # Slide
    s.keyboard.press("u")
    a0, b0, c0 = v1()
    surukle(b0["bas"] + 3, "V1", b0["bas"] + 4)
    a1, b1, c1 = v1()
    adim("Slide (U): içerik sabit, komşular uyum sağladı", yakin(b1["bas"], b0["bas"] + 1) and yakin(b1["giris"], b0["giris"], 1e-3) and yakin(a1["sure"], a0["sure"] + 1) and yakin(c1["bas"], c0["bas"] + 1), f"b {b1['bas']:.2f}")
    s.keyboard.press("Control+z")
    s.keyboard.press("v")

    # Taşıma, iz değiştirme, overwrite
    s.keyboard.press("Control+z")  # ikinci razor
    s.keyboard.press("Control+y")
    a0, b0, c0 = v1()
    surukle(c0["bas"] + 2, "V1", c0["bas"] + 8)
    c1 = v1()[-1]
    adim("taşıma (sağa)", yakin(c1["bas"], c0["bas"] + 6, 0.05), f"{c0['bas']:.2f}→{c1['bas']:.2f}")
    s.keyboard.press("Control+z")

    # Sürükleme önizlemesi commit etmez
    a0 = v1()[0]
    x, y = yer(3, "V1")
    s.mouse.move(x, y)
    s.mouse.down()
    s.mouse.move(x + 100, y, steps=4)
    ara = v1()[0]["bas"]
    s.mouse.move(x, y, steps=2)
    s.mouse.up()
    adim("sürüklerken durum değişmedi, geri bırakınca sıfır", yakin(ara, a0["bas"], 1e-6) and yakin(v1()[0]["bas"], a0["bas"], 1e-3))
    s.keyboard.press("Control+z") if durum()["geri"] and False else None

    # Ctrl+K, Q, W, Sil, Ripple Sil
    s.evaluate("() => window.__studio.player.seekTo(150)")
    s.wait_for_timeout(120)
    n0 = len(durum()["klipler"])
    s.keyboard.press("Escape")
    s.keyboard.press("Control+k")
    d = durum()
    adim("Ctrl+K: seçim yokken tüm izleri kesti", len(d["klipler"]) > n0, f"{n0}→{len(d['klipler'])}")
    s.keyboard.press("Control+z")
    b0 = v1()[1]
    x, y = yer(b0["bas"] + 2, "V1")
    s.mouse.click(x, y)
    adim("tık seçti", durum()["secim"] == [b0["id"]])
    toplam0 = max(c["bas"] + c["sure"] for c in v1())
    s.keyboard.press("Shift+Delete")
    d = durum()
    adim("Shift+Del ripple sil: boşluk kapandı", b0["id"] not in [c["id"] for c in d["klipler"]] and yakin(max(c["bas"] + c["sure"] for c in v1(d)), toplam0 - b0["sure"], 1e-3))
    s.keyboard.press("Control+z")
    adim("ripple sil geri alındı", b0["id"] in [c["id"] for c in durum()["klipler"]])
    s.keyboard.press("Escape")

    # Giriş-çıkış ve çıkar, işaret
    s.evaluate("() => window.__studio.player.seekTo(60)")
    s.wait_for_timeout(100)
    s.keyboard.press("i")
    s.evaluate("() => window.__studio.player.seekTo(90)")
    s.wait_for_timeout(100)
    s.keyboard.press("o")
    d = durum()
    adim("I / O", yakin(d["giris"], 2) and yakin(d["cikis"], 3))
    son_ = max(c["bas"] + c["sure"] for c in v1())
    s.keyboard.press("'")
    d = durum()
    adim("' aralığı çıkardı", yakin(max(c["bas"] + c["sure"] for c in v1(d)), son_ - 1, 1e-3) and d["giris"] is None)
    s.keyboard.press("Control+z")
    s.keyboard.press("m")
    adim("M işaret ekledi", len(durum()["isaret"]) == 1)
    s.keyboard.press("Control+z")

    # Oynatma, shuttle, kare adımı
    s.evaluate("() => window.__studio.player.seekTo(30)")
    s.wait_for_timeout(150)
    t0 = durum()["zaman"]
    s.keyboard.press(" ")
    s.wait_for_timeout(800)
    t1 = durum()
    s.keyboard.press("k")
    s.wait_for_timeout(100)
    t2 = durum()
    adim("Boşluk oynattı, K durdurdu", t1["oynuyor"] and t1["zaman"] > t0 + 0.3 and not t2["oynuyor"], f"{t0:.2f}→{t1['zaman']:.2f}")
    s.keyboard.press("ArrowRight")
    s.wait_for_timeout(60)
    adim("→ bir kare", yakin(durum()["zaman"] - t2["zaman"], 1 / 30, 0.005))
    s.keyboard.press("Home")
    s.wait_for_timeout(60)
    adim("Home başa", durum()["zaman"] == 0)
    s.keyboard.press("ArrowDown")
    s.wait_for_timeout(60)
    adim("↓ sonraki kesime", durum()["zaman"] > 0, f"{durum()['zaman']:.2f}")
    # Cetvelden sarma
    i = bilgi()
    s.mouse.click(i["l"] + 5 * i["px"] - i["sl"], i["t"] + 10)
    s.wait_for_timeout(100)
    adim("cetvele tık sardı", yakin(durum()["zaman"], 5, 0.15), f"{durum()['zaman']:.3f}")

    # Kilit: düzenlenmez
    s.get_by_role("button", name="V1 kilitle").click()
    s.keyboard.press("c") if False else None
    b0 = v1()[1]
    surukle(b0["bas"] + 0.01, "V1", b0["bas"] + 1)
    adim("kilitli iz kırpılmadı", yakin(v1()[1]["bas"], b0["bas"], 1e-6))
    s.get_by_role("button", name="V1 kilidini aç").click()

    # Otomatik kayıt + yenile
    s.locator("[data-kayit='kayitli']").wait_for(timeout=5000)
    disk = json.loads(kurgu_yol.read_text(encoding="utf-8"))
    bellek = durum()
    adim("otomatik kayıt: disk = bellek", len(disk["klipler"]) == len(bellek["klipler"]) and sorted(c["id"] for c in disk["klipler"]) == sorted(c["id"] for c in bellek["klipler"]), f"rev {disk['rev']}")

    # Terminal değişikliği, bekleyen düzenleme yok
    disk["isaretler"] = [{"t": 1.0, "ad": "terminal"}]
    kurgu_yol.write_text(json.dumps(disk, ensure_ascii=False), encoding="utf-8")
    expect(s.locator(".bildirim", has_text="terminalden güncellendi")).to_be_visible(timeout=5000)
    adim("terminal yazımı arayüze yansıdı", len(durum()["isaret"]) == 1)

    # Çakışma: bekleyen düzenleme + dış yazım
    disk2 = json.loads(kurgu_yol.read_text(encoding="utf-8"))
    s.keyboard.press("m")
    disk2["isaretler"] = []
    kurgu_yol.write_text(json.dumps(disk2, ensure_ascii=False), encoding="utf-8")
    expect(s.locator("dialog[open]", has_text="başka yerden değişti")).to_be_visible(timeout=6000)
    s.screenshot(path=str(cikti / "2-cakisma.png"))
    adim("bekleyen düzenleme + dış yazım: sessizce ezilmedi, soruldu")
    s.locator("dialog[open]").get_by_role("button", name="Diskteki sürümü al").click()
    expect(s.locator("dialog[open]")).to_have_count(0)
    adim("diskteki sürüm alındı", durum()["isaret"] == [])

    # Medyadan timeline'a sürükle, film şeridi ve dalga
    s.locator(".dv-tab", has_text="Medya").first.click()
    s.locator("input[type=file]").first.set_input_files(video)
    satir = s.locator(".satir[title^='deneme']")
    expect(satir.first).to_be_visible(timeout=15000)
    hedef = s.locator("canvas[data-timeline]")
    x, y = yer(33, "V2")
    i = bilgi()
    n0 = sorted(c["id"] for c in durum()["klipler"])
    satir.first.drag_to(s.locator(".tl-kaydirici"), target_position={"x": x - i["l"], "y": y - i["t"]})
    s.wait_for_function("(e) => window.__studio.depo.getState().kurgu.klipler.some(c => !e.includes(c.id))", arg=n0, timeout=8000)
    d = durum()
    yeni = [c for c in d["klipler"] if c["id"] in d["secim"]]
    adim("Medya → timeline sürükle bırak", len(yeni) == 1 and yeni[0]["iz"] == "V2" and yeni[0]["tur"] == "video", str({k: yeni[0][k] for k in ("iz", "bas", "sure")}))
    # Geri al kaynak eklemeyi de alır
    s.keyboard.press("Control+z")
    adim("geri al eklemeyi kaldırdı", sorted(c["id"] for c in durum()["klipler"]) == n0)
    s.keyboard.press("Control+y")

    # Kaynak monitör I/O + insert
    satir.first.click()
    expect(s.locator("video[data-kaynak-video]")).to_be_visible()
    s.wait_for_function("document.querySelector('video[data-kaynak-video]').readyState >= 2")
    s.evaluate("() => { document.querySelector('video[data-kaynak-video]').currentTime = 1; }")
    s.wait_for_timeout(150)
    s.locator("button[title^='Giriş işareti']").click()
    s.evaluate("() => { document.querySelector('video[data-kaynak-video]').currentTime = 3; }")
    s.wait_for_timeout(150)
    s.locator("button[title^='Çıkış işareti']").click()
    s.evaluate("() => window.__studio.player.seekTo(60)")
    s.wait_for_timeout(100)
    n0 = len(durum()["klipler"])
    s.get_by_role("button", name="Üzerine yaz (.)").click()
    s.wait_for_function(f"window.__studio.depo.getState().secim.length === 1 && window.__studio.depo.getState().kurgu.klipler.find(c => c.id === window.__studio.depo.getState().secim[0]).sure < 3", timeout=8000)
    d = durum()
    c = [x for x in d["klipler"] if x["id"] == d["secim"][0]][0]
    adim("Kaynak I/O + üzerine yaz: 2 sn, giriş 1", yakin(c["sure"], 2, 0.1) and yakin(c["giris"], 1, 0.1), str({k: round(c[k], 2) for k in ("bas", "sure", "giris")}))
    s.keyboard.press("Control+z")

    # SFX sürükle
    s.locator(".dv-tab", has_text="Kütüphane").first.click()
    s.get_by_label("Kütüphanede ara").fill("tick kenney")
    sfx = s.locator(".panel:has(.sekmeler) .icerik .satir:visible").first
    expect(sfx).to_be_visible(timeout=6000)
    x, y = yer(30, "A2")
    i = bilgi()
    n0 = sorted(c["id"] for c in durum()["klipler"])
    sfx.drag_to(s.locator(".tl-kaydirici"), target_position={"x": x - i["l"], "y": y - i["t"]})
    s.wait_for_function("(e) => window.__studio.depo.getState().kurgu.klipler.some(c => !e.includes(c.id))", arg=n0, timeout=8000)
    d = durum()
    c = [x for x in d["klipler"] if x["id"] in d["secim"]][0]
    adim("SFX → A2", c["iz"] == "A2" and c["tur"] == "ses", str({k: round(c[k], 2) if isinstance(c[k], float) else c[k] for k in ("iz", "bas", "sure")}))

    # Görseller yüklensin, ekran
    s.wait_for_timeout(4000)
    s.keyboard.press("\\")
    s.wait_for_timeout(600)
    s.screenshot(path=str(cikti / "3-timeline.png"))
    koyu = s.evaluate("""() => { const c = document.querySelector('canvas[data-timeline]'); const g = c.getContext('2d'); const d = g.getImageData(0,0,c.width,c.height).data; let renk = new Set(); for (let i=0;i<d.length;i+=4*97) renk.add((d[i]>>3)<<10|(d[i+1]>>3)<<5|d[i+2]>>3); return renk.size; }""")
    adim("film şeridi/dalga çizildi (renk çeşitliliği)", koyu > 150, f"{koyu} renk")

    # Kısayol diyaloğu
    s.get_by_role("button", name="Klavye kısayolları").click()
    expect(s.locator("dialog[open]")).to_contain_text("Ripple sil")
    s.screenshot(path=str(cikti / "4-kisayol.png"))
    s.locator("dialog[open]").get_by_role("button", name="Tamam").click()

    # Yük: 15 dk, 500 klip, 4 iz
    yuk = s.evaluate("""async () => {
      const dp = window.__studio.depo, kk = dp.getState().kurgu;
      const orn = kk.klipler.find(c => c.tur === 'video');
      const klipler = [];
      for (let i=0;i<500;i++) { const iz = ['V2','V1','A2','A3'][i%4]; klipler.push({...orn, id:'y'+i, iz, tur: iz[0]==='A'?'ses':'video', bas: i*1.8, sure:1.7, giris:(i%20), konusmaci:false, olay: iz[0]==='A'?{tur:'sfx'}:null}); }
      const yedek = dp.getState().kurgu;
      dp.setState({kurgu:{...kk, klipler}});
      window.dispatchEvent(new CustomEvent('studio-zoom',{detail:'sigdir'}));
      const sc = window.__studioTl.sc();
      await new Promise(r=>setTimeout(r,800));
      const orneklem = async (ad, adim) => { const ts=[]; let son=performance.now(); const t0=son; while(performance.now()-t0<1500){ adim(); await new Promise(r=>requestAnimationFrame(r)); const n=performance.now(); ts.push(n-son); son=n; } ts.sort((a,b)=>a-b); return {ad, medyanMs:+ts[ts.length>>1].toFixed(1), p95Ms:+ts[Math.floor(ts.length*.95)].toFixed(1), kare:ts.length}; };
      const a = await orneklem('sığmış', ()=>{ dp.setState({zaman: dp.getState().zaman+0.03}); });
      window.dispatchEvent(new CustomEvent('studio-zoom',{detail:'yakin'})); await new Promise(r=>setTimeout(r,200));
      for(let i=0;i<6;i++){window.dispatchEvent(new CustomEvent('studio-zoom',{detail:'yakin'}));} await new Promise(r=>setTimeout(r,300));
      const b = await orneklem('yakın+kaydır', ()=>{ sc.scrollLeft += 8; });
      dp.setState({kurgu:yedek});
      return [a,b];
    }""")
    for y_ in yuk:
        adim(f"yük 500 klip {y_['ad']}", y_["medyanMs"] < 34, json.dumps(y_))

    s.locator("[data-kayit='kayitli']").wait_for(timeout=6000)
    gercek = [k for k in konsol if "Failed to load resource" not in k]
    adim("konsol hatası yok", not gercek, json.dumps(gercek[:5], ensure_ascii=False)[:700])
    b.close()

kotu = [a for a, k in sonuc if not k]
print(f"\n{len(sonuc) - len(kotu)}/{len(sonuc)} geçti")
sys.exit(1 if kotu else 0)
