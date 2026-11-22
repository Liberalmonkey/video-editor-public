// Program monitörünün oynatıcısı tek yerden sürülür: timeline, kısayollar, düğmeler.
// WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Motor bağımsız: Remotion PlayerRef ve HyperFrames oynatıcısı
// (Monitorler.tsx HfMonitor bağdaştırıcısı) aynı üç yöntemi sağlar; zaman ve oynuyor durumu olaylarla depoya yazılır.
import { useKurgu } from "./depo";
import { kesimNoktalari } from "./komutlar";

export interface Oyuncu { seekTo: (kare: number) => void; play: () => void; pause: () => void }
let oyuncu: Oyuncu | null = null;
export const oyuncuBagla = (p: Oyuncu | null) => { oyuncu = p; };

const fps = () => useKurgu.getState().kurgu?.sekans.fps ?? 30;
export const bitisi = () => {
  const k = useKurgu.getState().kurgu;
  return k ? Math.max(0, ...k.klipler.map((c) => c.bas + c.sure)) : 0;
};

export const git = (t: number) => {
  const f = fps();
  const son = Math.max(0, Math.ceil(bitisi() * f) - 1);
  const kare = Math.min(son, Math.max(0, Math.round(t * f)));
  useKurgu.setState({ zaman: kare / f });
  oyuncu?.seekTo(kare);
};
export const kareGit = (n: number) => git(useKurgu.getState().zaman + n / fps());
export const kesimeGit = (yon: 1 | -1) => {
  const d = useKurgu.getState();
  if (!d.kurgu) return;
  const n = kesimNoktalari(d.kurgu);
  const hedef = yon > 0 ? n.find((x) => x > d.zaman + 1e-4) : [...n].reverse().find((x) => x < d.zaman - 1e-4);
  if (hedef !== undefined) git(hedef);
};

export const oynat = (hiz = 1) => {
  useKurgu.setState({ hiz });
  oyuncu?.play();
};
export const durdur = () => { oyuncu?.pause(); useKurgu.setState({ hiz: 1 }); };
export const degistir = () => { if (useKurgu.getState().oynuyor) durdur(); else oynat(1); };

// J/L: basıldıkça hızlanır; Premiere'in shuttle davranışı. K durur.
const ADIMLAR = [1, 2, 4];
export const shuttle = (yon: 1 | -1) => {
  const { oynuyor, hiz } = useKurgu.getState();
  const ayni = oynuyor && Math.sign(hiz) === yon;
  const i = ayni ? ADIMLAR.indexOf(Math.abs(hiz)) : -1;
  oynat(yon * ADIMLAR[Math.min(ADIMLAR.length - 1, i + 1)]);
};
