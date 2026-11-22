import { expect, test } from "vitest";
import { suz, type MotionKayit } from "./MotionPaneli";

const k = (id: string, kind: string, ek: Partial<MotionKayit> = {}): MotionKayit => ({ id, title: id, kind, file: `library/motion/custom/${id}/${id}.webm`, url: "", ...ek });
const hepsi = [k("ok-ciz", "overlay", { tags: ["ok"] }), k("gecis-iris-dikey", "transition"), k("alinti-karti", "lower-third", { param: { metin: { vars: "x" } }, ne_zaman: "Alıntı söylenince" })];

test("tür süzgeci şablonu ayrı tutar", () => {
  expect(suz(hepsi, "", "").length).toBe(3);
  expect(suz(hepsi, "sablon", "").map((e) => e.id)).toEqual(["alinti-karti"]);
  expect(suz(hepsi, "lower-third", "")).toEqual([]);
  expect(suz(hepsi, "overlay", "").map((e) => e.id)).toEqual(["ok-ciz"]);
});

test("arama etiket ve ne_zaman alanına bakar, Türkçe küçük harfle", () => {
  expect(suz(hepsi, "", "OK").map((e) => e.id)).toEqual(["ok-ciz"]);
  expect(suz(hepsi, "", "ALINTI söylenince").map((e) => e.id)).toEqual(["alinti-karti"]);
});
