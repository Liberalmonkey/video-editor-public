// WHY: 2026-11-28 stabilite denetimi bulguları (1, 2, 5, 6, 7, 9) için regresyon testleri.
import { readFileSync } from "node:fs";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { KurguProps } from "../../../remotion/tipler";

type Dinleyici = (e: any) => void;

const ortam = vi.hoisted(() => {
  const dinleyiciler = new Map<string, Dinleyici[]>();
  const kaynaklar: { url: string; onopen: (() => void) | null; onerror: (() => void) | null; onmessage: ((m: { data: string }) => void) | null; kapali: boolean; close: () => void }[] = [];

  class SahteEventSource {
    url: string;
    onopen: (() => void) | null = null;
    onerror: (() => void) | null = null;
    onmessage: ((m: { data: string }) => void) | null = null;
    kapali = false;
    constructor(url: string) {
      this.url = url;
      kaynaklar.push(this);
    }
    close = () => { this.kapali = true; };
  }

  (globalThis as any).window = {
    addEventListener: (tur: string, fn: Dinleyici) => {
      dinleyiciler.set(tur, [...(dinleyiciler.get(tur) ?? []), fn]);
    },
    removeEventListener: (tur: string, fn: Dinleyici) => {
      dinleyiciler.set(tur, (dinleyiciler.get(tur) ?? []).filter((x) => x !== fn));
    },
  };
  (globalThis as any).EventSource = SahteEventSource;
  (globalThis as any).localStorage = {
    veri: new Map<string, string>(),
    getItem(k: string) { return this.veri.get(k) ?? null; },
    setItem(k: string, v: string) { this.veri.set(k, v); },
  };
  return { dinleyiciler, kaynaklar };
});

import { isAkisiBaglan, useDepo, type Proje } from "../depo";
import { useKurgu, type KurguYaniti } from "./depo";

const bosKurgu = (ek: Partial<KurguProps> = {}): KurguProps => ({
  sekans: { w: 1080, h: 1920, fps: 30 },
  kaynaklar: {},
  kelimeler: {},
  izler: [
    { id: "V2", tur: "video", ad: "", kilit: false, sessiz: false, gizli: false, gain_db: 0 },
    { id: "V1", tur: "video", ad: "", kilit: false, sessiz: false, gizli: false, gain_db: 0 },
    { id: "A1", tur: "ses", ad: "", kilit: false, sessiz: false, gizli: false, gain_db: 0 },
  ],
  klipler: [],
  altyazi: { acik: true, iz: "V1" },
  isaretler: [],
  ...ek,
});

const yanitYap = (etag: string, kurgu: KurguProps = bosKurgu()): KurguYaniti => ({
  kurgu,
  medya: {},
  etag,
});

const jsonYanit = (veri: unknown, status = 200) =>
  new Response(JSON.stringify(veri), { status, headers: { "Content-Type": "application/json" } });

const ertele = <T,>() => {
  let coz!: (v: T) => void;
  let reddet!: (e: unknown) => void;
  const soz = new Promise<T>((c, r) => { coz = c; reddet = r; });
  return { soz, coz, reddet };
};

const bekle = async (n = 4) => {
  for (let i = 0; i < n; i++) await Promise.resolve();
};

