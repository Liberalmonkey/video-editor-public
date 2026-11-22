// Galeri kontağı (ADR 0045): bileşenler ızgarada, her hücre gerçek kare ya da dama zemin üstünde, istenen evrede.
// Dama zemin alfa kaybını (siyah ya da düz kutu) görünür yapar. vedit motion kontak bu kompozisyonu render eder.
import React from "react";
import { AbsoluteFill, Img, Sequence, staticFile, useVideoConfig } from "remotion";
import { TemaSaglayici, type TemaToken } from "../tema";
import type { Bolgeler } from "./cekirdek/tipler";
import { KAYIT } from "./kayit";
import { guvenliAlan, yerles } from "./cekirdek/yerlesim";

export interface GaleriProps {
  adlar: string[];
  zemin: "dama" | "kare";
  kare?: string | null;          // public içinde görsel (zemin "kare" ise)
  faz: number;                    // 0..1: klibin süresinde hangi an (0.18 giriş, 0.55 tutma, 0.93 çıkış)
  hucre: { w: number; h: number }; // hücre başına sekans boyutu (ör. 1080x1920 küçültülmüş)
  sutun: number;
  tema?: TemaToken | null;
  [k: string]: unknown;
}

const DAMA = "repeating-conic-gradient(#c8c8c8 0% 25%, #ffffff 0% 50%) 0 0 / 48px 48px";

const Hucre: React.FC<{ ad: string; p: GaleriProps }> = ({ ad, p }) => {
  const { fps } = useVideoConfig();
  const tanim = KAYIT[ad];
  if (!tanim) return null;
  const { w, h } = p.hucre;
  const sureKare = Math.round(tanim.meta.sure.varsayilan * fps);
  const f = Math.min(sureKare - 1, Math.round(p.faz * sureKare));
  const bol: Bolgeler = { guvenli: guvenliAlan(w, h), altyazi: null, yuzler: [], platform: [] };
  const s = yerles(tanim.meta, w, h, bol, "orta");
  const { Bilesen } = tanim;
  return (
    <div style={{ position: "relative", width: w, height: h, overflow: "hidden", background: p.zemin === "dama" ? DAMA : "#808080" }}>
      {p.zemin === "kare" && p.kare && <Img src={staticFile(p.kare)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />}
      <Sequence from={-f} layout="none">
        <div style={{ position: "absolute", left: s.kutu.x, top: s.kutu.y, width: s.kutu.w, height: s.kutu.h }}>
          <Bilesen param={tanim.sema.parse({})} kutu={{ ...s.kutu, x: 0, y: 0 }} hedef={{ x: s.kutu.w / 2, y: s.kutu.h + 80 }} sureKare={sureKare} u={Math.min(w, h) / 1080} />
        </div>
      </Sequence>
      <div style={{ position: "absolute", left: 8, bottom: 8, padding: "4px 10px", background: "rgba(0,0,0,0.7)", color: "#ffffff", font: "600 28px sans-serif" }}>{ad}</div>
    </div>
  );
};

export const Galeri: React.FC<GaleriProps> = (p) => (
  <TemaSaglayici tema={p.tema}>
    <AbsoluteFill style={{ background: "#202020", display: "grid", gridTemplateColumns: `repeat(${p.sutun}, ${p.hucre.w}px)`, gap: 6, alignContent: "start" }}>
      {p.adlar.map((ad) => <Hucre key={ad} ad={ad} p={p} />)}
    </AbsoluteFill>
  </TemaSaglayici>
);
