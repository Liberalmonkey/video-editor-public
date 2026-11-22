// Kareye bağlı zamanlama (ADR 0045). Yalnız useCurrentFrame, spring ve interpolate; CSS keyframe ve doğrusal eğri yok.
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { adimKare, adliEgriler, useTema, type Egriler, type TemaToken } from "../../tema";

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export interface Akis {
  f: number;          // klibin başından kare (stilin adım kare hızına yuvarlanmış)
  fps: number;
  sureKare: number;
  girKare: number;
  cikKare: number;
  hazirlikKare: number;
  // Anticipation: 0→1→0 atımı, [0, hazirlikKare] karelerinde; ana giriş (gir) bundan SONRA başlar.
  // Kullanım: konum = hedef + yon * (-genlik * ters + mesafe * (1 - gir)). Ters hazırlık ana yönün TERSİNE işaretlenir.
  ters: number;
  belir: number;      // 0→1, ilk 2 karede: öğe hazırlık sırasında görünür olsun (f=0'da gizli kalmasın)
  gir: number;        // 0→1, enter eğrisiyle (hazırlıktan sonra)
  cik: number;        // 0→1, exit eğrisiyle (çıkışta artar)
  gorunur: number;    // gir * (1 - cik): opaklık ve ölçek için
  e: Egriler;
  // i. öğenin gecikmeli girişi (stagger kare). Varsayılan 3 kare: 2-4 arası kural.
  sirali: (i: number, kare?: number, egri?: keyof Egriler) => number;
  // Vurgu: t0 karesinde başlayan, emphasis eğrili tek atım (0→1→0 değil, 0→1).
  vurgu: (t0: number, kare?: number) => number;
  // Follow-through: ana hareketten gecikmeli, aşıp oturan ikincil değer (spring).
  takip: (gecikme?: number, sert?: number) => number;
  // Nefes: -1..1 ince ambient sinüs (≈2.4 sn periyot), gorunur ile çarpılmış. Tutmada canlılık: ölçek 1 + 0.006 * nefes gibi.
  nefes: number;
  // Parlama: 0..1, giriş bitiminde bir kez karttan geçen ışık süpürmesi (tema.parlamaStil'e verilir; 0 ve 1'de görünmez).
  parlama: number;
  // Hız bulanıklığı: girişin ilk hızlı karelerinde 0..3.5 px (u ile çarpılmamış), tutmada 0; piksel/basamak stilde hep 0.
  hizBulaniklik: number;
  // Tek sönümlü yay (jöle yok): hazırlıktan sonra + gecikme karede başlar, 0→1. Çıkışla çarpılmaz (gorunur ile çarp).
  yay: (gecikme?: number, profil?: YayProfil) => number;
}

export type YayProfil = "keskin" | "ipeksi" | "agir" | "elastik";
// Sönüm oranı ζ = damping / (2·√(stiffness·mass)). keskin ≈0.74 (%3 taşma), ipeksi ≈1.1 ve agir ≈1.25 (taşmasız),
// elastik ≈0.58 (%10 taşma, ikinci salınım <%1: jöle değil).
export const YAY_PROFIL: Record<YayProfil, { damping: number; stiffness: number; mass: number }> = {
  keskin: { damping: 20, stiffness: 260, mass: 0.7 },
  ipeksi: { damping: 26, stiffness: 140, mass: 1 },
  agir: { damping: 30, stiffness: 90, mass: 1.6 },
  elastik: { damping: 14, stiffness: 180, mass: 0.8 },
};

// sureKare: klibin süresi. giris/cikis sn; tema sure_kat ile ölçeklenir. Çıkış girişten kısa tutulur.
// hazirlik: anticipation kare sayısı (2-4). Giriş süresinin içindedir: toplam giriş süresi değişmez.
export const useAkis = (sureKare: number, giris_sn = 0.4, cikis_sn = 0.25, hazirlik = 3): Akis =>
  akisHesapla(useTema(), useCurrentFrame(), useVideoConfig().fps, sureKare, giris_sn, cikis_sn, hazirlik);

// Saf hesap (React'siz): HyperFrames kompozisyonları (studio/hf/native/cekirdek.ts) aynı sayıyı buradan alır (ADR 0051).
export const akisHesapla = (t: TemaToken, ham: number, fps: number, sureKare: number, giris_sn = 0.4, cikis_sn = 0.25, hazirlik = 3): Akis => {
  const f = adimKare(t, ham, fps);
  const e = adliEgriler(t);
  const kat = t.hareket.sure_kat;
  const toplamGir = Math.max(3, Math.round(giris_sn * kat * fps));
  const hazirlikKare = Math.max(0, Math.min(hazirlik, toplamGir - 3));
  const girKare = toplamGir - hazirlikKare;
  const cikKare = Math.max(2, Math.min(toplamGir - 1, Math.round(cikis_sn * kat * fps)));
  const gir = e.enter(interpolate(f, [hazirlikKare, hazirlikKare + girKare], [0, 1], KIS));
  const cik = e.exit(interpolate(f, [sureKare - cikKare, sureKare], [0, 1], KIS));
  const ters = hazirlikKare ? Math.sin(Math.PI * interpolate(f, [0, hazirlikKare], [0, 1], KIS)) : 0;
  const belir = interpolate(f, [0, 2], [0, 1], KIS);
  const gorunur = gir * (1 - cik);
  // Basamaklı stil (piksel, lastik hortum): hareket kareden kareye sıçrar; bulanıklık ve nefes onu yumuşatmamalı.
  const basamak = t.hareket.easing === "basamak" || !!t.hareket.adim_fps;
  const girX = (k: number) => e.enter(interpolate(k, [hazirlikKare, hazirlikKare + girKare], [0, 1], KIS));
  const hiz = (girX(f) - girX(f - 1)) * girKare; // doğrusal girişte 1; ease-out başında 3-6
  const hizBulaniklik = basamak ? 0 : Math.max(0, Math.min(3.5, (hiz - 0.6) * 1.4)) * (1 - cik);
  const nefes = basamak ? 0 : Math.sin((2 * Math.PI * f) / (fps * 2.4)) * gorunur;
  const pBas = toplamGir - 2, pSure = Math.max(6, Math.round(0.55 * fps));
  const parlama = e.settle(interpolate(f, [pBas, pBas + pSure], [0, 1], KIS));
  return {
    f, fps, sureKare, girKare: toplamGir, cikKare, hazirlikKare, ters, belir, gir, cik, gorunur, e,
    sirali: (i, kare = 3, egri = "enter") => e[egri](interpolate(f, [hazirlikKare + i * kare, hazirlikKare + i * kare + girKare], [0, 1], KIS)),
    vurgu: (t0, kare = Math.round(0.3 * fps)) => e.emphasis(interpolate(f, [t0, t0 + kare], [0, 1], KIS)),
    // damping 14 / mass 0.8: %4-8 taşma, tek sönüm; ikinci salınım (jöle) yok.
    takip: (gecikme = 3, sert = 180) =>
      spring({ frame: f - gecikme, fps, config: { damping: 14, stiffness: sert, mass: 0.8 } }) * (1 - cik),
    nefes, parlama, hizBulaniklik,
    yay: (gecikme = 0, profil = "ipeksi") => spring({ frame: f - hazirlikKare - gecikme, fps, config: YAY_PROFIL[profil] ?? YAY_PROFIL.ipeksi }),
  };
};

// Çizim (stroke) ilerlemesi: path uzunluğuna göre dashoffset. ilerleme 0..1.
export const cizgiOfset = (uzunluk: number, ilerleme: number) => uzunluk * (1 - Math.max(0, Math.min(1, ilerleme)));
