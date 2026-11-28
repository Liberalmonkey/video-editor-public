// Timeline komutları: saf, immer taslağı üzerinde çalışır, test edilir. Çizim ve fare burayı bilmez.
// Değişmez: aynı izde klipler çakışmaz, süreler en az bir karedir.
import { HAZIR, genislet, pisir } from "../../../remotion/hazirEfekt";
import { altyaziKlipleri, kfDeger } from "../../../remotion/izdusum";
import type { Hazir, Iz, KF, Klip, KurguProps } from "../../../remotion/tipler";

export type K = KurguProps;
const EPS = 1e-6;

export const kareYuvarla = (t: number, fps: number) => Math.round(t * fps) / fps;
const bit = (c: Pick<Klip, "bas" | "sure">) => c.bas + c.sure;
const izKlipleri = (k: K, iz: string) => k.klipler.filter((c) => c.iz === iz).sort((a, b) => a.bas - b.bas);
const bul = (k: K, id: string) => k.klipler.find((c) => c.id === id);
// WHY: geçersiz iz referansında `as Iz` undefined değerini gizleyip komutlarda TypeError atmasın.
const izBul = (k: K, id: string): Iz | undefined => k.izler.find((i) => i.id === id);
const kilitsiz = (k: K) => k.izler.filter((i) => !i.kilit).map((i) => i.id);

// Kaynağın izin verdiği uç; süresiz kaynakta (görsel, sahne, metin) sınır yok.
const kaynakSuresi = (k: K, c: Klip) => {
  const s = c.kaynak ? k.kaynaklar[c.kaynak]?.sure : 0;
  return s && s > 0 ? s : Infinity;
};
const sonSinir = (k: K, c: Klip) => Math.max((kaynakSuresi(k, c) - c.giris) / c.hiz, c.sure); // içe alınan uzun klip küçülmeye zorlanmaz

let sayac = 0;
export const yeniId = (k: K, on = "c") => {
  let id = "";
  do id = `${on}${Date.now().toString(36)}${(sayac++).toString(36)}`; while (bul(k, id));
  return id;
};

export const KF_ALANLARI = ["x", "y", "olcek", "opaklik"] as const;
export type KfAlan = (typeof KF_ALANLARI)[number];
// Klibin başı kayınca keyframe'ler içerikte yerinde kalır. Kesilen ucun değeri korunur: animasyon sıçramaz.
const animli = (c: Klip, a: KfAlan) => c.donus.anim.includes(a) || c.donus[a].length > 1;
// Klibin animasyonlu keyframe listeleri: dönüşüm alanları ve kazanç.
type Liste = { al: () => KF[]; yaz: (l: KF[]) => void };
const kfListeleri = (c: Klip): Liste[] => [
  ...KF_ALANLARI.filter((a) => animli(c, a)).map((a) => ({ al: () => c.donus[a], yaz: (l: KF[]) => { c.donus[a] = l; } })),
  ...(c.ses.kf?.length ? [{ al: () => c.ses.kf!, yaz: (l: KF[]) => { c.ses.kf = l; } }] : []),
  // Hazır efekt "keyframe'e çevir" bu ikisine yazar (sarsıntı, eğim, bulanık giriş).
  ...(c.donus.aci?.length ? [{ al: () => c.donus.aci!, yaz: (l: KF[]) => { c.donus.aci = l; } }] : []),
  ...(c.efekt.bulanik_kf?.length ? [{ al: () => c.efekt.bulanik_kf!, yaz: (l: KF[]) => { c.efekt.bulanik_kf = l; } }] : []),
];
const kfKaydir = (c: Klip, d: number) => {
  for (const L of kfListeleri(c)) {
    const l = L.al();
    const uc: KF | null = d > 0 && l.length ? { t: 0, v: kfDeger(l, d, 0), ease: "dogrusal" } : null;
    const yeni = l.map((f) => ({ ...f, t: f.t - d })).filter((f) => f.t >= EPS || (d <= 0 && f.t >= -EPS));
    L.yaz(uc ? [uc, ...yeni] : yeni);
  }
  // Hazır efektin anı da içerikte yerinde kalır.
  if (c.hazir?.length) c.hazir = c.hazir.map((h) => (typeof h.t === "number" ? { ...h, t: Math.max(0, h.t - d) } : h));
};
// Sol parçanın sonu: kesim anındaki değer son keyframe olur.
const kfSonuKes = (c: Klip, d: number) => {
  for (const L of kfListeleri(c)) {
    const l = L.al();
    if (!l.length || d >= l[l.length - 1].t - EPS) continue;
    L.yaz([...l.filter((f) => f.t < d - EPS), { t: d, v: kfDeger(l, d, 0), ease: "dogrusal" }]);
  }
};

// Bağlı eşler: aynı yer ve süre. Biri kırpılınca diğeri de kırpılır, yoksa A/V senkronu sessizce kayar.
// Alt ile tek başına taşınan klip artık eş değildir; bağı sürer, kırpımı ayrılır.
const esler = (k: K, c: Klip) => (c.bag ? k.klipler.filter((x) => x.id !== c.id && x.bag === c.bag && !izBul(k, x.iz)?.kilit && Math.abs(x.bas - c.bas) < 1e-3 && Math.abs(x.sure - c.sure) < 1e-3) : []);

