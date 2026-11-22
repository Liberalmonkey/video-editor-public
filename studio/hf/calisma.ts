// HyperFrames kompozisyonunun çalışma zamanı: her karede klip katmanlarının dönüşümü, efekti ve görünürlüğü.
// WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Kurgu.tsx'teki Donusum ve Konusmaci hesabı birebir taşındı;
// hazır efekt ve keyframe değeri Remotion'la paylaşılan saf modülden (hazirEfekt.ts) okunur, iki motor aynı sayıyı üretir.
// HyperFrames sözleşmesi: tek paused GSAP zaman çizelgesi, her şey yalnız t'nin fonksiyonu (birikmiş durum yok).
import { deger, genislet, YON, type Izler } from "../remotion/hazirEfekt";
import type { Klip } from "../remotion/tipler";
import type { CizKlip } from "./derle";
import { buildPages, buildTokens, sayfaBul, sayfaHtml, type AltyaziVeri } from "./altyazi";
import { bezier } from "./bezier";
import { gecisStil, type GecisStil, type Renkler } from "./gecis";
import { altyaziKonum } from "./altyazi";
import { CAP_SPLIT_Y, STAGE_H, layoutP, ortaMi, yatayG, type DuzenSahne } from "./zaman";

declare const gsap: any;
declare global { interface Window { __KURGU: any; __timelines: Record<string, any>; __ada?: { ciz: (t: number) => void } } }

export { bezier } from "./bezier";
const GIRIS = bezier(0.16, 1, 0.3, 1), PUNCH_AC = bezier(0.34, 1.4, 0.64, 1), PUNCH_KAPA = bezier(0.45, 0, 0.55, 1);
const ez = (f: number, a: number, b: number, e: (x: number) => number) => e(Math.min(1, Math.max(0, (f - a) / (b - a))));

export interface Stil { opacity: number; filter: string; transform: string; clipPath: string; transformOrigin: string }

// Kurgu.tsx Donusum: el keyframe'i taban, hazır efekt izleri üstüne; giriş/çıkış geçişleri (orta noktalılar hariç).
export const donusum = (k: CizKlip, hz: Izler[] | undefined, tSeq: number, w: number, h: number): Stil => {
  const t = tSeq - k.on;
  const d = k.donus, e = k.efekt;
  let opak = deger(d.opaklik, hz, "opaklik", t, 1);
  let kay = 0, kayY = 0, gs = 1, gbul = 0;
  const gg = ortaMi(k.gecis_giris) ? null : k.gecis_giris, gc = k.gecis_cikis;
  if (gg && t < gg.sure) {
    const a = Math.min(1, t / gg.sure), kalan = 1 - GIRIS(a);
    if (gg.tur === "kaydir") kay = kalan * w;
    else if (gg.tur === "it" || gg.tur === "savur") {
      const [vx, vy] = YON[gg.yon ?? "sol"];
      kay = -vx * kalan * w; kayY = -vy * kalan * h;
      if (gg.tur === "savur") gbul = Math.sin(Math.PI * a) * 24;
    } else {
      opak *= a;
      if (gg.tur === "zoom") gs = 1 + 0.25 * kalan;
      if (gg.tur === "bulanik") gbul = (1 - a) * 20;
    }
  }
  if (gc) opak *= Math.min(1, Math.max(0, (k.sure - t) / gc.sure));
  const bul = deger(e.bulanik_kf?.length ? e.bulanik_kf : undefined, hz, "bulanik", t, e.bulanik) + gbul;
  const parl = deger(e.parlaklik_kf?.length ? e.parlaklik_kf : undefined, hz, "parlaklik", t, e.parlaklik);
  const filtre = [
    Math.abs(parl - 1) > 1e-4 && `brightness(${parl})`,
    e.kontrast !== 1 && `contrast(${e.kontrast})`,
    e.doygunluk !== 1 && `saturate(${e.doygunluk})`,
    bul > 0 && `blur(${bul}px)`,
  ].filter(Boolean).join(" ");
  const r = e.kirp;
  const x = deger(d.x, hz, "x", t, 0) + kay, y = deger(d.y, hz, "y", t, 0) + kayY;
  const s = deger(d.olcek, hz, "olcek", t, 1) * gs, a = deger(d.aci, hz, "aci", t, 0);
  return {
    opacity: opak,
    filter: filtre,
    clipPath: r ? `inset(${(r.ust ?? 0) * h}px ${(r.sag ?? 0) * w}px ${(r.alt ?? 0) * h}px ${(r.sol ?? 0) * w}px)` : "",
    transform: x || y || s !== 1 || a ? `translate(${x}px, ${y}px) scale(${s})${a ? ` rotate(${a}deg)` : ""}` : "",
    transformOrigin: d.capa ? `${d.capa.x * 100}% ${d.capa.y * 100}%` : "",
  };
};

