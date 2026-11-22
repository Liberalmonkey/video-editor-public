// HyperFrames içinde Remotion bileşenlerini çalıştıran ince taklit ("remotion" modülünün yerine paketlenir).
// WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Metin grafikleri ve SplitReel sahneleri saf kare fonksiyonudur
// (useCurrentFrame + useVideoConfig); bunları yeniden yazmak iki kopya doğururdu. Kare ve yapı bağlamı buradan gelir,
// saf yardımcılar (Easing, interpolate, random, spring) gerçek paketten aynen alınır: iki motor aynı sayıyı üretir.
// Kare süreleri HyperFrames'in saatinden türer; delayRender yok (fontlar tema.css @font-face ile yüklenir).
import React, { createContext, forwardRef, useContext } from "react";
import { Easing, interpolate, interpolateColors, measureSpring, random, spring } from "remotion-gercek";

export { Easing, interpolate, interpolateColors, measureSpring, random, spring };

export interface KareBaglam { frame: number; fps: number; width: number; height: number; durationInFrames: number }
const Kare = createContext<KareBaglam>({ frame: 0, fps: 30, width: 1080, height: 1920, durationInFrames: 1 });
export const KareSaglayici = Kare.Provider;

export const useCurrentFrame = () => useContext(Kare).frame;
export const useVideoConfig = () => {
  const k = useContext(Kare);
  return { fps: k.fps, width: k.width, height: k.height, durationInFrames: k.durationInFrames, id: "main", defaultProps: {}, props: {}, defaultCodec: null };
};

// Remotion Sequence: içindeki kare `from`'a göredir, aralık dışında çizilmez.
export const Sequence: React.FC<{ from?: number; durationInFrames?: number; children?: React.ReactNode; [k: string]: any }> = ({ from = 0, durationInFrames = Infinity, children }) => {
  const k = useContext(Kare);
  const f = k.frame - from;
  if (f < 0 || f >= durationInFrames) return null;
  return <Kare.Provider value={{ ...k, frame: f, durationInFrames: Number.isFinite(durationInFrames) ? durationInFrames : k.durationInFrames }}>{children}</Kare.Provider>;
};

export const AbsoluteFill = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ style, ...r }, ref) => (
  <div ref={ref} {...r} style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, width: "100%", height: "100%", display: "flex", flexDirection: "column", ...style }} />
));

export const Img = forwardRef<HTMLImageElement, React.ImgHTMLAttributes<HTMLImageElement>>((p, ref) => <img ref={ref} alt="" {...p} />);

// Ada içinde video çizilmez: medya HyperFrames klibidir (derle.ts). Buraya düşen bileşen hata verir, motor Remotion'a düşer.
const desteksiz = (ad: string) => () => { throw new Error(`HyperFrames adasında ${ad} yok`); };
export const OffthreadVideo = desteksiz("OffthreadVideo");
export const Video = desteksiz("Video");
export const Audio = desteksiz("Audio");

export const staticFile = (yol: string) => yol.replace(/^\/+/, "");
export const delayRender = (_ad?: string) => 0;
export const continueRender = (_h: number) => {};
export const cancelRender = (e: unknown) => { console.error(e); };
