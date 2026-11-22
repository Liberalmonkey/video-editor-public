import { produce } from "immer";
import { AudioLines, Eye, EyeOff, Hand, Link2, Lock, LockOpen, Magnet, MousePointer2, MoveHorizontal, Plus, Redo2, Rows3, Scissors, SplitSquareHorizontal, Trash2, Undo2, ZoomIn, ZoomOut } from "lucide-react";
import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import type { Klip, KurguProps } from "../../../remotion/tipler";
import { useDepo } from "../depo";
import { Bos, Dugme, IkonDugme } from "../ortak";
import { CETVEL, ciz, izYuksekligi, kazancY, sesBandi, yKazanc } from "./ciz";
import { sesiAyirUygula, useKurgu, type Arac, type KaynakOge } from "./depo";
import { degisinceHaberVer, temizle } from "./gorselOnbellek";
import * as K from "./komutlar";
import { git } from "./oynatici";

export const SURUKLE_TUR = "application/x-studio-kaynak";
const KENAR_PX = 7;
const YAPIS_PX = 8;

type Surukleme =
  | { tur: "tasi"; lider: Klip; idler: string[]; x0: number; y0: number; insert: boolean; satir0: number; hareket: boolean }
  | { tur: "kirp" | "rippleKirp"; id: string; kenar: "bas" | "son"; x0: number; u: number }
  | { tur: "rolling"; sol: string; sag: string; x0: number; u: number }
  | { tur: "slip" | "slide"; id: string; x0: number }
  | { tur: "kafa" }
  | { tur: "kazanc"; id: string; ust: number; yuk: number; kf: boolean; bas: number }
  | { tur: "lastik"; x0: number; y0: number; ek: string[] }
  | { tur: "el"; x0: number; y0: number; sx: number; sy: number };

const ARACLAR: [Arac, string, React.ReactNode, string][] = [
  ["sec", "Seç", <MousePointer2 size={15} />, "V"],
  ["razor", "Razor: tıkla, böl", <Scissors size={15} />, "C"],
  ["ripple", "Ripple kırp: kenarı sürükle", <SplitSquareHorizontal size={15} />, "B"],
  ["rolling", "Rolling: iki klibin kesimini kaydır", <MoveHorizontal size={15} />, "N"],
  ["slip", "Slip: yer sabit, kaynak kayar", <Rows3 size={15} />, "Y"],
  ["slide", "Slide: içerik sabit, klip kayar", <SplitSquareHorizontal size={15} style={{ transform: "rotate(90deg)" }} />, "U"],
  ["el", "El: görünümü kaydır", <Hand size={15} />, "H"],
];

const IzBaslik: React.FC<{ id: string }> = ({ id }) => {
  const iz = useKurgu((d) => d.kurgu?.izler.find((i) => i.id === id));
  const duzenle = useKurgu((d) => d.duzenle);
  if (!iz) return null;
  const degis = (a: "kilit" | "sessiz" | "gizli") => duzenle(`${id} ${a}`, (d) => { const i = d.izler.find((x) => x.id === id)!; i[a] = !i[a]; });
  const sil = () => {
    let sonuc = false;
    duzenle(`${id} izini sil`, (d) => { sonuc = K.izSil(d, id); });
    if (!sonuc) useDepo.getState().bildir("Klip olan ya da türünün son izi silinemez", true);
  };
  return (
    <div className={`iz-baslik ${iz.tur}`} style={{ height: izYuksekligi(iz) }}>
      <span className="iz-ad" title={iz.ad || id}>{id}{iz.ad ? ` ${iz.ad}` : ""}</span>
      <div className="iz-dugmeler">
        <IkonDugme ad={iz.kilit ? `${id} kilidini aç` : `${id} kilitle`} acik={iz.kilit} onClick={() => degis("kilit")}>{iz.kilit ? <Lock size={13} /> : <LockOpen size={13} />}</IkonDugme>
        {iz.tur === "video" && <IkonDugme ad={iz.gizli ? `${id} göster` : `${id} gizle`} acik={iz.gizli} onClick={() => degis("gizli")}>{iz.gizli ? <EyeOff size={13} /> : <Eye size={13} />}</IkonDugme>}
        <IkonDugme ad={`${id} izini sil`} className="iz-sil" onClick={sil}><Trash2 size={13} /></IkonDugme>
      </div>
    </div>
  );
};