// Kurgu.tsx Konusmaci: taban zoom bölünmüş sahnede (lp) 1'e gider; punch; odaklı punch kendi noktasına büyür.
export const konusmaci = (k: CizKlip, tGlobal: number, fps: number, lp = 0) => {
  const frame = tGlobal * fps;
  let punch = 1, odak = "";
  for (const pt of k.punches) {
    const n = typeof pt === "number" ? { t: pt } : pt;
    const a = (k.bas + (n.t - k.giris) / k.hiz) * fps;
    const b = typeof pt === "number" ? a + 30 : a + 8 + (n.sure ?? 1) * fps;
    const v = ez(frame, a, a + 8, PUNCH_AC) - ez(frame, b, b + 10, PUNCH_KAPA);
    punch += ((n.olcek ?? 1.1) - 1) * v;
    if (v > 0 && (n.x != null || n.y != null)) odak = `${(n.x ?? 0.5) * 100}% ${(n.y ?? 0.5) * 100}%`;
  }
  const z = (k.zoom + (1 - k.zoom) * lp) * (odak ? 1 : punch);
  return { z, odakOrigin: odak, odakTransform: odak ? `scale(${punch})` : "" };
};

const kur = () => {
  const veri = window.__KURGU;
  const { w, h, fps } = veri.sekans;
  const hazir = genislet(veri.tum as Klip[], { w, h, fps });
  const ogeler = (veri.klipler as CizKlip[]).map((k) => ({
    k, hz: hazir.get(k.id), kap: document.getElementById(`k-${k.id}`) as HTMLElement,
    don: document.getElementById(`d-${k.id}`) as HTMLElement,
    cx: document.getElementById(`cx-${k.id}`) as HTMLElement, gx: document.getElementById(`gx-${k.id}`) as HTMLElement,
    gkg: document.getElementById(`gkg-${k.id}`) as HTMLElement, gkc: document.getElementById(`gkc-${k.id}`) as HTMLElement,
    odak: document.getElementById(`o-${k.id}`) as HTMLElement | null,
    panel: document.getElementById(`p-${k.id}`) as HTMLElement | null,
    medya: document.getElementById(`m-${k.id}`) as HTMLElement | null,
  }));
  const av = veri.altyazi as AltyaziVeri | null;
  const sayfalar = av ? buildPages(buildTokens(av.words), av.stil?.en_kelime ?? 3, av.stil?.en_karakter ?? 18) : [];
  const altyaziKutu = document.getElementById("altyazi");
  let sonAltyazi = "";
  const sahneler = (veri.sahneler ?? []) as DuzenSahne[];
  const yatay = w > h, sahneG = yatayG(h);
  const panelZemin = veri.sahneZemin ?? "#0B0D12";
  const altyaziCiz = (t: number) => {
    if (!av || !altyaziKutu) return;
    const s = sayfaBul(sayfalar, t);
    const html = s ? sayfaHtml(av, s.pg, s.aktif) : "";
    if (html !== sonAltyazi) { altyaziKutu.innerHTML = html; sonAltyazi = html; } // yalnız t'den türer; DOM yazımı azaltılır
  };
  const renk: Renkler = { vurgu: "#FF7A00", ikincil: "#FFD400", yazi: "#FFFFFF", zemin: "#0B0D12", ...(veri.renk ?? {}) };
  const gecisYaz = (el: HTMLElement, katman: HTMLElement, g: GecisStil | null) => {
    el.style.transform = g?.transform ?? "";
    el.style.filter = g?.filter ?? "";
    el.style.clipPath = g?.clipPath ?? "";
    el.style.setProperty("mask-image", g?.mask || "");
    el.style.setProperty("-webkit-mask-image", g?.mask || "");
    const html = g?.katman ?? "";
    if (katman.innerHTML !== html) katman.innerHTML = html;
  };
  const ciz = (t: number) => {
    const lp = sahneler.length ? layoutP(Math.round(t * fps), fps, sahneler) : 0;
    altyaziCiz(t);
    if (sahneler.length && av && altyaziKutu) Object.assign(altyaziKutu.style, altyaziKonum(av, lp, sahneG, CAP_SPLIT_Y));
    window.__ada?.ciz(t); // metin grafikleri ve sahneler (ada.tsx); ada.js bu betikten önce yüklenir
    for (const o of ogeler) {
      const { k } = o;
      const gorunur = t >= k.bas - k.on && t < k.bas + k.sure + k.kuyruk;
      o.kap.style.visibility = gorunur ? "visible" : "hidden";
      if (!gorunur) continue;
      const tSeq = t - (k.bas - k.on);
      if (k.ham) continue;
      const st = donusum(k, o.hz, tSeq, w, h);
      o.don.style.opacity = st.opacity === 1 ? "" : String(st.opacity);
      o.don.style.filter = st.filter;
      o.don.style.clipPath = st.clipPath;
      o.don.style.transform = st.transform;
      o.don.style.transformOrigin = st.transformOrigin;
      // ADR 0045 orta noktalı geçiş: giren klip ön paydan sunumla açılır, çıkan klip kuyruğunda sunumla ayrılır.
      const og = k.gecis_giris, tk = tSeq - k.on;
      gecisYaz(o.gx, o.gkg, ortaMi(og) && tSeq < og!.sure ? gecisStil(og!, tSeq / og!.sure, "entering", w, h, renk) : null);
      gecisYaz(o.cx, o.gkc, ortaMi(k.cikis) && tk > k.sure - k.cikis!.sure / 2
        ? gecisStil(k.cikis!, (tk - (k.sure - k.cikis!.sure / 2)) / k.cikis!.sure, "exiting", w, h, renk) : null);
      if (k.konusmaci && o.odak && o.medya) {
        const kz = konusmaci(k, t, fps, lp);
        // Kurgu.tsx Konusmaci panel geometrisi (lp = 0'da tam kare).
        if (o.panel && sahneler.length) {
          const ps = o.panel.style, r = 40 * lp;
          if (yatay) {
            const sol = sahneG * lp;
            ps.left = `${sol}px`; ps.width = `${w - sol}px`; ps.borderRadius = `${r}px 0 0 ${r}px`;
            o.medya.style.left = `${-sol / 2}px`;
          } else {
            const ust = STAGE_H * lp;
            ps.top = `${ust}px`; ps.height = `${h - ust}px`; ps.borderRadius = `${r}px ${r}px 0 0`;
          }
          ps.background = lp > 0 ? panelZemin : "";
        }
        o.medya.style.transform = !yatay && lp > 0 ? `translateY(${-273 * lp}px) scale(${kz.z})` : `scale(${kz.z})`;
        o.odak.style.transformOrigin = kz.odakOrigin;
        o.odak.style.transform = kz.odakTransform;
      }
    }
  };
  const tl = gsap.timeline({ paused: true });
  const saat = { t: 0 };
  const kaydir = veri.kaydir ?? 0; // pencereli derlemede kompozisyonun 0'ı kurgunun `kaydir` saniyesi
  tl.to(saat, { t: veri.bitis, duration: veri.bitis, ease: "none", onUpdate: () => ciz(tl.time() + kaydir) }, 0);
  ciz(kaydir);
  window.__timelines = window.__timelines || {};
  window.__timelines["main"] = tl;
};

if (typeof window !== "undefined" && typeof document !== "undefined" && window.__KURGU) kur();
