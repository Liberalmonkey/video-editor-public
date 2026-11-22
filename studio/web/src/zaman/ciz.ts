// Timeline çizimi: durum alır, canvas'a yazar, durum tutmaz. Yalnız görünen klip ve piksel çizilir.
import type { Iz, Klip, KurguProps } from "../../../remotion/tipler";
import { zamanKodu } from "./depo";
import { seritAl, tepeAl } from "./gorselOnbellek";
import { KAZANC_ALT, KAZANC_UST, kazancAni, sesli } from "./komutlar";

export const CETVEL = 26;
export const YUK_VIDEO = 54;
export const YUK_SES = 42;
export const izYuksekligi = (i: Iz) => (i.tur === "video" ? YUK_VIDEO : YUK_SES);

// Ses çizgisi: ses klibinde tüm yükseklik, videoda alttaki dalga bandı. -24..+12 dB.
export const sesBandi = (k: KurguProps, c: Klip, y: number, h: number) => {
  if (!sesli(k, c)) return null;
  if (c.tur === "ses") return { ust: y + 1, yuk: h - 2 };
  const sh = Math.round((h - 2) * 0.62);
  return { ust: y + 1 + sh, yuk: h - 2 - sh };
};
export const kazancY = (db: number, b: { ust: number; yuk: number }) => b.ust + b.yuk * (1 - (Math.max(KAZANC_ALT, Math.min(KAZANC_UST, db)) - KAZANC_ALT) / (KAZANC_UST - KAZANC_ALT));
export const yKazanc = (y: number, b: { ust: number; yuk: number }) => KAZANC_ALT + (1 - Math.max(0, Math.min(1, (y - b.ust) / b.yuk))) * (KAZANC_UST - KAZANC_ALT);

const R = {
  zemin: "#101011", satir: "#161617", satirSes: "#141516", cizgi: "#000", cetvel: "#1e1e20", tik: "#55555b", yazi: "#adadb4",
  video: "#3a6299", gorsel: "#3a7f99", sahne: "#6f52a8", metin: "#a8527f", motion: "#996c3a", ses: "#2a7a5c", muzik: "#256a7a",
  vurgu: "#ff7a00", yapis: "#ffd400", kirmizi: "#ff6b6b",
};
const renk = (c: Klip) => (c.tur === "ses" ? (c.olay?.muzik ? R.muzik : R.ses) : R[c.tur]);

export interface CizimDurumu {
  k: KurguProps; medya: Record<string, string>; anahtar: string; w: number; h: number; x0: number; y0: number; pxSn: number;
  secim: Set<string>; zaman: number; giris: number | null; cikis: number | null;
  bulgular: { seviye: string; bas: number; bit: number }[]; yapis: number | null; lastik: { x1: number; y1: number; x2: number; y2: number } | null; hedefIz: string | null; birakma: number | null; imlec: number | null; kazancKlip: string | null;
}

const ETIKET: Record<number, number> = {};
const adimSec = (pxSn: number) => {
  if (ETIKET[pxSn]) return ETIKET[pxSn];
  const adaylar = [1 / 30, 2 / 30, 5 / 30, 10 / 30, 0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 1800];
  return adaylar.find((a) => a * pxSn >= 70) ?? 3600;
};

const etiket = (c: Klip, k: KurguProps) => {
  if (c.tur === "sahne") return c.sahne?.kind ? String(c.sahne.kind) + (c.sahne.title ? `: ${c.sahne.title}` : "") : "sahne";
  if (c.tur === "metin") return c.metin ?? "metin";
  const y = c.kaynak ? k.kaynaklar[c.kaynak]?.yol ?? "" : "";
  const dosya = y.slice(y.lastIndexOf("/") + 1).replace(/^[a-z]+:/, "");
  const ad = c.olay?.not ? `${c.olay.not}` : dosya || c.olay?.tur || c.tur;
  return c.ses_kapali ? `${ad} · ses ayrı` : ad;
};

