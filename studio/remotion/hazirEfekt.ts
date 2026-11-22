// WHY: bkz. wiki/decisions/0033-hazir-efektler.md. Hazır efekt keyframe matematiğinin tek yeri: önizleme ve render Kurgu.tsx'te
// bunu çalıştırır, Stüdyo "Keyframe'e çevir" de bunu kullanır. Python (hazir_efekt.py) yalnız ad/parametre denetler ve ses olayı çıkarır.
import KAYIT from "./hazirEfekt.json";
import { kfDeger } from "./izdusum";
import type { Hazir, KF, Klip, Yon } from "./tipler";

export interface Param { vars: number | string | boolean; min?: number; max?: number; secenek?: string[]; degisim?: (number | string)[] }
export interface Tanim { amac: string; ne_zaman: string; ses: boolean; rol: string; son?: boolean; ses_an?: number; ses_kare?: number; param: Record<string, Param> }
export const HAZIR = KAYIT as Record<string, Tanim>;

export type Ozellik = "x" | "y" | "olcek" | "opaklik" | "aci" | "bulanik" | "parlaklik";
export type Izler = Partial<Record<Ozellik, KF[]>>;
const CARPIM = new Set<Ozellik>(["olcek", "opaklik", "parlaklik"]);
export interface Ortam { w: number; h: number; fps: number }

const r4 = (n: number) => Math.round(n * 1e4) / 1e4;
const kf = (t: number, v: number, ease: KF["ease"] = "dogrusal"): KF => ({ t: r4(Math.max(0, t)), v: r4(v), ease });
export const YON: Record<Yon, [number, number]> = { sol: [-1, 0], sag: [1, 0], yukari: [0, -1], asagi: [0, 1] };
// Kutu dönünce köşe açılmasın: kendini örtmesi için gereken ölçek.
const donusOlcegi = (derece: number, o: Ortam) => {
  const a = (Math.abs(derece) * Math.PI) / 180;
  return Math.cos(a) + (Math.max(o.w, o.h) / Math.min(o.w, o.h)) * Math.sin(a) + (a ? 0.004 : 0);
};
// Sarsıntı için tohumlu üreteç (mulberry32): rastgelelik render'da değil klip kimliğinde.
const uretec = (tohum: string) => {
  let s = 0;
  for (const ch of tohum) s = (Math.imul(s ^ ch.charCodeAt(0), 2654435761) >>> 0);
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let z = Math.imul(s ^ (s >>> 15), 1 | s);
    z = (z + Math.imul(z ^ (z >>> 7), 61 | z)) ^ z;
    return ((z ^ (z >>> 14)) >>> 0) / 4294967296;
  };
};

interface Cozum { t: number; d: number; p: Record<string, any>; o: Ortam; c: Klip; tohum: string }
type Kurucu = (z: Cozum) => Izler;

