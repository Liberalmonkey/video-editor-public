// İçe aktarılmış Lottie (ADR 0046): @remotion/lottie ile kareye bağlı oynar; doygun renkler temaya eşlenir.
// Dosya: kurguda "library:motion/dis/<kaynak>/<id>/<id>.json"; render'da vedit public'e bağlar ("public:dis/<ad>.json").
import { Lottie as RLottie, type LottieAnimationData } from "@remotion/lottie";
import React, { useEffect, useState } from "react";
import { cancelRender, continueRender, delayRender, staticFile } from "remotion";
import { z } from "zod";
import { useTema, type TemaToken } from "../../../tema";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  dosya: z.string().min(3).default("library:motion/dis/ornek/ornek.json").describe("İçe aktarılmış Lottie JSON yolu"),
  renk: z.enum(["tema", "orijinal"]).default("tema").describe("tema: doygun renkler stilin vurgu ve ikincil rengine eşlenir"),
  dongu: z.boolean().default(false),
  hiz: z.number().min(0.25).max(3).default(1),
});

export const dosyaAdresi = (d: string) =>
  d.startsWith("public:") ? staticFile(d.slice(7)) : `/lib/${d.replace(/^library:/, "").split("/").map(encodeURIComponent).join("/")}`;

const onaltilik = (h: string): [number, number, number] => {
  const n = parseInt(h.slice(1, 7), 16);
  return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
};
const doygunluk = (r: number, g: number, b: number) => { const mx = Math.max(r, g, b), mn = Math.min(r, g, b); return mx === 0 ? 0 : (mx - mn) / mx; };
const ton = (r: number, g: number, b: number) => {
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  if (!d) return 0;
  const h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return (h * 60 + 360) % 360;
};

// Saf: animasyon verisinin kopyasında doygun renkleri (fl/st/gf sabit renk) temaya eşler. İlk görülen ton vurgu, uzak tonlar ikincil.
export const temayaBoya = (veri: LottieAnimationData, t: TemaToken): LottieAnimationData => {
  const kopya = JSON.parse(JSON.stringify(veri));
  const vurgu = onaltilik(t.renk.vurgu), ikincil = onaltilik(t.renk.ikincil);
  let ilkTon: number | null = null;
  const boya = (k: number[]) => {
    const [r, g, b] = k;
    if (doygunluk(r, g, b) < 0.25) return k; // nötr: siyah, beyaz, gri olduğu gibi
    const h = ton(r, g, b);
    if (ilkTon === null) ilkTon = h;
    const fark = Math.min(Math.abs(h - ilkTon), 360 - Math.abs(h - ilkTon));
    const [nr, ng, nb] = fark < 40 ? vurgu : ikincil;
    return [nr, ng, nb, k[3] ?? 1];
  };
  const gez = (o: any) => {
    if (Array.isArray(o)) { o.forEach(gez); return; }
    if (!o || typeof o !== "object") return;
    if ((o.ty === "fl" || o.ty === "st") && o.c && o.c.a === 0 && Array.isArray(o.c.k)) o.c.k = boya(o.c.k);
    for (const v of Object.values(o)) if (v && typeof v === "object") gez(v);
  };
  gez(kopya.layers);
  gez(kopya.assets);
  return kopya;
};

const LottieBilesen: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu }) => {
  const t = useTema();
  const [veri, setVeri] = useState<LottieAnimationData | null>(null);
  const [tutamac] = useState(() => delayRender(`Lottie ${param.dosya}`));
  useEffect(() => {
    fetch(dosyaAdresi(param.dosya)).then((r) => r.json()).then((j) => { setVeri(j); continueRender(tutamac); }).catch((e) => cancelRender(e));
  }, [param.dosya, tutamac]);
  if (!veri) return null;
  return (
    <RLottie animationData={param.renk === "tema" ? temayaBoya(veri, t) : veri} loop={param.dongu} playbackRate={param.hiz}
      style={{ width: kutu.w, height: kutu.h }} />
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: LottieBilesen });