const seritCiz = (g: CanvasRenderingContext2D, d: CizimDurumu, c: Klip, x: number, y: number, w: number, h: number) => {
  const yol = c.kaynak && d.k.kaynaklar[c.kaynak]?.yol;
  if (!yol) return;
  const s = seritAl(d.anahtar, yol);
  if (!s) return;
  const fw = s.img.naturalWidth / s.n, fh = s.img.naturalHeight;
  const tw = (fw / fh) * h;
  const solKirp = Math.max(0, -x), sagUc = Math.min(d.w, x + w);
  // Kareler klip başına hizalı: kaydırırken titremez.
  for (let i = Math.floor(solKirp / tw); x + i * tw < sagUc; i++) {
    const t = c.giris + ((i * tw) / d.pxSn) * c.hiz;
    const n = Math.min(s.n - 1, Math.floor(t / s.k));
    const px = x + i * tw;
    const gen = Math.min(tw, x + w - px);
    g.drawImage(s.img, n * fw, 0, fw * (gen / tw), fh, px, y, gen, h);
  }
};

const dalgaCiz = (g: CanvasRenderingContext2D, d: CizimDurumu, c: Klip, x: number, y: number, w: number, h: number, renkKod: string) => {
  const yol = c.kaynak && d.k.kaynaklar[c.kaynak]?.yol;
  if (!yol) return;
  const t = tepeAl(d.anahtar, yol);
  if (!t?.tepe.length) return;
  const orta = y + h / 2;
  const guc = Math.pow(10, c.ses.gain_db / 20);
  g.fillStyle = renkKod;
  const bas = Math.max(0, Math.floor(-x)), son = Math.min(d.w - x, w);
  const adim = (t.hz * c.hiz) / d.pxSn;
  g.beginPath();
  for (let px = bas; px < son; px++) {
    const a = Math.floor((c.giris + (px / d.pxSn) * c.hiz) * t.hz);
    let v = 0;
    for (let i = a, e = Math.max(a + 1, Math.ceil(a + adim)); i < e && i < t.tepe.length; i++) if (t.tepe[i] > v) v = t.tepe[i];
    const yuk = Math.max(0.5, Math.min(1, (v / 255) * Math.max(guc, 0.15)) * (h / 2));
    g.rect(x + px, orta - yuk, 1, yuk * 2);
  }
  g.fill();
};

