import { describe, expect, it } from "vitest";
import type { Bolgeler, MotionMeta } from "./tipler";
import { altyaziBandi, boyutHesapla, guvenliAlan, icinde, kesisim, platformBolgeleri, temizMi, yerles, yuzPayi } from "./yerlesim";

const W = 1080, H = 1920;
const meta = (ek: Partial<MotionMeta> = {}): MotionMeta => ({
  ad: "ikon/test", tur: "ikon", etiketler: [], ne_zaman: "", sure: { min: 1, varsayilan: 1.3, max: 1.6 }, giris_sn: 0.35, cikis_sn: 0.2,
  hero: false, en_boy: ["9:16"], yer: ["ust", "sag", "sol", "alt"], boyut: { w: 0.2, h: 0.2 }, en_kucuk_px: 180, ...ek,
});
const bolge = (ek: Partial<Bolgeler> = {}): Bolgeler => ({
  guvenli: guvenliAlan(W, H), altyazi: altyaziBandi(W, 1402, 84), yuzler: [], platform: platformBolgeleri(W, H), ...ek,
});

describe("yerleşim", () => {
  it("en küçük boyutun altına inmez: 1080 dikeyde ikon en az 180 px", () => {
    expect(boyutHesapla(meta({ boyut: { w: 0.05, h: 0.05 } }), W, H).w).toBeGreaterThanOrEqual(180);
    expect(boyutHesapla(meta(), 540, 960).w).toBeGreaterThanOrEqual(90); // ölçek kısa kenarla
  });

  it("yüz kutusuna, altyazı bandına ve platform arayüzüne değmez", () => {
    // Konuşmacı yüzü üst-ortada: instagram/1'deki "alındaki ?" durumu.
    const yuz = yuzPayi({ x: 330, y: 380, w: 420, h: 520 });
    const b = bolge({ yuzler: [yuz] });
    const s = yerles(meta(), W, H, b);
    expect(temizMi(s, b)).toBe(true);
    expect(kesisim(s.kutu, { x: 330, y: 380, w: 420, h: 520 })).toBe(0); // göz ve ağız (paysız yüz)
    expect(kesisim(s.kutu, b.altyazi!)).toBe(0);
    for (const p of b.platform) expect(kesisim(s.kutu, p)).toBe(0);
    expect(icinde(s.kutu, b.guvenli)).toBe(true);
  });

  it("tercih edilen yer çakışmasızsa o seçilir; çakışıyorsa sıradaki", () => {
    expect(yerles(meta(), W, H, bolge(), "sol").yer).toBe("sol");
    const ustYuz = { x: 0, y: 150, w: W, h: 600 };
    expect(yerles(meta(), W, H, bolge({ yuzler: [ustYuz] }), "ust").yer).not.toBe("ust");
  });

  it("deterministik: aynı girdi aynı kutu", () => {
    const b = bolge({ yuzler: [{ x: 300, y: 400, w: 500, h: 600 }] });
    expect(yerles(meta(), W, H, b)).toEqual(yerles(meta(), W, H, b));
  });

  it("hedefli call-out hedefin yanına düşer, üstüne değil", () => {
    const hedef = { x: 540, y: 900 };
    const s = yerles(meta({ yer: ["hedef"] }), W, H, bolge(), "hedef", hedef);
    const ic = hedef.x >= s.kutu.x && hedef.x <= s.kutu.x + s.kutu.w && hedef.y >= s.kutu.y && hedef.y <= s.kutu.y + s.kutu.h;
    expect(ic).toBe(false);
  });

  it("altyazı bandı iki satır ve nefes payı kadar geniş (3.1 boy)", () => {
    const b = altyaziBandi(W, 1402, 84);
    expect(b.h).toBe(Math.round(84 * 3.1));
    expect(b.y + b.h / 2).toBeCloseTo(1402, -1);
  });

  it("üst yerleşim platform üst barının altında kalır", () => {
    const s = yerles(meta({ yer: ["ust"] }), W, H, bolge(), "ust");
    expect(s.yer).toBe("ust");
    const bar = platformBolgeleri(W, H)[0];
    expect(s.kutu.y).toBeGreaterThanOrEqual(bar.y + bar.h);
    expect(s.kutu.y + s.kutu.h).toBeLessThan(H * 0.45);
  });

  it("tam yer kareyi kaplar", () => {
    const s = yerles(meta({ yer: ["tam"] }), W, H, bolge(), "tam");
    expect(s.kutu).toEqual({ x: 0, y: 0, w: W, h: H });
  });
});
