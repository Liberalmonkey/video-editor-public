import { describe, expect, it } from "vitest";
import { duz, guvenliY, parca, sigdir, yerlesim } from "./metinOlcu";

describe("motion metin ölçüleri", () => {
  it("uzun Türkçe kelime genişliğe sığacak kadar küçülür, kısa metin boyutunu korur", () => {
    expect(sigdir("KISA", 150, 970)).toBe(150);
    const b = sigdir("ÇEKOSLOVAKYALILAŞTIRAMADIKLARIMIZDAN", 150, 970);
    expect(b).toBeLessThan(60);
    expect(b).toBeGreaterThan(20);
  });
  it("yıldızlı parça vurgulanır, düz metinde yıldız kalmaz", () => {
    expect(parca("bu *çok* iyi")).toEqual([{ t: "bu ", v: false }, { t: "çok", v: true }, { t: " iyi", v: false }]);
    expect(duz("*İŞ* bitti")).toBe("İŞ bitti");
  });
  it("dikeyde altyazı bandına ve üst %12'ye inmez", () => {
    expect(guvenliY(0.9, false)).toBe(0.68);
    expect(guvenliY(0.02, false)).toBe(0.14);
    expect(guvenliY(0.9, true)).toBe(0.74);
  });
  it("soldaki çapa sola yaslanır, genişlik kareden taşmaz", () => {
    const y = yerlesim("altbant", undefined, 1080, 1920);
    expect(y.hiza).toBe("sol");
    expect(y.x + y.genislik).toBeLessThanOrEqual(1080);
  });
});