const klipCiz = (g: CanvasRenderingContext2D, d: CizimDurumu, c: Klip, iz: Iz, y: number, h: number) => {
  const x = c.bas * d.pxSn - d.x0;
  const w = Math.max(1, c.sure * d.pxSn);
  if (x > d.w || x + w < 0) return;
  const secili = d.secim.has(c.id);
  g.save();
  g.beginPath();
  g.rect(x, y + 1, w, h - 2);
  g.clip();
  g.fillStyle = renk(c);
  g.globalAlpha = iz.gizli || iz.sessiz ? 0.4 : 1;
  g.fillRect(x, y + 1, w, h - 2);
  const genis = w > 34;
  if (genis && (c.tur === "video" || c.tur === "motion")) {
    const yolVar = c.kaynak && d.k.kaynaklar[c.kaynak]?.ses && c.tur === "video" && !c.ses_kapali;
    const sh = yolVar ? Math.round((h - 2) * 0.62) : h - 2;
    seritCiz(g, d, c, x, y + 1, w, sh);
    if (yolVar) { g.fillStyle = "#13261f"; g.fillRect(x, y + 1 + sh, w, h - 2 - sh); dalgaCiz(g, d, c, x, y + 1 + sh, w, h - 2 - sh, "#58c79c"); }
  }
  if (genis && c.tur === "ses") dalgaCiz(g, d, c, x, y + 1, w, h - 2, "rgba(255,255,255,0.42)");
  if (w > 26) {
    const yaz = etiket(c, d.k);
    g.font = "500 11px Outfit, system-ui, sans-serif";
    const gx = Math.max(x, 0) + 5;
    const uzun = g.measureText(yaz).width + 8;
    if (c.tur === "video" || c.tur === "motion") { g.fillStyle = "rgba(0,0,0,0.55)"; g.fillRect(gx - 3, y + 3, uzun, 15); }
    g.fillStyle = "#fff";
    g.textBaseline = "top";
    g.fillText(yaz, gx, y + 5, Math.max(10, x + w - gx - 3));
  }
  const bant = w > 26 ? sesBandi(d.k, c, y, h) : null;
  if (bant) {
    const kf = c.ses.kf ?? [];
    const ly = Math.round(kazancY(c.ses.gain_db, bant)) + 0.5;
    g.strokeStyle = !kf.length && c.ses.gain_db === 0 ? "rgba(255,255,255,0.55)" : "#ffd400";
    g.lineWidth = 1;
    g.beginPath();
    if (!kf.length) { g.moveTo(x, ly); g.lineTo(x + w, ly); }
    else for (let px = Math.max(0, -x); px <= Math.min(w, d.w - x); px += 3) {
      const yy = kazancY(kazancAni(c, px / d.pxSn), bant);
      if (px <= Math.max(0, -x)) g.moveTo(x + px, yy); else g.lineTo(x + px, yy);
    }
    g.stroke();
    g.fillStyle = "#ffd400";
    for (const f of kf) { const fx = x + f.t * d.pxSn, fy = kazancY(f.v, bant); g.fillRect(fx - 2.5, fy - 2.5, 5, 5); }
    if (d.kazancKlip === c.id) {
      const db = kf.length ? kazancAni(c, d.zaman - c.bas) : c.ses.gain_db;
      const yaz = `${db > 0 ? "+" : ""}${db.toFixed(1)} dB`;
      g.font = "600 11px 'JetBrains Mono', Consolas, monospace";
      g.fillStyle = "rgba(0,0,0,0.75)";
      g.fillRect(Math.max(x, 0) + 4, ly - 15, g.measureText(yaz).width + 8, 14);
      g.fillStyle = "#ffd400";
      g.textBaseline = "top";
      g.fillText(yaz, Math.max(x, 0) + 8, ly - 14);
    }
  }
  if (c.bag && w > 30) { g.fillStyle = "#ffd400"; g.fillRect(x + w - 8, y + 4, 4, 4); }
  if (iz.kilit) {
    g.strokeStyle = "rgba(0,0,0,0.35)";
    g.lineWidth = 2;
    g.beginPath();
    for (let o = x - h; o < x + w; o += 10) { g.moveTo(o, y + h); g.lineTo(o + h, y); }
    g.stroke();
  }
  g.restore();
  const eksik = !!c.kaynak && !d.medya[c.kaynak];
  if (eksik) {
    g.fillStyle = "rgba(160,30,40,0.82)";
    g.fillRect(x, y + 1, w, h - 2);
    if (w > 60) { g.fillStyle = "#fff"; g.font = "600 11px Outfit, system-ui, sans-serif"; g.textBaseline = "top"; g.fillText("Dosya yok", Math.max(x, 0) + 5, y + 5, w - 8); }
  }
  g.lineWidth = secili ? 2 : 1;
  g.strokeStyle = secili ? R.vurgu : "rgba(0,0,0,0.6)";
  g.strokeRect(x + (secili ? 1 : 0.5), y + (secili ? 2 : 1.5), Math.max(1, w - (secili ? 2 : 1)), h - (secili ? 4 : 3));
};

const cetvelCiz = (g: CanvasRenderingContext2D, d: CizimDurumu) => {
  g.fillStyle = R.cetvel;
  g.fillRect(0, 0, d.w, CETVEL);
  const adim = adimSec(d.pxSn);
  const ara = adim / 5;
  g.font = "10px 'JetBrains Mono', Consolas, monospace";
  g.textBaseline = "top";
  g.strokeStyle = R.tik;
  g.fillStyle = R.yazi;
  g.lineWidth = 1;
  const t0 = Math.floor(d.x0 / d.pxSn / adim) * adim;
  g.beginPath();
  for (let t = t0; t * d.pxSn - d.x0 < d.w; t += ara) {
    const x = Math.round(t * d.pxSn - d.x0) + 0.5;
    const ana = Math.abs(t / adim - Math.round(t / adim)) < 1e-6;
    g.moveTo(x, CETVEL);
    g.lineTo(x, CETVEL - (ana ? 10 : 4));
    if (ana) g.fillText(zamanKodu(t, d.k.sekans.fps), x + 3, 3);
  }
  g.stroke();
};

