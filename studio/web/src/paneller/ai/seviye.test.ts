import { expect, test } from "vitest";
import type { MotorDurum } from "../../depo";
import { motorSebebi } from "./MotorModel";
import { EN_COK, editorSlotlari, gerekenMotorlar, grup, kkSlotlari, SEVIYELER, slotAyari, slotSirasi, suruOzet, tavan, type EkipAyar } from "./seviye";

const ayar = (ek: Partial<EkipAyar> = {}): EkipAyar => ({ ad: "x", ekip_seviye: "medium", motion: "yogun", ezme: {},
  gruplar: { orkestrator: { motor: "claude" }, editor: { motor: "claude" }, kk: { motor: "antigravity" } }, ...ek });

test("swarm tavanı: seviye kısaltması 3/6/9/12/15, en_cok kazanır (ADR 0059)", () => {
  expect(SEVIYELER.map((s) => EN_COK[s])).toEqual([3, 6, 9, 12, 15]);
  expect(tavan(ayar())).toBe(6);
  expect(tavan(ayar({ en_cok: 4 }))).toBe(4);
  expect(editorSlotlari(15)).toHaveLength(10);
  expect(kkSlotlari(3)).toEqual(["K1"]);
  expect(suruOzet(ayar({ en_cok: 9 }))).toContain("en çok 9 ajan");
});

test("slot sırası sayısaldır ve slot ayarı ezmeyi gruba tercih eder", () => {
  expect(["K2", "E10", "O", "E2", "K1"].sort(slotSirasi)).toEqual(["O", "E2", "E10", "K1", "K2"]);
  expect([grup("O"), grup("E7"), grup("K5")]).toEqual(["orkestrator", "editor", "kk"]);
  const a = ayar({ ezme: { E3: { motor: "codex" } } });
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

test("gereken motorlar: hızlıda orkestratör yok, ezme eklenir (ADR 0054, 0059)", () => {
  const a = ayar({ gruplar: { orkestrator: { motor: "codex" }, editor: { motor: "claude" }, kk: { motor: "antigravity" } }, ezme: { E2: { motor: "opencode" } } });
  expect(gerekenMotorlar(a).sort()).toEqual(["antigravity", "claude", "codex", "opencode"]);
  expect(gerekenMotorlar({ ...a, hizli: true, ezme: { O: { motor: "codex" } } }).sort()).toEqual(["antigravity", "claude"]);
  const yedekli = ayar({ gruplar: { orkestrator: { motor: "claude" }, editor: { motor: "claude", yedek_motor: "antigravity" }, kk: { motor: "claude" } } });
  expect(gerekenMotorlar(yedekli).sort()).toEqual(["antigravity", "claude"]);
  expect(suruOzet({ ...a, hizli: true })).toContain("orkestratörsüz");
});
