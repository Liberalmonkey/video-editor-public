import { describe, expect, it } from "vitest";
import { sekmeKayitlari } from "./KutuphanePaneli";

// /api/kutuphane yalnız sfx, muzik, motion, pano, font, kit, temalar döner. Galeri ve grafik kendi verisini getirir.
const veri = { sfx: [{ id: "a" }], muzik: [], motion: [{ id: "m" }], pano: [], font: [], kit: {}, temalar: [] };

describe("kütüphane sekme kayıtları", () => {
  it("listesi olmayan sekme sayı göstermez, panel düşmez", () => {
    expect(sekmeKayitlari(veri, "galeri")).toBeNull();
    expect(sekmeKayitlari(veri, "grafik")).toBeNull();
    expect(sekmeKayitlari(veri, "kit")).toBeNull();
  });
  it("listeli sekme kayıtları; eksik anahtar boş liste", () => {
    expect(sekmeKayitlari(veri, "sfx")).toHaveLength(1);
    expect(sekmeKayitlari({ sfx: [] }, "motion")).toEqual([]);
    expect(sekmeKayitlari(null, "sfx")).toEqual([]);
  });
});
