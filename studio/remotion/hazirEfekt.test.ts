import { describe, expect, it } from "vitest";
import { bol, hazirPisir } from "../web/src/zaman/komutlar";
import { deger, genislet, pisir } from "./hazirEfekt";
import type { Hazir, Klip, KurguProps } from "./tipler";

const O = { w: 1080, h: 1920, fps: 30 };
const klip = (id: string, bas: number, sure: number, hazir: Hazir[], donus: Partial<Klip["donus"]> = {}): Klip => ({
  id, iz: "V1", bas, sure, tur: "gorsel", kaynak: "G", giris: 0, hiz: 1, konusmaci: false, zoom: 1, punches: [],
  donus: { x: [], y: [], olcek: [], opaklik: [], anim: [], ...donus },
  efekt: { parlaklik: 1, kontrast: 1, doygunluk: 1, bulanik: 0 }, hazir,
  ses: { gain_db: 0, fade_in: 0, fade_out: 0, duck: false },
});
const ornek = (n: number) => Array.from({ length: n + 1 }, (_, i) => i / n);

describe("hazır efekt açılımı", () => {
  it("odak_zoom: seçilen nokta yerinde kalır, el ölçeği de hesaba katılır", () => {
    for (const el of [1, 1.2]) {
      const c = klip("a", 0, 3, [{ ad: "odak_zoom", x: 0.2, y: 0.3, sure: 0.5 }], { olcek: [{ t: 0, v: el, ease: "dogrusal" }] });
      const iz = genislet([c], O).get("a");
      const P = [0.2 * O.w, 0.3 * O.h], C = [0.5 * O.w, 0.5 * O.h];
      for (const t of ornek(20).map((u) => u * 3)) {
        const s = deger(c.donus.olcek, iz, "olcek", t, 1), x = deger(c.donus.x, iz, "x", t, 0), y = deger(c.donus.y, iz, "y", t, 0);
        // translate + scale (çapa ortada): nokta yalnız el ölçeğiyle nereye düşüyorsa orada kalır.
        expect(C[0] + s * (P[0] - C[0]) + x).toBeCloseTo(C[0] + el * (P[0] - C[0]), 1);
        expect(C[1] + s * (P[1] - C[1]) + y).toBeCloseTo(C[1] + el * (P[1] - C[1]), 1);
      }
      expect(deger(c.donus.olcek, iz, "olcek", 1, 1)).toBeCloseTo(el * 1.4, 4);
    }
  });

  it("ken_burns: kayma hiçbir anda büyümenin açtığı payı aşmaz", () => {
    for (const yon of ["sol", "sag", "yukari", "asagi"]) {
      const c = klip("k", 0, 4, [{ ad: "ken_burns", yon }]);
      const iz = genislet([c], O).get("k");
      for (const t of ornek(80).map((u) => u * 4)) {
        const s = deger([], iz, "olcek", t, 1);
        expect(s).toBeGreaterThan(1);
        expect(Math.abs(deger([], iz, "x", t, 0))).toBeLessThanOrEqual(((s - 1) / 2) * O.w + 1e-6);
        expect(Math.abs(deger([], iz, "y", t, 0))).toBeLessThanOrEqual(((s - 1) / 2) * O.h + 1e-6);
      }
    }
  });

  it("değişim sayacı: art arda kliplerde punch başka ölçek alır, yazılan değer korunur", () => {
    const l = [klip("a", 0, 2, [{ ad: "punch" }]), klip("b", 2, 2, [{ ad: "punch" }]), klip("c", 4, 2, [{ ad: "punch", s: 1.11 }])];
    const m = genislet(l, O);
    const tepe = (id: string) => deger([], m.get(id), "olcek", 0.5, 1);
    expect(tepe("a")).toBeCloseTo(1.12, 4);
    expect(tepe("b")).toBeCloseTo(1.16, 4);
    expect(tepe("c")).toBeCloseTo(1.11, 4);
  });

  it("pisir: el keyframe'i bileşimi aynen taşır, anim açılır, kayıt silinir", () => {
    const c = klip("p", 0, 3, [{ ad: "zoom_in", sure: 1, s: 1.2 }, { ad: "bulanik_gir" }], { olcek: [{ t: 0, v: 1.1, ease: "dogrusal" }] });
    const iz = genislet([c], O).get("p")!;
    const once = ornek(30).map((u) => u * 3).map((t) => [deger(c.donus.olcek, iz, "olcek", t, 1), deger(c.donus.opaklik, iz, "opaklik", t, 1), deger([], iz, "bulanik", t, 0)]);
    const k = { sekans: { w: O.w, h: O.h, fps: O.fps }, klipler: [c] } as unknown as KurguProps;
    hazirPisir(k, "p", 0);
    expect(c.hazir).toEqual([{ ad: "bulanik_gir" }]);
    expect(c.donus.anim).toContain("olcek");
    hazirPisir(k, "p", 0);
    expect(c.hazir).toEqual([]);
    ornek(30).map((u) => u * 3).forEach((t, i) => {
      expect(deger(c.donus.olcek, [], "olcek", t, 1)).toBeCloseTo(once[i][0], 4);
      expect(deger(c.donus.opaklik, [], "opaklik", t, 1)).toBeCloseTo(once[i][1], 4);
      expect(deger(c.efekt.bulanik_kf, [], "bulanik", t, 0)).toBeCloseTo(once[i][2], 4);
    });
  });

  it("pisir: tek iz verilince yalnız o özelliğe yazar", () => {
    const c = klip("q", 0, 2, []);
    pisir(c, { x: [{ t: 0, v: 0, ease: "expo" }, { t: 1, v: 50, ease: "dogrusal" }] });
    expect(c.donus.x).toEqual([{ t: 0, v: 0, ease: "expo" }, { t: 1, v: 50, ease: "dogrusal" }]);
    expect(c.donus.olcek).toEqual([]);
    expect(c.donus.anim).toEqual(["x"]);
  });

  it("bölünce efekt başladığı parçada kalır, çıkış efekti sağa geçer", () => {
    const c = klip("b", 0, 4, [{ ad: "punch", t: 1 }, { ad: "odak_zoom", t: 3 }, { ad: "cikis_kay" }]);
    const k = { sekans: { w: O.w, h: O.h, fps: O.fps }, izler: [{ id: "V1", tur: "video" }], klipler: [c] } as unknown as KurguProps;
    const sag = bol(k, c, 2)!;
    expect(c.hazir).toEqual([{ ad: "punch", t: 1 }]);
    expect(sag.hazir).toEqual([{ ad: "odak_zoom", t: 1 }, { ad: "cikis_kay" }]);
  });
});
