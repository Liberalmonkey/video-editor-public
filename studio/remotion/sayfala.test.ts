import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { buildPages, buildTokens } from "../../openmontage/remotion-composer/src/SplitReel";

// tests/test_kurgu.py aynı dosyayı hizli.sayfala ile sınar: ekran ve SRT aynı sayfalanır.
const ornekler = JSON.parse(readFileSync(resolve(__dirname, "../../tests/sayfala_ornek.json"), "utf-8"));

describe("sayfalama TS = Python", () => {
  for (const o of ornekler) {
    it(`${o.en_kelime} kelime, ${o.en_karakter} karakter`, () => {
      const s = buildPages(buildTokens(o.kelimeler), o.en_kelime, o.en_karakter);
      expect(s.map((p: { text: string }[]) => p.map((t) => t.text))).toEqual(o.sayfalar);
    });
  }
});
