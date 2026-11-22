import { describe, expect, it } from "vitest";
import type { Klip, KurguProps } from "../remotion/tipler";
import { bezier, donusum, konusmaci } from "./calisma";
import { derle, desteklenmeyenler } from "./derle";
import { layoutP } from "./zaman";

const klip = (o: Partial<Klip>): Klip => ({
  id: "c1", iz: "V1", bas: 0, sure: 2, tur: "video", kaynak: "s1", giris: 1, hiz: 1, konusmaci: false, zoom: 1, punches: [],
  donus: { x: [], y: [], olcek: [], opaklik: [], anim: [] }, efekt: { parlaklik: 1, kontrast: 1, doygunluk: 1, bulanik: 0 },
  ses: { gain_db: 0, fade_in: 0, fade_out: 0, duck: false }, ...o,
});
const kurgu = (klipler: Klip[], ek: Partial<KurguProps> = {}): KurguProps => ({
  sekans: { w: 1080, h: 1920, fps: 30 }, kaynaklar: { s1: { yol: "inputs:a.mp4", sure: 10, ses: true }, s2: { yol: "inputs:b.mp4", sure: 10, ses: true } },
  izler: [{ id: "V1", tur: "video", ad: "V1", kilit: false, sessiz: false, gizli: false, gain_db: 0 }],
  klipler, altyazi: { acik: false, iz: "V1" }, ...ek,
});
const ortam = { mod: "render" as const, medyaUrl: (id: string) => `_k/${id}.mp4`, calismaUrl: "hf/calisma.js", gsapUrl: "hf/gsap.min.js" };

describe("derle", () => {
  it("video klibini HyperFrames klibi olarak yazar", () => {
    const { html, desteklenmeyen } = derle(kurgu([klip({})]), ortam);
    expect(desteklenmeyen).toEqual([]);
    expect(html).toContain('data-composition-id="main"');
    expect(html).toMatch(/<video id="m-c1" class="clip" src="_k\/s1.mp4" data-start="0" data-duration="2" data-track-index="1" data-media-start="1"/);
    expect(html).toContain('data-has-audio="true" data-volume="1"');
  });

  it("çapraz geçişte önceki klip kuyrukla uzar, giren klibe ses fade'i gelir", () => {
    const a = klip({ id: "a", sure: 2 }), b = klip({ id: "b", bas: 2, kaynak: "s2", gecis_giris: { tur: "capraz", sure: 0.5 } });
    const { html } = derle(kurgu([a, b]), ortam);
    expect(html).toMatch(/id="m-a"[^>]*data-duration="2.5"[^>]*data-fade-out="0.5"/);
    expect(html).toMatch(/id="m-b"[^>]*data-track-index="2"[^>]*data-fade-in="0.5"/);
  });

  it("taşınmamış özellikleri listeler", () => {
    const d = desteklenmeyenler(kurgu([
      klip({ id: "s", tur: "sahne", sahne: { kind: "stat", layout: "full" } }),
      klip({ id: "f", tur: "sahne", sahne: { kind: "fizik" } }),
      klip({ id: "n", tur: "motion", kaynak: null, bilesen: { ad: "ikon/tik" } }),
      klip({ id: "m", tur: "metin", kaynak: null, metin: "A", metin_stil: { tip: "anahtar" } }),
      klip({ id: "g", gecis_giris: { tur: "iris", sure: 0.6 } }),
    ], { altyazi: { acik: true, iz: "V1" }, words: [{ w: "a", s: 0, e: 0.2 }] }));
    expect(d).toEqual(["native:ikon/tik", "sahne:fizik"]);
  });

  it("metin grafiği ve sahneler React adasına düşer; ada yoksa ada.js yüklenmez", () => {
    const o = { ...ortam, adaUrl: "hf/ada.js" };
    expect(derle(kurgu([klip({})]), o).html).not.toContain("ada.js");
    const { html } = derle(kurgu([
      klip({ id: "m", tur: "metin", kaynak: null, bas: 1, sure: 2, metin: "A", metin_stil: { tip: "etiket" } }),
      klip({ id: "s", tur: "sahne", kaynak: null, bas: 3, sure: 2, sahne: { kind: "stat", layout: "split" } }),
      klip({ id: "t", tur: "sahne", kaynak: null, bas: 5, sure: 2, sahne: { kind: "hook", layout: "full" } }),
    ]), o);
    expect(html).toContain('<script src="hf/ada.js">');
    expect(html).toContain('id="ada-m"');
    expect(html).toContain('id="ada-sts"');
    const veri = JSON.parse(html.match(/window.__KURGU = (.*);<\/script>/)![1]);
    const ad = Object.fromEntries(veri.adalar.map((a: any) => [a.id, a]));
    expect(ad.m).toMatchObject({ tur: "metin", bas: 30, sure: 60 });
    expect(ad.sts).toMatchObject({ tur: "bolunmus", bas: 90, sure: 70 }); // tam ekrana dönüşte +10 kare
    expect(ad.t).toMatchObject({ tur: "baslik", bas: 150 });
    expect(veri.klipler.find((k: any) => k.id === "t").ham).toBe(true);
  });
});

