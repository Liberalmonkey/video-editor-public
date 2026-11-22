// Canlı ses metresi. WHY: bkz. wiki/decisions/0022-av-ayirma-metre-yatay.md
// Master gerçek çıkıştır; kanal, dosya tepesi çarpı kazançtır çünkü Remotion iz başına ses düğümü vermez.
// İkisi de önizlemedir: ducking ve loudnorm içermez. Ölçülmüş sayı "Son miks" kutusundadır.
import { sesEgrisi } from "../../../remotion/izdusum";
import type { KurguProps } from "../../../remotion/tipler";
import type { Tepe } from "./gorselOnbellek";

export const OLCEK_ALT = -60, OLCEK_UST = 6;
export const db = (g: number) => (g > 0 ? 20 * Math.log10(g) : -Infinity);
export const konum = (d: number) => Math.max(0, Math.min(1, (d - OLCEK_ALT) / (OLCEK_UST - OLCEK_ALT)));

const SONUM = 20;    // dB/sn
const TUTMA = 1.5;   // sn
const KIRPMA = -0.1; // dBFS

// Anında yükselir, yavaş iner; tepe bir süre kalır; kırpma tıklanana kadar kalır.
export interface Cubuk { db: number; tepe: number; tepeKalan: number; kirpti: boolean }
export const yeniCubuk = (): Cubuk => ({ db: -Infinity, tepe: -Infinity, tepeKalan: 0, kirpti: false });
export const ilerlet = (c: Cubuk, seviye: number, dt: number): Cubuk => {
  const d = Math.max(seviye, Number.isFinite(c.db) ? c.db - SONUM * dt : -Infinity);
  const yeniTepe = d >= c.tepe;
  const tepeKalan = yeniTepe ? TUTMA : c.tepeKalan - dt;
  return {
    db: d < OLCEK_ALT ? -Infinity : d,
    tepe: yeniTepe ? d : tepeKalan > 0 ? c.tepe : Math.max(d, c.tepe - SONUM * dt),
    tepeKalan: Math.max(0, tepeKalan),
    kirpti: c.kirpti || seviye >= KIRPMA,
  };
};

// Kanalın t anındaki doğrusal genliği: tepe çarpı klip ve iz kazancı, fade dahil.
export const kanalSeviye = (k: KurguProps, iz: string, t: number, solo: string[], tepeAl: (yol: string) => Tepe | null): number => {
  const i = k.izler.find((x) => x.id === iz);
  if (!i || i.sessiz || (solo.length && !solo.includes(iz))) return 0;
  let en = 0;
  for (const c of k.klipler) {
    if (c.iz !== iz || t < c.bas || t >= c.bas + c.sure || !c.kaynak) continue;
    const sesli = c.tur === "ses" || (c.tur === "video" && !c.ses_kapali && k.kaynaklar[c.kaynak]?.ses);
    if (!sesli) continue;
    const y = k.kaynaklar[c.kaynak]?.yol;
    const p = y ? tepeAl(y) : null;
    if (!p?.tepe.length) continue;
    const n = Math.floor((c.giris + (t - c.bas) * c.hiz) * p.hz);
    const ham = Math.max(p.tepe[n] ?? 0, p.tepe[n + 1] ?? 0) / 255;
    const fps = k.sekans.fps;
    en = Math.max(en, ham * sesEgrisi(c, i.gain_db, fps)((t - c.bas) * fps));
  }
  return en;
};

// Master: Remotion'ın ana düğümünden okunur. Dinleme sesi okumadan sonra gelir: metre kullanıcının hoparlör ayarından etkilenmez.
const SAKLA = "studio.dinleme.v1";
let dinleme = (() => { try { return Number(localStorage.getItem(SAKLA) ?? 1); } catch { return 1; } })();
let dugum: { l: AnalyserNode; r: AnalyserNode; tampon: Float32Array<ArrayBuffer>; cikis: GainNode } | null = null;

export const dinlemeAl = () => dinleme;
export const dinlemeYaz = (v: number) => {
  dinleme = v;
  if (dugum) dugum.cikis.gain.value = v;
  try { localStorage.setItem(SAKLA, String(v)); } catch { /* özel pencere */ }
};

export const metreBagla = (ctx: AudioContext, ana: GainNode) => {
  const ayir = ctx.createChannelSplitter(2);
  const l = ctx.createAnalyser(), r = ctx.createAnalyser();
  l.fftSize = r.fftSize = 2048;
  const cikis = ctx.createGain();
  cikis.gain.value = dinleme;
  ana.connect(ayir);
  ayir.connect(l, 0);
  ayir.connect(r, 1);
  ana.disconnect(ctx.destination);
  ana.connect(cikis);
  cikis.connect(ctx.destination);
  dugum = { l, r, tampon: new Float32Array(new ArrayBuffer(2048 * 4)), cikis };
  return () => {
    dugum = null;
    try {
      ana.disconnect(ayir);
      ana.disconnect(cikis);
      cikis.disconnect();
      ana.connect(ctx.destination);
    } catch { /* ses bağlamı kapanmış */ }
  };
};

const tepe = (a: AnalyserNode, t: Float32Array<ArrayBuffer>) => {
  a.getFloatTimeDomainData(t);
  let en = 0;
  for (let i = 0; i < t.length; i++) { const v = Math.abs(t[i]); if (v > en) en = v; }
  return en;
};
export const masterBagli = () => !!dugum;
// Mono kaynakta ikinci kanal boştur; bu durumda iki çubuk da aynı sinyali gösterir.
export const masterOku = (): [number, number] => {
  if (!dugum) return [0, 0];
  const a = tepe(dugum.l, dugum.tampon), b = tepe(dugum.r, dugum.tampon);
  return [a, b || a];
};
