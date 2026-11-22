import { expect, test } from "vitest";
import type { MotorDurum } from "../depo";
import { motorSebebi, SLOT_ADI, SLOTLAR } from "./EkipPaneli";

test("altı slot: üç editör, üç kalite kontrol", () => {
  expect(SLOTLAR).toEqual(["E1", "E2", "E3", "K1", "K2", "K3"]);
  expect(Object.keys(SLOT_ADI)).toHaveLength(6);
});

test("kurulu olmayan ya da uyarılı motor sebebiyle görünür, hazır motor boş sebep verir", () => {
  const hazir: MotorDurum = { ad: "Claude Code", kurulu: true, surum: "2", modeller: [], seviyeler: ["low", "high"] };
  expect(motorSebebi(hazir)).toBe("");
  expect(motorSebebi({ ...hazir, kurulu: false, kurulum: "npm i" })).toContain("kurulu değil");
  expect(motorSebebi({ ...hazir, hata: "Model listesi boş; giriş yapıldı mı?" })).toContain("giriş");
  expect(motorSebebi(undefined)).toBe("taranıyor");
});