describe("ön render", () => {
  it("fizik sahnesi ön render eşlemesiyle video klibi olur, eşlemesiz desteklenmez", () => {
    const k = klip({ id: "fz", tur: "sahne", kaynak: "s1", bas: 1, sure: 3, giris: 0, sahne: { kind: "fizik", layout: "full" } as any });
    expect(desteklenmeyenler(kurgu([k]))).toEqual(["sahne:fizik"]);
    expect(desteklenmeyenler(kurgu([k]), {}, { onRender: true })).toEqual([]);
    const { html, desteklenmeyen } = derle(kurgu([k]), { ...ortam, onRender: { fz: "hf/onrender/fz-1.webm" } });
    expect(desteklenmeyen).toEqual([]);
    expect(html).toMatch(/<video id="m-fz" class="clip" src="hf\/onrender\/fz-1.webm" data-start="1" data-duration="3"[^>]*muted/);
    const veri = JSON.parse(html.match(/window.__KURGU = (.*);<\/script>/)![1]);
    expect(veri.klipler.find((c: any) => c.id === "fz").ham).toBe(true);
  });
});

describe("ses zarfı", () => {
  it("ses.kf Remotion sesEgrisi ile aynı kazancı data-automation'a yazar", () => {
    const k = klip({ id: "m", iz: "A1", tur: "ses", kaynak: "s1", bas: 1, sure: 4, giris: 0,
      ses: { gain_db: 0, fade_in: 0, fade_out: 0, duck: false, kf: [{ t: 0, v: 0, ease: "dogrusal" }, { t: 2, v: -12, ease: "dogrusal" }] } as any });
    const p = kurgu([k]);
    p.izler.push({ id: "A1", tur: "ses", ad: "A1", kilit: false, sessiz: false, gizli: false, gain_db: 0 });
    expect(desteklenmeyenler(p)).toEqual([]);
    const { html } = derle(p, ortam);
    const ham = html.match(/id="a-m"[^>]*data-automation="([^"]+)"/)![1].replace(/&quot;/g, '"');
    const nokta = JSON.parse(ham).lanes[0].points as { t: number; v: number }[];
    const bul = (t: number) => nokta.find((x) => Math.abs(x.t - t) < 1e-3)!.v;
    expect(bul(0)).toBeCloseTo(1, 3);
    expect(bul(1)).toBeCloseTo(10 ** (-6 / 20), 3);   // 2 sn'de -12 dB'e doğrusal: 1. sn -6 dB
    expect(bul(3)).toBeCloseTo(10 ** (-12 / 20), 3);
    expect(html).not.toMatch(/id="a-m"[^>]*data-volume/);
  });
});

