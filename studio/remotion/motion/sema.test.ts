import { describe, expect, it } from "vitest";
import { TUMU } from "./kayit";
import { guncelMi } from "./sema-yaz";

describe("native motion kaydı", () => {
  it("library/motion/native/sema.json güncel (değilse: cd studio && npm run sema)", () => {
    expect(guncelMi()).toBe(true);
  });

  it("her bileşen sözleşmeye uyar: benzersiz ad, süre sınırı, çıkış girişten kısa, en küçük boyut", () => {
    const adlar = new Set<string>();
    for (const t of TUMU) {
      const m = t.meta;
      expect(adlar.has(m.ad), m.ad).toBe(false);
      adlar.add(m.ad);
      expect(m.ad.split("/").length, m.ad).toBe(2);
      expect(m.sure.min <= m.sure.varsayilan && m.sure.varsayilan <= m.sure.max, m.ad).toBe(true);
      expect(m.cikis_sn < m.giris_sn, `${m.ad}: çıkış girişten hızlı olmalı`).toBe(true);
      if (m.tur !== "gecis" && m.tur !== "zemin") expect(m.giris_sn >= 0.2 && m.giris_sn <= 0.5, m.ad).toBe(true);
      if (m.tur === "ikon") expect(m.en_kucuk_px >= 160, `${m.ad}: telefonda okunur ikon en az 160 px`).toBe(true);
      expect(m.yer.length > 0 && m.en_boy.length > 0, m.ad).toBe(true);
      // Varsayılan parametre şemadan geçmeli: param verilmeyen klip de çizilir.
      expect(() => t.sema.parse({}), `${m.ad}: boş param`).not.toThrow();
      // z.strictObject: bilinmeyen alan (yanlış yazılmış param) sessizce düşmesin.
      expect(() => t.sema.parse({ __bilinmeyen__: 1 }), `${m.ad}: z.strictObject kullan`).toThrow();
    }
  });
});
