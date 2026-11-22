// Telefonda okunurluk ölçüleri (ADR 0045). instagram/1: ince ve küçük ikonlar okunmuyordu.
import { ikonCizgi, type TemaToken } from "../../tema";
import type { Kutu } from "./tipler";

// İkon çizgi kalınlığı, viewBox biriminde. Alt sınırlar: stilin ikon çizgisi (px) ve kutu kısa kenarının %7'si.
// Bütün ikonlar bunu kullanır: aynı karede ikon çizgileri aynı kalınlıkta görünür.
export const IKON_CIZGI_ORAN = 0.07;
export const ikonKalinlik = (t: TemaToken, kutu: Kutu, u: number, viewBox = 24) => {
  const kisa = Math.min(kutu.w, kutu.h);
  const px = Math.max(ikonCizgi(t) * u, kisa * IKON_CIZGI_ORAN);
  return (px * viewBox) / kisa;
};
// Dış kontur (okunurluk): renkli çizginin iki yanında bu kadar viewBox birimi koyu kenar.
// 1.6 birim kalın siyah çerçeve "MS Paint" clipart'ı gibi duruyordu; 1.0 okunurluğu korur, çizgiyi ezmez.
export const KONTUR_EK = 1.0;
