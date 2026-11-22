import { describe, expect, it } from "vitest";
import { KAYIT } from "./kayit";
import { boyutBul, sureHesapla } from "./Tekil";

describe("MotionTekil yardımcıları", () => {
  describe("boyutBul", () => {
    it("9:16 için 1080x1920 döner", () => {
      expect(boyutBul("9:16")).toEqual({ w: 1080, h: 1920 });
    });

    it("16:9 için 1920x1080 döner", () => {
      expect(boyutBul("16:9")).toEqual({ w: 1920, h: 1080 });
    });

    it("1:1 ve varsayılan için 1080x1080 döner", () => {
      expect(boyutBul("1:1")).toEqual({ w: 1080, h: 1080 });
      expect(boyutBul(undefined)).toEqual({ w: 1080, h: 1080 });
      expect(boyutBul(null)).toEqual({ w: 1080, h: 1080 });
    });
  });

  describe("sureHesapla", () => {
    it("geçerli bileşende süre verilmezse meta.sure.varsayilan değerini döner", () => {
      const ornekAd = "ikon/ates";
      expect(KAYIT[ornekAd]).toBeDefined();
      expect(sureHesapla(ornekAd)).toBe(KAYIT[ornekAd].meta.sure.varsayilan);
      expect(sureHesapla(ornekAd, null)).toBe(KAYIT[ornekAd].meta.sure.varsayilan);
    });

    it("özel pozitif süre verilirse doğrudan onu döner", () => {
      expect(sureHesapla("ikon/ates", 3.5)).toBe(3.5);
      expect(sureHesapla("bilinmeyen/bilesen", 4.2)).toBe(4.2);
    });

    it("sıfır, negatif veya geçersiz sürede bileşenin varsayılanına düşer", () => {
      const ornekAd = "kart/cta-karti";
      expect(KAYIT[ornekAd]).toBeDefined();
      expect(sureHesapla(ornekAd, 0)).toBe(KAYIT[ornekAd].meta.sure.varsayilan);
      expect(sureHesapla(ornekAd, -2)).toBe(KAYIT[ornekAd].meta.sure.varsayilan);
      expect(sureHesapla(ornekAd, Number.NaN)).toBe(KAYIT[ornekAd].meta.sure.varsayilan);
    });

    it("bilinmeyen bileşen adında pozitif yedek süre döner", () => {
      const yedek = sureHesapla("olmayan/bilesen");
      expect(yedek).toBeGreaterThan(0);
      expect(sureHesapla("olmayan/bilesen", null)).toBe(yedek);
    });
  });
});