// t anında böl; sağ parçayı döner. Aynı t'de bölünen eşlerin sağ parçaları aynı yeni bağı alır: ortağı bilmek gerekmez.
export const bol = (k: K, c: Klip, t: number): Klip | null => {
  if (t <= c.bas + EPS || t >= bit(c) - EPS) return null;
  const sag: Klip = JSON.parse(JSON.stringify(c));
  sag.id = yeniId(k);
  sag.bag = c.bag ? `${c.bag}:${Math.round(t * 1000)}` : null;
  const d = t - c.bas;
  c.sure = d;
  c.gecis_cikis = null;
  sag.gecis_giris = null;
  sag.bas = t;
  sag.sure -= d;
  sag.giris = c.giris + d * c.hiz;
  // Hazır efekt başladığı parçada kalır; anı yazılmamış çıkış efekti klip sonuna bağlıdır, sağa geçer.
  if (c.hazir?.length) {
    const solda = (h: Hazir) => (typeof h.t === "number" ? h.t : HAZIR[h.ad]?.son ? Infinity : 0) < d - EPS;
    sag.hazir = c.hazir.filter((h) => !solda(h));
    c.hazir = c.hazir.filter(solda);
  }
  kfKaydir(sag, d);
  kfSonuKes(c, d);
  k.klipler.push(sag);
  return sag;
};

// Razor. Sahne bölünmez: animasyonu baştan başlar, kullanıcı kırpar.
export const kes = (k: K, id: string, t: number) => {
  const c = bul(k, id);
  if (!c || c.tur === "sahne" || izBul(k, c.iz)?.kilit) return null;
  const ortaklar = c.bag ? k.klipler.filter((x) => x.id !== c.id && x.bag === c.bag && x.tur !== "sahne" && !izBul(k, x.iz)?.kilit) : [];
  const sag = bol(k, c, t);
  for (const x of ortaklar) bol(k, x, t);
  return sag;
};

// Oynatma kafasında keser: seçim varsa onları, yoksa kilitsiz tüm izleri.
export const kafadaKes = (k: K, t: number, secili: string[]) => {
  const hedef = k.klipler.filter((c) => c.bas < t - EPS && bit(c) > t + EPS && (secili.length ? secili.includes(c.id) : true));
  for (const c of hedef) kes(k, c.id, t);
};

export const sil = (k: K, idler: string[]) => {
  k.klipler = k.klipler.filter((c) => !idler.includes(c.id) || !!izBul(k, c.iz)?.kilit);
};

// Sabit içerik uzar ve kısalır, kesilmez: müzik, sahne, metin, görsel.
const surekli = (c: Klip) => c.tur === "sahne" || c.tur === "metin" || c.tur === "gorsel" || !!c.olay?.muzik;

// [a,b) aralığını verilen izlerden çıkarır, sonrasını sola çeker.
export const aralikSil = (k: K, a: number, b: number, izler = kilitsiz(k), haric: string[] = []) => {
  const d = b - a;
  if (d <= EPS) return;
  for (const iz of izler) {
    for (const c of izKlipleri(k, iz)) {
      if (haric.includes(c.id) || bit(c) <= a + EPS) continue;
      if (c.bas >= b - EPS) { c.bas -= d; continue; }
      if (surekli(c)) {
        const kesisim = Math.min(bit(c), b) - Math.max(c.bas, a);
        if (kesisim >= c.sure - EPS) { k.klipler = k.klipler.filter((x) => x !== c); continue; }
        c.sure -= kesisim;
        if (c.bas > a) c.bas = a;
        continue;
      }
      if (c.tur === "ses" && !c.olay?.muzik && !c.olay?.konusma && c.bas >= a) { k.klipler = k.klipler.filter((x) => x !== c); continue; } // aralıktaki SFX olayı gider
      const sag = bit(c) > b + EPS ? bol(k, c, b) : null;
      const orta = c.bas < a - EPS ? bol(k, c, a) : c;
      if (orta) k.klipler = k.klipler.filter((x) => x !== orta);
      if (sag) sag.bas -= d;
    }
  }
};

// Ripple sil: seçili kliplerin süreleri kilitsiz izlerden çıkar. Sondan başa: öndeki kaydırma arkadakini bozmaz.
export const rippleSil = (k: K, idler: string[]) => {
  const secili = k.klipler.filter((c) => idler.includes(c.id) && !izBul(k, c.iz)?.kilit);
  const araliklar = secili.map((c) => [c.bas, bit(c)] as [number, number]).sort((x, y) => x[0] - y[0]);
  const birlesik: [number, number][] = [];
  for (const [a, b] of araliklar) {
    const son = birlesik[birlesik.length - 1];
    if (son && a <= son[1] + EPS) son[1] = Math.max(son[1], b); else birlesik.push([a, b]);
  }
  for (const [a, b] of birlesik.reverse()) aralikSil(k, a, b);
};

// t'den sonrasını d kadar açar: insert. Kesilebilir klip bölünür, sürekli içerik uzamaz, geride kalır.
export const aralikAc = (k: K, t: number, d: number, izler = kilitsiz(k), haric: string[] = []) => {
  for (const iz of izler) {
    for (const c of izKlipleri(k, iz)) {
      if (haric.includes(c.id) || bit(c) <= t + EPS) continue;
      if (c.bas >= t - EPS) { c.bas += d; continue; }
      if (surekli(c)) continue;
      const sag = bol(k, c, t);
      if (sag) sag.bas += d;
    }
  }
};

// [a,b) aralığını izde boşaltır: overwrite. `haric` klipler dokunulmaz.
export const uzerineYaz = (k: K, iz: string, a: number, b: number, haric: string[] = []) => {
  for (const c of izKlipleri(k, iz)) {
    if (haric.includes(c.id) || bit(c) <= a + EPS || c.bas >= b - EPS) continue;
    if (c.bas >= a - EPS && bit(c) <= b + EPS) { k.klipler = k.klipler.filter((x) => x !== c); continue; }
    if (c.bas < a && bit(c) > b) { bol(k, c, b); const orta = bol(k, c, a); k.klipler = k.klipler.filter((x) => x !== orta); continue; }
    if (c.bas < a) { c.sure = a - c.bas; continue; }
    const d = b - c.bas;
    c.bas = b; c.giris += d * c.hiz; c.sure -= d; kfKaydir(c, d);
  }
};

