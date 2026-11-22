// Dalga formu ve film şeridi: kaynak başına bir kez istenir, gelince timeline yeniden çizilir.
import { sor } from "../api";

export interface Tepe { hz: number; tepe: number[] }
export interface Serit { n: number; k: number; img: HTMLImageElement }

const tepeler = new Map<string, Tepe | null>();
const seritler = new Map<string, Serit | null>();
let degisti = () => {};
export const degisinceHaberVer = (f: () => void) => { degisti = f; };
export const temizle = () => { tepeler.clear(); seritler.clear(); };

// Geçici hata ya da henüz hazır olmayan dosya: anahtar silinir, sonraki çizimde yeniden istenir. Bekleme istek fırtınasını önler.
const sonraDene = (m: Map<string, unknown>, yol: string) => { setTimeout(() => { if (m.get(yol) === null) { m.delete(yol); degisti(); } }, 5000); };

export const tepeAl = (anahtar: string, yol: string): Tepe | null => {
  if (!tepeler.has(yol)) {
    tepeler.set(yol, null);
    fetch(`/api/peak/${anahtar}?${sor({ yol })}`).then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((v) => { if (v) { tepeler.set(yol, v); degisti(); } }).catch(() => sonraDene(tepeler, yol));
  }
  return tepeler.get(yol) ?? null;
};

export const seritAl = (anahtar: string, yol: string): Serit | null => {
  if (!seritler.has(yol)) {
    seritler.set(yol, null);
    fetch(`/api/serit/${anahtar}?${sor({ yol })}`).then((r) => (r.ok ? r.json() : Promise.reject(r.status))).then((v) => {
      if (!v?.n) return;
      const img = new Image();
      img.onload = () => { seritler.set(yol, { n: v.n, k: v.k, img }); degisti(); };
      img.src = v.url;
    }).catch(() => sonraDene(seritler, yol));
  }
  return seritler.get(yol) ?? null;
};