const KURUCU: Record<string, Kurucu> = {
  zoom_in: ({ t, d, p }) => ({ olcek: [kf(t, 1, "yumusak"), kf(t + d, p.s)] }),
  zoom_out: ({ t, d, p }) => ({ olcek: [kf(t, p.s, "yumusak"), kf(t + d, 1)] }),
  punch: ({ t, d, p, o }) => {
    const gir = 6 / o.fps, birak = 8 / o.fps;
    return { olcek: [kf(t, 1, "geri"), kf(t + gir, p.s), kf(t + gir + d, p.s, "yumusak"), kf(t + gir + d + birak, 1)] };
  },
  odak_zoom: ({ t, d, p, o, c }) => {
    const olcek = [kf(t, 1, "expo"), kf(t + d, p.s)];
    if (p.geri_don) olcek.push(kf(t + d + p.tut, p.s, "yumusak"), kf(t + d + p.tut + 0.4, 1));
    // Nokta yerinde kalsın: çapaya göre ölçeklenen noktayı aynı eğriyle geri it. El ölçeği de hesaba katılır.
    const capa = c.donus.capa ?? { x: 0.5, y: 0.5 }, el = kfDeger(c.donus.olcek, t, 1);
    const dx = (p.x - capa.x) * o.w * el, dy = (p.y - capa.y) * o.h * el;
    return { olcek, x: olcek.map((f) => ({ ...f, v: r4((1 - f.v) * dx) })), y: olcek.map((f) => ({ ...f, v: r4((1 - f.v) * dy) })) };
  },
  ken_burns: ({ t, d, p, o }) => {
    const [vx, vy] = YON[p.yon as Yon], s0 = 1 + (p.s - 1) / 2;
    // Kayma her an büyümenin açtığı payın %90'ında kalır: ikisi de aynı eğri ve doğrusal, uçlarda tutan arada da tutar.
    const pay = (s: number, boy: number) => 0.9 * ((s - 1) / 2) * boy;
    const iz = (v: number, boy: number) => [kf(t, -v * pay(s0, boy), "yumusak"), kf(t + d, v * pay(p.s, boy))];
    return { olcek: [kf(t, s0, "yumusak"), kf(t + d, p.s)], ...(vx ? { x: iz(vx, o.w) } : { y: iz(vy, o.h) }) };
  },
  giris_pop: ({ t, d, p }) => ({ olcek: [kf(t, p.s, "geri"), kf(t + d, 1)], opaklik: [kf(t, 0, "cikis"), kf(t + d * 0.6, 1)] }),
  giris_kay: ({ t, d, p, o }) => {
    const [vx, vy] = YON[p.yon as Yon], m = p.mesafe * (vx ? o.w : o.h);
    const iz = [kf(t, -(vx || vy) * m, "expo"), kf(t + d, 0)];
    return { ...(vx ? { x: iz } : { y: iz }), opaklik: [kf(t, 0, "cikis"), kf(t + d * 0.5, 1)] };
  },
  cikis_kay: ({ t, d, p, o }) => {
    const [vx, vy] = YON[p.yon as Yon], m = p.mesafe * (vx ? o.w : o.h);
    const iz = [kf(t, 0, "giris"), kf(t + d, (vx || vy) * m)];
    return { ...(vx ? { x: iz } : { y: iz }), opaklik: [kf(t + d * 0.4, 1, "giris"), kf(t + d, 0)] };
  },
  cikis_sol: ({ t, d, p }) => ({ olcek: [kf(t, 1, "giris"), kf(t + d, p.s)], opaklik: [kf(t, 1, "giris"), kf(t + d, 0)] }),
  sarsinti: ({ t, d, p, o, tohum }) => {
    const rnd = uretec(tohum), n = Math.max(4, Math.round((d * o.fps) / 2)), aci = p.guc / 20;
    const x = [kf(t, 0, "yumusak")], y = [kf(t, 0, "yumusak")], a = [kf(t, 0, "yumusak")];
    for (let i = 1; i < n; i++) {
      const g = (1 - (i - 1) / (n - 1)) ** 2, isaret = i % 2 ? 1 : -1, ti = t + (i * d) / n;
      x.push(kf(ti, isaret * p.guc * g * (0.6 + 0.4 * rnd()), "yumusak"));
      y.push(kf(ti, -isaret * p.guc * g * (0.3 + 0.5 * rnd()), "yumusak"));
      a.push(kf(ti, (rnd() * 2 - 1) * aci * g, "yumusak"));
    }
    x.push(kf(t + d, 0)); y.push(kf(t + d, 0)); a.push(kf(t + d, 0));
    // Sarsıntı payı: her yanda guc kadar kayma ve en büyük açı örtülür.
    const os = donusOlcegi(aci, o) + (2 * p.guc) / Math.min(o.w, o.h);
    return { x, y, aci: a, olcek: [kf(t, 1, "cikis"), kf(t + 1 / o.fps, os), kf(t + d, os, "yumusak"), kf(t + d + 4 / o.fps, 1)] };
  },
  nabiz: ({ t, d, p, o }) => {
    const olcek: KF[] = [];
    for (let i = 0; i < Math.round(p.adet); i++) olcek.push(kf(t + i * d, 1, "cikis"), kf(t + i * d + 3 / o.fps, p.s, "yumusak"));
    olcek.push(kf(t + Math.round(p.adet) * d, 1));
    return { olcek };
  },
  egim: ({ t, d, p, o }) => ({ aci: [kf(t, p.aci, "expo"), kf(t + d, 0)], olcek: [kf(t, donusOlcegi(p.aci, o), "expo"), kf(t + d, 1)] }),
  bulanik_gir: ({ t, d, p }) => ({ bulanik: [kf(t, p.guc, "cikis"), kf(t + d, 0)], opaklik: [kf(t, 0, "cikis"), kf(t + d * 0.5, 1)] }),
  // WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Gerçek düşüş: düşerken "giris" (x²) yerçekimiyle birebir,
  // çıkışta "cikis" (1-(1-x)²) yavaşlayan atışla birebir. Sekme yüksekliği e², süresi e ile kısalır.
  giris_dus: ({ t, d, p, o }) => {
    const H0 = p.mesafe * o.h, T0 = d * 0.45, g = (2 * H0) / (T0 * T0);
    const y = [kf(t, -H0, "giris"), kf(t + T0, 0)];
    let an = t + T0, h = H0;
    for (let i = 0; i < 6; i++) {
      h *= p.sekme * p.sekme;
      const yarim = Math.sqrt((2 * h) / g);
      if (h < 2 || an + 2 * yarim > t + d) break;
      y[y.length - 1].ease = "cikis";
      y.push(kf(an + yarim, -h, "giris"), kf(an + 2 * yarim, 0));
      an += 2 * yarim;
    }
    return { y, opaklik: [kf(t, 0, "cikis"), kf(t + 2 / o.fps, 1)] };
  },
  carp_zoom: ({ t, d, p, o, c, tohum }) => {
    const f = 1 / o.fps, rnd = uretec(tohum);
    const olcek = [kf(t, 1, "yumusak"), kf(t + 6 * f, 0.965, "giris"), kf(t + 12 * f, p.s, "tut"), kf(t + Math.max(d, 18 * f), p.s)];
    const capa = c.donus.capa ?? { x: 0.5, y: 0.5 }, el = kfDeger(c.donus.olcek, t, 1);
    const dx = (p.x - capa.x) * o.w * el, dy = (p.y - capa.y) * o.h * el;
    const x = olcek.map((k) => ({ ...k, v: r4((1 - k.v) * dx) })), y = olcek.map((k) => ({ ...k, v: r4((1 - k.v) * dy) }));
    // Çarpma karesinden sonra 6 kare sönen sarsıntı (tohumlu): odak izine eklenir.
    const sx: KF[] = [], sy: KF[] = [];
    for (let i = 1; i <= 6; i++) {
      const g = Math.exp(-i / 1.8) * p.guc, ti = t + (12 + i) * f;
      sx.push(kf(ti, (1 - p.s) * dx + (i % 2 ? 1 : -1) * g * (0.6 + 0.4 * rnd()), "yumusak"));
      sy.push(kf(ti, (1 - p.s) * dy - (i % 2 ? 1 : -1) * g * (0.3 + 0.4 * rnd()), "yumusak"));
    }
    const ekle = (iz: KF[], s: KF[]) => [...iz.slice(0, 3), ...s, ...iz.slice(3)].sort((a, b) => a.t - b.t);
    return { olcek, x: ekle(x, sx), y: ekle(y, sy) };
  },
  giris_carp: ({ t, d, p, o }) => {
    const f = 1 / o.fps, v = t + 6 * f;
    const olcek = [kf(t, p.s, "giris"), kf(v, 1, "yumusak"), kf(v + 3 * f, 1.04, "yumusak"), kf(v + 6 * f, 0.985, "yumusak"), kf(v + 9 * f, 1.01, "yumusak"), kf(Math.max(v + 12 * f, t + d), 1)];
    return { olcek, aci: [kf(t, p.aci, "giris"), kf(v, 0)], opaklik: [kf(t, 0, "cikis"), kf(t + 2 * f, 1)] };
  },
  // El kamerası: iki farklı frekanslı sinüsün toplamı (tohumlu faz), 3-4 karede bir örneklenir; girişte ve çıkışta
  // genlik 0'dan açılıp kapanır. Sabit ölçek payı salınımın en kötü anını örter (kenar açılmaz, kesimde zıplamaz).
  el_kamerasi: ({ t, d, p, o, tohum }) => {
    const rnd = uretec(tohum), u = Math.min(o.w, o.h) / 1080, A = p.guc * u, aciA = p.guc / 40;
    const faz = Array.from({ length: 6 }, () => rnd() * Math.PI * 2);
    const w1 = 2 * Math.PI * p.hiz, w2 = w1 * 1.73;
    const adim = Math.max(3 / o.fps, d / 400), n = Math.max(2, Math.ceil(d / adim));
    const rampa = Math.max(1e-4, Math.min(0.4, d / 4));
    const x: KF[] = [], y: KF[] = [], a: KF[] = [];
    for (let i = 0; i <= n; i++) {
      const ti = t + Math.min(d, i * adim), z = ti - t;
      const zarf = Math.min(1, z / rampa, (d - z) / rampa);
      const yum = zarf * zarf * (3 - 2 * zarf);
      x.push(kf(ti, yum * A * (0.7 * Math.sin(w1 * z + faz[0]) + 0.3 * Math.sin(w2 * z + faz[1]))));
      y.push(kf(ti, yum * A * 0.8 * (0.65 * Math.sin(w1 * 0.83 * z + faz[2]) + 0.35 * Math.sin(w2 * 1.21 * z + faz[3]))));
      a.push(kf(ti, yum * aciA * (0.6 * Math.sin(w1 * 0.61 * z + faz[4]) + 0.4 * Math.sin(w2 * 0.77 * z + faz[5]))));
    }
    const s = Math.max(p.s, donusOlcegi(aciA, o) + (2 * A) / Math.min(o.w, o.h));
    return { x, y, aci: a, olcek: [kf(t, s), kf(t + d, s)] };
  },
  // Hızlı zoom: 8 karede expo rampa, sonra tutma (geri bırakmaz). Odak noktası odak_zoom gibi yerinde kalır.
  hizli_zoom: ({ t, d, p, o, c }) => {
    const ramp = 8 / o.fps;
    const olcek = [kf(t, 1, "expo"), kf(t + ramp, p.s), kf(t + Math.max(d, ramp + 1 / o.fps), p.s)];
    const capa = c.donus.capa ?? { x: 0.5, y: 0.5 }, el = kfDeger(c.donus.olcek, t, 1);
    const dx = (p.x - capa.x) * o.w * el, dy = (p.y - capa.y) * o.h * el;
    return { olcek, x: olcek.map((k) => ({ ...k, v: r4((1 - k.v) * dx) })), y: olcek.map((k) => ({ ...k, v: r4((1 - k.v) * dy) })) };
  },
  // Odak karartma: arka plan bulanıklaşır ve kararır (parlaklik izi Kurgu.tsx'te brightness'a gider). Bulanıklık kenarda
  // saydam hale açar; onu örten ölçek payı bulanıklıkla birlikte gelir ve gider.
  odak_karart: ({ t, d, p, o }) => {
    const g = Math.min(p.gecis, d / 2), son = t + d;
    const zarf = (v0: number, v1: number) => (son - g <= t + g + 1e-4
      ? [kf(t, v0, "yumusak"), kf(t + d / 2, v1, "yumusak"), kf(son, v0)]
      : [kf(t, v0, "yumusak"), kf(t + g, v1), kf(son - g, v1, "yumusak"), kf(son, v0)]);
    const iz: Izler = { parlaklik: zarf(1, p.parlaklik) };
    if (p.bulanik > 0) {
      iz.bulanik = zarf(0, p.bulanik);
      iz.olcek = zarf(1, 1 + (3 * p.bulanik) / Math.min(o.w, o.h));
    }
    return iz;
  },
};

