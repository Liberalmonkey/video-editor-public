// Native çekirdeğinin "remotion" modülü: yalnız saf kare matematiği (ADR 0051). Tam paket React ve wall-clock kodu
// (requestAnimationFrame, Date.now, Math.random) taşır; HyperFrames lint'i bunları reddeder, çizim yolu da kullanmaz.
// Easing, interpolate ve spring Remotion'un kendi dosyalarıdır (sürüm package.json'da sabit): iki motor aynı sayıyı üretir.
import { Easing } from "../../node_modules/remotion/dist/cjs/easing.js";
import { interpolate } from "../../node_modules/remotion/dist/cjs/interpolate.js";
import { spring } from "../../node_modules/remotion/dist/cjs/spring/index.js";

export { Easing, interpolate, spring };

// remotion random ile birebir (mulberry32 + dize özeti); tohumsuz çağrı yoktur (deterministik olmalı).
const mulberry32 = (a: number) => {
  let t = a + 0x6d2b79f5;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};
const ozet = (s: string) => {
  let h = 0;
  for (let i = 0; i < s.length; i++) { h = (h << 5) - h + s.charCodeAt(i); h |= 0; }
  return h;
};
export const random = (tohum: string | number) => (typeof tohum === "string" ? mulberry32(ozet(tohum)) : mulberry32(tohum * 10000000000));

const yok = (ad: string) => () => { throw new Error(`HFN: ${ad} kullanılmaz (sahne karesi akisHesapla'dan gelir)`); };
export const useCurrentFrame = yok("useCurrentFrame");
export const useVideoConfig = yok("useVideoConfig");
