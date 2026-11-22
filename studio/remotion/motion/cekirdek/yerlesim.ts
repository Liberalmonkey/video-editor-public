// Yerleşim (ADR 0045): güvenli alan, platform arayüzü, altyazı bandı ve yüz kutusundan kaçınan deterministik seçim.
// Saf fonksiyonlar; React'e bağlı değil, vitest ile sınanır.
import type { Bolgeler, Kutu, MotionMeta, Nokta, Yer } from "./tipler";

export const kesisim = (a: Kutu, b: Kutu) =>
  Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x)) * Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));

export const icinde = (a: Kutu, b: Kutu) => a.x >= b.x - 0.5 && a.y >= b.y - 0.5 && a.x + a.w <= b.x + b.w + 0.5 && a.y + a.h <= b.y + b.h + 0.5;

// Güvenli alan: dikeyde kenarlardan %6, yatayda %5 (title safe).
export const guvenliAlan = (w: number, h: number): Kutu => {
  const dx = Math.round(w * (h > w ? 0.06 : 0.05)), dy = Math.round(h * 0.05);
  return { x: dx, y: dy, w: w - 2 * dx, h: h - 2 * dy };
};

// 9:16 platform arayüzü (Reels, Shorts, TikTok ortak zarfı): üst bar, alt açıklama ve sağ düğme sütunu.
export const platformBolgeleri = (w: number, h: number): Kutu[] =>
  h > w ? [
    { x: 0, y: 0, w, h: Math.round(h * 0.1) },
    { x: 0, y: Math.round(h * 0.8), w, h: h - Math.round(h * 0.8) },
    { x: Math.round(w * 0.86), y: Math.round(h * 0.42), w: w - Math.round(w * 0.86), h: Math.round(h * 0.38) },
  ] : [];

// Altyazı bandı: satır merkezi y, yazı boyu; iki satır, kontur ve nefes payıyla (3.1 boy: alt grafik altyazıya yapışmasın).
export const altyaziBandi = (w: number, y: number, boyut: number): Kutu => ({ x: 0, y: Math.round(y - boyut * 1.55), w, h: Math.round(boyut * 3.1) });

// Yüz kutusuna pay: göz ve ağız kenara yakın kalabilir; üstte alın/saç için ek pay verilir.
export const yuzPayi = (k: Kutu, oran = 0.12): Kutu => {
  const ustEk = oran + 0.22;
  return { x: k.x - k.w * oran, y: k.y - k.h * ustEk, w: k.w * (1 + 2 * oran), h: k.h * (1 + oran + ustEk) };
};

export const boyutHesapla = (meta: MotionMeta, w: number, h: number) => {
  const kisa = Math.min(w, h), u = kisa / 1080;
  const en = Math.max(meta.boyut.w * kisa, meta.en_kucuk_px * u);
  const boy = Math.max(meta.boyut.h * kisa, meta.en_kucuk_px * u * (meta.boyut.h / meta.boyut.w));
  return { w: Math.round(en), h: Math.round(boy), u };
};