export const baglilar = (k: K, idler: string[]) => {
  const s = new Set(idler);
  for (const c of k.klipler) if (c.bag && (s.has(c.id) || k.klipler.some((x) => s.has(x.id) && x.bag === c.bag))) s.add(c.id);
  return [...s];
};

export const bagla = (k: K, idler: string[]) => {
  const secili = k.klipler.filter((c) => idler.includes(c.id));
  const bagli = secili.some((c) => c.bag);
  const grup = bagli ? null : yeniId(k, "b");
  for (const c of secili) c.bag = grup;
};

// Taşıma. dIz: aynı türdeki izler arasında satır farkı. insert: hedefte yer açar, overwrite: üzerine yazar.
export const tasi = (k: K, idler: string[], dt: number, dIz: number, insert = false) => {
  const secili = k.klipler.filter((c) => idler.includes(c.id) && !izBul(k, c.iz)?.kilit);
  if (!secili.length) return;
  const enKucuk = Math.min(...secili.map((c) => c.bas));
  const d = Math.max(dt, -enKucuk);
  const izHedef = (c: Klip) => {
    const iz = izBul(k, c.iz);
    if (!iz) return c.iz;
    const ayni = k.izler.filter((i) => i.tur === iz.tur);
    const hedef = ayni[ayni.findIndex((i) => i.id === c.iz) + dIz];
    return hedef && !hedef.kilit ? hedef.id : c.iz;
  };
  const hedefler = secili.map((c) => ({ c, iz: izHedef(c), a: c.bas + d, b: bit(c) + d }));
  // Klipler kendi izinden önce çıkar: kendi eski yeriyle çakışmasın.
  const haric = secili.map((c) => c.id);
  if (insert) {
    const a = Math.min(...hedefler.map((h) => h.a)), b = Math.max(...hedefler.map((h) => h.b));
    const izler = [...new Set(hedefler.map((h) => h.iz))];
    const yedek = secili.map((c) => [c, c.iz] as const);
    for (const [c] of yedek) c.iz = "\u0000tasiniyor"; // açma sırasında bölünmesin
    aralikAc(k, a, b - a, izler);
    // Sürekli içerik açılırken kesilmez; hedef aralıkta kaldıysa burada yer açılır.
    for (const iz of izler) uzerineYaz(k, iz, a, b);
    for (const h of hedefler) { h.c.iz = h.iz; h.c.bas = h.a; }
    return;
  }
  for (const h of hedefler) uzerineYaz(k, h.iz, h.a, h.b, haric);
  for (const h of hedefler) { h.c.iz = h.iz; h.c.bas = h.a; }
};

const komsu = (k: K, c: Klip) => {
  const l = izKlipleri(k, c.iz);
  const i = l.findIndex((x) => x.id === c.id);
  return { once: l[i - 1] as Klip | undefined, sonra: l[i + 1] as Klip | undefined };
};
const kare = (k: K) => 1 / k.sekans.fps;

// Kırpılabilecek pay: komşuya ve kaynak sınırına dayanır.
const kirpPayi = (k: K, c: Klip, kenar: "bas" | "son", dt: number) => {
  const { once, sonra } = komsu(k, c);
  if (kenar === "son") {
    const ust = Math.min(sonSinir(k, c), sonra ? sonra.bas - c.bas : Infinity);
    return Math.min(Math.max(kare(k), c.sure + dt), ust) - c.sure;
  }
  const kaynakPay = c.kaynak && kaynakSuresi(k, c) !== Infinity ? c.giris / c.hiz : Infinity;
  const alt = -Math.min(kaynakPay, c.bas - (once ? bit(once) : 0));
  return Math.min(Math.max(dt, alt), c.sure - kare(k));
};
const kirpUygula = (c: Klip, kenar: "bas" | "son", d: number) => {
  if (kenar === "son") { c.sure += d; return; }
  c.bas += d; c.sure -= d; c.giris = Math.max(0, c.giris + d * c.hiz);
  kfKaydir(c, d);
};
// Eşlerin hepsine sığan en küçük pay uygulanır: biri komşuya dayanınca diğeri de durur.
const enKucukPay = (l: number[], dt: number) => l.reduce((a, b) => (Math.abs(b) < Math.abs(a) ? b : a), dt);

// Normal kırpma.
export const kirp = (k: K, id: string, kenar: "bas" | "son", dt: number) => {
  const c = bul(k, id);
  if (!c || izBul(k, c.iz)?.kilit) return;
  const ortak = [c, ...esler(k, c)];
  const d = enKucukPay(ortak.map((x) => kirpPayi(k, x, kenar, dt)), dt);
  for (const x of ortak) kirpUygula(x, kenar, d);
};

// Ripple kırpma: süre değişir, sonrası kayar, boşluk açılmaz. Diğer izler aralık silme ve açma kuralıyla senkron kalır;
// yalnız kaydırmak, uzun klibin altına bir sonrakini sokardı.
export const rippleKirp = (k: K, id: string, kenar: "bas" | "son", dt: number) => {
  const c = bul(k, id);
  if (!c || izBul(k, c.iz)?.kilit) return;
  // Eşler aralık işlemine girmez: sile sile bölünüp bağını yitirirdi, doğrudan aynı kırpımı alır.
  const ortak = [c, ...esler(k, c)];
  const haric = ortak.map((x) => x.id);
  if (kenar === "son") {
    const sinir = bit(c);
    const d = enKucukPay(ortak.map((x) => Math.min(Math.max(kare(k), x.sure + dt), sonSinir(k, x)) - x.sure), dt);
    for (const x of ortak) x.sure += d;
    if (d < 0) aralikSil(k, sinir + d, sinir, kilitsiz(k), haric); else aralikAc(k, sinir, d, kilitsiz(k), haric);
    return;
  }
  const d = enKucukPay(ortak.map((x) => {
    const pay = x.kaynak && kaynakSuresi(k, x) !== Infinity ? x.giris / x.hiz : Infinity;
    return Math.min(Math.max(dt, -pay), x.sure - kare(k));
  }), dt);
  for (const x of ortak) { x.sure -= d; x.giris = Math.max(0, x.giris + d * x.hiz); kfKaydir(x, d); }
  if (d > 0) aralikSil(k, c.bas, c.bas + d, kilitsiz(k), haric); else aralikAc(k, c.bas, -d, kilitsiz(k), haric);
};

