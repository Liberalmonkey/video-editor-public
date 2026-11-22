import React from "react";
import { Composition, registerRoot } from "remotion";
import { Kurgu } from "./Kurgu";
import { Galeri, type GaleriProps } from "./motion/Galeri";
import { Tekil, boyutBul, sureHesapla, type TekilProps } from "./motion/Tekil";
import type { KurguProps } from "./tipler";

export const bitis = (p: KurguProps) => p.bitis ?? Math.max(1, ...p.klipler.map((c) => c.bas + c.sure));

const Root: React.FC = () => (
  <>
  <Composition
    id="MotionTekil"
    component={Tekil as React.FC<any>}
    durationInFrames={60}
    fps={30}
    width={1080}
    height={1080}
    defaultProps={{ ad: "ikon/tik", param: {}, en_boy: "1:1", sure: null, tema: null }}
    calculateMetadata={({ props }) => {
      const p = props as unknown as TekilProps;
      const { w, h } = boyutBul(p.en_boy);
      return {
        width: w,
        height: h,
        fps: 30,
        durationInFrames: Math.max(15, Math.ceil(sureHesapla(p.ad, p.sure) * 30)),
      };
    }}
  />
  <Composition
    id="MotionGaleri"
    component={Galeri as React.FC<any>}
    durationInFrames={1}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={{ adlar: [], zemin: "dama", faz: 0.55, hucre: { w: 540, h: 960 }, sutun: 4 }}
    calculateMetadata={({ props }) => {
      const p = props as unknown as GaleriProps;
      const satir = Math.max(1, Math.ceil(p.adlar.length / p.sutun));
      return { width: p.sutun * p.hucre.w + (p.sutun - 1) * 6, height: satir * p.hucre.h + (satir - 1) * 6 };
    }}
  />
  <Composition
    id="Kurgu"
    component={Kurgu as React.FC<any>}
    durationInFrames={30}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={{ sekans: { w: 1080, h: 1920, fps: 30 }, kaynaklar: {}, izler: [], klipler: [], altyazi: { acik: false, iz: "V1" } }}
    calculateMetadata={({ props }) => {
      const p = props as unknown as KurguProps;
      return { width: p.sekans.w, height: p.sekans.h, fps: p.sekans.fps, durationInFrames: Math.ceil(bitis(p) * p.sekans.fps) };
    }}
  />
  </>
);

registerRoot(Root);
