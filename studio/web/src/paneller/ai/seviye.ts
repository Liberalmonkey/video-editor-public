// Swarm tipleri ve ajan tavanı. WHY: bkz. wiki/decisions/0059-swarm-edit.md
// Seviye artık ajan tavanıdır (editör + kalite kontrol); sayıyı, dağılımı ve modeli orkestratör seçer.
// Tavanlar sunucudaki ekip_sema.EN_COK ile aynıdır; test ikisini birbirine bağlar.

export const SEVIYELER = ["low", "medium", "high", "xhigh", "max"] as const;
export type Seviye = (typeof SEVIYELER)[number];
export const EN_COK: Record<Seviye, number> = { low: 3, medium: 6, high: 9, xhigh: 12, max: 15 };
export const EDITOR_EN_COK = 10, KK_EN_COK = 5;
// En küçük geçerli ekip 3 (E1 kurgu + bir editör + bir QC), en büyük 15; sunucu ekip_sema.EkipAyar.en_cok ile aynı.
export const EN_AZ = 3, EN_COK_SINIR = 15;

export const GRUPLAR = ["orkestrator", "editor", "kk"] as const;
export type Grup = (typeof GRUPLAR)[number];
export const GRUP_ADI: Record<Grup, string> = { orkestrator: "Orkestratör", editor: "Editörler", kk: "Kalite kontrol" };

export interface Slot { motor: string; model?: string | null; seviye?: string | null; yedek_motor?: string | null; yedek_model?: string | null; yedek_seviye?: string | null }
export interface EkipAyar {
  ad: string; ekip_seviye: Seviye; gruplar: Record<Grup, Slot>; ezme: Record<string, Slot>;
  eszamanlilik?: number | null; motion: string; stil?: string | null;
  hizli?: boolean; // ADR 0054, 0058: plan çağrısı yok, 2 editör + dilim başına QC
  en_cok?: number | null; // ADR 0059: swarm ajan tavanı; yoksa seviyeden
}
export type SlotDurumAdi = "bekliyor" | "calisiyor" | "bitti" | "hata" | "yedek" | "atlandi";
export interface SlotDurum { durum: SlotDurumAdi; rol?: string; aralik?: [number, number] | null; motor: string; model?: string | null; sure?: number | null; token?: number | null; tahmini?: boolean }
export type KapiDurumAdi = "bekliyor" | "acik" | "gecti" | "kaldi";
export interface Kapi { id: string; ad: string; durum: KapiDurumAdi; not: string }
export interface EkipDurum {
  yok?: boolean; seviye: Seviye; asama: string; bitti: boolean; dagitim?: "orkestrator" | "varsayilan" | "hizli" | null; en_cok?: number | null;
  acik: { P0: number; P1: number; P2: number };
  kurallar?: { atanan: number; uyum_eksik: number; yeni: number; tekrar: number; dogrulanan: number; dogrulanamayan: number };
  kapilar: Kapi[]; slotlar: Record<string, SlotDurum>;
}

export const tavan = (a: Pick<EkipAyar, "en_cok" | "ekip_seviye">) => a.en_cok ?? EN_COK[a.ekip_seviye] ?? 6;
// Tavanın izin verdiği en çok slot (ezme çipleri): her ekipte en az bir QC, en az bir editör.
export const editorSlotlari = (t: number) => Array.from({ length: Math.min(EDITOR_EN_COK, Math.max(2, t - 1)) }, (_, i) => `E${i + 1}`);
export const kkSlotlari = (t: number) => Array.from({ length: Math.min(KK_EN_COK, Math.max(1, t - 2)) }, (_, i) => `K${i + 1}`);
export const grup = (slot: string): Grup => (slot === "O" ? "orkestrator" : slot.startsWith("E") ? "editor" : "kk");
export const slotAyari = (a: EkipAyar, slot: string): Slot => a.ezme?.[slot] ?? a.gruplar[grup(slot)];
// Kurulu olması gereken motorlar: grupların ve ezmelerin (hızlıda orkestratör çağrılmaz). Sayı plana göre değiştiği için slota bakılmaz.
// Sunucu (studio/ekip.py dogrula) ile aynı kural: birincil ve yedek motorlar kurulu olmalı; hızlıda orkestratör çağrılmaz.
export const gerekenMotorlar = (a: EkipAyar) => {
  const sl = [...Object.entries(a.gruplar).filter(([g]) => !(a.hizli && g === "orkestrator")).map(([, v]) => v),
    ...Object.entries(a.ezme ?? {}).filter(([s]) => !(a.hizli && s === "O")).map(([, v]) => v)];
  return [...new Set(sl.flatMap((v) => [v.motor, v.yedek_motor]).filter((m): m is string => !!m))];
};
export const suruOzet = (a: EkipAyar) => (a.hizli ? "2 editör · dilim başına kalite kontrol · orkestratörsüz"
  : `en çok ${tavan(a)} ajan · sayıyı ve modelleri orkestratör seçer`);

// Slot sırası: O, E1..E10, K1..K5 (sözlük sırası E10'u E2'den önce koyardı).
export const slotSirasi = (a: string, b: string) => {
  const g = (x: string) => (x === "O" ? 0 : x[0] === "E" ? 1 : 2);
  return g(a) - g(b) || Number(a.slice(1) || 0) - Number(b.slice(1) || 0);
};

export const sn = (v: number) => v.toLocaleString("tr", { maximumFractionDigits: 1 });
export const tokenEtiketi = (t?: number | null, tahmini?: boolean) => (t ? `${tahmini ? "~" : ""}${t >= 1000 ? `${Math.round(t / 1000)}k` : t} tok` : "");