export const ciz = (g: CanvasRenderingContext2D, d: CizimDurumu) => {
  g.fillStyle = R.zemin;
  g.fillRect(0, 0, d.w, d.h);

  let y = CETVEL - d.y0;
  for (const iz of d.k.izler) {
    const h = izYuksekligi(iz);
    if (y + h > CETVEL && y < d.h) {
      g.fillStyle = iz.tur === "video" ? R.satir : R.satirSes;
      g.fillRect(0, y, d.w, h);
      if (d.hedefIz === iz.id) { g.fillStyle = "rgba(255,122,0,0.12)"; g.fillRect(0, y, d.w, h); }
      for (const c of d.k.klipler) if (c.iz === iz.id) klipCiz(g, d, c, iz, y, h);
      g.fillStyle = R.cizgi;
      g.fillRect(0, y + h - 1, d.w, 1);
    }
    y += h;
  }

  // Giriş-çıkış aralığı
  if (d.giris !== null || d.cikis !== null) {
    const a = (d.giris ?? 0) * d.pxSn - d.x0, b = (d.cikis ?? d.w / d.pxSn + d.x0 / d.pxSn) * d.pxSn - d.x0;
    g.fillStyle = "rgba(255,255,255,0.06)";
    g.fillRect(a, CETVEL, b - a, d.h);
  }

  cetvelCiz(g, d);

  if (d.giris !== null || d.cikis !== null) {
    const a = (d.giris ?? 0) * d.pxSn - d.x0, b = (d.cikis ?? d.w / d.pxSn + d.x0 / d.pxSn) * d.pxSn - d.x0;
    g.fillStyle = "rgba(255,122,0,0.35)";
    g.fillRect(a, CETVEL - 5, b - a, 5);
  }
  for (const m of d.k.isaretler ?? []) {
    const x = m.t * d.pxSn - d.x0;
    if (x < -8 || x > d.w + 8) continue;
    g.fillStyle = "#5ccf8a";
    g.beginPath(); g.moveTo(x - 5, 12); g.lineTo(x + 5, 12); g.lineTo(x + 5, 19); g.lineTo(x, 25); g.lineTo(x - 5, 19); g.closePath(); g.fill();
  }

  for (const b of d.bulgular) {
    const a = b.bas * d.pxSn - d.x0, e = Math.max(a + 4, b.bit * d.pxSn - d.x0);
    if (e < 0 || a > d.w) continue;
    g.fillStyle = b.seviye === "P0" ? R.kirmizi : b.seviye === "P1" ? "#e8b84a" : "#8b8b93";
    g.fillRect(a, CETVEL - 3, e - a, 3);
  }

  if (d.imlec !== null) { g.fillStyle = "rgba(255,255,255,0.55)"; g.fillRect(Math.round(d.imlec), CETVEL, 1, d.h); }
  if (d.birakma !== null) { g.fillStyle = R.vurgu; g.fillRect(Math.round(d.birakma * d.pxSn - d.x0), 0, 2, d.h); }
  if (d.yapis !== null) { g.fillStyle = R.yapis; g.fillRect(Math.round(d.yapis * d.pxSn - d.x0), 0, 1, d.h); }
  if (d.lastik) {
    const { x1, y1, x2, y2 } = d.lastik;
    g.fillStyle = "rgba(255,122,0,0.12)";
    g.strokeStyle = R.vurgu;
    g.lineWidth = 1;
    g.fillRect(Math.min(x1, x2), Math.min(y1, y2), Math.abs(x2 - x1), Math.abs(y2 - y1));
    g.strokeRect(Math.min(x1, x2) + 0.5, Math.min(y1, y2) + 0.5, Math.abs(x2 - x1), Math.abs(y2 - y1));
  }

  // Oynatma kafası
  const px = Math.round(d.zaman * d.pxSn - d.x0);
  if (px > -8 && px < d.w + 8) {
    g.fillStyle = R.vurgu;
    g.fillRect(px, 0, 1, d.h);
    g.beginPath(); g.moveTo(px - 6, 0); g.lineTo(px + 7, 0); g.lineTo(px + 7, 10); g.lineTo(px + 0.5, 17); g.lineTo(px - 6, 10); g.closePath(); g.fill();
  }
};