describe("native bileşen", () => {
  const meta = { ad: "ikon/tik", tur: "ikon", etiketler: [], ne_zaman: "", sure: { min: 1, varsayilan: 1.3, max: 1.6 }, giris_sn: 0.35, cikis_sn: 0.2,
    hero: false, en_boy: ["9:16"], yer: ["ust"], boyut: { w: 0.26, h: 0.26 }, en_kucuk_px: 180 } as any;
  const o = { ...ortam, cekirdekUrl: "hf/native/cekirdek.js", native: { "ikon/tik": { meta, varsayilan: { renk: "olumlu" } } } };
  const n = (ek: Partial<Klip> = {}) => klip({ id: "n1", tur: "motion", kaynak: null, bas: 2, sure: 1.3, bilesen: { ad: "ikon/tik", param: { renk: "vurgu", odakKarart: true } }, ...ek });

  it("taşınan bileşen alt kompozisyon olarak bağlanır; taşınmayan Remotion'a düşer", () => {
    expect(desteklenmeyenler(kurgu([n()]), o.native)).toEqual([]);
    expect(desteklenmeyenler(kurgu([n({ bilesen: { ad: "ikon/kalp" } })]), o.native)).toEqual(["native:ikon/kalp"]);
    const { html, baglamalar } = derle(kurgu([n()]), o);
    expect(baglamalar).toEqual([{ kok: "n-n1", ad: "ikon/tik", src: "hf/n/n-n1.html" }]);
    expect(html).toMatch(/id="n-n1" data-composition-id="n-n1" data-composition-src="hf\/n\/n-n1.html" data-start="1.999667" data-duration="1.300333"/);
    expect(html).toContain('<script src="hf/native/cekirdek.js">');
    const yer = JSON.parse(html.match(/window.__HFN_YER = (.*?);<\/script>/)![1])["n-n1"];
    expect(yer).toMatchObject({ sureKare: 39, fps: 30, ofset: 0, giris_sn: 0.35, cikis_sn: 0.2, karart: true, param: { renk: "vurgu" } });
    expect(yer.param.odakKarart).toBeUndefined();
    expect(yer.kutu.w).toBe(281); // round(0.26 × 1080), boyutHesapla
    expect(yer.kutu.y).toBeGreaterThanOrEqual(192); // platform üst barının altında
  });

  it("yarım kareye düşen başlangıç Remotion gibi yuvarlanır, kare sınırının hemen önüne yazılır", () => {
    // 1.65 sn × 30 = 49,5 → Remotion Sequence from 50. Ms'ye yuvarlanmış "1.667" HyperFrames'te 51. kareye düşüyordu.
    const { html } = derle(kurgu([n({ bas: 1.65 })]), o);
    const bas = Number(html.match(/id="n-n1"[^>]*data-start="([\d.]+)"/)![1]);
    expect(bas * 30).toBeGreaterThan(49.98);
    expect(bas * 30).toBeLessThan(50);
  });

  it("pencere klibin başını keserse sahne saati ofsetle ilerler", () => {
    const { html } = derle(kurgu([n()]), { ...o, pencere: [2.5, 5] });
    expect(html).toMatch(/id="n-n1"[^>]*data-start="0" data-duration="0.8"/);
    expect(JSON.parse(html.match(/window.__HFN_YER = (.*?);<\/script>/)![1])["n-n1"].ofset).toBeCloseTo(0.5);
  });
});

describe("çalışma zamanı", () => {
  it("bezier uçlarda 0 ve 1", () => {
    const e = bezier(0.16, 1, 0.3, 1);
    expect(e(0)).toBe(0);
    expect(e(1)).toBe(1);
    expect(e(0.5)).toBeGreaterThan(0.8);
  });

  it("giriş geçişinde opaklık 0'dan başlar, keyframe ölçeği uygulanır", () => {
    const k = { ...klip({ gecis_giris: { tur: "capraz", sure: 1 }, donus: { x: [], y: [], olcek: [{ t: 0, v: 1.2, ease: "dogrusal" }], opaklik: [], anim: ["olcek"] } }), on: 0, kuyruk: 0, cikis: null };
    expect(donusum(k, undefined, 0, 1080, 1920).opacity).toBe(0);
    expect(donusum(k, undefined, 1.5, 1080, 1920).transform).toContain("scale(1.2)");
  });

  it("punch zoom'u büyütür ve bırakır", () => {
    const k = { ...klip({ konusmaci: true, punches: [{ t: 2, olcek: 1.2, sure: 0.5 }] }), on: 0, kuyruk: 0, cikis: null };
    expect(konusmaci(k, 0, 30).z).toBe(1);
    expect(konusmaci(k, 1.3, 30).z).toBeGreaterThan(1.15);
    expect(konusmaci(k, 3, 30).z).toBe(1);
  });

  it("bölünmüş düzen: panel 10 karede iner, taban zoom 1'e gider, tam ekrana döner", () => {
    const sc = [{ layout: "split", start: 1 }, { layout: "full", start: 3 }];
    expect(layoutP(29, 30, sc)).toBe(0);
    expect(layoutP(40, 30, sc)).toBe(1);
    expect(layoutP(35, 30, sc)).toBeGreaterThan(0.4);
    expect(layoutP(100, 30, sc)).toBe(0);
    const k = { ...klip({ konusmaci: true, zoom: 1.2 }), on: 0, kuyruk: 0, cikis: null };
    expect(konusmaci(k, 0, 30, 1).z).toBe(1);
    expect(konusmaci(k, 0, 30, 0).z).toBe(1.2);
  });
});