// Rolling: iki bitişik klibin ortak kesimi kayar, toplam süre değişmez.
export const rolling = (k: K, solId: string, sagId: string, dt: number) => {
  const a = bul(k, solId), b = bul(k, sagId);
  if (!a || !b || izBul(k, a.iz)?.kilit) return;
  const ust = Math.min(sonSinir(k, a) - a.sure, b.sure - kare(k));
  const pay = b.kaynak && kaynakSuresi(k, b) !== Infinity ? b.giris / b.hiz : Infinity;
  const ea = esler(k, a), eb = esler(k, b);
  // Eşin de aynı payı olmalı; bitişik olmayan eş kendi komşusuna dayanır.
  const d = enKucukPay([Math.min(Math.max(dt, -Math.min(a.sure - kare(k), pay)), ust), ...ea.map((x) => kirpPayi(k, x, "son", dt)), ...eb.map((x) => kirpPayi(k, x, "bas", dt))], dt);
  for (const x of [a, ...ea]) x.sure += d;
  for (const x of [b, ...eb]) { x.bas += d; x.sure -= d; x.giris = Math.max(0, x.giris + d * x.hiz); kfKaydir(x, d); }
};

// Slip: yer ve süre sabit, kaynakta pencere kayar.
export const slip = (k: K, id: string, dt: number) => {
  const c = bul(k, id);
  if (!c || !c.kaynak || izBul(k, c.iz)?.kilit) return;
  const ust = Math.max(0, kaynakSuresi(k, c) - c.sure * c.hiz);
  const yeni = Math.min(Math.max(0, c.giris + dt * c.hiz), ust === Infinity ? c.giris + dt * c.hiz : ust);
  // Aynı kaynaktaki eş de kayar: görüntü ve ses aynı kaynak anında kalır.
  for (const x of esler(k, c)) if (x.kaynak === c.kaynak) x.giris = yeni;
  c.giris = yeni;
};

// Slide: içerik sabit, klip komşuların arasında kayar; toplam süre değişmez.
// shortcut: bağlı eşi olan klip kaymaz, önce Ctrl+L ile çözülür; iki izde birlikte slide gerekirse burada genişletilir.
export const slide = (k: K, id: string, dt: number) => {
  const c = bul(k, id);
  if (!c || izBul(k, c.iz)?.kilit || esler(k, c).length) return;
  const { once, sonra } = komsu(k, c);
  const bitisikOnce = once && Math.abs(bit(once) - c.bas) < EPS ? once : undefined;
  const bitisikSonra = sonra && Math.abs(bit(c) - sonra.bas) < EPS ? sonra : undefined;
  let alt = -c.bas, ust = Infinity;
  if (once) alt = bitisikOnce ? -(bitisikOnce.sure - kare(k)) : once ? bit(once) - c.bas : alt;
  if (bitisikSonra) {
    const pay = bitisikSonra.kaynak && kaynakSuresi(k, bitisikSonra) !== Infinity ? bitisikSonra.giris / bitisikSonra.hiz : Infinity;
    alt = Math.max(alt, -pay);
    ust = bitisikSonra.sure - kare(k);
  } else if (sonra) ust = sonra.bas - bit(c);
  if (bitisikOnce) ust = Math.min(ust, sonSinir(k, bitisikOnce) - bitisikOnce.sure);
  const d = Math.min(Math.max(dt, alt), ust);
  if (bitisikOnce) bitisikOnce.sure += d;
  if (bitisikSonra) { bitisikSonra.bas += d; bitisikSonra.sure -= d; bitisikSonra.giris = Math.max(0, bitisikSonra.giris + d * bitisikSonra.hiz); kfKaydir(bitisikSonra, d); }
  c.bas += d;
};

// Q/W: oynatma kafasından önceki ya da sonraki kısmı ripple ile siler.
export const qw = (k: K, t: number, yon: "q" | "w", secili: string[]) => {
  const izler = kilitsiz(k);
  const adaylar = k.klipler.filter((c) => izler.includes(c.iz) && c.bas < t - EPS && bit(c) > t + EPS && (secili.length ? secili.includes(c.id) : c.tur !== "sahne" && !c.olay?.muzik));
  const c = adaylar.sort((x, y) => izler.indexOf(y.iz) - izler.indexOf(x.iz))[0];
  if (!c) return;
  if (yon === "q") rippleKirp(k, c.id, "bas", t - c.bas);
  else rippleKirp(k, c.id, "son", t - bit(c));
};

export interface YeniKlip { tur: Klip["tur"]; iz: string; bas: number; sure: number; kaynak?: string | null; giris?: number; olay?: Record<string, any> | null; metin?: string | null; metin_stil?: Record<string, any> | null; sahne?: Record<string, any> | null; ses?: Partial<Klip["ses"]>; bilesen?: Klip["bilesen"] }

