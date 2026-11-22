// Kapak alanının saf yardımcıları (vitest: yardimci.test.ts). WHY: bkz. wiki/decisions/0027-kapak-sayfasi.md, 0052-kapak-is-akisi-v2.md
import type { Alan, Durum, GorselMotor, Yazi } from "./tipler";

export const VARSAYILAN_PLATFORM: Record<string, string> = { instagram: "instagram", "youtube-animasyon": "youtube" };
export const YERLESIM_ADI: Record<string, string> = { sol: "Sol", sag: "Sağ", ust: "Üst", alt: "Alt" };
// Kalıp: ad, satırların ve ek sözün o kalıptaki işi (boş ek: kalıp ek söz kullanmaz). Kaynak: kapak.KALIP, sablon.html.
export const KALIP: Record<string, { ad: string; ek: string; ipucu: string }> = {
  klasik: { ad: "Klasik", ek: "", ipucu: "Özne bir yanda, 2-4 kelime karşı yanda." },
  "dev-yazi": { ad: "Dev yazı", ek: "Arkadaki dev söz", ipucu: "Dev söz öznenin arkasında; iki satır altta." },
  "alt-bant": { ad: "Alt bant", ek: "Üst yardımcı satır", ipucu: "Tek dev söz altta; küçük satır sol üstte." },
  bolunmus: { ad: "Bölünmüş", ek: "", ipucu: "1. satır sol yarının, 2. satır sağ yarının etiketi (önce / sonra)." },
  rozet: { ad: "Rozet", ek: "", ipucu: "Yalnız sağ üstte 1-2 kelime; sahne anlatır." },
  not: { ad: "El yazısı not", ek: "El yazısı not", ipucu: "Kısa el yazısı not ve ok; başlık altta." },
  seri: { ad: "Seri", ek: "Üstteki marka sözü", ipucu: "Marka sözü başın arkasında, iki satır altta; girdi klasöründeki logo1 ve logo2 iki yana gelir." },
  yazisiz: { ad: "Yazısız", ek: "", ipucu: "Hiç yazı yok; görsel tek başına anlatır." },
};
export const KAYNAK_ADI: Record<string, string> = { agy: "agy", kare: "video karesi", elle: "eldeki kare", dis: "dış platform", duzeltme: "düzeltme" };
// Görsel düzeltme için hazır istekler (kullanıcı serbestçe de yazar).
export const DUZELT_CIPLER = [
  "Yüz ifadesini daha şaşkın yap", "Arka planı sadeleştir ve koyulaştır", "Işığı daha dramatik yap (yan ışık, kontrast)",
  "Özneyi biraz büyüt ve öne al", "Elleri düzelt", "Renkleri daha canlı yap",
];

// "satır1|satır2" tek alanda taşınır; satırın içindeki | ayırıcıyı bozmasın
export const satirTemiz = (s: string) => s.replace(/\|/g, " ").trim();
export const metinAlani = (y: Pick<Yazi, "satir1" | "satir2">) => `${satirTemiz(y.satir1)}|${satirTemiz(y.satir2)}`;
// Başlık kutusunun (tuval yüzdesi) çiğnediği alanların adları: ic alanın dışına taşma ya da dis alana girme.
export const tasanAlanlar = (r: number[], alanlar: Alan[]) => alanlar.filter(({ kutu: [s, u, sa, a], tur }) =>
  (tur === "ic" ? r[0] < s || r[1] < u || r[2] > sa || r[3] > a : !(r[2] <= s || r[3] <= u || r[0] >= sa || r[1] >= a))).map((g) => g.ad);
export const yaziAlanlari = (y: Yazi) => ({ metin: metinAlani(y), vurgu: y.vurgu, yerlesim: y.yerlesim, olcek: y.olcek, karart: y.karart, kutu: y.kutu,
  kalip: y.kalip, stil: y.stil, ek: y.ek });

const sinir = (v: number) => Math.min(100, Math.max(0, v));
const iki = (v: number) => Math.round(v * 100) / 100;
// Fareyle çizilen kutu (iki köşe, tuval yüzdesi) → [sol, üst, sağ, alt]. Ters çizim düzelir, kenara kırpılır;
// %2'den küçük kutu tıklama sayılır (null). Sunucu (kapak.bolge_px) aynı sınırı uygular.
export const kutuNormal = (a: [number, number], b: [number, number]): [number, number, number, number] | null => {
  const [s, sa] = [sinir(a[0]), sinir(b[0])].sort((x, y) => x - y);
  const [u, al] = [sinir(a[1]), sinir(b[1])].sort((x, y) => x - y);
  return sa - s < 2 || al - u < 2 ? null : [iki(s), iki(u), iki(sa), iki(al)];
};

export type AdimId = "video" | "fikir" | "uret" | "duzelt" | "teslim";
export const ADIMLAR: { id: AdimId; ad: string }[] = [
  { id: "video", ad: "Video" }, { id: "fikir", ad: "Fikir ve prompt" }, { id: "uret", ad: "Üret" },
  { id: "duzelt", ad: "Düzelt" }, { id: "teslim", ad: "Master prompt ve teslim" },
];
// Adımın durumu: tamam, sırada (ilk tamamlanmamış) ya da bekliyor. Kullanıcı sırayı atlayabilir; şerit yalnız yol gösterir.
export const adimDurumu = (d: Pick<Durum, "kareler" | "oneri" | "brief" | "adaylar" | "secim"> | null) => {
  const tamam: Record<AdimId, boolean> = {
    video: !!d?.kareler.length,
    fikir: !!(d?.oneri?.briefler.length || d?.brief.length),
    uret: !!d?.adaylar.length,
    duzelt: !!d?.adaylar.some((a) => a.ebeveyn !== null || a.zemin_kaynagi === "dis") || !!d?.secim,
    teslim: !!d?.secim && !d.secim.eski,
  };
  const sirada = ADIMLAR.find((a) => !tamam[a.id])?.id ?? null;
  return ADIMLAR.map((a) => ({ ...a, durum: tamam[a.id] ? "tamam" : a.id === sirada ? "sirada" : "bekliyor" } as const));
};

// Görsel motoru rozeti: agy görsel modelini seçtirmez; adı ve kota açılışı loglardan okunur (gorsel.kota).
export const motorMetni = (m: GorselMotor | undefined, simdi = new Date()) => {
  const ad = m?.model ?? "agy varsayılanı (Nano Banana)";
  if (!m?.kapali || !m.acilis) return { metin: `Görsel modeli: ${ad} · agy sabit`, kapali: false };
  const t = new Date(m.acilis);
  const dk = Math.max(1, Math.round((t.getTime() - simdi.getTime()) / 60000));
  const saat = t.toLocaleTimeString("tr", { hour: "2-digit", minute: "2-digit" });
  return { metin: `Görsel kotası dolu · ${saat}'te açılır (${dk < 60 ? `${dk} dk` : `${Math.round(dk / 60)} sa`})`, kapali: true };
};

// /dosya/<stüdyo>/<proje>/<kök>/<yol>: kök outputs ya da inputs; yol parçaları ayrı kodlanır.
export const dosyaUrl = (p: { studyo: string; ad: string }, kok: string, yol: string, v?: number) =>
  `/dosya/${p.studyo}/${p.ad}/${kok}/${yol.split("/").map(encodeURIComponent).join("/")}${v ? `?v=${v}` : ""}`;
// "inputs:1.mp4" → /dosya adresi
export const videoUrl = (p: { studyo: string; ad: string }, yol: string) => {
  const [kok, ...ic] = yol.split(":");
  return dosyaUrl(p, kok, ic.join(":"));
};
