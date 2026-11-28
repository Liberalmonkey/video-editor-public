import { describe, expect, it, vi } from "vitest";
import type { KurguProps } from "../../../remotion/tipler";

const seritMock = vi.fn();
vi.mock("./gorselOnbellek", () => ({
  seritAl: (...a: unknown[]) => seritMock(...a),
  tepeAl: () => null,
}));

import { ciz, type CizimDurumu } from "./ciz";

const sahteCtx = () => {
  const drawImage = vi.fn();
  const g = {
    fillStyle: "", strokeStyle: "", lineWidth: 1, font: "", textBaseline: "top", globalAlpha: 1,
    fillRect: vi.fn(), strokeRect: vi.fn(), beginPath: vi.fn(), rect: vi.fn(), clip: vi.fn(),
    save: vi.fn(), restore: vi.fn(), moveTo: vi.fn(), lineTo: vi.fn(), stroke: vi.fn(),
    closePath: vi.fn(), fill: vi.fn(), fillText: vi.fn(), measureText: () => ({ width: 20 }),
    drawImage,
  } as unknown as CanvasRenderingContext2D;
  return { g, drawImage };
};

const durum = (): CizimDurumu => {
  const k: KurguProps = {
    sekans: { w: 1080, h: 1920, fps: 30 },
    kaynaklar: { s1: { yol: "inputs:a.mp4", sure: 10, ses: false } },
    izler: [{ id: "V1", tur: "video", ad: "V1", kilit: false, sessiz: false, gizli: false, gain_db: 0 }],
    klipler: [{
      id: "c1", iz: "V1", bas: 0, sure: 5, tur: "video", kaynak: "s1", giris: 0, hiz: 1, konusmaci: false, zoom: 1, punches: [],
      donus: { x: [], y: [], olcek: [], opaklik: [], anim: [] },
      efekt: { parlaklik: 1, kontrast: 1, doygunluk: 1, bulanik: 0 },
      ses: { gain_db: 0, fade_in: 0, fade_out: 0, duck: false },
    }],
    altyazi: { acik: false, iz: "V1" },
  };
  return {
    k, medya: { s1: "/m/s1.mp4" }, anahtar: "s/p", w: 600, h: 200, x0: 0, y0: 0, pxSn: 30,
    secim: new Set(), zaman: 0, giris: null, cikis: null, bulgular: [], yapis: null,
    lastik: null, hedefIz: null, birakma: null, imlec: null, kazancKlip: null,
  };
};

describe("ciz seritCiz sonsuz döngü koruması (bulgu 11)", () => {
  it("bozuk görsel boyutları, s.n<=0 veya s.k<=0 iken sonsuz döngüye girmeden çıkar", () => {
    const bozuklar = [
      { n: 0, k: 1, img: { naturalWidth: 100, naturalHeight: 50 } },
      { n: -2, k: 1, img: { naturalWidth: 100, naturalHeight: 50 } },
      { n: 4, k: 0, img: { naturalWidth: 100, naturalHeight: 50 } },
      { n: 4, k: 1, img: { naturalWidth: 0, naturalHeight: 50 } },
      { n: 4, k: 1, img: { naturalWidth: 100, naturalHeight: 0 } },
    ];
    for (const s of bozuklar) {
      seritMock.mockReturnValue(s);
      const { g, drawImage } = sahteCtx();
      ciz(g, durum());
      expect(drawImage).not.toHaveBeenCalled();
    }
  });
});