export const klipYap = (k: K, y: YeniKlip): Klip => ({
  id: yeniId(k), iz: y.iz, bas: y.bas, sure: y.sure, tur: y.tur, kaynak: y.kaynak ?? null, giris: y.giris ?? 0, hiz: 1, bag: null,
  ses_kapali: false, konusmaci: false, zoom: 1, punches: [],
  donus: { x: [], y: [], olcek: [], opaklik: [], anim: [] },
  efekt: { parlaklik: 1, kontrast: 1, doygunluk: 1, bulanik: 0, kirp: null },
  ses: { gain_db: 0, fade_in: 0.012, fade_out: 0.012, duck: false, ...y.ses },
  gecis_giris: null, gecis_cikis: null, sahne: y.sahne ?? null, metin: y.metin ?? null, metin_stil: y.metin_stil ?? null, olay: y.olay ?? null, ...(y.bilesen ? { bilesen: y.bilesen } : {}),
});

export const klipEkle = (k: K, y: YeniKlip, insert = false) => {
  const iz = izBul(k, y.iz);
  if (!iz || iz.kilit) return null;
  if (insert) aralikAc(k, y.bas, y.sure);
  uzerineYaz(k, y.iz, y.bas, y.bas + y.sure); // insert'te sürekli içerik açılmaz, burada yer açılır
  const c = klipYap(k, y);
  k.klipler.push(c);
  return c;
};

export const izEkle = (k: K, tur: Iz["tur"]) => {
  const on = tur === "video" ? "V" : "A";
  let n = 1;
  while (k.izler.some((i) => i.id === `${on}${n}`)) n++;
  const iz: Iz = { id: `${on}${n}`, tur, ad: "", kilit: false, sessiz: false, gizli: false, gain_db: 0 };
  // Video izi en üste, ses izi en alta; Premiere düzeni.
  if (tur === "video") k.izler.unshift(iz); else k.izler.push(iz);
  return iz.id;
};

// Ayrık ses için iz: boş ise A1 ya da yalnız konuşma klibi taşıyan iz. SFX ve müzik izine karışmaz.
const konusmaIzi = (k: K, a: number, b: number) => {
  const uygun = k.izler.find((i) => {
    if (i.tur !== "ses" || i.kilit) return false;
    const l = k.klipler.filter((c) => c.iz === i.id);
    return (l.length ? l.every((c) => c.olay?.konusma) : i.id === "A1" || i.ad === "Konuşma") && !l.some((c) => c.bas < b - EPS && bit(c) > a + EPS);
  });
  if (uygun) return uygun.id;
  const id = izEkle(k, "ses");
  const iz = k.izler.pop() as Iz;
  iz.ad = "Konuşma";
  k.izler.splice(k.izler.findIndex((i) => i.tur === "ses"), 0, iz);
  return id;
};

const ayrilabilir = (k: K, c: Klip) => c.tur === "video" && !c.ses_kapali && !!c.kaynak && !!k.kaynaklar[c.kaynak]?.ses;

// Görüntü ve sesi ayırır. Ses, aynı kaynak aralığıyla bağlı klip olur; iz kazancı klibe geçer ki seviye sıçramasın.
// shortcut: önceki klibin çapraz geçiş kuyruğu ayrık sese geçmez, yalnız giriş fade'i taşınır; duyulursa kuyruk da ses klibine eklenir.
export const sesiAyir = (k: K, idler: string[]) => {
  const secili = k.klipler.filter((c) => idler.includes(c.id) && ayrilabilir(k, c) && !izBul(k, c.iz)?.kilit).sort((a, b) => a.bas - b.bas);
  const yeni: string[] = [];
  let hizli = 0;
  for (const c of secili) {
    if (c.hiz !== 1) { hizli++; continue; } // shortcut: ffmpeg miksinde atempo yok, hızlı klip ayrılmaz; gerekirse olaysesi'ne eklenir
    const grup = c.bag ?? yeniId(k, "b");
    const gg = c.gecis_giris && c.gecis_giris.tur !== "kaydir" ? c.gecis_giris.sure : 0;
    const izKazanc = izBul(k, c.iz)?.gain_db ?? 0;
    const s = klipYap(k, { tur: "ses", iz: konusmaIzi(k, c.bas, bit(c)), bas: c.bas, sure: c.sure, kaynak: c.kaynak, giris: c.giris, olay: { konusma: true },
      ses: { ...c.ses, gain_db: c.ses.gain_db + izKazanc, fade_in: Math.max(c.ses.fade_in, gg), kf: (c.ses.kf ?? []).map((f) => ({ ...f, v: f.v + izKazanc })) } });
    s.bag = grup;
    c.bag = grup;
    c.ses_kapali = true;
    k.klipler.push(s);
    yeni.push(s.id);
  }
  return { yeni, hizli };
};

// Ayrıştırılmış konuşma: ses klibi vokal kaynağına geçer, kelimeler aynı zamanda olduğu için kopyalanır.
// Sesi hâlâ videodaysa önce ayrılır. Görüntüye birleştirilemez: kaynağı artık farklıdır.
export const vokaleGec = (k: K, id: string, v: { id: string; yol: string; sure: number }) => {
  const c = bul(k, id);
  if (!c?.kaynak) return null;
  const eski = c.kaynak;
  k.kaynaklar[v.id] = { yol: v.yol, sure: v.sure, ses: true };
  if (k.kelimeler?.[eski]) k.kelimeler[v.id] = k.kelimeler[eski].map((w) => ({ ...w }));
  const sesId = c.olay?.konusma ? c.id : sesiAyir(k, [c.id]).yeni[0];
  const s = sesId ? bul(k, sesId) : null;
  if (s) s.kaynak = v.id;
  return s?.id ?? null;
};

