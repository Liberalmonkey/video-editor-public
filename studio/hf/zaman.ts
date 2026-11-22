// Kurgu zaman payları: derleyici (klip aralığı) ve çalışma zamanı (dönüşüm) aynı kuralı kullanır.
// WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Kurgu.tsx'teki kuyrukPayi/onPayi ile birebir (ADR 0045).
import type { Gecis, Klip, KurguProps } from "../remotion/tipler";
import { bezier } from "./bezier";

// Orta noktası kesimde olan geçişler (gecisler.tsx ORTA ile aynı küme).
export const ORTA = new Set(["sil", "kay", "saat", "iris", "kirbac", "isik", "piksel", "zoom_kirbac", "film_yanigi", "bolunme", "bozulma", "yirtma"]);
export const ortaMi = (g: Gecis | null | undefined): boolean => !!g && ORTA.has(g.tur);

// Çapraz geçişte önceki klip kuyruğu altta sürer; orta noktalı geçişte yarısı.
export const kuyrukPayi = (p: Pick<KurguProps, "kaynaklar">, k: Klip, sonra: Klip | undefined): number => {
  const g = sonra?.gecis_giris;
  if (!g || g.tur === "kararma" || Math.abs(k.bas + k.sure - sonra!.bas) > 1e-3) return 0;
  const istek = ortaMi(g) ? g.sure / 2 : g.sure;
  const s = k.kaynak ? p.kaynaklar[k.kaynak]?.sure : 0;
  return s && s > 0 ? Math.max(0, Math.min(istek, (s - k.giris) / k.hiz - k.sure)) : istek;
};

// Orta noktalı geçişte giren klibin ön payı.
export const onPayi = (k: Klip): number =>
  !ortaMi(k.gecis_giris) ? 0 : k.tur === "gorsel" ? k.gecis_giris!.sure / 2 : Math.max(0, Math.min(k.gecis_giris!.sure / 2, k.giris / k.hiz));

export const dbGuc = (db: number) => Math.pow(10, db / 20);

// SplitReel layoutP birebir: bölünmüş sahneye geçişte 10 karede 0'dan 1'e (panel iner), tam ekrana dönüşte 1'den 0'a.
export const STAGE_H = 998;
export const CAP_SPLIT_Y = 1066;
const DUZEN = bezier(0.65, 0, 0.35, 1);
export interface DuzenSahne { layout?: string | null; start: number }
export const layoutP = (frame: number, fps: number, scenes: DuzenSahne[]): number => {
  let prev = 0, p = 0;
  for (const s of scenes) {
    const target = s.layout === "split" ? 1 : 0;
    const st = Math.round(s.start * fps);
    if (frame < st) break;
    const k = DUZEN(Math.min(1, Math.max(0, (frame - st) / 10)));
    p = prev + (target - prev) * k;
    prev = target;
  }
  return p;
};
// Yatayda sahne sütununun genişliği (Kurgu.tsx yatayDuzen).
export const yatayG = (h: number) => Math.round(1080 * (h / STAGE_H));

// SplitReel temaUygula'daki T.bg: koyu zeminli stilde stilin zemini, açık zeminli stilde yazı rengi.
const lum = (h: string) => {
  const n = parseInt(h.slice(1), 16);
  const [r, g, b] = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
export const sahneZemin = (renk?: Record<string, string> | null): string =>
  !renk?.zemin ? "#0B0D12" : lum(renk.zemin) < 0.18 ? renk.zemin : renk.yazi;
