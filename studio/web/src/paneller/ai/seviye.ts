// Ekip v3 tipleri ve seviye tablosu. WHY: bkz. wiki/decisions/0053-seviyeli-ekip-orkestrator.md
// Sayılar sunucudaki ekip_sema.SEVIYE ile aynıdır; test ikisini birbirine bağlar.

export const SEVIYELER = ["low", "medium", "high", "xhigh", "max"] as const;
export type Seviye = (typeof SEVIYELER)[number];
export const SEVIYE: Record<Seviye, { editor: number; kk: number }> = {
  low: { editor: 2, kk: 1 }, medium: { editor: 4, kk: 2 }, high: { editor: 6, kk: 3 }, xhigh: { editor: 8, kk: 4 }, max: { editor: 10, kk: 5 },
};
export const SEVIYE_ADI: Record<Seviye, string> = { low: "Low", medium: "Medium", high: "High", xhigh: "XHigh", max: "Max" };

export const GRUPLAR = ["orkestrator", "editor", "kk"] as const;
export type Grup = (typeof GRUPLAR)[number];
export const GRUP_ADI: Record<Grup, string> = { orkestrator: "Orkestratör", editor: "Editörler", kk: "Kalite kontrol" };

export interface Slot { motor: string; model?: string | null; seviye?: string | null; yedek_motor?: string | null; yedek_model?: string | null; yedek_seviye?: string | null }
export interface EkipAyar {
  ad: string; ekip_seviye: Seviye; gruplar: Record<Grup, Slot>; ezme: Record<string, Slot>;
  eszamanlilik?: number | null; motion: string; stil?: string | null;
  hizli?: boolean; // ADR 0054: low, orkestratörsüz, render yalnız gerekince
}
export type SlotDurumAdi = "bekliyor" | "calisiyor" | "bitti" | "hata" | "yedek" | "atlandi";
export interface SlotDurum { durum: SlotDurumAdi; rol?: string; aralik?: [number, number] | null; motor: string; model?: string | null; sure?: number | null; token?: number | null; tahmini?: boolean }
export type KapiDurumAdi = "bekliyor" | "acik" | "gecti" | "kaldi";
export interface Kapi { id: string; ad: string; durum: KapiDurumAdi; not: string }
export interface EkipDurum {
  yok?: boolean; seviye: Seviye; asama: string; bitti: boolean; dagitim?: "orkestrator" | "varsayilan" | "hizli" | null;
  acik: { P0: number; P1: number; P2: number };
  kurallar?: { atanan: number; uyum_eksik: number; yeni: number; tekrar: number; dogrulanan: number; dogrulanamayan: number };
  kapilar: Kapi[]; slotlar: Record<string, SlotDurum>;
}

export const editorSlotlari = (s: Seviye) => Array.from({ length: SEVIYE[s].editor }, (_, i) => `E${i + 1}`);
export const kkSlotlari = (s: Seviye) => Array.from({ length: SEVIYE[s].kk }, (_, i) => `K${i + 1}`);
export const slotlar = (s: Seviye) => ["O", ...editorSlotlari(s), ...kkSlotlari(s)];
export const grup = (slot: string): Grup => (slot === "O" ? "orkestrator" : slot.startsWith("E") ? "editor" : "kk");
export const slotAyari = (a: EkipAyar, slot: string): Slot => a.ezme?.[slot] ?? a.gruplar[grup(slot)];
export const seviyeOzet = (s: Seviye) => `${SEVIYE[s].editor} editör · ${SEVIYE[s].kk} kalite kontrol · orkestratör`;
export const HIZLI_OZET = `${SEVIYE.low.editor} editör · ${SEVIYE.low.kk} kalite kontrol · orkestratörsüz`;

// Slot sırası: O, E1..E10, K1..K5 (sözlük sırası E10'u E2'den önce koyardı).
export const slotSirasi = (a: string, b: string) => {
  const g = (x: string) => (x === "O" ? 0 : x[0] === "E" ? 1 : 2);
  return g(a) - g(b) || Number(a.slice(1) || 0) - Number(b.slice(1) || 0);
};

export const sn = (v: number) => v.toLocaleString("tr", { maximumFractionDigits: 1 });
export const tokenEtiketi = (t?: number | null, tahmini?: boolean) => (t ? `${tahmini ? "~" : ""}${t >= 1000 ? `${Math.round(t / 1000)}k` : t} tok` : "");
