import type { Klip } from "../../remotion/tipler";

export const bitisHesapla = (klipler: Pick<Klip, "bas" | "sure">[]) => Math.max(0, ...klipler.map((c) => c.bas + c.sure));