export const Timeline: React.FC = () => {
  const kurgu = useKurgu((d) => d.kurgu);
  const anahtar = useKurgu((d) => d.anahtar);
  const arac = useKurgu((d) => d.arac);
  const yapisma = useKurgu((d) => d.yapisma);
  const kayit = useKurgu((d) => d.kayit);
  const geriVar = useKurgu((d) => d.geri.length > 0);
  const ileriVar = useKurgu((d) => d.ileri.length > 0);
  const ayarla = useKurgu((d) => d.ayarla);
  const duzenle = useKurgu((d) => d.duzenle);

  const kap = useRef<HTMLDivElement>(null);
  const kaydirici = useRef<HTMLDivElement>(null);
  const tuval = useRef<HTMLCanvasElement>(null);
  const basliklar = useRef<HTMLDivElement>(null);
  const [pxSn, setPxSn] = useState(30);
  const pxRef = useRef(30);
  pxRef.current = pxSn;

  const on = useRef<KurguProps | null>(null);   // sürükleme önizlemesi
  const sur = useRef<Surukleme | null>(null);
  const yapisRef = useRef<number | null>(null);
  const lastikRef = useRef<{ x1: number; y1: number; x2: number; y2: number } | null>(null);
  const birakRef = useRef<{ t: number; iz: string | null } | null>(null);
  const imlecRef = useRef<number | null>(null);
  const kirli = useRef(true);
  const [boyut, setBoyut] = useState({ w: 800, h: 300 });

  const iste = useCallback(() => { kirli.current = true; }, []);
  // Test köprüsü: ölçüm betikleri piksel hesabı için kullanır.
  useEffect(() => { (window as any).__studioTl = { px: () => pxRef.current, sc: () => kaydirici.current, tuval: () => tuval.current }; }, []);

  // Çizim döngüsü: yalnız değişince.
  useEffect(() => {
    let dur = false;
    const dongu = () => {
      if (dur) return;
      requestAnimationFrame(dongu);
      const t = tuval.current, sc = kaydirici.current, d = useKurgu.getState();
      const k = on.current ?? d.kurgu;
      if (!kirli.current || !t || !sc || !k || !d.anahtar) return;
      kirli.current = false;
      const oran = devicePixelRatio || 1;
      const w = sc.clientWidth, h = sc.clientHeight;
      if (t.width !== Math.round(w * oran) || t.height !== Math.round(h * oran)) {
        t.width = Math.round(w * oran); t.height = Math.round(h * oran);
        t.style.width = `${w}px`; t.style.height = `${h}px`;
        t.style.marginBottom = `${-h}px`; // WHY: sticky canvas kaydırma alanını büyütmesin, boyutu arkadaki boşluk belirler
      }
      const g = t.getContext("2d")!;
      g.setTransform(oran, 0, 0, oran, 0, 0);
      ciz(g, {
        k, medya: d.medya, anahtar: d.anahtar, bulgular: d.bulgular, w, h, x0: sc.scrollLeft, y0: sc.scrollTop, pxSn: pxRef.current, secim: new Set(d.secim), zaman: d.zaman, giris: d.giris, cikis: d.cikis,
        yapis: yapisRef.current, lastik: lastikRef.current, hedefIz: birakRef.current?.iz ?? null, birakma: birakRef.current?.t ?? null, imlec: imlecRef.current, kazancKlip: sur.current?.tur === "kazanc" ? sur.current.id : null,
      });
      if (basliklar.current) basliklar.current.style.transform = `translateY(${-sc.scrollTop}px)`;
    };
    dongu();
    degisinceHaberVer(iste);
    const izle = useKurgu.subscribe((s, o) => {
      if (s.kurgu !== o.kurgu || s.secim !== o.secim || s.zaman !== o.zaman || s.giris !== o.giris || s.cikis !== o.cikis || s.bulgular !== o.bulgular || s.medya !== o.medya) iste();
      // Oynarken kafa görünümden çıkarsa sayfa kayar.
      if (s.oynuyor && s.zaman !== o.zaman && kaydirici.current) {
        const sc = kaydirici.current, x = s.zaman * pxRef.current;
        if (x > sc.scrollLeft + sc.clientWidth - 30 || x < sc.scrollLeft) sc.scrollLeft = Math.max(0, x - 40);
      }
    });
    return () => { dur = true; izle(); };
  }, [iste]);

  useEffect(() => { temizle(); iste(); }, [anahtar, iste]);
  useLayoutEffect(iste);

  useEffect(() => {
    const sc = kaydirici.current;
    if (!sc) return;
    const ro = new ResizeObserver(() => { setBoyut({ w: sc.clientWidth, h: sc.clientHeight }); iste(); });
    ro.observe(sc);
    return () => ro.disconnect();
  }, [iste, !!kurgu]);

  const zumla = useCallback((yeni: number, odak?: number) => {
    const sc = kaydirici.current;
    if (!sc) return;
    const px = Math.min(600, Math.max(0.5, yeni));
    const ox = odak ?? useKurgu.getState().zaman * pxRef.current - sc.scrollLeft;
    const t = (sc.scrollLeft + ox) / pxRef.current;
    pxRef.current = px;
    setPxSn(px);
    requestAnimationFrame(() => { sc.scrollLeft = Math.max(0, t * px - ox); iste(); });
  }, [iste]);

  const sigdir = useCallback(() => {
    const sc = kaydirici.current, k = useKurgu.getState().kurgu;
    if (!sc || !k) return;
    // WHY: boş ya da çok kısa kurgu en yüksek zoom'da açılmasın; ilk klip ekranda görünsün.
    const b = Math.max(30, ...k.klipler.map((c) => c.bas + c.sure));
    zumla((sc.clientWidth - 30) / b, 0);
    requestAnimationFrame(() => { sc.scrollLeft = 0; });
  }, [zumla]);
  useEffect(() => {
    const f = (e: Event) => {
      const d = (e as CustomEvent).detail;
      if (d === "sigdir") sigdir();
      else zumla(pxRef.current * (d === "yakin" ? 1.25 : 0.8));
    };
    window.addEventListener("studio-zoom", f);
    return () => window.removeEventListener("studio-zoom", f);
  }, [sigdir, zumla]);
  // İlk klip eklenince kurgu ölçeğine geç.
  const bosMu = useRef(true);
  useEffect(() => {
    const dolu = !!kurgu?.klipler.length;
    if (dolu && bosMu.current) requestAnimationFrame(sigdir);
    bosMu.current = !dolu;
  }, [kurgu?.klipler.length, sigdir]);
  // Proje açılınca tamamı görünsün.
  const ilkKurgu = useRef<string | null>(null);
  useEffect(() => { if (anahtar && kurgu && ilkKurgu.current !== anahtar) { ilkKurgu.current = anahtar; requestAnimationFrame(sigdir); } }, [anahtar, !!kurgu, sigdir]);

  useEffect(() => {
    const sc = kaydirici.current;
    if (!sc) return;
    const teker = (e: WheelEvent) => {
      if (!e.ctrlKey && !e.altKey) return;
      e.preventDefault();
      zumla(pxRef.current * Math.exp(-e.deltaY * 0.0016), e.clientX - sc.getBoundingClientRect().left);
    };
    sc.addEventListener("wheel", teker, { passive: false });
    return () => sc.removeEventListener("wheel", teker);
  }, [zumla, !!kurgu]);

  const konum = (e: { clientX: number; clientY: number }) => {
    const sc = kaydirici.current!, r = sc.getBoundingClientRect();
    return { px: e.clientX - r.left, py: e.clientY - r.top, x: e.clientX - r.left + sc.scrollLeft, y: e.clientY - r.top + sc.scrollTop };
  };
  const satirBul = (k: KurguProps, y: number) => {
    let a = CETVEL;
    for (const iz of k.izler) { const h = izYuksekligi(iz); if (y >= a && y < a + h) return iz; a += h; }
    return null;
  };
  const klipBul = (k: KurguProps, x: number, y: number) => {
    const iz = satirBul(k, y);
    if (!iz) return { iz: null, c: null as Klip | null, kenar: null as "bas" | "son" | null };
    const t = x / pxRef.current;
    const c = k.klipler.find((q) => q.iz === iz.id && t >= q.bas - 1e-6 && t < q.bas + q.sure) ?? null;
    let kenar: "bas" | "son" | null = null;
    if (c) {
      const sol = x - c.bas * pxRef.current, sag = (c.bas + c.sure) * pxRef.current - x;
      const pay = Math.min(KENAR_PX, c.sure * pxRef.current / 3);
      if (sol <= pay) kenar = "bas"; else if (sag <= pay) kenar = "son";
    }
    return { iz, c, kenar };
  };
  const satirUst = (k: KurguProps, id: string) => {
    let a = CETVEL;
    for (const iz of k.izler) { if (iz.id === id) return a; a += izYuksekligi(iz); }
    return a;
  };
  // İmleç ses çizgisine ±4 px yakınsa çizgi tutulur; klip kenarı önceliklidir.
  const cizgiBul = (k: KurguProps, c: Klip, kenar: "bas" | "son" | null, x: number, y: number) => {
    if (kenar) return null;
    const iz = k.izler.find((i) => i.id === c.iz)!;
    const b = sesBandi(k, c, satirUst(k, c.iz), izYuksekligi(iz));
    return b && !iz.kilit && Math.abs(y - kazancY(K.kazancAni(c, x / pxRef.current - c.bas), b)) <= 4 ? b : null;
  };
  const yapisDene = (t: number, haric: string[] = []) => {
    const d = useKurgu.getState();
    if (!d.yapisma || !d.kurgu) { yapisRef.current = null; return t; }
    const ada = K.kesimNoktalari(d.kurgu, haric);
    ada.push(d.zaman);
    if (d.giris !== null) ada.push(d.giris);
    if (d.cikis !== null) ada.push(d.cikis);
    const s = K.yapis(t, ada, YAPIS_PX / pxRef.current);
    yapisRef.current = s;
    return s ?? t;
  };
  const kareyeYuvarla = (t: number) => K.kareYuvarla(t, useKurgu.getState().kurgu?.sekans.fps ?? 30);

  const imlecBul = (k: KurguProps, x: number, y: number): string => {
    const a = useKurgu.getState().arac;
    if (y < CETVEL) return "col-resize";
    if (a === "el") return "grab";
    const { c, kenar } = klipBul(k, x, y);
    if (a === "razor") return c ? "crosshair" : "default";
    if (!c) return "default";
    if (a === "slip" || a === "slide") return "ew-resize";
    if (a === "sec" && cizgiBul(k, c, kenar, x, y)) return "ns-resize";
    return kenar ? "ew-resize" : a === "sec" ? "default" : "default";
  };

  const bas = (e: React.PointerEvent) => {
    const d = useKurgu.getState(), k = d.kurgu;
    const sc = kaydirici.current!;
    if (!k || e.button !== 0) return;
    const { px, py, x, y } = konum(e);
    if (py >= sc.clientHeight || px >= sc.clientWidth) return; // kaydırma çubuğu
    tuval.current!.setPointerCapture(e.pointerId);
    d.ayarla({ odak: "program" });

    if (d.arac === "el") { sur.current = { tur: "el", x0: e.clientX, y0: e.clientY, sx: sc.scrollLeft, sy: sc.scrollTop }; return; }
    if (py < CETVEL) { sur.current = { tur: "kafa" }; git(yapisDene(x / pxRef.current)); return; }

    const { iz, c, kenar } = klipBul(k, x, y);
    if (d.arac === "razor") {
      if (c && iz && !iz.kilit) {
        const t = kareyeYuvarla(yapisDene(x / pxRef.current));
        duzenle("Razor", (f) => { if (e.shiftKey) K.kafadaKes(f, t, []); else K.kes(f, c.id, t); });
      }
      yapisRef.current = null;
      return;
    }
    if (!c || iz?.kilit) {
      if (!(e.shiftKey || e.ctrlKey)) d.sec([]);
      sur.current = { tur: "lastik", x0: px, y0: py, ek: e.shiftKey || e.ctrlKey ? d.secim : [] };
      return;
    }

    let secim = d.secim;
    const grup = e.altKey ? [c.id] : K.baglilar(k, [c.id]);
    if (e.ctrlKey || e.shiftKey) {
      secim = secim.includes(c.id) ? secim.filter((i) => !grup.includes(i)) : [...new Set([...secim, ...grup])];
    } else if (!secim.includes(c.id)) secim = grup;
    d.sec(secim);
    d.ayarla({ odakKlip: c.id });

    if (d.arac === "sec") {
      const cizgi = cizgiBul(k, c, kenar, x, y);
      // Animasyonlu kazançta sürükleme tıklanan anda keyframe yazar; değilse tüm çizgiyi taşır.
      if (cizgi) { sur.current = { tur: "kazanc", id: c.id, ...cizgi, kf: !!c.ses.kf?.length, bas: x / pxRef.current - c.bas }; return; }
      if (kenar) { sur.current = { tur: "kirp", id: c.id, kenar, x0: x, u: kenar === "bas" ? c.bas : c.bas + c.sure }; return; }
      if (secim.includes(c.id)) sur.current = { tur: "tasi", lider: c, idler: secim, x0: x, y0: y, insert: false, satir0: k.izler.findIndex((i) => i.id === c.iz), hareket: false };
      return;
    }
    if (d.arac === "ripple" && kenar) { sur.current = { tur: "rippleKirp", id: c.id, kenar, x0: x, u: kenar === "bas" ? c.bas : c.bas + c.sure }; return; }
    if (d.arac === "rolling" && kenar) {
      const l = k.klipler.filter((q) => q.iz === c.iz).sort((a, b) => a.bas - b.bas);
      const n = l.findIndex((q) => q.id === c.id);
      const sol = kenar === "bas" ? l[n - 1] : l[n], sag = kenar === "bas" ? l[n] : l[n + 1];
      if (sol && sag && Math.abs(sol.bas + sol.sure - sag.bas) < 1e-3) sur.current = { tur: "rolling", sol: sol.id, sag: sag.id, x0: x, u: sag.bas };
      return;
    }
    if (d.arac === "slip") { sur.current = { tur: "slip", id: c.id, x0: x }; return; }
    if (d.arac === "slide") { sur.current = { tur: "slide", id: c.id, x0: x }; }
  };

  const komutHesapla = (s: Surukleme, e: { clientX: number; clientY: number; ctrlKey: boolean }): ((d: KurguProps) => void) | null => {
    const { x, y } = konum(e);
    const u = pxRef.current;
    const k = useKurgu.getState().kurgu!;
    if (s.tur === "tasi") {
      let dt = (x - s.x0) / u;
      const t = s.lider.bas + dt, son = t + s.lider.sure;
      const d = useKurgu.getState();
      const ada = K.kesimNoktalari(k, s.idler);
      ada.push(d.zaman);
      const a = d.yapisma ? K.yapis(t, ada, YAPIS_PX / u) : null;
      const b = d.yapisma ? K.yapis(son, ada, YAPIS_PX / u) : null;
      yapisRef.current = a ?? b;
      if (a !== null) dt = a - s.lider.bas; else if (b !== null) dt = b - s.lider.bas - s.lider.sure;
      else dt = kareyeYuvarla(s.lider.bas + dt) - s.lider.bas;
      // Satır farkı aynı türdeki izler arasında sayılır.
      const hedef = satirBul(k, y);
      const izTur = k.izler[s.satir0].tur;
      const ayni = k.izler.filter((i) => i.tur === izTur);
      const dIz = hedef && hedef.tur === izTur ? ayni.findIndex((i) => i.id === hedef.id) - ayni.findIndex((i) => i.id === k.izler[s.satir0].id) : 0;
      const ins = e.ctrlKey;
      return (f) => K.tasi(f, s.idler, dt, dIz, ins);
    }
    if (s.tur === "kirp" || s.tur === "rippleKirp") {
      const hedef = kareyeYuvarla(yapisDene(s.u + (x - s.x0) / u, [s.id]));
      const dt = hedef - s.u;
      return s.tur === "kirp" ? (f) => K.kirp(f, s.id, s.kenar, dt) : (f) => K.rippleKirp(f, s.id, s.kenar, dt);
    }
    if (s.tur === "rolling") {
      const hedef = kareyeYuvarla(yapisDene(s.u + (x - s.x0) / u, [s.sol, s.sag]));
      return (f) => K.rolling(f, s.sol, s.sag, hedef - s.u);
    }
    if (s.tur === "kazanc") { const db = yKazanc(y, s); return (f) => K.kazancYaz(f, s.id, db, s.kf ? s.bas : undefined); }
    if (s.tur === "slip") { const dt = kareyeYuvarla((x - s.x0) / u); return (f) => K.slip(f, s.id, dt); }
    if (s.tur === "slide") { const dt = kareyeYuvarla((x - s.x0) / u); return (f) => K.slide(f, s.id, dt); }
    return null;
  };
  const AD: Record<string, string> = { tasi: "Taşı", kirp: "Kırp", rippleKirp: "Ripple kırp", rolling: "Rolling", slip: "Slip", slide: "Slide", kazanc: "Kazanç" };

  const hareket = (e: React.PointerEvent) => {
    const d = useKurgu.getState(), k = d.kurgu;
    const sc = kaydirici.current;
    if (!k || !sc) return;
    const s = sur.current;
    const { px, py, x, y } = konum(e);
    if (!s) {
      tuval.current!.style.cursor = imlecBul(k, x, y);
      const yeni = d.arac === "razor" && y >= CETVEL ? px : null;
      if (yeni !== imlecRef.current) { imlecRef.current = yeni; iste(); }
      return;
    }
    if (s.tur === "kafa") { git(yapisDene(x / pxRef.current)); iste(); return; }
    if (s.tur === "el") { sc.scrollLeft = s.sx - (e.clientX - s.x0); sc.scrollTop = s.sy - (e.clientY - s.y0); return; }
    if (s.tur === "lastik") {
      lastikRef.current = { x1: s.x0, y1: s.y0, x2: px, y2: py };
      const ta = (Math.min(s.x0, px) + sc.scrollLeft) / pxRef.current, tb = (Math.max(s.x0, px) + sc.scrollLeft) / pxRef.current;
      const ya = Math.min(s.y0, py) + sc.scrollTop, yb = Math.max(s.y0, py) + sc.scrollTop;
      let a = CETVEL;
      const bulunan: string[] = [];
      for (const iz of k.izler) {
        const h = izYuksekligi(iz);
        if (!iz.kilit && a < yb && a + h > ya) for (const c of k.klipler) if (c.iz === iz.id && c.bas < tb && c.bas + c.sure > ta) bulunan.push(c.id);
        a += h;
      }
      d.sec([...new Set([...s.ek, ...bulunan])]);
      iste();
      return;
    }
    if (s.tur === "tasi" && !s.hareket) {
      if (Math.abs(x - s.x0) < 3 && Math.abs(y - s.y0) < 3) return; // tıklama sürüklemeye dönmesin
      s.hareket = true;
    }
    const f = komutHesapla(s, e);
    if (f) { on.current = produce(k, f); iste(); }
  };

  const birak = (e: React.PointerEvent) => {
    const s = sur.current;
    sur.current = null;
    lastikRef.current = null;
    if (s && s.tur !== "kafa" && s.tur !== "el" && s.tur !== "lastik" && !(s.tur === "tasi" && !s.hareket)) {
      const f = komutHesapla(s, e);
      on.current = null;
      if (f) duzenle(AD[s.tur], f);
    }
    on.current = null;
    yapisRef.current = null;
    iste();
  };

  const surukle = (e: React.DragEvent) => {
    if (!e.dataTransfer.types.includes(SURUKLE_TUR)) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "copy";
    const k = useKurgu.getState().kurgu;
    if (!k) return;
    const { x, y } = konum(e);
    birakRef.current = { t: kareyeYuvarla(yapisDene(Math.max(0, x / pxRef.current))), iz: satirBul(k, y)?.id ?? null };
    iste();
  };
  const dusur = (e: React.DragEvent) => {
    const veri = e.dataTransfer.getData(SURUKLE_TUR);
    const b = birakRef.current;
    birakRef.current = null;
    yapisRef.current = null;
    iste();
    if (!veri || !b) return;
    e.preventDefault();
    useKurgu.getState().kaynaktanEkle(JSON.parse(veri) as KaynakOge, b.t, b.iz, e.ctrlKey);
  };

  if (!kurgu) return <div className="panel"><Bos baslik="Timeline boş" metin="Bir proje aç ve kurgu oluştur." /></div>;

  const toplamH = kurgu.izler.reduce((n, i) => n + izYuksekligi(i), CETVEL) + 60;
  const toplamW = Math.max(boyut.w, Math.max(0, ...kurgu.klipler.map((c) => c.bas + c.sure)) * pxSn + boyut.w * 0.7);
  const KAYIT: Record<string, [string, string]> = { kayitli: ["iyi", "Kaydedildi"], bekliyor: ["", "Kaydedilecek"], kaydediliyor: ["", "Kaydediliyor"], hata: ["hata", "Kaydedilemedi"] };

  return (
    <div className="panel" ref={kap}>
      <div className="arac tl-arac">
        <div className="arac-grup" role="toolbar" aria-label="Kurgu araçları">
          {ARACLAR.map(([a, ad, ikon, tus]) => <IkonDugme key={a} ad={`${ad} (${tus})`} acik={arac === a} aria-pressed={arac === a} onClick={() => ayarla({ arac: a })}>{ikon}</IkonDugme>)}
        </div>
        <span className="ayrac" />
        <IkonDugme ad="Yapışma (S)" acik={yapisma} aria-pressed={yapisma} onClick={() => ayarla({ yapisma: !yapisma })}><Magnet size={15} /></IkonDugme>
        <IkonDugme ad="Bağla ya da ayır (Ctrl+L)" onClick={() => { const s = useKurgu.getState().secim; if (s.length) duzenle("Bağla", (f) => K.bagla(f, s)); }}><Link2 size={15} /></IkonDugme>
        <IkonDugme ad="Sesi ayır ya da birleştir (Shift+A)" onClick={sesiAyirUygula}><AudioLines size={15} /></IkonDugme>
        <span className="ayrac" />
        <IkonDugme ad="Geri al (Ctrl+Z)" disabled={!geriVar} onClick={() => useKurgu.getState().geriAl()}><Undo2 size={15} /></IkonDugme>
        <IkonDugme ad="Yinele (Ctrl+Y)" disabled={!ileriVar} onClick={() => useKurgu.getState().yinele()}><Redo2 size={15} /></IkonDugme>
        <span className={`rozet ${KAYIT[kayit][0]}`} data-kayit={kayit}>{KAYIT[kayit][1]}</span>
        <span className="bosluk" />
        <Dugme onClick={() => duzenle("Video izi ekle", (f) => { K.izEkle(f, "video"); })}><Plus size={13} /> V</Dugme>
        <Dugme onClick={() => duzenle("Ses izi ekle", (f) => { K.izEkle(f, "ses"); })}><Plus size={13} /> A</Dugme>
        <span className="ayrac" />
        <IkonDugme ad="Uzaklaş (-)" onClick={() => zumla(pxSn * 0.8)}><ZoomOut size={15} /></IkonDugme>
        <input type="range" aria-label="Yakınlaştırma" min={-1} max={9.3} step={0.01} value={Math.log2(pxSn)} onChange={(e) => zumla(2 ** Number(e.target.value))} style={{ width: 96, padding: 0, minHeight: 0 }} />
        <IkonDugme ad="Yakınlaş (+)" onClick={() => zumla(pxSn * 1.25)}><ZoomIn size={15} /></IkonDugme>
        <Dugme onClick={sigdir} title="Tümünü sığdır (\)">Sığdır</Dugme>
      </div>
      <div className="tl-govde">
        <div className="tl-basliklar">
          <div className="tl-kose" style={{ height: CETVEL }} />
          <div className="tl-basliklar-ic"><div ref={basliklar}>{kurgu.izler.map((i) => <IzBaslik key={i.id} id={i.id} />)}</div></div>
        </div>
        <div className="tl-kaydirici" ref={kaydirici} onScroll={iste} onDragOver={surukle} onDrop={dusur}
          onDragLeave={() => { birakRef.current = null; iste(); }}>
          <canvas ref={tuval} className="tl-tuval" data-timeline role="application" tabIndex={0} aria-label={`Zaman çizelgesi, ${kurgu.klipler.length} klip. Klavye kısayolları üst şeritteki listede.`} onPointerDown={bas} onPointerMove={hareket} onPointerUp={birak} onPointerCancel={birak}
            onDoubleClick={(e) => {
              const k = useKurgu.getState().kurgu;
              if (!k || useKurgu.getState().arac !== "sec") return;
              const { x, y } = konum(e);
              const { c, kenar } = klipBul(k, x, y);
              if (!c || !cizgiBul(k, c, kenar, x, y)) return;
              // Animasyonlu kazançta çift tık keyframe ekler ya da siler; sabitse 0 dB.
              if (c.ses.kf?.length) duzenle("Kazanç keyframe", (f) => K.sesKfDegistir(f, c.id, x / pxRef.current - c.bas, 8 / pxRef.current));
              else duzenle("Kazanç", (f) => K.kazancYaz(f, c.id, 0));
            }}
            onPointerLeave={() => { if (imlecRef.current !== null) { imlecRef.current = null; iste(); } }} />
          <div style={{ width: toplamW, height: toplamH }} />
        </div>
      </div>
    </div>
  );
};