// Ayrılmış kanalları (müzik, davul…) kaynak klibiyle aynı yer ve kaynak anında, her biri kendi sessiz izine koyar.
// Sessiz başlar: asıl ses hâlâ çalıyorsa üst üste binmesin; kullanıcı karıştırırken M'yi kapatır. WHY: bkz. wiki/decisions/0034-ses-araclari.md
export const stemEkle = (k: K, id: string, stemler: { ad: string; id: string; yol: string; sure: number }[]) => {
  const c = bul(k, id);
  if (!c?.kaynak) return 0;
  for (const s of stemler) {
    k.kaynaklar[s.id] = { yol: s.yol, sure: s.sure, ses: true };
    const iz = izEkle(k, "ses");
    const yeniIz = izBul(k, iz);
    if (yeniIz) Object.assign(yeniIz, { ad: s.ad, sessiz: true });
    klipEkle(k, { tur: "ses", iz, bas: c.bas, sure: c.sure, kaynak: s.id, giris: c.giris, olay: { muzik: true } });
  }
  return stemler.length;
};

// Geri birleştirir: ses videoyla aynı yer ve kaynak anındaysa. Kaymış ses birleşince senkron bozulacağı için durur.
export const sesiBirlestir = (k: K, idler: string[]) => {
  const secili = baglilar(k, idler);
  let birlesen = 0, kayik = 0;
  for (const s of k.klipler.filter((c) => secili.includes(c.id) && c.olay?.konusma)) {
    const v = k.klipler.find((c) => c.ses_kapali && c.kaynak === s.kaynak && c.bag === s.bag && Math.abs(c.bas - s.bas) < 1e-3 && Math.abs(c.sure - s.sure) < 1e-3 && Math.abs(c.giris - s.giris) < 1e-3);
    if (!v) { kayik++; continue; }
    v.ses_kapali = false;
    const vIzKazanc = izBul(k, v.iz)?.gain_db ?? 0;
    v.ses = { ...s.ses, gain_db: s.ses.gain_db - vIzKazanc, kf: (s.ses.kf ?? []).map((f) => ({ ...f, v: f.v - vIzKazanc })) };
    k.klipler = k.klipler.filter((c) => c.id !== s.id);
    if (!k.klipler.some((c) => c.id !== v.id && c.bag === v.bag)) v.bag = null;
    birlesen++;
  }
  return { birlesen, kayik };
};

export const izSil = (k: K, id: string) => {
  const iz = izBul(k, id);
  if (!iz || k.klipler.some((c) => c.iz === id)) return false;
  if (k.izler.filter((i) => i.tur === iz.tur).length <= 1) return false;
  k.izler = k.izler.filter((i) => i.id !== id);
  return true;
};

// ---------------- Efekt Kontrolleri
const kfSirala = (l: KF[]) => l.sort((x, y) => x.t - y.t);

// Kapalıysa tek sabit değer; açıksa oynatma kafasında keyframe yazar. t klibin başından.
export const degerYaz = (k: K, id: string, a: KfAlan, t: number, v: number) => {
  const c = bul(k, id);
  if (!c) return;
  if (!animli(c, a)) { c.donus[a] = [{ t: 0, v, ease: "dogrusal" }]; return; }
  const l = c.donus[a];
  const var_ = l.find((f) => Math.abs(f.t - t) < 1 / (2 * k.sekans.fps));
  if (var_) var_.v = v; else { l.push({ t, v, ease: "dogrusal" }); kfSirala(l); }
};

export const animDegistir = (k: K, id: string, a: KfAlan, t: number, varsayilan: number) => {
  const c = bul(k, id);
  if (!c) return;
  const su = kfDeger(c.donus[a], t, varsayilan);
  if (animli(c, a)) {
    c.donus.anim = c.donus.anim.filter((x) => x !== a);
    c.donus[a] = su === varsayilan ? [] : [{ t: 0, v: su, ease: "dogrusal" }];
  } else {
    c.donus.anim.push(a);
    c.donus[a] = [{ t, v: su, ease: "dogrusal" }];
  }
};

export const kfDegistir = (k: K, id: string, a: KfAlan, t: number, varsayilan: number) => {
  const c = bul(k, id);
  if (!c) return;
  const l = c.donus[a];
  const i = l.findIndex((f) => Math.abs(f.t - t) < 1 / (2 * k.sekans.fps));
  if (i >= 0) l.splice(i, 1);
  else { l.push({ t, v: kfDeger(l, t, varsayilan), ease: "dogrusal" }); kfSirala(l); }
};

export const kfTasi = (k: K, id: string, a: KfAlan, eski: number, yeni: number) => {
  const c = bul(k, id);
  const f = c?.donus[a].find((x) => Math.abs(x.t - eski) < 1e-4);
  if (!c || !f) return;
  f.t = Math.max(0, Math.min(c.sure, yeni));
  kfSirala(c.donus[a]);
};

export const kfEgri = (k: K, id: string, a: KfAlan, t: number, ease: KF["ease"]) => {
  const f = bul(k, id)?.donus[a].find((x) => Math.abs(x.t - t) < 1 / (2 * k.sekans.fps));
  if (f) f.ease = ease;
};

// Hız: kaynak aralığı korunur, süre değişir. Yer yoksa sonraki klibe kadar kısalır.
export const hizAyarla = (k: K, id: string, hiz: number) => {
  const c = bul(k, id);
  // WHY: render'da ayrık ses ffmpeg miksidir, hız uygulanmaz; görüntü tek başına hızlanırsa senkron gider.
  if (!c || izBul(k, c.iz)?.kilit || (c.ses_kapali && esler(k, c).some((x) => x.olay?.konusma))) return;
  const h = Math.min(8, Math.max(0.1, hiz));
  const { sonra } = komsu(k, c);
  const hedef = (c.sure * c.hiz) / h;
  const oran = c.hiz / h;
  c.hiz = h;
  c.sure = Math.max(kare(k), Math.min(hedef, sonra ? sonra.bas - c.bas : Infinity));
  // Keyframe'ler içerikte yerinde kalsın.
  for (const L of kfListeleri(c)) L.yaz(L.al().map((f) => ({ ...f, t: f.t * oran })));
  // Hazır efektin anı içerikle kayar; süresi hareket süresidir, hızdan bağımsız kalır (aralık denetimi bozulmasın).
  if (c.hazir?.length) c.hazir = c.hazir.map((h) => (typeof h.t === "number" ? { ...h, t: h.t * oran } : h));
  c.punches = [...c.punches];
};

