// @vitest-environment node
import { describe, expect, it } from "vitest";
// @ts-expect-error bake.mjs tip bildirgesi yok; Node betiği olarak da çalışır
import { bake } from "./bake.mjs";
import { araDurum, darbe, durum, kelvin, type Bake } from "./FizikSahne";
import { deger, genislet } from "../hazirEfekt";
import type { Klip } from "../tipler";

// WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Fizik sahnesinin sözü: aynı girdi aynı kareyi verir, temas anı
// kuramla tutar, ses olayı temas karesindedir.

describe("fizik bake", () => {
  it("deterministik: aynı girdi iki kez birebir aynı yörüngeyi verir", async () => {
    const a = await bake({ preset: "domino", param: { adet: 8 }, fps: 30, sure: 2 });
    const b = await bake({ preset: "domino", param: { adet: 8 }, fps: 30, sure: 2 });
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
  });

  it("serbest düşme: ilk temas ve çarpma hızı kuramla tutar", async () => {
    const h = 3, r = 0.25, g = 9.81;
    const b: Bake = await bake({ preset: "top-dusme", param: { yukseklik: h, yaricap: r, yatay_hiz: 0, sekme: 0.7 }, fps: 30, sure: 2 });
    const ilk = b.temas[0];
    const t = Math.sqrt((2 * (h - r)) / g), v = Math.sqrt(2 * g * (h - r));
    expect(Math.abs(ilk.t - t)).toBeLessThan(1 / 30); // bir kareden az sapma
    expect(Math.abs(ilk.hiz - v) / v).toBeLessThan(0.03);
    expect(ilk.kare).toBe(Math.round(ilk.t * 30));
    // İkinci çarpma hızı sekme katsayısıyla düşer.
    expect(b.temas[1].hiz / ilk.hiz).toBeCloseTo(0.7, 1);
  });

  it("yuvarlanma: kaymadan yuvarlanan kürenin ivmesi 5/7·g·sinθ", async () => {
    const b: Bake = await bake({ preset: "yuvarlanma", param: { egim: 20, uzunluk: 8, surtunme: 1, engel: "yok" }, fps: 60, sure: 1 });
    const a0 = durum(b, "top", 6).p, a1 = durum(b, "top", 36).p; // 0,1 ile 0,6 sn arası, rampa üstünde
    const yol = Math.hypot(a1[0] - a0[0], a1[1] - a0[1]);
    const ivme = (5 / 7) * 9.81 * Math.sin((20 * Math.PI) / 180);
    const kuram = 0.5 * ivme * (0.6 ** 2 - 0.1 ** 2);
    expect(Math.abs(yol - kuram) / kuram).toBeLessThan(0.08);
  });

  it("araba: hız ölçümü ivmeyle doğrusal artar, en yüksek hızda durur", async () => {
    const b: Bake = await bake({ preset: "araba-ivme", param: { ivme: 5, en_hiz: 10 }, fps: 30, sure: 4 });
    const kmsa = b.olcum.deger;
    expect(kmsa[0]).toBe(0);
    expect(kmsa[Math.round(1.15 * 30)]).toBeCloseTo(5 * 3.6, 0); // 0,15 sn bekleme + 1 sn
    expect(Math.max(...kmsa)).toBeCloseTo(36, 0);
  });

  it("ara durum ve darbe: alt-kare konumu iki kayıt arasında, darbe temas karesinde başlar", async () => {
    const b: Bake = await bake({ preset: "top-dusme", param: {}, fps: 30, sure: 2 });
    const k = b.temas[0].kare;
    expect(darbe(b, k - 1, "top")).toBe(0);
    expect(darbe(b, k, "top")).toBeGreaterThan(0);
    const a = durum(b, "top", 10).p[1], c = durum(b, "top", 11).p[1], m = araDurum(b, "top", 10.5).p[1];
    expect(m).toBeCloseTo((a + c) / 2, 5);
  });

  it("renk sıcaklığı: düşük kelvin sıcak, yüksek kelvin soğuk", () => {
    const rgb = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
    const [r1, , b1] = rgb(kelvin(3000)), [r2, , b2] = rgb(kelvin(9000));
    expect(r1).toBeGreaterThan(b1);
    expect(b2).toBeGreaterThan(b1);
  });
});

describe("fiziksel hazır efektler", () => {
  const O = { w: 1080, h: 1920, fps: 30 };
  const klip = (hazir: any[]): Klip => ({
    id: "a", iz: "V2", bas: 0, sure: 3, tur: "gorsel", kaynak: "G", giris: 0, hiz: 1, konusmaci: false, zoom: 1, punches: [],
    donus: { x: [], y: [], olcek: [], opaklik: [], anim: [] }, efekt: { parlaklik: 1, kontrast: 1, doygunluk: 1, bulanik: 0 }, hazir,
    ses: { gain_db: 0, fade_in: 0, fade_out: 0, duck: false },
  } as any);

  it("giris_dus: düşüş yerçekimiyle hızlanır, ilk temas sürenin %45'inde, sekmeler alçalır", () => {
    const c = klip([{ ad: "giris_dus", t: 0, sure: 1, mesafe: 0.5, sekme: 0.5 }]);
    const iz = genislet([c], O).get("a")!;
    const y = (t: number) => deger([], iz, "y", t, 0);
    expect(y(0)).toBeCloseTo(-0.5 * O.h, 0);
    expect(Math.abs(y(0.45))).toBeLessThan(1);
    // İlk yarıda alınan yol, ikinci yarıdakinin üçte biri (t² yasası): ivmeli düşüş.
    const ilk = y(0.225) - y(0), ikinci = y(0.45) - y(0.225);
    expect(ikinci / ilk).toBeCloseTo(3, 0);
    const tepeler = iz.flatMap((z) => z.y ?? []).filter((k) => k.v < 0).map((k) => -k.v);
    expect(tepeler.length).toBeGreaterThan(1); // başlangıç ve en az bir sekme tepesi
    for (let i = 1; i < tepeler.length; i++) expect(tepeler[i]).toBeLessThan(tepeler[i - 1]);
  });

  it("carp_zoom: önce geri çekilir, 12. karede hedef ölçektedir", () => {
    const c = klip([{ ad: "carp_zoom", t: 0, sure: 1.2, s: 1.6 }]);
    const iz = genislet([c], O).get("a")!;
    expect(deger([], iz, "olcek", 6 / 30, 1)).toBeLessThan(1);
    expect(deger([], iz, "olcek", 12 / 30, 1)).toBeCloseTo(1.6, 3);
  });
});