beforeEach(() => {
  ortam.kaynaklar.length = 0;
  useKurgu.getState().ac(null, null);
  useDepo.setState({
    studyolar: [],
    projeler: [],
    aktif: null,
    kurguDurum: "yok",
    goruntu: null,
    surum: 0,
    bildirimler: [],
    isler: [],
    gunlukler: {},
    baglanti: true,
  });
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe("Bulgu 1: kaydet tek uçuş kilidi ve proje geçişi", () => {
  it("kayıt sürerken duzenle() durumu kaydediliyor tutar; ikinci kaydet() önce ilkini bekleyip güncel kurguyu yeni etag ile yazar", async () => {
    const p1 = ertele<Response>();
    const p2 = ertele<Response>();
    const istekler: { etag: string | null; fps: number }[] = [];
    let cagri = 0;

    vi.stubGlobal("fetch", vi.fn((_url: string, init?: RequestInit) => {
      const hdr = (init?.headers ?? {}) as Record<string, string>;
      const govde = JSON.parse(String(init?.body)) as KurguProps;
      istekler.push({ etag: hdr["If-Match"] ?? null, fps: govde.sekans.fps });
      return ++cagri === 1 ? p1.soz : p2.soz;
    }));

    useKurgu.getState().ac("instagram/a", yanitYap("e1"));
    useKurgu.getState().duzenle("fps 60", (d) => { d.sekans.fps = 60; });

    const k1 = useKurgu.getState().kaydet();
    expect(useKurgu.getState().kayit).toBe("kaydediliyor");
    expect(istekler).toHaveLength(1);

    // Kayıt sürerken yeni düzenleme: durum "kaydediliyor" kalmalı, paralel ikinci PUT çıkmamalı.
    useKurgu.getState().duzenle("fps 24", (d) => { d.sekans.fps = 24; });
    expect(useKurgu.getState().kayit).toBe("kaydediliyor");
    expect(istekler).toHaveLength(1);

    // Kayıt sürerken çağrılan ikinci kaydet() uçuştakini beklemeli.
    const k2 = useKurgu.getState().kaydet();
    await bekle();
    expect(istekler).toHaveLength(1);

    // İlk PUT bittiğinde ikinci PUT yeni etag ("e2") ve güncel kurgu (fps: 24) ile başlamalı.
    p1.coz(jsonYanit({ etag: "e2" }));
    await k1;
    await bekle();
    expect(istekler).toHaveLength(2);
    expect(istekler[1]).toEqual({ etag: "e2", fps: 24 });

    p2.coz(jsonYanit({ etag: "e3" }));
    await k2;
    expect(useKurgu.getState().kayit).toBe("kayitli");
    expect(useKurgu.getState().etag).toBe("e3");
  });

  it("projeAc() uçuştaki kayıt ve bekleyen düzenleme yazılana kadar eski projeyi kapatmaz", async () => {
    const put1 = ertele<Response>();
    const put2 = ertele<Response>();
    const putGovdeler: number[] = [];
    let putSayisi = 0;

    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      if (init?.method === "PUT") {
        putGovdeler.push((JSON.parse(String(init.body)) as KurguProps).sekans.fps);
        return ++putSayisi === 1 ? put1.soz : put2.soz;
      }
      return Promise.resolve(jsonYanit(yanitYap("b1", bosKurgu({ sekans: { w: 1920, h: 1080, fps: 30 } }))));
    }));

    const pA: Proje = { studyo: "instagram", ad: "a", kurgu: true, props: false };
    const pB: Proje = { studyo: "instagram", ad: "b", kurgu: true, props: false };
    useDepo.setState({ aktif: pA });
    useKurgu.getState().ac("instagram/a", yanitYap("e1"));
    useKurgu.getState().duzenle("ilk", (d) => { d.sekans.fps = 50; });

    const ilkKayit = useKurgu.getState().kaydet();
    // Kayıt uçuşta iken yeni düzenleme yapılıp hemen başka projeye geçiliyor.
    useKurgu.getState().duzenle("ikinci", (d) => { d.sekans.fps = 25; });
    const gecis = useDepo.getState().projeAc(pB);
    await bekle();

    // İlk PUT bitmeden pA kapatılmamalı.
    expect(useKurgu.getState().anahtar).toBe("instagram/a");
    put1.coz(jsonYanit({ etag: "e2" }));
    await ilkKayit;
    await bekle();

    // İkinci PUT bekleyen düzenlemeyi (fps 25) yazmalı; o bitmeden pB açılmamalı.
    expect(putGovdeler).toEqual([50, 25]);
    expect(useKurgu.getState().anahtar).toBe("instagram/a");

    put2.coz(jsonYanit({ etag: "e3" }));
    await gecis;
    expect(useKurgu.getState().anahtar).toBe("instagram/b");
  });
});

describe("Bulgu 2: hata durumunda tazele/beforeunload ve izle() proje yarışı", () => {
  it("tazele() kayit === 'hata' iken yerel kurguyu ezmez, çakışma diyaloğu açar", () => {
    useKurgu.getState().ac("instagram/a", yanitYap("e1"));
    useKurgu.getState().duzenle("yerel", (d) => { d.sekans.fps = 60; });
    useKurgu.setState({ kayit: "hata" });

    useKurgu.getState().tazele(yanitYap("e2", bosKurgu({ sekans: { w: 1080, h: 1920, fps: 30 } })));
    expect(useKurgu.getState().cakisma).toBe(true);
    expect(useKurgu.getState().kurgu?.sekans.fps).toBe(60);
    expect(useKurgu.getState().geri).toHaveLength(1);
  });

  it("beforeunload kayit === 'hata' iken e.preventDefault() çağırır", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>(() => {})));
    useKurgu.getState().ac("instagram/a", yanitYap("e1"));
    useKurgu.setState({ kayit: "hata" });

    const preventDefault = vi.fn();
    for (const fn of ortam.dinleyiciler.get("beforeunload") ?? []) fn({ preventDefault });
    expect(preventDefault).toHaveBeenCalledTimes(1);
  });

  it("izle() await sonrası proje değiştiyse eski SSE yanıtı yeni projeyi ezmez", async () => {
    const geciken = ertele<Response>();
    vi.stubGlobal("fetch", vi.fn(() => geciken.soz));

    useKurgu.getState().ac("instagram/a", yanitYap("a1", bosKurgu({ sekans: { w: 1080, h: 1920, fps: 30 } })));
    const esA = ortam.kaynaklar[ortam.kaynaklar.length - 1];
    const olay = esA.onmessage?.({ data: "a2" });

    // Yanıt gelmeden başka proje açılıyor.
    useKurgu.getState().ac("instagram/b", yanitYap("b1", bosKurgu({ sekans: { w: 1920, h: 1080, fps: 60 } })));
    geciken.coz(jsonYanit(yanitYap("a2", bosKurgu({ sekans: { w: 720, h: 1280, fps: 24 } }))));
    await olay;

    expect(useKurgu.getState().anahtar).toBe("instagram/b");
    expect(useKurgu.getState().kurgu?.sekans.fps).toBe(60);
    expect(useKurgu.getState().etag).toBe("b1");
  });
});

