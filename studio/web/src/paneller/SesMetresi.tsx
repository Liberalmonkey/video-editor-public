import React, { useEffect, useRef } from "react";
import { useKurgu } from "../zaman/depo";
import { tepeAl } from "../zaman/gorselOnbellek";
import { db, ilerlet, kanalSeviye, konum, masterOku, yeniCubuk, type Cubuk } from "../zaman/metre";

const RENK = { yesil: "#3fbf7f", sari: "#e8b84a", kirmizi: "#ff6b6b", zemin: "#0b0b0c", tepe: "#f4f4f5", tik: "rgba(255,255,255,0.14)" };

// Oynatmayı yavaşlatmasın: React dışında, değer değişince çizer.
const cubukCiz = (g: CanvasRenderingContext2D, c: Cubuk, x: number, y: number, w: number, h: number, yatay: boolean) => {
  g.fillStyle = RENK.zemin;
  g.fillRect(x, y, w, h);
  const boy = yatay ? w : h;
  const bant = (a: number, b: number, renk: string) => {
    const p0 = konum(a) * boy, p1 = konum(Math.min(b, c.db)) * boy;
    if (p1 <= p0) return;
    g.fillStyle = renk;
    if (yatay) g.fillRect(x + p0, y, p1 - p0, h); else g.fillRect(x, y + h - p1, w, p1 - p0);
  };
  bant(-60, -12, RENK.yesil);
  bant(-12, -3, RENK.sari);
  bant(-3, 6, RENK.kirmizi);
  if (Number.isFinite(c.tepe) && c.tepe > -60) {
    const p = konum(c.tepe) * boy;
    g.fillStyle = c.tepe >= -3 ? RENK.kirmizi : RENK.tepe;
    if (yatay) g.fillRect(x + p - 1, y, 1.5, h); else g.fillRect(x, y + h - p, w, 1.5);
  }
  // 0 dBFS işareti: üstü kırpar.
  const s = konum(0) * boy;
  g.fillStyle = RENK.tik;
  if (yatay) g.fillRect(x + s, y, 1, h); else g.fillRect(x, y + h - s, w, 1);
  if (c.kirpti) {
    g.fillStyle = RENK.kirmizi;
    if (yatay) g.fillRect(x + w - 3, y, 3, h); else g.fillRect(x, y, w, 3);
  }
};

export const SesMetresi: React.FC<{ iz?: string; yatay?: boolean; genislik: number; yukseklik: number }> = ({ iz, yatay = false, genislik, yukseklik }) => {
  const tuval = useRef<HTMLCanvasElement>(null);
  const cubuk = useRef<Cubuk[]>([]);

  useEffect(() => {
    const t = tuval.current;
    if (!t) return;
    const oran = devicePixelRatio || 1;
    t.width = Math.round(genislik * oran);
    t.height = Math.round(yukseklik * oran);
    const g = t.getContext("2d")!;
    g.setTransform(oran, 0, 0, oran, 0, 0);
    const kanal = iz ? 1 : 2;
    cubuk.current = Array.from({ length: kanal }, yeniCubuk);
    let dur = false, once = performance.now(), son = "";
    const dongu = (simdi: number) => {
      if (dur) return;
      requestAnimationFrame(dongu);
      const dt = Math.min(0.1, (simdi - once) / 1000);
      once = simdi;
      const d = useKurgu.getState();
      const oynuyor = d.oynuyor && !!d.kurgu && !!d.anahtar;
      let seviye: number[];
      if (!oynuyor) seviye = Array(kanal).fill(0);
      else if (iz) seviye = [kanalSeviye(d.kurgu!, iz, d.zaman, d.solo, (y) => tepeAl(d.anahtar!, y))];
      else seviye = masterOku();
      cubuk.current = cubuk.current.map((c, i) => ilerlet(c, db(seviye[i]), dt));
      // Testler ve erişilebilirlik okuru için son değer.
      const yaz = cubuk.current.map((c) => (Number.isFinite(c.db) ? c.db.toFixed(1) : "-inf")).join(" ");
      const durum = yaz + cubuk.current.map((c) => `${c.kirpti}${c.tepe.toFixed(1)}`).join();
      if (durum === son) return;
      son = durum;
      t.dataset.db = yaz;
      const ara = 1;
      const bo = yatay ? (yukseklik - ara * (kanal - 1)) / kanal : (genislik - ara * (kanal - 1)) / kanal;
      cubuk.current.forEach((c, i) => {
        if (yatay) cubukCiz(g, c, 0, i * (bo + ara), genislik, bo, true);
        else cubukCiz(g, c, i * (bo + ara), 0, bo, yukseklik, false);
      });
    };
    requestAnimationFrame(dongu);
    return () => { dur = true; };
  }, [iz, genislik, yukseklik, yatay]);

  const ad = iz ? `${iz} seviye metresi, önizleme` : "Ana çıkış metresi, önizleme";
  return (
    <canvas
      ref={tuval} className="metre" role="img" aria-label={ad} data-metre={iz ?? "master"}
      title={`${ad}. Ducking ve loudnorm içermez. Kırmızı uç 0 dB üstü demek; tıkla, sıfırla.`}
      style={{ width: genislik, height: yukseklik }}
      onClick={() => { cubuk.current = cubuk.current.map((c) => ({ ...c, kirpti: false })); }}
    />
  );
};
