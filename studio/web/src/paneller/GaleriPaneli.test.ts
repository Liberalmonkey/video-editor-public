import { describe, expect, it, test } from "vitest";
import { galeriSuz, type GaleriOge } from "./GaleriPaneli";

const O: GaleriOge[] = [
  { tur: "fizik", id: "domino", title: "Domino taşları sırayla devrilir", ne_zaman: "Zincirleme etki" },
  { tur: "isik", id: "gun-batimi", title: "Gün batımı", ne_zaman: "Duygusal, kapanış" },
  { tur: "tema", id: "altin-fintech", title: "altin-fintech", ne_zaman: "Finans, yatırım" },
];

describe("galeri süzgeci", () => {
  it("tür ve Türkçe büyük-küçük harf duyarsız arama", () => {
    expect(galeriSuz(O, "fizik", "").map((o) => o.id)).toEqual(["domino"]);
    expect(galeriSuz(O, "", "GÜN").map((o) => o.id)).toEqual(["gun-batimi"]);
    expect(galeriSuz(O, "", "finans yatırım").map((o) => o.id)).toEqual(["altin-fintech"]);
    expect(galeriSuz(O, "tema", "domino")).toEqual([]);
  });
});

test("gizlenen öğe ve eski motion yalnız 'Gizlenenleri göster' açıkken (ADR 0061)", () => {
  const o = [{ tur: "fizik", id: "domino", title: "Domino", gizli: true }, { tur: "motion", id: "ok", title: "Ok", eski: true }, { tur: "tema", id: "t", title: "T" }];
  expect(galeriSuz(o, "", "").map((x) => x.id)).toEqual(["t"]);
  expect(galeriSuz(o, "", "", true).map((x) => x.id)).toEqual(["domino", "ok", "t"]);
});
