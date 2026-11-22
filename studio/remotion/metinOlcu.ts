// Motion metin grafiklerinin saf hesapları: yazı sığdırma, vurgu parçaları, güvenli alan. Test edilir, React'e bağlı değil.
// WHY: bkz. wiki/decisions/0031-motion-grafik.md.

// shortcut: Montserrat 800 harf genişliği tahmini (em), ölçüm yok. Taşma görülürse canvas measureText'e geç.
const harfG = (c: string) =>
  /[İIıilj.,:;'!|]/.test(c) ? 0.34 : /[MWmwĞ@]/.test(c) ? 0.98 : /[A-ZÇÖŞÜ0-9%₺$€#]/.test(c) ? 0.76 : c === " " ? 0.28 : 0.62;
export const metinG = (s: string) => [...s].reduce((a, c) => a + harfG(c), 0);

// En uzun kelime tek satıra, tüm metin en çok `satir` satıra sığsın; boyut yalnız küçülür.
export const sigdir = (metin: string, boyut: number, genislik: number, satir = 2) => {
  const kelimeler = metin.split(/\s+/).filter(Boolean);
  const enUzun = Math.max(0.5, ...kelimeler.map(metinG));
  return Math.max(8, Math.min(boyut, (genislik * 0.94) / enUzun, (genislik * 0.94 * satir) / Math.max(0.5, metinG(metin))));
};

// `*kelime*` vurgu rengiyle çizilir; yıldızlar görünmez.
export const parca = (s: string) =>
  s.split(/(\*[^*]+\*)/).filter(Boolean).map((t) => (t.length > 2 && t.startsWith("*") && t.endsWith("*") ? { t: t.slice(1, -1), v: true } : { t, v: false }));
export const duz = (s: string) => parca(s).map((p) => p.t).join("");

const sinir = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));

// 9:16: üst %12 ve alt %22 (altyazı bandı) dışı; 16:9: altyazı 0,875'te, çapa en çok 0,74. Çapa dikeyde ortadır.
export const guvenliY = (y: number, yatay: boolean) => (yatay ? sinir(y, 0.09, 0.74) : sinir(y, 0.14, 0.68));

// Varsayılan yerler yüzün (ortanın üstü) dışında: dikeyde yüzün altı, yatayda alt üçte bir.
const DIKEY: Record<string, { x: number; y: number }> = {
  anahtar: { x: 0.5, y: 0.6 }, altbant: { x: 0.06, y: 0.62 }, etiket: { x: 0.06, y: 0.17 }, cagri: { x: 0.5, y: 0.6 },
  daktilo: { x: 0.5, y: 0.6 }, sayac: { x: 0.5, y: 0.58 }, ilerleme: { x: 0.5, y: 0.15 }, bolum: { x: 0.5, y: 0.56 },
};
const YATAY: Record<string, { x: number; y: number }> = {
  anahtar: { x: 0.5, y: 0.62 }, altbant: { x: 0.05, y: 0.72 }, etiket: { x: 0.05, y: 0.12 }, cagri: { x: 0.3, y: 0.66 },
  daktilo: { x: 0.5, y: 0.66 }, sayac: { x: 0.5, y: 0.64 }, ilerleme: { x: 0.5, y: 0.09 }, bolum: { x: 0.5, y: 0.5 },
};

// Yatay hiza çapadan: solda sola, sağda sağa, ortada ortaya yaslanır; genişlik kenara kadar kalan yerdir.
export const varsayilanKonum = (tip: string, yatay: boolean) => (yatay ? YATAY : DIKEY)[tip] ?? { x: 0.5, y: 0.6 };

export const yerlesim = (tip: string, konum: { x?: number; y?: number } | undefined, W: number, H: number) => {
  const yatay = W > H;
  const v = varsayilanKonum(tip, yatay);
  const x = sinir(konum?.x ?? v.x, 0, 1), y = guvenliY(konum?.y ?? v.y, yatay);
  const pay = 0.05 * W;
  const hiza: "sol" | "orta" | "sag" = x < 0.34 ? "sol" : x > 0.66 ? "sag" : "orta";
  const genislik = hiza === "sol" ? W * (1 - x) - pay : hiza === "sag" ? W * x - pay : 2 * Math.min(x, 1 - x) * W - 2 * pay;
  return { x: x * W, y: y * H, hiza, genislik: Math.max(0.3 * W, Math.min(genislik, yatay ? 0.6 * W : W - 2 * pay)) };
};
