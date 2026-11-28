import { describe, expect, it } from "vitest";
import { cakismaMetni, sekmeKayitlari } from "./KutuphanePaneli";

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

describe("409 çakışma metni (bulgu 13)", () => {
  it("geçerli JSON, eksik alan ve düz metinde çökmez", () => {
    expect(cakismaMetni(JSON.stringify({ yuva: ["gecis"], projeler: ["p1", "p2"] }))).toBe("Kit yuvası: gecis\nKullanan projeler: p1, p2");
    expect(cakismaMetni(JSON.stringify({ yuva: ["gecis"] }))).toBe("Kit yuvası: gecis");
    expect(cakismaMetni("Düz metin 409 yanıtı")).toBe("Düz metin 409 yanıtı");
  });
});
