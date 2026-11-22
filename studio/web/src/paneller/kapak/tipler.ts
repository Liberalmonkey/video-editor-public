// Kapak alanının veri tipleri: /api/kapak/{s}/{a} (kapak.durum) ve /master (kapak.master). WHY: bkz. wiki/decisions/0052-kapak-is-akisi-v2.md

// Kırpma alanı, tuval yüzdesi [sol, üst, sağ, alt]. ic: başlık içinde kalır; dis: başlık girmez. Kaynak: kapak.GUVENLI.
export interface Alan { ad: string; kutu: [number, number, number, number]; tur: "ic" | "dis" }
export interface Yazi { satir1: string; satir2: string; vurgu: string; yerlesim: string; olcek: number; karart: boolean; kutu: boolean; kalip: string; stil: string; ek: string }
export interface Olcum { kelime: number; harf: number | null; kontrast: number | null; notlar: string[]; gecti: boolean }
export interface Aday extends Yazi {
  n: number; yol: string; aci: string | null; v: number; olcum: Olcum | null; puan: number | null; elestiri: string;
  ebeveyn: number | null; zemin_kaynagi: string; duzeltme: string; kare: number | null; video: string | null;
}
// Yapılı brief (kapak_prompt.BRIEF_ALANLARI + yazı). govde: agy'ye gidecek sahne tarifi (sunucu hesaplar).
export interface Brief {
  sahne?: string; ifade?: string; kompozisyon?: string; isik?: string; palet?: string; yazi_alani?: string; prompt?: string;
  satir1?: string; satir2?: string; vurgu?: string; aci?: string; kalip?: string; ek?: string; stil?: string; not_tr?: string;
  kare?: number; video?: string; govde?: string;
}
export interface Video { yol: string; ad: string; tur: "girdi" | "kurgu" | "teslim" }
export interface Referans { tur: "yuz" | "stil"; ad: string; kok: string; yol: string; silinir: boolean }
export interface GorselMotor { model: string | null; acilis?: string | null; kapali?: boolean }
export interface Hedef { id: string; ad: string; nerede: string; yazi: string }
export interface Durum {
  platform: string; oran: string; w: number; h: number; en_cok: number;
  yerlesimler: string[]; guvenli: Alan[];
  kaliplar: string[]; kesitli: string[]; logo: number;
  stiller: { ad: string; aciklama: string; kutu: boolean }[];
  adaylar: Aday[];
  videolar: Video[]; video: string | null;
  kareler: { n: number; yol: string; el: boolean }[];
  referanslar: Referans[];
  brief: Brief[];
  oneri: { fikir?: string; briefler: Brief[] } | null;
  secim: { n: number; dosya: string; eski?: boolean } | null;
  gorsel_motor: GorselMotor; hedefler: Hedef[];
}
export interface MasterHedef { hedef: string; ad: string; nerede: string; yazili: boolean; prompt: string; ayar: [string, string][]; notlar: string[] }
export interface Master {
  kaynak: string; md: string;
  hedefler: Record<string, { yazili: MasterHedef; bos: MasterHedef }>;
  ekler: { no: number; rol: string; dosya: string; kok: string | null; yol: string | null }[];
}