const adaylar = (yer: Yer, g: Kutu, b: { w: number; h: number }, hedef: Nokta | null): Kutu[] => {
  const ortaX = g.x + (g.w - b.w) / 2, ortaY = g.y + (g.h - b.h) / 2;
  const sat = (y: number) => [0.5, 0, 1, 0.25, 0.75].map((k) => ({ x: g.x + (g.w - b.w) * k, y, ...b }));
  switch (yer) {
    // Üst bant: Reels üst arayüzünün (%10) hemen altında temiz baş üstü boşluğu (güvenli alanın %6-16'sı).
    case "ust": return [0.06, 0.1, 0.16, 0.22].flatMap((k) => sat(g.y + g.h * k));
    case "alt": return [0.62, 0.54, 0.7].flatMap((k) => sat(g.y + g.h * k - b.h / 2));
    case "orta": return [ortaY, ortaY - g.h * 0.12, ortaY + g.h * 0.12].flatMap((y) => sat(y));
    case "sol": return [0.3, 0.5, 0.7].map((k) => ({ x: g.x, y: g.y + g.h * k - b.h / 2, ...b }));
    case "sag": return [0.3, 0.5, 0.7].map((k) => ({ x: g.x + g.w - b.w, y: g.y + g.h * k - b.h / 2, ...b }));
    case "hedef": {
      if (!hedef) return [];
      // Hedefin çevresinde sekiz yön, hedefe bir kutu payı mesafede (call-out çizgisi için boşluk).
      return [[0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1]].map(([dx, dy]) => ({
        x: hedef.x - b.w / 2 + dx * (b.w * 0.8), y: hedef.y - b.h / 2 + dy * (b.h * 1.1), ...b,
      }));
    }
    case "tam": return [{ x: 0, y: 0, w: g.x * 2 + g.w, h: g.y * 2 + g.h }];
  }
};

export interface Secim { kutu: Kutu; ceza: number; yer: Yer }

// Yüz kutusu paylı gelir (yuzPayi, %12). Çekirdek (göz, ağız) ağır, pay halkası hafif cezalanır.
const cekirdek = (k: Kutu, oran = 0.12): Kutu => {
  const w = k.w / (1 + 2 * oran), h = k.h / (1 + 2 * oran);
  return { x: k.x + (k.w - w) / 2, y: k.y + (k.h - h) / 2, w, h };
};
const TERCIH = 0.05; // tercih sırasında bir adım geri gitmenin bedeli (alan oranı cinsinden)

// Ceza (alan oranı): yüz çekirdeği ×4, yüz payı ×0.5, altyazı ×3, platform ×2; güvenli alan dışı +1; tercih sırası 0.05/adım.
export const yerles =(meta: MotionMeta, w: number, h: number, bol: Bolgeler, tercih?: Yer, hedef: Nokta | null = null): Secim => {
  const b = boyutHesapla(meta, w, h);
  if (meta.yer.includes("tam") && (tercih === "tam" || meta.yer[0] === "tam")) return { kutu: { x: 0, y: 0, w, h }, ceza: 0, yer: "tam" };
  const sira: Yer[] = tercih && tercih !== "tam" ? [tercih, ...meta.yer.filter((y) => y !== tercih)] : meta.yer.filter((y) => y !== "tam");
  let en: Secim | null = null;
  sira.forEach((yer, si) => {
    for (const k of adaylar(yer, bol.guvenli, b, hedef)) {
      const alan = k.w * k.h;
      let ceza = 0;
      for (const y of bol.yuzler) {
        const ic = kesisim(k, cekirdek(y));
        ceza += (4 * ic + 0.5 * (kesisim(k, y) - ic)) / alan;
      }
      if (bol.altyazi) ceza += (3 * kesisim(k, bol.altyazi)) / alan;
      for (const p of bol.platform) ceza += (2 * kesisim(k, p)) / alan;
      if (!icinde(k, bol.guvenli)) ceza += 1;
      ceza += si * TERCIH;
      if (!en || ceza < en.ceza - 1e-9) en = { kutu: { x: Math.round(k.x), y: Math.round(k.y), w: k.w, h: k.h }, ceza, yer };
    }
  });
  return en ?? { kutu: { x: bol.guvenli.x, y: bol.guvenli.y, ...b }, ceza: 99, yer: sira[0] ?? "orta" };
};

// Çekirdek yüze, altyazıya ya da platforma değmeyen seçim (tercih bedeli ve pay halkası tolere edilir).
export const temizMi = (s: Secim, b: Bolgeler) =>
  b.yuzler.every((y) => kesisim(s.kutu, cekirdek(y)) === 0) && (!b.altyazi || kesisim(s.kutu, b.altyazi) === 0) && b.platform.every((p) => kesisim(s.kutu, p) === 0);