const sinirla = (v: number, pr: Param) => Math.min(pr.max ?? Infinity, Math.max(pr.min ?? -Infinity, v));

// Parametreler: yazılan değer sınırlanır; yoksa art arda kliplerde değişim listesi sırayla, o da yoksa varsayılan.
export const cozumle = (c: Klip, h: Hazir, sira: number) => {
  const tn = HAZIR[h.ad];
  const p: Record<string, any> = {};
  let degisti = false;
  for (const [ad, pr] of Object.entries(tn.param)) {
    const v = h[ad];
    if (typeof pr.vars === "number") p[ad] = typeof v === "number" && Number.isFinite(v) ? sinirla(v, pr) : pr.degisim ? (degisti = true, pr.degisim[sira % pr.degisim.length]) : pr.vars;
    else if (typeof pr.vars === "boolean") p[ad] = typeof v === "boolean" ? v : pr.vars;
    else p[ad] = pr.secenek?.includes(v) ? v : pr.degisim ? (degisti = true, pr.degisim[sira % pr.degisim.length]) : pr.vars;
  }
  let d = p.sure as number;
  const t = typeof h.t === "number" ? Math.max(0, h.t) : tn.son ? Math.max(0, c.sure - d) : 0;
  if (!d) d = Math.max(0.04, c.sure - t); // sure 0: klibin sonuna kadar
  return { t, d, p, degisti };
};

