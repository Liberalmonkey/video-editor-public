// src/vedit/schemas.py Kurgu ile aynı şekil. Doğrulama arka uçtadır.
export interface KF { t: number; v: number; ease: "dogrusal" | "yumusak" | "giris" | "cikis" | "tut" | "geri" | "expo" | "yay" }
export interface Kelime { w: string; s: number; e: number }
export interface Kaynak { yol: string; sure: number; w?: number | null; h?: number | null; ses: boolean }
export interface Iz { id: string; tur: "video" | "ses"; ad: string; kilit: boolean; sessiz: boolean; gizli: boolean; gain_db: number }
export type Yon = "sol" | "sag" | "yukari" | "asagi";
// ADR 0045: sil, kay, saat, iris, kirbac, isik, piksel (+ zoom_kirbac, film_yanigi, bolunme, bozulma, yirtma) orta noktası kesimde olan geçişlerdir (gecisler.tsx).
export interface Gecis { tur: "capraz" | "kararma" | "kaydir" | "zoom" | "it" | "savur" | "bulanik" | "sil" | "kay" | "saat" | "iris" | "kirbac" | "isik" | "piksel" | "zoom_kirbac" | "film_yanigi" | "bolunme" | "bozulma" | "yirtma"; sure: number; yon?: Yon }
// Konuşmacı punch nesnesi: olcek hedef çarpan, sure tutma (sn), x/y odak 0..1 (ADR 0033). Sayı biçimi eskisi gibi.
export interface Punch { t: number; olcek?: number; sure?: number; x?: number | null; y?: number | null }
// Hazır efekt: ad ve parametreleri (studio/remotion/hazirEfekt.json); t klibin başından sn.
export interface Hazir { ad: string; t?: number; sure?: number; ses?: boolean; [k: string]: any }
// metin_stil: tip yoksa düz metin (font/boyut/renk). Motion türleri ADR 0031; konum, hedef ve kutu 0..1 oranıdır.
export type MetinTipi = "anahtar" | "altbant" | "etiket" | "cagri" | "daktilo" | "sayac" | "ilerleme" | "bolum" | "vurgu";
export interface MetinStil {
  tip?: MetinTipi; font?: string; boyut?: number; renk?: string; vurgu?: string; arka?: string; buyuk?: boolean;
  konum?: { x?: number; y?: number }; hedef?: { x: number; y: number }; kutu?: { x: number; y: number; w: number; h: number };
  bicim?: "kutu" | "daire" | "alt_cizgi"; kalinlik?: number; hiz?: number;
  deger?: number; baslangic?: number; onek?: string; sonek?: string; ondalik?: number; adim?: number; toplam?: number; numara?: string;
  [k: string]: any;
}
export interface Klip {
  id: string; iz: string; bas: number; sure: number;
  tur: "video" | "gorsel" | "metin" | "sahne" | "motion" | "ses";
  kaynak?: string | null; giris: number; hiz: number; bag?: string | null;
  ses_kapali?: boolean; // ses ayrı klipte: görüntü sessiz
  konusmaci: boolean; zoom: number; punches: (number | Punch)[];
  donus: { x: KF[]; y: KF[]; olcek: KF[]; opaklik: KF[]; aci?: KF[]; capa?: { x: number; y: number } | null; anim: ("x" | "y" | "olcek" | "opaklik" | "aci")[] };
  efekt: { parlaklik: number; kontrast: number; doygunluk: number; bulanik: number; bulanik_kf?: KF[]; parlaklik_kf?: KF[]; kirp?: Record<string, number> | null };
  hazir?: Hazir[];
  ses: { gain_db: number; fade_in: number; fade_out: number; duck: boolean; temizle?: boolean; kf?: KF[] };
  gecis_giris?: Gecis | null; gecis_cikis?: Gecis | null;
  sahne?: Record<string, any> | null; metin?: string | null; metin_stil?: MetinStil | null; olay?: Record<string, any> | null;
  sablon?: { ad: string; param?: Record<string, any>; tema?: string } | null;  // motion şablonu (ADR 0036)
  hf?: { ad: string; param?: Record<string, any>; tema?: string } | null;  // HyperFrames kompozisyonu, saydam webm (ADR 0050)
  // Native motion bileşeni (ADR 0045) ve kelime çapası (ADR 0048).
  bilesen?: { ad: string; param?: Record<string, any>; yer?: "oto" | "ust" | "orta" | "alt" | "sol" | "sag" | "hedef" | "tam"; hedef?: { x: number; y: number } | null; hero?: boolean | null; odak_karart?: boolean | null } | null;
  capa?: { kaynak: string; kelime?: number | null; t?: number | null; once_kare?: number } | null;
}
// Kare koordinatı oranı (0..1). vedit kurgu_reframe'den yazar: [bas, son) aralığında görünen yüzler.
export interface YuzAraligi { bas: number; son: number; kutular: { x: number; y: number; w: number; h: number }[] }
export interface AltyaziStil { font: string; agirlik?: number; boyut: number; renk: string; aktif_renk: string; kontur: number; kontur_renk: string; kip: "kelime" | "tam"; en_kelime: number; en_karakter: number; konum?: number | null; dosya?: string | null }
export interface Altyazi { acik: boolean; iz: string; stil?: AltyaziStil | null }
export interface KurguProps {
  sekans: { w: number; h: number; fps: number };
  motor?: "oto" | "hf" | "remotion"; // ADR 0051: render ve önizleme motoru (oto: HyperFrames yapabiliyorsa o)
  kaynaklar: Record<string, Kaynak>;
  kelimeler?: Record<string, Kelime[]>;
  izler: Iz[];
  klipler: Klip[];
  altyazi: Altyazi;
  isaretler?: { t: number; ad: string }[];
  motion_tema?: string;
  rev?: number;
  words?: Kelime[];              // render: hazır izdüşüm
  bitis?: number;
  medya?: Record<string, string>; // önizleme: kaynak id → proxy adresi
  onizleme?: boolean;
  bolgeler?: { yuzler?: YuzAraligi[] }; // render: vedit yazar (ADR 0045); yoksa yalnız güvenli alan ve altyazı
  metreBagla?: (ctx: AudioContext, ana: GainNode) => () => void; // önizleme: ana ses düğümüne metre takar
  [k: string]: unknown;
}
