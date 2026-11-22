import { describe, expect, it } from "vitest";
import { VARSAYILAN } from "../../../tema";
import { temayaBoya } from "./Lottie";

describe("Lottie tema boyası", () => {
  it("doygun renkler vurgu ve ikincile, nötrler olduğu gibi; kaynak veri değişmez", () => {
    const veri: any = { layers: [{ shapes: [
      { ty: "fl", c: { a: 0, k: [1, 0, 0, 1] } },     // kırmızı → vurgu
      { ty: "st", c: { a: 0, k: [0.95, 0.1, 0.05, 1] } }, // aynı ton → vurgu
      { ty: "fl", c: { a: 0, k: [0, 0.2, 1, 1] } },   // mavi → ikincil
      { ty: "fl", c: { a: 0, k: [1, 1, 1, 1] } },     // beyaz → değişmez
    ] }] };
    const s = temayaBoya(veri, VARSAYILAN) as any;
    const hex = (k: number[]) => "#" + k.slice(0, 3).map((v) => Math.round(v * 255).toString(16).padStart(2, "0")).join("").toUpperCase();
    expect(hex(s.layers[0].shapes[0].c.k)).toBe(VARSAYILAN.renk.vurgu);
    expect(hex(s.layers[0].shapes[1].c.k)).toBe(VARSAYILAN.renk.vurgu);
    expect(hex(s.layers[0].shapes[2].c.k)).toBe(VARSAYILAN.renk.ikincil);
    expect(s.layers[0].shapes[3].c.k).toEqual([1, 1, 1, 1]);
    expect(veri.layers[0].shapes[0].c.k).toEqual([1, 0, 0, 1]);
  });
});