// Klip kimliği -> her hazır efektin göreli izleri (dizin hazir[] ile aynı). Değişim sayacı izde art arda kliplerde sürer.
export const genislet = (klipler: Klip[], o: Ortam): Map<string, Izler[]> => {
  const m = new Map<string, Izler[]>();
  const izler = new Map<string, Klip[]>();
  for (const c of klipler) if (c.hazir?.length) izler.set(c.iz, [...(izler.get(c.iz) ?? []), c]);
  for (const c of klipler) if (!c.hazir?.length && izler.has(c.iz)) izler.get(c.iz)!.push(c);
  for (const l of izler.values()) {
    let sayac: Record<string, number> = {};
    for (const c of l.sort((a, b) => a.bas - b.bas)) {
      const adlar = new Set((c.hazir ?? []).map((h) => h.ad));
      sayac = Object.fromEntries(Object.entries(sayac).filter(([a]) => adlar.has(a)));
      if (!c.hazir?.length) continue;
      m.set(c.id, c.hazir.map((h, i) => {
        if (!HAZIR[h.ad]) return {};
        const { t, d, p, degisti } = cozumle(c, h, sayac[h.ad] ?? 0);
        if (degisti) sayac[h.ad] = (sayac[h.ad] ?? 0) + 1;
        return KURUCU[h.ad]({ t, d, p, o, c, tohum: `${c.id}:${i}` });
      }));
    }
  }
  return m;
};

