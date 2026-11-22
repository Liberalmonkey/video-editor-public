// Remotion Easing.bezier ile aynı eğri; çalışma zamanı ve geçişler paylaşır (ADR 0051).
export const bezier = (x1: number, y1: number, x2: number, y2: number) => {
  const A = (a: number, b: number) => 1 - 3 * b + 3 * a, B = (a: number, b: number) => 3 * b - 6 * a, C = (a: number) => 3 * a;
  const egri = (t: number, a: number, b: number) => ((A(a, b) * t + B(a, b)) * t + C(a)) * t;
  const egim = (t: number, a: number, b: number) => 3 * A(a, b) * t * t + 2 * B(a, b) * t + C(a);
  const tBul = (x: number) => {
    let t = x;
    for (let i = 0; i < 8; i++) {
      const e = egim(t, x1, x2);
      if (Math.abs(e) < 1e-7) break;
      t -= (egri(t, x1, x2) - x) / e;
    }
    if (t >= 0 && t <= 1 && Math.abs(egri(t, x1, x2) - x) < 1e-6) return t;
    let a = 0, b = 1;
    t = x;
    for (let i = 0; i < 40; i++) {
      const v = egri(t, x1, x2);
      if (Math.abs(v - x) < 1e-7) break;
      if (v < x) a = t; else b = t;
      t = (a + b) / 2;
    }
    return t;
  };
  return (x: number) => (x <= 0 ? 0 : x >= 1 ? 1 : egri(tBul(x), y1, y2));
};
