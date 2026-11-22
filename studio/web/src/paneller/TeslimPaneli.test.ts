import { expect, test } from "vitest";
import { hedefBoyut, isAlanlari, type Ayar } from "./TeslimPaneli";

test("çözünürlük kademesi sekans yönünü korur", () => {
  expect([720, 1080, 1440, 2160].map((k) => hedefBoyut(1080, 1920, k))).toEqual([[720, 1280], [1080, 1920], [1440, 2560], [2160, 3840]]);
  expect(hedefBoyut(1920, 1080, 1440)).toEqual([2560, 1440]);
  expect(hedefBoyut(1920, 1080, null)).toEqual([1920, 1080]);
});

test("varsayılan ayar iş isteğine fazladan alan eklemez", () => {
  const a: Ayar = { cozunurluk: null, kalite: "yayin", kodek: "h264", fps: null, platform: "", ad: "", yenile: false };
  expect(JSON.parse(JSON.stringify(isAlanlari(a)))).toEqual({ kalite: "yayin", kodek: "h264", yenile: false });
  expect(isAlanlari({ ...a, cozunurluk: 1440, fps: 60, ad: "v-2k" })).toMatchObject({ cozunurluk: 1440, fps: 60, cikti_adi: "v-2k" });
});
