import { expect, test } from "vitest";
import { varsayilanModel, type MotorDurum } from "../depo";
import { istektekiStil, modelAdi, modelGruplari } from "./AjanPaneli";

const oc: MotorDurum = {
  ad: "OpenCode", kurulu: true, surum: "v2.3.0", varsayilan: "opencode/big-pickle", modeller: [
    { id: "opencode/big-pickle", ad: "big-pickle", grup: "OpenCode Zen", ucretsiz: true },
    { id: "openai/gpt-5", ad: "gpt-5", grup: "OpenAI" },
    { id: "openrouter/anthropic/claude-opus", ad: "anthropic/claude-opus", grup: "OpenRouter" },
    { id: "openrouter/x/y:free", ad: "x/y:free", grup: "OpenRouter", ucretsiz: true },
  ],
};

test("model grupları sırayı korur; arama kimlik, ad, grup ve 'ücretsiz' etiketinde geçer", () => {
  expect(modelGruplari(oc.modeller, "").map((g) => [g.grup, g.liste.length])).toEqual([["OpenCode Zen", 1], ["OpenAI", 1], ["OpenRouter", 2]]);
  expect(modelGruplari(oc.modeller, "free").flatMap((g) => g.liste.map((m) => m.id))).toEqual(["opencode/big-pickle", "openrouter/x/y:free"]);
  expect(modelGruplari(oc.modeller, "router claude").flatMap((g) => g.liste.map((m) => m.id))).toEqual(["openrouter/anthropic/claude-opus"]);
  // seçili model süzülse de görünür kalır, yoksa select boş değer gösterirdi
  expect(modelGruplari(oc.modeller, "zzz", "openai/gpt-5").flatMap((g) => g.liste.map((m) => m.id))).toEqual(["openai/gpt-5"]);
});

test("varsayılan model ve okunur ad", () => {
  expect(varsayilanModel(oc)).toBe("opencode/big-pickle");
  expect(varsayilanModel({ ...oc, varsayilan: "yok/model" })).toBe("opencode/big-pickle");
  expect(varsayilanModel({ ...oc, varsayilan: null, modeller: oc.modeller.slice(1) })).toBe("openai/gpt-5");
  expect(modelAdi(oc, "openai/gpt-5")).toBe("gpt-5");
  expect(modelAdi(oc, "openrouter/listede/olmayan")).toBe("olmayan");
});

test("istekte adı geçen stil bulunur; tire ve boşluk aynı sayılır, en uzun ad kazanır", () => {
  const stiller = ["ai-reels", "reels", "ornek-marka"];
  expect(istektekiStil("ai-reels stiliyle hızlı bir animasyon yap", stiller)).toBe("ai-reels");
  expect(istektekiStil("AI Reels gibi olsun", stiller)).toBe("ai-reels");
  expect(istektekiStil("reels, sıkı kurgu", stiller)).toBe("reels");
  expect(istektekiStil("ornek-markax ile", stiller)).toBeNull();
  expect(istektekiStil("sadece sessizlikleri kes", stiller)).toBeNull();
});
