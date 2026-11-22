// Altyazı: sayfalama ve kare başına HTML. Varsayılan ADR 0014 standardı (okunan kelime turuncu, gerisi beyaz, siyah
// kontur, Montserrat 800), stil seçiliyse stilin altyazı token'ı (ADR 0043).
// WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. SplitReel.tsx Captions/buildTokens/buildPages ve Kurgu.tsx
// StilliAltyazi/YatayAltyazi ile birebir; SplitReel Remotion'a bağlı olduğu için saf kopya burada (Python: hizli.sayfala).
import type { AltyaziStil, Kelime } from "../remotion/tipler";

export const CAP_Y = 1402;          // dikey tam ekranda altyazı merkezi (SplitReel)
export const YATAY_ALTYAZI_Y = 945; // yatayda alt güvenli alan (Kurgu.tsx)
export const CAP_VARSAYILAN = { fg: "#FFFFFF", active: "#FF7A00", stroke: "#000000" }; // ADR 0014

export interface Tok { text: string; s: number; e: number }

const temiz = (w: string) => w.trim().replace(/^zeka(ya)?$/i, (m) => (m.toLowerCase() === "zeka" ? "zekâ" : "zekâya"));

export const buildTokens = (words: Kelime[]): Tok[] => {
  const out: Tok[] = [];
  for (const w of words) {
    const txt = w.w.trim();
    if (out.length && /^['’,]/.test(txt)) {
      const prev = out[out.length - 1];
      prev.text = prev.text.replace(/[.,]$/, "") + txt;
      prev.e = w.e;
    } else out.push({ text: temiz(txt), s: w.s, e: w.e });
  }
  return out;
};

export const buildPages = (toks: Tok[], enKelime = 3, enKarakter = 18): Tok[][] => {
  const pages: Tok[][] = [];
  let cur: Tok[] = [];
  for (const t of toks) {
    const len = [...cur, t].map((x) => x.text).join(" ").length;
    if (cur.length && (cur.length >= enKelime || len > enKarakter)) { pages.push(cur); cur = []; }
    cur.push(t);
    if (/[.!?]$/.test(t.text)) { pages.push(cur); cur = []; }
  }
  if (cur.length) pages.push(cur);
  return pages;
};

// t anında gösterilecek sayfa ve okunan kelime; yoksa null.
export const sayfaBul = (pages: Tok[][], t: number): { pg: Tok[]; aktif: number } | null => {
  const idx = pages.findIndex((pg, i) => t >= pg[0].s - 0.04 && t < (pages[i + 1] ? pages[i + 1][0].s - 0.04 : pg[pg.length - 1].e + 0.5));
  if (idx < 0) return null;
  const pg = pages[idx];
  if (t > pg[pg.length - 1].e + 0.45) return null;
  const aktif = pg.findIndex((tok, i) => t >= tok.s && (pg[i + 1] ? t < pg[i + 1].s : t < tok.e + 0.3));
  return { pg, aktif };
};

const YEDEK: Record<string, string> = { Fraunces: "serif", "Playfair Display": "serif", "EB Garamond": "serif", Caveat: "cursive", "JetBrains Mono": "monospace", VT323: "monospace" };
export const yigin = (ad: string) => `'${ad}', ${YEDEK[ad] ?? "sans-serif"}`;
const kac = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

export interface AltyaziVeri {
  acik: boolean;
  words: Kelime[];
  stil: AltyaziStil | null;                 // null: ADR 0014 standardı
  renk: typeof CAP_VARSAYILAN;              // standart kipte renkler (stilli temada token'dan)
  yatay: boolean;
  w: number; h: number;
}

// Kapsayıcının konumu (sayfadan bağımsız): bir kez yazılır.
export const kutuStili = (v: AltyaziVeri): string => {
  const s = v.stil;
  if (s) {
    const y = s.konum != null ? s.konum * v.h : v.yatay ? YATAY_ALTYAZI_Y : CAP_Y;
    return `position:absolute;left:40px;width:${v.w - 80}px;top:${y - s.boyut}px;min-height:${s.boyut * 2}px;display:flex;flex-wrap:wrap;`
      + `justify-content:center;align-items:center;column-gap:${s.boyut * 0.28}px`;
  }
  // Standart kutu 1080 geniş; yatayda ortaya ve alt güvenli alana taşınır (Kurgu.tsx YatayAltyazi, bölünmüş sahne yokken).
  const tasi = v.yatay ? `;transform:translate(${v.w / 2 - 540}px, ${YATAY_ALTYAZI_Y - CAP_Y}px)` : "";
  return `position:absolute;left:0;width:1080px;top:${CAP_Y - 50}px;height:100px;display:flex;justify-content:center;align-items:center;gap:20px${tasi}`;
};

// Bölünmüş sahnede (lp > 0) kutunun kare başına konumu: Kurgu.tsx StilliAltyazi, SplitReel Captions ve YatayAltyazi.
export const altyaziKonum = (v: AltyaziVeri, lp: number, sahneG: number, capSplitY: number): Record<string, string> => {
  const s = v.stil;
  const sol = v.yatay ? sahneG * lp : 0;
  if (s) {
    const y = s.konum != null ? s.konum * v.h : v.yatay ? YATAY_ALTYAZI_Y : CAP_Y + (capSplitY - CAP_Y) * lp;
    return { left: `${sol + 40}px`, width: `${v.w - sol - 80}px`, top: `${y - s.boyut}px` };
  }
  if (v.yatay) {
    const cx = v.w / 2 + (sahneG / 2) * lp;
    return { transformOrigin: `540px ${CAP_Y}px`, transform: `translate(${cx - 540}px, ${YATAY_ALTYAZI_Y - CAP_Y}px) scale(${1 - 0.2 * lp})` };
  }
  return { top: `${CAP_Y + (capSplitY - CAP_Y) * lp - 50}px` };
};

// Sayfanın HTML'i: okunan kelime aktif renkte.
export const sayfaHtml = (v: AltyaziVeri, pg: Tok[], aktif: number): string => {
  const s = v.stil;
  return pg.map((tok, i) => {
    const a = i === aktif && (!s || s.kip === "kelime");
    if (s) {
      const stil = `font-family:${yigin(s.font)};font-weight:${s.agirlik ?? 800};font-size:${s.boyut}px;letter-spacing:${s.kontur / 2}px;`
        + `line-height:1.1;color:${a ? s.aktif_renk : s.renk};paint-order:stroke fill`
        + (s.kontur ? `;-webkit-text-stroke:${s.kontur}px ${s.kontur_renk}` : "");
      return `<span style="${stil}">${kac(tok.text)}</span>`;
    }
    return `<span style="font-family:'Montserrat', sans-serif;font-weight:800;font-size:72px;line-height:1;display:inline-block;`
      + `color:${a ? v.renk.active : v.renk.fg};-webkit-text-stroke:12px ${v.renk.stroke};paint-order:stroke fill">${kac(tok.text)}</span>`;
  }).join("");
};