// Hazır efekt (ADR 0033): klibe kayıt olarak yazılır, keyframe'e render'da açılır. t klibin başından.
export const hazirEkle = (k: K, id: string, ad: string, t: number) => {
  const c = bul(k, id);
  if (!c || !HAZIR[ad]) return;
  const tt = Math.round(Math.max(0, Math.min(c.sure - kare(k), t)) * 1000) / 1000;
  c.hazir = [...(c.hazir ?? []), HAZIR[ad].son || !tt ? { ad } : { ad, t: tt }];
};
// v undefined: alan silinir, varsayılana döner.
export const hazirYaz = (k: K, id: string, i: number, alan: string, v: number | string | boolean | undefined) => {
  const h = bul(k, id)?.hazir?.[i];
  if (!h) return;
  if (v === undefined) delete h[alan]; else h[alan] = v;
};
export const hazirSil = (k: K, id: string, i: number) => { bul(k, id)?.hazir?.splice(i, 1); };
// Keyframe'e çevir: o anki açılım (değişim sayacı dahil) el keyframe'ine yazılır, kayıt silinir.
export const hazirPisir = (k: K, id: string, i: number) => {
  const c = bul(k, id);
  const iz = genislet(k.klipler, { w: k.sekans.w, h: k.sekans.h, fps: k.sekans.fps }).get(id)?.[i];
  if (!c || !iz) return;
  pisir(c, iz);
  c.hazir!.splice(i, 1);
};

// Yazı ve sahne klibi oluşturma
// Üst katman klibi konuşmacıyı ya da sahneyi ezmesin: aralığı boş en üst iz, yoksa yeni iz.
export const bosIz = (k: K, a: number, b: number) => {
  const iz = k.izler.find((i) => i.tur === "video" && !i.kilit && !k.klipler.some((c) => c.iz === i.id && c.bas < b - EPS && bit(c) > a + EPS));
  return iz ? iz.id : izEkle(k, "video");
};

export const metinEkle = (k: K, t: number, metin: string) => klipEkle(k, { tur: "metin", iz: bosIz(k, t, t + 3), bas: t, sure: 3, metin });

export const sahneEkle = (k: K, t: number, sahne: Record<string, any>, sure: number) => {
  const iz = k.izler.find((i) => i.tur === "video" && !i.kilit && k.klipler.some((c) => c.iz === i.id && c.tur === "sahne")) ?? k.izler.find((i) => i.tur === "video" && !i.kilit);
  // WHY: bölünmüş sahne en altta çizilir; altındaki video konuşmacı düzenine geçmezse sahneyi tamamen örter.
  if (sahne.layout === "split") for (const c of k.klipler) if (c.iz === k.altyazi.iz && c.tur === "video" && c.bas < t + sure - EPS && bit(c) > t + EPS) c.konusmaci = true;
  return iz ? klipEkle(k, { tur: "sahne", iz: iz.id, bas: t, sure, sahne }) : null;
};

export const SEKANSLAR = { "9:16": { w: 1080, h: 1920 }, "16:9": { w: 1920, h: 1080 } } as const;
export type Oran = keyof typeof SEKANSLAR;
export const sekansOrani = (k: K): Oran => (k.sekans.w > k.sekans.h ? "16:9" : "9:16");
export const sekansAyarla = (k: K, o: Oran) => { k.sekans.w = SEKANSLAR[o].w; k.sekans.h = SEKANSLAR[o].h; };
// Boş kurguya ilk video gelince sekans ona uyar; kare kaynak dikey sayılır.
export const sekansKaynaktan = (k: K, w?: number | null, h?: number | null): Oran | null => {
  if (!w || !h) return null;
  const o: Oran = w > h ? "16:9" : "9:16";
  if (o === sekansOrani(k)) return null;
  sekansAyarla(k, o);
  return o;
};

