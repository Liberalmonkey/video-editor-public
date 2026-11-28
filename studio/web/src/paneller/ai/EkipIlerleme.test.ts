import { describe, expect, it } from "vitest";
import { gecerliEkipDurum } from "./EkipIlerleme";

describe("EkipIlerleme durum doğrulaması (bulgu 13)", () => {
  it("slotlar veya acik eksikse geçersiz sayar, tam durum geçerlidir", () => {
    expect(gecerliEkipDurum(null)).toBe(false);
    expect(gecerliEkipDurum({ yok: true, kapilar: [], slotlar: {}, acik: { P0: 0, P1: 0, P2: 0 } })).toBe(false);
    expect(gecerliEkipDurum({ kapilar: [], acik: { P0: 0, P1: 0, P2: 0 } })).toBe(false);
    expect(gecerliEkipDurum({ kapilar: [], slotlar: [] , acik: { P0: 0, P1: 0, P2: 0 } })).toBe(false);
    expect(gecerliEkipDurum({ kapilar: [], slotlar: {} })).toBe(false);
    expect(gecerliEkipDurum({ kapilar: [], slotlar: {}, acik: { P0: 0, P1: 0, P2: 0 } })).toBe(true);
  });
});
