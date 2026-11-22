import type { Kelime, KF, Klip, KurguProps } from "./tipler";

const yuvarla = (n: number) => Math.round(n * 1000) / 1000;

// Altyazı sesi izler: görüntüsü altyazı izinde olup sesi ayrılmış klip düşer, ayrılan ses girer.
export const altyaziKlipleri = (k: Pick<KurguProps, "klipler" | "altyazi">) =>
  k.klipler.filter((c) => c.kaynak && (c.olay?.konusma || (c.iz === k.altyazi.iz && !c.ses_kapali))).sort((a, b) => a.bas - b.bas);

// src/vedit/kurgu.py izdusum ile aynı kural; test iki tarafı aynı örnekle sınar.
export const izdusum = (k: Pick<KurguProps, "klipler" | "kelimeler" | "altyazi">): Kelime[] => {
  if (!k.altyazi.acik) return [];
  const cikti: Kelime[] = [];
  for (const c of altyaziKlipleri(k)) {
    const bit = c.giris + c.sure * c.hiz;
    for (const w of k.kelimeler?.[c.kaynak!] ?? []) {
      if (c.giris <= w.s && w.s < bit) {
        cikti.push({ w: w.w, s: yuvarla(c.bas + (w.s - c.giris) / c.hiz), e: yuvarla(c.bas + (Math.min(w.e, bit) - c.giris) / c.hiz) });
      }
    }
  }
  return cikti;
};

export const dbGuc = (db: number) => Math.pow(10, db / 20);

// Tek karenin altındaki fade yalnız ilk kareyi susturur; kesim tıkı önlemini ffmpeg tarafı taşır.
export const sesEgrisi = (k: Klip, izDb: number, fps: number, kuyruk = 0) => {
  const g = dbGuc(k.ses.gain_db + izDb);
  const kf = k.ses.kf?.length ? k.ses.kf : null; // kazanç keyframe'i: dB, klip başından
  const toplam = k.sure * fps;
  const inn = k.ses.fade_in * fps, out = k.ses.fade_out * fps;
  const gGiris = k.gecis_giris && k.gecis_giris.tur !== "kaydir" ? k.gecis_giris.sure * fps : 0;
  const q = kuyruk * fps;
  return (f: number) => {
    let v = kf ? dbGuc(kfDeger(kf, f / fps, k.ses.gain_db) + izDb) : g;
    if (inn >= 1 && f < inn) v *= f / inn;
    if (out >= 1 && !q && f > toplam - out) v *= Math.max(0, (toplam - f) / out);
    if (gGiris && f < gGiris) v *= f / gGiris;
    if (q && f > toplam) v *= Math.max(0, 1 - (f - toplam) / q);
    return v;
  };
};

// geri, expo, yay: ADR 0033. Hepsi 0'da 0, 1'de tam 1 (keyframe sınırında sıçrama olmaz).
export const EGRI: Record<KF["ease"], (x: number) => number> = {
  dogrusal: (x: number) => x,
  yumusak: (x: number) => x * x * (3 - 2 * x),
  giris: (x: number) => x * x,
  cikis: (x: number) => 1 - (1 - x) * (1 - x),
  tut: () => 0,
  geri: (x: number) => 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2, // en çok ~%10 taşar
  expo: (x: number) => (x >= 1 ? 1 : (1 - 2 ** (-10 * x)) / (1 - 2 ** -10)),
  yay: (x: number) => 1 - Math.exp(-6 * x) * Math.cos(2.5 * Math.PI * x), // cos(2.5π) = 0: tam 1'de biter
};

// Keyframe değeri; `ease` soldaki keyframe'den sonraki parçayı belirler.
export const kfDeger = (kf: KF[], t: number, varsayilan: number): number => {
  if (!kf.length) return varsayilan;
  if (t <= kf[0].t) return kf[0].v;
  for (let i = 1; i < kf.length; i++) {
    if (t < kf[i].t) {
      const a = kf[i - 1], b = kf[i];
      return a.v + (b.v - a.v) * EGRI[a.ease]((t - a.t) / (b.t - a.t));
    }
  }
  return kf[kf.length - 1].v;
};
