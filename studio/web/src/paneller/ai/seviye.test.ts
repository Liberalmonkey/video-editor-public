import { expect, test } from "vitest";
import type { MotorDurum } from "../../depo";
import { motorSebebi } from "./MotorModel";
import { grup, HIZLI_OZET, SEVIYE, SEVIYELER, seviyeOzet, slotAyari, slotlar, slotSirasi, type EkipAyar } from "./seviye";

test("seviye tablosu: low 2+1, medium 4+2, high 6+3, xhigh 8+4, max 10+5; her seviyede bir orkestratör", () => {
  expect(SEVIYELER.map((s) => [SEVIYE[s].editor, SEVIYE[s].kk])).toEqual([[2, 1], [4, 2], [6, 3], [8, 4], [10, 5]]);
  expect(slotlar("low")).toEqual(["O", "E1", "E2", "K1"]);
  expect(slotlar("max")).toHaveLength(16);
  expect(seviyeOzet("medium")).toBe("4 editör · 2 kalite kontrol · orkestratör");
});

test("slot sırası sayısaldır ve slot ayarı ezmeyi gruba tercih eder", () => {
  expect(["K2", "E10", "O", "E2", "K1"].sort(slotSirasi)).toEqual(["O", "E2", "E10", "K1", "K2"]);
  expect([grup("O"), grup("E7"), grup("K5")]).toEqual(["orkestrator", "editor", "kk"]);
  const a: EkipAyar = { ad: "x", ekip_seviye: "high", motion: "yogun", ezme: { E3: { motor: "codex" } },
    gruplar: { orkestrator: { motor: "claude" }, editor: { motor: "claude" }, kk: { motor: "antigravity" } } };
  expect(slotAyari(a, "E3").motor).toBe("codex");
  expect(slotAyari(a, "E4").motor).toBe("claude");
  expect(slotAyari(a, "K1").motor).toBe("antigravity");
});

test("kurulu olmayan ya da uyarılı motor sebebiyle görünür, hazır motor boş sebep verir", () => {
  const hazir: MotorDurum = { ad: "Claude Code", kurulu: true, surum: "2", modeller: [], seviyeler: ["low", "high"] };
  expect(motorSebebi(hazir)).toBe("");
  expect(motorSebebi({ ...hazir, kurulu: false, kurulum: "npm i" })).toContain("kurulu değil");
  expect(motorSebebi({ ...hazir, hata: "Model listesi boş; giriş yapıldı mı?" })).toContain("giriş");
  expect(motorSebebi(undefined)).toBe("taranıyor");
});

test("hızlı ön ayar low ekibini orkestratörsüz özetler (ADR 0054)", () => {
  expect(HIZLI_OZET).toBe("2 editör · 1 kalite kontrol · orkestratörsüz");
  const a: EkipAyar = { ad: "x", ekip_seviye: "max", motion: "yogun", ezme: {}, hizli: true,
    gruplar: { orkestrator: { motor: "claude" }, editor: { motor: "claude" }, kk: { motor: "antigravity" } } };
  expect(slotlar(a.hizli ? "low" : a.ekip_seviye).filter((s) => !(a.hizli && s === "O"))).toEqual(["E1", "E2", "K1"]);
});
