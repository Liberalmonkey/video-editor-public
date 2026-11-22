import { describe, expect, it } from "vitest";
import type { KurguProps } from "../../../remotion/tipler";
import { db, ilerlet, kanalSeviye, konum, yeniCubuk } from "./metre";
import * as K from "./komutlar";

const tepe = { hz: 50, tepe: Array(5000).fill(255) };
const kurgu = (ek: Partial<KurguProps> = {}): KurguProps => {
  const k: KurguProps = {
    sekans: { w: 1080, h: 1920, fps: 30 }, kaynaklar: { A: { yol: "inputs:a.mp4", sure: 100, ses: true } }, kelimeler: {},
    izler: [{ id: "V1", tur: "video", ad: "", kilit: false, sessiz: false, gizli: false, gain_db: 0 }, { id: "A1", tur: "ses", ad: "", kilit: false, sessiz: false, gizli: false, gain_db: 0 }],
    klipler: [], altyazi: { acik: false, iz: "V1" }, ...ek,
  };
  k.klipler = [{ ...K.klipYap(k, { tur: "video", iz: "V1", bas: 1, sure: 10, kaynak: "A" }), id: "v" }];
  return k;
};
const oku = (k: KurguProps, t: number, iz = "V1", solo: string[] = []) => kanalSeviye(k, iz, t, solo, () => tepe);

describe("kanal seviyesi", () => {
  it("klip dışında sıfır, içinde tepe", () => {
    const k = kurgu();
    expect(oku(k, 0.5)).toBe(0);
    expect(oku(k, 5)).toBeCloseTo(1);
    expect(oku(k, 11)).toBe(0);
  });
  it("klip ve iz kazancı toplanır: +6 dB iki kat", () => {
    const k = kurgu();
    k.izler[0].gain_db = 3; k.klipler[0].ses.gain_db = 3;
    expect(db(oku(k, 5))).toBeCloseTo(6, 1);
  });
  it("sustur, solo ve ayrık ses sıfırlar", () => {
    const k = kurgu();
    expect(oku({ ...k, izler: k.izler.map((i) => ({ ...i, sessiz: true })) }, 5)).toBe(0);
    expect(oku(k, 5, "V1", ["A1"])).toBe(0);
    expect(oku({ ...k, klipler: [{ ...k.klipler[0], ses_kapali: true }] }, 5)).toBe(0);
  });
  it("fade yarıda yarım genlik", () => {
    const k = kurgu();
    k.klipler[0].ses.fade_in = 2;
    expect(oku(k, 2)).toBeCloseTo(0.5, 2);
  });
  it("tepe verisi gelmediyse sıfır, hata yok", () => {
    expect(kanalSeviye(kurgu(), "V1", 5, [], () => null)).toBe(0);
  });
});

describe("çubuk", () => {
  it("anında yükselir, 20 dB/sn iner", () => {
    let c = ilerlet(yeniCubuk(), -10, 0.016);
    expect(c.db).toBe(-10);
    c = ilerlet(c, -Infinity, 0.5);
    expect(c.db).toBeCloseTo(-20);
  });
  it("tepe 1,5 sn tutulur, sonra iner", () => {
    let c = ilerlet(yeniCubuk(), -6, 0.016);
    for (let i = 0; i < 14; i++) c = ilerlet(c, -Infinity, 0.1);
    expect(c.tepe).toBe(-6);
    for (let i = 0; i < 5; i++) c = ilerlet(c, -Infinity, 0.1);
    expect(c.tepe).toBeLessThan(-6);
  });
  it("kırpma tıklanana kadar kalır, -60 altı susar", () => {
    let c = ilerlet(yeniCubuk(), 1, 0.016);
    expect(c.kirpti).toBe(true);
    for (let i = 0; i < 80; i++) c = ilerlet(c, -Infinity, 0.1);
    expect(c.kirpti).toBe(true);
    expect(c.db).toBe(-Infinity);
  });
  it("ölçek uçları", () => {
    expect([konum(-60), konum(6), konum(-100), konum(50)]).toEqual([0, 1, 0, 1]);
  });
});
