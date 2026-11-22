import { describe, expect, it } from "vitest";
import { suz, type Kural } from "./KurallarPaneli";

const k = (id: string, ek: Partial<Kural> = {}): Kural => ({
  id, metin: `YAP: ${id} kuralı`, neden: "", kapsam: "global", hedef_rol: "hepsi", kategori: "genel", onem: "P1", kaynak: "kullanici",
  kanit: [], durum: "aktif", tekrar: 1, olusturma: "2026-11-20", guncelleme: "2026-11-20", ...ek,
});
const F = { ara: "", durum: "hepsi", rol: "hepsi", kategori: "hepsi", onem: "hepsi" };

describe("kural süzgeci", () => {
  it("varsayılan görünüm silinenleri gizler, Silinen süzgeci yalnız onları gösterir", () => {
    const l = [k("K1"), k("K2", { durum: "silinen" }), k("K3", { durum: "pasif" })];
    expect(suz(l, F).map((x) => x.id)).toEqual(["K1", "K3"]);
    expect(suz(l, { ...F, durum: "silinen" }).map((x) => x.id)).toEqual(["K2"]);
  });
  it("önem önce, sonra tekrar sırası; Türkçe büyük-küçük harfle arama", () => {
    const l = [k("K1", { onem: "P2" }), k("K2", { onem: "P0" }), k("K3", { tekrar: 4 }), k("K4", { metin: "YAPMA: İkonu yüze koyma" })];
    expect(suz(l, F).map((x) => x.id)).toEqual(["K2", "K3", "K4", "K1"]);
    expect(suz(l, { ...F, ara: "ikonu" }).map((x) => x.id)).toEqual(["K4"]);
  });
  it("rol ve kategori süzgeci", () => {
    const l = [k("K1", { hedef_rol: "E2", kategori: "grafik" }), k("K2", { hedef_rol: "E3", kategori: "ses" })];
    expect(suz(l, { ...F, rol: "E2" }).map((x) => x.id)).toEqual(["K1"]);
    expect(suz(l, { ...F, kategori: "ses" }).map((x) => x.id)).toEqual(["K2"]);
  });
});