describe("hız seçenekleri", () => {
  it("ölçek kökü küçültür, sahneyi ölçekler", () => {
    const { html } = derle(kurgu([klip({})]), { ...ortam, olcek: 0.5 });
    expect(html).toContain('data-width="540" data-height="960"');
    expect(html).toContain("transform: scale(0.5)");
  });

  it("pencere dışındaki klipleri atar, içerdekileri kaydırır", () => {
    const a = klip({ id: "a", bas: 0, sure: 4 }), b = klip({ id: "b", bas: 4, sure: 4, kaynak: "s2" }), c = klip({ id: "c", bas: 8, sure: 4 });
    const { html, bitis } = derle(kurgu([a, b, c]), { ...ortam, pencere: [3, 6] });
    expect(bitis).toBe(3);
    expect(html).not.toContain('id="m-c"');
    expect(html).toMatch(/id="m-a"[^>]*data-start="0" data-duration="1"[^>]*data-media-start="4"/);
    expect(html).toMatch(/id="m-b"[^>]*data-start="1" data-duration="2"[^>]*data-media-start="1"/);
    expect(html).toContain('"kaydir":3');
  });
});

import { buildPages, buildTokens, sayfaBul, sayfaHtml, CAP_VARSAYILAN } from "./altyazi";

describe("altyazı", () => {
  const words = [{ w: "Merhaba", s: 0, e: 0.4 }, { w: "dünya.", s: 0.5, e: 0.9 }, { w: "Yeni", s: 1.2, e: 1.5 }, { w: "sayfa", s: 1.6, e: 2 }];
  it("cümle sonunda yeni sayfa, okunan kelime turuncu (ADR 0014)", () => {
    const pages = buildPages(buildTokens(words));
    expect(pages.map((p) => p.map((t) => t.text))).toEqual([["Merhaba", "dünya."], ["Yeni", "sayfa"]]);
    const s = sayfaBul(pages, 0.6)!;
    expect(s.aktif).toBe(1);
    const v = { acik: true, words, stil: null, renk: CAP_VARSAYILAN, yatay: false, w: 1080, h: 1920 };
    expect(sayfaHtml(v, s.pg, s.aktif)).toMatch(/color:#FFFFFF[^>]*>Merhaba<\/span><span[^>]*color:#FF7A00[^>]*>dünya.</);
    expect(sayfaBul(pages, 3.5)).toBeNull();
  });

  it("derleyici altyazı kutusunu yazar", () => {
    const { html, desteklenmeyen } = derle(kurgu([klip({})], { altyazi: { acik: true, iz: "V1" }, words }), ortam);
    expect(desteklenmeyen).toEqual([]);
    expect(html).toContain('<div id="altyazi" style="position:absolute;left:0;width:1080px;top:1352px');
  });
});

import { random as rRandom } from "remotion";
import { gecisStil, random, ORTA_GECIS } from "./gecis";
import { ORTA } from "./zaman";

describe("geçişler", () => {
  const renk = { vurgu: "#FF7A00", ikincil: "#FFD400", yazi: "#FFFFFF", zemin: "#0B0D12" };
  it("random Remotion ile aynı (piksel ve bozulma blok sırası)", () => {
    for (const t of ["piksel-3-7", "yirt-4", "boz-ex-5"]) expect(random(t)).toBe(rRandom(t));
  });
  it("orta noktalı küme iki yerde aynı", () => {
    expect([...ORTA].sort()).toEqual([...ORTA_GECIS].sort());
  });
  it("her geçiş uçlarda geçerli stil üretir", () => {
    for (const tur of ORTA_GECIS) for (const yon of ["entering", "exiting"] as const) for (const p of [0, 0.5, 1]) {
      const s = gecisStil({ tur: tur as any, sure: 0.6, yon: "sol" }, p, yon, 1080, 1920, renk);
      expect(typeof s.transform).toBe("string");
    }
    expect(gecisStil({ tur: "sil", sure: 0.6, yon: "sol" }, 0.5, "entering", 1080, 1920, renk).clipPath).toContain("polygon(100% 0%");
    expect(gecisStil({ tur: "iris", sure: 0.6 }, 1, "entering", 1080, 1920, renk).clipPath).toMatch(/^path\("M /);
  });
});