describe("Bulgu 9: kaynaktanEkle() proje değişimi ve güncel kurgudan id üretimi", () => {
  it("await sürerken proje değişirse medya ve klip yeni projeye yazılmaz", async () => {
    const sorgu = ertele<Response>();
    vi.stubGlobal("fetch", vi.fn(() => sorgu.soz));

    useKurgu.getState().ac("instagram/a", yanitYap("a1"));
    const ekle = useKurgu.getState().kaynaktanEkle({ yol: "inputs/a.mp4", ad: "a.mp4", tur: "video" }, 0, "V1", false);

    useKurgu.getState().ac("instagram/b", yanitYap("b1"));
    sorgu.coz(jsonYanit({ url: "/dosya/a.mp4", sure: 5, w: 1080, h: 1920, ses: true, kelimeler: [] }));
    await ekle;

    expect(useKurgu.getState().anahtar).toBe("instagram/b");
    expect(useKurgu.getState().kurgu?.klipler).toHaveLength(0);
    expect(Object.keys(useKurgu.getState().medya)).toHaveLength(0);
  });

  it("eşzamanlı çakışan son-ekli eklemelerde medya ve kurgu.kaynaklar aynı id'yi kullanır", async () => {
    const r1 = ertele<Response>();
    const r2 = ertele<Response>();
    let n = 0;
    vi.stubGlobal("fetch", vi.fn(() => (++n === 1 ? r1.soz : r2.soz)));

    useKurgu.getState().ac("instagram/a", yanitYap("a1"));
    const son = "x".repeat(40) + ".mp4";
    const e1 = useKurgu.getState().kaynaktanEkle({ yol: `klasor1/${son}`, ad: "bir", tur: "video" }, 0, "V1", false);
    const e2 = useKurgu.getState().kaynaktanEkle({ yol: `klasor2/${son}`, ad: "iki", tur: "video" }, 6, "V1", false);

    r1.coz(jsonYanit({ url: "/dosya/1.mp4", sure: 5, w: 1080, h: 1920, ses: true, kelimeler: [] }));
    await e1;
    r2.coz(jsonYanit({ url: "/dosya/2.mp4", sure: 5, w: 1080, h: 1920, ses: true, kelimeler: [] }));
    await e2;

    const d = useKurgu.getState();
    const kaynakIdler = Object.keys(d.kurgu!.kaynaklar).sort();
    expect(kaynakIdler).toHaveLength(2);
    expect(Object.keys(d.medya).sort()).toEqual(kaynakIdler);
    for (const c of d.kurgu!.klipler) {
      expect(d.medya[c.kaynak!]).toBeTruthy();
      expect(d.kurgu!.kaynaklar[c.kaynak!]).toBeTruthy();
    }
  });
});

describe("Bulgu 5: isAkisiBaglan() bozuk SSE ve eksik yeni alanı koruması", () => {
  it("bozuk JSON fırlatmaz, v.yeni eksik olsa da bitiş yenilemesi çalışır", async () => {
    vi.stubGlobal("fetch", vi.fn((url: string) => {
      if (url === "/api/projeler") return Promise.resolve(jsonYanit({ studyolar: ["instagram"], projeler: [] }));
      return Promise.resolve(jsonYanit(yanitYap("e1")));
    }));

    const kapat = isAkisiBaglan();
    const es = ortam.kaynaklar[ortam.kaynaklar.length - 1];

    expect(() => es.onmessage?.({ data: "{kesik-json" })).not.toThrow();

    useDepo.setState({
      isler: [{ id: 7, komut: "taslak", baslik: "Taslak", durum: "calisiyor", baslangic: 1, bitis: null, kod: null }],
      surum: 0,
    });

    // v.yeni yokken bile çökmemeli ve bitiş akışı çalışmalı.
    expect(() => es.onmessage?.({ data: JSON.stringify({ id: 7, komut: "taslak", baslik: "Taslak", durum: "bitti", baslangic: 1, bitis: 2, kod: 0 }) })).not.toThrow();
    await bekle();

    expect(useDepo.getState().surum).toBe(1);
    expect(useDepo.getState().bildirimler.some((b) => b.metin.includes("Bitti: Taslak"))).toBe(true);
    kapat();
  });

  it("onopen yeniden bağlantıda reddedilen kaydet() hatasını yakalar", async () => {
    const kaydetCasus = vi.spyOn(useKurgu.getState(), "kaydet").mockRejectedValueOnce(new Error("ağ koptu"));
    useDepo.setState({ baglanti: false });

    const kapat = isAkisiBaglan();
    const es = ortam.kaynaklar[ortam.kaynaklar.length - 1];
    es.onopen?.();
    await bekle();

    expect(kaydetCasus).toHaveBeenCalledTimes(1);
    expect(useDepo.getState().bildirimler.some((b) => b.hata && b.metin.includes("ağ koptu"))).toBe(true);
    kapat();
  });
});