export const KAZANC_ALT = -24, KAZANC_UST = 12;
// Bu kliplerde ses çizgisi ve kazanç anlamlı: ses klibi ya da sesi üzerinde duran video.
export const sesli = (k: K, c: Klip) => c.tur === "ses" || (c.tur === "video" && !c.ses_kapali && !!c.kaynak && !!k.kaynaklar[c.kaynak]?.ses);
const dbSinir = (db: number) => Math.max(-60, Math.min(24, Math.round(db * 2) / 2));
// Klip başından t anındaki kazanç, dB.
export const kazancAni = (c: Klip, t: number) => (c.ses.kf?.length ? kfDeger(c.ses.kf, t, c.ses.gain_db) : c.ses.gain_db);
// t verilir ve kazanç animasyonluysa o anda keyframe yazar; yoksa tüm eğriyi birlikte kaydırır.
export const kazancYaz = (k: K, id: string, db: number, t?: number) => {
  const c = bul(k, id);
  if (!c || izBul(k, c.iz)?.kilit) return;
  const v = dbSinir(db);
  if (!c.ses.kf?.length || t === undefined) {
    if (c.ses.kf?.length) { const d = v - c.ses.gain_db; c.ses.kf = c.ses.kf.map((f) => ({ ...f, v: dbSinir(f.v + d) })); }
    c.ses.gain_db = v;
    return;
  }
  const tt = Math.max(0, Math.min(c.sure, t));
  const var_ = c.ses.kf.find((f) => Math.abs(f.t - tt) < 1 / (2 * k.sekans.fps));
  if (var_) var_.v = v; else { c.ses.kf.push({ t: tt, v, ease: "dogrusal" }); kfSirala(c.ses.kf); }
};
// Kazanç animasyonu aç/kapat. Kapatınca o anki değer sabit kalır.
export const sesKfAnim = (k: K, id: string, t: number) => {
  const c = bul(k, id);
  if (!c || izBul(k, c.iz)?.kilit) return;
  if (c.ses.kf?.length) { c.ses.gain_db = dbSinir(kazancAni(c, t)); c.ses.kf = []; }
  else c.ses.kf = [{ t: Math.max(0, Math.min(c.sure, t)), v: c.ses.gain_db, ease: "dogrusal" }];
};
// t'ye `tol` kadar yakın keyframe varsa siler, yoksa o andaki değerle ekler. Son keyframe silinince değer sabit kalır.
export const sesKfDegistir = (k: K, id: string, t: number, tol: number) => {
  const c = bul(k, id);
  if (!c || izBul(k, c.iz)?.kilit) return;
  const l = c.ses.kf ?? [];
  const i = l.findIndex((f) => Math.abs(f.t - t) <= tol);
  if (i >= 0) {
    if (l.length === 1) c.ses.gain_db = l[0].v;
    l.splice(i, 1);
  } else { l.push({ t: Math.max(0, Math.min(c.sure, t)), v: dbSinir(kazancAni(c, t)), ease: "dogrusal" }); kfSirala(l); }
  c.ses.kf = l;
};
export const kazancEkle = (k: K, idler: string[], d: number) => {
  for (const c of k.klipler) if (idler.includes(c.id) && sesli(k, c)) kazancYaz(k, c.id, c.ses.gain_db + d);
};

// Metinden ve öneriden kurgu: sekans aralıklarını tüm kilitsiz izlerden ripple ile çıkarır. Sondan başa: öndeki silme arkadakini kaydırmaz.
export const araliklariCikar = (k: K, l: [number, number][]) => {
  const birlesik: [number, number][] = [];
  for (const [a, b] of [...l].filter(([a, b]) => b - a > EPS).sort((x, y) => x[0] - y[0])) {
    const son = birlesik[birlesik.length - 1];
    if (son && a <= son[1] + EPS) son[1] = Math.max(son[1], b); else birlesik.push([a, b]);
  }
  for (const [a, b] of birlesik.reverse()) aralikSil(k, a, b);
  return birlesik.reduce((n, [a, b]) => n + b - a, 0);
};

// Altyazı kelimeleri kaynak zamanında durur; panel klip başına izdüşümle gösterir.
export interface KelimeSatiri { kaynak: string; i: number; w: string; s: number; e: number; klip: string }
export const kelimeSatirlari = (k: K): KelimeSatiri[] => {
  const cikti: KelimeSatiri[] = [];
  for (const c of altyaziKlipleri(k)) {
    const son = c.giris + c.sure * c.hiz;
    (k.kelimeler?.[c.kaynak!] ?? []).forEach((w, i) => {
      if (c.giris <= w.s && w.s < son) cikti.push({ kaynak: c.kaynak!, i, w: w.w, s: c.bas + (w.s - c.giris) / c.hiz, e: c.bas + (Math.min(w.e, son) - c.giris) / c.hiz, klip: c.id });
    });
  }
  return cikti;
};

export const kelimeYaz = (k: K, kaynak: string, i: number, w: string) => {
  const l = k.kelimeler?.[kaynak];
  if (l?.[i]) l[i].w = w;
};
export const kelimeSil = (k: K, kaynak: string, i: number) => { k.kelimeler?.[kaynak]?.splice(i, 1); };
// Sınır kayması: komşuyu geçmez, en az bir kare kalır.
export const kelimeZaman = (k: K, kaynak: string, i: number, ds: number, de: number) => {
  const l = k.kelimeler?.[kaynak];
  const w = l?.[i];
  if (!l || !w) return;
  const kr = kare(k);
  const s = Math.max(i ? l[i - 1].e : 0, w.s + ds);
  const e = Math.min(l[i + 1]?.s ?? Infinity, w.e + de);
  if (e - s < kr) return;
  w.s = s; w.e = e;
};

// Yapışma: `adaylar` içinde `eşik` saniyeden yakın olanı döner.
export const yapis = (t: number, adaylar: number[], esik: number) => {
  let en: number | null = null, f = esik;
  for (const a of adaylar) { const d = Math.abs(a - t); if (d <= f) { f = d; en = a; } }
  return en;
};

export const kesimNoktalari = (k: K, haric: string[] = []) => {
  const s = new Set<number>([0]);
  for (const c of k.klipler) if (!haric.includes(c.id)) { s.add(c.bas); s.add(bit(c)); }
  for (const m of k.isaretler ?? []) s.add(m.t);
  return [...s].sort((a, b) => a - b);
};

// Çakışma denetimi: testler ve kaydetme öncesi güvenlik.
export const cakisma = (k: K) => {
  for (const i of k.izler) {
    const l = izKlipleri(k, i.id);
    for (let n = 1; n < l.length; n++) if (l[n].bas < bit(l[n - 1]) - 1e-3) return `${i.id}: ${l[n - 1].id} ile ${l[n].id} çakışıyor`;
  }
  for (const c of k.klipler) if (c.sure <= 0) return `${c.id}: süre sıfır`;
  return null;
};

// ADR 0045/0046: native motion bileşeni (ör. içe aktarılmış Lottie: dis/lottie) boş bir görüntü izine eklenir.
export const bilesenEkle = (k: K, t: number, bilesen: NonNullable<Klip["bilesen"]>, sure: number) =>
  klipEkle(k, { tur: "motion", iz: bosIz(k, t, t + sure), bas: t, sure, bilesen });
