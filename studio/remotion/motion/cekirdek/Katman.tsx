// Native motion klibinin kurgudaki kabı (ADR 0045): bölgeleri okur, yerleşimi seçer, bileşeni kutusuna çizer.
import React, { createContext, useContext, useMemo } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { rgba, useTema } from "../../tema";
import { KAYIT } from "../kayit";
import type { Bolgeler, Nokta, Yer } from "./tipler";
import { guvenliAlan, platformBolgeleri, yerles } from "./yerlesim";
import { useAkis } from "./zaman";

// Kurgu.tsx bir kare aralığının bölgelerini verir (altyazı bandı, aralıkta görünen bütün yüz kutuları). Yoksa yalnız güvenli alan.
export type BolgeKaynagi = (kare: number, sonKare?: number) => Partial<Bolgeler>;
const BolgeBaglam = createContext<BolgeKaynagi>(() => ({}));
export const BolgeSaglayici = BolgeBaglam.Provider;

// odak_karart (ya da param.odakKarart): bileşen kutusunun arkasında yumuşak radyal karartma; grafik öne çıkar.
export interface BilesenKlibi { ad: string; param?: Record<string, unknown>; yer?: Yer | "oto"; hedef?: { x: number; y: number } | null; odak_karart?: boolean | null }

export const MotionKatman: React.FC<{ b: BilesenKlibi; sureKare: number; basKare: number }> = ({ b, sureKare, basKare }) => {
  const { width: w, height: h } = useVideoConfig();
  const t = useTema();
  const kaynak = useContext(BolgeBaglam);
  const tanim = KAYIT[b.ad];
  // Yerleşim klibin girişinde bir kez seçilir: grafik oynarken yer değiştirmez. Bu yüzden klip boyunca görünen her yüzden kaçar
  // (instagram/1: konfeti girişte boş olan ortaya kondu, 1 sn sonra yakın plana geçen yüzün üstünde kaldı).
  const secim = useMemo(() => {
    if (!tanim) return null;
    const ek = kaynak(basKare, basKare + sureKare);
    const bol: Bolgeler = { guvenli: guvenliAlan(w, h), altyazi: ek.altyazi ?? null, yuzler: ek.yuzler ?? [], platform: ek.platform ?? platformBolgeleri(w, h) };
    const hedef: Nokta | null = b.hedef ? { x: b.hedef.x * w, y: b.hedef.y * h } : null;
    return { ...yerles(tanim.meta, w, h, bol, b.yer && b.yer !== "oto" ? b.yer : undefined, hedef), hedef };
  }, [tanim, kaynak, basKare, sureKare, w, h, b.yer, b.hedef]);
  useCurrentFrame();
  const a = useAkis(sureKare, tanim?.meta.giris_sn ?? 0.4, tanim?.meta.cikis_sn ?? 0.25, 0);
  if (!tanim || !secim) return null; // kurgu-denetle bilinmeyen adı zaten reddeder
  // odakKarart bileşen parametresi değildir: Zod şeması strict, parse'a girmeden ayrılır.
  const { odakKarart, ...ham } = (b.param ?? {}) as Record<string, unknown>;
  const karart = b.odak_karart === true || odakKarart === true;
  const param = tanim.sema.parse(ham);
  const { Bilesen } = tanim;
  const k = secim.kutu, cx = k.x + k.w / 2, cy = k.y + k.h / 2;
  const tam = k.w >= w - 1 && k.h >= h - 1;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {karart && (
        <AbsoluteFill style={{
          opacity: a.gorunur,
          background: tam
            ? `radial-gradient(ellipse 75% 65% at 50% 50%, transparent 30%, ${rgba(t.renk.ikon_kontur, 0.36)} 100%)`
            : `radial-gradient(ellipse ${Math.max(k.w * 1.25, w * 0.5)}px ${Math.max(k.h * 1.6, h * 0.3)}px at ${cx}px ${cy}px, ${rgba(t.renk.ikon_kontur, 0.36)} 0%, ${rgba(t.renk.ikon_kontur, 0.22)} 55%, transparent 100%)`,
        }} />
      )}
      <div style={{ position: "absolute", left: k.x, top: k.y, width: k.w, height: k.h }}>
        <Bilesen param={param} kutu={{ ...k, x: 0, y: 0 }} hedef={secim.hedef && { x: secim.hedef.x - k.x, y: secim.hedef.y - k.y }} sureKare={sureKare} u={Math.min(w, h) / 1080} />
      </div>
    </AbsoluteFill>
  );
};