describe("Bulgu 7: projeAc/kurguAl istek sayacı ve ProjePaneli silme karşılaştırması", () => {
  it("hızlı art arda projeAc() çağrılarında eski geçiş yeni seçimi ezmez", async () => {
    const kaydetBekle = ertele<void>();
    vi.spyOn(useKurgu.getState(), "kaydet").mockImplementationOnce(() => kaydetBekle.soz).mockResolvedValue(undefined);
    vi.stubGlobal("fetch", vi.fn((url: string) =>
      Promise.resolve(jsonYanit(yanitYap(url.endsWith("/b") ? "eb" : "ea", bosKurgu({ sekans: { w: 1080, h: 1920, fps: url.endsWith("/b") ? 60 : 24 } })))),
    ));

    const pA: Proje = { studyo: "instagram", ad: "a", kurgu: true, props: false };
    const pB: Proje = { studyo: "instagram", ad: "b", kurgu: true, props: false };

    const g1 = useDepo.getState().projeAc(pA);
    const g2 = useDepo.getState().projeAc(pB);
    kaydetBekle.coz();
    await Promise.all([g1, g2]);

    expect(useDepo.getState().aktif).toEqual(pB);
    expect(useKurgu.getState().anahtar).toBe("instagram/b");
    expect(useKurgu.getState().kurgu?.sekans.fps).toBe(60);
  });

  it("aynı proje için paralel kurguAl() çağrılarında geç dönen eski yanıt yeni durumu ezmez", async () => {
    const eski = ertele<Response>();
    const yeni = ertele<Response>();
    let n = 0;
    vi.stubGlobal("fetch", vi.fn(() => (++n === 1 ? eski.soz : yeni.soz)));

    const pA: Proje = { studyo: "instagram", ad: "a", kurgu: true, props: false };
    useDepo.setState({ aktif: pA });

    const c1 = useDepo.getState().kurguAl();
    const c2 = useDepo.getState().kurguAl();

    yeni.coz(jsonYanit(yanitYap("yeni-etag", bosKurgu({ sekans: { w: 1080, h: 1920, fps: 60 } }))));
    await c2;
    expect(useKurgu.getState().etag).toBe("yeni-etag");
    expect(useKurgu.getState().kurgu?.sekans.fps).toBe(60);

    eski.coz(jsonYanit(yanitYap("eski-etag", bosKurgu({ sekans: { w: 1080, h: 1920, fps: 24 } }))));
    await c1;
    expect(useKurgu.getState().etag).toBe("yeni-etag");
    expect(useKurgu.getState().kurgu?.sekans.fps).toBe(60);
  });

  it("ProjePaneli silme kontrolü referans eşitliği yerine studyo+ad karşılaştırır", () => {
    const kaynak = readFileSync(path.resolve(__dirname, "../paneller/ProjePaneli.tsx"), "utf8");
    expect(kaynak).not.toContain("if (aktif === p)");
    expect(kaynak).toContain("guncelAktif?.studyo === p.studyo && guncelAktif.ad === p.ad");
  });
});

describe("Bulgu 6: main.tsx kök PanelKoruma ve onDidLayoutChange temizliği", () => {
  it("kök render PanelKoruma('Uygulama') ile sarılı ve layout aboneliği dispose ediliyor", () => {
    const kaynak = readFileSync(path.resolve(__dirname, "../main.tsx"), "utf8");
    expect(kaynak).toContain('<PanelKoruma ad="Uygulama"><App /></PanelKoruma>');
    expect(kaynak).toContain("layoutDinleyici.current = e.api.onDidLayoutChange(");
    expect(kaynak).toContain("layoutDinleyici.current?.dispose()");
  });
});