// El keyframe'i ile hazır izlerin bileşimi: ölçek ve opaklık çarpılır, diğerleri toplanır. Çakışma yoktur, el değeri taban olur.
export const deger = (el: KF[] | undefined, izler: Izler[] | undefined, oz: Ozellik, t: number, vars: number) => {
  let v = kfDeger(el ?? [], t, vars);
  for (const iz of izler ?? []) {
    const l = iz[oz];
    if (l?.length) v = CARPIM.has(oz) ? v * kfDeger(l, t, 1) : v + kfDeger(l, t, 0);
  }
  return v;
};

// Keyframe'e çevir: tek hazır efektin izleri klibin el keyframe'lerine yazılır.
// shortcut: el izi zaten animasyonluysa bileşim yalnız keyframe anlarında örneklenir (eğri arası yaklaşık); tam isabet gerekirse kare kare örnekle.
export const pisir = (c: Klip, iz: Izler) => {
  const yaz = (el: KF[], oz: Ozellik, vars: number): KF[] => {
    const l = iz[oz]!;
    const anlar = [...new Set([...el.length > 1 ? el.map((f) => f.t) : [], ...l.map((f) => f.t)])].sort((a, b) => a - b);
    return anlar.map((t) => kf(t, deger(el, [iz], oz, t, vars), l.find((f) => Math.abs(f.t - t) < 1e-4)?.ease ?? el.find((f) => Math.abs(f.t - t) < 1e-4)?.ease ?? "dogrusal"));
  };
  const d = c.donus;
  for (const oz of ["x", "y", "olcek", "opaklik", "aci"] as const) {
    if (!iz[oz]?.length) continue;
    d[oz] = yaz(d[oz] ?? [], oz, oz === "olcek" || oz === "opaklik" ? 1 : 0);
    if (!d.anim.includes(oz)) d.anim.push(oz);
  }
  if (iz.bulanik?.length) c.efekt.bulanik_kf = yaz(c.efekt.bulanik_kf ?? [], "bulanik", c.efekt.bulanik);
  if (iz.parlaklik?.length) c.efekt.parlaklik_kf = yaz(c.efekt.parlaklik_kf ?? [], "parlaklik", c.efekt.parlaklik);
};
