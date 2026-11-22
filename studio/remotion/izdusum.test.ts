import { describe, expect, it } from "vitest";
import { izdusum, kfDeger } from "./izdusum";

// tests/test_kurgu.py ile aynı örnek: iki taraf aynı sonucu vermeli.
const kelimeler = { V01: [{ w: "a", s: 1, e: 2 }, { w: "b", s: 5, e: 7 }, { w: "c", s: 11, e: 12 }] };
const klip = (hiz: number) => ({ id: "c1", iz: "V1", tur: "video", kaynak: "V01", bas: 10, sure: 4, giris: 4, hiz }) as any;
const altyazi = { acik: true, iz: "V1" };

describe("izdusum", () => {
  it("kesimi izler", () => {
    expect(izdusum({ klipler: [klip(1)], kelimeler, altyazi })).toEqual([{ w: "b", s: 11, e: 13 }]);
  });
  it("hızı izler", () => {
    expect(izdusum({ klipler: [klip(2)], kelimeler, altyazi })).toEqual([{ w: "b", s: 10.5, e: 11.5 }, { w: "c", s: 13.5, e: 14 }]);
  });
  it("kapalıysa boş", () => {
    expect(izdusum({ klipler: [klip(1)], kelimeler, altyazi: { acik: false, iz: "V1" } })).toEqual([]);
  });
});

describe("kfDeger", () => {
  const kf = [{ t: 1, v: 0, ease: "dogrusal" as const }, { t: 3, v: 10, ease: "tut" as const }, { t: 5, v: 20, ease: "dogrusal" as const }];
  it("uçlarda sabit, arada doğrusal, tut eğrisi basamak", () => {
    expect(kfDeger([], 1, 7)).toBe(7);
    expect(kfDeger(kf, 0, 7)).toBe(0);
    expect(kfDeger(kf, 2, 7)).toBe(5);
    expect(kfDeger(kf, 4, 7)).toBe(10);
    expect(kfDeger(kf, 9, 7)).toBe(20);
  });
});
