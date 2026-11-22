// Native motion bileşen sözleşmesi (ADR 0045). Her bileşen bu tiplere karşı yazılır; aile kartları bu dosyayı değiştirmez.
import type React from "react";
import type { z } from "zod";

export type MotionTur = "ikon" | "cizim" | "kart" | "altbant" | "cta" | "veri" | "cerceve" | "parcacik" | "zemin" | "gecis" | "tipografi";
export type Yer = "ust" | "orta" | "alt" | "sol" | "sag" | "hedef" | "tam";
export type EnBoy = "9:16" | "16:9" | "1:1" | "4:5";

// meta.json biçimi. library/motion/native/sema.json bunun kopyasını Python'a taşır.
export interface MotionMeta {
  ad: string;                 // "<aile>/<ad>", kayıt anahtarı
  tur: MotionTur;
  etiketler: string[];
  ne_zaman: string;           // ai-edit için tek cümle: hangi sözde, hangi anlamda
  sure: { min: number; varsayilan: number; max: number }; // sn
  giris_sn: number;           // 0.3-0.5 (ikon daha kısa olabilir)
  cikis_sn: number;           // girişten kısa
  hero: boolean;              // ekranda aynı anda tek hero
  en_boy: EnBoy[];
  yer: Yer[];                 // tercih sırası; yerleşim ilk çakışmasız adayı seçer
  boyut: { w: number; h: number }; // kısa kenarın oranı (1080 dikeyde w 0.3 → 324 px)
  en_kucuk_px: number;        // kısa kenarı 1080 olan karede en küçük kutu kenarı
  kaynak?: { ad: string; url: string; lisans: string } | null; // geometri ya da fikir alındıysa
}

export interface Kutu { x: number; y: number; w: number; h: number } // px
export interface Nokta { x: number; y: number }                    // px

// Bileşenin kaçınacağı bölgeler, o karede (Kurgu.tsx sağlar; vedit yüz kutusunu kurgu_reframe'den yazar).
export interface Bolgeler {
  guvenli: Kutu;     // en-boya göre güvenli alan
  altyazi: Kutu | null;
  yuzler: Kutu[];    // göz ve ağız dahil yüz kutusu, payıyla
  platform: Kutu[];  // 9:16 platform arayüzü (üst bar, alt açıklama, sağ düğmeler)
}

export interface BilesenProps<P> {
  param: P;
  kutu: Kutu;          // yerleşimin seçtiği alan (px); bileşen bunun içine çizer
  hedef?: Nokta | null; // call-out ve çizimde işaret edilen nokta (px, kare koordinatı)
  sureKare: number;     // klibin kare cinsinden süresi
  u: number;            // ölçek: kısa kenar / 1080
}

export interface Tanim<S extends z.ZodType = z.ZodType> {
  meta: MotionMeta;
  sema: S;
  Bilesen: React.FC<BilesenProps<z.infer<S>>>;
}

// Tip çıkarımı için: export default tanimla({ meta, sema, Bilesen })
export const tanimla = <S extends z.ZodType>(t: Tanim<S>): Tanim<S> => t;
